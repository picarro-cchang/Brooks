# Implementation of capture algorithm for ethane analyzer

from Host.Pipeline.Blocks import TransformManyBlock
from Host.Pipeline.EthaneBlocks import ratio_analysis, EthaneClassifier

import numpy as np
import sys
from traitlets import (Bool, Dict, Enum, Float, HasTraits, Instance, Integer, List, Unicode)
import cPickle

def checkPeakDectectorHolding(value):
    ivalue = int(value)
    return bool(abs(value-ivalue) <= 1.0e-4 and ivalue == 10)

def checkPeakDectectorCancelling(value):
    ivalue = int(value)
    return bool(abs(value-ivalue) <= 1.0e-4 and ivalue == 5)

def checkPeakDectectorSurveying(value):
    ivalue = int(value)
    return bool(abs(value-ivalue) <= 1.0e-4 and ivalue == 0)

def checkPeakDetectorTriggered(value):
    ivalue = int(value)
    return bool(abs(value-ivalue) <= 1.0e-4 and ivalue == 3)

def checkValveCancelling(value):
    mask = 0x10
    ivalue = int(value)
    return bool(abs(value-ivalue) <= 1.0e-4 and (ivalue & mask) != 0)

def checkValveCollecting(value):
    mask = 0x1
    ivalue = int(value)
    return bool(abs(value-ivalue) <= 1.0e-4 and (ivalue & mask) != 0)

def checkValveReferenceGasInjection(value):
    mask = 0x8
    ivalue = int(value)
    return bool(abs(value-ivalue) <= 1.0e-4 and (ivalue & mask) != 0)

def checkValveSurveying(value):
    # Need to mask off valve 6 which is used for EQ
    return bool((abs(value) <= 1.0e-4) or (abs(value-32) <= 1.0e-4))

def linfit(x,y,sigma):
    # Calculate the linear fit of (x,y) to a line, where sigma are the errors in the y values
    S = sum(1/sigma**2)
    Sx = sum(x/sigma**2)
    Sy = sum(y/sigma**2)
    t = (x-Sx/S)/sigma
    Stt = sum(t**2)
    b = sum(t*y/sigma)/Stt
    a = (Sy-Sx*b)/S
    sa2 = (1+Sx**2/(S*Stt))/S
    sb2 = 1/Stt
    return a, b, np.sqrt(sa2), np.sqrt(sb2)

class IsotopicIdentity(HasTraits): # Fetch from database
    noLowerBound = Float(-45.0)
    yesLowerBound = Float(-38.0)
    yesUpperBound = Float(-25.0)
    noUpperBound = Float(-10.0)

