#!/usr/bin/python
#
# FILE:
#   RDFrequencyConverter.py
#
# DESCRIPTION:
#   Converts between WLM angle and frequencies using AutoCal structures
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   30-Sep-2009  alex/sze  Initial version.
#   02-Oct-2009  alex      Add RPC functions.
#   09-Oct-2009  sze       Supporting new warm box calibration files and uploading of virtual laser parameters to DAS
#   11-Oct-2009  sze       Added routines to support CalibrateSystem
#   14-Oct-2009  sze       Added support for calibration rows in schemes
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
import inspect
from numpy import *
import os
import Queue
import threading
import time
import traceback
from cStringIO import StringIO
from binascii import crc32
from Host.autogen import interface
from Host.Common.WlmCalUtilities import AutoCal
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.SharedTypes import BROADCAST_PORT_RD_RECALC, BROADCAST_PORT_RDRESULTS
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER
from Host.Common.SharedTypes import Scheme, Singleton
from Host.Common import Listener, Broadcaster
from Host.Common import CmdFIFO, StringPickler

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
EventManagerProxy_Init("RDFrequencyConverter")

MIN_SIZE = 30

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
        table = entry.schemeTable
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

    def processCalSpectrum(self):
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
                    continue
                count = array([d[k].count for k in rows])
                tunerMean = float(sum(tuner*count))/sum(count)
                tunerDev  = tuner - tunerMean
                # Use the median to center the tuner, for robustness
                tunerCenter = float(self.medianHist(tuner,count,useAverage=False))
                Log("Standard deviation of tuner: %.1f" % std(tunerDev))
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
                offGrid = abs(dtheta/anglePerFsr - m).max()
                if offGrid > float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","MAX_OFFGRID")):
                    Log("Calibration not done, offGrid parameter = %.2f" % (offGrid,))
                else:
                    Log("Updating WLM Calibration for virtual laser", dict(vLaserNum = vLaserNum))
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


Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                         ClientName="RDFrequencyConverter")
                                         
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
            
