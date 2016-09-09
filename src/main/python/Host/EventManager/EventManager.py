#!/usr/bin/python
#
"""
File Name: EventManager.py
Purpose:
    This application serves as the single location to log events for all
    applications.
    It will also be a general event manager for managing intra-application
    events for the instrument, but this is not completed yet.

File History:
    06-02-18 russ  First release
    06-05-09 russ  Added AccessLevel instead of Public; Event Data can now be any type (dict recommended)
    06-10-26 russ  Added INI file; Events logged to file (with archiving); Limit on event log length in RAM
    08-04-04 sze   Added Linux compatibility
    08-09-18 alex  Replaced ConfigParser with CustomConfigObj
    09-01-14 sze   Reduced number of threads needed to clear lurking files
    10-01-22 sze   Changed date format display to ISO standard
    11-01-26 alex  Use GMT for event logs and local time for broadcasting

Notes:
    There is an optional GUI that can be launched via command-line or via an
    RPC call.  The GUI takes no memory when not in use.
    This replaces the simple Logger.py that existed before.

    Event properties...
    ---
    Index (Time alone may get confusing in case of DST)
    LogTime (time at which the logger received the log)
    SourceTime (time at which the log was sent - comes from the source)
    Code
    EventText
    VerboseDescription (default to "" and optional)
    Source (eg: Driver, Filer, etc)
    Level
      - 3 = Causes a performance hit or crash (eg: top level exception trap, app restarted)
      - 2 = Significant (eg: Conc Alarm occurred, Flow stopped, etc)
      - 1 = info only; used to help with post-mortems (eg: Command received)
      - 0 = debug (ONLY for msg's that would be spam - only send if debugging)
    AccessLevel (default = picarro only)

    RPC calls
    ---
    LogEvent
    RegisterEvents
      -Preregister events to cut down on perpetual traffic - also allows more verbose descriptions
    LogEventNum

    Usage
    ---
    LogEvent("Something happened", 1)
    RegisterEvent(Source, Num, EventText, VerboseDesc, AccessLevel)
    LogEventNum(Source, Num)

    Code notes
    ---
    The fundamental creation of all log entries occurs in EventLogger._CreateEventLog
    The fundamental collection of all logs (and display) occurs in EventLogger._AddEventLog

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "EventManager"
DEFAULT_EVENT_CODE = 0
_DEFAULT_CONFIG_NAME = "EventManager.ini"
_MAIN_CONFIG_SECTION = "MainConfig"
LOGFILE_PREFIX = "EventLog_"
LOGFILE_EXTENSION = "txt"

import sys
import os
import threading
import time
from glob import glob

from Host.Common import SharedTypes #to get the right TCP port to use
from Host.Common import CmdFIFO
from Host.Common import Broadcaster
from Host.Common.CustomConfigObj import CustomConfigObj

if sys.platform == 'win32':
    TimeStamp = time.clock
else:
    TimeStamp = time.time

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

CRDS_Archiver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_ARCHIVER,
                                            APP_NAME,
                                            IsDontCareConnection = True)

print("Loading rpdb2")
import rpdb2
rpdb2.start_embedded_debugger("hostdbg",timeout=0)
print("rpdb2 loaded")

class EventInfo(object):
    """The general class object for identifying event types - NOT discrete events.

    Discrete events (with time and other instance data) are captured with the
    EventLog class.

      Description = The text description of the event (eg: 'Application started')
      Level       = The severity of the event (from 0-3).  See below.
                      3 = Causes a performance hit or crash (eg: top level
                          exception trap, app restarted)
                      2 = Significant (eg: Conc Alarm occurred, Flow stopped, etc)
                      1 = info only; used to help with post-mortems (eg: Command
                          received)
                      0 = debug. ONLY for msg's that would normally be spam - only
                          send if debugging.  Please wrap with 'if __debug__'
      Code        = Numeric code for the event.  Should be unique across apps.
                      - A value of -1 is default and generic
      AccessLevel = Who should be able to see the event.
                       0 = Public... anyone can see
                       1 = Access level 1 (service tech?)
                     100 = Picarro only (the default)
                    eg: "Pump disabled" would be public
      VerboseDesc = A nice lengthy explanation of a pre-defined event.  This
                    should really not be used for one-time-only message events
                    that are created.
    """
    def __init__(self, Description, Data = "", Level = 1, Code = 0, AccessLevel = SharedTypes.ACCESS_PICARRO_ONLY,
                 VerboseDesc = ""):
        self.Description = Description
        self.Level = Level
        self.Code = Code      #Numeric code for the eventr.  Should be
        self.AccessLevel = AccessLevel  #
        self.VerboseDescription = VerboseDesc
        if self.AccessLevel < SharedTypes.ACCESS_PICARRO_ONLY:
            self.Public = True
        else:
            self.Public = False

    def __str__(self):
        if self.Code == 0:
            codeStr = "n/a"
        else:
            codeStr = str(self.Code)
        ret = "L%s | C%s | '%s'" % (self.Level, codeStr, self.Description)
        return ret

class EventLog(object):
    """Adds additional info required to record an occurrence of a single event.

    The actual event information is in the contained Event member (type EventInfo).

    Full events can be created on the fly by defining the event with all of the
    constructor args of this class (avoid using verbose if possible).

    To record an event of a pre-defined type (EventInfo instance), pass in the
    instance as the Description argument.

    Special EventLog properties over and above EventInfo are:

      Index     = The log entry # (starting at 1)
      Source    = Which application logged the event
      EventTime = The best guess at when the event occured. Options for this are
                  (in order of preference):
                      1. The client who requested the log sent a time
                      2. The time at which the RPC server dispatcher received
                         the log request
                      3. The LogTime (see below)
      LogTime   = The time at which the log entry is actually made.
      Data      = Data for the particular event occurrence.  eg: an event type
                  of 'Application started' might have data of 'CustomerGUI'. This
                  can be any data type, but a dict is recommended.

    There can be some lag between EventTime and LogTime (eg: if the logger is
    archiving, or if it is slow due to lower priority), and this is stored as
    the _LogLag attribute.

    NOTE: a nice thing is that no matter what the time stamps are, the rpc
    server implementation (and tcp queue) always ensures that events are
    serialized in order of receipt.

    The reason that EventLogger does not derive from EventInfo (which originally
    made sense) is to allow arbitrary pre-definition of event types.  Making
    EventInfo a member makse this easy.
    """

    InstanceCounter = 0 #for counting an index for all instances
    def __init__(self, Source,
                 Description = None,
                 Data = "",
                 Level = 1,
                 Code = DEFAULT_EVENT_CODE,
                 AccessLevel = SharedTypes.ACCESS_PICARRO_ONLY,
                 VerboseDescription = "",
                 EventTime = 0):
        EventLog.InstanceCounter += 1
        self.Index = self.InstanceCounter
        self.Data = Data
        self.Source = Source
        self.LogTime = time.time() #time at which the logger received the event
        #self.Time = SourceTime or time.time()
        self.EventTime = EventTime or self.LogTime #best guess at the event time
        self._LogLag = self.LogTime - self.EventTime

        if isinstance(Description, EventInfo):
            self.Event = Description
        else:
            #Should be a string, but if not we're going to interpret it as a string...
            self.Event = EventInfo(str(Description), Level = Level, Data = Data, Code = Code, AccessLevel = AccessLevel, VerboseDesc = VerboseDescription)

        assert isinstance(self.Event, EventInfo) #for Wing

    def __str__(self):
        timeStr = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.EventTime))
        ret = "%4s | %s | %-10s | %s" % (self.Index, timeStr, self.Source, self.Event)
        if self.Data:
            ret += ": %s" % (self.Data)
        return ret

class EventLogFile(object):
    """Class to manage writing (and reading) of event logs to disk."""
    #TODO: Implement reading
    FORMAT_VERSION = 1
    def __init__(self, LogDir, TimeStandard="gmt"):
        self.NumWrittenEvents = 0
        self.LogDir = LogDir
        self.LogPath = ""
        self.TimeStandard = TimeStandard
        if self.TimeStandard.lower() == "local":
            self.maketimetuple = time.localtime
        else:
            self.maketimetuple = time.gmtime

    def _CreateNewLogFilePath(self):
        """Creates a new log file named with the current time stamp and with a version header."""
        if self.TimeStandard.lower() == "local":
            timeStr = time.strftime("%Y_%m_%d_%H_%M_%S",self.maketimetuple())
        else:
            timeStr = time.strftime("%Y_%m_%d_%H_%M_%SZ",self.maketimetuple())

        fname = "%s%s.%s" % (LOGFILE_PREFIX,
                             timeStr,
                             LOGFILE_EXTENSION)
        self.LogPath = os.path.join(self.LogDir, fname)
        fp = file(self.LogPath, "w")
        fp.write("v%s\n" % self.FORMAT_VERSION)
        fp.close()

    def WriteEvent(self, AnEventLog):
        """Writes a string representation of the provided event log to disk."""
        assert isinstance(AnEventLog, EventLog)
        el = AnEventLog #character saver
        timeStr = time.strftime("%Y-%m-%d %H:%M:%S",self.maketimetuple(el.EventTime))
        summaryLine = "%s\t%s\t%s\tL%s\tC%s\t%s" % (el.Index,
                                                    timeStr,
                                                    el.Source,
                                                    el.Event.Level,
                                                    el.Event.Code,
                                                    el.Event.Description)
        if el.Data:
            summaryLine += " : %s" % (el.Data,)

        if not self.LogPath:
            self._CreateNewLogFilePath()
        fp = file(self.LogPath, "a")
        fp.write("%s\n" % summaryLine)
        if el.Event.VerboseDescription:
            verboseList = el.Event.VerboseDescription.splitlines()
            #print "verboseList = %r" % verboseList
            fp.write("~~ VERBOSE ~~ (%s)\n" % len(verboseList))
            for line in verboseList:
                fp.write("%s\n" % line) #Doing this rather than writelines and keepends to ensure terminating \n
            fp.write("~~ END VERBOSE ~~\n")
        fp.close()
        self.NumWrittenEvents += 1

class EventLogger(object):
    Version = "1.0"

    class ConfigurationOptions(object):
        """Container class/structure for EventManager options."""
        def __init__(self):
            self.LogToFile = True             # Whether or not to write logs to a file
            self.LogFileDir = ""              # Path to store the event log to on disk
            self.LogFileLength = 0            # The max number of events to store in a log file
            self.ArchiveGroupName = ""        # Librarian archive name to send to when LogFileLength is reached
            self.MaxResidentEvents = 0        # How many events to accumulate before truncating to MinResidentEvents
            self.MinResidentEvents = 0        # How many events to truncate to when Max is reached
            self.BroadcastEvents = False      # Whether events should be broadcasted

        def Load(self, IniPath):
            """Loads the configuration from the specified ini/config file."""
            if not os.path.exists(IniPath):
                raise Exception("Configuration file '%s' not found." % IniPath)

            cp = CustomConfigObj(IniPath)
            basePath = os.path.split(IniPath)[0]
            self.LogFileDir = os.path.join(basePath, cp.get(_MAIN_CONFIG_SECTION, "LogFileDir"))
            self.LogToFile = cp.getboolean(_MAIN_CONFIG_SECTION, "LogToFile")
            self.LogFileLength = cp.getint(_MAIN_CONFIG_SECTION, "LogFileLength")
            self.ArchiveGroupName = cp.get(_MAIN_CONFIG_SECTION, "ArchiveGroupName")
            self.MaxResidentEvents = cp.getint(_MAIN_CONFIG_SECTION, "MaxResidentEvents")
            self.MinResidentEvents = cp.getint(_MAIN_CONFIG_SECTION, "MinResidentEvents")
            self.BroadcastEvents = cp.getboolean(_MAIN_CONFIG_SECTION, "BroadcastEvents")
            self.TimeStandard = cp.get(_MAIN_CONFIG_SECTION,"TimeStandard","gmt")

    def __init__(self, ConfigPath):
        self.Config = EventLogger.ConfigurationOptions()
        self.ConfigPath = ConfigPath

        self.EventList = [] #the list of all recorded events
        self.EventSourceCounter = {} #a dictionary holding the event count for each source
        self.EventSourceList = [] #the list of unique sources that have raised events

        self.RegisteredEventTypes = {}
        self.LoggerStopped = False

        self.RpcServer = CmdFIFO.CmdFIFOServer(("", SharedTypes.RPC_PORT_LOGGER),
                                                ServerName = "EventManager",
                                                ServerDescription = "General event logger for all CRDS Host software.",
                                                ServerVersion = self.Version,
                                                threaded = True)
        cmdMode = CmdFIFO.CMD_TYPE_VerifyOnly
        self.RpcServer.register_function(self.RPC_LogEvent, DefaultMode = cmdMode, NameSlice = 4)
        self.RpcServer.register_function(self.RPC_LogEventCode, DefaultMode = cmdMode, NameSlice = 4)
        self.RpcServer.register_function(self.RPC_Debug_LogOne, DefaultMode = cmdMode, NameSlice = 4)
        self.RpcServer.register_function(self.RPC_Debug_LogMany, DefaultMode = cmdMode, NameSlice = 4)
        self.RpcServer.register_function(self.RPC_ShowEventViewer, DefaultMode = CmdFIFO.CMD_TYPE_Blocking, NameSlice = 4)
        self.RpcServer.register_function(self.RPC_LogMsg, DefaultMode = cmdMode, NameSlice = 4)
        self.RpcServer.register_function(self.RPC_GetLogInfo, DefaultMode = CmdFIFO.CMD_TYPE_Blocking, NameSlice = 4)
        #self.RpcServer.register_function(self.RPC_CloseEventViewer, DefaultMode = CmdFIFO.CMD_TYPE_Blocking, NameSlice = 4)

        self.EventBroadcaster = Broadcaster.Broadcaster(SharedTypes.BROADCAST_PORT_EVENTLOG)

        self.ShowViewer = False
        self.Viewer = None
        self.ViewerUpdateFunc = None

        self._LogFile = None


    def _ArchiveLurkingEventLogs(self):
        """Queues up a request to archive all lurking event logs.

        It is queued for later, because the Librarian may not be up and running yet.
        """
        lurkers = glob(os.path.join(self.Config.LogFileDir, "%s*.%s" % (LOGFILE_PREFIX, LOGFILE_EXTENSION)))
        #queue up the archiving
        # - can't be too quick since Librarian must start, but
        # - don't want to be too slow in case we need to archive a new log in the mean time
        #   - shouldn't happen if log file length is long enough
        #   - if shutting down EventManager sooner than this, lurkers should ideally be archived
        #     before the current log, but out of order archiving is not a huge deal, esp when
        #     lurkers should only exist in odd circumstances
        if len(lurkers)>0:
            if __debug__: print "Lurking files found:\n%s" % "\n".join(lurkers)
            lurkers.sort()
            def _DoFileArchive():
                for fpath in lurkers:
                    if __debug__: print "Archiving file %s" % fpath
                    CRDS_Archiver.ArchiveFile(self.Config.ArchiveGroupName, fpath, True)
                    time.sleep(5)
            threading.Timer(5*60, _DoFileArchive).start()

    def Launch(self):
        self.Config.Load(self.ConfigPath)
        try: os.makedirs(self.Config.LogFileDir)
        except Exception: pass

        #Archive any old event log files lurking around...
        self._ArchiveLurkingEventLogs()
        self.RpcServer.serve_forever()
        #set the event to indicate we're done...
        self.LoggerStopped = True
        if self.Viewer:
            self.Viewer.ShutDown()

    def PreRegisterEvent(self, Desc, Level = 1, Code = DEFAULT_EVENT_CODE, AccessLevel = SharedTypes.ACCESS_PICARRO_ONLY, Verbose = "", ReplaceOldEvent = False):
        """Pre-registers event descriptions for future use.

        Events can be referenced in the future simply by the event code.

        This should NOT be done via RPC since registered events will be lost if/when
        the logger application restarts.  Events to be pre-registered should be
        loaded from a file or included in a module.
        """
        #make the event...
        if Code == DEFAULT_EVENT_CODE:
            raise Exception("Pre-registered events cannot have the default event code (%s) as the event code." % DEFAULT_EVENT_CODE)
        elif str(Code) in self.RegisteredEventTypes:
            if not ReplaceOldEvent:
                raise Exception("An event has already been pre-registered with code %s: '%s'" % (Code, self.RegisteredEventTypes[str(Code)]))

        theEvent = EventInfo(Description = Desc, Level = Level, Code=Code, AccessLevel=AccessLevel, VerboseDesc=Verbose)
        #add it to the registered event dictionary...
        self.RegisteredEventTypes[str(Code)] = theEvent

    def _CreateEventLog(self, Desc, Data = "", Level = 1, Code = -1, AccessLevel = SharedTypes.ACCESS_PICARRO_ONLY, Verbose = "", SourceTime = 0, SourceNameOverride = None):
        #Magically get the source name from the CmdFIFO server...
        source = SourceNameOverride or self.RpcServer.CurrentCmd_ClientName

        #get the current count for this source (and add it to the trackers if not there)
        countForThisSource = self.EventSourceCounter.setdefault(source, 0)
        if countForThisSource == 0:
            self.EventSourceList.append(source)
        self.EventSourceCounter[source] = countForThisSource + 1

        #And the time that the dispatcher received the log (there may be some lag we
        #don't want if the log queue gets jammed while archiving or something)...
        #  - only do it this way if not provided by the caller...
        sourceTime = SourceTime or self.RpcServer.CurrentCmd_RxTime
        #print "s=", sourceTime
        thisEvent = EventLog(source,
                             Description = Desc,
                             Data = Data,
                             Level = Level,
                             Code = Code,
                             AccessLevel = AccessLevel,
                             VerboseDescription = Verbose,
                             EventTime = sourceTime
                             )
        return thisEvent

    def _AddEventLog(self, TheEvent):
        assert isinstance(TheEvent, EventLog)
        self.EventList.append(TheEvent)

        #Truncate the resident event list if too big...
        listTruncated = False
        if len(self.EventList) >= self.Config.MaxResidentEvents:
            if self.Viewer:
                #now cut the reference count down and avoid double memory usage next...
                self.Viewer.ChangeDataSource(None)
            self.EventList = self.EventList[-1 * abs(self.Config.MinResidentEvents):]
            listTruncated = True

        #Log to file if we're supposed to...
        if self.Config.LogToFile:
            if not self._LogFile:
                self._LogFile = EventLogFile(self.Config.LogFileDir, self.Config.TimeStandard)
            self._LogFile.WriteEvent(TheEvent)
            if self._LogFile.NumWrittenEvents >= self.Config.LogFileLength:
                #archive the file and set it so we'll make a new one...
                CRDS_Archiver.ArchiveFile(self.Config.ArchiveGroupName, self._LogFile.LogPath, True)
                self._LogFile = None
        #endif (self.Config.LogToFile)

        #Broadcast it to those who care...
        if self.Config.BroadcastEvents:
            try:
                self.EventBroadcaster.send("%s\n" % str(TheEvent))
            except Exception, E:
                if __debug__: print "Exception occurred on Broadcast: %s %e" % (E, E)
                #eat it (want to avoid the logger itself posting messages to avoid a message flood)...
                pass
                #self.Events.append(EventLog("EventLogger", "Exception trapped during Event Broadcast.", 1, 0, False , "Logging of this exception blocked for the next Exception trapped is below:\n---\n%s\n%r\n---"  % (E, E))

        #Update the GUI...
        if self.ViewerUpdateFunc:
            try:
                if listTruncated:
                    self.Viewer.ChangeDataSource(self.EventList)
                self.ViewerUpdateFunc()
            except Exception, E:
                if __debug__: print repr(E), E
                #eat all errors that might come from the non-essential GUI...
                pass

    def RPC_LogEvent(self, Desc, Data = "", Level = 1, Code = -1, \
        AccessLevel = SharedTypes.ACCESS_PICARRO_ONLY, Verbose = "", SourceTime = 0):
        """Used to log a generic event that can be defined at the time of calling.

        Levels are from 0-3 in increasing order of severity as below:
          3 - Critical - Causes a performance hit or crash (eg: top level
                         exception trap, app restarted)
          2 - Standard - Significant event (eg: Alarm occurred, Cfg change, etc)
          1 - Info     - Used to help with post-mortems (eg: Command received)
          0 - Debug    - ie: SPAM!  ONLY send if debugging
        """
        #Create a new entry...
        thisEvent = self._CreateEventLog(Desc, Data=Data, Level=Level, Code=Code, \
        AccessLevel=AccessLevel, Verbose=Verbose, SourceTime=SourceTime)
        #Add the event to the log...
        self._AddEventLog(thisEvent)

    def RPC_LogEventCode(self, EventCode, Data = "", SourceTime = 0):
        """Log an event that has been pre-defined.

        The event is referenced with the unique event code.

        This allows events to be pre-registered with verbose information that need
        not be sent every time. This saves on RPC bandwidth and on coding.
        """
        try:
            thisEvent = self.RegisteredEventTypes[str(EventCode)]
        except KeyError:
            raise Exception("No event has been pre-registered with code '%s'" % EventCode)
        self._CreateEventLog(thisEvent, Data = Data, SourceTime = SourceTime)
        self._AddEventLog(thisEvent)

    def RPC_Debug_LogOne(self):
        """A quick debug RPC call that needs no args so it is fast with the test client.
        """
        thisEvent = self._CreateEventLog("Bogus debug event", Data = "RPC_Debug_LogOne", Verbose = "This is a single event")
        self._AddEventLog(thisEvent)
        return "Debug entry finished!" #just testing something here

    def RPC_Debug_LogMany(self, Count, Delay_s = 0):
        """A quick way to flood the logger with messages.

        Delay_s is the delay between successive messages and is 0 by default.

        NOTE: the delay is done on the logger side, so there is no way to interleave
        log entries with this call.  All will be successive.
        """
        for i in range(Count):
            thisEvent = self._CreateEventLog("Log %s of %s generated with Debug_LogMany." % (i+1, Count))
            self._AddEventLog(thisEvent)
            time.sleep(Delay_s)

    def RPC_ShowEventViewer(self):
        """Launches the event viewer GUI.

        If already showing, this does nothing.
        """
        self.ShowViewer = True
        if self.Viewer:
            #Already viewing!
            return "Viewer already running!"
        else:
            #The main loop will handle firing the app up
            self.RPC_LogEvent("Event viewer launched")
            return "OK"

    def RPC_CloseEventViewer(self, ConfirmShutDown = False):
        """NOT CURRENTLY WORKING WELL SO NOT INCLUDED!

        IT WORKS, EXCEPT YOU NEED TO ROLL THE MOUSE OVER THE WINDOW FOR IT TO
        SHUT DOWN FOR SOME REASON.  WEIRD.

        Closes the event viewer GUI.

        If the GUI is not open, this does nothing.
        """
        if not self.Viewer:
            ret = "No viewer running!"
        else:
            self.Viewer.ShutDown()
            if ConfirmShutDown:
                #When the application shuts down the main loop will set self.Viewer to
                #None, so we can wait for this.
                shutdownComplete = False
                timeout = 5
                startTime = TimeStamp()
                while TimeStamp() - startTime < timeout:
                    if not self.Viewer:
                        shutdownComplete = True
                        break
                    time.sleep(0.1)
                if shutdownComplete:
                    ret = "Viewer confirmed to be shut down"
                else:
                    ret = "ERR: Waited %s seconds and Viewer did not shut down." % (timeout,)
            else:
                ret = "OK"
        #Make sure it doesn't start up again...
        self.ShowViewer = False
        return ret

    def RPC_LogMsg(self, source = "", msg = ""):
        """
        THIS CALL IS DEPRECATED.  Please use LogEvent instead.

        This call is present to allow drop-in replacement of the newer 'EventLogger'
        in place of the old 'Logger'.
        """
        self.RPC_LogEvent(msg)

    def RPC_GetLogInfo(self):
        """Return basic info on the stored event list."""
        logLength = len(self.EventList)
        maxIndex = self.EventList[-1].Index
        return dict(Length = logLength, MaxIndex = maxIndex)

HELP_STRING = \
""" EventManager.py [-v|--viewer] [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help.
-v, --viewer         Show the event viewing GUI
-c                   Specify a config file.  Default = "./EventManager.ini"
"""

def PrintUsage():
    print HELP_STRING

def HandleCommandSwitches():
    import getopt

    shortOpts = 'hvc:'
    longOpts = ["help", "viewer"]
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
    showViewer = False
    configFile = os.path.dirname(AppPath) + "/" + _DEFAULT_CONFIG_NAME

    if '-h' in options:
        PrintUsage()
        sys.exit()

    if "-v" in options or "--viewer" in options:
        showViewer = True

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return (showViewer, configFile)

def LaunchViewerGUI(EL):
    import Host.EventManager.EventManagerGUI as EventManagerGUI
    logViewer = EventManagerGUI.LogViewer(EL.EventList, EventSourceCounter = EL.EventSourceCounter, EventSourceList = EL.EventSourceList)
    #Now link the EventLogger to the viewer...
    EL.Viewer = logViewer
    EL.ViewerUpdateFunc = logViewer.UpdateEventData
    #Launch the GUI app...
    logViewer.Launch() #This call blocks until GUI exit
    #Make sure we don't start it up again if we exited the GUI with the X
    EL.ShowViewer = False
    EL.Viewer = None
    EL.ViewerUpdateFunc = None
    #clean up so that we stay clean with this logger...

    del logViewer, EventManagerGUI

def Main():
    #General runtime philosophy is dictated by the fact that a wxApp needs to run
    #on the main thread.  because of this...
    #  1. Start the logger application on it's own thread
    #  2. Main thread will wait for the logger to finish
    #  3. While waiting, give the main thread to the wxApp if needed
    #  4. Shutting down of the wxApp (to get the main thread back) will be done
    #     by the wxApp being shut down when the logger exits.

    showViewer, configFile = HandleCommandSwitches()

    #create and kick off the event logging engine...
    EL = EventLogger(configFile)
    t = threading.Thread(target = EL.Launch)
    t.setDaemon(True)
    t.start()

    if showViewer:
        EL.ShowViewer = True

    #Now just loop and wait for the logger to shut down (while letting the
    #viewer app be on the main thread)...
    while not EL.LoggerStopped:
        if EL.ShowViewer:
            if EL.Viewer == None:
                #Need to start it up. Blocks until GUI exits.
                LaunchViewerGUI(EL)
        else:
            #We shouldn't be showing the viewer.
            assert not EL.Viewer, "Code error!  The viewer app should not be running at this time!"
        time.sleep(1.0)

# Viewer started by:
#   1. command line
#   2. RPC call
# Viewer stopped by
#   1. Closing the viewer (X)
#   2. RPC call
#   3. Logger server stopped

if __name__ == "__main__":
    Main()