#!/usr/bin/env python
import socket
import os
import sys
import time
import Queue
import threading
import struct
from numpy import *
from collections import deque
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SharedTypes import TCP_PORT_PERIPH_INTRF

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

APP_NAME = "Peripheral Interface"
APP_DESCRIPTION = "Socket client and interpolator"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "serial2socket.ini"

MAX_SENSOR_QUEUE_SIZE = 2000
HOST = 'localhost'
NUM_CHANNELS = 4
     
def linInterp(pPair, tPair, t):
    try:
        dtime = tPair[1] - tPair[0]
        if dtime == 0:
            return 0.5*(pPair[0] + pPair[1])
        else:
            return ((t-tPair[0])*pPair[1] + (tPair[1]-t)*pPair[0]) / dtime
    except:
        return 0.0
        
class PeriphIntrf(object):
    def __init__(self, configFile):
        co = CustomConfigObj(configFile)
        iniAbsBasePath = os.path.split(os.path.abspath(configFile))[0]
        self.queue = Queue.Queue(0)
        self.sock = None
        self.getThread = None
        self.sensorList = []
        self.parser = []
        self.dataLabels = []
        for p in range(NUM_CHANNELS):
            self.sensorList.append(deque())
            paserFunc = co.get("PORT%d" % p, "SCRIPTFUNC").strip()
            scriptPath =  os.path.join(iniAbsBasePath, co.get("SETUP", "SCRIPTPATH"))
            scriptFilename = os.path.join(scriptPath, paserFunc) + ".py"
            exec compile(file(scriptFilename,"r").read().replace("\r",""),scriptFilename,"exec")
            self.parser.append(eval(paserFunc))
            labelList = [i.strip() for i in co.get("PORT%d" % p, "DATALABELS").split(",")]
            if labelList[0]:
                self.dataLabels.append(labelList)
            else:
                self.dataLabels.append([])
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
                    #sys.stdout.write('\n')
                    # Store in sensorList
                    self.sensorLock.acquire()
                    try:
                        parsedList = self.parser[port](newStr)
                        if parsedList:
                            self.sensorList[port].append((ts, parsedList))
                            if len(self.sensorList[port]) > MAX_SENSOR_QUEUE_SIZE:
                                self.sensorList[port].popleft()
                    except Exception, err:
                        print "%r" % (err,)
                    finally:
                        self.sensorLock.release()
                    state = "SYNC1"

    def startSocketThread(self):
        appThread = threading.Thread(target = self.getFromSocket)
        appThread.setDaemon(True)
        appThread.start()
        
    def startStateMachineThread(self):
        appThread = threading.Thread(target = self.sensorStateMachine)
        appThread.setDaemon(True)
        appThread.start()
         
    def selectAllDataByTime(self, requestTime):
        sensorDataList = [[[], []]]*NUM_CHANNELS
        self.sensorLock.acquire()
        localSensorList = self.sensorList[:]
        self.sensorLock.release()
        try:
            for port in range(NUM_CHANNELS):
                for idx in range(len(localSensorList[port])):
                    (ts, valList) = localSensorList[port][idx]
                    if len(valList) > 0 and ts >= requestTime:
                        # Save a list of [[time0, time1], [(val00, val01), (val10, val11), (val20, val21), ...]]
                        if idx > 0:
                            lastVal = localSensorList[port][idx-1]
                            sensorDataList[port] = [[lastVal[0], ts], zip(lastVal[1], valList)]
                        else:
                            sensorDataList[port] = [[ts, ts], zip(valList, valList)]
                        break
        except Exception, err:
            print "%r" % (err,)
        return sensorDataList
        
    def getDataByTime(self, requestTime, dataList):
        sensorDataList = self.selectAllDataByTime(requestTime)
        interpDict = {}
        for port in range(NUM_CHANNELS):
            timeDataLists = sensorDataList[port]
            for dataIdx in range(len(timeDataLists[1])):
                interpDict[self.dataLabels[port][dataIdx]] = linInterp(timeDataLists[1][dataIdx], timeDataLists[0], requestTime)
        retList = []
        for data in dataList:
            try:
                retList.append(interpDict[data])
            except:
                retList.append(0.0)
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
    configFile = HandleCommandSwitches()
    p = PeriphIntrf(configFile)
