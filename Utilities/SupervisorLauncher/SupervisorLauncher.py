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
from configobj import ConfigObj
from SupervisorLauncherFrame import SupervisorLauncherFrame
from Host.Common import CmdFIFO
import threading

RPC_PORT_DRIVER    = 50010
RPC_PORT_QUICK_GUI = 50220
APP_NAME = "SupervisorLauncher"
DEFAULT_CONFIG_NAME = "SupervisorLauncher.ini"

CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                         APP_NAME,
                                         IsDontCareConnection = False)
CRDS_QuickGui = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_QUICK_GUI,
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
    
class SupervisorLauncher(SupervisorLauncherFrame):
    def __init__(self, configFile, *args, **kwds):
        self.co = ConfigObj(configFile)
        typeChoices = self.co.keys()
        typeChoices.remove("Main")
        SupervisorLauncherFrame.__init__(self, typeChoices, *args, **kwds)
        apacheDir = self.co["Main"]["APACHEDir"].strip()
        self.supervisorIniDir = os.path.join(apacheDir, "AppConfig\Config\Supervisor")
        quickGuiIniFile = os.path.join(apacheDir, "AppConfig\Config\QuickGui\QuickGui.ini")
        try:
            hostDir = self.co["Main"]["HostDir"].strip()
        except:
            hostDir = "Host"
        self.supervisorExeDir = os.path.join(apacheDir, hostDir)
        self.startupSupervisorIni = os.path.join(self.supervisorIniDir, self.co["Main"]["StartupSupervisorIni"].strip())
        self.onSelect(None)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect, self.comboBoxSelect)
        self.Bind(wx.EVT_BUTTON, self.onLaunch, self.buttonLaunch)

    def onSelect(self, event):
        self.supervisorType = self.comboBoxSelect.GetValue()
        self.supervisorIni = os.path.join(self.supervisorIniDir, self.co[self.supervisorType]["SupervisorIniFile"].strip())
            
    def onLaunch(self, event):
        winProcessListStr = getWinProcessListStr()
        if "\Supervisor.exe" in winProcessListStr or "\supervisor.exe" in winProcessListStr:
            d = wx.MessageDialog(None,"Picarro CRDS analyzer is currently running.\nDo you want to re-start the analyzer now?\n\nSelect \"Yes\" to re-start the analyzer with the selected measurement mode.\nSelect \"No\" to cancel this action and keep running the current measurement mode.", "Re-start CRDS Analyzer Confirmation", \
            style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
            restart = (d.ShowModal() == wx.ID_YES)
            d.Destroy()
            if restart:
                for task in taskList:
                    try:
                        os.system("C:/WINDOWS/system32/taskkill.exe /IM %s /F" % task)
                    except:
                        pass
                CRDS_Driver.CmdFIFO.StopServer()
                shutil.copy2(self.supervisorIni, self.startupSupervisorIni)
                time.sleep(1)
            else:
                return
        os.chdir(self.supervisorExeDir)
        subprocess.Popen(["supervisor.exe","-f","-c",self.supervisorIni])

        # Change QuickGui Title
        setTitleThread = threading.Thread(target=self.setGuiTitle)
        setTitleThread.setDaemon(True)
        setTitleThread.start()
                
    def setGuiTitle(self):
        titleSet = False
        count = 0
        while (not titleSet) and (count < 20):
            try:
                CRDS_QuickGui.setTitle(self.co[self.supervisorType]["Title"].strip())
                titleSet = True
            except:
                winProcessListStr = getWinProcessListStr()
                if "\Supervisor.exe" in winProcessListStr or "\supervisor.exe" in winProcessListStr:
                    pass
                else:
                    count += 1
                time.sleep(0.5)
                
HELP_STRING = \
"""

SupervisorLauncher.py [-h] [-c <FILENAME>]

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
    frame = SupervisorLauncher(configFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()