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

class ActionHandler(object):
    def __init__(self, sim):
        self.sim = sim
        self.action = {
            interface.ACTION_WRITE_BLOCK: self.writeBlock,
            interface.ACTION_SET_TIMESTAMP: self.setTimestamp,
            interface.ACTION_GET_TIMESTAMP: self.getTimestamp,
            interface.ACTION_INIT_RUNQUEUE: self.initRunqueue,
            interface.ACTION_TEST_SCHEDULER: self.testScheduler,
            interface.ACTION_STREAM_REGISTER_ASFLOAT: self.streamRegisterAsFloat,
            interface.ACTION_STREAM_FPGA_REGISTER_ASFLOAT: self.streamFpgaRegisterAsFloat,
            interface.ACTION_RESISTANCE_TO_TEMPERATURE: self.resistanceToTemperature,
            interface.ACTION_TEMP_CNTRL_SET_COMMAND: self.unknownAction,
            interface.ACTION_APPLY_PID_STEP: self.unknownAction,
            interface.ACTION_TEMP_CNTRL_LASER1_INIT: self.tempCntrlLaser1Init,
            interface.ACTION_TEMP_CNTRL_LASER1_STEP: self.tempCntrlLaser1Step,
            interface.ACTION_TEMP_CNTRL_LASER2_INIT: self.tempCntrlLaser2Init,
            interface.ACTION_TEMP_CNTRL_LASER2_STEP: self.tempCntrlLaser2Step,
            interface.ACTION_TEMP_CNTRL_LASER3_INIT: self.tempCntrlLaser3Init,
            interface.ACTION_TEMP_CNTRL_LASER3_STEP: self.tempCntrlLaser3Step,
            interface.ACTION_TEMP_CNTRL_LASER4_INIT: self.tempCntrlLaser4Init,
            interface.ACTION_TEMP_CNTRL_LASER4_STEP: self.tempCntrlLaser4Step,
            interface.ACTION_FILTER: self.filter,
            interface.ACTION_FLOAT_REGISTER_TO_FPGA: self.floatRegisterToFpga,
            interface.ACTION_FPGA_TO_FLOAT_REGISTER: self.fpgaToFloatRegister,
            interface.ACTION_INT_TO_FPGA: self.intToFpga,
            interface.ACTION_CURRENT_CNTRL_LASER1_INIT: self.currentCntrlLaser1Init,
            interface.ACTION_CURRENT_CNTRL_LASER1_STEP: self.currentCntrlLaser1Step,
            interface.ACTION_SIMULATE_LASER_CURRENT_READING: self.simulateLaserCurrentReading,
            interface.ACTION_UPDATE_WLMSIM_LASER_TEMP: self.updateWlmsimLaserTemp,
        }

    def currentCntrlLaser1Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser1CurrentControl = Laser1CurrentControl(self.sim.das_registers, self.sim)
        return interface.STATUS_OK

    def currentCntrlLaser1Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser1CurrentControl.step()

    def doAction(self, command, params, env, when):
        if command in self.action:
            return self.action[command](params, env, when, command)
        else:
            print "Unimplemented action: %d" % command

    def filter(self, params, env, when, command):
        if 2 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        MAX_ORDER = 8
        x = self.sim.rdDasReg(params[0])
        filtEnv = self.sim.envStore[env]
        div = filtEnv.den[0]
        if div == 0:
            y = 0
            return interface.ERROR_BAD_FILTER_COEFF
        y = filtEnv.state[0] + (filtEnv.num[0] / div) * (x + filtEnv.offset)
        for i in range(MAX_ORDER - 1):
            filtEnv.state[i] = filtEnv.state[i+1] + (filtEnv.num[i+1] * (x + filtEnv.offset) - filtEnv.den[i+1]*y) / div
        filtEnv.state[MAX_ORDER - 1] = (filtEnv.num[MAX_ORDER] * (x + filtEnv.offset)  - filtEnv.den[MAX_ORDER]*y) / div
        self.sim.wrDasReg(params[1], y)
        return interface.STATUS_OK

    def floatRegisterToFpga(self, params, env, when, command):
        # Copy contents of a floating point register to an FPGA register,
        #  treating value as an unsigned int. The FPGA register is the sum
        #  of two arguments so that we can pass a block base and an offset within
        #  the block.
        if 3 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.wrFPGA(params[1], params[2], int(self.sim.rdDasReg(params[0])))
        return interface.STATUS_OK

    def fpgaToFloatRegister(self, params, env, when, command):
        # Copy contents of an FPGA register to a floating point register,
        #  treating value as an unsigned short. The FPGA register is the sum
        #  of two arguments so that we can pass a block base and an offset within
        #  the block.
        if 3 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.wrDasReg(params[2], self.sim.rdFPGA(params[0], params[1]))
        return interface.STATUS_OK

    def getTimestamp(self, params, env, when, command):
        # Timestamp is an integer number of ms
        if 2 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        ts = self.sim.getDasTimestamp()
        self.sim.wrDasReg(params[0], ts & 0xFFFFFFFF)
        self.sim.wrDasReg(params[1], ts >> 32)
        return interface.STATUS_OK

    def initRunqueue(self, params, env, when, command):
        if 1 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        if params[0] != len(self.sim.operationGroups):
            Log("Incorrect number of operation groups in initRunqueue")
        self.sim.initScheduler()
        return interface.STATUS_OK

    def intToFpga(self, params, env, when, command):
        # Copy integer (passed as first parameter) to the specified FPGA register.
        #  The FPGA register is the sum of two arguments so that we can pass a
        #  block base and an offset within the block.
        if 3 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.wrFPGA(params[1], params[2], params[0])
        return interface.STATUS_OK

    def resistanceToTemperature(self, params, env, when, command):
        if 5 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        resistance = self.sim.rdDasReg(params[0])
        constA = self.sim.rdDasReg(params[1])
        constB = self.sim.rdDasReg(params[2])
        constC = self.sim.rdDasReg(params[3])
        if 1.0 < resistance < 5.0e6:
            lnR = math.log(resistance)
            result = 1/(constA + (constB * lnR) + (constC * lnR ** 3)) - 273.15
            self.sim.wrDasReg(params[4], result)
        else:
            self.sim.dsp_message_queue.append((when, interface.LOG_LEVEL_CRITICAL, "Bad resistance in resistanceToTemperature"))
        return interface.STATUS_OK

    def setTimestamp(self, params, env, when, command):
        # Timestamp is an integer number of ms 
        if 2 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        ts = params[0] + (params[1] << 32)
        self.sim.setDasTimestamp(ts)
        return interface.STATUS_OK

    def simulateLaserCurrentReading(self, params, env, when, command):
        # For the specified laser number (1-origin), place the simulated laser current reading (obtained
        #  by combining coarse and fine laser contributions) into the specified register.  The scaling is
        #  360nA/fine_current unit, and 10 fine_current units = 1 coarse_current unit.
        if 2 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        dac = 0
        if params[0] == 1:
            dac = 10*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER1_COARSE_CURRENT) + 2*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER1_FINE_CURRENT)
        elif params[0] == 2:
            dac = 10*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER2_COARSE_CURRENT) + 2*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER2_FINE_CURRENT)
        elif params[0] == 3:
            dac = 10*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER3_COARSE_CURRENT) + 2*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER3_FINE_CURRENT)
        elif params[0] == 4:
            dac = 10*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER4_COARSE_CURRENT) + 2*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER4_FINE_CURRENT)
        current = 0.00036*dac
        self.sim.wrDasReg(params[1], current)
        return interface.STATUS_OK
 
    def streamFpgaRegisterAsFloat(self, params, env, when, command):
        """This action streams the value of an FPGA register. The first parameter
            is the stream number, the second is the location in the FPGA map and
            the third is the register number."""
        if 3 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        streamNum = params[0]
        value = self.sim.rdFPGA(params[1], params[2])
        self.sim.sensor_queue.append((when, streamNum, value))

    def streamRegisterAsFloat(self, params, env, when, command):
        """This action streams the value of a register. The first parameter
            is the stream number and the second is the register number."""
        if 2 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        streamNum = params[0]
        value = self.sim.rdDasReg(params[1])
        self.sim.sensor_queue.append((when, streamNum, value))

    def testScheduler(self, params, env, when, command):
        # Send back parmeters via DSP message queue to test operation
        #  of scheduler
        message = "At %d testScheduler %s" % (when, " ".join(["%d" % param for param in params]))
        self.sim.dsp_message_queue.append((when, interface.LOG_LEVEL_STANDARD, message))
        return interface.STATUS_OK

    def tempCntrlLaser1Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser1TempControl = Laser1TempControl(self.sim.das_registers)
        return interface.STATUS_OK

    def tempCntrlLaser2Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser2TempControl = Laser2TempControl(self.sim.das_registers)
        return interface.STATUS_OK

    def tempCntrlLaser3Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser3TempControl = Laser3TempControl(self.sim.das_registers)
        return interface.STATUS_OK

    def tempCntrlLaser4Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser4TempControl = Laser4TempControl(self.sim.das_registers)
        return interface.STATUS_OK

    def tempCntrlLaser1Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser1TempControl.step()

    def tempCntrlLaser2Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser2TempControl.step()

    def tempCntrlLaser3Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser3TempControl.step()

    def tempCntrlLaser4Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser4TempControl.step()

    def unknownAction(self, params, env, when, command):
        self.sim.dsp_message_queue.append((when, interface.LOG_LEVEL_CRITICAL, "Unknown action code %d" % command))
        return interface.STATUS_OK

    def updateWlmsimLaserTemp(self, params, env, when, command):
        # In the simulator, this action has been hijacked to also compute the
        #  wavelength monitor outputs and the ratios based on the temperature 
        #  and current of the selected laser
        laserNum = self.sim.readBitsFPGA(
            interface.FPGA_INJECT + interface.INJECT_CONTROL,
            interface.INJECT_CONTROL_LASER_SELECT_B, 
            interface.INJECT_CONTROL_LASER_SELECT_W) + 1
        laserTemp = self.sim.rdDasReg("LASER%d_TEMPERATURE_REGISTER" % laserNum)
        laserCurrent = 0.00036 * (10 * self.sim.rdFPGA(
            "FPGA_INJECT", 
            "INJECT_LASER%d_COARSE_CURRENT" % laserNum) + 
            2 * self.sim.rdFPGA(
            "FPGA_INJECT", 
            "INJECT_LASER%d_FINE_CURRENT" % laserNum))
        print "Laser %d, Temp %.3f, Current %.3f" % (laserNum, laserTemp, laserCurrent)
        return interface.STATUS_OK

    def writeBlock(self, params, env, when, command):
        offset = params[0]
        for i in range(len(params)-1):
            self.sim.sharedMem[offset + i] = params[i + 1]
        return interface.STATUS_OK


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
            self.prbsReg = 0x1
        elif self.state == interface.TEMP_CNTRL_ManualState:
            self.setDasStatusBit(self.activeBit)
            self.resetDasStatusBit(self.lockBit)
            if self.manualTec > self.Amax:
                self.manualTec = self.Amax
            if self.manualTec < self.Amin:
                self.manualTec = self.Amin
            self.tec = self.manualTec
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

