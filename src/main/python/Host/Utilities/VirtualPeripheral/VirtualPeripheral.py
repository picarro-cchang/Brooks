import sys
import os
import time
import getopt
import socket
from datetime import datetime
from struct import pack

from Host.Common.SharedTypes import TCP_PORT_PERIPH_INTRF
from Host.Common.timestamp import getTimestamp
from Host.Common.CustomConfigObj import CustomConfigObj

class VirturalPeripheral(object):
    def __init__(self, configFile, dataFile, inertialGPS=False):
        if not os.path.exists(configFile):
            raise Exception("Configuration file not found: %s" % configFile)
        self.config = configFile
        if not os.path.exists(dataFile):
            raise Exception("Data file not found: %s" % dataFile)
        self.dataFile = dataFile
        self.inertialGPS = inertialGPS
            
    def SendGPS2Socket(self, timeStr, degLat, degLong, port, delim):
    # format: http://www.trimble.com/OEM_ReceiverHelp/V4.44/en/NMEA-0183messages_GGA.html
        sgnLat = "N" if degLat >= 0 else "S"
        sgnLong = "E" if degLong >= 0 else "W"
        LatStr = "%02d%f" % (abs(int(degLat)), (abs(degLat) % 1) * 60)
        LongStr = "%03d%f" % (abs(int(degLong)), (abs(degLong) % 1) * 60)
        fit = 1
        dataStr = "$GPGGA,%s,%s,%s,%s,%s,%d" % (timeStr, LatStr, sgnLat, LongStr, sgnLong, fit)
        header = self.MakeDataHeader(port, len(dataStr))
        self.sock.send(header + dataStr + delim)
        
    def SendSigmaGPS2Socket(self, timeStr, sigmaLat, sigmaLong, port, delim):
    # format: http://www.trimble.com/OEM_ReceiverHelp/V4.44/en/NMEA-0183messages_GST.html
        dataStr = "$GPGST,%s,,,,,%s,%s" % (timeStr, sigmaLat, sigmaLong)
        header = self.MakeDataHeader(port, len(dataStr))
        self.sock.send(header + dataStr + delim)
        
    def SendGillWindSpeed2Socket(self, windLat, windLon, port, delim):
        data = "Q,%+07.2f,%+07.2f,M,00," % (windLon, windLat)
        checksum = 0
        for b in data:
            checksum ^= ord(b)
        dataStr = "%c%s%c%2X" % (2, data, 3, checksum)
        header = self.MakeDataHeader(port, 27)
        self.sock.send(header + dataStr + delim)
        
    def MakeDataHeader(self, port, dataLength):
        id = "%c%c" % (0x5A, 0xA5)
        timestamp = pack('<Q', getTimestamp())
        port = chr(port)
        byteCount = pack('<H', dataLength)
        return "".join([id, timestamp, port, byteCount])
    
    def getDataFromFile(self):
        with open(self.dataFile, 'r') as f:
            data = f.read().split('\n
            self.data = []
            for index in range(len(data)):
                line = data[index]
                if len(line) > 0:
                    self.data.append(line.split(','))

    def run(self):
        co = CustomConfigObj(self.config)
        for section in co.list_sections():
            label = co.get(section, "DATALABELS", "")
            if "GPS" in label:
                portGps = int(section[4:])
            elif "WS_WIND" in label:
                portGill = int(section[4:])
        # create socket server
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            serversocket.bind(('localhost', TCP_PORT_PERIPH_INTRF))
        except socket.error , msg:
            print 'Bind failed. Error code: ' + str(msg[0]) + 'Error message: ' + msg[1]
            sys.exit(1)
        serversocket.listen(1)
        f = open(self.dataFile, 'r') 
        data = f.read().split('\n')
        length = len(data)
        try:
            while True:
                s = raw_input("Start communicating with client? (Y/N): ")
                if s.lower() != 'y':
                    break
                while True: # waiting for the client
                    (clientsocket, address) = serversocket.accept()
                    if clientsocket is not None:
                        self.sock = clientsocket
                        print 'Connected with ' + address[0] + ':' + str(address[1])
                        break
            
                index = 0
                timeOffset = 0
                gpsTimeOffset = 0
                try:
                    while True:
                        line = data[index]
                        if len(line) > 0:
                            if self.inertialGPS:
                                ts, gpsTime, degLat, degLong, sigmaLat, sigmaLong, windLat, windLon = line.split(',')    # gpsTime is in form of epoch time
                            else:
                                ts, gpsTime, degLat, degLong, windLat, windLon = line.split(',')
                            ts = float(ts)
                            gpsTime = float(gpsTime)
                            t = time.time()
                            if timeOffset == 0:
                                # shift the recorded time by a constant value
                                timeOffset = t - ts
                                gpsTimeOffset = t - gpsTime
                                newGpsTime = t
                            else:
                                newGpsTime = gpsTime + gpsTimeOffset
                                time.sleep(ts + timeOffset - t)
                            timeStr = "%s.%d" % (time.strftime("%H%M%S", time.gmtime(newGpsTime)), 1000*newGpsTime % 1000)
                            self.SendGPS2Socket(timeStr, float(degLat), float(degLong), portGps, '\n') 
                            if self.inertialGPS:
                                self.SendSigmaGPS2Socket(timeStr, float(sigmaLat), float(sigmaLong), portGps, '\n') 
                            self.SendGillWindSpeed2Socket(float(windLat), float(windLon), portGill, '\n')
                        index += 1 
                        if index == length:
                            index = 0
                            timeOffset = 0
                            time.sleep(1)
                except Exception,e: 
                    print str(e)
        finally:
            f.close()
            self.sock.close()
            serversocket.close()

HELP_STRING = """VirturalPeripheral.py [-c <FILENAME>] [-h|--help]
-h, --help           print this help
-c                   name of configuration file
-d                   name of data file
-i                   inertial GPS
"""

def printUsage():
    print HELP_STRING
    
def handleCommandSwitches():
    shortOpts = 'c:hd:i'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit(0)

    #Start with option defaults...
    configFile = ""
    dataFile = ""
    inertialGPS = False
    
    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
    if "-d" in options:
        dataFile = options["-d"]
        print "Data file specified at command line: %s" % dataFile
    if "-i" in options:
        inertialGPS = True
        print "Inertial GPS is specified"

    return (configFile, dataFile, inertialGPS)

if __name__ == "__main__":
    configFile, dataFile, inertialGPS = handleCommandSwitches()
    vp = VirturalPeripheral(configFile, dataFile, inertialGPS)
    vp.run()