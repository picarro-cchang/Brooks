#!/usr/bin/python
#
"""
File Name: RDFrequencyConverter.py
Purpose: Converts between WLM angle and frequencies using AutoCal structures

File History:
    30-Sep-2009  alex/sze  Initial version.
    02-Oct-2009  alex      Added RPC functions.
    09-Oct-2009  sze       Supporting new warm box calibration files and uploading of virtual laser parameters to DAS
    11-Oct-2009  sze       Added routines to support CalibrateSystem
    14-Oct-2009  sze       Added support for calibration rows in schemes
    16-Oct-2009  alex      Added .ini file and update active warmbox and hotbox calibration files
    20-Oct-2009  alex      Added functionality to handle scheme switch and update warmbox and hotbox calibration files
    21-Oct-2009  alex      Added calibration file paths to .ini file. Added RPC_setCavityLengthTuning() and RPC_setLaserCurrentTuning().
    22-Apr-2010  sze       Fixed non-updating of angle schemes when no calibration points are present
    20-Sep-2010  sze       Added pCalOffset parameter to RPC_loadWarmBoxCal for flight calibration
    24-Oct-2010  sze       Put scheme version number in high order bits of schemeVersionAndTable in ProcessedRingdownEntry type
Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "RDFrequencyConverter"

import sys
import getopt
import inspect
import shutil
import os
import Queue
import threading
import time
import datetime
import traceback
from numpy import *
from cStringIO import StringIO
from binascii import crc32

from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, Listener, Broadcaster
from Host.Common.SharedTypes import Singleton
from Host.Common.SchemeProcessor import Scheme
from Host.Common.SharedTypes import BROADCAST_PORT_RD_RECALC, BROADCAST_PORT_RDRESULTS
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER, RPC_PORT_ARCHIVER
from Host.Common.WlmCalUtilities import AutoCal
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
EventManagerProxy_Init(APP_NAME)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

MIN_SIZE = 30

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    APP_NAME, IsDontCareConnection = False)

Archiver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ARCHIVER,
                                    APP_NAME, IsDontCareConnection = True)
                                    
            
class CalibrationPoint(object):
    """Structure for collecting interspersed ringdowns in a scheme which are marked as calibration points."""
    def __init__(self):
        self.tunerVals = []
        self.thetaCalCos = []
        self.thetaCalSin = []
        self.laserTempVals = []
        self.tunerMed = None
        self.thetaCalMed = None
        self.laserTempMed = None
        self.vLaserNum = None
        self.count = 0

class SchemeBasedCalibrator(object):
    def __init__(self):
        self.currentCalSpectrum = {} # keys = schemeRows, values = CalibrationPoint objects
        self.schemeNum = None
        self.rdFreqConv = RDFrequencyConverter()
        self.calibrationDone = [False for i in range(interface.NUM_VIRTUAL_LASERS)]
        
    def clear(self):
        self.currentCalSpectrum.clear()
        self.schemeNum = None
    
    def isCalibrationDone(self,vLaserNumList):
        # Check if calibration has been done for the specified list of virtual lasers
        return [self.calibrationDone[vLaserNum-1] for vLaserNum in vLaserNumList]
    
    def clearCalibrationDone(self,vLaserNumList):
        # Clear calibration done flag for the specified list of virtual lasers
        for vLaserNum in vLaserNumList:
            self.calibrationDone[vLaserNum-1] = False
        
    def processCalPoint(self,entry):
        # For each calibration point received in the scheme, update the parameters associated with this point
        row = entry.schemeRow
        # At this stage entry.schemeVersionAndTable just has the scheme table information
        table = entry.schemeVersionAndTable
        if row not in self.currentCalSpectrum:
            self.currentCalSpectrum[row] = CalibrationPoint()
            if self.schemeNum is None:
                self.schemeNum = table
            else:
                if self.schemeNum != table:
                    Log("Scheme mismatch while processing calibration point",dict(expectedScheme=self.schemeNum,schemeFound=table),Level=2)
                    self.clear()
                    return
        calPoint = self.currentCalSpectrum[row]
        calPoint.count += 1
        calPoint.thetaCalCos.append(cos(entry.wlmAngle))
        calPoint.thetaCalSin.append(sin(entry.wlmAngle))
        calPoint.laserTempVals.append(entry.laserTemperature)
        calPoint.tunerVals.append(entry.tunerValue)
        calPoint.vLaserNum = 1 + ((entry.laserUsed >> 2) & 7)

    def calFailed(self,vLaserNum):
        scs = self.rdFreqConv.shortCircuitSchemes
        self.rdFreqConv.calFailed[vLaserNum-1] += 1
        self.rdFreqConv.calSucceeded[vLaserNum-1] = 0
        if self.rdFreqConv.calFailed[vLaserNum-1] >= int(scs['failureThreshold']):
            if Driver.getSpectCntrlMode() != interface.SPECT_CNTRL_SchemeMultipleNoRepeatMode:
                Driver.setMultipleNoRepeatScan()
                Log("Setting multiple scheme no repeat mode",dict(calSucceeded=self.rdFreqConv.calSucceeded,
                calFailed=self.rdFreqConv.calFailed))
        
    def calSucceeded(self,vLaserNum):
        scs = self.rdFreqConv.shortCircuitSchemes
        self.rdFreqConv.calFailed[vLaserNum-1] = 0
        self.rdFreqConv.calSucceeded[vLaserNum-1] += 1
        valid = (self.rdFreqConv.calSucceeded != 0)
        if all(self.rdFreqConv.calFailed==0) and all(self.rdFreqConv.calSucceeded[valid]>=int(scs['successThreshold'])):
            if Driver.getSpectCntrlMode() != interface.SPECT_CNTRL_SchemeMultipleMode:
                Driver.setMultipleScan()
                Log("Setting multiple scheme mode",dict(calSucceeded=self.rdFreqConv.calSucceeded,
                calFailed=self.rdFreqConv.calFailed))
    
    def processCalSpectrum(self):
        scs = self.rdFreqConv.shortCircuitSchemes
        d = self.currentCalSpectrum
        if len(d) < int(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","MIN_CALROWS")):
            return
        for row in d:
            # Find median WlmAngles, tuner values and laser temperatures
            #  N.B. We must deal with the sine and cosine parts separately
            b = d[row]
            assert(isinstance(b,CalibrationPoint))
            b.thetaCalMed = arctan2(median(b.thetaCalSin),median(b.thetaCalCos))
            b.tunerMed = median(b.tunerVals)
            b.laserTempMed = median(b.laserTempVals)
        # Process the data one laser at a time
        calDone = False
        for vLaserNum in range(1,interface.NUM_VIRTUAL_LASERS+1):
            rows = [k for k in d if (d[k].vLaserNum == vLaserNum)] # Rows involving this virtual laser
            if rows:
                laserTemp = array([d[k].laserTempMed for k in rows])
                thetaCal  = array([d[k].thetaCalMed  for k in rows]) # These angles may not be on the correct revolution
                thetaHat  = self.rdFreqConv.RPC_laserTemperatureToAngle(vLaserNum,laserTemp)
                thetaCal  +=  2*pi*floor((thetaHat-thetaCal)/(2*pi) + 0.5) # Rotate the angles according to laser temperature
                tuner     = array([d[k].tunerMed for k in rows])
                # Ideally, tuner values should be close together. We check for large jumps and forgo calibration in such cases
                jump = abs(diff(tuner)).max()
                if jump > float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","MAX_JUMP")):
                    Log("Calibration not done, maximum jump between calibration rows: %.1f" % (jump,))
                    if scs: self.calFailed(vLaserNum)
                    continue
                count = array([d[k].count for k in rows])
                tunerMean = float(sum(tuner*count))/sum(count)
                tunerDev  = tuner - tunerMean
                # Use the median to center the tuner, for robustness
                tunerCenter = float(self.medianHist(tuner,count,useAverage=False))
                # Center the tuner ramp waveform about the median tuner value at the calibration rows
                #  Since this can get stuck behind scheme uploads due to Driver command serialization,
                #  we'll do it in a separate thread
                tunerCenteringThread = threading.Thread(target = self.centerTuner, args=(tunerCenter,))
                tunerCenteringThread.setDaemon(True)
                tunerCenteringThread.start()

                # Calculate the shifted WLM angles which correspond to exact FSR separation
                #  The ADJUST_FACTOR is an underestimate of the WLM angle shift corresponding to a digitizer
                #  unit of tuner. This provides a degree of under-relaxation and filtering.
                # print thetaCal
                thetaShifted = thetaCal - (float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","ADJUST_FACTOR")) * tunerDev)
                # Now use the information in scheme for updating the calibration
                perm = thetaShifted.argsort()
                thetaShifted = thetaShifted[perm]
                dtheta = diff(thetaShifted)
    
                # Ensure that the differences between the WLM angles at the calibration rows are close to multiples of the 
                #  FSR before we do the calibration. This prevents calibrations from occurring if the pressure is changing, etc.
                m = round_(dtheta / float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","APPROX_WLM_ANGLE_PER_FSR")))
                anglePerFsr = mean(dtheta[m == 1])
                m = round_(dtheta/anglePerFsr) # Quantize m to indicate multiples of the FSR
                devs = abs(dtheta/anglePerFsr - m)
                offGrid = devs.max()
                if offGrid > float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","MAX_OFFGRID")):
                    Log("Calibration not done, PZT sdev = %.1f, offGrid parameter = %.2f, fraction>0.25 = %.2f" % (std(tunerDev),offGrid,sum(devs>0.25)/float(len(devs))))
                    if scs: self.calFailed(vLaserNum)
                else:
                    #Update the live copy of the polar<->freq coefficients...
                    waveNumberSetpoints = zeros(len(rows),dtype=float) #pre-allocate space
                    for i,calRow in enumerate(rows):
                        waveNumberSetpoints[i] = self.rdFreqConv.freqScheme[self.schemeNum].setpoint[calRow]
                    waveNumberSetpoints = waveNumberSetpoints[perm] #sorts in the same way that thetaShifted was
                    #Calculate number of calibration points at each FSR, so they may be weighted properly
                    weights = self.calcWeights(cumsum(concatenate(([0],m))))
                    #Now do the actual updating of the conversion coefficients...
                    self.rdFreqConv.RPC_updateWlmCal(vLaserNum,thetaShifted,waveNumberSetpoints,weights,
                                                     float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","RELAX")),True,
                                                     float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","RELAX_DEFAULT")),      
                                                     float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","RELAX_ZERO"))) 
                    self.calibrationDone[vLaserNum-1] = True
                    stdTuner = std(tunerDev)
                    if scs: 
                        if stdTuner>float(scs['maxTunerStandardDeviation']): self.calFailed(vLaserNum)
                        else: self.calSucceeded(vLaserNum)
                    Log("WLM Cal for virtual laser %d done, angle per FSR = %.4g, PZT sdev = %.1f" % (vLaserNum,anglePerFsr,stdTuner))
                    
                    # Check if it's time to update and archive the warmbox calibration file
                    if self.rdFreqConv.timeToUpdateWarmBoxCal():
                        Log("Time to update warm box calibration file")
                        #  we'll do it in a separate thread in case it takes too long to write the new calibration file to disk
                        updateWarmBoxCalThread = threading.Thread(target = self.updateWarmBoxCal, args=(self.rdFreqConv.warmBoxCalFilePathActive,))
                        updateWarmBoxCalThread.setDaemon(True)
                        updateWarmBoxCalThread.start()
    
    def updateWarmBoxCal(self,warmBoxCalFilePathActive):
        self.rdFreqConv.resetWarmBoxCalTime()
        self.rdFreqConv.RPC_updateWarmBoxCal(warmBoxCalFilePathActive)
        
    def centerTuner(self,tunerCenter):
        self.rdFreqConv.RPC_centerTuner(tunerCenter)
        
    def calcWeights(self,x):
        """Calculate weights associated with integer array x. Elements of x must be sorted. 
        The weight associated with x[i] is the number of times x[i] appears in the array, 
        and this is placed in the result array w[i]."""
        w = zeros(x.shape,int_)
        kprev = 0
        c = 1
        for k in range(1,len(x)):
            if x[k] != x[k-1]:
                w[kprev:k] = c
                kprev = k
                c = 1
            else:
                c += 1
        w[kprev:] = c
        return w
    
    def medianHist(self,values,freqs,useAverage=True):
        """Compute median from arrays of values and frequencies. The array of values need not be 
        in ascending order"""
        if len(values) != len(freqs):
            raise ValueError("Lengths of values and freqs must be equal in medianHist")
        perm = argsort(values)
        csum = cumsum(freqs[perm])
        if useAverage and (csum[-1] % 2 == 0):
            mid2 = csum[-1]/2
            mid1 = mid2 - 1
            return 0.5*(values[perm[sum(mid1 >= csum)]]+values[perm[sum(mid2 >= csum)]])
        else:
            mid = (csum[-1]-1)/2
            return values[perm[sum(mid >= csum)]]
                                         
class RpcServerThread(threading.Thread):
    def __init__(self, rpcServer, exitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.rpcServer = rpcServer
        self.exitFunction = exitFunction
    def run(self):
        self.rpcServer.serve_forever()
        try: #it might be a threading.Event
            self.exitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")

def validateChecksum(fname):
    fp = file(fname,'rb')
    try:
        calStr = fp.read()
        cPos = calStr.find("#checksum=")
        if cPos<0:
            raise ValueError("No checksum in file")
        else:
            try:
                csum1 = int(calStr[cPos+10:])
                csum2 = crc32(calStr[:cPos], 0)
            except Exception, e:
                raise ValueError("Error calculating checksum %r" % e)
            if csum1 == csum2:
                return "OK"
            else:
                raise ValueError("Bad checksum")
    finally:
        fp.close()
            
class RDFrequencyConverter(Singleton):
    initialized = False
    def __init__(self, configPath=None):        
        if not self.initialized:
            if configPath != None:
                # Read from .ini file
                cp = CustomConfigObj(configPath)
                basePath = os.path.split(configPath)[0]
                self.saveWlmHistPeriod_s = cp.getfloat("MainConfig", "saveWlmHistPeriod_s", "120")
                self.wbCalUpdatePeriod_s = cp.getfloat("MainConfig", "wbCalUpdatePeriod_s", "1800")
                self.hbCalUpdatePeriod_s = cp.getfloat("MainConfig", "hbCalUpdatePeriod_s", "1800")
                self.wbArchiveGroup = cp.get("MainConfig", "wbArchiveGroup", "WBCAL")
                self.hbArchiveGroup = cp.get("MainConfig", "hbArchiveGroup", "HBCAL")
                self.warmBoxCalFilePathActive = os.path.abspath(os.path.join(basePath, cp.get("CalibrationPath", "warmboxCalActive", "")))
                self.warmBoxCalFilePathFactory = os.path.abspath(os.path.join(basePath, cp.get("CalibrationPath", "warmboxCalFactory", "")))
                self.hotBoxCalFilePathActive = os.path.abspath(os.path.join(basePath, cp.get("CalibrationPath", "hotboxCalActive", "")))
                self.hotBoxCalFilePathFactory = os.path.abspath(os.path.join(basePath, cp.get("CalibrationPath", "hotboxCalFactory", "")))
                if "ShortCircuitSchemes" in cp:
                    self.shortCircuitSchemes = dict(cp["ShortCircuitSchemes"])
                else:
                    self.shortCircuitSchemes = {}
            else:
                raise ValueError("Configuration file must be specified to initialize RDFrequencyConverter")
        
            self.numLasers = interface.NUM_VIRTUAL_LASERS
            self.rdQueue = Queue.Queue()
            self.rdQueueMaxLevel = 0
            self.rdProcessedCache = []
            self.rpcThread = None
            self._shutdownRequested = False
            self.freqConvertersLoaded = False
            # Ensure no ringdowns are being collected when the RDFrequencyConverter starts up
            Driver.stopScan()
            self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_FREQ_CONVERTER),
                                                    ServerName = "FrequencyConverter",
                                                    ServerDescription = "Frequency Converter for CRDS hardware",
                                                    threaded = True)
            #Register the rpc functions...
            for s in dir(self):
                attr = self.__getattribute__(s)
                if callable(attr) and s.startswith("RPC_") and (not inspect.isclass(attr)):
                    self.rpcServer.register_function(attr, NameSlice = 4)
                    
            self.processedRdBroadcaster = Broadcaster.Broadcaster(
                                        port=BROADCAST_PORT_RD_RECALC,
                                        name="Ringdown frequency converter broadcaster",logFunc = Log)
            
            self.freqScheme = {}
            self.angleScheme = {}
            self.isAngleSchemeConverted = {}
            self.freqConverter = {}
            self.warmBoxCalFilePath = ""
            self.hotBoxCalFilePath = ""
            self.hotBoxCal = None
            self.initialized = True
            self.cavityLengthTunerAdjuster = None
            self.laserCurrentTunerAdjuster = None
            self.lastSchemeCount = -1
            self.sbc = SchemeBasedCalibrator()
            self.dthetaMax = None 
            self.dtempMax = None
            self.tuningMode = None
            self.schemeMgr = None
            self.warmBoxCalUpdateTime = 0
            self.hotBoxCalUpdateTime = 0
            self.calFailed = zeros(interface.NUM_VIRTUAL_LASERS)
            self.calSucceeded = zeros(interface.NUM_VIRTUAL_LASERS)
            
    def rdFilter(self,entry):
        # Figure if we finished a scheme and whether we should process cal points in the last scheme
        if (entry.status & interface.RINGDOWN_STATUS_SequenceMask) != self.lastSchemeCount:
            if self.sbc.currentCalSpectrum:
                self.sbc.processCalSpectrum()
            # We must unconditionally recompile the scheme files whether or not
            #  there is a cal spectrum, in order to account for changing WLM offset
            if self.schemeMgr:
                schemeMgrUpdateThread = threading.Thread(target=self.schemeMgr.update)
                schemeMgrUpdateThread.setDaemon(True)
                schemeMgrUpdateThread.start()
            self.sbc.clear()
            self.lastSchemeCount = (entry.status & interface.RINGDOWN_STATUS_SequenceMask)
        # Check if this is a calibration row and process it accordingly
        if entry.subschemeId & interface.SUBSCHEME_ID_IsCalMask:
            rowNum = entry.schemeRow
            # The scheme version has not yet been placed in schemeVersionAndTable 
            schemeTable = entry.schemeVersionAndTable
            angleError = mod(entry.wlmAngle - self.angleScheme[schemeTable].setpoint[rowNum],2*pi)
            tempError  = entry.laserTemperature - self.angleScheme[schemeTable].laserTemp[rowNum]
            if min(angleError,2*pi-angleError) < self.dthetaMax and abs(tempError) < self.dtempMax:
                # The spectral point is close to the setpoint
                self.sbc.processCalPoint(entry)
        return entry
    
    def run(self):
        # Start the thread to save WLM history into database
        saveWlmThread = threading.Thread(target = self.runSaveWlmHistory)
        saveWlmThread.setDaemon(True)
        saveWlmThread.start()
        
        # Start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.RPC_shutdown)
        self.rpcThread.start()
        startTime = time.time()
        timeout = 0.1
        while not self._shutdownRequested:
            try:
                rdQueueSize = self.rdQueue.qsize()
                if rdQueueSize > self.rdQueueMaxLevel:
                    self.rdQueueMaxLevel = rdQueueSize
                    Log("rdQueueSize reaches new peak level %d" % self.rdQueueMaxLevel)
                self.tuningMode = Driver.rdDasReg("ANALYZER_TUNING_MODE_REGISTER")
                if rdQueueSize > MIN_SIZE or time.time()-startTime > timeout:
                    self._batchConvert()
                    startTime = time.time()
                else:
                    time.sleep(0.02)
                    continue
                while self.rdProcessedCache:
                    try:
                        rdProcessedData = self.rdProcessedCache.pop(0)
                        self.processedRdBroadcaster.send(StringPickler.ObjAsString(rdProcessedData))   
                    except:
                        break
            except:
                type,value,trace = sys.exc_info()
                Log("Error: %s: %s" % (str(type),str(value)),Verbose=traceback.format_exc(),Level=3)
                while not self.rdQueue.empty(): self.rdQueue.get(False)
                self.rdProcessedCache = []
                time.sleep(0.02)
        Log("RD Frequency Converter RPC handler shut down")

    def _batchConvert(self):
        """Convert WLM angles and laser temperatures to wavenumbers in a vectorized way, using
        wlmAngleAndlaserTemperature2WaveNumber"""

        if self.rdProcessedCache:
            raise RuntimeError("_batchConvert called while cache is not empty")
        wlmAngle = [[] for i in range(self.numLasers)]
        laserTemperature = [[] for i in range(self.numLasers)]
        cacheIndex = [[] for i in range(self.numLasers)]
        # Get data from the queue into the cache
        index = 0
        while not self.rdQueue.empty():
            try:
                rdProcessedData = interface.ProcessedRingdownEntryType()
                rdData = self.rdQueue.get(False)
                for name,ctype in rdData._fields_:
                    if name != "padToCacheLine":
                        setattr(rdProcessedData, name, getattr(rdData,name))
                self.rdProcessedCache.append(rdProcessedData)
                vLaserNum = 1 + ((rdData.laserUsed >> 2) & 0x7) # 1-based virtual laser number
                wlmAngle[vLaserNum-1].append(rdData.wlmAngle)
                laserTemperature[vLaserNum-1].append(rdData.laserTemperature)
                cacheIndex[vLaserNum-1].append(index)
                index += 1
            except Queue.Empty:
                break
        # Do the angle to wavenumber conversions for each available laser
        for vLaserNum in range(1,self.numLasers+1):
            if cacheIndex[vLaserNum-1]: # There are angles to convert for this laser
                self._assertVLaserNum(vLaserNum)
                fc = self.freqConverter[vLaserNum-1]
                waveNo = fc.thetaCalAndLaserTemp2WaveNumber(array(wlmAngle[vLaserNum-1]), array(laserTemperature[vLaserNum-1]))
                for i,w in enumerate(waveNo):
                    index = cacheIndex[vLaserNum-1][i]
                    rdProcessedData = self.rdProcessedCache[index]
                    rdProcessedData.waveNumber = w
                    # At this point schemeVersionAndTable only has the scheme table
                    schemeTable = rdProcessedData.schemeVersionAndTable
                    if schemeTable in self.freqScheme:
                        freqScheme = self.freqScheme[schemeTable]
                        # Here we prepend the version to schemeVersionAndTable
                        rdProcessedData.schemeVersionAndTable = schemeTable | (freqScheme.version << interface.SCHEME_VersionShift)
                        schemeRow = rdProcessedData.schemeRow
                        rdProcessedData.waveNumberSetpoint = freqScheme.setpoint[schemeRow]
                        rdProcessedData.extra1 = freqScheme.extra1[schemeRow]
                        rdProcessedData.extra2 = freqScheme.extra2[schemeRow]
                        rdProcessedData.extra3 = freqScheme.extra3[schemeRow]
                        rdProcessedData.extra4 = freqScheme.extra4[schemeRow]
                    else:
                        rdProcessedData.waveNumberSetpoint = 0
                        
    def _assertVLaserNum(self, vLaserNum):
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
    
    def runSaveWlmHistory(self):
        while True:
            self._saveWlmHistory()
            #Log("WLM history saved in database")
            time.sleep(self.saveWlmHistPeriod_s)
            
    def _saveWlmHistory(self):
        """Save WLM history to database"""
        for i in self.freqConverter:
            try:
                ac = self.freqConverter[i]
                if ac is not None:
                    vLaserNum = i+1
                    wlmOffset = ac.offset
                    deltaCoeffs = ac.coeffs - ac.coeffsOrig
                    valMin = deltaCoeffs.min()
                    valMax = deltaCoeffs.max()
                    freqMin = ac.sLinear[1] + deltaCoeffs.argmin()*ac.sLinear[0]
                    freqMax = ac.sLinear[1] + deltaCoeffs.argmax()*ac.sLinear[0]
                    timestamp = Driver.hostGetTicks()
                    wlmHist = (timestamp,vLaserNum,wlmOffset,freqMin,valMin,freqMax,valMax,)
                    Driver.saveWlmHist(wlmHist)
            except:
                pass
                
    def resetWarmBoxCalTime(self):
        self.warmBoxCalUpdateTime = Driver.hostGetTicks()
        
    def timeToUpdateWarmBoxCal(self):
        return (Driver.hostGetTicks() - self.warmBoxCalUpdateTime) > (self.wbCalUpdatePeriod_s*1000)

    def resetHotBoxCalTime(self):
        self.hotBoxCalUpdateTime = Driver.hostGetTicks()
        
    def timeToUpdateHotBoxCal(self):
        return (Driver.hostGetTicks() - self.hotBoxCalUpdateTime) > (self.hbCalUpdatePeriod_s*1000)
    
    def RPC_getShortCircuitSchemeStatus(self):
        """Returns True if a nonempty [ShortCircuitSchemes] section is in this INI file. When this is True,
        sequences start with the spectrum collector in SchemeMultipleNoRepeatMode, rather than in
        SchemeMultipleMode"""
        return len(self.shortCircuitSchemes)>0
        
    def RPC_configSchemeManager(self, schemeDict, schemeSeq):
        self.schemeMgr = SchemeManager(schemeDict, schemeSeq)
        self.schemeMgr.startup()
        
    def RPC_angleToLaserTemperature(self,vLaserNum,angles):
        self._assertVLaserNum(vLaserNum)
        return self.freqConverter[vLaserNum-1].thetaCal2LaserTemp(angles)

    def RPC_angleToWaveNumber(self,vLaserNum,angles):
        self._assertVLaserNum(vLaserNum)
        return self.freqConverter[vLaserNum-1].thetaCal2WaveNumber(angles)

    def RPC_setCavityLengthTuning(self):
        """ Set the instrument to use cavity length tuning, and load up DAS registers appropriately """
        Driver.wrDasReg("ANALYZER_TUNING_MODE_REGISTER", interface.ANALYZER_TUNING_CavityLengthTuningMode)
        self.tuningMode = interface.ANALYZER_TUNING_CavityLengthTuningMode
        self.cavityLengthTunerAdjuster.setTunerRegisters()

    def RPC_setLaserCurrentTuning(self):
        """ Set the instrument to use laser current tuning, and load up DAS registers appropriately """
        Driver.wrDasReg("ANALYZER_TUNING_MODE_REGISTER", interface.ANALYZER_TUNING_LaserCurrentTuningMode)
        self.tuningMode = interface.ANALYZER_TUNING_LaserCurrentTuningMode
        self.laserCurrentTunerAdjuster.setTunerRegisters(centerValue=32768)
        
    def RPC_setFsrHoppingTuning(self):
        """ Set the instrument to use FSR Hopping tuning, and load up DAS registers appropriately """
        Driver.wrDasReg("ANALYZER_TUNING_MODE_REGISTER", interface.ANALYZER_TUNING_FsrHoppingTuningMode)
        self.tuningMode = interface.ANALYZER_TUNING_FsrHoppingTuningMode
        
    def RPC_centerTuner(self,tunerCenter):
        if self.tuningMode == interface.ANALYZER_TUNING_CavityLengthTuningMode:
            self.cavityLengthTunerAdjuster.setTunerRegisters(tunerCenter)
        elif self.tuningMode == interface.ANALYZER_TUNING_LaserCurrentTuningMode:
            self.laserCurrentTunerAdjuster.setTunerRegisters(32768)

    def RPC_clearCalibrationDone(self,vLaserNumList):
        # Clear calibration done flags for the specified list of virtual lasers
        return self.sbc.clearCalibrationDone(vLaserNumList)
            
    def RPC_convertScheme(self, schemeNum):
        # Convert scheme from frequency (wave number) to angle
        scheme = self.freqScheme[schemeNum]
        angleScheme = self.angleScheme[schemeNum]
        numEntries = scheme.numEntries
        dataByLaser = {}
        for i in xrange(numEntries):
            vLaserNum = scheme.virtualLaser[i] + 1
            waveNum = float(scheme.setpoint[i])
            if vLaserNum not in dataByLaser:
                dataByLaser[vLaserNum] = ([],[])
            dataByLaser[vLaserNum][0].append(i)
            dataByLaser[vLaserNum][1].append(waveNum)
        for vLaserNum in dataByLaser:
            self._assertVLaserNum(vLaserNum)
            fc = self.freqConverter[vLaserNum-1]
            waveNum = array(dataByLaser[vLaserNum][1])
            wlmAngle = fc.waveNumber2ThetaCal(waveNum)
            laserTemp = fc.thetaCal2LaserTemp(wlmAngle)
            for j,i in enumerate(dataByLaser[vLaserNum][0]):
                angleScheme.setpoint[i] = wlmAngle[j]
                angleScheme.laserTemp[i]= laserTemp[j]
        self.isAngleSchemeConverted[schemeNum] = True

    def RPC_getHotBoxCalFilePath(self):
        return self.hotBoxCalFilePath

    def RPC_getHotBoxCalParam(self,secName,optName):
        return self.hotBoxCal[secName][optName]
    
    def RPC_getWarmBoxCalFilePath(self):
        return self.warmBoxCalFilePath
    
    def RPC_isCalibrationDone(self,vLaserNumList):
        # Check if calibration has been done for the specified list of virtual lasers
        return self.sbc.isCalibrationDone(vLaserNumList)
    
    def RPC_laserTemperatureToAngle(self,vLaserNum,laserTemperatures):
        self._assertVLaserNum(vLaserNum)
        return self.freqConverter[vLaserNum-1].laserTemp2ThetaCal(laserTemperatures)
    
    def RPC_loadHotBoxCal(self, hotBoxCalFilePath=""):
        self.hotBoxCalUpdateTime = Driver.hostGetTicks()
        if hotBoxCalFilePath != "":
            self.hotBoxCalFilePathActive = os.path.abspath(hotBoxCalFilePath)
        if os.path.isfile(self.hotBoxCalFilePathActive):
            # Need to run checksum on the active one. If failed, factory version will be used.
            # Need to be implemented!
            # Here assume checksum has passed
            self.hotBoxCalFilePath = self.hotBoxCalFilePathActive
        else:
            self.hotBoxCalFilePath = self.hotBoxCalFilePathFactory
            
        self.hotBoxCal = CustomConfigObj(self.hotBoxCalFilePath)
        if "AUTOCAL" not in self.hotBoxCal:
            raise ValueError("No AUTOCAL section in hot box calibration.")
        if ("CAVITY_LENGTH_TUNING" not in self.hotBoxCal) and \
           ("LASER_CURRENT_TUNING" not in self.hotBoxCal):
            raise ValueError("Hot box calibration must contain at least one of CAVITY_LENGTH_TUNING or LASER_CURRENT_TUNING sections.")
        if "CAVITY_LENGTH_TUNING" in self.hotBoxCal:
            self.cavityLengthTunerAdjuster = TunerAdjuster("CAVITY_LENGTH_TUNING")
        else:
            self.cavityLengthTunerAdjuster = None
        if "LASER_CURRENT_TUNING" in self.hotBoxCal:
            self.laserCurrentTunerAdjuster = TunerAdjuster("LASER_CURRENT_TUNING")
        else:
            self.laserCurrentTunerAdjuster = None
        self.dthetaMax = self.hotBoxCal["AUTOCAL"]["MAX_ANGLE_TARGETTING_ERROR"]
        self.dtempMax  = self.hotBoxCal["AUTOCAL"]["MAX_TEMP_TARGETTING_ERROR"]
        # Set up the PZT scaling register
        if "PZT_SCALE_FACTOR" in self.hotBoxCal["CAVITY_LENGTH_TUNING"]:
            pztScale = self.hotBoxCal["CAVITY_LENGTH_TUNING"]["PZT_SCALE_FACTOR"]
        else:
            pztScale = 0xFFFF
        Driver.wrFPGA("FPGA_SCALER","SCALER_SCALE1",int(pztScale))
        # Set up the PZT_INCR_PER_CAVITY_FSR register
        fsr = self.hotBoxCal["CAVITY_LENGTH_TUNING"]["FREE_SPECTRAL_RANGE"]
        Driver.wrDasReg("PZT_INCR_PER_CAVITY_FSR",float(fsr))
        
        return "OK"
        
    def RPC_loadWarmBoxCal(self, warmBoxCalFilePath="",pCalOffset=None):
        # Loads the specified warm box calibration file (or the default if not specified)
        #  into the analyzer. If pCalOffset is specified, this is used to force a constant
        #  angle offset for all virtual lasers so that the coefficients for pressure 
        #  calibration may be determined
        
        # When an empty file name is passed for warmBoxCalFilePath,
        #  The active file path is checked to see if it exists. If so, its checksum is verified.
        #  If the active file does not exist or if the checksum is bad, the factory file is used.
        #
        # When a non-empty file name is passed for warmBoxCalFilePath,
        #  Checksums are ignored and the specified file is used unconditionally. Any errors in the
        #   file or the non-existence of the file will cause an exception. The active file name is
        
        self.warmBoxCalUpdateTime = Driver.hostGetTicks()
        if warmBoxCalFilePath == "":
            if os.path.isfile(self.warmBoxCalFilePathActive):
                try:
                    validateChecksum(self.warmBoxCalFilePathActive)
                    self.warmBoxCalFilePath = self.warmBoxCalFilePathActive
                except:
                    Log('Bad checksum in active warm box calibration file, using factory file',Level = 2)
                    self.warmBoxCalFilePath = self.warmBoxCalFilePathFactory
            else:
                Log('No active warm box calibration file, using factory file',Level = 0)
                self.warmBoxCalFilePath = self.warmBoxCalFilePathFactory
        else:
            self.warmBoxCalFilePath = os.path.abspath(warmBoxCalFilePath)
                     
        # Load up the frequency converters for each laser in the DAS...
        ini = CustomConfigObj(self.warmBoxCalFilePath)
        for vLaserNum in range(1, self.numLasers + 1): # N.B. In AutoCal, laser indices are 1 based
            ac = AutoCal()
            self.freqConverter[vLaserNum-1] = ac.loadFromIni(ini, vLaserNum)
            # Send the virtual laser information to the DAS
            paramSec = "VIRTUAL_PARAMS_%d" % vLaserNum
            if paramSec in ini:
                p = ini[paramSec]
                aLaserNum = int(ini["LASER_MAP"]["ACTUAL_FOR_VIRTUAL_%d" % vLaserNum])
                laserParams = { 'actualLaser':     aLaserNum-1, 
                                'ratio1Center':    float(p['RATIO1_CENTER']),
                                'ratio1Scale':     float(p['RATIO1_SCALE']),
                                'ratio2Center':    float(p['RATIO2_CENTER']),
                                'ratio2Scale':     float(p['RATIO2_SCALE']),
                                'phase':           float(p['PHASE']),
                                'tempSensitivity': float(p['TEMP_SENSITIVITY']),
                                'calTemp':         float(p['CAL_TEMP']),
                                'calPressure':     float(p['CAL_PRESSURE']),
                                'pressureC0':      float(p['PRESSURE_C0']),
                                'pressureC1':      float(p['PRESSURE_C1']),
                                'pressureC2':      float(p['PRESSURE_C2']),
                                'pressureC3':      float(p['PRESSURE_C3'])}
                if pCalOffset is not None:
                    laserParams['calPressure'] = 760.0
                    laserParams['pressureC0'] = pCalOffset
                    laserParams['pressureC1'] = 0.0
                    laserParams['pressureC2'] = 0.0
                    laserParams['pressureC3'] = 0.0
                Driver.wrVirtualLaserParams(vLaserNum,laserParams)
        # Start the ringdown listener only once there are frequency converters available to do the conversion
        if not self.freqConvertersLoaded:
            self.rdListener = Listener.Listener(self.rdQueue,
                                        BROADCAST_PORT_RDRESULTS,
                                        interface.RingdownEntryType,
                                        streamFilter = self.rdFilter,
                                        retry = True,
                                        name = "Ringdown frequency converter listener",logFunc = Log)
            self.freqConvertersLoaded = True
        return "OK"
        
    def RPC_replaceOriginalWlmCal(self,vLaserNum):
        # Copy current spline coefficients to original coefficients
        self._assertVLaserNum(vLaserNum)
        self.freqConverter[vLaserNum-1].replaceOriginal()

    def RPC_restoreOriginalWlmCal(self,vLaserNum):
        # Replace current spline coefficients with original spline coefficients
        self._assertVLaserNum(vLaserNum)
        self.freqConverter[vLaserNum-1].replaceCurrent()

    def RPC_ignoreSpline(self,vLaserNum):
        # Do not use cubic spline corrections for angle to frequency transformations for virtual laser vLaserNum
        if (vLaserNum-1 in self.freqConverter) and self.freqConverter[vLaserNum-1] is not None:
            self.freqConverter[vLaserNum-1].ignoreSpline = True
        
    def RPC_useSpline(self,vLaserNum):
        # Do use cubic spline corrections for angle to frequency transformations for virtual laser vLaserNum
        if (vLaserNum-1 in self.freqConverter) and self.freqConverter[vLaserNum-1] is not None:
            self.freqConverter[vLaserNum-1].ignoreSpline = False
        
    def RPC_setHotBoxCalParam(self,secName,optName,optValue):
        self.hotBoxCal[secName][optName] = optValue
        if self.timeToUpdateHotBoxCal():
            Log("Time to update hot box calibration file")
            self.RPC_updateHotBoxCal(self.hotBoxCalFilePathActive)
            self.resetHotBoxCalTime()

    def RPC_getWlmOffset(self, vLaserNum):
        """Fetches the offset in the WLM calibration. vLaserNum is 1-based.
        Returns offset in wavenumbers.
        """
        self._assertVLaserNum(vLaserNum)
        return self.freqConverter[vLaserNum-1].getOffset()

    def RPC_setWlmOffset(self, vLaserNum, offset):
        """Updates the offset in the WLM calibration by the specified value.
        vLaserNum is 1-based. offset is in wavenumbers.
        """
        self._assertVLaserNum(vLaserNum)
        self.freqConverter[vLaserNum-1].setOffset(offset)
        
    def RPC_shutdown(self):
        self._shutdownRequested = True
        
    def RPC_updateHotBoxCal(self,fileName=None):
        """
        Write calibration back to the file with a new checksum.
        """
        # Archive the current HotBoxCal first (add timestamp to the filename too)
        timeStamp = datetime.datetime.today().strftime("%Y%m%d_%H%M%S")
        hotBoxCalFilePathWithTime = self.hotBoxCalFilePath.replace(".ini", "_%s.ini" % timeStamp)
        shutil.copy2(self.hotBoxCalFilePath, hotBoxCalFilePathWithTime)
        Archiver.ArchiveFile(self.hbArchiveGroup, hotBoxCalFilePathWithTime, True)
        Log("Archived %s" % hotBoxCalFilePathWithTime)
        
        fp = None
        if self.hotBoxCal is None:
            raise ValueError("Hot box calibration has not been loaded")
        try:
            # self.hotBoxCal["AUTOCAL"]["CAVITY_FSR"] = self.cavityFsr
            self.hotBoxCal["timestamp"] = Driver.hostGetTicks()
            calStrIO = StringIO()
            self.hotBoxCal.write(calStrIO)
            calStr = calStrIO.getvalue()
            calStr = calStr[:calStr.find("#checksum=")]
            checksum = crc32(calStr, 0)
            calStr += "#checksum=%d" % checksum
            if fileName is not None:
                self.hotBoxCalFilePath = fileName
            fp = file(self.hotBoxCalFilePath, "wb")
            fp.write(calStr)
        finally:
            calStrIO.close()
            if fp is not None: fp.close()
    
    def RPC_updateWarmBoxCal(self,fileName=None):
        """
        Write calibration back to the file with a new checksum.
        """
        # Archive the current WarmBoxCal firstadd timestamp to the filename too)
        timeStamp = datetime.datetime.today().strftime("%Y%m%d_%H%M%S")
        warmBoxCalFilePathWithTime = self.warmBoxCalFilePath.replace(".ini", "_%s.ini" % timeStamp)
        shutil.copy2(self.warmBoxCalFilePath, warmBoxCalFilePathWithTime)
        Archiver.ArchiveFile(self.wbArchiveGroup, warmBoxCalFilePathWithTime, True)
        Log("Archived %s" % warmBoxCalFilePathWithTime)
        
        fp = None
        cp = CustomConfigObj(self.warmBoxCalFilePath)
        for i in self.freqConverter.keys():
            ac = self.freqConverter[i]
            if ac is not None:
                ac.updateIni(cp, i+1) # Note: In Autocal1, laser indices are 1 based
        try:
            cp["timestamp"] = Driver.hostGetTicks()
            calStrIO = StringIO()
            cp.write(calStrIO)
            calStr = calStrIO.getvalue()
            calStr = calStr[:calStr.find("#checksum=")]
            checksum = crc32(calStr, 0)
            calStr += "#checksum=%d" % checksum
            if fileName is not None:
                self.warmBoxCalFilePath = fileName
            fp = file(self.warmBoxCalFilePath, "wb")
            fp.write(calStr)
        finally:
            calStrIO.close()
            if fp is not None: fp.close()

    def RPC_updateWlmCal(self,vLaserNum,thetaCal,waveNumbers,weights,relax=5e-3,relative=True,relaxDefault=5e-3,relaxZero=5e-5):
        """Updates the wavelength monitor calibration using the information that angles specified as "thetaCal"
           map to the specified list of waveNumbers. Also relax the calibration towards the default using
           Laplacian regularization and the specified value of relaxDefault."""
        self._assertVLaserNum(vLaserNum)
        self.freqConverter[vLaserNum-1].updateWlmCal(thetaCal,waveNumbers,weights,relax,relative,relaxDefault,relaxZero)
        
    def RPC_uploadSchemeToDAS(self, schemeNum):
        # Upload angle scheme to DAS
        if not self.isAngleSchemeConverted[schemeNum]:
            raise Exception("Scheme not converted to angle yet.")
        angleScheme = self.angleScheme[schemeNum]
        Driver.wrScheme(schemeNum, *(angleScheme.repack()))
        
    def RPC_waveNumberToAngle(self,vLaserNum,waveNumbers):
        self._assertVLaserNum(vLaserNum)
        return self.freqConverter[vLaserNum-1].waveNumber2ThetaCal(waveNumbers)

    def RPC_wrFreqScheme(self, schemeNum, freqScheme):
        self.freqScheme[schemeNum] = freqScheme
        self.angleScheme[schemeNum] = freqScheme.makeAngleTemplate()
        self.isAngleSchemeConverted[schemeNum] = False


class TunerAdjuster(object):
    def __init__(self,section):
        rdFreqConv = RDFrequencyConverter()
        self.ditherAmplitude   = float(rdFreqConv.RPC_getHotBoxCalParam(section,"DITHER_AMPLITUDE"))
        self.freeSpectralRange = float(rdFreqConv.RPC_getHotBoxCalParam(section,"FREE_SPECTRAL_RANGE"))
        self.minValue          = float(rdFreqConv.RPC_getHotBoxCalParam(section,"MIN_VALUE"))
        self.maxValue          = float(rdFreqConv.RPC_getHotBoxCalParam(section,"MAX_VALUE"))
        self.upSlope           = float(rdFreqConv.RPC_getHotBoxCalParam(section,"UP_SLOPE"))
        self.downSlope         = float(rdFreqConv.RPC_getHotBoxCalParam(section,"DOWN_SLOPE"))
    def findCenter(self,value,minCen,maxCen,fsr):
        """Finds the best center value for the tuner, given that the mean over the current scan
        is value, and the minimum and maximum allowed center values are given. We preferentially
        choose a value close to minCen."""
        if maxCen < minCen:
            Log("Invalid minCen and maxCen in findCenter",
                dict(minCen = minCen, maxCen = maxCen), Level=2)
        #
        n1 = floor((minCen-value)/fsr)
        n2 = floor((maxCen-value)/fsr)
        # In the best case, we can find a value which falls between minCen and maxCen and which
        #  is separated from the initial value by a multiple of the FSR
        #
        #  maxCen ----
        #                --- value + n2*fsr
        #
        #                --- value + (n1+1)*fsr
        #  minCen ----
        #
        #  value -----
        # The condition for this to be the case is that (n1+1)<=n2. We return 
        #  value+(n1+1)*fsr to be closest to minCen
        if (n1+1) <= n2:  # There is enough of a gap between minCen and maxCen
            return value + (n1+1)*fsr
        else:
            # In the other case, maxCen and minCen are so close together that there is no 
            #  value+n*fsr (for integral n) lying between them
            #
            #                --- value + (n2+1)*fsr
            #  maxCen ---
            #  minCen ---
            #                --- value + n1*fsr
            # We return either maxCen or minCen depending on which is closer to the grid of
            #  value+n*fsr
            #
            if abs(value + n1*fsr - minCen) < abs(value + (n2+1)*fsr - maxCen): return minCen
            return maxCen
    def setTunerRegisters(self, centerValue=None, fsrFactor = 1.3, windowFactor = 0.9):
        """Sets up the tuner values to center the tuner waveform around centerValue, using data 
        contained in the TunerAdjuster object.

        The ramp amplitude is adjusted such that the peak-to-peak value of the ramp window is 
            fsrFactor*self.freeSpectralRange.
        The actual ramp sweep exceeds the window by ditherPeakToPeak on each side.

        TUNER_WINDOW_RAMP_HIGH_REGISTER <- centerValue + rampAmpl
        TUNER_WINDOW_RAMP_LOW_REGISTER  <- centerValue - rampAmpl
        TUNER_SWEEP_RAMP_HIGH_REGISTER  <- centerValue + rampAmpl + ditherPeakToPeak//2
        TUNER_SWEEP_RAMP_LOW_REGISTER   <- centerValue - rampAmpl - ditherPeakToPeak//2

        TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER  <- ditherPeakToPeak//2
        TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER   <- ditherPeakToPeak//2
        TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER <- (windowFactor*ditherPeakToPeak)//2
        TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER  <- (windowFactor*ditherPeakToPeak)//2

        FPGA_TWGEN, TWGEN_SLOPE_UP    <- self.upSlope
        FPGA_TWGEN, TWGEN_SLOPE_DOWN  <- self.downSlope
        """
        rampAmpl = float(0.5* fsrFactor * self.freeSpectralRange)
        ditherPeakToPeak = 2 * self.ditherAmplitude
        centerMax = self.maxValue - ditherPeakToPeak//2 - rampAmpl
        centerMin = self.minValue + ditherPeakToPeak//2 + rampAmpl
        if centerMin > centerMax:
            # We need to use the maximum range available 
            centerValue = 0.5*(self.minValue + self.maxValue)
            rampAmpl = self.maxValue - centerValue - ditherPeakToPeak//2
            if 2*rampAmpl < self.freeSpectralRange:
                Log("Insufficient PZT range to cover cavity FSR",
                    dict(fsr = self.freeSpectralRange, rampAmpl = rampAmpl), Level=2)
        else:
            centerValue = self.findCenter(centerValue, centerMin, centerMax, self.freeSpectralRange)
            
        Driver.wrDasReg("TUNER_WINDOW_RAMP_HIGH_REGISTER",centerValue + rampAmpl)
        Driver.wrDasReg("TUNER_WINDOW_RAMP_LOW_REGISTER", centerValue - rampAmpl)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_HIGH_REGISTER", centerValue + rampAmpl + ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_LOW_REGISTER",  centerValue - rampAmpl - ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER",ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER", ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER",(windowFactor*ditherPeakToPeak)//2)
        Driver.wrDasReg("TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER", (windowFactor*ditherPeakToPeak)//2)
        Driver.wrFPGA("FPGA_TWGEN","TWGEN_SLOPE_UP",int(self.upSlope))
        Driver.wrFPGA("FPGA_TWGEN","TWGEN_SLOPE_DOWN",int(self.downSlope))

HELP_STRING = """RDFrequencyConverter.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./RDFrequencyConverter.ini"
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:'
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
    rdFreqConvertApp = RDFrequencyConverter(configFile)
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    rdFreqConvertApp.run()
    Log("Exiting program")
