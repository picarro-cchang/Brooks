#!/usr/bin/python
#
# File Name: StopSupervisor.py
# Purpose: Stop supervisor and all supervised components.
#
# 

import sys
import os
import wx
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR

APP_NAME = "SupervisorTerminator"

CRDS_Supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
                                         APP_NAME,
                                         IsDontCareConnection = False)
#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

class StopSupervisorFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Stop CRDS Software")
        self.SetBackgroundColour("#E0FFFF")

        # labels
        self.labelTitle = wx.StaticText(self, -1, "Stop CRDS Software", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

        self.selectShutdownType = wx.RadioBox(self, -1, "Select shutdown method",
        choices=["Stop software but keep driver running", "Stop software and driver", "Turn off analyzer in current state"],
        majorDimension=1, style=wx.RA_SPECIFY_COLS)

        # button
        self.buttonStop = wx.Button(self, -1, "Stop", style=wx.ALIGN_CENTRE, size=(110, 20))
        self.buttonStop.SetBackgroundColour(wx.Colour(237, 228, 199))

        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        sizer_1.Add(self.labelTitle, 0, wx.TOP|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 20)
        sizer_1.Add(self.selectShutdownType, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 20)
        sizer_1.Add(self.buttonStop, 0, wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 20)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

class StopSupervisor(StopSupervisorFrame):
    def __init__(self, *args, **kwds):
        StopSupervisorFrame.__init__(self, *args, **kwds)
        self.Bind(wx.EVT_BUTTON, self.onStop, self.buttonStop)
        
    def onStop(self, event):
        try:
            if CRDS_Supervisor.CmdFIFO.PingFIFO() == "Ping OK":
                d = wx.MessageDialog(None,"Do you want to Stop the analyzer now?\n\nSelect \"Yes\" to stop the analyzer.\nSelect \"No\" to cancel this action.", "Stop CRDS Analyzer Confirmation", \
                style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
                stop = (d.ShowModal() == wx.ID_YES)
                d.Destroy()
                if stop:
                    self.Stop()
                else:
                    return
            else:
                d = wx.MessageDialog(None,"Analyzer is not running\n", "Action cancelled", style=wx.ICON_EXCLAMATION)
                d.ShowModal()
                d.Destroy()
        except:
            d = wx.MessageDialog(None,"Analyzer is not running\n", "Action cancelled", style=wx.ICON_EXCLAMATION)
            d.ShowModal()
            d.Destroy()
            
    def Stop(self, option=None):
        try:
            # Kill the RestartSurveyor (if it exists)
            os.system(r'taskkill.exe /IM RestartSurveyor.exe /F')
            # Kill the startup splash screen as well (if it exists)
            os.system(r'taskkill.exe /IM HostStartup.exe /F')
            # Kill QuickGui if it isn't under Supervisor's supervision
            os.system(r'taskkill.exe /IM QuickGui.exe /F')
            # Kill Controller if it isn't under Supervisor's supervision
            os.system(r'taskkill.exe /IM Controller.exe /F')

            if option is None:
                sel = self.selectShutdownType.GetSelection()
            else:
                sel = option
            if sel == 0:
                CRDS_Supervisor.TerminateApplications(False, False)
            if sel == 1:
                CRDS_Supervisor.TerminateApplications(False, True)
            if sel == 2:
                CRDS_Supervisor.TerminateApplications(True, True)
            self.Destroy()
        except:
            if option is None:
                raise
            else:
                print "Analyzer is not running. Action cancelled"

HELP_STRING = \
"""\
StopSupervisor.py [-h] [-o<OPTION>]

Where the options can be a combination of the following:
-h              Print this help.
-o              Specify option for shutting down supervisor. If not specified, a GUI will be shown inquiring the shut-down option
                    0: Stop software but keep driver running
                    1: Stop software and driver
                    2: Turn off analyzer in current state
"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt
    alarmConfigFile = None
    shortOpts = 'ho:'
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
        sys.exit()
    
    #Start with option defaults...
    shutDownOption = -1

    if "-o" in options:
        shutDownOption = int(options["-o"])
        print "Shutdown option specified at command line: %d" % shutDownOption
        
    return shutDownOption            
            
if __name__ == "__main__":
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    shutDownOption = HandleCommandSwitches()
    frame = StopSupervisor(None, -1, "")
    if shutDownOption == -1:
        app.SetTopWindow(frame)
        frame.Show()
        app.MainLoop()
    else:
        frame.Stop(shutDownOption)