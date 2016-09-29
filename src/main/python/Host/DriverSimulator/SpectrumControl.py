#!/usr/bin/python
#
"""
File Name: SpectrumControl.py
Purpose: Classes for temperature controllers

File History:
    26-Sep-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""
from Host.autogen import interface
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.DriverSimulator.Utilities import prop_das, prop_fpga

APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)


class SpectrumControl(object):
    state = prop_das(interface.SPECT_CNTRL_STATE_REGISTER)
    mode = prop_das(interface.SPECT_CNTRL_MODE_REGISTER)
    active = prop_das(interface.SPECT_CNTRL_ACTIVE_SCHEME_REGISTER)
    next = prop_das(interface.SPECT_CNTRL_NEXT_SCHEME_REGISTER)
    iter = prop_das(interface.SPECT_CNTRL_SCHEME_ITER_REGISTER)
    row = prop_das(interface.SPECT_CNTRL_SCHEME_ROW_REGISTER)
    dwell = prop_das(interface.SPECT_CNTRL_DWELL_COUNT_REGISTER)
    defaultThreshold = prop_das(interface.SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER)
    analyzerTuningMode = prop_das(interface.ANALYZER_TUNING_MODE_REGISTER)
    virtLaser = prop_das(interface.VIRTUAL_LASER_REGISTER)
    dasStatus = prop_das(interface.DAS_STATUS_REGISTER)
    injectControlMode = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MODE_B, interface.INJECT_CONTROL_MODE_W)
    lockEnabled = prop_fpga(interface.FPGA_RDMAN, interface.RDMAN_OPTIONS, interface.RDMAN_OPTIONS_LOCK_ENABLE_B, interface.RDMAN_OPTIONS_LOCK_ENABLE_W)
    laserShutdownEnabled = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B, interface.INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W)
    soaShutdownEnabled = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B, interface.INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W)
    rampDitherMode = prop_fpga(interface.FPGA_RDMAN, interface.RDMAN_CONTROL, interface.RDMAN_CONTROL_RAMP_DITHER_B, interface.RDMAN_CONTROL_RAMP_DITHER_W)

    def __init__(self, sim):
        self.sim = sim
        self.das_registers = sim.das_registers
        self.fpga_registers = sim.fpga_registers
        self.schemeCounter = 0
        self.incrCounter = 0
        self.incrCounterNext = 0
        self.useMemo = 0
        self.prevState = interface.SPECT_CNTRL_IdleState

    def setAutomaticLaserCurrentControl(self):
        self.sim.wrDasReg("LASER1_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER2_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER3_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER4_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_AutomaticState")
        # Setting the FPGA optical injection block to automatic mode has to be done independently
        #  of setting the individual current controllers. Care is needed since the current controllers
        #  periodically write to the INJECT_CONTROL register.
        self.injectControlMode = 1

    def setAutomaticLaserTemperatureControl(self):
        self.sim.wrDasReg("LASER1_TEMP_CNTRL_STATE_REGISTER","TEMP_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER2_TEMP_CNTRL_STATE_REGISTER","TEMP_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER3_TEMP_CNTRL_STATE_REGISTER","TEMP_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER4_TEMP_CNTRL_STATE_REGISTER","TEMP_CNTRL_AutomaticState")

    def setManualLaserCurrentControl(self):
        self.sim.wrDasReg("LASER1_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
        self.sim.wrDasReg("LASER2_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
        self.sim.wrDasReg("LASER3_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")
        self.sim.wrDasReg("LASER4_CURRENT_CNTRL_STATE_REGISTER","LASER_CURRENT_CNTRL_ManualState")

    def step(self):
        stateAtStart = self.state
        if self.state == interface.SPECT_CNTRL_StartingState:
            # Start of a new scheme
            self.useMemo = 0
            self.incrCounterNext = self.incrCounter + 1
            self.schemeCounter += 1
            self.setAutomaticLaserTemperatureControl()
            self.setAutomaticLaserCurrentControl()
            self.state = interface.SPECT_CNTRL_RunningState
            if self.mode in [
                interface.SPECT_CNTRL_SchemeSingleMode,
                interface.SPECT_CNTRL_SchemeMultipleMode,
                interface.SPECT_CNTRL_SchemeMultipleNoRepeatMode,
            ]:
                # For schemes, enable frequency locking unless we are in FSR hopping mode
                if self.mode == interface.ANALYZER_TUNING_FsrHoppingTuningMode:
                    self.lockEnabled = 0
                else:
                    self.lockEnabled = 1
                self.iter = 0
                self.row = 0
                self.dwell = 0
                # When starting acquisition, go to scheme specified by next
                self.active = self.next
        elif self.state == interface.SPECT_CNTRL_StartManualState:
            # Start of a manual temperature control mode (no scheme)
            self.useMemo = 0
            self.incrCounterNext = self.incrCounter + 1
            self.schemeCounter += 1
            self.mode = interface.SPECT_CNTRL_ContinuousManualTempMode
            self.setAutomaticLaserCurrentControl()
            self.state = interface.SPECT_CNTRL_RunningState
        elif self.state == interface.SPECT_CNTRL_RunningState:
            # Collect ringdowns
            if self.prevState in [
                interface.SPECT_CNTRL_StartingState,
                interface.SPECT_CNTRL_StartManualState,
                interface.SPECT_CNTRL_PausedState
            ]:
                self.switchToRampMode()
                self.laserShutdownEnabled = 1
                self.soaShutdownEnabled = 1
                self.sim.startRdcycle = True
        elif self.state == interface.SPECT_CNTRL_IdleState:
            if self.prevState != interface.SPECT_CNTRL_IdleState:
                self.switchToRampMode()
                self.setManualLaserCurrentControl()
            self.useMemo = False
        elif self.state == interface.SPECT_CNTRL_DiagnosticState:
            self.switchToRampMode()
            self.setAutomaticLaserCurrentControl()
        else:
            self.switchToRampMode()

        self.prevState = stateAtStart
        return interface.STATUS_OK

    def switchToRampMode(self):
        self.sim.tunerSimulator.switchToRampMode()