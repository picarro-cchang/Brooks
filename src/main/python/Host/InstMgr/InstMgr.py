#!/usr/bin/python
#
"""
File Name: InstMgr.py
Purpose:
    The instrument manager application is responsible for the following:
    1. Overall instrument awareness and state machine
       - Command management based on overall state, i.e. can't start a measurement if in self-test state.
       - Knows the states of each sub-system.
    2. Instrument startup
    3. Instrument shutdown
    4. Instrument Error handling and Health Monitoring
    5. System wide procedures
       - Start and stop measuring commands.

The instrument manager state transition methods such as _EnterWarming, _EnterMeasure etc can be called from many
  different places, including RPCs (which are served in a separate thread). They perform actions and then return.
  The _Monitor method loops around in the main thread and periodically calls RPCs from other applications. From
  the data collected, it updates the instrument manager status flags and may call the state transition methods.

File History:
    06-10-xx al   In progress
    06-12-11 Al   Fixed a bunch of things: exception handling, recovery scheme, application restart notification etc..
    06-12-11 Al   Changed errorList to contain a list of tuples containing time, error number and error name.
    06 12-12 Al   Added a few except statements for meassys RPC calls.
    06-12-13 Al   Moved SampleMgr import statement up above EventMgrProxitInit
    06-12-18 Al   Using AppStatus class to track and report status.
    06-12-20 Al   Changes required for cal manager and data manager integration.
    06-12-21 Al   Fixed transition from Warming and removed FlowStop call in INSTRMGR_Start
    06-12-21 Al   Remove instrument shutdown when RpcServerExit is requested.
    06-12-21 Al   Remove check for laser temperature lock to transition from Warming.
    06-12-21 Al   Fix parking issues.
    06-12-22 Al   Don't turn off temperature control when the instrument is shutdown.
    07-01-16 sze  Print out exception message on error
    07-03-16 sze  Fixed Shutdown RPC call so that supervisor terminates applications when codes 1 or 2 are used
    07-10-23 sze  Added SetInstrumentMode RPC call. Note that _SetupInstModeDispatcher is used to define the valid
                  instrument modes and to set up the actions to be performed when that mode is selected.
    08-04-30 sze  Call TerminateApplications with powerOff == True
    08-05-08 sze  Removed code that performs automatic calibration
    08-09-18 alex Replaced ConfigParser with CustomConfigObj
    09-10-21 alex Replaced CalManager with RDFrequencyConverter. Added an option to run without SampleManager.
    10-02-25 sze  When SampleManager is disabled, do not adjust valves
    10-04-26 sze  Allow flow to be established in the Monitor if the valves are all closed, whether or not
                   we are in measuring mode. It is up to the sample manager to check that the cavity temperature
                   is not too far off to protect the cavity from condensation.
    10-04-27 sze  Modified error recovery features for G2000 analyzer. Provide an RPC to trigger a simulated error condition.
                    Make the warming state be the entry point for recovering from problems. During monitoring, check if the
                    measurement system is not enabled, and enable it as necessary. Changed GetStateRpc to return a dictionary
                    of states.
    10-06-07 alex  Stop ringdown acquisition in warming mode
    10-08-12 alex  Added RPC functions and INI parameter to enable/disable auto restart flow after valve control is disabled.

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

import sys
import os.path
import time
import threading
import struct  #for converting numbers to byte format
import getopt
import traceback

from Host.autogen import interface
from Host.SampleManager.SampleManager import SAMPLEMGR_STATUS_STABLE, SAMPLEMGR_STATUS_PARKED, SAMPLEMGR_STATUS_PURGED, SAMPLEMGR_STATUS_PREPARED, SAMPLEMGR_STATUS_FLOWING
from Host.Common import CmdFIFO, Broadcaster
from Host.Common.SharedTypes import STATUS_PORT_INST_MANAGER, BROADCAST_PORT_INSTMGR_DISPLAY,\
    RPC_PORT_SPECTRUM_COLLECTOR, RPC_PORT_SUPERVISOR, RPC_PORT_FREQ_CONVERTER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.AppStatus import AppStatus
from Host.Common.InstMgrInc import INSTMGR_STATUS_READY, INSTMGR_STATUS_MEAS_ACTIVE, INSTMGR_STATUS_ERROR_IN_BUFFER, INSTMGR_STATUS_GAS_FLOWING, INSTMGR_STATUS_PRESSURE_LOCKED, INSTMGR_STATUS_CLEAR_MASK
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED, INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR
from Host.Common.SafeFile import FileExists
from Host.Common.InstErrors import *
from Host.Common.EventManagerProxy import *
from Host.Common.SingleInstance import SingleInstance
from Host.Common.AppRequestRestart import RequestRestart

APP_NAME = "InstMgr"
APP_VERSION = 1.0
_DEFAULT_CONFIG_NAME = "InstMgr.ini"
_MAIN_CONFIG_SECTION = "MainConfig"
CONFIG_DIR = os.environ['PICARRO_CONF_DIR']
LOG_DIR = os.environ['PICARRO_LOG_DIR']

EventManagerProxy_Init(APP_NAME)

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

#Set up a useful TimeStamp function...
if sys.platform == 'win32':
    from time import clock as TimeStamp
else:
    from time import time as TimeStamp

# ---------------------------------------------------------------------------
# These should be added to interface???
# Enumerated definitions for DASCNTRL_StateType
from ctypes import *
DASCNTRL_StateType = c_ushort
DASCNTRL_Reset = 0 # DASCNTRL Reset state.
DASCNTRL_Ready = 1 # DASCNTRL Ready state.
DASCNTRL_Startup = 2 # DASCNTRL Startup state.
DASCNTRL_Diagnostic = 3 # DASCNTRL Diagnostic state.
DASCNTRL_Error = 4 # DASCNTRL Error state.
DASCNTRL_DspNotBooted = 5 # DASCNTRL Dsp Not Booted.
# ---------------------------------------------------------------------------

# INSTRMGR state type
INSTMGR_STATE = 0
INSTMGR_WARMING_STATE = 1
INSTMGR_MEASURING_STATE = 2

# INSTMGR Shutdown types
INSTMGR_SHUTDOWN_PREP_SHIPMENT = 0 # shutdown host and DAS and prepare for shipment
INSTMGR_SHUTDOWN_HOST_AND_DAS  = 1 # shutdown host and DAS
INSTMGR_SHUTDOWN_HOST          = 2 # shutdown host and leave DAS in current state

# INSTMGR RPC return codes
INSTMGR_RPC_SUCCESS = 0
INSTMGR_RPC_NOT_READY = -1
INSTMGR_RPC_FAILED = -2

INSTMGR_STATE_UNDEFINED = -100
INSTMGR_STATE_RESET = 0
INSTMGR_STATE_WARMING = 1
INSTMGR_STATE_READY = 2
INSTMGR_STATE_MEASURING = 3
INSTMGR_STATE_DAS_RESTART = 4
INSTMGR_STATE_ERROR = 5
INSTMGR_STATE_PARKING = 6

StateName = {}
StateName[INSTMGR_STATE_UNDEFINED] = "<ERROR - UNDEFINED STATE!>"
StateName[INSTMGR_STATE_RESET] = "RESET"
StateName[INSTMGR_STATE_WARMING] = "WARMING"
StateName[INSTMGR_STATE_READY] = "READY"
StateName[INSTMGR_STATE_MEASURING] = "MEASURING"
StateName[INSTMGR_STATE_DAS_RESTART] = "DAS_RESTARTING"
StateName[INSTMGR_STATE_ERROR] = "ERROR"
StateName[INSTMGR_STATE_PARKING] = "PARKING"

WARMING_STATE_UNDEFINED = -100
WARMING_STATE_TEMP_STAB = 0

WarmingStateName = {}
WarmingStateName[WARMING_STATE_UNDEFINED] = "<WARMING UNDEFINED STATE!>"
WarmingStateName[WARMING_STATE_TEMP_STAB] = "WARMING_TEMP_STAB"

MEAS_STATE_UNDEFINED = -100
MEAS_STATE_PRESSURE_STAB = 0
MEAS_STATE_PURGING = 1
MEAS_STATE_SAMPLE_PREPARE = 2
MEAS_STATE_CONT_MEASURING = 3
MEAS_STATE_BATCH_MEASURING = 4

MeasStateName = {}
MeasStateName[MEAS_STATE_UNDEFINED] = "<MEASURING - UNDEFINED STATE!>"
MeasStateName[MEAS_STATE_PRESSURE_STAB] = "MEAS_PRESSURE_STAB"
MeasStateName[MEAS_STATE_PURGING] = "MEAS_PURGING"
MeasStateName[MEAS_STATE_SAMPLE_PREPARE] = "MEAS_SAMPLE_PREPARE"
MeasStateName[MEAS_STATE_CONT_MEASURING] = "MEAS_CONT_MEASURING"
MeasStateName[MEAS_STATE_BATCH_MEASURING] = "MEAS_BATCH_MEASURING"

# LockedStatus indexes
LASER_TEMP_LOCKED_STATUS         = 0
CAVITY_TEMP_LOCKED_STATUS        = 1
WARM_CHAMBER_TEMP_LOCKED_STATUS  = 2
PRESSURE_LOCKED_STATUS           = 3

EVENT_TEMP_LOCKED = 0
EVENT_PRESSURE_LOCKED = 1
EVENT_PURGING_COMPLETE = 2
EVENT_SAMPLE_PREPARE = 3
EVENT_START_INST = 4
EVENT_SHUTDOWN_INST = 5
EVENT_START_MEAS = 6
EVENT_STOP_MEAS = 7
EVENT_RESTART_INST = 8
EVENT_ABORT_INST = 9
EVENT_RESTART_DAS = 10
EVENT_MEAS_DONE = 11
EVENT_PARK = 12

# Maximum number of entries in error list
MAX_ERROR_LIST_NUM = 64

# including these error definitions will enable RPC calls to print out correct errors
class CommandError(Exception):
    """Root of all exceptions caused by a bad/inappropriate command."""
class InvalidModeSelection(Exception):
    """An invalid mode was selected."""

class DummySampleManager(object):
    def __init__(self):
        self.DriverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                            "DummySampleManager",
                                            IsDontCareConnection = False)
    def _SetMode(self, mode):
        Log("Running without Sample Manager - mode set skipped", Level = 0)
    def FlowStart(self):
        #self.pressureTarget = 140
        #self.DriverRpc.wrDasReg("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER", self.pressureTarget)
        #self.DriverRpc.wrDasReg("VALVE_CNTRL_STATE_REGISTER", interface.VALVE_CNTRL_OutletControlState)
        #start = self.DriverRpc.rdDasReg("VALVE_CNTRL_INLET_VALVE_MIN_REGISTER")
        #target = 18000
        #step = 500
        #iterations = int((target-start)/step)
        #self.inletTarget = start + iterations*step
        #interval = 2
        #maxPressureChange = 10
        #self._StepInletValve( start, step, iterations, interval, maxPressureChange)
        #self.DriverRpc.wrDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER", 18000)
        Log("Flow started by Dummy Sample Manager", Level = 0)
    def FlowStop(self):
        Log("Running with Dummy Sample Manager - flow stop skipped", Level = 0)
    def Prepare(self):
        Log("Running with Dummy Sample Manager - prepare skipped", Level = 0)
    def FlowPumpDisable(self):
        Log("Running with Dummy Sample Manager - flow pump disable skipped", Level = 0)
    def Park(self):
        Log("Running with Dummy Sample Manager - park skipped", Level = 0)
    def GetStatus(self):
        pass
        # Log("Running with Dummy Sample Manager - always returns pressure stable status", Level = 0)
        return SAMPLEMGR_STATUS_STABLE | SAMPLEMGR_STATUS_FLOWING
        #if abs(self.DriverRpc.rdDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER")-self.inletTarget) < 1 and abs(self.DriverRpc.getPressureReading()-self.pressureTarget) < 1:
        #    return SAMPLEMGR_STATUS_STABLE | SAMPLEMGR_STATUS_FLOWING
        #else:
        #    return SAMPLEMGR_STATUS_FLOWING
    def _StepInletValve( self, start, step, iterations, interval, maxPressureChange):
        index = 0
        value = start
        prevPressure = self.DriverRpc.getPressureReading()
        while index <= iterations:
            if self.DriverRpc.rdDasReg("VALVE_CNTRL_STATE_REGISTER") == interface.VALVE_CNTRL_OutletControlState:
                pressure = self.DriverRpc.getPressureReading()
                # check pressure, we do not want to harm cavity
                if abs(pressure-prevPressure) < maxPressureChange:
                    self.DriverRpc.wrDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER", value)
                    value += step
                    index+=1
                time.sleep(interval)
                prevPressure = pressure
            else:
                self.DriverRpc.wrDasReg("VALVE_CNTRL_STATE_REGISTER", interface.VALVE_CNTRL_OutletControlState)
                index = 0
                value = start
                prevPressure = self.DriverRpc.getPressureReading()

class ConfigurationOptions(object):
    def __init__(self):
        # - AutoEnableAfterBadShutdown is to avoid auto-measure after power failures
        self.AutoMeasure = False
        self.AutoStartEngine = False
        self.StartAppType = 0
        self.TempLockTimeout = 120  # 120 minutes
        self.PressureLockTimeout = 5 # 5 minutes
        self.AutoRestartFlow = True # Flow restarts automatically if valves are disabled
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
            tbMsg = traceback.format_exc()
            Log("Exception raised when calling exit function at exit of RPC server.",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = tbMsg)
class InstMgr(object):
    """This is the Instrument Manager application object."""
    def __init__(self, configPath, noSampleMgr=False):
        self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME,
                                                     IsDontCareConnection=False)
        self.noSampleMgr = noSampleMgr
        self.flowStarted = False
        self.State = INSTMGR_STATE_RESET
        self.powerOff = True
        self.terminateProtectedProcess = True
        self._SetupInstModeDispatcher()
        if __debug__: Log("Loading config options.")
        self.configPath = configPath
        self.Config = ConfigurationOptions()
        self.diableDataManager = False

        # Most of the internal vars are first defined in INSTR_Start
        # instead of in the constructor.  This can cause errors
        # or exceptions if restartCount or ErrorList is accessed
        # early.
        #
        # Hack here to prevent undefine attribute error if these are
        # accessed before the start/restart command is run.
        #
        self.restartCount = 0
        self.ErrorList = []

        if __debug__: Log("Setting up RPC connections.")
        #set up a connections to other apps
        self.DriverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                                    APP_NAME,
                                                    IsDontCareConnection = False)

        self.MeasSysRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM,
                                                     APP_NAME,
                                                     IsDontCareConnection = False)

        self.DataMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER,
                                                     APP_NAME,
                                                     IsDontCareConnection = False)

        self.FreqConvRpc  = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,
                                                     APP_NAME,
                                                     IsDontCareConnection = False)

        self.SpectrumCollectorRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,
                                                        APP_NAME,
                                                        IsDontCareConnection = False)

        self.SupervisorRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
                                                        APP_NAME,
                                                        IsDontCareConnection = False)

        if not self.noSampleMgr:
            self.SampleMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SAMPLE_MGR,
                                                            APP_NAME,
                                                            IsDontCareConnection = False)
        else:
            self.SampleMgrRpc = DummySampleManager()

        # used during error recovery
        self.rpcDict = {RPC_PORT_DATA_MANAGER:INST_ERROR_DATA_MANAGER_RESTART,
                        RPC_PORT_MEAS_SYSTEM:INST_ERROR_MEAS_SYS_RESTART,
                        RPC_PORT_DRIVER:INST_ERROR_DRIVER_RESTART}
        if not self.noSampleMgr:
            self.rpcDict[RPC_PORT_SAMPLE_MGR] = INST_ERROR_SAMPLE_MANAGER_RESTART

        if __debug__: Log("Setting up RPC server.")
        #Now set up the RPC server...
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_INSTR_MANAGER),
                                                ServerName = APP_NAME,
                                                ServerDescription = "The instrument manager.",
                                                ServerVersion = APP_VERSION,
                                                threaded = True)

        if __debug__: Log("Registering RPC functions.")
        #Register the rpc functions...
        self.RpcServer.register_function(self.INSTMGR_StartRpc)
        self.RpcServer.register_function(self.INSTMGR_ShutdownRpc)
        self.RpcServer.register_function(self.INSTMGR_StartMeasureRpc)
        self.RpcServer.register_function(self.INSTMGR_StopMeasureRpc)
        self.RpcServer.register_function(self.INSTMGR_StartSelfTestRpc)
        self.RpcServer.register_function(self.INSTMGR_StopSelfTestRpc)
        self.RpcServer.register_function(self.INSTMGR_GetErrorRpc)
        self.RpcServer.register_function(self.INSTMGR_ClearErrorRpc)
        self.RpcServer.register_function(self.INSTMGR_ReportErrorRpc)
        self.RpcServer.register_function(self.INSTMGR_ReportRestartRpc)
        self.RpcServer.register_function(self.INSTMGR_GetStatusRpc)
        self.RpcServer.register_function(self.INSTMGR_startFlowRpc)
        self.RpcServer.register_function(self.INSTMGR_stopFlowRpc)
        self.RpcServer.register_function(self.INSTMGR_disablePumpRpc)
        self.RpcServer.register_function(self.INSTMGR_simulateErrorRpc)
        self.RpcServer.register_function(self.INSTMGR_GetStateRpc)
        self.RpcServer.register_function(self.INSTMGR_SendDisplayMessageRpc)
        self.RpcServer.register_function(self.INSTMGR_SetInstrumentModeRpc)
        self.RpcServer.register_function(self.INSTMGR_EnableAutoRestartFlow)
        self.RpcServer.register_function(self.INSTMGR_DisableAutoRestartFlow)
        self.RpcServer.register_function(self.INSTMGR_ModifyAuxStatusRpc)

        if __debug__: Log("Setting up RPC callback functions.")
        # register callback functions
        self.AppStatus = AppStatus(0,STATUS_PORT_INST_MANAGER,APP_NAME)
        self.DisplayBroadcaster = Broadcaster.Broadcaster(BROADCAST_PORT_INSTMGR_DISPLAY)
    def _SendDisplayMessage(self, msg):
        try:
            Log(msg, Level = 0)
            formatString=">%ds" %(len(msg)+1)  #Initial format string: - '>' for big endian(labview GUI uses big endian byte order)
                                               #                       - +1 for null terminator
            # add null termination before broadcasting.
            self.DisplayBroadcaster.send(struct.pack(formatString, "%s\n" %msg))
        except:
            tbMsg = traceback.format_exc()
            Log("Exception occurred on Display message Broadcast",Data = dict(Note = "<See verbose for debug info>"),Level = 2,Verbose = tbMsg)
    def _SetStatus(self, bitMask):
        self.AppStatus._Status |= bitMask
        try:
            self.AppStatus._SendStatus()
        except:
            tbMsg = traceback.format_exc()
            Log("Exception occurred on Set Status Broadcast:", Data = dict(Note = "<See verbose for debug info>"),Level = 2,Verbose = tbMsg)
    def _ClearStatus(self, bitMask):
        self.AppStatus._Status &= ~bitMask
        try:
            self.AppStatus._SendStatus()
        except:
            tbMsg = traceback.format_exc()
            Log("Exception occurred on Clear Status Broadcast:",Data = dict(Note = "<See verbose for debug info>"),Level = 2,Verbose = tbMsg)
    def _HandleError(self, error):
        """ Handles error recovery scenarios.  DO NOT CALL from within _StateHandler to
            avoid recursion."""
        Log("Handling Error %s." % error_info[-error].name, Level = 2)

        errorRec = error_info[-error].errorRec
        Log("Error recovery action: %s" % errorActionDict[errorRec], Level = 2)
        if errorRec == CLEAR_ERROR:
            rpcPortNum = error_info[-error].rpcPortNum
            if rpcPortNum in self.rpcDict:
            # call appropriate clearError RPC
                self.rpcDict[rpcPortNum].Error_Clear()
        elif errorRec != DO_NOTHING :
            if errorRec == SHUTDOWN_INST:
                self._StateHandler(EVENT_SHUTDOWN_INST)
            elif errorRec == RESTART_INST:
                if self.restartCount < self.Config.InstRestartTimeout:
                    self.restartCount = self.restartCount + 1
                    self._StateHandler(EVENT_RESTART_INST)
                else:
                    self._StateHandler(EVENT_ABORT_INST)
            elif errorRec == RESTART_DAS:
                if self.dasRestartCount < self.Config.DasRestartTimeout:
                    self._StateHandler(EVENT_RESTART_DAS)
                    self.dasRestartCount = self.dasRestartCount + 1
                else:
                    self._StateHandler(EVENT_ABORT_INST)
            elif errorRec == RESTART_MEAS:
                if self.measRestartCount < self.Config.MeasRestartTimeout:
                    self._StateHandler(EVENT_STOP_MEAS)
                    self._StateHandler(EVENT_START_MEAS)
                    self.measRestartCount = self.measRestartCount + 1
                else:
                    self._StateHandler(EVENT_STOP_MEAS)

        # Add to error list
        if len(self.ErrorList) >= MAX_ERROR_LIST_NUM:
            # If list is full treat list like circular queue.  Delete older entry and add to the end.
            del self.ErrorList[0]

        # errorList consist of a list of tuples containing time, error number and error name
        timeStr = "%s" % ( time.strftime("%y/%m/%d %H:%M:%S.%S",time.localtime(time.time())))
        errorTuple = (timeStr, -error, error_info[-error].name)
        self.ErrorList.append(errorTuple)

        self._SetStatus(INSTMGR_STATUS_SYSTEM_ERROR)
    def _EnterWarming(self):
        """ called when entering warming state """
        self._SendDisplayMessage("Warming...")
        self.MeasSysRpc.Disable()
        self.DataMgrRpc.Disable()
        self.DriverRpc.stopScan()

        self.cavityTempLockCount = 0
        self.warmChamberTempLockCount = 0
        self._ClearStatus(INSTMGR_STATUS_READY)

        # make sure Meas Sys and Data manager apps are out of error state.
        try:
            clear1 = False
            stateDict = self.MeasSysRpc.GetStates()
            if stateDict['State_MeasSystem'] == 'ERROR':
                Log("Clearing MeasSys Error")
                self.MeasSysRpc.Error_Clear()
                clear1 = True

            clear2 = False
            stateDict = self.DataMgrRpc.GetState()
            if stateDict['State'] == 'ERROR':
                Log("Clearing DataManager Error")
                self.DataMgrRpc.Error_Clear()
                clear2 = True

            count = 0
            while(clear1 or clear2):
                stateDict = self.MeasSysRpc.GetStates()
                if stateDict['State_MeasSystem'] != 'ERROR':
                    clear1 = False

                stateDict = self.DataMgrRpc.GetState()
                if stateDict['State'] != 'ERROR':
                    clear2 = False
                count += 1
                if count >= 5:
                    if clear1:
                        tbMsg = traceback.format_exc()
                        Log("Failed to clear MeaSys",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
                        return INST_ERROR_MEAS_SYS
                    elif clear2:
                        tbMsg = traceback.format_exc()
                        Log("Failed to clear DataMgr",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
                        return INST_ERROR_DATA_MANAGER
                time.sleep(1)
        except:
            tbMsg = traceback.format_exc()
            Log("Clear error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_MEAS_SYS

        # Put the data manager into the warming mode
        try:
            self.DataMgrRpc.Mode_Set(self.Config.warmMode)
        except:
            tbMsg = traceback.format_exc()
            Log("DataMgr Set mode error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_DATA_MANAGER_RPC_FAILED

        # start DAS engine, i.e. laser current and laser, warm chamber and cavity temperature control
        try:
            status = self.DriverRpc.startTempControl()
            if status != INST_ERROR_OKAY:
                Log("Start Temp Control Failed %d" % status)
                return status
        except:
            tbMsg = traceback.format_exc()
            Log("Start temp control: error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_LASER_TEMP_CONTROL_ENABLE_FAILED

        try:
            status = self.DriverRpc.startLaserControl()
            if status != INST_ERROR_OKAY:
                Log("Start Laser Control Failed %d" % status)
                return status
        except:
            tbMsg = traceback.format_exc()
            Log("Start laser control: error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_LASER_I_CONTROL_ENABLE_FAILED

        self._SendDisplayMessage("Uploading warmbox cal to DAS...")
        status = self.FreqConvRpc.loadWarmBoxCal()
        if status != "OK":
            Log("Uploading warmbox cal failed %d" % status)
            return INST_ERROR_DAS_CAL_WRITE_FAILED

        try:
            self.SampleMgrRpc._SetMode(self.Config.sampleMgrMode)
        except:
            tbMsg = traceback.format_exc()
            Log("SampleMgr mode set: error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_SAMPLE_MGR_RPC_FAILED

        # go into warming state and wait for temperatures and pressure to stabilize.
        self.State = INSTMGR_STATE_WARMING
        self.WarmingState = WARMING_STATE_TEMP_STAB
        self.LockedStatus = [ "Unlocked", "Unlocked", "Unlocked", "Unlocked" ]
        self._SetStatus(INSTMGR_STATUS_WARMING_UP)
        self.MeasuringState = MEAS_STATE_PRESSURE_STAB
        self.LockedStatus[PRESSURE_LOCKED_STATUS] = "Unlocked"
        self._SendDisplayMessage("Temp and pressure stabilizing...")

        return INST_ERROR_OKAY

    def _EnterMeasure(self):
        """ called when entering measuring state """
        self._SendDisplayMessage("Preparing to measure")

        # Wait for up to 5s for the measurement system to get into READY or ENABLED state

        for waitTime in range(5):
            stateDict = self.MeasSysRpc.GetStates()
            if stateDict['State_MeasSystem'] in ['READY','ENABLED']:
                break
            time.sleep(1)
        else:
            Log("MeasSys fails to enter READY or ENABLED state in _EnterMeasure",Level=2)

        try:
            self.MeasSysRpc.Mode_Set(self.Config.measMode)
        except:
            tbMsg = traceback.format_exc()
            Log("MeasSys Set mode error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_MEAS_SYS_RPC_FAILED

        self.State = INSTMGR_STATE_MEASURING

        return INST_ERROR_OKAY
        #if self.Config.sampleMgrMode in ["ProportionalMode", "BatchMode"]:
        #    self.SampleMgrRpc.FlowStart()
        #    self.pressureLockCount = 0
        #    self.MeasuringState = MEAS_STATE_PRESSURE_STAB
        #    self._SetStatus(INSTMGR_STATUS_GAS_FLOWING)
        #    self._SendDisplayMessage("Pressure stabilizing...")
        #    self.LockedStatus[PRESSURE_LOCKED_STATUS] = "Unlocked"
        #    return INST_ERROR_OKAY
        #else:
        #    return INST_ERROR_INVALID_SAMPLE_MGR_MODE
    def _RestartMeasure(self):
        """ called when restarting measuring state """
        self._SendDisplayMessage("Restart Measuring")

        try:
            self.MeasSysRpc.Disable()
        except:
            tbMsg = traceback.format_exc()
            Log("MeasSys Disable error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_MEAS_SYS_RPC_FAILED

        try:
            self.DataMgrRpc.Disable()
        except:
            tbMsg = traceback.format_exc()
            Log("DataMgr Disable error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_DATA_MANAGER_RPC_FAILED

        #if self.Config.sampleMgrMode in ["ProportionalMode", "BatchMode"]:
        #    try:
        #        if not self.noSampleMgr: self.SampleMgrRpc.FlowStart()
        #    except:
        #        tbMsg = traceback.format_exc()
        #        Log("Start Flow: error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
        #        return INST_ERROR_SAMPLE_MGR_RPC_FAILED

            self.pressureLockCount = 0
            self.MeasuringState = MEAS_STATE_PRESSURE_STAB
        #    self._SetStatus(INSTMGR_STATUS_GAS_FLOWING)
            self._SendDisplayMessage("Pressure stabilizing...")
            self.LockedStatus[PRESSURE_LOCKED_STATUS] = "Unlocked"
            return INST_ERROR_OKAY
        else:
            return INST_ERROR_INVALID_MEAS_SYS_MODE
    def _ExitMeasure(self):
        """ called when exiting measuring state """
        self._SendDisplayMessage("Leaving Measuring")

        if self.diableDataManager:
            # Disable Data Manager
            try:
                self.DataMgrRpc.Disable(keepSyncScripts=True)
                self._SendDisplayMessage("Disabling Data Manager")
            except:
                tbMsg = traceback.format_exc()
                Log("DataMgr Disable error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
        else:
            # Put the data manager back into the warming mode
            try:
                self.DataMgrRpc.Mode_Set(self.Config.warmMode)
                self._SendDisplayMessage("Putting Data Manager in warming mode")
            except:
                tbMsg = traceback.format_exc()
                Log("DataMgr Set mode error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
                return INST_ERROR_DATA_MANAGER_RPC_FAILED

        try:
            self.SampleMgrRpc.FlowStop()
        except:
            tbMsg = traceback.format_exc()
            Log("Stop Flow: error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_SAMPLE_MGR_RPC_FAILED

        try:
            self.MeasSysRpc.Disable()
        except:
            tbMsg = traceback.format_exc()
            Log("MeasSys Disable error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_MEAS_SYS_RPC_FAILED

        self._ClearStatus(INSTMGR_STATUS_GAS_FLOWING | INSTMGR_STATUS_MEAS_ACTIVE)
        return INST_ERROR_OKAY

    def _StartMeasuring(self):
        """ called to start measuring """
        self._VerifyInstallerId()
        self._SendDisplayMessage("Measuring...")

        try:
            self.DataMgrRpc.Mode_Set(self.Config.measMode)
        except:
            tbMsg = traceback.format_exc()
            Log("DataMgr Set mode error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_DATA_MANAGER_RPC_FAILED

        try:
            self.MeasSysRpc.Enable()
        except:
            tbMsg = traceback.format_exc()
            Log("MeasSys Enable error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_MEAS_SYS_RPC_FAILED

        try:
            self.DataMgrRpc.Enable()
        except:
            tbMsg = traceback.format_exc()
            Log("DataMgr Enable error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_DATA_MANAGER_RPC_FAILED

        self.MeasuringState = MEAS_STATE_CONT_MEASURING
        self._SetStatus(INSTMGR_STATUS_MEAS_ACTIVE)

        self.restartCount = 0
        self.dasRestartCount = 0
        self.measRestartCount = 0
        return INST_ERROR_OKAY

    def _SamplePrepare(self):
        """ called to prepare sample """
        self._SendDisplayMessage("Preparing Sample")

        try:
            self.SampleMgrRpc.Prepare()
        except:
            tbMsg = traceback.format_exc()
            Log("SampleMgr Prepare: error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_SAMPLE_MGR_RPC_FAILED

        return INST_ERROR_INVALID_SAMPLE_MGR_MODE
    def _ResetSequence(self):
        """ perform reset sequence"""
        # Cannot turn off pump with G2000
        #try:
        #    self.SampleMgrRpc.FlowPumpDisable()
        #except:
        #    tbMsg = traceback.format_exc()
        #    Log("Sample Mgr Rpc: error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)

        try:
            self.MeasSysRpc.Disable()
        except:
            tbMsg = traceback.format_exc()
            Log("Disable Measure error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)

        try:
            self.DataMgrRpc.Disable()
        except:
            tbMsg = traceback.format_exc()
            Log("DataMgr Disable error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_DATA_MANAGER_RPC_FAILED

        Log("Analyzer operation halted",Level = 3)

        try:
            self.DriverRpc.hostReady('False')
        except:
            tbMsg = traceback.format_exc()
            Log("Host Ready failed ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
    def _Reset(self):
        """ called to reset instrument """
        self._SendDisplayMessage("Reset")

        self._ClearStatus(INSTMGR_STATUS_READY | INSTMGR_STATUS_GAS_FLOWING | INSTMGR_STATUS_PRESSURE_LOCKED | INSTMGR_STATUS_WARMING_UP | INSTMGR_STATUS_MEAS_ACTIVE | INSTMGR_STATUS_CAVITY_TEMP_LOCKED | INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED)

        self.State = INSTMGR_STATE_RESET
        self.LockedStatus = [ "Unlocked", "Unlocked", "Unlocked", "Unlocked" ]

        self._ResetSequence()

        return INST_ERROR_OKAY
    def _Abort(self):
        """ called to abort instrument """
        self._SendDisplayMessage("Aborted")

        self._ClearStatus(INSTMGR_STATUS_READY | INSTMGR_STATUS_GAS_FLOWING | INSTMGR_STATUS_PRESSURE_LOCKED | INSTMGR_STATUS_WARMING_UP | INSTMGR_STATUS_MEAS_ACTIVE | INSTMGR_STATUS_CAVITY_TEMP_LOCKED | INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED)
        self._SetStatus(INSTMGR_STATUS_SYSTEM_ERROR)

        self.State = INSTMGR_STATE_ERROR
        self.LockedStatus = [ "Unlocked", "Unlocked", "Unlocked", "Unlocked" ]

        self._ResetSequence()

        return INST_ERROR_OKAY
    def _Park(self):
        """ called when entering parking state """
        self._SendDisplayMessage("Parking")
        self.State = INSTMGR_STATE_PARKING

        # Disable auto restart flow in parking state
        self.INSTMGR_DisableAutoRestartFlow()

        try:
            status = self.SampleMgrRpc.Park()
            self._SendDisplayMessage("Parking Sample Manager")
        except:
            tbMsg = traceback.format_exc()
            Log("Park instrument: error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)

        return INST_ERROR_OKAY

    def _StateHandler(self, event):

        # if __debug__: Log("State Handler: event %d state %d" % (event, self.State))

        status = INST_ERROR_OKAY

        if event == EVENT_RESTART_INST:
            self.flowStarted = False
            status = self._EnterWarming()
        elif event == EVENT_RESTART_DAS:
            try:
                self.DriverRpc.resetDas()
            except:
                tbMsg = traceback.format_exc()
                Log("Reset DAS ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
                # expecting an exception since we're resetting the DAS
                pass

            self.State = INSTMGR_STATE_DAS_RESTART
        elif event == EVENT_SHUTDOWN_INST:
            status = self._Reset()
        elif event == EVENT_ABORT_INST:
            status = self._Abort()
        elif event == EVENT_PARK:
            status = self._Park()
        elif event == EVENT_START_INST:
            if self.State == INSTMGR_STATE_RESET or self.State == INSTMGR_STATE_ERROR:
                status = self._EnterWarming()
            else:
                status = INST_ERROR_INVALID_STATE
        elif event == EVENT_TEMP_LOCKED:
            if self.State == INSTMGR_STATE_WARMING and self.WarmingState == WARMING_STATE_TEMP_STAB:
                self._ClearStatus(INSTMGR_STATUS_SYSTEM_ERROR | INSTMGR_STATUS_WARMING_UP)
                self._SetStatus(INSTMGR_STATUS_READY)

                self.DriverRpc.hostReady('True')

                if self.Config.AutoMeasure == True:
                    status = self._EnterMeasure()
                else:
                    self.State = INSTMGR_STATE_READY
        elif event == EVENT_START_MEAS:
            if self.State == INSTMGR_STATE_READY:
                status = self._EnterMeasure()
            else:
                status = INST_ERROR_INVALID_STATE
        elif event == EVENT_STOP_MEAS:
            if self.State == INSTMGR_STATE_MEASURING:
                status = self._ExitMeasure()
                self.State = INSTMGR_STATE_READY
            else:
                status = INST_ERROR_INVALID_STATE
        elif event == EVENT_PRESSURE_LOCKED:
            if self.State == INSTMGR_STATE_MEASURING and self.MeasuringState == MEAS_STATE_PRESSURE_STAB:
                status = self._StartMeasuring()
        elif event == EVENT_PURGING_COMPLETE:
            if self.State == INSTMGR_STATE_MEASURING and self.MeasuringState == MEAS_STATE_PURGING:
                status = self._SamplePrepare()
        elif event == EVENT_SAMPLE_PREPARE:
            if self.State == INSTMGR_STATE_MEASURING and self.MeasuringState == MEAS_STATE_SAMPLE_PREPARE:
                status = self._StartMeasuring()
        elif event == EVENT_MEAS_DONE:
            if self.State == INSTMGR_STATE_MEASURING:
                if self.MeasuringState == MEAS_STATE_BATCH_MEASURING:
                    status = self._RestartMeasure()
                elif self.MeasuringState == MEAS_STATE_CONT_MEASURING:
                    status = INST_ERROR_OKAY
                else:
                    status = INST_ERROR_INVALID_STATE
                    raise Exception("Measuring State %d Doesn't Exist" % self.MeasuringState)
        else:
            status = INST_ERROR_INVALID_EVENT
            raise Exception("Instrument Event %d Doesn't Exist" % event)

        return status
    def _LoadConfigFile(self, configPath):
        if not FileExists(configPath):
            Log("Configuration file not found.", Data = dict(Path = configPath), Level = 2)
            raise Exception("File '%s' not found." % configPath)

        self.cp = CustomConfigObj(configPath)

        try:
            self.Config.AutoMeasure = self.cp.getboolean("DEFAULT", "AutoMeasure", False)
            self.Config.AutoStartEngine = self.cp.getboolean("DEFAULT", "AutoStartEngine", False)
            self.Config.AutoRestartFlow = self.cp.getboolean("DEFAULT", "AutoRestartFlow", True)
            self.Config.StartAppType = self.cp.get("DEFAULT", "StartingAppType", "")
            self.Config.TempLockTimeout = self.cp.getint("DEFAULT", "TempLockTimeout_min", 120)
            self.Config.PressureLockTimeout = self.cp.getint("DEFAULT", "PressureLockTimeout_min", 5)
            self.Config.InstRestartTimeout = self.cp.getint("DEFAULT", "InstRestartTimeout_iter", 3)
            self.Config.DasRestartTimeout = self.cp.getint("DEFAULT", "DasRestartTimeout_iter", 3)
            self.Config.MeasRestartTimeout = self.cp.getint("DEFAULT", "MeasRestartTimeout_iter", 3)
            self.Config.AppTypeList = self.cp.list_sections()

            if self.Config.StartAppType in self.Config.AppTypeList:
                self.Config.measMode = self.cp.get(self.Config.StartAppType,"MeasMode", "")
                self.Config.sampleMgrMode = self.cp.get(self.Config.StartAppType, "SampleMgrMode", "")
                self.Config.warmMode = self.cp.get(self.Config.StartAppType, "WarmMode", "")
            else:
                self.Config.measMode = ""
                self.Config.sampleMgrMode = ""
        except:
            tbMsg = traceback.format_exc()
            Log("LoadConfigFile failed, using default config",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            self.Config.AppTypeList = []

        if self.Config.measMode == "":
            raise Exception("App Type %d Doesn't Exist" % self.Config.StartAppType)

    def _VerifyInstallerId(self):
        (validInstallerId, analyzerType, installerId) = self.DriverRpc.verifyInstallerId()
        if not validInstallerId:
            Log("EEPROM ID (%s) does not match Software Installer ID (%s) - please correct EEPROM or re-install software" % (analyzerType,installerId),Level=3)
        elif analyzerType != None and installerId != None:
            Log("EEPROM ID matches Software Installer ID (%s)" % (analyzerType,),Level=1)

    def _Monitor(self):

        while True and self.MonitorShutdown == False:
            try:
                #if __debug__: Log("DAS Monitor: state=%s warmingState=%s measuring state=%s" % ( StateName[self.State], WarmingStateName[self.WarmingState], MeasStateName[self.MeasuringState]))
                lockStatus = self.DriverRpc.getLockStatus()
                dasState = self.DriverRpc.DAS_GetState(0)
                pressure = self.DriverRpc.getPressureReading()
                inletValve, outletValve = self.DriverRpc.getProportionalValves()

                if inletValve > 0 and outletValve > 0:
                    self._SetStatus(INSTMGR_STATUS_GAS_FLOWING)
                else:
                    self._ClearStatus(INSTMGR_STATUS_GAS_FLOWING)

                sampleMgrStatus = self.SampleMgrRpc.GetStatus()
                if (( sampleMgrStatus & SAMPLEMGR_STATUS_STABLE ) == SAMPLEMGR_STATUS_STABLE ):
                    pressureLocked = "Locked"
                else:
                    pressureLocked = "Unlocked"

                if (not self.flowStarted) or \
                   (self.Config.AutoRestartFlow and self.DriverRpc.rdDasReg("VALVE_CNTRL_STATE_REGISTER") == interface.VALVE_CNTRL_DisabledState):
                    if self.noSampleMgr:
                        pass
                    else:
                        self.MeasuringState = MEAS_STATE_PRESSURE_STAB
                        self.SampleMgrRpc.FlowStart()
                    self.flowStarted = True

            except Exception, e:
                Log("Das Monitor: error %s" % (e,),Level = 2)

                lockStatus = None
                resetCount = None
                dasState = None
                pressureLocked = None

            if self.State != INSTMGR_STATE_ERROR:
                if dasState != None:
                    if dasState == DASCNTRL_Error or dasState == DASCNTRL_Reset: #or dasState == DASCNTRL_DspNotBooted:
                    # DAS needs to be reset
                        self._HandleError(INST_ERROR_DAS_ERROR_OCCURRED)

            if (( self.State != INSTMGR_STATE_ERROR ) and ( self.State != INSTMGR_STATE_RESET )):
                if lockStatus != None:
                    if lockStatus["laserTempLockStatus"] != self.LockedStatus[LASER_TEMP_LOCKED_STATUS]:
                        self.LockedStatus[LASER_TEMP_LOCKED_STATUS] = lockStatus["laserTempLockStatus"]

                    if lockStatus["warmChamberTempLockStatus"] != self.LockedStatus[WARM_CHAMBER_TEMP_LOCKED_STATUS]:
                        self.LockedStatus[WARM_CHAMBER_TEMP_LOCKED_STATUS] = lockStatus["warmChamberTempLockStatus"]
                        if self.LockedStatus[WARM_CHAMBER_TEMP_LOCKED_STATUS] == "Locked":
                            self._SetStatus(INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED)
                            self._SendDisplayMessage("Temp locked:WB")
                        else:
                            self._ClearStatus(INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED)
                            self._SendDisplayMessage("Temp unlocked:WB")

                    if lockStatus["cavityTempLockStatus"] != self.LockedStatus[CAVITY_TEMP_LOCKED_STATUS]:
                        self.LockedStatus[CAVITY_TEMP_LOCKED_STATUS] = lockStatus["cavityTempLockStatus"]
                        if self.LockedStatus[CAVITY_TEMP_LOCKED_STATUS] == "Locked":
                            self._SetStatus(INSTMGR_STATUS_CAVITY_TEMP_LOCKED)
                            self._SendDisplayMessage("Temp locked:HB")
                        else:
                            self._ClearStatus(INSTMGR_STATUS_CAVITY_TEMP_LOCKED)
                            self._SendDisplayMessage("Temp unlocked:HB")

                if pressureLocked != None:
                    if pressureLocked != self.LockedStatus[PRESSURE_LOCKED_STATUS]:
                        self.LockedStatus[PRESSURE_LOCKED_STATUS] = pressureLocked
                        if self.LockedStatus[PRESSURE_LOCKED_STATUS] == "Locked":
                            self._SetStatus(INSTMGR_STATUS_PRESSURE_LOCKED)
                            self._SendDisplayMessage("Pressure locked")
                        else:
                            self._ClearStatus(INSTMGR_STATUS_PRESSURE_LOCKED)
                            self._SendDisplayMessage("Pressure unlocked")

                if self.State == INSTMGR_STATE_WARMING:
                    if self.LockedStatus[CAVITY_TEMP_LOCKED_STATUS] == "Locked" and self.LockedStatus[WARM_CHAMBER_TEMP_LOCKED_STATUS] == "Locked":
                        status = self._StateHandler(EVENT_TEMP_LOCKED)
                        if status != INST_ERROR_OKAY:
                            self._HandleError(status)

                if self.State == INSTMGR_STATE_WARMING or self.State == INSTMGR_STATE_READY or self.State == INSTMGR_STATE_MEASURING:
                    if self.LockedStatus[CAVITY_TEMP_LOCKED_STATUS] == "Locked":
                        self.cavitytempLockCount = 0
                    else:
                        self.cavityTempLockCount = self.cavityTempLockCount + 1
                        if self.cavityTempLockCount >= self.Config.TempLockTimeout*30: #DAS monitor runs every 2 seconds and TempLockTimeout config is in minutes
                            self._HandleError(INST_ERROR_TEMP_LOCK_TIMEOUT)

                    if self.LockedStatus[WARM_CHAMBER_TEMP_LOCKED_STATUS] == "Locked":
                        self.warmChambertempLockCount = 0
                    else:
                        self.warmChamberTempLockCount = self.warmChamberTempLockCount + 1
                        if self.warmChamberTempLockCount >= self.Config.TempLockTimeout*30: #DAS monitor runs every 2 seconds and TempLockTimeout config is in minutes
                            self._HandleError(INST_ERROR_TEMP_LOCK_TIMEOUT)

                if self.State == INSTMGR_STATE_MEASURING:
                    if self.LockedStatus[PRESSURE_LOCKED_STATUS] == "Locked":
                        self.pressureLockCount = 0
                        status = self._StateHandler(EVENT_PRESSURE_LOCKED)
                        if status != INST_ERROR_OKAY:
                            self._HandleError(status)
                    else:
                        self.pressureLockCount = self.pressureLockCount + 1
                        if self.pressureLockCount >= self.Config.PressureLockTimeout*30: #DAS monitor runs every 2 seconds and PressureLockTimeout config is in minutes
                            self._HandleError(INST_ERROR_PRESSURE_LOCK_TIMEOUT)

                    if self.MeasuringState == MEAS_STATE_PURGING:
                        if (( sampleMgrStatus & SAMPLEMGR_STATUS_PURGED ) == SAMPLEMGR_STATUS_PURGED ):
                            status = self._StateHandler(EVENT_PURGING_COMPLETE)
                    if self.MeasuringState == MEAS_STATE_SAMPLE_PREPARE:
                        if (( sampleMgrStatus & SAMPLEMGR_STATUS_PREPARED ) == SAMPLEMGR_STATUS_PREPARED ):
                            status = self._StateHandler(EVENT_SAMPLE_PREPARE)

                if self.State == INSTMGR_STATE_PARKING:
                    self._SendDisplayMessage("Pressure = %d Torr" % pressure)
                    if (( sampleMgrStatus & SAMPLEMGR_STATUS_PARKED ) == SAMPLEMGR_STATUS_PARKED ):
                        status = self._StateHandler(EVENT_SHUTDOWN_INST)
                        # ask supervisor to terminate all applications including INSTMGR
                        self.SupervisorRpc.TerminateApplications(self.powerOff, self.terminateProtectedProcess)

                if self.MeasuringState in [MEAS_STATE_CONT_MEASURING, MEAS_STATE_BATCH_MEASURING]:
                    try:
                        stateDict = self.MeasSysRpc.GetStates()
                        if stateDict['State_MeasSystem'] == 'READY':
                            self.MeasSysRpc.Enable()
                    except:
                        pass
                    try:
                        stateDict = self.DataMgrRpc.GetState()
                        if stateDict['State'] == 'READY' and not self.diableDataManager:
                            print "self.DataMgrRpc.Enable()"
                            self.DataMgrRpc.Enable()
                    except:
                        pass

            time.sleep(5)
    def _PurgingCompleteCallback(self):
        self._SendDisplayMessage("Purge complete")

        status = self._StateHandler(EVENT_PURGING_COMPLETE)
        if status != INST_ERROR_OKAY:
            self._HandleError(status)
    def _SamplePrepareCompleteCallback(self):
        self._SendDisplayMessage("Sample prepare complete")

        status = self._StateHandler(EVENT_SAMPLE_PREPARE)
        if status != INST_ERROR_OKAY:
            self._HandleError(status)
    def INSTMGR_Shutdown(self):
        self._SendDisplayMessage("Shutdown")

        status = self._StateHandler(EVENT_SHUTDOWN_INST)
    def INSTMGR_Start(self):
        self._SendDisplayMessage("Starting")
        self._LoadConfigFile(self.configPath)
        self.flowStarted = False
        self.restartCount = 0
        self.dasRestartCount = 0
        self.measRestartCount = 0
        self.LockedStatus = [ "Unlocked", "Unlocked", "Unlocked", "Unlocked" ]
        self._ClearStatus(INSTMGR_STATUS_CLEAR_MASK)
        self.ErrorList = []
        self.State = INSTMGR_STATE_RESET
        self.MeasuringState = MEAS_STATE_UNDEFINED
        self.WarmingState = WARMING_STATE_UNDEFINED
        self.InstrumentMode = {}
        self.cavityTempLockCount = 0
        self.warmChamberTempLockCount = 0
        self.pressureLockCount = 0

        try:
            self.version = self.DriverRpc.allVersions()["interface"]
        except:
            tbMsg = traceback.format_exc()
            Log("INSTMGR_Start:Interface Version Get error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            self.version = 0

        try:
            self.MeasSysRpc.Disable()
        except:
            tbMsg = traceback.format_exc()
            Log("Disable Measure error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)

        try:
            self.DataMgrRpc.StartInstMgrListener()
            self.DataMgrRpc.Disable()
        except:
            tbMsg = traceback.format_exc()
            Log("DataMgr Disable error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            return INST_ERROR_DATA_MANAGER_RPC_FAILED

        if self.Config.AutoStartEngine == True:
            status = self._EnterWarming()
            if status != INST_ERROR_OKAY:
                self._HandleError(status)
        else:
            status = self._Reset()

        #start the rpc server on another thread...
        self.RpcThread = RpcServerThread(self.RpcServer, self._RpcServerExit)
        self.RpcThread.start()

        self.MonitorShutdown = False

        # start DAS monitor. It monitors for errors and lock status changes
        self._Monitor()

    def INSTMGR_Start_virtualMode(self):
        self._SendDisplayMessage("Starting Instrument Manager in virtual mode")
        self._LoadConfigFile(self.configPath)
        self.flowStarted = False
        self.restartCount = 0
        self.dasRestartCount = 0
        self.measRestartCount = 0
        self.LockedStatus = [ "Unlocked", "Unlocked", "Unlocked", "Unlocked" ]
        self._ClearStatus(INSTMGR_STATUS_CLEAR_MASK)
        self.ErrorList = []
        self.State = INSTMGR_STATE_RESET
        self.MeasuringState = MEAS_STATE_UNDEFINED
        self.WarmingState = WARMING_STATE_UNDEFINED
        self.InstrumentMode = {}
        self.cavityTempLockCount = 0
        self.warmChamberTempLockCount = 0
        self.pressureLockCount = 0

        # settings for DataManager
        self.DataMgrRpc.StartInstMgrListener()
        self.DataMgrRpc.Mode_Set(self.Config.measMode)
        self.DataMgrRpc.Enable()
        # settings for RDFreqConverter
        self.FreqConvRpc.loadWarmBoxCal()

        #start the rpc server on another thread...
        self.RpcThread = RpcServerThread(self.RpcServer, self._RpcServerExit)
        self.RpcThread.start()

        self.MonitorShutdown = False

        while True and self.MonitorShutdown == False:
            # Keep sending "all is well" status in virtual mode
            self._SetStatus(0x3C3)
            time.sleep(5)

    def _GetInstrumentMode(self):
        return self.InstrumentMode

    def _RpcServerExit(self):
        self.MonitorShutdown = True
        self.RpcServer.stop_server()
    def INSTMGR_StartRpc(self):
        self.flowStarted = False
        self.restartCount = 0
        self.dasRestartCount = 0
        self.measRestartCount = 0
        status = self._StateHandler(EVENT_START_INST)
        if status != INST_ERROR_OKAY:
            self._HandleError(status)
            if status == INST_ERROR_INVALID_STATE or status == INST_ERROR_INVALID_EVENT:
                return INSTMGR_RPC_NOT_READY
            else:
                return INSTMGR_RPC_FAILED
        else:
            return INSTMGR_RPC_SUCCESS
    def INSTMGR_ShutdownRpc(self, shutdownType, shutdown=True):

        self.powerOff = True
        self.terminateProtectedProcess = True

        # stop measuring
        if shutdownType == INSTMGR_SHUTDOWN_PREP_SHIPMENT:
            self.diableDataManager = True
        else:
            self.diableDataManager = False
        status = self._StateHandler(EVENT_STOP_MEAS)

        # TODO ask EventMgr to archive logs.  Functionality doesn't exist in EventMgr yet.
        if shutdownType == INSTMGR_SHUTDOWN_PREP_SHIPMENT:
            # go into PARK State and wait for parking to complete before shutting down instrument
            # SupervisorRpc.TerminateApplications(True) is called within _Monitor once pressure is correct
            status = self._StateHandler(EVENT_PARK)
            self.powerOff = shutdown
            self.terminateProtectedProcess = shutdown
            if status == INST_ERROR_OKAY:
                return status
        elif shutdownType == INSTMGR_SHUTDOWN_HOST_AND_DAS:
            # shutdown Host
            status = self._StateHandler(EVENT_PARK)
            # shutdown Host only
            self.powerOff = False
            # turn off temperature control on DAS
            try:
                self.DriverRpc.stopTempControl()
            except:
                tbMsg = traceback.format_exc()
                Log("Stop temp control: error ",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            if status == INST_ERROR_OKAY:
                return status
        elif shutdownType == INSTMGR_SHUTDOWN_HOST:
            # shutdown Host only
            # Since the Driver is still running we assume the user doesn't want the computer
            # to power down.
            status = self._StateHandler(EVENT_SHUTDOWN_INST)
            self.powerOff = False
            self.terminateProtectedProcess = False

        # ask supervisor to terminate all applications including INSTMGR
        self.SupervisorRpc.TerminateApplications(self.powerOff, self.terminateProtectedProcess)

        if status != INST_ERROR_OKAY:
            self._HandleError(status)
            if status == INST_ERROR_INVALID_STATE or status == INST_ERROR_INVALID_EVENT:
                return INSTMGR_RPC_NOT_READY
            else:
                return INSTMGR_RPC_FAILED
        else:
            return INSTMGR_RPC_SUCCESS
    def INSTMGR_StartMeasureRpc(self):
        self.measRestartCount = 0
        status = self._StateHandler(EVENT_START_MEAS)
        if status != INST_ERROR_OKAY:
            self._HandleError(status)
            if status == INST_ERROR_INVALID_STATE or status == INST_ERROR_INVALID_EVENT:
                return INSTMGR_RPC_NOT_READY
            else:
                return INSTMGR_RPC_FAILED
        else:
            return INSTMGR_RPC_SUCCESS
    def INSTMGR_StopMeasureRpc(self):
        status = self._StateHandler(EVENT_STOP_MEAS)
        if status != INST_ERROR_OKAY:
            self._HandleError(status)
            if status == INST_ERROR_INVALID_STATE or status == INST_ERROR_INVALID_EVENT:
                return INSTMGR_RPC_NOT_READY
            else:
                return INSTMGR_RPC_FAILED
        else:
            return INSTMGR_RPC_SUCCESS
    def INSTMGR_startFlowRpc(self):
        status = self.SampleMgrRpc.FlowStart()
        if status == INST_ERROR_OKAY:
            self.flowStarted = True
            return INSTMGR_RPC_SUCCESS
        else:
            return INSTMGR_RPC_FAILED
    def INSTMGR_stopFlowRpc(self):
        status = self.SampleMgrRpc.FlowStop()
        if status == INST_ERROR_OKAY:
            self.flowStarted = False
            return INSTMGR_RPC_SUCCESS
        else:
            return INSTMGR_RPC_FAILED

    def INSTMGR_simulateErrorRpc(self,error):
        # Force instrument to handle the specified error
        return self._HandleError(error)

    def INSTMGR_disablePumpRpc(self):
        # No pump to be disabled in G2000
        return INSTMGR_RPC_SUCCESS
    def INSTMGR_StartSelfTestRpc(self, selfTestType):
        Log("self test not supported")
    def INSTMGR_StopSelfTestRpc(self, selfTestType):
        Log("self test not supported")
    def INSTMGR_ReportErrorRpc(self, error):
        if self.State == INSTMGR_STATE_PARKING:
            # Don't do anything when instrument is parking
            return INSTMGR_RPC_SUCCESS
        elif error < INST_ERROR_OKAY and error >= INST_ERROR_MAX:
            self._HandleError(error)
            self._SetStatus(INSTMGR_STATUS_ERROR_IN_BUFFER)
            return INSTMGR_RPC_SUCCESS
        elif error == INST_ERROR_OKAY:
            return INSTMGR_RPC_SUCCESS
        else:
            raise Exception("Invalid Error Code")
    def INSTMGR_ReportRestartRpc(self, portList):

        if __debug__:Log ("Restart Reported port=%s" %portList)

        restartPort = None
        for port in portList:
            if port in self.rpcDict:
                if restartPort == None:
                    restartPort = port
                else:
                    # more than one app is being restarted so perform multi app restart
                    self._HandleError(INST_ERROR_MULTI_APP_RESTART)
                    self._SetStatus(INSTMGR_STATUS_ERROR_IN_BUFFER)
                    return INSTMGR_RPC_SUCCESS

        if restartPort != None:
            self._HandleError(self.rpcDict[restartPort])
            self._SetStatus(INSTMGR_STATUS_ERROR_IN_BUFFER)

        return INSTMGR_RPC_SUCCESS
    def INSTMGR_GetErrorRpc(self, numErrors):
        listSize = len(self.ErrorList)
        if numErrors > listSize:
            numErrors = listSize

        # returns list of time, error code, error name tuple(s).
        return self.ErrorList[0:numErrors]
    def INSTMGR_ClearErrorRpc(self, numErrors):
        listSize = len(self.ErrorList)
        if numErrors > listSize:
            del self.ErrorList[0:listSize]
        else:
            del self.ErrorList[0:numErrors]

        if len(self.ErrorList) == 0:
            self._ClearStatus(INSTMGR_STATUS_ERROR_IN_BUFFER)

        return INSTMGR_RPC_SUCCESS
    def INSTMGR_ModifyAuxStatusRpc(self,auxStatus,auxStatusMask=0xFFFF):
        # Modify auxiliary status bits, which are the high-order 16 bits of
        #  the 32-bit status word. Only the bits specified in the mask are
        #  modified
        auxStatusMask &= 0xFFFF
        status = auxStatus & auxStatusMask
        self._ClearStatus(auxStatusMask << 16)
        self._SetStatus(status << 16)
        return INSTMGR_RPC_SUCCESS
    def INSTMGR_GetStatusRpc(self):
        return self.AppStatus._Status
    def INSTMGR_GetStateRpc(self):
        return {"InstMgr":StateName[self.State],
                "Warming":WarmingStateName[self.WarmingState],
                "Measuring":MeasStateName[self.MeasuringState]}
    def INSTMGR_SendDisplayMessageRpc(self, message):
        self._SendDisplayMessage(message)
        return INSTMGR_RPC_SUCCESS
    def INSTMGR_SetInstrumentModeRpc(self,modeDict):
        """Instrument modes are set up as a list of key=value pairs in the INSTRUMENT_MODE section of a measurement mode file.
        When a new measurement mode is started, these pairs are compared against a set of previously-cached values to see if
        any have changed. Those which have changed cause a function defined in InstModeDispatcher to be dispatched."""
        for key,value in modeDict.items():
            if key not in self.ValidInstrumentModes:
                raise KeyError("Unknown instrument mode key: %s" % (key,))
            if value not in self.ValidInstrumentModes[key]:
                raise ValueError("Unknown value for instrument mode: %s=%s" % (key,value))
        changedModes = self._FindChangedInstrumentModes(modeDict)
        # Do whatever actions are needed to effect the mode change
        for key in changedModes:
            self.InstModeDispatcher[key][changedModes[key]]()
        self.InstrumentMode.update(changedModes)

    def INSTMGR_EnableAutoRestartFlow(self):
        self.Config.AutoRestartFlow = True
        Log("Enabled auto-restart-flow")

    def INSTMGR_DisableAutoRestartFlow(self):
        self.Config.AutoRestartFlow = False
        Log("Disabled auto-restart-flow")

    def _FindChangedInstrumentModes(self,modeDict):
        changedModes = {}
        for key,value in modeDict.items():
            if key not in self.InstrumentMode or self.InstrumentMode[key] != value:
                changedModes[key]=value
        return changedModes

    def _SetInstMode_Tuning_CavityLength(self):
        self.FreqConvRpc.setCavityLengthTuning()

    def _SetInstMode_Tuning_LaserCurrent(self):
        self.FreqConvRpc.setLaserCurrentTuning()

    def _SetInstMode_Tuning_FsrHopping(self):
        self.FreqConvRpc.setFsrHoppingTuning()

    def _SetupInstModeDispatcher(self):
        self.InstModeDispatcher = {}
        self.InstModeDispatcher["Tuning"] = {}
        self.InstModeDispatcher["Tuning"]["CavityLength"] = self._SetInstMode_Tuning_CavityLength
        self.InstModeDispatcher["Tuning"]["LaserCurrent"] = self._SetInstMode_Tuning_LaserCurrent
        self.InstModeDispatcher["Tuning"]["FsrHopping"] = self._SetInstMode_Tuning_FsrHopping
        self.ValidInstrumentModes = {}
        for key,validModes in self.InstModeDispatcher.items():
            self.ValidInstrumentModes[key] = validModes.keys()

HELP_STRING = \
"""\
InstMgr.py [-h] [--no_sample_mgr] [-c<FILENAME>]

