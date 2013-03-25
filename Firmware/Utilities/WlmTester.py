#!/usr/bin/python
"""
 FILE:
   WlmTester.py

 DESCRIPTION:
   Utility to measure effect of temperature cycling on wavelength monitor. The PZT is held in a fixed location
   and the cavity is held at a constant pressure near atmospheric. The laser frequency is scanned by directing 
   the tuner voltage to the fine laser current, and ringdowns are collected. These should be spaced at the cavity
   FSR, so the wavelength monitor ratios recorded at the ringdown times correspond to these equally-spaced frequencies.
   By cycling the warm box temperature and tracking how the ratios change, we can see if there is drift in the monitor.
   
   i)  Laser locker special mode is needed to direct tuner to the fine laser current
   ii) PZT voltage should be held fixed by entering "laser current tuning" mode
   iii) Tuner ramp window and sweep need to be adjusted so ringdowns can occur over the full range of fine current
   iv)  Ramp slopes should be equal
   iv) The backoff and WLM averaging should be set to 1
   v)  Ringdowns should be allowed on both slopes of the tuner
   vi) Spectrum manager should be placed in continuous mode to start acquisition without a scheme
   vii) Disable dither mode and laser locking

 SEE ALSO:
   Specify any related information.

 HISTORY:
   19-Mar-2010  sze  Initial version.

  Copyright (c) 2010 Picarro, Inc. All rights reserved
"""
import sys
import getopt
import os
import time
import types
import pickle
import socket

from configobj import ConfigObj
from numpy import *
import pylab
import Host.autogen.interface as interface
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("WlmTester")

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="WlmTester")
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
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="WlmTester")
            self.initialized = True

# For convenience in calling driver and frequency converter functions
Driver = DriverProxy().rpc
RdFreqConv = RdFreqConvProxy().rpc

def _value(valueOrName):
    """Convert valueOrName into an value, raising an exception if the name is not found"""
    if isinstance(valueOrName,types.StringType):
        try:
            valueOrName = getattr(interface,valueOrName)
        except AttributeError:
            raise AttributeError("Value identifier not recognized %r" % valueOrName)
    return valueOrName

def changeBitsFPGA(base,reg,lsb,width,value):
    lsb, width, value = _value(lsb), _value(width), _value(value)
    mask = ((1<<width)-1) << lsb
    current = Driver.rdFPGA(base,reg)
    Driver.wrFPGA(base,reg,(current & ~mask)|((value << lsb) & mask))

def setAutomaticControl():
    "Puts laser current control into automatic mode"
    Driver.wrDasReg("LASER1_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_AutomaticState")
    Driver.wrDasReg("LASER2_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_AutomaticState")
    Driver.wrDasReg("LASER3_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_AutomaticState")
    Driver.wrDasReg("LASER4_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_AutomaticState")
    changeBitsFPGA("FPGA_INJECT","INJECT_CONTROL","INJECT_CONTROL_MODE_B","INJECT_CONTROL_MODE_W",1)

