#!/usr/bin/python
#
# FILE:
#   CalibrateSystem.py
#
# DESCRIPTION:
#   Calibrate the wavelength monitor for a virtual laser by measuring the PZT
#  sensitivity and generating an FSR scheme which is then optimized.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   8-Oct-2009  sze  Modified Silverstone utility
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#

import sys
import getopt
from numpy import *
import os
import Queue
import socket
import time
import threading
import traceback
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from scipy.optimize import fmin
from Host.Common.WlmCalUtilities import bestFit
from os.path import join, split, splitext
from shutil import copyfile
APPROX_FSR = 0.08


if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("CalibrateSystem")

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

class CalibrateSystem(object):
    def __init__(self,configFile,options):
        self.config = ConfigObj(configFile)
        self.fsr = None
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
            self.fsr = float(options["-f"])
        elif "CAVITY_FSR" in self.config["SETTINGS"]:
            self.fsr = float(self.config["SETTINGS"]["CAVITY_FSR"])
        
        
        self.seq = 0
        self.processingDone = threading.Event()
        self.clearLists()
        # Define a listener for the ringdown data
        self.listener = Listener(None,SharedTypes.BROADCAST_PORT_RDRESULTS,RingdownEntryType,self.rdFilter)

    def clearLists(self):
        self.tunerList = []
        self.angleList = []
        self.schemeRowList = []

    def setupRampMode(self,ditherPeakToPeak,tunerMean,rampAmpl,tunerMin = 5000,tunerMax=60000):
        # Load DAS registers to give a ramp whose window is centered about tunerMean and has amplitude rampAmpl
        rampAmpl = float(rampAmpl)
        tunerMean = float(tunerMean)
        ditherPeakToPeak = float(ditherPeakToPeak)
        
        if 2*rampAmpl + ditherPeakToPeak > tunerMax - tunerMin:
            rampAmpl = (tunerMax - tunerMin - ditherPeakToPeak)//2
            
        if tunerMean < tunerMin + rampAmpl + ditherPeakToPeak//2:
            tunerMean = tunerMin + rampAmpl + ditherPeakToPeak//2
        if tunerMean > tunerMax - (rampAmpl + ditherPeakToPeak//2):
            tunerMean = tunerMax - (rampAmpl + ditherPeakToPeak//2)
        
        msg = "Recentering tuner around %d" % (tunerMean,)
        print msg
        print>>self.op, msg

        Driver.wrDasReg("TUNER_WINDOW_RAMP_HIGH_REGISTER", tunerMean + rampAmpl)
        Driver.wrDasReg("TUNER_WINDOW_RAMP_LOW_REGISTER",  tunerMean - rampAmpl)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_HIGH_REGISTER",  tunerMean + rampAmpl + ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_LOW_REGISTER",   tunerMean - rampAmpl - ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER", ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER",  ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER",int(0.45*ditherPeakToPeak))
        Driver.wrDasReg("TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER", int(0.45*ditherPeakToPeak))

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
        jobName = time.strftime("CalibrateSystem_%Y%m%d_%H%M%S",startTime)
        self.op = file(jobName + ".txt","w")
       

        # Save the original warm and hot box calibration files in the current directory
        wbCalFileName = RDFreqConv.getWarmBoxCalFilePath()
        hbCalFileName = RDFreqConv.getHotBoxCalFilePath()
        root, ext = splitext(split(wbCalFileName)[1])
        copyfile(wbCalFileName,'%s_before_%s%s' % (root,jobName,ext))
        root, ext = splitext(split(hbCalFileName)[1])
        copyfile(hbCalFileName,'%s_before_%s%s' % (root,jobName,ext))
        
        try:
            regVault = Driver.saveRegValues(["TUNER_SWEEP_RAMP_HIGH_REGISTER",
                                             "TUNER_SWEEP_RAMP_LOW_REGISTER",
                                             "TUNER_WINDOW_RAMP_HIGH_REGISTER",
                                             "TUNER_WINDOW_RAMP_LOW_REGISTER",
                                             "TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER",
                                             "TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER",
                                             "TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER",
                                             "TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER",
                                             "PZT_OFFSET_VIRTUAL_LASER1",
                                             "PZT_OFFSET_VIRTUAL_LASER2",
                                             "PZT_OFFSET_VIRTUAL_LASER3",
                                             "PZT_OFFSET_VIRTUAL_LASER4",
                                             "PZT_OFFSET_VIRTUAL_LASER5",
                                             "PZT_OFFSET_VIRTUAL_LASER6",
                                             "PZT_OFFSET_VIRTUAL_LASER7",
                                             "PZT_OFFSET_VIRTUAL_LASER8",
                                             ])
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_IdleState)
            print>>self.op, "Virtual laser Index: %d"   % self.vLaserNum
            print>>self.op, "Center wavenumber:   %.3f" % self.waveNumberCen
            print>>self.op, "Number of steps:     %d"   % self.nSteps
            Driver.wrDasReg("PZT_OFFSET_VIRTUAL_LASER%d" % self.vLaserNum,0)

            tunerCenter = 32768 # Center position
            rampAmpl = 25000    # Set to sweep over more than an FSR
            ditherPeakToPeak = 8000
            self.setupRampMode(ditherPeakToPeak,tunerCenter,rampAmpl)
            # Ensure that we start with original calibration information
            RDFreqConv.restoreOriginalWlmCal(self.vLaserNum)
            theta0 = RDFreqConv.waveNumberToAngle(self.vLaserNum,[self.waveNumberCen])[0]
            # Make a fine angle-based scheme covering +/- 6FSR for determining PZT sensitivity
            # fwd = arange(-600.0,601.0)
            fwd = arange(-150.0,151.0)
            steps = concatenate((fwd,fwd[::-1]))
            # wlmAngles = theta0 + steps*(self.approxFsr/50.0)
            wlmAngles = theta0 + steps*(self.approxFsr/25.0)
            laserTemps = RDFreqConv.angleToLaserTemperature(self.vLaserNum,wlmAngles)
            nRepeat = 3
            dwell = 2
            self.makeAndUploadScheme(wlmAngles,laserTemps,self.vLaserNum,nRepeat,dwell)
            Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER",SPECT_CNTRL_SchemeSingleMode)
            # Start collecting data in the rdFilter
            self.clearLists()
            self.tunerSum = zeros(laserTemps.shape,dtype='d')
            self.count = zeros(laserTemps.shape)
            self.processingDone.clear()
            time.sleep(1.0)
            msg = "Collecting data for PZT sensitivity measurement"
            print msg
            print>>self.op, msg
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_StartingState)
            while not self.processingDone.isSet():
                self.processingDone.wait(1.0)
                sys.stdout.write(".")
            print "\nCompleted data collection for PZT sensitivity measurement"
            # Discard the first repetition, and turn the rest into arrays
            L = min(len(self.angleList),len(self.tunerList),len(self.schemeRowList))
            self.angleList = array(self.angleList[L//nRepeat:L+1],'d')
            self.tunerList = array(self.tunerList[L//nRepeat:L+1],'d')
            self.schemeRowList = array(self.schemeRowList[L//nRepeat:L+1],'d')
            # To find the PZT sensitivity, we carry out an optimization. The following cost
            #  function wraps the angle and tuner information around a torus, using p[0] and
            #  p[1] as the trial periods.
            def cost(p,angle,tuner):
                x = angle/p[0] - tuner/p[1]
                c1 = std(x - floor(x))
                return c1
                #c2 = std(x+0.5 - floor(x+0.5))
                #return min(c1,c2)
            
            fBest = 1e38
            for trialSens in range(7000,50000,1000):
                popt = fmin(cost,array([self.approxFsr,trialSens]),args=(self.angleList,self.tunerList),maxiter=10000,maxfun=50000)
                fopt = cost(popt,self.angleList,self.tunerList)
                if fopt < fBest:
                    fBest = fopt
                    pBest = popt
            popt = pBest
            fopt = fBest
            msg = "Residual: %.3f" % (fopt,)
            print msg
            print>>self.op, msg
            msg = "Cavity FSR  (WLM radians):    %.5f" % (popt[0],)
            print msg
            print>>self.op, msg
            msg = "Sensitivity (digU/FSR): %.0f" % (popt[1],)
            print msg
            print>>self.op, msg
            RDFreqConv.setHotBoxCalParam("CAVITY_LENGTH_TUNING","PZT_SCALE_FACTOR",Driver.rdFPGA("FPGA_SCALER","SCALER_SCALE1"))
            RDFreqConv.setHotBoxCalParam("CAVITY_LENGTH_TUNING","FREE_SPECTRAL_RANGE",popt[1])
            RDFreqConv.setHotBoxCalParam("AUTOCAL","APPROX_WLM_ANGLE_PER_FSR",popt[0])
            # Next generate a scheme consisting of nominal FSR steps
            angleFSR = float(popt[0])
            tunerFSR = float(popt[1])
            theta0 = RDFreqConv.waveNumberToAngle(self.vLaserNum,[self.waveNumberCen])[0]
            fwd = arange(-self.nSteps,self.nSteps+1)
            steps = concatenate((fwd,fwd[::-1]))
            wlmAngles = theta0 + steps*angleFSR
            laserTemps = RDFreqConv.angleToLaserTemperature(self.vLaserNum,wlmAngles)
            nRepeat = 1
            dwell = 10
            maxIter = 10
            for iter in range(maxIter):
                self.tunerSum = zeros(wlmAngles.shape,dtype='d')
                self.count = zeros(wlmAngles.shape)
                self.makeAndUploadScheme(wlmAngles,laserTemps,self.vLaserNum,nRepeat,dwell)
                Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER",SPECT_CNTRL_SchemeSingleMode)
                # Start collecting data in the rdFilter
                self.clearLists()
                self.processingDone.clear()
                time.sleep(1.0)
                msg = "Starting spectrum acquisition (pass %d of %d)" % (iter+1,maxIter)
                print msg
                print>>self.op, msg
                Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_StartingState)
                while not self.processingDone.isSet():
                    self.processingDone.wait(1.0)
                    sys.stdout.write(".")
                print
                # Find mean and standard deviation of tuner values
                good = self.count.nonzero()
                self.tunerSum[good] = self.tunerSum[good]/self.count[good]
                tunerMean = mean(self.tunerSum[good])
                sDev = std(self.tunerSum[good]-tunerMean)
                msg = "Standard deviation: %.1f" % (sDev,)
                print msg
                print>>self.op, msg
                # Calculate by how much to change the angles in the scheme to flatten the
                #  tuner values
                tunerMedian = median(self.tunerSum[good])
                tunerDev = self.tunerSum[good] - tunerMedian
                # print tunerDev
                wlmAngles[good] = wlmAngles[good] - self.angleRelax*tunerDev
                # Recenter the tuner if necessary
                if abs(tunerCenter-tunerMedian) > 0.2*tunerFSR:
                    tunerCenter = tunerMedian
                rampAmpl = 0.65*tunerFSR
                ditherPeakToPeak = 8000
                self.setupRampMode(ditherPeakToPeak,tunerCenter,rampAmpl)

            # Use the list of wlmAngles to update the current spline coefficients
            cavityFSR = self.update(wlmAngles,self.vLaserNum)
            RDFreqConv.setHotBoxCalParam("AUTOCAL","CAVITY_FSR",cavityFSR)
            RDFreqConv.setHotBoxCalParam("AUTOCAL","CAVITY_FSR_VLASER_%d" % self.vLaserNum,cavityFSR)
        except Exception,e:
            print>>self.op, "ERROR: %s" % e
            print>>self.op, traceback.format_exc()
            raise
        finally:
            RDFreqConv.updateWarmBoxCal()
            RDFreqConv.updateHotBoxCal()
            root, ext = splitext(split(wbCalFileName)[1])
            copyfile(wbCalFileName,'%s_after_%s%s' % (root,jobName,ext))
            root, ext = splitext(split(hbCalFileName)[1])
            copyfile(hbCalFileName,'%s_after_%s%s' % (root,jobName,ext))
            Driver.restoreRegValues(regVault)

HELP_STRING = """CalibrateSystem.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./CalibrateSystem.ini"
-f                   specify a measured cavity FSR (in wavenumbers)
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
    c = CalibrateSystem(configFile, options)
    c.run()
