#!/usr/bin/python
#
"""
File Name: LaserCurrentControl.py
Purpose: Classes for laser current controllers

File History:
    19-Sep-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""

from Host.autogen import interface
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.DriverSimulator.Utilities import prop_das, prop_fpga

APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)


class LaserCurrentControl(object):
    # Base class for laser current controllers
    # The following are properties in the subclasses
    state = None
    manualCoarse = None
    manualFine = None
    swpMin = None
    swpMax = None
    swpInc = None
    currentEnable = None
    laserEnable = None
    automatic = None
    fpgaCoarse = None
    fpgaFine = None

    def __init__(self, sim):
        self.sim = sim
        self.das_registers = sim.das_registers
        self.fpga_registers = sim.fpga_registers
        self.coarse = 0
        self.swpDir = 1
        self.state = interface.LASER_CURRENT_CNTRL_DisabledState
        self.laserNum = None

    def step(self):
        if self.state == interface.LASER_CURRENT_CNTRL_DisabledState:
            self.coarse = 0
            fine = 0
            self.currentEnable = 0
            self.laserEnable = 0
        elif self.state == interface.LASER_CURRENT_CNTRL_AutomaticState:
            self.coarse = self.manualCoarse
            fine = 32768
            self.currentEnable = 1
            self.laserEnable = 1 # 0 In reality, the laser is turned on by the FPGA
        elif self.state == interface.LASER_CURRENT_CNTRL_ManualState:
            self.coarse = self.manualCoarse
            fine = self.manualFine
            self.currentEnable = 1
            self.laserEnable = 1
            self.automatic = 0
        elif self.state == interface.LASER_CURRENT_CNTRL_SweepingState:
            self.coarse += self.swpDir * self.swpInc
            if self.coarse >= self.swpMax:
                self.coarse = self.swpMax
                self.swpDir = -1
            elif self.coarse <= self.swpMin:
                self.coarse = self.swpMin
                self.swpDir = 1
            fine = self.manualFine
            self.currentEnable = 1
            self.laserEnable = 1
            self.automatic = 0
        self.fpgaCoarse = self.coarse
        self.fpgaFine = fine
        return interface.STATUS_OK


class Laser1CurrentControl(LaserCurrentControl):
    state = prop_das(interface.LASER1_CURRENT_CNTRL_STATE_REGISTER)
    manualCoarse = prop_das(interface.LASER1_MANUAL_COARSE_CURRENT_REGISTER)
    manualFine = prop_das(interface.LASER1_MANUAL_FINE_CURRENT_REGISTER)
    swpMin = prop_das(interface.LASER1_CURRENT_SWEEP_MIN_REGISTER)
    swpMax = prop_das(interface.LASER1_CURRENT_SWEEP_MAX_REGISTER)
    swpInc = prop_das(interface.LASER1_CURRENT_SWEEP_INCR_REGISTER)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER1_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER1_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER1_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER1_ENABLE_W)
    automatic = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MODE_B, interface.INJECT_CONTROL_MODE_W)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER1_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER1_FINE_CURRENT)
    laserNum = 1


class Laser2CurrentControl(LaserCurrentControl):
    state = prop_das(interface.LASER2_CURRENT_CNTRL_STATE_REGISTER)
    manualCoarse = prop_das(interface.LASER2_MANUAL_COARSE_CURRENT_REGISTER)
    manualFine = prop_das(interface.LASER2_MANUAL_FINE_CURRENT_REGISTER)
    swpMin = prop_das(interface.LASER2_CURRENT_SWEEP_MIN_REGISTER)
    swpMax = prop_das(interface.LASER2_CURRENT_SWEEP_MAX_REGISTER)
    swpInc = prop_das(interface.LASER2_CURRENT_SWEEP_INCR_REGISTER)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER2_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER2_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER2_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER2_ENABLE_W)
    automatic = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MODE_B, interface.INJECT_CONTROL_MODE_W)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER2_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER2_FINE_CURRENT)
    laserNum = 2


class Laser3CurrentControl(LaserCurrentControl):
    state = prop_das(interface.LASER3_CURRENT_CNTRL_STATE_REGISTER)
    manualCoarse = prop_das(interface.LASER3_MANUAL_COARSE_CURRENT_REGISTER)
    manualFine = prop_das(interface.LASER3_MANUAL_FINE_CURRENT_REGISTER)
    swpMin = prop_das(interface.LASER3_CURRENT_SWEEP_MIN_REGISTER)
    swpMax = prop_das(interface.LASER3_CURRENT_SWEEP_MAX_REGISTER)
    swpInc = prop_das(interface.LASER3_CURRENT_SWEEP_INCR_REGISTER)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER3_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER3_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER3_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER3_ENABLE_W)
    automatic = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MODE_B, interface.INJECT_CONTROL_MODE_W)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER3_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER3_FINE_CURRENT)
    laserNum = 3


class Laser4CurrentControl(LaserCurrentControl):
    state = prop_das(interface.LASER4_CURRENT_CNTRL_STATE_REGISTER)
    manualCoarse = prop_das(interface.LASER4_MANUAL_COARSE_CURRENT_REGISTER)
    manualFine = prop_das(interface.LASER4_MANUAL_FINE_CURRENT_REGISTER)
    swpMin = prop_das(interface.LASER4_CURRENT_SWEEP_MIN_REGISTER)
    swpMax = prop_das(interface.LASER4_CURRENT_SWEEP_MAX_REGISTER)
    swpInc = prop_das(interface.LASER4_CURRENT_SWEEP_INCR_REGISTER)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER4_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER4_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER4_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER4_ENABLE_W)
    automatic = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MODE_B, interface.INJECT_CONTROL_MODE_W)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER4_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER4_FINE_CURRENT)
    laserNum = 4
