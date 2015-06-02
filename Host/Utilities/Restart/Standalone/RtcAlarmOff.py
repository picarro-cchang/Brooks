#!/usr/bin/python
#
"""
File Name: RtcAlarmOff.py
Purpose: Turn off RTC alarm in BIOS which restarts computer at
    specified time

File History:
    24-Jan-2011  sze  Initial version.

Copyright (c) 2011 Picarro, Inc. All rights reserved
"""
from os import system
from _winreg import ConnectRegistry, SetValueEx, CloseKey, OpenKey
from _winreg import KEY_WRITE, REG_SZ, HKEY_LOCAL_MACHINE
from Host.Utilities.Restart.Standalone.CMOS import CMOS

if __name__ == "__main__":
    cmos = CMOS()
    cmos.setAlarmEnable(False)
    aReg = ConnectRegistry(None,HKEY_LOCAL_MACHINE)
    aKey = OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce", 0, KEY_WRITE)
    try:
        SetValueEx(aKey,"MyNewKey",0, REG_SZ, r"c:\picarro\G2000\HostExe\restart3.bat")
    except EnvironmentError:
        print "Encountered problems writing into the Registry..."
    CloseKey(aKey)
    CloseKey(aReg)
    system('shutdown -s -t 5 -c "Picarro analyzer reset (phase 2 of 3)"')