"""
Copyright 2010-2012 Picarro Inc.

Instrument Performance Verification
"""

import sys
import os
import time
import threading
import bz2
import traceback
import re
from collections import deque
from Queue import Queue
from datetime import datetime, timedelta

import tables
import wx
import numpy

from Host.autogen import interface
from Host.Common import timestamp
from Host.Common import Broadcaster
from Host.Common import TextListener
from Host.Common import CmdFIFO
from Host.Common import EventManagerProxy
from Host.Common import Tracer
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SharedTypes import RPC_PORT_DRIVER
from Host.Common.SharedTypes import RPC_PORT_ARCHIVER
from Host.Common.SharedTypes import RPC_PORT_IPV
from Host.Common.SharedTypes import BROADCAST_PORT_IPV
from Host.Common.SharedTypes import BROADCAST_PORT_EVENTLOG
from Host.Common.SingleInstance import SingleInstance
from Host.Common.GuiTools import getInnerStr

from IPVFrame import IPVFrame
from ReportSender import ReportSender


APP_NAME = "IPV"
APP_DESCRIPTION = "Instrument Performance Verification"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "IPV.ini"


EventManagerProxy.EventManagerProxy_Init(APP_NAME,DontCareConnection = False)

def Log(desc, data=None, level=1, code=-1, verbose=''):
    EventManagerProxy.Log(desc, Data=data, Level=level, Code=code,
                          Verbose=verbose)

def LogExc(desc):
    EventManagerProxy.LogExc(desc)


DB_LEVEL = 2
# level 0 = 1 sec; level 1 = 10 sec; level 2 = 100 sec; ...

DEFAULT_IPV_DIR = "C:/Picarro/G2000/Log/IPV_RPT/"
REPORT_FORMAT = "%-30s,%-10s,%-30s,%-30s,%-65s,%-65s,%-65s\n"
EVENTLOG_FORMAT = "%-10s,%-12s,%-12s,%-30s,%-10s,%s\n"
STREAM_NUM_TO_NAME_DICT = {}
NAME_TO_STREAM_NUM_DICT = {}
for streamNum in interface.STREAM_MemberTypeDict:
    STREAM_NUM_TO_NAME_DICT[streamNum] = interface.STREAM_MemberTypeDict[streamNum][7:]
    NAME_TO_STREAM_NUM_DICT[interface.STREAM_MemberTypeDict[streamNum][7:]] = streamNum

UNIXORIGIN = datetime(1970,1,1,0,0,0,0)

INTERNAL_VERSION_RX = re.compile(
    r'Internal\s\("git-v1:(.*)"\)')

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

CRDS_Archiver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ARCHIVER,
                                            APP_NAME,
                                            IsDontCareConnection = False)

CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                            APP_NAME,
                                            IsDontCareConnection = False)

def floatListToString(fList, precision=3):
    format = "%."+ "%ie" % int(precision)
    return " ".join([format % i for i in fList])

def listToString(inList):
    return " ".join([str(i) for i in inList])

def datetimeToUnixTime(t):
    td = t - UNIXORIGIN
    return td.days*86400 + td.seconds

def getSpecUTC(specTime = "00:00:00", option="float"):
    """Get the sepcified GMT time"""
    (hr, min, sec) = specTime.split(":")
    newTime = datetime.timetuple(datetime.utcnow().replace(hour=int(hr), minute=int(min), second = int(sec)))
    if option.lower() == "tuple":
        return newTime
    if option.lower() == "float":
        return time.mktime(newTime)
    elif option.lower() == "string":
        return time.ctime(time.mktime(newTime))

def getUTCTime(option="float"):
    """Get UTC (GMT) time"""
    uctTimeTuple = datetime.timetuple(datetime.utcnow())
    if option.lower() == "tuple":
        return uctTimeTuple
    elif option.lower() == "float":
        return time.mktime(uctTimeTuple)
    elif option.lower() == "string":
        return time.ctime(time.mktime(uctTimeTuple))

