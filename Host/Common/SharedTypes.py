#!/usr/bin/python
#
# FILE:
#   SharedTypes.py
#
# DESCRIPTION:
#  Class definitions and other information (notably Rpc ports) which need to be shared among the
#  CRDS applications and drivers
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   07-Jan-2009  sze  Initial version.
#   21-Jul-2009  sze  Added GenHandler.
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import time

# Constants...
ACCESS_PUBLIC = 0
ACCESS_PICARRO_ONLY = 100

#RPC_PORT... are the port numbers used by CmdFIFO XML-RPC servers
RPC_PORT_LOGGER             = 50000
RPC_PORT_DRIVER             = 50010
RPC_PORT_FILER              = 50020
RPC_PORT_SUPERVISOR         = 50030
RPC_PORT_SUPERVISOR_BACKUP  = 50031
RPC_PORT_INTERFACE          = 50040
RPC_PORT_CONTROLLER         = 50050
RPC_PORT_ARCHIVER           = 50060
RPC_PORT_MEAS_SYSTEM        = 50070
RPC_PORT_SAMPLE_MGR         = 50080
RPC_PORT_DATALOGGER         = 50090
RPC_PORT_ALARM_SYSTEM       = 50100
RPC_PORT_INSTR_MANAGER      = 50110
RPC_PORT_COMMAND_HANDLER    = 50120
RPC_PORT_EIF_HANDLER        = 50130
RPC_PORT_PANEL_HANDLER      = 50140
RPC_PORT_LOCAL_GUI          = 50150
RPC_PORT_DATA_MANAGER       = 50160
RPC_PORT_CAL_MANAGER        = 50170
RPC_PORT_FITTER             = 50180
RPC_PORT_FILE_ERASER        = 50190
RPC_PORT_VALVE_SEQUENCER    = 50200

#TCP_PORT... are the port numbers used by "normal" TCP servers
TCP_PORT_INTERFACE          = 51000
TCP_PORT_FITTER             = 51010
TCP_PORT_COMMAND_HANDLER    = 51020
TCP_PORT_SUPERVISOR         = 23456

#BROADCAST_PORT... are the port numbers used by broadcasters
BROADCAST_PORT_EVENTLOG          = 40010
BROADCAST_PORT_SENSORSTREAM      = 40020 #All sensor data from the driver
BROADCAST_PORT_RDRESULTS         = 40030 #RD's broadcast straight from the driver
BROADCAST_PORT_RD_RECALC         = 40031 #The re-calculated ringdowns (angle->freq) from the MeasSys
BROADCAST_PORT_RCB               = 40040
BROADCAST_PORT_MEAS_SYSTEM       = 40050
BROADCAST_PORT_DATA_MANAGER      = 40060
BROADCAST_PORT_INSTMGR_DISPLAY   = 40070
BROADCAST_PORT_PROCESSED_RESULTS = 40100

# Subscheme ID bit used to indicate this row is part of a WLM calibration
CALIBRATION_ID = 4096

#STATUS_PORT... are the ports used for status register broadcasts
# - 41xxx series, set to match the RPC port 50xxx series
# - all blocks will must also have an RPC command of Status_Get()
STATUS_PORT_MEAS_SYSTEM     = 41050
STATUS_PORT_SAMPLE_MGR      = 41080
STATUS_PORT_DATALOGGER      = 41090
STATUS_PORT_ALARM_SYSTEM    = 41100
STATUS_PORT_INST_MANAGER    = 41110
STATUS_PORT_DATA_MANAGER    = 41160
STATUS_PORT_CAL_MANAGER     = 41170

# Exception classes
class CrdsException(Exception):
    """Base class for all CRDS exceptions."""
class DasException(CrdsException):
    """Base class for all DAS layer exceptions."""
class DasAccessException(DasException):
    """Invalid access to DAS registers."""

class Singleton(object):
    """An inheritable singleton class"""
    _instance = None
    def __new__(cls,*a,**k):
        if not cls._instance:
            cls._instance=super(Singleton,cls).__new__(cls,*a,**k)
        return cls._instance

class GenHandler(object):
    """This class is used to call a generator repeatedly and to perform some specified
    action on the output of that generator, either for a duration which is as close as 
    possible to a specified value, or until the generator is exhausted. In __init__,
    a function is passed to produce a new generator, if an active one does not currently
    exist. A function accepting the output of the generator is also required.
    
    It is useful when handling a number of queues within a single threaded environment
    so that we do not spend too much time trying to empty out a queue while others 
    remain unserviced. The generator function in such a case would give a generator
    that yields elements popped off the queue and raise StopIteration once the queue 
    is empty."""
    
    def __init__(self,genFunc,processFunc):
        self.genFunc = genFunc
        self.processFunc = processFunc
        self.generator = None
        self.totTime = 0
        self.num = 0
        self.avgTime = None
        
    def process(self,timeLimit):
        if not self.generator:
            self.generator = self.genFunc()
        start = time.clock()

        n = 0
        if (self.avgTime is not None) and self.avgTime != 0.0: 
            nTimes = timeLimit/self.avgTime
            while n<nTimes:
                try:
                    d = self.generator.next()
                    self.processFunc(d)
                    n += 1
                except StopIteration:
                    self.generator = None
                    break
        else:
            while time.clock()-start < timeLimit:
                try:
                    d = self.generator.next()
                    self.processFunc(d)
                    n += 1
                except StopIteration:
                    self.generator = None
                    break

        duration = time.clock()-start
        self.totTime += duration
        self.num += n
        if self.totTime > 10.0:
            self.num *= (10.0/self.totTime)
            self.totTime = 10.0
            self.avgTime = self.totTime/self.num
        return duration
    
##Misc stuff...

if __debug__:
    #verify that we have no accidental port overlapping...
    usedPorts = {}
    localsNow = {}
    localsNow.update(locals())
    for k in localsNow:
        assert isinstance(k, str)
        if k.startswith("RPC_PORT_") or k.startswith("TCP_PORT_") or k.startswith("BROADCAST_PORT_"):
            p = str(locals()[k])
            if p in usedPorts:
                raise Exception("An IP port has been duplicated and must be fixed!" + \
                                "'%s' and '%s' are both %s" % (k,usedPorts[p],p))
            else:
                usedPorts[p] = k
    del localsNow, k, usedPorts
