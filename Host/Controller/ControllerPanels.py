import wx
import sys

from ControllerModels import DriverProxy, ControllerRpcHandler, waveforms
from ControllerPanelsGui import CommandLogPanelGui, LaserPanelGui
from ControllerPanelsGui import HotBoxPanelGui, RingdownPanelGui
from Host.autogen import interface
from Host.Common.GraphPanel import Series
from Host.Common import CmdFIFO, SharedTypes, timestamp
import threading

wfmPoints = interface.CONTROLLER_WAVEFORM_POINTS
ringdownPoints = interface.CONTROLLER_RINGDOWN_POINTS

class RingdownPanel(RingdownPanelGui):
    def __init__(self,*a,**k):
        RingdownPanelGui.__init__(self,*a,**k)
        self.ringdownGraph.SetGraphProperties(xlabel='Wavenumber - 6000 (1/cm)',
            timeAxes=(False,False),ylabel='Loss (ppm/cm)',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.ringdownWfms = [Series(ringdownPoints) for i in range(2)]
        wx.CallAfter(self.onSelectGraphType,None)
    def  update(self):
        self.ringdownGraph.Update(delay=0)
    def  onClear(self,evt):
        for s,sel,stats,attr in self.ringdownGraph._pointSeries:
            s.Clear()
    def  onSelectGraphType(self,evt):
        def  printData(data):
            print data.timestamp, data.uncorrectedAbsorbance
        choice = self.graphTypeRadioBox.GetSelection()
        y = ""
        self.appendData = printData
        if choice == 0:
            self.ringdownGraph.SetGraphProperties(xlabel='Wavenumber - 6000 (1/cm)',
            timeAxes=(False,False),ylabel='Loss (ppm/cm)',grid=True,
            ylabel='Loss (ppm/cm)',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Loss"
        elif choice == 1:
            def  lossVsTime(data):
                utime = timestamp.unixTime(data.timestamp)
                loss_u = data.uncorrectedAbsorbance
                loss_c = data.correctedAbsorbance
                waveforms["Ringdown"]["uncorrected"].Add(utime, loss_u)
                waveforms["Ringdown"]["corrected"].Add(utime, loss_c)
            self.ringdownGraph.SetGraphProperties(xlabel='',
            timeAxes=(True,False),ylabel='Loss (ppm/cm)',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Loss"
            self.appendData = lossVsTime

        self.ringdownGraph.RemoveAllSeries()

        if y == "Loss":
            if self.uncorrectedCheckBox.IsChecked():
                self.ringdownGraph.AddSeriesAsPoints(
                    waveforms["Ringdown"]["uncorrected"],
                    colour='black',fillcolour='red',marker='square',
                    size=1,width=1)
            if self.correctedCheckBox.IsChecked():
                self.ringdownGraph.AddSeriesAsPoints(
                    waveforms["Ringdown"]["corrected"],
                    colour='black',fillcolour='green',marker='square',
                    size=1,width=1)
        for w in self.ringdownWfms:
            w.Clear()
    def  onSelectLossType(self,evt):
        choice = self.graphTypeRadioBox.GetSelection()
        if choice in [0,1,2,3]:
            self.ringdownGraph.RemoveAllSeries()
            if self.uncorrectedCheckBox.IsChecked():
                self.ringdownGraph.AddSeriesAsPoints(
                    waveforms["Ringdown"]["uncorrected"],
                    colour='black',fillcolour='red',marker='square',
                    size=1,width=1)
            if self.correctedCheckBox.IsChecked():
                self.ringdownGraph.AddSeriesAsPoints(
                    waveforms["Ringdown"]["corrected"],
                    colour='black',fillcolour='green',marker='square',
                    size=1,width=1)

class LaserPanel(LaserPanelGui):
    def __init__(self,*a,**k):
        LaserPanelGui.__init__(self,*a,**k)
        self.temperatureGraph.SetGraphProperties(
            ylabel='Temperature (degC)',
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            grid=True,backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.tecGraph.SetGraphProperties(
            ylabel='TEC Current',grid=True,
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.currentGraph.SetGraphProperties(
            ylabel='Laser Current',grid=True,
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.temperatureWfm = Series(wfmPoints)
        self.temperatureGraph.AddSeriesAsLine(self.temperatureWfm,
            colour='red',width=1)
        self.tecWfm = Series(wfmPoints)
        self.tecGraph.AddSeriesAsLine(self.tecWfm,
            colour='red',width=1)
        self.currentWfm = Series(wfmPoints)
        self.currentGraph.AddSeriesAsLine(self.currentWfm,
            colour='red',width=1)

    def update(self):
        self.temperatureGraph.Update(delay=0)
        self.tecGraph.Update(delay=0)
        self.currentGraph.Update(delay=0)

    def onClear(self,evt):
        for s,sel,stats,attr in self.temperatureGraph._lineSeries:
            s.Clear()
        for s,sel,stats,attr in self.tecGraph._lineSeries:
            s.Clear()
        for s,sel,stats,attr in self.currentGraph._lineSeries:
            s.Clear()

class HotBoxPanel(HotBoxPanelGui):
    def __init__(self,*a,**k):
        HotBoxPanelGui.__init__(self,*a,**k)
        self.temperatureGraph.SetGraphProperties(
            ylabel='Temperature (degC)',
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            grid=True,backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.tecGraph.SetGraphProperties(
            ylabel='TEC Current',grid=True,
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.heaterGraph.SetGraphProperties(
            ylabel='Heater Current',grid=True,
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.cavityTemperatureWfm = Series(wfmPoints)
        self.temperatureGraph.AddSeriesAsLine(self.cavityTemperatureWfm,
            colour='red',width=1)
        self.heatsinkTemperatureWfm = Series(wfmPoints)
        self.temperatureGraph.AddSeriesAsLine(self.heatsinkTemperatureWfm,
            colour='blue',width=1)
        self.tecWfm = Series(wfmPoints)
        self.tecGraph.AddSeriesAsLine(self.tecWfm,
            colour='red',width=1)
        self.heaterWfm = Series(wfmPoints)
        self.heaterGraph.AddSeriesAsLine(self.heaterWfm,
            colour='red',width=1)

    def update(self):
        self.temperatureGraph.Update(delay=0)
        self.tecGraph.Update(delay=0)
        self.heaterGraph.Update(delay=0)

    def onClear(self,evt):
        for s,sel,stats,attr in self.temperatureGraph._lineSeries:
            s.Clear()
        for s,sel,stats,attr in self.tecGraph._lineSeries:
            s.Clear()
        for s,sel,stats,attr in self.heaterGraph._lineSeries:
            s.Clear()

    def onWaveformSelectChanged(self, event):
        self.temperatureGraph.RemoveAllSeries()
        if self.cavityTemperatureCheckbox.IsChecked():
            self.temperatureGraph.AddSeriesAsLine(self.cavityTemperatureWfm,
                colour='red',width=1)
        if self.heatsinkTemperatureCheckbox.IsChecked():
            self.temperatureGraph.AddSeriesAsLine(self.heatsinkTemperatureWfm,
                colour='blue',width=1)

class CommandLogPanel(CommandLogPanelGui):
    def __init__(self,*a,**k):
        CommandLogPanelGui.__init__(self,*a,**k)
        self.logListCtrl.InsertColumn(0,"Seq",width=70)
        self.logListCtrl.InsertColumn(1,"Date/Time",width=140)
        self.logListCtrl.InsertColumn(2,"Source",width=100)
        self.logListCtrl.InsertColumn(3,"Level",width=50)
        self.logListCtrl.InsertColumn(4,"Code",width=50)
        self.logListCtrl.InsertColumn(5,"Message",width=500)
        self.updateStreamFileState = threading.Semaphore(1)
        # Register a function which when called, indicates that
        #  the stream file state widgets on the panel should be
        #  updated
        token = ControllerRpcHandler()._registerNotification(
            self.updateStreamFileState.release)
        self.driverRpc = DriverProxy().rpc
        self.driverRpc.registerStreamStatusObserver(
            SharedTypes.RPC_PORT_CONTROLLER,token)

    def onSteamFileCheck(self, event):
        """Start or stop collecting sensor stream to an hdf5 file"""
        cb = event.GetEventObject()
        # N.B. The openStreamFile and closeStreamFile functions MUST be
        #  called in VerifyOnly mode, since they perform a "notify" during
        #  execution, which attempts to enqueue another request on the
        #  CmdFIFO before this function is finished.
        if cb.IsChecked():
            self.driverRpc.openStreamFile()
        else:
            self.driverRpc.closeStreamFile()

    def setStreamFileState(self):
        """Call this within idle task to update stream file state widgets"""
        if self.updateStreamFileState.acquire(False):
            response = DriverProxy().rpc.getStreamFileStatus()
            self.streamFileCheckbox.SetValue(response["status"]=="open")
            self.streamFileTextCtrl.SetValue(response["filename"])
            self.streamFileTextCtrl.SetInsertionPointEnd()

    def addMessage(self,msg):
        seq, dateTime, source, level, code, txt = msg.split("|")
        index = self.logListCtrl.InsertStringItem(sys.maxint,seq)
        self.logListCtrl.SetStringItem(index,1,dateTime)
        self.logListCtrl.SetStringItem(index,2,source)
        self.logListCtrl.SetStringItem(index,3,level)
        self.logListCtrl.SetStringItem(index,4,code)
        self.logListCtrl.SetStringItem(index,5,txt.strip()[1:-1])
