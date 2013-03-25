"""
File Name: GlobalHawk.py
Purpose: This is responsible for network communications with the NASA Global Hawk Aircraft

File History:
    11-09-05 sze   Initial release
    
Copyright (c) 2011 Picarro, Inc. All rights reserved
"""

APP_NAME = "Global Hawk"
APP_DESCRIPTION = "Communication with Global Hawk Aircraft Network"
__version__ = 1.0

import asynchat
import asyncore
import datetime
import getopt
import os
from Queue import Queue
import socket
import sys
import time
import types

from Host.autogen import interface
from Host.Common.configobj import ConfigObj
from Host.Common import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.SharedTypes import Singleton, BROADCAST_PORT_DATA_MANAGER, BROADCAST_PORT_SENSORSTREAM
from Host.Common.StringPickler import ArbitraryObject
from Host.Common.timestamp import getTimestamp, timestampToUtcDatetime

EventManagerProxy_Init(APP_NAME)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
    
class TcpServer(asyncore.dispatcher):
    """Receives connections and establishes handlers for each client.
    """
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        self.handler = None
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(address)
        self.address = self.socket.getsockname()
        self.listen(1)
        return
    def handle_accept(self):
        # Called when a client connects to our socket
        client_info = self.accept()
        if self.handler is None or self.handler.closed:
            self.handler = TcpHandler(sock=client_info[0])
        else:
            GoAwayHandler(sock=client_info[0])
    def handle_close(self):
        self.close()
        return
        
class UdpServer(asynchat.async_chat):
    def __init__(self,address):
        asynchat.async_chat.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(address)
        self.set_terminator('\n')
        self.buffer = []
    def collect_incoming_data(self,data):
        self.buffer.append(data)
    def found_terminator(self):
        print "UDP: %s" % "".join(self.buffer)
        self.buffer = []
    def handle_connect(self):
        pass
                
class GoAwayHandler(asynchat.async_chat):
    """Tell client to go away and close the connection"""
    def __init__(self,sock):
        asynchat.async_chat.__init__(self,sock)
        self.set_terminator('\n')
        self.push("Server busy with existing TCP connection\r\n")
        self.close_when_done()
    def collect_incoming_data(self,data):
        return
    def found_terminator(self):
        return
    
class TcpHandler(asynchat.async_chat):
    """Handles processing data from a single client.
    """
    def __init__(self,sock):
        asynchat.async_chat.__init__(self,sock)
        self.set_terminator('\n')
        self.push("Connected to Picarro TCP server\r\n")
        self.closed = False
        self.buffer = []
    def collect_incoming_data(self,data):
        self.buffer.append(data)
    def found_terminator(self):
        print "TCP: %s" % "".join(self.buffer)
        self.buffer = []
    def handle_close(self):
        self.closed = True
        self.close()        

def format(fmtList,v):
    for t,f in fmtList:
        if isinstance(v,t): 
            try:
                return f % (v,)
            except TypeError:
                return f
    return '%s' % (v,)

