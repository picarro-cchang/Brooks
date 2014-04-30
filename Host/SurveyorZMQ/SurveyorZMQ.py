#!/usr/bin/python
"""
File Name: SurveyorZMQ.py
Purpose: Accepts high-level surveyor commands via ZMQ and makes necessary analyser RPC calls

File History:
    13-Apr-2014  sze   Initial version

Copyright (c) 2014 Picarro, Inc. All rights reserved
"""
import json
import threading
import traceback
import zmq
import Pyro

from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_INSTR_MANAGER, RPC_PORT_SURVEYOR_ZMQ, ZMQ_PORT_SURVEYOR_CMD
from Host.Common import CmdFIFO
from Host.Common.EventManagerProxy import Log, LogExc, EventManagerProxy_Init

APP_NAME = "SurveyorZMQ"

EventManagerProxy_Init(APP_NAME)

class SurveyorZMQ(object):
    def __init__(self):
        self.driverRpc = None
        self.instMgrRpc = None
        self.context = zmq.Context()
        self.responder = None
        if self.context:
            self.responder = self.context.socket(zmq.REP)
            self.responder.bind("tcp://*:%d" % ZMQ_PORT_SURVEYOR_CMD)

    def close(self):
        if self.responder:
            self.responder.close()
        if self.context:
            self.context.term()

    def doDriverRpc(self, funcName, *args, **kwargs):
        if self.driverRpc is None:
            self.driverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "SurveyorZMQ")
        try:
            return {"value": getattr(self.driverRpc, funcName)(*args, **kwargs)}
        except Pyro.errors.ProtocolError:
            LogExc("Cannot communicate with Driver")
            self.driverRpc = None
            return {"error": "Cannot connect to Analyzer Driver"}
        except:
            LogExc()
            msg = traceback.format_exc()
            return {"error": msg.splitlines()[-1], "verbose":msg}
        
    def doInstMgrRpc(self, funcName, *args, **kwargs):
        if self.instMgrRpc is None:
            self.instMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER, ClientName = "SurveyorZMQ")
        try:
            return {"value": getattr(self.instMgrRpc, funcName)(*args, **kwargs)}
        except Pyro.errors.ProtocolError:
            LogExc("Cannot communicate with InstMgr")
            self.instMgrRpc = None
            return {"error": "Cannot connect to Analyzer InstMgr"}
        except:
            LogExc()
            msg = traceback.format_exc()
            return {"error": msg.splitlines()[-1], "verbose":msg}

    def dispatch(self, cmd):
        atoms = cmd.strip().split()
        if atoms[0] == "Shutdown":
            result = self.doInstMgrRpc("INSTMGR_ShutdownRpc", 0)
            return result if ("error" in result) else {"status": "ok"}
        elif atoms[0] == "StartReferenceGasCapture":
            result = self.doDriverRpc("wrDasReg", "PEAK_DETECT_CNTRL_STATE_REGISTER", "PEAK_DETECT_CNTRL_PrimingState")
            return result if ("error" in result) else {"status": "ok"}
        elif atoms[0] == "StartIsotopicCapture":
            result = self.doDriverRpc("wrDasReg", "PEAK_DETECT_CNTRL_STATE_REGISTER", "PEAK_DETECT_CNTRL_ArmedState")
            return result if ("error" in result) else {"status": "ok"}
        elif atoms[0] == "CancelCapture":
            result = self.doDriverRpc("wrDasReg", "PEAK_DETECT_CNTRL_STATE_REGISTER", "PEAK_DETECT_CNTRL_CancellingState")
            return result if ("error" in result) else {"status": "ok"}
        elif atoms[0] == "StartReferenceGasInjection":
            valve = 3 # Valve to open to inject the reference gas
            valveMask = 1 << (valve-1)
            flagValve = 4 # Flag valve, active for flagSamples which is long enough to indicate injection took place
            flagValveMask = 1 << (flagValve-1)
            mask = valveMask | flagValveMask
            samples = 5 # Units of 200ms
            flagSamples = 10
            result = self.doDriverRpc("wrValveSequence", [[mask, mask, samples], 
                                                          [mask, flagValveMask, flagSamples],
                                                          [mask, 0, 1], [0, 0, 0]])
            if "error" in result:
                return result
            else:
                result = self.doDriverRpc("wrDasReg", "VALVE_CNTRL_SEQUENCE_STEP_REGISTER", 0)
                return result if ("error" in result) else {"status": "ok"}
        else:
            return {"error": "Unknown command: %s" % cmd}

    def main(self):
        while True:
            cmd = self.responder.recv()
            Log("SurveyorZMQ received command: %s" % cmd)
            result = self.dispatch(cmd)
            self.responder.send(json.dumps(result))

def main():
    surveyorZMQ = SurveyorZMQ()
    th = threading.Thread(target=surveyorZMQ.main)
    th.setDaemon(True)
    th.start()
    rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_SURVEYOR_ZMQ),
                                       ServerName="SurveyorZMQ",
                                       ServerDescription="SurveyorZMQ",
                                       ServerVersion="1.0",
                                       threaded=True)
    try:
        while True:
            rpcServer.daemon.handleRequests(0.5)
            if not th.isAlive(): break
        Log("Supervised SurveyorZMQ died", Level=2)
    except:
        LogExc("CmdFIFO for SurveyorZMQ stopped", Level=2)
    finally:
        surveyorZMQ.close()
        
if __name__ == '__main__':
    main()