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
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
import Queue
import getopt
import numpy
import os
import socket
import time
from scipy.optimize import fmin
APPROX_FSR = 0.077

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

# For convenience in calling driver functions
Driver = DriverProxy().rpc

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
    pos = numpy.digitize(x=xf,bins=x)
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
        yu.append(numpy.median(y[i:i+s]))
        i += s
    return (numpy.array(xu,dtype=x.dtype),numpy.array(yu,dtype=y.dtype))

class CalibrateSystem(object):
    def __init__(self,configFile,options):
        self.config = ConfigObj(configFile)
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
        
        self.seq = 0
        self.processResults = False
        self.clearLists()
        # Define a listener for the ringdown data
        self.listener = Listener(None,SharedTypes.BROADCAST_PORT_RDRESULTS,RingdownEntryType,self.rdFilter)

    def clearLists(self):
        self.pztList = []
        self.angleList = []
        self.schemeRowList = []

    def setupRampMode(self,ditherPeakToPeak,tunerMean,rampAmpl,tunerMin = 5000,tunerMax=60000):
        # Load DAS registers to give a ramp whose window is centered about tunerMean and has amplitude rampAmpl
        rampAmpl = float(rampAmpl)
        tunerMean = float(tunerMean)
        ditherPeakToPeak = float(ditherPeakToPeak)
        if tunerMean > tunerMin + rampAmpl and tunerMean < tunerMax - rampAmpl:
            msg = "Recentering tuner around %d" % (tunerMean,)
            print msg
            print>>self.op, msg
            if tunerMean - rampAmpl - ditherPeakToPeak < tunerMin:
                tunerMean += 2*rampAmpl
            if tunerMean + rampAmpl + ditherPeakToPeak > tunerMax:
                tunerMean -= 2*rampAmpl

        Driver.wrDasReg("TUNER_WINDOW_RAMP_HIGH_REGISTER", tunerMean + rampAmpl)
        Driver.wrDasReg("TUNER_WINDOW_RAMP_LOW_REGISTER",  tunerMean - rampAmpl)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_HIGH_REGISTER",  tunerMean + rampAmpl + ditherPeakToPeak)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_LOW_REGISTER",   tunerMean - rampAmpl - ditherPeakToPeak)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER", ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER",  ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER",int(0.45*ditherPeakToPeak))
        Driver.wrDasReg("TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER", int(0.45*ditherPeakToPeak))

    def rdFilter(self,entry):
        print entry
        
        
    if 0:
        def resultsFilter(self,entry):
            if self.processResults:
                fitStatus = c_int8(entry.etalonAndLaserSelectAndFitStatus & 0xFF).value
                if (entry.subSchemeId & 0x7FFF) == self.seq and \
                  fitStatus not in [ss_autogen.ERROR_RD_WRONG_SCHEME_INDEX]:
                    # We need to process these data
                    schemeRow = entry.schemeIndex
                    self.pztSum[schemeRow] += entry.tunerValue
                    self.pztList.append(entry.tunerValue)
                    self.angleList.append(entry.lockValue.asFloat)
                    self.schemeRowList.append(schemeRow)
                    self.count[schemeRow] += 1
                if self.version <4:
                    schemeStatus = entry.schemeStatus
                else:
                    schemeStatus = (entry.schemeStatusAndSchemeTableIndex >> 8) & 0xFF
                if (schemeStatus & ss_autogen.SchemeCompleteSingleModeBitMask) or \
                   (schemeStatus & ss_autogen.SchemeCompleteRepeatModeMask)or \
                   ((schemeStatus & ss_autogen.SchemeActiveBitMask) == 0 and (time.time()-self.startCollect)>30):
                    self.processResults = False
    
        def update(self,angles,laserIndex,FSR=None,nRefine=4):
            theta = numpy.array(angles,dtype='d')
            dtheta = numpy.diff(theta)
            m = numpy.mean(abs(dtheta))
            while True:
                r = numpy.round_(dtheta/m)
                good = numpy.nonzero(r)
                m1 = numpy.mean(dtheta[good]/r[good])
                if m == m1: break
                m = m1
            cr = numpy.zeros(len(theta),dtype='l')
            cr[1:] = numpy.cumsum(r)
            # cr contains FSR indices associated with WLM angles in theta
            # Sort these into ascending order and coalasce points with same index
            p = cr.argsort()
            cr = cr[p]
            theta = theta[p]
            cr,theta = coalascePoints(cr,theta)
            # Use interpolation to fill in calibration points so they are closer together than the spline knots
            waveNumbers = numpy.linspace(cr[0],cr[-1],nRefine*(cr[-1]-cr[0])+1)
            theta = linearInterp(cr,theta,waveNumbers)
            # Determine the cavity FSR if necessary
            if FSR == None:
                w = self.FilerRpc.AngleToWavenumber([float(th) for th in angles],laserIndex)["waveNumber"]
                p = calUtilities.bestFit(numpy.cumsum(r),w[1:],1)
                FSR = p.coeffs[0]
            waveNumbers *= FSR
            msg = "Free spectral range = %f" % (FSR,)
            print msg
            print>>self.op, msg
            msg = "Laser index (1-origin) = %d" % (laserIndex+1,)
            print msg
            print>>self.op, msg
            for i in range(50):
                self.FilerRpc.UpdateWlmCal([float(th) for th in theta],[float(w) for w in waveNumbers],1.0,laserIndex,0.1,True)
            self.FilerRpc.ReplaceOriginalWlmCal(laserIndex)
            return FSR
    
        def makeAndUploadScheme(self,thetaList,tempList,laserIndex,repeat,dwell):
            self.seq += 1
            fullFilename = os.path.join(self.tempDir,"calScheme%d.abs" % (self.seq,))
            baseScheme = 14
            lp = file(fullFilename,"w")
            msg = "Preparing scheme file: %s" % fullFilename
            print msg
            print>>self.op, msg
            print >>lp, repeat
            numEntries = len(thetaList)
            print >>lp, numEntries
            toks = 6 * ["0"]
            for i in range(numEntries):
                toks[0] = "%.4f" % (float(thetaList[i]),)
                toks[1] = "%d" % (dwell,)
                toks[2] = "%d" % (self.seq,)
                toks[3] = "%d" % (laserIndex,)
                toks[5] = "%.4f" % (float(tempList[i]),)
                print >>lp, " ".join(toks)
            lp.close()
            activeIndex = self.DriverRpc.rdDasReg("RD_ACTIVE_SCHEME_TABLE_INDEX_REGISTER")
            schemeIndex = baseScheme
            if schemeIndex == activeIndex:
                schemeIndex += 1
            self.DriverRpc.wrDasReg("RD_LOAD_SCHEME_TABLE_INDEX_REGISTER",schemeIndex)
            self.FilerRpc.UploadSchemeFile(fullFilename,1)
    

    def run(self):
        # Check that the driver can communicate
        try:
            print "Driver version: %s" % Driver.allVersions()
        except:
            raise ValueError,"Cannot communicate with driver, aborting"

        try:
            regVault = Driver.saveRegValues(["TUNER_SWEEP_RAMP_HIGH_REGISTER",
                                             "TUNER_SWEEP_RAMP_LOW_REGISTER",
                                             "TUNER_WINDOW_RAMP_HIGH_REGISTER",
                                             "TUNER_WINDOW_RAMP_LOW_REGISTER",
                                             "TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER",
                                             "TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER",
                                             "TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER",
                                             "TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER"
                                             ])
            self.op = file(time.strftime("CalibrateSystem_%Y%m%d_%H%M%S.txt",time.localtime()),"w")
            currentMean = 32768 # Center position
            rampAmpl = 17000    # Set to greater than an FSP
            ditherPeakToPeak = 3200
            self.setupRampMode(ditherPeakToPeak,currentMean,rampAmpl)
            print "Listening for 10s"
            time.sleep(10)
        finally:
            Driver.restoreRegValues(regVault)
            
            
    if 0:
        def run(self):
            # Get here after the specified measurement time
            try:
                # Open output file for results
                self.op = file(time.strftime("CalibrateSystem_%Y%m%d_%H%M%S.txt",time.localtime()),"w")
                currentMean = 51000
                self.setupRampMode(2500,currentMean,11500) # Start with a wide ramp
                self.RdResultClass = getRdResultClass(self.version)
                self.listener = Listener.Listener(None,BROADCAST_PORT_RDRESULTS,self.RdResultClass,self.resultsFilter)
                if len(sys.argv) > 1:
                    laserIndex = int(sys.argv[1]) - 1
                else:
                    laserIndex = int(raw_input("Laser index (1-origin)? ")) - 1
                self.seq = 0
                if len(sys.argv) > 2:
                    wcen = float(sys.argv[2])
                else:
                    wcen = float(raw_input("Center value of wavenumber? "))
                if len(sys.argv) > 3:
                    nsteps = int(sys.argv[3])
                else:
                    nsteps = int(raw_input("Number of steps on each side of center? "))
                # Ensure that we start with original calibration information
                self.FilerRpc.RestoreOriginalWlmCal(laserIndex)
                theta0 = self.FilerRpc.WavenumberToAngle(wcen,laserIndex)["angle"]
                # First make a fine scheme for determining the PZT sensitivity
                steps = range(-600,601)
                steps += range(600,-601,-1)
                dtheta = APPROX_FSR/50
                nRepeat = 3
                dwell = 2
                self.DriverRpc.wrDasReg("SPECTCNTRL_SCAN_MODE_REGISTER",ss_autogen.SPECTCNTRL_SingleScheme)
                thetaList = theta0 + numpy.array(steps,dtype='d')*dtheta
                tempList = self.FilerRpc.AngleToLaserTemperature([float(t) for t in thetaList],laserIndex)["laserTemperature"]
                self.clearLists()
    
                self.pztSum = numpy.zeros(len(tempList),dtype='d')
                self.count = numpy.zeros(len(tempList))
                self.makeAndUploadScheme(thetaList,tempList,laserIndex,nRepeat,dwell)
                self.processResults = True
                self.startCollect = time.time()
    
                print>>self.op, "Laser Index:       %d" % (laserIndex + 1,)
                print>>self.op, "Center wavenumber: %.3f" % (wcen,)
                print>>self.op, "Number of steps:   %d" % (nsteps,)
    
                msg = "Collecting data for PZT sensitivity measurement"
                print msg
                print>>self.op, msg
                self.FilerRpc.AcquireSpectrum()
    
                while self.processResults:
                    time.sleep(1.0)
                L = min(len(self.angleList),len(self.pztList),len(self.schemeRowList))
                self.angleList = numpy.array(self.angleList[L//nRepeat:L+1],'d')
                self.pztList = numpy.array(self.pztList[L//nRepeat:L+1],'d')
                self.schemeRowList = numpy.array(self.schemeRowList[L//nRepeat:L+1],'d')
    
                def pztcost(p,angle,pzt):
                    x = angle/p[0] - pzt/p[1]
                    c1 = numpy.std(x - numpy.floor(x))
                    c2 = numpy.std(x + 0.5 - numpy.floor(x+0.5))
                    return min(c1,c2)
    
                foptBest = 1e38
                for trialSens in [7000,8000,9000,10000,11000,12000,13000,14000,15000,16000,17000,18000,19000,20000,21000,22000]:
                    popt = fmin(pztcost,numpy.array([0.077,trialSens]),args=(self.angleList,self.pztList),maxiter=10000,maxfun=50000)
                    fopt = pztcost(popt,self.angleList,self.pztList)
                    if fopt < foptBest:
                        foptBest = fopt
                        poptBest = popt
    
                popt = poptBest
                fopt = foptBest
                msg = "Residual: %.3f" % (fopt,)
                print msg
                print>>self.op, msg
                msg = "Cavity FSR  (WLM radians):    %.5f" % (popt[0],)
                print msg
                print>>self.op, msg
                msg = "Sensitivity (digU/FSR): %.0f" % (popt[1],)
                print msg
                print>>self.op, msg
                self.FilerRpc.UpdatePztParameters(float(popt[1]))
                self.FilerRpc.UpdateAutocalParameters(-1,float(popt[0]))
                angleFSR = float(popt[0])
                pztSens = float(popt[1])
                steps = range(-nsteps,nsteps+1)
                steps += range(nsteps-1,-nsteps,-1)
                dtheta = angleFSR
                baseScheme = 14
                dwell = 10
                nRepeat = 1
                theta0 = self.FilerRpc.WavenumberToAngle(wcen,laserIndex)["angle"]
                seq = 0
                self.DriverRpc.wrDasReg("SPECTCNTRL_SCAN_MODE_REGISTER",ss_autogen.SPECTCNTRL_SingleScheme)
                thetaList = theta0 + numpy.array(steps,dtype='d')*dtheta
                tempList = self.FilerRpc.AngleToLaserTemperature([float(t) for t in thetaList],laserIndex)["laserTemperature"]
    
                repeat = 1
                dwell = 10
    
                for iter in range(10):
                    self.pztSum = numpy.zeros(len(tempList),dtype='d')
                    self.count = numpy.zeros(len(tempList))
                    self.makeAndUploadScheme(thetaList,tempList,laserIndex,repeat,dwell)
                    self.clearLists()
                    self.processResults = True
                    self.startCollect = time.time()
                    msg = "Starting spectrum acquisition"
                    print msg
                    print>>self.op, msg
                    self.FilerRpc.AcquireSpectrum()
                    while self.processResults:
                        time.sleep(1.0)
                    # Find mean of pzt values
                    good = self.count.nonzero()
                    self.pztSum[good] = self.pztSum[good]/self.count[good]
                    pztMean = float(numpy.mean(self.pztSum[good]))
                    sDev = numpy.std(self.pztSum[good]-pztMean)
                    msg = "Standard deviation: %.1f" % (sDev,)
                    print msg
                    print>>self.op, msg
                    pztMean = numpy.median(self.pztSum[good])
                    pztDev = self.pztSum[good] - pztMean
                    thetaList[good] = thetaList[good] - 5e-6*pztDev
                    if abs(currentMean-pztMean) > 0.5*pztSens:
                        currentMean = pztMean
                    self.setupRampMode(2500,currentMean,0.65*pztSens)
    
                fullPath = os.path.join(self.tempDir,"calScheme%d.abs" % (self.seq,))
                sp = file(fullPath,"r")
                nrepeat = int(getNextNonNullLine(sp).split()[0])
                numEntries = int(getNextNonNullLine(sp).split()[0])
                angleList = []
                for i in range(numEntries):
                    toks = getNextNonNullLine(sp).split()
                    angleList.append(float(toks[0]))
                sp.close()
                cavityFSR = float(self.update(angleList,laserIndex))
                msg = "Cavity FSR = %.6f" % (cavityFSR,)
                print msg
                print>>self.op, msg
                fname = time.strftime("WlmCalibration_%Y%m%d_%H%M%S.ini",time.localtime())
                newCalFile = os.path.join(os.getcwd(),fname)
                self.FilerRpc.SaveCalFile(newCalFile)
                msg = "New calibration file is: %s" % (newCalFile,)
                print msg
                print>>self.op, msg
                self.FilerRpc.UpdateAutocalParameters(-1,-1,-1,cavityFSR)
                fname = time.strftime("Master_%Y%m%d_%H%M%S.ini",time.localtime())
                newMasterFile = os.path.join(os.getcwd(),fname)
                self.FilerRpc.WriteIniFile(newMasterFile)
    
            finally:
                self.DriverRpc.restoreRegValues(regVault)

HELP_STRING = """CalibrateSystem.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./CalibrateSystem.ini"
-s                   number of steps on each side of center
-v                   specify virtual laser (1-origin) to calibrate
-w                   center wavenumber about which to calibrate
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:s:v:w:'
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
