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
from Host.Common.CustomConfigObj import CustomConfigObj
from FluxSwitcherGuiFrame import FluxSwitcherGuiFrame
from Host.Common.FluxSwitcher import FluxSwitcher

DEFAULT_CONFIG_NAME = "FluxSwitcherGui.ini"

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)
    
class FluxSwitcherGui(FluxSwitcherGuiFrame):
    def __init__(self, configFile, supervisorConfigFile, flux, *args, **kwds):
        self.co = CustomConfigObj(configFile)
        self.switcher = FluxSwitcher(configFile, supervisorConfigFile, flux)
        typeChoices = self.co.keys()
        FluxSwitcherGuiFrame.__init__(self, typeChoices, flux, *args, **kwds)
        self.Bind(wx.EVT_BUTTON, self.onLaunch, self.buttonLaunch)

    def onLaunch(self, event):
        self.buttonLaunch.Enable(False)
        type = self.comboBoxSelect.GetValue()
        self.switcher.select(type)
        self.switcher.launch()
        self.buttonLaunch.Enable(True)
                
HELP_STRING = \
"""

FluxSwitcherGui.py [-h] [-c <FILENAME>] [-s <FILENAME>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.
-s         : Specify the SupervisorLauncher.ini file

"""

def PrintUsage():
    print HELP_STRING
    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:s:", ["help","not_flux"])
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

    if "-s" in options:
        supervisorConfigFile = options["-s"]
        print "Supervisor Launcher config file specified at command line: %s" % supervisorConfigFile
        
    flux = "--not_flux" not in options
    
    return configFile, supervisorConfigFile, flux
    
if __name__ == "__main__":
    configFile, supervisorConfigFile, flux = HandleCommandSwitches()
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = FluxSwitcherGui(configFile, supervisorConfigFile, flux, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()