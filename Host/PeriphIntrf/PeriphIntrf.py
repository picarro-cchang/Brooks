#!/usr/bin/env python
import socket
import os
import sys
import time
import Queue
import threading
import struct
import traceback
from numpy import *
from collections import deque

from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SharedTypes import TCP_PORT_PERIPH_INTRF
from Host.Common.timestamp import getTimestamp, unixTime
from Host.Common.MeasData import MeasData
from Host.Common.Broadcaster import Broadcaster

import Errors
from PeriphProcessor import PeriphProcessor


#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): # we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

APP_NAME = "Peripheral Interface"
APP_DESCRIPTION = "Socket client and interpolator"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "serial2socket.ini"

DEFAULT_SENSOR_QUEUE_SIZE = 2000
HOST = 'localhost'

from Host.Common.EventManagerProxy import *
from Host.PeriphIntrf.Interpolators import Interpolators

EventManagerProxy_Init(APP_NAME)

        
class PeriphIntrf(object):
    
    INTERPOLATORS = {
        'linear'    : Interpolators.linear,
        'max'       : Interpolators.max,
        'bitwiseOr' : Interpolators.bitwiseOr
    }

    def __init__(self, configFile, dmBroadcaster):
        co = CustomConfigObj(configFile)
        iniAbsBasePath = os.path.split(os.path.abspath(configFile))[0]
        self.DataBroadcaster = dmBroadcaster
        self.sensorQSize = co.getint("SETUP", "SENSORQUEUESIZE", DEFAULT_SENSOR_QUEUE_SIZE)
        self.queue = Queue.Queue(0)
        self.sock = None
        self.getThread = None
        self.sensorList = []
        self.parserFuncCode = []
        self.dataLabels = []
        self.dataInterpolators = []
        self.parsers = []
        self.scriptFilenames = []
        self.offsets = []
        self.numChannels = len([s for s in co.list_sections() if s.startswith("PORT")])
        self.lastTimestamps = {}
        self.outputDict = {}
        self.parserVersion = None
        for p in range(self.numChannels):
            self.outputDict[p] = None
            self.sensorList.append(deque())
            parserFunc = co.get("PORT%d" % p, "SCRIPTFUNC").strip()
            scriptPath =  os.path.join(iniAbsBasePath, co.get("SETUP", "SCRIPTPATH"))
            scriptFilename = os.path.join(scriptPath, parserFunc) + ".py"
            self.scriptFilenames.append(scriptFilename)
            if parserFunc.startswith("parse"):
                scriptCodeObj = compile(file(scriptFilename,"r").read().replace("\r",""),scriptFilename,"exec")
                try:
                    exec scriptCodeObj in globals()
                    if not self.parserVersion:
                        self.parserVersion = PARSER_VERSION
                    if self.parserVersion > 0.0:
                        self.parserFuncCode.append(scriptCodeObj)
                    else:
                        self.parserFuncCode.append(eval(parserFunc))
                except:
                    self.parserFuncCode.append(eval(parserFunc))
            else:
                self.parserFuncCode.append(None)
            if not self.parserVersion:
                self.parserVersion = 0.0
            print "Peripheral Interface parser version number: ", self.parserVersion
            
            labelList = [i.strip() for i in co.get("PORT%d" % p, "DATALABELS").split(",")]
            if labelList[0]:
                self.dataLabels.append(labelList)
            else:
                self.dataLabels.append([])

            # Load interpolator mappings
            interpList = [i.strip() for i in co.get("PORT%d" % p, "INTERPOLATORS").split(',')]
            if len(interpList) != len(labelList):
                raise Errors.InterpolationListIncomplete("The # of interpolators (%s) does not match the # of "
                                                         "data labels (%s)" % (len(interpList), len(labelList)))

            interps = {}
            for i, interp in enumerate(interpList):
                if interp not in PeriphIntrf.INTERPOLATORS:
                    raise Errors.InterpolationTypeUnknown("Data label '%s' has an unknown interpolation type "
                                                          "'%s'." % (labelList[i], interp))
                interps[labelList[i]] = interp

            self.dataInterpolators.append(interps)

            self.parsers.append(parserFunc)
            self.offsets.append(co.getfloat("PORT%d" % p, "OFFSET", 0.0))
            
        # Set up the peripheral processor
        try:
            self.procInputPorts = [int(p) for p in co.get("PROCESSOR", "INPUTPORTS").split(",") if p.strip()]
            procOutputPort = co.getint("PROCESSOR", "OUTPUTPORT")
            procParams = dict(co["PROCESSOR"])
            procLabels = [self.dataLabels[i] for i in self.procInputPorts]
            scriptPath = self.scriptFilenames[procOutputPort]
            self.periphProcessor = PeriphProcessor(self, procLabels, procOutputPort, scriptPath, procParams)
        except Exception:
            print traceback.format_exc()
            self.procInputPorts = []
            self.periphProcessor = None
        
        self.sensorLock = threading.Lock()
        self._shutdownRequested = False
        self.connect()
        self.startSocketThread()
        self.startStateMachineThread()
    
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, TCP_PORT_PERIPH_INTRF))
        except socket.error, msg:
            sys.stderr.write("[ERROR] %s\n" % msg[1])
            raise
            
    def getFromSocket(self):
        try:
            while not self._shutdownRequested:
                data = self.sock.recv(1024)
                if len(data)>0:
                    for c in data: 
                        self.queue.put(c)
                else:
                    time.sleep(0.01)
        finally:
            self.sock.close()

    def sensorStateMachine(self):
        state = "SYNC1"
        value = 0
        counter = 0
        while not self._shutdownRequested:
            try:
                c = self.queue.get(timeout=1.0)
            except Queue.Empty:
                continue
            if state == "SYNC1":
                if ord(c) == 0x5A: state = "SYNC2"
            elif state == "SYNC2":
                if ord(c) == 0xA5: 
                    value, counter, maxcount = 0, 0, 8
                    state = "TIMESTAMP"
                else:
                    state = "SYNC1"
            elif state == "TIMESTAMP":
                value += ord(c)<<(8*counter)
                counter += 1
                if counter == maxcount:
                    ts = value
                    state = "PORT"
            elif state == "PORT":
                port = ord(c)
                value, counter, maxcount = 0, 0, 2
                state = "BYTECOUNT"
            elif state == "BYTECOUNT":
                value += ord(c)<<(8*counter)
                counter += 1
                if counter == maxcount:
                    #print ts, port, value
                    counter, maxcount = 0, value
                    newStr = ""
                    state = "DATA"
            elif state == "DATA":
                newStr += c
                if c not in ['\r','\n']: 
                    pass
                    #sys.stdout.write(c)
                counter += 1
                if counter >= maxcount:
                    try:
                        if self.parserVersion > 0.0:
                            dataEnviron = {"_OUTPUT_" : self.outputDict[port], "_RAWSTRING_": newStr}
                            exec self.parserFuncCode[port] in dataEnviron
                            self.outputDict[port] = dataEnviron["_OUTPUT_"]
                            parsedList = dataEnviron["_OUTPUT_"]
                        else:
                            # Make it backward compatibility
                            parsedList = self.parserFuncCode[port](newStr)

                        self.lastTimestamps[port] = ts
                        if parsedList:
                            self.appendAndSendOutData(port,ts,parsedList)
                            if port in self.procInputPorts and self.periphProcessor:
                                self.periphProcessor.appendData(self.procInputPorts.index(port),ts,parsedList)
                    except Exception, err:
                        print traceback.format_exc()
                        print "%r" % (err,)
                    state = "SYNC1"

    def appendAndSendOutData(self,port,ts,parsedList):
        self.sensorLock.acquire()
        try:
            self.sensorList[port].append((ts, parsedList))
            if len(self.sensorList[port]) > self.sensorQSize:
                self.sensorList[port].popleft()
                                
            measGood = True
            reportDict = dict(zip(self.dataLabels[port],parsedList))
            measData = MeasData(self.parsers[port], unixTime(ts), reportDict, measGood, port)
            self.DataBroadcaster.send(measData.dumps())
        except Exception, err:
            print traceback.format_exc()
            print "%r" % (err,)
        finally:
            self.sensorLock.release()
                        
    def startSocketThread(self):
        appThread = threading.Thread(target = self.getFromSocket)
        appThread.setDaemon(True)
        appThread.start()
        
    def startStateMachineThread(self):
        appThread = threading.Thread(target = self.sensorStateMachine)
        appThread.setDaemon(True)
        appThread.start()
         
    def selectAllDataByTime(self, requestTime):
        sensorDataList = []
        for i in range(self.numChannels):
            sensorDataList.append([[], []])
        self.sensorLock.acquire()
        try:
            for port in range(self.numChannels):
                # Obtain data from which we can linearly interpolate the data at requestTime
                # Ideally we get two time stamps which bracket the requested time. If this is
                #  not possible because the requested time is outside the range stored in a deque,
                #  the closest point available is returned
                ts, savedTs = None, None
                valList, savedValList = None, None
                for (tsRaw, valList) in reversed(self.sensorList[port]):
                    # Apply the offset (in seconds) to the timestamp (in milliseconds) recorded for 
                    #  these data to compensate for the time taken for the sample to enter the cavity 
                    #  and be probed by the light.
                    # A negative offset for a port means that there the gas concentration is measured
                    #  AFTER the data are measured at the peripheral port. Since "requestTime" is the
                    #  timestamp of the ringdowns, we need to interpolate into the pripheral data at
                    #  requestTime + 1000*offset, This is equivalent to changing the raw peripheral
                    #  timestamp by subtracting 1000*offset.
                    ts = tsRaw - 1000.0*self.offsets[port]
                    if len(valList) == 0: break
                    if ts < requestTime:
                        if savedTs is None:
                            sensorDataList[port] = [[ts,ts],zip(valList,valList)]
                        else:
                            sensorDataList[port] = [[ts,savedTs],zip(valList,savedValList)]
                        break
                    else:
                        savedTs = ts
                        savedValList = valList
                else:
                    if ts is not None: sensorDataList[port] = [[ts,ts],zip(valList,valList)]
        except Exception, err:
            print traceback.format_exc()
            print "%r" % (err,)
        self.sensorLock.release()
        return sensorDataList
        
    def getDataByTime(self, requestTime, dataList):
        sensorDataList = self.selectAllDataByTime(requestTime)
        interpDict = {}

        for port in range(self.numChannels):
            timeDataLists = sensorDataList[port]

            for dataIdx in range(len(timeDataLists[1])):
                dataLabel = self.dataLabels[port][dataIdx]
                assert dataLabel in dataList
                interpType = self.dataInterpolators[port][dataLabel]

                interpDict[dataLabel] = PeriphIntrf.INTERPOLATORS[interpType](timeDataLists[1][dataIdx],
                                                                              timeDataLists[0], requestTime)

        retList = []
        for data in dataList:
            try:
                retList.append(interpDict[data])
            except:
                retList.append(None)
        return retList
        
    def shutdown(self):
        self._shutdownRequested = True

HELP_STRING = \
"""

PeriphIntrf.py [-h] [-c <FILENAME>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.

"""

def PrintUsage():
    print HELP_STRING
    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:", ["help"])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
  
    return configFile
    
if __name__ == "__main__":
    from pylab import *
    from numpy import *
    configFile = HandleCommandSwitches()
    p = PeriphIntrf(configFile)
    while True:
        ts = getTimestamp()
        tVals = ts - arange(0.0,10000.0,57)
        r = [p.getDataByTime(t,["FOO1"])[0] for t in tVals]
        #if not(None in r):
        #    plot(tVals-tVals[0],r,'x')
        #    show()
        time.sleep(1.0)
