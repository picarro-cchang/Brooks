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
    def __init__(self, configFile, supervisorConfigFile):
        self.co = CustomConfigObj(configFile)
        self.coSupervisor = CustomConfigObj(supervisorConfigFile)
        apacheDir = self.coSupervisor["Main"]["APACHEDir"].strip()
        self.supervisorIniDir = os.path.join(apacheDir, "AppConfig\Config\Supervisor")
        self.guiIniDir = os.path.join(apacheDir, "AppConfig\Config\QuickGui")
        self.fluxSupervisorIni = os.path.join(self.supervisorIniDir, self.coSupervisor["Flux"]["SupervisorIniFile"].strip())
        self.startupSupervisorIni = os.path.join(self.supervisorIniDir, self.coSupervisor["Main"]["StartupSupervisorIni"].strip())

    def select(self, type):
        self.mode = self.co[type]["Mode"].strip()
        self.guiIni = os.path.join(self.guiIniDir, self.co[type]["GuiIni"].strip())
        self.supervisorIni = os.path.join(self.supervisorIniDir, self.co[type]["SupervisorIni"].strip())
            
    def launch(self):
        CRDS_MeasSys.Mode_Set(self.mode)
        time.sleep(5)
        CRDS_DataManager.Mode_Set(self.mode)
        os.system("C:/WINDOWS/system32/taskkill.exe /IM QuickGui.exe /F")
        time.sleep(.1)
        launchQuickGuiThread = threading.Thread(target = self._restartQuickGui)
        launchQuickGuiThread.setDaemon(True)
        launchQuickGuiThread.start()
    
    def _restartQuickGui(self):
        subprocess.Popen(["C:/Picarro/G2000/HostExe/QuickGui.exe","-c",self.guiIni])
        shutil.copy2(self.supervisorIni, self.fluxSupervisorIni)
        shutil.copy2(self.supervisorIni, self.startupSupervisorIni)
    
if __name__ == "__main__":
    configFile = sys.argv[1]
    type = sys.argv[2]
    s = FluxSwitcher(configFile)
    s.select(type)
    s.launch()