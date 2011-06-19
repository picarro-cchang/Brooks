#!/usr/bin/python
#
# FILE:
#   CalibrateFsr.py
#
# DESCRIPTION:
#   Calibrate the wavelength monitor for a virtual laser by using FSR hopping
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#  27-Apr-2011  sze  Initial release
#
#  Copyright (c) 2011 Picarro, Inc. All rights reserved
#

import sys
import types
import getopt
from numpy import *
import os
import Queue
import socket
import time
import threading
from configobj import ConfigObj
from Host.autogen import interface
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from scipy.optimize import fmin
from Host.Common.WlmCalUtilities import bestFit
from os.path import join, split, splitext
from shutil import copyfile


if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("CalibrateFsr")

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="CalibrateFsr")
            self.initialized = True

class RDFreqConvProxy(SharedTypes.Singleton):
    """Encapsulates access to the Ringdown Frequency Converter via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_FREQ_CONVERTER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="CalibrateFsr")
            self.initialized = True

class SpectrumCollectorProxy(SharedTypes.Singleton):
    """Encapsulates access to the Spectrum Collector via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_SPECTRUM_COLLECTOR)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="CalibrateFsr")
            self.initialized = True

# For convenience in calling driver and frequency converter functions
Driver = DriverProxy().rpc
RDFreqConv = RDFreqConvProxy().rpc
SpectrumCollector = SpectrumCollectorProxy().rpc

def _value(valueOrName):
    if isinstance(valueOrName,types.StringType):
        try:
            valueOrName = getattr(interface,valueOrName)
        except AttributeError:
            raise AttributeError("Value identifier not recognized %r" % valueOrName)
    return valueOrName

def setFPGAbits(FPGAblockName,FPGAregName,optList):
    optMask = 0
    optNew = 0
    for opt,val in optList:
        bitpos = 1<<_value("%s_%s_B" % (FPGAregName,opt))
        fieldMask = (1<<_value("%s_%s_W" % (FPGAregName,opt)))-1
        optMask |= bitpos*fieldMask
        optNew  |= bitpos*val
    oldVal = Driver.rdFPGA(FPGAblockName,FPGAregName)
    newVal = ((~optMask) & oldVal) | optNew
    Driver.wrFPGA(FPGAblockName,FPGAregName,newVal)

def getNextNonNullLine(sp):
    """ Return next line in a stream which is not blank and which does not
    start with a # character"""
    while True:
        line = sp.readline().strip()
        if not line or line[0] == "#":
            continue
        else:
            return line

def linearInterp(x,y,xf):
    """Linear interpolation. The points (x,y) are assumed to be sorted so that
    the x values are strictly monotonically increasing. xf is the set of points
    at which the interpolates are to be calculated"""

    # Sort x values into increasing order
    p = x.argsort()
    x = x.copy()[p]
    y = y.copy()[p]
    xf = xf.copy()
    sat = xf>=x[-1]

    # Replace values of xf outside the valid range with x[0]
    xf[xf<x[0]]= x[0]
    xf[sat] = x[0]

    # Find locations of xf values within array x
    pos = digitize(x=xf,bins=x)
    h = x[pos]-x[pos-1]
    yf = y[pos-1] + (y[pos]-y[pos-1])*(xf-x[pos-1])/h

    # Handle values of xf above the largest element of x
    yf[sat] = y[-1]
    return yf

def nsame(v):
    # Count number of identical elements at the start of an array
    i = 0
    for x in v:
        if x != v[0]: break
        i += 1
    return i

def coalascePoints(x,y):
    """Given a set of points (x,y), coalasce points with equal x values, taking the median
    of all y values associated with this x."""
    # Sort x values into increasing order
    p = x.argsort()
    x = x.copy()[p]
    y = y.copy()[p]
    xu = []
    yu = []
    i = 0
    while i<len(x):
        s = nsame(x[i:])
        xu.append(x[i])
        yu.append(median(y[i:i+s]))
        i += s
    return (array(xu,dtype=x.dtype),array(yu,dtype=y.dtype))

