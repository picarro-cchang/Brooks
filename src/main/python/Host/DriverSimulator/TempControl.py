#!/usr/bin/python
#
"""
File Name: TempControl.py
Purpose: Classes for temperature controllers

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


class TempControl(object):
    # Base class for temperature controllers
    # The following are properties in the subclasses
    r = None
    b = None
    c = None
    h = None
    K = None
    Ti = None
    Td = None
    N = None
    S = None
    Imax = None
    Amin = None
    Amax = None
    ffwd = None
    userSetpoint = None
    state = None
    tol = None
    swpMin = None
    swpMax = None
    swpInc = None
    prbsAmp = None
    prbsMean = None
    prbsGen = None
    temp = None
    dasTemp = None
    tec = None
    manualTec = None
    extMax = None
    extTemp = None

    def __init__(self, das_registers):
        self.das_registers = das_registers
        self.disabledValue = 0x8000
        self.extMax = 0
        self.extTemp = 0
        self.swpDir = 1
        self.state = interface.TEMP_CNTRL_DisabledState
        self.lockCount = 0
        self.unlockCount = 0
        self.firstIteration = True
        self.perr = 0
        self.derr1 = 0
        self.derr2 = 0
        self.Dincr = 0
        self.tec = self.disabledValue
        self.lastTec = self.disabledValue
        self.a = self.disabledValue
        self.u = self.disabledValue
        self.r = self.userSetpoint
        self.prbsReg = 0
        self.activeBit = None
        self.lockBit = None

    def resetDasStatusBit(self, bitnum):
        mask = 1 << bitnum
        self.das_registers[interface.DAS_STATUS_REGISTER] &= (~mask)

    def setDasStatusBit(self, bitnum):
        mask = 1 << bitnum
        self.das_registers[interface.DAS_STATUS_REGISTER] |= mask

    def getDasStatusBit(self, bitnum):
        mask = 1 << bitnum
        return 0 != (self.das_registers[interface.DAS_STATUS_REGISTER] & mask)

    def step(self):
        if self.state == interface.TEMP_CNTRL_DisabledState:
            self.resetDasStatusBit(self.activeBit)
            self.resetDasStatusBit(self.lockBit)
            self.tec = self.disabledValue
            self.firstIteration = True
            self.prbsReg = 0x1
        elif self.state == interface.TEMP_CNTRL_ManualState:
            self.setDasStatusBit(self.activeBit)
            self.resetDasStatusBit(self.lockBit)
            if self.manualTec > self.Amax:
                self.manualTec = self.Amax
            if self.manualTec < self.Amin:
                self.manualTec = self.Amin
            self.tec = self.manualTec
            self.firstIteration = True
            self.prbsReg = 0x1
        elif self.state in [interface.TEMP_CNTRL_EnabledState,
                            interface.TEMP_CNTRL_AutomaticState]:
            if self.state == interface.TEMP_CNTRL_EnabledState:
                self.r = self.userSetpoint
            self.setDasStatusBit(self.activeBit)
            error = self.r - self.temp
            inRange = (error >= -self.tol) and (error <= self.tol)
            if self.firstIteration:
                self.firstIteration = False
                self.pidBumplessRestart()
            else:
                self.pidStep()
            if self.getDasStatusBit(self.lockBit):
                if not inRange:
                    self.unlockCount += 1
                else:
                    self.unlockCount = 0
                if self.unlockCount > interface.TEMP_CNTRL_UNLOCK_COUNT:
                    self.resetDasStatusBit(self.lockBit)
            else:
                if inRange:
                    self.lockCount += 1
                else:
                    self.lockCount = 0
                if self.lockCount > interface.TEMP_CNTRL_LOCK_COUNT:
                    self.setDasStatusBit(self.lockBit)
            self.tec = self.a
            self.prbsReg = 0x1
        elif self.state == interface.TEMP_CNTRL_SweepingState:
            self.setDasStatusBit(self.activeBit)
            self.resetDasStatusBit(self.lockBit)
            self.r += self.swpDir * self.swpInc
            if self.r >= self.swpMax:
                self.r = self.swpMax
                self.swpDir = -1
            elif self.r <= self.swpMin:
                self.r = self.swpMin
                self.swpDir = 1
            if self.firstIteration:
                self.firstIteration = False
                self.pidBumplessRestart()
            else:
                self.pidStep()
            self.tec = self.a
            self.prbsReg = 0x1
        elif self.state == interface.TEMP_CNTRL_SendPrbsState:
            self.setDasStatusBit(self.activeBit)
            self.resetDasStatusBit(self.lockBit)
            if self.prbsReg & 0x1:
                tecNext = self.prbsMean + self.prbsAmp
                self.prbsReg ^= self.prbsGen
            else:
                tecNext = self.prbsMean - self.prbsAmp
            if tecNext > self.Amax:
                tecNext = self.Amax
            if tecNext < self.Amin:
                tecNext = self.Amin
            self.tec = tecNext
            self.prbsReg >>= 1
            self.firstIteration = True
        # If there is a heatsink temperature sensor whose value should
        #  not exceed self.extMax, move the tec towards self.disabledValue
        if (self.extMax is not None) and (self.extTemp is not None):
            if self.extTemp > self.extMax:
                change = self.disabledValue - self.lastTec
                if change > self.Imax:
                    change = self.Imax
                if change < -self.Imax:
                    change = -self.Imax
                self.tec = self.lastTec + change
                self.a = self.tec
        self.lastTec = self.tec
        return interface.STATUS_OK

    def pidBumplessRestart(self):
        perr = self.b * self.r - self.temp
        derr = self.c * self.r - self.temp
        self.perr = perr
        self.derr1 = derr
        self.derr2 = derr
        self.Dincr = 0
        self.u = self.a

    def pidStep(self):
        # Implement PID controller by calculating the change of the
        #  actuator necessary on a timestep

        # Compute integral, proportional and derivative error terms
        err = self.r - self.temp
        perr = self.b * self.r - self.temp
        derr = self.c * self.r - self.temp
        # The feedforward term is added to the actuator value directly
        #  and bypasses the loop, This is done by initializing the change
        #  variable with this term
        change = self.ffwd * (self.temp - self.dasTemp)
        # Calculate contributions to the change of the actuator value
        # self.u is the actuator value calculated by PID algorithm
        # self.a is the constrained actuator value, limited by 
        # self.Amin, self.Amax and self.Imax
        Pincr = self.K * (perr - self.perr)
        Iincr = (self.K * self.h / self.Ti) * err + (self.a - self.u - change) / self.S
        Dincr = self.Td / (self.Td + self.N * self.h) * (self.Dincr + self.K * self.N * (derr - 2 * self.derr1 + self.derr2))
        self.u = self.u + Pincr + Iincr + Dincr
        # Now apply constraints on actuator
        change = self.u - self.a
        if change > self.Imax:
            change = self.Imax
        if change < -self.Imax:
            change = -self.Imax
        self.a = self.a + change
        if self.a > self.Amax:
            self.a = self.Amax
        if self.a < self.Amin:
            self.a = self.Amin
        # Update the state of the pid variables
        self.Dincr = Dincr
        self.derr2 = self.derr1
        self.derr1 = derr
        self.perr = perr


class Laser1TempControl(TempControl):
    r = prop(interface.LASER1_TEMP_CNTRL_SETPOINT_REGISTER)
    b = prop(interface.LASER1_TEMP_CNTRL_B_REGISTER)
    c = prop(interface.LASER1_TEMP_CNTRL_C_REGISTER)
    h = prop(interface.LASER1_TEMP_CNTRL_H_REGISTER)
    K = prop(interface.LASER1_TEMP_CNTRL_K_REGISTER)
    Ti = prop(interface.LASER1_TEMP_CNTRL_TI_REGISTER)
    Td = prop(interface.LASER1_TEMP_CNTRL_TD_REGISTER)
    N = prop(interface.LASER1_TEMP_CNTRL_N_REGISTER)
    S = prop(interface.LASER1_TEMP_CNTRL_S_REGISTER)
    Imax = prop(interface.LASER1_TEMP_CNTRL_IMAX_REGISTER)
    Amin = prop(interface.LASER1_TEMP_CNTRL_AMIN_REGISTER)
    Amax = prop(interface.LASER1_TEMP_CNTRL_AMAX_REGISTER)
    ffwd = prop(interface.LASER1_TEMP_CNTRL_FFWD_REGISTER)
    userSetpoint = prop(interface.LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER)
    state = prop(interface.LASER1_TEMP_CNTRL_STATE_REGISTER)
    tol = prop(interface.LASER1_TEMP_CNTRL_TOLERANCE_REGISTER)
    swpMin = prop(interface.LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER)
    swpMax = prop(interface.LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER)
    swpInc = prop(interface.LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER)
    prbsAmp = prop(interface.LASER1_TEC_PRBS_AMPLITUDE_REGISTER)
    prbsMean = prop(interface.LASER1_TEC_PRBS_MEAN_REGISTER)
    prbsGen = prop(interface.LASER1_TEC_PRBS_GENPOLY_REGISTER)
    temp = prop(interface.LASER1_TEMPERATURE_REGISTER)
    dasTemp = prop(interface.DAS_TEMPERATURE_REGISTER)
    tec = prop(interface.LASER1_TEC_REGISTER)
    manualTec = prop(interface.LASER1_MANUAL_TEC_REGISTER)
    extMax = None
    extTemp = None

    def __init__(self, *args, **kwargs):
        super(Laser1TempControl, self).__init__(*args, **kwargs)
        self.activeBit = interface.DAS_STATUS_Laser1TempCntrlActiveBit
        self.lockBit = interface.DAS_STATUS_Laser1TempCntrlLockedBit
        self.resetDasStatusBit(self.lockBit)


class Laser2TempControl(TempControl):
    r = prop(interface.LASER2_TEMP_CNTRL_SETPOINT_REGISTER)
    b = prop(interface.LASER2_TEMP_CNTRL_B_REGISTER)
    c = prop(interface.LASER2_TEMP_CNTRL_C_REGISTER)
    h = prop(interface.LASER2_TEMP_CNTRL_H_REGISTER)
    K = prop(interface.LASER2_TEMP_CNTRL_K_REGISTER)
    Ti = prop(interface.LASER2_TEMP_CNTRL_TI_REGISTER)
    Td = prop(interface.LASER2_TEMP_CNTRL_TD_REGISTER)
    N = prop(interface.LASER2_TEMP_CNTRL_N_REGISTER)
    S = prop(interface.LASER2_TEMP_CNTRL_S_REGISTER)
    Imax = prop(interface.LASER2_TEMP_CNTRL_IMAX_REGISTER)
    Amin = prop(interface.LASER2_TEMP_CNTRL_AMIN_REGISTER)
    Amax = prop(interface.LASER2_TEMP_CNTRL_AMAX_REGISTER)
    ffwd = prop(interface.LASER2_TEMP_CNTRL_FFWD_REGISTER)
    userSetpoint = prop(interface.LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER)
    state = prop(interface.LASER2_TEMP_CNTRL_STATE_REGISTER)
    tol = prop(interface.LASER2_TEMP_CNTRL_TOLERANCE_REGISTER)
    swpMin = prop(interface.LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER)
    swpMax = prop(interface.LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER)
    swpInc = prop(interface.LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER)
    prbsAmp = prop(interface.LASER2_TEC_PRBS_AMPLITUDE_REGISTER)
    prbsMean = prop(interface.LASER2_TEC_PRBS_MEAN_REGISTER)
    prbsGen = prop(interface.LASER2_TEC_PRBS_GENPOLY_REGISTER)
    temp = prop(interface.LASER2_TEMPERATURE_REGISTER)
    dasTemp = prop(interface.DAS_TEMPERATURE_REGISTER)
    tec = prop(interface.LASER2_TEC_REGISTER)
    manualTec = prop(interface.LASER2_MANUAL_TEC_REGISTER)
    extMax = None
    extTemp = None

    def __init__(self, *args, **kwargs):
        super(Laser2TempControl, self).__init__(*args, **kwargs)
        self.activeBit = interface.DAS_STATUS_Laser2TempCntrlActiveBit
        self.lockBit = interface.DAS_STATUS_Laser2TempCntrlLockedBit
        self.resetDasStatusBit(self.lockBit)


class Laser3TempControl(TempControl):
    r = prop(interface.LASER3_TEMP_CNTRL_SETPOINT_REGISTER)
    b = prop(interface.LASER3_TEMP_CNTRL_B_REGISTER)
    c = prop(interface.LASER3_TEMP_CNTRL_C_REGISTER)
    h = prop(interface.LASER3_TEMP_CNTRL_H_REGISTER)
    K = prop(interface.LASER3_TEMP_CNTRL_K_REGISTER)
    Ti = prop(interface.LASER3_TEMP_CNTRL_TI_REGISTER)
    Td = prop(interface.LASER3_TEMP_CNTRL_TD_REGISTER)
    N = prop(interface.LASER3_TEMP_CNTRL_N_REGISTER)
    S = prop(interface.LASER3_TEMP_CNTRL_S_REGISTER)
    Imax = prop(interface.LASER3_TEMP_CNTRL_IMAX_REGISTER)
    Amin = prop(interface.LASER3_TEMP_CNTRL_AMIN_REGISTER)
    Amax = prop(interface.LASER3_TEMP_CNTRL_AMAX_REGISTER)
    ffwd = prop(interface.LASER3_TEMP_CNTRL_FFWD_REGISTER)
    userSetpoint = prop(interface.LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER)
    state = prop(interface.LASER3_TEMP_CNTRL_STATE_REGISTER)
    tol = prop(interface.LASER3_TEMP_CNTRL_TOLERANCE_REGISTER)
    swpMin = prop(interface.LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER)
    swpMax = prop(interface.LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER)
    swpInc = prop(interface.LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER)
    prbsAmp = prop(interface.LASER3_TEC_PRBS_AMPLITUDE_REGISTER)
    prbsMean = prop(interface.LASER3_TEC_PRBS_MEAN_REGISTER)
    prbsGen = prop(interface.LASER3_TEC_PRBS_GENPOLY_REGISTER)
    temp = prop(interface.LASER3_TEMPERATURE_REGISTER)
    dasTemp = prop(interface.DAS_TEMPERATURE_REGISTER)
    tec = prop(interface.LASER3_TEC_REGISTER)
    manualTec = prop(interface.LASER3_MANUAL_TEC_REGISTER)
    extMax = None
    extTemp = None

    def __init__(self, *args, **kwargs):
        super(Laser3TempControl, self).__init__(*args, **kwargs)
        self.activeBit = interface.DAS_STATUS_Laser3TempCntrlActiveBit
        self.lockBit = interface.DAS_STATUS_Laser3TempCntrlLockedBit
        self.resetDasStatusBit(self.lockBit)


class Laser4TempControl(TempControl):
    r = prop(interface.LASER4_TEMP_CNTRL_SETPOINT_REGISTER)
    b = prop(interface.LASER4_TEMP_CNTRL_B_REGISTER)
    c = prop(interface.LASER4_TEMP_CNTRL_C_REGISTER)
    h = prop(interface.LASER4_TEMP_CNTRL_H_REGISTER)
    K = prop(interface.LASER4_TEMP_CNTRL_K_REGISTER)
    Ti = prop(interface.LASER4_TEMP_CNTRL_TI_REGISTER)
    Td = prop(interface.LASER4_TEMP_CNTRL_TD_REGISTER)
    N = prop(interface.LASER4_TEMP_CNTRL_N_REGISTER)
    S = prop(interface.LASER4_TEMP_CNTRL_S_REGISTER)
    Imax = prop(interface.LASER4_TEMP_CNTRL_IMAX_REGISTER)
    Amin = prop(interface.LASER4_TEMP_CNTRL_AMIN_REGISTER)
    Amax = prop(interface.LASER4_TEMP_CNTRL_AMAX_REGISTER)
    ffwd = prop(interface.LASER4_TEMP_CNTRL_FFWD_REGISTER)
    userSetpoint = prop(interface.LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER)
    state = prop(interface.LASER4_TEMP_CNTRL_STATE_REGISTER)
    tol = prop(interface.LASER4_TEMP_CNTRL_TOLERANCE_REGISTER)
    swpMin = prop(interface.LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER)
    swpMax = prop(interface.LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER)
    swpInc = prop(interface.LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER)
    prbsAmp = prop(interface.LASER4_TEC_PRBS_AMPLITUDE_REGISTER)
    prbsMean = prop(interface.LASER4_TEC_PRBS_MEAN_REGISTER)
    prbsGen = prop(interface.LASER4_TEC_PRBS_GENPOLY_REGISTER)
    temp = prop(interface.LASER4_TEMPERATURE_REGISTER)
    dasTemp = prop(interface.DAS_TEMPERATURE_REGISTER)
    tec = prop(interface.LASER4_TEC_REGISTER)
    manualTec = prop(interface.LASER4_MANUAL_TEC_REGISTER)
    extMax = None
    extTemp = None

    def __init__(self, *args, **kwargs):
        super(Laser4TempControl, self).__init__(*args, **kwargs)
        self.activeBit = interface.DAS_STATUS_Laser4TempCntrlActiveBit
        self.lockBit = interface.DAS_STATUS_Laser4TempCntrlLockedBit
        self.resetDasStatusBit(self.lockBit)
