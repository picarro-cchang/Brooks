#!/usr/bin/python
#
"""
File Name: DataLogger.py
Purpose: The data logger application is responsible logging of public and private logs.

Notes:
    The logs can be user configurable or configured via factory defaults.
    The following configuration is set via .ini file:
     - Storage folder
     - Data columns list
     - Log rate
     - Max log duration, i.e The data is logged for the max log duration, archived and repeated.
       If the MaxLogDuration is in 24hr increments, the repeat always starts at midnight.
     - Whether the log is enabled by default.
     - Name of DataManager source script.
     - Broadcast port number.
    User log configuration is stored in userLog.ini. Private factory configured logs
    configuration is stored in privateLog.ini.
    The following subset of user log configuration can be changed using RPC calls:
     - Adding/removing data columns
     - Starting/stopping logging.
     - Changing logging rate.

    File History:
    06-11-xx al   In progress
    06-12-11 Al   Imported MeasData class instead of having duplicate definition.
    06-12-18 Al   Added mailbox, filter enable and 24 folders
    06-12-19 Al   Fixed bug in Write.  Was using CreateLogTime before first call to _Create
    06-12-21 Al   Added 1. call to _CheckSize after writing to mailbox
                        2. Truncation of entry.
                        3. Fixed bug in _Create which caused the listener to crash,
                          because sub directory name was changed before file was renamed.
    06-12-21 Al   Added alarm status listener
    06-12-22 Al   Changed mkdir to makedirs so whole directory path is created if it doesn't exist.
    07-03-14 sze  Added DATALOGGER_getFilenameRpc to return log filename. Added
                  DataLog.CopyToMailboxAndArchive which renames an Active file to an inactive one.
                  Added RemoveEmptySubdirs to Directory class which removes empty directories when the
                  DataLogger is started.
    07-10-05 sze  Introduced BareTime configuration option to reduce number of time columns in output fie
    07-10-05 sze  Allow data columns to change in the middle of a file (a new header is written). Data
                  columns (after the time and alarm) are sorted.
    08-09-18 alex Replaced SortedConfigParser with CustomConfigObj
    08-09-26 alex Changed the function names in Directory and DataLog classes so only class-internal functions start with "_"
    08-09-29 alex Moved file logging management to Archiver
    10-01-19 alex Changed the way to copy data to mailbox and move data to archive. Since these
                  2 threads are not synchronized, we should just make an additional local copy and
                  simply move both of them to mailbox and archive location.
    10-01-22 sze  Moved file accesses out of listeners and into handler threads so that the listeners do
                  not become disconnected when the file system is busy.
    10-03-15 sze  Allow datalog files to be written in HDF5 format by setting usehdf5 option to True (default
                  is False). Create new file if data columns change and filter_enabled is False. If filter_enabled
                  is True, the data file always contains the specified columns, and unfilled values get zero entries
    10-03-18 sze  Record time to millisecond resolution to facilitate timing of data reporting rate
    10-04-27 sze  Report bad data flagged by measurement system by setting bit 16 of the alarm status column
    10-10-23 sze  Remove DATE_TIME column (replaced by time) and get ms timestamp info from DataManager
    10-12-08 alex Provide an option to use GMT or local time in log file name (GMT is used by default)
    12-02-07 alex Disable write-back function to INI file
    12-10-08 sze  Allow data manager to report a quantity ALARM_STATUS, which is logical ORed with the alarm status
                  reported by the alarm system. This allows extra bits to be set by the data manager for conditions such
                  as excessive acquisition delay, large tuner standard deviation etc.

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

####
# Set constants for this file...
####
APP_NAME = "DataLogger"
APP_VERSION = 1.0
APP_DESCRIPTION = "The data logger"
_CONFIG_NAME = "DataLogger.ini"
_PRIVATE_CONFIG_NAME = "PrivateLog.ini"
_USER_CONFIG_NAME = "UserLog.ini"

import datetime
import sys
import os
import Queue
import re
import stat
import time
import threading
import socket #for transmitting data to the fitter
import struct #for converting numbers to byte format
import shutil
import traceback
from inspect import isclass
from tables import *

from Host.Common import CmdFIFO, StringPickler, Listener, Broadcaster, timestamp
from Host.Common.SharedTypes import RPC_PORT_DATALOGGER, BROADCAST_PORT_DATA_MANAGER, RPC_PORT_INSTR_MANAGER, \
                                    RPC_PORT_ARCHIVER, RPC_PORT_DRIVER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SafeFile import SafeFile, FileExists
from Host.Common.MeasData import MeasData
from Host.Common.AppStatus import STREAM_Status
from Host.Common.InstErrors import *
from Host.Common.parsePeriphIntrfConfig import parsePeriphIntrfConfig
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

DATALOGGER_RPC_SUCCESS = 0
DATALOGGER_RPC_NOT_READY = -1
DATALOGGER_RPC_FAILED = -2

TWENTY_FOUR_HOURS_IN_SECONDS = 86400
ONE_HOUR_IN_SECONDS = 3600
#Set up a useful AppPath reference...
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

if __debug__:
    print("Loading rpdb2")
    import rpdb2
    rpdb2.start_embedded_debugger("hostdbg",timeout=0)
    print("rpdb2 loaded")

CRDS_Archiver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ARCHIVER,
                                            APP_NAME,
                                            IsDontCareConnection = True)

CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                            APP_NAME,
                                            IsDontCareConnection = False)

# Not used now, but may be useful in the future
CRDS_InstMgr = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER,
                                            APP_NAME,
                                            IsDontCareConnection = True)

def deleteFile(filename):
    """Delete a file, reporting any error, but not causing an exception. Returns True if delete succeeded"""
    try:
        os.chmod(filename,stat.S_IREAD | stat.S_IWRITE)
        os.remove(filename)
        return True
    except OSError,e:
        Log("Error deleting file: %s. %s" % (filename,e))
        return False

class Mbox(object):
    """Class to manage mailbox directory """
    def __init__(self, enabled, mailGroupName):
        self.Enabled = enabled
        self.GroupName = mailGroupName

class DataLog(object):
    """Class to manage writing (and reading) of data logs to disk."""
    COLUMN_WIDTH = 26
    def __init__(self, EngineName, TimeStandard, Mbox, BackupGroupName = None, PeriphDictTuple = ()):
        self.EnabledDataList = []
        self.DecimationFactor = 1
        self.DecimationCount = 0
        self.MaxLogDuration = TWENTY_FOUR_HOURS_IN_SECONDS
        self.Enabled = False
        self.StopPending = False
        self.SourceScript = ""
        self.Port = BROADCAST_PORT_DATA_MANAGER
        self.CreateLogTime = 0
        self.CreateLogTimestamp = 0
        self.LogPath = ""
        self.Fname = ""
        self.EngineName = EngineName
        if TimeStandard.lower() == "local":
            self.TimeStandard = "local"
        else:
            self.TimeStandard = "gmt"
        self.LogName = ""
        self.Mbox = Mbox
        self.BackupGroupName = BackupGroupName
        self.PeriphDictTuple = PeriphDictTuple
        self.SubDir = ""
        self.BareTime = False
        self.useHdf5 = False
        self.oldDataList = []
        self.queue = Queue.Queue(0)
        self.handler = threading.Thread(target=self.qHandler)
        self.handler.setDaemon(True)
        self.handler.start()
        self.maxDuration = {}
        self.fp = None
        self.table = None
        self.lastFlush = 0
        self.restart = False

    def qHandler(self):
        while True:
            action,args = self.queue.get()
            now = TimeStamp()
            if action == "write":
                self._Write(*args)
            elif action == "copyToMailboxAndArchive":
                self._CopyToMailboxAndArchive(*args)
            duration = TimeStamp() - now
            if duration > 10:
                Log("Datalog: %s action %s takes %.3fs" % (self.LogPath,action,duration))
            if duration > self.maxDuration.get(self.LogPath,0):
                self.maxDuration[self.LogPath] = duration
                Log("Datalog: %s action %s takes new max time %.3f" % (self.LogPath,action,duration))

    def Write(self, Time, DataDict):
        self.queue.put(("write",[Time,DataDict.copy()]))

    def Close(self):
        if self.fp is not None:
            self.fp.close()
            self.table = None
            self.fp = None
        if self.liveArchive:
            time.sleep(2.0)
            CRDS_Archiver.StopLiveArchive(self.ArchiveGroupName, self.LogPath)

    def CopyToMailboxAndArchive(self, srcPath=""):
        if not srcPath:
            self.Close()
            ts = self.CreateLogTimestamp
        else:
            # Try to extract timestamp from the file name
            # The date and time should be two consecutive fields, one with eight digits and the next with six
            m = re.compile("-(\d{8}-\d{6})-").search(os.path.split(srcPath)[1])
            if m:
                ts = timestamp.unixTimeToTimestamp(time.mktime(time.strptime(m.group(1),"%Y%m%d-%H%M%S")))
            else:
                ts = None
        self.queue.put(("copyToMailboxAndArchive",[srcPath,ts]))

    def LoadConfig(self, ConfigParser, basePath, LogName):
        self.LogName = LogName
        self.EnabledDataList = [d.strip() for d in ConfigParser.get(self.LogName, "datalist").split(',')]
        self.DecimationFactor = ConfigParser.getint(self.LogName, "decimationfactor")
        self.MaxLogDuration = ONE_HOUR_IN_SECONDS * ConfigParser.getfloat(self.LogName, "maxlogduration_hrs")
        self.Enabled = ConfigParser.getboolean(self.LogName, "enabled")
        self.FilterEnabled = ConfigParser.getboolean(self.LogName, "filterenabled")
        self.MboxEnabled = ConfigParser.getboolean(self.LogName, "mailboxenable", False)
        self.backupEnabled = ConfigParser.getboolean(self.LogName, "backupenable", False)
        self.SourceScript = ConfigParser.get(self.LogName, "sourcescript")
        self.UpdateInterval = ConfigParser.getfloat(self.LogName, "updateInterval", 10.0)

        print("LogName: %s MaxLogDuration in seconds: %s" % (LogName, self.MaxLogDuration))

        # Add peripheral columns if available
        try:
            if self.PeriphDictTuple:
                for pDict in self.PeriphDictTuple:
                    if self.SourceScript in pDict["source"]:
                        for d in pDict["data"]:
                            if d not in self.EnabledDataList:
                                self.EnabledDataList.append(d)
        except Exception, err:
            print "%r" % err
        self.Port = ConfigParser.getint(self.LogName, "port")
        self.BareTime = ConfigParser.getboolean(self.LogName, "baretime")
        self.useHdf5 = ConfigParser.getboolean(self.LogName, "usehdf5", False)
        self.liveArchive = ConfigParser.getboolean(self.LogName, "liveArchive", False)
        self.ArchiveGroupName = ConfigParser.get(self.LogName, "ArchiveGroupName", default="")
        self.PrintTimeInHalfSecond = ConfigParser.getboolean(self.LogName, "printTimeInHalfSecond", False)
        self.WriteEpochTime = ConfigParser.getboolean(self.LogName, "writeEpochTime", True)
        self.WriteJulianDays = ConfigParser.getboolean(self.LogName, "writeJulianDays", True)
        delimiter = ConfigParser.get(self.LogName, "delimiter", "")
        pattern = r"\s*\"(.*)\"\s*"
        pattern2 = r"\s*'(.*)'\s*"
        if re.match(pattern, delimiter):
            self.delimiter = re.sub(pattern, r'\1', delimiter)
        elif re.match(pattern2, delimiter):
            self.delimiter = re.sub(pattern2, r'\1', delimiter)
        else:
            self.delimiter = delimiter
        if sys.platform == "win32":
            relDir = "%s\%s" % (ConfigParser.get(self.LogName, "srcfolder"),self.LogName)
        else:
            relDir = "%s/%s" % (ConfigParser.get(self.LogName, "srcfolder"),self.LogName)
        self.srcDir = os.path.join(basePath, relDir)

        # Handle Linux if we want the log in the default user home directory.
        # If in the ini we have 'srcfolder = ~/Picarro/Log', expand the '~' to
        # the home directory of the user running the code.
        # If the directories don't exist they are created in _Create().
        #
        if relDir.startswith("~"):
            relDir = os.path.expanduser(relDir)
            self.srcDir = relDir

        if self.liveArchive and self.useHdf5:
            raise ValueError('Cannot use live archive with HDF5 files in %s' % LogName)

        # Archive all old files
        for root, dirs, files in os.walk(self.srcDir):
            for filename in files:
                if ('mailbox_copy' not in root) and ('backup_copy' not in root):
                    path = os.path.join(root,filename)
                    # print "Cleaning...", path
                    self.CopyToMailboxAndArchive(path)


    def _CopyToMailboxAndArchive(self, srcPath="", ts=None):
        if srcPath == "":
            if self.LogPath != "":
                srcPath = self.LogPath
            else:
                return
        if ts is None:
            ts = timestamp.getTimestamp()

        startTime = TimeStamp()
        # If Mailbox option is enabled:
        # Make an additional copy and move 2 separate copies to archive and mailbox locations
        # The problem of copying to mailbox fisrt and then moving to archive location is that
        # the archiving thread may be done before the copying thread finishes
        # Do the same thing to "backup_copy" folder if enabled.
        if self.Mbox.Enabled and self.MboxEnabled:
            srcPathCopy = os.path.dirname(srcPath) + '/mailbox_copy'
            if not os.path.exists(srcPathCopy):
                os.makedirs(srcPathCopy)
            srcPathCopy = os.path.join(srcPathCopy, os.path.basename(srcPath))
            shutil.copy2(srcPath, srcPathCopy)
            # if mailbox enabled, copy file to mailbox directory first
            CRDS_Archiver.ArchiveFile(self.Mbox.GroupName, srcPathCopy, True, ts)
        if self.BackupGroupName != None and self.backupEnabled:
            srcPathCopy = os.path.dirname(srcPath) + '/backup_copy'
            if not os.path.exists(srcPathCopy):
                os.makedirs(srcPathCopy)
            srcPathCopy = os.path.join(srcPathCopy, os.path.basename(srcPath))
            shutil.copy2(srcPath, srcPathCopy)
            # if backup enabled, copy file to backup directory first
            CRDS_Archiver.ArchiveFile(self.BackupGroupName, srcPathCopy, True, ts)
        # Archive only non-live archives
        if self.ArchiveGroupName:
            if not self.liveArchive:
                CRDS_Archiver.ArchiveFile(self.ArchiveGroupName, srcPath, True, ts)
            else:
                deleteFile(srcPath)
        Log("Datalog archive processing %s took %s seconds" % (os.path.basename(srcPath),TimeStamp()-startTime))


    def _Create(self, DataList):
        """Creates a new log file named with a header which contains all the tokens in the DataList."""
        # Deal with old file first
        if self.LogPath != "":
            if self.table != None:
                self.table.flush()
                self.table = None
            self.Close()
            del self.maxDuration[self.LogPath]
            self._CopyToMailboxAndArchive(self.LogPath)
            self.LogPath = ""

        # check to see if directory exists. If it doesn't create it.
        if( os.access(self.srcDir, os.F_OK) == False ):
            os.makedirs(self.srcDir)

        # Create name and path of new file
        self._SetLogPathAndTimestamp()

        # If multiple files are to be created in the same second,
        # wait for 2 seconds before creating the new one to avoid
        # the race condition
        if os.access(self.LogPath, os.F_OK):
            time.sleep(2)
            self._SetLogPathAndTimestamp()

        if self.useHdf5:
            # Create file and make a new table
            self.fp = openFile(self.LogPath,"w")
            self._MakeTable(DataList)
        else:
            # Create file and write header
            self.fp = file(self.LogPath, "w")
            self._WriteHeader(DataList)

        if self.liveArchive:
            CRDS_Archiver.StartLiveArchive(self.ArchiveGroupName, self.LogPath, self.CreateLogTimestamp)

        Log("A new log file (%s) created at %s" % (self.LogPath, self.timeString))

    def _SetLogPathAndTimestamp(self):
        self.CreateLogTimestamp = timestamp.getTimestamp()
        self.CreateLogTime = timestamp.unixTime(self.CreateLogTimestamp)

        if self.TimeStandard == "local":
            self.LogHour = time.localtime(self.CreateLogTime).tm_hour #used to determine when we reached midnight
            self.timeString = time.strftime("%Y%m%d-%H%M%S",time.localtime(self.CreateLogTime))
        else:
            # Use GMT (UTC)
            self.LogHour = time.gmtime(self.CreateLogTime).tm_hour #used to determine when we reached midnight
            self.timeString = time.strftime("%Y%m%d-%H%M%SZ",time.gmtime(self.CreateLogTime))
            # Z is for GMT (UTC) according to ISO 8601 format

        if self.useHdf5:
            self.Fname = "%s-%s-%s.h5" % (self.EngineName,
                                            self.timeString,
                                            self.LogName)
        else:
            self.Fname = "%s-%s-%s.dat" % (self.EngineName,
                                            self.timeString,
                                            self.LogName)
        self.LogPath = os.path.abspath(os.path.join(self.srcDir, self.Fname))

    def _WriteEntry(self, string):
        if self.delimiter:
            self.fp.write(string + self.delimiter)
        else:   # write data into columns with fixed width
            self.fp.write((string[:self.COLUMN_WIDTH-1]).ljust(self.COLUMN_WIDTH))

    def _WriteHeader(self,DataList):
        if self.BareTime:
            # ISO8601 UTC time
            self._WriteEntry("DATETIME (ISO8601 UTC)")
        else:
            self._WriteEntry("DATE")
            self._WriteEntry("TIME")
            self._WriteEntry("FRAC_DAYS_SINCE_JAN1")
            self._WriteEntry("FRAC_HRS_SINCE_JAN1")
            if self.WriteJulianDays:
                self._WriteEntry("JULIAN_DAYS")

        if self.WriteEpochTime:
            self._WriteEntry("EPOCH_TIME")

        self._WriteEntry("ALARM_STATUS")
        self._WriteEntry("INST_STATUS")

        for dataName in DataList:
            self._WriteEntry(dataName)

        self.fp.write("\n")
        self.DecimationCount = 0

    def _MakeTable(self,DataList):
        """Construct the HDF5 table from the entries in DataList"""
        tableDict = {}
        filters = Filters(complevel=1,fletcher32=True)
        if not self.BareTime:
            tableDict["FRAC_DAYS_SINCE_JAN1"] = Float32Col()
            tableDict["FRAC_HRS_SINCE_JAN1"]  = Float32Col()
            if self.WriteJulianDays:
                tableDict["JULIAN_DAYS"] = Float32Col()
        for dataName in DataList:
            if dataName in ["time"]:
                tableDict[dataName] = Float64Col()
            elif dataName in ["timestamp"]:
                tableDict[dataName] = UInt64Col()
            else:
                tableDict[dataName] = Float32Col()
        self.DecimationCount = 0
        if self.table is not None:
            self.table.flush()
        self.table = self.fp.createTable(self.fp.root,"results",tableDict,filters=filters)

    def _MakeListFromDict(self, DataDict):
        DataList = []
        dataKeys = sorted(DataDict.keys())
        if self.FilterEnabled:
            for data in self.EnabledDataList:
                DataList.append(data)
        else:
            for data in dataKeys:
                DataList.append(data)
        return DataList


    def _Write(self, Time, DataDict):
        """Writes a representation of the provided data to disk, either in text or H5 mode"""

        DataDict = DataDict.copy()

        if self.TimeStandard == "local":
            currentTime = time.localtime(Time)
        else:
            currentTime = time.gmtime(Time)

        self.DecimationCount+=1
        if self.DecimationCount >= self.DecimationFactor:
            DataList = self._MakeListFromDict(DataDict)

            # check to see if file was created yet.
            if self.LogPath == "" or self.restart:
                self._Create(DataList)
                self.oldDataList = DataList
                self.restart = False

            self.DecimationCount = 0

            logDuration = (Time - self.CreateLogTime)

            if ( self.MaxLogDuration % TWENTY_FOUR_HOURS_IN_SECONDS ) == 0:
                #if DEBUG: Log("24Incr Log Duration =%f. MaxLogDuration=%f" % (logDuration, self.MaxLogDuration))
                # MaxLogDuration is set to a 24 increment therefore create new file at 12:00 during the last 24 hrs of logging
                # If difference <= 24 hrs then check to see if it's midnight yet.
                if (self.MaxLogDuration - logDuration) <= TWENTY_FOUR_HOURS_IN_SECONDS:
                    if currentTime.tm_hour < self.LogHour:
                        self._Create(DataList)
                        self.oldDataList = DataList
            else:
                #if DEBUG: Log("Not24Incr Log Duration =%f. MaxLogDuration=%f" % (logDuration, self.MaxLogDuration))
                # MaxLogDuration is not a 24 increment therefore wait for LogDuration to be >= MaxLogDuration
                if logDuration >= self.MaxLogDuration:
                    self._Create(DataList)
                    self.oldDataList = DataList

            self.LogHour = currentTime.tm_hour

            # Start by writing fixed data to file
            #calculate SecondsFromEpoch as of Jan1 of this year
            string = "%s 01 01 00 00 00" % time.strftime("%Y",currentTime)
            timeTuple =time.strptime( string, "%Y %m %d %H %M %S")
            Jan1SecondsSinceEpoch = time.mktime( timeTuple )

            if DataList != self.oldDataList:
                # Start a new file since data columns have changed
                self._Create(DataList)
                self.oldDataList = DataList

            if self.useHdf5:
                row = self.table.row
                if not self.BareTime:
                    days = (Time-Jan1SecondsSinceEpoch)/TWENTY_FOUR_HOURS_IN_SECONDS
                    row["FRAC_DAYS_SINCE_JAN1"] = days
                    hrs = (Time-Jan1SecondsSinceEpoch)/ONE_HOUR_IN_SECONDS
                    row["FRAC_HRS_SINCE_JAN1"]  = hrs
                    if self.WriteJulianDays:
                        row["JULIAN_DAYS"] = days+1.0
                for data in DataList:
                    row[data] = DataDict.get(data,0.0)
                row.append()
                now = TimeStamp()
                if now-self.lastFlush >  self.UpdateInterval:
                    self.table.flush()
                    self.lastFlush = now
            else:
                if self.BareTime:
                    # ISO8601 UTC date and time with fractional seconds
                    timeStr = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(Time))
                    fracSec = Time - int(Time)
                    timeStr += (".%03d" % int(1000*fracSec))
                    timeStr += "Z"
                    self._WriteEntry(timeStr)
                else:
                    #write DATE
                    self._WriteEntry(time.strftime("%Y-%m-%d",currentTime))
                    #write TIME
                    timeStr = time.strftime("%H:%M:%S",currentTime)
                    fracSec = Time - int(Time)
                    if self.PrintTimeInHalfSecond:
                        if fracSec >= 0.5:
                            timeStr += ".50"
                        else:
                            timeStr += ".00"
                    else:
                        timeStr += (".%03d" % int(1000*fracSec))
                    self._WriteEntry(timeStr)
                    #write FRAC_DAYS_SINCE_JAN1
                    days = (Time-Jan1SecondsSinceEpoch)/TWENTY_FOUR_HOURS_IN_SECONDS
                    self._WriteEntry("%.8f" %days)
                    #write FRAC_HRS_SINCE_JAN1
                    hrs = (Time-Jan1SecondsSinceEpoch)/ONE_HOUR_IN_SECONDS
                    self._WriteEntry("%.6f" %hrs)
                    #write JULIAN_DAYS if enabled
                    if self.WriteJulianDays:
                        self._WriteEntry("%.8f" % (days+1))

                #write EPOCH_TIME if enabled
                if self.WriteEpochTime:
                    self._WriteEntry("%.3f" % Time)

                self._WriteEntry("%.0f" % DataDict.get('ALARM_STATUS', 0))
                self._WriteEntry("%.0f" % DataDict.get('INST_STATUS', 0))

                for data in DataList:
                    self._WriteEntry("%.10E" % DataDict.get(data,0.0))

                self.fp.write("\n")
                now = TimeStamp()
                if now-self.lastFlush >  self.UpdateInterval:
                    self.fp.flush()
                    self.lastFlush = now


####
## Classes...
####
class DataLogger(object):
    """This is Data Logger object."""
    def __init__(self, ConfigPath, UserConfigPath, PrivateConfigPath):

        if DEBUG: Log("Loading config options.")
        self.ConfigPath = ConfigPath
        self.UserConfigPath = UserConfigPath
        self.PrivateConfigPath = PrivateConfigPath

        self.md = MeasData()

        if DEBUG: Log("Setting up RPC server.")
        #Now set up the RPC server...
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_DATALOGGER),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = APP_VERSION,
                                                threaded = True)


        if DEBUG: Log("Registering RPC functions.")
        #Register the rpc functions...
        self.RpcServer.register_function(self.DATALOGGER_getDataRpc)
        self.RpcServer.register_function(self.DATALOGGER_getFilenameRpc)
        self.RpcServer.register_function(self.DATALOGGER_addUserDataRpc)
        self.RpcServer.register_function(self.DATALOGGER_removeUserDataRpc)

        self.RpcServer.register_function(self.DATALOGGER_startLogRpc)
        self.RpcServer.register_function(self.DATALOGGER_stopLogRpc)
        self.RpcServer.register_function(self.DATALOGGER_logEnabledRpc)

        self.RpcServer.register_function(self.DATALOGGER_setDecimationFactorRpc)
        self.RpcServer.register_function(self.DATALOGGER_getDecimationFactorRpc)
        self.RpcServer.register_function(self.DATALOGGER_getUserLogsRpc)
        self.RpcServer.register_function(self.DATALOGGER_getPrivateLogsRpc)

        self.DataListenerLastTime = 0
        self.maxDataListenerRtt = 0

    def _LoadDefaultConfig(self):
        cp = CustomConfigObj(self.ConfigPath)
        self.basePath = os.path.split(self.ConfigPath)[0]
        try:
            try:
                self.engineName = CRDS_Driver.fetchInstrInfo("analyzername")
                if self.engineName == None:
                    self.engineName = cp.get("DEFAULT", "ENGINE")
            except Exception, err:
                print err
                self.engineName = cp.get("DEFAULT", "ENGINE")
            mailGroupName = cp.get("DEFAULT", "ArchiveGroupName")
            mailGroupEnabled = cp.getboolean("DEFAULT", "mboxenabled")
            self.backupGroupName = cp.get("DEFAULT", "BackupGroupName")
            self.timeStandard = cp.get("DEFAULT","TimeStandard",default="gmt")
            # Handle peripheral interface columns
            try:
                periphIntrfConfig = os.path.join(self.basePath, cp.get("PeriphIntrf", "periphIntrfConfig"))
                self.periphDictTuple = parsePeriphIntrfConfig(periphIntrfConfig, selectAll=False)
            except Exception, err:
                print "%r" % err
                self.periphDictTuple = ()
        except:
            tbMsg = traceback.format_exc()
            Log("Load Config Exception:",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            self.engineName = "Unknown Engine"
            mailGroupName = ""
            mailGroupEnabled = False
            self.backupGroupName = None
            self.timeStandard = "gmt"
            self.periphDictTuple = ()

        self.mbox = Mbox(mailGroupEnabled, mailGroupName)

    def _LoadCustomConfig(self, ConfigParser, LogDict):
        """Creates log dict which store DataLog object for every log section defined in confile file.
           Also creates SrcDict and PortDict which contains lists of DataLog objects for each source scripts and port number."""

        logList = ConfigParser.list_sections()
        for logName in logList:
            dl = DataLog(self.engineName, self.timeStandard, self.mbox, self.backupGroupName, self.periphDictTuple)
            #load config from .ini
            try:
                dl.LoadConfig(ConfigParser, self.basePath, logName)
            except:
                tbMsg = traceback.format_exc()
                Log("Load Log Config Exception:",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
                continue

            LogDict[logName]=dl

            # update Source Script Dict
            if dl.SourceScript not in self.SrcDict:
                logList = [logName]
            else:
                logList = self.SrcDict[dl.SourceScript]
                logList.append(logName)

            self.SrcDict[dl.SourceScript] = logList

            # update Port Dict
            if dl.Port not in self.PortDict:
                logList = [logName]
            else:
                logList = self.PortDict[dl.Port]
                logList.append(logName)

            self.PortDict[dl.Port]= logList

    def _DataListener(self, dataMgrObject):
        try:
            self.md.ImportPickleDict(dataMgrObject)
        except:
            tbMsg = traceback.format_exc()
            Log("Import Pickle Exception:",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)

        now = TimeStamp()
        if self.DataListenerLastTime != 0:
            rtt = now - self.DataListenerLastTime
            if rtt > self.maxDataListenerRtt:
                Log("Maximum data listener loop RTT so far: %.3f" % (self.maxDataListenerRtt,))
                self.maxDataListenerRtt = rtt
        self.DataListenerLastTime = now

        #Log("Data Listener: source=%s data=%s" % (self.md.Source,self.md.Data))
        # check to make sure this a broadcast that I'm interested in
        if self.md.Source in self.SrcDict:
            # iterate through all user and default log config found in the list
            for logName in self.SrcDict[self.md.Source]:
                if logName in self.UserLogDict:
                    dataLog = self.UserLogDict[logName]
                    if dataLog.Enabled:
                        dataLog.Write(self.md.Time, self.md.Data)
                    # Remove Active_ prefix from files for logs which are being stopped
                    if dataLog.StopPending:
                        dataLog.CopyToMailboxAndArchive()
                        dataLog.StopPending = False
                if logName in self.PrivateLogDict:
                    dataLog = self.PrivateLogDict[logName]
                    if dataLog.Enabled:
                        dataLog.Write(self.md.Time, self.md.Data)
                    # Remove the Active_ prefix from files for logs which are being stopped
                    if dataLog.StopPending:
                        dataLog.CopyToMailboxAndArchive()
                        dataLog.StopPending = False

    def DATALOGGER_start(self):
        """Called to start the Data Logger."""
        #Log("Data Logger started")
        self.UserLogDict = {}    # contains DataLog objects for each log section found in user config file.
        self.PrivateLogDict = {} # contains DataLog objects for each log section found in private config file.
        self.SrcDict = {}      # Dictionary of source scripts which contains list of log names.
                                 # Used for filtering of broadcast data.
        self.PortDict = {}     # Dictionary of port numbers which contains list of log names.

        if not FileExists(self.ConfigPath):
            Log("File not found.", Data = dict(Path = self.ConfigPath), Level = 2)
            raise Exception("File '%s' not found." % self.ConfigPath)
        if not FileExists(self.UserConfigPath):
            Log("File not found.", Data = dict(Path = self.UserConfigPath), Level = 2)
            raise Exception("File '%s' not found." % self.UserConfigPath)
        if not FileExists(self.PrivateConfigPath):
            Log("File not found.", Data = dict(Path = self.PrivateConfigPath), Level = 2)
            raise Exception("File '%s' not found." % self.PrivateConfigPath)

        self.UserCp = CustomConfigObj(self.UserConfigPath)
        self.PrivateCp = CustomConfigObj(self.PrivateConfigPath)

        self._LoadDefaultConfig()
        self._LoadCustomConfig(self.PrivateCp, self.PrivateLogDict)
        self._LoadCustomConfig(self.UserCp, self.UserLogDict)
        Log("Data Logger: source dict=%s; port dict=%s" % (self.SrcDict,self.PortDict))

        for port,value in self.PortDict.iteritems():
            self.Listener = Listener.Listener(None, port, StringPickler.ArbitraryObject, self._DataListener, retry = True,
                                              name = "Data Logger data listener",logFunc = Log)

        self.RpcServer.serve_forever()
        self.DATALOGGER_shutdown()
        if DEBUG: Log("Shutting Down Data Logger.")

    def DATALOGGER_shutdown(self):
        for dl in self.UserLogDict:
            dl.Close()
        for dl in self.PrivateLogDict:
            dl.Close()

    def DATALOGGER_getDataRpc(self, LogName):
        """Returns a string containing a list of data columns being logged for the specified log."""
        dataListStr=""
        if LogName in self.PrivateLogDict:
            dl =  self.PrivateLogDict[LogName]
            # convert list to string
            for token in dl.EnabledDataList:
                dataListStr+="%s," %token
            #remove traling comma
            if len(dataListStr) > 0:
                dataListStr = dataListStr[0:len(dataListStr)-1]

            return dataListStr
        elif LogName in self.UserLogDict:
            dl =  self.UserLogDict[LogName]
            # convert list to string
            for token in dl.EnabledDataList:
                dataListStr+="%s," %token
            #remove trailing comma
            if len(dataListStr) > 0:
                dataListStr = dataListStr[0:len(dataListStr)-1]

            return dataListStr
        else:
            return dataListStr
    def DATALOGGER_getFilenameRpc(self, LogName):
        """Returns a string containing the file currently associated with the specified log."""
        if LogName in self.PrivateLogDict:
            dl =  self.PrivateLogDict[LogName]
            return dl.LogPath
        elif LogName in self.UserLogDict:
            dl =  self.UserLogDict[LogName]
            return dl.LogPath
        else:
            return "Invalid LogName"
    def DATALOGGER_getUserLogsRpc(self):
        list = []
        for data,value in self.UserLogDict.iteritems():
            list.append(data)

        return DATALOGGER_RPC_SUCCESS, list
    def DATALOGGER_getPrivateLogsRpc(self):
        list = []
        for data,value in self.PrivateLogDict.iteritems():
            list.append(data)

        return DATALOGGER_RPC_SUCCESS, list
    def DATALOGGER_addUserDataRpc(self, UserLogName, tokenListStr):
        """Adds a list of data columns to the specified existing user log."""
        if UserLogName in self.UserLogDict:
            dl =  self.UserLogDict[UserLogName]
            tokenList = tokenListStr.split(',')
            # check to see if token is in DataList. If it isn't, add it.
            listUpdated = False
            for token in tokenList:
                if token not in dl.EnabledDataList:
                    dl.EnabledDataList.append(token)
                    listUpdated = True

            if listUpdated == True:

                if self.UserLogDict[UserLogName].FilterEnabled:
                    # re-initialize LogPath string to make sure file is created when data comes in.
                    self.UserLogDict[UserLogName].LogPath = ""

                # convert list to string
                dataListStr=""
                for token in dl.EnabledDataList:
                    dataListStr+="%s," %token
                #remove trailing comma
                if len(dataListStr) > 0:
                    dataListStr = dataListStr[0:len(dataListStr)-1]
                # write string to UserConfig
                self.UserCp.set(UserLogName,"datalist", dataListStr)
                #fp = open(self.UserConfigPath,"wb")
                #self.UserCp.write(fp)
                #fp.close()

            return DATALOGGER_RPC_SUCCESS
        else:
            return DATALOGGER_RPC_FAILED
    def DATALOGGER_removeUserDataRpc(self, UserLogName, tokenListStr):
        """Removes a list of data columns to the specified user log."""
        if UserLogName in self.UserLogDict:
            dl =  self.UserLogDict[UserLogName]
            tokenList = tokenListStr.split(',')
            # check to see if token is in DataList. If it is remove it.
            listUpdated = False
            for token in tokenList:
                if token in dl.EnabledDataList:
                    dl.EnabledDataList.remove(token)
                    listUpdated = True

            if listUpdated == True:

                if self.UserLogDict[UserLogName].FilterEnabled:
                    # re-initialize LogPath string to make sure file is created when data comes in.
                    self.UserLogDict[UserLogName].LogPath = ""

                # convert list to string
                dataListStr=""
                for token in dl.EnabledDataList:
                    dataListStr+="%s," %token
                #remove trailing comma
                if len(dataListStr) > 0:
                    dataListStr = dataListStr[0:len(dataListStr)-1]
                # write string to UserConfig
                self.UserCp.set(UserLogName,"datalist", dataListStr)
                #fp = open(self.UserConfigPath,"wb")
                #self.UserCp.write(fp)
                #fp.close()

            return DATALOGGER_RPC_SUCCESS
        else:
            return DATALOGGER_RPC_FAILED
    def DATALOGGER_startLogRpc(self, UserLogName, restart = False):
        """Called to enable logging of the specified user log."""
        if UserLogName in self.UserLogDict:
            dl =  self.UserLogDict[UserLogName]
            dl.Enabled = True
            if restart:
                self.UserLogDict[UserLogName].restart = True
            else:
                # re-initialize LogPath string to make sure file is created when data comes in.
                self.UserLogDict[UserLogName].LogPath =""

            self.UserCp.set(UserLogName,"enabled", "true")
            #fp = open(self.UserConfigPath,"wb")
            #self.UserCp.write(fp)
            #fp.close()

            return DATALOGGER_RPC_SUCCESS
        else:
            return DATALOGGER_RPC_FAILED
    def DATALOGGER_stopLogRpc(self, UserLogName):
        """Called to disable logging of the specified user log."""
        if UserLogName in self.UserLogDict:
            dl =  self.UserLogDict[UserLogName]
            dl.Enabled = False
            dl.StopPending = True
            self.UserCp.set(UserLogName,"enabled", "false")
            #fp = open(self.UserConfigPath,"wb")
            #self.UserCp.write(fp)
            #fp.close()

            return DATALOGGER_RPC_SUCCESS
        else:
            return DATALOGGER_RPC_FAILED
    def DATALOGGER_logEnabledRpc(self, LogName):
        """Returns True if the specified user or private log is enabled."""
        if LogName in self.UserLogDict:
            dl =  self.UserLogDict[LogName]
            return dl.Enabled
        elif LogName in self.PrivateLogDict:
            dl =  self.PrivateLogDict[LogName]
            return dl.Enabled
        else:
            return False
    def DATALOGGER_setDecimationFactorRpc(self, UserLogName, factor):
        """Called to set the decimation factor of the specified user log."""
        if UserLogName in self.UserLogDict:
            dl =  self.UserLogDict[UserLogName]
            dl.DecimationFactor = factor

            self.UserCp.set(UserLogName,"decimationfactor", "%d" % factor)
            #fp = open(self.UserConfigPath,"wb")
            #self.UserCp.write(fp)
            #fp.close()
            return DATALOGGER_RPC_SUCCESS
        else:
            return DATALOGGER_RPC_FAILED
    def DATALOGGER_getDecimationFactorRpc(self, LogName):
        """Called to set the decimation factor of the specified user log."""
        if LogName in self.UserLogDict:
            dl =  self.UserLogDict[LogName]
            return dl.DecimationFactor
        elif LogName in self.PrivateLogDict:
            dl =  self.PrivateLogDict[LogName]
            return dl.DecimationFactor
        else:
            return 0
HELP_STRING = \
"""\
DataLogger.py [-h] [-u<FILENAME>] [-d<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-u  Specify a different user log config file.  User = "./UserLog.ini"
-d  Specify a different private log config file.  Private = "./PrivateLog.ini"

"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:u:p:", ["help"])
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
    configFile = os.path.dirname(AppPath) + "/" + _CONFIG_NAME
    privateConfigFile = os.path.dirname(AppPath) + "/" + _PRIVATE_CONFIG_NAME
    userConfigFile = os.path.dirname(AppPath) + "/" + _USER_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        Log ("Config file specified at command line: %s" % configFile)

    if "-u" in options:
        userConfigFile = options["-u"]
        Log ("User Config file specified at command line: %s" % userConfigFile)

    if "-p" in options:
        privateConfigFile = options["-p"]
        Log ("Private Config file specified at command line: %s" % privateConfigFile)

    return (configFile, userConfigFile, privateConfigFile)
def main():
    #Get and handle the command line options...
    configFile, userConfigFile, privateConfigFile = HandleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    try:
        app = DataLogger(configFile, userConfigFile, privateConfigFile)
        app.DATALOGGER_start()
    except Exception, E:
        if DEBUG: raise
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))

if __name__ == "__main__":
    DEBUG = __debug__
    try:
        # workaround for exception: AttributeError: _strptime_time
        # time.strptime() is not thread-safe
        # details: http://code-trick.com/python-bug-attribute-error-_strptime/
        time.strptime(time.ctime())
        main()
    except:
        tbMsg = traceback.format_exc()
        Log("Unhandled exception trapped by last chance handler",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = tbMsg)
    Log("Exiting program")
    sys.stdout.flush()
else:
    # This file is included from within a test harness
    DEBUG = True
    def Log(string,Data={},Level=0,Verbose=""):
        print "Log [%d]: %s" % (Level,string,)
        if Data: print "Data: %s" % (Data,)
        if Verbose: print "Verbose: %s" % Verbose
