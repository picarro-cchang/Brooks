import wx
import sys
from Host.Common.GraphPanel import GraphPanel, Sequence, Series
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

APP_NAME = "GraphPanelExample"

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = os.path.abspath(sys.argv[0])

class ScopePanel(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        # Define the graph panel
        bg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        self.graphPanel1 = GraphPanel(parent=self,id=-1)
        self.graphPanel1.SetGraphProperties(xlabel='Time (ms)',timeAxes=(False,False),ylabel='Detector output',
            grid=True,frameColour=bg,backgroundColour=bg)
        self.graphPanel1.Update()
        self.graphPanel2 = GraphPanel(parent=self,id=-1)
        self.graphPanel2.SetGraphProperties(xlabel='Time (ms)',timeAxes=(False,False),ylabel='PZT Voltage',
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
        self.graphPanel1.AddSeriesAsLine(self.graph1Waveform,colour="red",width=1)
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
        self.graphPanel2.SetGraphProperties(XSpec=(xMin,xMax))
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
        self.label_std_dev = wx.StaticText(self, -1, "Std Dev")
        self.text_ctrl_std_dev = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        
        sizer_1.Add(self.check_box_enable_average, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.label_average, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.text_ctrl_average, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        sizer_1.Add(self.check_box_enable, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.label_std_dev, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer_1.Add(self.text_ctrl_std_dev, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        sizer_1.AddStretchSpacer()
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        
        self.Bind(wx.EVT_CHECKBOX, self.onAverageCheckbox, self.check_box_enable_average)
        self.Bind(wx.EVT_CHECKBOX, self.onEnableCheckbox, self.check_box_enable)
                
        self.Bind(wx.EVT_TEXT_ENTER, self.onAverageEnter, self.text_ctrl_average)
        self.text_ctrl_average.Bind(wx.EVT_KILL_FOCUS, self.onAverageEnter)

    def registerObserver(self,handler,observer):
        name = handler if isinstance(handler,types.StringType) else handler.__name__
        if name not in self.handlers:
            self.handlers[name] = []
        self.handlers[name].append(observer)
        
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
    def __init__(self,configFile):
        wx.Frame.__init__(self,parent=None,id=-1,title='Detector Viewer',size=(1000,700))
        panel = wx.Panel(self,id=-1)
        self.notebook = wx.Notebook(panel,-1,style=wx.NB_NOPAGETHEME)
        self.scopePanel = ScopePanel(self.notebook)
        self.notebook.AddPage(self.scopePanel,"Cavity Scan")
        self.controlPanel = ControlPanel(panel,-1)
        self.config = ConfigObj(configFile)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.notebook,proportion=1,flag=wx.EXPAND)
        sizer_1.Add(self.controlPanel,proportion=0,flag=wx.EXPAND)
        sizer_1.Add(sizer_2,proportion=1,flag=wx.EXPAND)
        panel.SetSizer(sizer_1)
        self.nSample = 0
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.onTimer,self.timer)
        self.timer.Start(250)
        self.graphPanel = [self.scopePanel.graphPanel1,self.scopePanel.graphPanel2]
        
    def onTimer(self,evt):
        numGraphs = 2
        for idx in range(numGraphs):
            if not self.graphPanel[idx].GetIsNewXAxis():
                pass
            else:
                actIndices = range(numGraphs)
                actIndices.remove(idx)
                currXAxis = tuple(self.graphPanel[idx].GetLastDraw()[1])
                if not self.graphPanel[idx].GetUnzoomed():
                    #print "Graph %d zooming others in time-locked mode" % idx
                    for i in actIndices:
                        self.graphPanel[i].SetUnzoomed(False)
                        self.graphPanel[i].SetForcedXAxis(currXAxis)
                        self.graphPanel[i].Update(forcedRedraw=True)
                        self.graphPanel[i].ClearForcedXAxis()
                    self.allTimeLocked = True  
                    break
                elif self.allTimeLocked:
                    #print "Graph %d unzooming others in time-locked mode" % idx
                    # Unzoom other plots
                    for i in actIndices:
                        self.graphPanel[i].SetUnzoomed(True)
                        self.graphPanel[i].Update(forcedRedraw=True)
                    self.allTimeLocked = False
                    break

        self.scopePanel.setYLim1(0,16500)    
        self.scopePanel.setXLim(0,1000)
        self.scopePanel.Update()
        
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
