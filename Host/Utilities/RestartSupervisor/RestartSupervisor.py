"""
Copyright 2013, Picarro Inc.

Responsible for restarting the supervisor (and the driver) on receipt
of an RPC command or if the supervisor fails to respond to repeated
pings
"""

APP_NAME = "Restart Supervisor"
APP_DESCRIPTION = "Automatically restarts the supervisor if it has died"
__version__ = 1.0

import getopt
import os
import subprocess
import sys
import time
import win32process
import threading
import inspect

from Host.autogen import interface
from Host.Common import CmdFIFO
from Host.Common.SingleInstance import SingleInstance
from Host.Common.configobj import ConfigObj
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR, Singleton
from Host.Common import SharedTypes
from Host.Common import EventManagerProxy
from Host.Common.Win32 import Kernel32


if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy.EventManagerProxy_Init(APP_NAME, DontCareConnection=True)


class RestartSupervisor(object):
    initialized = False

    def __init__(self, configPath=None):
        if not self.initialized:
            self.rpcServer = CmdFIFO.CmdFIFOServer(
                ('', SharedTypes.RPC_PORT_RESTART_SUPERVISOR),
                ServerName=APP_NAME,
                ServerDescription=APP_DESCRIPTION,
                ServerVersion=__version__,
                threaded=True)

            for s in dir(self):
                attr = self.__getattribute__(s)
                if callable(attr) and s.startswith('RPC_') and \
                    (not inspect.isclass(attr)):
                    self.rpcServer.register_function(attr, name=s, NameSlice=4)

            if configPath != None:
                config = ConfigObj(configPath)
                # Read from .ini file
                try:
                    self.launchType = config["Main"]["Type"].strip().lower()
                except:
                    self.launchType = "exe"
                try:
                    self.consoleMode = int(config["Main"]["ConsoleMode"])
                except:
                    self.consoleMode = 2
                apacheDir = config["Main"]["APACHEDir"].strip()
                self.supervisorIniDir = os.path.join(apacheDir, "AppConfig\Config\Supervisor")
                try:
                    hostDir = config["Main"]["HostDir"].strip()
                except:
                    hostDir = "Host"
                self.supervisorHostDir = os.path.join(apacheDir, hostDir)
                self.startupSupervisorIni = os.path.join(self.supervisorIniDir,
                                                         config["Main"]["StartupSupervisorIni"].strip())
                self.supervisorIni = self.startupSupervisorIni
                # Number of missed pings before restarting supervisor and driver
                try:
                    self.restartThreshold = int(config["Main"]["RestartThreshold"])
                except:
                    self.restartThreshold = 2
                # Number of restarts before performing reboot
                try:
                    self.rebootThreshold = int(config["Main"]["RebootThreshold"])
                except:
                    self.rebootThreshold = 10
            else:
                raise ValueError("Configuration file must be specified to initialize RestartSupervisor")
            self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME, IsDontCareConnection=False)
            self.initialized = True

        EventManagerProxy.Log("%s application started." % APP_NAME)


    @CmdFIFO.rpc_wrap
    def RPC_Terminate(self):
        EventManagerProxy.Log("Exiting %s." % APP_NAME)
        Kernel32.exitProcess(0)

    def killUncontrolled(self):
        # Kill the startup splash screen as well (if it exists)
        os.system(r'taskkill.exe /IM HostStartup.exe /F')
        # Kill QuickGui if it isn't under Supervisor's supervision
        os.system(r'taskkill.exe /IM QuickGui.exe /F')
        # Kill Controller if it isn't under Supervisor's supervision
        os.system(r'taskkill.exe /IM Controller.exe /F')

    def restart(self):
        try:
            if self.supervisor.CmdFIFO.PingDispatcher() == "Ping OK":
                pid = self.supervisor.CmdFIFO.GetProcessID()
                self.killUncontrolled()
                self.supervisor.TerminateApplications(False, False)
                # Kill supervisor by PID if it does not stop within 20 seconds
                try:
                    for k in range(10):
                        p = self.supervisor.CmdFIFO.GetProcessID()
                        if p == pid:
                            time.sleep(2.0)
                    os.system(r'taskkill /F /PID %d' % pid)
                except:
                    time.sleep(2.0)
        except:
            pass
        time.sleep(5.0)
        os.chdir(self.supervisorHostDir)
        info = subprocess.STARTUPINFO()
        if self.consoleMode != 1:
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = subprocess.SW_HIDE
        dwCreationFlags = win32process.CREATE_NEW_CONSOLE

        if self.launchType == "exe":
            subprocess.Popen(["supervisor.exe", "-f", "-c", self.supervisorIni], startupinfo=info, creationflags=dwCreationFlags)
        else:
            subprocess.Popen(["python.exe", "Supervisor.py", "-f", "-c", self.supervisorIni], startupinfo=info, creationflags=dwCreationFlags)

        # Launch HostStartup
        if self.launchType == "exe":
            info = subprocess.STARTUPINFO()
            subprocess.Popen(["HostStartup.exe", "-c", self.supervisorIni], startupinfo=info)
        return 'OK'

    def reboot(self):
        self.killUncontrolled()
        os.chdir(self.supervisorHostDir)
        os.system("ResetAnalyzer.exe")
        return "OK"

    def run(self):
        restartCount = 0
        while True:
            failCount = 0
            while True:
                try:
                    if self.supervisor.CmdFIFO.PingDispatcher() == "Ping OK":
                        failCount = 0
                    else:
                        failCount += 1
                except:
                    failCount += 1
                print "Supervisor ping failures", failCount
                if failCount >= self.restartThreshold:
                    restartCount += 1
                    if restartCount >= self.rebootThreshold:
                        print "Rebooting"
                        self.reboot()
                    else:
                        print "Restarting"
                        self.restart()
                    break
                time.sleep(30.0)

    def launch(self):
        appThread = threading.Thread(target=self.run)
        appThread.setDaemon(True)
        appThread.start()

        self.rpcServer.serve_forever()


HELP_STRING = """RestartSupervisor.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./RestartSupervisor.ini"
"""


def printUsage():
    print HELP_STRING


def handleCommandSwitches():
    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options.setdefault(o, a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h', "")
    #Start with option defaults...
    configFile = os.path.splitext(AppPath)[0] + ".ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile, options

if __name__ == "__main__":
    restartSupervisorApp = SingleInstance("RestartSupervisor")
    if restartSupervisorApp.alreadyrunning():
        print "Instance of RestartSupervisor application is already running"
    else:
        configFile, options = handleCommandSwitches()
        app = RestartSupervisor(configFile)
        app.launch()
    print "Exiting program"
