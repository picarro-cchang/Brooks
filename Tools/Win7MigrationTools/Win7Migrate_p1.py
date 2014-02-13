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
import time
import logging
import ConfigParser
#import wx

from optparse import OptionParser

import Win7MigrationToolsDefs as mdefs
import Win7MigrationUtils as mutils



def findAndValidateDrives(debug=False):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Finding and validating drives for Windows 7 migration backup.")

    # main drive is C:\; get the drive this program is running from (which is the backup partition)
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


def getSupportedAnalyzerTypes(drive):
    # Returns a list of supported analyzer types, using the folder names
    # for all of the installers on the migration drive
    supportedTypes = []
    installerParentDir = os.path.join(drive,
                                      os.path.sep,
                                      mdefs.MIGRATION_TOOLS_FOLDER_NAME,
                                      mdefs.INSTALLER_FOLDER_ROOT_NAME)

    # this returns a list of just the filenames (not the full paths)
    fileList = os.listdir(installerParentDir)

    for item in fileList:
        filename = os.path.join(installerParentDir, item)

        if os.path.isdir(filename):
            supportedTypes.append(item)

    return fileList



class UIMigration(object):
    def __init__(self, instDrive=None,
                 migBackupDrive=None,
                 instDriveName=None,
                 analyzerName=None,
                 analyzerType=None):
        self.instDrive = instDrive
        self.migBackupDrive = migBackupDrive
        self.instDriveName = instDriveName
        self.analyzerName = analyzerName
        self.analyzerType = analyzerType

        if self.instDriveName is None:
            self.instDriveName = ""

        if self.analyzerName is None:
            self.analyzerName = mdefs.MIGRATION_UNKNOWN_ANALYZER_NAME

        if self.analyzerType is None:
            self.analyzerType = mdefs.MIGRATION_UNKNOWN_ANALYZER_TYPE

        # set default new volume name as same as the instrument
        self.newVolumeName = self.instDriveName

        # if it is an empty string, set the default to the analyzer name
        if self.newVolumeName == "":
            self.newVolumeName = self.analyzerName

        self.logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

    def printInfo(self):
        print ""
        print "Instrument drive:       %s" % self.instDrive
        #print "Migration main drive:   %s" % self.migMainDrive
        print "Migration backup drive: %s" % self.migBackupDrive
        print "Analyzer type:          %s" % self.analyzerType

        # TODO: For now, analyzer name doesn't really matter because
        #       we aren't doing anything with it. But if we need it
        #       for naming My Computer then we'll need to display
        #       it and prompt for it if unknown.
        #print "Analyzer name:          %s" % self.analyzerName
        print ""

    def confirmToProceed(self):
        assert self.instDrive
        assert self.migBackupDrive
        assert self.instDriveName

        # TODO: add wx UI for this, for now just use the command line
        self.printInfo()

        # Prompt for an analyzer type if don't have one
        # Build a list of supported types from the folder names containing the installers
        # e.g., folders are: 
        #     F:\Win7MigrationTools\PicarroInstallers\CFADS
        #     F:\Win7MigrationTools\PicarroInstallers\CFFDS
        #     etc.
        supportedTypes = getSupportedAnalyzerTypes(self.migBackupDrive)
        haveAnalyzerType = False
        userUpdatedType = False

        if self.analyzerType in supportedTypes:
            haveAnalyzerType = True

        # This forces the user to enter a valid analyzer type
        while not haveAnalyzerType:
            print ""
            print "Supported analyzer types for migration:"
            print "    %s" % supportedTypes
            print ""

            inputStr = raw_input("Please enter your analyzer type, or Q to quit: ")
            inputStr = inputStr.upper()

            if inputStr in supportedTypes:
                haveAnalyzerType = True
                userUpdatedType = True
                self.analyzerType = inputStr
                print ""
            elif inputStr == "Q":
                print ""
                self.logger.info("Win7 migration aborted by user (no valid analyzer type was entered).")
                return False
            else:
                print "Unsupported analyzer type '%s'!" % inputStr

        # prompt for an analyzer name if not set
        #if self.analyzerName == mdefs.MIGRATION_UNKNOWN_ANALYZER_NAME:
        #    pass

        # print a summary of instrument info one more time
        self.printInfo()
        inputStr = raw_input("Continue with migration to Windows 7? Y to continue, N to abort: ")
        inputStr = inputStr.upper()

        if inputStr != "Y":
            self.logger.info("Win7 migration aborted by user (backup)!")
            return False

        if userUpdatedType is True:
            self.logger.info("User entered analyzer type = '%s'" % self.analyzerType)

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

    def getAnalyzerType(self):
        return self.analyzerType

    def getAnalyzerName(self):
        return self.analyzerName

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
        done = False
        while done is False:
            runningProcessesList = anInfo.stopAnalyzerAndDriver()
            if runningProcessesList is None:
                done = True
            else:
                print "%r still running! Quit the application, or open the Task Manager or Process Explorer and kill the process(es)." % runningProcessesList
                raw_input("Hit the <Enter> key after you have done this: ")

    else:
        logger.info("(debug) Skipped stopping software and driver.")


