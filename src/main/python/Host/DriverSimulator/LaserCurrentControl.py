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

APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)


def das_register_getter(index):
    def fget(self):
        return self.das_registers[index]
    return fget


def das_register_setter(index):
    def fset(self, value):
        self.das_registers[index] = value
    return fset


def prop(index):
    return property(das_register_getter(index), das_register_setter(index))


class LaserCurrentControl(object):
    # Base class for laser current controllers
    # The following are properties in the subclasses
    state = None
    manual_coarse = None
    manual_fine = None
    swpMin = None
    swpMax = None
    swpInc = None

    def __init__(self, das_registers, sim):
        self.das_registers = das_registers
        self.sim = sim
        self.coarse = 0
        self.swpDir = 1
        self.state = interface.LASER_CURRENT_CNTRL_DisabledState
        self.fpga_coarse = None
        self.fpga_fine = None
        self.fpga_control = None
        self.laserNum = None

    def step(self):
        current_enable_mask = 1 << (interface.INJECT_CONTROL_LASER_CURRENT_ENABLE_B + self.laserNum - 1)
        laser_enable_mask = 1 << (interface.INJECT_CONTROL_MANUAL_LASER_ENABLE_B + self.laserNum - 1)
        automatic_mask = 1 << interface.INJECT_CONTROL_MODE_B

        if self.state == interface.LASER_CURRENT_CNTRL_DisabledState:
            self.coarse = 0
            fine = 0
            self.sim.changeInMaskFPGA(
                self. fpga_control, 
                current_enable_mask | laser_enable_mask, 
                0)
        elif self.state == interface.LASER_CURRENT_CNTRL_AutomaticState:
            self.coarse = self.manual_coarse
            fine = 32768
            self.sim.changeInMaskFPGA(
                self. fpga_control, 
                current_enable_mask | laser_enable_mask, 
                current_enable_mask)
        elif self.state == interface.LASER_CURRENT_CNTRL_ManualState:
            self.coarse = self.manual_coarse
            fine = self.manual_fine
            self.sim.changeInMaskFPGA(
                self. fpga_control, 
                current_enable_mask | laser_enable_mask | automatic_mask, 
                current_enable_mask | laser_enable_mask)
        elif self.state == interface.LASER_CURRENT_CNTRL_SweepingState:
            self.coarse += self.swpDir * self.swpInc
            if self.coarse >= self.swpMax:
                self.coarse = self.swpMax
                self.swpDir = -1
            elif self.coarse <= self.swpMin:
                self.coarse = self.swpMin
                self.swpDir = 1
            fine = self.manual_fine
            self.sim.changeInMaskFPGA(
                self. fpga_control, 
                current_enable_mask | laser_enable_mask | automatic_mask, 
                current_enable_mask | laser_enable_mask)
        self.sim.wrFPGA(self.fpga_coarse, 0, self.coarse)
        self.sim.wrFPGA(self.fpga_fine, 0, fine)
        return interface.STATUS_OK


class Laser1CurrentControl(LaserCurrentControl):
    state = prop(interface.LASER1_CURRENT_CNTRL_STATE_REGISTER)
    manual_coarse = prop(interface.LASER1_MANUAL_COARSE_CURRENT_REGISTER)
    manual_fine = prop(interface.LASER1_MANUAL_FINE_CURRENT_REGISTER)
    swpMin = prop(interface.LASER1_CURRENT_SWEEP_MIN_REGISTER)
    swpMax = prop(interface.LASER1_CURRENT_SWEEP_MAX_REGISTER)
    swpInc = prop(interface.LASER1_CURRENT_SWEEP_INCR_REGISTER)

    def __init__(self, *args, **kwargs):
        super(Laser1CurrentControl, self).__init__(*args, **kwargs)
        self.fpga_coarse = interface.FPGA_INJECT + interface.INJECT_LASER1_COARSE_CURRENT
        self.fpga_fine = interface.FPGA_INJECT + interface.INJECT_LASER1_FINE_CURRENT
        self.fpga_control = interface.FPGA_INJECT + interface.INJECT_CONTROL
        self.laserNum = 1


class Laser2CurrentControl(LaserCurrentControl):
    state = prop(interface.LASER2_CURRENT_CNTRL_STATE_REGISTER)
    manual_coarse = prop(interface.LASER2_MANUAL_COARSE_CURRENT_REGISTER)
    manual_fine = prop(interface.LASER2_MANUAL_FINE_CURRENT_REGISTER)
    swpMin = prop(interface.LASER2_CURRENT_SWEEP_MIN_REGISTER)
    swpMax = prop(interface.LASER2_CURRENT_SWEEP_MAX_REGISTER)
    swpInc = prop(interface.LASER2_CURRENT_SWEEP_INCR_REGISTER)

    def __init__(self, *args, **kwargs):
        super(Laser2CurrentControl, self).__init__(*args, **kwargs)
        self.fpga_coarse = interface.FPGA_INJECT + interface.INJECT_LASER2_COARSE_CURRENT
        self.fpga_fine = interface.FPGA_INJECT + interface.INJECT_LASER2_FINE_CURRENT
        self.fpga_control = interface.FPGA_INJECT + interface.INJECT_CONTROL
        self.laserNum = 2


class Laser3CurrentControl(LaserCurrentControl):
    state = prop(interface.LASER3_CURRENT_CNTRL_STATE_REGISTER)
    manual_coarse = prop(interface.LASER3_MANUAL_COARSE_CURRENT_REGISTER)
    manual_fine = prop(interface.LASER3_MANUAL_FINE_CURRENT_REGISTER)
    swpMin = prop(interface.LASER3_CURRENT_SWEEP_MIN_REGISTER)
    swpMax = prop(interface.LASER3_CURRENT_SWEEP_MAX_REGISTER)
    swpInc = prop(interface.LASER3_CURRENT_SWEEP_INCR_REGISTER)

    def __init__(self, *args, **kwargs):
        super(Laser3CurrentControl, self).__init__(*args, **kwargs)
        self.fpga_coarse = interface.FPGA_INJECT + interface.INJECT_LASER3_COARSE_CURRENT
        self.fpga_fine = interface.FPGA_INJECT + interface.INJECT_LASER3_FINE_CURRENT
        self.fpga_control = interface.FPGA_INJECT + interface.INJECT_CONTROL
        self.laserNum = 3


class Laser4CurrentControl(LaserCurrentControl):
    state = prop(interface.LASER4_CURRENT_CNTRL_STATE_REGISTER)
    manual_coarse = prop(interface.LASER4_MANUAL_COARSE_CURRENT_REGISTER)
    manual_fine = prop(interface.LASER4_MANUAL_FINE_CURRENT_REGISTER)
    swpMin = prop(interface.LASER4_CURRENT_SWEEP_MIN_REGISTER)
    swpMax = prop(interface.LASER4_CURRENT_SWEEP_MAX_REGISTER)
    swpInc = prop(interface.LASER4_CURRENT_SWEEP_INCR_REGISTER)

    def __init__(self, *args, **kwargs):
        super(Laser4CurrentControl, self).__init__(*args, **kwargs)
        self.fpga_coarse = interface.FPGA_INJECT + interface.INJECT_LASER4_COARSE_CURRENT
        self.fpga_fine = interface.FPGA_INJECT + interface.INJECT_LASER4_FINE_CURRENT
        self.fpga_control = interface.FPGA_INJECT + interface.INJECT_CONTROL
        self.laserNum = 4
