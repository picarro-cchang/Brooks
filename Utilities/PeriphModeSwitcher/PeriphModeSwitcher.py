#!/usr/bin/python
#
# File Name: PeriphModeSwitcher.py
# Purpose: Allows user to switch peripheral modes
#
# File History:
# 11-07-21 alex  Created

import sys
import os
import time
import shutil
import win32gui
import wx
from Host.Common.CustomConfigObj import CustomConfigObj
from PeriphModeSwitcherFrame import PeriphModeSwitcherFrame
from Host.Common.SingleInstance import SingleInstance

DEFAULT_CONFIG_NAME = "PeriphModeSwitcher.ini"

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)
    
class PeriphModeSwitcher(PeriphModeSwitcherFrame):
    def __init__(self, configFile, *args, **kwds):
        self.co = CustomConfigObj(configFile)
        basePath = os.path.split(configFile)[0]
        try:
            self.periphIntrfConfig = os.path.abspath(os.path.join(basePath, self.co.get("PeriphIntrf", "periphIntrfConfig")))
        except Exception, err:
            print "%r" % err
            self.periphIntrfConfig = os.path.abspath(os.path.join(basePath, "../PeriphIntrf/RunSerial2Socket.ini"))
            
        try:
            periphCo = CustomConfigObj(self.periphIntrfConfig)
            currentPeriphMode = periphCo.get("SETUP", "ID")
        except Exception, err:
            print "%r" % err
            currentPeriphMode = None
            
        try:
            periphModeDir = os.path.abspath(os.path.join(basePath, self.co.get("PeriphIntrf", "periphModeDir")))
        except Exception, err:
            print "%r" % err
            periphModeDir = os.path.dirname(self.periphIntrfConfig)
            
        self.periphModeDict = {}
        if os.path.isdir(periphModeDir):
            for f in [d for d in os.listdir(periphModeDir) if d.startswith("PeriphMode_")]:
                self.periphModeDict[f.split(".")[0][11:]] = os.path.join(periphModeDir, f)
        else:
            raise Exception, "PeriphMode files not found in %s" % (periphModeDir,)
            
        typeChoices = sorted(self.periphModeDict.keys())
        PeriphModeSwitcherFrame.__init__(self, typeChoices, currentPeriphMode, *args, **kwds)
        
        self.Bind(wx.EVT_BUTTON, self.onApply, self.buttonApply)
        
    def onApply(self, event):
        periphMode = self.comboBoxSelect.GetValue()
        periphModeFile = self.periphModeDict[periphMode]
        try:
            shutil.copy2(periphModeFile, self.periphIntrfConfig)
        except:
            pass
                
        d = wx.MessageDialog(None,"Please re-start the analyzer software to enable the new peripheral mode", "Selected Peripheral Mode: %s" % periphMode, \
        style=wx.OK | wx.ICON_INFORMATION | wx.STAY_ON_TOP)
        d.ShowModal()
        d.Destroy()
        time.sleep(0.5)
        self.Destroy()
                
HELP_STRING = \
"""

PeriphModeSwitcher.py [-h] [-c <FILENAME>]

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
    periphModeSwitcherApp = SingleInstance("PicarroPeriphModeSwitcher")
    if periphModeSwitcherApp.alreadyrunning():
        try:
            handle = win32gui.FindWindowEx(0, 0, None, "Peripheral Mode Switcher")
            win32gui.SetForegroundWindow(handle)
        except:
            pass
    else:
        app = wx.PySimpleApp()
        wx.InitAllImageHandlers()
        frame = PeriphModeSwitcher(configFile, None, -1, "")
        app.SetTopWindow(frame)
        frame.Show()
        app.MainLoop()