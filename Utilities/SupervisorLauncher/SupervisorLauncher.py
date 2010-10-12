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
import win32gui
import shutil
from configobj import ConfigObj
from SupervisorLauncherFrame import SupervisorLauncherFrame
from Host.Common import CmdFIFO
from Host.Common.SingleInstance import SingleInstance
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR, RPC_PORT_QUICK_GUI

APP_NAME = "SupervisorLauncher"
DEFAULT_CONFIG_NAME = "SupervisorLauncher.ini"

CRDS_Supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
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
    
class SupervisorLauncher(SupervisorLauncherFrame):
    def __init__(self, configFile, autoLaunch, *args, **kwds):
        self.co = ConfigObj(configFile)
        try:
            self.launchType = self.co["Main"]["Type"].strip().lower()
        except:
            self.launchType = "exe"
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
        self.supervisorHostDir = os.path.join(apacheDir, hostDir)
        self.startupSupervisorIni = os.path.join(self.supervisorIniDir, self.co["Main"]["StartupSupervisorIni"].strip())
        
        self.onSelect(None)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect, self.comboBoxSelect)
        self.Bind(wx.EVT_BUTTON, self.onLaunch, self.buttonLaunch)
        if autoLaunch:
            self.supervisorIni = self.startupSupervisorIni
            self.forcedLaunch = True
            self.onLaunch(None)
            time.sleep(3)
            self.Destroy()
        
    def onSelect(self, event):
        self.supervisorType = self.comboBoxSelect.GetValue()
        self.supervisorIni = os.path.join(self.supervisorIniDir, self.co[self.supervisorType]["SupervisorIniFile"].strip())
            
    def onLaunch(self, event):
        # Terminate the current supervisor
        try:
            if CRDS_Supervisor.CmdFIFO.PingDispatcher() == "Ping OK":
                pid = CRDS_Supervisor.CmdFIFO.GetProcessID()
                if self.forcedLaunch:
                    restart = True
                else:
                    d = wx.MessageDialog(None,"Picarro CRDS analyzer is currently running.\nDo you want to re-start the analyzer now?\n\nSelect \"Yes\" to re-start the analyzer with the selected measurement mode.\nSelect \"No\" to cancel this action and keep running the current measurement mode.", "Re-start CRDS Analyzer Confirmation", \
                    style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
                    restart = (d.ShowModal() == wx.ID_YES)
                    d.Destroy()
                if restart:
                    CRDS_Supervisor.TerminateApplications()
                else:
                    return
                # Kill supervisor by PID if it does not stop within 5 seconds
                try:
                    for k in range(5):
                        p = CRDS_Supervisor.CmdFIFO.GetProcessID()
                        if p == pid: time.sleep(1.0)
                    os.system(r'taskkill /F /PID %d' % pid)
                except:
                    time.sleep(2.0)
                    pass
                # Kill the startup splash screen
                os.system(r'taskkill.exe /IM HostStartup.exe /F')
                # Kill QuickGui if it isn't under Supervisor's supervision
                os.system(r'taskkill.exe /IM QuickGui.exe /F')
        except:
            pass
            
        if (not self.forcedLaunch) and (self.launchType == "exe"):
            try:
                shutil.copy2(self.supervisorIni, self.startupSupervisorIni)
            except:
                pass
                
        os.chdir(self.supervisorHostDir)
        info = subprocess.STARTUPINFO()
        if self.consoleMode != 1:
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = subprocess.SW_HIDE
            
        if self.launchType == "exe":
            subprocess.Popen(["supervisor.exe","-c",self.supervisorIni], startupinfo=info)
        else:
            subprocess.Popen(["python.exe", "Supervisor.py","-c",self.supervisorIni], startupinfo=info)

        # Launch HostStartup
        if self.launchType == "exe":
            info = subprocess.STARTUPINFO()
            subprocess.Popen(["HostStartup.exe","-c",self.supervisorIni], startupinfo=info)
        #else:
        #   os.chdir(r"C:\Picarro\G2000\Host\Utilities\SupervisorLauncher")
        #   subprocess.Popen(["python.exe", "HostStartup.py","-c",self.supervisorIni.replace("EXE","")], startupinfo=info)
        
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
                try:
                    if CRDS_Supervisor.CmdFIFO.PingFIFO() == "Ping OK":
                        pass
                    else:
                        count += 1
                except:
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