#!/usr/bin/python
#
"""
File Name: DasSimulator.py
Purpose: Simulation of analyzer for diagnostic purposes

File History:
    19-Sep-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""
from collections import deque
import ctypes
import heapq
import math
import types

from Host.autogen import interface
from Host.Common import timestamp
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.DriverSimulator.ActionHandler import ActionHandler

APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)


def _value(valueOrName):
    """Convert valueOrName into an value, raising an exception if the name is not found"""
    if isinstance(valueOrName, types.StringType):
        try:
            valueOrName = getattr(interface, valueOrName)
        except AttributeError:
            raise AttributeError("Value identifier not recognized %r" % valueOrName)
    return valueOrName


class DasSimulator(object):
    class HostToDspSender(object):
        def __init__(self, sim):
            self.sim = sim

        def doOperation(self, operation, when=None):
            if when is None:
                when = self.sim.getDasTimestamp()
            return self.sim.actionHandler.doAction(operation.opcode, operation.operandList, operation.env, when)

        def rdEnv(self, addressOrName, envClass):
            address = _value(addressOrName)
            return self.sim.envStore[address]

        def rdRegFloat(self, regIndexOrName):
            return self.sim.rdDasReg(regIndexOrName)

        def rdRegUint(self, regIndexOrName):
            return self.sim.rdDasReg(regIndexOrName)

        def rdFPGA(self, base, reg):
            return self.sim.rdFPGA(base, reg)

        def wrEnv(self, addressOrName, env):
            address = _value(addressOrName)
            self.sim.envStore[address] = env

        def wrFPGA(self, base, reg, value, convert=True):
            return self.sim.wrFPGA(base, reg, value, convert)

        def wrRegFloat(self, regIndexOrName, value, convert=True):
            return self.sim.wrDasReg(regIndexOrName, value, convert)

        def wrRegUint(self, regIndexOrName, value, convert=True):
            return self.sim.wrDasReg(regIndexOrName, value, convert)

    def __init__(self):
        self.das_registers = interface.INTERFACE_NUMBER_OF_REGISTERS * [0]
        self.fpga_registers = 512*[0]
        self.dsp_message_queue = deque(maxlen=interface.NUM_MESSAGES)
        self.sensor_queue = deque(maxlen=interface.NUM_SENSOR_ENTRIES)
        self.ringdown_queue = deque(maxlen=interface.NUM_RINGDOWN_ENTRIES)
        # shared_mem is an array of 32-bit unsigned integers
        self.shared_mem = interface.SHAREDMEM_SIZE * [0]
        self.hostToDspSender = DasSimulator.HostToDspSender(self)
        self.actionHandler = ActionHandler(self)
        # The following attributes are associated with the scheduler
        self.operationGroups = []
        self.scheduler = None
        # The following stores environment structures
        self.envStore = {}
        # The following will contain the temperature controller objects
        self.laser1TempControl = None
        self.laser2TempControl = None
        self.laser3TempControl = None
        self.laser4TempControl = None
        #
        self.ts_offset = 0  # Timestamp offset in ms
        self.wrDasReg("VERIFY_INIT_REGISTER", 0x19680511)

    def changeBitsFPGA(self, regNum, lsb, width, value):
        current = self.fpga_registers[regNum]
        mask = ((1 << width) - 1) << lsb
        current = (current & ~mask) | ((value << lsb) & mask)
        self.fpga_registers[regNum] = current

    def changeInMaskFPGA(self, regNum, mask, value):
        current = self.fpga_registers[regNum]
        self.fpga_registers[regNum] = (current & ~mask) | (value & mask)

    def getDasTimestamp(self):
        # Get ms DAS timestamp
        return self.ts_offset + timestamp.getTimestamp()

    def getMessage(self):
        if len(self.dsp_message_queue) > 0:
            ts, logLevel, message = self.dsp_message_queue.popleft()
            return ts, message
        else:
            return None

    def getSensorData(self):
        if len(self.sensor_queue) > 0:
            data = interface.SensorEntryType()
            data.timestamp, data.streamNum, data.value = self.sensor_queue.popleft() 
            return data
        else:
            return None

    def initScheduler(self):
        now = self.getDasTimestamp()
        self.scheduler = Scheduler(self.operationGroups, now, self.hostToDspSender.doOperation)

    def rdDasReg(self, regIndexOrName):
        index = self._reg_index(regIndexOrName)
        if 0 <= index < len(self.das_registers):
            return self.das_registers[index]
        else:
            raise IndexError('Register index not in range')

    def rdFPGA(self, baseIndexOrName, regIndexOrName):
        base = self._value(baseIndexOrName)
        reg = self._value(regIndexOrName)
        return self.fpga_registers[base + reg]

    def readBitsFPGA(self, regNum, lsb, width):
        current = self.fpga_registers[regNum]
        mask = ((1 << width) - 1) << lsb
        return (current & mask) >> lsb

    def setDasTimestamp(self, ts):
        # Set ms DAS timestamp
        self.ts_offset = ts - timestamp.getTimestamp()

    def uploadSchedule(self, groups):
        self.operationGroups = groups

    def wrDasReg(self, regIndexOrName, value, convert=True):
        if convert:
            value = self._value(value)
        index = self._reg_index(regIndexOrName)
        if 0 <= index < len(self.das_registers):
            ri = interface.registerInfo[index]
            if ri.type in [ctypes.c_uint, ctypes.c_int, ctypes.c_long]:
                self.das_registers[index] = int(value)
            elif ri.type == ctypes.c_float:
                self.das_registers[index] = float(value)
            else:
                raise ValueError("Type %s of register %s is not known" % (ri.type, regIndexOrName,))
        else:
            raise IndexError('Register index not in range')

    def wrFPGA(self, baseIndexOrName, regIndexOrName, value, convert=True):
        base = self._value(baseIndexOrName)
        reg = self._value(regIndexOrName)
        if convert:
            value = self._value(value)
        self.fpga_registers[base + reg] = int(value)

    def _reg_index(self, indexOrName):
        """Convert a name or index into an integer index, raising an exception if the name is not found"""
        if isinstance(indexOrName, types.IntType):
            return indexOrName
        else:
            try:
                return interface.registerByName[indexOrName.strip().upper()]
            except KeyError:
                raise ValueError("Unknown register name %s" % (indexOrName,))

    def _value(self, valueOrName):
        """Convert valueOrName into an value, raising an exception if the name is not found"""
        if isinstance(valueOrName, types.StringType):
            try:
                valueOrName = getattr(interface, valueOrName)
            except AttributeError:
                raise AttributeError("Value identifier not recognized %s" % valueOrName)
        return valueOrName


class Scheduler(object):
    def __init__(self, operationGroups, ts, doOperation):
        # Within the constructor a runqueue is initialized
        #  with groups of operations which have to be performed
        #  at times starting with ts (ms). Groups are scheduled
        #  at times which are integer multiples of their periods.
        #  They are further ordered by group
        # Note that the periods are specified in units of 100ms.
        self.operationGroups = operationGroups
        self.startTimestamp = ts
        self.doOperation = doOperation
        # The run queue is a minqueue with entries
        # (when, priority, what)
        self.runqueue = [] 
        self.initRunqueue()

    def initRunqueue(self):
        for group in self.operationGroups:
            period_ms = 100*group.period
            when = int(period_ms * math.ceil(float(self.startTimestamp) / period_ms))
            item = (when, group.priority, group)
            heapq.heappush(self.runqueue, item)
        print "Initial runqueue"
        for when, priority, group in sorted(self.runqueue):
            print when, priority, group

    def execUntil(self, ts):
        while self.runqueue:

            # Get the next action to perform
            when, priority, group = self.runqueue[0]
            if when > ts:
                return
            heapq.heappop(self.runqueue)
            # Enqueue next time this is to be performed
            period_ms = 100*group.period
            item = (when + period_ms, group.priority, group)
            heapq.heappush(self.runqueue, item)
            # Carry out the actions in the list
            for operation in group.operationList:
                self.doOperation(operation, when)


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
