#!/usr/bin/python
#
# File Name: DataLogger.py
# Purpose:
# The data logger application is responsible logging of public and private logs.
# The logs can be user configurable or configured via factory defaults.
# The following configuration is set via .ini file:
#  - Storage folder
#  - Data columns list
#  - Log rate
#  - Max log duration, i.e The data is logged for the max log duration, archived and repeated.
#    If the MaxLogDuration is in 24hr increments, the repeat always starts at midnight.
#  - Whether the log is enabled by default.
#  - Name of DataManager source script.
#  - Broadcast port number.
# User log configuration is stored in userLog.ini. Private factory configured logs
# configuration is stored in privateLog.ini.
# The following subset of user log configuration can be changed using RPC calls:
#  - Adding/removing data columns
#  - Starting/stopping logging.
#  - Changing logging rate.
#
# File History:
# 06-11-xx al  In progress
# 06-12-11 Al  Imported MeasData class instead of having duplicate definition.
# 06-12-18 Al  Added mailbox, filter enable and 24 folders
# 06-12-19 Al  Fixed bug in Write.  Was using CreateLogTime before first call to _Create
# 06-12-21 Al  Added 1. call to _CheckSize after writing to mailbox
#                    2. Truncation of entry.
#                    3. Fixed bug in _Create which caused the listener to crash,
#                       because sub directory name was changed before file was renamed.
# 06-12-21 Al  Added alarm status listener
# 06-12-22 Al  Changed mkdir to makedirs so whole directory path is created if it doesn't exist.
# 07-03-14 sze Added DATALOGGER_getFilenameRpc to return log filename. Added
#               DataLog.CopyToMailboxAndArchive which renames an Active file to an inactive one.
#               Added RemoveEmptySubdirs to Directory class which removes empty directories when the
#               DataLogger is started.
# 07-10-05 sze Introduced BareTime configuration option to reduce number of time columns in output fie
# 07-10-05 sze Allow data columns to change in the middle of a file (a new header is written). Data
#               columns (after the time and alarm) are sorted.
# 08-09-18  alex  Replaced SortedConfigParser with CustomConfigObj
# 08-09-26  alex  Changed the function names in Directory and DataLog classes so only class-internal functions start with "_"
# 08-09-29  alex  Moved file logging management to Archiver
# 10-01-19  alex  Changed the way to copy data to mailbox and move data to archive. Since these
#                 2 threads are not synchronized, we should just make an additional local copy and
#                 simply move both of them to mailbox and archive location.
# 10-01-22  sze   Moved file accesses out of listeners and into handler threads so that the listeners do
#                   not become disconnected when the file system is busy.
####
## Set constants for this file...
####
APP_NAME = "DataLogger"
APP_VERSION = 1.0
APP_DESCRIPTION = "The data logger"
_CONFIG_NAME = "DataLogger.ini"
_PRIVATE_CONFIG_NAME = "PrivateLog.ini"
_USER_CONFIG_NAME = "UserLog.ini"

import sys
import os
import Queue
import stat
import time
import threading
import socket #for transmitting data to the fitter
import struct #for converting numbers to byte format
import time
import shutil
import traceback
from inspect import isclass

from Host.Common import CmdFIFO, StringPickler, Listener, Broadcaster
from Host.Common.SharedTypes import RPC_PORT_DATALOGGER, BROADCAST_PORT_DATA_MANAGER, RPC_PORT_INSTR_MANAGER, STATUS_PORT_ALARM_SYSTEM, RPC_PORT_ARCHIVER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SafeFile import SafeFile, FileExists
from Host.Common.MeasData import MeasData
from Host.Common.AppStatus import STREAM_Status
from Host.Common.InstErrors import *
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

CRDS_Archiver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ARCHIVER,
                                            APP_NAME,
                                            IsDontCareConnection = True)

# Not used now, but may be useful in the future                                            
CRDS_InstMgr = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER,
                                            APP_NAME,
                                            IsDontCareConnection = True)                                            

class Mbox(object):
    """Class to manage mailbox directory """
    def __init__(self, enabled, mailGroupName):
        self.Enabled = enabled
        self.GroupName = mailGroupName