class LaserSimulator(object):
    # This code simulates the behavior of a laser
    #
    # The default parameters are based on the following model implemented in the FPGA
    # When 5*coarse + fine changes by 65536, the laser frequency changes by 
    #  one FSR of the wavelength monitor or 50GHz (1.66782 wavenumbers)
    # The sensitivity of the laser frequency to current is thus -1.0596 GHz/mA
    #  or -0.035344 wavenumber/mA
    #
    # When 18*laserTemp(in millidegrees) changes by 65536, the laser frequency
    #  changes by 50GHz. The sensitivity of the laser frequency to current is 
    #  thus -13.7329 GHz/degree or -0.45808 wavenumber/degree
    #
    # The nominal frequency of the laser is attained at a laser current of 150mA
    #  and a laser temperature of 25 degC
    def __init__(self, nominal_wn = 6237.0, temp_sens = -0.45808, current_sens = -0.035344):
        self.nominal_wn = nominal_wn
        self.temp_sens = temp_sens
        self.current_sens = current_sens

    def wavenum(self, temp, current):
        return self.nominal_wn + self.temp_sens * (temp - 25.0) + self.current_sens * (current - 150.0)

class LaserDacSimulator(object):
    # The relationship between laser current DACs and laser current in mA is
    #
    # current = 0.00036 * (10*coarse + 2*fine)
    # Thus for coarse = 36000 and fine = 32768, we have a current of 153.193 mA
    #  1mA of current change results from changing the coarse value by 277.78 digU
    #  or the fine value by 1388,89 digU
    def __init__(self, coarse_sens = 0.0036, fine_sens = 0.00072, offset = 0):
        self.coarse_sens = coarse_sens
        self.fine_sens = fine_sens
        self.offset = offset

    def current_from_dac(self, coarse, fine):
        return self.offset + self.coarse_sens * coarse + self.fine_sens * fine

class WlmSimulator(object):
    # This code simulates the behavior of the wavelength monitor. The wavelength monitor
    #  angle is theta and the etalon reflectivity factor is rho.
    # eta1 = rho * I1 * (1-sin(theta)) / (1 - rho*sin(theta)) + eta1_offset
    # ref1 = I1 * (1-rho)/ (1 - rho*sin(theta)) + ref1_offset
    