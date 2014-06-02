"""
Copyright 2014, Picarro Inc.
"""

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

    def __init__(self):
        self.driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER,
                                                 ClientName = "ControlBridge")
        self.instMgr = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_INSTR_MANAGER,
                                                  ClientName = "ControlBridge")

        self.context = zmq.Context()

        self.controlSocket = self.context.socket(zmq.REP)
        self.controlSocket.connect("tpc://127.0.0.1:%d" % SharedTypes.TCP_PORT_CONTROL_BRIDGE_ZMQ)

        self.commands = {
            "armIsotopicCapture" : self._armIsotopicCapture,
            "cancelIsotopicCapture" : self._cancelIsotopicCapture
        }
 
    def run(self):

        while True:
            try:
                cmd = self.controlSocket.recv_string()

                try:
                    self.commands[cmd]()
                    response = ControlBridge.RESPONSE_STATUS["success"]

                except KeyError:
                    response = ControlBridge.RESPONSE_STATUS["unknown"]

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
        val = self.driver.interfaceValue("PEAK_DETECT_CNTRL_PrimingState")

        if val != 6:
            # TODO What is 6?            
            pass

        self.driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER", 6)

        # Poll for state 8 / cancellation?

    def _startReferenceGasInjection(self):
        pass
