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
# Check out the unit tests especially log_test18.py, log_test20.py and log_test21.py which have good examples on using Filters.
#
# History
#
# 2014-01-30  tw  Initial version.

import os
import sys
import shutil
import subprocess
import time
import win32api
import logging
import wx

from optparse import OptionParser

import Win7MigrationToolsDefs as mdefs


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
    print "runCommand: '%s'" % command

    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)

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
    ret = runCommand("label %s %s" % (drive, volumeName))

    print "setVolumeName: ret='%s'" % ret
    print "ret=%r" % ret

    for line in ret:
        print "line='%s'" % line
    return ret


def findAndValidateDrives(debug=False):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.debug("Finding and validating drives.")

    # main drive is C:\; get the drive this program is running from (which should be partition 1)
    instDrive = "C:"
    hostExeDir = os.path.normpath("C:/Picarro/g2000/HostExe")
    migMainDrive = os.path.splitdrive(os.getcwd())[0]      # returns something like F:

    # get drive this app is running from (should be running from the 1st partition of the migration drive)
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]

    migBackupDrive = None
    foundNamedDrive = []

    for drive in drives:
        try:
            # example: drive = "C:\\" (requires backslash)
            # returns tuple with file system info, volume name is the first value in the tuple
            driveInfo = win32api.GetVolumeInformation(drive)

            if driveInfo[0] == mdefs.PARTITION_2_VOLUME_NAME:
                # save this drive letter and colon (strip off the ending backslash)
                foundNamedDrive.append(drive[:2])

        except Exception, e:
            # Ignore all exceptions. I know we will get some (e.g., a DVD drive that doesn't have any media, etc.)
            # Not very useful to even bother reporting these.
            #logger.debug("An exception occurred getting info for drive '%s' (ignored). Exception=%r, e=%r" % (drive, Exception, e))
            pass

    if len(foundNamedDrive) == 1:
        # there should only be 1 drive with the required volume name
        migBackupDrive = foundNamedDrive[0]
        logger.debug("Found migration drive used as backup destination (%s)" % migBackupDrive)
    else:
        # log this as an error
        if len(foundNamedDrive) == 0:
            logger.error("No drives found with the volume name '%s'" % mdefs.PARTITION_2_VOLUME_NAME)
        else:
            logger.error("Multiple drives found with the volume name '%s', drives = %r" % (mdefs.PARTITION_2_VOLUME_NAME, foundNamedDrive))

    # validate the instrument drive, there should be a HostExe folder in the expected Picarro path
    if not os.path.isdir(hostExeDir):
        instDrive = None
        logger.error("Picarro analyzer software does not appear to be installed, dir does not exist (%s)." % hostExeDir)

    # validate the current drive by looking for the Win7MigrationTools folder on the drive
    # splitdrive() left us with just the drive letter and colon so put the separator back in
    migMainToolsDir = os.path.join(migMainDrive, os.sep, mdefs.MIGRATION_TOOLS_FOLDER_NAME)

    if not os.path.isdir(migMainToolsDir):
        migMainDrive = None
        logger.error("Failed to validate migration drive, expected dir does not exist! (%s)" % migMainToolsDir)

    # TODO: validate 2nd partition by looking for some known folders/files that should be installed

    fSuccess = True
    if instDrive is None or migMainDrive is None or migBackupDrive is None:
        fSuccess = False
    logger.debug("Drive validation done, fSuccess=%s." % fSuccess)

    return instDrive, migMainDrive, migBackupDrive


