#!/usr/bin/python
#
# FILE:
#   CheckOpticalSwitch.py
#
# DESCRIPTION:
#   Create laser calibration information by scanning laser temperature and reading wavemeter
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   5-Oct-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
import getopt
import os
from Queue import Queue, Empty
import serial
import socket
import time

from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

APP_NAME = "CheckSwitch"
EventManagerProxy_Init(APP_NAME)

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER,
                                    APP_NAME, IsDontCareConnection = False)

class Averager(object):
    # Averages non-None values added to it
    def __init__(self):
        self.total = 0
        self.count = 0
    def addValue(self,value):
        if value is not None:
            self.total += value
            self.count += 1
    def getAverage(self):
        if self.count != 0:
            return self.total/self.count
        else:
            raise ValueError,"No values to average"

class CheckSwitch(object):
    def __init__(self,outputFile,nLasers):
        self.nLasers = nLasers
        self.outputFile = outputFile
            
        # Define a queue for the sensor stream data
        self.queue = Queue(0)
        self.streamFilterState = "COLLECTING_DATA"
        self.resultDict = {}
        self.latestDict = {}
        self.lastTime = 0
        
        self.listener = Listener(self.queue,SharedTypes.BROADCAST_PORT_SENSORSTREAM,
                                 SensorEntryType,self.streamFilter)
                                 
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
        # Check that the driver can communicate
        try:
            print "Driver version: %s" % Driver.allVersions()
        except:
            raise ValueError,"Cannot communicate with driver, aborting"
    
        op = open(self.outputFile,"wb",0)
      
        while True:
            for i in range(self.nLasers):
                aLaserNum = i + 1
                Driver.selectActualLaser(aLaserNum)
                time.sleep(0.3)
                self.flushQueue()
                # Read the wavelength monitor data
                tStart,d,last = self.queue.get()
                t = tStart
                etalon1Avg = Averager()
                reference1Avg = Averager()
                etalon2Avg = Averager()
                reference2Avg = Averager()

                # Average the available information in the queue
                time.sleep(1)
                while True:
                    try:
                        t,d,last = self.queue.get(False)
                        etalon1Avg.addValue(d.get("Etalon1"))
                        reference1Avg.addValue(d.get("Reference1"))
                        etalon2Avg.addValue(d.get("Etalon2"))
                        reference2Avg.addValue(d.get("Reference2"))
                    except Empty:
                        if t-tStart < 1000: 
                            time.sleep(1)
                            continue
                        etalon1 = etalon1Avg.getAverage()
                        reference1 = reference1Avg.getAverage()
                        etalon2 = etalon2Avg.getAverage()
                        reference2 = reference2Avg.getAverage()
                        msg = "%9d %9.0f %9.0f %9.0f %9.0f" % (aLaserNum,etalon1,reference1,etalon2,reference2)
                        op.write("%s\n" % msg)
                        print msg
                        break

HELP_STRING = """CheckOpticalSwitch.py [-n<NUMBER_OF_LASERS>] [-o<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-n                   number of lasers
-o                   output file name (default: CheckOpticalSwitch.txt)
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hn:o:'
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
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    outputFile = "CheckOpticalSwitch.txt"
    if "-o" in options:
        outputFile = options["-o"]
    nLasers = 2
    if "-n" in options:
        nLasers = int(options["-n"])
    return outputFile, nLasers

if __name__ == "__main__":
    outputFile, nLasers = handleCommandSwitches()
    m = CheckSwitch(outputFile, nLasers)
    m.run()
