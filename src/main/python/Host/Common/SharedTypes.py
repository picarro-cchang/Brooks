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
import types
from Host.autogen import interface
from Host.Common.namedtuple import namedtuple

# Constants...
ACCESS_PUBLIC = 0
ACCESS_PICARRO_ONLY = 100

# RPC_PORT... are the port numbers used by CmdFIFO XML-RPC servers
RPC_PORT_LOGGER = 50000
RPC_PORT_CONTAINER = 50005
RPC_PORT_DRIVER = 50010
RPC_PORT_DRIVER_EMULATOR = 50011
RPC_PORT_FREQ_CONVERTER = 50015
RPC_PORT_FILER = 50020
RPC_PORT_SUPERVISOR = 50030
RPC_PORT_SUPERVISOR_BACKUP = 50031
RPC_PORT_RESTART_SUPERVISOR = 50032
RPC_PORT_INTERFACE = 50040
RPC_PORT_CONTROLLER = 50050
RPC_PORT_ARCHIVER = 50060
RPC_PORT_MEAS_SYSTEM = 50070
RPC_PORT_SPECTRUM_COLLECTOR = 50075
RPC_PORT_SAMPLE_MGR = 50080
RPC_PORT_DATALOGGER = 50090
RPC_PORT_ALARM_SYSTEM = 50100
RPC_PORT_INSTR_MANAGER = 50110
RPC_PORT_COMMAND_HANDLER = 50120
RPC_PORT_EIF_HANDLER = 50130
RPC_PORT_PANEL_HANDLER = 50140
RPC_PORT_LOCAL_GUI = 50150
RPC_PORT_DATA_MANAGER = 50160
RPC_PORT_CAL_MANAGER = 50170
RPC_PORT_FITTER_BASE = 50180  # Fitters use consecutive ports starting from this one
RPC_PORT_FILE_ERASER = 50190
RPC_PORT_VALVE_SEQUENCER = 50200
RPC_PORT_COORDINATOR = 50210
RPC_PORT_QUICK_GUI = 50220
RPC_PORT_READ_EXT_SENSOR = 50230
RPC_PORT_ACTIVE_FILE_MANAGER = 50300
RPC_PORT_IPV = 50400
RPC_PORT_O2_SENSOR_MONITOR = 50410
RPC_PORT_READ_GPSWS = 50071
RPC_PORT_PERIPH_INTRF = 50072
RPC_PORT_CONFIG_MONITOR = 50073
RPC_PORT_AUTOSAMPLER = 50074
RPC_PORT_PEAK_FINDER = 50501
RPC_PORT_PEAK_ANALYZER = 50502
RPC_PORT_ECHO_P3_BASE = 50600
RPC_PORT_ECHO_P3_MAX = 50699
RPC_PORT_SURVEYOR_ZMQ = 50700
RPC_PORT_MOBILE_KIT_MONITOR = 50710
RPC_PORT_CONTROL_BRIDGE = 50720
RPC_PORT_DATAMANAGER_PUBLISHER = 50730

# TCP_PORT... are the port numbers used by "normal" TCP servers
TCP_PORT_INTERFACE = 51000
TCP_PORT_FITTER = 51010
TCP_PORT_COMMAND_HANDLER = 51020
TCP_PORT_SUPERVISOR = 23456
TCP_PORT_PERIPH_INTRF = 51030
TCP_PORT_DATAMANAGER_ZMQ_PUB = 5555
TCP_PORT_DATAMANAGER_ZMQ_SUB_SYNC = 5556
TCP_PORT_CONTROL_BRIDGE_ZMQ = 5557

# ZMQ_PORT... are the port numbers used by ZMQ sockets
ZMQ_PORT_SURVEYOR_CMD = 52701

# BROADCAST_PORT... are the port numbers used by broadcasters
BROADCAST_PORT_EVENTLOG = 40010
BROADCAST_PORT_SENSORSTREAM = 40020  # All sensor data from the driver
BROADCAST_PORT_RDRESULTS = 40030  # RD's broadcast straight from the driver
# The re-calculated ringdowns (angle->freq) from the RDFrequencyConverter
BROADCAST_PORT_RD_RECALC = 40031
BROADCAST_PORT_RCB = 40040
BROADCAST_PORT_SPECTRUM_COLLECTOR = 40045
BROADCAST_PORT_MEAS_SYSTEM = 40050
BROADCAST_PORT_DATA_MANAGER = 40060
BROADCAST_PORT_PERIPH_INTRF = 40065
BROADCAST_PORT_INSTMGR_DISPLAY = 40070
# Fitters use consecutive ports starting from this one
BROADCAST_PORT_FITTER_BASE = 40080
BROADCAST_PORT_PROCESSED_RESULTS = 40100
BROADCAST_PORT_IPV = 40110

