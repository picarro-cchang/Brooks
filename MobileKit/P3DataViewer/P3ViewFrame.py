#!/usr/bin/python
"""
File Name: P3ViewFrame.py
Purpose: Allows graphical display of data from PCubed

File History:
    19-Dec-2013  sze   Initial Version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
import wx
from configobj import ConfigObj
import gettext
from optparse import OptionParser
from Queue import Queue, Empty
import os
import sys
import time
import traceback

from Host.Common.GraphPanel import GraphPanel
from DataModel import DataModel
from DisplayModel import DisplayModel
from Notifier import Notifier
from P3Access import P3Access
from P3ViewFrameGui import P3ViewFrameGui
from EmailSender import EmailSender
                        
class P3ViewFrame(P3ViewFrameGui):
    def __init__(self, *args, **kwargs):
        P3ViewFrameGui.__init__(self, *args, **kwargs)
        self.graphPanelXY.SetGraphProperties(xlabel='X',timeAxes=(False,False),ylabel='Y',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            logScale=(False,False))
        self.graphPanelXVar.SetGraphProperties(xlabel='Time',timeAxes=(True,False),ylabel='X',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            logScale=(False,False))
        self.graphPanelYVar.SetGraphProperties(xlabel='Time',timeAxes=(True,False),ylabel='Y',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            logScale=(False,False))
        self.listCtrlNotifications.InsertColumn(0,"Message",width=500)
        self.p3Access = None
        self.dataModel = None
        self.displayModel = None
        self.notifier = None
        self.notificationQueue = Queue(0)
        self.config = None
        self.allTimeLocked = False
        self.updateTimer = None
        self.monitorTextCntrls = {}
        self.emailSender = None
        self.emailSent = False
        
    def addNotificationMessage(self,msg):
        index = self.listCtrlNotifications.InsertStringItem(sys.maxint,msg)
        self.listCtrlNotifications.EnsureVisible(index)
        
    def startup(self, options, args):
        configPath = os.path.abspath(options.config)
        basePath = os.path.split(configPath)[0]
        self.config = ConfigObj(configPath)
        assert 'Authentication' in self.config, "Authentication section missing in %s" % options.config
        self.p3Access = P3Access(self.config['Authentication'])
        assert 'Scripts' in self.config, "Scripts section missing in %s" % options.config
        self.dataModel = DataModel(self.p3Access)
        self.displayModel = DisplayModel(self.dataModel)
        self.dataModel.addListener(self.dataListener)
        self.displayModel.addListener(self.displayListener)
        assert 'Email' in self.config, "Email section missing in %s" % options.config
        self.emailSender = EmailSender(self.config['Email'])
        
        # Make the notification panel by getting list of variables to monitor
        notificationPane = self.window_1_pane_1
        self.notifier = Notifier(self.dataModel, basePath, self.config['Scripts'], notificationPane, self.emailSender)
        self.monitorTextCntrls = self.notifier.makePanel()
        self.notifier.addListener(self.notificationListener)
        self.notifier.startMonitor()

        self.graphPanelXVar.AddSeriesAsLine(self.displayModel.xSeries, colour='blue', width=2)
        self.graphPanelYVar.AddSeriesAsLine(self.displayModel.ySeries, colour='blue', width=2)
        self.graphPanelXY.AddSeriesAsLine(self.displayModel.xySeries, colour='blue', width=2)
        self.graphPanelXY.AddSeriesAsPoints(self.displayModel.xySeries, colour='red', fillcolour='red', 
                                           marker='square', size=1,width=1)

        self.Bind(wx.EVT_TIMER, self.onTimer)
        self.updateTimer = wx.Timer(self)
        self.updateTimer.Start(milliseconds=500)
        
        self.dataModel.getAnalyzers()
        
    def handleLockedAxes(self):
        graphPanels = [self.graphPanelXVar, self.graphPanelYVar]
        axisChanged = False
        for idx in range(len(graphPanels)):
            refPanel = graphPanels[idx]
            assert isinstance(refPanel, GraphPanel)
            if refPanel.GetIsNewXAxis():
                axisChanged = True
                actIndices = range(len(graphPanels))
                actIndices.remove(idx)
                currXAxis = tuple(graphPanels[idx].GetLastDraw()[1])
                self.displayModel.setTimeRange(currXAxis)
                if not refPanel.GetUnzoomed():
                    #print "Graph %d zooming others in time-locked mode" % idx
                    for i in actIndices:
                        panel = graphPanels[i]
                        panel.SetUnzoomed(False)
                        panel.SetForcedXAxis(currXAxis)
                        panel.Update(forcedRedraw=True)
                        panel.ClearForcedXAxis()
                    self.allTimeLocked = True  
                    break
                elif self.allTimeLocked:
                    #print "Graph %d unzooming others in time-locked mode" % idx
                    # Unzoom other plots
                    for i in actIndices:
                        panel = graphPanels[i]
                        panel.SetUnzoomed(True)
                        panel.Update(forcedRedraw=True)
                    self.allTimeLocked = False
                    break
        return axisChanged
    
    def onTimer(self,evt):
        self.dataModel.outputQueueHandler()
        axisChanged = self.handleLockedAxes()
        self.graphPanelXVar.Update(delay=0, forcedRedraw=axisChanged)
        self.graphPanelYVar.Update(delay=0, forcedRedraw=axisChanged)
        self.graphPanelXY.Update(delay=0, forcedRedraw=axisChanged)
        self.notificationQueueHandler()
        if evt: evt.Skip()
        
    def notificationQueueHandler(self):
        while not self.notificationQueue.empty():
            try:
                changed, value = self.notificationQueue.get(block=False)
                if changed == "message":
                    for line in value.splitlines():
                        self.addNotificationMessage(line)
                elif changed == "variable":
                    name, text, status = value
                    control = self.monitorTextCntrls[name]
                    assert isinstance(control, wx.TextCtrl)
                    control.SetValue(text)
                    if status == "NORMAL":
                        fg, bg = "BLACK", "WHITE"
                    elif status == "WARNING":
                        fg, bg = "BLACK", "YELLOW"
                    elif status == "ERROR":
                        fg, bg = "BLACK", "RED"
                    control.SetBackgroundColour(bg)
                    control.SetForegroundColour(fg)
            except Empty:
                pass
            
    
    def dataListener(self, dataModel):
        changed = dataModel.changed
        if changed == "analyzers":
            self.cbAnalyzerName.SetItems(dataModel.analyzers)
            if 'Analyzer' in self.config['Settings']:
                analyzer = self.config['Settings']['Analyzer']
                assert analyzer in dataModel.analyzers, "Cannot find analyzer %s in environment" % analyzer
                self.cbAnalyzerName.SetStringSelection(analyzer)
            else:
                self.cbAnalyzerName.SetSelection(0)
            self.onSelectAnalyzer(None)
        elif changed == "analyzerLogs":
            if dataModel.analyzerLogs is None:
                self.cbLogName.Clear()
            else:
                logs = ["Live"] + dataModel.analyzerLogs
                self.cbLogName.SetItems(logs)
                if 'Log' in self.config['Settings']:
                    logName = self.config['Settings']['Log']
                    assert logName in logs, "Cannot find log %s for analyzer" % logName
                    self.cbLogName.SetStringSelection(logName)
                else:
                    self.cbLogName.SetSelection(0)
                self.onSelectLog(None)
        elif changed == "logVars":
            if dataModel.logVars is not None:
                self.selectDisplayVariables(dataModel)

    def selectDisplayVariables(self, dataModel):
        logVars = [var for var in dataModel.logVars if var not in ["ANALYZER"]]
        self.cbXVariable.SetItems(logVars)
        if self.displayModel.xvar in logVars:
            self.cbXVariable.SetStringSelection(self.displayModel.xvar)
        else:
            if 'X' in self.config['Settings']:
                xvar = self.config['Settings']['X']
                if xvar in logVars:
                    self.cbXVariable.SetStringSelection(xvar)
                else:
                    self.cbXVariable.SetSelection(0)
            else:
                self.cbXVariable.SetSelection(0)
                
        self.cbYVariable.SetItems(logVars)
        if self.displayModel.yvar in logVars:
            self.cbYVariable.SetStringSelection(self.displayModel.yvar)
        else:
            if 'Y' in self.config['Settings']:
                yvar = self.config['Settings']['Y']
                if yvar in logVars:
                    self.cbYVariable.SetStringSelection(yvar)
                else:
                    self.cbYVariable.SetSelection(0)
            else:
                self.cbYVariable.SetSelection(0)
        self.onSelectVariables()
        
    def displayListener(self, displayModel):
        self.graphPanelXVar.ylabel = displayModel.xvar
        self.graphPanelYVar.ylabel = displayModel.yvar
        self.graphPanelXY.xlabel = displayModel.xvar
        self.graphPanelXY.ylabel = displayModel.yvar
        
    def notificationListener(self, notificationModel):
        changed = notificationModel.changed
        self.notificationQueue.put((changed, getattr(notificationModel, changed)))
            
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

    # Handle exceptions by showing a modal dialog
    def excepthook(self, etype, value, tb):
        msg = "%s: %s\nTraceback:\n%s" % ( etype, value, '\n'.join(traceback.format_tb(tb)))
        if not self.emailSent:
            self.emailSender.sendMessage("Error from P3Viewer", msg)
            self.emailSent = True
        dlg = wx.MessageDialog(None, msg, 'Unhandled Exception', wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        
class MyApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config", help="Configuration file", default="P3Monitor.ini")
        options, args = parser.parse_args()
        frame_1 = P3ViewFrame(None, wx.ID_ANY, "")
        sys.excepthook = frame_1.excepthook
        frame_1.startup(options, args)
        self.SetTopWindow(frame_1)
        frame_1.Show()
        return 1

if __name__ == "__main__":
    gettext.install("P3Viewer")
    app = MyApp(0)
    app.MainLoop()
    