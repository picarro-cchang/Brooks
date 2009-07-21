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

schedulerPriorities = dict(SENSOR_READ=1,SENSOR_CONVERT=2,
                           CONTROLLER=3,ACTUATOR_CONVERT=4,
                           ACTUATOR_WRITE=5,STREAMER=6,
                           MODEL=7)

# Periods are expressed in tenths of a second
schedulerPeriods = dict(FAST=2, MEDIUM=10, SLOW=50)

class DasConfigure(object):
    def __init__(self,dasInterface):
        self.dasInterface = dasInterface
        self.opGroups = {}

    def run(self):
        sender = self.dasInterface.hostToDspSender
        ts = timestamp.getTimestamp()
        sender.doOperation(Operation("ACTION_SET_TIMESTAMP",[ts&0xFFFFFFFF,ts>>32]))
        # Check initial value of NOOP register
        if 0x19680511 != sender.rdRegUint("VERIFY_INIT_REGISTER"):
            raise ValueError("VERIFY_INIT_REGISTER not initialized correctly")

        # Define operation groups as a dictionary accessed using
        #  e.g. self.opGroups["FAST"]["SENSOR_READ"]
        for rate in schedulerPeriods:
            self.opGroups[rate] = {}
            for opType in schedulerPriorities:
                self.opGroups[rate][opType] = OperationGroup(
                    priority=schedulerPriorities[opType],
                    period=schedulerPeriods[rate])

#        self.opGroups["FAST"]["SENSOR_READ"].addOperation(
#            Operation("ACTION_READ_LASER_TEC_MONITORS"))

#        self.opGroups["FAST"]["SENSOR_READ"].addOperation(
#            Operation("ACTION_READ_LASER_THERMISTOR_RESISTANCE",
#                      [2,"LASER2_RESISTANCE_REGISTER"]))

        self.opGroups["FAST"]["SENSOR_READ"].addOperation(
            Operation("ACTION_READ_LASER_THERMISTOR_RESISTANCE",
                      [3,"LASER3_RESISTANCE_REGISTER"]))
#        self.opGroups["FAST"]["SENSOR_READ"].addOperation(
#             Operation("ACTION_READ_LASER_CURRENT",
#                 [3,"LAER3_CURRENT_MONITOR_REGISTER"]))

#         self.opGroups["FAST"]["CONTROLLER"].addOperation(
#             Operation("ACTION_FILTER",
#                 ["LASER2_TEMPERATURE_REGISTER","LASER2_TEC_REGISTER"],
#                 "FILTER_ENV"))
#
        self.opGroups["FAST"]["MODEL"].addOperation(
            Operation("ACTION_FILTER",
                 ["LASER1_TEC_REGISTER","LASER1_TEMPERATURE_REGISTER"],
                 "LASER_TEMP_MODEL_ENV"))

#        self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(
#            Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
#                ["LASER1_RESISTANCE_REGISTER",
#                 "CONVERSION_LASER1_THERM_CONSTA_REGISTER",
#                 "CONVERSION_LASER1_THERM_CONSTB_REGISTER",
#                 "CONVERSION_LASER1_THERM_CONSTC_REGISTER",
#                 "LASER1_TEMPERATURE_REGISTER"]))

        self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(
            Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
                ["LASER2_RESISTANCE_REGISTER",
                 "CONVERSION_LASER2_THERM_CONSTA_REGISTER",
                 "CONVERSION_LASER2_THERM_CONSTB_REGISTER",
                 "CONVERSION_LASER2_THERM_CONSTC_REGISTER",
                 "LASER2_TEMPERATURE_REGISTER"]))
