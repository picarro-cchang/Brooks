#!/usr/bin/python
#
# FILE:
#   ViewLaserLocking.py
#
# DESCRIPTION:
#   Utility to display how laser locks to a setpoint
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   1-Jun-2011  sze  Initial version.
#
#  Copyright (c) 2010 Picarro, Inc. All rights reserved
#
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
    Driver.wrDasReg("LASER1_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
    Driver.wrDasReg("LASER2_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
    Driver.wrDasReg("LASER3_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
    Driver.wrDasReg("LASER4_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")

def selectLaser(aLaserNum):
    changeBitsFPGA("FPGA_INJECT","INJECT_CONTROL","INJECT_CONTROL_LASER_SELECT_B","INJECT_CONTROL_LASER_SELECT_W",aLaserNum-1)

if __name__ == "__main__":
    try:
        regVault = Driver.saveRegValues(["VIRTUAL_LASER_REGISTER",
                                        ("FPGA_RDMAN","RDMAN_OPTIONS"),
                                        ("FPGA_RDMAN","RDMAN_TIMEOUT_DURATION"),
                                        ("FPGA_RDMAN","RDMAN_PRECONTROL_DURATION"),
                                        ("FPGA_LASERLOCKER","LASERLOCKER_CS"),
                                        ("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_MULTIPLIER"),
                                        ("FPGA_LASERLOCKER","LASERLOCKER_RATIO2_MULTIPLIER"),
                                        ("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_CENTER"),
                                        ("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_CENTER"),
                                        "SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER",
                                        ])
        # Stop any acquisition
        Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_IdleState")
        changeBitsFPGA("FPGA_RDMAN","RDMAN_CONTROL","RDMAN_CONTROL_RESET_RDMAN_B","RDMAN_CONTROL_RESET_RDMAN_W",1)
        vLaserNum = int(raw_input("Virtual laser number? "))
        laserParams = Driver.rdVirtualLaserParams(vLaserNum)
        aLaserNum = laserParams['actualLaser'] + 1
        ratio1Center, ratio1Scale = laserParams['ratio1Center'], laserParams['ratio1Scale']
        ratio2Center, ratio2Scale = laserParams['ratio2Center'], laserParams['ratio2Scale']
        phase = laserParams['phase']
        # Disable laser locking
        changeBitsFPGA("FPGA_RDMAN","RDMAN_OPTIONS","RDMAN_OPTIONS_LOCK_ENABLE_B","RDMAN_OPTIONS_LOCK_ENABLE_W",0)
        # Disable ringdowns on both slopes
        changeBitsFPGA("FPGA_RDMAN","RDMAN_OPTIONS","RDMAN_OPTIONS_UP_SLOPE_ENABLE_B","RDMAN_OPTIONS_UP_SLOPE_ENABLE_W",0)
        changeBitsFPGA("FPGA_RDMAN","RDMAN_OPTIONS","RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B","RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_W",0)
        # Set precontrol duration and ringdown timeout to 6ms
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_PRECONTROL_DURATION",50)
        # Set ringdown timeout duration to one second
        Driver.wrDasReg("SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER",1000000)
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_TIMEOUT_DURATION",1000000)
        selectLaser(aLaserNum)
        setAutomaticControl()
        # Disable PRBS generation
        changeBitsFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS","LASERLOCKER_CS_PRBS_B","LASERLOCKER_CS_PRBS_W",0)
        status = Driver.rdFPGA("FPGA_RDMAN","RDMAN_STATUS")
        print "Initial RD manager status: 0x%x" % status
        # Tell RDMAN to collect data
        changeBitsFPGA("FPGA_RDMAN","RDMAN_CONTROL","RDMAN_CONTROL_START_RD_B","RDMAN_CONTROL_START_RD_W",1)
        time.sleep(1.2)
        status = Driver.rdFPGA("FPGA_RDMAN","RDMAN_STATUS")
        print "Final RD manager status: 0x%x" % status
        bank = (status & (1<<RDMAN_STATUS_BANK_B)) == (1<<RDMAN_STATUS_BANK_B)
        # Get acquired data for analysis
        if bank:
            data,meta,param = Driver.rdRingdown(1)
        else:
            data,meta,param = Driver.rdRingdown(0)
        ratio1 = mean(meta[0,256:]/32768.0)    
        ratio2 = mean(meta[1,256:]/32768.0)    
        setManualControl()
        # Convert WLM ratios into angles
        X = ratio1 - ratio1Center
        Y = ratio2 - ratio2Center
        theta = arctan2(
          ratio1Scale * Y - ratio2Scale * X * sin(phase),
          ratio2Scale * X * cos(phase))
        print "In steady-state: Ratio1 = %.3f, Ratio2 = %.3f, WlmAngle = %.3f" % (ratio1,ratio2,theta)
        # Set up the laser locking parameters to target the mean angle
        ratio1Multiplier = (-sin(theta + phase))/(ratio1Scale * cos(phase))
        ratio2Multiplier = cos(theta)/(ratio2Scale * cos(phase))
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_MULTIPLIER",int(ratio1Multiplier*32767.0))
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_RATIO2_MULTIPLIER",int(ratio2Multiplier*32767.0))
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_CENTER",int(ratio1Center*32768.0))
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_RATIO2_CENTER",int(ratio2Center*32768.0))
        # Set precontrol duration and ringdown timeout
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_PRECONTROL_DURATION",500)
        # Set ringdown timeout duration to one second
        Driver.wrDasReg("SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER",5110)
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_TIMEOUT_DURATION",5110)
        # Enable laser locking
        changeBitsFPGA("FPGA_RDMAN","RDMAN_OPTIONS","RDMAN_OPTIONS_LOCK_ENABLE_B","RDMAN_OPTIONS_LOCK_ENABLE_W",1)
        # Disable PRBS generation
        changeBitsFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS","LASERLOCKER_CS_PRBS_B","LASERLOCKER_CS_PRBS_W",0)
        status = Driver.rdFPGA("FPGA_RDMAN","RDMAN_STATUS")
        time.sleep(2.0)
        setAutomaticControl()
        print "Initial RD manager status: 0x%x" % status
        # Tell RDMAN to collect data
        changeBitsFPGA("FPGA_RDMAN","RDMAN_CONTROL","RDMAN_CONTROL_START_RD_B","RDMAN_CONTROL_START_RD_W",1)
        time.sleep(1.2)
        status = Driver.rdFPGA("FPGA_RDMAN","RDMAN_STATUS")
        print "Final RD manager status: 0x%x" % status
        bank = (status & (1<<RDMAN_STATUS_BANK_B)) == (1<<RDMAN_STATUS_BANK_B)
        # Get acquired data for analysis
        if bank:
            data,meta,param = Driver.rdRingdown(1)
        else:
            data,meta,param = Driver.rdRingdown(0)
        setManualControl()
        ratio1 = mean(meta[0,256:]/32768.0)    
        ratio2 = mean(meta[1,256:]/32768.0)    
    finally:
        Driver.restoreRegValues(regVault)
    # Plot ratios and fine laser current    
    ratio1 = (meta[0,:]/32768.0)    
    ratio2 = (meta[1,:]/32768.0)    
    fineCurrent = meta[4,:]
    pylab.figure()
    pylab.plot(arange(512),ratio1,arange(512),ratio2)
    pylab.ylabel("Ratios")
    pylab.grid(True)
    pylab.figure()
    pylab.plot(arange(512),fineCurrent)
    pylab.grid(True)
    pylab.show()
