#!/usr/bin/python
#
"""
File Name: AlarmSystem.py
Purpose:
    This starts up the actual alarm system in legacy mode to retain compatibility with the old
    system of configuration files

File History:
    14-04-07 sze   Initial version

Copyright (c) 2014 Picarro, Inc. All rights reserved
"""

####
## Set constants for this file...
####
APP_NAME = "AlarmSystemLegacyStub"
APP_VERSION = 1.0
APP_DESCRIPTION = "The alarm system"
_CONFIG_NAME = "AlarmSystem.ini"

import sys
import os
import getopt
import traceback

from Host.Common import CmdFIFO
from Host.autogen import interface
from Host.Common.SharedTypes import RPC_PORT_DATA_MANAGER
from Host.Common.EventManagerProxy import Log, LogExc, EventManagerProxy_Init
EventManagerProxy_Init(APP_NAME)

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

HELP_STRING = \
"""\
AlarmSystem.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help
-c  Specify a different alarm config file.  Default = "./AlarmSystem.ini"
"""

def PrintUsage():
    print HELP_STRING

def HandleCommandSwitches():
    shortOpts = 'hc:'
    longOpts = ["help"]

    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + _CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        Log ("Config file specified at command line: %s" % configFile)

    return configFile

def main():
    #Get and handle the command line options...
    configFile = HandleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    try:
        DataManager = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER,
                                                 APP_NAME, IsDontCareConnection=False)
        rtn = DataManager.SetLegacyAlarmConfig(configFile)
        assert(rtn == interface.STATUS_OK)
        Log("Exiting program")
    except Exception, E:
        if __debug__: raise
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))

if __name__ == "__main__":
    try:
        main()
    except:
        tbMsg = traceback.format_exc()
        Log("Unhandled exception trapped by last chance handler",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = tbMsg)
    Log("Exiting program")
    sys.stdout.flush()
