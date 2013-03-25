#!/usr/bin/python
#
# FILE:
#   AdjustWlmOffset.py
#
# DESCRIPTION:
#   Utility to help adjust the WLM offset parameter by aligning a scheme point to the peak
#    of a spectral feature
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   14-Feb-2010  sze  Initial version.
#
#  Copyright (c) 2010 Picarro, Inc. All rights reserved
#
import sys
import getopt
import os
import time
import socket

from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes, SchemeProcessor
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("AdjustWlmOffset")

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

if __name__ == "__main__":
    while True:
        vLaserNum = raw_input("Virtual laser number? ")
        if not vLaserNum.strip(): break
        vLaserNum = int(vLaserNum)
        # Read the current WLM offset
        offset = RdFreqConv.getWlmOffset(vLaserNum)
        print "Current WLM offset is: %.4f" % offset
        # Stop current spectrum acquisition
        Driver.wrDasReg(SPECT_CNTRL_STATE_REGISTER,SPECT_CNTRL_IdleState)
        # We use two scheme indices to ping-pong between as the offset is changed
        schemeIndex = 0
        schemeFileName = raw_input("Scheme file to use? ")
        freqScheme = SchemeProcessor.Scheme(schemeFileName)
        while True:
            RdFreqConv.wrFreqScheme(schemeIndex,freqScheme)
            RdFreqConv.convertScheme(schemeIndex)
            RdFreqConv.uploadSchemeToDAS(schemeIndex)
            # Set up multiple mode so that scheme keeps running
            Driver.wrDasReg("SPECT_CNTRL_NEXT_SCHEME_REGISTER",schemeIndex)
            Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER","SPECT_CNTRL_SchemeMultipleMode")            
            # Start acquisition using the scheme
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_StartingState")
            #
            newOffset = raw_input("New WLM offset? ")
            if not newOffset.strip(): break
            newOffset = float(newOffset)
            Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER","SPECT_CNTRL_SchemeSingleMode")            
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_IdleState")
            time.sleep(1.0)
            RdFreqConv.setWlmOffset(vLaserNum,newOffset)
            schemeIndex = 1-schemeIndex
    writeBack = raw_input("Update warmbox calibration file %s? (y/N)" % RdFreqConv.getWarmBoxCalFilePath())
    if writeBack.strip()[:1] in ['y','Y']:
        RdFreqConv.updateWarmBoxCal()
        