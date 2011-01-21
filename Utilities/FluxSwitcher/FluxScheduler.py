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
import win32gui
import shutil
from Host.Common import CmdFIFO
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SharedTypes import RPC_PORT_MEAS_SYSTEM
from Host.Common.SingleInstance import SingleInstance
from Host.Common.FluxSwitcher import FluxSwitcher
from Host.Utilities.SupervisorLauncher.SupervisorLauncher import SupervisorLauncher
from FluxSchedulerFrame import FluxSchedulerFrame

DEFAULT_CONFIG_NAME = "FluxScheduler.ini"
FLUX_TYPES = ["CO2_H2O", "H2O_CH4", "CO2_CH4"]

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
    def __init__(self, configFile, supervisorConfigFile, *args, **kwds):
        self.co = CustomConfigObj(configFile)
        self.switcher = FluxSwitcher(configFile, supervisorConfigFile)
        self.supervisorLauncher = SupervisorLauncher(supervisorConfigFile, False, True, None, -1, "")
        typeChoices = self.co.keys()
        typeChoices.append("High_Precision_3_Gas")
        typeChoices.remove("Main")
        self.numTypes = len(typeChoices)
        self.minDwell = max(self.co.getfloat("Main", "MinDwell", default=15), 0)
        FluxSchedulerFrame.__init__(self, typeChoices, *args, **kwds)
        self.terminate = False
        self.dwellList = []
        self.selectList = []
        self.currentFlowMode = None
        self.buttonLaunch1.Enable(True)
        self.buttonLaunch2.Enable(True)
        self.buttonStop.Enable(False)
        self._enableSelects()
        self.Bind(wx.EVT_BUTTON, self.onStop, self.buttonStop)
        self.Bind(wx.EVT_BUTTON, self.onLaunch1, self.buttonLaunch1)
        self.Bind(wx.EVT_BUTTON, self.onLaunch2, self.buttonLaunch2)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        
    def onClose(self, event):
        self.supervisorLauncher.Destroy()
        self.Destroy()

    def onStop(self, event):
        self.terminate = True
        self.buttonLaunch1.Enable(True)
        self.buttonLaunch2.Enable(True)
        self.buttonStop.Enable(False)
        self._enableSelects()
        
    def onLaunch1(self, event):
        self.terminate = False
        self.buttonLaunch1.Enable(False)
        self.buttonLaunch2.Enable(False)
        self.buttonStop.Enable(True)
        self._disableSelects()
        self.dwellList = []
        self.selectList = []
        for i in range(self.numTypes):
            dwell = float(self.dwell[i].GetValue())
            if dwell > 0.0:
                if dwell >= self.minDwell:
                    self.dwellList.append(dwell)
                    self.selectList.append(self.comboBoxSelect1[i].GetValue())
                else:
                    d = wx.MessageDialog(None, "Minimum dwell time is %.1f minutes. Enter 0 to skip a mode." % self.minDwell, "Incorrect Dwell Time", wx.OK|wx.ICON_ERROR)
                    d.ShowModal()
                    d.Destroy()
                    return
            else:
                continue
        runSchedulerThread = threading.Thread(target = self._runScheduler)
        runSchedulerThread.setDaemon(True)
        runSchedulerThread.start()

    def onLaunch2(self, event):
        self.buttonLaunch1.Enable(False)
        self.buttonLaunch2.Enable(False)
        self._disableSelects()
        runSwitcherThread = threading.Thread(target = self._runSwitcher)
        runSwitcherThread.setDaemon(True)
        runSwitcherThread.start()
      
    def _runSwitcher(self):
        type = self.comboBoxSelect2.GetValue()
        if type in FLUX_TYPES:
            if self.currentFlowMode != "High":
                self.launchSupvervisor("Flux")
                self.currentFlowMode = "High"
                measState = None
                while measState != 'ENABLED':
                    time.sleep(1)
                    try:
                        MeasSysRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM,
                                     "FluxScheduler",
                                      IsDontCareConnection = False)
                        measState = MeasSysRpc.GetStates()['State_MeasSystem']
                    except:
                        measState = None
            self.switcher.select(type)
            self.switcher.launch()
        else:
            if self.currentFlowMode != "Low":
                self.launchSupvervisor("High_Precision_3_Gas")
                self.currentFlowMode = "Low"
        print "Run mode %s\n" % type
        self.buttonLaunch1.Enable(True)
        self.buttonLaunch2.Enable(True)
        self._enableSelects()
        
    def _runScheduler(self):
        idx = 0
        numModes = len(self.dwellList)
        if numModes > 0:
            while not self.terminate:
                type = self.selectList[idx]
                if type in FLUX_TYPES:
                    if self.currentFlowMode != "High":
                        self.launchSupvervisor("Flux")
                        self.currentFlowMode = "High"
                        measState = None
                        while measState != 'ENABLED':
                            time.sleep(1)
                            try:
                                MeasSysRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM,
                                             "FluxScheduler",
                                              IsDontCareConnection = False)
                                measState = MeasSysRpc.GetStates()['State_MeasSystem']
                            except:
                                measState = None
                    self.switcher.select(type)
                    self.switcher.launch()
                else:
                    if self.currentFlowMode != "Low":
                        self.launchSupvervisor("High_Precision_3_Gas")
                        self.currentFlowMode = "Low"
                        measState = None
                        while measState != 'ENABLED':
                            time.sleep(1)
                            try:
                                MeasSysRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM,
                                             "FluxScheduler",
                                              IsDontCareConnection = False)
                                measState = MeasSysRpc.GetStates()['State_MeasSystem']
                            except:
                                measState = None
                print "Run mode %s\n" % type
                if numModes == 1:
                    break
                startTime = time.time()
                while time.time() - startTime <= self.dwellList[idx]*60.0:
                    if self.terminate:
                        print "Scheduler stopped by request\n"
                        break
                    else:
                        time.sleep(1)
                idx = (idx+1) % numModes
        else:
            self.onStop(None)
            
    def launchSupvervisor(self, supervisorType):
        self.supervisorLauncher.assignType(supervisorType)
        self.supervisorLauncher.runForcedLaunch()
                        
    def _disableSelects(self):
        for i in range(self.numTypes):
            self.dwell[i].Enable(False)
            self.comboBoxSelect1[i].Enable(False)
            self.comboBoxSelect2.Enable(False)
        
    def _enableSelects(self):
        for i in range(self.numTypes):
            self.dwell[i].Enable(True)
            self.comboBoxSelect1[i].Enable(True)
            self.comboBoxSelect2.Enable(True)
            
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
        switches, args = getopt.getopt(sys.argv[1:], "hc:s:", ["help"])
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
        
    return configFile, supervisorConfigFile
    
if __name__ == "__main__":
    fluxSchedulerApp = SingleInstance("PicarroFluxModeScheduler")
    if fluxSchedulerApp.alreadyrunning():
        try:
            handle = win32gui.FindWindowEx(0, 0, None, "Flux Mode Scheduler")
            win32gui.SetForegroundWindow(handle)
        except:
            pass
    else:
        configFile, supervisorConfigFile = HandleCommandSwitches()
        app = wx.PySimpleApp()
        wx.InitAllImageHandlers()
        frame = FluxScheduler(configFile, supervisorConfigFile, None, -1, "")
        app.SetTopWindow(frame)
        frame.Show()
        app.MainLoop()