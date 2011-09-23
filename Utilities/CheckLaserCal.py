#!/usr/bin/python
#
# FILE:
#   CheckLaserCal.py
#
# DESCRIPTION:
#   Checks the laser calibration using the specified .wlm file and determines
#    the new coarse laser current setting needed to best match the wavelength 
#    monitor vs laser temperature data.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   31-Jul-2011  sze  Initial version
#
#  Copyright (c) 2011 Picarro, Inc. All rights reserved
#
import sys
import getopt
from numpy import *
import os
import socket
import traceback
from Queue import Queue, Empty
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.WlmCalUtilities import AutoCal, WlmFile

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("CheckLaserCal")

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

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="CalibrateSystem")
            self.initialized = True

class RDFreqConvProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_FREQ_CONVERTER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="Controller")
            self.initialized = True

# For convenience in calling driver and frequency converter functions
Driver = DriverProxy().rpc
RDFreqConv = RDFreqConvProxy().rpc

class CheckLaserCal(object):
    def __init__(self,options):
        self.aLaserNum = int(options['-a'])
        if self.aLaserNum<=0 or self.aLaserNum>MAX_LASERS:
            raise ValueError("Laser number must be in range 1..%d." % (MAX_LASERS,))
        self.wlmFilename = options['-f']
        if not os.path.exists(self.wlmFilename):
            raise ValueError("WLM calibration file %s does not exist." % (self.wlmFilename,))
        if "-w" in options:
            self.waitTime = float(options["-w"])
            if self.waitTime < 0:
                raise ValueError("Negative WAIT_TIME is invalid.")

        # Define a queue for the sensor stream data
        self.queue = Queue(0)
        self.streamFilterState = "COLLECTING_DATA"
        self.resultDict = {}
        self.latestDict = {}
        self.waitTime = 0.0
        self.lastTime = 0
        self.tempTol = 0.01
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
        # Make up an AutoCal object from the .wlm file
        w = WlmFile(file(self.wlmFilename,"r"))
        a = AutoCal()
        a.loadFromWlmFile(w)
        try:
            regVault = Driver.saveRegValues(["LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % self.aLaserNum,
                                             "LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % self.aLaserNum,
                                             "LASER%d_MANUAL_FINE_CURRENT_REGISTER" % self.aLaserNum,
                                             ("FPGA_INJECT","INJECT_CONTROL")])
            if self.waitTime > 0:
                print "Waiting for %.1f minutes" % self.waitTime
                time.sleep(60.0*self.waitTime)
            
            self.coarseCurrent = float(w.parameters['laser_current'])
            # Set up laser current and select the laser
            Driver.wrDasReg("LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % self.aLaserNum, self.coarseCurrent)
            Driver.wrDasReg("LASER%d_MANUAL_FINE_CURRENT_REGISTER" % self.aLaserNum, 32768)
            Driver.selectActualLaser(self.aLaserNum)
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % self.aLaserNum,TEMP_CNTRL_EnabledState)
        
            for i in range(len(w.TLaser)):
                self.tempScan = w.TLaser[i]
                Driver.wrDasReg("LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % self.aLaserNum, self.coarseCurrent)
                print "Setting laser temperature to %.3f" % (self.tempScan,)
                Driver.wrDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % self.aLaserNum,self.tempScan)
                # Wait for laser temperature to stabilize
                tWait = 3.5
                self.flushQueue()
                tStart,d,last = self.queue.get()
                t = tStart
                while t < tStart + tWait or abs(last["Laser%dTemp" % self.aLaserNum]-self.tempScan) > self.tempTol:
                    t,d,last = self.queue.get()
                    
                print "Laser temperature is now %.3f" % (last["Laser%dTemp" % self.aLaserNum],)
                tStart,d,last = self.queue.get()
                t = tStart
                ratio1Avg = Averager()
                ratio2Avg = Averager()
                laserTempAvg = Averager()
                etalonTempAvg = Averager()
                # Average the information in the queue for at least one second
                while True:
                    try:
                        t,d,last = self.queue.get(False)
                        ratio1Avg.addValue(d.get("Ratio1"))
                        ratio2Avg.addValue(d.get("Ratio2"))
                        laserTempAvg.addValue(d.get("Laser%dTemp" % self.aLaserNum))
                        etalonTempAvg.addValue(last.get("EtalonTemp"))
                    except Empty:
                        if t-tStart < 1000: continue
                        ratio1 = ratio1Avg.getAverage()
                        ratio2 = ratio2Avg.getAverage()
                        laserTemp = laserTempAvg.getAverage()
                        etalonTemp = etalonTempAvg.getAverage()
                        break
                    except:
                        print traceback.format_exc()
                ratio1 = ratio1/32768.0
                ratio2 = ratio2/32768.0
                # Calculate the ratios based on quantities in the .wlm file. We may need to calculate
                #  these differently for different types of wavelength monitor
                ratio1_ref = w.Ratio1[i]
                ratio2_ref = w.Ratio2[i]
                #
                var1 = a.ratio1Scale*(ratio2-a.ratio2Center) - a.ratio2Scale*(ratio1-a.ratio1Center)*sin(a.wlmPhase)
                var2 = a.ratio2Scale*(ratio1-a.ratio1Center)*cos(a.wlmPhase)
                theta = arctan2(var1,var2)
                
                var1 = a.ratio1Scale*(ratio2_ref-a.ratio2Center) - a.ratio2Scale*(ratio1_ref-a.ratio1Center)*sin(a.wlmPhase)
                var2 = a.ratio2Scale*(ratio1_ref-a.ratio1Center)*cos(a.wlmPhase)
                theta_ref = arctan2(var1,var2)
                
                theta_diff = theta-theta_ref
                if theta_diff > pi: theta_diff -= 2*pi
                if theta_diff <= -pi: theta_diff += 2*pi
                
                print laserTemp, etalonTemp, self.coarseCurrent, theta_diff                        
                self.coarseCurrent += 500.0*theta_diff
                
            print a.ratio1Center
            print a.ratio2Center
            print a.ratio1Scale
            print a.ratio2Scale
            print a.wlmPhase
            print a.tEtalonCal
            print a.wlmTempSensitivity

            print w.TLaser
            print w.Ratio1
            print w.Ratio2
            print w.TEtalon
        finally:
            Driver.restoreRegValues(regVault)
            Driver.startEngine()
        
HELP_STRING = """CheckLaserCal.py [-a <laserNum>] [-w <wlmFilename>] [-h|--help]
Checks the current laser calibration against that in the specified .wlm file and
determines the coarse laser current required to make the temperature vs wavelength
monitor ratios correspond most closely to those in the file.

Where the options specify:

-h, --help           print this help
-a                   actual laser number (1-origin) to check
-f                   name of .wlm file containing integration data for the laser
-w                   (optional) wait time in minutes before starting
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hf:w:a:'
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
    return options

if __name__ == "__main__":
    options = handleCommandSwitches()
    c = CheckLaserCal(options)
    c.run()
