#!/usr/bin/python
#
# File Name: TTLIntrf.py
# Purpose: Provides TTL interface with GC or other devices
#
# Notes: Just copied from Autosampler.py with the serial functions removed. The get and set functions are generalized.
#
# File History:
# 03-04-09 alex  Created file (based on Autosampler.py)

from ctypes import windll, c_int
import time

class TimeoutError(Exception):
    pass

class DriverError(Exception):
    pass

class IbaseDio(object):
    def __init__(self):
        DLL_Path = ["ib_wdt.dll"]
        for p in DLL_Path:        
            try:
                self.dioDLL = windll.LoadLibrary(p)
                break
            except:
                continue
        else:
            raise ValueError("Cannot load iBASE DIO shared library")

        self.installDriver = self.dioDLL.InstallDriver
        self.installDriver.argtypes = []
        self.installDriver.restype  = c_int

        self.removeDriver = self.dioDLL.RemoveDriver
        self.removeDriver.argtypes = []
        self.removeDriver.restype  = c_int

        self.isDioAvailable = self.dioDLL.IsDioAvailable
        self.isDioAvailable.argtypes = [c_int]
        self.isDioAvailable.restype  = c_int

        self.setDioInputMask = self.dioDLL.SetDioInputMask
        self.setDioInputMask.argtypes = [c_int]
        self.setDioInputMask.restype  = c_int

        self.setDioOutputMask = self.dioDLL.SetDioOutputMask
        self.setDioOutputMask.argtypes = [c_int]
        self.setDioOutputMask.restype  = c_int

        self.getDioInput = self.dioDLL.GetDioInput
        self.getDioInput.argtypes = [c_int]
        self.getDioInput.restype  = c_int

        self.setDioOutput = self.dioDLL.SetDioOutput
        self.setDioOutput.argtypes = [c_int]
        self.setDioOutput.restype  = c_int

class TTLIntrf(object):
    def __init__(self, assertSig, deassertSig):
        self.dio = IbaseDio()
        self.assertSig = assertSig
        self.deassertSig = deassertSig
        
    def open(self):
        self.dio.installDriver()
        if not self.dio.isDioAvailable(0):
            self.dio.removeDriver()
            raise DriverError("No DIO driver installed for SBC")            
        self.dio.setDioInputMask(0x0F)
        self.dio.setDioOutputMask(0xF0)
        self.dio.shadow = 0xF0
        self.dio.setDioOutput(self.dio.shadow)

    def close(self):
        # Deassert signals on close
        self.dio.shadow = 0xF0
        self.dio.setDioOutput(self.dio.shadow)
        self.dio.removeDriver()
        
    def initialize(self):
        self.open()
            
    def setControl(self,line,value):
        """Sets the value of control line (1-4) to specified value (0 or 1)"""
        mask = 1<<(3+line)
        self.dio.shadow &= ~mask
        if value: 
            self.dio.shadow |= mask
        self.dio.setDioOutput(self.dio.shadow)

    def assertControl(self, line):
        """Asserts the value of control line (1-4)"""
        self.setControl(line,self.assertSig)
        
    def deassertControl(self, line):
        """Deasserts the value of control line (1-4)"""  
        self.setControl(line,self.deassertSig)
        
    def getControl(self,line):
        """Gets the value of control line (1-4). Returns 1 if asserted."""
        mask = 1<<(3+line)          
        return self.assertSig == (self.dio.shadow & mask)>>(3+line)
        
    def getStatus(self,line):
        """Gets the value of status line (1-4). Returns 1 if asserted."""
        mask = 1<<(line-1)
        return self.assertSig == (self.dio.getDioInput(0) & mask)>>(line-1)