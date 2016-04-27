"""
Copyright 2014, Picarro Inc.
"""

import time
import threading

import zmq

from Host.Common import SharedTypes
from Host.Common import EventManagerProxy as EventManager
from Host.Common import CmdFIFO

EventManager.EventManagerProxy_Init('ControlBridge')

class ControlBridge(object):

    RESPONSE_STATUS = {
        "success" : 0,
        "unknown" : 1
    }

    # Previously defined in the gdu.js REST call to AnalyzerServer
    INJECT_VALVE_BIT = 2
    INJECT_VALVE_MASK = 1 << INJECT_VALVE_BIT
    INJECT_FLAG_VALVE_BIT = 3
    INJECT_FLAG_VALVE_MASK = 1 << INJECT_FLAG_VALVE_BIT
    INJECT_MASK = INJECT_VALVE_MASK | INJECT_FLAG_VALVE_MASK
    INJECT_SAMPLES = 5
    EXTRA_FLAG_SAMPLES = 50 # each is 0.2 seconds

    def __init__(self):
        self.driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER,
                                                 ClientName = "ControlBridge")
        EventManager.Log('Connected to Driver')
        self.instMgr = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_INSTR_MANAGER,
                                                  ClientName = "ControlBridge")
        EventManager.Log('Connected to Instrument Manager')

        self.context = zmq.Context()

        self.controlSocket = self.context.socket(zmq.REP)
        self.controlSocket.bind("tcp://127.0.0.1:%d" % SharedTypes.TCP_PORT_CONTROL_BRIDGE_ZMQ)

        self.commands = {
            "armIsotopicCapture" : self._armIsotopicCapture,
            "shutdown" : self._shutdown,
            "cancelIsotopicAnalysis" : self._cancelIsotopicAnalysis,
            "getPeakDetectorState" : self._getPeakDetectorState,
            "setToIdle" : self._setToIdle,
            "referenceGasPrime" : self._referenceGasPrime,
            "referenceGasInjection" : self._referenceGasInjection,
            "setToEQMode": self._setToEQMode,
            "setToSurveyorMode": self._setToSurveyorMode
        }
 
    def run(self):
        try:
            while True:
                cmd = self.controlSocket.recv_string()
                ret = None

                try:
                    ret = self.commands[cmd]()
                    response = ControlBridge.RESPONSE_STATUS["success"]

                except KeyError:
                    response = ControlBridge.RESPONSE_STATUS["unknown"]

                self.controlSocket.send_string("%d,%s" % (response, ret))

        finally:
            self.controlSocket.close()
            self.context.term()

    def _getPeakDetectorState(self):
        return self.driver.rdDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER")

    def _armIsotopicCapture(self):
        self.driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER", 1)

    def _setToIdle(self):
        self.driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER", 0)

    def _shutdown(self):
        self.instMgr.INSTMGR_ShutdownRpc(0)

    def _cancelIsotopicAnalysis(self):
        self.driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER", 5)

        doneCount = 0

        while True:
            if doneCount == 600:
                break

            val = self.driver.rdDasReg('PEAK_DETECT_CNTRL_STATE_REGISTER')
            EventManager.Log("Waiting for peak detector to return to Idle: %s" % val)

            if val == 0:
                doneCount += 1

            time.sleep(0.010)

    def _referenceGasPrime(self):
        self.driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER", 6)

    def _referenceGasInjection(self):
        self.driver.wrValveSequence([
            [ControlBridge.INJECT_MASK, ControlBridge.INJECT_MASK, ControlBridge.INJECT_SAMPLES],
            [ControlBridge.INJECT_MASK, ControlBridge.INJECT_FLAG_VALVE_MASK, ControlBridge.EXTRA_FLAG_SAMPLES],
            [ControlBridge.INJECT_MASK, 0, 1],
            [0, 0, 0]
        ])
        
        self.driver.wrDasReg("VALVE_CNTRL_SEQUENCE_STEP_REGISTER", 0)
        
    def _setToEQMode(self):
        self.driver.closeValves(0x20)   # close valve 6
        
    def _setToSurveyorMode(self):
        self.driver.openValves(0x20)   # open valve 6

    def _setToSurveyorMode(self):
        self.driver.openValves(0x20)   # open valve 6
    
    def _setToEQMode(self):
        self.driver.closeValves(0x20)   # close valve 6
        
    
        
if __name__ == '__main__':
    bridge = ControlBridge()
    bridge.run()