class CalibrateFsr(object):
    def __init__(self,configFile,options):
        self.config = ConfigObj(configFile)
        self.basePath = os.path.split(os.path.abspath(configFile))[0]
        self.spectrumFile = "./CalibrateFsr.h5"
        # Analyze options
        if "-s" in options:
            self.nSteps = int(options["-s"])
        else:
            self.nSteps = int(self.config["SETTINGS"]["NSTEPS"])
        if self.nSteps < 5 or self.nSteps > 500:
            raise ValueError("NSTEPS must be in range 5..500")
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
        self.angleRelax = float(self.config["SETTINGS"]["ANGLE_RELAX"])
        if "-a" in options:
            self.approxFsr = float(options["-a"])
        elif "APPROX_FSR_ANGLE" in self.config["SETTINGS"]:
            self.approxFsr = float(self.config["SETTINGS"]["APPROX_FSR_ANGLE"])
        else:
            self.approxFsr = APPROX_FSR
        if "-f" in options:
            self.spectrumFile = options["-f"]
        elif "SPECTRUM_FILE" in self.config["SETTINGS"]:
            self.spectrumFile = self.config["SETTINGS"]["SPECTRUM_FILE"]
            
        self.spectrumFile = os.path.join(self.basePath,self.spectrumFile)
        
        self.seq = 0
        self.processingDone = threading.Event()
        self.clearLists()
        # Define a listener for the ringdown data
        # self.listener = Listener(None,SharedTypes.BROADCAST_PORT_RDRESULTS,RingdownEntryType,self.rdFilter)

    def clearLists(self):
        self.tunerList = []
        self.angleList = []
        self.schemeRowList = []

    def makeAndUploadScheme(self,wlmAngles,laserTemps,vLaserNum,repeat,dwell):
        # Generate an angle-based scheme with subschemeId given by the value of self.seq.
        # Use scheme number 14, unless it is the current scheme, in which case use scheme 15.
        # Make the scheme the next scheme to be run.
        self.seq += 1
        schemeNum = 14
        numEntries = len(wlmAngles)
        dwells = dwell*ones(wlmAngles.shape)
        subschemeIds = self.seq*ones(wlmAngles.shape)
        virtualLasers = (vLaserNum-1)*ones(wlmAngles.shape)
        thresholds = zeros(wlmAngles.shape)
        pztSetpoints = zeros(wlmAngles.shape)
        if schemeNum == Driver.rdDasReg("SPECT_CNTRL_ACTIVE_SCHEME_REGISTER"): 
            schemeNum = 15
        Driver.wrScheme(schemeNum,repeat,zip(wlmAngles,dwells,subschemeIds,virtualLasers,thresholds,pztSetpoints,laserTemps))
        Driver.wrDasReg("SPECT_CNTRL_NEXT_SCHEME_REGISTER",schemeNum)
        
    def rdFilter(self,entry):
        """Accumulates statistics in dictionaries (tunerSum and count) keyed by scheme row. These are
            used for flattening the PZT values during the FSR scheme.
           tunerList and angleList are lists containing all ringdowns (without regard to scheme row)
            which are used to determine the approximate FSR and sensitivity during the initial
            fine scheme."""
        assert isinstance(entry,RingdownEntryType)
        if not self.processingDone.isSet():
            if not(entry.status & RINGDOWN_STATUS_RingdownTimeout) and self.seq == (entry.subschemeId & SUBSCHEME_ID_IdMask):
                schemeRow = entry.schemeRow
                self.tunerSum[schemeRow] += entry.tunerValue
                self.tunerList.append(entry.tunerValue)
                self.angleList.append(entry.wlmAngle)
                self.schemeRowList.append(schemeRow)
                self.count[schemeRow] += 1
            # Check when we get to the end of the scheme
            if (entry.status & RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask) or \
               (entry.status & RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask):
                self.processingDone.set()

    def update(self,wlmAngles,vLaserNum,nRefine=4):
        # We now have a list of wlmAngles that correspond to frequencies separated by
        #  multiples of the cavity FSR. We use them to update the B-spline coefficients
        #  in the wavelength monitor calibration.
        theta = array(wlmAngles,dtype='d')
        dtheta = diff(theta)
        # Try to find an average angle change corresponding to an FSR. The values of 
        #  abs(dtheta) are integer multiples of the desired quantity.
        m = mean(abs(dtheta))
        while True:
            r = round_(dtheta/m)
            good = nonzero(r)
            m1 = mean(dtheta[good]/r[good])
            if m == m1: break
            m = m1
        cr = zeros(len(theta),dtype='l')
        cr[1:] = cumsum(r)
        # cr now counts the number of FSR associated with WLM angles in theta
        # Sort these into ascending order and coalasce points with same index
        p = cr.argsort()
        cr = cr[p]
        theta = theta[p]
        cr,theta = coalascePoints(cr,theta)
        # Use interpolation to fill in calibration points so they are closer together than the spline knots
        waveNumbers = linspace(cr[0],cr[-1],nRefine*(cr[-1]-cr[0])+1)
        theta = linearInterp(cr,theta,waveNumbers)
        # Determine the cavity FSR if necessary
        if self.fsr == None:
            w = RDFreqConv.angleToWaveNumber(vLaserNum,wlmAngles)
            self.fsr = bestFit(cumsum(r),w[1:],1).coeffs[0]
        waveNumbers *= self.fsr
        msg = "Cavity free spectral range = %f wavenumbers" % (self.fsr,)
        print msg
        print>>self.op, msg
        msg = "Virtual laser number = %d" % (vLaserNum,)
        print msg
        print>>self.op, msg
        for i in range(50):
            RDFreqConv.updateWlmCal(vLaserNum,theta,waveNumbers,1.0,0.1,True)
        RDFreqConv.replaceOriginalWlmCal(vLaserNum)
        return self.fsr

    def run(self):
        # Check that the driver can communicate
        try:
            print "Driver version: %s" % Driver.allVersions()
        except:
            raise ValueError,"Cannot communicate with driver, aborting"
            
        startTime = time.localtime()
        jobName = time.strftime("CalibrateFsr_%Y%m%d_%H%M%S",startTime)
        self.op = file(jobName + ".txt","w")
       

        # Save the original warm and hot box calibration files in the current directory
        wbCalFileName = RDFreqConv.getWarmBoxCalFilePath()
        hbCalFileName = RDFreqConv.getHotBoxCalFilePath()
        root, ext = splitext(split(wbCalFileName)[1])
        copyfile(wbCalFileName,'%s_before_%s%s' % (root,jobName,ext))
        root, ext = splitext(split(hbCalFileName)[1])
        copyfile(hbCalFileName,'%s_before_%s%s' % (root,jobName,ext))
        
        # Determine the actual laser corresponding to this virtual laser
        laserParams = Driver.rdVirtualLaserParams(self.vLaserNum)
        aLaserNum = laserParams["actualLaser"] + 1
        
        try:
            # Ensure that we do not use spline (i.e., only use linear model)
            RDFreqConv.ignoreSpline(self.vLaserNum)
            # Calculate the laser temperature range over which we should sweep
            minWaveNumber = self.waveNumberCen - self.nSteps*0.0206
            maxWaveNumber = self.waveNumberCen + self.nSteps*0.0206
            theta = RDFreqConv.waveNumberToAngle(self.vLaserNum,[maxWaveNumber,minWaveNumber])
            minLaserTemp,maxLaserTemp = RDFreqConv.angleToLaserTemperature(self.vLaserNum,theta)
            
            print "Laser %d temperature range %.3f to %.3f" % (aLaserNum, minLaserTemp, maxLaserTemp)

            regVault = Driver.saveRegValues(["LASER%d_TEMP_CNTRL_SWEEP_MAX_REGISTER" % aLaserNum,
                                             "LASER%d_TEMP_CNTRL_SWEEP_MIN_REGISTER" % aLaserNum,
                                             "LASER%d_TEMP_CNTRL_SWEEP_INCR_REGISTER" % aLaserNum,
                                             "LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % aLaserNum,
                                             "LASER%d_TEMP_CNTRL_STATE_REGISTER" % aLaserNum,
                                             "ANALYZER_TUNING_MODE_REGISTER",
                                             "TUNER_SWEEP_RAMP_HIGH_REGISTER",
                                             "TUNER_SWEEP_RAMP_LOW_REGISTER",
                                             "TUNER_WINDOW_RAMP_HIGH_REGISTER",
                                             "TUNER_WINDOW_RAMP_LOW_REGISTER",
                                             ("FPGA_TWGEN","TWGEN_SLOPE_UP"),
                                             ("FPGA_TWGEN","TWGEN_SLOPE_DOWN"),
                                             ("FPGA_TWGEN","TWGEN_CS"),
                                             "SPECT_CNTRL_MODE_REGISTER",
                                             ("FPGA_RDMAN","RDMAN_OPTIONS"),
                                             ("FPGA_INJECT","INJECT_CONTROL"),
                                             "RDFITTER_META_BACKOFF_REGISTER",
                                             "RDFITTER_META_SAMPLES_REGISTER",
                                             "VIRTUAL_LASER_REGISTER",
                                             ("FPGA_LASERLOCKER","LASERLOCKER_OPTIONS"),
                                             ("FPGA_LASERLOCKER","LASERLOCKER_TUNING_OFFSET")
                                             ])
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_IdleState)
            print>>self.op, "Virtual laser Index: %d"   % self.vLaserNum
            print>>self.op, "Center wavenumber:   %.3f" % self.waveNumberCen
            print>>self.op, "Number of steps:     %d"   % self.nSteps
            Driver.wrDasReg("PZT_OFFSET_VIRTUAL_LASER%d" % self.vLaserNum,0)

            # Set up laser temperature sweep
            
            sweepIncr = 0.04 # degrees in 0.2s => 1 degree every 5 s
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_SWEEP_MAX_REGISTER" % aLaserNum,maxLaserTemp)
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_SWEEP_MIN_REGISTER" % aLaserNum,minLaserTemp)
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_SWEEP_INCR_REGISTER" % aLaserNum,sweepIncr)
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % aLaserNum, minLaserTemp)
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % aLaserNum, "TEMP_CNTRL_EnabledState")
            
            # Set up analyzer for frequency hopping mode acquisition

            Driver.wrDasReg("ANALYZER_TUNING_MODE_REGISTER",ANALYZER_TUNING_LaserCurrentTuningMode)
            Driver.wrFPGA("FPGA_TWGEN","TWGEN_SLOPE_UP",1000)
            Driver.wrFPGA("FPGA_TWGEN","TWGEN_SLOPE_DOWN",1000)
            Driver.wrDasReg("TUNER_SWEEP_RAMP_LOW_REGISTER",14500)
            Driver.wrDasReg("TUNER_WINDOW_RAMP_LOW_REGISTER",15000)
            Driver.wrDasReg("TUNER_WINDOW_RAMP_HIGH_REGISTER",50500)
            Driver.wrDasReg("TUNER_SWEEP_RAMP_HIGH_REGISTER",50000)
            setFPGAbits("FPGA_TWGEN","TWGEN_CS",[("TUNE_PZT",0)])
            Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER","SPECT_CNTRL_ContinuousManualTempMode")
            setFPGAbits("FPGA_RDMAN","RDMAN_OPTIONS",[("LOCK_ENABLE",0),
                                                      ("UP_SLOPE_ENABLE",1),
                                                      ("DOWN_SLOPE_ENABLE",1),
                                                      ("DITHER_ENABLE",0)])
            Driver.wrDasReg("RDFITTER_META_BACKOFF_REGISTER", 1)
            Driver.wrDasReg("RDFITTER_META_SAMPLES_REGISTER", 1)
            setFPGAbits("FPGA_LASERLOCKER","LASERLOCKER_OPTIONS",[("DIRECT_TUNE",1)])

            # Set up actual laser and virtual laser
            setFPGAbits("FPGA_INJECT","INJECT_CONTROL",[("LASER_SELECT",aLaserNum-1)])
            Driver.wrDasReg("VIRTUAL_LASER_REGISTER",self.vLaserNum-1)
            
            print "Waiting for laser temperature to settle"
            while abs(Driver.rdDasReg("LASER%d_TEMPERATURE_REGISTER" % aLaserNum)-minLaserTemp)>0.01:
                sys.stdout.write('.')
                time.sleep(1.0)
            sys.stdout.write('\n')
            time.sleep(2.0)
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % aLaserNum, "TEMP_CNTRL_SweepingState")

            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_StartManualState")
            
            SpectrumCollector.setAuxiliarySpectrumFile(self.spectrumFile)
            print "Starting to acquire data in FSR hopping mode"
            start = time.clock()
            totTime = 0.2*2*(maxLaserTemp-minLaserTemp)/sweepIncr
            complete = 0
            while complete < 100:
                now = time.clock()
                complete = round(100*(now-start)/totTime)
                sys.stdout.write("\r%d%% complete" % complete)
                time.sleep(2.0)
            sys.stdout.write("\r100% complete\n")
        except Exception,e:
            print>>self.op,"ERROR: %s" % e
            raise
        finally:
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_IdleState)
            #RDFreqConv.updateWarmBoxCal()
            #RDFreqConv.updateHotBoxCal()
            #root, ext = splitext(split(wbCalFileName)[1])
            #copyfile(wbCalFileName,'%s_after_%s%s' % (root,jobName,ext))
            #root, ext = splitext(split(hbCalFileName)[1])
            #copyfile(hbCalFileName,'%s_after_%s%s' % (root,jobName,ext))
            RDFreqConv.useSpline(self.vLaserNum)
            Driver.restoreRegValues(regVault)
            time.sleep(2.0)
            Driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_TUNING_OFFSET",32768)

HELP_STRING = """CalibrateFsr.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./CalibrateFsr.ini"
-f                   specify an output file for spectrum: default = "./CalibrateFsr.h5"
-s                   number of steps on each side of center
-v                   specify virtual laser (1-origin) to calibrate
-w                   center wavenumber about which to calibrate
-a                   approximate cavity FSR in WLM angle (radians)
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:s:v:w:a:f:'
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
    c = CalibrateFsr(configFile, options)
    c.run()
