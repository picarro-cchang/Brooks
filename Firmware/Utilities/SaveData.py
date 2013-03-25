#!/usr/bin/python
#
# FILE:
#   SaveRawRD.py
#
# DESCRIPTION:
#   Listen to the sensor queue and RD results queue and write them to an HDF5 file
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   15-Oct-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
from tables import *
from ctypes import *
from numpy import *
import os
import Queue
import time
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.timestamp import unixTime
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("SaveData")

ctype2coltype = { c_byte:Int8Col, c_uint:UInt32Col, c_int:Int32Col, 
                  c_short:Int16Col, c_ushort:UInt16Col, c_longlong:Int64Col, 
                  c_float:Float32Col, c_double:Float64Col }

class SaveData(object):
    def __init__(self):
        filters = Filters(complevel=1,fletcher32=True)
        self.h5f = openFile("test.h5","w")
        self.rdQueue = Queue.Queue()
        self.sensorQueue = Queue.Queue()
        self.colDict = { }
        for name,cls in ProcessedRingdownEntryType._fields_:
            self.colDict[name] = (ctype2coltype[cls])()
        TableType = type("TableType",(IsDescription,),self.colDict)
        self.rdTable = self.h5f.createTable(self.h5f.root,"ringdowns",TableType,filters=filters)
 
        self.colDict = { "timestamp" : Int64Col() }
        for name in STREAM_MemberTypeDict.values():
            self.colDict[name[7:]] = Float32Col()
        TableType = type("TableType",(IsDescription,),self.colDict)
        filters = Filters(complevel=1,fletcher32=True)
        self.sensorTable = self.h5f.createTable(self.h5f.root,"sensors",TableType,filters=filters)
        
        self.numRd = 0
        self.streamFilterState = "COLLECTING_DATA"
        self.resultDict = {}
        self.latestDict = {}
        self.lastTime = 0
        self.numSens = 0
        # Define listeners for the ringdown and sensor data
        self.rdListener = Listener(self.rdQueue,SharedTypes.BROADCAST_PORT_RD_RECALC,ProcessedRingdownEntryType,retry=True)
        self.sensorListener = Listener(self.sensorQueue,SharedTypes.BROADCAST_PORT_SENSORSTREAM,SensorEntryType,self.streamFilter)
        
    def streamFilter(self,result):
        # This filter is designed to enqueue sensor entries which all have the same timestamp.
        #  A 3-ple consisting of the timestamp, a dictionary of sensor data at that time
        #  and a dictionary of the most current sensor data as of that time 
        #  is placed on the listener queue. The dictionary is keyed by the stream name 
        #  (e.g. STREAM_Laser1Temp gives the key "Laser1Temp" obtained by starting from the 7'th
        #  character in the stream index)
        #  A state machine is used to cache the first sample that occure at a new time and to 
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
        try:
            while True:
                while True:
                    try:
                        entry = self.rdQueue.get(block=False,timeout=0.5)
                        row = self.rdTable.row
                        for name,cls in ProcessedRingdownEntryType._fields_:
                            row[name] = getattr(entry,name)
                        self.numRd += 1
                        row.append()
                        if self.numRd % 200 == 0: sys.stdout.write("^")
                    except Queue.Empty:
                        break
                while True:
                    try:
                        timestamp,result,latest = self.sensorQueue.get(block=False,timeout=0.5)
                        row = self.sensorTable.row
                        row["timestamp"] = timestamp
                        for name in latest:
                            row[name] = latest[name]
                        self.numSens += 1
                        row.append()
                        if self.numSens % 25 == 0: sys.stdout.write(".")
                    except Queue.Empty:
                        break
                
        finally:
            self.rdTable.flush()
            self.sensorTable.flush()
            self.h5f.close()
            
if __name__ == "__main__":
    e = SaveData()
    e.run()
