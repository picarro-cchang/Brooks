#!/usr/bin/python
#
# FILE:
#   ControllerPanels.py
#
# DESCRIPTION:
#   Code for controller gui panels
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   5-May-2009  sze  Initial version with laser, hot box and command log panels
#  17-Jul-2009  sze  Added ringdown panel
#  27-Jul-2009  sze  Added wavelength monitor panel
#   1-Aug-2009  sze  Added more graph types (loss vs ratio, tuner vs time and ratio) to ringdown panel
#   3-Aug-2009  sze  Renamed MAX_VLASERS to NUM_VIRTUAL_LASERS
#   5-Aug-2009  sze  Corrected typo, ensure last line in log is made visible
#  18-Aug-2009  sze  Added more graph types to ringdown panel, removed black borders from point symbols
#  25-Aug-2009  sze  Changed graph ylabels for two graphs to add units
#  28-Aug-2009  sze  Added pressure, warm box and statistics panels
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import wx
import threading
from math import log10, sqrt
import os
import sys

from WebControllerModels import DriverProxy, RDFreqConvProxy, SpectrumCollectorProxy, ControllerRpcHandler, waveforms, dasInfo
from WebControllerModels import ringdowns, ringdownLock
from WebControllerPanelsGui import CommandLogPanelGui
from WebControllerPanelsGui import LaserPanelGui, PressurePanelGui
from WebControllerPanelsGui import WarmBoxPanelGui, HotBoxPanelGui, RingdownPanelGui
from WebControllerPanelsGui import WlmPanelGui, StatsPanelGui

from Host.autogen import interface
from Host.Common.Allan import AllanVar
from Host.Common.RdStats import RdStats
from Host.Common.GraphPanel import Series, ColorSeries
from Host.Common import CmdFIFO, SharedTypes, timestamp
from Host.Common import jsonRpcTools
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

statsPoints = interface.CONTROLLER_STATS_POINTS
wfmPoints = interface.CONTROLLER_WAVEFORM_POINTS
ringdownPoints = interface.CONTROLLER_RINGDOWN_POINTS

Driver = DriverProxy().rpc
RDFreqConv = RDFreqConvProxy().rpc
SpectrumCollector = SpectrumCollectorProxy().rpc

