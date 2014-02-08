# Win7Migrate_p2.py
#
# Part 2 of migration tools for WinXP to Win7
#
# Runs the installer (or at least suggests one?)
# Part 1 needs to save off the instrument type so this script
# can find the recommended installer.

import os
import sys
import shutil
import subprocess
import time
#import win32api
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

    # validate the instrument drive, there should not yet be a HostExe folder in the expected Picarro path
    if os.path.isdir(hostExeDir):
        instDrive = None
        logger.error("Picarro analyzer software is already installed, dir exists (%s)." % hostExeDir)

    # this program is running from the backup drive
    # returns something like F:
    migBackupDrive = os.path.splitdrive(os.getcwd())[0]

    fSuccess = True
    if instDrive is None or migBackupDrive is None:
        fSuccess = False
    logger.info("Drive validation done, fSuccess=%s." % fSuccess)

    return instDrive, migBackupDrive


def osGetInstallers(root, filenamePrefix):
    """
    Enumerator that walks through files under a root folder. Returns full dir path
    and filename path for any files that match filenamePrefix.
    """
    # convert to lowercase for comparison
    filenamePrefix = filenamePrefix.lower()

    for dirpath, dirnames, filenames in os.walk(root):
        for edir in dirnames:
            dirnames.remove(edir)

        for efile in filenames:
            # use lowercase for comparison
            efile = efile.lower()
            ix = efile.find(filenamePrefix)

            # eliminate files that don't match the prefix
            if ix != 0:
                filenames.remove(efile)

        # return the full directory and full filename paths
        for filename in filenames:
            yield dirpath, os.path.join(dirpath, filename)


def findInstaller(analyzerType):
    """
    Returns the installer filename (full path) for the analyzer type, or None
    on error (none or more than one found)
    """
    # The PicarroInstallers folder contains subfolders named by
    # instrument type.
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Preparing to run installer for analyzer type '%s'." % analyzerType)

    curDir = os.getcwd()
    installerDir = os.path.join(curDir, mdefs.INSTALLER_FOLDER_ROOT_NAME)

    if not os.path.isdir(installerDir):
        logger.error("Installer folder for analyzer type '%s' does not exist, aborting. Please contact Picarro for further assistance." % analyzerType)
        return None

    # Look in the folder for a filename that begins with "setup_<analyzerType>_".
    # There should be exactly one file there. Skip any directories within the folder
    # (shouldn't be any there anyway).
    installerList = []

    prefix = "setup_%s_" % analyzerType
    for dirpath, filename in osGetInstallers(installerDir, prefix):
        installerList.append(os.path.join(dirpath, filename))

    if len(installerList) == 0:
        logger.error("No installer found in '%s' for analyzer type '%s'" % (installerDir, analyzerType))
        return None

    elif len(installerList) > 1:
        logger.error("More than one installer found in '%s' for analyzer type '%s'" % (installerDir, analyzerType))
        return None

    # return the filename
    return installerList[0]


def runInstaller(installerName):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Running installer '%s'." % installerName)
    retCode = subprocess.call([installerName])

    # retCode is 2 on Cancel, 0 on success
    if retCode != 0:
        logger.info("Installer returned error code %d" % retCode)
        return False
    else:
        return True


def isCleanInstall():
    installerFolders = ["C:/Picarro/g2000/AppConfig",
                        "C:/Picarro/g2000/CommonConfig",
                        "C:/Picarro/g2000/InstrConfig"]

    # it's not a clean install unless none of the above config folders already exist
    isClean = True

    for folder in installerFolders:
        if os.path.isdir(folder):
            isClean = False
            break

    return isClean