class UIMigration(object):
    def __init__(self, instDrive=None,
                 migMainDrive=None,
                 migBackupDrive=None,
                 instDriveName=None):
        self.instDrive = instDrive
        self.migMainDrive = migMainDrive
        self.migBackupDrive = migBackupDrive
        self.instDriveName = instDriveName

        if self.instDriveName is None:
            self.instDriveName = ""

        # set default new volume name as same as the instrument
        self.newVolumeName = self.instDriveName

        self.logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

    def confirmToProceed(self):
        assert self.instDrive
        assert self.migMainDrive
        assert self.migBackupDrive
        assert self.instDriveName

        # TODO: add wx UI for this, for now just use the command line
        print ""
        print "Instrument drive:       %s" % self.instDrive
        print "Migration main drive:   %s" % self.migMainDrive
        print "Migration backup drive: %s" % self.migBackupDrive
        print ""
        inputStr = raw_input("Continue with migration to Windows 7? Y to continue, N to abort: ")
        inputStr = inputStr.upper()

        if inputStr != "Y":
            self.logger.info("Win7 migration aborted by user (backup)!")
            return False

        # Prompt for new Win7 volume name
        haveWin7DriveName = False
        while not haveWin7DriveName:
            print "in outer while loop"
            while True:
                print ""
                print "New Win7 boot drive name:  %s" % self.newVolumeName
                inputStr = raw_input("Is the new Win7 drive name correct? Y (yes) / N (no)/ A (abort): ")
                inputStr = inputStr.upper()

                if inputStr == "A":
                    # Abort
                    self.logger.info("Win7 migration aborted by user (configuring Win7 drive name)!")
                    return False

                elif inputStr == "N":
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



def validatePicarroSystem(debug=False):
    # Confirm the Analyzer software is running and get the analyzer name.
    # This is another system validation.
    # We'll use it later as a default for the new hard drive. We may need to
    # save it off somewhere since a different script will be running when that
    # happens. Or just name the volume now with the current name from WinXP?
    return True


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

            try:
                # copy2 retains the last access and modification times as well as permissions
                shutil.copy2(fromFilename, toFilename)
                logger.info("Copy '%s' to '%s'" % (fromFilename, toFilename))

            except Exception, e:
                logger.error("Copy failed, '%r' during copy '%s' to '%s'" % (e, fromFilename, toFilename))

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

Win7 migration utility part 1.
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

    root.info("***** Win7 migration part 1 started. *****")

    # ==== Validation ====
    #
    # Find and validate the instrument main drive and both migration drive partitions
    instDrive, migMainDrive, migBackupDrive = findAndValidateDrives(options.debug)

    root.info("instrument drive='%s', migration drive partition 1='%s', migration drive partition 2='%s'" %
              (instDrive, migMainDrive, migBackupDrive))

    if instDrive is None or migMainDrive is None or migBackupDrive is None:
        # error should already have been logged, bail out
        # TODO: pop an error dialog and direct user to the error log
        errMsg = "Drive validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)

    # Confirm the Analyzer software is running, get the analyzer name, etc.
    ret = validatePicarroSystem(options.debug)

    if not ret:
        errMsg = "System validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)

    # Report drive letters and other info to user, and ask for confirmation
    # to proceed.
    #
    # TODO: Ask for volume name to use for new main Win7 drive. Default to
    #       same volume name as XP drive.
    instDriveName = getVolumeName(instDrive)

    root.info("instrument drive volume name = '%s" % instDriveName)

    uiMig = UIMigration(instDrive=instDrive,
                        migMainDrive=migMainDrive,
                        migBackupDrive=migBackupDrive,
                        instDriveName=instDriveName)

    ret = uiMig.confirmToProceed()

    if not ret:
        errMsg = "Migration aborted. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)


    # ==== Backup ====
    #

    # Backup files from XP drive to Win7 drive partition 2.
    ret = backupFiles(instDrive, migBackupDrive)

    # Set the volume name for the migration main (Win7 boot) drive
    win7DriveName = uiMig.getNewVolumeName()
    result = setVolumeName(migMainDrive, win7DriveName)

    msg = "Part 1 of migration from WinXP to Win7 completed successfully!"
    root.info(msg)

    print ""
    print "%s" % msg
    #showSuccessDialog(msg)

    # TODO: Show prompt that the instrument will now be shut down. Stop the
    #       instrument and driver, and shut down Windows.

    # TODO: Show instructions for what to do next (remove the WinXP drive and
    #       install the Win7 drive).


if __name__ == "__main__":
    main()

