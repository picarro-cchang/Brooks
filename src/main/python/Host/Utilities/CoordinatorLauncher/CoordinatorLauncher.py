#!/usr/bin/python
#
# File Name: CoordinatorLauncher.py
# Purpose: Launch coordinator with correct coordinator .ini file and pulse analysis .ini file
#
# File History:
# 10-01-28 alex  Created

import sys
import os
import subprocess
import wx
import time
import threading
import psutil
from configobj import ConfigObj
from Host.Utilities.CoordinatorLauncher.CoordinatorLauncherFrame import CoordinatorLauncherFrame
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_VALVE_SEQUENCER

APP_NAME = "CoordinatorLauncher"
DEFAULT_CONFIG_NAME = "CoordinatorLauncher.ini"

CRDS_ValveSequencer = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_VALVE_SEQUENCER, ClientName = APP_NAME)

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

class CoordinatorLauncher(CoordinatorLauncherFrame):
    def __init__(self, configFile, *args, **kwds):
        self.co = ConfigObj(configFile)
        coorChoices = self.co.keys()
        coorChoices.remove("Main")
        CoordinatorLauncherFrame.__init__(self, coorChoices, *args, **kwds)
        apacheDir = self.co["Main"]["APACHEDir"].strip()
        try:
            self.launchType = self.co["Main"]["Type"].strip().lower()
        except:
            self.launchType = "exe" if sys.platform == "win32" else "py"
        self.coordinatorIniDir = os.path.join(apacheDir, "AppConfig/Config/Coordinator")
        self.onSelect(None)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect, self.comboBoxSelect)
        self.Bind(wx.EVT_BUTTON, self.onLaunch, self.buttonLaunch)

    def onSelect(self, event):
        self.coordinatorType = self.comboBoxSelect.GetValue()
        # Sometimes the coordinator script may not be in the standard folder
        # So we allow the user to specify the full path of the coordinator script
        coordintaorFile = self.co[self.coordinatorType]["CoordinatorIni"]
        if not os.path.isfile(coordintaorFile):
            self.coordinatorIni = os.path.join(self.coordinatorIniDir, coordintaorFile)
        else:
            self.coordinatorIni = coordintaorFile
        try:
            self.coordinatorArgs = self.co[self.coordinatorType]["Arguments"]
        except:
            self.coordinatorArgs = ""

    def onLaunch(self, event):
        try:
            myPid = os.getpid()
            for proc in psutil.process_iter():
                if "Coordinator." in " ".join(proc.cmdline()) and (proc.pid != myPid):
                    d = wx.MessageDialog(None,"Coordinator is currently running.\nDo you want to re-start the Coordinator now?", "Re-start Coordinator Confirmation", \
                        style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
                    restart = (d.ShowModal() == wx.ID_YES)
                    d.Destroy()
                    if restart:
                        proc.kill()
                        time.sleep(1)
                    else:
                        return
        except Exception, err:
            print "%r" % err

        try:
            valSeqStatus = CRDS_ValveSequencer.getValveSeqStatus()
            if "ON" in valSeqStatus:
                d = wx.MessageDialog(None,"External Valve Sequencer is currently running.\nIt will be terminated when Coordinator starts.\nDo you want to continue?", "Coordinator Launcher Confirmation", \
                style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
                confirm = (d.ShowModal() == wx.ID_YES)
                d.Destroy()
                if confirm:
                    CRDS_ValveSequencer.stopValveSeq()
                else:
                    return
        except Exception, err:
            print "%r" % err

        launchCoordinatorThread = threading.Thread(target = self._launchCoordinator)
        launchCoordinatorThread.setDaemon(True)
        launchCoordinatorThread.start()
        time.sleep(3)
        self.Destroy()

    def _launchCoordinator(self):
        #info = subprocess.STARTUPINFO()
        argList = self.coordinatorArgs.split(" ")
        while "" in argList:
            argList.remove("")
        if self.launchType != "exe":
            if sys.platform == "win32":
                info = subprocess.STARTUPINFO()
                proc = subprocess.Popen(["python.exe", "Coordinator.py"] + argList + ["-c",self.coordinatorIni], startupinfo=info)
            elif sys.platform == "linux2":
                cmd = ["python", "-O", "/home/picarro/SI2000/Host/Coordinator/Coordinator.py"] + argList + ["-c",self.coordinatorIni] #self.supervisorIni]
                proc = subprocess.Popen(cmd)

HELP_STRING = \
"""

CoordinatorLauncher.py [-h] [-c <FILENAME>]

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
    app = wx.App(False)
    frame = CoordinatorLauncher(configFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()