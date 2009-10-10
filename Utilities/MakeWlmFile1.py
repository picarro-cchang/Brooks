#!/usr/bin/python
#
# FILE:
#   MakeWlmFile1.py
#
# DESCRIPTION:
#   Create laser and wavelength monitor calibration information by scanning laser temperature
#    and reading wavemeter and wavelength monitor
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

from BurleighReply import BurleighReply
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("MakeWlmFile1")

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

class WlmFileMaker(object):
    def __init__(self,configFile,options):
        self.config = ConfigObj(configFile)
        if "-l" in options:
            self.laserNum = int(options["-l"])
        else:
            self.laserNum = int(self.config["SETTINGS"]["LASER"])
        if self.laserNum<=0 or self.laserNum>MAX_LASERS:
            raise ValueError("LASER must be in range 1..4")

        if "-f" in options:
            fname = options["-f"]
        else:
            fname = self.config["SETTINGS"]["FILENAME"]
        self.fname = fname.strip() + ".wlm"
        self.fp = file(self.fname,"w")

        if "-w" in options:
            self.waitTime = int(options["-w"])
        else:
            self.waitTime = float(self.config["SETTINGS"]["WAIT_TIME"])
        if self.waitTime < 0:
            raise ValueError("Negative WAIT_TIME is invalid")

        if "-i" in options:
            self.coarseCurrent = int(options["-i"])
        else:
            self.coarseCurrent = float(self.config["SETTINGS"]["LASER_CURRENT"])
        if self.coarseCurrent < 0 or self.coarseCurrent >= 65536:
            raise ValueError("LASER_CURRENT must be in range 0..65535")
        
        if "--min" in options:
            self.tempMin = float(options["--min"])
        else:
            self.tempMin = float(self.config["SETTINGS"]["TEMP_MIN"])
        if self.tempMin < 3.0 or self.tempMin >= 55.0:
            raise ValueError("TEMP_MIN must be in range 3.0 to 55.0")

        if "--max" in options:
            self.tempMax = float(options["--max"])
        else:
            self.tempMax = float(self.config["SETTINGS"]["TEMP_MAX"])
        if self.tempMax < 3.0 or self.tempMax > 55.0:
            raise ValueError("TEMP_MAX must be in range 3.0 to 55.0")

        if "--step" in options:
            self.tempStep = float(options["--step"])
        else:
            self.tempStep = float(self.config["SETTINGS"]["TEMP_STEP"])
        if self.tempStep < 0.01 or self.tempStep > 10.0:
            raise ValueError("TEMP_STEP must be in range 0.01 to 10.0")

        if "--tol" in options:
            self.tempTol = float(options["--tol"])
        else:
            self.tempTol = float(self.config["SETTINGS"]["TEMP_TOLERANCE"])
        if self.tempTol < 0.001 or self.tempTol > 0.1:
            raise ValueError("TEMP_TOLERANCE must be in range 0.001 to 0.1")
        
        # Define a queue for the sensor stream data
        self.queue = Queue(0)
        self.streamFilterState = "COLLECTING_DATA"
        self.resultDict = {}
        self.latestDict = {}
        self.lastTime = 0
        
        self.listener = Listener(self.queue,SharedTypes.BROADCAST_PORT_SENSORSTREAM,
                                 SensorEntryType,self.streamFilter)
        
        # Open serial port to Burleigh for non-blocking read
        try:
            self.ser = serial.Serial(0,19200,timeout=0)
            self.wavemeter = BurleighReply(self.ser,0.02)
        except:
            raise Exception("Cannot open serial port - aborting")
        self.serialTimeout = 10.0

    def WaitForString(self,timeout,msg=""):
        tWait = 0
        while tWait < timeout:
            reply = self.wavemeter.GetString()
            if reply != "":
                # print "Reply >%s<" % (list(reply),)
                return reply
            time.sleep(0.5)
            tWait += 0.5
        else:
            raise IOError(msg)

    def readWavenumber(self):
        while True:
            self.ser.write("READ:SCAL:FREQ?\n");
            reply = self.WaitForString(self.serialTimeout,"Timeout waiting for response to READ command")
            try:
            # N.B. Sunnyvale Burleigh reads out frequencies in THz
                waveno = float(reply)/0.0299792458
                return waveno
            except:
                pass # Try again
        
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

        print "Asking wavemeter for identification"
        self.ser.write("\n*IDN?\n");
        reply = self.WaitForString(self.serialTimeout,"Timeout waiting for response to *IDN?")
        print "Wavemeter id: %s" % reply

        try:
            regVault = Driver.saveRegValues(["LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % self.laserNum,
                                             "LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % self.laserNum,
                                             "LASER%d_MANUAL_FINE_CURRENT_REGISTER" % self.laserNum,
                                             ("FPGA_INJECT","INJECT_CONTROL")])

            if self.waitTime > 0:
                print "Waiting for %.1f minutes" % self.waitTime
                time.sleep(60.0*self.waitTime)
                
            self.fp.write("[CRDS Header]\n")
            self.fp.write("FileType=Wavelength Monitor Calibration\n")
            self.fp.write("Filename=%s\n" % self.fname)
            self.fp.write(time.strftime("Date=%Y%m%d\n",time.localtime()))
            self.fp.write(time.strftime("Time=%H%M%S\n",time.localtime()))
            self.fp.write("\n[Parameters]\n")

            # Set up laser current and select the laser
            Driver.wrDasReg("LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % self.laserNum, self.coarseCurrent)
            Driver.wrDasReg("LASER%d_MANUAL_FINE_CURRENT_REGISTER" % self.laserNum, 32768)
            Driver.selectActualLaser(self.laserNum)
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % self.laserNum,self.tempMin)
            
            print "Turning off laser, and ensuring no spectrum acquisition is active"
            Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % self.laserNum,LASER_CURRENT_CNTRL_DisabledState)
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_IdleState)
            # TO DO: Turn off SOA as well
            time.sleep(2.0)
            
            tDuration = 15
            print "Measuring WLM offsets for %.1f seconds" % tDuration
            etalon1Avg = Averager()
            reference1Avg = Averager()
            etalon2Avg = Averager()
            reference2Avg = Averager()
            
            self.flushQueue()
            tStart,d,last = self.queue.get()
            t = tStart
            ticker = tStart
            while t < tStart + tDuration*1000:
                if t > ticker + 1000:
                    sys.stderr.write(".")
                    ticker += 1000
                # Note: get returns none if the key is not in the dictionary
                etalon1Avg.addValue(d.get("Etalon1"))
                reference1Avg.addValue(d.get("Reference1"))
                etalon2Avg.addValue(d.get("Etalon2"))
                reference2Avg.addValue(d.get("Reference2"))
                t,d,last = self.queue.get()
            print

            etalon1_offset = etalon1Avg.getAverage()
            reference1_offset = reference1Avg.getAverage()
            etalon2_offset = etalon2Avg.getAverage()
            reference2_offset = reference2Avg.getAverage()
            
            # Write out offset information to file
            self.fp.write("laser_current=%.2f\n" % self.coarseCurrent)
            self.fp.write("etalon1_offset=%.2f\n" % etalon1_offset)
            self.fp.write("reference1_offset=%.2f\n" % reference1_offset)
            self.fp.write("etalon2_offset=%.2f\n" % etalon2_offset)
            self.fp.write("reference2_offset=%.2f\n" % reference2_offset)

            print "WLM offsets: %.2f, %.2f, %.2f, %.2f" %  \
                  (etalon1_offset,reference1_offset,etalon2_offset,reference2_offset)

            tDuration = 20
            print "Turning on laser and waiting for %.1f seconds for stabilization" % tDuration
            Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % self.laserNum,LASER_CURRENT_CNTRL_ManualState)
            self.flushQueue()
            tStart,d,last = self.queue.get()
            t = tStart
            ticker = tStart
            while t < tStart + tDuration*1000:
                if t > ticker + 1000:
                    sys.stderr.write(".")
                    ticker += 1000
                t,d,last = self.queue.get()
            print
            
            self.fp.write("\n[Data column names]\n")
            self.fp.write("0=Laser temperature\n")
            self.fp.write("1=Wavenumber\n")
            self.fp.write("2=Wavelength ratio 1\n")
            self.fp.write("3=Wavelength ratio 2\n")
            self.fp.write("4=Etalon temperature\n")
            self.fp.write("5=Etalon 1 (offset removed)\n")
            self.fp.write("6=Reference 1 (offset removed)\n")
            self.fp.write("7=Etalon 2 (offset removed)\n")
            self.fp.write("8=Reference 2 (offset removed)\n")
            self.fp.write("9=Points averaged\n")
            self.fp.write("\n[Data]\n")

            self.tempScan = self.tempMin
            print "Scanning laser temperature from %.3f to %.3f" % (self.tempMin,self.tempMax)
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % self.laserNum,TEMP_CNTRL_EnabledState)
            
            while self.tempScan <= self.tempMax:
                Driver.wrDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % self.laserNum,self.tempScan)
                # Wait for laser temperature to stabilize
                tWait = 3.5
                self.flushQueue()
                tStart,d,last = self.queue.get()
                t = tStart
                while t < tStart + tWait or abs(last["Laser%dTemp" % self.laserNum]-self.tempScan) > self.tempTol:
                    t,d,last = self.queue.get()

                # Read wavemeter twice, first read is to flush any information from before
                #  the temperature stabilized
                waveno = self.readWavenumber()
                waveno = self.readWavenumber()
                
                # Read the wavelength monitor data
                tStart,d,last = self.queue.get()
                t = tStart
                ratio1Avg = Averager()
                ratio2Avg = Averager()
                laserTempAvg = Averager()
                etalonTempAvg = Averager()
                etalon1Avg = Averager()
                reference1Avg = Averager()
                etalon2Avg = Averager()
                reference2Avg = Averager()
                nRatios1 = 0
                nRatios2 = 0

                # Average the available information in the queue

                while True:
                    try:
                        t,d,last = self.queue.get(False)
                        etalon1Avg.addValue(d.get("Etalon1"))
                        reference1Avg.addValue(d.get("Reference1"))
                        etalon2Avg.addValue(d.get("Etalon2"))
                        reference2Avg.addValue(d.get("Reference2"))
                        try:
                            ratio1Avg.addValue((d["Etalon1"]-etalon1_offset)/(d["Reference1"]-reference1_offset))
                            nRatios1 += 1
                        except IndexError:
                            pass
                        try:
                            ratio2Avg.addValue((d["Etalon2"]-etalon2_offset)/(d["Reference2"]-reference2_offset))
                            nRatios2 += 1
                        except IndexError:
                            pass
                        laserTempAvg.addValue(d.get("Laser%dTemp" % self.laserNum))
                        etalonTempAvg.addValue(last.get("EtalonTemp"))
                    except Empty:
                        if t-tStart < 1000: continue
                        ratio1 = ratio1Avg.getAverage()
                        ratio2 = ratio2Avg.getAverage()
                        laserTemp = laserTempAvg.getAverage()
                        etalonTemp = etalonTempAvg.getAverage()
                        nRatios = min(nRatios1,nRatios2)
                        etalon1 = etalon1Avg.getAverage()-etalon1_offset
                        reference1 = reference1Avg.getAverage()-reference1_offset
                        etalon2 = etalon2Avg.getAverage()-etalon2_offset
                        reference2 = reference2Avg.getAverage()-reference2_offset
                        
                        msg = "%9.3f %12.5f %9.5f %9.5f %9.3f %9.2f %9.2f %9.2f %9.2f %3d" % \
                          (laserTemp,waveno,ratio1,ratio2,etalonTemp,etalon1,reference1,etalon2,reference2,nRatios)
                        self.fp.write("%s\n" % msg)
                        print msg
                        break
                self.tempScan += self.tempStep
            print "Calibration done, result is in file: %s" % self.fname
            
        finally:
            if self.fp:
                self.fp.close()
            Driver.restoreRegValues(regVault)
            Driver.startEngine()

HELP_STRING = """MakeWlmFile1.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./MakeWlmFile1.ini"
-f                   name of output file (without extension)
-i                   coarse laser current (digitizer units)
-l                   laser number (1-index)
--max                maximum laser temperature
--min                minimum laser temperature
--step               laser temperature step
--tol                laser temperature tolerance
-w                   wait time (in minutes)
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:i:l:f:w:'
    longOpts = ["help","min=","max=","step=","tol="]
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
    m = WlmFileMaker(configFile, options)
    m.run()
