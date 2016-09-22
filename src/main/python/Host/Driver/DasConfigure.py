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
import traceback
from numpy import *
from Host.autogen import interface
from Host.Common import SharedTypes, hostDasInterface
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common import timestamp
from Host.Common.SharedTypes import Operation, OperationGroup

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("Driver")

schedulerPriorities = dict(SENSOR_READ=1,SENSOR_CONVERT=2,
                           SENSOR_PROCESSING=3,
                           CONTROLLER=4,ACTUATOR_CONVERT=5,
                           ACTUATOR_WRITE=6,STREAMER=7,
                           MODEL=8)

# Periods are expressed in tenths of a second
schedulerPeriods = dict(FAST=2, MEDIUM=10, SLOW=50)

class DasConfigure(SharedTypes.Singleton):
    initialized = False
    def __init__(self,dasInterface=None,instrConfig=None,driverConfig=None):
        if not self.initialized:
            # assert isinstance(dasInterface, hostDasInterface.DasInterface)
            if dasInterface is None or instrConfig is None:
                raise ValueError("DasConfigure has not been initialized correctly")
            self.i2cConfig = {} # Indicates if I2C associated with specific index was detected
            self.dasInterface = dasInterface
            self.opGroups = {}
            self.instrConfig = instrConfig
            self.driverConfig = driverConfig
            self.installed = {}
            for key in instrConfig["CONFIGURATION"]:
                self.installed[key] = int(instrConfig["CONFIGURATION"][key])
            self.enableInterpolation = self.installed.get("ENABLE_INTERPOLATION",1)
            self.heaterCntrlMode = self.installed.get("HEATER_CONTROL_MODE",0)
            self.initialized = True
            self.parameter_forms = interface.parameter_forms
            self.extraSchedule = None
            self.extraInit = None
            self.extraScheduleCode = None
            self.extraInitCode = None
            if "DasConfigure" in self.driverConfig:
                dasConfig = self.driverConfig["DasConfigure"]
                self.extraSchedule = dasConfig.get("schedule",None)
                self.extraInit = dasConfig.get("init",None)
            if self.extraSchedule is not None:
                self.extraScheduleCode = compile(self.extraSchedule.replace("\r\n","\n"),"<schedule>","exec")
            if self.extraInit is not None:
                self.extraInitCode = compile(self.extraInit.replace("\r\n","\n"),"<init>","exec")
            self.scriptEnv = {"Operation":Operation,"GROUPS":self.opGroups}
    def installCheck(self,key):
        return self.installed.get(key,0)

    def setHardwarePresent(self):
        mapping = [("LASER1_PRESENT",      1<<interface.HARDWARE_PRESENT_Laser1Bit),
                   ("LASER2_PRESENT",      1<<interface.HARDWARE_PRESENT_Laser2Bit),
                   ("LASER3_PRESENT",      1<<interface.HARDWARE_PRESENT_Laser3Bit),
                   ("LASER4_PRESENT",      1<<interface.HARDWARE_PRESENT_Laser4Bit),
                   ("SOA_PRESENT",         1<<interface.HARDWARE_PRESENT_SoaBit),
                   ("POWER_BOARD_PRESENT", 1<<interface.HARDWARE_PRESENT_PowerBoardBit),
                   ("WARM_BOX_PRESENT",    1<<interface.HARDWARE_PRESENT_WarmBoxBit),
                   ("HOT_BOX_PRESENT",     1<<interface.HARDWARE_PRESENT_HotBoxBit),
                   ("DAS_TEMP_MONITOR",    1<<interface.HARDWARE_PRESENT_DasTempMonitorBit),
                   ("ANALOG_INTERFACE",    1<<interface.HARDWARE_PRESENT_AnalogInterface),
                   ("FIBER_AMPLIFIER_PRESENT",    1<<interface.HARDWARE_PRESENT_FiberAmplifierBit),
                   ("FAN_CONTROL_DISABLED", 1<<interface.HARDWARE_PRESENT_FanCntrlDisabledBit),
                   ("FLOW_SENSOR_PRESENT",  1<<interface.HARDWARE_PRESENT_FlowSensorBit),
                   ("RDD_VAR_GAIN_PRESENT", 1<<interface.HARDWARE_PRESENT_RddVarGainBit),
                   ]
        mask = 0
        for key, bit in mapping:
            if self.installCheck(key) > 0:
                mask |= bit
        self.dasInterface.hostToDspSender.wrRegUint("HARDWARE_PRESENT_REGISTER",mask)

    def run(self):
        # If heaterCntrlMode == interface.HEATER_CNTRL_MODE_TEC_TARGET, we need to make some changes in the parameter
        #  forms for heater control
        if self.heaterCntrlMode in [interface.HEATER_CNTRL_MODE_TEC_TARGET]:
            for formName,p in self.parameter_forms:
                if formName == 'Heater Controller Parameters':
                    for i,pItem in enumerate(p):
                        if pItem[2] == interface.HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER:
                            p[i] = ('dsp','float',interface.HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Target value of hot box TEC','digU','%.0f',1,1)
                        elif pItem[2] == interface.HEATER_TEMP_CNTRL_TOLERANCE_REGISTER:
                            p[i] = ('dsp','float',interface.HEATER_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','digU','%.3f',1,1)
                        elif pItem[2] == interface.HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER:
                            p[i] = ('dsp','float',interface.HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','digU','%.0f',1,1)
                        elif pItem[2] == interface.HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER:
                            p[i] = ('dsp','float',interface.HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Max sweep value','digU','%.0f',1,1)
                        elif pItem[2] == interface.HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER:
                            p[i] = ('dsp','float',interface.HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','digU/sample','%.0f',1,1)
                    break
        sender = self.dasInterface.hostToDspSender
        self.scriptEnv["DO_OPERATION"] = sender.doOperation
        ts = timestamp.getTimestamp()
        sender.doOperation(Operation("ACTION_SET_TIMESTAMP",[ts&0xFFFFFFFF,ts>>32]))
        # Check initial value of NOOP register
        if 0x19680511 != sender.rdRegUint("VERIFY_INIT_REGISTER"):
            raise ValueError("VERIFY_INIT_REGISTER not initialized correctly")
        self.setHardwarePresent()
        # Reset I2C multiplexers
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[1<<interface.KERNEL_CONTROL_I2C_RESET_B,"FPGA_KERNEL","KERNEL_CONTROL"]))
        # Define operation groups as a dictionary accessed using
        #  e.g. self.opGroups["FAST"]["SENSOR_READ"]
        for rate in schedulerPeriods:
            self.opGroups[rate] = {}
            for opType in schedulerPriorities:
                self.opGroups[rate][opType] = OperationGroup(
                    priority=schedulerPriorities[opType],
                    period=schedulerPeriods[rate])

        # Start heartbeat to let sentry handler know that the scheduler is alive
        self.opGroups["FAST"]["CONTROLLER"].addOperation(Operation("ACTION_SCHEDULER_HEARTBEAT"))


        # Schedule code specified in the initialization file
        if self.extraScheduleCode is not None:
            try:
                exec self.extraScheduleCode in self.scriptEnv
            except:
                LogExc("Error processing extra scheduler code in Driver initialization file", Level=3)

        soa = self.installCheck("SOA_PRESENT")
        fiber_amp = self.installCheck("FIBER_AMPLIFIER_PRESENT")
        if soa and fiber_amp:
            raise ValueError,"Cannot have both SOA and fiber amplifier present"

        injCtrl = sender.rdFPGA("FPGA_INJECT","INJECT_CONTROL")

        # Disable SOA current bit in FPGA if both SOA_PRESENT and FIBER_AMPLIFIER_PRESENT flags are not set in
        #  the Master.ini file

        soaPresent = 1<<interface.INJECT_CONTROL_SOA_PRESENT_B
        if soa or fiber_amp:
            injCtrl |= soaPresent
        else:
            injCtrl &= ~soaPresent
        sender.wrFPGA("FPGA_INJECT","INJECT_CONTROL",injCtrl)

        if fiber_amp:
            injCtrl2 = sender.rdFPGA("FPGA_INJECT","INJECT_CONTROL2")
            sender.wrFPGA("FPGA_INJECT","INJECT_CONTROL2",injCtrl2 | (1<<interface.INJECT_CONTROL2_FIBER_AMP_PRESENT_B))

        for laserNum in range(1,5):
            present = self.installCheck("LASER%d_PRESENT" % laserNum)
            if laserNum == 4:
                if soa:
                    if present:
                        raise ValueError,"Cannot have both laser 4 and SOA present"
                    else:
                        present = soa
                elif fiber_amp:
                    if present:
                        raise ValueError,"Cannot have both laser 4 and fiber amplifier` present"
                    # The fiber amplifier thermal control operates on a slower timescale
                    if fiber_amp > 0:
                        # Temperature reading
                        self.opGroups["SLOW"]["SENSOR_READ"].addOperation(
                            Operation("ACTION_READ_THERMISTOR_RESISTANCE",
                                      ["I2C_LASER%d_THERMISTOR_ADC" % laserNum,
                                      "LASER%d_RESISTANCE_REGISTER" % laserNum,
                                      "LASER%d_THERMISTOR_SERIES_RESISTANCE_REGISTER" % laserNum]))
                        self.opGroups["SLOW"]["SENSOR_CONVERT"].addOperation(
                            Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
                                ["LASER%d_RESISTANCE_REGISTER" % laserNum,
                                 "CONVERSION_LASER%d_THERM_CONSTA_REGISTER" % laserNum,
                                 "CONVERSION_LASER%d_THERM_CONSTB_REGISTER" % laserNum,
                                 "CONVERSION_LASER%d_THERM_CONSTC_REGISTER" % laserNum,
                                 "LASER%d_TEMPERATURE_REGISTER" % laserNum]))
                    self.opGroups["SLOW"]["STREAMER"].addOperation(
                        Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                            ["STREAM_Laser%dTemp" % laserNum,"LASER%d_TEMPERATURE_REGISTER" % laserNum]))
                    # TEC current
                    self.opGroups["SLOW"]["ACTUATOR_WRITE"].addOperation(
                        Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
                            ["LASER%d_TEC_REGISTER" % laserNum,"FPGA_PWM_LASER%d" % laserNum,"PWM_PULSE_WIDTH"]))
                    self.opGroups["SLOW"]["STREAMER"].addOperation(
                        Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                            ["STREAM_Laser%dTec" % laserNum,"LASER%d_TEC_REGISTER" % laserNum]))
                    self.opGroups["SLOW"]["CONTROLLER"].addOperation(
                        Operation("ACTION_TEMP_CNTRL_LASER%d_STEP" % laserNum))

            if present:
                # Set present to a negative number to disable I2C reads
                if present > 0:
                    # Temperature reading
                    self.opGroups["FAST"]["SENSOR_READ"].addOperation(
                        Operation("ACTION_READ_THERMISTOR_RESISTANCE",
                                  ["I2C_LASER%d_THERMISTOR_ADC" % laserNum,
                                  "LASER%d_RESISTANCE_REGISTER" % laserNum,
                                  "LASER%d_THERMISTOR_SERIES_RESISTANCE_REGISTER" % laserNum]))
                    self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(
                        Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
                            ["LASER%d_RESISTANCE_REGISTER" % laserNum,
                             "CONVERSION_LASER%d_THERM_CONSTA_REGISTER" % laserNum,
                             "CONVERSION_LASER%d_THERM_CONSTB_REGISTER" % laserNum,
                             "CONVERSION_LASER%d_THERM_CONSTC_REGISTER" % laserNum,
                             "LASER%d_TEMPERATURE_REGISTER" % laserNum]))
                else:
                    # Use a filter with similar characteristics to a real laser to simulate the thermal dynamics
                    self.opGroups["FAST"]["MODEL"].addOperation(
                        Operation("ACTION_FILTER",
                            ["LASER%d_TEC_REGISTER" % laserNum,
                             "LASER%d_TEMPERATURE_REGISTER" % laserNum],
                            "LASER%d_TEMP_MODEL_ENV" % laserNum))
                    env = interface.FilterEnvType()
                    env.offset = -40000.0
                    degree = 7
                    env.num[0:degree+1] = [   0.00000000e+00,  -2.98418514e-05,  -1.01071361e-04,   6.39149028e-05,
                                              5.23341031e-05,   2.66718772e-05,  -1.01386506e-05,  -9.73607948e-06]
                    env.den[0:degree+1] = [   1.00000000e+00,  -1.37628382e+00,   2.19598434e-02,   1.01673929e-01,
                                              2.99996581e-01,   2.93872141e-02,  -7.45088401e-02,  -1.42310788e-04]
                    ss_in = 32768
                    ss_out = (ss_in+env.offset)*sum(env.num[0:degree+1])/sum(env.den[0:degree+1])
                    for i in range(degree)[::-1]:
                        env.state[i] = (ss_in+env.offset)*env.num[i+1]-ss_out*env.den[i+1]
                        if i<degree-1:
                            env.state[i] += env.state[i+1]
                    sender.wrEnv("LASER%d_TEMP_MODEL_ENV" % laserNum,env)

                self.opGroups["FAST"]["STREAMER"].addOperation(
                    Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                        ["STREAM_Laser%dTemp" % laserNum,"LASER%d_TEMPERATURE_REGISTER" % laserNum]))
                # TEC current
                self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
                    Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
                        ["LASER%d_TEC_REGISTER" % laserNum,"FPGA_PWM_LASER%d" % laserNum,"PWM_PULSE_WIDTH"]))
                self.opGroups["FAST"]["STREAMER"].addOperation(
                    Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                        ["STREAM_Laser%dTec" % laserNum,"LASER%d_TEC_REGISTER" % laserNum]))
                self.opGroups["FAST"]["CONTROLLER"].addOperation(
                    Operation("ACTION_TEMP_CNTRL_LASER%d_STEP" % laserNum))

                # Laser current
                self.opGroups["FAST"]["CONTROLLER"].addOperation(
                    Operation("ACTION_CURRENT_CNTRL_LASER%d_STEP" % laserNum))
                if laserNum == 4 and (soa or fiber_amp):
                    pass
                else:
                    if present > 0:
                        self.opGroups["FAST"]["SENSOR_READ"].addOperation(
                            Operation("ACTION_READ_LASER_CURRENT",
                                      [laserNum,
                                       "CONVERSION_LASER%d_CURRENT_SLOPE_REGISTER" % laserNum,
                                       "CONVERSION_LASER%d_CURRENT_OFFSET_REGISTER" % laserNum,
                                       "LASER%d_CURRENT_MONITOR_REGISTER" % laserNum]))
                    else:
                        self.opGroups["FAST"]["SENSOR_READ"].addOperation(
                            Operation("ACTION_SIMULATE_LASER_CURRENT_READING",
                                      [laserNum,"LASER%d_CURRENT_MONITOR_REGISTER" % laserNum]))
                    self.opGroups["FAST"]["STREAMER"].addOperation(
                        Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                            ["STREAM_Laser%dCurrent" % laserNum,"LASER%d_CURRENT_MONITOR_REGISTER" % laserNum]))

        # Read the DAS temperature into DAS_TEMPERATURE_REGISTER and stream it
        if self.installCheck("DAS_TEMP_MONITOR"):
            self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(Operation("ACTION_DS1631_READTEMP",
                                                                           ["DAS_TEMPERATURE_REGISTER"]))
            self.opGroups["FAST"]["STREAMER"].addOperation(Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                                                                     ["STREAM_DasTemp","DAS_TEMPERATURE_REGISTER"]))

        # Set up interpolator environments for the warm box TEC, cavity TEC and heater

        env = interface.InterpolatorEnvType()
        env.current = env.target = 32768
        sender.wrEnv("WARM_BOX_TEC_INTERPOLATOR_ENV",env)

        env = interface.InterpolatorEnvType()
        env.current = env.target = 32768
        sender.wrEnv("CAVITY_TEC_INTERPOLATOR_ENV",env)

        env = interface.InterpolatorEnvType()
        env.current = env.target = 0
        sender.wrEnv("HEATER_INTERPOLATOR_ENV",env)

        present = self.installCheck("WARM_BOX_PRESENT")

        if present:
            # Etalon temperature
            # Read this quickly so that we get good temperature corrections for the wavelength monitor
            if present > 0:
                self.opGroups["FAST"]["SENSOR_READ"].addOperation(
                    Operation("ACTION_READ_THERMISTOR_RESISTANCE",
                        ["I2C_ETALON_THERMISTOR_ADC",
                         "ETALON_RESISTANCE_REGISTER",
                         "ETALON_THERMISTOR_SERIES_RESISTANCE_REGISTER"]))

            self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(
                Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
                    ["ETALON_RESISTANCE_REGISTER",
                     "CONVERSION_ETALON_THERM_CONSTA_REGISTER",
                     "CONVERSION_ETALON_THERM_CONSTB_REGISTER",
                     "CONVERSION_ETALON_THERM_CONSTC_REGISTER",
                     "ETALON_TEMPERATURE_REGISTER"]))
            # However, the streamed temperature data can be slow
            self.opGroups["SLOW"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_EtalonTemp","ETALON_TEMPERATURE_REGISTER"]))

            # Warm Box
            if present > 0:
                self.opGroups["SLOW"]["SENSOR_READ"].addOperation(
                    Operation("ACTION_READ_THERMISTOR_RESISTANCE",
                        ["I2C_WARM_BOX_THERMISTOR_ADC",
                         "WARM_BOX_RESISTANCE_REGISTER",
                         "WARM_BOX_THERMISTOR_SERIES_RESISTANCE_REGISTER"]))

                self.opGroups["SLOW"]["SENSOR_READ"].addOperation(
                    Operation("ACTION_READ_THERMISTOR_RESISTANCE",
                        ["I2C_WARM_BOX_HEATSINK_THERMISTOR_ADC",
                         "WARM_BOX_HEATSINK_RESISTANCE_REGISTER",
                         "WARM_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER"]))

            self.opGroups["SLOW"]["SENSOR_CONVERT"].addOperation(
                Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
                    ["WARM_BOX_RESISTANCE_REGISTER",
                     "CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER",
                     "CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER",
                     "CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER",
                     "WARM_BOX_TEMPERATURE_REGISTER"]))

            self.opGroups["SLOW"]["SENSOR_CONVERT"].addOperation(
                Operation("ACTION_RESISTANCE_TO_TEMPERATURE",
                    ["WARM_BOX_HEATSINK_RESISTANCE_REGISTER",
                     "CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER",
                     "CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER",
                     "CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER",
                     "WARM_BOX_HEATSINK_TEMPERATURE_REGISTER"]))

            self.opGroups["SLOW"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_WarmBoxTemp","WARM_BOX_TEMPERATURE_REGISTER"]))

            self.opGroups["SLOW"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_WarmBoxHeatsinkTemp","WARM_BOX_HEATSINK_TEMPERATURE_REGISTER"]))

            self.opGroups["SLOW"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_WarmBoxTec","WARM_BOX_TEC_REGISTER"]))

            self.opGroups["SLOW"]["CONTROLLER"].addOperation(
                Operation("ACTION_TEMP_CNTRL_WARM_BOX_STEP"))

        # Set up interpolation for warm box TEC. Make the following unconditional so that
        #  the PWM will always start up.

        if self.enableInterpolation:
            rateRatio = schedulerPeriods["SLOW"]//schedulerPeriods["FAST"]

            self.opGroups["SLOW"]["ACTUATOR_CONVERT"].addOperation(
                Operation("ACTION_INTERPOLATOR_SET_TARGET",
                          ["WARM_BOX_TEC_REGISTER",rateRatio],
                          "WARM_BOX_TEC_INTERPOLATOR_ENV"))

            self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
                Operation("ACTION_INTERPOLATOR_STEP",
                          ["FPGA_PWM_WARMBOX","PWM_PULSE_WIDTH"],
                          "WARM_BOX_TEC_INTERPOLATOR_ENV"))
        else:
            self.opGroups["SLOW"]["ACTUATOR_WRITE"].addOperation(
                Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
                          ["WARM_BOX_TEC_REGISTER","FPGA_PWM_WARMBOX","PWM_PULSE_WIDTH"]))

        # Hot Box

        present = self.installCheck("HOT_BOX_PRESENT")

        if present:
            # Hot box temperatures
            if present > 0:
                self.opGroups["SLOW"]["SENSOR_READ"].addOperation(
                    Operation("ACTION_READ_THERMISTOR_RESISTANCE",
                        ["I2C_CAVITY_THERMISTOR_ADC",
                         "CAVITY_RESISTANCE_REGISTER",
                         "CAVITY_THERMISTOR_SERIES_RESISTANCE_REGISTER"]))

                self.opGroups["SLOW"]["SENSOR_READ"].addOperation(
                    Operation("ACTION_READ_THERMISTOR_RESISTANCE",
                        ["I2C_HOT_BOX_HEATSINK_THERMISTOR_ADC",
                         "HOT_BOX_HEATSINK_RESISTANCE_REGISTER",
                         "HOT_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER"]))

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

            self.opGroups["SLOW"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_CavityTemp","CAVITY_TEMPERATURE_REGISTER"]))

            self.opGroups["SLOW"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_HotBoxHeatsinkTemp","HOT_BOX_HEATSINK_TEMPERATURE_REGISTER"]))

            self.opGroups["SLOW"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_HotBoxTec","CAVITY_TEC_REGISTER"]))

            #self.opGroups["SLOW"]["STREAMER"].addOperation(
            #    Operation("ACTION_STREAM_REGISTER_ASFLOAT",
            #        ["STREAM_HotBoxHeater","HEATER_CNTRL_MARK_REGISTER"]))

            self.opGroups["SLOW"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_HotBoxHeater","HEATER_MARK_REGISTER"]))

            self.opGroups["SLOW"]["CONTROLLER"].addOperation(
                Operation("ACTION_TEMP_CNTRL_CAVITY_STEP"))

            if self.heaterCntrlMode in [interface.HEATER_CNTRL_MODE_TEC_TARGET]:
                self.opGroups["SLOW"]["SENSOR_PROCESSING"].addOperation(
                    Operation("ACTION_FLOAT_ARITHMETIC",
                             ["CAVITY_TEC_REGISTER","CAVITY_TEC_REGISTER",
                             "HEATER_CNTRL_SENSOR_REGISTER","FLOAT_ARITHMETIC_Average"]))
            elif self.heaterCntrlMode in [interface.HEATER_CNTRL_MODE_DELTA_TEMP,interface.HEATER_CNTRL_MODE_HEATER_FIXED]:
                self.opGroups["SLOW"]["SENSOR_PROCESSING"].addOperation(
                    Operation("ACTION_FLOAT_ARITHMETIC",
                             ["HOT_BOX_HEATSINK_TEMPERATURE_REGISTER","CAVITY_TEMPERATURE_REGISTER",
                              "HEATER_CNTRL_SENSOR_REGISTER","FLOAT_ARITHMETIC_Subtraction"]))

            self.opGroups["SLOW"]["CONTROLLER"].addOperation(Operation("ACTION_HEATER_CNTRL_STEP"))

            # Set up the interpolator for the heater

            if self.enableInterpolation:
                rateRatio = schedulerPeriods["SLOW"]//schedulerPeriods["FAST"]

                self.opGroups["SLOW"]["ACTUATOR_CONVERT"].addOperation(
                    Operation("ACTION_INTERPOLATOR_SET_TARGET",
                              ["HEATER_MARK_REGISTER",rateRatio],
                              "HEATER_INTERPOLATOR_ENV"))

                self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
                    Operation("ACTION_INTERPOLATOR_STEP",
                              ["FPGA_PWM_HEATER","PWM_PULSE_WIDTH"],
                              "HEATER_INTERPOLATOR_ENV"))

            else:
                self.opGroups["SLOW"]["ACTUATOR_WRITE"].addOperation(
                    Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
                              ["HEATER_MARK_REGISTER","FPGA_PWM_HEATER","PWM_PULSE_WIDTH"]))

            #self.opGroups["SLOW"]["CONTROLLER"].addOperation(
            #    Operation("ACTION_HEATER_CNTRL_STEP"))

            #self.opGroups["SLOW"]["ACTUATOR_WRITE"].addOperation(
            #    Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
            #        ["HEATER_CNTRL_MARK_REGISTER","FPGA_PWM_HEATER","PWM_PULSE_WIDTH"]))

        # Set up interpolation for cavity TEC. Make the following unconditional so that
        #  the PWM will always start up.


        if self.enableInterpolation:
            rateRatio = schedulerPeriods["SLOW"]//schedulerPeriods["FAST"]


            self.opGroups["SLOW"]["ACTUATOR_CONVERT"].addOperation(
                Operation("ACTION_INTERPOLATOR_SET_TARGET",
                          ["CAVITY_TEC_REGISTER",rateRatio],
                          "CAVITY_TEC_INTERPOLATOR_ENV"))

            self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
                Operation("ACTION_INTERPOLATOR_STEP",
                          ["FPGA_PWM_HOTBOX","PWM_PULSE_WIDTH"],
                          "CAVITY_TEC_INTERPOLATOR_ENV"))
        else:
            self.opGroups["SLOW"]["ACTUATOR_WRITE"].addOperation(
                Operation("ACTION_FLOAT_REGISTER_TO_FPGA",
                          ["CAVITY_TEC_REGISTER","FPGA_PWM_HOTBOX","PWM_PULSE_WIDTH"]))

        # Fan control
        fanCntrl = not self.installCheck("FAN_CONTROL_DISABLED")
        if fanCntrl:
            self.opGroups["SLOW"]["CONTROLLER"].addOperation(Operation("ACTION_FAN_CNTRL_STEP"))
            self.opGroups["SLOW"]["ACTUATOR_WRITE"].addOperation(
                Operation("ACTION_ACTIVATE_FAN",["FAN_CNTRL_STATE_REGISTER"]))

        # Valve control

        if present:
            # Pressure reading
            if present>0:
                self.opGroups["FAST"]["SENSOR_READ"].addOperation(
                    Operation("ACTION_READ_PRESSURE_ADC",
                        ["I2C_CAVITY_PRESSURE_ADC",
                         "CAVITY_PRESSURE_ADC_REGISTER"]))

                self.opGroups["FAST"]["SENSOR_READ"].addOperation(
                    Operation("ACTION_READ_PRESSURE_ADC",
                        ["I2C_AMBIENT_PRESSURE_ADC",
                         "AMBIENT_PRESSURE_ADC_REGISTER"]))

                self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
                    Operation("ACTION_SET_INLET_VALVE",
                              ["VALVE_CNTRL_INLET_VALVE_REGISTER","VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER"]))

                self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
                    Operation("ACTION_SET_OUTLET_VALVE",
                              ["VALVE_CNTRL_OUTLET_VALVE_REGISTER","VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER"]))

                self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
                    Operation("ACTION_MODIFY_VALVE_PUMP_TEC_FROM_REGISTER",
                              [0x3F,"VALVE_CNTRL_SOLENOID_VALVES_REGISTER"]))

            self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(
                Operation("ACTION_ADC_TO_PRESSURE",
                    ["CAVITY_PRESSURE_ADC_REGISTER",
                     "CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER",
                     "CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER",
                     "CAVITY_PRESSURE_REGISTER"]))

            self.opGroups["FAST"]["SENSOR_CONVERT"].addOperation(
                Operation("ACTION_ADC_TO_PRESSURE",
                    ["AMBIENT_PRESSURE_ADC_REGISTER",
                     "CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER",
                     "CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER",
                     "AMBIENT_PRESSURE_REGISTER"]))

            self.opGroups["FAST"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_CavityPressure","CAVITY_PRESSURE_REGISTER"]))

            self.opGroups["FAST"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_AmbientPressure","AMBIENT_PRESSURE_REGISTER"]))

            self.opGroups["FAST"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_InletValve","VALVE_CNTRL_INLET_VALVE_REGISTER"]))

            self.opGroups["FAST"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_OutletValve","VALVE_CNTRL_OUTLET_VALVE_REGISTER"]))

            self.opGroups["FAST"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_ValveMask","VALVE_CNTRL_SOLENOID_VALVES_REGISTER"]))

            self.opGroups["SLOW"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_FanState","FAN_CNTRL_STATE_REGISTER"]))

            self.opGroups["FAST"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_MPVPosition","VALVE_CNTRL_MPV_POSITION_REGISTER"]))

            self.opGroups["FAST"]["CONTROLLER"].addOperation(
                Operation("ACTION_VALVE_CNTRL_STEP"))

        # Ringdown detector variable gain control

        rddVarGainPresent = self.installCheck("RDD_VAR_GAIN_PRESENT")
        if rddVarGainPresent:
            self.opGroups["FAST"]["CONTROLLER"].addOperation(
                Operation("ACTION_RDD_CNTRL_STEP"))

        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_SPECTRUM_CNTRL_STEP"))

        self.opGroups["FAST"]["CONTROLLER"].addOperation(
            Operation("ACTION_TUNER_CNTRL_STEP"))

        # Update the laser temperature register of the WLM simulator
        self.opGroups["FAST"]["ACTUATOR_WRITE"].addOperation(
            Operation("ACTION_UPDATE_WLMSIM_LASER_TEMP"))

        # Streaming outputs of wavelength monitor
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_FPGA_REGISTER_ASFLOAT",
                ["STREAM_Etalon1","FPGA_LASERLOCKER","LASERLOCKER_ETA1"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_FPGA_REGISTER_ASFLOAT",
                ["STREAM_Reference1","FPGA_LASERLOCKER","LASERLOCKER_REF1"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_FPGA_REGISTER_ASFLOAT",
                ["STREAM_Etalon2","FPGA_LASERLOCKER","LASERLOCKER_ETA2"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_FPGA_REGISTER_ASFLOAT",
                ["STREAM_Reference2","FPGA_LASERLOCKER","LASERLOCKER_REF2"]))

        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_FPGA_REGISTER_ASFLOAT",
                ["STREAM_Ratio1","FPGA_LASERLOCKER","LASERLOCKER_RATIO1"]))
        self.opGroups["FAST"]["STREAMER"].addOperation(
            Operation("ACTION_STREAM_FPGA_REGISTER_ASFLOAT",
                ["STREAM_Ratio2","FPGA_LASERLOCKER","LASERLOCKER_RATIO2"]))

        if self.installCheck("FLOW_SENSOR_PRESENT"):
            self.opGroups["FAST"]["SENSOR_READ"].addOperation(
                Operation("ACTION_READ_FLOW_SENSOR",
                        ["I2C_FLOW1_SENSOR","CONVERSION_FLOW1_SCALE_REGISTER",
                         "CONVERSION_FLOW1_OFFSET_REGISTER","FLOW1_REGISTER"]))
            self.opGroups["FAST"]["STREAMER"].addOperation(
                Operation("ACTION_STREAM_REGISTER_ASFLOAT",
                    ["STREAM_Flow1","FLOW1_REGISTER"]))

        self.opGroups["MEDIUM"]["STREAMER"].addOperation(
            Operation("ACTION_TEST_SCHEDULER", [1, 2, 3, 4]))

        # Stop the scheduler before loading new schedule
        sender.wrRegUint("SCHEDULER_CONTROL_REGISTER",0);
        # Schedule operation groups which are non-empty
        groups = [g for c in self.opGroups.values()
                    for g in c.values() if g]
        self.dasInterface.uploadSchedule(groups)

        # Perform one-time initializations

        sender.doOperation(Operation("ACTION_INIT_RUNQUEUE",[len(groups)]))

        # Schedule code specified in the initialization file
        if self.extraInitCode is not None:
            try:
                exec self.extraInitCode in self.scriptEnv
            except:
                LogExc("Error processing extra initialization code in Driver initialization file", Level=3)

        runCont = (1<<interface.PWM_CS_RUN_B) | (1<<interface.PWM_CS_CONT_B)

        for laserNum in range(1,5):
            if self.installCheck("LASER%d_PRESENT" % laserNum) or (laserNum == 4 and (soa or fiber_amp)):
                sender.doOperation(Operation("ACTION_TEMP_CNTRL_LASER%d_INIT" % laserNum))
                sender.doOperation(Operation("ACTION_CURRENT_CNTRL_LASER%d_INIT" % laserNum))
                sender.doOperation(Operation("ACTION_INT_TO_FPGA",[0x8000,"FPGA_PWM_LASER%d" % laserNum,"PWM_PULSE_WIDTH"]))
                # Enable the PWM state machines in the FPGA
                sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_PWM_LASER%d" % laserNum,"PWM_CS"]))

        sender.doOperation(Operation("ACTION_TEMP_CNTRL_WARM_BOX_INIT"))
        sender.doOperation(Operation("ACTION_TEMP_CNTRL_CAVITY_INIT"))
        sender.doOperation(Operation("ACTION_HEATER_CNTRL_INIT"))
        if fanCntrl: sender.doOperation(Operation("ACTION_FAN_CNTRL_INIT"))
        if rddVarGainPresent: sender.doOperation(Operation("ACTION_RDD_CNTRL_INIT"))

        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[0x8000,"FPGA_PWM_WARMBOX","PWM_PULSE_WIDTH"]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_PWM_WARMBOX","PWM_CS"]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[0x8000,"FPGA_PWM_HOTBOX","PWM_PULSE_WIDTH"]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_PWM_HOTBOX","PWM_CS"]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[0x0,"FPGA_PWM_HEATER","PWM_PULSE_WIDTH"]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_PWM_HEATER","PWM_CS"]))

        # Must do following AFTER turning on the warm box and hot box PWM and allowing the monostable
        #  to trigger

        # Remove reset on I2C multiplexers
        time.sleep(0.5)
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[0,"FPGA_KERNEL","KERNEL_CONTROL"]))

        # Check to see which I2C devices are installed on this instrument
        for i in range(len(interface.i2cByIndex)):
            ident = interface.i2cByIndex[i]
            status = sender.doOperation(Operation("ACTION_I2C_CHECK",interface.i2cByIdent[ident][-3:]))
            self.i2cConfig[ident] = (status >= 0)
            print "%s present: %s" % (ident,"True" if self.i2cConfig[ident] else "False")

        sender.doOperation(Operation("ACTION_VALVE_CNTRL_INIT"))
        sender.doOperation(Operation("ACTION_SPECTRUM_CNTRL_INIT"))
        sender.doOperation(Operation("ACTION_TUNER_CNTRL_INIT"))

        sender.wrRegFloat("LASER1_RESISTANCE_REGISTER",10000.0)
        sender.wrRegFloat("LASER2_RESISTANCE_REGISTER",9000.0)
        sender.wrRegFloat("LASER3_RESISTANCE_REGISTER",8000.0)
        sender.wrRegFloat("LASER4_RESISTANCE_REGISTER",7000.0)
        sender.wrRegFloat("LASER1_CURRENT_MONITOR_REGISTER",110.0)
        sender.wrRegFloat("LASER2_CURRENT_MONITOR_REGISTER",120.0)
        sender.wrRegFloat("LASER3_CURRENT_MONITOR_REGISTER",130.0)
        sender.wrRegFloat("LASER4_CURRENT_MONITOR_REGISTER",140.0)

        sender.wrRegFloat("ETALON_RESISTANCE_REGISTER",5800.0)
        sender.wrRegFloat("WARM_BOX_RESISTANCE_REGISTER",5900.0)
        sender.wrRegFloat("WARM_BOX_HEATSINK_RESISTANCE_REGISTER",5800.0)
        sender.wrRegFloat("HOT_BOX_HEATSINK_RESISTANCE_REGISTER",60000.0)
        sender.wrRegFloat("CAVITY_RESISTANCE_REGISTER",59000.0)

        sender.wrRegUint("AMBIENT_PRESSURE_ADC_REGISTER",11000000)
        sender.wrRegUint("CAVITY_PRESSURE_ADC_REGISTER",1500000)

        # Start the ringdown manager
        runCont = (1<<interface.RDMAN_CONTROL_RUN_B) | (1<<interface.RDMAN_CONTROL_CONT_B)
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_RDMAN","RDMAN_CONTROL"]))
        #  Start the laser locker
        runCont = (1<<interface.LASERLOCKER_CS_RUN_B) | (1<<interface.LASERLOCKER_CS_CONT_B)
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_LASERLOCKER","LASERLOCKER_CS"]))

        # Start the dynamic PWM blocks running
        runCont = (1<<interface.DYNAMICPWM_CS_RUN_B) | (1<<interface.DYNAMICPWM_CS_CONT_B) | (1<<interface.DYNAMICPWM_CS_PWM_ENABLE_B)
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_DYNAMICPWM_INLET","DYNAMICPWM_CS"]))
        sender.doOperation(Operation("ACTION_INT_TO_FPGA",[runCont,"FPGA_DYNAMICPWM_OUTLET","DYNAMICPWM_CS"]))
        time.sleep(2)
        sender.doOperation(Operation("ACTION_SENTRY_INIT"))
        # Set the scheduler running
        sender.wrRegUint("SCHEDULER_CONTROL_REGISTER",1)