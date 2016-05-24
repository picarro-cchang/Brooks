from collections import deque
import json
from mock import call, MagicMock
import numpy as np
import os
import sys
import tempfile
import traceback
import unittest
from Host.Pipeline.Blocks import Pipeline
from Host.Pipeline.CaptureBlocks import CaptureAnalyzerBlock
from traitlets.config import Config
import pylab as plt

class CaptureBlockTest(unittest.TestCase):
    def test_capture1(self):
        myconfig = Config()
        myconfig.CaptureAnalyzerBlock.captureType = "Ethane"              # Type of capture mode to use
        myconfig.CaptureAnalyzerBlock.methane_ethane_sdev_ratio = 0.2     # Ratio of methane conc. sdev to ethane conc. sdev
        myconfig.CaptureAnalyzerBlock.methane_ethylene_sdev_ratio = 0.09  # Ratio of methane conc. sdev to ethylene conc. sdev
        myconfig.EthaneClassifier.nng_lower = 0.0  # Lower limit of ratio for not natural gas hypothesis
        myconfig.EthaneClassifier.nng_upper = 0.1e-2  # Upper limit of ratio for not natural gas hypothesis
        myconfig.EthaneClassifier.ng_lower = 2e-2  # Lower limit of ratio for natural gas hypothesis
        myconfig.EthaneClassifier.ng_upper = 10e-2  # Upper limit of ratio for natural gas hypothesis
        myconfig.EthaneClassifier.nng_prior = 0.27  # Prior probability of not natural gas hypothesis
        myconfig.EthaneClassifier.thresh_confidence = 0.9  # Threshold confidence level for definite hypothesis
        myconfig.EthaneClassifier.reg = 0.05  # Regularization parameter

        # Synthesize a data set consisting of a peak followed by a replay
        # We minimally need the methane and ethane concentrations, together with a valve mask
        # and a peak detector state time series
        # PeakDetectStates:
        # Idle=0, Armed=1, TriggerPending=2, Triggered=3, Inactive=4, Cancelling=5
        # Priming=6, Purging=7, InjectionPending=8, Transitioning=9, Holding=10
        t = np.arange(0, 250, 0.25)
        tPulse = 5.0
        wPulse = 1.5
        tReplayPeak = 100.0 + tPulse
        tBaseStart = tPulse + 3.5
        tHoldStart = tReplayPeak + 0.5
        tStop = 200.0
        A = 0.07
        ratio = 0.03
        pulse = A * np.exp(-0.5*((t-tPulse) / wPulse) **2) + A * np.exp(-0.5 * ((t-tReplayPeak) / wPulse) **2)
        pulse[t>=tHoldStart] = pulse[t==tHoldStart]
        pulse[t>=tPulse] = np.maximum(pulse[t>=tPulse], pulse[t==tBaseStart])
        pulse[t>=tStop] = 0
        ch4 = 0.5 + pulse + 0.001 * np.random.randn(len(pulse))
        c2h6 =  ratio * pulse + 0.004 * np.random.randn(len(pulse))
        valveMask = np.zeros_like(pulse)
        valveOffset = 0.0
        peakDetectorOffset = 0.0
        valveMask[(t>=tBaseStart+valveOffset) & (t<tStop+valveOffset)] = 3
        valveMask[t<=tPulse+valveOffset] = 8
        #valveMask[(t>=tHoldStart) & (t<tHoldStart + 2.0)] = 16
        peakDetectState = np.zeros_like(pulse)
        peakDetectState[t<tPulse+peakDetectorOffset] = 1
        peakDetectState[(t>=tPulse+peakDetectorOffset) & (t<tBaseStart+peakDetectorOffset)] = 2
        peakDetectState[(t>=tBaseStart+peakDetectorOffset) & (t<tReplayPeak-3*wPulse+peakDetectorOffset)] = 3
        peakDetectState[(t>=tReplayPeak-3*wPulse+peakDetectorOffset) & (t<tHoldStart+peakDetectorOffset)] = 9
        peakDetectState[(t>=tHoldStart+peakDetectorOffset) & (t<tStop+peakDetectorOffset)] = 10
        # Create a mock data set
        data = []
        for i in range(len(t)):
            data.append(dict(EPOCH_TIME=1300000000+t[i], ValveMask=valveMask[i], peak_detector_state=peakDetectState[i],
                             CH4=ch4[i], C2H6=c2h6[i], species=170))

        cab = CaptureAnalyzerBlock(config=myconfig)
        for newDat in data:
            for result in cab.newData(newDat):
                print result

        #ax1 = plt.subplot(4, 1, 1)
        #plt.plot(t, ch4)
        #plt.subplot(4, 1, 2, sharex=ax1)
        #plt.plot(t, c2h6)
        #plt.subplot(4, 1, 3, sharex=ax1)
        #plt.plot(t, valveMask)
        #plt.subplot(4, 1, 4, sharex=ax1)
        #plt.plot(t, peakDetectState)
        #plt.show()

if __name__ == "__main__":
    unittest.main()