class CaptureAnalyzerBlock(TransformManyBlock):
    baseBuffer = List()
    baseSkipPoints = Integer(0)
    captureType = Enum(("Ethane", "Isotopic"), default_value="Ethane", config=True)
    concentrationHighThreshold = Float(20.0)
    delayBuffer = List()
    deltaPositiveThreshold = Float(0.0)
    deltaNegativeThreshold = Float(-80.0)
    doneAnalysisThreshold = Integer(5)
    ethaneClassifier = Instance(EthaneClassifier)
    ethaneRatioPositiveThreshold = Float(0.1)
    ethaneRatioNegativeThreshold = Float(-0.05)
    ethaneRatioSdevHighThreshold = Float(0.05)
    hasTooFewPoints = Bool(False)
    isCancelled = Bool(False)
    isHandlingCancellation = Bool(False)
    isotopicIdentity = Instance(IsotopicIdentity)
    keelingBuffer = List()
    keelingEndpointOffset = Integer(6)
    keelingSamplesToSkip = Integer(24)
    lastAnalysis = Dict(allow_none=True)
    lastCollecting = Bool(False)
    lastPeak = Dict(allow_none=True)
    maxDurationSeconds = Float(30.0)
    measBuffer = List()
    methane_ethane_sdev_ratio = Float(None, allow_none=True, config=True)
    methane_ethylene_sdev_ratio = Float(None, allow_none=True, config=True)
    minBaseSamples = Integer(100)
    minKeelingSamples = Integer(10)
    minPeakSamples = Integer(100)
    notCollectingCount = Integer(0)
    peakBuffer = List()
    peakSkipPoints = Integer(15)
    referenceGas = Bool(False)
    referenceGasEthaneRatioValue = Float(0.030) # Look up in table
    referenceGasEthaneRatioValueTolerance = Float(0.010)
    referenceGasIsotopicValue = Float(-35.0) # Look up in table
    referenceGasIsotopicValueTolerance = Float(2.5)
    sigmaUncertainty = 11.0
    transportDurationSeconds = Float(5.0)
    uncertaintyHighThreshold = Float(5.0)

    def __init__(self, **kwargs):
        super(CaptureAnalyzerBlock, self).__init__(self.newData, **kwargs)
        self.delayBuffer = []
        self.measBuffer = []
        self.keelingBuffer = []
        self.baseBuffer = []
        self.peakBuffer = []
        self.ethaneClassifier = EthaneClassifier(config=self.config)
        self.isotopicIdentity = IsotopicIdentity()
        self.lastAnalysis = None

    def getDispositionAndConfidence(self):
        if self.isCancelled:
            return 'USER_CANCELLATION', float('nan')
        elif self.hasTooFewPoints:
            return 'SAMPLE_SIZE_TOO_SMALL', float('nan')
        if self.lastAnalysis is None:
            print 'ERROR: Last Analysis cannot be none for disposition determination'
            return 'ERROR', float('nan')
        elif self.captureType == 'Isotopic':
            return self.getIsotopicDisposition(), float('nan')
        elif self.captureType == 'Ethane':
            return self.getEthaneDispositionAndConfidence()
        else:
            raise RuntimeError('Unknown captureType')

    def getIsotopicDisposition(self):
        delta = self.lastAnalysis["delta"]
        uncertainty = self.lastAnalysis["uncertainty"]
        if uncertainty > self.uncertaintyHighThreshold:
            return 'UNCERTAINTY_OUT_OF_RANGE'
        elif delta <= self.deltaNegativeThreshold or delta >= self.deltaPositiveThreshold:
            return 'DELTA_OUT_OF_RANGE'
        else:
            if self.referenceGas:
                rangeMin = delta - uncertainty
                rangeMax = delta + uncertainty
                if (rangeMin < self.referenceGasIsotopicValue - self.referenceGasIsotopicValueTolerance or
                    rangeMax > self.referenceGasIsotopicValue + self.referenceGasIsotopicValueTolerance):
                    return 'ISOTOPIC_REFERENCE_FAIL'
                else:
                    return 'ISOTOPIC_REFERENCE_PASS'
            else:
                rangeMin = delta - uncertainty
                rangeMax = delta + uncertainty
                if rangeMin <= self.deltaNegativeThreshold or rangeMax >= self.deltaPositiveThreshold:
                    return 'DELTA_OUT_OF_RANGE'
                else:
                    if (rangeMin >= self.isotopicIdentity.yesLowerBound and
                        rangeMax < self.isotopicIdentity.yesUpperBound):
                        return 'NATURAL_GAS'
                    elif (rangeMin >= self.isotopicIdentity.noUpperBound or
                          rangeMax < self.isotopicIdentity.noLowerBound):
                        return 'NOT_NATURAL_GAS'
                    else:
                        return 'POSSIBLE_NATURAL_GAS'

    def getEthaneDispositionAndConfidence(self):
        ethane_ratio = self.lastAnalysis["ethane_ratio"]
        ethane_ratio_sdev = self.lastAnalysis["ethane_ratio_sdev"]
        if ethane_ratio_sdev > self.ethaneRatioSdevHighThreshold:
            return 'ETHANE_RATIO_SDEV_OUT_OF_RANGE', float('nan')
        elif ethane_ratio <= self.ethaneRatioNegativeThreshold or ethane_ratio >= self.ethaneRatioPositiveThreshold:
            return 'ETHANE_RATIO_OUT_OF_RANGE', float('nan')
        else:
            if self.referenceGas:
                rangeMin = ethane_ratio - ethane_ratio_sdev
                rangeMax = ethane_ratio + ethane_ratio_sdev
                if (rangeMin < self.referenceGasEthaneRatioValue - self.referenceGasEthaneRatioValueTolerance or
                    rangeMax > self.referenceGasEthaneRatioValue + self.referenceGasEthaneRatioValueTolerance):
                    return 'ETHANE_REFERENCE_FAIL', float('nan')
                else:
                    return 'ETHANE_REFERENCE_PASS', float('nan')
            else:
                verdict, confidence = self.ethaneClassifier.verdict(ethane_ratio, ethane_ratio_sdev)
                return verdict, confidence

    def newData(self, newDat):
        # collecting => tape recorder is playing back
        # not collecting => analyzer samples inlet directly
        result = None
        isTriggered = False
        isHolding = False
        if self.captureType == "Ethane":
            isTriggered = checkPeakDetectorTriggered(newDat['PeakDetectorState'])
            isHolding = checkPeakDectectorHolding(newDat['PeakDetectorState'])

        isCollecting = checkValveCollecting(newDat['ValveMask'])
        # Delay collecting state by transportLag to compensate for valve switching
        self.delayBuffer.append(newDat)
        while self.delayBuffer[-1]["EPOCH_TIME"] - self.delayBuffer[0]["EPOCH_TIME"] > self.transportDurationSeconds:
            oldDat = self.delayBuffer.pop(0)
            isCollecting = checkValveCollecting(oldDat['ValveMask'])

