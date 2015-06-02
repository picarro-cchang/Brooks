#!/usr/bin/python
#
"""
File Name: RestoreStartup.py
Purpose: Restore startup folder for analyzer

File History:
    24-Jan-2011  sze  Initial version.

Copyright (c) 2011 Picarro, Inc. All rights reserved
"""

from os import system
from os.path import abspath, join, split
from shutil import move
from glob import glob

def moveWildToDir(src,dest):
    srcFiles = glob(src)
    for f in srcFiles:
        move(abspath(f),join(dest,split(f)[1]))

if __name__ == "__main__":
    dest  = r"C:\Documents and Settings\picarro\Start Menu\Programs\Startup"
    src   = r"C:\Picarro\G2000\Log\DisabledStartup"
    moveWildToDir(src + "\\*", dest)
    system('shutdown -r -t 5 -c "Picarro analyzer reset (phase 3 of 3)"')