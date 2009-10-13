#!/usr/bin/python
#
# FILE:
#   ExamineRDCount.py
#
# DESCRIPTION:
#   Listen to the processed RD results queue and print out some fields for debug
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   13-Oct-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
import getopt
from numpy import *
import os
import Queue
import socket
import time
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from scipy.optimize import fmin
from Host.Common.WlmCalUtilities import bestFit

#APPROX_FSR = 0.077
APPROX_FSR = 0.1


if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("ExamineRD")

class ExamineRD(object):
    def __init__(self):
        # Define a listener for the ringdown data
        self.listener = Listener(None,SharedTypes.BROADCAST_PORT_RD_RECALC,ProcessedRingdownEntryType,self.rdFilter)

    def rdFilter(self,entry):
        assert isinstance(entry,ProcessedRingdownEntryType)
        print entry.status, entry.count, entry.schemeTable, entry.schemeRow
        
    def run(self):
        while True:
            sys.stdout.write(".")
            time.sleep(1)
            
if __name__ == "__main__":
    e = ExamineRD()
    e.run()
