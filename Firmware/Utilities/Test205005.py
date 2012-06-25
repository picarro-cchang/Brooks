#!/usr/bin/python
#
# FILE:
#   Test205005.py tests the G2000 power board outlet valve PWM drive 
#
# DESCRIPTION:
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   13-Dec-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
import getopt
import os
from Queue import Queue, Empty
import serial
import socket
import time

from numpy import *
from pylab import *
from TestUtilities import *
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from TestPowerBoardValveDriver2 import TestPowerBoardValveDriver

if __name__ == "__main__":
    pname = sys.argv[0]
    bname = os.path.basename(pname)
    if len(sys.argv) < 2:
        engineName = raw_input("Engine name? ")
    else:
        engineName = sys.argv[1]
    assert bname[:4].upper() == "TEST", "Test program name %s is invalid (should start with Test)" % (bname,)
    tp = TestParameters(engineName,bname[4:10])
    tst = TestPowerBoardValveDriver(tp,"Outlet")
    tst.run()
    tp.appendReport()
    tp.makeHTML()
