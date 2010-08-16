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
import win32gui
import shutil
from configobj import ConfigObj
from SupervisorLauncherFrame import SupervisorLauncherFrame
from Host.Common import CmdFIFO
import threading
from Host.Common.SingleInstance import SingleInstance

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

TASKLIST = [
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
    def __init__(self, configFile, autoLaunch, *args, **kwds):
        self.co = ConfigObj(configFile)
        self.forcedLaunch = False
        typeChoices = self.co.keys()
        typeChoices.remove("Main")
        SupervisorLauncherFrame.__init__(self, typeChoices, *args, **kwds)
        try:
            self.consoleMode = int(self.co["Main"]["ConsoleMode"])
        except:
            self.consoleMode = 2
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
        if autoLaunch:
            self.supervisorIni = self.startupSupervisorIni
            self.consoleMode = 2
            self.forcedLaunch = True
            self.onLaunch(None)
            time.sleep(3)
            self.Destroy()
        
    def onSelect(self, event):
        self.supervisorType = self.comboBoxSelect.GetValue()
        self.supervisorIni = os.path.join(self.supervisorIniDir, self.co[self.supervisorType]["SupervisorIniFile"].strip())
            
    def onLaunch(self, event):
        winProcessListStr = getWinProcessListStr()
        if "\Supervisor.exe" in winProcessListStr or "\supervisor.exe" in winProcessListStr:
            if self.forcedLaunch:
                restart = True
            else:
                d = wx.MessageDialog(None,"Picarro CRDS analyzer is currently running.\nDo you want to re-start the analyzer now?\n\nSelect \"Yes\" to re-start the analyzer with the selected measurement mode.\nSelect \"No\" to cancel this action and keep running the current measurement mode.", "Re-start CRDS Analyzer Confirmation", \
                style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
                restart = (d.ShowModal() == wx.ID_YES)
                d.Destroy()
            if restart:
                for task in TASKLIST:
                    try:
                        os.system("C:/WINDOWS/system32/taskkill.exe /IM %s /F" % task)
                    except:
                        pass
                CRDS_Driver.CmdFIFO.StopServer()
                try:
                    shutil.copy2(self.supervisorIni, self.startupSupervisorIni)
                except:
                    pass
                time.sleep(1)
            else:
                return
        os.chdir(self.supervisorExeDir)
        info = subprocess.STARTUPINFO()
        if self.consoleMode != 1:
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = subprocess.SW_HIDE
        subprocess.Popen(["supervisor.exe","-f","-c",self.supervisorIni], startupinfo=info)

        # Change QuickGui Title
        setTitleThread = threading.Thread(target=self.setGuiTitle)
        setTitleThread.setDaemon(True)
        setTitleThread.start()
                
    def setGuiTitle(self):
        titleSet = False
        try:
            newTitle = self.co[self.supervisorType]["Title"].strip()
        except:
            newTitle = None
        count = 0
        while (not titleSet) and (newTitle != None) and (count < 20):
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
-a         : Automatically launch the last selected supervisor ini without showing the "mode switcher" window

"""

def PrintUsage():
    print HELP_STRING
    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:a", ["help"])
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
        
    autoLaunch = "-a" in options

    return (configFile, autoLaunch)
    
if __name__ == "__main__":
    (configFile, autoLaunch) = HandleCommandSwitches()
    supervisorLauncherApp = SingleInstance("PicarroSupervisorLauncher")
    if supervisorLauncherApp.alreadyrunning() and not autoLaunch:
        try:
            handle = win32gui.FindWindowEx(0, 0, None, "Picarro Mode Switcher")
            win32gui.SetForegroundWindow(handle)
        except:
            pass
    else:
        app = wx.PySimpleApp()
        wx.InitAllImageHandlers()
        frame = SupervisorLauncher(configFile, autoLaunch, None, -1, "")
        app.SetTopWindow(frame)
        frame.Show()
        app.MainLoop()