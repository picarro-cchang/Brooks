#!/usr/bin/python
#
# File Name: EventManagerProxy.py
# Purpose:
#   A set of short functions to make logging to the event manager consistent
#   and easy.
#
# Notes:
#  - This file is designed to be imported with "from EventManagerProxy import *"
#  - EventManagerProxy_Init must be called first before using the functions.
#
# File History:
# 06-08-29 russ  First release
# 06-11-13 sze   Ensure that logger problems do not kill the caller
# 06-12-01 russ  Reversed previous change (that is what DontCareConnection is for);
#                Made DontCareConnection default to True instead
# 06-12-04 russ  Added PrintEverything debug option
# 07-09-03 sze   Commented out better traceback call to reduce length of messages

from Host.Common import SharedTypes #to get the right TCP port to use
from Host.Common import CmdFIFO
from SharedTypes import RPC_PORT_LOGGER, ACCESS_PICARRO_ONLY

import traceback
import sys

__EventManagerProxy = None
_PrintEverything = False

#set the explicit list of what to export for "from LoggingProxy import *"...
__all__ = ["EventManagerProxy_Init", "Log", "LogExc"]

def EventManagerProxy_Init(ApplicationName, DontCareConnection = True, PrintEverything = False):
    """Initializes the EventManagerProxy.  Must be done before any other calls."""
    global __EventManagerProxy
    global _PrintEverything
    _PrintEverything = PrintEverything
    __EventManagerProxy = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_LOGGER,
                                                     ApplicationName,
                                                     IsDontCareConnection = DontCareConnection)

def Log(Desc, Data = None, Level = 1, Code = -1, AccessLevel = ACCESS_PICARRO_ONLY, Verbose = "", SourceTime = 0):
    """Short global log function that sends a log to the EventManager."""
    if __debug__:
        if _PrintEverything or Level >= 2:
            print "*** LOGEVENT (%d) = %s; Data = %r" % (Level, Desc, Data)
            if Verbose:
                print "+++ VERBOSE DATA FOLLOWS +++\n%s" % Verbose
    __EventManagerProxy.LogEvent(Desc, Data, Level, Code, AccessLevel, Verbose, SourceTime)

def LogExc(Msg = "Exception occurred", Data = {}, Level = 2, Code = -1, AccessLevel = ACCESS_PICARRO_ONLY, SourceTime = 0):
    """Sends a log of the current exception to the EventManager.

    Data must be a dictionary - exception info will be added to it.

    An advanced traceback is included as the verbose data.

    """
    excType, excValue, excTB = sys.exc_info()
    logDict = Data
    logDict.update(dict(Type = excType.__name__, Value = str(excValue), Note = "<See verbose for debug info>"))
    #verbose = BetterTraceback.get_advanced_traceback(1)
    verbose = traceback.format_exc()
    Log(Msg, logDict, Level, Code, AccessLevel, verbose, SourceTime)
