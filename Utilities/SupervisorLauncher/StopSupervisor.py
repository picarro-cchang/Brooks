#!/usr/bin/python
#
# File Name: SupervisorLauncher.py
# Purpose: Launch supervisor with correct supervisor .ini file and pulse analysis .ini file
#
# File History:
# 10-01-28 alex  Created

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
from StopSupervisorFrame import StopSupervisorFrame
from Host.Common import CmdFIFO

RPC_PORT_DRIVER = 50010
APP_NAME = "SupervisorTerminator"

CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                         APP_NAME,
                                         IsDontCareConnection = False)

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

taskList = [
"BackupSupervisor.exe",
"Supervisor.exe",
"EventManager.exe",
"Archiver.exe",
"RDFrequencyConverter.exe",
"SpectrumCollector.exe",
"Fitter.exe",
"MeasSystem.exe",
"DataManager.exe",
"SampleManager.exe",
"InstMgr.exe",
"AlarmSystem.exe",
"ValveSequencer.exe",
"QuickGui.exe",
"DataLogger.exe",
"CommandInterface.exe",
"Controller.exe",
"Coordinator.exe"
]

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
    
class StopSupervisor(StopSupervisorFrame):
    def __init__(self, *args, **kwds):
        StopSupervisorFrame.__init__(self, *args, **kwds)
        self.Bind(wx.EVT_BUTTON, self.onStop, self.buttonStop)

    def onStop(self, event):
        winProcessListStr = getWinProcessListStr()
        if "\Supervisor.exe" in winProcessListStr or "\supervisor.exe" in winProcessListStr:
            d = wx.MessageDialog(None,"Do you want to Stop the analyzer now?\n\nSelect \"Yes\" to stop the analyzer.\nSelect \"No\" to cancel this action.", "Stop CRDS Analyzer Confirmation", \
            style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
            stop = (d.ShowModal() == wx.ID_YES)
            d.Destroy()
            if stop:
                for task in taskList:
                    try:
                        os.system("C:/WINDOWS/system32/taskkill.exe /IM %s /F" % task)
                    except:
                        pass
                CRDS_Driver.CmdFIFO.StopServer()
                self.Destroy()
            else:
                return
        else:
            d = wx.MessageDialog(None,"Analyzer is not running\n", "Action cancelled", style=wx.ICON_EXCLAMATION)
            d.ShowModal()
            d.Destroy()
    
if __name__ == "__main__":
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = StopSupervisor(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()