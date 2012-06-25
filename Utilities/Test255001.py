#!/usr/bin/env python
#
# File Name: Test255001.py
# Purpose: Test program for checking how laser 1 temperature responds to a step in the setpoint
#
# Notes:
#
# File History:
# 2010-08-20 sze   Initial version

import sys
import getopt
import os
from Queue import Queue, Empty
import serial
import socket
import time

from tables import *
from numpy import *
from pylab import *
from TestUtilities import *
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.Listener import Listener
from Host.Common.timestamp import unixTime

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="MakeWlmFile1")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc

class LaserTemperatureSetpointStepTest(object):
    def __init__(self,tp):
        self.testParameters = tp
        self.hdfName = "data1.h5"
        self.h5 = openFile(tp.absoluteTestDirectory + self.hdfName,"w")
        self.graph1Name = "graph1.png"
        try:
            print "Driver version: %s" % Driver.allVersions()
        except:
            raise ValueError,"Cannot communicate with driver, aborting"

        # Define a queue for the sensor stream data
        self.queue = Queue(0)
        self.streamFilterState = "COLLECTING_DATA"
        self.resultDict = {}
        self.latestDict = {}
        self.lastTime = 0

    def flushQueue(self):
        while True:
            try:
                self.queue.get(False)
                continue
            except Empty:
                break
       
    def streamFilter(self,result):
        # This filter is designed to enqueue sensor entries which all have the same timestamp.
        #  A 3-ple consisting of the timestamp, a dictionary of sensor data at that time
        #  and a dictionary of the most current sensor data as of that time 
        #  is placed on the listener queue. The dictionary is keyed by the stream name 
        #  (e.g. STREAM_Laser1Temp gives the key "Laser1Temp" obtained by starting from the 7'th
        #  character in the stream index)
        #  A state machine is used to cache the first sample that occurs at a new time and to 
        #  return the dictionary collected at the last time.
        self.latestDict[STREAM_MemberTypeDict[result.streamNum][7:]] = result.value
        
        if self.streamFilterState == "RETURNED_RESULT":
            self.lastTime = self.cachedResult.timestamp
            self.resultDict = {STREAM_MemberTypeDict[self.cachedResult.streamNum][7:] : self.cachedResult.value}
            
        if result.timestamp != self.lastTime:
            self.cachedResult = SensorEntryType(result.timestamp,result.streamNum,result.value)
            self.streamFilterState = "RETURNED_RESULT"
            if self.resultDict:
                return self.lastTime,self.resultDict.copy(),self.latestDict.copy()
            else:
                return
        else:
            self.resultDict[STREAM_MemberTypeDict[result.streamNum][7:]] = result.value
            self.streamFilterState = "COLLECTING_DATA"

    def run(self):
        self.listener = Listener(self.queue,SharedTypes.BROADCAST_PORT_SENSORSTREAM,
                                 SensorEntryType,self.streamFilter)
        filters = Filters(complevel=1,fletcher32=True)
        try:
            regVault = Driver.saveRegValues(["LASER1_TEMP_CNTRL_STATE_REGISTER",
                                             "LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER",
                                             "LASER1_MANUAL_TEC_REGISTER"])
            dataList = []
            setPoint = 25.0
            stepSize = 2.0
            lockTol = 0.003
            stabilizeDuration = 30.0
            baselineDuration = 30.0
            stepDuration = 30.0
            DacStepSize = 1000
            DacStepDuration = 120.0
            Driver.wrDasReg("LASER1_TEMP_CNTRL_STATE_REGISTER","TEMP_CNTRL_EnabledState")
            Driver.wrDasReg("LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER",setPoint)
            print "Waiting for loop to stabilize before collecting data"
            self.flushQueue()
            tStart,d,last = self.queue.get()
            t = tStart
            while t-tStart < 1000*stabilizeDuration:
                t,d,last = self.queue.get()
                sys.stdout.write('.')
            print "\nRecording baseline data"
            while t-tStart < 1000*baselineDuration:
                if "Laser1Temp" in d and "Laser1Tec" in d:
                    print "%20.1f %20.3f %20.0f" % (0.001*(t-tStart),d["Laser1Temp"],d["Laser1Tec"])
                    dataList.append((t,0.001*(t-tStart),d["Laser1Temp"],d["Laser1Tec"]))
                t,d,last = self.queue.get()
            print "Applying step in temperature setpoint"
            Driver.wrDasReg("LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER",setPoint+stepSize)
            tStart = t
            tecVals = []
            while t-tStart < 1000*baselineDuration:
                if "Laser1Temp" in d and "Laser1Tec" in d:
                    print "%20.1f %20.3f %20.0f" % (0.001*(t-tStart),d["Laser1Temp"],d["Laser1Tec"])
                    dataList.append((t,0.001*(t-tStart),d["Laser1Temp"],d["Laser1Tec"]))
                    tecVals.append(d["Laser1Tec"])
                t,d,last = self.queue.get()
            tecMean = mean(tecVals[len(tecVals)//2:])
            print "Applying step in TEC drive"
            Driver.wrDasReg("LASER1_TEMP_CNTRL_STATE_REGISTER","TEMP_CNTRL_ManualState")
            Driver.wrDasReg("LASER1_MANUAL_TEC_REGISTER",int(tecMean+DacStepSize))
            tStart = t
            while t-tStart < 1000*DacStepDuration:
                if "Laser1Temp" in d and "Laser1Tec" in d:
                    print "%20.1f %20.3f %20.0f" % (0.001*(t-tStart),d["Laser1Temp"],d["Laser1Tec"])
                    dataList.append((t,0.001*(t-tStart),d["Laser1Temp"],d["Laser1Tec"]))
                t,d,last = self.queue.get()
        finally:
            self.listener.stop()
            Driver.restoreRegValues(regVault)
        
        #results = array(dataList,[('timestamp',int64),('TimeSinceStart',float32),('CavityPressure',float32)])
        #table = self.h5.createTable("/","results",results,title="Cavity Leak Test",filters=filters)
        #table.attrs.EngineName = tp.parameters["EngineName"]
        #table.attrs.DateTime = tp.parameters["DateTime"]
        #table.attrs.TestCode = tp.parameters["TestCode"]
        #table.attrs.Description = "Cavity pressure with valves closed"
        #table.attrs.TestDuration = testDuration
        self.h5.close()

if __name__ == "__main__":
  pname = sys.argv[0]
  bname = os.path.basename(pname)
  if len(sys.argv) < 2:
    engineName = raw_input("Engine name? ")
  else:
    engineName = sys.argv[1]
  assert bname[:4].upper() == "TEST", "Test program name %s is invalid (should start with Test)" % (bname,)
  tp = TestParameters(engineName,bname[4:10])
  tst = LaserTemperatureSetpointStepTest(tp)
  tst.run()
  tp.appendReport()
  # tp.makeHTML()
