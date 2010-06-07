#!/usr/bin/python
#
# File Name: FluxScheduler.py
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
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.FluxSwitcher import FluxSwitcher
from FluxSchedulerFrame import FluxSchedulerFrame

DEFAULT_CONFIG_NAME = "FluxScheduler.ini"

MIN_DWELL = 15

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

def getWinProcessListStr():
    pList = win32process.EnumProcesses()
    moduleList = []
    for p in pList:
        try:
            h = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,0,p)
            moduleList.append(win32process.GetModuleFileNameEx(h,None))
        except Exception,e:
            pass
            #print "Cannot fetch information for %s: %s" % (p,e)
    processListStr = "\n".join(moduleList)
    return processListStr
    
class FluxScheduler(FluxSchedulerFrame):
    def __init__(self, configFile, *args, **kwds):
        self.co = CustomConfigObj(configFile)
        self.switcher = FluxSwitcher(configFile)
        typeChoices = self.co.keys()
        FluxSchedulerFrame.__init__(self, typeChoices, *args, **kwds)
        self.dwellList = []
        self.selectList = []
        self.Bind(wx.EVT_BUTTON, self.onLaunch, self.buttonLaunch)

    def onLaunch(self, event):
        self.buttonLaunch.Enable(False)
        for i in range(3):
            dwell = float(self.dwell[i].GetValue())
            if dwell > 0.0:
                if dwell >= MIN_DWELL:
                    self.dwellList.append(dwell)
                    self.selectList.append(self.comboBoxSelect[i].GetValue())
                else:
                    d = wx.MessageDialog(None, "Minimum dwell time is %.1f minutes. Enter 0 to skip a mode." % MIN_DWELL, "Incorrect Dwell Time", wx.OK|wx.ICON_ERROR)
                    d.ShowModal()
                    d.Destroy()
                    return
            else:
                continue
        launchQuickGuiThread = threading.Thread(target = self._runScheduler)
        launchQuickGuiThread.setDaemon(True)
        launchQuickGuiThread.start()
    
    def _runScheduler(self):
        idx = 0
        numModes = len(self.dwellList)
        if numModes > 0:
            while True:
                type = self.selectList[idx]
                self.switcher.select(type)
                self.switcher.launch()
                print "Run mode %s\n" % type
                if numModes == 1:
                    break
                time.sleep(self.dwellList[idx]*60.0)
                idx = (idx+1) % numModes
        else:
            return
            
HELP_STRING = \
"""

FluxScheduler.py [-h] [-c <FILENAME>]

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
    frame = FluxScheduler(configFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()