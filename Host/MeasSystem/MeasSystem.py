#!/usr/bin/python
#
# File Name: MeasSystem.py
# Purpose:
#   This application is the "top level" measurement system.  All gas measurements
#   should be handled by this app.
#
#   When completed, this app should be the source for all gas measurements
#   (broadcasted as a stream to anyone who will listen, like the GUI, the
#   electrical interface, and the front panel).
#
# Notes:
#
# ToDo:
#
# File History:
# 06-09-13 russ  First release
# 06-09-15 russ  skip-fitting cmdline; cleaned up app shutdown; SpectrumTimeout_s in INI file
# 06-12-11 Al    Added INSTMGR_reportErrorRpc call when entering error state.
# 06-12-13 Al    Moved INSTMGR_reportErrorRpc call further down.
# 06-12-18 Al    Changed INSTMGR rpc to don't care.
# 06-12-19 russ  Integration with full HostCore (eg: InstMgr); Debug config settings; Removed
#                stabilizing state; SetWlmOffset and polar cal support; misc changes
# 06-12-20 russ  Fixed RPC_Mode_Set
# 06-12-21 russ  Parameterized RingdownTimeout_s (in ini file now)
# 07-01-26 sze   Added CalUpdatePeriod_s in ini file for updating active warm box calibration data
#                        Added GetWlmOffset RPC call, made it and SetWlmOffset compatible with polar and legacy systems
# 07-08-22 sze   Send binary data to archiver in wrapped format
# 07-09-26 sze   Support multiple fitter processes in a pool. Configuration keys FitterAddr0, FitterPort0, etc. are used
#                 to specify where the fitters are listening for data from the measurement system.
# 07-10-23 sze   When a mode change takes place, _SetupMeasMode() is called, which asks the instrument manager to make
#                 any required changes to the instrument mode
# 08-09-18  alex  Replaced SortedConfigParser with CustomConfigObj
# 08-10-13  alex  Replaced TCP in FitterPool by RPC
# 08-10-20  alex  Closed all client connection (_HandleState_INIT) before restarting the broadcaster in SpectrumManager
# 09-06-25  alex  Only "ArchiveFile", no more "ArchiveData" for spectrum data
# 09-10-16  alex  Work with new structure of cost-reduction platform

if __name__ != "__main__":
    raise Exception("%s is not importable!" % __file__)

APP_NAME = "MeasSystem"
APP_VERSION = 1.0
_DEFAULT_CONFIG_NAME = "MeasSystem.ini"
_MAIN_CONFIG_SECTION = "MainConfig"
_SCHEME_CONFIG_SECTION = "SCHEME_CONFIG"

import sys
import os.path
import getopt
import Queue
import profile
import time
import threading
import sets
from inspect import isclass

import FitterPool
from Host.Common import CmdFIFO
from Host.Common import ModeDef
from Host.Common import BetterTraceback
from Host.Common import AppStatus
from Host.Common.SharedTypes import CrdsException
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_INSTR_MANAGER, RPC_PORT_MEAS_SYSTEM, RPC_PORT_FITTER, RPC_PORT_SPECTRUM_COLLECTOR, RPC_PORT_FREQ_CONVERTER
from Host.Common.SharedTypes import BROADCAST_PORT_MEAS_SYSTEM
from Host.Common.SharedTypes import STATUS_PORT_MEAS_SYSTEM
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SafeFile import SafeFile, FileExists
from Host.Common.MeasData import MeasData  #For wrapping processor data packets up to send to the Data Manager
from Host.Common.Broadcaster import Broadcaster
from Host.Common.InstErrors import INST_ERROR_MEAS_SYS
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME, PrintEverything = __debug__)

if sys.platform == 'win32':
    threading._time = time.clock #prevents threading.Timer from getting screwed by local time changes
    
STATE__UNDEFINED = -100
STATE_ERROR = 0x0F
STATE_INIT = 0
STATE_READY = 1
STATE_ENABLED = 2
STATE_SHUTDOWN = 3

