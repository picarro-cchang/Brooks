#!/usr/bin/python
#
# FILE:
#   ControllerFrame.py
#
# DESCRIPTION:
#   Top level frame for the controller application
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   07-Apr-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import wx
import sys
import traceback

from ControllerFrameGui import ControllerFrameGui
from ControllerModels import waveforms, parameterForms, panels, DriverProxy
from ControllerModels import LogListener, SensorListener, RingdownListener, ControllerRpcHandler
from Host.Common.ParameterDialog import ParameterDialog
from Host.autogen import interface
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common import SharedTypes
from configobj import ConfigObj

# For convenience in calling driver functions
Driver = DriverProxy().rpc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
EventManagerProxy_Init("Controller")

class ControllerFrame(ControllerFrameGui):
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
        self.updateTimer.Start(milliseconds=250)
        self.openParamDialogs = {}
        self.setupParameterDialogs()
        self.setupWaveforms()
        self.logListener = LogListener()
        self.sensorListener = SensorListener()
        self.ringdownListener = RingdownListener()
        self.rpcHandler = ControllerRpcHandler()
        self.Bind(wx.EVT_IDLE, self.onIdle)
        panels["Laser1"]=self.laser1Panel
        panels["Laser2"]=self.laser2Panel
        panels["Laser3"]=self.laser3Panel
        panels["Laser4"]=self.laser4Panel
        panels["WarmBox"]=self.warmBoxPanel
        panels["HotBox"]=self.hotBoxPanel
        panels["Pressure"]=self.pressurePanel
        panels["Wlm"]=self.wlmPanel
        panels["Ringdown"]=self.ringdownPanel
        panels["Stats"]=self.statsPanel

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
            tec=self.hotBoxPanel.tecWfm,
            heater=self.hotBoxPanel.heaterWfm)
        waveforms["Pressure"]=dict(
            ambientPressure=self.pressurePanel.ambientPressureWfm,
            cavityPressure=self.pressurePanel.cavityPressureWfm,
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
            ratio2=self.ringdownPanel.ringdownWfms[1])
        for vLaser in range(interface.NUM_VIRTUAL_LASERS):
            waveforms["Ringdown"]["tuner_%d" % (vLaser+1,)] = self.ringdownPanel.ringdownWfms[vLaser]
            waveforms["Ringdown"]["wavenumber_%d" % (vLaser+1,)] = self.ringdownPanel.ringdownWfms[vLaser]
            waveforms["Ringdown"]["fineCurrent_%d" % (vLaser+1,)] = self.ringdownPanel.ringdownWfms[vLaser]


    def setupParameterDialogs(self):
        idmin = None
        for f in interface.parameter_forms:
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

    def onClose(self,evt):
        for id in self.openParamDialogs:
            try:
                self.openParamDialogs[id].Close()
            except:
                pass
        self.updateTimer.Stop()
        self.Close()

    def onUpdateTimer(self,evt):
        pageNum = self.topNotebook.GetSelection()
        pageText = self.topNotebook.GetPageText(pageNum)
        if pageText == "Laser1":
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
        elif pageText == "Statistics":
            self.statsPanel.update()

    def onIdle(self,evt):
        # Deal with updating the command log panel
        self.commandLogPanel.setStreamFileState()
        self.commandLogPanel.updateLoopStatus()
        self.commandLogPanel.updateAcquisitionState()
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

    def onWriteIni(self, event):
        Driver.writeIniFile()


class Sequencer(object):
    "Supervises running of a sequence of schemes, using a block of four scheme table entries"
    IDLE = 0
    STARTUP = 1
    SEND_SCHEME = 2
    WAIT_UNTIL_ACTIVE = 3
    WAIT_FOR_SCHEME_DONE = 4
    def __init__(self,config):
        self.state = Sequencer.IDLE
        self.sequence = 1
        self.scheme = 1
        self.repeat = 1
        self.sequences = []
        self.getSequences(config)
        print self.sequences

    def getSequences(self,config):
        index = 1
        section = "SEQUENCE%02d" % (index,)
        try:
            while section in config:
                cs = config[section]
                nSchemes = int(cs["NSCHEMES"])
                schemes = []
                for i in range(nSchemes):
                    schemeFileName = cs["SCHEME%02d" % (i+1,)]
                    repetitions = int(cs["REPEAT%02d" % (i+1,)])
                    schemes.append((Scheme(schemeFileName),repetitions))
                self.sequences.append(schemes)
                index += 1
                section = "SEQUENCE%02d" % (index,)
            Log("Sequences read: %d" % len(self.sequences))
        except Exception,e:
            LogExc("Error in sequencer ini file")

# Report GUI exceptions in EventManager
def excepthook(type,value,trace):
    exc = traceback.format_exception(type,value,trace)
    Log("Unhandled Exception: %s: %s" % (str(type),str(value)),
            Verbose="".join(exc),Level=3)
    sys.__excepthook__(type,value,trace)

if __name__ == "__main__":
    # sys.excepthook = excepthook
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    controllerFrame = ControllerFrame(None, wx.ID_ANY, "")
    try:
        app.SetTopWindow(controllerFrame)
        controllerFrame.Show()
        app.MainLoop()
    finally:
        Driver.unregisterStreamStatusObserver(
            SharedTypes.RPC_PORT_CONTROLLER)
