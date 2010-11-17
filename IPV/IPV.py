#!/usr/bin/python
#
# File Name: IPV.py
# Purpose: Picarro Instrument Performance Verification
#
# File History:
# 10-06-26 alex  Created

APP_NAME = "IPV"
APP_DESCRIPTION = "Instrument Performance Verification"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "IPV.ini"

import sys
import os
import sqlite3
import tables
import wx
import time
import threading
import paramiko
from Queue import Queue
from numpy import *
from datetime import datetime, timedelta 
from IPVFrame import IPVFrame
from Host.autogen import interface
from Host.Common import timestamp
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_ARCHIVER, RPC_PORT_IPV
from Host.Common import CmdFIFO
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME,DontCareConnection = False)

DB_LEVEL = 2
# level 0 = 1 sec; level 1 = 10 sec; level 2 = 100 sec; ...
REPORT_FORMAT = "%-30s,%-10s,%-30s,%-30s,%-65s,%-65s,%-65s\n"
STREAM_NUM_TO_NAME_DICT = {}
NAME_TO_STREAM_NUM_DICT = {}
for streamNum in interface.STREAM_MemberTypeDict:
    STREAM_NUM_TO_NAME_DICT[streamNum] = interface.STREAM_MemberTypeDict[streamNum][7:]
    NAME_TO_STREAM_NUM_DICT[interface.STREAM_MemberTypeDict[streamNum][7:]] = streamNum

UNIXORIGIN = datetime(1970,1,1,0,0,0,0)

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
    def __init__(self, configFile):
        co = CustomConfigObj(configFile, list_values = True)
        self.ipvDir = os.path.abspath(co.get("FileUpload", "ipvDir"))
        self.ipvRemoteDir = co.get("FileUpload", "ipvRemoteDir")
        self.ipvExtension = co.get("FileUpload", "ipvExtension")
        self.ipvArchiveGroupName = co.get("IPVBackup", "archiveGroupName")
        self.rdfDir = os.path.abspath(co.get("FileUpload", "rdfDir"))
        self.rdfRemoteDir = co.get("FileUpload", "rdfRemoteDir", "")
        self.rdfArchiveGroupName = co.get("RDFBackup", "archiveGroupName")
        
        #self._mkRemoteDir(self.ipvRemoteDir)
        #self._mkRemoteDir(self.rdfRemoteDir)
        #try:
        #    self.ipvBackupDir = os.path.abspath(co.get("FileUpload", "ipvBackupDir"))
        #    if not os.path.isdir(self.ipvBackupDir):
        #        os.makedirs(self.ipvBackupDir)
        #except:
        #    self.ipvBackupDir = None
            
        # Build the channel and client to the remote server
        self.sftpClient = None
        try:
            host = co.get("FileUpload", "host")
            user = co.get("FileUpload", "user")
            password = co.get("FileUpload", "password")
            channel = paramiko.Transport((host, 22))
            channel.connect(username=user, password=password)
            self.sftpClient = paramiko.SFTPClient.from_transport(channel)
        except Exception, err:
            print "%r" % err
        # Some useful available functions of self.sftpClient include:
        # close(self)
        # get_channel(self)
        # listdir(self, path='.')
        # listdir_attr(self, path='.')
        # open(self, filename, mode='r', bufsize=-1)
        # remove(self, path)
        # rename(self, oldpath, newpath)
        # mkdir(self, path, mode=0777)
        # rmdir(self, path)
        # stat(self, path)
        # lstat(self, path)
        # chdir(self, path)
        # utime(self, path, times): 
        # truncate(self, path, size): 
        # getcwd(self)
        # put(self, localpath, remotepath, callback=None)
        # get(self, remotepath, localpath, callback=None)
        
    def uploadAndArchiveIPV(self):
        for root, dirs, files in os.walk(self.ipvDir):
            for filename in files:
                filepath = os.path.join(root, filename)
                if os.path.basename(filename).split('.')[-1] in self.ipvExtension:
                    try:
                        self._uploadAndArchiveFile(filepath, self.ipvRemoteDir, self.ipvArchiveGroupName, True)
                    except OSError,errorMsg:
                        Log('%r' % (errorMsg))

    def uploadAndArchiveRDF(self, timeLimits):
        rdfFilelist = self._searchRdfFiles(timeLimits)
        for filepath in rdfFilelist:
            try:
                self._uploadAndArchiveFile(filepath, self.rdfRemoteDir, self.rdfArchiveGroupName, False)
            except OSError,errorMsg:
                Log('%r' % (errorMsg))
            
    def _uploadAndArchiveFile(self, filepath, remoteDir = "", archiveGroupName = "", removeOriginal = True):
        (dir, filename) = os.path.split(filepath)
        filepath = filepath.replace("\.", "").replace("\\", "/")
        if remoteDir:
            remoteFilepath = os.path.join(remoteDir, filename).replace("\.", "").replace("\\", "/")
            print "Uploading %s to %s" % (filepath, remoteFilepath)
            s = None
            try:
                startTime = time.time()
                s = self.sftpClient.put(filepath, remoteFilepath)
                endTime = time.time()
                uploadTime = endTime - startTime
            except Exception, err:
                print "%r" % err
            if s != None:
                print "Finished uploading %.2f bytes in %.2f seconds" % (s.st_size, uploadTime)
            else:
                print "Failed uploading"
                
        if archiveGroupName:
            print "Archiving %s" % (filepath,)
            try:
                CRDS_Archiver.ArchiveFile(archiveGroupName, filepath, removeOriginal)
            except Exception, err:
                print "%r" % err
            
    def _searchRdfFiles(self, timeLimits):
        fileList = []
        try:
            for root, dirs, files in os.walk(self.rdfDir):
                for filename in files:
                    filepath = os.path.join(root,filename)
                    fileMtime = os.path.getmtime(filepath)
                    if (fileMtime > timeLimits[0] and fileMtime < timeLimits[1]):
                        fileList.append(filepath)
        except Exception, err:
            print err
        #print fileList
        return fileList

    def _mkRemoteDir(self, remoteDir):
        childrenRemoteDirList = []
        parentRemoteDir = remoteDir
        successful = False
        while not successful:
            try:
                s = self.sftpClient.listdir(parentRemoteDir)
                successful = True
            except Exception, err:
                (parentRemoteDir, child) = os.path.split(parentRemoteDir)
                childrenRemoteDirList.append(child)
        if len(childrenRemoteDirList) > 0:
            newPath = parentRemoteDir
            for i in range (len(childrenRemoteDirList)-1, -1, -1):
                newPath = newPath+"/"+childrenRemoteDirList[i]
                self.sftpClient.mkdir(newPath)
                
