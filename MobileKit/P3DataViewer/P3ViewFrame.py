#!/usr/bin/python
"""
File Name: P3ViewFrame.py
Purpose: Allows graphical display of data from PCubed

File History:
    19-Dec-2013  sze   Initial Version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
import wx
import gettext
from math import isnan
import numpy as np
from Queue import Queue, Empty
import sys
import time
import threading
import traceback

from Host.Common.GraphPanel import Series

from P3RestApi import P3RestApi
from P3ViewFrameGui import P3ViewFrameGui

SERIES_POINTS = 10000

class P3Access(object):
    def __init__(self):
        restP = {}
        restP['host'] = "p3.picarro.com"
        restP['port'] = 443
        restP['site'] = 'stage'
        restP['identity'] = 'zYa8P106vCc8IfpYGv4qcy2z8YNeVjHJw1zaBDth'
        restP['psys'] = 'stage'
        restP['svc'] = 'gdu'
        restP['debug'] = False
        restP['version'] = '1.0'
        restP['resource'] = 'AnzMeta'
        restP['rprocs'] = ["AnzMeta:byAnz"]
        self.anzMeta = P3RestApi(**restP)
        
        restP['resource'] = 'AnzLogMeta'
        restP['rprocs'] = ["AnzLogMeta:byEpoch"]
        self.anzLogMeta = P3RestApi(**restP)
        
        restP['resource'] = 'AnzLog'
        restP['rprocs'] = ["AnzLog:byEpoch", "AnzLog:byPos"]
        self.anzLog = P3RestApi(**restP)
        
        restP['resource'] = 'GduService'
        restP['rprocs'] = ["GduService:runProcess", "GduService:getProcessStatus"]
        self.gduService = P3RestApi(**restP)
        
        self.inputQueue = Queue(0)
        self.outputQueue = Queue(0)
        self.workerThread = threading.Thread(target=self.worker)
        self.workerThread.setDaemon(True)
        self.workerThread.start()
        
    def worker(self):
        """Performs unit of work from input queue by calling a method and enqueuing result.

        The entries on the input queue are tuples with following elements:
            func: Method to call
            args: Positional arguments for method
            kwargs: Keyword arguments for method
            ident: Identification that is passed through to output
            onSuccess: Callback function for success, called with result and ident
            onFail: Callback function for failure, called with exception and ident
        """
        assert isinstance(self.inputQueue, Queue)
        while True:
            print "Worker looping"
            func, args, kwargs, ident, onSuccess, onFail = self.inputQueue.get()
            try:
                result = func(*args, **kwargs)
                self.outputQueue.put((onSuccess, result, ident))
            except Exception, exc:
                self.outputQueue.put((onFail, exc, ident))
        
    def getAnalyzerList(self):
        res = self.anzMeta.get({'existing_tkt':True, 'qryobj':{'qry':'byAnz', 'doclist':True}})
        return res[1]['result']['ANALYZER']
    
    def getLogFiles(self, analyzer, limit=10):
        res = self.anzLogMeta.get({'existing_tkt':True, 
                                   'qryobj':{'qry':'byEpoch', 'doclist':True, 'anz':analyzer,
                                             'startEtm':0, 'endEtm':2000000000, 'logtype':'dat', 
                                             'limit':limit, 'reverse':True }})
        if res[1]['result']:
            return analyzer, res[1]['result']['name']
        else:
            return analyzer, []
        
    def getLogMetadata(self, alog):
        res = self.anzLogMeta.get({'existing_tkt':True, 
                                   'qryobj':{'qry':'byEpoch', 'alog':alog, 'startEtm':0,
                                             'logtype':'dat', 'limit':1, 'doclist':True}})
        result = res[1]['result']
        return alog, result
    
    def getLogByPos(self, alog, startPos, limit=500):
        res = self.anzLog.get({'existing_tkt':True, 
                          'qryobj':{'alog':alog, 
                                    'qry':'byPos', 'doclist':True, 'logtype':'dat', 
                                    'startPos':startPos, 'limit':limit}})        
        result = res[1]['result']
        return alog, result
    
    
class Subject(object):
    """Something to which listeners can subscribe for updates.
    """
    def __init__(self, *a, **kwds):
        if "name" in kwds:
            self.name = kwds["name"]
        else:
            self.name = "unknown"

        self.listeners = {}
        self.nextListenerIndex = 0
        self.changed = ""

    def addListener(self, listenerFunc):
        """Adds a function to the list of listeners for subject.
        
        Args: 
            listenerFunc: A function to be called when the subject is updated. It is called passing
               the subject as the only parameter.
        
        Returns:
            An integer index which is useful for removing the listener.
        """
        self.listeners[self.nextListenerIndex] = listenerFunc
        retVal = self.nextListenerIndex

        self.nextListenerIndex += 1
        return retVal

    def removeListener(self, listenerIndex):
        """Removes a listener from the list.
        
        Args:
            listenerIndex: The index that was returned when the listener was added
        """
        del self.listeners[listenerIndex]

    def update(self):
        """Calls all the active listeners.
        """
        for l in self.listeners:
            self.listeners[l](self)
            
    def set(self, var, value, force=False):
        """Set a variable and call listeners.
        
        Args:
            var: Name of variable, which must be an attribute of the model
            value: Value to set the varible to
            force: Call update whether or not variable has changed
        """
        oldValue = getattr(self, var)
        if force or (oldValue != value):
            setattr(self, var, value)
            self.changed = var
            self.update()
    
class DataModel(Subject):
    """Model for analyzer log data fetched from PCubed.

    Args:
        p3Access: P3Access object for communicating with PCubed.
    """
    parameterSetIndex = 0

    def __init__(self, p3Access):
        assert isinstance(p3Access, P3Access)
        Subject.__init__(self)
        self.analyzers = None
        self.analyzer = None
        self.logName = None
        self.logFileId = None
        self.analyzerLogs = None
        self.logMetaData = None
        self.logVars = None
        self.logData = None
        self.lastException = None
        self.changed = ""
        self.p3Access = p3Access

        self.startPos = None
        self.batchSize = None
        
    def newParameterSetIndex(self):
        """Gets next parameter set index.

        A new parameterSetIndex is generated whenever any of the parameters which affect
        getting of data logs change. By checking the value, it is possible to  
        """
        DataModel.parameterSetIndex += 1
        return DataModel.parameterSetIndex

    def outputQueueHandler(self):
        while not self.p3Access.outputQueue.empty():
            func, result, ident = self.p3Access.outputQueue.get()
            func(result, ident)

    def failed(self, exc, index):
        """Callback when an exception is raised.

        Args:
            exc: Exception object returned from P3Access method call
        """
        self.set("lastException", exc)
        
    def getAnalyzers(self):
        """Gets analyzers available in the environment.
        """
        self.p3Access.inputQueue.put((self.p3Access.getAnalyzerList,(),{},
                                      self.newParameterSetIndex(),
                                      self.getAnalyzerListSuccess, 
                                      self.failed))
        
    def getAnalyzerListSuccess(self, analyzerList, index):
        """Success callback when fetching list of analyzers.

        Args:
            analyzerList: List of analyzers in the environment
        """
        self.set("analyzers", analyzerList)
    
    def getAnalyzerLogs(self, analyzer, limit=10):
        """Set the analyzer and get its logs.

        The most recent logs are fetched in reverse time order.

        Args:
            analyzer: Name of analyzer
            limit: Maximum number of logs to fetch
        """
        parameterSetIndex = self.newParameterSetIndex()
        assert analyzer in self.analyzers
        self.set("analyzer", analyzer)
        self.set("logName", None)
        self.set("logFileId", None)
        self.set("analyzerLogs", None)
        self.set("logMetaData", None)
        self.set("logVars", None)
        self.set("logData", None)
        self.p3Access.inputQueue.put((self.p3Access.getLogFiles, (),
                                      dict(analyzer=analyzer, limit=limit),
                                      parameterSetIndex,
                                      self.getAnalyzerLogsSuccess,
                                      self.failed))

    def getAnalyzerLogsSuccess(self, result, index):
        """Success callback when fetching list of analyzer logs.

        Args:
            result: tuple consisting of (analyzer, analyzerLogs)
        """
        analyzer, analyzerLogs = result
        self.set("analyzerLogs", analyzerLogs)
        
    def getAnalyzerLog(self, logName, startPos=0, batchSize=500):
        """Set the logName, fetch associated metadata and data.

        This gets the metadata and asynchronously calls getAnalyzerMetadataSuccess
            if it completes successfully.

        Args:
            logName: Name of analyzer log to fetch or @@Live:<analyzer>
            startPos: Row at which to start fetching log
            batchSize: Maximum number of rows to fetch on each PCubed query
        """
        parameterSetIndex = self.newParameterSetIndex()
        assert logName.startswith("@@Live:") or logName in self.analyzerLogs
        self.startPos = startPos
        self.batchSize = batchSize
        self.set("logName", logName)
        self.set("logMetaData", None)
        self.set("logVars", None)
        self.set("logData", None)
        self.p3Access.inputQueue.put((self.p3Access.getLogMetadata, (),
                                      dict(alog=logName),
                                      parameterSetIndex,
                                      self.getAnalyzerMetadataSuccess,
                                      self.failed))
        
    def getAnalyzerMetadataSuccess(self, result, index):
        """Success callback when fetching metadata for a log.

        Sets the logMetaData and logVars model variables, then calls P3Access
            getLogByPos method to fetch first set of rows of log data.

        Args:
            result: tuple consisting of (logName, metadata)
        """
        if self.parameterSetIndex != index: 
            return
        alog, metadata = result
        docmap = metadata['docmap'][0]
        logFileId = metadata["FILENAME_nint"][0]
        self.set("logMetaData", metadata)
        self.set("logFileId", logFileId)        
        self.set("logVars", sorted(docmap.keys()))
        self.p3Access.inputQueue.put((self.p3Access.getLogByPos,(),
                                      dict(alog=alog, startPos=self.startPos, limit=self.batchSize),
                                      index,
                                      self.getLogByPosSuccess, 
                                      self.failed))

    def getLogMore(self, alog, index):
        """Called to get more rows from the log file when there was no data on the last call
        """
        if self.parameterSetIndex != index: 
            return
        if alog.startswith("@@Live:"):
            # Make metadata call to see if we have a new log
            self.p3Access.inputQueue.put((self.p3Access.getLogMetadata, (),
                                          dict(alog=alog),
                                          index,
                                          self.checkNewLogfileSuccess,
                                          self.failed))
        else:
            # Try getting more data
            self.p3Access.inputQueue.put((self.p3Access.getLogByPos,(),
                                          dict(alog=alog, startPos=self.startPos, limit=self.batchSize),
                                          index,
                                          self.getLogByPosSuccess, 
                                          self.failed))

    def checkNewLogfileSuccess(self, result, index):
        if self.parameterSetIndex != index: 
            return
        alog, metadata = result
        logFileId = metadata["FILENAME_nint"][0]
        print self.logFileId, logFileId
        if self.logFileId != logFileId:
            print "Log restart detected during slow poll"            
            # This is a new log file
            docmap = metadata['docmap'][0]
            self.set("logMetaData", metadata)
            self.set("logVars", sorted(docmap.keys()))
            self.set("logFileId", logFileId)
            self.set("logData", None)
            self.startPos = 0
        # Get the next chunk of data
        self.p3Access.inputQueue.put((self.p3Access.getLogByPos,(),
                                      dict(alog=alog, startPos=self.startPos, limit=self.batchSize),
                                      index,
                                      self.getLogByPosSuccess, 
                                      self.failed))
        
    def getLogByPosSuccess(self, result, index):
        """Success callback when fetching rows from a data log.

        Extends the logData model variable, then tries to get more data.
            If the most recent fetch returned no rows, the subsequent fetch
            is delayed by 5s. If the log name has changed since the request
            was enqueued, discard the data received.

        TODO: What happens when user restarts the data log and we have selected "live"?

        Args:
            result: tuple consisting of (logName, metadata)
        """
        if self.parameterSetIndex != index: 
            return
        if self.logData is None:
            self.logData = {}
        alog, logData = result

        if "FILENAME_nint" in logData:
            logFileId = set(logData["FILENAME_nint"])
            assert len(logFileId) == 1, "Did not expect file ids %s in log data" % logFileId
            if self.logFileId != logFileId.pop():
                print "Log restart detected by changing logFileId"
                # Make metadata call to get information about the new log
                self.p3Access.inputQueue.put((self.p3Access.getLogMetadata, (),
                                              dict(alog=alog),
                                              index,
                                              self.checkNewLogfileSuccess,
                                              self.failed))
        for var in logData:
            if var not in self.logData:
                self.logData[var] = []
            self.logData[var].extend(logData[var])
        newStartPos = self.logData["row"][-1] + 1
        print self.startPos
        if self.startPos == newStartPos:
            print "Waiting awhile before getting more data"
            wx.FutureCall(5000, self.getLogMore, alog=alog, index=index)
        else:
            self.set("logData", self.logData, force=True)
            self.startPos = newStartPos
            self.p3Access.inputQueue.put((self.p3Access.getLogByPos,(),
                                          dict(alog=alog, startPos=self.startPos, limit=self.batchSize),
                                          index,
                                          self.getLogByPosSuccess, 
                                          self.failed))
        
class DisplayModel(Subject):
    def __init__(self, dataModel):
        Subject.__init__(self)
        self.dataModel = dataModel
        self.xvar = ''
        self.yvar = ''
        self.xSeries = Series(SERIES_POINTS)
        self.ySeries = Series(SERIES_POINTS)
        self.xySeries = Series(SERIES_POINTS)
        self.nextPlotPoint = 0
        self.dataModel.addListener(self.dataListener)
        self.addListener(self.displayListener)
        
    def setVariables(self, xvar, yvar):
        self.set('xvar', xvar)
        self.set('yvar', yvar)

    def fillSeries(self):
        if self.dataModel.logData is not None and self.xvar and self.yvar:
            rows = self.dataModel.logData['row']
            xValues = self.dataModel.logData[self.xvar]
            yValues = self.dataModel.logData[self.yvar]
            while self.nextPlotPoint < len(xValues):
                row = rows[self.nextPlotPoint]
                xValue = xValues[self.nextPlotPoint]
                yValue = yValues[self.nextPlotPoint]
                rowGood = (row is not None) and row > 0
                xGood = (xValue is not None) and np.isfinite(xValue)
                yGood = (yValue is not None) and np.isfinite(yValue)
                
                if rowGood and xGood:
                    self.xSeries.Add(row, xValue)
                else:    
                    self.xSeries.Add(row, np.NaN)
                if rowGood and yGood:
                    self.ySeries.Add(row, yValue)
                else:    
                    self.xSeries.Add(row, np.NaN)
                if rowGood and xGood and yGood:
                    self.xySeries.Add(xValue, yValue)
                else:    
                    self.xySeries.Add(np.NaN, np.NaN)
                self.nextPlotPoint += 1
            pass
        
    def displayListener(self, displayModel):
        changed = self.changed
        if changed in ['xvar', 'yvar']:
            self.xSeries.Clear()
            self.ySeries.Clear()
            self.xySeries.Clear()
            self.nextPlotPoint = 0
            self.fillSeries()
        
    def dataListener(self, dataModel):
        changed = dataModel.changed
        if changed in ["logFileId"]:
            self.xSeries.Clear()
            self.ySeries.Clear()
            self.xySeries.Clear()
            self.nextPlotPoint = 0
        elif changed in ["logData"]:
            self.fillSeries()
        
                        
class P3ViewFrame(P3ViewFrameGui):
    def __init__(self, *args, **kwargs):
        P3ViewFrameGui.__init__(self, *args, **kwargs)
        self.graphPanelXY.SetGraphProperties(xlabel='X',timeAxes=(False,False),ylabel='Y',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            logScale=(False,False))
        self.graphPanelXVar.SetGraphProperties(xlabel='row',timeAxes=(False,False),ylabel='X',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            logScale=(False,False))
        self.graphPanelYVar.SetGraphProperties(xlabel='row',timeAxes=(False,False),ylabel='Y',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            logScale=(False,False))

        self.p3Access = P3Access()
        self.dataModel = DataModel(self.p3Access)
        self.displayModel = DisplayModel(self.dataModel)

        self.graphPanelXVar.AddSeriesAsLine(self.displayModel.xSeries, colour='blue', width=2)
        self.graphPanelYVar.AddSeriesAsLine(self.displayModel.ySeries, colour='blue', width=2)

        self.graphPanelXY.AddSeriesAsLine(self.displayModel.xySeries, colour='blue', width=2)
        self.graphPanelXY.AddSeriesAsPoints(self.displayModel.xySeries, colour='red', fillcolour='red', 
                                           marker='square', size=1,width=1)
        self.dataModel.addListener(self.viewListener)
        
        self.Bind(wx.EVT_TIMER, self.onTimer)
        self.updateTimer = wx.Timer(self)
        self.updateTimer.Start(milliseconds=500)
        
    def onTimer(self,evt):
        self.dataModel.outputQueueHandler()
        self.graphPanelXVar.Update(delay=0)
        self.graphPanelYVar.Update(delay=0)
        self.graphPanelXY.Update(delay=0)
        if evt: evt.Skip()
        
    def startup(self):
        self.dataModel.getAnalyzers()
    
    def viewListener(self, model):
        changed = model.changed
        print model.changed
        if changed == "analyzers":
            self.cbAnalyzerName.SetItems(model.analyzers)
            self.cbAnalyzerName.SetSelection(0)
            self.onSelectAnalyzer(None)
        elif changed == "analyzerLogs":
            if model.analyzerLogs is None:
                self.cbLogName.Clear()
            else:
                logs = ["Live"] + model.analyzerLogs
                self.cbLogName.SetItems(logs)
                self.cbLogName.SetSelection(0)
                self.onSelectLog(None)
        elif changed == "logVars":
            if model.logVars is None:
                pass
            else:
                logVars = [var for var in model.logVars if var not in ["ANALYZER"]]
                self.cbXVariable.SetItems(logVars)
                if self.displayModel.xvar not in logVars:
                    self.cbXVariable.SetSelection(0)
                else:
                    self.cbXVariable.SetStringSelection(self.displayModel.xvar)
                self.cbYVariable.SetItems(logVars)
                if self.displayModel.yvar not in logVars:
                    self.cbYVariable.SetSelection(0)
                else:
                    self.cbYVariable.SetStringSelection(self.displayModel.yvar)
                self.onSelectVariables()
        elif changed == "logData":
            self.updateDashboard(model.logData)
        elif changed == "logFileId":
            self.clearDashboard()
            
    def clearDashboard(self):
        self.textCtrlLastPointTime.SetValue("")
        self.textCtrlInterval.SetValue("")
        self.textCtrlSystemStatus.SetValue("")
        self.textCtrlInstrumentStatus.SetValue("")
        self.textCtrlCarSpeed.SetValue("")
        self.textCtrlWindSpeed.SetValue("")

    def updateDashboard(self, data):
        SPEED_CONV = 3600.0/1609.344 # m/s to mph
        if data:
            if "EPOCH_TIME" in data:
                epochTime = data["EPOCH_TIME"]
                self.textCtrlLastPointTime.SetValue(time.ctime(epochTime[-1]))
                lastPoints = epochTime[-10:]
                if len(lastPoints) > 2:
                    interval = (lastPoints[-1] - lastPoints[0])/(len(lastPoints)-1)
                    self.textCtrlInterval.SetValue("%.2f s" % interval)
            else:
                self.textCtrlLastPointTime.SetValue("UNAVAILABLE")
                
            if "CAR_SPEED" in data:
                carSpeed = data["CAR_SPEED"][-1]
                if carSpeed is not None:
                    self.textCtrlCarSpeed.SetValue("%.1f m/s (%.1f mph)" % (carSpeed, carSpeed*SPEED_CONV))
                else:
                    self.textCtrlCarSpeed.SetValue("INVALID")
            else:
                self.textCtrlCarSpeed.SetValue("UNAVAILABLE")
                    
            if "WIND_N" in data and "WIND_E" in data:
                windN = data["WIND_N"][-1]
                windE = data["WIND_E"][-1]
                if windN is not None and windE is not None:
                    windSpeed = abs(windN + 1j*windE)
                    self.textCtrlWindSpeed.SetValue("%.1f m/s (%.1f mph)" % (windSpeed, windSpeed*SPEED_CONV))
                else:
                    self.textCtrlWindSpeed.SetValue("INVALID")
            else:
                self.textCtrlWindSpeed.SetValue("UNAVAILABLE")
                
            if "INST_STATUS" in data:
                instStatus = data["INST_STATUS"][-1]
                if instStatus is not None:
                    self.textCtrlInstrumentStatus.SetValue("%08x" % instStatus)
                else:
                    self.textCtrlInstrumentStatus.SetValue("INVALID")
            else:
                self.textCtrlInstrumentStatus.SetValue("UNAVAILABLE")
                
            if "SYSTEM_STATUS" in data:
                systemStatus = data["SYSTEM_STATUS"][-1]
                if systemStatus is not None:
                    self.textCtrlSystemStatus.SetValue("%08X" % systemStatus)
                else:
                    self.textCtrlSystemStatus.SetValue("INVALID")
            else:
                self.textCtrlSystemStatus.SetValue("UNAVAILABLE")
                    
        
    def onSelectAnalyzer(self, event):
        analyzer = self.cbAnalyzerName.GetStringSelection()
        self.dataModel.getAnalyzerLogs(analyzer)
        
    def onSelectLog(self, event):
        logName = self.cbLogName.GetStringSelection()
        if logName == "Live":
            logName = "@@Live:" + self.dataModel.analyzer
        self.dataModel.getAnalyzerLog(logName)
        
    def onSelectXVariable(self, event):
        self.onSelectVariables()
        
    def onSelectYVariable(self, event):
        self.onSelectVariables()
    
    def onSelectVariables(self):
        xvar = self.cbXVariable.GetStringSelection()
        yvar = self.cbYVariable.GetStringSelection()
        self.displayModel.setVariables(xvar, yvar)
        
class MyApp(wx.App):
    def OnInit(self):
        # Handle exceptions by showing a modal dialog
        def _excepthook(etype, value, tb):
            dlg = wx.MessageDialog(None,
                                   "%s\nTraceback:\n%s" % (
                                       value, '\n'.join(traceback.format_tb(tb))),
                                   'Unhandled Exception', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        # sys.excepthook = _excepthook
        wx.InitAllImageHandlers()
        frame_1 = P3ViewFrame(None, wx.ID_ANY, "")
        frame_1.startup()
        self.SetTopWindow(frame_1)
        frame_1.Show()
        return 1

if __name__ == "__main__":
    gettext.install("P3Viewer")
    app = MyApp(0)
    app.MainLoop()
    