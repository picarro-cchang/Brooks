"""
File Name: AircraftValveSwitcher.py
Purpose: Customized utility to enable fast valve switching using current valve sequencer

File History:
    2012-04-04 alex  Created
    
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""

APP_NAME = "AircraftValveSwitcher"
APP_DESCRIPTION = "AircraftValveSwitcher"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "AircraftValveSwitcher.ini"

import wx
import sys
import os
import time
import threading
from Host.Common import CmdFIFO
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.TTLIntrf import TTLIntrf
from Host.Common.SingleInstance import SingleInstance
from Host.Common.SharedTypes import RPC_PORT_VALVE_SEQUENCER, RPC_PORT_SUPERVISOR, RPC_PORT_INSTR_MANAGER
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

class AircraftValveSwitcherFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.CAPTION|wx.MINIMIZE_BOX|wx.CLOSE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.SetTitle("Aircraft Valve Switcher")
        copyrightText = "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0]
        self.labelFooter = wx.StaticText(self.panel2, -1, copyrightText, style=wx.ALIGN_CENTER)
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.panel2.SetBackgroundColour("#85B24A")

        self.labelCurStatus = wx.StaticText(self.panel1, -1, "Current Status", size = (150,-1))
        self.valCurStatus = wx.TextCtrl(self.panel1, -1, "", size = (150, -1), style = wx.TE_READONLY)
        self.valCurStatus.SetBackgroundColour("#FFFF99")
        
        self.labelCurSeq = wx.StaticText(self.panel1, -1, "Current Valve Sequence", size = (150,-1))
        self.valCurSeq = wx.TextCtrl(self.panel1, -1, "", size = (150, -1), style = wx.TE_READONLY)
        self.valCurSeq.SetBackgroundColour("#FFFF99")

        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)

        grid_sizer_1 = wx.FlexGridSizer(0, 2)
        grid_sizer_1.Add(self.labelCurStatus, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.valCurStatus, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.labelCurSeq, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.valCurSeq, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_1.Add(grid_sizer_1, 0)
        sizer_1.Add((-1,10))
        self.panel1.SetSizer(sizer_1)

        sizer_2.Add(self.labelFooter, 0, wx.EXPAND|wx.BOTTOM, 5)
        self.panel2.SetSizer(sizer_2)

        sizer_3.Add(self.panel1, 0, wx.EXPAND, 0)
        sizer_3.Add(self.panel2, 0, wx.EXPAND, 0)
        
        self.SetSizer(sizer_3)
        sizer_3.Fit(self)
        self.Layout()
        
class AircraftValveSwitcher(AircraftValveSwitcherFrame):
    def __init__(self, configFile, *args, **kwds):
        self.valveSequencerRPC = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_VALVE_SEQUENCER, APP_NAME)
        self.supervisorRPC = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME)
        self.instMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER, APP_NAME)
        self.configFile = configFile
        self.co = CustomConfigObj(configFile)
        timerIntervalS = self.co.getfloat("MAIN", "timerIntervalS", 2.0)
        self.landingTimeout = self.co.getfloat("MAIN", "landingTimeout", 660.0)
        self.shutdownDelayCount = self.co.getint("MAIN", "shutdownDelayCount", 10)
        self.shutdownOption = self.co.getint("MAIN", "shutdownOption", 0)
        self.dioChannel = self.co.getint("DIO", "dioChannel", 1)
        dioFlightSig = self.co.getint("DIO", "dioFlightSig", 1)
        assert dioFlightSig in [0, 1], "DIO Flight signal must be either 0 or 1"
        self.powerOnSeq = self.co.get("MAIN", "powerOnSeq", "")
        self.flightSeq = self.co.get("MAIN", "flightSeq", "")
        self.landingSeq = self.co.get("MAIN", "landingSeq", "")
        assert os.path.isfile(self.powerOnSeq), "'%s' is not a valid file" % self.powerOnSeq
        assert os.path.isfile(self.flightSeq), "'%s' is not a valid file" % self.flightSeq
        assert os.path.isfile(self.landingSeq), "'%s' is not a valid file" % self.landingSeq
        self.dio =  TTLIntrf(dioFlightSig, 1-dioFlightSig)
        self.dio.open()
        self.state = "Init"
        self.seq = ""
        self.shutdownTimestamp = None
        self.shutdownCount = 0
        self.valveSequencerRPC.stopValveSeq()
        AircraftValveSwitcherFrame.__init__(self, *args, **kwds)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.timer.Start(timerIntervalS*1000)

    
    def readDIO(self):
        return self.dio.getStatus(self.dioChannel)
        
    def shutdown(self):
        if self.shutdownOption == 0:
            self.instMgrRpc.INSTMGR_ShutdownRpc(2)
        else:
            self.supervisorRPC.TerminateApplications(powerDown=False,stopProtected=True)
        
    def onTimer(self, event):
            dio = self.readDIO()
            if self.state == "Init":
                if not dio:
                    self.valveSequencerRPC.loadSeqFile(self.powerOnSeq)
                    self.seq = os.path.basename(self.powerOnSeq)
                    self.state = "Power On"
                    self.valveSequencerRPC.startValveSeq()
                elif dio:
                    self.valveSequencerRPC.loadSeqFile(self.flightSeq)
                    self.seq = os.path.basename(self.flightSeq)
                    self.state = "Flight"
                    self.valveSequencerRPC.startValveSeq()
            elif self.state == "Power On":
                if dio:
                    self.valveSequencerRPC.loadSeqFile(self.flightSeq)
                    self.seq = os.path.basename(self.flightSeq)
                    self.state = "Flight"
            elif self.state == "Flight":
                if not dio:
                    self.valveSequencerRPC.loadSeqFile(self.landingSeq)
                    self.seq = os.path.basename(self.landingSeq)
                    self.state = "Landing"
            elif self.state == "Landing":
                if (int(self.valveSequencerRPC.getValveSeqStatus().split(";")[1]) & 0x1F) == 0 and not self.shutdownTimestamp:
                    self.shutdownTimestamp = time.time()
                if self.shutdownTimestamp:
                    if time.time() - self.shutdownTimestamp > self.landingTimeout:
                        self.state = "Shutting Down"
            elif self.state == "Shutting Down":
                if self.shutdownCount > self.shutdownDelayCount:
                    self.dio.close()
                    self.shutdown()
                    sys.exit(0)
                else:
                   self.shutdownCount += 1 
            #print "Current state = %s" % (self.state,)
            self.valCurStatus.SetValue(self.state)
            if self.state == "Shutting Down":
                self.valCurStatus.SetForegroundColour("red")
            self.valCurSeq.SetValue(self.seq)
            
HELP_STRING = \
"""
AircraftValveSwitcher.py [-h] [-c <FILENAME>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.
"""

def PrintUsage():
    print HELP_STRING
    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:", ["help"])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
        
    return configFile
    
if __name__ == "__main__":
    #Get and handle the command line options...
    configFile = HandleCommandSwitches()
    Log("%s started." % APP_NAME, Level = 0)
    # Check if it's already running
    app = SingleInstance("AircraftValveSwitcher")
    if app.alreadyrunning():
        try:
            handle = win32gui.FindWindowEx(0, 0, None, "Aircraft Valve Switcher")
            win32gui.SetForegroundWindow(handle)
        except:
            pass
    else:
        app = wx.PySimpleApp()
        wx.InitAllImageHandlers()
        frame = AircraftValveSwitcher(configFile, None, -1, "")
        app.SetTopWindow(frame)
        frame.Show()
        app.MainLoop()