class IPV(IPVFrame):
    def __init__(self, configFile, useViewer, *args, **kwds):
        self.useViewer = useViewer
        self.commandQueue = Queue()
        self._processIni(configFile)
        self.fUploader = FileUploader(configFile)
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
        
        IPVFrame.__init__(self, self.numRowsList, *args, **kwds)
        self.SetTitle("Picarro Instrument Performance Verification (%s, Host Verseion: %s)" % (self.instName, self.softwareVersion))
        self._writeToStatus("Starting Time: %s" % time.ctime(self.reportTime))
        self._writeToStatus("Time interval: %.2f hours" % (self.repeatSec/3600.0))
                
        # Fill table with default values
        self._setDefaultResults()
                
        # Bind button event
        self.Bind(wx.EVT_BUTTON, self.onRunIPV, self.buttonRunIPV)
        self.Bind(wx.EVT_BUTTON, self.onCreateDiagFile, self.buttonCreateDiagFile)
        self.Bind(wx.EVT_BUTTON, self.onUploadAndArchive, self.buttonUploadAndArchive)
        self.Bind(wx.EVT_IDLE, self.onIdle)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        
        # Start the RPC server
        self.startServer()
        
        if self.useViewer:
            self.Show()
        else:
            self.Hide()
            
    def _getTime(self, format=0):
        if format == 0:
            return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(getUTCTime("float")))
        else:
            return time.strftime("%Y%m%d%H%M%S", time.localtime(getUTCTime("float")))
            
    def _writeToStatus(self, message):
        self.statusMessage.append("%s   %s\n" % (self._getTime(), message,))
        self.statusMessage = self.statusMessage[-30:]
        self.textCtrlStatus.SetValue("".join(self.statusMessage))
        
    def _processIni(self, configFile):
        self.statusMessage = []
        co = CustomConfigObj(configFile, list_values = True)
        self.diagFilePrefix = co.get("Main", "diagFilePrefix", "C:/UserData/IPV/Diag")
        dirName = os.path.dirname(self.diagFilePrefix)
        if not os.path.isdir(dirName):
            os.mkdir(dirName)
        self.reportFilePrefix = co.get("Main", "reportFilePrefix", "C:/UserData/IPV/Report")
        self.instType = CRDS_Driver.fetchInstrInfo("analyzer")
        self.instName = self.instType + CRDS_Driver.fetchInstrInfo("analyzernum")
        self.softwareVersion = CRDS_Driver.allVersions()["host release"]
        self.useUTC = co.getboolean("Main", "useUTC", True)
        self.rdfDurationHrs = co.getfloat("Main", "rdfDurationHrs", 6.0)
        self.requiredDataHrs = co.getfloat("Main", "requiredDataHrs", 12.0)
        self.startTime = co.get("Main", "startTime", "00:00:00")
        self.repeatSec = 3600 * co.getfloat("Main", "repeatHrs", 6.0)
        assert self.repeatSec > 60, "The repeated time must be longer than 1 minute"
        self.reportTime = getSpecUTC(self.startTime, "float")
        currTime = getUTCTime("float")
        while currTime > self.reportTime:
            self.reportTime += self.repeatSec
        print "Starting Time: %s" % time.ctime(self.reportTime)
            
        dbFilename = co.get("Main", "dbFilename")
        # Flatten the ini file
        newCo = co[self.instType]
        for sig in co["Common"]:
            if sig not in newCo:
                newCo[sig] = co["Common"][sig]
        self.co = CustomConfigObj(newCo)
        
    def enqueueViewerCommand(self, command, *args, **kwargs):
        self.commandQueue.put((command, args, kwargs))
        
    def startServer(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_IPV),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True)
        self.rpcServer.register_function(self.getIPVReport)
        self.rpcServer.register_function(self.uploadAndArchiveIPV)
        self.rpcServer.register_function(self.uploadAndArchiveRDF)
        self.rpcServer.register_function(self.createDiagFile)
        self.rpcServer.register_function(self.shutdown)
        self.rpcServer.register_function(self.showViewer)
        self.rpcServer.register_function(self.hideViewer)
        # Start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.shutdown)
        self.rpcThread.start()
        
    def shutdown(self):
        self.Destroy()
        self._shutdownRequested = True
        
    def getIPVReport(self, auto):
        ipvStatus = self._updateIPV()
        if ipvStatus[0]:
            self._writeReport()
            if not ipvStatus[1] and auto:
                self.onCreateDiagFile(None)
                self.onUploadAndArchive(None)
            
    def uploadAndArchiveIPV(self):
        self._writeToStatus("Archiving and/or uploading IPV reports...")
        self.fUploader.uploadAndArchiveIPV()
  
    def uploadAndArchiveRDF(self):
        self._writeToStatus("Archiving and/or uploading RDF files...")
        self.fUploader.uploadAndArchiveRDF(self.rdfUnixTimeLimits)
        
    def createDiagFile(self):
        self._createH5File()
        self._writeH5File()
        log("Diagnostic file saved as: %s"%self.h5Filename)
        self._writeToStatus("Diagnostic file saved as: %s"%self.h5Filename)
        print "Diagnostic file saved as: %s"%self.h5Filename
        #d = wx.MessageDialog(None,"Diagnostic file saved as:\n\n%s\n\n"%self.h5Filename, "Diagnostic File Saved", \
        #style=wx.OK | wx.ICON_INFORMATION | wx.STAY_ON_TOP)
        #d.ShowModal()
        #d.Destroy()
        
    def showViewer(self):
        self.Show()
      
    def hideViewer(self):
        self.Hide()
        
    def startIPVThread(self):
        appThread = threading.Thread(target = self.runIPV)
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
        
    def onUploadAndArchive(self, event):
        self.uploadAndArchiveIPV()
        self.uploadAndArchiveRDF()
        
    def _updateIPV(self):
        self._disableButtons()
        currTime = time.strftime("%Y/%m/%d  %H:%M:%S", time.localtime())
        self.enqueueViewerCommand(self.textCtrlTimestamp.SetValue, currTime)
        
        self.endDatetime = datetime.now()
        if self.useUTC:
            offset = datetime.utcnow() - datetime.now()
            self.endDatetime += offset 
        rdfStartDatetime = self.endDatetime - timedelta(hours=self.rdfDurationHrs)

        # Time range (Unix time) for RDF data retrieval
        self.rdfUnixTimeLimits = [datetimeToUnixTime(rdfStartDatetime), datetimeToUnixTime(self.endDatetime)]
        
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
                dataDurHrs = max(1.0, self.co.getfloat(sigName,"durationHrs",6.0))
                startDatetime = self.endDatetime - timedelta(hours=dataDurHrs)
                startTimestamp = timestamp.datetimeToTimestamp(startDatetime)
                endTimestamp = timestamp.datetimeToTimestamp(self.endDatetime)
                timeLimits = [startTimestamp, endTimestamp]
                level = 2
                reqNumData =  int(self.requiredDataHrs*3600*10**(-level))
                actNumData = self._estNumData(sigName, level, endTimestamp)
                if reqNumData > (actNumData+1):
                    self._writeToStatus("Analyzer not stabilized yet.")
                    print "Analyzer not stabilized yet."
                    ipvFinished = False
                    allOK = False
                    #d = wx.MessageDialog(None, "Analyzer not stabilized yet. Please run IPV later.", "Analyzer not stabilized", wx.OK|wx.ICON_ERROR)
                    #d.ShowModal()
                    #d.Destroy()
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
        endTime = datetime.strftime(self.endDatetime, "%Y%m%d%H%M%S")
        self.reportFilename = "%s_%s_Host_%s_%s.csv" % (self.reportFilePrefix, self.instName, self.softwareVersion, endTime)
        linesToWrite = [REPORT_FORMAT % ("Signal","Status","Action","Method","Set Point","Tolerance","Value")]
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
        try:
            fd = open(self.reportFilename, "w")
            fd.writelines(linesToWrite)
            fd.close()
            log("Summary report saved as: %s"%self.reportFilename)
            self._writeToStatus("Summary report saved as: %s"%self.reportFilename)
            print "Summary report saved as: %s"%self.reportFilename
            #d = wx.MessageDialog(None,"Summary report saved as:\n\n%s\n\n"%self.reportFilename, "Summary Report Saved", \
            #style=wx.OK | wx.ICON_INFORMATION | wx.STAY_ON_TOP)
            #d.ShowModal()
            #d.Destroy()
        except Exception, err:
            self._writeToStatus("%r" % err)
            print "%r" % err
        
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
        self.enqueueViewerCommand(self.buttonUploadAndArchive.Enable, False)

    def _enableButtons(self):
        self.enqueueViewerCommand(self.buttonRunIPV.Enable, True)
        self.enqueueViewerCommand(self.buttonCreateDiagFile.Enable, True)
        self.enqueueViewerCommand(self.buttonUploadAndArchive.Enable, True)
        
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
            return polyfit(array(timeList), array(valList), 1)[0]
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
                    self._writeToStatus("%r" % err)
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
                testVal = mean(valList)
                if abs(testVal-setpoint) > tolerance:
                    result.append("Failed")
                else:
                    result.append("OK")
            elif method == "std":
                testVal =std(valList)
                if testVal > (tolerance + setpoint):
                    result.append("Failed")
                else:
                    result.append("OK")
            elif method == "variation":
                testVal = std(valList)/mean(valList)
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
        endTime = datetime.strftime(self.endDatetime, "%Y%m%d%H%M%S")
        self.h5Filename = "%s_%s_%s.h5" % (self.diagFilePrefix, self.instName, endTime)
        try:
            self.h5 = tables.openFile(self.h5Filename, mode="w", title="Picarro IPV File")
        except Exception, err:
            self._writeToStatus("%r" % err)
            print "%r" % err
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
    configFile, useViewer = HandleCommandSwitches()
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = IPV(configFile, useViewer, None, -1, "")
    frame.startIPVThread()
    app.SetTopWindow(frame)
    if useViewer:
        frame.Show()
    app.MainLoop()