StateName = {}
StateName[STATE__UNDEFINED] = "<ERROR - UNDEFINED STATE!>"
StateName[STATE_ERROR] = "ERROR"
StateName[STATE_INIT] = "INIT"
StateName[STATE_READY] = "READY"
StateName[STATE_ENABLED] = "ENABLED"
StateName[STATE_SHUTDOWN] = "SHUTDOWN"

STATUS_MASK_WaitingForFitter   = 0x40
DEFAULT_FITTER_TIMEOUT_s = 300

####
## Some debugging/development helpers...
####
if __debug__:
    from pprint import pprint
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

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                     APP_NAME, IsDontCareConnection = False)

SpectrumCollector = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR, \
                                    APP_NAME, IsDontCareConnection = False)

FreqConverter = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,
                                     APP_NAME, IsDontCareConnection = False)
                                     
class MeasSystemError(CrdsException):
    """Base class for MeasSystem errors."""
class SpectrumTimeout(MeasSystemError):
    """Timeout period reached while waiting for a spectrum."""
class MeasurementDisabled(MeasSystemError):
    """The measurement was disabled in the middle of doing something."""
class InvalidModeSelection(MeasSystemError):
    """An invalid mode was selected."""
class ShutdownRequestCaptured(MeasSystemError):
    """An invalid mode was selected."""