#
        self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(
             Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
                 ["LASER3_RESISTANCE_REGISTER",
                  "CONVERSION_LASER3_THERM_CONSTA_REGISTER",
                  "CONVERSION_LASER3_THERM_CONSTB_REGISTER",
                  "CONVERSION_LASER3_THERM_CONSTC_REGISTER",
                  "LASER3_TEMPERATURE_REGISTER"]))


        #self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(
        #    Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
        #        ["LASER4_RESISTANCE_REGISTER",
        #         "CONVERSION_LASER4_THERM_CONSTA_REGISTER",
        #         "CONVERSION_LASER4_THERM_CONSTB_REGISTER",
        #         "CONVERSION_LASER4_THERM_CONSTC_REGISTER",
        #         "LASER4_TEMPERATURE_REGISTER"]))

        REG_LASER1_PWM_WIDTH = interface.FPGA_LASER1_PWM + interface.PWM_PULSE_WIDTH
        self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
            Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
                ["LASER1_TEC_REGISTER",REG_LASER1_PWM_WIDTH]))
        REG_LASER2_PWM_WIDTH = interface.FPGA_LASER2_PWM + interface.PWM_PULSE_WIDTH
        self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
            Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
                ["LASER2_TEC_REGISTER",REG_LASER2_PWM_WIDTH]))
        REG_LASER3_PWM_WIDTH = interface.FPGA_LASER3_PWM + interface.PWM_PULSE_WIDTH
        self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
            Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
                ["LASER3_TEC_REGISTER",REG_LASER3_PWM_WIDTH]))
        REG_LASER4_PWM_WIDTH = interface.FPGA_LASER4_PWM + interface.PWM_PULSE_WIDTH
        self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
            Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
                ["LASER4_TEC_REGISTER",REG_LASER4_PWM_WIDTH]))

        # Read the DAS temperature into LASER4_TEMPERATURE_REGISTER
        self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(
            Operation("ACTION_DS1631_READTEMP",
                ["LASER4_TEMPERATURE_REGISTER"]))

        self.opGroups["SLOW"]["SENSOR_CONVERT"].addOperation(
            Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
                ["CAVITY_RESISTANCE_REGISTER",
                 "CONVERSION_CAVITY_THERM_CONSTA_REGISTER",
                 "CONVERSION_CAVITY_THERM_CONSTB_REGISTER",
                 "CONVERSION_CAVITY_THERM_CONSTC_REGISTER",
                 "CAVITY_TEMPERATURE_REGISTER"]))

        self.opGroups["SLOW"]["SENSOR_CONVERT"].addOperation(
            Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
                ["HOT_BOX_HEATSINK_RESISTANCE_REGISTER",
                 "CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER",
                 "CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER",
                 "CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER",
                 "HOT_BOX_HEATSINK_TEMPERATURE_REGISTER"]))

        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_TEMP_CNTRL_LASER1_STEP"))
        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_TEMP_CNTRL_LASER2_STEP"))
        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_TEMP_CNTRL_LASER3_STEP"))
        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_TEMP_CNTRL_LASER4_STEP"))
        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_TUNER_CNTRL_STEP"))
        self.opGroups["SLOW"]["CONTROLLER"].addOperation(
            Operation("ACTION_TEMP_CNTRL_CAVITY_STEP"))

        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_CURRENT_CNTRL_LASER1_STEP"))
        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_CURRENT_CNTRL_LASER2_STEP"))
        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_CURRENT_CNTRL_LASER3_STEP"))
        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_CURRENT_CNTRL_LASER4_STEP"))

        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser1Temp","LASER1_TEMPERATURE_REGISTER"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser1Tec","LASER1_TEC_REGISTER"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser2Temp","LASER2_TEMPERATURE_REGISTER"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser2Tec","LASER2_TEC_REGISTER"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser3Temp","LASER3_TEMPERATURE_REGISTER"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser3Tec","LASER3_TEC_REGISTER"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser4Temp","LASER4_TEMPERATURE_REGISTER"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser4Tec","LASER4_TEC_REGISTER"]))

        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser1Current","LASER1_CURRENT_MONITOR_REGISTER"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser2Current","LASER2_CURRENT_MONITOR_REGISTER"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser3Current","LASER3_CURRENT_MONITOR_REGISTER"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_Laser4Current","LASER4_CURRENT_MONITOR_REGISTER"]))

        self.opGroups["SLOW"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_CavityTemp","CAVITY_TEMPERATURE_REGISTER"]))

        self.opGroups["SLOW"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_HotChamberTecTemp","HOT_BOX_HEATSINK_TEMPERATURE_REGISTER"]))

        self.opGroups["SLOW"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_HotChamberTec","CAVITY_TEC_REGISTER"]))

        self.opGroups["SLOW"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_REGISTER",
                ["STREAM_HotChamberHeater","HEATER_CNTRL_MARK_REGISTER"]))

        # Stop the scheduler before loading new schedule
        sender.wrRegUint("SCHEDULER_CONTROL_REGISTER",0);
        # Schedule operation groups which are non-empty
        groups = [g for c in self.opGroups.values()
                    for g in c.values() if g]
        self.dasInterface.uploadSchedule(groups)

        # Perform one-time initializations

        sender.doOperation(Operation("ACTION_INIT_RUNQUEUE",[len(groups)]))
        sender.doOperation(Operation("ACTION_TEMP_CNTRL_LASER1_INIT"))
        sender.doOperation(Operation("ACTION_TEMP_CNTRL_LASER2_INIT"))
        sender.doOperation(Operation("ACTION_TEMP_CNTRL_LASER3_INIT"))
        sender.doOperation(Operation("ACTION_TEMP_CNTRL_LASER4_INIT"))
        sender.doOperation(Operation("ACTION_TEMP_CNTRL_CAVITY_INIT"))
        sender.doOperation(Operation("ACTION_CURRENT_CNTRL_LASER1_INIT"))
        sender.doOperation(Operation("ACTION_CURRENT_CNTRL_LASER2_INIT"))
        sender.doOperation(Operation("ACTION_CURRENT_CNTRL_LASER3_INIT"))
        sender.doOperation(Operation("ACTION_CURRENT_CNTRL_LASER4_INIT"))
        sender.doOperation(Operation("ACTION_TUNER_CNTRL_INIT"))
        sender.wrRegFloat("LASER1_RESISTANCE_REGISTER",10000.0)
        sender.wrRegFloat("LASER2_RESISTANCE_REGISTER",9000.0)
        sender.wrRegFloat("LASER3_RESISTANCE_REGISTER",8000.0)
        sender.wrRegFloat("LASER4_RESISTANCE_REGISTER",7000.0)
        sender.wrRegFloat("HOT_BOX_HEATSINK_RESISTANCE_REGISTER",100000.0)
        sender.wrRegFloat("CAVITY_RESISTANCE_REGISTER",100000.0)

        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[0x8000,REG_LASER1_PWM_WIDTH]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[0x8000,REG_LASER2_PWM_WIDTH]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[0x8000,REG_LASER3_PWM_WIDTH]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[0x8000,REG_LASER4_PWM_WIDTH]))
        runCont = (1<<interface.PWM_CS_RUN_B) | (1<<interface.PWM_CS_CONT_B)
        REG_LASER1_PWM_CS = interface.FPGA_LASER1_PWM + interface.PWM_CS
        REG_LASER2_PWM_CS = interface.FPGA_LASER2_PWM + interface.PWM_CS
        REG_LASER3_PWM_CS = interface.FPGA_LASER3_PWM + interface.PWM_CS
        REG_LASER4_PWM_CS = interface.FPGA_LASER4_PWM + interface.PWM_CS
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,REG_LASER1_PWM_CS]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,REG_LASER2_PWM_CS]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,REG_LASER3_PWM_CS]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,REG_LASER4_PWM_CS]))

        # Initialize filter coefficients and write environment
        #  of filter
        damp = 0.95
        phi = 2.0*pi/20
        filtEnv = interface.FilterEnvType()
        filtEnv.den[0:3] = [1.0, -2*damp*cos(phi), damp**2]
        filtEnv.num[0] = sum(filtEnv.den[0:3])
        filtEnv.ptr = 0
        sender.wrEnv("FILTER_ENV",filtEnv)

        tempModelEnv = interface.FilterEnvType()
        a, b = 0.8, 0.99
        A, B = 0.5e-3, 0.5e-3
        tempModelEnv.num[0:3] = [A*(1-a)**2 + B*(1-b)**2,
                                 -2*(A*(1-a)**2*b + B*a*(1-b)**2),
                                 A*(1-a)**2*b**2 + B*a**2*(1-b)**2]
        tempModelEnv.den[0:5] = [1,
                                 -2*(a+b),
                                 (a**2 + 4*a*b + b**2),
                                 -2*a*b*(a+b),
                                 a**2*b**2]
        tempModelEnv.ptr = 0
        sender.wrEnv("LASER_TEMP_MODEL_ENV",tempModelEnv)

        # Set the scheduler running
        sender.wrRegUint("SCHEDULER_CONTROL_REGISTER",1);
