# InstUtils.py
#
# Instrument utility functions for the Win7 migration scripts

import os
import logging

import Win7MigrationToolsDefs as mdefs

from Host.Common import CmdFIFO
#from Host.Common import SharedTypes
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_SUPERVISOR

APP_NAME = "Win7MigrationTools"

class AnalyzerInfo(object):
    def __init__(self, appName = None):
        if appName is None:
            appName = APP_NAME

        self.logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

        try:
            self.driverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, 
                                                        ClientName = appName)
        except:
            self.driverRpc = None

        if self.driverRpc is None:
            self.logger.error("Instrument is not running!")

        try:
            self.crdsSupervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
                                                             ClientName = appName,
                                                             IsDontCareConnection = False)
        except:
            self.crdsSupervisor = None


        self._fetchAnalyzerNameAndSerial()
        self._fetchAnalyzerHostSoftwareVersion()

    def _fetchAnalyzerNameAndSerial(self):
        try:
            analyzerId = self.driverRpc.fetchObject("LOGIC_EEPROM")[0]
            self.analyzerName = analyzerId["Analyzer"]
            self.analyzerNum = analyzerId["AnalyzerNum"]
            self.chassis = analyzerId["Chassis"]
        except:
            self.analyzerName = "Unknown"
            self.analyzerNum = ""
            self.chassis = "Unknown"

        self.analyzerId = self.analyzerName + self.analyzerNum

    def _fetchAnalyzerHostSoftwareVersion(self):
        v = ""
        try:
            dV = self.driverRpc.allVersions()
            self.hostSoftwareVersion = dV["host release"]

            #boldText = "SOFTWARE RELEASE VERSION : %s\n" % dV["host release"]
            klist = dV.keys()
            klist.sort()
            v += "Version strings:\n"
            for k in klist:
                if k != "host release":
                    v += "%s : %s\n" % (k,dV[k])

            self.allVersion = v

        except:
            self.hostSoftwareVersion = "Software version information unavailable"

    def isInstrumentRunning(self):
        if self.driverRpc is not None:
            return True
        else:
            return False

    def getAnalyzerSoftwareVersion(self):
        return self.hostSoftwareVersion

    def getAllSoftwareVersion(self):
        return self.allVersion

    def getAnalyzerName(self):
        return self.analyzerName

    def getAnalyzerNum(self):
        return self.analyzerNum

    def getAnalyzerChassis(self):
        return self.chassis

    def getAnalyzerNameAndNum(self):
        analyzerNameNum = self.analyzerName + self.analyzerNum
        return analyzerNameNum

    def stopAnalyzerAndDriver(self):
        # leave the version info as cached
        if self.crdsSupervisor is not None:
            # kill off all of the apps
            # Kill the startup splash screen as well (if it exists)
            os.system(r'taskkill.exe /IM HostStartup.exe /F')
            # Kill QuickGui if it isn't under Supervisor's supervision
            os.system(r'taskkill.exe /IM QuickGui.exe /F')
            # Kill Controller if it isn't under Supervisor's supervision
            os.system(r'taskkill.exe /IM Controller.exe /F')

            # kill the driver (powerDown=False,stopProtected=True)
            self.crdsSupervisor.TerminateApplications(False, True)
        else:
            self.logger.info("Analyzer is not running.")

        # since we're stopping the Analyzer, must reset the driver handle
        self.driverRpc = None
        self.crdsSupervisor = None


def main():
    anInfo = AnalyzerInfo()

    print "Analyzer running: %s" % anInfo.isInstrumentRunning()

    print "Analyzer name:    %s" % anInfo.getAnalyzerName()
    print "Analyzer number:  %s" % anInfo.getAnalyzerNum()
    print "Analyzer chassis: %s" % anInfo.getAnalyzerChassis()
    print "Analyzer software version: %s" % anInfo.getAnalyzerSoftwareVersion()
    print ""
    print "Analyzer software version (all): %s" % anInfo.getAllSoftwareVersion()

    # stop the software
    if anInfo.isInstrumentRunning():
        response = raw_input("Instrument is running, stop the software and driver? Y or N: ")
        response = response.upper()

        if response == "Y":
            print "Stopping the software and driver, please wait."
            anInfo.stopAnalyzerAndDriver()
            print "Software and driver has been stopped."

    else:
        print "Instrument is not running"



if __name__ == "__main__":
    main()