# Subscheme ID bit used to indicate this row is part of a WLM calibration
CALIBRATION_ID = 4096

# STATUS_PORT... are the ports used for status register broadcasts
# - 41xxx series, set to match the RPC port 50xxx series
# - all blocks will must also have an RPC command of Status_Get()
STATUS_PORT_MEAS_SYSTEM = 41050
STATUS_PORT_SAMPLE_MGR = 41080
STATUS_PORT_DATALOGGER = 41090
STATUS_PORT_ALARM_SYSTEM = 41100
STATUS_PORT_INST_MANAGER = 41110
STATUS_PORT_DATA_MANAGER = 41160
STATUS_PORT_CAL_MANAGER = 41170

# Exception classes


class CrdsException(Exception):
    """Base class for all CRDS exceptions."""


class DasException(CrdsException):
    """Base class for all DAS layer exceptions."""


class DasAccessException(DasException):
    """Invalid access to DAS registers."""


class DasCommsException(DasException):
    """DAS communication exception."""


class UsbConnectionError(DasException):
    """Exception thrown when connecting to or disconnecting from USB."""


class ClaimInterfaceError(DasException):
    """Exception thrown if unable to claim USB interface."""


class UsbPacketLengthError(DasException):
    """Exception thrown on encountering unexpected USB packet."""


class StateDatabaseError(DasException):
    """Exception thrown on state database errors."""


class Singleton(object):
    """An inheritable singleton class"""
    _instance = None

    def __new__(cls, *a, **k):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *a, **k)
        return cls._instance


class Bunch(object):
    """ This class is used to group together a collection as a single object,
        so that they may be accessed as attributes of that object"""

    def __init__(self, **kwds):
        """ The namespace of the object may be initialized using keyword arguments """
        self.__dict__.update(kwds)

    def __call__(self, *args, **kwargs):
        return self.call(self, *args, **kwargs)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.__dict__)

    def __repr__(self):
        return self.__str__()

HandlerTuple = namedtuple(
    'HandlerTuple', ['duration', 'nprocessed', 'finished'])


class makeHandler(object):
    """This class is used to call a reader function repeatedly and to perform some specified
    action on the output of that reader, either for a duration which is as close as
    possible to a specified value, or until the reader returns None.

    It is useful when handling a number of queues within a single threaded environment
    so that we do not spend too much time trying to empty out a queue while others
    remain unserviced."""

    def __init__(self, readerFunc, processFunc):
        """
        Args:
            readerFunc: Function which is called to read some data and which returns None
                if none is available
            processFunc: Function which returns the number of entries successfully processed. For
                backwards compatibility, returning None is equivalent to returning 1.
        """
        self.processFunc = processFunc
        self.reader = readerFunc

    def process(self, timeLimit):
        """Process until timeLimit or the reader returns None.

        Args:
            timeLimit: Maximum number of seconds to call readerFunc

        Returns: HandlerTuple with attributes
            duration: Time spent in this function
            nprocessed: Number of entries processed
            finished: Boolean indicating if we stopped because reader returned None rather
                than hitting the time limit
        """
        assert isinstance(timeLimit, (int, long, float))
        start = time.time()
        nprocessed = 0
        finished = False
        while time.time() - start < timeLimit:
            data = self.reader()
            if data is not None:
                nData = self.processFunc(data)
                if nData is None:
                    nData = 1
                nprocessed += nData
            else:
                finished = True
                break

        duration = time.time() - start
        return HandlerTuple(duration=duration, nprocessed=nprocessed, finished=finished)

schemeTableClassMemo = {}


def getSchemeTableClass(numRows):
    """Return a scheme table array class of type SchemeTableType*numRows.

    Args:
        numRows: Number of rows in the scheme

    Types are memoized to avoid repeatedly making the same class.
    """
    assert isinstance(numRows, (int, long))
    if numRows > interface.NUM_SCHEME_ROWS:
        raise ValueError, "Maximum number of scheme rows is %d" % interface.NUM_SCHEME_ROWS

    if numRows not in schemeTableClassMemo:
        SchemeRowArray = interface.SchemeRowType * numRows

        class SchemeTableType(ctypes.Structure):
            _fields_ = [("numRepeats", ctypes.c_uint),
                        ("numRows", ctypes.c_uint),
                        ("rows", SchemeRowArray)]
        schemeTableClassMemo[numRows] = SchemeTableType
    return schemeTableClassMemo[numRows]

