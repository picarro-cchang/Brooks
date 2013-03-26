# Test locking of wavelength monitor using polar algorithms

import sys
import getopt
from numpy import *
import os
import Queue
import socket
import time
import threading
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

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

class TestFreqLocker:
    def teardown_class(self):
        self.listener.stop()
    def setup_class(self):
        def rdFilter(entry):
            assert isinstance(entry,RingdownEntryType)
            # Check when we get to the end of the scheme
            if (entry.status & RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask) or \
               (entry.status & RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask):
                self.processingDone.set()
            if not (entry.status & RINGDOWN_STATUS_RingdownTimeout):
                return entry
        self.seq = 0
        self.processingDone = threading.Event()
        self.queue = Queue.Queue()
        self.listener = Listener(self.queue,SharedTypes.BROADCAST_PORT_RDRESULTS,RingdownEntryType,rdFilter)
        
        
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
    def test_talkers(self):
        assert Driver.allVersions()["interface"] == 1
        assert RDFreqConv.getWarmBoxCalFilePath()
    def test_vLaserParams(self):
        lookup = {"TEMP_SENSITIVITY":"tempSensitivity",
                  "RATIO1_CENTER" : "ratio1Center", 
                  "RATIO2_CENTER" : "ratio2Center",
                  "RATIO1_SCALE" : "ratio1Scale", 
                  "RATIO2_SCALE" : "ratio2Scale",
                  "PHASE" : "phase",
                  "CAL_TEMP" : "calTemp",
                  "CAL_PRESSURE" : "calPressure",
                  "PRESSURE_C0" : "pressureC0",
                  "PRESSURE_C1" : "pressureC1",
                  "PRESSURE_C2" : "pressureC2",
                  "PRESSURE_C3" : "pressureC3",
                 }
        wp = RDFreqConv.getWarmBoxCalFilePath()
        wConfig = ConfigObj(wp)
        for vLaserNum in range(1,9):
            secName = "VIRTUAL_PARAMS_%d" % vLaserNum
            if secName in wConfig:
                print "vLaserNum: %d" % vLaserNum
                vLaserSec = wConfig[secName]
                vLaserDict = Driver.rdVirtualLaserParams(vLaserNum)
                for k in lookup:
                    assert allclose(float(vLaserSec[k]),float(vLaserDict[lookup[k]])),"Comparison of %s for virtual laser %s failed" % (k,vLaserNum)
                assert(int(wConfig["LASER_MAP"]["ACTUAL_FOR_VIRTUAL_%d" % vLaserNum]) == vLaserDict["actualLaser"]+1)        
    def test_convertAngle(self):
        vLaserNum = 1
        wp = RDFreqConv.getWarmBoxCalFilePath()
        wConfig = ConfigObj(wp)
        vLaserSec = wConfig["VIRTUAL_PARAMS_%d" % vLaserNum]
        aBase = float(vLaserSec["ANGLE_BASE"])
        aIncr = float(vLaserSec["ANGLE_INCREMENT"])
        nCoeffs = int(vLaserSec["NCOEFFS"])
        aCen = aBase+aIncr*nCoeffs//2
        # Check equally spaced angles go to equally spaced temperatures
        wlmAngles = linspace(aCen-pi,aCen+pi,51)
        laserTemps = RDFreqConv.angleToLaserTemperature(vLaserNum,wlmAngles)
        dTemp = diff(laserTemps)
        assert allclose(mean(dTemp),dTemp,rtol=1e-3)

        # Generate an angle based scheme and send it to the DAS
        wlmAngle = array([aCen])
        laserTemp = RDFreqConv.angleToLaserTemperature(vLaserNum,wlmAngle)
        repeat = 1
        dwell = 300
        Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_IdleState)
        self.makeAndUploadScheme(wlmAngle,laserTemp,vLaserNum,repeat,dwell)
        Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER",SPECT_CNTRL_SchemeSingleMode)
        # Start collecting data
        Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_StartingState)
        self.processingDone.clear()
        self.processingDone.wait()
        wlmAngleList = []
        ratio1List = []
        ratio2List = []
        while not self.queue.empty():
            rdEntry = self.queue.get()
            wlmAngleList.append(rdEntry.wlmAngle)
            ratio1List.append(rdEntry.ratio1)
            ratio2List.append(rdEntry.ratio2)
        wlmAngleList = array(wlmAngleList,dtype=float)
        ratio1List = array(ratio1List,dtype=float)
        ratio2List = array(ratio2List,dtype=float)
        wlmAngleMean = mean(wlmAngleList[len(wlmAngleList)//2:])
        ratio1Mean = mean(ratio1List[len(ratio1List)//2:])
        ratio2Mean = mean(ratio2List[len(ratio2List)//2:])
        lockError = mod(wlmAngleMean - wlmAngle,2*pi)
        assert 0 <= lockError < 0.005 or 0 <= 2*pi-lockError < 0.005
        # Check that ratios lock to the correct angle on the WLM ellipse
        ratio1Center = float(vLaserSec["RATIO1_CENTER"])
        ratio2Center = float(vLaserSec["RATIO2_CENTER"])
        ratio1Scale = float(vLaserSec["RATIO1_SCALE"])
        ratio2Scale = float(vLaserSec["RATIO2_SCALE"])
        phase = float(vLaserSec["PHASE"])
        ratio1 = ratio1Mean/32768.0
        ratio2 = ratio2Mean/32768.0
        assert allclose((ratio1-ratio1Center)*ratio2Scale*sin(wlmAngleMean + phase),
                        (ratio2-ratio2Center)*ratio1Scale*cos(wlmAngleMean),rtol=5e-3)
        
if __name__ == "__main__":
    t = TestFreqLocker()
    t.setup_class()
    t.test_talkers()
    t.teardown_class()
    t = TestFreqLocker()
    t.setup_class()
    t.test_convertAngle()
    t.teardown_class()
