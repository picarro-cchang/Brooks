# Win7Migrate_p1.py
#
# Part 1 of the Win7 migration. Backs up config files, data, and Analyzer host software
# onto the 2nd partition, then preps the system for part 2 (install software and
# restore specific config files).
# 
# If you change this utility, don't forget to bump the common version number in
# Win7MigrationToolsDefs.py
#
# Notes:
#
# http://www.red-dove.com/python_logging.html#download
# Check out the unit tests especially log_test18.py, log_test20.py and log_test21.py which have good examples on using Filters.
#
# History
#
# 2014-01-30  tw  Initial version.
from __future__ import with_statement

import os
import sys
import shutil
import subprocess
import time
import win32api
import logging
import ConfigParser
#import wx

from optparse import OptionParser

import Win7MigrationToolsDefs as mdefs
import Win7MigrationUtils as mutils


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

    # I think we need to use this to get the output:
    # stdout_value = p.communicate()
    # or this? stdout_value, stderr_value = p.communicate()
    # print "stdout:", repr(stdout_value)
    return iter(p.stdout.readline, b'')


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
    # Not clear what is returned
    ret = runCommand("label %s %s" % (drive, volumeName))

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


def validateWindowsVersion(debug=False):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Validating Windows version.")

    # Expect this script to be running on Windows XP
    if sys.getwindowsversion().major != int(5):
        if debug is False:
            logger.error("Current operating system is not Windows XP!")
            validWinVersion = False
        else:
            logger.info("(debug) Current operating system is not Windows XP, ignoring.")
            validWinVersion = True
    else:
        logger.info("Validated operating system, running Windows XP.")
        validWinVersion = True

    return validWinVersion


def validatePythonVersion(debug=False):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Validating Python version.")

    pythonVer = str(sys.version_info.major) + "." + str(sys.version_info.minor)

    if pythonVer != "2.5":
        if debug is False:
            logger.error("Current Python version is %s, expected 2.5!" % pythonVer)
            validPythonVersion = False
        else:
            logger.error("(debug) Running Python version %s, expected 2.5, ignoring" % pythonVer)
            validPythonVersion = True
    else:
        logger.info("Validated Python, current version is 2.5")
        validPythonVersion = True

    return validPythonVersion


def findAndValidateDrives(debug=False):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Finding and validating drives.")

    # main drive is C:\; get the drive this program is running from (which should be partition 1)
    instDrive = "C:"
    hostExeDir = os.path.normpath("C:/Picarro/g2000/HostExe")

    # validate the instrument drive, there should be a HostExe folder in the expected Picarro path
    if not os.path.isdir(hostExeDir):
        instDrive = None
        logger.error("Picarro analyzer software does not appear to be installed, dir does not exist (%s)." % hostExeDir)

    # this program is running from the backup drive
    # returns something like F:
    migBackupDrive = os.path.splitdrive(os.getcwd())[0]

    """
    # This is unnecessary, we should be able to run from wherever this is installed.
    # validate the current drive by looking for the Win7MigrationTools folder on the drive
    # splitdrive() left us with just the drive letter and colon so put the separator back in
    migToolsDir = os.path.join(migBackupDrive, os.sep, mdefs.MIGRATION_TOOLS_FOLDER_NAME)

    if not os.path.isdir(migToolsDir):
        migBackupDrive = None
        logger.error("Failed to validate migration drive, expected dir does not exist! (%s)" % migToolsDir)
    """

    fSuccess = True
    if instDrive is None or migBackupDrive is None:
        fSuccess = False
    logger.info("Drive validation done, fSuccess=%s." % fSuccess)

    return instDrive, migBackupDrive


