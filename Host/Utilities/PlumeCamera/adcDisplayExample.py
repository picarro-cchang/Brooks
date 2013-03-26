import wx

import cPickle
import inspect
try:
    import json
except:
    import simplejson as json
import threading
import numpy
import os
import Queue
import sys
import time
import types
import zmq

from Host.Common.GraphPanel import GraphPanel, Sequence, Series
from Host.Common.configobj import ConfigObj

ADC_CMD_PORT = 5201
ADC_BROADCAST_PORT = 5202

APP_NAME = "adcDisplayExample"

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = os.path.abspath(sys.argv[0])

class ScopePanel(wx.Panel):
    def __init__(self, *args, **kwds):
        nGraphs = kwds.get("nGraphs",1)
        if "nGraphs" in kwds: del kwds["nGraphs"]
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        # Define the graph panel
        bg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        self.graphPanels = []
        self.graphWaveforms = []
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.maxWaveformPoints = 4096
        for i in range(nGraphs):
            gp = GraphPanel(parent=self,id=-1)
            gp.SetGraphProperties(xlabel='Time (ms)',timeAxes=(False,False),ylabel='Channel %d' % i,
                                  grid=True,frameColour=bg,backgroundColour=bg)
            gp.Update()
            vbox.Add(gp,proportion=1,flag=wx.GROW)
            self.graphPanels.append(gp)
            gw = Series(self.maxWaveformPoints)
            self.graphWaveforms.append(gw)
            gp.AddSeriesAsLine(gw,width=2,colour="blue")
        self.SetSizer(vbox)
        vbox.Fit(self)
    def Update(self):
        for gp in self.graphPanels:
            gp.Update()
    def setXLim(self,xMin,xMax,whichGraphs=None):
        for i, gp in enumerate(self.graphPanels):
            if whichGraphs is None or i in whichGraphs:
                gp.SetGraphProperties(XSpec=(xMin,xMax))
    def setYLim(self,yMin,yMax,whichGraphs):
        for i, gp in enumerate(self.graphPanels):
            if whichGraphs is None or i in whichGraphs:
                gp.SetGraphProperties(YSpec=(yMin,yMax))

class ControlPanel(wx.Panel):        
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        self.root = kwds.get("root", None)
        if "root" in kwds: del kwds["root"]

        wx.Panel.__init__(self, *args, **kwds)
        
        self.handlers = {}
        
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        
        self.button_start = wx.Button(self,-1,"Start")
        self.button_stop = wx.Button(self,-1,"Stop")
        self.button_quit = wx.Button(self,-1,"Quit")
        
        sizer_1.Add(self.button_start, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        sizer_1.Add(self.button_stop, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        sizer_1.Add(self.button_quit, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        
        self.Bind(wx.EVT_BUTTON, self.onStart, self.button_start)
        self.Bind(wx.EVT_BUTTON, self.onStop,  self.button_stop)
        self.Bind(wx.EVT_BUTTON, self.onQuit,  self.button_quit)

    def onStart(self,evt):
        self.root.onStart(evt)

    def onStop(self,evt):
        self.root.onStop(evt)

    def onQuit(self,evt):
        self.root.onQuit(evt)

class MeasCompInterface(object):
    """Class for accessing Measurement Computing hardware"""
    # Note that we have two zmq contexts, since the subscription to the
    #  ADC data takes place in a thread and the data is placed in a Queue
    #  for access via the main (GUI) thread. The access to the command
    #  port occuurs wholly within the main thread.
    def __init__(self,root=None):
        self.zmqContext = zmq.Context()
        self.cmdSocket = self.zmqContext.socket(zmq.REQ)
        self.cmdSocket.connect("tcp://127.0.0.1:%d" % ADC_CMD_PORT)
        self.dataQueue = Queue.Queue()
        self.listenThread = None
        self.stopThread = False
        self.maxSamples = 10000
        self.root = root

    def threadRun(self):
        context = zmq.Context()
        listenSocket = context.socket(zmq.SUB)
        listenSocket.connect("tcp://127.0.0.1:%d" % ADC_BROADCAST_PORT)
        listenSocket.setsockopt(zmq.SUBSCRIBE, "")
        poller = zmq.Poller()
        poller.register(listenSocket,zmq.POLLIN)
        while not self.stopThread:
            # Timeout is present so that we can stop the thread
            socks = dict(poller.poll(1000))
            if socks.get(listenSocket) == zmq.POLLIN:
                data = cPickle.loads(listenSocket.recv())
                for d in data:
                    if self.dataQueue.qsize() >= self.maxSamples:
                        self.dataQueue.get()
                    self.dataQueue.put(d)
        listenSocket.close()
        context.term()

    def startListening(self):
        self.listenThread = threading.Thread(target=self.threadRun)
        self.listenThread.setDaemon(True)
        self.listenThread.start()

    def sendCommand(self,cmdDict):
        self.cmdSocket.send(json.dumps(cmdDict))
        return json.loads(self.cmdSocket.recv())

    def getQueueLength(self):
        return self.dataQueue.qsize()

    def close(self):
        ret = self.sendCommand({"func": "close", "args": []})
        self.stopThread = True
        self.listenThread.join()
        self.cmdSocket.close()
        self.zmqContext.term()
        return ret

class Viewer(wx.Frame):
    def __init__(self,configFile):
        wx.Frame.__init__(self,parent=None,id=-1,title='ADC Viewer',size=(1000,700))
        panel = wx.Panel(self,id=-1)
        self.notebook = wx.Notebook(panel,-1,style=wx.NB_NOPAGETHEME)
        self.scopePanel = ScopePanel(self.notebook,nGraphs=4)
        self.notebook.AddPage(self.scopePanel,"ADC Waveforms")
        self.controlPanel = ControlPanel(panel,-1,root=self)
        self.mci = MeasCompInterface(root=self)
        self.config = ConfigObj(configFile)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.notebook,proportion=1,flag=wx.EXPAND)
        sizer_1.Add(self.controlPanel,proportion=0,flag=wx.EXPAND)
        sizer_1.Add(sizer_2,proportion=1,flag=wx.EXPAND)
        panel.SetSizer(sizer_1)
        self.mci.startListening()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.onTimer,self.timer)
        self.timer.Start(200)
        self.sample = 0

    def onStart(self,evt):
        print self.mci.sendCommand({"func": "start", "args": []})

    def onStop(self,evt):
        print self.mci.sendCommand({"func": "stop", "args": []})

    def onQuit(self,evt):
        print self.mci.close()
        self.Close()

    def onTimer(self,evt):
        while not self.mci.dataQueue.empty():
            data = self.mci.dataQueue.get()
            for i,d in enumerate(data):
                self.scopePanel.graphWaveforms[i].Add(self.sample,d)
            self.sample += 1
        for gp in self.scopePanel.graphPanels:
            gp.Update()

_DEFAULT_CONFIG_NAME = "adcDisplayExample.ini"

HELP_STRING = """
adcDisplayExample.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file.  Default = "./adcDisplayExample.ini"

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
    frame = Viewer(configFile)
    frame.Show()
    app.MainLoop()
    
if __name__ == "__main__":
    main()
