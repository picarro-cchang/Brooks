#!/usr/bin/python
#
# File Name: FluxSwitcherGui.py
# Purpose: Switch scanning modes in flux analyzers without shutting down the software
#
# File History:
# 10-06-03 alex  Created

import sys
import os
import subprocess
import wx
import time
import threading
import win32api
import win32process
import win32con
import shutil
from configobj import ConfigObj
from FluxSwitcherGuiFrame import FluxSwitcherGuiFrame
from Host.Common import CmdFIFO
import threading

RPC_PORT_MEAS_SYSTEM        = 50070
RPC_PORT_DATA_MANAGER       = 50160
RPC_PORT_DATALOGGER         = 50090
APP_NAME = "FluxSwitcherGui"
DEFAULT_CONFIG_NAME = "FluxSwitcher.ini"

CRDS_MeasSys = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM,
                                         APP_NAME,
                                         IsDontCareConnection = False)
CRDS_DataManager = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER,
                                         APP_NAME,
                                         IsDontCareConnection = False)
CRDS_DataLogger = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATALOGGER,
                                         APP_NAME,
                                         IsDontCareConnection = False)
#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)
    
class FluxSwitcherGui(FluxSwitcherGuiFrame):
    def __init__(self, configFile, *args, **kwds):
        self.co = ConfigObj(configFile)
        typeChoices = self.co.keys()
        FluxSwitcherGuiFrame.__init__(self, typeChoices, *args, **kwds)
        self.onSelect(None)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect, self.comboBoxSelect)
        self.Bind(wx.EVT_BUTTON, self.onLaunch, self.buttonLaunch)

    def onSelect(self, event):
        select = self.comboBoxSelect.GetValue()
        self.mode = self.co[select]["Mode"].strip()
        self.guiIni = self.co[select]["GuiIni"]
            
    def onLaunch(self, event):
        self.buttonLaunch.Enable(False)
        #CRDS_DataLogger.DATALOGGER_stopLogRpc("DataLog_User")
        #CRDS_DataLogger.DATALOGGER_stopLogRpc("DataLog_User_Sync")
        #CRDS_DataLogger.DATALOGGER_stopLogRpc("DataLog_Private")
        CRDS_MeasSys.Mode_Set(self.mode)
        time.sleep(4)
        CRDS_DataManager.Mode_Set(self.mode)
        os.system("C:/WINDOWS/system32/taskkill.exe /IM QuickGui.exe /F")
        time.sleep(.1)
        launchQuickGuiThread = threading.Thread(target = self._restartQuickGui)
        launchQuickGuiThread.setDaemon(True)
        launchQuickGuiThread.start()
    
    def _restartQuickGui(self):
        subprocess.Popen(["C:/Picarro/G2000/HostExe/QuickGui.exe","-c",self.guiIni])
        self.buttonLaunch.Enable(True)
        #time.sleep(4)
        #CRDS_DataLogger.DATALOGGER_startLogRpc("DataLog_User")
        #CRDS_DataLogger.DATALOGGER_startLogRpc("DataLog_User_Sync")
        #CRDS_DataLogger.DATALOGGER_startLogRpc("DataLog_Private")
                
HELP_STRING = \
"""

FluxSwitcherGui.py [-h] [-c <FILENAME>]

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
    configFile = HandleCommandSwitches()
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = FluxSwitcherGui(configFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()