class CommandError(MeasSystemError):
    """Root of all exceptions caused by a bad/inappropriate command."""
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
class MeasSystem(object):
    """Container class/structure for MeasSystem options."""
    class ConfigurationOptions(object):
        def __init__(self, SimMode = False):
            self.SimMode = SimMode
            self.SpectrumTimeout_s = 0
            self.ModeDefinitionFile = ""
            #Debugging settings (all off unless Debug option is set, in which case they get loaded)...
            self.StartEngine = False
            self.AutoEnableOnCleanStart = False
            self.StartingMeasMode = ""
            self.fitterIpAddressList = []
            self.fitterPortList = []
            
        def Load(self, IniPath):
            """Loads the configuration from the specified ini/config file."""
            cp = CustomConfigObj(IniPath) 
            
            basePath = os.path.split(IniPath)[0]

            if not self.SimMode:
                self.SpectrumTimeout_s = cp.getfloat(_MAIN_CONFIG_SECTION, "SpectrumTimeout_s")
            else:
                self.SpectrumTimeout_s = 0.0
            self.FitterTimeout_s = cp.getfloat(_MAIN_CONFIG_SECTION, "FitterTimeout_s", DEFAULT_FITTER_TIMEOUT_s)
            self.ModeDefinitionFile = os.path.join(basePath, cp.get(_MAIN_CONFIG_SECTION, "ModeDefinitionFile"))
            # Fetch the IP addresses and ports of the fitters in the pool
            nFitters = 0
            while cp.has_option(_MAIN_CONFIG_SECTION,"FitterAddr%d" % (nFitters,)) or \
                  cp.has_option(_MAIN_CONFIG_SECTION,"FitterPort%d" % (nFitters,)):
                self.fitterIpAddressList.append( \
                    cp.get(_MAIN_CONFIG_SECTION,"FitterAddr%d" % (nFitters,),"localhost"))
                self.fitterPortList.append( \
                    cp.getint(_MAIN_CONFIG_SECTION,"FitterPort%d" % (nFitters,),RPC_PORT_FITTER))
                nFitters += 1
            if nFitters == 0:
                self.fitterIpAddressList = [ "localhost" ]
                self.fitterPortList = [ RPC_PORT_FITTER ]

            self.Laser0TunerOffset = cp.getfloat(_MAIN_CONFIG_SECTION, "Laser0TunerOffset", default = 0.0)
            self.Laser1TunerOffset = cp.getfloat(_MAIN_CONFIG_SECTION, "Laser1TunerOffset", default = 0.0)

            self.StartEngine = cp.getboolean(_MAIN_CONFIG_SECTION, "StartEngine", "False")
            self.AutoEnableOnCleanStart = cp.getboolean(_MAIN_CONFIG_SECTION, "AutoEnableOnCleanStart", "False")
            self.StartingMeasMode = cp.get(_MAIN_CONFIG_SECTION, "StartingMeasMode", "")
    #endclass (ConfigurationOptions for MeasSystem)

    def __init__(self, ConfigPath, SkipFitting, noInstMgr = False, SimMode = False):
        # # # IMPORTANT # # #
        # THIS SHOULD ONLY CONTAIN VARIABLE/PROPERTY INITS... any actual code that
        # can fail (like talking to another CRDS app or reading the HDD) should be
        # in the INIT state handler.
        # # # # # # # # # # #
        self.__State = STATE_INIT
        self.__LastState = self.__State
        self._Status = AppStatus.AppStatus(STATE_INIT, STATUS_PORT_MEAS_SYSTEM, APP_NAME)
        self._EnableEvent = threading.Event()
        self._ClearErrorEvent = threading.Event()
        self._ShutdownRequested = False #The main state handling loop will exit when this is true
        self._FatalError = False  #The main state handling loop will also exit when this is true
        self._UninterruptedSpectrumCount = 0
        self.SkipFitting = SkipFitting

        #Measurement mode properties...
        # - Modes is a dict of MeasMode info indicating all the config info per mode
        self.MeasModes = {}
        self.CurrentMeasMode = None
        if 0: assert isinstance(self.CurrentMeasMode, ModeDef.MeasMode) #for wing


        self.ConfigPath = ConfigPath
        self.Config = MeasSystem.ConfigurationOptions(SimMode)
        self.Config.Load(self.ConfigPath)

        self.FitterPool = FitterPool.FitterPool(self.Config.fitterPortList,
                                                self.Config.fitterIpAddressList,
                                                self.Config.FitterTimeout_s)
        self.SpectrumQueue = Queue.Queue()

        #Set up the Broadcaster that will be used to send processor data to the Data Manager...
        self.ProcDataBroadcaster = Broadcaster(BROADCAST_PORT_MEAS_SYSTEM, APP_NAME, logFunc=Log)
        #Now set up the RPC server...
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_MEAS_SYSTEM),
                                                ServerName = "MeasSystem",
                                                ServerDescription = "The measurement system that coordinates gas measurements.",
                                                ServerVersion = APP_VERSION,
                                                threaded = True)

        self.RpcThread = None
        #Register the rpc functions...
        for s in dir(self):
            attr = self.__getattribute__(s)
            if callable(attr) and s.startswith("RPC_") and (not isclass(attr)):
                self.RpcServer.register_function(attr, NameSlice = 4)
        
        self.noInstMgr = noInstMgr
        if not self.noInstMgr:
            self.rdInstMgr = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER,
                                                        APP_NAME,
                                                        IsDontCareConnection = True)
                                                        
    def _AssertValidCallingState(self, StateList):
        if self.__State not in StateList:
            raise CommandError("Command invalid in present state ('%s')." % StateName[self.__State])
    def RPC_Enable(self):
        """Enables the measurement system in the mode set by Mode_Set.
        """
        try: #catch for DAS errors (and any other remote procedure call error)...
            if __debug__: Log("System Enable request received - RPC_Enable()", Level = 0)
            ##Validate that the call is possible and/or makes sense...
            self._AssertValidCallingState([STATE_INIT,        #Will try and enable when ready
                                           STATE_READY,       #Triggers transition to ENABLED
                                           STATE_ENABLED,     #No problem enabling again!
                                           ])
            if not self.CurrentMeasMode:
                raise CommandError("Cannot enable without setting a measurement mode first")

            ##React to the call...
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

    def RPC_Disable(self):
        """Disables the measurement system and stops the instrument from scanning.
        """
        if __debug__: Log("System DISable request received - RPC_Disable()", Level = 0)
        self._EnableEvent.clear()
        return "OK"

    def RPC_Shutdown(self):
        """Shuts down the measurement system.

        This has the same affect as stopping the RPC server.

        """
        self._EnableEvent.clear()
        self._ShutdownRequested = True

    def RPC_Mode_Set(self, ModeName):
        """Sets the measurement mode.

        This chooses a measurement plan based on the mode name.

        Mode changes are only valid when the instrument is not measuring.

        """
        self._AssertValidCallingState([STATE_READY,   
                                       STATE_ENABLED,
                                     ])
        if self.CurrentMeasMode and (ModeName == self.CurrentMeasMode.Name):
            return
        elif not ModeName in self.MeasModes.keys():
            raise InvalidModeSelection("An invalid mode was selected: '%s'" % ModeName)
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

    def RPC_SyncToPcClock(self):
        return Driver.resyncDas()

    def RPC_Backdoor__SetData(self, Name, Value):
        return SpectrumCollector.setTagalongData(Name, Value)

    def RPC_Backdoor__GetData(self, Name):
        return SpectrumCollector.getTagalongData(Name)

    def RPC_Backdoor__DeleteData(self, Name):
        return SpectrumCollector.deleteTagalongData(Name)

    def RPC_GetStates_Number(self):
        """Returns a dictionary with a numeric indication of the system states."""
        ret = dict(State_MeasSystem = self.__State)
        return ret

    def RPC_GetStates(self):
        """Returns a dictionary with a text indication of the system states."""
        ret = dict(State_MeasSystem = StateName[self.__State])
        return ret
        
    def RPC_GetSensorData(self):
        """Returns most recent sensor data from the DAS"""
        return SpectrumCollector.getSensorData()
        
    def _ChangeMode(self, ModeName):
        """Changes the measurement mode of the instrument."""
        self._UninterruptedSpectrumCount = 0
        self.CurrentMeasMode = self.MeasModes[ModeName]
        self._SetupMeasMode()
        
    def _SetupMeasMode(self):
        """Perform any instrument setup required for this mode by calling the instrument manager"""
        if not self.noInstMgr:
            modeDict = self.CurrentMeasMode._GetInstrumentMode()
            self.rdInstMgr.INSTMGR_SetInstrumentModeRpc(modeDict)
            Log("Setting instrument mode: %s" % (modeDict,))
        else:
            Log("Running without Instrument Manager - can't set mode in instrument")

    def _GetSpectrum(self):
        """Returns a measured spectrum, blocking for a timeout period until available.

        The timeout period is self._SpectrumTimeous_s.  If no spectrum is available
        after the timeout, SpectrumTimeout is raised.

        """
        spectrumGrabbed = False
        startTime = TimeStamp()
        while not spectrumGrabbed:
            try:
                spectrum = SpectrumCollector.getFromSpectrumQueue(timeout = 0.05)
                spectrumGrabbed = True
            except Queue.Empty, data:
                if self._ShutdownRequested:
                    raise ShutdownRequestCaptured
                    
                if not self._EnableEvent.isSet():
                    raise MeasurementDisabled
                    
                if (self.Config.SpectrumTimeout_s != 0) and ((TimeStamp() - startTime) > self.Config.SpectrumTimeout_s):
                    # SpectrumTimeout_s=0 means no time-out requirement is given
                    raise SpectrumTimeout, data
        return spectrum
        
    def _SendSpectrumToFitter(self, Spectrum):
        self._Status.UpdateStatusBit(STATUS_MASK_WaitingForFitter, True)
        if self._UninterruptedSpectrumCount == 0:
            ret = self.FitterPool.Init()
        fitResults = self.FitterPool.FitData(Spectrum.copy())
        self._Status.UpdateStatusBit(STATUS_MASK_WaitingForFitter, False)
        return fitResults
    def _SendSpectrumToCalMgr(self, Spectrum):
        Log("REQUEST RECEIVED TO SEND SPECTRUM TO CAL MANAGER (UNIMPLEMENTED)", Level = 0)
        calResults = {}
        return calResults
    def _SendProcessorResultsForAnalysis(self, MeasTime_s, ResultLabelDict):
        """Sends the provided results to the Data Manager for analysis.

        ResultLabelDict must be a dict of dicts.
          - keys of the main dict are the result labels to be passed upwards
          - values are dicts, where the dict is a set of token value pairs (the data)

        """
        for resultLabel in ResultLabelDict.keys():
            dataPacket = MeasData(resultLabel, MeasTime_s, ResultLabelDict[resultLabel])
            txMsg = dataPacket.dumps()
            self.ProcDataBroadcaster.send(txMsg)
    def _ProcessFitResults(self, FitResults):
        """
        """
        pass
        #"%% Fit results would be processed here!"
    def __SetState(self, NewState):
        """Sets the state of the MeasSystem.  Variable init is done as appropriate."""
        if NewState == self.__State:
            return

        if __debug__: #code helper - make sure state changes are happening only from where we expect
            callerName = sys._getframe(1).f_code.co_name
            if not callerName.startswith("_HandleState_"):
                raise Exception("Code error!  State changes should only be made/managed in _MainLoop!!  Change attempt made from %s." % callerName)

        #Do any state initialization that is needed...
        if NewState == STATE_READY:
            pass
        elif NewState == STATE_ENABLED:
            self._UninterruptedSpectrumCount = 0
        elif NewState == STATE_ERROR:
            self._EnableEvent.clear()
            self._ClearErrorEvent.clear()

        #and now actually change the state variable and log the change...
        self.__LastState = self.__State
        self.__State = NewState
        if NewState == STATE_ERROR:
            eventLevel = 3
            if not self.noInstMgr:
                self.rdInstMgr.INSTMGR_ReportErrorRpc(INST_ERROR_MEAS_SYS)
        else:
            eventLevel = 1
        self._Status.UpdateState(self.__State)
        Log("State changed",
            dict(State = StateName[NewState],
                 PreviousState = StateName[self.__LastState]),
            Level = eventLevel)
    def _HandleState_INIT(self):
        try:
            ##Load the main application configuration settings...
            self.Config.Load(self.ConfigPath)

            ##Figure out what modes are available and load all details...
            self.MeasModes = ModeDef.LoadModeDefinitions(self.Config.ModeDefinitionFile)
            Log("Mode definitions loaded", dict(ModeNames = self.MeasModes.keys()))

            ##Figure out the unique set of schemes to give to the SchemeManager...
            allSchemes = []
            for m in self.MeasModes.values():
                allSchemes.extend(m.Schemes)
            uniqueSchemes = list(sets.Set(allSchemes))
            uniqueSchemes.sort()
            #now want to assign the schemes to indexes in the DAS
            # - should make a dict with keys = scheme names, values = DAS index
            # - need to make sure that all have backups and the count does not exceed what is available
            #The management scheme is:
            # - DAS table indices 0-6 are the primary slots
            # - DAS table indices 7-13 are the alternate slots
            # - DAS table indices 14 & 15 are for asap schemes
            #This scheme is hard-coded right now.. had plans to make it configurable
            #(and had a big INI file for it), but no real point right now (and I lost
            #the INI file!)
            if len(uniqueSchemes) > 7:
                raise Exception("Too many unique schemes identified in the modes!  Only 7 supported right now.")
            schemeDict = {}
            schemeSeq = []
            for i in range(len(uniqueSchemes)):
                #this will build up the scheme set with keys based on the full path to the initial scheme...
                schemeDict[uniqueSchemes[i]] = (uniqueSchemes[i], i, i + 7)
                schemeSeq.append(uniqueSchemes[i])
            #After sending this schemeSet to the SchemeManager in RDFrequencyConverter, schemes can simply be referred to by their names...
            FreqConverter.configSchemeManager(schemeDict, schemeSeq)
            
            # Set up spectrum queue in Spectrum Collector
            SpectrumCollector.setMaxSpectrumQueueSize(40)

            # See if the fitter is running (if not the exception will be picked up below)...
            if not self.SkipFitting:
                self.FitterPool.Ping()
            # Set the fitter proxy up to be interruptable while waiting for a long fit...
            self.FitterPool.SetEnableEvent(self._EnableEvent)

            # Deal with startup configuration options...
            if self.Config.StartEngine:
                Log("Engine started (with Driver.startEngine) due to 'StartEngine' startup config setting.")
                Driver.startEngine()
            if self.Config.AutoEnableOnCleanStart:
                Log("EnableEvent set due to 'AutoEnableOnCleanStart' startup config setting.")
                #Set it up to automatically start...
                self._EnableEvent.set()
                
            # Set laser tuner parameters
            try:
                Driver.wrDasReg("FPGA_TUNER_LASER0_OFFSET_REGISTER", self.Config.Laser0TunerOffset)
                Driver.wrDasReg("FPGA_TUNER_LASER1_OFFSET_REGISTER", self.Config.Laser1TunerOffset)
            except:
                pass

            # Set up the starting measurement mode (if defined... normally we wait to be told in ready state)
            if self.Config.StartingMeasMode:
                self._ChangeMode(self.Config.StartingMeasMode)
                Log("Startup measurement mode name initialized", dict(Name = self.Config.StartingMeasMode))

            self.__SetState(STATE_READY)
        except:
            LogExc(Data = dict(State = StateName[self.__State]))
            self.__SetState(STATE_ERROR)
            #self._FatalError = True
    def _HandleState_READY(self):
        try:
            exitState = STATE__UNDEFINED
            self._EnableEvent.wait(0.05)
            if self._EnableEvent.isSet():
                if not self.CurrentMeasMode:
                    raise MeasSystemError("No measurement mode set - Can't enable the measurement system!")
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
        #TODO: Keep running track of the number of pending spectra that need to be sent
        #TODO: Do not let spectral count accumulate
        exitState = STATE__UNDEFINED
        try:
            if (not self._EnableEvent.isSet()) or self._ShutdownRequested:
                exitState = STATE_READY
            else:
                if self._UninterruptedSpectrumCount == 0:
                    Driver.startScan()
                spectrum = None
                try:
                    #Get the spectrum...
                    spectrum = self._GetSpectrum()
                    if spectrum["controlData"]["RDDataSize"] >= 1:
                        spectrumName = self.CurrentMeasMode.SpectrumIdLookup[spectrum["sensorData"]["SpectrumID"]]
                        # Run it through the processors that have been set up for the spectrum...
                        # For each processor, processorResults consist of a list of tuples [(time1,ResultDict1),(time2,ResultDict2)...]
                        # The results from all the processors are sorted into time order and broadcast. If times from two processors
                        #  coincide, the resulting dictionaries are merged.

                        # allResults is keyed first by time, second by ResultDataLabel
                        allResults = {}
                        for p in self.CurrentMeasMode.Processors[spectrumName]: #ONLY ONE PROCESSOR TYPE NOW (FITTER), BUT LEAVING CODE IN PLACE
                            assert isinstance(p, ModeDef.ProcessorInfo)
                            if p.ProcessorType == ModeDef.PROCESSOR_TYPE_FITTER and not self.SkipFitting:
                                processorResults = self._SendSpectrumToFitter(spectrum)
                            elif p.ProcessorType == ModeDef.PROCESSOR_TYPE_CALMGR:
                                #NOT IMPLEMENTED
                                processorResults = self._SendSpectrumToCalMgr(spectrum)
                            #endif
                            # Update allResults with the output of the processor
                            for t,rDict in processorResults:
                                if t in allResults:
                                    if p.ResultDataLabel in allResults[t]:
                                        allResults[t][p.ResultDataLabel].update(rDict)
                                    else:
                                        allResults[t][p.ResultDataLabel] = rDict.copy()
                                else:
                                    allResults[t] = { p.ResultDataLabel:rDict.copy() }
                        #endfor
                        for t in sorted(allResults.keys()):
                            self._SendProcessorResultsForAnalysis(t, allResults[t])

                        self._UninterruptedSpectrumCount += 1
                    else:
                        print "Empty spectrum retrieved."
                        Log("Empty spectrum retrieved.", Level = 0)
                    exitState = STATE_ENABLED
                    #print "SIZE = ", self.RdQueue.qsize()
                except (ShutdownRequestCaptured,
                        MeasurementDisabled,
                        FitterPool.FitterInterrupted):
                    if __debug__:
                        Log("User requested shutdown while handling ENABLED state.", Level = 0)
                    exitState = STATE_READY
                except SpectrumTimeout:
                    #No handling right now if we don't get data when we expect it...
                    LogExc("Timed out while waiting for a completed spectrum to appear in the queue")
                    exitState = STATE_ERROR
                except FitterPool.FitterTimeout:
                    LogExc("Timed out while waiting for fitter to finish/respond")
                    exitState = STATE_ERROR
                except FitterPool.FitterError:
                    LogExc("Error occured during fitting")
                    exitState = STATE_ERROR
        except:
            LogExc(Data = dict(State = StateName[self.__State]))
            exitState = STATE_ERROR
            self.__SetState(STATE_ERROR)
        #endtry
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
            stateHandler[self.__State]()
        #end while

        ##Any shutdown handling should go here...
        #Shut the rpc server down...
        self.RpcServer.stop_server()
        wait_s = 2
        self.RpcThread.join(wait_s)
        if self.RpcThread.isAlive():
            Log("Timed out while waiting for RpcServerThread to close.  Terminating rudely!",
                Data = dict(WaitTime_s = wait_s),
                Level = 2)

        if self._FatalError:
            Log("MeasSystem terminated due to a fatal error.", Level = 3)
        else:
            Log("MeasSystem exited due to shutdown request.", Level = 2)

    def Start(self):
        self._MainLoop()

