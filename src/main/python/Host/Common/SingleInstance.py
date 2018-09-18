#!/usr/bin/python
#
# File Name: SingleInstance.py
# Purpose: Cavity Ringdown Instrument Driver for Silverstone DAS
#
# Notes:
# Uses a pid file to limit application to a single instance

import commands
import os


class SingleInstance:
    """ Limits application to single instance """
    # The recommended place to put pid files is /run.  This location is
    # preferred because early in the boot process this directory is cleared
    # out so we don't have stale pid files hanging about after a power
    # failure.
    #
    # /run is owned by root. User level pid files go into /run/user/<uid>/picarro
    # pid files should have the .pid extension.  Add it if it's not in the
    # name.
    #
    def __init__(self, name):
        if "pid" not in name:
            name = name + ".pid"
        pidFilePath = "/run/user/" + str(os.getuid()) + "/picarro/"
        if not os.path.exists(pidFilePath):
            try:
                os.mkdir(pidFilePath, 0775)
            except OSError:
                print("Cannot create directory: %s" % pidFilePath)
        self.name = pidFilePath + name
        if os.path.exists(self.name):
            with open(self.name, "r") as pidFile:
                pid = pidFile.read().strip()
            pidRunning = commands.getoutput('ls /proc | grep %s' % pid)
            if pidRunning:
                self.lasterror = True
            else:
                self.lasterror = False
        else:
            self.lasterror = False
        if not self.lasterror:
            with open(self.name, "w") as fp:
                fp.write(str(os.getpid()))

    def alreadyrunning(self):
        return self.lasterror

    def __del__(self):
        if not self.lasterror and os.path.exists(self.name):
            try:
                os.remove(self.name)
            except OSError:
                print("Cannot remove: %s" % self.name)


if __name__ == "__main__":
    myapp = SingleInstance("Example")
    if myapp.alreadyrunning():
        raise RuntimeError("Example is already running")
    else:
        print "Example running, press <Enter> to terminate"
        raw_input()
