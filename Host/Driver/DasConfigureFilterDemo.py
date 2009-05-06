#!/usr/bin/python
#
# FILE:
#   DasConfigure.py
#
# DESCRIPTION:
#   Configure the DAS scheduler tables
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   12-Apr-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import ctypes
import sys
import time
from numpy import *
from Host.autogen import interface
from Host.Common import SharedTypes
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common import timestamp
from Host.Common.hostDasInterface import Operation, OperationGroup

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("Driver")

class DasConfigure(object):
    def __init__(self,dasInterface):
        self.dasInterface = dasInterface

    def run(self):
        sender = self.dasInterface.hostToDspSender
        ts = timestamp.getTimestamp()
        sender.doOperation(Operation("ACTION_SET_TIMESTAMP",[ts&0xFFFFFFFF,ts>>32]))
        # Check initial value of NOOP register
        if 0xABCD1234 != sender.rdRegUint("NOOP_REGISTER"):
            raise ValueError("NOOP_REGISTER not initialized correctly")

        ticker  = OperationGroup(priority=1,period=1000)
        ticker.addOperation(Operation("ACTION_TEST_SCHEDULER",[1,2,3]))

        outputs = OperationGroup(priority=5, period=100)
        outputs.addOperation(Operation("ACTION_PULSE_GENERATOR",
            ["LOW_DURATION_REGISTER","HIGH_DURATION_REGISTER",
            "LASER2_TEMPERATURE_REGISTER"],"PULSE_GEN_ENV"))

        processors = OperationGroup(priority=7, period=100)
        processors.addOperation(Operation("ACTION_FILTER",
            ["LASER2_TEMPERATURE_REGISTER","LASER2_TEC_PWM_REGISTER"],
            "FILTER_ENV"))

        streamer = OperationGroup(priority=11,period=100)
        streamer.addOperation(Operation("ACTION_STREAM_REGISTER",
            ["STREAM_Laser2Temp","LASER2_TEMPERATURE_REGISTER"]))
        streamer.addOperation(Operation("ACTION_STREAM_REGISTER",
            ["STREAM_Laser2Tec","LASER2_TEC_PWM_REGISTER"]))

        groups = [ticker,outputs,processors,streamer]

        self.dasInterface.uploadSchedule(groups)
        sender.doOperation(Operation("ACTION_INIT_RUNQUEUE",[len(groups)]))

        # Initialize filter coefficients and write environment
        #  of filter
        damp = 0.95
        phi = 2.0*pi/20
        filtEnv = interface.FilterEnvType()
        filtEnv.den[0:3] = [1.0, -2*damp*cos(phi), damp**2]
        filtEnv.num[0] = sum(filtEnv.den[0:3])
        filtEnv.ptr = 0
        sender.wrEnv("FILTER_ENV",filtEnv)

        sender.wrRegUint("SCHEDULER_CONTROL_REGISTER",1);
