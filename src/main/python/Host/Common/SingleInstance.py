#!/usr/bin/python
#
# File Name: SingleInstance.py
# Purpose: Cavity Ringdown Instrument Driver for Silverstone DAS
#
# Notes:
# Uses a Mutex to limit application to a single instance
#
# File History:
# 06-10-17 sze   Created file (modified from Python Cookbook)
# 08-03-12 sze   Added linux support

import sys

if sys.platform == "win32":
    from win32event import CreateMutex
    from win32api import GetLastError
    from winerror import ERROR_ALREADY_EXISTS

    class SingleInstance:
        """ Limits application to single instance """

        def __init__(self,name):
            self.mutexname = name
            self.mutex = CreateMutex(None, False, self.mutexname)
            self.lasterror = GetLastError()

        def alreadyrunning(self):
            return (self.lasterror == ERROR_ALREADY_EXISTS)

elif sys.platform == "linux2":
    import commands
    import os
    class SingleInstance:
        """ Limits application to single instance """
        # The recommended place to put pid files is /run.  This location is
        # preferred because early in the boot process this directory is cleared
        # out so we don't have stale pid files hanging about after a power
        # failure.
        #
        # /run is owned by root. User level pid files go into /run/user/<uid>.
        # pid files should have the .pid extension.  Add it if it's not in the
        # name.
        #
        def __init__(self,name):
            if "pid" not in name:
                name = name + ".pid"
            pidFilePath = "/run/user/" + str(os.getuid()) + "/"
            self.name = pidFilePath + name
            if os.path.exists(self.name):
                pid = open(self.name,"r").read().strip()
                pidRunning = commands.getoutput('ls /proc | grep %s' % pid)
                if pidRunning:
                    self.lasterror = True
                else:
                    self.lasterror = False
            else:
                self.lasterror = False
            if not self.lasterror:
                fp = open(self.name,'w')
                fp.write(str(os.getpid()))
                fp.close()

        def alreadyrunning(self):
            return self.lasterror

        def __del__(self):
            if not self.lasterror:
                if os.path.exists(self.name):
                    os.unlink(self.name)                

if __name__ == "__main__":
    myapp = SingleInstance("Example")
    if myapp.alreadyrunning():
        raise RuntimeError("Example is already running")
    else:
        print "Example running, press <Enter> to terminate"
        raw_input();
