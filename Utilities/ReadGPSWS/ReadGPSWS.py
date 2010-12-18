"""
File Name: ReadGPSWS.py
Purpose:
    Report GPS and Weather Station data into Picarro analyzer

File History:
    12-17-10 Alex  Integrate this module into G2000 package

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

import sys
import serial
import time
import os.path
import threading
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_READ_GPSWS, RPC_PORT_MEAS_SYSTEM
from Host.Common.EventManagerProxy import *

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

APP_NAME = "ReadGPSWS"
APP_DESCRIPTION = "Read GPS and Weather Station data"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "ReadGPSWS.ini"

EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

class ReadGPSWS(object):
    def __init__(self, configFile):
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_READ_GPSWS),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True) 
        config = CustomConfigObj(configFile)
        self.enGPS = config.getboolean("Enable", "enableGPS", True)
        portGPS = config.get("Serial", "portGPS", "COM1")
        baudrateGPS = config.getint("Serial", "baudrateGPS", 19200)
        
        if self.enGPS:
            self.gps = serial.Serial(port=portGPS,baudrate=baudrateGPS,bytesize=8,parity="N",stopbits=1,timeout=0.05)
            self.gps.open()
            
        self.enWS = config.getboolean("Enable", "enableWS", True)
        portWS = config.get("Serial", "portWS", "COM2")
        baudrateWS = config.getint("Serial", "baudrateWS", 9600)
        if self.enWS:
            self.ws = serial.Serial(port=portWS,baudrate=baudrateWS,bytesize=8,parity="N",stopbits=1,timeout=0.05)
            self.ws.open()

        self.latitudeCenter = config.getfloat("Location", "latitudeCenter", 41.03166)
        self.longitudeCenter = config.getfloat("Location", "longitudeCenter", -109.63833)
        
        self.measSystemRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % (RPC_PORT_MEAS_SYSTEM,),ClientName="GPSWSSender")

    def read(self):
        try:
            while True:
                result = []
                if self.enGPS:
                    try:
                        lineGPS = self.gps.readline()
                        atomsGPS = lineGPS.split(",")
                        #print atomsGPS
                        if atomsGPS[0] == "$GPGGA":
                            result = ["%s:%s:%s UTC," % (atomsGPS[1][:2],atomsGPS[1][2:4],atomsGPS[1][4:6])]
                            result.append("%s %s %s," % (atomsGPS[2][:2],atomsGPS[2][2:],atomsGPS[3]))
                            result.append("%s %s %s," % (atomsGPS[4][:3],atomsGPS[4][3:],atomsGPS[5]))
                            result.append("%s" % atomsGPS[6])
                            timeSinceMidnight = 60*(60*int(atomsGPS[1][:2])+int(atomsGPS[1][2:4]))+int(atomsGPS[1][4:6])
                            degLat  = int(atomsGPS[2][:2]) if atomsGPS[3]=="N" else -int(atomsGPS[2][:2])
                            degLong = int(atomsGPS[4][:3]) if atomsGPS[5]=="E" else -int(atomsGPS[4][:3])
                            minLat  = float(atomsGPS[2][2:])
                            minLong = float(atomsGPS[4][3:])
                            degLat  += minLat/60.0  if atomsGPS[3]=="N" else -minLat/60.0
                            degLong += minLong/60.0 if atomsGPS[5]=="E" else -minLong/60.0
                            fit = int(atomsGPS[6])
                            self.measSystemRpc.Backdoor.SetData("GPS_TIME", timeSinceMidnight)
                            self.measSystemRpc.Backdoor.SetData("GPS_ABS_LAT", degLat)
                            self.measSystemRpc.Backdoor.SetData("GPS_REL_LAT", degLat-int(degLat))
                            self.measSystemRpc.Backdoor.SetData("GPS_ABS_LONG", degLong)
                            self.measSystemRpc.Backdoor.SetData("GPS_REL_LONG", degLong-int(degLong))
                            self.measSystemRpc.Backdoor.SetData("GPS_FIT", fit)
                    except Exception, errMsg:
                        pass
                        #print errMsg
                if self.enWS:
                    try:
                        lineWS = self.ws.readline()
                        atomsWS = lineWS.split(",")
                        result.append(", %s, %s, %s, %s, %s" % tuple(atomsWS[:5]))
                        self.measSystemRpc.Backdoor.SetData("WS_WIND_SPEED", float(atomsWS[0]))
                        self.measSystemRpc.Backdoor.SetData("WS_WIND_DIRECTION", int(atomsWS[1]))
                        self.measSystemRpc.Backdoor.SetData("WS_TEMP", float(atomsWS[2]))
                        self.measSystemRpc.Backdoor.SetData("WS_REL_HUMIDITY", float(atomsWS[3]))
                        self.measSystemRpc.Backdoor.SetData("WS_PRESSURE", float(atomsWS[4]))
                    except Exception, errMsg:
                        pass
                        #print errMsg
                # Combination
                print  " ".join(result)
                time.sleep(0.1)
        finally:
            if self.enGPS:
                self.gps.close()
            if self.enWS:
                self.ws.close()
            
    def runApp(self):
        rpcThread = threading.Thread(target = self.read)
        rpcThread.setDaemon(True)
        rpcThread.start()
        self.RpcServer.serve_forever()
        
HELP_STRING = \
""" readGps.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help.
-c                   Specify a config file.  Default = "./readGPSWS.ini"
"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt

    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)

    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if '-h' in options:
        PrintUsage()
        sys.exit()

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return (configFile)

def main():
    #Get and handle the command line options...
    configFile = HandleCommandSwitches()
    Log("%s application started." % APP_NAME)  
    try:
        rGPSWS = ReadGPSWS(configFile)
        rGPSWS.runApp()        
    except Exception, E:
        if DEBUG: raise
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))
  
if __name__ == "__main__":
    DEBUG = __debug__
    main()
    
