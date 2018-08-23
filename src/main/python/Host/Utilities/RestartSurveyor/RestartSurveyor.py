"""
Copyright 2015, Picarro Inc.

Responsible for restarting the analyzer software if the supervisor fails to respond to repeated
pings
"""
APP_NAME = "Restart Surveyor"
APP_DESCRIPTION = "Automatically restarts the Surveyor software stack if Supervisor has died"
__version__ = 1.0

import getopt
import os
import subprocess
import sys
import time
import win32process
import shlex
import threading

from Host.Common import CmdFIFO
from Host.Common.SingleInstance import SingleInstance
from Host.Common.configobj import ConfigObj
from Host.Common import SharedTypes
from Host.Common import EventManagerProxy

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy.EventManagerProxy_Init(APP_NAME, DontCareConnection=True)

class RestartSurveyor(object):
    initialized = False

    def __init__(self, configPath=None):
        if not self.initialized:
            self.rpcServer = CmdFIFO.CmdFIFOServer(
                ('', SharedTypes.RPC_PORT_RESTART_SUPERVISOR),
                ServerName=APP_NAME,
                ServerDescription=APP_DESCRIPTION,
                ServerVersion=__version__,
                threaded=True)
                
            self.rpcServer.register_function(self.restart)

            if configPath != None:
                config = ConfigObj(configPath)
                self.iniBasePath = os.path.split(os.path.abspath(configPath))[0]

                # Read from .ini file
                try:
                    self.surveyorApp = os.path.join(self.iniBasePath, config["Main"]["SurveyorApp"].strip())
                except:
                    self.surveyorApp = "Analyzer.exe"
                self.surveyorAppPath = os.path.split(os.path.abspath(self.surveyorApp))[0]
                #
                try:
                    self.launchArgs= config["Main"]["LaunchArgs"].strip()
                except:
                    self.launchArgs = ""
                #
                self.appsToTerminate = []
                if "AppsToTerminate" in config:
                    for option in config["AppsToTerminate"]:
                        if option.startswith("App"):
                            appName = config["AppsToTerminate"][option].strip()
                            self.appsToTerminate.append(appName)

                # Number of missed pings before restarting
                try:
                    self.restartThreshold = int(config["Main"]["RestartThreshold"])
                except:
                    self.restartThreshold = 2
            else:
                raise ValueError("Configuration file must be specified to initialize RestartSupervisor")
            self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_SUPERVISOR, APP_NAME, IsDontCareConnection=False)
            self.initialized = True

        EventManagerProxy.Log("%s application started." % APP_NAME)

    def restart(self):
        try:
            if self.supervisor.CmdFIFO.PingDispatcher() == "Ping OK":
                pid = self.supervisor.CmdFIFO.GetProcessID()
                self.supervisor.TerminateApplications(False, True)
                # Kill supervisor by PID if it does not stop within 20 seconds
                try:
                    for _ in range(10):
                        p = self.supervisor.CmdFIFO.GetProcessID()
                        if p == pid:
                            time.sleep(2.0)
                    os.system(r'taskkill /F /PID %d' % pid)
                except:
                    time.sleep(2.0)
        except:
            pass
        time.sleep(5.0)
        # Kill specified applications by name
        for app in self.appsToTerminate:
            os.system(r'taskkill.exe /IM %s /F' % app)
        time.sleep(5.0)
        os.chdir(self.surveyorAppPath)
        info = subprocess.STARTUPINFO()
        dwCreationFlags = win32process.CREATE_NEW_CONSOLE
        args = shlex.split(self.surveyorApp + " " + self.launchArgs, posix=False)
        subprocess.Popen(args, startupinfo=info, creationflags=dwCreationFlags)
        return 'OK'

    def run(self):
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
                print "Restarting"
                self.restart()
            time.sleep(30.0)

    def launch(self):
        appThread = threading.Thread(target=self.run)
        appThread.setDaemon(True)
        appThread.start()
        self.rpcServer.serve_forever()

HELP_STRING = """RestartSurveyor.py [-c<FILENAME>] [-h|--help]

where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./RestartSurveyor.ini"
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
    restartSurveyorApp = SingleInstance("RestartSurveyor")
    if restartSurveyorApp.alreadyrunning():
        print "Instance of RestartSurveyor application is already running"
    else:
        configFile, options = handleCommandSwitches()
        app = RestartSurveyor(configFile)
        app.launch()
    print "Exiting program"
