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
from Host.DriverSimulator.Simulators import InjectionSimulator, SpectrumSimulator, TunerSimulator
from Host.DriverSimulator.SpectrumControl import SpectrumControl

APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)


def _value(valueOrName):
    """Convert valueOrName into an value, raising an exception if the name is not found"""
    if isinstance(valueOrName, types.UnicodeType):
        valueOrName = str(valueOrName)
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

    def __init__(self, driver):
        self.driver = driver
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
        # and the laser current controllers
        self.laser1CurrentControl = None
        self.laser2CurrentControl = None
        self.laser3CurrentControl = None
        self.laser4CurrentControl = None
        # and the spectrum controller
        self.spectrumControl = SpectrumControl(self)
        #
        self.laser1Simulator = None
        self.laser2Simulator = None
        self.laser3Simulator = None
        self.laser4Simulator = None
        #
        self.injectionSimulator = InjectionSimulator(self)
        self.spectrumSimulator = SpectrumSimulator(self)
        #
        self.tunerSimulator = TunerSimulator(self)
        # self.pztSimulator = PztSimulator(self)
        # self.laserLockerSimulator = LaserLockerSimulator(self)
        # self.cavitySimulator = CavitySimulator(self)
        #
        self.simulators = set()
        #
        self.initDasRegisters()
        self.ts_offset = 0  # Timestamp offset in ms
        self.wrDasReg("VERIFY_INIT_REGISTER", 0x19680511)

    def addSimulator(self, simulator):
        self.simulators.add(simulator)

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

    def getRingdownData(self):
        if len(self.ringdown_queue) > 0:
            return self.ringdown_queue.popleft() 
        else:
            return None

    def initDasRegisters(self):
        for ri in interface.registerInfo:
            if ri.initial is not None:
                self.wrDasReg(ri.name, ri.initial)

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
        if isinstance(indexOrName, types.UnicodeType):
            indexOrName = str(indexOrName)
        if isinstance(indexOrName, types.IntType):
            return indexOrName
        else:
            try:
                return interface.registerByName[indexOrName.strip().upper()]
            except KeyError:
                raise ValueError("Unknown register name %s" % (indexOrName,))

    def _value(self, valueOrName):
        """Convert valueOrName into an value, raising an exception if the name is not found"""
        if isinstance(valueOrName, types.UnicodeType):
            valueOrName = str(valueOrName)
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
