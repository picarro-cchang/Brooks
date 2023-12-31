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
import shutil
from configobj import ConfigObj
from Host.Utilities.SupervisorLauncher.SupervisorLauncherFrame import (SupervisorLauncherFrame, UserNotificationsFrameGui)
from Host.autogen import interface
from Host.Common import CmdFIFO
from Host.Common.SingleInstance import SingleInstance
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR, RPC_PORT_QUICK_GUI, RPC_PORT_DRIVER

APP_NAME = "SupervisorLauncher"
DEFAULT_CONFIG_NAME = "SupervisorLauncher.ini"

CRDS_Supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME, IsDontCareConnection=False)
CRDS_QuickGui = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_QUICK_GUI, APP_NAME, IsDontCareConnection=False)
CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, APP_NAME, IsDontCareConnection=False)
#Set up a useful AppPath reference...
if hasattr(sys, "frozen"):  #we're running compiled with py2exe
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
            self.launchType = "exe" if sys.platform == "win32" else "py"
        self.notificationsFrame = None
        self.startSupervisorThread = None
        self.delay = delay
        self.autoLaunch = autoLaunch
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
        self.supervisorIniDir = os.path.join(apacheDir, r"AppConfig/Config/Supervisor")
        quickGuiIniFile = os.path.join(apacheDir, r"AppConfig/Config/QuickGui/QuickGui.ini")
        try:
            hostDir = self.co["Main"]["HostDir"].strip()
        except:
            hostDir = "Host"
        self.supervisorHostDir = os.path.join(apacheDir, hostDir)
        self.startupSupervisorIni = os.path.join(self.supervisorIniDir, self.co["Main"]["StartupSupervisorIni"].strip())
        try:
            self.timeBeforeKillApp = int(self.co["Main"]["timeBeforeKillApp"].strip())
        except:
            self.timeBeforeKillApp = 5000  # millisecond

        self.onSelect(None)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect, self.comboBoxSelect)
        self.Bind(wx.EVT_BUTTON, self.onLaunch, self.buttonLaunch)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.timer.Start(1000)
        self.closeValves = closeValves
        self.killAll = killAll
        if self.delay:
            self.notificationsFrame = UserNotificationsFrameGui(None, -1, "")
            self.notificationsFrame.button_dismiss.SetLabel("System Clock Reset - Restarting Analyzer")
            self.notificationsFrame.Show()
            wx.CallLater(1000 * self.delay, self.doAutomatic)
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
        elif self.autoLaunch and self.delay > 0:  # auto launching by Driver due to system clock reset
            self.supervisorIni = self.startupSupervisorIni
            self.runForcedLaunch()
            wx.CallLater(3000, self.Hide)
        elif self.autoLaunch and self.delay == 0:  # auto launching by Start Instrument
            self.supervisorIni = self.startupSupervisorIni
            self.runForcedLaunch()
            if self.timeBeforeKillApp > 0:
                wx.CallLater(self.timeBeforeKillApp, self.Destroy)
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
                    killList = ["HostStartup", "QuickGui", "Controller"]
                    for proc in psutil.process_iter():
                        cmd = " ".join(proc.cmdline())
                        for kp in killList:
                            if kp in cmd:
                                proc.kill()
                                break
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
                    if sys.platform == "win32":
                        os.system(r'taskkill /F /PID %d' % pid)
                    else:
                        try:
                            proc = psutil.Process(pid)
                            proc.kill()
                        except:
                            pass
                except:
                    time.sleep(2.0)
                    pass
                if self.closeValves:
                    CRDS_Driver.wrDasReg(interface.VALVE_CNTRL_STATE_REGISTER, interface.VALVE_CNTRL_DisabledState)
                    CRDS_Driver.setValveMask(0)
        except:
            pass

        if (not self.forcedLaunch):  #and (self.launchType == "exe"):
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
            if sys.platform == "win32":
                info = subprocess.STARTUPINFO()
                proc = subprocess.Popen(["python.exe", "Supervisor.py", "-c", self.supervisorIni], startupinfo=info)
            elif sys.platform == "linux2":
                if os.path.exists("Supervisor.py"):
                    cmd = ["xterm", "-T", "Supervisor", "-e", "python", "-O", "Supervisor.py", "-c", self.supervisorIni]
                else:
                    cmd = ["xterm", "-T", "Supervisor", "-e", "python", "-O", "Supervisor.pyo", "-c", self.supervisorIni]
                proc = subprocess.Popen(cmd)
        else:
            backupSupervisorRunning = False
            for loops in range(5):
                if backupSupervisorRunning:
                    break
                os.system("taskkill /im Supervisor.exe /f")
                os.system("taskkill /im HostStartup.exe /f")
                info = subprocess.STARTUPINFO()
                if self.consoleMode != 1:
                    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    info.wShowWindow = subprocess.SW_HIDE
                supervisor_proc = subprocess.Popen(["supervisor.exe", "-c", self.supervisorIni], startupinfo=info)
                info = subprocess.STARTUPINFO()
                subprocess.Popen(["HostStartup.exe", "-c", self.supervisorIni], startupinfo=info)
                for waitBackupSupervisor in range(12):
                    if backupSupervisorRunning:
                        break
                    retcode = supervisor_proc.poll()
                    if retcode is not None:  # i.e. main supervisor terminated
                        break
                    # Call psutil to see if backup supervisor is running
                    for proc in psutil.process_iter():
                        try:
                            if proc.name.lower().startswith('supervisor.exe'):
                                backupSupervisorRunning = '--backup' in proc.cmdline
                                if backupSupervisorRunning: break
                        except psutil.Error:
                            pass
                    time.sleep(10.0)
                else:
                    raise RuntimeError("Timed out waiting for backup supervisor")
            else:
                raise RuntimeError("Too many restart attempts for supervisor")
            time.sleep(2.0)
        self.setGuiTitle()
        self.Close()

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
    modeSpecified = options.get("-m", None)

    return (configFile, autoLaunch, closeValves, delay, killAll, modeSpecified)


def main():
    (configFile, autoLaunch, closeValves, delay, killAll, modeSpecified) = HandleCommandSwitches()
    # Save the pid file in the /tmp/ directory so Supervisor doesn't try to
    # restart the app during its MonitorApps loop
    path = "/tmp/"
    supervisorLauncherApp = SingleInstance("SupervisorLauncher", path)

    if supervisorLauncherApp.alreadyrunning() and not (autoLaunch or modeSpecified != None):
        if sys.platform == "win32":
            import win32gui
            try:
                handle = win32gui.FindWindowEx(0, 0, None, "Picarro Mode Switcher")
                win32gui.SetForegroundWindow(handle)
            except:
                pass
    else:
        myPid = os.getpid()
        for proc in psutil.process_iter():
            if "SupervisorLauncher" in " ".join(proc.cmdline()) and (proc.pid != myPid):
                proc.kill()
                break

        app = wx.App(False)
        frame = SupervisorLauncher(configFile, autoLaunch, closeValves, delay, killAll, None, -1, "", mode=modeSpecified)
        if not autoLaunch:
            frame.initMode()
            app.SetTopWindow(frame)
            # frame.Show()
        app.MainLoop()


if __name__ == "__main__":
    main()