def backupWin7ConfigFiles(fromDrive, toDrive):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Backing up Win7 configuration files, from '%s' to '%s'." % (fromDrive, toDrive))

    # skip bzr files and folders
    # TODO: Any chance of ending up with unins000.dat or unins000.exe? Exclude them too.
    excludeDirs = [".bzr"]
    excludeFiles = [".bzrignore"]

    # list of folders to backup
    foldersToBackupList = mdefs.CONFIG_WIN7_FOLDERS_TO_BACKUP_LIST

    # Back up the folders to the 2nd partition
    for folder in foldersToBackupList:
        folder = os.path.normpath(folder)

        if not os.path.isdir(folder):
            # folder doesn't exist on Win7 host drive (really it should)
            # for now just skip it (don't create the folder on the backup drive)
            logger.warning("Cannot backup '%s' as it does not exist on new Win7 boot drive!" % folder)
            continue

        for dirpath, fromFilename in mutils.osWalkSkip(folder, excludeDirs, excludeFiles):
            # construct the destination file path for the copy
            toFilename = os.path.join(toDrive,
                                      os.path.sep,
                                      mdefs.BACKUP_WIN7_CONFIG_FOLDER_ROOT_NAME) + os.path.splitdrive(fromFilename)[1]

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

    logger.info("Successfully backed up Win7 configuration files.")


