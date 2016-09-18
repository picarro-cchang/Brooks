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
    21-Oct-2009  alex      Added calibration file paths to .ini file. Added RPC_setCavityLengthTuning() and
                               RPC_setLaserCurrentTuning().
    22-Apr-2010  sze       Fixed non-updating of angle schemes when no calibration points are present
    20-Sep-2010  sze       Added pCalOffset parameter to RPC_loadWarmBoxCal for flight calibration
    24-Oct-2010  sze       Put scheme version number in high order bits of schemeVersionAndTable in
                               ProcessedRingdownEntry type
    09-Mar-2012  sze       Use 7th (1-origin) column of scheme file to specify laser temperature offset from the
                               nominal temperature
    15-Feb-2013  sze       Always center tuner about 32768, rather than around value passed in as argument
    13-Dec-2013  sze       Corrected bug which was ignoring values of MAX_ANGLE_TARGETTING_ERROR and
                            MAX_TEMP_TARGETTING_ERROR from hot box calibration file.
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
from numpy import arctan2, array, argsort, concatenate, cos, cumsum, diff, floor, int_, mean, median, mod
from numpy import pi, round_, sin, std, zeros
from cStringIO import StringIO
from binascii import crc32

from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, Listener, Broadcaster
from Host.Common.SharedTypes import Singleton
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

if __debug__:
    print("Loading rpdb2")
    import rpdb2
    rpdb2.start_embedded_debugger("hostdbg",timeout=0)
    print("rpdb2 loaded")

class CalibrationDataInRow(object):
    """Structure for collecting ringdown metadata for calibration ringdowns associated with a scheme row.

    Scheme rows are marked as calibration points by turning on the SUBSCHEME_ID_IsCalMask bit.
    This structure stores the laser temperature, PZT and WLM angles at such points, for updating
    the wavelength monitor calibration, since they are known to be separated by the cavity FSR.
    """
    def __init__(self):
        self.tunerVals = []
        self.pztVals = []
        self.thetaCalCos = []
        self.thetaCalSin = []
        self.laserTempVals = []
        self.tunerMed = None
        self.thetaCalMed = None
        self.laserTempMed = None
        self.vLaserNum = None
        self.count = 0

