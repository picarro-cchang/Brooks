#!/usr/bin/python
#
# FILE:
#   FindWlmOffset.py
#
# DESCRIPTION:
#   Utility to help find the WLM offset parameter by moving a spectral peak to the
#  specified frequency
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   30-Mar-2010  sze  Initial version.
#
#  Copyright (c) 2010 Picarro, Inc. All rights reserved
#
import sys
import getopt
from configobj import ConfigObj
# import matplotlib.pyplot as mp
import numpy as np
import os
import cPickle
import socket
import struct
import time
import Queue
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.StringPickler import StringAsObject, ObjAsString
from Host.Common.WlmCalUtilities import WlmFile
from Host.Common.ctypesConvert import ctypesToDict, dictToCtypes
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.Listener import Listener

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("FindWlmOffset")

WMAX_TOLERANCE = 1e-5

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
            
class RdFreqConvProxy(SharedTypes.Singleton):
    """Encapsulates access to the ringdown frequency converter via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_FREQ_CONVERTER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="MakeWlmFile1")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc
RdFreqConv = RdFreqConvProxy().rpc

class WlmOffsetFinder(object):
    def __init__(self,configFile,options):
        self.config = ConfigObj(configFile)
        # Analyze options
        if "-v" in options:
            self.vLaserNum = int(options["-v"])
        else:
            self.vLaserNum = int(self.config["SETTINGS"]["VIRTUAL_LASER"])
        if self.vLaserNum < 1 or self.vLaserNum > NUM_VIRTUAL_LASERS:
            raise ValueError("VIRTUAL_LASER must be in range 1..%d" % NUM_VIRTUAL_LASERS)
        if "-w" in options:
            self.waveNumberCen = float(options["-w"])
        else:
            self.waveNumberCen = float(self.config["SETTINGS"]["CENTER_WAVENUMBER"])
        if "-a" in options:
            self.autoMode = True
        else:
            self.autoMode = False
        if "-t" in options:
            self.wMaxTol = float(options["-t"])
        else:
            self.wMaxTol = WMAX_TOLERANCE
            
        self.rdQueue = Queue.Queue(0)
        
    def run(self):
        # Define listener for the ringdown data
        self.rdListener = Listener(self.rdQueue,SharedTypes.BROADCAST_PORT_RD_RECALC,ProcessedRingdownEntryType,retry=True)
        # Stop current spectrum acquisition
        Driver.wrDasReg(SPECT_CNTRL_STATE_REGISTER,SPECT_CNTRL_IdleState)
        # Create a fine scheme centered about the specified peak
        sch = SharedTypes.Scheme()
        sch.nrepeat = 1
        scan = np.linspace(self.waveNumberCen-0.05,self.waveNumberCen+0.05,501)
        sch.setpoint = np.concatenate((scan,scan[-2:0:-1]))
        sch.dwell = np.ones(sch.setpoint.shape)
        sch.subschemeId = np.zeros(sch.setpoint.shape)
        sch.virtualLaser = (self.vLaserNum-1)*np.ones(sch.setpoint.shape)
        sch.threshold = np.zeros(sch.setpoint.shape)
        sch.pztSetpoint = np.zeros(sch.setpoint.shape)
        sch.laserTemp = np.zeros(sch.setpoint.shape)
        sch.numEntries = len(sch.setpoint)
        # We use two scheme indices to ping-pong between as the offset is changed
        schemeIndex = 0
        while True:
            # Read the current WLM offset
            offset = RdFreqConv.getWlmOffset(self.vLaserNum)
            print "Current WLM offset is: %.6f" % offset
            RdFreqConv.wrFreqScheme(schemeIndex,sch)
            RdFreqConv.convertScheme(schemeIndex)
            RdFreqConv.uploadSchemeToDAS(schemeIndex)
            # Set up single mode for the scheme
            Driver.wrDasReg("SPECT_CNTRL_NEXT_SCHEME_REGISTER",schemeIndex)
            Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER","SPECT_CNTRL_SchemeSingleMode")            
            # Start acquisition using the scheme
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_StartingState")
            # Wait until the spectrum has been collected
            while Driver.rdDasReg("SPECT_CNTRL_STATE_REGISTER") != SPECT_CNTRL_IdleState:
                sys.stdout.write(".")
                time.sleep(1.0)
            print "\nProcessing ringdowns"
            waveNumber = []
            loss = []
            while self.rdQueue.qsize() > 0:
                entry = self.rdQueue.get()
                waveNumber.append(entry.waveNumber)
                loss.append(entry.uncorrectedAbsorbance)
            #
            # Find the top 5% of loss points and fit them with a parabola
            thresh = 0.9
            sortedLoss = sorted(loss)
            loss = np.array(loss)
            waveNumber = np.array(waveNumber)
            thresh = sortedLoss[int(thresh*len(sortedLoss))]
            window = (loss >= thresh) & (abs(waveNumber-self.waveNumberCen) < 0.05)
            q = np.polyfit(waveNumber[window],loss[window],2)
            #print "Good points", sum(window)
            #mp.plot(waveNumber,np.polyval(q,waveNumber),waveNumber,loss,'.')
            #mp.show()
            wMax = -0.5*q[1]/q[0]
            print "Peak position: %.6f" % wMax
            if self.autoMode:
                if abs(self.waveNumberCen - wMax) < self.wMaxTol: break
            else:
                done = raw_input("Done? [N] ")
                if done.strip()[:1] in ['y','Y']: break
            offset = offset-wMax+self.waveNumberCen
            Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER","SPECT_CNTRL_SchemeSingleMode")            
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_IdleState")
            time.sleep(1.0)
            RdFreqConv.setWlmOffset(self.vLaserNum,offset)
            schemeIndex = 1-schemeIndex
        if self.autoMode:
            RdFreqConv.updateWarmBoxCal()
        else:
            writeBack = raw_input("Update warmbox calibration file %s? (y/N)" % RdFreqConv.getWarmBoxCalFilePath())
            if writeBack.strip()[:1] in ['y','Y']:
                RdFreqConv.updateWarmBoxCal()

HELP_STRING = """findWlmOffset.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./findWlmOffset.ini"
-v                   specify virtual laser (1-origin) to calibrate
-w                   center wavenumber of spectral line
-a                   auto mode - automatically stops when the difference between target and new peak wavenumbers 
                     is within the tolerance, and writes back the warmbox calibration file
-t                   peak wavenumber tolerance used in the auto mode
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hac:v:w:t:'
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
    m = WlmOffsetFinder(configFile, options)
    m.run()
        