Where the options can be a combination of the following:
-h                  Print this help.
-c                  Specify a different config file.  Default = "./InstMgr.ini"
--no_sample_mgr     Run this application without Sample Manager.
--vi                Enter virtual mode that runs without analyser

"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    shortOpts = 'h'
    longOpts = ["no_sample_mgr", "help", "vi", "ini="]
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
    configFile = os.path.dirname(AppPath) + "/" + _DEFAULT_CONFIG_NAME

    if "--ini" in options:
        configFile = os.path.join(CONFIG_DIR, options["--ini"])
        Log ("Config file specified at command line: %s" % configFile)

    if "--no_sample_mgr" in options:
        noSampleMgr = True
    else:
        noSampleMgr = False

    if "--vi" in options:
        virtualMode = True
    else:
        virtualMode = False

    return (configFile, noSampleMgr, virtualMode)
def main():
    #Get and handle the command line options...
    configFile, noSampleMgr, virtualMode = HandleCommandSwitches()
    my_instance = SingleInstance(APP_NAME)
    if my_instance.alreadyrunning():
        Log("Instance of %s already running" % APP_NAME, Level=2)
    else:
        Log("%s started." % APP_NAME, Level=0)
        try:
            app = InstMgr(configFile, noSampleMgr)
            if virtualMode:
                app.INSTMGR_Start_virtualMode()
            else:
                app.INSTMGR_Start()
        except Exception, e:
            if __debug__:
                raise
            LogExc("Unhandled exception in %s: %s" % (APP_NAME, e), Level=3)
            # Request a restart from Supervisor via RPC call
            restart = RequestRestart(APP_NAME)
            if restart.requestRestart(APP_NAME) is True:
                Log("Restart request to supervisor sent", Level=0)
            else:
                Log("Restart request to supervisor not sent", Level=2)
        Log("Exiting program")


if __name__ == "__main__":
    main()
