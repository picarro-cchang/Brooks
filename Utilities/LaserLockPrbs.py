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
        # Convert WLM ratios into angles
        X = (meta[0,:]/32768.0) - ratio1Center
        Y = (meta[1,:]/32768.0) - ratio2Center
        thetaCal = unwrap(arctan2(
          ratio1Scale * Y - ratio2Scale * X * sin(phase),
          ratio2Scale * X * cos(phase)))
        # Extract fine laser current excitation
        fineCurrent = meta[4,:]
        # Calculate FFTs to find response of angle to current
        thetaCal = thetaCal[256:]
        fineCurrent = fineCurrent[256:]
        THETA_CAL = fft.fft(thetaCal)
        FINE_CURRENT = fft.fft(fineCurrent)
        # Calculate delay
        phi = unwrap(angle(-THETA_CAL/FINE_CURRENT))
        p = polyfit(range(2,48),phi[2:48],1)
        delaySamples = -p[0]*256/(2*pi)
        print "Delay in samples: %.3f" % delaySamples
        num,den,res,rank,sv,mock = find_ARMA(fineCurrent,thetaCal,[3,4,5,6],[1,2,3,4,5,6])
        # Transfer functions as ratios of polynomials in z^-1
        sysG = Ltid.fromNumDen(num,den)
        w = arange(128)*pi/128.0
        resp = sysG.freqz(w)
        fname = raw_input("File name for output? ")
        saveVars = ["num","den","ratio1Center","ratio1Scale","ratio2Center","ratio2Scale","phase","thetaCal","fineCurrent"]
        pickle.dump(dict([(v,locals()[v]) for v in saveVars]),file(fname,"wb"))
        pylab.plot(w,20*log10(abs(resp)),w,20*log10(abs(THETA_CAL[:128]/FINE_CURRENT[:128])),'x')
        pylab.show()
    finally:
        Driver.restoreRegValues(regVault)