class UIMigration(object):
    def __init__(self, instDrive=None,
                 migBackupDrive=None,
                 instDriveName=None,
                 analyzerName=None):
        self.instDrive = instDrive
        self.migBackupDrive = migBackupDrive
        self.instDriveName = instDriveName
        self.analyzerName = analyzerName

        if self.instDriveName is None:
            self.instDriveName = ""

        if self.analyzerName is None:
            self.analyzerName = ""

        # set default new volume name as same as the instrument
        self.newVolumeName = self.instDriveName

        # if it is an empty string, set the default to the analyzer name
        if self.newVolumeName == "":
            self.newVolumeName = self.analyzerName

        self.logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

    def confirmToProceed(self):
        assert self.instDrive
        assert self.migBackupDrive
        assert self.instDriveName

        # TODO: add wx UI for this, for now just use the command line
        print ""
        print "Instrument drive:       %s" % self.instDrive
        #print "Migration main drive:   %s" % self.migMainDrive
        print "Migration backup drive: %s" % self.migBackupDrive

        if self.analyzerName != "":
            print "Analyzer name:          %s" % self.analyzerName
        print ""

        inputStr = raw_input("Continue with migration to Windows 7? Y to continue, N to abort: ")
        inputStr = inputStr.upper()

        if inputStr != "Y":
            self.logger.info("Win7 migration aborted by user (backup)!")
            return False

        # Prompt for new Win7 volume name
        haveWin7DriveName = False
        while not haveWin7DriveName:
            #print "in outer while loop"
            while True:
                print ""
                print "New Win7 boot drive name:  %s" % self.newVolumeName
                inputStr = raw_input("Is the new Win7 drive name correct? Y (yes) / N (no): ")
                inputStr = inputStr.upper()

                if inputStr == "N":
                    # Allow user to enter a different name for the drive
                    inputStr = raw_input("Enter the name for your new Windows 7 boot drive: ")
                    print "inputStr='%s'" % inputStr
                    self.newVolumeName = inputStr

                elif inputStr == "Y":
                    # User approved the new drive name, done
                    haveWin7DriveName = True
                    break

        self.logger.info("New Win7 boot drive volume name: '%s'" % self.newVolumeName)

        # Done, user has confirmed to continue with backup
        return True

    def getNewVolumeName(self):
        if self.newVolumeName is None:
            return ""
        else:
            return self.newVolumeName


def validatePicarroSystem(anInfo, debug=False):
    # Confirm the Analyzer software is running.
    assert anInfo

    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

    ret = anInfo.isInstrumentRunning()
    if ret is False:
        logger.info("Analyzer software is not running!")

        if debug is True:
            logger.info("(debug) Skipped analyzer software running check")
            ret = True
    else:
        logger.info("Validated instrument, software is running.")

    return ret


def stopSoftwareAndDriver(anInfo, debug=False):
    assert anInfo

    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Stopping the software and driver.")

    if not debug:
        anInfo.stopAnalyzerAndDriver(debug)
    else:
        logger.info("(debug) Skipped stopping software and driver.")


def shutdownWindows(debug=False):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

    logger.info("Shutting down Windows.")
    # more shutdown options we may want to use
    # /c "message" can be used to show a message, max 127 chars
    # /t xx  sets timer for shutdown in xx seconds, default is 20 seconds

    if debug is False:
        command = "shutdown /s /f -t 30"
        logger.info("Windows shutdown with command = '%s'" % command)
        runCommand(command)
        return True

    else:
        # for debug give the user a chance to bail out
        print ""
        response = raw_input("(debug) Do you really want to shut down Windows? Y or N: ")
        response = response.upper()

        if response == "Y":
            # set the shutdown timer to 2 minutes
            command = "shutdown /s /f -t 120"
            logger.info("(debug) Shutting down Windows with command = '%s'" % command)
            logger.info("(debug) You can abort the shutdown using 'shutdown -a'")
            runCommand(command)
            return True
        else:
            logger.info("(debug) Windows shutdown skipped.")
            return False


"""
def promptToRemoveMigrationDrives(migMainDrive=None,
                                  migBackupDrive=None):
    assert migMainDrive
    assert migBackupDrive

    print ""
    print "You must use Safely Remove Hardware in the System Tray to unmount the"
    print ""
    print "IMPORTANT: Be sure to remove both partitions: %s and %s" % (migMainDrive, migBackupDrive)
    print ""
"""


def backupFiles(fromDrive, toDrive):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Backing up configuration files, data, and software from '%s' to '%s'." % (fromDrive, toDrive))

    # skip bzr files and folders
    # TODO: Any chance of ending up with unins000.dat or unins000.exe? Exclude them too.
    excludeDirs = [".bzr"]
    excludeFiles = [".bzrignore"]

    # Back up the folders to the 2nd partition
    for folder in mdefs.FOLDERS_TO_BACKUP_LIST:
        folder = os.path.normpath(folder)

        if not os.path.isdir(folder):
            # folder doesn't exist on WinXP host drive
            # for now just skip it (don't create the folder on the backup drive)
            # TODO: is this what we want to do ultimately?
            logger.warning("Cannot backup '%s' as it does not exist on WinXP instrument drive!" % folder)
            continue

        for dirpath, fromFilename in osWalkSkip(folder, excludeDirs, excludeFiles):
            # construct the destination file path for the copy
            toFilename = os.path.join(toDrive,
                                      os.path.sep,
                                      mdefs.BACKUP_FOLDER_ROOT_NAME) + os.path.splitdrive(fromFilename)[1]

            # create the destination dir if it doesn't already exist
            targetDir = os.path.split(toFilename)[0]
            if not os.path.isdir(targetDir):
                os.makedirs(targetDir)

            # We intentionally do not catch any file copy exceptions. The
            # last copy message in the log should indicate which file it
            # barfed on, if this fails.
            # copy2 retains the last access and modification times as well as permissions
            logger.info("Copying '%s' to '%s'" % (fromFilename, toFilename))
            shutil.copy2(fromFilename, toFilename)

    logger.debug("Done backing up configuration files, data, and software.")


