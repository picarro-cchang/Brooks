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

import sys
import os
import getopt

from Host.Common import CmdFIFO
from Host.autogen import interface
from Host.Common.SharedTypes import RPC_PORT_DATA_MANAGER, RPC_PORT_SUPERVISOR
from Host.Common.EventManagerProxy import Log, LogExc, EventManagerProxy_Init
from Host.Common.SingleInstance import SingleInstance
from Host.Common.AppRequestRestart import RequestRestart
####
## Set constants for this file...
####
APP_NAME = "AlarmSystem"
APP_VERSION = 1.0
APP_DESCRIPTION = "The alarm system"
_CONFIG_NAME = "AlarmSystem.ini"
CONFIG_DIR = os.environ['PICARRO_CONF_DIR']
LOG_DIR = os.environ['PICARRO_LOG_DIR']

EventManagerProxy_Init(APP_NAME)

# Set up supervisor RPC
supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME,
                                                     IsDontCareConnection=False)

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
    shortOpts = 'h'
    longOpts = ["help", "ini="]

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

    configFile = ""
    if "--ini" in options:
        configFile = os.path.join(CONFIG_DIR, options["--ini"])
        Log ("Config file specified at command line: %s" % configFile)

    return configFile

def main():
    #Get and handle the command line options...
    configFile = HandleCommandSwitches()
    my_instance = SingleInstance(APP_NAME)
    if my_instance.alreadyrunning():
        Log("Instance of %s already running" % APP_NAME, Level=2)
    else:
        Log("%s started." % APP_NAME, Level=1)
        try:
            DataManager = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER,
                                                     APP_NAME, IsDontCareConnection=False)
            rtn = DataManager.SetLegacyAlarmConfig(configFile)
            assert(rtn == interface.STATUS_OK)
            Log("Exiting program")
        except Exception, e:
            LogExc("Unhandled exception in %s: %s" % (APP_NAME, e), Level=3)
            # Request a restart from Supervisor via RPC call
            restart = RequestRestart(APP_NAME)
            if restart.requestRestart(APP_NAME) is True:
                Log("Restart request to supervisor sent", Level=0)
            else:
                Log("Restart request to supervisor not sent", Level=2)


if __name__ == "__main__":
    main()