def promptUserToStopSoftwareAndDriver():
    print ""
    print "Please stop the software and driver if it is running."
    print ""
    print "Double-click the Diagnostics folder on the desktop, then"
    print "run the Stop Instrument application in that folder."
    print "Choose the second selection, 'Stop software and driver',"
    print "then click the Stop button."
    print ""
    print ""

    raw_input("After everything has shutdown, type Y to continue: ")



def shutdownWindows(debug=False):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

    logger.info("Shutting down Windows.")
    # more shutdown options we may want to use
    # /c "message" can be used to show a message, max 127 chars
    # /t xx  sets timer for shutdown in xx seconds, default is 20 seconds

    if debug is False:
        command = "shutdown /s /f -t 30"
        logger.info("Windows shutdown with command = '%s'" % command)
        mutils.runCommand(command)
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
            mutils.runCommand(command)
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


def backupFiles(fromDrive, toDrive, backupConfigsOnly):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

    if not backupConfigsOnly:
        logger.info("Backing up configuration files, data, and software from '%s' to '%s'." % (fromDrive, toDrive))
    else:
        logger.info("Backing up configuration files only, from '%s' to '%s'." % (fromDrive, toDrive))

    # skip bzr files and folders
    # TODO: Any chance of ending up with unins000.dat or unins000.exe? If so, exclude them too.
    #       Need to use regular expressions to find them since can end up with several.
    excludeDirs = [".bzr"]
    excludeFiles = [".bzrignore"]

    # construct list of folders to backup
    foldersToBackupList = mdefs.CONFIG_FOLDERS_TO_BACKUP_LIST

    if not backupConfigsOnly:
        for folder in mdefs.DATA_FOLDERS_TO_BACKUP_LIST:
            foldersToBackupList.append(folder)

    # Back up the folders to the 2nd partition
    for folder in foldersToBackupList:
        folder = os.path.normpath(folder)

        if not os.path.isdir(folder):
            # folder doesn't exist on WinXP host drive
            # for now just skip it (don't create the folder on the backup drive)
            # TODO: is this what we want to do ultimately?
            logger.warning("Cannot backup '%s' as it does not exist on WinXP instrument drive!" % folder)
            continue

        for dirpath, fromFilename in mutils.osWalkSkip(folder, excludeDirs, excludeFiles):
            # construct the destination file path for the copy
            toFilename = os.path.join(toDrive,
                                      os.path.sep,
                                      mdefs.BACKUP_XP_FOLDER_ROOT_NAME) + os.path.splitdrive(fromFilename)[1]

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


