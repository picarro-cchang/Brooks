import wx
import sys
from Host.Common.GraphPanel import GraphPanel, Sequence, Series
from Host.Common.CmdFIFO import CmdFIFOServerProxy
from Host.Common.configobj import ConfigObj
from Host.Common.SharedTypes import ctypesToDict, RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER, BROADCAST_PORT_RD_RECALC
from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR 
from Host.autogen import interface
import numpy
import os
from threading import Thread
import Queue
import time
import types
import inspect
from numpy.fft import *

APP_NAME = "DetectorSD"

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = os.path.abspath(sys.argv[0])

Driver = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,APP_NAME, IsDontCareConnection = False)
FreqConverter = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,APP_NAME, IsDontCareConnection = False)
SpectrumCollector = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,APP_NAME, IsDontCareConnection = False)


def AmplitudeSpectralDensity(x, y):
# Algorithm from Heinzel, Rudiger, and Schilling " Spectrum and spectral-density estimation 
#     by the Discrete Fourier Transform, including a comprehensive list of window functions 
#     and some new flat-top windows"
# HFT95 window chosen for compatibility with Agilent spectrum analyzers
# Returns the RMS amplitude spectral density, in units/sqrt(Hz)
    N = x.shape[0]
    if N%2 == 1:
        x = numpy.delete(x, N-1, 0)
        y = numpy.delete(y, N-1, 0)
        N -= 1
        
    fs = 1/(x[1] - x[0])
    a, b = numpy.polyfit(x, y, 1)
    y = y - (a*x + b)
    windoweddata = numpy.zeros(N)
    S1, S2 = 0.0, 0.0
    for i in range(N):
        z = 2*numpy.pi*i/N
        w = 1 - 1.9383379*numpy.cos(z) + 1.3045202*numpy.cos(2*z) - 0.4028270*numpy.cos(3*z) + 0.0350665*numpy.cos(4*z)
        S1 += w
        S2 += w*w
        windoweddata[i] = y[i]*w
    
    ENBW = fs*S2/S1**2
    spectrum = (numpy.sqrt(2)/S1)*numpy.abs(fft(windoweddata))/numpy.sqrt(ENBW)    
    frequency = fftfreq(N, d=1/fs)
    sieve = frequency > 0
    return frequency[sieve], spectrum[sieve], ENBW

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

def setAnalyzerTuningMode(mode):
    Driver.wrDasReg("ANALYZER_TUNING_MODE_REGISTER",mode)
    
def setSpectCntrlDiagnostic():
    Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_DiagnosticState")
    
def setTunerOffset(offset):
    Driver.wrFPGA("FPGA_TWGEN","TWGEN_PZT_OFFSET",offset)
    
def setActiveLaser(laserNum):
    laserMask = 1<<(laserNum-1)
    setFPGAbits("FPGA_INJECT","INJECT_CONTROL",[("LASER_SELECT",laserNum-1)])
    setFPGAbits("FPGA_INJECT","INJECT_CONTROL",[("MODE",0)])
    setFPGAbits("FPGA_INJECT","INJECT_CONTROL",[("LASER_CURRENT_ENABLE",laserMask)])
    setFPGAbits("FPGA_INJECT","INJECT_CONTROL",[("MANUAL_LASER_ENABLE",laserMask)])

def setDirectTune(enable):
    setFPGAbits("FPGA_LASERLOCKER","LASERLOCKER_OPTIONS",[("DIRECT_TUNE",enable)])
    
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

