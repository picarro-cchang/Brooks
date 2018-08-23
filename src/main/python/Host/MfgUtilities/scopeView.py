
APP_NAME = "ScopeView"

import sys
import wx
import time
from Queue import Queue, Empty
from numpy import *
from pylab import *
import types
from Host.MfgUtilities.ModeViewGUI import ModeViewGUI
import win32com.client
import pythoncom

from Host.Common import timestamp
from Host.Common.CmdFIFO import CmdFIFOServerProxy
from Host.Common.configobj import ConfigObj
from Host.Common.Listener import Listener
from Host.Common.GraphPanel import Series
from Host.Common.Listener import Listener
from Host.Common.TextListener import TextListener
from Host.Common.SharedTypes import ctypesToDict, RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER, BROADCAST_PORT_RD_RECALC
from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR
from Host.autogen import interface

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

Driver = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,APP_NAME, IsDontCareConnection = False)
FreqConverter = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,APP_NAME, IsDontCareConnection = False)
SpectrumCollector = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,APP_NAME, IsDontCareConnection = False)

def blockMean(y,start,blocksize):
    y = asarray(y)
    n = len(y)
    nblocks = (n-start)/blocksize
    return mean(reshape(y[start:start+nblocks*blocksize],(nblocks,-1)),axis=1)

def xcorr(x,y):
    return real(ifft(fft(x)*conj(fft(y))))

def circshift(x,s):
    return concatenate((x[-s:],x[:-s]))

def _value(valueOrName):
    if isinstance(valueOrName,types.StringType):
        try:
            valueOrName = getattr(interface,valueOrName)
        except AttributeError:
            raise AttributeError("Value identifier not recognized %r" % valueOrName)
    return valueOrName

def setFPGAbits(FPGAblockName,FPGAregName,optList):
    optMask = 0
    optNew = 0
    for opt,val in optList:
        bitpos = 1<<_value("%s_%s_B" % (FPGAregName,opt))
        fieldMask = (1<<_value("%s_%s_W" % (FPGAregName,opt)))-1
        optMask |= bitpos*fieldMask
        optNew  |= bitpos*val
    oldVal = Driver.rdFPGA(FPGAblockName,FPGAregName)
    newVal = ((~optMask) & oldVal) | optNew
    Driver.wrFPGA(FPGAblockName,FPGAregName,newVal)

def stopAcquisition():
    Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_IdleState")
    time.sleep(0.5)

def setTunerOffset(offset):
    Driver.wrFPGA("FPGA_TWGEN","TWGEN_PZT_OFFSET",offset)

def setActiveLaser(laserNum):
    laserMask = 1<<(laserNum-1)
    setFPGAbits("FPGA_INJECT","INJECT_CONTROL",[("LASER_SELECT",laserNum-1)])
    setFPGAbits("FPGA_INJECT","INJECT_CONTROL",[("MODE",0)])
    setFPGAbits("FPGA_INJECT","INJECT_CONTROL",[("LASER_CURRENT_ENABLE",laserMask)])
    setFPGAbits("FPGA_INJECT","INJECT_CONTROL",[("MANUAL_LASER_ENABLE",laserMask)])

def turnOffLasers():
    setFPGAbits("FPGA_INJECT","INJECT_CONTROL",[("MODE",0)])
    for i in range(4):
        laserNum = i+1
        Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % laserNum,"LASER_CURRENT_CNTRL_DisabledState")

def setLaserTemperature(laserNum,setpoint):
    Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % laserNum,"TEMP_CNTRL_EnabledState")
    Driver.wrDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % laserNum,setpoint)

def setLaserCurrent(laserNum,coarse,fine=32768):
    Driver.wrDasReg("LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % laserNum,coarse)
    Driver.wrDasReg("LASER%d_MANUAL_FINE_CURRENT_REGISTER" % laserNum,fine)
    Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % laserNum,"LASER_CURRENT_CNTRL_ManualState")

def setTuner(rampParams=None,ditherParams=None,slopes=None):
    if rampParams is not None:
        sweepLow,winLow,winHigh,sweepHigh = rampParams
        Driver.wrDasReg("TUNER_SWEEP_RAMP_LOW_REGISTER", sweepLow)
        Driver.wrDasReg("TUNER_WINDOW_RAMP_LOW_REGISTER", winLow)
        Driver.wrDasReg("TUNER_WINDOW_RAMP_HIGH_REGISTER", winHigh)
        Driver.wrDasReg("TUNER_SWEEP_RAMP_HIGH_REGISTER", sweepHigh)
    if ditherParams is not None:
        sweepLow,winLow,winHigh,sweepHigh = ditherParams
        Driver.wrDasReg("TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER", sweepLow)
        Driver.wrDasReg("TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER", winLow)
        Driver.wrDasReg("TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER", winHigh)
        Driver.wrDasReg("TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER", sweepHigh)
    if slopes is not None:
        up,down = slopes
        Driver.wrFPGA("FPGA_TWGEN","TWGEN_SLOPE_UP",up)
        Driver.wrFPGA("FPGA_TWGEN","TWGEN_SLOPE_DOWN",down)