def restoreXPFolders(fromDrive, toDrive):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Restoring WinXP configuration files, from '%s' to '%s'." % (fromDrive, toDrive))

    # skip bzr files and folders
    # TODO: Any chance of ending up with unins000.dat or unins000.exe? Exclude them too.
    excludeDirs = [".bzr"]
    excludeFiles = [".bzrignore"]

    # list of folders to restore
    foldersToRestoreList = []

    # config folders in the list are relative to the backup drive folder and C: (dest)
    for folder in mdefs.CONFIG_FOLDERS_TO_RESTORE_LIST:
        folder = os.path.join(fromDrive, mdefs.BACKUP_XP_FOLDER_ROOT_NAME, folder)
        foldersToRestoreList.append(folder)

    # Restore the folders to the C: drive
    for folder in foldersToRestoreList:
        srcFolder = os.path.normpath(os.path.join(fromDrive, mdefs.BACKUP_XP_FOLDER_ROOT_NAME, folder))
        dstFolder = os.path.normpath(os.path.join(toDrive, folder))

        for dirpath, fromFilename in mutils.osWalkSkip(srcFolder, excludeDirs, excludeFiles):
            # construct the destination file path for the copy
            toFilename = os.path.join(toDrive,
                                      os.path.sep,
                                      os.path.splitdrive(fromFilename)[1])

            # create the destination dir if it doesn't already exist
            targetDir = os.path.split(toFilename)[0]
            if not os.path.isdir(targetDir):
                logger.warning("Creating '%s' on new Win7 boot drive since it does not exist." % targetDir)
                os.makedirs(targetDir)

            # We intentionally do not catch any file copy exceptions. The
            # last copy message in the log should indicate which file it
            # barfed on, if this fails.
            # copy2 retains the last access and modification times as well as permissions
            logger.info("Copying '%s' to '%s'" % (fromFilename, toFilename))
            #shutil.copy2(fromFilename, toFilename)

    logger.info("Successfully backed up Win7 configuration files.")


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

    root.info("***** Win7 migration part 2 (install) started. *****")


    root.warning("Migration part 2 (install) needs to be implemented!")

    # ==== Validation =====
    # Find and validate the instrument main drive and the migration drive backup partition
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

    # TODO: software should not be running
    anInfo = mutils.AnalyzerInfo()
    if anInfo.isInstrumentRunning():
        root.warning("Instrument is running, attempting to stop the software and driver.")
        ret = anInfo.stopAnalyzerAndDriver()

        if ret is not None:
            root.error("Instrument is still running, failed to stop software and driver!")
            sys.exit(1)

    # Windows validation (6= Win7)
    ret = mutils.validateWindowsVersion(6, options.debug)

    if not ret:
        errMsg = "Windows OS validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)

    """
    # Python validation (should be Python 2.7)
    # Skipping this, irrelevant check when running this
    # as a compiled script.
    ret = mutils.validatePythonVersion("2.7", options.debug)

    if not ret:
        errMsg = "Python validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        sys.exit(1)
    """

    # we're running from the backup partition
    # the C: drive is the Windows and main partition


    # get the volume name, analyzer name, and analyzer type from the config file
    # the config file is expected to be in the same folder as we are running
    if not os.path.isfile(mdefs.CONFIG_FILENAME):
        root.error("Generated file '%s' is missing, aborting." % mdefs.CONFIG_FILENAME)
        sys.exit(1)

    defaults = {}
    cp = ConfigParser.ConfigParser(defaults)
    cp.read(mdefs.CONFIG_FILENAME)

    if not cp.has_section(mdefs.CONFIG_SECTION):
        root.error("Format problem with generated file '%s', aborting." % mdefs.CONFIG_FILENAME)

    analyzerName = cp.get(mdefs.CONFIG_SECTION, mdefs.ANALYZER_NAME)
    analyzerType = cp.get(mdefs.CONFIG_SECTION, mdefs.ANALYZER_TYPE)
    volumeName = cp.get(mdefs.CONFIG_SECTION, mdefs.VOLUME_NAME)

    # TODO: get mdefs.COMPUTER_NAME, mdefs.MY_COMPUTER_ICON_NAME so we can set them below

    # TODO: warn user if installing over existing software?

    # ==== Install Software ====

    # it's a virgin install if no config folders or HostExe on the Win7 drive
    isClean = isCleanInstall()

    if isClean is True:
        root.info("Clean analyzer software install on Win7 boot drive, new config files will be backed up.")
    else:
        root.info("Not a clean analyzer software install on Win7 boot drive, one or more config folders already exist. Config files will not be backed up.")

    # run the installer (use analyzer type to determine which one)
    # installers are in subfolders in the PicarroInstallers folder
    installerName = findInstaller(analyzerType)

    if installerName is None:
        # no installer found, already logged an error so bail out now
        sys.exit(1)

    ret = runInstaller(installerName)

    if not ret:
        root.error("Installer failed or was canceled, aborting.")
        sys.exit(1)

    # if this was a virgin install (config folders did not exist), backup
    # the config folders so they can be compared later in case there is
    # a problem getting the system running so Service can compare them
    if isClean is True:
        # back up the installed config folders
        backupWin7ConfigFiles(instDrive, migBackupDrive)

    # set the volume name (use saved volume name)
    if volumeName != "":
        root.info("Setting C: drive name to '%s'" % volumeName)
        ret = mutils.setVolumeName("C:", volumeName)

        if not ret:
            root.error("Setting C: drive name to '%s' failed! It will need to be set manually, continuing with migration." % volumeName)
        else:
            root.info("C: drive name successfully set to '%s'" % volumeName)

    # TODO: set the computer name and My Computer icon name

    # ==== Restore Configs ====
    # restore config files
    restoreXPFolders(migBackupDrive, instDrive)

    # TODO: restore user data

    # TODO: restore autosampler config files

    # TODO: fix up config files that have known issues
    # HIDS needs a manual upgrade to InstrConfig\Calibration\InstrCal\FitterConfig.ini:
    #   http://redmine.blueleaf.com/projects/software/wiki/140-22InternalChangelog

    # ==== Start the instrument ====
    # TODO: start up the instrument? reboot so it is started? or give instructions?


def main():
    usage = """
%prog [options]

Win7 migration utility part 2 (install).
"""

    parser = OptionParser(usage=usage)

    parser.add_option('-v', '--version', dest='version', action='store_true',
                      default=False, help=('Report the version number.'))

    parser.add_option('--debug', dest='debug', action='store_true',
                      default=False, help=('Enables debugging.'))

    parser.add_option('--restoreConfigsOnly', dest="restoreConfigsOnly",
                      action='store_true', default=False,
                      help=('Restore the config files only, no user data files or logs.'))

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