##########################################################################
# Utilities for converting between ctypes objects and dictionaries
##########################################################################


def ctypesToDict(structure):
    """Either return argument unchanged or create a dictionary from a ctypes structure
    where the keys are the field names.

    Args:
        structure: primitive type or ctypes Structure object

    Returns: Dictionary with structure which mirrors the original structure, or the
        argument itself.
    """
    if isinstance(structure, (float, int, long, str, unicode)):
        return structure
    else:
        assert isinstance(structure, ctypes.Structure)
        result = {}
        for field in structure._fields_:  # pylint: disable=W0212
            attrib = getattr(structure, field[0])
            if hasattr(attrib, '_length_'):
                attrAsList = []
                for elem in attrib:
                    attrAsList.append(ctypesToDict(elem))
                result[field[0]] = attrAsList
            else:
                result[field[0]] = ctypesToDict(attrib)
        return result


def dictToCtypes(dictionary, cobject):
    """Fill the ctypes object cobject with the contents of the dictionary

    Args:
        dictionary: Dictionary whose keys are used to populate cobject
        cobject: Object into which the contents of the dictionary are to be placed

    Raises: Value error if cobject does not have a field that is a key in the dictionary
    """
    for key in dictionary:
        if isinstance(dictionary[key], dict):
            dictToCtypes(dictionary[key], getattr(cobject, key))
        elif isinstance(dictionary[key], list):
            for i, subTree in enumerate(dictionary[key]):
                if not isinstance(subTree, dict):
                    getattr(cobject, key)[i] = subTree
                else:
                    dictToCtypes(subTree, getattr(cobject, key)[i])
        else:
            if hasattr(cobject, key):
                setattr(cobject, key, dictionary[key])
            else:
                raise ValueError, "Unknown structure field name %s" % key


def lookup(symbol):
    """Look up a string or unicode symbol in the interface module, if needed

    Args:
        sym: String or unicode symbol to look up in interface. Int, float or long are passed through
    """
    assert isinstance(symbol, (int, long, float, str, unicode))
    if isinstance(symbol, (str, unicode)):
        symbol = getattr(interface, symbol)
    return symbol


class Operation(object):  # pylint: disable=R0903
    """An operation which can be executed using a DSP action.

    Args:
        opcode: The code for the action to be executed
        operandList: List of operands associated with the action
        env: Start address of environment in DSP environment area for storing persistent information
            associated with this action
    """

    def __init__(self, opcode, operandList=None, env=0):
        assert isinstance(opcode, (int, long, str, unicode))
        assert isinstance(operandList, types.NoneType) or hasattr(
            operandList, '__iter__')
        assert isinstance(opcode, (int, long, str, unicode))
        self.opcode = lookup(opcode)
        self.env = lookup(env)
        if operandList is None:
            self.operandList = []
        else:
            self.operandList = [lookup(opr) for opr in operandList]


class OperationGroup(object):
    """An collection of actions with associated priority and period that can be run by the DSP.

    Args:
        priority: Priority associared with this group
        period: Period associated with this group (multiples of 100ms)
        operationList: List of Operation instances comprising this group
    """

    def __init__(self, priority, period, operationList=None):
        assert isinstance(priority, (int, long))
        assert isinstance(period, (int, long))
        assert isinstance(operationList, types.NoneType) or hasattr(
            operationList, '__iter__')

        if priority < 0 or priority >= 16:
            raise ValueError("Priority out of range (0-15)")
        if period < 0 or period >= 4096:
            raise ValueError("Period out of range (0-4095)")
        self.priority = priority
        self.period = period
        if operationList == None:
            self.operationList = []
        else:
            self.operationList = operationList

    def addOperation(self, operation):
        """Add an operation to the group.

        Args:
            operation: Instance of an Operation to add to the group
        """
        self.operationList.append(operation)

    def numOperations(self):
        """Get number of operations in the group.

        Returns: Number of operations in the group
        """
        return len(self.operationList)

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

# Misc stuff...

if __debug__:
    # verify that we have no accidental port overlapping...
    usedPorts = {}
    localsNow = {}
    localsNow.update(locals())
    for k in localsNow:
        assert isinstance(k, str)
        if k.startswith("RPC_PORT_") or k.startswith("TCP_PORT_") or k.startswith("BROADCAST_PORT_"):
            p = str(locals()[k])
            if p in usedPorts:
                raise Exception("An IP port has been duplicated and must be fixed!" +
                                "'%s' and '%s' are both %s" % (k, usedPorts[p], p))
            else:
                usedPorts[p] = k
    del localsNow, k, usedPorts
