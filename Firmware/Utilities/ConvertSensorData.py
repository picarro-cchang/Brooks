#!/usr/bin/python
#
# FILE:
#   ConvertSensorData.py
#
# DESCRIPTION:
#   Processes a sensor data stream file and writes out an H5 file suitable for viewing
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
    def __init__(self,argList):
        filters = Filters(complevel=1,fletcher32=True)
        if len(argList)>=1: 
            infileName = argList[0]
        if len(argList)>=2: 
            outfileName = argList[1]        
        self.h5f = openFile(outfileName,"w") 
        self.colDict = { "timestamp" : Int64Col() }
        for name in STREAM_MemberTypeDict.values():
            self.colDict[name[7:]] = Float32Col()
        TableType = type("TableType",(IsDescription,),self.colDict)
        filters = Filters(complevel=1,fletcher32=True)
        self.sensorTable = self.h5f.createTable(self.h5f.root,"sensors",TableType,filters=filters)
        
        self.sf = openFile(infileName,"r")
        self.streamFilterState = "COLLECTING_DATA"
        self.resultDict = {}
        self.latestDict = {}
        self.lastTime = 0
        self.numSens = 0

        
    def streamProcess(self,row):
        # This filter is designed to enqueue sensor entries which all have the same timestamp.
        #  A 3-ple consisting of the timestamp, a dictionary of sensor data at that time
        #  and a dictionary of the most current sensor data as of that time 
        #  is placed on the listener queue. The dictionary is keyed by the stream name 
        #  (e.g. STREAM_Laser1Temp gives the key "Laser1Temp" obtained by starting from the 7'th
        #  character in the stream index)
        #  A state machine is used to cache the first sample that occure at a new time and to 
        #  return the dictionary collected at the last time.
        self.latestDict[STREAM_MemberTypeDict[row['streamNum']][7:]] = row['value']
        
        if self.streamFilterState == "RETURNED_RESULT":
            self.lastTime = self.cachedResult.timestamp
            self.resultDict = {STREAM_MemberTypeDict[self.cachedResult.streamNum][7:] : self.cachedResult.value}
            
        if row['time'] != self.lastTime:
            self.cachedResult = SensorEntryType(row['time'],row['streamNum'],row['value'])
            self.streamFilterState = "RETURNED_RESULT"
            if self.resultDict:
                #print self.lastTime,self.resultDict.copy(),self.latestDict.copy()
                outRow = self.sensorTable.row
                outRow["timestamp"] = self.lastTime
                for name in self.latestDict:
                    outRow[name] = self.latestDict[name]
                outRow.append()
            else:
                return
        else:
            self.resultDict[STREAM_MemberTypeDict[row['streamNum']][7:]] = row['value']
            self.streamFilterState = "COLLECTING_DATA"
        
    def run(self):
        sensorTable = self.sf.root.sensors
        try:
            for row in sensorTable.iterrows():
                self.streamProcess(row)
        finally:
            self.sensorTable.flush()
            self.h5f.close()
            self.sf.close()
if __name__ == "__main__":
    e = SaveData(sys.argv[1:])
    e.run()
