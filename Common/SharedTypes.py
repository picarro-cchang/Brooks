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
#   07-Jan-2009  sze  Initial version
#   21-Jul-2009  sze  Added GenHandler
#   03-Aug-2009  sze  Added getSchemeTableClass
#   04-Aug-2009  sze  Added ctypesToDict and dictToCtypes
#   30-Sep-2009  sze  Added Scheme class

#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import ctypes
import os
import time
from Host.autogen import interface

# Constants...
ACCESS_PUBLIC = 0
ACCESS_PICARRO_ONLY = 100

#RPC_PORT... are the port numbers used by CmdFIFO XML-RPC servers
RPC_PORT_LOGGER             = 50000
RPC_PORT_DRIVER             = 50010
RPC_PORT_FREQ_CONVERTER     = 50015
RPC_PORT_FILER              = 50020
RPC_PORT_SUPERVISOR         = 50030
RPC_PORT_SUPERVISOR_BACKUP  = 50031
RPC_PORT_INTERFACE          = 50040
RPC_PORT_CONTROLLER         = 50050
RPC_PORT_ARCHIVER           = 50060
RPC_PORT_MEAS_SYSTEM        = 50070
RPC_PORT_SPECTRUM_COLLECTOR = 50075
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
RPC_PORT_COORDINATOR        = 50210
RPC_PORT_QUICK_GUI          = 50220

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
class DasCommsException(DasException):
    """DAS communication exception."""

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

    def process(self,timeLimit):
        if not self.generator:
            self.generator = self.genFunc()

        start = time.clock()
        while time.clock()-start < timeLimit:
            try:
                d = self.generator.next()
                self.processFunc(d)
            except StopIteration:
                self.generator = None
                break

        duration = time.clock()-start
        return duration

schemeTableClassMemo = {}
def getSchemeTableClass(numRows):
    # Generate a scheme table dynamically with numRows rows. These are memoized to avoid
    #  wasting memory for duplicate classes

    if numRows > interface.NUM_SCHEME_ROWS:
        raise ValueError, "Maximum number of scheme rows is %d" % interface.NUM_SCHEME_ROWS
    
    if numRows not in schemeTableClassMemo:
        SchemeRowArray = interface.SchemeRowType * numRows
        
        class SchemeTableType(ctypes.Structure):
            _fields_ = [("numRepeats",ctypes.c_uint),
                        ("numRows",ctypes.c_uint),
                        ("rows",SchemeRowArray)]
        schemeTableClassMemo[numRows] = SchemeTableType
    return schemeTableClassMemo[numRows]

# Utilities for converting between ctypes objects and dictionaries

def ctypesToDict(s):
    """Create a dictionary from a ctypes structure where the keys are the field names"""
    if isinstance(s,(float,int,long,str)):
        return s
    else:
        r = {}
        for f in s._fields_:
            a = getattr(s,f[0])
            if hasattr(a,'_length_'):
                l = []
                for e in a:
                    l.append(ctypesToDict(e))
                r[f[0]] = l
            else:
                r[f[0]] = ctypesToDict(a)
        return r

def dictToCtypes(d,c):
    """Fill the ctypes object c with data from the dictionary d"""
    for k in d:
        if isinstance(d[k],dict):
            dictToCtypes(d[k],getattr(c,k))
        elif isinstance(d[k],list):
            for i,e in enumerate(d[k]):
                if not isinstance(e,dict):
                    getattr(c,k)[i] = e
                else:
                    dictToCtypes(e,getattr(c,k)[i])
        else:
            if hasattr(c,k):
                setattr(c,k,d[k])
            else:
                raise ValueError,"Unknown structure field name %s" % k

# Routines for reading scheme files

def getNextNonNullLine(sp):
    """ Return next line in a stream which is not blank and which does not
    start with a # character. Raise an exception if the file ends."""
    while True:
        line = sp.readline()
        if not line:
            raise ValueError("Premature end of scheme file %s" % sp.name)
        line = line.strip()
        if not line or line[0] == "#":
            continue
        else:
            return line
        
class Bunch(object):
    """ This class is used to group together a collection as a single object, so that 
         they may be accessed as attributes of that object"""
    def __init__(self,**kwds):
        """ The namespace of the object may be initialized using keyword arguments """
        self.__dict__.update(kwds)
    def __call__(self,*args,**kwargs):
        return self.call(self,*args,**kwargs)

class Scheme(object):
    """Class containing a scheme."""
    def __init__(self,fileName=None):
        # Create an scheme from the specified file, or a blank
        #  Scheme if no file is specified
        self.nrepeat = 0
        self.numEntries = 0
        self.setpoint = []
        self.dwell = []
        self.subschemeId = []
        self.virtualLaser = []
        self.threshold = []
        self.pztSetpoint = []
        self.laserTemp = []
        if fileName is not None:
            self.fileName = os.path.abspath(fileName)
            # Read the scheme file
            sp = file(self.fileName,"r")
            self.nrepeat = int(getNextNonNullLine(sp).split()[0])
            self.numEntries = int(getNextNonNullLine(sp).split()[0])
            for i in range(self.numEntries):
                toks = getNextNonNullLine(sp).split()
                toks += (7-len(toks)) * ["0"]
                self.setpoint.append(float(toks[0]))
                self.dwell.append(int(toks[1]))
                self.subschemeId.append(int(toks[2]))
                self.virtualLaser.append(int(toks[3]))
                self.threshold.append(float(toks[4]))
                self.pztSetpoint.append(float(toks[5]))
                self.laserTemp.append(float(toks[6]))
                if (i & 0xF) == 0: time.sleep(0) # Processor yield
            sp.close()
    
    def makeAngleTemplate(self):
        # Make an angle based scheme template from a frequency based scheme where the setpoint 
        #  and laserTemp fields are copies of the original, while all the other fields point to
        #  the originals
        s = Scheme()
        s.nrepeat = self.nrepeat
        s.numEntries = self.numEntries
        s.setpoint = self.setpoint[:]
        s.dwell = self.dwell
        s.subschemeId = self.subschemeId
        s.virtualLaser = self.virtualLaser
        s.threshold = self.threshold
        s.pztSetpoint = self.pztSetpoint
        s.laserTemp = self.laserTemp[:]
        return s
        
    def repack(self):
        # Generate a tuple (repeats,zip(setpoint,dwell,subschemeId,virtualLaser,threshold,pztSetpoint,laserTemp))
        #  from the scheme, which is appropriate for sending it to the DAS
        return (self.nrepeat,zip(self.setpoint,self.dwell,self.subschemeId,self.virtualLaser,self.threshold,
                                 self.pztSetpoint,self.laserTemp))
        
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