"""
# for this to work I have to create a wx.App object
# frame title for dialogs
#print mdefs.MIGRATION_DIALOG_CAPTION
#title = mdefs.MIGRATION_DIALOG_CAPTION % "1"

def showErrorDialog(msg):
    title = mdefs.MIGRATION_DIALOG_CAPTION % "1"
    wx.MessageBox(msg, caption=title, style=wx.OK | wx.ICON_ERROR)


def showSuccessDialog(msg):
    title = mdefs.MIGRATION_DIALOG_CAPTION
    wx.MessageBox(msg, caption=title, style=wx.OK | wx.ICON_INFORMATION)
"""


def main():
    usage = """
%prog [options]

Win7 migration utility part 1 (back up).
"""

    parser = OptionParser(usage=usage)

    parser.add_option('-v', '--version', dest='version', action='store_true',
                      default=False, help=('Report the version number.'))

    parser.add_option('--debug', dest='debug', action='store_true',
                      default=False, help=('Enables debugging.'))

    parser.add_option('--logLevel', dest='logLevel',
                      default=None, help=('Set logging level.\n',
                                          '0  = NOTSET',
                                          '10 = DEBUG',
                                          '20 = INFO'
                                          '30 = WARNING',
                                          '40 = ERROR',
                                          '50 = CRITICAL'))

    parser.add_option('--logFilename', '--logFile', dest='logFilename',
                      default=None, help=('Output logging information to the specified filename in addition to stdout.'))

    parser.add_option('--logToNewFile', dest='logToNewFile', action='store_true',
                      default=False, help=('Resets the log file if it exists. Default is to append to the existing file.'))

    parser.add_option('--localTime', dest='localTime', action='store_true',
                      default=False, help=('Log timestamps in local time (default is GMT).'))

    options, _ = parser.parse_args()

    if options.version is True:
        print mdefs.MIGRATION_TOOLS_VERSION
        sys.exit(0)

    # Set up logging stuff
    if options.logLevel is None:
        logLevel = logging.INFO
    else:
        # TODO: would be nice support string args here (e.g. "DEBUG" or "debug", etc.)
        logLevel = int(options.logLevel)

    handler = logging.StreamHandler()   # default= write to sys.stderr

    if logLevel >= logging.INFO:
        fmtLocal = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
        fmtGmt = logging.Formatter("%(asctime)sZ %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    else:
        # debug level includes filename and line number in log output
        fmtLocal = logging.Formatter("%(asctime)s %(filename)s, line=%(lineno)d: %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
        fmtGmt = logging.Formatter("%(asctime)sZ %(filename)s, line=%(lineno)d: %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")

    fmtGmt.converter = time.gmtime
    fmt = fmtGmt

    if options.localTime is True:
        fmt = fmtLocal

    handler.setFormatter(fmt)

    root = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

    root.setLevel(logLevel)
    root.addHandler(handler)

    # Always log to a file as well as stdout
    if options.logFilename is None:
        if options.localTime is True:
            logFilename = time.strftime(mdefs.MIGRATION_TOOLS_LOGFILENAME_BASE)
            logFilename = logFilename + ".log"
        else:
            logFilename = time.strftime(mdefs.MIGRATION_TOOLS_LOGFILENAME_BASE, time.gmtime())
            logFilename = logFilename + "Z.log"

        # TODO: append this base filename to a drive and folder
        #       should this go on the new drive partition 1? or partition 2?
    else:
        # Filename specified on the command line, we still run it through strftime
        if options.localTime is True:
            logFilename = time.strftime(options.logFilename)
        else:
            logFilename = time.strftime(options.logFilename, time.gmtime())

    # set a handler for logging to a file
    mode = 'a'
    if options.logToNewFile is True:
        mode = 'w'

    handlerFile = logging.FileHandler(logFilename, mode)
    handlerFile.setFormatter(fmt)
    root.addHandler(handlerFile)

    root.info("***** Win7 migration part 1 (back up) started. *****")

    # ==== Validation ====
    #
    # Find and validate the instrument main drive and both migration drive partitions
    instDrive, migBackupDrive = findAndValidateDrives(options.debug)

    root.info("instrument drive='%s', migration backup partition ='%s'" %
              (instDrive, migBackupDrive))

    if instDrive is None or migBackupDrive is None:
        # error should already have been logged, bail out
        # TODO: pop an error dialog and direct user to the error log
        errMsg = "Drive validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)

    # Windows validation (should be WinXP)
    ret = validateWindowsVersion(options.debug)

    if not ret:
        errMsg = "Windows OS validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)

    # Python validation (should be Python 2.5)
    ret = validatePythonVersion(options.debug)

    if not ret:
        errMsg = "Python validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)

    anInfo = mutils.AnalyzerInfo()

    # Confirm the Analyzer software is running, get the analyzer name, etc.
    ret = validatePicarroSystem(anInfo, options.debug)

    if not ret:
        errMsg = "System validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)

    analyzerName = anInfo.getAnalyzerNameAndNum()
    analyzerType = anInfo.getAnalyzerName()

    if options.debug is True:
        if analyzerType == "Unknown":
            # hack for my testing without an instrument
            analyzerType = "CFKADS"
            analyzerName = "CFKADS9999"
            root.info("(debug) Using pseudo instrument name '%s'" % analyzerName)

    # Report drive letters and other info to user, and ask for confirmation
    # to proceed.
    #
    # TODO: Ask for volume name to use for new main Win7 drive. Default to
    #       same volume name as XP drive.
    instDriveName = getVolumeName(instDrive)

    root.info("Instrument drive volume name = '%s'" % instDriveName)

    uiMig = UIMigration(instDrive=instDrive,
                        migBackupDrive=migBackupDrive,
                        instDriveName=instDriveName,
                        analyzerName=analyzerName)

    ret = uiMig.confirmToProceed()

    if not ret:
        errMsg = "Migration aborted. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1) 

    # Must shutdown the software and driver before backing up
    isRunning = stopSoftwareAndDriver(anInfo, options.debug)

    # ==== Backup ====
    #
    # Backup files from XP drive to Win7 drive partition 2.
    ret = backupFiles(instDrive, migBackupDrive)

    # TODO: Back up autosampler (.exe, config files, etc.)
    root.warning("Autosampler backup needs to be implemented!")

    # TODO: Back up other modules config files that aren't part of configs
    root.warning("Backup of other config files for misc. modules needs to be implemented!")

    # Get the volume name the user wants to use for the Win7 boot drive
    win7DriveName = uiMig.getNewVolumeName()

    #ret = setVolumeName(migMainDrive, win7DriveName)    # this logs the results

    # use win7DriveName and analyzerType to save off new volume name
    # and analyzer type for running the installer
    #
    # Write a simple config file with key/value entries for win7DriveName
    # and analyzerType to be used in migration part 2.
    # Could generate a .py script that gets loaded and compiled at run-time
    # (as this will be a compiled script) but writing a config file works too.
    defaults = {}
    cp = ConfigParser.ConfigParser(defaults)
    cp.add_section(mdefs.CONFIG_SECTION)
    cp.set(mdefs.CONFIG_SECTION, mdefs.VOLUME_NAME, win7DriveName)
    cp.set(mdefs.CONFIG_SECTION, mdefs.ANALYZER_TYPE, analyzerType)
    cp.set(mdefs.CONFIG_SECTION, mdefs.ANALYZER_NAME, analyzerName)

    filename = os.path.join(os.getcwd(), mdefs.CONFIG_FILENAME)
    with open(filename, "w") as f:
        cp.write(f)

    # ==== Shut down ====
    msg = "Part 1 of migration from WinXP to Win7 completed successfully!"
    root.info(msg)

    # TODO: Show instructions for what to do next (remove the WinXP drive and
    #       install the Win7 drive).
    #root.warning("Instructions for install step need to be implemented!")

    print ""
    print "%s" % msg
    #showSuccessDialog(msg)

    # Shut down Windows.
    shutdownWindows(options.debug)


if __name__ == "__main__":
    main()