#        if checkValveSurveying(newDat['ValveMask']):
        if checkPeakDectectorSurveying(newDat['PeakDetectorState']):
            self.isHandlingCancellation = False

        if not self.isHandlingCancellation:
            result = self.acquisitionActive(newDat, isCollecting, isTriggered, isHolding)

        self.lastCollecting = isCollecting

        if result is not None:
            yield result

    def acquisitionActive(self, newDat, isCollecting, isTriggered, isHolding):
#        if checkValveCancelling(newDat['ValveMask']):
        if checkPeakDectectorCancelling(newDat['PeakDetectorState']):
            self.isHandlingCancellation = True
            self.isCancelled = True  # For benefit of getDispositionAndConfidence()
            disposition, confidence = self.getDispositionAndConfidence()
            result = dict(
                delta=float('nan'),
                uncertainty=float('nan'),
                ethane_ratio=float('nan'),
                ethane_ratio_sdev=float('nan'),
                replayMax=float('nan'),
                replayLMin=float('nan'),
                replayRMin=float('nan'),
                disposition=disposition,
                confidence=confidence,
                referenceGas=self.referenceGas,
                data=newDat)
            self.isCancelled = False
            self.lastPeak = None
            self.lastAnalysis = None
            self.hasTooFewPoints = False
            self.lastCollecting = isCollecting
            self.referenceGas = False
            self.keelingBuffer = []
            self.baseBuffer = []
            self.peakBuffer = []
            return result

        if checkValveReferenceGasInjection(newDat['ValveMask']):
            self.referenceGas = True

        if self.notCollectingCount > self.doneAnalysisThreshold and self.lastAnalysis is not None:
            disposition, confidence = self.getDispositionAndConfidence()
            self.lastAnalysis["disposition"] = disposition
            self.lastAnalysis["confidence"] = confidence
            result = self.lastAnalysis
            self.lastPeak = None
            self.lastAnalysis = None
            self.isCancelled = False
            self.hasTooFewPoints = False
            self.lastCollecting = isCollecting
            self.referenceGas = False
            return result

        if not isCollecting:
            # Phase I/IV: We are between T1 & T2 or after T3
            # Keep filling up measurement buffer with unstretched peak data
            self.notCollectingCount += 1
            self.measBuffer.append(newDat)
            while self.measBuffer[-1]["EPOCH_TIME"] - self.measBuffer[0]["EPOCH_TIME"] > self.maxDurationSeconds:
                self.measBuffer.pop(0)
            if self.lastCollecting:
                # We have just transitioned from replay (filling up Keeling buffer) back to real-time
                #  acquisition
                if self.captureType == 'Isotopic':
                    self.doKeelingAnalysis()
                elif self.captureType == 'Ethane':
                    self.doEthaneAnalysis()
        else:
            # Phase II/III: We are between T2 & T3
            # Tape recorder is playing back, keep filling up Keeling buffer
            self.notCollectingCount = 0
            if self.captureType == 'Isotopic':
                if newDat["CH4"] <= self.concentrationHighThreshold:
                    self.keelingBuffer.append(newDat)
            elif self.captureType == 'Ethane':
                if isTriggered:
                    self.baseBuffer.append(newDat)
                elif isHolding:
                    self.peakBuffer.append(newDat)

            if (not self.lastCollecting) and len(self.measBuffer)>0:
                # We have just transitioned from real-time acquisition to replay of the tape recorder
                # This is the time T2. We need to find the peak in measBuff to associate with the
                #  upcoming capture analysis
                ch4 = np.asarray([dat["CH4"] for dat in self.measBuffer])
                self.lastPeak = self.measBuffer[np.argmax(ch4)]
                self.measBuffer = []

    def doEthaneAnalysis(self):
        if len(self.baseBuffer) >= self.minBaseSamples:
            if len(self.peakBuffer) < self.minPeakSamples:
                self.setTooFewPoints()
            else:
                baseCH4 = np.asarray([dat["CH4"] for dat in self.baseBuffer[self.baseSkipPoints:]])
                peakCH4 = np.asarray([dat["CH4"] for dat in self.peakBuffer[self.peakSkipPoints:]])
                baseC2H6 = np.asarray([dat["C2H6"] for dat in self.baseBuffer[self.baseSkipPoints:]])
                peakC2H6 = np.asarray([dat["C2H6"] for dat in self.peakBuffer[self.peakSkipPoints:]])
                methane = np.concatenate((baseCH4, peakCH4))
                ethane = np.concatenate((baseC2H6, peakC2H6))
                ethane_nominal_sdev = self.peakBuffer[0].get('ethane_nominal_dev', 0.004)
                ethane_ratio, ethane_ratio_sdev, methane_sdev, ethane_sdev, pip_energy, methane_ptp = \
                    ratio_analysis(methane, ethane, self.methane_ethane_sdev_ratio)
                # Make sure that the reported standard deviation is at least equal to the nominal value
                sdev_factor = max(ethane_nominal_sdev / ethane_sdev, 1.0)
                ethane_sdev *= sdev_factor
                methane_sdev *= sdev_factor
                ethane_ratio_sdev *= sdev_factor
                if self.lastPeak is not None:
                    self.lastAnalysis = dict(
                        delta=None,
                        uncertainty=None,
                        ethane_ratio=ethane_ratio,
                        ethane_ratio_sdev=ethane_ratio_sdev,
                        replayMax=np.mean(peakCH4),
                        replayLMin=np.mean(baseCH4),
                        replayRMin=np.mean(peakC2H6) - np.mean(baseC2H6),
                        disposition='UNKNOWN',
                        confidence=float('nan'),
                        referenceGas=self.referenceGas,
                        data=self.lastPeak)
                    self.lastPeak = None
        self.baseBuffer = []
        self.peakBuffer = []


    def doKeelingAnalysis(self):
        if len(self.keelingBuffer) > self.minKeelingSamples + self.keelingSamplesToSkip:
            self.hasTooFewPoints = False
            selectedSamples = self.keelingBuffer[self.keelingSamplesToSkip:-(self.doneAnalysisThreshold+self.keelingEndpointOffset)]
            ch4 = np.asarray([dat["CH4"] for dat in selectedSamples])
            delta = np.asarray([dat["HP_Delta_iCH4_Raw"] for dat in selectedSamples])
            if len(ch4)>0 and len(delta)>0:
                inverseCH4 = 1.0/np.maximum(ch4,0.001)
                sigmas = inverseCH4 * self.sigmaUncertainty
                replayMax = max(ch4)
                idxMax = np.argmax(ch4)
                if idxMax == 0:
                    replayLMin = ch4[0]
                    replayRMin = ch4[idxMax:]
                elif idxMax == len(ch4) - 1:
                    replayLMin = ch4[:idxMax]
                    replayRMin = ch4[-1]
                else:
                    replayLMin = min(ch4[:idxMax])
                    replayRMin = min(ch4[idxMax:])

                a,b,sigmaA,sigmaB = linfit(inverseCH4, delta, sigmas)

                if self.lastPeak is not None:
                    self.lastAnalysis = dict(
                        delta=a,
                        uncertainty=sigmaA,
                        ethane_ratio=float('nan'),
                        ethane_ratio_sdev=float('nan'),
                        replayMax=replayMax,
                        replayLMin=replayLMin,
                        replayRMin=replayRMin,
                        disposition='UNKNOWN',
                        confidence=float('nan'),
                        referenceGas=self.referenceGas,
                        data=self.lastPeak)
                    self.lastPeak = None
            else:
                self.setTooFewPoints()
        else:
            self.setTooFewPoints()
        self.keelingBuffer = []

    def setTooFewPoints(self):
        self.hasTooFewPoints = True
        if self.lastPeak is not None:
            self.lastAnalysis = dict(
                delta=float('nan'),
                uncertainty=float('nan'),
                ethane_ratio=float('nan'),
                ethane_ratio_sdev=float('nan'),
                replayMax=float('nan'),
                replayLMin=float('nan'),
                replayRMin=float('nan'),
                disposition='UNKNOWN',
                confidence=float('nan'),
                referenceGas=self.referenceGas,
                data=self.lastPeak)
            self.lastPeak = None
