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
            #interface.ACTION_TEMP_CNTRL_LASER1_INIT: self.tempCntrlLaser1Init,
            #interface.ACTION_TEMP_CNTRL_LASER1_STEP: self.tempCntrlLaser1Step,
        }

    def doAction(self, command, params, env, when):
        if command in self.action:
            return self.action[command](params, env, when, command)
        else:
            print "Unimplemented action: %d" % command 

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

    def unknownAction(self, params, env, when, command):
        self.sim.dsp_message_queue.append((when, interface.LOG_LEVEL_CRITICAL, "Unknown action code %d" % command))
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

        def rdRegFloat(self, regIndexOrName):
            return self.sim.rdDasReg(regIndexOrName)

        def rdRegUint(self, regIndexOrName):
            return self.sim.rdDasReg(regIndexOrName)

        def rdFPGA(self, base, reg):
            return self.sim.rdFPGA(base, reg)

        def wrEnv(self, *args, **kwargs):
            print "wrEnv called: %s, %s" % (args, kwargs)

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

        self.ts_offset = 0  # Timestamp offset in ms
        self.wrDasReg("VERIFY_INIT_REGISTER", 0x19680511)

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
        #  They are further ordered by group priority.
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

