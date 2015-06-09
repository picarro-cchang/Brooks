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
from Host.MfgUtilities.thermalAnalysis2 import find_ARMA, Ltid

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
                                        ("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_MULTIPLIER"),
                                        ("FPGA_LASERLOCKER","LASERLOCKER_RATIO2_MULTIPLIER"),
                                        ("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_CENTER"),
                                        ("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_CENTER"),
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
        fineCurrent1 = fineCurrent[256:]
        THETA_CAL = fft.fft(thetaCal)
        FINE_CURRENT1 = fft.fft(fineCurrent1)
        # Calculate delay
        phi = unwrap(angle(-THETA_CAL/FINE_CURRENT1))
        p = polyfit(range(2,48),phi[2:48],1)
        delaySamples = -p[0]*256/(2*pi)
        print "Delay in samples: %.3f" % delaySamples
        num1,den1,res,rank,sv,mock = find_ARMA(fineCurrent1,thetaCal,[3,4,5,6],[1,2,3,4,5,6])
        # Transfer functions as ratios of polynomials in z^-1
        sysG1 = Ltid.fromNumDen(num1,den1)
        w = arange(128)*pi/128.0
        resp1 = sysG1.freqz(w)
        # Set up the laser locking parameters to target the mean angle, so that we can get the response
        #  from the fine current to the lock_error signal
        theta = mean(thetaCal)
        print theta
        ratio1Multiplier = (-sin(theta + phase))/(ratio1Scale * cos(phase))
        ratio2Multiplier = cos(theta)/(ratio2Scale * cos(phase))
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_MULTIPLIER",int(ratio1Multiplier*32767.0))
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_RATIO2_MULTIPLIER",int(ratio2Multiplier*32767.0))
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_CENTER",int(ratio1Center*32768.0))
        Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_RATIO2_CENTER",int(ratio2Center*32768.0))
        # Send PRBS again
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
        #
        error_signal = meta[5,:]
        neg = error_signal>=32768
        error_signal[neg] = error_signal[neg] - 65536
        fineCurrent = meta[4,:]

        # Convert WLM ratios into angles
        X = (meta[0,:]/32768.0) - ratio1Center
        Y = (meta[1,:]/32768.0) - ratio2Center
        thetaCalNew = unwrap(arctan2(
          ratio1Scale * Y - ratio2Scale * X * sin(phase),
          ratio2Scale * X * cos(phase)))
        print mean(thetaCalNew[256:])

        # Calculate FFTs to find response of angle to current
        error_signal = error_signal[256:]
        fineCurrent2 = fineCurrent[256:]
        ERROR_SIGNAL = fft.fft(error_signal)
        FINE_CURRENT2 = fft.fft(fineCurrent2)
        # Calculate delay
        phi = unwrap(angle(-ERROR_SIGNAL/FINE_CURRENT2))
        p = polyfit(range(2,48),phi[2:48],1)
        delaySamples = -p[0]*256/(2*pi)
        print "Delay in samples: %.3f" % delaySamples
        num2,den2,res,rank,sv,mock = find_ARMA(fineCurrent2,error_signal,[3,4,5,6],[1,2,3,4,5,6])
        # Transfer functions as ratios of polynomials in z^-1
        sysG2 = Ltid.fromNumDen(num2,den2)
        w = arange(128)*pi/128.0
        resp2 = sysG2.freqz(w)

        fname = raw_input("File name for output? ")
        saveVars = ["num1","den1","num2","den2","ratio1Center","ratio1Scale","ratio2Center","ratio2Scale","phase","thetaCal","fineCurrent"]
        pickle.dump(dict([(v,locals()[v]) for v in saveVars]),file(fname,"wb"))
        pylab.figure()
        pylab.plot(w,20*log10(abs(resp1)),w,20*log10(abs(THETA_CAL[:128]/FINE_CURRENT1[:128])),'x')
        pylab.grid(True)
        pylab.figure()
        pylab.plot(w,20*log10(abs(resp2)),w,20*log10(abs(ERROR_SIGNAL[:128]/FINE_CURRENT2[:128])),'x')
        pylab.grid(True)
        pylab.show()
    finally:
        Driver.restoreRegValues(regVault)