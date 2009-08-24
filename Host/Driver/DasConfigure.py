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
    def __init__(self,dasInterface,instrConfig):
        self.dasInterface = dasInterface
        self.opGroups = {}
        self.instrConfig = instrConfig

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

        for laserNum in range(1,5):
            if int(self.instrConfig["Configuration"].get("LASER%d_PRESENT" % laserNum,0)):
                # Temperature reading
                self.opGroups["FAST"]["SENSOR_READ"].addOperation(
                    Operation("ACTION_READ_LASER_THERMISTOR_RESISTANCE",
                              [laserNum,"LASER%d_RESISTANCE_REGISTER" % laserNum]))
                self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(
                    Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
                        ["LASER%d_RESISTANCE_REGISTER" % laserNum,
                         "CONVERSION_LASER%d_THERM_CONSTA_REGISTER" % laserNum,
                         "CONVERSION_LASER%d_THERM_CONSTB_REGISTER" % laserNum,
                         "CONVERSION_LASER%d_THERM_CONSTC_REGISTER" % laserNum,
                         "LASER%d_TEMPERATURE_REGISTER" % laserNum]))
                self.opGroups["FAST"]["STREAMER"].addOperation(
                    Operation("ACTION_STREAM_REGISTER",
                        ["STREAM_Laser%dTemp" % laserNum,"LASER%d_TEMPERATURE_REGISTER" % laserNum]))
                # TEC current
                self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
                    Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
                        ["LASER%d_TEC_REGISTER" % laserNum,"FPGA_PWM_LASER%d" % laserNum,"PWM_PULSE_WIDTH"]))
                self.opGroups["FAST"]["STREAMER"].addOperation(
                    Operation("ACTION_STREAM_REGISTER",
                        ["STREAM_Laser%dTec" % laserNum,"LASER%d_TEC_REGISTER" % laserNum]))
                self.opGroups["FAST"]["CONTROLLER"].addOperation(
                    Operation("ACTION_TEMP_CNTRL_LASER%d_STEP" % laserNum))
                # Laser current
                self.opGroups["FAST"]["CONTROLLER"].addOperation(
                    Operation("ACTION_CURRENT_CNTRL_LASER%d_STEP" % laserNum))
                self.opGroups["FAST"]["STREAMER"].addOperation(
                    Operation("ACTION_STREAM_REGISTER",
                        ["STREAM_Laser%dCurrent" % laserNum,"LASER%d_CURRENT_MONITOR_REGISTER" % laserNum]))
                
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
            Operation("ACTION_SPECTRUM_CNTRL_STEP"))

        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_FPGA_REGISTER",
                ["STREAM_Etalon1","FPGA_WLMSIM","WLMSIM_ETA1"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_FPGA_REGISTER",
                ["STREAM_Reference1","FPGA_WLMSIM","WLMSIM_REF1"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_FPGA_REGISTER",
                ["STREAM_Etalon2","FPGA_WLMSIM","WLMSIM_ETA2"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_FPGA_REGISTER",
                ["STREAM_Reference2","FPGA_WLMSIM","WLMSIM_REF2"]))
        
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

        runCont = (1<<interface.PWM_CS_RUN_B) | (1<<interface.PWM_CS_CONT_B)
        for laserNum in range(1,5):
            if int(self.instrConfig["Configuration"].get("LASER%d_PRESENT" % laserNum,0)):
                sender.doOperation(Operation("ACTION_TEMP_CNTRL_LASER%d_INIT" % laserNum))
                sender.doOperation(Operation("ACTION_CURRENT_CNTRL_LASER%d_INIT" % laserNum))
                sender.doOperation(Operation("ACTION_INT_TO_FPGA",[0x8000,"FPGA_PWM_LASER%d" % laserNum,"PWM_PULSE_WIDTH"]))
                sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_PWM_LASER%d" % laserNum,"PWM_CS"]))

        sender.doOperation(Operation("ACTION_TEMP_CNTRL_CAVITY_INIT"))
        sender.doOperation(Operation("ACTION_SPECTRUM_CNTRL_INIT"))
        sender.doOperation(Operation("ACTION_TUNER_CNTRL_INIT"))

        #sender.wrRegFloat("LASER1_RESISTANCE_REGISTER",10000.0)
        #sender.wrRegFloat("LASER2_RESISTANCE_REGISTER",9000.0)
        #sender.wrRegFloat("LASER3_RESISTANCE_REGISTER",8000.0)
        #sender.wrRegFloat("LASER4_RESISTANCE_REGISTER",7000.0)

        sender.wrRegFloat("HOT_BOX_HEATSINK_RESISTANCE_REGISTER",100000.0)
        sender.wrRegFloat("CAVITY_RESISTANCE_REGISTER",100000.0)
        
        # Start the ringdown manager
        runCont = (1<<interface.RDMAN_CONTROL_RUN_B) | (1<<interface.RDMAN_CONTROL_CONT_B)
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_RDMAN","RDMAN_CONTROL"]))
        #  Start the laser locker
        runCont = (1<<interface.LASERLOCKER_CS_RUN_B) | (1<<interface.LASERLOCKER_CS_CONT_B)
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_LASERLOCKER","LASERLOCKER_CS"]))

        # Set the scheduler running
        sender.wrRegUint("SCHEDULER_CONTROL_REGISTER",1);