class RDFrequencyConverter(Singleton):
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.numLasers = interface.NUM_VIRTUAL_LASERS
            self.rdQueue = Queue.Queue()
            self.rdProcessedCache = []
            self.rpcThread = None
            self._shutdownRequested = False
            self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_FREQ_CONVERTER),
                                                    ServerName = "FrequencyConverter",
                                                    ServerDescription = "Frequency Converter for CRDS hardware",
                                                    threaded = True)
            #Register the rpc functions...
            for s in dir(self):
                attr = self.__getattribute__(s)
                if callable(attr) and s.startswith("RPC_") and (not inspect.isclass(attr)):
                    self.rpcServer.register_function(attr, NameSlice = 4)
                    
            self.rdListener = Listener.Listener(self.rdQueue,
                                        BROADCAST_PORT_RDRESULTS,
                                        interface.RingdownEntryType,
                                        streamFilter = self.rdFilter,
                                        retry = True,
                                        name = "Ringdown frequency converter listener",logFunc = Log)
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
            
    def rdFilter(self,entry):
        # Figure if we finished a scheme and whether we should process cal points in the last scheme
        if 0 != (entry.status & interface.RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask) or \
           0 != (entry.status & interface.RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask) or \
           (entry.status & interface.RINGDOWN_STATUS_SequenceMask) != self.lastSchemeCount:
            if self.sbc.currentCalSpectrum:
                self.sbc.processCalSpectrum()
            self.sbc.clear()
            self.lastSchemeCount = (entry.status & interface.RINGDOWN_STATUS_SequenceMask)
        # Check if this is a calibration row and process it accordingly
        if entry.subschemeId & interface.SUBSCHEME_ID_IsCalMask:
            rowNum = entry.schemeRow
            angleError = mod(entry.wlmAngle - self.angleScheme[entry.schemeTable].setpoint[entry.schemeRow],2*pi)
            tempError  = entry.laserTemperature - self.angleScheme[entry.schemeTable].laserTemp[entry.schemeRow]
            if min(angleError,2*pi-angleError) < self.dthetaMax and abs(tempError) < self.dtempMax:
                # The spectral point is close to the setpoint
                self.sbc.processCalPoint(entry)
        return entry
    
    def run(self):
        #start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.RPC_shutdown)
        self.rpcThread.start()
        startTime = time.time()
        timeout = 2.0
        while not self._shutdownRequested:
            try:
                self.tuningMode = Driver.rdDasReg("ANALYZER_TUNING_MODE_REGISTER")
                if self.rdQueue.qsize() > MIN_SIZE or time.time()-startTime > timeout:
                    self._batchConvert()
                    startTime = time.time()
                else:
                    time.sleep(1.0)
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
                time.sleep(1.0)
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
                    if name != "wlmAngle":
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
                if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
                    raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
                fc = self.freqConverter[vLaserNum-1]
                waveNo = fc.thetaCalAndLaserTemp2WaveNumber(array(wlmAngle[vLaserNum-1]), array(laserTemperature[vLaserNum-1]))
                for i,w in enumerate(waveNo):
                    index = cacheIndex[vLaserNum-1][i]
                    rdProcessedData = self.rdProcessedCache[index]
                    rdProcessedData.waveNumber = w
                    rdProcessedData.waveNumberSetpoint = self.freqScheme[rdProcessedData.schemeTable].setpoint[rdProcessedData.schemeRow]

    def RPC_angleToLaserTemperature(self,vLaserNum,angles):
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        return self.freqConverter[vLaserNum-1].thetaCal2LaserTemp(angles)

    def RPC_angleToWaveNumber(self,vLaserNum,angles):
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        return self.freqConverter[vLaserNum-1].thetaCal2WaveNumber(angles)
    
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
            if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
                raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
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
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        return self.freqConverter[vLaserNum-1].laserTemp2ThetaCal(laserTemperatures)
    
    def RPC_loadHotBoxCal(self, hotBoxCalFilePath):
        self.hotBoxCalFilePath = os.path.abspath(hotBoxCalFilePath)
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
        
    def RPC_loadWarmBoxCal(self, warmBoxCalFilePath):
        # Load up the frequency converters for each laser in the DAS...
        self.warmBoxCalFilePath = os.path.abspath(warmBoxCalFilePath)
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
                                'ratio2Scale':     float(p['RATIO1_SCALE']),
                                'phase':           float(p['PHASE']),
                                'tempSensitivity': float(p['TEMP_SENSITIVITY']),
                                'calTemp':         float(p['CAL_TEMP']),
                                'calPressure':     float(p['CAL_PRESSURE']),
                                'pressureC0':      float(p['PRESSURE_C0']),
                                'pressureC1':      float(p['PRESSURE_C1']),
                                'pressureC2':      float(p['PRESSURE_C2']),
                                'pressureC3':      float(p['PRESSURE_C3'])}
                Driver.wrVirtualLaserParams(vLaserNum,laserParams)

    def RPC_replaceOriginalWlmCal(self,vLaserNum):
        # Copy current spline coefficients to original coefficients
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        self.freqConverter[vLaserNum-1].replaceOriginal()

    def RPC_restoreOriginalWlmCal(self,vLaserNum):
        # Replace current spline coefficients with original spline coefficients
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        self.freqConverter[vLaserNum-1].replaceCurrent()
        
    def RPC_setHotBoxCalParam(self,secName,optName,optValue):
        self.hotBoxCal[secName][optName] = optValue
        
    def RPC_shutdown(self):
        self._shutdownRequested = True
        
    def RPC_updateHotBoxCal(self,fileName=None):
        """
        Write calibration back to the file with a new checksum.
        """
        fp = None
        if self.hotBoxCal is None:
            raise ValueError("Hot box calibration has not been loaded")
        try:
            calStrIO = StringIO()
            self.hotBoxCal.write(calStrIO)
            calStr = calStrIO.getvalue()
            calStr = calStr[:calStr.find("#checksum=")]
            checksum = crc32(calStr, 0)
            calStr += "#checksum=%d" % checksum
            if fileName is not None:
                fp = file(fileName, "wb")
            else:
                fp = file(self.hotBoxCalFilePath, "wb")
            fp.write(calStr)
        finally:
            calStrIO.close()
            if fp is not None: fp.close()
    
    def RPC_updateWarmBoxCal(self,fileName=None):
        """
        Write calibration back to the file with a new checksum.
        """
        fp = None
        cp = CustomConfigObj(self.warmBoxCalFilePath)
        for i in self.freqConverter.keys():
            ac = self.freqConverter[i]
            if ac is not None:
                ac.updateIni(cp, i+1) # Note: In Autocal1, laser indices are 1 based
        try:
            calStrIO = StringIO()
            cp.write(calStrIO)
            calStr = calStrIO.getvalue()
            calStr = calStr[:calStr.find("#checksum=")]
            checksum = crc32(calStr, 0)
            calStr += "#checksum=%d" % checksum
            if fileName is not None:
                fp = file(fileName, "wb")
            else:
                fp = file(self.warmBoxCalFilePath, "wb")
            fp.write(calStr)
        finally:
            calStrIO.close()
            if fp is not None: fp.close()

    def RPC_updateWlmCal(self,vLaserNum,thetaCal,waveNumbers,weights,relax=5e-3,relative=True,relaxDefault=5e-3,relaxZero=5e-5):
        """Updates the wavelength monitor calibration using the information that angles specified as "thetaCal"
           map to the specified list of waveNumbers. Also relax the calibration towards the default using
           Laplacian regularization and the specified value of relaxDefault."""
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        self.freqConverter[vLaserNum-1].updateWlmCal(thetaCal,waveNumbers,weights,relax,relative,relaxDefault,relaxZero)
        
    def RPC_uploadSchemeToDAS(self, schemeNum):
        # Upload angle scheme to DAS
        if not self.isAngleSchemeConverted[schemeNum]:
            raise Exception("Scheme not converted to angle yet.")
        angleScheme = self.angleScheme[schemeNum]
        Driver.wrScheme(schemeNum, *(angleScheme.repack()))
        
    def RPC_waveNumberToAngle(self,vLaserNum,waveNumbers):
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
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
        is value, and the minimum and maximum allowed center values are given"""
        n1 = floor((minCen-value)/fsr)
        n2 = floor((maxCen-value)/fsr)
        if (n1+1) <= n2:  # There is enough of a gap between minCen and maxCen to work in
            if (n1+1) > 0: return value + (n1+1)*fsr # Ensures we are above minCen
            if n2 < 0: return value + n2*fsr         # Ensures we are below maxCen
            return value
        else:
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
        TUNER_SWEEP_RAMP_HIGH_REGISTER  <- centerValue + rampAmpl + ditherPeakToPeak
        TUNER_SWEEP_RAMP_LOW_REGISTER   <- centerValue - rampAmpl - ditherPeakToPeak

        TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER  <- ditherPeakToPeak//2
        TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER   <- ditherPeakToPeak//2
        TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER <- (windowFactor*ditherPeakToPeak)//2
        TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER  <- (windowFactor*ditherPeakToPeak)//2

        FPGA_TWGEN, TWGEN_SLOPE_UP    <- self.upSlope
        FPGA_TWGEN, TWGEN_SLOPE_DOWN  <- self.downSlope
        """
        rampAmpl = float(0.5* fsrFactor * self.freeSpectralRange)
        ditherPeakToPeak = 2 * self.ditherAmplitude
        centerMax = self.maxValue - ditherPeakToPeak - rampAmpl
        centerMin = self.minValue + ditherPeakToPeak + rampAmpl
        if centerMin > centerMax:
            Log("Error recentering tuner waveform", dict(centerMax = int(centerMax), centerMin = int(centerMin)))
            return
        centerValue = self.findCenter(centerValue, centerMin, centerMax, self.freeSpectralRange)
        Driver.wrDasReg("TUNER_WINDOW_RAMP_HIGH_REGISTER",centerValue + rampAmpl)
        Driver.wrDasReg("TUNER_WINDOW_RAMP_LOW_REGISTER", centerValue - rampAmpl)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_HIGH_REGISTER", centerValue + rampAmpl + ditherPeakToPeak)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_LOW_REGISTER",  centerValue - rampAmpl - ditherPeakToPeak)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER",ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER", ditherPeakToPeak//2)
        Driver.wrDasReg("TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER",(windowFactor*ditherPeakToPeak)//2)
        Driver.wrDasReg("TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER", (windowFactor*ditherPeakToPeak)//2)
        Driver.wrFPGA("FPGA_TWGEN","TWGEN_SLOPE_UP",int(self.upSlope))
        Driver.wrFPGA("FPGA_TWGEN","TWGEN_SLOPE_DOWN",int(self.downSlope))
        
if __name__ == "__main__":
    rdFreqConvertApp = RDFrequencyConverter()
    #rdFreqConvertApp.RPC_loadCal("WarmBoxCal.ini")
    #rdFreqConvertApp.RPC_wrFreqScheme(0, Scheme("sample2.sch"))
    #rdFreqConvertApp.RPC_convertScheme(0)
    #rdFreqConvertApp.RPC_uploadSchemeToDAS(0)
    #rdFreqConvertApp.RPC_updateCal()
    Log("RDFrequencyConverter starting")
    rdFreqConvertApp.run()
    Log("RDFrequencyConverter exiting")