class SchemeBasedCalibrator(object):
    """Calibrator for WLM splines based on scheme rows marked as calibration points.

    We update the calibration of each virtual laser individually, based on the calibration points
        which involve that virtual laser.
    """
    def __init__(self):
        # Calibration points are stored in a dictionary keyed by the row number in the scheme
        #  schemeNum is the scheme table index in the DAS
        self.calDataByRow = {}
        self.schemeNum = None
        self.rdFreqConv = RDFrequencyConverter()
        self.calibrationDone = [False for _ in range(interface.NUM_VIRTUAL_LASERS)]

    def clear(self):
        self.calDataByRow.clear()
        self.schemeNum = None

    def isCalibrationDone(self, vLaserNumList):
        """Check if calibration has been done for the specified list of virtual lasers.

        Args:
            vLaserNumList: List of integer virtual laser indexes (1-origin)

        Returns: List of Boolean results
        """
        return [self.calibrationDone[vLaserNum-1] for vLaserNum in vLaserNumList]

    def clearCalibrationDone(self, vLaserNumList):
        """Clear calibration done flag for the specified list of virtual lasers.

        Args:
            vLaserNumList: List of integer virtual laser indexes (1-origin)
        """
        for vLaserNum in vLaserNumList:
            self.calibrationDone[vLaserNum-1] = False

    def processCalRingdownEntry(self, entry):
        """Process a ringdown entry which is marked as a calibration row.

        The ringdown metadata for ringdowns associated with a particular scheme row should cluster
        tightly around values for that row. These data are stored in lists in a CalibrationDataInRow
        object so that we can later compute medians of the various metadata, which are used to update
        the WLM splines. These ojects are stored in a hash table keyed by the scheme row.

        Args:
            entry: RingdownEntryType object corresponding to a ringdown marked with the calibration flag
        """
        assert isinstance(entry, interface.RingdownEntryType)

        row = entry.schemeRow
        # At this stage entry.schemeVersionAndTable is the scheme table index (version is added later)
        table = entry.schemeVersionAndTable
        if row not in self.calDataByRow:  # Make new entry in the hash table
            self.calDataByRow[row] = CalibrationDataInRow()
            if self.schemeNum is None:
                self.schemeNum = table
            else:
                if self.schemeNum != table:
                    Log("Scheme table mismatch while processing calibration row",
                        dict(expectedScheme=self.schemeNum,schemeFound=table), Level=2)
                    self.clear()
                    return
        # Update the metadata
        calDataForRow = self.calDataByRow[row]
        calDataForRow.count += 1
        # We separately deal with sin and cos to avoid 2*pi ambiguity for angles which mess up median
        #  calculation
        calDataForRow.thetaCalCos.append(cos(entry.wlmAngle))
        calDataForRow.thetaCalSin.append(sin(entry.wlmAngle))
        calDataForRow.laserTempVals.append(entry.laserTemperature)
        calDataForRow.tunerVals.append(entry.tunerValue)
        calDataForRow.pztVals.append(entry.pztValue)
        calDataForRow.vLaserNum = 1 + ((entry.laserUsed >> 2) & 7)

    def calFailed(self, vLaserNum):
        """Mark a calibration attempt as having failed.

        Typical causes of failure include an unstable etalon temperature during warmup, rapid changes in pressure,
        or the analyzer getting choked. When this happens, the analyzer ringdown rate can be very slow due to
        transitions into ramp mode. This routine looks for more than a certain number of consecutive failures to
        calibrate, and if these occur, the driver is instructed to ignore the repeat count in the scheme file. By
        causing the scheme to finish more quickly, it may be possible to switch modes or otherwise recover from the
        slowdown. Note that this is only called if the "ShortCircuitSchemes" section is present in the
        RDFrequencyConverter configuration file.

        Args:
            vLaserNum: Virtual laser index (1-origin) for failed calibration attempt
        """
        scs = self.rdFreqConv.shortCircuitSchemes
        self.rdFreqConv.calFailed[vLaserNum-1] += 1
        self.rdFreqConv.calSucceeded[vLaserNum-1] = 0
        if self.rdFreqConv.calFailed[vLaserNum-1] >= int(scs['failureThreshold']):
            if Driver.getSpectCntrlMode() != interface.SPECT_CNTRL_SchemeMultipleNoRepeatMode:
                Driver.setMultipleNoRepeatScan()
                Log("Setting multiple scheme no repeat mode", dict(calSucceeded=self.rdFreqConv.calSucceeded,
                calFailed=self.rdFreqConv.calFailed))

    def calSucceeded(self, vLaserNum):
        """Mark a calibration attempt as having succeeded.

        This routine looks for more than a certain number of consecutive successful calibrations, and switches the
        driver back to SchemeMultipleMode from SchemeMultipleNoRepeatMode so that the repeat count is honored.
        Note that this is only called if the "ShortCircuitSchemes" section is present in the RDFrequencyConverter
        configuration file.

        Args:
            vLaserNum: Virtual laser index (1-origin) for successful calibration attempt
        """
        scs = self.rdFreqConv.shortCircuitSchemes
        self.rdFreqConv.calFailed[vLaserNum-1] = 0
        self.rdFreqConv.calSucceeded[vLaserNum-1] += 1
        valid = (self.rdFreqConv.calSucceeded != 0)
        if all(self.rdFreqConv.calFailed==0) and all(self.rdFreqConv.calSucceeded[valid]>=int(scs['successThreshold'])):
            if Driver.getSpectCntrlMode() != interface.SPECT_CNTRL_SchemeMultipleMode:
                Driver.setMultipleScan()
                Log("Setting multiple scheme mode", dict(calSucceeded=self.rdFreqConv.calSucceeded,
                calFailed=self.rdFreqConv.calFailed))

    def applySchemeBasedCalibration(self):
        """Called after a scheme is completed to process data from calibration rows.
        """
        scs = self.rdFreqConv.shortCircuitSchemes
        calDataByRow = self.calDataByRow
        if len(calDataByRow) < int(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","MIN_CALROWS")):
            return
        for row in calDataByRow:
            # Find median WlmAngles, tuner values and laser temperatures
            #  N.B. We must deal with the sine and cosine parts separately
            calData = calDataByRow[row]
            assert(isinstance(calData, CalibrationDataInRow))
            calData.thetaCalMed = arctan2(median(calData.thetaCalSin), median(calData.thetaCalCos))
            calData.tunerMed = median(calData.tunerVals)
            calData.pztMed = median(calData.pztVals)
            calData.laserTempMed = median(calData.laserTempVals)
        # Process the data one virtual laser at a time
        for vLaserNum in range(1, interface.NUM_VIRTUAL_LASERS + 1):
            # Get scheme rows involving this virtual laser. If the calibration were correct, the PZT values for all
            # ringdowns associated with the rows would be equal. We find medians of the metadata for each row
            # and look at the variation between the rows to derive the corrections.
            rows = [k for k in calDataByRow if (calDataByRow[k].vLaserNum == vLaserNum)]
            if len(rows) >= 2:
                # Find the WLM angles for these ringdowns by using the laser temperature to rotate the
                #  WLM angles (thetaCal) to the correct revolution
                laserTemp = array([calDataByRow[k].laserTempMed for k in rows])
                thetaCal  = array([calDataByRow[k].thetaCalMed  for k in rows])
                # thetaHat are WLM angles associated with the measured laser temperatures
                thetaHat  = self.rdFreqConv.RPC_laserTemperatureToAngle(vLaserNum, laserTemp)
                thetaCal  +=  2*pi*floor((thetaHat-thetaCal)/(2*pi) + 0.5) # Apply correction for revolution
                tuner     = array([calDataByRow[k].tunerMed for k in rows])
                pzt       = array([calDataByRow[k].pztMed for k in rows])
                # Ideally, PZT values for all rows should be close together. We check for large jumps and forgo
                #  calibration in such cases
                jump = abs(diff(pzt)).max()
                if jump > float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","MAX_JUMP")):
                    Log("Calibration not done, maximum jump between calibration rows: %.1f" % (jump,))
                    if scs: # If short circuit schemes are enabled, this should be counted as a failed calibration
                        self.calFailed(vLaserNum)
                    continue
                # We find the deviation of the tuner values for each calibration row from the weighted average
                #  over all caliibration rows. This is used to center the tuner values.
                count = array([calDataByRow[k].count for k in rows])
                tunerMean = float(sum(tuner*count))/sum(count)
                tunerDev  = tuner - tunerMean
                # Use the median with useAverage=False to center the tuner. This always returns one of the tuner
                #  values that actually occured.
                tunerCenter = float(self.medianHist(tuner, count, useAverage=False))
                # Center the tuner ramp waveform about the median tuner value at the calibration rows
                #  Since this can get stuck behind scheme uploads due to Driver command serialization,
                #  we do it in a separate thread
                tunerCenteringThread = threading.Thread(target = self.centerTuner, args=(tunerCenter,))
                tunerCenteringThread.setDaemon(True)
                tunerCenteringThread.start()

                # The deviation of the PZT values from their weighted average is used to adjust the wavelength
                #  monitor spline calibration
                pztMean = float(sum(pzt*count))/sum(count)
                pztDev  = pzt - pztMean
                # If pztDev is not all zeros, this indicates that the collection of WLM angles which was
                #  used by the laser frequency locker do not correspond precisely to frequencies separated
                #  by the cavity FSR. We use the values in the deviations to adjust the WLM angles by
                #  multiplying each PZT deviation by an adjust factor (with units of
                #  (WLM radians)/(PZT digitizer units)) and using this as a correction.
                #
                # The ADJUST_FACTOR should be an underestimate of the WLM angle shift corresponding to
                #  a digitizer unit of PZT. This provides a degree of under-relaxation and filtering.
                #
                thetaShifted = thetaCal - (float(
                    self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL","ADJUST_FACTOR")) * pztDev)
                # Elements in thetaShifted should correspond to a set of frequencies separated by
                #  multiples of the cavity FSR. We now need to determine what these multiples are
                perm = thetaShifted.argsort()
                thetaShifted = thetaShifted[perm]
                dtheta = diff(thetaShifted)
                # We need to know approximately what wavelength monitor angle corresponds to a cavity
                #  FSR so that the values in thetaShifted can be assigned to FSRs. We use a two step process
                #  here to do this:
                # 1) The APPROX_WLM_ANGLE_PER_FSR is divided into dtheta, and the result is rounded to the
                #     nearest integers. Since the angle per fsr is only approximate, we get less sure of these
                #     multiples as they get larger. We select only the WLM angle jumps corresponding to one FSR.
                # 2) From the selected WLM angle jumps corresponding to one cavity FSR, we make a better
                #     estimate of the WLM angle per cavity FSR, and use these to improve fsrJump
                # Note that all this work is done to determine if we should do the calibration or not (depending
                #  on the offgrid parameter calculated later). The scheme is used to determine the frequencies
                #  associated with the WLM angles.
                fsrJump = round_(dtheta / float(self.rdFreqConv.RPC_getHotBoxCalParam(
                    "AUTOCAL","APPROX_WLM_ANGLE_PER_FSR")))

                dthetaSel = dtheta[fsrJump == 1]
                if len(dthetaSel) >= 1:
                    anglePerFsr = mean(dthetaSel)
                    fsrJumpRevised = round_(dtheta/anglePerFsr) # Quantize fsrJump to indicate multiples of the FSR
                    if (fsrJump != fsrJumpRevised).any():
                        Log("During WLM calibration, counting of FSRs may have been inaccurate. vLaserNum: %d" % vLaserNum)
                    fsrJump = fsrJumpRevised
                    # Ensure that the differences between the WLM angles at the calibration rows are close
                    #  to multiples of the FSR before we do the calibration. This prevents calibrations from
                    #  occurring if the pressure is changing, etc.
                    devs = abs(dtheta/anglePerFsr - fsrJump)
                    offGrid = devs.max()
                    if offGrid > float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL", "MAX_OFFGRID")):
                        Log("Calibration not done, PZT sdev = %.1f, offGrid parameter = %.2f, fraction>0.25 = %.2f" %
                            (std(pztDev), offGrid, sum(devs>0.25)/float(len(devs))))
                        if scs:
                            self.calFailed(vLaserNum)
                    else:
                        #Update the live copy of the polar<->freq coefficients...
                        waveNumberSetpoints = zeros(len(rows), dtype=float) #pre-allocate space
                        # Get the wavenumber setpoints from the scheme rows
                        for i, calRow in enumerate(rows):
                            waveNumberSetpoints[i] = self.rdFreqConv.freqScheme[self.schemeNum].setpoint[calRow]
                        waveNumberSetpoints = waveNumberSetpoints[perm] #sorts in the same way that thetaShifted was
                        #Calculate number of calibration points at each FSR, so they may be weighted properly
                        weights = self.calcWeights(cumsum(concatenate(([0], fsrJump))))
                        #Now do the actual updating of the conversion coefficients...
                        try:
                            maxDiff = float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL", "MAX_WAVENUM_DIFF"))
                        except KeyError:
                            maxDiff = 0.4
                        self.rdFreqConv.RPC_updateWlmCal(
                            vLaserNum, thetaShifted, waveNumberSetpoints, weights,
                            float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL", "RELAX")),True,
                            float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL", "RELAX_DEFAULT")),
                            float(self.rdFreqConv.RPC_getHotBoxCalParam("AUTOCAL", "RELAX_ZERO")),
                            maxDiff)
                        self.calibrationDone[vLaserNum-1] = True
                        stdTuner = std(tunerDev)
                        stdPzt = std(pztDev)
                        if scs:
                            if stdTuner > float(scs['maxTunerStandardDeviation']):
                                self.calFailed(vLaserNum)
                            else:
                                self.calSucceeded(vLaserNum)
                        Log("WLM Cal for virtual laser %d done, angle per FSR = %.4g, PZT sdev = %.1f" %
                            (vLaserNum, anglePerFsr, stdPzt))

    def centerTuner(self, tunerCenter):
        self.rdFreqConv.RPC_centerTuner(tunerCenter)

    def calcWeights(self, intData):
        """Calculate weights associated with integer array intData. Elements of intData must be sorted.
        The weight associated with intData[i] is the number of times intData[i] appears in the array,
        and this is placed in the result array weights[i]."""
        weights = zeros(intData.shape, int_)
        kprev = 0
        counter = 1
        for k in range(1, len(intData)):
            if intData[k] != intData[k-1]:
                weights[kprev:k] = counter
                kprev = k
                counter = 1
            else:
                counter += 1
        weights[kprev:] = counter
        return weights

    def medianHist(self, values, freqs, useAverage=True):
        """Compute median of a set of values, where each value has an associated frequency.

        Args:
            values: Array of values
            freqs: Array of frequencies associated with above values
            useAverage: If the sum of frequencies is even, take average of the two central values
        Returns: Median of the data set
        """
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
    filePtr = file(fname,'rb')
    try:
        calStr = filePtr.read()
        cPos = calStr.find("#checksum=")
        if cPos < 0:
            raise ValueError("No checksum in file")
        else:
            try:
                csum1 = int(calStr[cPos+10:])
                csum2 = crc32(calStr[:cPos], 0)
            except Exception, exc:
                raise ValueError("Error calculating checksum %r" % exc)
            if csum1 == csum2:
                return "OK"
            else:
                raise ValueError("Bad checksum")
    finally:
        filePtr.close()

class RDFrequencyConverter(Singleton):
    initialized = False
    def __init__(self, configPath=None, virtualMode=False):
        if not self.initialized:
            self.tunerCenter = None
            self.virtualMode = virtualMode

            if configPath != None:
                # Read from .ini file
                config = CustomConfigObj(configPath)
                basePath = os.path.split(configPath)[0]
                self.saveWlmHistPeriod_s = config.getfloat("MainConfig", "saveWlmHistPeriod_s", "120")
                self.wbCalUpdatePeriod_s = config.getfloat("MainConfig", "wbCalUpdatePeriod_s", "1800")
                self.hbCalUpdatePeriod_s = config.getfloat("MainConfig", "hbCalUpdatePeriod_s", "1800")
                self.wbArchiveGroup = config.get("MainConfig", "wbArchiveGroup", "WBCAL")
                self.hbArchiveGroup = config.get("MainConfig", "hbArchiveGroup", "HBCAL")
                self.warmBoxCalFilePathActive = os.path.abspath(os.path.join(
                    basePath, config.get("CalibrationPath", "warmboxCalActive", "")))
                self.warmBoxCalFilePathFactory = os.path.abspath(os.path.join(
                    basePath, config.get("CalibrationPath", "warmboxCalFactory", "")))
                self.hotBoxCalFilePathActive = os.path.abspath(os.path.join(
                    basePath, config.get("CalibrationPath", "hotboxCalActive", "")))
                self.hotBoxCalFilePathFactory = os.path.abspath(os.path.join(
                    basePath, config.get("CalibrationPath", "hotboxCalFactory", "")))
                if "ShortCircuitSchemes" in config:
                    self.shortCircuitSchemes = dict(config["ShortCircuitSchemes"])
                else:
                    self.shortCircuitSchemes = {}

                if config.has_option('MainConfig', 'tunerCenter'):
                    self.tunerCenter = config.getint('MainConfig', 'tunerCenter')
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
            if not virtualMode:
                Driver.stopScan()
            self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_FREQ_CONVERTER),
                                                    ServerName = "FrequencyConverter",
                                                    ServerDescription = "Frequency Converter for CRDS hardware",
                                                    threaded = True)
            #Register the rpc functions...
            for attrName in dir(self):
                attr = self.__getattribute__(attrName)
                if callable(attr) and attrName.startswith("RPC_") and (not inspect.isclass(attr)):
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
            # For each virtual laser, keep track of the number of times the scheme-based calibration
            #  process has succeeded and failed
            self.calFailed = zeros(interface.NUM_VIRTUAL_LASERS)
            self.calSucceeded = zeros(interface.NUM_VIRTUAL_LASERS)
            self.rdListener = None

    def rdFilter(self, entry):
        """Filter applied to RingdownEntryType objects obtained from Driver. Within this filter, the
        scheme calibration rows are pulled out and used to run the WLM calibration. The entries are
        then placed onto the ringdown queue.

        Args:
            entry: RingdownEntryType obtained from Listener to Driver
        """
        assert isinstance(entry, interface.RingdownEntryType)
        if (entry.status & interface.RINGDOWN_STATUS_SequenceMask) != self.lastSchemeCount:
            # We have got to a new scheme
            if self.sbc.calDataByRow:
                self.sbc.applySchemeBasedCalibration()
            self.sbc.clear()
            self.lastSchemeCount = (entry.status & interface.RINGDOWN_STATUS_SequenceMask)
        # Check if this is a calibration row and process it accordingly
        if entry.subschemeId & interface.SUBSCHEME_ID_IsCalMask:
            rowNum = entry.schemeRow
            # The scheme version has not yet been placed in schemeVersionAndTable
            schemeTable = entry.schemeVersionAndTable
            angleError = mod(entry.wlmAngle - self.angleScheme[schemeTable].setpoint[rowNum], 2 * pi)
            tempError  = entry.laserTemperature - self.angleScheme[schemeTable].laserTemp[rowNum]
            if (min(angleError, 2 * pi - angleError) < self.dthetaMax) and (abs(tempError) < self.dtempMax):
                # The spectral point is close to the setpoint
                self.sbc.processCalRingdownEntry(entry)
            else:
                Log("WLM Calibration point cannot be used: rowNum: %d, tempError: %.1f, angleError: %.4f, vLaserNum: %d" %
                    (rowNum, tempError, min(angleError, 2 * pi - angleError), 1 + ((entry.laserUsed >> 2) & 7)))
        return entry

    def run(self):
        """Runs main loop of the RDFrequencyConverter.

        Ringdowns from the driver are passed through the ringdown filter and are then placed onto the
        ringdown queue.
        """
        # Start the thread for saving WLM history into database
        saveWlmThread = threading.Thread(target = self.runSaveWlmHistory)
        saveWlmThread.setDaemon(True)
        saveWlmThread.start()

        # Start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.RPC_shutdown)
        self.rpcThread.start()
        startTime = time.time()
        timeout = 0.5

        while self.virtualMode:
            time.sleep(1.0)

        self.tuningMode = Driver.rdDasReg("ANALYZER_TUNING_MODE_REGISTER")
        while not self._shutdownRequested:
            # Check if it's time to update and archive the warmbox calibration file
            if self.timeToUpdateWarmBoxCal():
                Log("Time to update warm box calibration file")
                #  we'll do it in a separate thread in case it takes too long to write the new calibration file to disk
                updateWarmBoxCalThread = threading.Thread(target = self.updateWarmBoxCal,
                                                          args=(self.warmBoxCalFilePathActive,))
                updateWarmBoxCalThread.setDaemon(True)
                updateWarmBoxCalThread.start()
            try:
                rdQueueSize = self.rdQueue.qsize()
                if rdQueueSize > self.rdQueueMaxLevel:
                    self.rdQueueMaxLevel = rdQueueSize
                    Log("rdQueueSize reaches new peak level %d" % self.rdQueueMaxLevel)
                if rdQueueSize > MIN_SIZE or time.time()-startTime > timeout:
                    self._batchConvert()
                    startTime = time.time()
                    self.tuningMode = Driver.rdDasReg("ANALYZER_TUNING_MODE_REGISTER")
                else:
                    time.sleep(0.02)
                    continue
                while self.rdProcessedCache:
                    try:
                        rdProcessedData = self.rdProcessedCache.pop(0)
                        self.processedRdBroadcaster.send(StringPickler.ObjAsString(rdProcessedData))
                    except IndexError:
                        break
            except:
                excType, value, _trace = sys.exc_info()
                Log("Error: %s: %s" % (str(excType), str(value)), Verbose=traceback.format_exc(), Level=3)
                while not self.rdQueue.empty():
                    self.rdQueue.get(False)
                self.rdProcessedCache = []
                time.sleep(0.02)
        Log("RD Frequency Converter RPC handler shut down")

    def _batchConvert(self):
        """Convert WLM angles and laser temperatures to wavenumbers in a vectorized way, using
        wlmAngleAndlaserTemperature2WaveNumber.
        """

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
                for name, _ctype in rdData._fields_:
                    if name != "padToCacheLine":
                        setattr(rdProcessedData, name, getattr(rdData, name))
                self.rdProcessedCache.append(rdProcessedData)
                vLaserNum = 1 + ((rdData.laserUsed >> 2) & 0x7) # 1-based virtual laser number
                wlmAngle[vLaserNum-1].append(rdData.wlmAngle)
                laserTemperature[vLaserNum-1].append(rdData.laserTemperature)
                cacheIndex[vLaserNum-1].append(index)
                index += 1
            except Queue.Empty:
                break
        # Do the angle to wavenumber conversions for each available laser
        for vLaserNum in range(1, self.numLasers+1):
            if cacheIndex[vLaserNum-1]: # There are angles to convert for this laser
                self._assertVLaserNum(vLaserNum)
                freqConv = self.freqConverter[vLaserNum-1]
                waveNumbers = freqConv.thetaCalAndLaserTemp2WaveNumber(array(wlmAngle[vLaserNum-1]),
                                                            array(laserTemperature[vLaserNum-1]))
                for i, waveNumber in enumerate(waveNumbers):
                    index = cacheIndex[vLaserNum-1][i]
                    rdProcessedData = self.rdProcessedCache[index]
                    rdProcessedData.waveNumber = waveNumber
                    # At this point schemeVersionAndTable only has the scheme table
                    schemeTable = rdProcessedData.schemeVersionAndTable
                    if schemeTable in self.freqScheme:
                        freqScheme = self.freqScheme[schemeTable]
                        # Here we prepend the version to schemeVersionAndTable
                        shiftedVersion = (freqScheme.version << interface.SCHEME_VersionShift)
                        rdProcessedData.schemeVersionAndTable = schemeTable | shiftedVersion
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

    def updateWarmBoxCal(self, warmBoxCalFilePathActive):
        self.resetWarmBoxCalTime()
        self.RPC_updateWarmBoxCal(warmBoxCalFilePathActive)

    def runSaveWlmHistory(self):
        while True:
            self._saveWlmHistory()
            #Log("WLM history saved in database")
            time.sleep(self.saveWlmHistPeriod_s)

    def _saveWlmHistory(self):
        """Save WLM history to the state database"""
        for i in self.freqConverter:
            try:
                freqConv = self.freqConverter[i]
                if freqConv is not None:
                    vLaserNum = i+1
                    wlmOffset = freqConv.offset
                    deltaCoeffs = freqConv.coeffs - freqConv.coeffsOrig
                    valMin = deltaCoeffs.min()
                    valMax = deltaCoeffs.max()
                    freqMin = freqConv.sLinear[1] + deltaCoeffs.argmin()*freqConv.sLinear[0]
                    freqMax = freqConv.sLinear[1] + deltaCoeffs.argmax()*freqConv.sLinear[0]
                    timestamp = Driver.hostGetTicks()
                    wlmHist = (timestamp, vLaserNum, wlmOffset, freqMin, valMin, freqMax, valMax)
                    Driver.saveWlmHist(wlmHist)
            except Exception, exc:
                Log("Exception in saveWlmHistory: %s" % exc)

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

    def RPC_angleToLaserTemperature(self, vLaserNum, angles):
        self._assertVLaserNum(vLaserNum)
        return self.freqConverter[vLaserNum-1].thetaCal2LaserTemp(angles)

    def RPC_angleToWaveNumber(self, vLaserNum, angles):
        self._assertVLaserNum(vLaserNum)
        return self.freqConverter[vLaserNum-1].thetaCal2WaveNumber(angles)

    def RPC_setCavityLengthTuning(self):
        """ Set the instrument to use cavity length tuning, and load up DAS registers appropriately """
        Driver.wrDasReg("ANALYZER_TUNING_MODE_REGISTER", interface.ANALYZER_TUNING_CavityLengthTuningMode)
        self.tuningMode = interface.ANALYZER_TUNING_CavityLengthTuningMode
        self.cavityLengthTunerAdjuster.setTunerRegisters(self.tunerCenter)

    def RPC_setLaserCurrentTuning(self):
        """ Set the instrument to use laser current tuning, and load up DAS registers appropriately """
        Driver.wrDasReg("ANALYZER_TUNING_MODE_REGISTER", interface.ANALYZER_TUNING_LaserCurrentTuningMode)
        self.tuningMode = interface.ANALYZER_TUNING_LaserCurrentTuningMode
        self.laserCurrentTunerAdjuster.setTunerRegisters(centerValue=32768)

    def RPC_setFsrHoppingTuning(self):
        """ Set the instrument to use FSR Hopping tuning, and load up DAS registers appropriately """
        Driver.wrDasReg("ANALYZER_TUNING_MODE_REGISTER", interface.ANALYZER_TUNING_FsrHoppingTuningMode)
        self.tuningMode = interface.ANALYZER_TUNING_FsrHoppingTuningMode

    def RPC_centerTuner(self, tunerCenter):
        if self.tunerCenter:
            tunerTarget = self.tunerCenter
        else:
            tunerTarget = tunerCenter

        if self.tuningMode == interface.ANALYZER_TUNING_CavityLengthTuningMode:
            self.cavityLengthTunerAdjuster.setTunerRegisters(tunerTarget)
        elif self.tuningMode == interface.ANALYZER_TUNING_LaserCurrentTuningMode:
            self.laserCurrentTunerAdjuster.setTunerRegisters(tunerTarget)

    def RPC_clearCalibrationDone(self, vLaserNumList):
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
                dataByLaser[vLaserNum] = ([], [])
            dataByLaser[vLaserNum][0].append(i)
            dataByLaser[vLaserNum][1].append(waveNum)
        for vLaserNum in dataByLaser:
            self._assertVLaserNum(vLaserNum)
            freqConv = self.freqConverter[vLaserNum-1]
            waveNum = array(dataByLaser[vLaserNum][1])
            wlmAngle = freqConv.waveNumber2ThetaCal(waveNum)
            laserTemp = freqConv.thetaCal2LaserTemp(wlmAngle)
            for j, i in enumerate(dataByLaser[vLaserNum][0]):
                angleScheme.setpoint[i] = wlmAngle[j]
                # Add in scheme.laserTemp as an offset to the value calculated
                angleScheme.laserTemp[i]= laserTemp[j] + scheme.laserTemp[i]
        self.isAngleSchemeConverted[schemeNum] = True

    def RPC_getHotBoxCalFilePath(self):
        return self.hotBoxCalFilePath

    def RPC_getHotBoxCalParam(self, secName, optName):
        return self.hotBoxCal[secName][optName]

    def RPC_getWarmBoxCalFilePath(self):
        return self.warmBoxCalFilePath

    def RPC_isCalibrationDone(self, vLaserNumList):
        # Check if calibration has been done for the specified list of virtual lasers
        return self.sbc.isCalibrationDone(vLaserNumList)

    def RPC_laserTemperatureToAngle(self, vLaserNum, laserTemperatures):
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
            raise ValueError("Hot box calibration must contain at least one of " +
                             "CAVITY_LENGTH_TUNING or LASER_CURRENT_TUNING sections.")
        if "CAVITY_LENGTH_TUNING" in self.hotBoxCal:
            self.cavityLengthTunerAdjuster = TunerAdjuster("CAVITY_LENGTH_TUNING")
        else:
            self.cavityLengthTunerAdjuster = None
        if "LASER_CURRENT_TUNING" in self.hotBoxCal:
            self.laserCurrentTunerAdjuster = TunerAdjuster("LASER_CURRENT_TUNING")
        else:
            self.laserCurrentTunerAdjuster = None
        self.dthetaMax = float(self.hotBoxCal["AUTOCAL"]["MAX_ANGLE_TARGETTING_ERROR"])
        self.dtempMax  = float(self.hotBoxCal["AUTOCAL"]["MAX_TEMP_TARGETTING_ERROR"])
        # Set up the PZT scaling register
        if "PZT_SCALE_FACTOR" in self.hotBoxCal["CAVITY_LENGTH_TUNING"]:
            pztScale = int(self.hotBoxCal["CAVITY_LENGTH_TUNING"]["PZT_SCALE_FACTOR"])
        else:
            pztScale = 0xFFFF
        Driver.wrFPGA("FPGA_SCALER","SCALER_SCALE1", int(pztScale))
        # Set up the PZT_INCR_PER_CAVITY_FSR register
        fsr = float(self.hotBoxCal["CAVITY_LENGTH_TUNING"]["FREE_SPECTRAL_RANGE"])
        Driver.wrDasReg("PZT_INCR_PER_CAVITY_FSR", fsr)

        return "OK"

    def RPC_loadWarmBoxCal(self, warmBoxCalFilePath="", pCalOffset=None):
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

        if not self.virtualMode:
            self.warmBoxCalUpdateTime = Driver.hostGetTicks()
        if warmBoxCalFilePath == "":
            if os.path.isfile(self.warmBoxCalFilePathActive):
                try:
                    validateChecksum(self.warmBoxCalFilePathActive)
                    self.warmBoxCalFilePath = self.warmBoxCalFilePathActive
                except ValueError:
                    Log('Bad checksum in active warm box calibration file, using factory file', Level = 2)
                    self.warmBoxCalFilePath = self.warmBoxCalFilePathFactory
            else:
                Log('No active warm box calibration file, using factory file', Level = 0)
                self.warmBoxCalFilePath = self.warmBoxCalFilePathFactory
        else:
            self.warmBoxCalFilePath = os.path.abspath(warmBoxCalFilePath)

        # Load up the frequency converters for each laser in the DAS...
        ini = CustomConfigObj(self.warmBoxCalFilePath)
        for vLaserNum in range(1, self.numLasers + 1): # N.B. In AutoCal, laser indices are 1 based
            freqConv = AutoCal()
            self.freqConverter[vLaserNum-1] = freqConv.loadFromIni(ini, vLaserNum)
            # Send the virtual laser information to the DAS
            paramSec = "VIRTUAL_PARAMS_%d" % vLaserNum
            if paramSec in ini:
                param = ini[paramSec]
                aLaserNum = int(ini["LASER_MAP"]["ACTUAL_FOR_VIRTUAL_%d" % vLaserNum])
                laserParams = { 'actualLaser':     aLaserNum-1,
                                'ratio1Center':    float(param['RATIO1_CENTER']),
                                'ratio1Scale':     float(param['RATIO1_SCALE']),
                                'ratio2Center':    float(param['RATIO2_CENTER']),
                                'ratio2Scale':     float(param['RATIO2_SCALE']),
                                'phase':           float(param['PHASE']),
                                'tempSensitivity': float(param['TEMP_SENSITIVITY']),
                                'calTemp':         float(param['CAL_TEMP']),
                                'calPressure':     float(param['CAL_PRESSURE']),
                                'pressureC0':      float(param['PRESSURE_C0']),
                                'pressureC1':      float(param['PRESSURE_C1']),
                                'pressureC2':      float(param['PRESSURE_C2']),
                                'pressureC3':      float(param['PRESSURE_C3'])}
                if pCalOffset is not None:
                    laserParams['calPressure'] = 760.0
                    laserParams['pressureC0'] = pCalOffset
                    laserParams['pressureC1'] = 0.0
                    laserParams['pressureC2'] = 0.0
                    laserParams['pressureC3'] = 0.0
                if not self.virtualMode:
                    Driver.wrVirtualLaserParams(vLaserNum, laserParams)
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

    def RPC_replaceOriginalWlmCal(self, vLaserNum):
        # Copy current spline coefficients to original coefficients
        self._assertVLaserNum(vLaserNum)
        self.freqConverter[vLaserNum-1].replaceOriginal()

    def RPC_restoreOriginalWlmCal(self, vLaserNum):
        # Replace current spline coefficients with original spline coefficients
        self._assertVLaserNum(vLaserNum)
        self.freqConverter[vLaserNum-1].replaceCurrent()

    def RPC_ignoreSpline(self, vLaserNum):
        # Do not use cubic spline corrections for angle to frequency transformations for virtual laser vLaserNum
        if (vLaserNum-1 in self.freqConverter) and self.freqConverter[vLaserNum-1] is not None:
            self.freqConverter[vLaserNum-1].ignoreSpline = True

    def RPC_useSpline(self, vLaserNum):
        # Do use cubic spline corrections for angle to frequency transformations for virtual laser vLaserNum
        if (vLaserNum-1 in self.freqConverter) and self.freqConverter[vLaserNum-1] is not None:
            self.freqConverter[vLaserNum-1].ignoreSpline = False

    def RPC_setHotBoxCalParam(self, secName, optName, optValue):
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

    def RPC_getLaserTempOffset(self, vLaserNum):
        """Fetches the temp offset for the virtual laser. vLaserNum is 1-based.
        Returns offset in degrees.
        """
        self._assertVLaserNum(vLaserNum)
        return self.freqConverter[vLaserNum-1].getTempOffset()

    def RPC_setLaserTempOffset(self, vLaserNum, offset):
        """Updates the Temp offset for the virtual laser.
        vLaserNum is 1-based. offset is in degrees.
        """
        self._assertVLaserNum(vLaserNum)
        self.freqConverter[vLaserNum-1].setTempOffset(offset)

    def RPC_shutdown(self):
        self._shutdownRequested = True

    def RPC_updateHotBoxCal(self, fileName=None):
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
            if fp is not None:
                fp.close()

    def RPC_getWarmBoxConfig(self):
        config = CustomConfigObj(self.warmBoxCalFilePath)
        for i in self.freqConverter.keys():
            freqConv = self.freqConverter[i]
            if freqConv is not None:
                freqConv.updateIni(config, i+1) # Note: In Autocal1, laser indices are 1 based
        return config

    def RPC_updateWarmBoxCal(self, fileName=None):
        """
        Write calibration back to the file with a new checksum.
        """
        # Archive the current WarmBoxCal file if this is not null, first adding timestamp to the filename)
        if not self.warmBoxCalFilePath:
            return

        timeStamp = datetime.datetime.today().strftime("%Y%m%d_%H%M%S")
        warmBoxCalFilePathWithTime = self.warmBoxCalFilePath.replace(".ini", "_%s.ini" % timeStamp)
        shutil.copy2(self.warmBoxCalFilePath, warmBoxCalFilePathWithTime)
        Archiver.ArchiveFile(self.wbArchiveGroup, warmBoxCalFilePathWithTime, True)
        Log("Archived %s" % warmBoxCalFilePathWithTime)

        filePtr = None
        config = CustomConfigObj(self.warmBoxCalFilePath)
        for i in self.freqConverter.keys():
            freqConv = self.freqConverter[i]
            if freqConv is not None:
                freqConv.updateIni(config, i+1) # Note: In Autocal1, laser indices are 1 based
        try:
            config["timestamp"] = Driver.hostGetTicks()
            calStrIO = StringIO()
            config.write(calStrIO)
            calStr = calStrIO.getvalue()
            calStr = calStr[:calStr.find("#checksum=")]
            checksum = crc32(calStr, 0)
            calStr += "#checksum=%d" % checksum
            if fileName is not None:
                self.warmBoxCalFilePath = fileName
            filePtr = file(self.warmBoxCalFilePath, "wb")
            filePtr.write(calStr)
        finally:
            calStrIO.close()
            if filePtr is not None:
                filePtr.close()

    def RPC_updateWlmCal(self, vLaserNum, thetaCal, waveNumbers, weights, relax=5e-3,
                         relative=True, relaxDefault=5e-3, relaxZero=5e-5, maxDiff=0.4):
        """Updates the wavelength monitor calibration using the information that angles specified as "thetaCal"
           map to the specified list of waveNumbers. Also relax the calibration towards the default using
           Laplacian regularization and the specified value of relaxDefault."""
        self._assertVLaserNum(vLaserNum)
        self.freqConverter[vLaserNum-1].updateWlmCal(thetaCal, waveNumbers, weights, relax,
                                                     relative, relaxDefault, relaxZero, maxDiff)

    def RPC_uploadSchemeToDAS(self, schemeNum):
        # Upload angle scheme to DAS
        if not self.isAngleSchemeConverted[schemeNum]:
            raise Exception("Scheme not converted to angle yet.")
        angleScheme = self.angleScheme[schemeNum]
        Driver.wrScheme(schemeNum, *(angleScheme.repack()))

    def RPC_waveNumberToAngle(self, vLaserNum, waveNumbers):
        self._assertVLaserNum(vLaserNum)
        return self.freqConverter[vLaserNum-1].waveNumber2ThetaCal(waveNumbers)

    def RPC_wrFreqScheme(self, schemeNum, freqScheme):
        self.freqScheme[schemeNum] = freqScheme
        self.angleScheme[schemeNum] = freqScheme.makeAngleTemplate()
        self.isAngleSchemeConverted[schemeNum] = False


class TunerAdjuster(object):
    def __init__(self, section):
        rdFreqConv = RDFrequencyConverter()
        self.ditherAmplitude   = float(rdFreqConv.RPC_getHotBoxCalParam(section,"DITHER_AMPLITUDE"))
        self.freeSpectralRange = float(rdFreqConv.RPC_getHotBoxCalParam(section,"FREE_SPECTRAL_RANGE"))
        self.minValue          = float(rdFreqConv.RPC_getHotBoxCalParam(section,"MIN_VALUE"))
        self.maxValue          = float(rdFreqConv.RPC_getHotBoxCalParam(section,"MAX_VALUE"))
        self.upSlope           = float(rdFreqConv.RPC_getHotBoxCalParam(section,"UP_SLOPE"))
        self.downSlope         = float(rdFreqConv.RPC_getHotBoxCalParam(section,"DOWN_SLOPE"))
    def findCenter(self, value, minCen, maxCen, fsr):
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
            if abs(value + n1*fsr - minCen) < abs(value + (n2+1)*fsr - maxCen):
                return minCen
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
        centerMax = self.maxValue - ditherPeakToPeak // 2 - rampAmpl
        centerMin = self.minValue + ditherPeakToPeak // 2 + rampAmpl
        if centerMin > centerMax:
            # We need to use the maximum range available
            centerValue = 0.5*(self.minValue + self.maxValue)
            rampAmpl = self.maxValue - centerValue - ditherPeakToPeak // 2
            if 2*rampAmpl < self.freeSpectralRange:
                Log("Insufficient PZT range to cover cavity FSR",
                    dict(fsr = self.freeSpectralRange, rampAmpl = rampAmpl), Level=2)
        else:
            centerValue = self.findCenter(centerValue, centerMin, centerMax, self.freeSpectralRange)

        Driver.wrDasReg("TUNER_WINDOW_RAMP_HIGH_REGISTER", centerValue + rampAmpl)
        Driver.wrDasReg("TUNER_WINDOW_RAMP_LOW_REGISTER", centerValue - rampAmpl)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_HIGH_REGISTER", centerValue + rampAmpl + ditherPeakToPeak // 2)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_LOW_REGISTER",  centerValue - rampAmpl - ditherPeakToPeak // 2)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER", ditherPeakToPeak // 2)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER", ditherPeakToPeak // 2)
        Driver.wrDasReg("TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER", (windowFactor * ditherPeakToPeak) // 2)
        Driver.wrDasReg("TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER", (windowFactor * ditherPeakToPeak) // 2)
        Driver.wrFPGA("FPGA_TWGEN", "TWGEN_SLOPE_UP", int(self.upSlope))
        Driver.wrFPGA("FPGA_TWGEN", "TWGEN_SLOPE_DOWN", int(self.downSlope))

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
    longOpts = ["help", "vi"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, exc:
        print "%s %r" % (exc, exc)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    opts = {}
    for opt, arg in switches:
        opts.setdefault(opt, arg)
    if "/?" in args or "/h" in args:
        opts.setdefault('-h',"")
    #Start with option defaults...
    configFile = os.path.splitext(AppPath)[0] + ".ini"
    if "-h" in opts or "--help" in opts:
        printUsage()
        sys.exit()
    if "-c" in opts:
        configFile = opts["-c"]
    if "--vi" in opts:
        virtualMode = True
    else:
        virtualMode = False
    return configFile, virtualMode, opts

if __name__ == "__main__":
    configFilename, virtualMode, options = handleCommandSwitches()
    rdFreqConvertApp = RDFrequencyConverter(configFilename, virtualMode)
    Log("%s started." % APP_NAME, dict(ConfigFile = configFilename), Level = 0)
    rdFreqConvertApp.run()
    Log("Exiting program")