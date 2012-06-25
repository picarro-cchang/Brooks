#!/usr/bin/python
#
# FILE:
#   LaserLockPrbs.py
#
# DESCRIPTION:
#   Utility to measure response of laser frequency to PRBS current excitation
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
from thermalAnalysis2 import find_ARMA, Ltid

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
    data.asInt = LASER_CURRENT_CNTRL_ManualState;
    Driver.wrDasReg("LASER1_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
    Driver.wrDasReg("LASER2_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
    Driver.wrDasReg("LASER3_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
    Driver.wrDasReg("LASER4_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")

def selectLaser(aLaserNum):
    changeBitsFPGA("FPGA_INJECT","INJECT_CONTROL","INJECT_CONTROL_LASER_SELECT_B","INJECT_CONTROL_LASER_SELECT_W",aLaserNum-1)

# from Host.autogen.interface import RDMAN_OPTIONS_UP_SLOPE_ENABLE_B, RDMAN_OPTIONS_UP_SLOPE_ENABLE_W
# from Host.autogen.interface import RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B, RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_W

if __name__ == "__main__":
    try:
        regVault = Driver.saveRegValues(["VIRTUAL_LASER_REGISTER",
                                         ("FPGA_LASERLOCKER","LASERLOCKER_WM_INT_GAIN"),
                                         ("FPGA_LASERLOCKER","LASERLOCKER_WM_PROP_GAIN"),
                                         ("FPGA_LASERLOCKER","LASERLOCKER_WM_DERIV_GAIN"),
                                         ("FPGA_RDMAN","RDMAN_OPTIONS"),
                                         ("FPGA_RDMAN","RDMAN_TIMEOUT_DURATION"),
                                         ("FPGA_LASERLOCKER","LASERLOCKER_CS"),
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
        # Disable ringdowns on both slopes
        changeBitsFPGA("FPGA_RDMAN","RDMAN_OPTIONS","RDMAN_OPTIONS_UP_SLOPE_ENABLE_B","RDMAN_OPTIONS_UP_SLOPE_ENABLE_W",0)
        changeBitsFPGA("FPGA_RDMAN","RDMAN_OPTIONS","RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B","RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_W",0)
        # Set up a set of gains for the wavelength locker
        I_gain = 64
        P_gain = 0
        D_gain = 0
        #
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_WM_INT_GAIN",I_gain)
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_WM_PROP_GAIN",P_gain)
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_WM_DERIV_GAIN",D_gain)
        # Set ringdown timeout duration to one second
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_TIMEOUT_DURATION",1000000)
        selectLaser(aLaserNum)
        setAutomaticControl()
        # Enable PRBS generation
        changeBitsFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS","LASERLOCKER_CS_PRBS_B","LASERLOCKER_CS_PRBS_W",1)
        status = Driver.rdFPGA("FPGA_RDMAN","RDMAN_STATUS")
        print "Initial RD manager status: 0x%x" % status
        # Tell RDMAN to collect data
        changeBitsFPGA("FPGA_RDMAN","RDMAN_CONTROL","RDMAN_CONTROL_START_RD_B","RDMAN_CONTROL_START_RD_W",1)
        time.sleep(1)
        status = Driver.rdFPGA("FPGA_RDMAN","RDMAN_STATUS")
        print "Final RD manager status: 0x%x" % status
        bank = (status & (1<<RDMAN_STATUS_BANK_B)) == (1<<RDMAN_STATUS_BANK_B)
        # Get acquired data for analysis
        if bank:
            data,meta,param = Driver.rdRingdown(1)
        else:
            data,meta,param = Driver.rdRingdown(0)

        # Extract fine laser current excitation
        fineCurrent = meta[4,:]-32768
        # Extract output of PID
        pid_out = meta[6,:]

        fineCurrent = fineCurrent[256:]
        FINE_CURRENT = fft.fft(fineCurrent)
        pid_out = pid_out[256:]
        PID_OUT = fft.fft(pid_out)
        
        w = arange(128)*pi/128.0
        resp = PID_OUT/FINE_CURRENT
        
        z = exp(1j*w)
        T = (I_gain/32768.0)*z/(z-1) + (P_gain/32768.0) + (D_gain/32768.0)*(z-1)/z
        
        pylab.figure()
        pylab.subplot(2,1,1)
        pylab.plot(fineCurrent)
        pylab.grid(True)
        pylab.subplot(2,1,2)
        pylab.plot(pid_out)
        pylab.grid(True)
        pylab.figure()
        pylab.subplot(2,1,1)
        pylab.plot(w,20*log10(abs(resp[:128])),w,20*log10(abs(T)))
        pylab.grid(True)
        pylab.subplot(2,1,2)
        pylab.plot(w,180.0*unwrap(angle(resp[:128]))/pi,w,180.0*angle(T)/pi)
        pylab.grid(True)
        pylab.show()
    finally:
        Driver.restoreRegValues(regVault)
