APP_NAME = "BuildStation"

import sys
import wx
import time
from collections import deque
from Queue import Queue, Empty
import inspect
from numpy import *
from fastLomb import fastLomb
import types
from Host.Common import timestamp
from Host.Common.CmdFIFO import CmdFIFOServerProxy
from Host.Common.configobj import ConfigObj
from Host.Common.Listener import Listener
from Host.Common.GraphPanel import Series
from Host.Common.Listener import Listener
from Host.Common.SharedTypes import ctypesToDict, RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER, BROADCAST_PORT_RD_RECALC
from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR
from Host.autogen import interface
from Host.Utilities.SuperBuildStation.BuildStationCommon import _value, setFPGAbits, Driver, FreqConverter, SpectrumCollector

class RingdownAnalyzer(object):
    def __init__(self,frame,config):
        self.frame = frame
        self.config = config
        self.minGraphPoints = 500
        self.maxWaveformPoints = 20000
        self.graphPoints = int(self.frame.text_ctrl_graph_points.GetValue())

        self.maxSpectrumPoints = 40000
        self.maxRipplePoints = 5*self.maxSpectrumPoints
        self.waveNoArray = zeros(self.maxSpectrumPoints,float)
        self.uLossArray  = zeros(self.maxSpectrumPoints,float)
        self.timestampArray  = zeros(self.maxSpectrumPoints,uint64)
        self.nextFree = 0
        self.dataLen = 0
        self.limitWaveforms = []
        if '_Ripple Lines' in self.config:
            lines = self.config["_Ripple Lines"]
            for l in lines:
                if l.startswith('Line'):
                    x1,y1,x2,y2 = [float(s) for s in lines[l]]
                    limitWaveform = Series(2)
                    limitWaveform.Add(x1,y1)
                    limitWaveform.Add(x2,y2)
                    self.limitWaveforms.append(limitWaveform)
        self.spectrumWaveformGood = Series(self.maxSpectrumPoints)
        self.spectrumWaveformBad = Series(self.maxSpectrumPoints)
        self.rippleWaveform = Series(self.maxRipplePoints)
        self.rejectionWindow = float(self.frame.text_ctrl_rejection_window.GetValue())
        self.rejectionScale = float(self.frame.text_ctrl_rejection_scale.GetValue())
        self.frame.graph_panel_spectrum.SetGraphProperties(xlabel='Wavenumber',timeAxes=(False,False),ylabel='Ripple (ppb/cm)',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.frame.graph_panel_spectrum.AddSeriesAsPoints(self.spectrumWaveformGood,colour='blue',fillcolour='blue',marker='square',size=1,width=1)
        self.frame.graph_panel_spectrum.AddSeriesAsPoints(self.spectrumWaveformBad,colour='red',fillcolour='red',marker='square',size=1,width=1)
        self.frame.graph_panel_ripple.SetGraphProperties(xlabel='Ripple Period',timeAxes=(False,False),ylabel='Ripple Amplitude (ppb/cm)',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            XSpec=(0.0,2.0))
        self.frame.graph_panel_ripple.AddSeriesAsLine(self.rippleWaveform,colour='blue',width=2)
        for limitWaveform in self.limitWaveforms:
            self.frame.graph_panel_ripple.AddSeriesAsLine(limitWaveform,colour='red',width=4)

        self.rdQueue = Queue(500)
        self.graph1Waveform = Series(self.maxWaveformPoints)
        self.graph2Waveform = Series(self.maxWaveformPoints)
        self.graphAgainstTime()
        self.rdListener = Listener(self.rdQueue,BROADCAST_PORT_RD_RECALC,interface.ProcessedRingdownEntryType,self.rdFilter,retry=True)
        self.discardSamples = 0
        self.varDeque = deque()
        self.varSum = zeros(3,dtype=float)
        self.varSumSq = zeros(3,dtype=float)
        self.varPoints = 200
        self.latency = 500
        self.cavityPressure = 140
        self.lastRdTs = None
        rateAverage = 100
        self.rateAverageFactor = 1./rateAverage
        self.averageInterval = 0.1
        self.avg_rd_time = 0.0
        self.rd_time = 0.0
        self.s2s = 0.0
        self.rdIndex = 0
        self.timerCount = 0
        self.tsLast = timestamp.getTimestamp()
        self.setupObservers()
        self.active = False

    def setupObservers(self):
        f = self.frame
        f.registerObserver("onClear",self.onClear)
        f.registerObserver("onGraphPointsEnter",self.onGraphPointsEnter)
        f.registerObserver("onRdThresholdEnter",self.onRdThresholdEnter)
        f.registerObserver("onDitherEnable",self.onDitherEnable)
        f.registerObserver("onRejectionWindowEnter",self.onRejectionWindowEnter)
        f.registerObserver("onRejectionScaleEnter",self.onRejectionScaleEnter)

    def start(self):
        if not self.active:
            self.active = True
            Driver.wrFPGA("FPGA_RDMAN","RDMAN_DIVISOR",1)
            setFPGAbits("FPGA_RDMAN","RDMAN_OPTIONS",[("SCOPE_MODE",False)])
            self.captureTimer()

    def stop(self):
        if self.active:
            self.releaseTimer()
            self.active = False

    def captureTimer(self):
        f = self.frame
        f.registerObserver("onTimer",self.onTimer)
        self.frame.startTimer(100)

    def releaseTimer(self):
        f = self.frame
        self.frame.stopTimer()
        f.deregisterObserver("onTimer",self.onTimer)

    def graphAgainstRingdown(self):
        self.frame.graph_panel_1.SetGraphProperties(xlabel='Ringdown',timeAxes=(False,False),ylabel='Ringdown Index',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.frame.graph_panel_1.AddSeriesAsPoints(self.graph1Waveform,colour='red',fillcolour='red',marker='square',size=1,width=1)
        self.frame.graph_panel_2.SetGraphProperties(xlabel='Ringdown',timeAxes=(False,False),ylabel='Shot to shot (%)',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.frame.graph_panel_2.AddSeriesAsPoints(self.graph2Waveform,colour='red',fillcolour='red',marker='square',size=1,width=1)
        self.plotType = 'ringdown'

    def graphAgainstTime(self):
        self.frame.graph_panel_1.SetGraphProperties(xlabel='Time',timeAxes=(True,False),ylabel='RD Time (us)',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.frame.graph_panel_1.AddSeriesAsPoints(self.graph1Waveform,colour='red',fillcolour='red',marker='square',size=1,width=1)
        self.frame.graph_panel_2.SetGraphProperties(xlabel='Time',timeAxes=(True,False),ylabel='Shot to shot (%)',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.frame.graph_panel_2.AddSeriesAsPoints(self.graph2Waveform,colour='red',fillcolour='red',marker='square',size=1,width=1)
        self.plotType = 'time'

    def graphAgainstWavenumber(self):
        self.frame.graph_panel_1.SetGraphProperties(xlabel='Wavenumber',timeAxes=(False,False),ylabel='RD Time (us)',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.frame.graph_panel_1.AddSeriesAsPoints(self.graph1Waveform,colour='red',fillcolour='red',marker='square',size=1,width=1)
        self.frame.graph_panel_2.SetGraphProperties(xlabel='Wavenumber',timeAxes=(False,False),ylabel='Shot to shot (%)',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.frame.graph_panel_2.AddSeriesAsPoints(self.graph2Waveform,colour='red',fillcolour='red',marker='square',size=1,width=1)
        self.plotType = 'wavenumber'

    def rdFilter(self,data):
        try:
            localDict = ctypesToDict(data)
            ts = localDict['timestamp']
            t = timestamp.unixTime(ts)
            uLoss = localDict['uncorrectedAbsorbance']
            wavenum = localDict['waveNumber']
            cavityPressure = localDict['cavityPressure']
            if uLoss != 0.0:
                return ts,t,wavenum,uLoss,cavityPressure
        except Exception,e:
            print "rdFilter exception: %s, %r" % (e,e)

    def onRefresh(self):
        self.frame.text_ctrl_graph_points.SetValue("%d" % self.graphPoints)
        self.frame.text_ctrl_rd_threshold.SetValue("%d" % Driver.rdDasReg("SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER"))

    def onGraphPointsEnter(self,frame):
        self.graphPoints = int(frame.text_ctrl_graph_points.GetValue())
        if self.graphPoints < self.minGraphPoints:
            self.graphPoints = self.minGraphPoints
        elif self.graphPoints > self.maxWaveformPoints:
            self.graphPoints = self.maxWaveformPoints
        frame.text_ctrl_graph_points.SetValue('%s' % self.graphPoints)
        self.setGraphPoints()

    def setGraphPoints(self,graphPoints=None):
        if graphPoints is not None: self.graphPoints = graphPoints
        self.graph1Waveform.setMaxPoints(self.graphPoints)
        self.graph2Waveform.setMaxPoints(self.graphPoints)

    def onRdThresholdEnter(self,frame):
        rdThreshold = int(frame.text_ctrl_rd_threshold.GetValue())
        rdThreshold = min(16383,max(0,rdThreshold))
        frame.text_ctrl_rd_threshold.SetValue('%s' % rdThreshold)
        self.setRdThreshold(rdThreshold)

    def setRdThreshold(self,rdThreshold):
        Driver.wrDasReg("SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER",rdThreshold)
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_THRESHOLD",rdThreshold)

    def onDitherEnable(self,frame):
        if frame.checkbox_dither_enable.IsChecked():
            setFPGAbits("FPGA_RDMAN","RDMAN_OPTIONS",[("DITHER_ENABLE",True)])
        else:
            setFPGAbits("FPGA_RDMAN","RDMAN_OPTIONS",[("DITHER_ENABLE",False)])

    def onTimer(self,frame):
        pageNum = frame.notebook_graphs.GetSelection()
        pageText = frame.notebook_graphs.GetPageText(pageNum)
        c = 0.0299792458
        self.timerCount += 1
        tsNow = timestamp.getTimestamp()
        self.tsLast = tsNow
        while not self.rdQueue.empty():
            try:
                ts,t,wavenum,uLoss,self.cavityPressure = self.rdQueue.get(timeout=0.1)
            except Empty:
                continue

            self.waveNoArray[self.nextFree] = wavenum
            self.uLossArray[self.nextFree] = uLoss
            self.timestampArray[self.nextFree] = ts
            self.nextFree += 1
            if self.nextFree >= self.maxSpectrumPoints:
                self.nextFree -= self.maxSpectrumPoints
            self.dataLen = min(self.maxSpectrumPoints,self.dataLen+1)

            datum = array([uLoss,t,wavenum])
            if self.discardSamples > 0:
                self.discardSamples -= 1
                self.averageInterval = 0.1
                continue
            else:
                if self.lastRdTs != None:
                    self.averageInterval = (1.0-self.rateAverageFactor)*self.averageInterval + \
                                            0.001*self.rateAverageFactor*(ts-self.lastRdTs)
                self.lastRdTs = ts
                self.varDeque.append(datum)
                self.varSum += datum
                self.varSumSq += datum**2
                npoints = len(self.varDeque)
                if npoints > self.varPoints:
                    npoints -= 1
                    oldDatum = self.varDeque.popleft()
                    self.varSum -= oldDatum
                    self.varSumSq -= oldDatum**2
                meanLoss = self.varSum[0]/npoints
                self.avg_rd_time = 1/(c*meanLoss)
                meanTime = self.varSum[1]/npoints
                meanWavenum = self.varSum[2]/npoints
                stdDevLoss = sqrt(self.varSumSq[0]/npoints - meanLoss**2)
                self.s2s = 100.0*stdDevLoss/meanLoss
                self.rd_time = 1/(c*uLoss)
                if self.plotType == 'time':
                    self.graph1Waveform.Add(t,self.rd_time)
                    self.graph2Waveform.Add(t,self.s2s)
                elif self.plotType == 'ringdown':
                    self.graph1Waveform.Add(self.rdIndex,self.rd_time)
                    self.graph2Waveform.Add(self.rdIndex,self.s2s)
                    self.rdIndex += 1
                elif self.plotType == 'wavenumber':
                    self.graph1Waveform.Add(wavenum,self.rd_time)
                    self.graph2Waveform.Add(meanWavenum,self.s2s)
                if tsNow-ts < self.latency:
                    break
        if pageText == 'Ripple Analysis' and self.timerCount % 20 == 0:
            if self.dataLen > 0:
                ofac = 10
                hifac = 0.5
                x = self.waveNoArray[:self.dataLen]
                y = self.uLossArray[:self.dataLen]
                good = arange(self.dataLen,dtype=int) # Indices of good points
                good = good[y>0]
                for _ in range(50):
                    if len(good)==0: break
                    trend = polyval(polyfit(x[good],y[good],1),x)
                    y1 = y - trend
                    peak_pos = good[argmax(y1[good])]
                    peak_val = y1[peak_pos]
                    peak_waveno = x[peak_pos]
                    good = good[abs(x[good]-peak_waveno) > self.rejectionWindow]
                    noiseLev = std(y1[good])
                    if peak_val < self.rejectionScale*noiseLev: break
                overRange = abs(y-mean(trend)) > trend.ptp() + 8*noiseLev
                if len(good)>0:
                    px,py,nout,jmax,prob,datavar = fastLomb(x[good],y1[good],ofac,hifac)
                    self.spectrumWaveformGood.Clear()
                    for xx,yy in zip(x[good],y1[good]):
                        self.spectrumWaveformGood.Add(xx,1000.0*yy)
                    bad = ones(self.dataLen,dtype=bool) # Indices of good points
                    bad[good] = False
                    bad[overRange] = False
                    self.spectrumWaveformBad.Clear()
                    for xx,yy in zip(x[bad],y1[bad]):
                        self.spectrumWaveformBad.Add(xx,1000.0*yy)
                    sel = (1/px)>0.01
                    py = 2000*sqrt(datavar*py/self.dataLen)
                    self.rippleWaveform.Clear()
                    for xx,yy in zip(1/px[sel],py[sel]):
                        self.rippleWaveform.Add(xx,yy)
                    self.frame.graph_panel_ripple.Update(delay=0)
                    self.frame.graph_panel_spectrum.Update(delay=0)

        self.rd_rate = 1.0/self.averageInterval
        self.frame.graph_panel_1.Update(delay=0)
        currXAxis = tuple(self.frame.graph_panel_1.GetLastDraw()[1])
        self.frame.graph_panel_2.SetGraphProperties(XSpec=currXAxis)
        self.frame.graph_panel_2.Update(delay=0)
        self.frame.text_ctrl_rd_time.SetValue("%.3f" % self.avg_rd_time)
        self.frame.text_ctrl_s2s.SetValue("%.4f" % self.s2s)
        self.frame.text_ctrl_rd_rate.SetValue("%.1f" % self.rd_rate)
        self.frame.text_ctrl_cavity_pressure.SetValue("%.2f" % self.cavityPressure)

    def clearBuffers(self):
        time.sleep(1.0)
        while not self.rdQueue.empty():
            while not self.rdQueue.empty():
                self.rdQueue.get(timeout=0.1)
            time.sleep(2.0)
        self.varSum = zeros(3,dtype=float)
        self.varSumSq = zeros(3,dtype=float)
        while len(self.varDeque)>0: self.varDeque.popleft()
        self.discardSamples = 10

    def onClear(self,frame):
        self.graph1Waveform.Clear()
        self.graph2Waveform.Clear()
        self.spectrumWaveformBad.Clear()
        self.spectrumWaveformGood.Clear()
        self.rippleWaveform.Clear()
        self.rdIndex = 0
        self.nextFree = 0
        self.dataLen = 0
        try:
            self.frame.graph_panel_1.Update()
            self.frame.graph_panel_2.Update()
            self.frame.graph_panel_ripple.Update()
            self.frame.graph_panel_spectrum.Update()
        except:
            pass

    def onRejectionScaleEnter(self,frame):
        self.rejectionScale = float(frame.text_ctrl_rejection_scale.GetValue())

    def onRejectionWindowEnter(self,frame):
        self.rejectionWindow = float(frame.text_ctrl_rejection_window.GetValue())