class ModeViewFrame(ModeViewGUI):
    configName = 'ModeView.ini'
    mainPos = 500.0
    mainSep = 3000.0
    guiSave = {'text_ctrl':['min_1','max_1'],
               'combo_box':[],
               'checkbox':['autoscale_1']}
    cast = {'text_ctrl':str,
            'combo_box':str,
            'checkbox': lambda x:x == 'True'}
    def __init__(self,*args,**kwargs):
        ModeViewGUI.__init__(self,*args,**kwargs)
        self.maxWaveformPoints = 4095
        self.graph1Waveform = Series(self.maxWaveformPoints)
        self.graph_panel_1.SetGraphProperties(xlabel='PZT Position',timeAxes=(False,False),ylabel='Mode Amplitude',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.graph_panel_1.AddSeriesAsLine(self.graph1Waveform,colour='red',width=2)
        self.text_ctrl_min_1.Bind(wx.EVT_KILL_FOCUS, self.onMin1Enter)
        self.text_ctrl_max_1.Bind(wx.EVT_KILL_FOCUS, self.onMax1Enter)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.restoreGuiSettings()
        self.applySettings()
        cfg = ConfigObj(self.configName)
        stopAcquisition()
        setTunerOffset(0)
        self.slope = 4000
        self.pztPk2pk = 65000
        self.divisor = 512
        self.setupSweep()
        self.selectLaser(2)
        self.setLaserCurrent(36000)
        self.setLaserTemperature(15.0)
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_NUM_SAMP",4095)
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_DIVISOR",self.divisor-1)
        setFPGAbits("FPGA_RDMAN","RDMAN_OPTIONS",[("DITHER_ENABLE",False),("SCOPE_MODE",True),("SCOPE_SLOPE",True)])
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.timer.Start(100)

    def setupSweep(self):
        slope = int(self.slope)
        rmax = int(32768.0+0.5*self.pztPk2pk)
        rmin = int(32768.0-0.5*self.pztPk2pk)
        setTuner(rampParams=(rmin,rmin,rmax,rmax),slopes=(slope,slope))

    def restoreGuiSettings(self):
        cfg = ConfigObj(self.configName)
        for c in cfg:
            if c in self.guiSave:
                for i in cfg[c]:
                    if i in self.guiSave[c]:
                        name = '%s_%s' % (c,i)
                        getattr(eval('self.' + name),'SetValue')(self.cast[c](cfg[c][i]))

    def saveGuiSettings(self):
        cfg = ConfigObj(self.configName)
        for c in self.guiSave:
            if c not in cfg: cfg[c] = {}
            for i in self.guiSave[c]:
                name = '%s_%s' % (c,i)
                cfg[c][i] = getattr(eval('self.' + name),'GetValue')()
        cfg.write()

    def applySettings(self):
        self.onAutoscale1()

    def selectLaser(self,aLaserNum):
        self.aLaserNum = aLaserNum
        setActiveLaser(aLaserNum)

    def setLaserTemperature(self,laserTemp):
        self.laserTemperature = laserTemp
        setLaserTemperature(self.aLaserNum,laserTemp)

    def setLaserCurrent(self,laserCurrent):
        self.laserCurrent = laserCurrent

    def getBlock(self,chan="C3",npoints=1000,aver=50):
        x = asarray(self.dso.GetScaledWaveform(chan,npoints*aver,0))
        return blockMean(x,0,aver)

    def onAutoscale1(self, evt=None):
        if self.checkbox_autoscale_1.IsChecked():
            self.graph_panel_1.SetGraphProperties(YSpec="auto")
        else:
            self.graph_panel_1.SetGraphProperties(YSpec=(float(self.text_ctrl_min_1.GetValue()),float(self.text_ctrl_max_1.GetValue())))
        if evt: evt.Skip()

    def onMin1Enter(self,evt=None):
        if not self.checkbox_autoscale_1.IsChecked():
            self.graph_panel_1.SetGraphProperties(YSpec=(float(self.text_ctrl_min_1.GetValue()),float(self.text_ctrl_max_1.GetValue())))
        if evt: evt.Skip()

    def onMax1Enter(self,evt=None):
        if not self.checkbox_autoscale_1.IsChecked():
            self.graph_panel_1.SetGraphProperties(YSpec=(float(self.text_ctrl_min_1.GetValue()),float(self.text_ctrl_max_1.GetValue())))
        if evt: evt.Skip()

    def onTimer(self, evt=None):
        d = Driver.rdOscilloscopeTrace()
        for x,y in enumerate(d & 16383):
            self.graph1Waveform.Add(x,y)
        self.graph_panel_1.Update(delay=0)
        if evt: evt.Skip()

    def onClear(self,evt=None):
        self.refWt = 0
        self.graph1Waveform.Clear()
        if evt: evt.Skip()

    def onClose(self,evt=None):
        self.timer.Stop()
        self.saveGuiSettings()
        if evt: evt.Skip()

    def onQuit(self,evt=None):
        self.Close()
        self.disconnectScope()
        if evt: evt.Skip()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = ModeViewFrame(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()