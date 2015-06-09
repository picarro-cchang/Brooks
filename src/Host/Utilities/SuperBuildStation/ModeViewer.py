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

APP_NAME = "ModeViewer"

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = os.path.abspath(sys.argv[0])

Driver = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,APP_NAME, IsDontCareConnection = False)
FreqConverter = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,APP_NAME, IsDontCareConnection = False)
SpectrumCollector = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,APP_NAME, IsDontCareConnection = False)

def xcorr(x,y):
    return numpy.real(numpy.fft.ifft(numpy.fft.fft(x)*numpy.conj(numpy.fft.fft(y))))

def circshift(x,s):
    return numpy.concatenate((x[-s:],x[:-s]))

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
        self.graphPanel1.SetGraphProperties(xlabel='PZT Position',timeAxes=(False,False),ylabel='Mode Amplitude',
            grid=True,frameColour=bg,backgroundColour=bg)
        self.graphPanel1.Update()
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.graphPanel1,proportion=1,flag=wx.GROW)
        self.SetSizer(vbox)
        vbox.Fit(self)
        # Create the sequences for the graphs
        self.maxWaveformPoints = 4096
        self.graph1Waveform = Series(self.maxWaveformPoints)
        self.graphPanel1.RemoveAllSeries()
        self.graphPanel1.AddSeriesAsLine(self.graph1Waveform,colour="red",width=1)
    def setText(self,x,y,strings):
        self.graphPanel1.RemoveAllText()
        self.graphPanel1.Text(x,y,strings,color="black",just=(0.5,1.2))
    def Update(self):
        self.graphPanel1.Update()
    def setXLim(self,xMin,xMax):
        self.graphPanel1.SetGraphProperties(XSpec=(xMin,xMax))
    def setYLim(self,yMin,yMax):
        self.graphPanel1.SetGraphProperties(YSpec=(yMin,yMax))

class ControlPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)

        self.handlers = {}
        self.serialNumber = ""
        self.average = 64

        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.label_serialNumber = wx.StaticText(self, -1, "Cavity Serial No")
        self.text_ctrl_serialNumber = wx.TextCtrl(self, -1, "%s" % self.serialNumber, style=wx.TE_PROCESS_ENTER)
        self.label_laser = wx.StaticText(self, -1, "Laser")
        self.combo_box_laser = wx.ComboBox(self, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.label_average = wx.StaticText(self, -1, "Average")
        self.text_ctrl_average = wx.TextCtrl(self, -1, "%d" % self.average, style=wx.TE_PROCESS_ENTER)

        self.button_clear = wx.Button(self, wx.ID_CLEAR, "")
        sizer_1.Add(self.label_serialNumber, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.text_ctrl_serialNumber, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        sizer_1.Add(self.label_laser, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.combo_box_laser, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
        sizer_1.Add(self.label_average, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.text_ctrl_average, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        sizer_1.AddStretchSpacer()
        sizer_1.Add(self.button_clear, 0, wx.ALL|wx.EXPAND, 10)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)

        self.Bind(wx.EVT_TEXT_ENTER, self.onSerialNumberEnter, self.text_ctrl_serialNumber)
        self.text_ctrl_serialNumber.Bind(wx.EVT_KILL_FOCUS, self.onSerialNumberEnter)

        self.Bind(wx.EVT_TEXT_ENTER, self.onAverageEnter, self.text_ctrl_average)
        self.text_ctrl_average.Bind(wx.EVT_KILL_FOCUS, self.onAverageEnter)

        self.Bind(wx.EVT_BUTTON, self.onClear, self.button_clear)

    def registerObserver(self,handler,observer):
        name = handler if isinstance(handler,types.StringType) else handler.__name__
        if name not in self.handlers:
            self.handlers[name] = []
        self.handlers[name].append(observer)

    def onSerialNumberEnter(self,evt):
        self.serialNumber = int(self.text_ctrl_serialNumber.GetValue())
        if evt: evt.Skip()

    def onAverageEnter(self,evt):
        self.average = float(self.text_ctrl_average.GetValue())
        if evt: evt.Skip()

    def onClear(self,evt):
        funcName = inspect.stack()[0][3]
        if funcName in self.handlers:
            for obs in self.handlers[funcName]: obs()
        if evt: evt.Skip()

class ModeSelectPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        self.modeName = kwds["name"]
        del kwds["name"]
        wx.Panel.__init__(self, *args, **kwds)
        self.sizer_1_staticbox = wx.StaticBox(self, -1, self.modeName)
        self.cbPlotData = wx.CheckBox(self, -1, "Plot Data")
        self.eModeAmplitude = wx.TextCtrl(self, -1, " ", style=wx.TE_CENTRE)
        self.eColor = wx.TextCtrl(self, -1, " ", size=(10,-1))
        self.cbPlotData.SetValue(1)
        self.eModeAmplitude.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
        self.eColor.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_1 = wx.StaticBoxSizer(self.sizer_1_staticbox, wx.VERTICAL)
        sizer_1.Add(self.cbPlotData, 0, wx.TOP|wx.BOTTOM, 5)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2.Add(self.eModeAmplitude, 1, wx.RIGHT, 5)
        sizer_2.Add(self.eColor, 0, wx.RIGHT, 5)
        sizer_1.Add(sizer_2,0,wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
    def setColor(self,value):
        self.eColor.SetBackgroundColour(value)
        self.eColor.Refresh()
    def setPercentage(self,value):
        self.eModeAmplitude.SetValue("%.2f%%" % value)
    def setPlotDataFlag(self,flag):
        return self.cbPlotData.SetValue(flag)
    def getPlotDataFlag(self):
        return self.cbPlotData.GetValue()

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

class ModePanel(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.seriesColor = ["yellow","red","green","black","blue"]
        modeNames = ["(1,1),(0,5)","Horizontal","(0,3),(2,1)","Focus","Vertical"]
        self.nModes = 5
        self.nGraphTypes = 1
        self.nowVisible = [False, True, False, True, True]
        self.lastVisible = (self.nModes*self.nGraphTypes)*[True] # Make a copy
        # Define the graph panel
        bg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        self.graphPanel1 = GraphPanel(parent=self,id=-1)
        self.graphPanel1.SetGraphProperties(ylabel='Mode Amplitudes (%)',grid=True,
                                           backgroundColour=bg,frameColour=bg)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.graphPanel1,proportion=1,flag=wx.GROW)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.modeSelectPanels = []
        for m in range(self.nModes):
            self.modeSelectPanels.append(ModeSelectPanel(parent=self,id=-1,name=modeNames[m]))
            hbox.Add(self.modeSelectPanels[m],proportion=1)
        self.fsrPanel = GenericPanel(parent=self,id=-1,name="Cavity FSR")
        hbox.Add(self.fsrPanel,proportion=1,flag=wx.ALIGN_BOTTOM)
        vbox.Add(hbox,flag=wx.GROW)
        self.SetSizer(vbox)
        vbox.Fit(self)
        # Create the series for the graphs
        nPoints = 1000
        self.modeSeries = []
        self.graphPanel1.RemoveAllSeries()
        for i in range(self.nModes):
            self.modeSeries.append(Series(nPoints))
            vis = self.nowVisible[self.modeAndTypeToIndex(i)]
            self.modeSelectPanels[i].setPlotDataFlag(vis)
            if vis:
                self.graphPanel1.AddSeriesAsPoints(self.modeSeries[i],colour=self.seriesColor[i],width=1,size=1)
            self.modeSelectPanels[i].setColor(self.seriesColor[i])
        self.setMaxPoints(250)
        self.graphPanel1.Update()
    def modeAndTypeToIndex(self,m):
        return m
    def addData(self,t,modeAmpl):
        for i,amp in enumerate(modeAmpl):
            self.modeSeries[i].Add(t,amp)
    def setVisible(self,modeNum,graphType,visible):
        self.nowVisible[self.modeAndTypeToIndex(modeNum)] = visible
    def setPercentage(self,modeNum,value):
        self.modeSelectPanels[modeNum].setPercentage(value)
    def setFsr(self,value):
        self.fsrPanel.setValue("%.0f" % value)
    def clearAllSequences(self):
        for i in range(self.nModes):
            self.modeSeries[i].Clear()
    def setMaxPoints(self,maxPoints):
        for i in range(self.nModes):
            self.modeSeries[i].setMaxPoints(maxPoints)
    def Update(self):
        if self.lastVisible != self.nowVisible:
            self.graphPanel1.RemoveAllSeries()
            for i in range(self.nModes):
                if self.nowVisible[self.modeAndTypeToIndex(i)]:
                    self.graphPanel1.AddSeriesAsPoints(self.modeSeries[i],colour=self.seriesColor[i],width=1,size=1)
            self.lastVisible = self.nowVisible[:]
        self.graphPanel1.Update()

class ModeViewer(wx.Frame):
    mainPos = 500.0
    mainSep = 3000.0

    def __init__(self,configFile):
        wx.Frame.__init__(self,parent=None,id=-1,title='Mode Viewer',size=(1000,700))
        panel = wx.Panel(self,id=-1)
        self.notebook = wx.Notebook(panel,-1,style=wx.NB_NOPAGETHEME)
        self.scopePanel = ScopePanel(self.notebook)
        self.notebook.AddPage(self.scopePanel,"Cavity Scan")
        self.modePanel = ModePanel(self.notebook)
        self.notebook.AddPage(self.modePanel,"Mode Amplitudes")
        self.controlPanel = ControlPanel(panel,-1)
        self.config = ConfigObj(configFile)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.notebook,proportion=1,flag=wx.EXPAND)
        sizer_1.Add(self.controlPanel,proportion=0,flag=wx.EXPAND)
        sizer_1.Add(sizer_2,proportion=1,flag=wx.EXPAND)
        panel.SetSizer(sizer_1)
        self.setupAnalyzer()
        self.flash = True
        self.controlPanel.registerObserver("onClear",self.onClear)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.onTimer,self.timer)
        self.timer.Start(250)

    def selectLaser(self,aLaserNum):
        self.aLaserNum = aLaserNum
        setActiveLaser(aLaserNum)

    def setLaserTemperature(self,laserTemp):
        self.laserTemperature = laserTemp
        setLaserTemperature(self.aLaserNum,laserTemp)

    def setLaserCurrent(self,laserCurrent):
        self.laserCurrent = laserCurrent

    def setupAnalyzer(self):
        self.npoints = 4096
        x = numpy.arange(self.npoints,dtype=float)
        self.ref = numpy.exp(-0.5*((x-self.mainPos)/100)**2)
        self.data = numpy.zeros(self.npoints,dtype=float)
        self.winsize = (self.npoints)/4
        stopAcquisition()
        setAnalyzerTuningMode(interface.ANALYZER_TUNING_CavityLengthTuningMode)
        setTunerOffset(0)
        setDirectTune(False)
        self.slope = 4000
        self.pztPk2pk = 65000
        self.divisor = 512
        self.setupSweep()
        cd = self.config['configuration']
        self.selectLaser(int(cd['laser']))
        self.setLaserCurrent(int(cd['laserCurrent']))
        self.setLaserTemperature(float(cd['laserTemperature']))
        self.modeDict = {}
        for mode in self.config['ranges']:
            self.modeDict[mode] = {'range':[int(x) for x in self.config['ranges'][mode]]}
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_NUM_SAMP",self.npoints-1)
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_DIVISOR",self.divisor-1)
        setFPGAbits("FPGA_RDMAN","RDMAN_OPTIONS",[("DITHER_ENABLE",False),("SCOPE_MODE",True),("SCOPE_SLOPE",True)])
        self.refWt = 1
        self.fsr = 0
        self.sampleNo = 0
        self.lost = 10
    def setupSweep(self):
        slope = int(self.slope)
        rmax = int(32768.0+0.5*self.pztPk2pk)
        rmin = int(32768.0-0.5*self.pztPk2pk)
        setTuner(rampParams=(rmin,rmin,rmax,rmax),slopes=(slope,slope))

    def onClear(self,evt=None):
        self.modePanel.clearAllSequences()
        self.refWt = 1
        if evt: evt.Skip()

    def onTimer(self,evt):
        sel = self.notebook.GetSelection()
        N = self.npoints
        winsize = self.winsize
        d = Driver.rdOscilloscopeTrace()
        d = d[:N] & 16383
        # Compute the largest cross-correlation within a small window of zero
        ccorr = numpy.fft.fftshift(xcorr(numpy.concatenate((self.ref,self.ref[0]*numpy.ones(N))),
                               numpy.concatenate((d,d[0]*numpy.ones(N)))))
        # The following finds the shift that must be applied to the second signal
        #  to best align it with the first
        shift = numpy.argmax(ccorr[N-winsize:N+winsize])-winsize

        skip = N/2
        # Find number of samples to the next copy of the cavity spectrum
        pkpos = numpy.argmax(numpy.asarray(ccorr[N+shift-skip::-1])) + skip
        fsr = 0.004*self.slope*self.divisor*pkpos/512.0

        scale = (pkpos/self.mainSep)**0.05
        self.slope *= scale
        self.pztPk2pk *= scale
        self.setupSweep()
        # Adjust the temperature of the laser to center one peak at self.mainPos
        dTemp = abs(shift)*0.001/300
        if dTemp > 0.001: dTemp = 0.001
        if shift < 0: self.setLaserTemperature(self.laserTemperature+dTemp)
        else: self.setLaserTemperature(self.laserTemperature-dTemp)

        # Update the averaged data with the shifted waveform, and update the FSR
        self.data = (self.refWt*self.data + circshift(d,shift))/(self.refWt + 1)
        #self.data = d # circshift(d,shift)
        self.fsr  = (self.refWt*self.fsr  + fsr)/(self.refWt + 1)
        self.refWt = min(self.controlPanel.average,self.refWt+1)
        if abs(shift)>100 or abs(pkpos-self.mainSep)>25:
            self.lost += 1
            if self.lost>10: self.refWt = 1
            #print shift, pkpos, "<-----"
        else:
            self.lost = 0
            #print shift, pkpos
        for mode in self.modeDict:
            md = self.modeDict[mode]
            xmin,xmax = md['range']
            md['sum'] = sum(self.data[xmin:xmax])
            md['min'] = min(self.data[xmin:xmax])
            md['count'] = xmax - xmin
        ymin = min([self.modeDict[mode]['min'] for mode in self.modeDict])
        for mode in self.modeDict:
            md = self.modeDict[mode]
            md['area'] = md['sum'] - md['count']*ymin
        pkAreas = numpy.asarray([self.modeDict[m]['area'] for m in ['Main1','Saddle','Horizontal','Polarization','Focus','Vertical','Main2']])
        modeAmpl = 2.0*pkAreas[1:-1]/(pkAreas[0]+pkAreas[-1])

        self.modePanel.setFsr(self.fsr)
        if self.refWt > 2:
            self.modePanel.addData(self.sampleNo,100.0*modeAmpl)
            for m,a in enumerate(modeAmpl):
                self.modePanel.setPercentage(m,100.0*a)
            self.sampleNo += 1
            self.modePanel.fsrPanel.setColor("green")
        else:
            if self.flash:
                self.modePanel.fsrPanel.setColor("red")
            else:
                self.modePanel.fsrPanel.setColor(wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
            self.flash = not self.flash
        if sel == 0:
            w = self.scopePanel.graph1Waveform
            w.Clear()
            for x,y in enumerate(self.data):
                w.Add(x,y)
            self.scopePanel.setYLim(0,16500)
            self.scopePanel.setXLim(0,N)
            self.scopePanel.Update()
        elif sel == 1:
            for m in range(len(modeAmpl)):
                vis = self.modePanel.modeSelectPanels[m].getPlotDataFlag()
                self.modePanel.setVisible(m,0,vis)
            self.modePanel.Update()
        if evt: evt.Skip()

_DEFAULT_CONFIG_NAME = "ModeViewer.ini"

HELP_STRING = \
"""\
ModeViewer.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file.  Default = "./ModeViewer.ini"

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
    frame = ModeViewer(configFile)
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()