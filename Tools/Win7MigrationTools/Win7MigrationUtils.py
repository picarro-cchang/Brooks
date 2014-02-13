# InstUtils.py
#
# Instrument utility functions for the Win7 migration scripts

import os
import sys
import logging
#import psutil
import time
import win32api
import subprocess

import Win7MigrationToolsDefs as mdefs

from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_SUPERVISOR, RPC_PORT_INSTR_MANAGER

"""
import CmdFIFO
RPC_PORT_DRIVER             = 50010
RPC_PORT_SUPERVISOR         = 50030
RPC_PORT_INSTR_MANAGER      = 50110
"""

APP_NAME = "Win7MigrationTools"

# INSTMGR Shutdown types from InstrMgr.py
INSTMGR_SHUTDOWN_PREP_SHIPMENT = 0 # shutdown host and DAS and prepare for shipment
INSTMGR_SHUTDOWN_HOST_AND_DAS  = 1 # shutdown host and DAS
INSTMGR_SHUTDOWN_HOST          = 2 # shutdown host and leave DAS in current state


def osWalkSkip(root, excludeDirs, excludeFiles):
    """
    Enumerator that walks through files under a root folder, skipping any dirs
     and filenames that passed in. Returns full dir path and filename path.

    excludeDirs     list of directory names to exclude (pass an empty list if none to exclude)
    excludeFiles    list of file names to exclude (pass an empty list if none to exclude)
    """
    for dirpath, dirnames, filenames in os.walk(root):
        for edir in excludeDirs:
            if edir in dirnames:
                dirnames.remove(edir)

        for efile in excludeFiles:
            if efile in filenames:
                filenames.remove(efile)

        # return the full directory and full filename paths
        for filename in filenames:
            yield dirpath, os.path.join(dirpath, filename)


def validateWindowsVersion(verNeeded, debug=False):
    """
    verNeeded       5 for WinXP, 6 for Win7
    """
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Validating Windows version.")

    if int(verNeeded) == 5:
        osName = "WindowsXP"
    elif int(verNeeded) == 6:
        osName = "Windows 7"
    else:
        osName = "unsupported for migration tools"

    if sys.getwindowsversion().major != int(verNeeded):
        if debug is False:
            logger.error("Current operating system is not %s!" % osName)
            validWinVersion = False
        else:
            logger.info("(debug) Current operating system is not %s, ignoring." % osName)
            validWinVersion = True
    else:
        logger.info("Validated operating system, %s is running." % osName)
        validWinVersion = True

    return validWinVersion


def validatePythonVersion(verStrNeeded, debug=False):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Validating Python version.")

    pythonVer = str(sys.version_info.major) + "." + str(sys.version_info.minor)

    if pythonVer != verStrNeeded:
        if debug is False:
            logger.error("Current Python version is %s, expected verStrNeeded!" % (pythonVer, verStrNeeded))
            validPythonVersion = False
        else:
            logger.error("(debug) Running Python version %s, expected %s, ignoring" % (pythonVer, verStrNeeded))
            validPythonVersion = True
    else:
        logger.info("Validated Python, current version is %s" % pythonVer)
        validPythonVersion = True

    return validPythonVersion



def runCommand(command):
    """
    # Run a command line command so we can capture its output.
    # Code is from here:
    #   http://stackoverflow.com/questions/4760215/running-shell-command-from-python-and-capturing-the-output
    """
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Executing command: '%s'" % command)

    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)

    stdout_value, stderr_value = p.communicate()
    # print "stdout:", repr(stdout_value)
    #return iter(p.stdout.readline, 'b')
    return stdout_value, stderr_value


def getVolumeName(driveLetter):
    """
    Returns the volume name for the drive letter argument.
    """
    # The Win32 API needs the drive letter followed by a colon and backslash 
    drive = driveLetter[0:1] + ":\\"

    driveInfo = win32api.GetVolumeInformation(drive)
    return driveInfo[0]


