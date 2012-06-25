#!/usr/bin/python
#
"""
File Name: CMOS.py
Purpose: Routines to access the CMOS RAM in a PC

File History:
    24-Jan-2011  sze  Initial version.

Copyright (c) 2011 Picarro, Inc. All rights reserved
"""
import time
from os import popen
from ctypes import c_ushort
from ctypes import windll

# Load the DLL here
class InpOut32(object):
    def __init__(self):
        DLL_Path = ["InpOut32.dll",r"C:\Picarro\G2000\HostExe\InpOut32.dll"]
        for p in DLL_Path:        
            try:
                self.ioDLL = windll.LoadLibrary(p)
                break
            except:
                continue
        else:
            raise ValueError("Cannot load InpOut32 shared library")

        self.Inp32 = self.ioDLL.Inp32
        self.Inp32.argtypes = [c_ushort]
        self.Inp32.restype  = c_ushort

        self.Out32 = self.ioDLL.Out32
        self.Out32.argtypes = [c_ushort,c_ushort]

class CMOS(object):
    CHKSUM_MSB = 125
    CHKSUM_LSB = 126
    ALARM_ENABLE = 84
    ALARM_ENABLE_MASK = 0x1
    ALARM_DAY = 85
    ALARM_HOUR = 86
    ALARM_MIN = 87
    ALARM_SEC = 88
    
    def __init__(self):
        self.ioDll = InpOut32()

    def saveToFile(self,fname=None):
        self.orig = self.dumpCMOS()
        if fname is None:
            fname = time.strftime("CMOS_%Y%m%d_%H%M%S")
        op = file(fname,"w")
        for i,d in enumerate(self.orig):
            msg = "%3d : %03d = 0x%02x" % (i,d,d)
            print>>op, msg
        op.close()
        
    def read(self,addr):
        try:
            self.ioDll.Out32(0x70,addr)
            return self.ioDll.Inp32(0x71)
        finally:
            time.sleep(0.001)

    def write(self,addr,value):
        try:
            self.ioDll.Out32(0x70,addr)
            self.ioDll.Out32(0x71,value)
        finally:
            time.sleep(0.001)
    
    def dumpCMOS(self):
        contents = []
        for i in range(128):
            contents.append(self.read(i))
            time.sleep(0.001)
        return contents

    def getRTC(self):
        year = int("%02x" % self.read(9))
        month = int("%02x" % self.read(8))
        day = int("%02x" % self.read(7))
        hour  = int("%02x" % self.read(4))
        min = int("%02x" % self.read(2))
        sec = int("%02x" % self.read(0))
        return year,month,day,hour,min,sec
    
    def getChecksum(self):
        return 256*self.read(self.CHKSUM_MSB) + self.read(self.CHKSUM_LSB)

    def setChecksum(self,chksum):
        self.write(self.CHKSUM_MSB,chksum>>8)
        self.write(self.CHKSUM_LSB,chksum&0xFF)

    def getAlarmDay(self):
        return self.read(self.ALARM_DAY)

    def getAlarmHour(self):
        return self.read(self.ALARM_HOUR)

    def getAlarmMin(self):
        return self.read(self.ALARM_MIN)

    def getAlarmSec(self):
        return self.read(self.ALARM_SEC)

    def setAlarmDay(self,new):
        if new<0 or new>31:
            raise ValueError("Bad day: %d" % new)
        old, oldChksum = self.read(self.ALARM_DAY), self.getChecksum()
        if new != old:
            self.write(self.ALARM_DAY,new)
            self.setChecksum(oldChksum+new-old)

    def setAlarmHour(self,new):
        if new<0 or new>23:
            raise ValueError("Bad hour: %d" % new)
        old, oldChksum = self.read(self.ALARM_HOUR), self.getChecksum()
        if new != old:
            self.write(self.ALARM_HOUR,new)
            self.setChecksum(oldChksum+new-old)

    def setAlarmMin(self,new):
        if new<0 or new>59:
            raise ValueError("Bad minute: %d" % new)
        old, oldChksum = self.read(self.ALARM_MIN), self.getChecksum()
        if new != old:
            self.write(self.ALARM_MIN,new)
            self.setChecksum(oldChksum+new-old)

    def setAlarmSec(self,new):
        if new<0 or new>59:
            raise ValueError("Bad second: %d" % new)
        old, oldChksum = self.read(self.ALARM_SEC), self.getChecksum()
        if new != old:
            self.write(self.ALARM_SEC,new)
            self.setChecksum(oldChksum+new-old)
        
    def getAlarmEnable(self):
        return bool(self.read(self.ALARM_ENABLE) & self.ALARM_ENABLE_MASK)

    def setAlarmEnable(self,new):
        if new<0 or new>1:
            raise ValueError("Bad alarm enable: %s" % new)
        old, oldChksum = self.read(self.ALARM_ENABLE), self.getChecksum()
        if new:
            new = old | self.ALARM_ENABLE_MASK
        else:
            new = old & ~(self.ALARM_ENABLE_MASK)
        if new != old:
            self.write(self.ALARM_ENABLE,new)
            self.setChecksum(oldChksum+new-old)

    def getBiosName(self):
        biosSettings = popen('wmic bios get /format:list','r').read()
        for x in biosSettings.split('\r\n'):
            try:
                key,value = x.split("=")
                if key == 'Name': return value
            except:
                pass
