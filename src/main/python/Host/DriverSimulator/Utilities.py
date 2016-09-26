#!/usr/bin/python
#
"""
File Name: Utilities.py
Purpose: Utility functions for simulators

File History:
    25-Sep-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""
def das_register_getter(index):
    def fget(self):
        return self.das_registers[index]
    return fget


def das_register_setter(index):
    def fset(self, value):
        self.das_registers[index] = value
    return fset


def fpga_register_getter(base, reg, lsb=0, width=16):
    def fget(self):
        current = self.fpga_registers[base + reg]
        if lsb == 0 and width == 16:
            return current
        else:
            mask = ((1 << width) - 1) << lsb
            return (current & mask) >> lsb
    return fget


def fpga_register_setter(base, reg, lsb=0, width=16):
    def fset(self, value):
        if lsb == 0 and width == 16:
            current = value
        else:
            current = self.fpga_registers[base + reg] 
            mask = ((1 << width) - 1) << lsb
            current = (current & ~mask) | ((value << lsb) & mask)
        self.fpga_registers[base + reg] = current
    return fset


def prop_das(index):
    return property(das_register_getter(index), das_register_setter(index))


def prop_fpga(base, reg, lsb=0, width=16):
    return property(
        fpga_register_getter(base, reg, lsb, width),
        fpga_register_setter(base, reg, lsb, width))
