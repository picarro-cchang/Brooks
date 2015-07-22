#!/usr/bin/python
#
# File Name: SupervisorLauncher.py
# Purpose: Launch supervisor with correct supervisor .ini file and pulse analysis .ini file
#
# File History:
# 10-01-28 alex  Created

import sys
import os
import psutil
import subprocess
import wx
import time
import threading
import win32gui
import shutil
from configobj import ConfigObj
from Host.Utilities.SupervisorLauncher.SupervisorLauncherFrame import (SupervisorLauncherFrame,
    UserNotificationsFrameGui)
from Host.autogen import interface
from Host.Common import CmdFIFO
from Host.Common.SingleInstance import SingleInstance
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR, RPC_PORT_QUICK_GUI, RPC_PORT_DRIVER

APP_NAME = "SupervisorLauncher"
DEFAULT_CONFIG_NAME = "SupervisorLauncher.ini"

CRDS_Supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
                                         APP_NAME,
                                         IsDontCareConnection = False)
CRDS_QuickGui = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_QUICK_GUI,
                                         APP_NAME,
                                         IsDontCareConnection = False)
CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                         APP_NAME,
                                         IsDontCareConnection = False)
#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

class SupervisorLauncher(SupervisorLauncherFrame):
    def __init__(self, configFile, autoLaunch, closeValves, delay, killAll, *args, **kwds):
        self.mode = None
        if 'mode' in kwds:
            self.mode = kwds['mode']
            del kwds['mode']
        self.co = ConfigObj(configFile)
        try:
            self.launchType = self.co["Main"]["Type"].strip().lower()
        except:
            self.launchType = "exe"
        self.notificationsFrame = None
        self.startSupervisorThread = None
        self.delay = delay
        self.explicitModeLaunch = False
        self.forcedLaunch = False
        typeChoices = self.co.keys()
        typeChoices.remove("Main")
        SupervisorLauncherFrame.__init__(self, typeChoices, *args, **kwds)
        try:
            self.consoleMode = int(self.co["Main"]["ConsoleMode"])
        except:
            self.consoleMode = 2
        apacheDir = self.co["Main"]["APACHEDir"].strip()
        self.supervisorIniDir = os.path.join(apacheDir, r"AppConfig\Config\Supervisor")
        quickGuiIniFile = os.path.join(apacheDir, r"AppConfig\Config\QuickGui\QuickGui.ini")
        try:
            hostDir = self.co["Main"]["HostDir"].strip()
        except:
            hostDir = "Host"
        self.supervisorHostDir = os.path.join(apacheDir, hostDir)
        self.startupSupervisorIni = os.path.join(self.supervisorIniDir, self.co["Main"]["StartupSupervisorIni"].strip())

        self.onSelect(None)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect, self.comboBoxSelect)
        self.Bind(wx.EVT_BUTTON, self.onLaunch, self.buttonLaunch)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.timer.Start(1000)
        self.closeValves = closeValves
        self.killAll = killAll
        if self.delay:
            self.notificationsFrame = UserNotificationsFrameGui(None,-1,"")
            self.notificationsFrame.button_dismiss.SetLabel("System Clock Reset - Restarting Analyzer")
            self.notificationsFrame.Show()
            wx.CallLater(1000*self.delay, self.doAutomatic)
        else:
            self.doAutomatic()

    def onTimer(self, event):
        if self.startSupervisorThread is not None:
            if not self.startSupervisorThread.is_alive():
                if self.notificationsFrame is not None:
                    if not self.notificationsFrame.closed:
                        return
                    self.notificationsFrame.Close()
                    self.notificationsFrame = None
                self.timer.Stop()
                self.Close()

    def doAutomatic(self):
        if self.mode is not None:
            self.assignType(self.mode)
            self.runExplicitModeLaunch()
            wx.CallLater(3000, self.Hide)
        elif autoLaunch:
            self.supervisorIni = self.startupSupervisorIni
            self.runForcedLaunch()
            wx.CallLater(3000, self.Hide)
        else:
            self.Show()

    def initMode(self):
        ini = ConfigObj(self.startupSupervisorIni)
        try:
            self.comboBoxSelect.SetValue(ini['ModeSwitcher']['Mode'])
        except:
            pass
        self.assignType(self.comboBoxSelect.GetValue())

    def onSelect(self, event):
        self.supervisorType = self.comboBoxSelect.GetValue()
        self.supervisorIni = os.path.join(self.supervisorIniDir, self.co[self.supervisorType]["SupervisorIniFile"].strip())

    def assignType(self, supervisorType):
        self.supervisorType = supervisorType
        self.supervisorIni = os.path.join(self.supervisorIniDir, self.co[self.supervisorType]["SupervisorIniFile"].strip())

    def runExplicitModeLaunch(self):
        self.explicitModeLaunch = True
        self.onLaunch(None)

    def runForcedLaunch(self):
        self.forcedLaunch = True
        self.onLaunch(None)

    def onLaunch(self, event):
        # Terminate the current supervisor
        try:
            if CRDS_Supervisor.CmdFIFO.PingDispatcher() == "Ping OK":
                pid = CRDS_Supervisor.CmdFIFO.GetProcessID()
                if self.forcedLaunch or self.explicitModeLaunch:
                    restart = True
                else:
                    d = wx.MessageDialog(None,"Picarro CRDS analyzer is currently running.\nDo you want to re-start the analyzer now?\n\nSelect \"Yes\" to re-start the analyzer with the selected measurement mode.\nSelect \"No\" to cancel this action and keep running the current measurement mode.", "Re-start CRDS Analyzer Confirmation", \
                    style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
                    restart = (d.ShowModal() == wx.ID_YES)
                    d.Destroy()
                if restart:
                    # Kill the startup splash screen
                    os.system(r'taskkill.exe /IM HostStartup.exe /F')
                    # Kill QuickGui if it isn't under Supervisor's supervision
                    os.system(r'taskkill.exe /IM QuickGui.exe /F')
                    # Kill Controller if it isn't under Supervisor's supervision
                    os.system(r'taskkill.exe /IM Controller.exe /F')
                    if self.killAll:
                        CRDS_Supervisor.TerminateApplications(False, True)
                    else:
                        CRDS_Supervisor.TerminateApplications(False, False)
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
                if self.closeValves:
                    CRDS_Driver.wrDasReg( interface.VALVE_CNTRL_STATE_REGISTER, interface.VALVE_CNTRL_DisabledState )
                    CRDS_Driver.setValveMask(0)
        except:
            pass

        if (not self.forcedLaunch) and (self.launchType == "exe"):
            try:
                shutil.copy2(self.supervisorIni, self.startupSupervisorIni)
                startupIni = ConfigObj(self.startupSupervisorIni, list_values=False)
                startupIni['ModeSwitcher'] = {}
                startupIni['ModeSwitcher']['Mode'] = self.supervisorType
                startupIni.write_empty_values = True
                startupIni.write()
            except:
                pass

        self.startSupervisorThread = threading.Thread(target=self.startSupervisor)
        self.startSupervisorThread.setDaemon(True)
        self.startSupervisorThread.start()

    def startSupervisor(self):
        os.chdir(self.supervisorHostDir)

        # At this point, we start up the supervisor and host startup
        #
        # while True:
        #     Kill supervisors, kill HostStartup.exe
        #     Start supervisor, start HostStartup.exe
        #     backup_supervisor_running = False
        #     while not backup_supervisor_running:
        #         if main supervisor has terminated:
        #             break
        #         backup_supervisor_running = (Get process list and scan for backup supervisor ok)
        #         sleep(2.0)
        #     if backup_supervisor_running:
        #         send title to QuickGui
        #         break

        if self.launchType != "exe":
            proc = subprocess.Popen(["python.exe", "Supervisor.py","-c",self.supervisorIni], startupinfo=info)
        else:
            backupSupervisorRunning = False
            while not backupSupervisorRunning:
                os.system("taskkill /im Supervisor.exe /f")
                os.system("taskkill /im HostStartup.exe /f")
                info = subprocess.STARTUPINFO()
                if self.consoleMode != 1:
                    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    info.wShowWindow = subprocess.SW_HIDE
                supervisor_proc = subprocess.Popen(["supervisor.exe","-c",self.supervisorIni], startupinfo=info)
                info = subprocess.STARTUPINFO()
                subprocess.Popen(["HostStartup.exe","-c",self.supervisorIni], startupinfo=info)
                while not backupSupervisorRunning:
                    retcode = supervisor_proc.poll()
                    if retcode is not None: # i.e. main supervisor terminated
                        break
                    # Call psutil to see if backup supervisor is running
                    for proc in psutil.process_iter():
                        try:
                            if proc.name.lower().startswith('supervisor.exe'):
                                backupSupervisorRunning = '--backup' in proc.cmdline
                                if backupSupervisorRunning: break
                        except psutil.Error:
                            pass
                    time.sleep(2.0)
        self.setGuiTitle()

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
-k         : Kill all applications including Driver when switching modes
-v         : Close all solenoid valves and disable inlet/outlet valves during mode switching
-m         : Launch the specified supervisor mode (use quotes if the mode contains spaces)

"""

def PrintUsage():
    print HELP_STRING

def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:d:avkm:", ["help"])
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

    delay = 0
    if "-d" in options:
        delay = float(options["-d"])

    autoLaunch = "-a" in options
    closeValves = "-v" in options
    killAll = "-k" in options
    modeSpecified = options.get("-m",None)

    return (configFile, autoLaunch, closeValves, delay, killAll, modeSpecified)

if __name__ == "__main__":
    (configFile, autoLaunch, closeValves, delay, killAll, modeSpecified) = HandleCommandSwitches()
    supervisorLauncherApp = SingleInstance("PicarroSupervisorLauncher")

    if supervisorLauncherApp.alreadyrunning() and not (autoLaunch or modeSpecified!=None):
        try:
            handle = win32gui.FindWindowEx(0, 0, None, "Picarro Mode Switcher")
            win32gui.SetForegroundWindow(handle)
        except:
            pass
    else:
        try:
            handle = win32gui.FindWindowEx(0, 0, None, "Picarro Mode Switcher")
            win32gui.CloseWindow(handle)
        except:
            pass
        app = wx.PySimpleApp()
        wx.InitAllImageHandlers()
        frame = SupervisorLauncher(configFile, autoLaunch, closeValves, delay, killAll, None, -1, "", mode=modeSpecified)
        frame.initMode()
        app.SetTopWindow(frame)
        #frame.Show()
        app.MainLoop()
#
# SupervisorLauncher.py -d 3 -k -a -c c:\Picarro\G2000\AppConfig\Config\Utilities\SupervisorLauncher.ini