class ScopePanel(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        # Define the graph panel
        bg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        self.graphPanel1 = GraphPanel(parent=self,id=-1)
        self.graphPanel1.SetGraphProperties(xlabel='Time (ms)',timeAxes=(False,False),ylabel='Detector Output (digU)',
            grid=True,frameColour=bg,backgroundColour=bg)
        self.graphPanel1.Update()
        self.graphPanel2 = GraphPanel(parent=self,id=-1)
        self.graphPanel2.SetGraphProperties(xlabel='Frequency (Hz)',timeAxes=(False,False),logScale=(True,True),ylabel='Spectral Density of Detector Output (digU/rtHz)',
            grid=True,frameColour=bg,backgroundColour=bg)
        self.graphPanel1.Update()
        self.graphPanel2.Update()
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.graphPanel1,proportion=1,flag=wx.GROW)
        vbox.Add(self.graphPanel2,proportion=1,flag=wx.GROW)
        self.SetSizer(vbox)
        vbox.Fit(self)
        # Create the sequences for the graphs
        self.maxWaveformPoints = 4096
        self.graph1Waveform = Series(self.maxWaveformPoints)
        self.graph2Waveform = Series(self.maxWaveformPoints)
        self.graphPanel1.RemoveAllSeries()
        self.graphPanel1.AddSeriesAsLine(self.graph1Waveform,statsFlag=True,colour="red",width=1)
        self.graphPanel2.RemoveAllSeries()
        self.graphPanel2.AddSeriesAsLine(self.graph2Waveform,colour="blue",width=1)
    def setText(self,x,y,strings):
        self.graphPanel1.RemoveAllText()
        self.graphPanel1.Text(x,y,strings,color="black",just=(0.5,1.2))
    def Update(self):
        self.graphPanel1.Update()
        self.graphPanel2.Update()
    def setXLim(self,xMin,xMax):
        self.graphPanel1.SetGraphProperties(XSpec=(xMin,xMax))
        #self.graphPanel2.SetGraphProperties(XSpec=(xMin,xMax))
    def setYLim1(self,yMin,yMax):
        self.graphPanel1.SetGraphProperties(YSpec=(yMin,yMax))
    def setYLim2(self,yMin,yMax):
        self.graphPanel2.SetGraphProperties(YSpec=(yMin,yMax))

