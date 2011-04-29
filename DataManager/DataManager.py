#!/usr/bin/python
#
"""
File Name: DataManager.py
Purpose: Collect and compute data. Report the results to higher level interface modules (GUI, etc) 

File History:
    2006-12-19 russ  First official release
    2006-12-20 russ  Fixed shutdown behaviour; Improved debug handling; Fixed RPC_Mode_Set
    2006-12-21 russ  Default MeasData label now the analysis script name + In-script ability to override this
    2008-02-14 sze   Include trap for Null source times
    2008-02-19 sze   Added RPC_StartInstMgrListener call, to avoid errors associated with trying to listen to instrument
                     manager at startup, when the instrument manager has not yet been started.
    2008-03-03 sze   Adding support for real-time serial output
    2008-03-07 sze   Moved rescheduling of periodic scripts to end of last execution, to avoid out-of-order executions,
                     periodic scripts now execute at times which are integer multiples of the period.
    2008-09-18 alex  Replaced ConfigParser with CustomConfigObj
    2009-01-21 alex  Added pulse analyzer
    2009-04-30 alex  Added preserved time base feature for serial output
    2009-05-11 alex  Added more STATUS_MASK_SyncToggle_N flags so more than 4 periodic scripts can be run
    2009-05-11 alex  Corrected the time stamp for broadcasting in _HandleScriptExecution() function. The current Data Manager 
                     broadcasts fitter results with the actual data time, but broadcasts periodic script results with 
                     script running time. This has be to changed for re-sync data for data alignment with the original data. 
                     Data Manager needs to be modified so that when the script reports "time" in the output dictionary, 
                     the reported time will be use for broadcasting. 
                     If the script output doesn't contain "time" information, the script running time will be used 
                     (same as before). This modification affects both broadcasting and serial output.
    2009-08-08 alex  Allowed RPC_PulseAnalyzer_SetParam() to update the parameter values in DataManager.ini file
    2009-10-16 alex  Added an option to run DataManager without InstMgr
    2010-02-03 sze   Execute synchronous and data-driven scripts within a single thread in order to avoid using a lock
    2010-03-28 sze   Give scripts initiated by forwarding data priority over those initiated by collected data
    2010-04-27 sze   Not having an analyzer for some data is now logged, rather than causing an exception.
    2010-05-05 alex  Create the RPC functions and measBuffer for Coordinator to retrieve conc data.
    2010-08-19 alex  Create the RPC functions and pulseBuffer for command interface to retrieve pulse data.
    
Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

####
## Set constants for this file...
####
APP_NAME = "DataManager"
APP_VERSION = 1.0
_DEFAULT_CONFIG_NAME = "DataManager.ini"
_MAIN_CONFIG_SECTION = "Setup"
_SERIAL_CONFIG_SECTION = "SerialOutput"

STATE__UNDEFINED = -100
STATE_ERROR = 0x0F
STATE_INIT = 0
STATE_READY = 1
STATE_ENABLED = 2

StateName = {}
StateName[STATE__UNDEFINED] = "<ERROR - UNDEFINED STATE!>"
StateName[STATE_ERROR] = "ERROR"
StateName[STATE_INIT] = "INIT"
StateName[STATE_READY] = "READY"
StateName[STATE_ENABLED] = "ENABLED"

STATUS_MASK_Analyzing    = 0x40
# The bit(s) of toggle masks must be higher than the bottom 4 bits (state) which can't be toggled.
STATUS_MASK_SyncToggle_1 = 0x1000
STATUS_MASK_SyncToggle_2 = 0x2000
STATUS_MASK_SyncToggle_3 = 0x4000
STATUS_MASK_SyncToggle_4 = 0x8000
STATUS_MASK_SyncToggle_5 = 0x10000
STATUS_MASK_SyncToggle_6 = 0x20000
STATUS_MASK_SyncToggle_7 = 0x40000
STATUS_MASK_SyncToggle_8 = 0x80000

USERCAL_SLOPE_INDEX = 0
USERCAL_OFFSET_INDEX = 1

DEFAULT_SERIAL_OUT_DELAY = 10.0 # the time delay of sending the fitter results to serial output
SERIAL_CMD_DELAY = 0.02 # the execution time delay between sending a command and actually receiving the command on the serial output

import sys
import os
import Queue
import threading
import serial
import math
import time
import string
from inspect import isclass
from collections import deque
import ScriptRunner
import heapq

from PulseAnalyzer import PulseAnalyzer
from Host.autogen import interface
from Host.PeriphIntrf.PeriphIntrf import PeriphIntrf
from Host.CommandInterface import SerialInterface
from Host.Common import CmdFIFO, StringPickler
from Host.Common import ModeDef
from Host.Common import BetterTraceback
from Host.Common import InstMgrInc
from Host.Common import AppStatus
from Host.Common import timestamp
from Host.Common.SharedTypes import RPC_PORT_MEAS_SYSTEM, RPC_PORT_DRIVER, RPC_PORT_DATA_MANAGER, RPC_PORT_FREQ_CONVERTER,\
                                    RPC_PORT_INSTR_MANAGER, RPC_PORT_CONFIG_MONITOR
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER, BROADCAST_PORT_MEAS_SYSTEM, BROADCAST_PORT_SENSORSTREAM
from Host.Common.SharedTypes import STATUS_PORT_DATA_MANAGER, STATUS_PORT_INST_MANAGER
from Host.Common.SharedTypes import CrdsException
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SafeFile import SafeFile, FileExists
from Host.Common.MeasData import MeasData
from Host.Common.Broadcaster import Broadcaster
from Host.Common.Listener import Listener
from Host.Common.InstErrors import INST_ERROR_DATA_MANAGER
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

if sys.platform == 'win32':
    threading._time = time.clock #prevents threading.Timer from getting screwed by local time changes
    
####
## Some debugging/development helpers...
####
if __debug__:
    #verify that we have text names for each state...
    __localsNow = {}
    __localsNow.update(locals())
    for __k in __localsNow:
        if __k.startswith("STATE_"):
            assert (__localsNow[__k] in StateName.keys()), "Code Error - A StateName string entry needs to be defined for %s." % __k
            if __k != "STATE__UNDEFINED]":
                assert __localsNow[__k] <= 0x0F, "Legit state values must be < 0x0F, with 0x0F reserved for ERROR"
    del __localsNow, __k

####
## Decorators
####
def docstring_set(DocString):
    """Overrides the docstring for the decorated function to DocString"""
    def decorator(f):
        f.func_doc = DocString
        return f
    return decorator
####
## Functions
####
def NameOfThisCall():
    return sys._getframe(1).f_code.co_name

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

#Set up a useful TimeStamp function...
if sys.platform == 'win32':
    TimeStamp = time.clock
else:
    TimeStamp = time.time

####
## RPC connections to other CRDS applications...
####
CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                         APP_NAME,
                                         IsDontCareConnection = False)
CRDS_MeasSys = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM,
                                         APP_NAME,
                                         IsDontCareConnection = False)
CRDS_FreqConv = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,
                                         APP_NAME,
                                         IsDontCareConnection = False)
CRDS_ConfigMonitor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_CONFIG_MONITOR,
                                         APP_NAME,
                                         IsDontCareConnection = False)
####
## Custom exceptions...
####
class DataManagerError(CrdsException):
    """Base class for all DataManager exceptions"""
class CommandError(DataManagerError):
    """Root of all exceptions caused by a bad/inappropriate command."""
class InvalidModeSelection(DataManagerError):
    """An invalid mode was selected."""
    ####
    ## Classes...
    ####
class RpcServerThread(threading.Thread):
    def __init__(self, RpcServer, ExitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.RpcServer = RpcServer
        self.ExitFunction = ExitFunction
    def run(self):
        self.RpcServer.serve_forever()
        try: #it might be a threading.Event
            self.ExitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")

class MeasTuple(tuple):
    "A tuple that is able to be referenced with .time for [0] and .value for [1]"
    def __getattribute__(self, name):
        if name == "time":
            return self[0]
        elif name == "value":
            return self[1]
        elif name == "timestamp":
            return timestamp.unixTimeToTimestamp(self[0])
            
class DataManager(object):
    """Container class/structure for DataManager options."""
    class ConfigurationOptions(object):
        def __init__(self):
            self.AnalysisHistory = -1
            self.ModeDefinitionPath = ""
            self.InstrDataPaths = []
            self.UserCalibrationPath = ""
            self.AutoEnable = False
            self.StartingMeasMode = ""
            self.maketimetuple = time.gmtime

        def LoadSerialSettings(self,cp):
            # Get the optional settings for the serial port
            if cp.has_section(_SERIAL_CONFIG_SECTION):
                self.useSerial = cp.getboolean(_SERIAL_CONFIG_SECTION,"Enable",default=True)
            else:
                self.useSerial = False
                
            if self.useSerial:
                self.serialPort = cp.get(_SERIAL_CONFIG_SECTION,"Port",default="COM1")
                self.serialTimePreserved = cp.getboolean(_SERIAL_CONFIG_SECTION,"TimePreserved",default=False)
                if self.serialTimePreserved:
                    self.serialQueueTimeout = 0.01
                else:
                    self.serialQueueTimeout = 1
                self.serialDelay = abs(cp.getfloat(_SERIAL_CONFIG_SECTION,"Delay",default=DEFAULT_SERIAL_OUT_DELAY))
                self.serialBaud = cp.getint(_SERIAL_CONFIG_SECTION,"Baud",default=9600)
                self.xonxoff = cp.getboolean(_SERIAL_CONFIG_SECTION,"XonXoff",default=False)
                self.rtscts = cp.getboolean(_SERIAL_CONFIG_SECTION,"RtsCts",default=False)
                
                bits = cp.getint(_SERIAL_CONFIG_SECTION,"DataBits",default=8)
                self.serialDataBits = (bits == 5) and serial.FIVEBITS or \
                                      (bits == 6) and serial.SIXBITS  or \
                                      (bits == 7) and serial.SEVENBITS or \
                                      (bits == 8) and serial.EIGHTBITS
                if not self.serialDataBits: raise ValueError("Invalid number of data bits")

                bits = cp.getint(_SERIAL_CONFIG_SECTION,"StopBits",default=1)
                self.serialStopBits = (bits == 1) and serial.STOPBITS_ONE or \
                                      (bits == 2) and serial.STOPBITS_TWO
                if not self.serialStopBits: raise ValueError("Invalid number of stop bits")

                p = cp.get(_SERIAL_CONFIG_SECTION,"Parity",default='N')
                self.serialParity = (p in ['n','N']) and [serial.PARITY_NONE] or \
                                    (p in ['e','E']) and [serial.PARITY_EVEN] or \
                                    (p in ['o','O']) and [serial.PARITY_ODD]
                if not self.serialParity: raise ValueError("Invalid parity string (N/E/O)")
                self.serialParity = self.serialParity[0]
                   
                try:
                    self.pollChar = eval(cp.get(_SERIAL_CONFIG_SECTION,"PollChar"))
                    self.useSerialPoll = True
                except KeyError:
                    self.useSerialPoll = False
                    
                self.ignoreBadKeys = cp.getboolean(_SERIAL_CONFIG_SECTION,"IgnoreBadKeys",default=True)
                self.invalidValue = cp.getfloat(_SERIAL_CONFIG_SECTION,"InvalidValue",default=0.0)
                
                try:
                    self.emptyString = eval(cp.get(_SERIAL_CONFIG_SECTION,"EmptyString"))
                except KeyError:
                    self.emptyString = "\r\n"
                
                self.serialSource = cp.get(_SERIAL_CONFIG_SECTION,"Source")
                self.serialFormat = eval(cp.get(_SERIAL_CONFIG_SECTION,"Format"))
                c = 0
                self.serialColumns = []
                while cp.has_option(_SERIAL_CONFIG_SECTION,"Column%d" % c):
                    self.serialColumns.append(cp.get(_SERIAL_CONFIG_SECTION,"Column%d" % c))
                    c += 1

        def Load(self, IniPath):
            """Loads the configuration from the specified ini/config file."""
            if not FileExists(IniPath):
                raise Exception("Configuration file '%s' not found." % IniPath)
            basePath = os.path.split(IniPath)[0]
            cp = CustomConfigObj(IniPath) 

            self.AnalysisHistory = cp.getint(_MAIN_CONFIG_SECTION, "AnalysisHistory")
            self.ModeDefinitionPath = os.path.join(basePath, cp.get(_MAIN_CONFIG_SECTION, "ModeDefinitionPath"))
            self.UserCalibrationPath = os.path.join(basePath, cp.get(_MAIN_CONFIG_SECTION, "UserCalibrationPath"))
            calDataCount = cp.getint(_MAIN_CONFIG_SECTION, "InstrDataFile_Count")
            basePath = os.path.split(IniPath)[0]
            self.InstrDataPaths = []
            for i in range(1, calDataCount + 1):
                relPath = cp.get(_MAIN_CONFIG_SECTION, "InstrDataFile_%d" % i)
                self.InstrDataPaths.append(os.path.join(basePath, relPath))

            self.LoadSerialSettings(cp)
            self.AutoEnable = cp.getboolean(_MAIN_CONFIG_SECTION, "AutoEnable", "False")
            self.StartingMeasMode = cp.get(_MAIN_CONFIG_SECTION, "StartingMeasMode", "")
            if cp.get(_MAIN_CONFIG_SECTION,"TimeStandard","gmt").lower() == "local":
                self.maketimetuple = time.localtime
            else:
                self.maketimetuple = time.gmtime
                
            self.enablePeriphIntrf = False
            if cp.getboolean("Setup", "EnablePeriphIntrf", False):
                self.enablePeriphIntrf = True
                self.periphIntrfConfig = os.path.join(basePath, cp.get("Setup", "periphIntrfConfig", \
                                                                       "../PeriphIntrf/serial2socket.ini"))
                    
            self.enablePulseAnalyzer = False
            if "PulseAnalyzer" in cp: 
                if cp.getboolean("PulseAnalyzer", "enabled", False):
                    self.enablePulseAnalyzer = True

            return cp
        
    #endclass (ConfigurationOptions for DataManager)

    def __init__(self, ConfigPath, noInstMgr=False):
        # # # IMPORTANT # # #
        # THIS SHOULD ONLY CONTAIN VARIABLE/PROPERTY INITS... any actual code that
        # can fail (like talking to another CRDS app or reading the HDD) should be
        # in the INIT state handler.
        # # # # # # # # # # #
        self.__State = STATE_INIT
        self.__LastState = self.__State
        self._Status = AppStatus.AppStatus(STATE_INIT, STATUS_PORT_DATA_MANAGER, APP_NAME)
        self.InitCount = 0
        self.lastSourceTime_s = None
        self.ReInitRequested = False
        self._EnableEvent = threading.Event()
        self._ClearErrorEvent = threading.Event()
        self._ShutdownRequested = False #The main state handling loop will exit when this is true
        self._FatalError = False  #The main state handling loop will also exit when this is true

        self.DataQueue = Queue.Queue()      # Will hold collected data that need to be processed asynchronously
        self.forwardedDataQueue = []        # Used to hold generated data that need to be processed BEFORE any more collected data
        self.DataHistory = {}      # keys = data tokens; values = deque of two-tuples (time, value)
        self.ReportHistory = {}    # keys = data tokens; values = deque of two-tuples (time, value)
        self.LatestSensorData = {} # keys = sensor names; values = values
        self.SensorHistory = {}    # keys = sensor names; values = deque of two-tuples (time, value)

        #Measurement mode properties...
        # - Modes is a dict of MeasMode info idnicating all the config info per mode
        # - SchemePaths will hold the list of unique scheme paths, with the index
        #   of each matching the DAS scheme index loaded into...
        self.MeasModes = {}
        self.CurrentMeasMode = None
        if 0: assert isinstance(self.CurrentMeasMode, ModeDef.MeasMode) #for wing
        self.AnalyzerCode = {}   # keys = script paths; values = compiled code objects
        self.InstrData = {}      # keys,values taken from instr files
        self.ConfigPath = ConfigPath
        self.Config = DataManager.ConfigurationOptions()
        self.cp = None
        self.UserCalibration = {} #keys = measurement names; values = (slope, offset); default = (1, 0)
        self.UserCalAppListDict = {} #keys = primary measurement names; values = affected measurement names assoicated with each key
        self.MeasListener = None
        self.SensorListener = None
        self.InstMgrStatusListener = None
        self.LatestInstMgrStatus = -1
        #Set up the Broadcaster that will be used to send processor data to the Data Manager...
        self.DataBroadcaster = Broadcaster(BROADCAST_PORT_DATA_MANAGER, APP_NAME, logFunc=Log)
        # Serial port for use by the analysis scripts
        self.serial = None
        self.serialThread = None
        self.serialThreadAllowRun = True
        self.serialOutQueue = Queue.Queue(0)
        self.serialPollLock = threading.Lock()
        self.measBufferLock = threading.Lock()
        self.pulseBufferLock = threading.Lock()
        # Priority queue for synchronous scripts ordered by ideal execution time and period
        #  Entries on queue are (execTime, period, startTime, iteration, syncInfoObj)
        self.syncScriptQueue = []  
        self.syncScriptsLaunched = False
        self.lastTimeGood = True
        self.maxLate = 0
        self.maxScriptDuration = {}
        self.syncScriptDelayHist = {}
        
        #Now set up the RPC server...
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_DATA_MANAGER),
                                                ServerName = APP_NAME,
                                                ServerDescription = "",
                                                ServerVersion = APP_VERSION,
                                                threaded = True)
        self.RpcThread = None
        #Register the rpc functions...
        for s in dir(self):
            attr = self.__getattribute__(s)
            if callable(attr) and s.startswith("RPC_") and (not isclass(attr)):
                self.RpcServer.register_function(attr, NameSlice = 4)

        self.calEnabled = True
        self.measBufferConfig = ("",[],20) # (source, colList, bufSize)
        self.measBuffer = []
        self.pulseBufferSize = 512
        self.pulseBuffer = []
        self.pulseWaitForData = False
        self.noInstMgr = noInstMgr
        if not self.noInstMgr:
            self.rdInstMgr = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER,
                                                        APP_NAME,
                                                        IsDontCareConnection = False)
        self.CRDS_PeriphIntrf = None
        
        # Pulse Analyzer
        self.pulseAnalyzer = None
        self.runPulseAnalyzer = False
        self.addToPulseAnalyzer = False
                                          
    def _AssertValidCallingState(self, StateList):
        if self.__State not in StateList:
            raise CommandError("Command invalid in present state ('%s')." % StateName[self.__State])

    def serialInterfaceSender(self):
        """Get data off the serial output data queue and send it"""
        while self.serialThreadAllowRun:
            if self.Config.useSerialPoll:
                ch = self.serial.read()
                if ch != self.Config.pollChar: 
                    continue
                self.serialPollLock.acquire()
                self.serial.write(self.serialString)
                self.serialPollLock.release()                
            else:
                try:
                    (measDataTime, enqueueTime, serialOutputToWrite) = self.serialOutQueue.get(block=True,timeout=self.Config.serialQueueTimeout)
                    timeToSend = measDataTime + self.Config.serialDelay - time.time()
                    if self.Config.serialTimePreserved and timeToSend > SERIAL_CMD_DELAY:
                        time.sleep(timeToSend-SERIAL_CMD_DELAY)
                    self.serial.write(serialOutputToWrite)
                    if __debug__:
                        curTime = time.time()
                        if self.Config.serialTimePreserved:
                            offSchedule = curTime - (measDataTime + self.Config.serialDelay)
                            #if abs(offSchedule) > 1.0: 
                            #    Log("Serial output %.3f seconds off of schedule" % offSchedule, Level = 1)
                        else:
                            #offSchedule = curTime - measDataTime
                            # Record the time required to send the data out of queue
                            offSchedule = curTime - enqueueTime
                        if abs(offSchedule) > 1.0: 
                            Log("Serial output %.3f seconds off of schedule" % offSchedule, Level = 1)
                except Queue.Empty:
                    pass
        self.serialThreadAllowRun = True

    def killSerialThread(self):
        self.serialThreadAllowRun = False

    def RPC_Shutdown(self):
        """Shuts down the Data Manager

        This has the same affect as stopping the RPC server.

        """
        self._ShutdownRequested = True
    def RPC_ReInit(self):
        """Restarts the application, putting it through INIT state again."""
        self.ReInitRequested = True
    def RPC_Mode_Set(self, ModeName):
        """Sets the measurement mode, determining how data will be analyzed."""
        if self.CurrentMeasMode and (ModeName == self.CurrentMeasMode.Name):
            return
        elif not ModeName in self.MeasModes.keys():
            raise InvalidModeSelection(ModeName)
        self._ChangeMode(ModeName)
        return "OK"
    def RPC_Mode_Get(self):
        """Returns the name of the mode the measurement system is currently set to.

        This does not indicate whether it is enabled or not.
        """
        if self.CurrentMeasMode == None:
            return "<NOT SPECIFIED YET>"
        return self.CurrentMeasMode.Name
    def RPC_Mode_GetAvailable(self):
        """Returns a list of the available measurement modes."""
        return self.MeasModes.keys()
    def RPC_Error_Clear(self):
        """Clears the current error state (and starts in INIT state again).

        Doing this does not, of course, mean that the error itself has gone away,
        so the application may end up back in the error state again if the situation
        has not been fixed.

        """
        self._AssertValidCallingState([STATE_ERROR,])
        Log("Request received to clear error state")
        self._ClearErrorEvent.set()
    def RPC_GetState(self):
        """Returns a dictionary with a text indication of the system states."""
        ret = dict(State = StateName[self.__State])
        return ret
    def RPC_GetDelays(self):
        """Returns dictionary of data manager synchronous script delay histograms, keyed
        by script name. The 9 bins of each histogram are logarithmically spaced, with 
        bin=math.floor(2*log10(delay)+6)"""
        return self.syncScriptDelayHist
    def RPC_Enable(self):
        """Enables the data manager in the mode set by Mode_Set.
        """
        try: #catch for DAS errors (and any other remote procedure call error)...
            if __debug__: Log("System Enable request received - RPC_Enable()", Level = 0)
            ##Validate that the call is possible and/or makes sense...
            self._AssertValidCallingState([STATE_INIT,        #Will try and enable when ready
                                           STATE_READY,       #Triggers transition to ENABLED
                                           STATE_ENABLED,     #No problem enabling again!
                                           ])
            ##React to the call...
            if not self.CurrentMeasMode:
                raise CommandError("Cannot enable without setting a measurement mode first")
            if self.__State == STATE_ENABLED:
                return #we are already sweeping
            else:
                #Now to set the enabled event which will get us out of ready state...
                self._EnableEvent.set()
        except CommandError:
            if __debug__: LogExc("Command error", dict(State = StateName[self.__State]), Level = 0)
            raise
        except:
            LogExc("Unhandled exception in command call", Data = dict(Command = NameOfThisCall))
            raise
        return "OK"
    def RPC_Disable(self, keepSyncScripts=False):
        """Disables the measurement system and stops the instrument from scanning.
        """
        if __debug__: Log("System DISable request received - RPC_Disable()", Level = 0)
        if not keepSyncScripts:
            self._StopSyncScripts()
        self._EnableEvent.clear()
        return "OK"
    def RPC_StartInstMgrListener(self):
        """Start the listener for instrument manager status. This is called by the instrument manager when
        it starts up"""
        if self.InstMgrStatusListener == None:
            self.InstMgrStatusListener = Listener(None,
                                                  STATUS_PORT_INST_MANAGER,
                                                  AppStatus.STREAM_Status,
                                                  self._InstMgrStatusFilter,
                                                  retry = True,
                                                  name = "Data manager Instrument Manager listener",logFunc = Log)
            return "OK"
        else:
            return "Already started"
    
    def RPC_Cal_Enable(self):
        self.calEnabled = True
        Log("Calibration enabled")
    def RPC_Cal_Disable(self):
        self.calEnabled = False
        Log("Calibration disabled")
    def RPC_Cal_GetMeasNames(self):
        return self.UserCalAppListDict.keys()
    def RPC_Cal_AdjustZero(self, MeasName, ObservedOffset):
        """Changes the zero offset for the reported-vs-measured cal for the given MeasName.

        - ie: New_Cal_Offset = Old_Cal_Offset - ObservedOffset
        - Cal slope is untouched by this call.
          - if previously unspecified, the slope stays at unity
        - Internal HostCore measured values do not change with this call.
        - Revert to factory defaults with Cal_RestoreFactoryDefaults

        """
        try:
            oldOffset = self.UserCalibration[MeasName][USERCAL_OFFSET_INDEX]
            slope = self.UserCalibration[MeasName][USERCAL_SLOPE_INDEX]
        except LookupError:
            oldOffset = 0
            slope = 1
        newOffset = oldOffset - ObservedOffset
        Log("User calibration request received - AdjustZero",
            Data = dict(MeasName = MeasName,
                        OldOffset = oldOffset,
                        NewOffset = newOffset,
                        ObservedOffset = ObservedOffset))
        self.UserCalibration[MeasName] = (slope, newOffset)
        for appMeas in self.UserCalAppListDict[MeasName]:
            self.UserCalibration[appMeas] = (slope, newOffset)
        self._UpdateUserCalibrationFile()
    def RPC_Cal_AdjustSpan(self, MeasName, ExpectedMeas, ReportedMeas):
        """Changes the cal slope for the reported-vs-measured cal for the given MeasName.

        - ie: NewSlope = (OldSlope)*(ExpectedMeas - CalOffset)/(ReportedMeas - CalOffset)
        - Cal offset is not changed by this call
           - if previously unspecified, the offset stays at zero
        - Internal HostCore measured values do not change with this call.
        - Revert to factory defaults with Cal_RestoreFactoryDefaults

        """
        try:
            calOffset = self.UserCalibration[MeasName][USERCAL_OFFSET_INDEX]
            oldSlope = self.UserCalibration[MeasName][USERCAL_SLOPE_INDEX]
        except LookupError:
            calOffset = 0
            oldSlope = 1
        newSlope = (oldSlope * (ExpectedMeas - calOffset)/(ReportedMeas - calOffset))
        Log("User calibration request received - AdjustSpan",
            Data = dict(MeasName = MeasName,
                        OldSlope = oldSlope,
                        NewSlope = newSlope,
                        Offset = calOffset))
        self.UserCalibration[MeasName] = (newSlope, calOffset)
        for appMeas in self.UserCalAppListDict[MeasName]:
            self.UserCalibration[appMeas] = (newSlope, calOffset)
        self._UpdateUserCalibrationFile()
    def RPC_Cal_SetSlopeAndOffset(self, MeasName, Slope = 1, Offset = 0):
        """Changes both the cal slope and offset for the given MeasName.

        - Internal HostCore measured values do not change with this call.
        - Revert to factory defaults with Cal_RestoreFactoryDefaults

        """
        Log("User calibration request received - SetSlopeAndOffset",
            Data = dict(MeasName = MeasName,
                        NewSlope = Slope,
                        NewOffset = Offset))
        self.UserCalibration[MeasName] = (Slope, Offset)
        for appMeas in self.UserCalAppListDict[MeasName]:
            self.UserCalibration[appMeas] = (Slope, Offset)
        self._UpdateUserCalibrationFile()
    def RPC_Cal_RestoreFactoryDefaults(self, MeasName):
        """Restores the factory cal (slope =1, offset = 0) for MeasName.

        To restore all factory calibrations, use Cal_RestoreAllFactoryDefaults

        """
        Log("Factory defaults restored for user calibration of measurement", dict(MeasName = MeasName))
        #just set slope and offset to 1 and 0
        self.UserCalibration[MeasName] = (1, 0)
        for appMeas in self.UserCalAppListDict[MeasName]:
            self.UserCalibration[appMeas] = (1, 0)
        self._UpdateUserCalibrationFile()
    def RPC_Cal_RestoreAllFactoryDefaults(self):
        """Restores the factory cal (slope = 1, offset = 0) for all measurements.

        """
        Log("Factory default calibration restored for all measured values.", dict(Changed = self.UserCalibration.keys()))
        for MeasName in self.UserCalibration:
            self.UserCalibration[MeasName] = (1, 0)
            for appMeas in self.UserCalAppListDict[MeasName]:
                self.UserCalibration[appMeas] = (1, 0)
        self._UpdateUserCalibrationFile()
    def RPC_Cal_GetUserCalibrations(self):
        """Returns the set of user calibrations that have been specified.

        Returns a dictionary of two-tuples -> (slope, offset)

        If an expected measurement name is missing, this is normal and simply
        means that the user has never calibrated that measurement. ie: slope = 1,
        and offset = 0.

        If an empty dictionary is returned, there have been no user calibrations
        done whatsoever.

        """
        return self.UserCalibration
    def RPC_Cal_GetUserCal(self, measName):
        """Returns the set of user calibration for a specified measName

        Returns a tuple -> (slope, offset)

        """
        return self.UserCalibration[measName]

    def RPC_Cal_GetInstrCalibrations(self):
        """Returns instrument calibrations"""
        return self.InstrData
            
    def RPC_PulseAnalyzer_Set(self, source, concNameList, targetConc = None, thres1Pair = [0.0, 0.0], 
                              thres2Pair = [0.0, 0.0], triggerType = "in", waitTime = 0.0, 
                              validTimeAfterTrigger = 0.0, validTimeBeforeEnd = 0.0, timeout = 0.0, 
                              bufSize = 500, numPointsToTrigger = 1, numPointsToRelease = 1, armCond = None):
        try:
            self.pulseAnalyzer = PulseAnalyzer(source, concNameList, targetConc, thres1Pair, thres2Pair,
                                               triggerType, waitTime, validTimeAfterTrigger, validTimeBeforeEnd,
                                               timeout, bufSize, numPointsToTrigger, numPointsToRelease, armCond)
            self.runPulseAnalyzer = False
            self.addToPulseAnalyzer = False
            return "OK"
        except Exception, err:
            return err
        
    def RPC_PulseAnalyzer_StartRunning(self):
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        self.pulseAnalyzer.resetAnalyzer()
        self.runPulseAnalyzer = True
        self.addToPulseAnalyzer = False
        return "OK"
        
    def RPC_PulseAnalyzer_StopRunning(self):
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        self.runPulseAnalyzer = False
        return "OK"
            
    def RPC_PulseAnalyzer_StartAddingData(self):
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        self.pulseAnalyzer.resetAnalyzer()
        self.addToPulseAnalyzer = True
        self.runPulseAnalyzer = False
        return "OK"

    def RPC_PulseAnalyzer_StopAddingData(self):
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        self.addToPulseAnalyzer = False
        return "OK"
            
    def RPC_PulseAnalyzer_GetOutput(self):
        """Returns the result list in the format of [status, pulseFinished, concBufferDict]. 
        It won't clear the pulse anlayzer buffer.
        """
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            return self.pulseAnalyzer.getOutput()

    def RPC_PulseAnalyzer_GetTimestamp(self):
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            return self.pulseAnalyzer.getTimestamp()

    def RPC_PulseAnalyzer_GetDataReady(self):
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            return self.pulseAnalyzer.getDataReady()

    def RPC_PulseAnalyzer_IsTriggeredStatus(self):
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            return self.pulseAnalyzer.isTriggeredStatus()
            
    def RPC_PulseAnalyzer_Reset(self):
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            self.pulseAnalyzer.resetAnalyzer()
            return "OK"
            
    def RPC_PulseAnalyzer_GetStatistics(self):
        """Retrieve statistics of data in pulse analyzer buffer"""
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            return self.pulseAnalyzer.getStatistics()
            
    def RPC_PulseAnalyzer_GetPulseStartEndTime(self):
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            return self.pulseAnalyzer.getPulseStartEndTime()
            
    # Below pulse analyzer functions are used by Command Interface
    def RPC_PulseAnalyzer_GetBuffer(self):
        """Get every analysis output from pulse analyzer buffer. This will also clear the whole buffer"""
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            if len(self.pulseBuffer) == 0:
                return "Pulse buffer empty"
            self.pulseBufferLock.acquire()
            ret = self.pulseBuffer
            self.pulseBuffer = []
            self.pulseBufferLock.release()
            return ret
        
    def RPC_PulseAnalyzer_GetBufferFirst(self):
        """Get the first pulse analysis data from pulse analyzer buffer. It will also remove this data from the buffer"""
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            if len(self.pulseBuffer) == 0:
                return "Pulse buffer empty"
            self.pulseBufferLock.acquire()
            try:
                ret = self.pulseBuffer[0]
                self.pulseBuffer = self.pulseBuffer[1:]
            except:
                pass
            finally:
                self.pulseBufferLock.release()
            return ret
        
    def RPC_PulseAnalyzer_ClearBuffer(self):
        """Clear all the data in the internal pulse analyzer buffer"""
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            self.pulseBufferLock.acquire()
            self.pulseBuffer = []
            self.pulseBufferLock.release()
            return "OK"

    def RPC_PulseAnalyzer_GetStatus(self):
        if self.pulseAnalyzer == None:
            return "No Pulse Analyzer"
        else:
            return self.pulseAnalyzer.getStatus()
          
    def _AddToPulseBuffer(self, pulseData):
        self.pulseBufferLock.acquire()
        try:
            if len(self.pulseBuffer) >= self.pulseBufferSize:
                self.pulseBuffer = self.pulseBuffer[-(self.pulseBufferSize-1):]
            self.pulseBuffer.append(pulseData)
        except:
            pass
        finally:
            self.pulseBufferLock.release()
            
    def RPC_MeasBuffer_Set(self, source, colList, bufSize):
        """Set up an internal measurement buffer for the Coordinator"""
        self.measBufferLock.acquire()
        self.measBufferConfig = (source, colList, bufSize)
        self.measBuffer = []
        self.measBufferLock.release()
        return "OK"
        
    def RPC_MeasBuffer_Clear(self):
        """Clear all the data in the internal measurement buffer"""
        self.measBufferLock.acquire()
        self.measBuffer = []
        self.measBufferLock.release()
        return "OK"
        
    def RPC_MeasBuffer_Get(self):
        """Get all the data in the internal measurement buffer"""
        self.measBufferLock.acquire()
        ret = self.measBuffer
        self.measBuffer = []
        self.measBufferLock.release()
        return ret
        
    def RPC_MeasBuffer_GetFirst(self):
        """Get the first (oldest) data in the internal measurement buffer"""
        if len(self.measBuffer) == 0:
            return
        self.measBufferLock.acquire()
        ret = self.measBuffer[0]
        self.measBuffer = self.measBuffer[1:]
        self.measBufferLock.release()
        return ret
        
    def _AddToMeasBuffer(self, measData):
        (source, colList, bufSize) = self.measBufferConfig
        if len(colList) == 0 or bufSize < 1:
            return
        if measData.Source != source: 
            return
        self.measBufferLock.acquire()
        try:
            result = {"measTime":measData.Time}
            result["date"] = time.strftime("%Y/%m/%d %H:%M:%S", self.Config.maketimetuple(measData.Time))       
            for c in colList:
                result[c] = measData.Data[c]
            if len(self.measBuffer) >= bufSize:
                self.measBuffer = self.measBuffer[-(bufSize-1):]
            self.measBuffer.append(result)
        except:
            pass
        finally:
            self.measBufferLock.release()
                
    def _UpdateUserCalibrationFile(self):
        cp = CustomConfigObj(self.Config.UserCalibrationPath) 
        for measName in self.UserCalAppListDict.keys():
            if measName not in cp.list_sections():
                cp.add_section(measName)
            cp.set(measName, "slope", self.UserCalibration[measName][USERCAL_SLOPE_INDEX])
            cp.set(measName, "offset", self.UserCalibration[measName][USERCAL_OFFSET_INDEX])
        cp.write()
        # Commit and push such changes using Config Monitor
        CRDS_ConfigMonitor.monitor("User calibration changed")
        Log("User calibration file updated.", dict(Sections = self.UserCalibration.keys()))

    def _EnqueueSyncScript(self,sai,startTime,iteration):
        assert isinstance(sai, ModeDef.SyncAnalyzerInfo)
        heapq.heappush(self.syncScriptQueue,(startTime+iteration*sai.Period_s,sai.Period_s,startTime,iteration,sai))
    
    def _TimeToNextSyncScript(self):
        if self.syncScriptQueue:
            xeqTime,period,startTime,iteration,sai = self.syncScriptQueue[0]
            return xeqTime - time.time()
        else:
            return None
        
    def _LaunchSyncScripts(self):
        """Enqueues initial synchronous script execution requests. These run when time.time() is an integer
           multiple of the period of the script"""
        self.syncScriptsLaunched = True
        if self.CurrentMeasMode and self.CurrentMeasMode.SyncSetup:
            Log("Starting synchronous analyzers", dict(Count = len(self.CurrentMeasMode.SyncSetup),
                SyncAnalyzers = [sai.ReportName for sai in self.CurrentMeasMode.SyncSetup]))
            for sai in self.CurrentMeasMode.SyncSetup:
                assert isinstance(sai, ModeDef.SyncAnalyzerInfo)
                startTime = math.ceil(time.time()/sai.Period_s) * sai.Period_s
                self._EnqueueSyncScript(sai,startTime,0)
            Log("Synchronous analyzers have all been enqueued")
            
    def _ToggleStatusSyncBit(self, SyncInfoObj):
        index = self.CurrentMeasMode.SyncSetup.index(SyncInfoObj)
        if index == 0:
            mask = STATUS_MASK_SyncToggle_1
        elif index == 1:
            mask = STATUS_MASK_SyncToggle_2
        elif index == 2:
            mask = STATUS_MASK_SyncToggle_3
        elif index == 3:
            mask = STATUS_MASK_SyncToggle_4
        elif index == 4:
            mask = STATUS_MASK_SyncToggle_5            
        elif index == 5:
            mask = STATUS_MASK_SyncToggle_6 
        elif index == 6:
            mask = STATUS_MASK_SyncToggle_7            
        elif index == 7:
            mask = STATUS_MASK_SyncToggle_8
            
        self._Status.ToggleStatusBit(mask)
        
    def _RunNextSyncScript(self):
        if self.syncScriptQueue:
            xeqTime,period,startTime,iteration,sai = heapq.heappop(self.syncScriptQueue)
            late = time.time() - xeqTime
            codeObj = self.AnalyzerCode[sai.AnalyzerInfo.ScriptPath]
            scriptArgs = sai.AnalyzerInfo.ScriptArgs
            self._ToggleStatusSyncBit(sai)
            self._HandleScriptExecution(ScriptCodeObj = codeObj,
                                        ScriptArgs = scriptArgs,
                                        ReportSource = sai.ReportName,
                                        SourceTime_s = xeqTime,  #Want to report the perfect time, not actual time
                                        DataDict = {}, #no direct data, sync scripts use histories
                                        )
            if late > 0:
                bin = math.floor(2*math.log10(late)+6)
                bin = int(min(max(bin,0),8))
            else:
                bin = 0
            if sai.ReportName in self.syncScriptDelayHist:
                self.syncScriptDelayHist[sai.ReportName][bin] += 1
            else:
                self.syncScriptDelayHist[sai.ReportName] = [0 for bin in range(9)]
                
            if late > self.maxLate:
                Log("Max periodic script delay so far %.3fs on iteration %d: %s" % (late,iteration,sai.ReportName))
                self.maxLate = late
            if late > 0.25:
                Log("PERIODIC SCRIPT LATE BY %.3fs on iteration %d: %s" % (late,iteration,sai.ReportName), Level = 1)
            if late > 5*period: # Skip executions if we are very late
                skip = int(math.floor(late/period))
                iteration += skip
                Log("Skipping %d iterations of synchronous script %s" % (skip,sai.ReportName))
            # Enqueue next execution time for this script    
            if self.syncScriptsLaunched:
                self._EnqueueSyncScript(sai,startTime,iteration+1)
        else:
            Log("A request to run a sync script occured although none were enqueued")

    def _StopSyncScripts(self, WaitUntilSure = True):
        """Stops the existing sync timer scripts.
        """
        self.syncScriptQueue = []
        self.syncScriptsLaunched = False
        time.sleep(1)   # Wait to ensure currently running scripts have stopped
        self.syncScriptQueue = []
        Log("Synchronous analyzers have all been stopped.")
        
    def _ChangeMode(self, ModeName):
        """Changes the measurement mode of the DataManager."""
        if __debug__: Log("Measurement mode change request received", dict(NewMode = ModeName), Level = 0)
        if self.CurrentMeasMode:
            oldModeName = self.CurrentMeasMode.Name
        else:
            oldModeName = "<NOT SPECIFIED>"
        self._StopSyncScripts()
        self.CurrentMeasMode = self.MeasModes[ModeName]
        self._LaunchSyncScripts()
        Log("Measurement mode changed.", dict(NewMode = ModeName, OldMode = oldModeName))
        
    def __SetState(self, NewState):
        """Sets the state of the DataManager.  Variable init is done as appropriate."""
        if NewState == self.__State:
            return

        if __debug__: #code helper - make sure state changes are happening only from where we expect
            callerName = sys._getframe(1).f_code.co_name
            if not callerName.startswith("_HandleState_") and not callerName.startswith("_MainLoop"):
                raise Exception("Code error!  State changes should only be made/managed in _MainLoop!!  Change attempt made from %s." % callerName)

        #Do any on-entry state initialization that is needed...
        if NewState == STATE_INIT:
            pass
        elif NewState == STATE_ENABLED:
            pass
        elif NewState == STATE_READY:
            pass
        elif NewState == STATE_ERROR:
            self._ClearErrorEvent.clear()

        #and now actually change the state variable and log the change...
        self.__LastState = self.__State
        self.__State = NewState
        if NewState == STATE_ERROR:
            eventLevel = 3
            if not self.noInstMgr:
                #report the error - ideally this is a don't care connection, but it
                #can't be because we need to make InstMgr calls elsewhere where we need
                #return values, so call it on a thread to avoid any hangup if the
                #InstMgr is dead...
                errReportThread = threading.Thread(target = self._ReportInstError, args = (INST_ERROR_DATA_MANAGER, ))
                errReportThread.start()
        elif NewState == STATE_INIT:
            eventLevel = 2
        else:
            eventLevel = 1
        self._Status.UpdateState(self.__State)
        Log("State changed",
            dict(State = StateName[NewState],
                 PreviousState = StateName[self.__LastState]),
            Level = eventLevel)
    def _ReportInstError(self, ErrorCode):
        """Small function enabling the InstMgr error reporting call to be called on
        a thread (to get dontcare-like functionality)"""
        self.rdInstMgr.INSTMGR_ReportErrorRpc(ErrorCode)
    def _MeasDataFilter(self, Obj):
        measData = MeasData()
        measData.ImportPickleDict(Obj)
        return measData
    def _SensorFilter(self, obj):
        """Updates the latest sensor readings.

        This is executed for every sensor value picked up from the sensor stream
        broadcast.

        """
        if 0: assert isinstance(obj, interface.SensorEntryType) #for Wing

        streamTime  = obj.timestamp
        sensorName = interface.STREAM_MemberTypeDict[obj.streamNum][len("STREAM_"):]
        sensorValue = obj.value

        self.LatestSensorData[sensorName] = sensorValue
        #TODO: May want to fix the streamTime in the next addition, but relative *should* be fine...
        self._AddToHistory(self.SensorHistory, {sensorName:sensorValue}, streamTime)
    def _InstMgrStatusFilter(self, obj):
        """Updates the local (latest) copy of the instrument manager status bits."""
        if 0: assert isinstance(obj, AppStatus.STREAM_Status) #for Wing
        self.LatestInstMgrStatus = obj.status

    def _HandleState_INIT(self):
        #try:
        #    self.RPC_StartInstMgrListener()
        #    print "Started instrument manager status listener"
        #except:
        #    pass
        self.ReInitRequested = False
        try:
            self.InitCount += 1
            if self.InitCount > 1:
                Log("Re-initializing application", dict(InitCount = self.InitCount))
            ##Load the main application configuration settings...
            self.cp = self.Config.Load(self.ConfigPath)
            ## open the serial port (may be used by scripts)
            if self.serialThread != None:
                self.killSerialThread()
                self.serialThread.join(2.0)   
                if self.serialThread.isAlive():
                    Log("Cannot kill old serial output thread",Level=2)
                    raise RuntimeError("Cannot kill old serial output thread")
                self.serialThread = None
            if self.serial != None: 
                self.serial.close()
                self.serial = None
            if self.Config.useSerial:
                try:
                    self.serial = SerialInterface.SerialInterface()
                    self.serial.config( port = self.Config.serialPort,
                                        baudrate = self.Config.serialBaud,
                                        bytesize = self.Config.serialDataBits,
                                        parity = self.Config.serialParity,
                                        stopbits = self.Config.serialStopBits,
                                        xonxoff = self.Config.xonxoff,
                                        rtscts = self.Config.rtscts,
                                        timeout = 1 )
                    self.serialString = self.Config.emptyString
                    self.serial.open()
                    self.serialThread = threading.Thread(target=self.serialInterfaceSender)
                    self.serialThread.setDaemon(True)
                    self.serialThread.start()
                except Exception, e:
                    LogExc("Serial port initialization failed. EXCEPTION: %s %r" % (e, e), Level=3)
                    self.serial = None
            else:
                self.serial = None
            ##Figure out what modes are available and load all details...
            self.MeasModes = ModeDef.LoadModeDefinitions(self.Config.ModeDefinitionPath)
            Log("Mode definitions loaded", dict(ModeNames = self.MeasModes.keys()))
            ##Load the instrument data...
            for path in self.Config.InstrDataPaths:
                cp = CustomConfigObj(path, ignore_option_case=False)
                for k, v in cp.list_items("Data"):
                    self.InstrData[k] = float(v)

            ##Load up any customer-specified calibrations...
            try:
                #Check for nulls in the file (a sure sign of a corruption... better is a checksum but this can be coded later)...
                fp = file(self.Config.UserCalibrationPath, "r")
                if chr(0) in fp.read(): raise Exception("User calibration file corrupted - likely due to improper shutdown")
                fp.close()
                #Now read any cals...
                cp = CustomConfigObj(self.Config.UserCalibrationPath, ignore_option_case=False, list_values = True)
                for measName in cp.list_sections():
                    slope = cp.getfloat(measName, "slope")
                    offset = cp.getfloat(measName, "offset")
                    self.UserCalibration[measName] = (slope, offset)
                    try:
                        appList = cp.get(measName, "applist", "")
                        if len(appList) == 0:
                            appList = []
                        elif type(appList) != type([]):
                            appList = [appList]
                        self.UserCalAppListDict[measName] = appList
                        for appMeas in appList:
                            self.UserCalibration[appMeas] = (slope, offset)
                    except:
                        self.UserCalAppListDict[measName] = []
            except:
                #If *any* error occurs reading this file, always revert to factory defaults...
                LogExc("Error while reading customer specified measurement calibrations.")
                #self.RPC_Cal_RestoreAllFactoryDefaults()

            ##Set up the analyzer scripts...
            self.AnalyzerCode = {}
            allAnalyzerPaths = []
            for m in self.MeasModes.values():
                allAnalyzerPaths.extend([aio.ScriptPath for aio in m.Analyzers.values() if aio != None])
                for sai in m.SyncSetup:
                    allAnalyzerPaths.append(sai.AnalyzerInfo.ScriptPath)
            import sets
            uniqueAnalyzerPaths = list(sets.Set(allAnalyzerPaths))
            Log("Starting compilation of identified analyzer scripts", dict(Count = len(uniqueAnalyzerPaths)))
            for path in uniqueAnalyzerPaths:
                sourceString = file(path,"r").read()
                if sys.platform != 'win32':
                    sourceString = sourceString.replace("\r","")
                Log("Compiling analyzer script", dict(Path = path))
                codeObj = compile(sourceString, path, "exec") #providing path accurately allows debugging of script
                self.AnalyzerCode[path] = codeObj
            Log("Analyzer script compilation complete")

            #Set up some Listeners for the important data...
            #Set up our listener to catch MeasSystem data broadcasts (stop the old one if already exists)...
            if self.MeasListener != None:
                self.MeasListener.stop()
                self.MeasListener = None
            self.MeasListener = Listener(self.DataQueue,
                                         BROADCAST_PORT_MEAS_SYSTEM,
                                         StringPickler.ArbitraryObject,
                                         self._MeasDataFilter,
                                         retry = True,
                                         name = "Data manager measurement system listener",logFunc = Log)
            #And our listener to collect sensor data broadcasts (stop the old one if already exists)...
            if self.SensorListener != None:
                self.SensorListener.stop()
                self.SensorListener = None
            self.SensorListener = Listener(None,
                                         BROADCAST_PORT_SENSORSTREAM,
                                         interface.SensorEntryType,
                                         self._SensorFilter,
                                         retry = True,
                                         name = "Data manager sensor stream listener",logFunc = Log)
            # The Instrument Manager status listener is started only when the Instrument Manager has started and
            # issued an RPC call.
            # Deal with debug options...
            if self.Config.AutoEnable:
                Log("EnableEvent set due to 'Debug_AutoEnable' configuration setting.")
                #Set it up to automatically start...
                self._EnableEvent.set()

            if self.Config.StartingMeasMode:
                self.CurrentMeasMode = self.MeasModes[self.Config.StartingMeasMode]
                Log("Current mode name initialized", dict(Name = self.Config.StartingMeasMode))

            if self.Config.enablePeriphIntrf:
                try:
                    self.CRDS_PeriphIntrf = PeriphIntrf(self.Config.periphIntrfConfig)
                except Exception, err:
                    self.CRDS_PeriphIntrf = None
                    Log("Peripheral Interface not running. Error: %r" % err)
                    print "Peripheral Interface not running. Error: %r" % err
                    
            # Initialize pulse analyzer if endabled in INI file
            if self.Config.enablePulseAnalyzer:
                try:    
                    self._configPulseAnalyzerFromIni()
                    self.runPulseAnalyzer = True
                    self.addToPulseAnalyzer = False
                except Exception, err:
                    print "%r" % err
                                         
            self.__SetState(STATE_READY)
        except:
            LogExc(Data = dict(State = StateName[self.__State]))
            self.__SetState(STATE_ERROR)
            
    def _configPulseAnalyzerFromIni(self):
        source = self.cp.get("PulseAnalyzer", "source")
        concNameList = [conc.strip() for conc in self.cp.get("PulseAnalyzer","concNameList").split(",")]
        targetConc = self.cp.get("PulseAnalyzer", "targetConc")
        thres1Pair = [float(t) for t in self.cp.get("PulseAnalyzer","thres1Pair").split(",")]
        thres2Pair = [float(t) for t in self.cp.get("PulseAnalyzer","thres2Pair").split(",")]
        triggerType = self.cp.get("PulseAnalyzer", "triggerType")
        waitTime = self.cp.getfloat("PulseAnalyzer", "waitTime")
        validTimeAfterTrigger = self.cp.getfloat("PulseAnalyzer", "validTimeAfterTrigger")
        validTimeBeforeEnd = self.cp.getfloat("PulseAnalyzer", "validTimeBeforeEnd")
        timeout = self.cp.getfloat("PulseAnalyzer", "timeout")
        bufSize = self.cp.getint("PulseAnalyzer", "bufSize")
        numPointsToTrigger = self.cp.getint("PulseAnalyzer", "numPointsToTrigger")
        numPointsToRelease = self.cp.getint("PulseAnalyzer", "numPointsToRelease")
        armCond = self.cp.get("PulseAnalyzer", "armCond", "None")
        if armCond is not "None":
            armCond = [float(t) for t in armCond.split(",")]
        self.pulseAnalyzer = PulseAnalyzer(source, concNameList, targetConc, thres1Pair, thres2Pair,
                                           triggerType, waitTime, validTimeAfterTrigger, validTimeBeforeEnd,
                                           timeout, bufSize, numPointsToTrigger, numPointsToRelease, armCond)
        msg = "Pre-defined pulse analyzer started. (%s, %s, %s, %s)" % (targetConc, thres1Pair, thres2Pair, triggerType)
        print msg
        Log(msg)
        
    def _HandleState_READY(self):
        try:
            exitState = STATE__UNDEFINED
            self._EnableEvent.wait(0.05)

            #In ready mode, we can have synchronous scripts, not data-driven scripts
            # Launch synchronous scripts if they aren't already pending...
            if not self.syncScriptsLaunched:
                self._LaunchSyncScripts()
            # Allow script to run if we are within 10ms of the target execution time.
            if self.syncScriptQueue:
                timeToNextSyncScript = self._TimeToNextSyncScript()
                while timeToNextSyncScript != None and timeToNextSyncScript < 0.01: 
                    self._RunNextSyncScript()
                    timeToNextSyncScript = self._TimeToNextSyncScript()
            
            if self._EnableEvent.isSet():
                if not self.CurrentMeasMode:
                    raise DataManagerError("No measurement mode set - Can't enable the measurement system!")
                exitState = STATE_ENABLED
            else:
                exitState = STATE_READY
        except:
            LogExc(Data = dict(State = StateName[self.__State]))
            exitState = STATE_ERROR
        if exitState == STATE__UNDEFINED:
            raise Exception("HandleState_READY has a code error - the exitState has not been specified!!")
        self.__SetState(exitState)
    
    def _HandleState_ENABLED(self):
        #In this state we processing data as it is appears in the data queue
        # - Sync scripts will be running as appropriate for the mode
        try:
            exitState = STATE__UNDEFINED
            if not self._EnableEvent.isSet():
                self.__SetState(STATE_READY)
                return
            time.sleep(0)
            # Launch synchronous scripts if they aren't already pending...
            if self.CurrentMeasMode.SyncSetup and (not self.syncScriptsLaunched):
                self._LaunchSyncScripts()
            try:
                # First deal with synchronous scripts that need to be run. Allow script to
                #  run if we are within 10ms of the target execution time.
                if self.syncScriptQueue:
                    timeToNextSyncScript = self._TimeToNextSyncScript()
                    while timeToNextSyncScript != None and timeToNextSyncScript < 0.01: 
                        self._RunNextSyncScript()
                        timeToNextSyncScript = self._TimeToNextSyncScript()
                # Information on the forwarded data queue must be dealt with before processing more collected
                #  data, since it implicitly has an earlier timestamp
                if self.forwardedDataQueue:
                    data = self.forwardedDataQueue.pop(0)
                else:
                    # Check for collected data, ensuring that we get out at least every 0.5s to check if we need to stop
                    timeToNextSyncScript = self._TimeToNextSyncScript()
                    if timeToNextSyncScript != None:
                        dataQueueTimeout = min(max(0.0,timeToNextSyncScript),0.5)
                    else:
                        dataQueueTimeout = 0.5
                    data = self.DataQueue.get(timeout = dataQueueTimeout)
                assert isinstance(data, MeasData) # for Wing
                self._AnalyzeData(data)
                exitState = STATE_ENABLED
            except Queue.Empty:
                #don't even have a timeout here... if there is no data there is no data.  period.
                #This differs from the MeasSystem wherein if there is no data there may be a
                #problem with the DAS.
                exitState = STATE_ENABLED
        except:
            LogExc(Data = dict(State = StateName[self.__State]))
            exitState = STATE_ERROR
        if exitState == STATE__UNDEFINED:
            raise Exception("HandleState_ENABLED has a code error - the exitState has not been specified!!")
        self.__SetState(exitState)
        
    def _HandleState_ERROR(self):
        self._ClearErrorEvent.wait(0.05)
        if self._ClearErrorEvent.isSet():
            self.__SetState(STATE_INIT)
            
    def _MainLoop(self):
        #When started, sit and wait until a sweep is started (which sets the
        #Enabled Event). If enabled, loop and keep assembling spectra.  When
        #disabled, drop back to as if freshly started. All other activity is
        #asynchronous and event driven.
        #ALL STATE MANAGEMENT SHOULD IDEALLY BE DONE IN THIS MAIN LOOP!!!

        #start the rpc server on another thread...
        self.RpcThread = RpcServerThread(self.RpcServer, self.RPC_Shutdown)
        self.RpcThread.start()

        stateHandler = {}
        stateHandler[STATE_INIT] = self._HandleState_INIT
        stateHandler[STATE_READY] = self._HandleState_READY
        stateHandler[STATE_ENABLED] = self._HandleState_ENABLED
        stateHandler[STATE_ERROR] = self._HandleState_ERROR

        # ### THIS IS THE MAIN STATE HANDLER LOOP ### #
        while not self._ShutdownRequested and not self._FatalError:
            if self.ReInitRequested: self.__SetState(STATE_INIT)
            stateHandler[self.__State]()
        #end while

        ##Any shutdown handling should go here...
        self._StopSyncScripts()
        if not self._ShutdownRequested:
            self.RpcServer.stop_server()
        wait_s = 2
        self.RpcThread.join(wait_s)
        if self.RpcThread.isAlive():
            Log("Timed out while waiting for RpcServerThread to close.  Terminating rudely!",
                Data = dict(WaitTime_s = wait_s),
                Level = 2)
        if self._FatalError:
            Log("DataManager terminated due to a fatal error.", Level = 3)
        else:
            Log("DataManager exited due to shutdown request.", Level = 2)
            
    def Start(self):
        self._MainLoop()
        
    def _AddToHistory(self, HistoryDict, DataDict, DataTime):
        """Records DataDict elements into HistoryDict with the given DataTime stamp.

        History length is FIFO'd with a max len of self.Config.AnalysisHistory.

        Histories are made to be accessible as follows:

          HistoryDict[k][-10][0] == <timestamp of 10th most recent data token k>
          HistoryDict[k][-10][0] == HistoryDict[k][-10].time
          HistoryDict[k][-10][1] == HistoryDict[k][-10].value
          HistoryDict[k][-1] == DataDict[k]

        """
        for k in DataDict.keys():
            if not HistoryDict.has_key(k):
                #fifo'ing happening more than access, so a deque should be better than a list (I think)...
                HistoryDict[k] = deque()
            HistoryDict[k].append(MeasTuple((DataTime, DataDict[k])))
            #make sure the history is no larger than requested
            if len(HistoryDict[k]) > self.Config.AnalysisHistory:
                HistoryDict[k].popleft()
        #endfor

    def _SendSerial(self,measData):
        # Examine measData and format it for serial output if its report source name matches that specified in the configuration file
        if self.serial == None: return
        if measData.Source != self.Config.serialSource : return
        result = []
        badKeys = []
        for c in self.Config.serialColumns:
            try:
                result.append(measData.Data[c])
            except KeyError:
                if not self.Config.ignoreBadKeys:
                    badKeys.append(c)
                else:
                    result.append(self.Config.invalidValue)
        if badKeys:
            if self.lastTimeGood:
                Log("Data for column(s) not found for serial output",
                    Data={"BadKeys":badKeys,"ReportSource":measData.Source},Level=2)
            self.lastTimeGood = False
            return
        else:
            measDataTime = measData.Time
            self.lastTimeGood = True
            try:
                resultAsString = self.Config.serialFormat % tuple(result)
            except:
                Log("Bad format string for serial output data",
                    Data={"Format":self.Config.serialFormat,"Data":tuple(result)},Level=2)
                return
            if self.Config.useSerialPoll:
                self.serialPollLock.acquire()
                self.serialString = resultAsString
                self.serialPollLock.release()
            else:    
                self.serialOutQueue.put((measDataTime, time.time(), resultAsString))

    def _getPeriphData(self, requestTime, dataList):
        try:
            return self.CRDS_PeriphIntrf.getDataByTime(requestTime, dataList)
        except:
            Log("Peripheral Interface was interrupted")
            print "Peripheral Interface was interrupted"
            self.CRDS_PeriphIntrf = None
            
    def _HandleScriptExecution(self,
                               ScriptCodeObj,
                               ScriptArgs,
                               ReportSource,
                               SourceTime_s,
                               DataDict):
        """Executes the provided script with the input information provided.

        All reported data from the script is broadcasted.
        Forwarded data is forwarded to the incoming data queue.
        The data manager histories are updated appropriately.

        This wrapper call allows you to specify what you want to give to the
        script, but still deal with the script outputs "normally".

        """
        # Trap for time being None
        if SourceTime_s == None:
            Log("SourceTime invalid in data manager",
                Data={"SourceTime_s":SourceTime_s,"lastSourceTime_s":self.lastSourceTime_s,
                      "CompiledFile":ScriptCodeObj.co_filename,"ReportSource":ReportSource},
                Level=2)
            self.lastSourceTime_s = None
            return
        self.lastSourceTime_s = SourceTime_s
        ##First, run the script!!
        self._Status.UpdateStatusBit(STATUS_MASK_Analyzing, True)
        
        # self.LatestInstMgrStatus is updated by self.InstMgrStatusListener
        currentInstMgrStatus = self.LatestInstMgrStatus
        
        try:
            UserCalDict = self.RPC_Cal_GetUserCalibrations()
        except:
            UserCalDict = {}
            
        if self.CRDS_PeriphIntrf:
            periphIntrfFunc = self._getPeriphData
        else:
            periphIntrfFunc = None
            
        ret = ScriptRunner.RunAnalysisScript(ScriptCodeObj = ScriptCodeObj,
                                             ScriptArgs = ScriptArgs,
                                             SourceTime_s = SourceTime_s,
                                             DataDict = DataDict,
                                             InstrDataDict = self.InstrData,
                                             SensorDataDict = self.LatestSensorData,
                                             DataHistory = self.DataHistory,
                                             ReportHistory = self.ReportHistory,
                                             SensorHistory = self.SensorHistory,
                                             DriverRpcServer = CRDS_Driver,
                                             InstrumentStatus = self.LatestInstMgrStatus,
                                             MeasSysRpcServer = CRDS_MeasSys,
                                             FreqConvRpcServer = CRDS_FreqConv,
                                             PeriphIntrfFunc = periphIntrfFunc,
                                             SerialInterface = self.serial,
                                             ScriptName = ReportSource,
                                             ExcLogFunc = LogExc,
                                             UserCalDict = UserCalDict,
                                             CalEnabled = self.calEnabled)
        #unpack the returned tuple (space saving above)...
        (reportDict, forwardDict, newDataDict, measGood, reportSource_out) = ret
        self._Status.UpdateStatusBit(STATUS_MASK_Analyzing, False)

        # Update SourceTime_s with the "time" information provided by the script (if available)
        
        # Deal with explicit "time" and "timestamp" fields in the reportDict
        # 1. If "time" is present, it is used to set both SourceTime_s and "timestamp"
        # 2. Elif "timestamp" is present, it is used to set both SourceTime_s and "time"
        # 3. Elif neither is present, both are set from the SourceTime_s
        
        if reportDict:
            if "time" in reportDict:
                rptSourceTime_s = reportDict["time"]
                reportDict["timestamp"] = timestamp.unixTimeToTimestamp(rptSourceTime_s)
            elif "timestamp" in reportDict:
                rptSourceTime_s = timestamp.unixTime(reportDict["timestamp"])
                reportDict["time"] = rptSourceTime_s
            else:
                rptSourceTime_s = SourceTime_s
        else:
            rptSourceTime_s = SourceTime_s
        #Get the data histories set up for the next script execution...
        #Deal with the independent "report" history...
        self._AddToHistory(self.ReportHistory, reportDict, rptSourceTime_s)
        #Add new data generated to the history...
        # - will appear to subsequent scripts in the same history position, and with
        #   the same timesatamp, as the data that was incoming to this script (the
        #   "typical" _OLD_DATA" history)
        # - Script execution guaranteed that there are no duplicate keys that could
        #   put screwy double-ups into the history
        self._AddToHistory(self.DataHistory, newDataDict, rptSourceTime_s)

        #Broadcast any data that should be broadcasted/reported...
        #  - also dealing with user calibrations here
        if reportDict:
            # First do any required user calibration (linear rescaling of reported data)...
            # - THIS *MUST* BE DONE JUST PRIOR TO BROADCAST "UPWARDS" TO CUSTOMER-VISIBLE APPS
            # - all internal calculations don't care about what the customer thinks is
            #   the "correct" measured value.  The internal value will always be consistent.
            for measName, measValue in reportDict.items():
                try:
                    measValue = float(measValue)
                except:
                    Log("Data reported from script is not a number",
                        Data = {"measName":measName,"measValue":measValue},
                        Level=2)
                if self.UserCalibration.has_key(measName):
                    try:
                        slope = self.UserCalibration[measName][USERCAL_SLOPE_INDEX]
                        offset = self.UserCalibration[measName][USERCAL_OFFSET_INDEX]
                        reportDict[measName] = (measValue * slope) + offset
                    except Exception, err:
                        LogExc("User calibration failed. EXCEPTION: %s %r" % (err, err), Level=3)
            #Now figure out if the measurement is a "good" one...
            # - this is the AND of what the script already decided, and what the instrument
            #   conditions are indicating.  All have to indicate good or it isn't.
            if not self.noInstMgr:
                pressureLocked =    currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_PRESSURE_LOCKED
                cavityTempLocked =  currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_CAVITY_TEMP_LOCKED
                warmboxTempLocked = currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
                warmingUp =         currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_WARMING_UP
                systemError =       currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_SYSTEM_ERROR
                measGood = measGood and pressureLocked \
                                    and cavityTempLocked \
                                    and warmboxTempLocked \
                                    and (not warmingUp) \
                                    and (not systemError)
            else:
                measGood = 1
            #Broadcast the result data...
            measData = MeasData(reportSource_out, rptSourceTime_s, reportDict, measGood, self.RPC_Mode_Get())
            self.DataBroadcaster.send(measData.dumps())
            #Send to serial port if needed
            self._SendSerial(measData)
            # Add to the internal measBuffer for Coordinator
            self._AddToMeasBuffer(measData)
            # Use data for Pulse Analyzer
            if self.pulseAnalyzer != None:
                if self.runPulseAnalyzer:
                    self.pulseAnalyzer.runAnalyzer(measData)
                elif self.addToPulseAnalyzer:
                    self.pulseAnalyzer.addToBuffer(measData)
                # Add pulse analysis data to Data Manager pulse analysis buffer if available
                if self.pulseAnalyzer.getStatus() == "triggered":
                    self.pulseWaitForData = True
                if self.pulseWaitForData and self.pulseAnalyzer.getDataReady():
                    try:
                        pulseOutput = self.pulseAnalyzer.getStatistics()
                        pulseConcNameList = self.pulseAnalyzer.getConcNameList()
                        pulseData = [pulseOutput["timestamp_mean"]]
                        for concName in pulseConcNameList:
                            try:
                                pulseData.append(pulseOutput["%s_mean" % concName])
                                pulseData.append(pulseOutput["%s_std" % concName])
                                pulseData.append(pulseOutput["%s_slope" % concName])
                            except:
                                pass
                        self._AddToPulseBuffer(pulseData)
                    except Exception, err:
                        LogExc("Pulse analyzer operation failed. EXCEPTION: %s %r" % (err, err), Level=3)
                    self.pulseWaitForData = False
                
        #Put forwarded data in the to-be-analyzed queue...
        for dataPacketLabel in forwardDict.keys():
            dataPacketDict = forwardDict[dataPacketLabel]
            #Force a + prefix on all forwarded data labels...
            self.forwardedDataQueue.append(MeasData("+%s" % dataPacketLabel, rptSourceTime_s, dataPacketDict, Mode=self.RPC_Mode_Get()))
        time.sleep(0)
        
    def _AnalyzeData(self, Data):
        """Runs the analysis script appropriate for the given Data and current Mode."""
        #also need to provide
        # - portal for making Driver calls    (_DRIVER_RPC as CmdFIFOServerProxy)
        assert isinstance(Data, MeasData)
        measTime = Data.Time
        currentDataDict = Data.Data
        self._AddToHistory(self.DataHistory, currentDataDict, measTime)
        if Data.Source in self.CurrentMeasMode.Analyzers:
            analyzerPath = self.CurrentMeasMode.Analyzers[Data.Source].ScriptPath
        else:
            Log("Analyzer path not found for given data source! Data source = %s, Analyzers are %s" 
                   % (Data.Source, self.CurrentMeasMode.Analyzers.keys()),Level=2)
            return
        if not self.AnalyzerCode.has_key(analyzerPath):
            #may not always analyze!  Might just let the history collect
            # - eg: with sensor data... might just set up a sync script to report up
            #       the latest values extracted from the history
            return
        analyzerCode = self.AnalyzerCode[analyzerPath]
        analyzerArgs = self.CurrentMeasMode.Analyzers[Data.Source].ScriptArgs
        #Note that "currentDataDict[k] == self.DataHistory[k][-1]" is now true
        self._HandleScriptExecution(ScriptCodeObj = analyzerCode,
                                    ScriptArgs = analyzerArgs,
                                    ReportSource = os.path.split(analyzerPath)[1][:-3],
                                    SourceTime_s = measTime,
                                    DataDict = currentDataDict)
    #endclass (DataManager)
HELP_STRING = \
"""\
DataManager.py [--no_inst_mgr] [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h              Print this help.
-c              Specify a different config file.  Default = "./DataManager.ini"
--no_inst_mgr   Run this application without Instrument Manager.

"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt

    shortOpts = 'hc:'
    longOpts = ["help", "test", "no_inst_mgr"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    executeTest = False
    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()
    else:
        if "--test" in options:
            executeTest = True

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + _DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
        Log("Config file specified at command line", configFile)

    if "--no_inst_mgr" in options:
        noInstMgr = True
    else:
        noInstMgr = False
        
    return (configFile, noInstMgr, executeTest)
def ExecuteTest(DM):
    """A self test executed via the --test command-line switch."""
    print "No self test implemented yet!"
def main():
    #Get and handle the command line options...
    configFile, noInstMgr, test = HandleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    try:
        app = DataManager(configFile, noInstMgr)
        if test:
            threading.Timer(2, ExecuteTest(app)).start()
        app.Start()
    except:
        if __debug__: raise
        LogExc("Exception trapped outside DataManager execution")

if __name__ == "__main__":
    try:
        main()
    except:
        tbMsg = BetterTraceback.get_advanced_traceback()
        Log("Unhandled exception trapped by last chance handler",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = tbMsg)
    Log("Exiting program")
    sys.stdout.flush()