class GlobalHawk(Singleton):
    initialized = False
    def __init__(self, configPath=None):        
        if not self.initialized:
            if configPath != None:
                # Read from .ini file
                cp = ConfigObj(configPath)
                basePath = os.path.split(configPath)[0]
                self.statusHost, self.statusPort = cp['ADDRESSES']['STATUS'].split(':')
                self.statusPort = int(self.statusPort)
                self.statusSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                self.id = cp['INSTRUMENT_STATUS']['ID']
                self.sensorQueue = Queue(512)
                self.sensorListener = Listener.Listener(self.sensorQueue,
                                                        BROADCAST_PORT_SENSORSTREAM,
                                                        interface.SensorEntryType,
                                                        retry = True,
                                                        name = "GlobalHawk listener")
                self.dmQueue = Queue(512)
                self.dmListener = Listener.Listener(self.dmQueue,
                                                    BROADCAST_PORT_DATA_MANAGER,
                                                    ArbitraryObject,
                                                    retry = True,
                                                    name = "GlobalHawk listener")
                self.currentSensors = []
            else:
                raise ValueError("Configuration file must be specified to initialize GlobalHawk network interface")
        Log('GlobalHawk initialized',Data=dict(statusIP='%s:%d'%(self.statusHost,self.statusPort)))

    def sendStatus(self,data):
        self.statusSocket.sendto(data,(self.statusHost,self.statusPort))
        
    # Get data from sensor queue until some timestamp (from any stream) exceeds reportTime. 
    # If the queue becomes empty before this happens, return None
    # Otherwise, report latest values of sensor streams specified in streamIndices as a 
    #  list of the same length as streamIndices. This is a COPY of currentSensors so we can
    #  safely update currentSensors
    
    def setSensorStreams(self,streamIndices):
        # Specify list of stream indices that we wish to have reported
        self.streamIndices = streamIndices
        self.currentSensors = len(streamIndices)*[None]
        
    def getSensorData(self,reportTime):
        # Get all the data in the sensor queue up to reportTime and return all the current sensor
        #  values at that time. If the data in the sensor queue are all before reportTime, return None
        d = None
        try:
            while not self.sensorQueue.empty():
                d = self.sensorQueue.get()
                if d.timestamp>reportTime:
                    return self.currentSensors[:]   # Make a copy, since currentSensors is dynamically updated
                if d.streamNum in self.streamIndices:
                    self.currentSensors[self.streamIndices.index(d.streamNum)] = d.value
            return None
        finally:
            if d is not None:
                if d.streamNum in self.streamIndices:
                    self.currentSensors[self.streamIndices.index(d.streamNum)] = d.value
        
    def run(self):
        TcpServer(('localhost', 80000))
        UdpServer(('localhost', 80001))
        SENSOR_REPORT_PERIOD = 5000
        count = 0
        # TODO: For actual code, set up startTs from actual time, rather than from timestamp in the file
        # startTs = getTimestamp()
        d = self.sensorQueue.get()
        startTs = d.timestamp
        nextReport = SENSOR_REPORT_PERIOD*((startTs + SENSOR_REPORT_PERIOD)//SENSOR_REPORT_PERIOD)
        self.setSensorStreams([interface.STREAM_AmbientPressure,
                               interface.STREAM_CavityPressure,
                               interface.STREAM_CavityTemp,
                               interface.STREAM_WarmBoxTemp,
                               interface.STREAM_DasTemp,
                               interface.STREAM_InletValve,
                               interface.STREAM_OutletValve,
                               interface.STREAM_HotBoxTec,
                               interface.STREAM_WarmBoxTec,
                               interface.STREAM_Laser1Temp,
                               interface.STREAM_Laser2Temp,
                               interface.STREAM_Laser3Temp,
                               interface.STREAM_Laser4Temp])
        reportData = ['AmbientPressure','cavity_pressure','cavity_temperature',
                      'WarmBoxTemp','DasTemp','InletValve','CH4','CO2','H2O',
                      'wlm1_offset','wlm2_offset','wlm3_offset']
        formatList = [(int,'%d'),(float,'%.5f'),(types.NoneType,'')]
        
        while True:
            asyncore.loop(timeout=0.1,count=1)
            # Get data available on the data manager queue
            if not self.dmQueue.empty():
                status_fields = [self.id]
                d = self.dmQueue.get()
                ts, mode, source = d['data']['timestamp'], d['mode'], d['source']
                if source == 'analyze_CFADS': 
                    tsAsString = timestampToUtcDatetime(ts).strftime('%Y%m%dT%H%M%S') + '.%03d' % (ts % 1000,)
                    status_fields.append(tsAsString)
                    status_fields.append('DATA')
                    dd = d['data']
                    status_fields += [format(formatList,dd.get(v,None)) for v in reportData]
                    data = ','.join(status_fields)
                    self.sendStatus('%s\r\n' % data)
                    continue
            sensors = self.getSensorData(nextReport)
            if sensors is not None:
                # We have sensor data that was current as of nextReport
                status_fields = [self.id]
                tsAsString = timestampToUtcDatetime(nextReport).strftime('%Y%m%dT%H%M%S') + '.%03d' % (ts % 1000,)
                status_fields.append(tsAsString)
                status_fields.append('SENSORS')
                status_fields += [format(formatList,v) for v in sensors]
                data = ','.join(status_fields)
                self.sendStatus('%s\r\n' % data)
                nextReport += SENSOR_REPORT_PERIOD
        
HELP_STRING = """GlobalHawk.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./GlobalHawk.ini"
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
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
    configFile = os.path.splitext(AppPath)[0] + ".ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile, options

if __name__ == "__main__":
    configFile, options = handleCommandSwitches()
    app = GlobalHawk(configFile)
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    app.run()
    Log("Exiting program")
