#!/usr/bin/python
#
# File Name: FluxSwitcher.py
# Purpose: Automatically switch scanning modes in flux analyzers without shutting down the software
#
# File History:
# 10-06-04 alex  Created

import sys
import os
import subprocess
import time
import shutil
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import CmdFIFO
import threading
RPC_PORT_MEAS_SYSTEM        = 50070
RPC_PORT_DATA_MANAGER       = 50160
RPC_PORT_DATALOGGER         = 50090
APP_NAME = "FluxSwitcher"
DEFAULT_CONFIG_NAME = "FluxSwitcher.ini"

CRDS_MeasSys = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM,
                                         APP_NAME,
                                         IsDontCareConnection = False)
CRDS_DataManager = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER,
                                         APP_NAME,
                                         IsDontCareConnection = False)
CRDS_DataLogger = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATALOGGER,
                                         APP_NAME,
                                         IsDontCareConnection = False)

class FluxSwitcher(object):
    def __init__(self, configFile, supervisorConfigFile, flux=True):
        self.flux = flux
        self.co = CustomConfigObj(configFile)
        self.coSupervisor = CustomConfigObj(supervisorConfigFile)
        apacheDir = self.coSupervisor["Main"]["APACHEDir"].strip()
        self.supervisorIniDir = os.path.join(apacheDir, "AppConfig\Config\Supervisor")
        self.guiIniDir = os.path.join(apacheDir, "AppConfig\Config\QuickGui")
        self.startupSupervisorIni = os.path.join(self.supervisorIniDir, self.coSupervisor["Main"]["StartupSupervisorIni"].strip())
        if self.flux:
            self.fluxSupervisorIni = os.path.join(self.supervisorIniDir, self.coSupervisor["Flux"]["SupervisorIniFile"].strip())

    def select(self, type):
        self.mode = self.co[type]["Mode"].strip()
        self.guiIni = os.path.join(self.guiIniDir, self.co[type]["GuiIni"].strip())
        self.supervisorIni = os.path.join(self.supervisorIniDir, self.co[type]["SupervisorIni"].strip())

    def launch(self):
        for tries in range(5):
            try:
                print "Calling MeasSys.Mode_Set %s" % self.mode
                CRDS_MeasSys.Mode_Set(self.mode)
                break
            except:
                time.sleep(2.0)
        time.sleep(5)
        for tries in range(5):
            try:
                print "Calling DataManager.Mode_Set %s" % self.mode
                CRDS_DataManager.Mode_Set(self.mode)
                break
            except:
                time.sleep(2.0)
        os.system("C:/WINDOWS/system32/taskkill.exe /IM QuickGui.exe /F")
        time.sleep(.1)
        launchQuickGuiThread = threading.Thread(target = self._restartQuickGui)
        launchQuickGuiThread.setDaemon(True)
        launchQuickGuiThread.start()

    def _restartQuickGui(self):
        print "C:/Picarro/G2000/HostExe/QuickGui.exe"
        subprocess.Popen(["C:/Picarro/G2000/HostExe/QuickGui.exe","-c",self.guiIni])
        shutil.copy2(self.supervisorIni, self.startupSupervisorIni)
        if self.flux:
            shutil.copy2(self.supervisorIni, self.fluxSupervisorIni)

if __name__ == "__main__":
    configFile, supervisorConfigFile, flux, type = sys.argv[1:]
    if flux.lower() == "true":
        flux = True
    else:
        flux = False
    s = FluxSwitcher(configFile, supervisorConfigFile, flux)
    s.select(type)
    s.launch()