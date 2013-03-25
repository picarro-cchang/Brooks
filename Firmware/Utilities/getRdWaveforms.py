#!/usr/bin/python
#
# FILE:
#   getRdWaveforms.py
#
# DESCRIPTION:
#   Get ringdown waveforms
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   18-Aug-2010  sze  Initial version.
#
#  Copyright (c) 2010 Picarro, Inc. All rights reserved
#
import os
import sys
import time
import getopt
from configobj import ConfigObj
from numpy import *
from pylab import *
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.SharedTypes import RPC_PORT_DRIVER

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
    
Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    "", IsDontCareConnection = False)

class GetRdWaveforms(object):
    def __init__(self,configFile,options):
        pass
        
    def run(self):
        # Check that the driver can communicate
        try:
            print "Driver version: %s" % Driver.allVersions()
        except:
            raise ValueError,"Cannot communicate with driver, aborting"
        self.d = []
        for i in range(50):
            Driver.wrDasReg(SPECT_CNTRL_STATE_REGISTER,SPECT_CNTRL_PausedState)
            time.sleep(0.05)
            data, meta, params = Driver.rdRingdown(0)
            Driver.wrDasReg(SPECT_CNTRL_STATE_REGISTER,SPECT_CNTRL_RunningState)
            self.d.append(data)
            time.sleep(0.05)
            print i
        for data in self.d:
            plot(data)
        show()
        
        
HELP_STRING = """getRdWaveforms.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./getRdWaveforms.ini"
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
    #Start with option defaults...
    configFile = os.path.splitext(AppPath)[0] + ".ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile, options
    
if __name__ == "__main__":
    configFile, options = handleCommandSwitches()
    m = GetRdWaveforms(configFile, options)
    m.run()
