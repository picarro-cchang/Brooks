#!/usr/bin/python
#
"""
File Name: DasSimulator.py
Purpose: Simulation of analyzer for diagnostic purposes

File History:
    19-Sep-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""
import ctypes
import types

from Host.autogen import interface


class ActionHandler(object):
    def __init__(self, sim):
        self.sim = sim
        self.action = {
            interface.ACTION_WRITE_BLOCK: self.writeBlock,
        }

    def doAction(self, command, params, env):
        return self.action[command](params, env)

    def writeBlock(self, params, env):
        offset = params[0]
        for i in range(len(params)-1):
            self.sim.sharedMem[offset + i] = params[i + 1]
        return interface.STATUS_OK


class DasSimulator(object):
    class HostToDspSender(object):
        def __init__(self, sim):
            self.sim = sim

        def doOperation(self, operation):
            return self.sim.actionHandler.doAction(operation.opcode, operation.operandList, operation.env)

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
        self.shared_mem = interface.SHAREDMEM_SIZE * [0]
        self.hostToDspSender = DasSimulator.HostToDspSender(self)
        self.actionHandler = ActionHandler(self)
        self.wrDasReg("VERIFY_INIT_REGISTER", 0x19680511)

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

