import wx
import sys

from ControllerModels import DriverProxy, ControllerRpcHandler, waveforms
from ControllerPanelsGui import CommandLogPanelGui, LaserPanelGui
from ControllerPanelsGui import HotBoxPanelGui, RingdownPanelGui
from ControllerPanelsGui import WlmPanelGui
from Host.autogen import interface
from Host.Common.GraphPanel import Series
from Host.Common import CmdFIFO, SharedTypes, timestamp
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
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
        self.ringdownWfms = [Series(ringdownPoints) for i in range(interface.NUM_VIRTUAL_LASERS)] # Need one for each virtual laser
        wx.CallAfter(self.onSelectGraphType,None)
    def  update(self):
        self.ringdownGraph.Update(delay=0)
    def  onClear(self,evt):
        for s,sel,stats,attr in self.ringdownGraph._pointSeries:
            s.Clear()
    def  onSelectGraphType(self,evt):
        fillColours = ["red","green","blue","yellow","cyan","magenta","black","white"]
        def  printData(data):
            print data.timestamp, data.uncorrectedAbsorbance
        choice = self.graphTypeRadioBox.GetSelection()
        y = ""
        self.appendData = printData
        
        if choice == 0:
            def  lossVsWavenumber(data):
                wavenumber = data.wlmAngle
                loss_u = data.uncorrectedAbsorbance
                loss_c = data.correctedAbsorbance
                waveforms["Ringdown"]["uncorrected"].Add(wavenumber, loss_u)
                waveforms["Ringdown"]["corrected"].Add(wavenumber, loss_c)
            self.ringdownGraph.SetGraphProperties(xlabel='WLM Angle (rad)', # 'Wavenumber - 6000 (1/cm)',
            timeAxes=(False,False),ylabel='Loss (ppm/cm)',grid=True,
            ylabel='Loss (ppm/cm)',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Loss"
            self.appendData = lossVsWavenumber
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
        elif choice == 2:
            def  lossVsRatio1(data):
                loss_u = data.uncorrectedAbsorbance
                loss_c = data.correctedAbsorbance
                ratio1 = data.ratio1
                waveforms["Ringdown"]["uncorrected"].Add(ratio1/32768.0, loss_u)
                waveforms["Ringdown"]["corrected"].Add(ratio1/32768.0, loss_c)
            self.ringdownGraph.SetGraphProperties(xlabel='',
            timeAxes=(False,False),xlabel='Ratio 1',ylabel='Loss (ppm/cm)',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Loss"
            self.appendData = lossVsRatio1
        elif choice == 3:
            def  lossVsRatio2(data):
                loss_u = data.uncorrectedAbsorbance
                loss_c = data.correctedAbsorbance
                ratio2 = data.ratio2
                waveforms["Ringdown"]["uncorrected"].Add(ratio2/32768.0, loss_u)
                waveforms["Ringdown"]["corrected"].Add(ratio2/32768.0, loss_c)
            self.ringdownGraph.SetGraphProperties(xlabel='',
            timeAxes=(False,False),xlabel='Ratio 2',ylabel='Loss (ppm/cm)',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Loss"
            self.appendData = lossVsRatio2
        elif choice == 4:
            def  ratioVsWavenumber(data):
                wavenumber = data.wlmAngle
                ratio1 = data.ratio1
                ratio2 = data.ratio2
                waveforms["Ringdown"]["ratio1"].Add(wavenumber, ratio1/32768.0)
                waveforms["Ringdown"]["ratio2"].Add(wavenumber, ratio2/32768.0)
            self.ringdownGraph.SetGraphProperties(xlabel='WLM Angle (rad)', # 'Wavenumber - 6000 (1/cm)',
            timeAxes=(False,False),ylabel='WLM Ratios',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Ratios"
            self.appendData = ratioVsWavenumber
        elif choice == 5:
            def  tunerVsWavenumber(data):
                wavenumber = data.wlmAngle
                vLaser = (data.laserUsed >> 2) & 7
                waveforms["Ringdown"]["tuner_%d" % (vLaser+1,)].Add(wavenumber, data.tunerValue)
            self.ringdownGraph.SetGraphProperties(xlabel='WLM Angle (rad)', # 'Wavenumber - 6000 (1/cm)',
            timeAxes=(False,False),ylabel='Tuner value',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Tuner"
            self.appendData = tunerVsWavenumber
        elif choice == 6:
            def  tunerVsTime(data):
                utime = timestamp.unixTime(data.timestamp)
                vLaser = (data.laserUsed >> 2) & 7
                waveforms["Ringdown"]["tuner_%d" % (vLaser+1,)].Add(utime, data.tunerValue)
            self.ringdownGraph.SetGraphProperties(xlabel='',
            timeAxes=(True,False),ylabel='Tuner value',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Tuner"
            self.appendData = tunerVsTime
        elif choice == 7:
            def  tunerVsRatio1(data):
                ratio1 = data.ratio1
                vLaser = (data.laserUsed >> 2) & 7
                waveforms["Ringdown"]["tuner_%d" % (vLaser+1,)].Add(ratio1/32768.0, data.tunerValue)
            self.ringdownGraph.SetGraphProperties(xlabel='',
            timeAxes=(False,False),xlabel='Ratio 1',ylabel='Tuner value',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Tuner"
            self.appendData = tunerVsRatio1
        elif choice == 8:
            def  tunerVsRatio2(data):
                ratio2 = data.ratio2
                vLaser = (data.laserUsed >> 2) & 7
                waveforms["Ringdown"]["tuner_%d" % (vLaser+1,)].Add(ratio2/32768.0, data.tunerValue)
            self.ringdownGraph.SetGraphProperties(xlabel='',
            timeAxes=(False,False),xlabel='Ratio 2',ylabel='Tuner value',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Tuner"
            self.appendData = tunerVsRatio2
        elif choice == 9:
            def  wavenumberVsTime(data):
                utime = timestamp.unixTime(data.timestamp)
                wavenumber = data.wlmAngle
                vLaser = (data.laserUsed >> 2) & 7
                waveforms["Ringdown"]["wavenumber_%d" % (vLaser+1,)].Add(utime, wavenumber)
            self.ringdownGraph.SetGraphProperties(xlabel='', 
            timeAxes=(True,False),ylabel='Wavenumber',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Wavenumber"
            self.appendData = wavenumberVsTime
        elif choice == 10:
            def  fineCurrentVsWavenumber(data):
                wavenumber = data.wlmAngle
                vLaser = (data.laserUsed >> 2) & 7
                waveforms["Ringdown"]["fineCurrent_%d" % (vLaser+1,)].Add(wavenumber, data.fineLaserCurrent)
            self.ringdownGraph.SetGraphProperties(xlabel='WLM Angle (rad)', # 'Wavenumber - 6000 (1/cm)',
            timeAxes=(False,False),ylabel='Fine Laser Current',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "FineCurrent"
            self.appendData = fineCurrentVsWavenumber
        elif choice == 11:
            def  fineCurrentVsTime(data):
                utime = timestamp.unixTime(data.timestamp)
                wavenumber = data.wlmAngle
                vLaser = (data.laserUsed >> 2) & 7
                waveforms["Ringdown"]["fineCurrent_%d" % (vLaser+1,)].Add(utime, data.fineLaserCurrent)
            self.ringdownGraph.SetGraphProperties(xlabel='',
            timeAxes=(True,False),ylabel='Fine Laser Current',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "FineCurrent"
            self.appendData = fineCurrentVsTime

        self.ringdownGraph.RemoveAllSeries()

        if y == "Loss":
            if self.uncorrectedCheckBox.IsChecked():
                self.ringdownGraph.AddSeriesAsPoints(
                    waveforms["Ringdown"]["uncorrected"],
                    colour='red',fillcolour='red',marker='square',
                    size=1,width=1)
            if self.correctedCheckBox.IsChecked():
                self.ringdownGraph.AddSeriesAsPoints(
                    waveforms["Ringdown"]["corrected"],
                    colour='green',fillcolour='green',marker='square',
                    size=1,width=1)
        elif y == "FineCurrent":
            for vLaser in range(interface.NUM_VIRTUAL_LASERS):
                self.ringdownGraph.AddSeriesAsPoints(
                    waveforms["Ringdown"]["fineCurrent_%d" % (vLaser+1,)],
                    colour=fillColours[vLaser],fillcolour=fillColours[vLaser],marker='square',
                    size=1,width=1)
        elif y == "Tuner":
            for vLaser in range(interface.NUM_VIRTUAL_LASERS):
                self.ringdownGraph.AddSeriesAsPoints(
                    waveforms["Ringdown"]["tuner_%d" % (vLaser+1,)],
                    colour=fillColours[vLaser],fillcolour=fillColours[vLaser],marker='square',
                    size=1,width=1)
        elif y == "Wavenumber":
            for vLaser in range(interface.NUM_VIRTUAL_LASERS):
                self.ringdownGraph.AddSeriesAsPoints(
                    waveforms["Ringdown"]["wavenumber_%d" % (vLaser+1,)],
                    colour=fillColours[vLaser],fillcolour=fillColours[vLaser],marker='square',
                    size=1,width=1)
        elif y == "Ratios":
            self.ringdownGraph.AddSeriesAsPoints(
                waveforms["Ringdown"]["ratio1"],
                colour='red',fillcolour='red',marker='square',
                size=1,width=1)
            self.ringdownGraph.AddSeriesAsPoints(
                waveforms["Ringdown"]["ratio2"],
                colour='green',fillcolour='green',marker='square',
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
                    colour='red',fillcolour='red',marker='square',
                    size=1,width=2)
            if self.correctedCheckBox.IsChecked():
                self.ringdownGraph.AddSeriesAsPoints(
                    waveforms["Ringdown"]["corrected"],
                    colour='green',fillcolour='green',marker='square',
                    size=1,width=2)

class WlmPanel(WlmPanelGui):
    def __init__(self,*a,**k):
        WlmPanelGui.__init__(self,*a,**k)
        self.photocurrentGraph.SetGraphProperties(
            ylabel='Wavelength Monitor Photocurrents',
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            grid=True,backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.ratioGraph.SetGraphProperties(
            ylabel='Wavelength Monitor Ratios',grid=True,
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.etalon1Wfm = Series(wfmPoints)
        self.reference1Wfm = Series(wfmPoints)
        self.etalon2Wfm = Series(wfmPoints)
        self.reference2Wfm = Series(wfmPoints)
        self.photocurrentGraph.AddSeriesAsLine(self.etalon1Wfm,colour='yellow',width=2)
        self.photocurrentGraph.AddSeriesAsLine(self.reference1Wfm,colour='magenta',width=2)
        self.photocurrentGraph.AddSeriesAsLine(self.etalon2Wfm,colour='green',width=2)
        self.photocurrentGraph.AddSeriesAsLine(self.reference2Wfm,colour='blue',width=2)
        self.ratio1Wfm = Series(wfmPoints)
        self.ratio2Wfm = Series(wfmPoints)
        self.ratioGraph.AddSeriesAsLine(self.ratio1Wfm,colour='red',width=2)
        self.ratioGraph.AddSeriesAsLine(self.ratio2Wfm,colour='cyan',width=2)

    def update(self):
        self.photocurrentGraph.Update(delay=0)
        self.ratioGraph.Update(delay=0)

    def onClear(self,evt):
        for s,sel,stats,attr in self.photocurrentGraph._lineSeries:
            s.Clear()
        for s,sel,stats,attr in self.ratioGraph._lineSeries:
            s.Clear()
                
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
            ylabel='TEC PWM (digU)',grid=True,
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.currentGraph.SetGraphProperties(
            ylabel='Laser Current (mA)',grid=True,
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.temperatureWfm = Series(wfmPoints)
        self.temperatureGraph.AddSeriesAsLine(self.temperatureWfm,
            colour='red',width=2)
        self.tecWfm = Series(wfmPoints)
        self.tecGraph.AddSeriesAsLine(self.tecWfm,
            colour='red',width=2)
        self.currentWfm = Series(wfmPoints)
        self.currentGraph.AddSeriesAsLine(self.currentWfm,
            colour='red',width=2)

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
            colour='red',width=2)
        self.heatsinkTemperatureWfm = Series(wfmPoints)
        self.temperatureGraph.AddSeriesAsLine(self.heatsinkTemperatureWfm,
            colour='blue',width=2)
        self.tecWfm = Series(wfmPoints)
        self.tecGraph.AddSeriesAsLine(self.tecWfm,
            colour='red',width=2)
        self.heaterWfm = Series(wfmPoints)
        self.heaterGraph.AddSeriesAsLine(self.heaterWfm,
            colour='red',width=2)

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
                colour='red',width=2)
        if self.heatsinkTemperatureCheckbox.IsChecked():
            self.temperatureGraph.AddSeriesAsLine(self.heatsinkTemperatureWfm,
                colour='blue',width=2)

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

    def onStreamFileCheck(self, event):
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
        self.logListCtrl.EnsureVisible(index)