class RpcServerThread(threading.Thread):
    def __init__(self, rpcServer, exitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.rpcServer = rpcServer
        self.exitFunction = exitFunction
    def run(self):
        self.rpcServer.serve_forever()
        try: #it might be a threading.Event
            self.exitFunction()
            Log("RpcServer exited and no longer serving.")
            print "RpcServer exited and no longer serving."
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")
            print "Exception raised when calling exit function at exit of RPC server."

class FileUploader(object):
    def __init__(self, ipv):
        self.writeToStatus = ipv.writeToStatus
        self.instName = ipv.instName
        co = ipv.baseCo
        if not ipv.archiveDir:
            self.srcDir = ipv.ipvDir
        else:
            self.srcDir = ipv.archiveDir
        self.ipvExtension = co.get("FileUpload", "ipvExtension")
        testMode = co.getboolean("FileUpload", "testMode", "False")
        # XML-RPC setup
        if not testMode:
            xmlrpcUriUser = getInnerStr(co.get("FileUpload", "xmlrpcUriUser", "mfgteam"))
            try:
                xmlrpcUriUser = bz2.decompress(eval("\"%s\"" % xmlrpcUriUser))
            except Exception, err:
                self.writeToStatus("Error: %r. Use default XML-RPC login username" % err)
            xmlrpcUriPassword = getInnerStr(co.get("FileUpload", "xmlrpcUriPassword", "PridJaHop4"))
            try:
                xmlrpcUriPassword = bz2.decompress(eval("\"%s\"" % xmlrpcUriPassword))
            except Exception, err:
                self.writeToStatus("Error: %r. Use default XML-RPC login password" % err)
            xmlrpcTxUser = getInnerStr(co.get("FileUpload", "xmlrpcTxUser", "xml_user"))
            try:
                xmlrpcTxUser = bz2.decompress(eval("\"%s\"" % xmlrpcTxUser))
            except Exception, err:
                self.writeToStatus("Error: %r. Use default XML-RPC username" % err)
            xmlrpcTxPassword = getInnerStr(co.get("FileUpload", "xmlrpcTxPassword", "skCyrcFHVZecfD"))
            try:
                xmlrpcTxPassword = bz2.decompress(eval("\"%s\"" % xmlrpcTxPassword))
            except Exception, err:
                self.writeToStatus("Error: %r. Use default XML-RPC password" % err)
            try:
                self.xmlReportSender = ReportSender("http://%s:%s@mfg.picarro.com/xmlrpc/" % (xmlrpcUriUser, xmlrpcUriPassword),
                                                    xmlrpcTxUser, xmlrpcTxPassword)
                self.connectStatus = 1
            except Exception, err:
                self.writeToStatus("Failed to establish XML-RPC interface: %r" % err)
                self.xmlReportSender = None
                self.connectStatus = 0
        else:
            try:
                self.xmlReportSender = ReportSender("http://plucky/xmlrpc/", "picarro", "picarro")
                self.connectStatus = 1
            except Exception, err:
                self.writeToStatus("Failed to establish XML-RPC interface: %r" % err)
                self.xmlReportSender = None
                self.connectStatus = 0

    def getConnectStatus(self):
        return self.connectStatus

    def testConnect(self):
        try:
            if self.xmlReportSender.testConnect() == "OK":
                self.connectStatus = 1
            else:
                self.connectStatus = 0
        except:
            self.connectStatus = 0

    def uploadIPV(self):
        for root, dirs, files in os.walk(self.srcDir):
            for filename in files:
                filepath = os.path.join(root, filename)
                if os.path.basename(filename).split('.')[-1] in self.ipvExtension:
                    try:
                        self._sendFileXmlRpc(filepath)
                    except Exception, err:
                        self.writeToStatus('%r' % err)

    def _sendFileXmlRpc(self, filepath):
        try:
            if os.path.basename(filepath).split("_")[0] == "Report":
                ret = self.xmlReportSender.sendReport(filepath)
            else:
                ret = self.xmlReportSender.sendDiagFile(filepath)
            if ret == "OK":
                os.remove(filepath)
                self.writeToStatus("%s sent via XML-RPC" % (filepath,))
                self.connectStatus = 1
                return
            else:
                self.connectStatus = 0
        except:
            self.connectStatus = 0
        self.writeToStatus("Failed to send %s via XML-RPC" % (filepath,))

class IPV(IPVFrame):
    def __init__(self, configFile, useViewer, *args, **kwds):
        self.useViewer = useViewer
        self.commandQueue = Queue()
        self._processIni(configFile)
        self.eventListener = TextListener.TextListener(None,
                                          BROADCAST_PORT_EVENTLOG,
                                          self._eventFilter,
                                          retry = True,
                                          name = "IPV event log listener", logFunc = Log)
        self.eventDeque = deque()
        self.signalList = [sigName for sigName in self.co if self.co.getboolean(sigName,"enabled")]
        self.numSignals = len(self.signalList)
        self.descrDict = {}
        self.methodDict = {}
        self.setpointDict = {}
        self.toleranceDict = {}
        self.testValDict = {}
        self.statDict = {}
        self.statDescrDict = {}
        self.groupDict = {0:[], 1:[], 2:[]}
        for sigName in self.signalList:
            self.groupDict[self.co.getint(sigName,"group")].append(sigName)
            self.descrDict[sigName] = "  " + self.co.get(sigName,"descr","")
            self.methodDict[sigName] = self._getMethodList(sigName)
            self.setpointDict[sigName] = self._getSetpointList(sigName)
            self.toleranceDict[sigName] = self._getToleranceList(sigName)
            self.testValDict[sigName] = [0.0] * len(self.setpointDict[sigName])
            self.statDict[sigName] = "OK"
            self.statDescrDict[sigName] = ""

        self.numRowsList = []
        for group in self.groupDict:
            self.numRowsList.append(len(self.groupDict[group]))

        self.filters = tables.Filters(complevel=1, fletcher32=True)
        histColDict = {"time":tables.Int64Col(), "date_time":tables.Int64Col(), "idx":tables.Int32Col()}
        for sigName in self.signalList:
            if not sigName.startswith("WlmOffset"):
                histColDict[sigName] = tables.Float32Col(shape=(3,))
        self.histTableType = type("HistTableType",(tables.IsDescription,),histColDict)
        wlmColDict = {"vLaserNum":tables.Int32Col(), "time":tables.Int64Col(), "wlmOffset":tables.Float32Col()}
        self.wlmTableType = type("WlmTableType",(tables.IsDescription,),wlmColDict)
        self.h5 = None
        self.histTable = None
        self.wlmTable = None
        self._shutdownRequested = False
        self.connStatus = 0
        self.connStatusLock = threading.Lock()

        IPVFrame.__init__(self, self.numRowsList, *args, **kwds)
        self.SetTitle("Picarro Instrument Performance Verification (%s, Host Version: %s)" % (self.instName, self.softwareVersion))

        # Fill table with default values
        self._setDefaultResults()

        # Bind button event
        self.Bind(wx.EVT_BUTTON, self.onRunIPV, self.buttonRunIPV)
        self.Bind(wx.EVT_BUTTON, self.onCreateDiagFile, self.buttonCreateDiagFile)
        self.Bind(wx.EVT_BUTTON, self.onUpload, self.buttonUpload)
        self.Bind(wx.EVT_IDLE, self.onIdle)
        self.Bind(wx.EVT_CLOSE, self.onClose)

        # Start the RPC server
        self.startServer()

        # Status broadcaster
        self.IPVStatusBroadcaster = Broadcaster.Broadcaster(BROADCAST_PORT_IPV)

        if self.useViewer:
            self.Show()
        else:
            self.Hide()

        # Set up the file uploader
        self.fUploader = FileUploader(self)

        if self.launchLicense:
            try:
                self.instrCo.set("License", "launch", "False")
                self.instrCo.write()
            except:
                pass
            self.startIPVLicense()

        # If enalbed, start the three major threads
        if self.enabled:
            self.writeToStatus("Starting Time: %s" % time.ctime(self.reportTime))
            self.writeToStatus("Time interval: %.2f hours" % (self.repeatSec/3600.0))
            self.writeToStatus("Will test connectivity every %.2f hours." % self.testConnHrs)
            self.startIPVThread()
            self.startTestConnectionThread()
            self.startBroadcaseStatusThread()
        else:
            self.writeToStatus("IPV disabled")

    def _getTime(self, format=0):
        if format == 0:
            return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(getUTCTime("float")))
        else:
            return time.strftime("%Y%m%d%H%M%S", time.localtime(getUTCTime("float")))

    def _convertTimeStrLocalToGMT(self, timeStr, formatIn="%Y-%m-%d %H:%M:%S", formatOut="%Y-%m-%d %H:%M:%S"):
        return time.strftime(formatOut, time.gmtime(time.mktime(time.strptime(timeStr, formatIn))))

    def _eventFilter(self, data):
        """Listener filter for event logs"""
        try:
            index,eventTime,source,level,code,desc = [s.strip() for s in data.split("|",6)]
            level = level[1:]
            logDate, logTime = [s.strip() for s in self._convertTimeStrLocalToGMT(eventTime).split()]
            eventTuple = (index, logDate, logTime, source, level, desc)
            # Level 1.5 = info only; message shows on both GUI and EventLog
            if float(level) >= 2:
                self.eventDeque.append(eventTuple)
            while len(self.eventDeque) > self.maxNumbEventLogs:
                self.eventDeque.popleft()
        except:
            tbMsg = traceback.format_exc()
            Log("Listener Exception", data=dict(Note = "<See verbose for debug info>"), level=3, verbose=tbMsg)

    def writeToStatus(self, message):
        self.statusMessage.append("%s   %s\n" % (self._getTime(), message,))
        self.statusMessage = self.statusMessage[-30:]
        self.textCtrlStatus.SetValue("".join(self.statusMessage))
        self.textCtrlStatus.SetInsertionPointEnd()
        Log(message)

    def _mergeConfig(self):
        if not self.instrCo:
            return
        else:
            for section in self.baseCo.list_sections():
                for option in self.baseCo.list_options(section):
                    try:
                        if self.instrCo.has_option(section, option):
                            print "[%s][%s] was overwritten" % (section, option)
                            self.baseCo.set(section, option, self.instrCo.get(section, option))
                    except:
                        pass

    def _processIni(self, configFile):
        self.statusMessage = []
        self.baseCo = CustomConfigObj(configFile, list_values = True)
        basePath = os.path.split(configFile)[0]
        self.instrCoFilename = os.path.join(basePath, self.baseCo.get("Main", "instrConfigPath"))
        try:
            self.instrCo = CustomConfigObj(self.instrCoFilename, list_values = True)
        except:
            self.instrCo = None
        self._mergeConfig()
        self.enabled = self.baseCo.getboolean("Main", "enabled", False)

        # IPV license program
        try:
            self.launchLicense = self.baseCo.getboolean("License", "launch", False)
            self.licenseTrialDays = self.baseCo.getfloat("License", "trialDays", 90.0)
            self.licenseRemindDays = self.baseCo.getfloat("License", "remindDays", 3.0)
        except:
            self.launchLicense = False
            self.licenseTrialDays = 90.0
            self.licenseRemindDays = 3.0

        self.ipvDir = os.path.abspath(self.baseCo.get("Main", "ipvDir", DEFAULT_IPV_DIR))
        if not os.path.isdir(self.ipvDir):
            os.makedirs(self.ipvDir)
        self.diagFilePrefix = os.path.join(self.ipvDir, self.baseCo.get("Main", "diagFilePrefix", "Diag"))
        self.reportFilePrefix = os.path.join(self.ipvDir, self.baseCo.get("Main", "reportFilePrefix", "Report"))
        self.instType = CRDS_Driver.fetchInstrInfo("analyzer")
        self.instName = self.instType + CRDS_Driver.fetchInstrInfo("analyzernum")

        self.softwareVersion = CRDS_Driver.allVersions()["host release"]

        if 'Internal' in self.softwareVersion:
            Log("self.softwareVersion = '%s'" % self.softwareVersion)
            match = INTERNAL_VERSION_RX.match(self.softwareVersion)
            assert match is not None

            self.softwareVersion = "Internal-%s-0-0" % match.group(1)

        self.useUTC = self.baseCo.getboolean("Main", "useUTC", True)
        self.requiredDataHrs = self.baseCo.getfloat("Main", "requiredDataHrs", 12.0)
        self.startTime = self.baseCo.get("Main", "startTime", "00:00:00")
        self.repeatSec = 3600 * self.baseCo.getfloat("Main", "repeatHrs", 6.0)
        assert self.repeatSec > 60, "The repeated time must be longer than 1 minute"
        self.reportTime = getSpecUTC(self.startTime, "float")
        currTime = getUTCTime("float")
        while currTime > self.reportTime:
            self.reportTime += self.repeatSec
        print "Starting Time: %s" % time.ctime(self.reportTime)
        self.testConnHrs = self.baseCo.getfloat("Main", "testConnHrs", 0.5)

        # Set up archiver to manage local IPV files
        self.ipvArchiveGroupName = self.baseCo.get("IPVBackup", "archiveGroupName", "")
        if self.ipvArchiveGroupName:
            self.archiveDir = CRDS_Archiver.GetGroupInfo(self.ipvArchiveGroupName)["StorageDir"]
        else:
            self.archiveDir = None

        # Event logging
        self.maxNumbEventLogs = self.baseCo.getint("Main", "maxNumbEventLogs", 10)

        # Flatten the ini file
        try:
            newCo = self.baseCo[self.instType]
            for sig in self.baseCo["Common"]:
                if sig not in newCo:
                    newCo[sig] = self.baseCo["Common"][sig]
            self.co = CustomConfigObj(newCo)
        except:
            self.co = CustomConfigObj(self.baseCo["Common"])

    def enqueueViewerCommand(self, command, *args, **kwargs):
        self.commandQueue.put((command, args, kwargs))

    def startServer(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_IPV),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True)
        self.rpcServer.register_function(self.getIPVReport)
        self.rpcServer.register_function(self.uploadIPV)
        self.rpcServer.register_function(self.createDiagFile)
        self.rpcServer.register_function(self.shutdown)
        self.rpcServer.register_function(self.showViewer)
        self.rpcServer.register_function(self.hideViewer)
        self.rpcServer.register_function(self.getConnectStatus)
        # Start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.shutdown)
        self.rpcThread.start()

    def getConnectStatus(self):
        return self.fUploader.getConnectStatus()

    def shutdown(self):
        self.Destroy()
        self._shutdownRequested = True

    def archiveFile(self, filepath):
        if not self.ipvArchiveGroupName:
            return
        self.writeToStatus("Archiving %s to %s" % (filepath, self.archiveDir))
        try:
            CRDS_Archiver.ArchiveFile(self.ipvArchiveGroupName, filepath, removeOriginal=True)
        except Exception, err:
            self.writeToStatus("%r" % err)

    def getIPVReport(self, auto):
        ipvStatus = self._updateIPV()
        if ipvStatus[0]:
            self._writeReport()
            if auto:
                if not ipvStatus[1]:
                    self.onCreateDiagFile(None)
                self.uploadIPV()

    def uploadIPV(self):
        self.writeToStatus("Uploading IPV reports...")
        self.connStatusLock.acquire()
        try:
            self.fUploader.uploadIPV()
            self.connStatus = self.getConnectStatus()
        except:
            pass
        finally:
            self.connStatusLock.release()

    def createDiagFile(self):
        self._createH5File()
        self._writeH5File()

    def showViewer(self):
        self.Show()

    def hideViewer(self):
        self.Hide()

    def runLicense(self):
        f = os.popen("C:\Picarro\G2000\HostExe\IPVLicense.exe -s 0 -r %f -t %f -c %s" % (self.licenseRemindDays, self.licenseTrialDays, self.instrCoFilename), "r")
        f.read()

    def startIPVLicense(self):
        appThread = threading.Thread(target = self.runLicense)
        appThread.setDaemon(True)
        appThread.start()

    def startIPVThread(self):
        appThread = threading.Thread(target = self.runIPV)
        appThread.setDaemon(True)
        appThread.start()

    def startTestConnectionThread(self):
        appThread = threading.Thread(target = self.testConnection)
        appThread.setDaemon(True)
        appThread.start()

    def startBroadcaseStatusThread(self):
        appThread = threading.Thread(target = self.broadcastStatus)
        appThread.setDaemon(True)
        appThread.start()

    def runIPV(self):
        while not self._shutdownRequested:
            currTime = getUTCTime("float")
            if currTime > self.reportTime:
                self.getIPVReport(auto=True)
                self.reportTime += self.repeatSec
                time.sleep(self.repeatSec-60)
            else:
                if (self.reportTime-currTime) > 60:
                    time.sleep(self.reportTime-currTime-60)
                else:
                    time.sleep(10)

    def testConnection(self):
        while not self._shutdownRequested:
            self.connStatusLock.acquire()
            try:
                self.fUploader.testConnect()
                self.connStatus = self.getConnectStatus()
            except:
                pass
            finally:
                self.connStatusLock.release()
            time.sleep(3600 * self.testConnHrs)

    def broadcastStatus(self):
        while not self._shutdownRequested:
            self.connStatusLock.acquire()
            self.IPVStatusBroadcaster.send("%d,%f\n" % (self.connStatus, time.time()))
            self.connStatusLock.release()
            time.sleep(100)

    def onClose(self,event):
        self.hideViewer()

    def onIdle(self,event):
        while not self.commandQueue.empty():
            func, args, kwargs = self.commandQueue.get()
            func(*args, **kwargs)
        event.Skip()

    def onRunIPV(self, event):
        self.getIPVReport(auto=False)

    def onCreateDiagFile(self, event):
        self.createDiagFile()

    def onUpload(self, event):
        self.uploadIPV()

    def _updateIPV(self):
        self._disableButtons()
        currTime = time.strftime("%Y/%m/%d  %H:%M:%S", time.localtime())
        self.enqueueViewerCommand(self.textCtrlTimestamp.SetValue, currTime)

        self.endDatetime = datetime.now()
        if self.useUTC:
            offset = datetime.utcnow() - datetime.now()
            self.endDatetime += offset

        # Dict for H5 file
        self.dataDict = {}
        self.wlmDataDict = {}
        # Dict for data verification
        self.sigValueDict = {}

        ipvFinished = True
        allOK = True
        for group in self.groupDict:
            for rowIdx in range(self.numRowsList[group]):
                sigName = self.groupDict[group][rowIdx]
                dataDurHrs = max(0.1, self.co.getfloat(sigName,"durationHrs",6.0))
                startDatetime = self.endDatetime - timedelta(hours=dataDurHrs)
                startTimestamp = timestamp.datetimeToTimestamp(startDatetime)
                endTimestamp = timestamp.datetimeToTimestamp(self.endDatetime)
                timeLimits = [startTimestamp, endTimestamp]
                level = 2
                reqNumData =  int(self.requiredDataHrs*3600*10**(-level))
                actNumData = self._estNumData(sigName, level, endTimestamp)
                if reqNumData > (actNumData+1):
                    self.writeToStatus("Insufficient analyzer data for IPV analysis.")
                    print "Insufficient analyzer data for IPV analysis."
                    ipvFinished = False
                    allOK = False
                    self._enableButtons()
                    return (ipvFinished , allOK)
                if sigName.startswith("WlmOffset"):
                    self._readWlmDatabase(sigName, timeLimits)
                else:
                    self._readHistoryDatabase(sigName, timeLimits)
        allOK = self._verifySignals()
        self._enableButtons()
        return (ipvFinished , allOK)

    def _writeReport(self):
        if self.useUTC:
            endTime = datetime.strftime(self.endDatetime, "%Y%m%d%H%M%SZ")
        else:
            endTime = datetime.strftime(self.endDatetime, "%Y%m%d%H%M%S")
        self.reportFilename = "%s_%s_Host_%s_%s.csv" % (self.reportFilePrefix, self.instName, self.softwareVersion, endTime)
        print "softwareVersion = '%s'" % self.softwareVersion
        print "reportFilename = '%s'" % self.reportFilename
        linesToWrite = []
        linesToWrite.append(REPORT_FORMAT % ("Signal","Status","Action","Method","Set Point","Tolerance","Value"))
        for group in self.groupDict:
            for rowIdx in range(self.numRowsList[group]):
                sigName = self.groupDict[group][rowIdx]
                linesToWrite.append(REPORT_FORMAT % (sigName,
                                                     self.statDict[sigName],
                                                     self.statDescrDict[sigName],
                                                     listToString(self.methodDict[sigName]),
                                                     floatListToString(self.setpointDict[sigName], 3),
                                                     floatListToString(self.toleranceDict[sigName], 4),
                                                     floatListToString(self.testValDict[sigName], 4))
                                    )
        # Add event logs to the end if any:
        if len(self.eventDeque) > 0:
            linesToWrite.append("\n[EVENTS]\n")
            linesToWrite.append(EVENTLOG_FORMAT % ("Index","Date","Time","Source","Level","Description"))
            while len(self.eventDeque) > 0:
                eventTuple = self.eventDeque.popleft()
                linesToWrite.append(EVENTLOG_FORMAT % eventTuple)

        try:
            fd = open(self.reportFilename, "w")
            fd.writelines(linesToWrite)
            fd.close()
            # Archive the output file
            self.archiveFile(self.reportFilename)
        except Exception, err:
            self.writeToStatus("%r" % err)

    def _getMethodList(self, sigName):
        methodList = self.co.get(sigName,"method","")
        assert len(methodList) > 0, "No method specified for %s" % sigName
        if type(methodList) != type([]):
            methodList = [methodList]
        return methodList

    def _getSetpointList(self, sigName):
        setpointList = self.co.get(sigName,"setpoint","")
        assert len(setpointList) > 0, "No setpoint specified for %s" % sigName
        if type(setpointList) != type([]):
            setpointList = [setpointList]
        retList = []
        for setpoint in setpointList:
            try:
                retList.append(CRDS_Driver.rdDasReg(setpoint))
            except:
                retList.append(float(setpoint))
        return retList

    def _getToleranceList(self, sigName):
        toleranceList = self.co.get(sigName,"tolerance","")
        assert len(toleranceList) > 0, "No tolerance specified for %s" % sigName
        if type(toleranceList) != type([]):
            toleranceList = [toleranceList]
        retList = []
        for tolerance in toleranceList:
            try:
                retList.append(CRDS_Driver.rdDasReg(tolerance))
            except:
                retList.append(float(tolerance))
        return retList

    def _disableButtons(self):
        self.enqueueViewerCommand(self.buttonRunIPV.Enable, False)
        self.enqueueViewerCommand(self.buttonCreateDiagFile.Enable, False)
        self.enqueueViewerCommand(self.buttonUpload.Enable, False)

    def _enableButtons(self):
        self.enqueueViewerCommand(self.buttonRunIPV.Enable, True)
        self.enqueueViewerCommand(self.buttonCreateDiagFile.Enable, True)
        self.enqueueViewerCommand(self.buttonUpload.Enable, True)

    def _setDefaultResults(self):
        for group in self.groupDict:
            for rowIdx in range(self.numRowsList[group]):
                sigName = self.groupDict[group][rowIdx]
                self.enqueueViewerCommand(self.gridList[group].SetCellValue,rowIdx,0,"UNKNOWN")
                self.enqueueViewerCommand(self.gridList[group].SetCellAlignment,rowIdx,0,wx.ALIGN_CENTRE,wx.ALIGN_CENTRE)
                self.enqueueViewerCommand(self.gridList[group].SetCellFont,rowIdx,0,wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD))
                self.enqueueViewerCommand(self.gridList[group].SetRowLabelValue,rowIdx, self.co.get(sigName,"title",sigName))

    def _readHistoryDatabase(self, sigName, timeLimits):
        sqlCommand = "select time,idx,streamNum,value,minVal,maxVal from history" +\
                     " where level=? and time >= ? and time <= ? and streamNum=?"
        sqlArgs = (DB_LEVEL, timeLimits[0], timeLimits[1], NAME_TO_STREAM_NUM_DICT[sigName])
        values = CRDS_Driver.getHistoryByCommand(sqlCommand, sqlArgs)
        self.sigValueDict[sigName] = {"time":[], "value":[], "min":[], "max":[]}
        if len(values) > 0:
            for data in values:
                dTime = data[0]
                idx = data[1]
                if idx not in self.dataDict:
                    self.dataDict[idx] = {"time":dTime}
                else:
                    self.dataDict[idx]["time"] = max(self.dataDict[idx]["time"], dTime)
                self.dataDict[idx][sigName] = tuple(data[3:])
                self.dataDict[idx]["date_time"] = timestamp.unixTime(self.dataDict[idx]["time"])
                self.sigValueDict[sigName]["time"].append(data[0])
                self.sigValueDict[sigName]["value"].append(data[3])
                self.sigValueDict[sigName]["min"].append(data[4])
                self.sigValueDict[sigName]["max"].append(data[5])

    def _readWlmDatabase(self, sigName, timeLimits):
        vLaserNum = int(sigName[9:])
        sqlCommand = "select timestamp,vLaserNum,wlmOffset from wlmHistory" +\
                     " where timestamp >= ? and timestamp <= ? and vLaserNum=?"
        sqlArgs = (timeLimits[0], timeLimits[1], vLaserNum)
        values = CRDS_Driver.getHistoryByCommand(sqlCommand, sqlArgs)
        self.sigValueDict[sigName] = {"time":[], "value":[]}
        wlmDataIdx = 0
        if len(values) > 0:
            for data in values:
                self.wlmDataDict[wlmDataIdx]={"vLaserNum": vLaserNum}
                self.wlmDataDict[wlmDataIdx]["time"] = data[0]
                self.wlmDataDict[wlmDataIdx]["wlmOffset"] = data[2]
                self.sigValueDict[sigName]["time"].append(data[0])
                self.sigValueDict[sigName]["value"].append(data[2])
                wlmDataIdx += 1

    def _estNumData(self, sigName, level, endTime):
        startTime = endTime - (self.requiredDataHrs*3600*1000)
        sqlCommand = "select time from history" +\
                     " where level=? and time >= ? and time <= ? and streamNum=?"
        sqlArgs = (level, startTime, endTime, NAME_TO_STREAM_NUM_DICT[sigName])
        values = CRDS_Driver.getHistoryByCommand(sqlCommand, sqlArgs)
        return len(values)

    def _getSlope(self, timeList, valList):
        try:
            return numpy.polyfit(numpy.array(timeList), numpy.array(valList), 1)[0]
        except Exception, err:
            print "%r" % err
            return 0.0

    def _verifySignals(self):
        allOK = True
        for group in self.groupDict:
            for rowIdx in range(self.numRowsList[group]):
                sigName = self.groupDict[group][rowIdx]
                try:
                    if not self._verifyEachSignal(sigName, group, rowIdx):
                        allOK = False
                except Exception, err:
                    self.writeToStatus("%r" % err)
                    print "%r" % err
        return allOK

    def _verifyEachSignal(self, sigName, group, rowIdx):
        methodList = self.methodDict[sigName]
        result = []
        for idx in range(len(methodList)):
            method = methodList[idx].lower()
            if method not in ["min", "max", "mean", "std", "slope", "variation"]:
                return
            setpoint = self.setpointDict[sigName][idx]
            tolerance = self.toleranceDict[sigName][idx]
            timeList = self.sigValueDict[sigName]["time"]
            valList =self.sigValueDict[sigName]["value"]
            minList =self.sigValueDict[sigName]["min"]
            maxList =self.sigValueDict[sigName]["max"]
            if method == "mean":
                testVal = numpy.mean(valList)
                if abs(testVal-setpoint) > tolerance:
                    result.append("Failed")
                else:
                    result.append("OK")
            elif method == "std":
                testVal =numpy.std(valList)
                if testVal > (tolerance + setpoint):
                    result.append("Failed")
                else:
                    result.append("OK")
            elif method == "variation":
                testVal = numpy.std(valList)/numpy.mean(valList)
                if abs(testVal-setpoint) > tolerance:
                    result.append("Failed")
                else:
                    result.append("OK")
            elif method == "min":
                testVal = min(minList)
                if testVal < (setpoint-tolerance):
                    result.append("Failed")
                else:
                    result.append("OK")
            elif method == "max":
                testVal = max(maxList)
                if testVal > (setpoint+tolerance):
                    result.append("Failed")
                else:
                    result.append("OK")
            elif method == "slope":
                testVal = self._getSlope(timeList, valList)
                if abs(testVal-setpoint) > tolerance:
                    result.append("Failed")
                else:
                    result.append("OK")

            self.testValDict[sigName][idx] = testVal

        if "Failed" in result:
            self.statDict[sigName] = "WARNING"
            self.statDescrDict[sigName] = self.descrDict[sigName]
            self.enqueueViewerCommand(self.gridList[group].SetCellValue,rowIdx,0,"WARNING")
            self.enqueueViewerCommand(self.gridList[group].SetCellBackgroundColour,rowIdx,0,"yellow")
            self.enqueueViewerCommand(self.gridList[group].SetCellValue,rowIdx,1,self.descrDict[sigName])
            self.enqueueViewerCommand(self.gridList[group].SetCellTextColour,rowIdx,1,"red")
            okStatus = False
        else:
            self.statDict[sigName] = "OK"
            self.statDescrDict[sigName] = ""
            self.enqueueViewerCommand(self.gridList[group].SetCellValue,rowIdx,0,"OK")
            self.enqueueViewerCommand(self.gridList[group].SetCellBackgroundColour,rowIdx,0,"green")
            self.enqueueViewerCommand(self.gridList[group].SetCellValue,rowIdx,1,"")
            self.enqueueViewerCommand(self.gridList[group].SetCellTextColour,rowIdx,1,"black")
            okStatus = True

        return okStatus

    def _createH5File(self):
        if self.histTable != None:
            self.histTable.flush()
        if self.wlmTable != None:
            self.wlmTable.flush()
        if self.h5 != None:
            self.h5.close()
        if self.useUTC:
            endTime = datetime.strftime(self.endDatetime, "%Y%m%d%H%M%SZ")
        else:
            endTime = datetime.strftime(self.endDatetime, "%Y%m%d%H%M%S")
        self.h5Filename = "%s_%s_Host_%s_%s.h5" % (self.diagFilePrefix, self.instName, self.softwareVersion, endTime)
        try:
            self.h5 = tables.openFile(self.h5Filename, mode="w", title="Picarro IPV File")
        except Exception, err:
            self.writeToStatus("%r" % err)
            self.h5 = None
        self.histTable = None
        self.wlmTable = None

    def _closeH5File(self):
        if self.histTable != None:
            self.histTable.flush()
        if self.wlmTable != None:
            self.wlmTable.flush()
        if self.h5 != None:
            self.h5.close()

        # Archive the H5 file
        self.archiveFile(self.h5Filename)

        self.h5 = None
        self.histTable = None
        self.wlmTable = None

    def _writeH5File(self):
        if self.h5 != None:
            self.histTable = self.h5.createTable("/", "IPV_%dSec" % 10**DB_LEVEL, self.histTableType, filters=self.filters)
            row = self.histTable.row
            for idx in self.dataDict:
                for key in self.dataDict[idx]:
                    row[key] = self.dataDict[idx][key]
                row["idx"] = idx
                row.append()
            self.histTable.flush()

            self.wlmTable = self.h5.createTable("/", "IPV_WLM", self.wlmTableType, filters=self.filters)
            row = self.wlmTable.row
            for idx in self.wlmDataDict:
                for key in self.wlmDataDict[idx]:
                    row[key] = self.wlmDataDict[idx][key]
                row.append()
            self.wlmTable.flush()
            self._closeH5File()
        else:
            return

HELP_STRING = \
"""

IPV.py [-h] [-c <FILENAME>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.

"""

def PrintUsage():
    print HELP_STRING

def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hvc:", ["help","viewer"])
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
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    useViewer = "-v" in options or "--viewer" in options

    return configFile, useViewer

if __name__ == "__main__":
    ipvApp = SingleInstance("PicarroIPV")
    if ipvApp.alreadyrunning():
        try:
            CRDS_IPV = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_IPV,
                                                  APP_NAME,
                                                  IsDontCareConnection = False)
            CRDS_IPV.showViewer()
        except:
            pass
    else:
        configFile, useViewer = HandleCommandSwitches()
        app = wx.PySimpleApp()
        wx.InitAllImageHandlers()
        frame = IPV(configFile, useViewer, None, -1, "")
        app.SetTopWindow(frame)
        if useViewer:
            frame.Show()
        app.MainLoop()