def setManualControl():
    "Puts laser current control into manual mode"
    data.asInt = LASER_CURRENT_CNTRL_ManualState;
    Driver.wrDasReg("LASER1_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
    Driver.wrDasReg("LASER2_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
    Driver.wrDasReg("LASER3_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
    Driver.wrDasReg("LASER4_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
    
def selectLaser(aLaserNum):
    changeBitsFPGA("FPGA_INJECT","INJECT_CONTROL","INJECT_CONTROL_LASER_SELECT_B","INJECT_CONTROL_LASER_SELECT_W",aLaserNum-1)

if __name__ == "__main__":
    try:
        regVault = Driver.saveRegValues(["VIRTUAL_LASER_REGISTER",
                                         "TUNER_SWEEP_RAMP_HIGH_REGISTER",
                                         "TUNER_SWEEP_RAMP_LOW_REGISTER",
                                         "TUNER_WINDOW_RAMP_HIGH_REGISTER",
                                         "TUNER_WINDOW_RAMP_LOW_REGISTER",
                                         "SPECT_CNTRL_MODE_REGISTER",
                                         "ANALYZER_TUNING_MODE_REGISTER",
                                         "RDFITTER_META_BACKOFF_REGISTER",
                                         "RDFITTER_META_SAMPLES_REGISTER",
                                         "PZT_OFFSET_VIRTUAL_LASER1",
                                         "PZT_OFFSET_VIRTUAL_LASER2",
                                         "PZT_OFFSET_VIRTUAL_LASER3",
                                         "PZT_OFFSET_VIRTUAL_LASER4",
                                         "PZT_OFFSET_VIRTUAL_LASER5",
                                         "PZT_OFFSET_VIRTUAL_LASER6",
                                         "PZT_OFFSET_VIRTUAL_LASER7",
                                         "PZT_OFFSET_VIRTUAL_LASER8",
                                         ("FPGA_LASERLOCKER","LASERLOCKER_OPTIONS"),
                                         ("FPGA_TWGEN","TWGEN_SLOPE_DOWN"),
                                         ("FPGA_TWGEN","TWGEN_SLOPE_UP"),        
                                         ("FPGA_RDMAN","RDMAN_OPTIONS"),
                                         ("FPGA_RDMAN","RDMAN_TIMEOUT_DURATION"),
                                        ])
        # Stop any acquisition
        Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_IdleState")
        changeBitsFPGA("FPGA_RDMAN","RDMAN_CONTROL","RDMAN_CONTROL_RESET_RDMAN_B","RDMAN_CONTROL_RESET_RDMAN_W",1)
        vLaserNum = int(raw_input("Virtual laser number? "))
        Driver.wrDasReg("VIRTUAL_LASER_REGISTER",vLaserNum-1)
        laserParams = Driver.rdVirtualLaserParams(vLaserNum)
        aLaserNum = laserParams['actualLaser'] + 1
        ratio1Center, ratio1Scale = laserParams['ratio1Center'], laserParams['ratio1Scale']
        ratio2Center, ratio2Scale = laserParams['ratio2Center'], laserParams['ratio2Scale']
        phase = laserParams['phase']
        # Enable ringdowns on both slopes
        changeBitsFPGA("FPGA_RDMAN","RDMAN_OPTIONS","RDMAN_OPTIONS_UP_SLOPE_ENABLE_B","RDMAN_OPTIONS_UP_SLOPE_ENABLE_W",1)
        changeBitsFPGA("FPGA_RDMAN","RDMAN_OPTIONS","RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B","RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_W",1)
        # Set up tuner window limits
        Driver.wrDasReg("TUNER_WINDOW_RAMP_HIGH_REGISTER",49000)
        Driver.wrDasReg("TUNER_WINDOW_RAMP_LOW_REGISTER",21000)
        # Set up tuner sweep limits
        Driver.wrDasReg("TUNER_SWEEP_RAMP_HIGH_REGISTER",50000)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_LOW_REGISTER",20000)
        # Set up tuner slopes
        Driver.wrFPGA("FPGA_TWGEN","TWGEN_SLOPE_DOWN",1000)
        Driver.wrFPGA("FPGA_TWGEN","TWGEN_SLOPE_UP",1000)
        # Disable laser locking 
        changeBitsFPGA("FPGA_RDMAN","RDMAN_OPTIONS","RDMAN_OPTIONS_LOCK_ENABLE_B","RDMAN_OPTIONS_LOCK_ENABLE_W",0)
        # Disable dither mode
        changeBitsFPGA("FPGA_RDMAN","RDMAN_OPTIONS","RDMAN_OPTIONS_DITHER_ENABLE_B","RDMAN_OPTIONS_DITHER_ENABLE_W",0)
        # Select laser current tuning
        Driver.wrDasReg("ANALYZER_TUNING_MODE_REGISTER","ANALYZER_TUNING_LaserCurrentTuningMode")
        # Set up metadata averaging interval
        Driver.wrDasReg("RDFITTER_META_BACKOFF_REGISTER",1)
        Driver.wrDasReg("RDFITTER_META_SAMPLES_REGISTER",1)
        # Set ringdown timeout duration to one second
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_TIMEOUT_DURATION",1000000)
        # Send tuner signal to laser fine current
        changeBitsFPGA("FPGA_LASERLOCKER","LASERLOCKER_OPTIONS","LASERLOCKER_OPTIONS_DIRECT_TUNE_B","LASERLOCKER_OPTIONS_DIRECT_TUNE_W",1)
        # Center the cavity PZT
        Driver.wrDasReg("PZT_OFFSET_VIRTUAL_LASER%d" % vLaserNum,32768)
        # Enable continuous mode
        Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER","SPECT_CNTRL_ContinuousMode")
        # Select laser
        selectLaser(aLaserNum)
        # Start acquisition
        Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_StartingState")
        # Consider setting up constant cavity pressure and warm box temperature cycling here
        raw_input("<Return> to end test")
    finally:
        Driver.restoreRegValues(regVault)