class RingdownPanel(RingdownPanelGui):
    def __init__(self,*a,**k):
        RingdownPanelGui.__init__(self,*a,**k)
        self.ringdownGraph.SetGraphProperties(xlabel='Wavenumber (1/cm)',
            timeAxes=(False,False),ylabel='Loss (ppm/cm)',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.ringdownWfms = [ColorSeries(ringdownPoints) for i in range(2)]
        self.latestRingdown = None
        self.oldAppendData = None
        wx.CallAfter(self.onSelectGraphType,None)
    def  update(self):
        ringdownLock.acquire()
        try:
            if self.latestRingdown is None or self.appendData != self.oldAppendData:
                for r in ringdowns:
                    self.appendData(r)
                    self.latestRingdown = r.timestamp
            else:
                i = 1
                while i<=len(ringdowns) and ringdowns[-i].timestamp>self.latestRingdown:
                    i += 1
                while i>1:
                    r = ringdowns[-i+1]
                    self.appendData(r)
                    self.latestRingdown = r.timestamp
                    i -= 1
        finally:
            ringdownLock.release()
        self.oldAppendData = self.appendData
        self.ringdownGraph.Update(delay=0)
    def  onClear(self,evt):
        for w in waveforms["Ringdown"].values():
            w.RetainLast()
        self.ringdownGraph.Update(delay=0)
            
    def  onSelectGraphType(self,evt):
        colourNames = ["red","green","blue","yellow","cyan","magenta","black","white"]
        fillColours = [wx.NamedColor(c).GetRGB() for c in colourNames]
        def  printData(data):
            print data.timestamp, data.uncorrectedAbsorbance
        def dataGood(data):
            return not (data.status & interface.RINGDOWN_STATUS_RingdownTimeout)
        
        choice = self.graphTypeRadioBox.GetSelection()
        y = ""
        self.appendData = printData
        if choice == 0:
            def  lossVsWavenumber(data):
                if dataGood(data):
                    #wavenumber = data.wlmAngle
                    wavenumber = data.waveNumber
                    loss_u = data.uncorrectedAbsorbance
                    loss_c = data.correctedAbsorbance
                    waveforms["Ringdown"]["uncorrected"].Add(wavenumber, loss_u)
                    waveforms["Ringdown"]["corrected"].Add(wavenumber, loss_c)
            self.ringdownGraph.SetGraphProperties(xlabel='Wavenumber (1/cm)',
                                                  timeAxes=(False,False),ylabel='Loss (ppm/cm)',grid=True,
                                                  ylabel='Loss (ppm/cm)',grid=True,
                                                  frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
                                                  backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Loss"
            self.appendData = lossVsWavenumber
        elif choice == 1:
            def  lossVsTime(data):
                utime = timestamp.unixTime(data.timestamp)
                if dataGood(data):
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
                if dataGood(data):
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
                if dataGood(data):
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
                if dataGood(data):
                    #wavenumber = data.wlmAngle
                    wavenumber = data.waveNumber
                    ratio1 = data.ratio1
                    ratio2 = data.ratio2
                    waveforms["Ringdown"]["ratio1"].Add(wavenumber, ratio1/32768.0)
                    waveforms["Ringdown"]["ratio2"].Add(wavenumber, ratio2/32768.0)
            self.ringdownGraph.SetGraphProperties(xlabel='Wavenumber (1/cm)',
                                                  timeAxes=(False,False),ylabel='WLM Ratios',grid=True,
                                                  frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
                                                  backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Ratios"
            self.appendData = ratioVsWavenumber
        elif choice == 5:
            def  tunerVsWavenumber(data):
                if dataGood(data):
                    #wavenumber = data.wlmAngle
                    wavenumber = data.waveNumber
                    vLaser = (data.laserUsed >> 2) & 7
                    waveforms["Ringdown"]["tuner"].Add(wavenumber, data.tunerValue,fillColours[vLaser])
            self.ringdownGraph.SetGraphProperties(xlabel='Wavenumber (1/cm)',
            timeAxes=(False,False),ylabel='Tuner value',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Tuner"
            self.appendData = tunerVsWavenumber
        elif choice == 6:
            def  tunerVsTime(data):
                if dataGood(data):
                    utime = timestamp.unixTime(data.timestamp)
                    vLaser = int((data.laserUsed >> 2) & 7)
                    waveforms["Ringdown"]["tuner"].Add(utime, data.tunerValue,fillColours[vLaser])
            self.ringdownGraph.SetGraphProperties(xlabel='',
            timeAxes=(True,False),ylabel='Tuner value',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Tuner"
            self.appendData = tunerVsTime
        elif choice == 7:
            def  tunerVsRatio1(data):
                if dataGood(data):
                    ratio1 = data.ratio1
                    vLaser = (data.laserUsed >> 2) & 7
                    waveforms["Ringdown"]["tuner"].Add(ratio1/32768.0, data.tunerValue,fillColours[vLaser])
            self.ringdownGraph.SetGraphProperties(xlabel='',
            timeAxes=(False,False),xlabel='Ratio 1',ylabel='Tuner value',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Tuner"
            self.appendData = tunerVsRatio1
        elif choice == 8:
            def  tunerVsRatio2(data):
                if dataGood(data):
                    ratio2 = data.ratio2
                    vLaser = (data.laserUsed >> 2) & 7
                    waveforms["Ringdown"]["tuner"].Add(ratio2/32768.0, data.tunerValue,fillColours[vLaser])
            self.ringdownGraph.SetGraphProperties(xlabel='',
            timeAxes=(False,False),xlabel='Ratio 2',ylabel='Tuner value',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Tuner"
            self.appendData = tunerVsRatio2
        elif choice == 9:
            def  wavenumberVsTime(data):
                if dataGood(data):
                    utime = timestamp.unixTime(data.timestamp)
                    #wavenumber = data.wlmAngle
                    wavenumber = data.waveNumber
                    vLaser = (data.laserUsed >> 2) & 7
                    waveforms["Ringdown"]["wavenumber"].Add(utime, wavenumber,fillColours[vLaser])
            self.ringdownGraph.SetGraphProperties(xlabel='', 
            timeAxes=(True,False),ylabel='Wavenumber',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "Wavenumber"
            self.appendData = wavenumberVsTime
        elif choice == 10:
            def  fineCurrentVsWavenumber(data):
                if dataGood(data):
                    #wavenumber = data.wlmAngle
                    wavenumber = data.waveNumber
                    vLaser = (data.laserUsed >> 2) & 7
                    waveforms["Ringdown"]["fineCurrent"].Add(wavenumber, data.fineLaserCurrent,fillColours[vLaser])
            self.ringdownGraph.SetGraphProperties(xlabel='Wavenumber (1/cm)',
            timeAxes=(False,False),ylabel='Fine Laser Current',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            y = "FineCurrent"
            self.appendData = fineCurrentVsWavenumber
        elif choice == 11:
            def  fineCurrentVsTime(data):
                if dataGood(data):
                    utime = timestamp.unixTime(data.timestamp)
                    #wavenumber = data.wlmAngle
                    wavenumber = data.waveNumber
                    vLaser = (data.laserUsed >> 2) & 7
                    waveforms["Ringdown"]["fineCurrent"].Add(utime, data.fineLaserCurrent,fillColours[vLaser])
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
            self.ringdownGraph.AddSeriesAsPoints(
                waveforms["Ringdown"]["fineCurrent"],
                marker='square',
                size=1,width=1)
        elif y == "Tuner":
            self.ringdownGraph.AddSeriesAsPoints(
                waveforms["Ringdown"]["tuner"],
                marker='square',
                size=1,width=1)
        elif y == "Wavenumber":
            self.ringdownGraph.AddSeriesAsPoints(
                waveforms["Ringdown"]["wavenumber"],
                marker='square',
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
        wfmList = [self.etalon1Wfm,self.reference1Wfm,self.etalon2Wfm,self.reference2Wfm,self.ratio1Wfm,self.ratio2Wfm]
        sensorList = ["Etalon1","Reference1","Etalon2","Reference2","Ratio1","Ratio2"] 
        maxDuration = 180000
        jsonRpcTools.plotSensors(wfmList,sensorList,maxDuration)
        self.photocurrentGraph.Update(delay=0)
        self.ratioGraph.Update(delay=0)

    def onClear(self,evt):
        for w in waveforms["Wlm"].values():
            w.RetainLast()
                
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
        self.laserNum = None
        
    def setLaserNum(self,laserNum):
        self.laserNum = laserNum

    def update(self):
        wfmList = [self.temperatureWfm,self.tecWfm,self.currentWfm]
        sensorList = ["Laser%dTemp"%self.laserNum,"Laser%dTec"%self.laserNum,"Laser%dCurrent"%self.laserNum]
        maxDuration = 180000
        jsonRpcTools.plotSensors(wfmList,sensorList,maxDuration)
        self.temperatureGraph.Update(delay=0)
        self.tecGraph.Update(delay=0)
        self.currentGraph.Update(delay=0)

    def onClear(self,evt):
        for w in waveforms["Laser%d" % self.laserNum].values():
            w.RetainLast()
            
class PressurePanel(PressurePanelGui):
    def __init__(self,*a,**k):
        PressurePanelGui.__init__(self,*a,**k)
        self.pressureGraph.SetGraphProperties(
            ylabel='Pressure (torr)',
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            grid=True,backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.propValveGraph.SetGraphProperties(
            ylabel='Proportional Valve (digU)',grid=True,
            timeAxes=(True,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.ambientPressureWfm = Series(wfmPoints)
        # Don't show ambient pressure at initialization
        #self.pressureGraph.AddSeriesAsLine(self.ambientPressureWfm,
        #    colour='red',width=2)
        self.cavityPressureWfm = Series(wfmPoints)
        self.pressureGraph.AddSeriesAsLine(self.cavityPressureWfm,
            colour='green',width=2)
        self.inletValveWfm = Series(wfmPoints)
        self.propValveGraph.AddSeriesAsLine(self.inletValveWfm,
            colour='red',width=2)
        self.outletValveWfm = Series(wfmPoints)
        self.propValveGraph.AddSeriesAsLine(self.outletValveWfm,
            colour='green',width=2)

    def update(self):
        def updateState(indicator,newState):
            if indicator.GetValue() != newState:
                indicator.SetValue(newState)
        wfmList = [self.cavityPressureWfm,self.ambientPressureWfm,self.inletValveWfm,self.outletValveWfm,None]
        sensorList = ["CavityPressure","AmbientPressure","InletValve","OutletValve","ValveMask"]
        maxDuration = 180000
        result = jsonRpcTools.plotSensors(wfmList,sensorList,maxDuration)
        self.pressureGraph.Update(delay=0)
        self.propValveGraph.Update(delay=0)
        valveMask = result["ValveMask"]["ValveMask"]
        if len(valveMask)>0:
            solenoidValveStates = int(valveMask[-1])
            updateState(self.valve1State,wx.CHK_CHECKED if (solenoidValveStates & 0x1) else wx.CHK_UNCHECKED)
            updateState(self.valve2State,wx.CHK_CHECKED if (solenoidValveStates & 0x2) else wx.CHK_UNCHECKED)
            updateState(self.valve3State,wx.CHK_CHECKED if (solenoidValveStates & 0x4) else wx.CHK_UNCHECKED)
            updateState(self.valve4State,wx.CHK_CHECKED if (solenoidValveStates & 0x8) else wx.CHK_UNCHECKED)
            updateState(self.valve5State,wx.CHK_CHECKED if (solenoidValveStates & 0x10) else wx.CHK_UNCHECKED)
            updateState(self.valve6State,wx.CHK_CHECKED if (solenoidValveStates & 0x20) else wx.CHK_UNCHECKED)

    def onClear(self,evt):
        for w in waveforms["Pressure"].values():
            w.RetainLast()

    def onPressureWaveformSelectChanged(self, event):
        self.pressureGraph.RemoveAllSeries()
        if self.ambientPressureCheckbox.IsChecked():
            self.pressureGraph.AddSeriesAsLine(self.ambientPressureWfm,
                colour='red',width=2)
        if self.cavityPressureCheckbox.IsChecked():
            self.pressureGraph.AddSeriesAsLine(self.cavityPressureWfm,
                colour='green',width=2)

    def onValveWaveformSelectChanged(self, event):
        self.propValveGraph.RemoveAllSeries()
        if self.inletValveCheckbox.IsChecked():
            self.propValveGraph.AddSeriesAsLine(self.inletValveWfm,
                colour='red',width=2)
        if self.outletValveCheckbox.IsChecked():
            self.propValveGraph.AddSeriesAsLine(self.outletValveWfm,
                colour='green',width=2)

class WarmBoxPanel(WarmBoxPanelGui):
    def __init__(self,*a,**k):
        WarmBoxPanelGui.__init__(self,*a,**k)
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
        self.etalonTemperatureWfm = Series(wfmPoints)
        self.temperatureGraph.AddSeriesAsLine(self.etalonTemperatureWfm,
            colour='red',width=2)
        self.warmBoxTemperatureWfm = Series(wfmPoints)
        self.temperatureGraph.AddSeriesAsLine(self.warmBoxTemperatureWfm,
            colour='green',width=2)
        self.heatsinkTemperatureWfm = Series(wfmPoints)
        self.temperatureGraph.AddSeriesAsLine(self.heatsinkTemperatureWfm,
            colour='blue',width=2)
        self.tecWfm = Series(wfmPoints)
        self.tecGraph.AddSeriesAsLine(self.tecWfm,
            colour='red',width=2)

    def update(self):
        wfmList = [self.etalonTemperatureWfm,self.warmBoxTemperatureWfm,self.heatsinkTemperatureWfm,self.tecWfm]
        sensorList = ["EtalonTemp","WarmBoxTemp","WarmBoxHeatsinkTemp","WarmBoxTec"] 
        maxDuration = 3600000
        jsonRpcTools.plotSensors(wfmList,sensorList,maxDuration)
        self.temperatureGraph.Update(delay=0)
        self.tecGraph.Update(delay=0)

    def onClear(self,evt):
        for w in waveforms["WarmBox"].values():
            w.RetainLast()
            
    def onWaveformSelectChanged(self, event):
        self.temperatureGraph.RemoveAllSeries()
        if self.etalonTemperatureCheckbox.IsChecked():
            self.temperatureGraph.AddSeriesAsLine(self.etalonTemperatureWfm,
                colour='red',width=2)
        if self.warmBoxTemperatureCheckbox.IsChecked():
            self.temperatureGraph.AddSeriesAsLine(self.warmBoxTemperatureWfm,
                colour='green',width=2)
        if self.heatsinkTemperatureCheckbox.IsChecked():
            self.temperatureGraph.AddSeriesAsLine(self.heatsinkTemperatureWfm,
                colour='blue',width=2)            

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
        self.dasTemperatureWfm = Series(wfmPoints)        
        self.temperatureGraph.AddSeriesAsLine(self.dasTemperatureWfm,
            colour='green',width=2)
        self.tecWfm = Series(wfmPoints)
        self.tecGraph.AddSeriesAsLine(self.tecWfm,colour='red',width=2)
        self.heaterWfm = Series(wfmPoints)
        self.heaterGraph.AddSeriesAsLine(self.heaterWfm,colour='red',width=2)

    def update(self):
        wfmList = [self.cavityTemperatureWfm,self.heatsinkTemperatureWfm,self.dasTemperatureWfm,self.tecWfm,self.heaterWfm]
        sensorList = ["CavityTemp","HotBoxHeatsinkTemp","DasTemp","HotBoxTec","HotBoxHeater"] 
        maxDuration = 3600000
        jsonRpcTools.plotSensors(wfmList,sensorList,maxDuration)
        self.temperatureGraph.Update(delay=0)
        self.tecGraph.Update(delay=0)
        self.heaterGraph.Update(delay=0)

    def onClear(self,evt):
        for w in waveforms["HotBox"].values():
            w.RetainLast()

    def onWaveformSelectChanged(self, event):
        self.temperatureGraph.RemoveAllSeries()
        if self.cavityTemperatureCheckbox.IsChecked():
            self.temperatureGraph.AddSeriesAsLine(self.cavityTemperatureWfm,
                colour='red',width=2)
        if self.heatsinkTemperatureCheckbox.IsChecked():
            self.temperatureGraph.AddSeriesAsLine(self.heatsinkTemperatureWfm,
                colour='blue',width=2)
        if self.dasTemperatureCheckbox.IsChecked():
            self.temperatureGraph.AddSeriesAsLine(self.dasTemperatureWfm,
                colour='green',width=2)

class CommandLogPanel(CommandLogPanelGui):
    acqLabels = dict(start="Start Acquisition",resume="Resume Acquisition",
                     stop="Stop Acquisition",clear="Clear Error")
    def __init__(self,*a,**k):
        CommandLogPanelGui.__init__(self,*a,**k)
        self.seqName = ''
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
        Driver.registerStreamStatusObserver(
            SharedTypes.RPC_PORT_CONTROLLER,token)

    def onStreamFileCheck(self, event):
        """Start or stop collecting sensor stream to an hdf5 file"""
        cb = event.GetEventObject()
        # N.B. The openStreamFile and closeStreamFile functions MUST be
        #  called in VerifyOnly mode, since they perform a "notify" during
        #  execution, which attempts to enqueue another request on the
        #  CmdFIFO before this function is finished.
        if cb.IsChecked():
            Driver.openStreamFile()
        else:
            Driver.closeStreamFile()

    def setStreamFileState(self):
        """Call this within idle task to update stream file state widgets"""
        if self.updateStreamFileState.acquire(False):
            response = Driver.getStreamFileStatus()
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
        self.logListCtrl.SetStringItem(index,5,txt.strip()[1:])
        self.logListCtrl.EnsureVisible(index)
    
    def onStartEngine(self,event):
        Driver.startEngine()

    def onLoadCalibration(self,event):
        fname = RDFreqConv.getWarmBoxCalFilePath()
        if fname:
            defaultDir, defaultFile = os.path.split(fname)
        else:
            defaultDir, defaultFile = os.getcwd(),""
        try:
            dlg = wx.FileDialog(
                None, message="Select warm box calibration file", defaultDir=defaultDir,
                defaultFile=defaultFile, wildcard="Initialization file (*.ini)|*.ini",
                style=wx.OPEN
               )
            if dlg.ShowModal() == wx.ID_OK:
                fname = dlg.GetPath()
                if fname:
                    RDFreqConv.loadWarmBoxCal(fname)
                    Log("Uploading warm box calibration file %s" % fname)
                    self.warmBoxCalFileTextCtrl.SetLabel(os.path.split(fname)[1])
        finally:
            dlg.Destroy()
            
        if fname:
            defaultDir, defaultFile = os.path.split(fname)[0],""
        else:
            defaultDir, defaultFile = os.getcwd(),""            

        fname = RDFreqConv.getHotBoxCalFilePath()
        if fname:
            defaultDir, defaultFile = os.path.split(fname)
        try:
            dlg = wx.FileDialog(
                None, message="Select hot box calibration file", defaultDir=defaultDir,
                defaultFile=defaultFile, wildcard="Initialization file (*.ini)|*.ini",
                style=wx.OPEN
               )
            if dlg.ShowModal() == wx.ID_OK:
                fname = dlg.GetPath()
                RDFreqConv.loadHotBoxCal(fname)
                Log("Uploading hot box calibration file %s" % fname)
                self.hotBoxCalFileTextCtrl.SetLabel(os.path.split(fname)[1])
        finally:
            dlg.Destroy()
                
    def onStartAcquisition(self,event):
        currentLabel = self.startAcquisitionButton.GetLabel()
        if currentLabel == CommandLogPanel.acqLabels["start"]:
            seq = self.seqTextCtrl.GetLabel().strip()
            if seq:
                allSeq = SpectrumCollector.getSequenceNames()
                if seq in allSeq:
                    SpectrumCollector.startSequence(seq)
                else:
                    Log("Sequence %s is not recognized" % seq,Level=2)
                    return
            else:
                Log("No sequence specified")
        elif currentLabel == CommandLogPanel.acqLabels["resume"]:
            Driver.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER,interface.SPECT_CNTRL_RunningState)
        elif currentLabel in [CommandLogPanel.acqLabels["clear"],CommandLogPanel.acqLabels["stop"]]:
            Driver.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER,interface.SPECT_CNTRL_IdleState)

    def updateLoopStatus(self):
        # Update the controller loop status check indicators
        def make3State(status,activeBit,lockedBit):
            result = wx.CHK_UNCHECKED
            if status & (1<<activeBit):
                if status & (1<<lockedBit):
                    result = wx.CHK_CHECKED
                else:
                    result = wx.CHK_UNDETERMINED
            return result
        def update3State(indicator,newState):
            if indicator.Get3StateValue() != newState:
                indicator.Set3StateValue(newState)
        status = Driver.rdDasReg(interface.DAS_STATUS_REGISTER)
        update3State(self.laser1State,make3State(status,interface.DAS_STATUS_Laser1TempCntrlActiveBit,interface.DAS_STATUS_Laser1TempCntrlLockedBit))
        update3State(self.laser2State,make3State(status,interface.DAS_STATUS_Laser2TempCntrlActiveBit,interface.DAS_STATUS_Laser2TempCntrlLockedBit))
        update3State(self.laser3State,make3State(status,interface.DAS_STATUS_Laser3TempCntrlActiveBit,interface.DAS_STATUS_Laser3TempCntrlLockedBit))
        update3State(self.laser4State,make3State(status,interface.DAS_STATUS_Laser4TempCntrlActiveBit,interface.DAS_STATUS_Laser4TempCntrlLockedBit))
        update3State(self.warmBoxState,make3State(status,interface.DAS_STATUS_WarmBoxTempCntrlActiveBit,interface.DAS_STATUS_WarmBoxTempCntrlLockedBit))
        update3State(self.hotBoxState,make3State(status,interface.DAS_STATUS_CavityTempCntrlActiveBit,interface.DAS_STATUS_CavityTempCntrlLockedBit))
    def updateCalFileStatus(self):
        # Update the warm box and hot box calibration file names from the RDFreqConverter
        fname = os.path.split(RDFreqConv.getWarmBoxCalFilePath())[1]
        text = self.warmBoxCalFileTextCtrl.GetLabel()
        if text != fname:
            self.warmBoxCalFileTextCtrl.SetLabel(fname)
        fname = os.path.split(RDFreqConv.getHotBoxCalFilePath())[1]
        text = self.hotBoxCalFileTextCtrl.GetLabel()
        if text != fname:
            self.hotBoxCalFileTextCtrl.SetLabel(fname)

    def updateAcquisitionState(self):
        # Update the acquisition button label and the associated text control
        state = Driver.rdDasReg(interface.SPECT_CNTRL_STATE_REGISTER)
        if state == interface.SPECT_CNTRL_IdleState:
            self.startAcquisitionButton.SetLabel(CommandLogPanel.acqLabels["start"])
        elif state == interface.SPECT_CNTRL_PausedState:
            self.startAcquisitionButton.SetLabel(CommandLogPanel.acqLabels["resume"])
        elif state == interface.SPECT_CNTRL_ErrorState:
            self.startAcquisitionButton.SetLabel(CommandLogPanel.acqLabels["clear"])
        else:
            self.startAcquisitionButton.SetLabel(CommandLogPanel.acqLabels["stop"])
        t = SpectrumCollector.sequencerGetCurrent()
        result = ''
        if t is not None:
            seq,scheme,repeat,schemeName = t
            schemeName = os.path.split(schemeName)[-1]
            result = "%s: %s" % (seq,schemeName)
            self.seqTextCtrl.SetValue(result)
        else:
            seq = self.seqTextCtrl.GetValue().split(':')
            if len(seq)>1:
                self.seqTextCtrl.SetValue(seq[0])
        return result
        
    def disableAll(self):
        self.startEngineButton.Enable(False)
        self.laser1State.Enable(False)
        self.laser2State.Enable(False)
        self.laser3State.Enable(False)
        self.laser4State.Enable(False)
        self.warmBoxState.Enable(False)
        self.hotBoxState.Enable(False)
        self.streamFileCheckbox.Enable(False)
        self.streamFileTextCtrl.Enable(False)
        self.loadCalibrationButton.Enable(False)
        self.warmBoxCalFileTextCtrl.Enable(False)
        self.hotBoxCalFileTextCtrl.Enable(False)
        self.startAcquisitionButton.Enable(False)
        self.seqTextCtrl.Enable(False)
        #self.logListCtrl.Enable(False)
      
    def enableAll(self):
        self.startEngineButton.Enable(True)
        self.laser1State.Enable(True)
        self.laser2State.Enable(True)
        self.laser3State.Enable(True)
        self.laser4State.Enable(True)
        self.warmBoxState.Enable(True)
        self.hotBoxState.Enable(True)
        self.streamFileCheckbox.Enable(True)
        self.streamFileTextCtrl.Enable(True)
        self.loadCalibrationButton.Enable(True)
        self.warmBoxCalFileTextCtrl.Enable(True)
        self.hotBoxCalFileTextCtrl.Enable(True)
        self.startAcquisitionButton.Enable(True)
        self.seqTextCtrl.Enable(True)
        #self.logListCtrl.Enable(True)
        
class StatsPanel(StatsPanelGui):
    def __init__(self,*a,**k):
        StatsPanelGui.__init__(self,*a,**k)
        self.lossGraph.SetGraphProperties(
            xlabel='log10[Number of ringdowns]',
            ylabel='log10[Allan std dev(Loss)]',
            grid=True,
            timeAxes=(False,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            grid=True,backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.waveNumberGraph.SetGraphProperties(
            xlabel='log10[Number of ringdowns]',
            ylabel='log10[Allan std dev(Wavenumber)]',
            grid=True,
            timeAxes=(False,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.ratio1Graph.SetGraphProperties(
            xlabel='log10[Number of ringdowns]',
            ylabel='log10[Allan std dev(Ratio1)]',
            grid=True,
            timeAxes=(False,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.ratio2Graph.SetGraphProperties(
            xlabel='log10[Number of ringdowns]',
            ylabel='log10[Allan std dev(Ratio2)]',
            grid=True,
            timeAxes=(False,False),
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(
                wx.SYS_COLOUR_3DFACE))
        self.lossAllanVar = AllanVar(statsPoints)
        self.lossStats = Series(statsPoints)
        self.lossGraph.AddSeriesAsPoints(self.lossStats,
                colour='red',fillcolour='red',marker='square',
                size=1,width=1)
        self.waveNumberAllanVar = AllanVar(statsPoints)
        self.waveNumberStats = Series(statsPoints)
        self.waveNumberGraph.AddSeriesAsPoints(self.waveNumberStats,
                colour='red',fillcolour='red',marker='square',
                size=1,width=1)
        self.ratio1AllanVar = AllanVar(statsPoints)
        self.ratio1Stats = Series(statsPoints)
        self.ratio1Graph.AddSeriesAsPoints(self.ratio1Stats,
                colour='red',fillcolour='red',marker='square',
                size=1,width=1)
        self.ratio2AllanVar = AllanVar(statsPoints)
        self.ratio2Stats = Series(statsPoints)
        self.ratio2Graph.AddSeriesAsPoints(self.ratio2Stats,
                colour='red',fillcolour='red',marker='square',
                size=1,width=1)
        self.rdStats = RdStats(100)
        self.active = False
        
    def appendData(self,data):
        if self.active and 0 == (data.status & interface.RINGDOWN_STATUS_RingdownTimeout):
            self.rdStats.processDatum(data.timestamp/1000.0,data.uncorrectedAbsorbance)
            self.lossAllanVar.processDatum(data.uncorrectedAbsorbance)
            #self.waveNumberAllanVar.processDatum(data.wlmAngle)
            self.waveNumberAllanVar.processDatum(data.waveNumber)
            self.ratio1AllanVar.processDatum(data.ratio1)
            self.ratio2AllanVar.processDatum(data.ratio2)
                
    def updateSeriesAndStats(self):
        meanLoss,shot2shot,rate = self.rdStats.getStats()
        self.meanLossTextCtrl.SetValue("%.4f" % meanLoss)
        self.rateTextCtrl.SetValue("%.1f" % rate)
        self.lossStats.Clear()
        n,v = self.lossAllanVar.getVariances()
        self.ringdownsTextCtrl.SetValue("%d" % n)
        for k in range(statsPoints):
            if v[k]>0: self.lossStats.Add(log10(2**k),0.5*log10(v[k]))
        self.stdLossTextCtrl.SetValue("%.4f" % (1000.0*sqrt(v[0]),))
        if rate != 0.0:
            self.sensitivityTextCtrl.SetValue("%.5f" % (1000.0*sqrt(v[0]/rate),))
        if meanLoss != 0.0: self.shotToShotTextCtrl.SetValue("%.3f" % (100.0*sqrt(v[0])/meanLoss))    
        self.waveNumberStats.Clear()
        n,v = self.waveNumberAllanVar.getVariances()
        for k in range(statsPoints):
            if v[k]>0: self.waveNumberStats.Add(log10(2**k),0.5*log10(v[k]))
        # TO DO: Replace with proper calculation of frequency standard deviation (MHz) from wavenumber
        fStdDev = 29979.2458*sqrt(v[0])
        self.freqStdDevTextCtrl.SetValue("%.3f" % fStdDev)
        self.ratio1Stats.Clear()
        n,v = self.ratio1AllanVar.getVariances()
        for k in range(statsPoints):
            if v[k]>0: self.ratio1Stats.Add(log10(2**k),0.5*log10(v[k]))
        self.ratio2Stats.Clear()
        n,v = self.ratio2AllanVar.getVariances()
        for k in range(statsPoints):
            if v[k]>0: self.ratio2Stats.Add(log10(2**k),0.5*log10(v[k]))
            
    def update(self):
        self.updateSeriesAndStats()
        self.lossGraph.Update(delay=0)
        self.waveNumberGraph.Update(delay=0)
        self.ratio1Graph.Update(delay=0)
        self.ratio2Graph.Update(delay=0)

    def onStartStop(self,evt):
        if self.active:
            self.active = False
            self.startStopButton.SetLabel("Start")
            self.ringdownsTextCtrl.Disable()
            self.meanLossTextCtrl.Disable()
            self.stdLossTextCtrl.Disable()
            self.shotToShotTextCtrl.Disable()
            self.rateTextCtrl.Disable()
            self.sensitivityTextCtrl.Disable()
            self.freqStdDevTextCtrl.Disable()
        else:
            self.active = True
            self.startStopButton.SetLabel("Stop")
            self.rdStats.reset()
            self.lossAllanVar.reset()
            self.lossStats.Clear()
            self.waveNumberAllanVar.reset()
            self.waveNumberStats.Clear()
            self.ratio1AllanVar.reset()
            self.ratio1Stats.Clear()
            self.ratio2AllanVar.reset()
            self.ratio2Stats.Clear()
            self.ringdownsTextCtrl.Enable()
            self.meanLossTextCtrl.Enable()
            self.stdLossTextCtrl.Enable()
            self.shotToShotTextCtrl.Enable()
            self.rateTextCtrl.Enable()
            self.sensitivityTextCtrl.Enable()
            self.freqStdDevTextCtrl.Enable()