HELP_STRING = \
"""\
MeasSystem.py [-h] [--no_fitter] [--no_inst_mgr] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file.  Default = "./MeasSystem.ini"

--no_fitter    Will suppress all fitter transactions.
--no_inst_mgr  Run this application without Instrument Manager.
"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    shortOpts = 'hsc:'
    longOpts = ["help", "test", "no_fitter", "no_inst_mgr", "simulation"]
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
    noFitter = False
    noInstMgr = False
    simMode = False
    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()
    else:
        if "--test" in options:
            executeTest = True
        if "--no_fitter" in options:
            noFitter = True
        if "--no_inst_mgr" in options:
            noInstMgr = True
        if "-s" in options or "--simulation" in options:
            simMode = True
            
    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + _DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
        Log("Config file specified at command line", configFile)
        
    return (configFile, executeTest, noFitter, noInstMgr, simMode)
    
def ExecuteTest(MS):
    """A self test executed via the --test command-line switch."""
    assert isinstance(MS, MeasSystem)
    MS.RPC_Backdoor__SetScheme(r"C:\Code\PicarroVSS\SilverStone\_HostCore\MeasSystem\Schemes\H2S.sch")
    MS.RPC_Enable()
    print "MS enabled!!!"
    #MS.Disable()
    
def main():
    #Get and handle the command line options...
    configFile, test, noFitter, noInstMgr, simMode = HandleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    try:
        app = MeasSystem(configFile, noFitter, noInstMgr, simMode)
        if test:
            threading.Timer(2, ExecuteTest(app)).start()
        app.Start()
    except:
        if __debug__: raise
        LogExc("Exception trapped outside MeasSystem execution")

if __name__ == "__main__":
    try:
        #profile.run("main()","c:/temp/measSystemProfile")
        main()
    except:
        tbMsg = BetterTraceback.get_advanced_traceback()
        Log("Unhandled exception trapped by last chance handler",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = tbMsg)
    Log("Exiting program")
    sys.stdout.flush()