class ControlPanel(wx.Panel):        
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        
        self.handlers = {}
        self.serialNumber = ""
        self.average = 64
        self.averageCount = 0
        self.enableAverage = False
        self.enable = True
        
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        
        self.check_box_enable_average = wx.CheckBox(self, -1, "Exponential Average")
        self.label_average = wx.StaticText(self, -1, "Average")
        self.text_ctrl_average = wx.TextCtrl(self, -1, "%d" % self.average, style=wx.TE_PROCESS_ENTER)
        self.check_box_enable = wx.CheckBox(self, -1, "Enable")
        self.check_box_enable.SetValue(True)
        self.label_std_dev = wx.StaticText(self, -1, "Std Dev of Data")
        self.text_ctrl_std_dev = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        self.label_mean = wx.StaticText(self, -1, "Eq. Noise Bandwidth (kHz)")
        self.text_ctrl_mean = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        self.btn1 = wx.Button(self, label='Save Spectrum')
        
        sizer_1.Add(self.check_box_enable_average, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.label_average,            0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.text_ctrl_average,        0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        sizer_1.Add(self.check_box_enable,         0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.label_std_dev,            0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.text_ctrl_std_dev,        0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        sizer_1.Add(self.label_mean,               0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.text_ctrl_mean,           0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        sizer_1.Add(self.btn1,                     0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.AddStretchSpacer()
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        
        self.Bind(wx.EVT_CHECKBOX, self.onAverageCheckbox, self.check_box_enable_average)
        self.Bind(wx.EVT_CHECKBOX, self.onEnableCheckbox, self.check_box_enable)
                
        self.Bind(wx.EVT_TEXT_ENTER, self.onAverageEnter, self.text_ctrl_average)
        self.text_ctrl_average.Bind(wx.EVT_KILL_FOCUS, self.onAverageEnter)
        
        self.Bind(wx.EVT_BUTTON, self.OnButton_SaveData, self.btn1)
        self.saveSpectrumCallback = None
        
    def registerObserver(self,handler,observer):
        name = handler if isinstance(handler,types.StringType) else handler.__name__
        if name not in self.handlers:
            self.handlers[name] = []
        self.handlers[name].append(observer)
    
    def registerSaveSpectrumCallback(self, callback):
        self.saveSpectrumCallback = callback
        
    def onAverageEnter(self,evt):
        if not self.enableAverage:
            self.average = float(self.text_ctrl_average.GetValue())
        if evt: evt.Skip()
        
    def onAverageCheckbox(self,evt):
        self.enableAverage = self.check_box_enable_average.GetValue()
        if not self.enableAverage: 
            self.averageCount = 0
            self.text_ctrl_average.SetEditable(True)
            self.text_ctrl_average.SetValue("%d" % self.average)
        else:
            self.text_ctrl_average.SetEditable(False)
        if evt: evt.Skip()
        
    def onEnableCheckbox(self,evt):
        self.enable = self.check_box_enable.GetValue()
        if evt: evt.Skip()
    
    def OnButton_SaveData(self,evt):
        if self.saveSpectrumCallback is not None:
            self.saveSpectrumCallback()
        if evt: evt.Skip()
        
class GenericPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        self.staticBoxName = kwds["name"]
        del kwds["name"]
        wx.Panel.__init__(self, *args, **kwds)
        self.sizer_1_staticbox = wx.StaticBox(self, -1, self.staticBoxName)
        self.value = wx.TextCtrl(self, -1, " ", style=wx.TE_CENTRE)
        self.value.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
        self.eColor = wx.TextCtrl(self, -1, " ", size=(10,-1))
        self.eColor.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_1 = wx.StaticBoxSizer(self.sizer_1_staticbox, wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)       
        sizer_2.Add(self.value, 1, wx.RIGHT, 5)
        sizer_2.Add(self.eColor, 0, wx.RIGHT, 5)
        sizer_1.Add(sizer_2,0,wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
    def setColor(self,value=None):
        if not value:
            self.eColor.Show(False)
        else:
            self.eColor.SetBackgroundColour(value)
            self.eColor.Show(True)
        self.eColor.Refresh()
    def setValue(self,value):
        self.value.SetValue("%s" % value)

class DetectorViewer(wx.Frame):
    mainPos = 500.0
    mainSep = 3000.0

    def __init__(self,configFile):
        wx.Frame.__init__(self,parent=None,id=-1,title='Detector SD',size=(1000,700))
        panel = wx.Panel(self,id=-1)
        self.notebook = wx.Notebook(panel,-1,style=wx.NB_NOPAGETHEME)
        self.scopePanel = ScopePanel(self.notebook)
        self.notebook.AddPage(self.scopePanel,"Cavity Scan")
        self.controlPanel = ControlPanel(panel,-1)
        self.controlPanel.registerSaveSpectrumCallback(self.saveSpectrum)
        self.config = ConfigObj(configFile)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.notebook,proportion=1,flag=wx.EXPAND)
        sizer_1.Add(self.controlPanel,proportion=0,flag=wx.EXPAND)
        sizer_1.Add(sizer_2,proportion=1,flag=wx.EXPAND)
        panel.SetSizer(sizer_1)
        self.setupAnalyzer()
        self.nSample = 0
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.onTimer,self.timer)
        self.timer.Start(250)
        self.graphPanel = [self.scopePanel.graphPanel1,self.scopePanel.graphPanel2]

    def selectLaser(self,aLaserNum):
        self.aLaserNum = aLaserNum
        setActiveLaser(aLaserNum)
        
    def setLaserTemperature(self,laserTemp):
        self.laserTemperature = laserTemp
        setLaserTemperature(self.aLaserNum,laserTemp)

    def setLaserCurrent(self,laserCurrent):
        self.laserCurrent = laserCurrent
        
    def setupAnalyzer(self):
        self.npoints = 4095
        x = numpy.arange(self.npoints,dtype=float) 
        self.frequency = numpy.zeros(self.npoints,dtype=float)
        self.spectrum = numpy.zeros(self.npoints,dtype=float)
        stopAcquisition()
        setAnalyzerTuningMode(interface.ANALYZER_TUNING_CavityLengthTuningMode)
        setTunerOffset(0)
        setDirectTune(False) 
        self.upSlope = 8000
        self.downSlope = 8000
        self.pztPk2pk = 65000
        self.pztMax = 32768 + self.pztPk2pk//2
        self.pztMin = 32768 - self.pztPk2pk//2
        self.divisor = 2
        self.setupSweep()
        if self.config and ('configuration' in self.config):
            cd = self.config['configuration']
            if 'laser' in cd:
                self.selectLaser(int(cd['laser']))
            if 'laserCurrent' in cd:
                self.setLaserCurrent(int(cd['laserCurrent']))
            if 'laserTemperature' in cd:
                self.setLaserTemperature(float(cd['laserTemperature']))
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_NUM_SAMP",self.npoints)
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_DIVISOR",self.divisor-1)
        setFPGAbits("FPGA_RDMAN","RDMAN_OPTIONS",[("DITHER_ENABLE",False),("SCOPE_MODE",True),("SCOPE_SLOPE",True)])
        
    def setupSweep(self):
        rmax = self.pztMax
        rmin = self.pztMin
        setTuner(rampParams=(rmin,rmin,rmax,rmax),slopes=(self.upSlope,self.downSlope))
    
    def saveSpectrum(self):
        numpy.savetxt('DetectorSD.csv', numpy.c_[self.frequency,self.spectrum], delimiter=',')
    
    def onTimer(self,evt):
        extra = 9 # Extra bits in high-resolution tuner accumulator
        hTuner = 0.01 # Tuner interval in ms

        
        if self.nSample % 8 == 0:
            self.npoints = Driver.rdFPGA("FPGA_RDMAN","RDMAN_NUM_SAMP")
            self.divisor = Driver.rdFPGA("FPGA_RDMAN","RDMAN_DIVISOR")+1
            self.upSlope = Driver.rdFPGA("FPGA_TWGEN","TWGEN_SLOPE_UP")
            self.downSlope = Driver.rdFPGA("FPGA_TWGEN","TWGEN_SLOPE_DOWN")
            self.pztMax = Driver.rdDasReg("TUNER_SWEEP_RAMP_HIGH_REGISTER")
            self.pztMin = Driver.rdDasReg("TUNER_SWEEP_RAMP_LOW_REGISTER")

        self.nSample += 1
        
        N = self.npoints
        self.dt = self.divisor/(25.0e3) # In milliseconds
        tMax = N*self.dt
        
        if self.controlPanel.enable:
            d = Driver.rdOscilloscopeTrace()
            d = numpy.asarray(d[:N] & 16383, dtype=float)
            w = self.scopePanel.graph1Waveform
            w.Clear()        
            for x,y in enumerate(d):
                w.Add(x*self.dt,y)
                                    
            w = self.scopePanel.graph2Waveform
            w.Clear()
            f,SD,ENBW = AmplitudeSpectralDensity(numpy.arange(N)*self.dt*0.001, d)
            self.frequency = f
            if self.controlPanel.enableAverage:
                self.controlPanel.averageCount += 1
                if self.controlPanel.averageCount >= self.controlPanel.average:
                    self.controlPanel.averageCount = self.controlPanel.average
                self.spectrum = numpy.sqrt(((self.controlPanel.averageCount-1)*self.spectrum**2 + SD**2)/self.controlPanel.averageCount)
                self.controlPanel.text_ctrl_average.SetValue("%d / %d" % (self.controlPanel.averageCount,self.controlPanel.average))
            else:
                self.spectrum = SD
                
            for i,y in enumerate(self.spectrum):
                w.Add(f[i],y)
                
        numGraphs = 2
        for idx in range(numGraphs):
            if not self.graphPanel[idx].GetIsNewXAxis():
                pass
            else:
                actIndices = range(numGraphs)
                actIndices.remove(idx)
                currXAxis = tuple(self.graphPanel[idx].GetLastDraw()[1])

        #self.scopePanel.setYLim1(0,16500)
        self.scopePanel.setXLim(0,tMax)
        self.scopePanel.Update()

        self.controlPanel.text_ctrl_mean.SetValue('%.3g' % (ENBW/1000.))
        self.controlPanel.text_ctrl_std_dev.SetValue('%.2f' % numpy.std(d))
        
        if evt: evt.Skip()
    
_DEFAULT_CONFIG_NAME = "DetectorViewer.ini"

HELP_STRING = \
"""\
DetectorViewer.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file.  Default = "./DetectorViewer.ini"

"""

def PrintUsage():
    print HELP_STRING

def HandleCommandSwitches():
    import getopt
  
    shortOpts = 'c:h'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a
      
    if "/?" in args or "/h" in args:
        options["-h"] = ""
  
    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit(0)
 
    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + _DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
    
    return (configFile)


def main():
    app = wx.PySimpleApp()
    configFile = HandleCommandSwitches()
    frame = DetectorViewer(configFile)
    frame.Show()
    app.MainLoop()
    
if __name__ == "__main__":
    main()