class DataLog(object):
    """Class to manage writing (and reading) of data logs to disk."""
    COLUMN_WIDTH = 26
    def __init__(self, EngineName, Mbox, BackupGroupName = None):
        self.EnabledDataList = []
        self.DecimationFactor = 1
        self.DecimationCount = 0
        self.MaxLogDuration = TWENTY_FOUR_HOURS_IN_SECONDS
        self.Enabled = False
        self.StopPending = False
        self.SourceScript = ""
        self.Port = BROADCAST_PORT_DATA_MANAGER
        self.CreateLogTime = 0
        self.LogPath = ""
        self.Fname = ""
        self.EngineName = EngineName
        self.LogName = ""
        self.Mbox = Mbox
        self.BackupGroupName = BackupGroupName
        self.SubDir = ""
        self.AlarmStatus = 0
        self.BareTime = False
        self.oldDataList = []
        self.queue = Queue.Queue(0)
        self.handler = threading.Thread(target=self.qHandler)
        self.handler.setDaemon(True)
        self.handler.start()

    def qHandler(self):
        while True:
            action,args = self.queue.get()
            if action == "write":
                self._Write(*args)
            elif action == "copyToMailboxAndArchive":
                self._CopyToMailboxAndArchive(*args)
    
    def Write(self, Time, DataDict, alarmStatus):
        self.queue.put(("write",[Time,DataDict.copy(),alarmStatus]))
        
    def CopyToMailboxAndArchive(self, srcPath=""):
        self.queue.put(("copyToMailboxAndArchive",[srcPath]))
        
    def LoadConfig(self, ConfigParser, basePath, LogName):
        self.LogName = LogName
        self.EnabledDataList = ConfigParser.get(self.LogName, "datalist").split(',')
        self.DecimationFactor = ConfigParser.getint(self.LogName, "decimationfactor")
        self.MaxLogDuration = ONE_HOUR_IN_SECONDS * ConfigParser.getfloat(self.LogName, "maxlogduration_hrs")
        self.Enabled = ConfigParser.getboolean(self.LogName, "enabled")
        self.FilterEnabled = ConfigParser.getboolean(self.LogName, "filterenabled")
        self.MboxEnabled = ConfigParser.getboolean(self.LogName, "mailboxenable", False)
        self.backupEnabled = ConfigParser.getboolean(self.LogName, "backupenable", False)
        self.SourceScript = ConfigParser.get(self.LogName, "sourcescript")
        self.Port = ConfigParser.getint(self.LogName, "port")
        self.BareTime = ConfigParser.getboolean(self.LogName, "baretime")
        self.ArchiveGroupName = ConfigParser.get(self.LogName, "ArchiveGroupName")
        self.PrintTimeInHalfSecond = ConfigParser.getboolean(self.LogName, "printTimeInHalfSecond", False)
        self.WriteEpochTime = ConfigParser.getboolean(self.LogName, "writeEpochTime", True)
        relDir = "%s\%s" % (ConfigParser.get(self.LogName, "srcfolder"),self.LogName)
        self.srcDir = os.path.join(basePath, relDir)
        # Archive all old files
        for root, dirs, files in os.walk(self.srcDir):
            for filename in files:
                if ('mailbox_copy' not in root) and ('backup_copy' not in root):
                    path = os.path.join(root,filename)
                    self.CopyToMailboxAndArchive(path)

    def _CopyToMailboxAndArchive(self, srcPath=""):
        if srcPath == "":
            srcPath = self.LogPath
        #Log("Archiving: %s" % os.path.basename(srcPath))   
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
            CRDS_Archiver.ArchiveFile(self.Mbox.GroupName, srcPathCopy, True)
        if self.BackupGroupName != None and self.backupEnabled:
            srcPathCopy = os.path.dirname(srcPath) + '/backup_copy'
            if not os.path.exists(srcPathCopy):
                os.makedirs(srcPathCopy)
            srcPathCopy = os.path.join(srcPathCopy, os.path.basename(srcPath))     
            shutil.copy2(srcPath, srcPathCopy)
            # if mailbox enabled, copy file to mailbox directory first
            CRDS_Archiver.ArchiveFile(self.BackupGroupName, srcPathCopy, True) 
        # Archive
        CRDS_Archiver.ArchiveFile(self.ArchiveGroupName, srcPath, True)
            

    def _Create(self, DataList):
        """Creates a new log file named with a header which contains all the tokens in the DataList."""
        # Deal with old file first
        if self.LogPath != "":
            self._CopyToMailboxAndArchive()

        dirName = self.srcDir        
        # check to see if directory exists. If it doesn't create it.
        if( os.access(dirName, os.F_OK) == False ):
            os.makedirs(dirName)
       
        # Create name and path of new file
        self.CreateLogTime = time.time()    
        self.LogHour = time.localtime().tm_hour #used to determine when we reached midnight
        self.Fname = "%s-%s-%s.dat" % (self.EngineName,
                                  time.strftime("%Y%m%d-%H%M%S",time.localtime()),
                                  self.LogName)

        self.LogPath = os.path.join(dirName, self.Fname)
        Log("A new log file (%s) created at %s" % (self.LogPath, time.strftime("%Y%m%d-%H%M%S",time.localtime())))    
        # create file and write header
        fp = file(self.LogPath, "w")
        self._WriteHeader(fp,DataList)
        fp.close()

    def _WriteEntry(self, fp, string):
        fp.write((string[:self.COLUMN_WIDTH-1]).ljust(self.COLUMN_WIDTH))
        
    def _WriteHeader(self,fp,DataList):
        if not self.BareTime:
            self._WriteEntry(fp,"DATE")
            self._WriteEntry(fp,"TIME")
            self._WriteEntry(fp,"FRAC_DAYS_SINCE_JAN1")
            self._WriteEntry(fp,"FRAC_HRS_SINCE_JAN1")
        
        if self.WriteEpochTime:
            self._WriteEntry(fp,"EPOCH_TIME")
        
        self._WriteEntry(fp,"ALARM_STATUS")

        for dataName in DataList:
            self._WriteEntry(fp,dataName)

        fp.write("\n")
        self.DecimationCount = 0

    def _MakeListFromDict(self, DataDict):
        DataList = []
        dataKeys = sorted(DataDict.keys())
        if self.FilterEnabled:
            for data in self.EnabledDataList:
                if data in dataKeys:
                    DataList.append(data)
        else:
            for data in dataKeys:
                DataList.append(data)
        return DataList

    def _Write(self, Time, DataDict, alarmStatus):
        """Writes a string representation of the provided DataList to disk."""

        localtime = time.localtime(Time)

        self.DecimationCount+=1
        if self.DecimationCount >= self.DecimationFactor:
            DataList = self._MakeListFromDict(DataDict)

            # check to see if file was created yet.
            if self.LogPath == "":
                self._Create(DataList)
                self.oldDataList = DataList

            self.DecimationCount = 0

            logDuration = (Time - self.CreateLogTime)

            if ( self.MaxLogDuration % TWENTY_FOUR_HOURS_IN_SECONDS ) == 0:
                #if DEBUG: Log("24Incr Log Duration =%f. MaxLogDuration=%f" % (logDuration, self.MaxLogDuration))
                # MaxLogDuration is set to a 24 increment therefore create new file at 12:00 during the last 24 hrs of logging
                # If difference <= 24 hrs then check to see if it's midnight yet.
                if (self.MaxLogDuration - logDuration) <= TWENTY_FOUR_HOURS_IN_SECONDS:
                    if localtime.tm_hour < self.LogHour:
                        self._Create(DataList)
                        self.oldDataList = DataList
            else:
                #if DEBUG: Log("Not24Incr Log Duration =%f. MaxLogDuration=%f" % (logDuration, self.MaxLogDuration))
                # MaxLogDuration is not a 24 increment therefore wait for LogDuration to be >= MaxLogDuration
                if logDuration >= self.MaxLogDuration:
                    self._Create(DataList)
                    self.oldDataList = DataList

            self.LogHour = localtime.tm_hour

            # Start by writing fixed data to file
            #calculate SecondsFromEpoch as of Jan1 of this year
            string = "%s 01 01 00 00 00" % time.strftime("%Y",localtime)
            timeTuple =time.strptime( string, "%Y %m %d %H %M %S")
            Jan1SecondsSinceEpoch = time.mktime( timeTuple )

            fp = file(self.LogPath, "a")

            if DataList != self.oldDataList:
                print >>fp, "### Data columns have changed ###"
                self._WriteHeader(fp,DataList)
                self.oldDataList = DataList

            if not self.BareTime:
                #write DATE
                self._WriteEntry(fp,time.strftime("%Y-%m-%d",localtime))
                #write TIME
                timeStr = time.strftime("%H:%M:%S",localtime)
                fracSec = Time - int(Time)
                if self.PrintTimeInHalfSecond:
                    if fracSec >= 0.5:
                        timeStr += ".50"
                    else:
                        timeStr += ".00"
                else:
                    timeStr += (".%02d" % int(100*fracSec))
                self._WriteEntry(fp,timeStr)
                #write FRAC_DAYS_SINCE_JAN1
                days = (Time-Jan1SecondsSinceEpoch)/TWENTY_FOUR_HOURS_IN_SECONDS
                self._WriteEntry(fp,("%.8f" %days))
                #write FRAC_HRS_SINCE_JAN1
                hrs = (Time-Jan1SecondsSinceEpoch)/ONE_HOUR_IN_SECONDS
                self._WriteEntry(fp,("%.6f" %hrs))

            #write EPOCH_TIME if enabled
            if self.WriteEpochTime:
                self._WriteEntry(fp,("%.2f" %Time))
                
            #write ALARM_STATE
            self._WriteEntry(fp,("%d" %alarmStatus))

            for data in DataList:
                value = DataDict[data]
                if self.FilterEnabled:
                    if data in self.EnabledDataList:
                        self._WriteEntry(fp,("%E" %value))
                else:
                    self._WriteEntry(fp,("%E" %value))

            fp.write("\n")
            fp.close()

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

        #Set up instrument manager rpc connection to report errors

    def _LoadDefaultConfig(self):
        cp = CustomConfigObj(self.ConfigPath) 
        self.basePath = os.path.split(self.ConfigPath)[0]
        try:
            self.engineName = cp.get("DEFAULT", "ENGINE")
            mailGroupName = cp.get("DEFAULT", "ArchiveGroupName")
            mailGroupEnabled = cp.getboolean("DEFAULT", "mboxenabled")
            self.backupGroupName = cp.get("DEFAULT", "BackupGroupName")
        except:
            tbMsg = traceback.format_exc()
            Log("Load Config Exception:",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
            self.engineName = "Unknown Engine"
            mailGroupName = ""
            mailGroupEnabled = False
            self.backupGroupName = None
            
        self.mbox = Mbox(mailGroupEnabled, mailGroupName)

    def _LoadCustomConfig(self, ConfigParser, LogDict):
        """Creates log dict which store DataLog object for every log section defined in confile file.
           Also creates SrcDict and PortDict which contains lists of DataLog objects for each source scripts and port number."""

        logList = ConfigParser.list_sections()
        for logName in logList:
            dl = DataLog(self.engineName, self.mbox, self.backupGroupName)
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

        #Log("Data Listener: source=%s data=%s" % (self.md.Source,self.md.Data))
        # check to make sure this a broadcast that I'm interested in
        if self.md.Source in self.SrcDict:
            # iterate through all user and default log config found in the list
            for logName in self.SrcDict[self.md.Source]:
                if logName in self.UserLogDict:
                    dataLog = self.UserLogDict[logName]
                    if dataLog.Enabled:
                        dataLog.Write(self.md.Time, self.md.Data, dataLog.AlarmStatus)
                    # Remove Active_ prefix from files for logs which are being stopped
                    if dataLog.StopPending:
                        dataLog.CopyToMailboxAndArchive()
                        dataLog.StopPending = False
                if logName in self.PrivateLogDict:
                    dataLog = self.PrivateLogDict[logName]
                    if dataLog.Enabled:
                        dataLog.Write(self.md.Time, self.md.Data, dataLog.AlarmStatus)
                    # Remove the Active_ prefix from files for logs which are being stopped
                    if dataLog.StopPending:
                        dataLog.CopyToMailboxAndArchive()
                        dataLog.StopPending = False
                        
    def _AlarmListener( self, data ):
        """Listener for alarm status"""
        try:
            for logName, value in self.UserLogDict.iteritems():
                self.UserLogDict[logName].AlarmStatus = data.status
            for logName, value in self.PrivateLogDict.iteritems():
                self.PrivateLogDict[logName].AlarmStatus = data.status
        except:
            tbMsg = traceback.format_exc()
            Log("Listener Exception",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
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

        self.alarmListener = Listener.Listener(None, STATUS_PORT_ALARM_SYSTEM, STREAM_Status, self._AlarmListener, retry = True,
                                              name = "Data Logger alarm status listener",logFunc = Log)

        self.RpcServer.serve_forever()
        if DEBUG: Log("Shutting Down Data Logger.")
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
                fp = open(self.UserConfigPath,"wb")
                self.UserCp.write(fp)
                fp.close()

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
                fp = open(self.UserConfigPath,"wb")
                self.UserCp.write(fp)
                fp.close()

            return DATALOGGER_RPC_SUCCESS
        else:
            return DATALOGGER_RPC_FAILED
    def DATALOGGER_startLogRpc(self, UserLogName):
        """Called to enable logging of the specified user log."""
        if UserLogName in self.UserLogDict:
            dl =  self.UserLogDict[UserLogName]
            dl.Enabled = True
            # re-initialize LogPath string to make sure file is created when data comes in.
            self.UserLogDict[UserLogName].LogPath =""

            self.UserCp.set(UserLogName,"enabled", "true")
            fp = open(self.UserConfigPath,"wb")
            self.UserCp.write(fp)
            fp.close()

            return DATALOGGER_RPC_SUCCESS
        else:
            return DATALOGGER_RPC_FAILED
    def DATALOGGER_stopLogRpc(self, UserLogName):
        """Called to enable logging of the specified user log."""
        if UserLogName in self.UserLogDict:
            dl =  self.UserLogDict[UserLogName]
            dl.Enabled = False
            dl.StopPending = True
            self.UserCp.set(UserLogName,"enabled", "false")
            fp = open(self.UserConfigPath,"wb")
            self.UserCp.write(fp)
            fp.close()

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
            fp = open(self.UserConfigPath,"wb")
            self.UserCp.write(fp)
            fp.close()
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
