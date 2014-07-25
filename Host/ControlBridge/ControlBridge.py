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
            "cancelIsotopicCapture" : self._cancelIsotopicCapture,
            "shutdown" : self._shutdown,
            "cancelIsotopicAnalysis" : self._cancelIsotopicAnalysis,
            "startReferenceGasCapture" : self._startReferenceGasCapture
        }
 
    def run(self):

        try:
            while True:
                cmd = self.controlSocket.recv_string()
                EventManager.Log("Command: '%s'" % cmd)

                try:
                    self.commands[cmd]()
                    response = ControlBridge.RESPONSE_STATUS["success"]

                except KeyError:
                    response = ControlBridge.RESPONSE_STATUS["unknown"]

                EventManager.Log("Command response: '%s'" % response)
                self.controlSocket.send_string("%d" % response)

        finally:
            self.controlSocket.close()
            self.context.term()

    def _armIsotopicCapture(self):
        self.driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER", 1)

    def _cancelIsotopicCapture(self):
        self.driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER", 0)

    def _shutdown(self):
        self.instMgr.INSTMGR_ShutdownRpc(0)

    def _startReferenceGasCapture(self):
        t = threading.Thread(target=self._runReferenceGasCapture)
        t.start()

    def _runReferenceGasCapture(self):
        EventManager.Log('Starting reference gas capture command')
        val = self.driver.interfaceValue("PEAK_DETECT_CNTRL_PrimingState")

        if val != 6:
            EventManager.Log('PEAK_DETECT_CNTRL_PrimingState != 6!')
            # XXX Ask Sze? Does this mean that reference gas is supported for this instrument? IOW is it old?
            pass

        self.driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER", 6)

        while True:
            EventManager.Log('Waiting for prime/purge to complete')
            val = self.driver.rdDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER")
            
            if val == 8:
                EventManager.Log('Prime/purge complete')
                # Do injection
                break

            time.sleep(0.010)

        # Arm the system
        self._armIsotopicCapture()

        time.sleep(1.0)

        # Injection
        self.driver.wrValveSequence([
            [ControlBridge.INJECT_MASK, ControlBridge.INJECT_MASK, ControlBridge.INJECT_SAMPLES],
            [ControlBridge.INJECT_MASK, ControlBridge.INJECT_FLAG_VALVE_MASK, 30],
            [ControlBridge.INJECT_MASK, 0, 1],
            [0, 0, 0]
        ])
        
        self.driver.wrDasReg("VALVE_CNTRL_SEQUENCE_STEP_REGISTER", 0)

        EventManager.Log('Injection complete')

    def _cancelIsotopicAnalysis(self):
        self.driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER", 5)
        
if __name__ == '__main__':
    bridge = ControlBridge()
    bridge.run()