def doMigrate(options):
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
    # Find and validate the instrument main drive and the migration drive backup partition
    instDrive, migBackupDrive = findAndValidateDrives(options.debug)

    root.info("instrument drive='%s', migration backup drive ='%s'" %
              (instDrive, migBackupDrive))

    if instDrive is None or migBackupDrive is None:
        # error should already have been logged, bail out
        # TODO: pop an error dialog and direct user to the error log
        errMsg = "Drive validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)

    # Windows validation (5= WinXP)
    ret = mutils.validateWindowsVersion(5, options.debug)

    if not ret:
        errMsg = "Windows OS validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)

    """
    # Python validation (should be Python 2.5). Can't do it this
    # way for compiled code (it will be the version of Python that
    # it was compiled with).
    #
    # Alternatively we could compile and execute
    # a script at run-time. Since it doesn't matter all that much
    # (just a sanity check), skipping it for now.
    ret = mutils.validatePythonVersion("2.5", options.debug)

    if not ret:
        errMsg = "Python validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)
    """

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

    unknownAnalyzer = False

    if analyzerType == mdefs.MIGRATION_UNKNOWN_ANALYZER_TYPE:
        # analyzerType should be something like CFKADS
        # used in part 2 to find an installer
        # log it -- most likely there is a Pyro version mismatch so
        # we can't actually communicate with the instrument
        #
        # we'll prompt the user below for analyzer type, software version, etc.
        unknownAnalyzer = True
        root.info("Analyzer type unknown, prompting user to enter it")

    # Report drive letters and other info to user, and ask for confirmation
    # to proceed.
    #
    instDriveName = mutils.getVolumeName(instDrive)

    root.info("Instrument drive volume name = '%s'" % instDriveName)

    uiMig = UIMigration(instDrive=instDrive,
                        migBackupDrive=migBackupDrive,
                        instDriveName=instDriveName,
                        analyzerName=analyzerName,
                        analyzerType=analyzerType)

    # Ask for user confirmation to continue. This also prompts for analyzer type
    # (CFKADS, etc.) [future: prompt for name (CFKADS2133)]
    ret = uiMig.confirmToProceed()

    if not ret:
        errMsg = "Migration aborted. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)

     # Get the volume name the user wants to use for the Win7 boot drive
    win7DriveName = uiMig.getNewVolumeName()

    # Get the analyzer type and name, we may have needed to prompt the user for it
    analyzerType = uiMig.getAnalyzerType()
    analyzerName = uiMig.getAnalyzerName()

    # Save some config info in a file for migration part 2.
    defaults = {}
    cp = ConfigParser.ConfigParser(defaults)
    cp.add_section(mdefs.MIGRATION_CONFIG_SECTION)
    cp.set(mdefs.MIGRATION_CONFIG_SECTION, mdefs.VOLUME_NAME, win7DriveName)
    cp.set(mdefs.MIGRATION_CONFIG_SECTION, mdefs.ANALYZER_TYPE, analyzerType)
    cp.set(mdefs.MIGRATION_CONFIG_SECTION, mdefs.ANALYZER_NAME, analyzerName)

    # TODO: save off mdefs.COMPUTER_NAME, mdefs.MY_COMPUTER_ICON_NAME
    root.warning("Saving off computer name and name from My Computer needs to be implemented!")

    filename = os.path.join(os.getcwd(), mdefs.MIGRATION_CONFIG_FILENAME)
    with open(filename, "w") as f:
        cp.write(f)

    # Must shutdown the software and driver before backing up.
    # Will not return until nothing is running (prompts user to
    # kill from the TaskManager if times out waiting)
    # The user will need to do this if this is an unknown analyzer
    # (likely because Pyro versions don't match, the following WILL crash)
    if unknownAnalyzer is False:
        stopSoftwareAndDriver(anInfo, options.debug)
    else:
        promptUserToStopSoftwareAndDriver()

    # ==== Backup ====
    #
    # Backup files from XP drive to Win7 drive partition 2.
    backupFiles(instDrive, migBackupDrive, options.backupConfigsOnly)

    # TODO: Back up autosampler (.exe, config files, etc.)
    root.warning("Autosampler backup needs to be implemented!")

    # TODO: Back up other modules config files that aren't part of configs
    root.warning("Backup of config files for peripherals not using standard config folders needs to be implemented!")

    # ==== Shut down ====
    msg = "Part 1 of migration from WinXP to Win7 completed successfully!"
    root.info(msg)

    # TODO: Show instructions for what to do next (remove the WinXP drive and
    #       install the Win7 drive).
    root.warning("Instructions directing user to swap drives needs to be implemented!")

    print ""
    print "%s" % msg
    #showSuccessDialog(msg)

    # Shut down Windows unless the secret option was used to not do a shutdown.
    # Debug will shut it down, but with a longer timeout to give a chance to
    # enter a 'shutdown -a' command.
    if options.noShutdownWindows:
        root.info("Windows not getting shut down due to --noShutdownWindows command line option.")
    else:
        shutdownWindows(options.debug)


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

    parser.add_option('--backupConfigsOnly', dest="backupConfigsOnly",
                      action='store_true', default=False,
                      help=('Backup the config files only, no user data files or logs.'))

    parser.add_option('--noShutdownWindows', dest="noShutdownWindows",
                      action='store_true', default=False,
                      help=("Don't shutdown windows after this script finishes (default is to shut down Windows)."))

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

    doMigrate(options)


if __name__ == "__main__":
    main()

