#!/usr/bin/env python
import sys
import time
import threading
import traceback
from numpy import *
import Queue
from Host.Common import namedtuple

APP_NAME = "Peripheral Processor"

from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

class PeriphProcessor(object):
    def __init__(self, periphIntrf, dataLabels, outputPort, scriptPath, params):
        self.periphIntrf = periphIntrf
        self.dataLabels = dataLabels
        self.outputPort = outputPort
        self.params = params
        numChannels = len(dataLabels)
        sensorQSize = 100
        self.sensorList = []
        for p in range(numChannels):
            self.sensorList.append(Queue.Queue(sensorQSize))
        
        # Define the script environment and compile the script
        self.dataEnviron = {"SENSORLIST": self.sensorList, "WRITEOUTPUT": self.writeOutput, 
                            "PARAMS":self.params }
        sourceString = file(scriptPath,"r").read()
        if sys.platform != 'win32':
            sourceString = sourceString.replace("\r","")
        self.scriptCodeObj = compile(sourceString, scriptPath, "exec")
        print "Starting peripheral processor"
        self.startProcessThread()
                
    def appendData(self, port, ts, dataList):
        try:
            self.sensorList[port].put((ts, dict(zip(self.dataLabels[port], dataList))),block=False)
        except Exception, err:
            Log("Peripheral processor synchronization queue error: Check if some sensor is missing", Level=2, Verbose=traceback.format_exc())
        
    def writeOutput(self, ts, dataList):
        self.periphIntrf.appendAndSendOutData(self.outputPort, ts, dataList)

    def startProcessThread(self):
        appThread = threading.Thread(target = self.processData)
        appThread.setDaemon(True)
        appThread.start()
        
    def processData(self):
        exec self.scriptCodeObj in self.dataEnviron