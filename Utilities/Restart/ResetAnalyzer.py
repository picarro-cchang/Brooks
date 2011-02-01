#!/usr/bin/python
#
"""
File Name: ResetAnalyzer.py
Purpose: First step for cycling power to reset analyzer

File History:
    24-Jan-2011  sze  Initial version.

Copyright (c) 2011 Picarro, Inc. All rights reserved
"""
import sys
from os import system, makedirs
from os.path import abspath, exists, join, split, dirname
from _winreg import ConnectRegistry, SetValueEx, CloseKey, OpenKey
from _winreg import KEY_WRITE, REG_SZ, HKEY_LOCAL_MACHINE
from shutil import move
from glob import glob
from Host.Common.CMOS import CMOS

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
    
def moveWildToDir(src,dest):
    srcFiles = glob(src)
    for f in srcFiles:
        move(abspath(f),join(dest,split(f)[1]))
    
if __name__ == "__main__":
    src  = r"C:\Documents and Settings\picarro\Start Menu\Programs\Startup"
    dest = r"C:\Picarro\G2000\Log\DisabledStartup"
    cmos = CMOS()
    if cmos.getBiosName() != 'Phoenix - AwardBIOS v6.00PG':
        raise ValueError('Unrecognized BIOS, cannot continue')
    if not exists(dest): makedirs(dest)
    moveWildToDir(src + "\\*", dest)
    
    year,month,day,hour,min,sec = cmos.getRTC()
    # Advance by 5 min
    min += 5
    if min>=60:
        min -= 60
        hour += 1
        if hour >= 24:
            hour -= 24
    cmos.setAlarmDay(0)
    cmos.setAlarmHour(hour)
    cmos.setAlarmMin(min)
    cmos.setAlarmSec(sec)
    cmos.setAlarmEnable(True)
    print "Restarting at %2d:%02d:%02d" % (hour,min,sec)
    aReg = ConnectRegistry(None,HKEY_LOCAL_MACHINE)
    aKey = OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce", 0, KEY_WRITE)
    try:   
        exePath = join(dirname(AppPath), "RtcAlarmOff.exe")
        SetValueEx(aKey,"MyNewKey",0, REG_SZ, exePath) 
    except EnvironmentError:                                          
        print "Encountered problems writing into the Registry..."
    CloseKey(aKey)
    CloseKey(aReg)
    system('shutdown -r -t 5 -c "Picarro analyzer reset (phase 1 of 3)"')
    