#!/usr/bin/python
#
"""
File Name: Controller.py
Purpose: Top level frame for the controller application

File History:
    07-Apr-2009  sze  Initial version.

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "Controller"

import wx
import sys
import traceback

from Host.Controller.ControllerFrameGui import ControllerFrameGui
from Host.Controller.ControllerModels import waveforms, parameterForms, panels, DriverProxy, RDFreqConvProxy, SpectrumCollectorProxy
from Host.Controller.ControllerModels import LogListener, SensorListener, RingdownListener, ControllerRpcHandler
from Host.autogen import interface
from Host.Common import SharedTypes
from Host.Common.ParameterDialog import ParameterDialog
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
EventManagerProxy_Init(APP_NAME)

# For convenience in calling driver and frequency converter functions
Driver = DriverProxy().rpc
RDFreqConv = RDFreqConvProxy().rpc
SpectrumCollector = SpectrumCollectorProxy().rpc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

if __debug__:
    print("Loading rpdb2")
    import rpdb2
    rpdb2.start_embedded_debugger("hostdbg",timeout=0)
    print("rpdb2 loaded")

class Controller(ControllerFrameGui):
    def __init__(self,*a,**k):
        try:
            self.versions = Driver.allVersions()
        except:
            wx.MessageDialog(None,"Driver not accessible, cannot continue.",
                "Controller Startup Error",wx.OK|wx.ICON_ERROR).ShowModal()
            sys.exit()
        ControllerFrameGui.__init__(self,*a,**k)
        self.updateTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.onUpdateTimer,self.updateTimer)
        self.updateTimer.Start(milliseconds=1000)
        self.openParamDialogs = {}
        self.setupParameterDialogs()
        self.setupWaveforms()
        self.logListener = LogListener()
        self.sensorListener = SensorListener()
        self.ringdownListener = RingdownListener()
        self.rpcHandler = ControllerRpcHandler()
        self.Bind(wx.EVT_IDLE, self.onIdle)
        panels["Laser1"]=self.laser1Panel
        self.laser1Panel.setLaserNum(1)
        panels["Laser2"]=self.laser2Panel
        self.laser2Panel.setLaserNum(2)
        panels["Laser3"]=self.laser3Panel
        self.laser3Panel.setLaserNum(3)
        panels["Laser4"]=self.laser4Panel
        self.laser4Panel.setLaserNum(4)
        panels["WarmBox"]=self.warmBoxPanel
        panels["HotBox"]=self.hotBoxPanel
        panels["Pressure"]=self.pressurePanel
        panels["Wlm"]=self.wlmPanel
        panels["Ringdown"]=self.ringdownPanel
        panels["ProcessedLoss"]=self.processedLossPanel
        panels["Stats"]=self.statsPanel
        self.controllerFrameGui_statusbar.SetStatusText('',0)
        # Starting from user mode
        self.fullInterface = False
        self.password = "picarro"
        self.updateInterface()

    def setupWaveforms(self):
        waveforms["Laser1"]=dict(
            temperature=self.laser1Panel.temperatureWfm,
            tec=self.laser1Panel.tecWfm,
            current=self.laser1Panel.currentWfm)
        waveforms["Laser2"]=dict(
            temperature=self.laser2Panel.temperatureWfm,
            tec=self.laser2Panel.tecWfm,
            current=self.laser2Panel.currentWfm)
        waveforms["Laser3"]=dict(
            temperature=self.laser3Panel.temperatureWfm,
            tec=self.laser3Panel.tecWfm,
            current=self.laser3Panel.currentWfm)
        waveforms["Laser4"]=dict(
            temperature=self.laser4Panel.temperatureWfm,
            tec=self.laser4Panel.tecWfm,
            current=self.laser4Panel.currentWfm)
        waveforms["WarmBox"]=dict(
            etalonTemperature=self.warmBoxPanel.etalonTemperatureWfm,
            warmBoxTemperature=self.warmBoxPanel.warmBoxTemperatureWfm,
            heatsinkTemperature=self.warmBoxPanel.heatsinkTemperatureWfm,
            tec=self.warmBoxPanel.tecWfm)
        waveforms["HotBox"]=dict(
            cavityTemperature=self.hotBoxPanel.cavityTemperatureWfm,
            heatsinkTemperature=self.hotBoxPanel.heatsinkTemperatureWfm,
            dasTemperature=self.hotBoxPanel.dasTemperatureWfm,
            tec=self.hotBoxPanel.tecWfm,
            heater=self.hotBoxPanel.heaterWfm)
        waveforms["Pressure"]=dict(
            ambientPressure=self.pressurePanel.ambientPressureWfm,
            cavityPressure=self.pressurePanel.cavityPressureWfm,
            flow1=self.pressurePanel.flow1Wfm,
            inletValve=self.pressurePanel.inletValveWfm,
            outletValve=self.pressurePanel.outletValveWfm)
        waveforms["Wlm"]=dict(
            etalon1=self.wlmPanel.etalon1Wfm,
            reference1=self.wlmPanel.reference1Wfm,
            etalon2=self.wlmPanel.etalon2Wfm,
            reference2=self.wlmPanel.reference2Wfm,
            ratio1=self.wlmPanel.ratio1Wfm,
            ratio2=self.wlmPanel.ratio2Wfm,
            )
        waveforms["ProcessedLoss"]=dict(
            processedLoss1=self.processedLossPanel.processedLossWfm[0],
            processedLoss2=self.processedLossPanel.processedLossWfm[1],
            processedLoss3=self.processedLossPanel.processedLossWfm[2],
            processedLoss4=self.processedLossPanel.processedLossWfm[3],
            )
        waveforms["Stats"]=dict(
            loss=self.statsPanel.lossStats,
            waveNumber=self.statsPanel.waveNumberStats,
            ratio1=self.statsPanel.ratio1Stats,
            ratio2=self.statsPanel.ratio2Stats,
            )
        waveforms["Ringdown"]=dict(
            corrected=self.ringdownPanel.ringdownWfms[0],
            uncorrected=self.ringdownPanel.ringdownWfms[1],
            ratio1=self.ringdownPanel.ringdownWfms[0],
            ratio2=self.ringdownPanel.ringdownWfms[1],
            tuner=self.ringdownPanel.ringdownWfms[0],
            pzt=self.ringdownPanel.ringdownWfms[0],
            wavenumber=self.ringdownPanel.ringdownWfms[0],
            fineCurrent=self.ringdownPanel.ringdownWfms[0])

    def setupParameterDialogs(self):
        idmin = None
        for f in Driver.getParameterForms():
            title, details = f
            id = wx.NewId()
            if idmin == None: idmin = id
            item = wx.MenuItem(self.parameters,id,title,"",wx.ITEM_NORMAL)
            self.parameters.AppendItem(item)
            parameterForms[id] = f
            idmax = id
        self.Bind(wx.EVT_MENU_RANGE, self.onParameterDialog,
                  id=idmin, id2=idmax)

    def onParameterDialog(self,e):
        """Either open a new parameter dialog form or shift focus
           to a pre-existing one"""
        #print "In onParameterDialog"
        id = e.GetId()
        if id in self.openParamDialogs:
            try:
                self.openParamDialogs[id].Show()
                self.openParamDialogs[id].SetFocus()
                return
            except Exception,e:
                #print "Cannot give focus to parameter dialog form: %s" % (e,)
                del self.openParamDialogs[id]
        title,details = parameterForms[id]
        pd = ParameterDialog(None, wx.ID_ANY, "")
        pd.initialize(title,details)
        pd.getRegisterValues = Driver.rdRegList
        pd.putRegisterValues = Driver.wrRegList
        self.openParamDialogs[id] = pd
        #print "About to call ReadFromDas"
        pd.readParams()
        #print "About to show dialog"
        pd.Show()

    def onAbout(self,evt):
        v = "(c) 2005-2011, Picarro Inc.\n\n"
        try:
            dV = Driver.allVersions()
            klist = dV.keys()
            klist.sort()
            v += "Version strings:\n"
            for k in klist:
                v += "%s : %s\n" % (k,dV[k])
        except:
            v += "Driver version information unavailable"
        d = wx.MessageDialog(None,v,"Picarro CRDS",wx.OK)
        d.ShowModal()
        d.Destroy()

    def onClose(self,evt):
        for id in self.openParamDialogs:
            try:
                self.openParamDialogs[id].Close()
            except:
                pass
        self.updateTimer.Stop()
        self.Close()

    def onFullInterface(self,evt):
        if self.fullInterface:
            return
        else:
            dlg = wx.TextEntryDialog(self, 'Password: ','Authorization required', '', wx.OK | wx.CANCEL | wx.TE_PASSWORD)
            self.fullInterface = (dlg.ShowModal() == wx.ID_OK) and (dlg.GetValue() == self.password)
            dlg.Destroy()
        if self.fullInterface:
            self.updateInterface()

    def onUserInterface(self,evt):
        if not self.fullInterface:
            return
        else:
            self.fullInterface = False
            self.updateInterface()

    def updateInterface(self):
        """ Update the Controller GUI based on self.fullInterface."""
        if not self.fullInterface:
            self.controllerFrameGui_menubar.EnableTop(pos=1,enable=False)
            self.controllerFrameGui_menubar.EnableTop(pos=2,enable=False)
            self.commandLogPanel.disableAll()
        else:
            self.controllerFrameGui_menubar.EnableTop(pos=1,enable=True)
            self.controllerFrameGui_menubar.EnableTop(pos=2,enable=True)
            self.commandLogPanel.enableAll()

    def onUpdateTimer(self,evt):
        pageNum = self.topNotebook.GetSelection()
        pageText = self.topNotebook.GetPageText(pageNum)
        if pageText == "Command/Log":
            self.commandLogPanel.updateLoopStatus()
            self.commandLogPanel.updateCalFileStatus()
        elif pageText == "Laser1":
            self.laser1Panel.update()
        elif pageText == "Laser2":
            self.laser2Panel.update()
        elif pageText == "Laser3":
            self.laser3Panel.update()
        elif pageText == "Laser4":
            self.laser4Panel.update()
        elif pageText == "WarmBox":
            self.warmBoxPanel.update()
        elif pageText == "HotBox":
            self.hotBoxPanel.update()
        elif pageText == "Pressure":
            self.pressurePanel.update()
        elif pageText == "WavelengthMonitor":
            self.wlmPanel.update()
        elif pageText == "Ringdowns":
            self.ringdownPanel.update()
        elif pageText == "ProcessedLoss":
            self.processedLossPanel.update()
        elif pageText == "Statistics":
            self.statsPanel.update()

    def onIdle(self,evt):
        # Deal with updating the command log panel
        self.commandLogPanel.setStreamFileState()
        acqState = self.commandLogPanel.updateAcquisitionState()
        self.controllerFrameGui_statusbar.SetStatusText(acqState,0)
        # Deal with event manager log messages
        while True:
            msg = self.logListener.getLogMessage()
            if msg:
                self.commandLogPanel.addMessage(msg)
            else:
                break

        # Deal with Controller RPC calls within GUI idle loop
        try:
            daemon = self.rpcHandler.server.daemon
            daemon.handleRequests(0.0)
        except:
            Log("Controller shut down in response to termination of RPC server.",
                Level=2)
            self.onClose(evt)

    def onLoadIni(self, event):
        Driver.loadIniFile()
        SpectrumCollector.reloadSequences()
        # Sequencer().getSequences(Driver.getConfigFile())

    def onWriteIni(self, event):
        Driver.writeIniFile()

# Report GUI exceptions in EventManager
def excepthook(type,value,trace):
    exc = traceback.format_exception(type,value,trace)
    Log("Unhandled Exception: %s: %s" % (str(type),str(value)),
            Verbose="".join(exc),Level=3)
    sys.__excepthook__(type,value,trace)

if __name__ == "__main__":
    # sys.excepthook = excepthook
    app = wx.App(False)
    #wx.InitAllImageHandlers() # this function is deprecated in wx 3.0
    controller = Controller(None, wx.ID_ANY, "")
    try:
        app.SetTopWindow(controller)
        controller.Show()
        Log("%s started." % APP_NAME, Level = 0)
        app.MainLoop()
        Log("Exiting program")
    finally:
        Driver.unregisterStreamStatusObserver(
            SharedTypes.RPC_PORT_CONTROLLER)