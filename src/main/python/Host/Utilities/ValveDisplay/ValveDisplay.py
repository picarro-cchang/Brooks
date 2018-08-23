import wx
import configobj
import getopt
import os
import Queue
import sys
from configobj import ConfigObj
from Host.Utilities.ValveDisplay.ValveDisplayFrameGui import ValveDisplayFrameGui, ValveWidgetGui
from Host.Common import Listener
from Host.Common.SharedTypes import BROADCAST_PORT_SENSORSTREAM
from Host.autogen import interface

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = os.path.abspath(sys.argv[0])
AppPath = os.path.abspath(AppPath)

HELP_STRING = \
"""\
ValveDisplay [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different configuration file.  Default = "./ValveDisplay.ini"
"""
class ValveWidget(ValveWidgetGui):
    def setLabel(self,label):
        self.lblStatus.SetLabel(label)
    def setStatus(self,status):
        self.cbStatus.Set3StateValue(status)
class ValveDisplayFrame(ValveDisplayFrameGui):
    def __init__(self,*a,**k):
        ValveDisplayFrameGui.__init__(self,*a,**k)
        self.configFile = None
        self.streamQueue = Queue.Queue(0)
        self.valveData = []
        self.timer = wx.Timer(self)

    def run(self,configFile):
        self.configFile = configFile
        self.config = ConfigObj(configFile)
        # Read the valve numbers and descriptions from the configuration file
        #  The options in the Valves section have the form:
        # row<n>=valveNum,descr
        if "Valves" in self.config:
            valveDict = self.config["Valves"]
            valveData = {}
            for opt in valveDict:
                if opt.startswith("row"):
                    index = int(opt[3:])
                    valveNum,descr = valveDict[opt]
                    valveData[index] = [int(valveNum),descr]
        # We sort in order of row indices "n" and place the [valveNum,descr]
        #  pairs in the list self.valveData
        for k in sorted(valveData.keys()):
            self.valveData.append(valveData[k])
        # Figure out the size of the panel, using the width and rowheight options
        #  from the confuration file
        width = 200
        rowHeight = 40
        if "Panel" in self.config:
            panelDict = self.config["Panel"]
            width = int(panelDict.get("width",width))
            rowHeight = int(panelDict.get("rowheight",rowHeight))
        self.SetSize((width,rowHeight*len(self.valveData)))
        s = self.GetSizer()
        # Create the widgets in the display frame dynamically from the data
        #  in self.valveData. Append the widget to give [valveNum,descr,widget]
        #  in the self.valveData list
        for valveData in self.valveData:
            valveNum,descr = valveData
            widget = ValveWidget(self)
            widget.setLabel(descr)
            widget.setStatus(wx.CHK_UNDETERMINED)
            valveData.append(widget)
            s.Add(widget,1,wx.EXPAND,0)
            self.Layout()
        # Open the listener to the sensor stream
        self.streamListener = Listener.Listener(self.streamQueue,
                                                BROADCAST_PORT_SENSORSTREAM,
                                                interface.SensorEntryType,
                                                None,
                                                retry = True,
                                                name = "Controller sensor stream listener")
        self.Bind(wx.EVT_TIMER,self.onTimer)
        self.timer.Start(200)

    def onTimer(self,e):
        while not self.streamQueue.empty():
            data = self.streamQueue.get()
            if data.streamNum == interface.STREAM_ValveMask:
                valveMask = int(data.value)
                for valveData in self.valveData:
                    valveNum,descr,widget = valveData
                    open = valveMask & (1<<(valveNum - 1))
                    if open:
                        widget.setStatus(wx.CHK_CHECKED)
                    else:
                        widget.setStatus(wx.CHK_UNCHECKED)

def printUsage():
    print HELP_STRING
def handleCommandSwitches():
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
        printUsage()
        sys.exit(0)

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + "ValveDisplay.ini"

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile
class App(wx.App):
    def OnInit(self):
        configFile = handleCommandSwitches()
        self.valveFrame = ValveDisplayFrame(None, -1, "")
        self.valveFrame.run(configFile)
        self.valveFrame.Show()
        self.SetTopWindow(self.valveFrame)
        return True

if __name__ == "__main__":
    app = App(False)
    app.MainLoop()