def setVolumeName(driveLetter, volumeName):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

    drive = driveLetter[0:1] + ":"

    logger.info("Setting volume name for %s to '%s'" % (drive, volumeName))

    # Windows command syntax is "label C: name"
    stdout_value, stderr_value = runCommand("label %s %s" % (drive, volumeName))

    #print "setVolumeName: ret='%s'" % ret
    #print "ret=%r" % ret

    # Verify the volume name got set
    newVolumeName = getVolumeName(driveLetter)

    if newVolumeName != volumeName:
        ret = False
        logger.error("Setting volume name for %s to '%s' failed." % (drive, volumeName))
    else:
        ret = True
        logger.error("Setting volume name for %s to '%s' succeeded." % (drive, volumeName))

    return ret


def isProcessRunning(procname):
    p = subprocess.Popen(["cmd", "/c", "tasklist"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)

    sout, serr = p.communicate()

    if procname in sout:
        #print "'%s' is running" % procname
        return True
    else:
        #print "'%s' is NOT running" % procname
        return False


def findRunningProcesses(processNameList):
    runningProcList = []

    if processNameList is not None and len(processNameList) > 0:
        for procname in processNameList:
            if isProcessRunning(procname):
                runningProcList.append(procname)

    return runningProcList


def waitForRunningProcessesToEnd(processNameList, waitTimeoutSec):
    """
    processNameList     list of running process names to look for
    waitTimeoutSec      number of seconds before aborting looking for processes,
                        0.0 to never timeout

    Returns True if processes are still running (timed out),
    otherwise returns False
    """
    endTime = time.time() + waitTimeoutSec

    done = False
    timedOut = False

    while not done:
        # check for the running processes
        runningProcList = findRunningProcesses(processNameList)

        if len(runningProcList) == 0:
            done = True

        elif waitTimeoutSec > 0.0:
            if time.time() > endTime:
                done = True
                timedOut = True
                print "timed out waiting for", runningProcList

        if not done:
            print "waiting for running processes to end:", runningProcList
            time.sleep(10.0)

    return timedOut


class AnalyzerInfo(object):
    def __init__(self, appName = None):
        if appName is None:
            appName = APP_NAME

        self.logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

        try:
            self.driverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, 
                                                        ClientName = appName)
        except:
            self.logger.warn("Failed to connect to the driver!")
            self.driverRpc = None

        if self.driverRpc is None:
            self.logger.error("Instrument is not running!")

        try:
            self.crdsSupervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
                                                             ClientName = appName,
                                                             IsDontCareConnection = False)
        except:
            self.crdsSupervisor = None

        try:
            self.instrManager = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER,
                                                             ClientName = appName)
        except:
            self.instrManager = None

        self._fetchAnalyzerNameAndSerial()
        self._fetchAnalyzerHostSoftwareVersion()

    def _fetchAnalyzerNameAndSerial(self):
        try:
            analyzerId = self.driverRpc.fetchObject("LOGIC_EEPROM")[0]
            self.logger.info("fetchObject[LOGIC_EEPROM] returned '%r'" % analyzerId)
            self.analyzerName = analyzerId["Analyzer"]
            self.analyzerNum = analyzerId["AnalyzerNum"]
            self.chassis = analyzerId["Chassis"]
        except Exception, e:
            self.logger.warn("Exception occurred calling fetchObject[LOGIC_EEPROM]: %r, %r" % (Exception, e))
            self.analyzerName = mdefs.MIGRATION_UNKNOWN_ANALYZER_TYPE
            self.analyzerNum = ""
            self.chassis = mdefs.MIGRATION_UNKNOWN_CHASSIS_TYPE

        self.analyzerId = self.analyzerName + self.analyzerNum

    def _fetchAnalyzerHostSoftwareVersion(self):
        v = ""
        try:
            dV = self.driverRpc.allVersions()
            self.hostSoftwareVersion = dV["host release"]

            klist = dV.keys()
            klist.sort()
            v += "Version strings:\n"
            for k in klist:
                if k != "host release":
                    v += "%s : %s\n" % (k,dV[k])

            self.allVersion = v

        except:
            self.hostSoftwareVersion = "Software version information unavailable"
            self.allVersion = None

    def printAnalyzerNameAndSerial(self):
        print "analyzerId=", self.analyzerId
        print "analyzerName=", self.analyzerName
        print "analyzerNum=", self.analyzerNum
        print "chassis=", self.chassis

    def isInstrumentRunning(self):
        # Look for the Driver, Supervisor, and InstMgr processes
        instProcNames = ["Driver.exe", "Supervisor.exe", "InstMgr.exe"]
        instRunning = True

        for proc in instProcNames:
            if not isProcessRunning(proc):
                instRunning = False

        return instRunning

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

    """
    # cannot use psutil in WinXP/Python 2.5, it is not installed
    # and it is missing from py2exe builds (don't know how to fix this)
    def getPicarroProcesses(self):
        procByPort = {}
        for proc in psutil.process_iter():
            for c in proc.get_connections():
                port = c.local_address[1]
                if 50000 <= port <= 51000:
                    procByPort[port] = proc
        return procByPort
    """

    def waitForPicarroProcessesToEnd(self):
        # "SupervisorLauncher.exe" ?
        processNameList = ["Supervisor.exe", "Controller.exe", "QuickGui.exe",
                           "DataManager.exe", "Autosampler.exe", "Coordinator.exe",
                           "Driver.exe"]
        maxTimeoutSec = 300.0   # 5 min. should be plenty

        self.logger.info("Waiting for Picarro processes to end: %r" % processNameList)

        # This returns True if there are still some running processes (timed out waiting)
        ret = waitForRunningProcessesToEnd(processNameList, maxTimeoutSec)

        if ret is True:
            # timed out, return a list of what's still running
            runningProcList = findRunningProcesses(processNameList)
            self.logger.info("Timed out waiting for some Picarro processes to end!")
            for proc in runningProcList:
                self.logger.info("'%s' is still running." % proc)
        else:
            # processes have all ended, return None (nothing running)
            self.logger.info("No running Picarro processes detected.")
            runningProcList = None

        return runningProcList

    def stopAnalyzerAndDriverShutsdownWindowsTooUgh(self):
        if self.instrManager is not None:
            self.instrManager.INSTMGR_ShutdownRpc(INSTMGR_SHUTDOWN_HOST_AND_DAS)

            self.waitForPicarroProcessesToEnd()

    def stopAnalyzerAndDriver(self):
        # this is the harsh way to kill it off
        # leave the version info as cached
        if self.crdsSupervisor is not None:
            # kill off all of the apps
            # Kill the startup splash screen as well (if it exists)
            self.logger.debug("Executing 'taskkill.exe /IM HostStartup.exe /F'")
            os.system(r'taskkill.exe /IM HostStartup.exe /F')

            # Kill QuickGui if it isn't under Supervisor's supervision
            self.logger.debug("Executing 'taskkill.exe /IM QuickGui.exe /F'")
            os.system(r'taskkill.exe /IM QuickGui.exe /F')

            # Kill Controller if it isn't under Supervisor's supervision
            self.logger.debug("Executing 'taskkill.exe /IM Controller.exe /F'")
            os.system(r'taskkill.exe /IM Controller.exe /F')

            # kill the driver (powerDown=False,stopProtected=True)
            self.logger.debug("Terminating applications from the Supervisor")
            self.crdsSupervisor.TerminateApplications(False, True)

            # wait for everything to shut down
            self.logger.debug("Waiting for Picarro processes to end")
            ret = self.waitForPicarroProcessesToEnd()
        else:
            self.logger.info("Analyzer is not running.")
            ret = None

        # since we're stopping the Analyzer, must reset the driver handle
        # TODO: how do I disconnect these RPC handlers? or is setting them to None
        # sufficient (which should clean them up)?
        self.driverRpc = None
        self.crdsSupervisor = None

        # returns either None (everything is off) or a list of processes still running
        return ret


def main():
    anInfo = AnalyzerInfo()

    print "Analyzer running:  %s" % anInfo.isInstrumentRunning()

    print "Analyzer name:    '%s'" % anInfo.getAnalyzerName()
    print "Analyzer number:  '%s'" % anInfo.getAnalyzerNum()
    print "Analyzer chassis: '%s'" % anInfo.getAnalyzerChassis()
    print "Analyzer software version: '%s'" % anInfo.getAnalyzerSoftwareVersion()
    print ""
    print "Analyzer software version (all): '%s'" % anInfo.getAllSoftwareVersion()

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

    # temporary - find running Picarro processes, then wait
    """
    interval = 5.0

    while True:
        procByPort = anInfo.getPicarroProcesses()

        print "len=%d  procByPort=%r" % (len(procByPort), procByPort)

        time.sleep(interval)
    """



if __name__ == "__main__":
    main()