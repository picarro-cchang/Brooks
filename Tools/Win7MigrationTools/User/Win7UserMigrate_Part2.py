# Win7UserMigrate_p2.py
#
# Part 2 of user migration tools for WinXP to Win7
#
# Runs the analyzer installer.
# Part 1 can optionally save off the instrument type so this script
# can find the recommended analyzer installer.
#
# History
#
# 2014-03-21  tw  Initial version.
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
import filecmp
import difflib
import re

from optparse import OptionParser

import Win7UserMigrationToolsDefs as mdefs
import Win7UserMigrationUtils as mutils

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]


def findDrivesByName(driveName):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Finding drives named '%s'." % driveName)

    # Enumerate the drives and build a list with drive letters
    # that match the name exactly (case-insensitive). Returned
    # list will contain entries like ['C:', 'E:']
    driveName = driveName.lower()
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]

    matches = []

    # drive letter string will look like C:\ etc
    for drive in drives:
        try:
            # returns tuple with file system info
            driveInfo = win32api.GetVolumeInformation(drive)

            # volume name is the first value in the tuple
            curDriveName = driveInfo[0].lower()

            #print "curDriveName=", curDriveName

            logger.debug("drive=%s  curDriveName='%s'" % (drive, curDriveName))

            if curDriveName == driveName:
                # return the drive letter and colon, whack the backslash
                matches.append(drive[0:2])

        except Exception, e:
            # ignore exceptions, we will get them for the DVD drive
            # if there is no DVD in the drive, etc.
            pass

    #print "found matches=", matches
    logger.debug("found matches='%s'" % matches)
    return matches


def findAndValidateDrives():
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Finding and validating drives for Windows 7 migration.")

    # C: should be the same as the current drive (booted to Win7 partition of migration drive)
    # skip ourself (should be C:)
    curDrive = os.path.splitdrive(os.getcwd())[0]

    instDrive = curDrive
    hostExeDir = os.path.normpath("C:/Picarro/g2000/HostExe")

    # validate the instrument drive, there should not yet be a HostExe folder in the expected Picarro path
    # TODO: should we require that the software not be installed yet?
    if os.path.isdir(hostExeDir):
        #instDrive = None
        logger.warning("Picarro analyzer software is already installed, dir exists (%s)." % hostExeDir)

    # look for another drive that is also named picarro, it should be the WinXP image partition
    drives = findDrivesByName("picarro")

    # ignore the current drive
    if curDrive in drives:
        drives.remove(curDrive)

    logger.debug("drives='%s'" % drives)

    # init to no WinXP drive found
    winXPDrive = None

    if len(drives) == 0:
        # found no other drives named picarro
        winXPDrive = None

    else:
        # sanity check: look for installed Picarro config folders, use the first drive
        # that has all the config folders
        configDirs = ["AppConfig", "InstrConfig", "CommonConfig"]

        for drive in drives:
            configBase = os.path.normpath(os.path.join(drive, os.path.sep, "Picarro/g2000"))

            logger.debug("configBase='%s'" % configBase)

            # Assume found a drive that has all the folders
            found = True

            for configDir in configDirs:
                configPath = os.path.normpath(os.path.join(configBase, configDir))

                logger.debug("configPath='%s'" % configPath)

                if not os.path.isdir(configPath):
                    logger.error("Expected folder '%s' not found!" % configPath)
                    found = False
                    break

            if found is True:
                winXPDrive = drive
                break

    fSuccess = True
    if instDrive is None or winXPDrive is None:
        fSuccess = False
    logger.info("Drive validation done, fSuccess=%s." % fSuccess)

    return instDrive, winXPDrive


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


def findInstaller(migBackupDrive, analyzerType):
    """
    Returns the installer filename (full path) for the analyzer type, or None
    on error (none or more than one found)
    """
    # The PicarroInstallers folder contains subfolders named by
    # instrument type.
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Preparing to run installer for analyzer type '%s'." % analyzerType)

    installerDir = os.path.join(migBackupDrive, os.path.sep, mdefs.MIGRATION_TOOLS_FOLDER_NAME, mdefs.INSTALLER_FOLDER_ROOT_NAME, analyzerType)
    logger.debug("Installer folder for analyzer type '%s' is '%s'" % (analyzerType, installerDir))

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
                        "C:/Picarro/g2000/InstrConfig",
                        "C:/Picarro/g2000/HostExe"]

    # it's not a clean install unless *none* of the above config folders already exist
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
    excludeFiles = [".bzrignore", "analyzerState.db", "analyzerState.db-journal"]

    # list of folders to backup
    foldersToBackupList = mdefs.CONFIG_WIN7_FOLDERS_TO_BACKUP_LIST

    # if the Win7 backup folder exists, remove it so it doesn't contain
    # orphan files from the last backup
    backupDir = os.path.join(toDrive,
                             os.path.sep,
                             mdefs.BACKUP_WIN7_CONFIG_FOLDER_ROOT_NAME)

    if os.path.isdir(backupDir):
        logger.info("Win7 backup folder '%s' exists, removing it prior to config file backup." % backupDir)

        # An exception shouldn't happen, but could happen if Windows Explorer
        # has the folder open so continue.
        try:
            shutil.rmtree(backupDir)
        except Exception, e:
            logger.warning("Failed to remove Win7 backup folder, proceeding anyway. Exception=%r, %r" % (Exception, e))

    # Back up the folders
    for folder in foldersToBackupList:
        folder = os.path.normpath(folder)

        if not os.path.isdir(folder):
            # folder doesn't exist on Win7 host drive (really it should)
            # for now just skip it (don't create the folder on the backup drive)
            logger.warning("Cannot backup '%s' as it does not exist on the Win7 drive!" % folder)
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


def diffFiles(dcmp, fp):
    for name in dcmp.diff_files:
        # do a comparison between the files
        """
        print "*******"
        print "name: ", name
        print "dir1: ", dcmp.left
        print "dir2: ", dcmp.right
        """
        
        file1 = os.path.join(dcmp.left, name)
        file2 = os.path.join(dcmp.right, name)

        with open(file1, 'r') as f1:
            with open(file2, 'r') as f2:
                diff = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=file1, tofile=file2)
                    
                for line in diff:
                    fp.write(line)
                    #sys.stdout.write(line)

    # recurse
    for sub_dcmp in dcmp.subdirs.values():
        diffFiles(sub_dcmp, fp)


def computeDiffs(origDir, newDir, logFilename, diffFilename, diffMode):
    """
    Log the diffs between dirs.
    """
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)

    assert origDir is not None
    assert newDir is not None

    logger.info("Comparing '%s' and '%s', results in '%s' and diffs in '%s'" % (origDir,
                 newDir, logFilename, diffFilename))

    # 3rd arg is list of names to ignore (unclear if dirs or filenames)
    dirCmp = filecmp.dircmp(origDir, newDir)

    origStdout = sys.stdout
    sys.stdout = open(logFilename, 'wb')

    # reports filenames of same, missing, and different files
    dirCmp.report_full_closure()

    #logger.info("Calling print_diff_files")
    #logger.info("Difference list: %r" % dirCmp.diff_files)
    #print_diff_files(dirCmp)

    sys.stdout.close()
    sys.stdout = origStdout

    # Log the file differences. Append to the existing file, in case
    # the same filename is passed.
    with open(diffFilename, diffMode) as fp:
        diffFiles(dirCmp, fp)


def compareXPandWin7Configs(win7BackupDrive, winXPDrive, logfileSuffix):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Comparing backed up Win7 and WinXP config files")

    # treat empty suffix string as no suffix
    if logfileSuffix == "":
        logfileSuffix = None

    # root folder of the WinXP image partition (analyzer software installed)
    #rootXPFolder = os.path.normpath(os.path.join(winXPDrive, os.path.sep, mdefs.BACKUP_XP_FOLDER_ROOT_NAME))
    rootXPFolder = winXPDrive

    # root folder of the backup drive for Win7 config files
    rootWin7Folder = os.path.normpath(os.path.join(win7BackupDrive, os.path.sep, mdefs.BACKUP_WIN7_CONFIG_FOLDER_ROOT_NAME))

    # list of folders to compare is what we backed up
    foldersToCompareList = mdefs.CONFIG_WIN7_FOLDERS_TO_BACKUP_LIST

    for win7folder in foldersToCompareList:
        win7folder = os.path.normpath(win7folder)

        logger.debug("win7folder='%s'" % win7folder)

        """
        if not os.path.isdir(win7folder):
            # folder doesn't exist on Win7 host drive (really it should)
            # for now just skip it (don't create the folder on the backup drive)
            logger.warning("Cannot compare '%s' as it does not exist on the Win7 drive!" % win7folder)
            continue
        """

        # Strip off the C: from the current win7folder, and append this path to
        # the backup root folder to form the winXPfolder to compare
        winXPfolder = os.path.normpath(rootXPFolder + win7folder[2:])

        # Similar for the Win7 folder to compare with
        win7folderCompare = os.path.normpath(rootWin7Folder + win7folder[2:])

        # generate a filename to output the differences to
        # use logfileSuffix in part of the name if it is not None
        folderName = os.path.split(winXPfolder)[1]

        if logfileSuffix is not None:
            logFilename = os.path.join(os.getcwd(), "Compare_%s_%s.log" % (folderName, logfileSuffix))
            diffFilename = os.path.join(os.getcwd(), "Diff_%s_%s.log" % (folderName, logfileSuffix))

        else:
            logFilename = os.path.join(os.getcwd(), "Compare_%s.log" % folderName)
            diffFilename = os.path.join(os.getcwd(), "Diff_%s.log" % folderName)

        logFilename = os.path.normpath(logFilename)
        diffFilename = os.path.normpath(diffFilename)

        # do the comparison, don't append to an existing diff file
        diffMode = "w"
        computeDiffs(winXPfolder, win7folderCompare, logFilename, diffFilename, diffMode)


"""
# This restores folders from a backup dir
def restoreXPFoldersFromBackupDir(fromDrive, toDrive, folderList):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Restoring WinXP folders, from '%s' to '%s'." % (fromDrive, toDrive))
    logger.debug("restoreXPFolders: folderList = '%r'" % folderList)

    # skip bzr files and folders
    # TODO: Any chance of ending up with unins000.dat or unins000.exe? Exclude them too.
    excludeDirs = [".bzr"]
    excludeFiles = [".bzrignore"]

    # root folder is something like "K:\WinXPBackup"
    # folderList is a list containing items like "C:/Picarro/g2000/InstrConfig"
    rootFolder = os.path.normpath(os.path.join(fromDrive, os.path.sep, mdefs.BACKUP_XP_FOLDER_ROOT_NAME))
    skipCount = len(rootFolder)

    for folder in folderList:
        # remove the drive letter so we can construct the source folder path on the migration drive
        # splitdrive on "C:/Picarro/g2000/InstrConfig" returns this tuple:
        #   ('C:', '/Picarro/g2000/InstrConfig')
        # os.path.join doesn't handle mixed forward and backslashes well so build up paths with
        # forward slashes first
        baseFolder = os.path.splitdrive(folder)[1]
        srcFolder = fromDrive + '/' + mdefs.BACKUP_XP_FOLDER_ROOT_NAME + baseFolder
        srcFolder = os.path.normpath(srcFolder)

        for dirpath, fromFilename in mutils.osWalkSkip(srcFolder, excludeDirs, excludeFiles):
            # construct the destination file path for the copy
            # leave off the root part of the filepath and append it to the dest drive
            assert fromFilename.find(rootFolder) != -1

            toFilename = os.path.join(toDrive, os.path.sep, fromFilename[skipCount+1:])

            # create the destination dir if it doesn't already exist
            # (it may not if we are restoring user data, but should exist if restoring config files)
            targetDir = os.path.split(toFilename)[0]

            if not os.path.isdir(targetDir):
                logger.info("Creating '%s' on new Win7 boot drive since it does not exist." % targetDir)
                os.makedirs(targetDir)

            # We intentionally do not catch any file copy exceptions. The
            # last copy message in the log should indicate which file it
            # barfed on, if this fails.
            # copy2 retains the last access and modification times as well as permissions
            logger.info("Copying '%s' to '%s'" % (fromFilename, toFilename))
            shutil.copy2(fromFilename, toFilename)

    logger.info("Successfully restored WinXP configuration files.")
"""

def restoreXPFiles(fromDrive, toDrive, fileList):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Restoring specific WinXP files, from '%s' to '%s'." % (fromDrive, toDrive))
    logger.debug("restoreXPFiles: fileList = '%r'" % fileList)

    # items in fileList are something like 'C:/Picarro/g2000/AppConfig/Config/Utilities/SupervisorLauncher.ini'
    issuedWarning = False

    for filename in fileList:
        # whack off the drive letter
        baseFilename = os.path.splitdrive(filename)[1]
        fromFilename = fromDrive + "/" + mdefs.BACKUP_XP_FOLDER_ROOT_NAME + baseFilename
        fromFilename = os.path.normpath(fromFilename)

        # destination filename is just the filename in the list
        toFilename = os.path.normpath(filename)

        if os.path.isfile(fromFilename):
            # make sure destination folder exists, or create it if it doesn't
            toFolder = os.path.split(filename)[0]

            if not os.path.isdir(toFolder):
                logger.info("Destination directory '%s' does not exist, creating the path." % toFolder)
                os.makedirs(toFolder)

            logger.info("Copying '%s' to '%s'" % (fromFilename, toFilename))

            # do the copy
            shutil.copy2(fromFilename, toFilename)

        else:
            logger.warn("Source file '%s' does not exist, skipping copy" % fromFilename)
            issuedWarning = True

    if not issuedWarning:
        logger.info("Successfully restored specific WinXP files")
    else:
        logger.error("Some problems encountered copying files, be sure to examine the log file!")


def restoreXPFolders(fromDrive, toDrive, folderList):
    # Restore files in a folder list from one partition to another
    # Expect the paths to be the same except for the drive letter
    # folderList is a list containing items like "C:/Picarro/g2000/InstrConfig"
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Restoring WinXP folders, from '%s' to '%s'." % (fromDrive, toDrive))
    logger.info("restoreXPFolders: folderList = '%r'" % folderList)

    # skip bzr files and folders
    # TODO: Any chance of ending up with unins000.dat or unins000.exe? Exclude them too.
    excludeDirs = [".bzr"]
    excludeFiles = [".bzrignore", "analyzerState.db", "analyzerState.db-journal"]

    for folder in folderList:
        # remove the drive letter so we can construct the source folder path on the migration drive
        # splitdrive on "C:/Picarro/g2000/InstrConfig" returns this tuple:
        #   ('C:', '/Picarro/g2000/InstrConfig')
        # replace the drive letter with the WinXP drive letter
        baseFolder = os.path.splitdrive(folder)[1]
        srcFolder = fromDrive + baseFolder
        srcFolder = os.path.normpath(srcFolder)

        logger.debug("srcFolder='%s'" % srcFolder)

        # if source folder doesn't exist, log it but continue
        if not os.path.isdir(srcFolder):
            logger.warn("Source folder '%s' does not exist." % srcFolder)
            continue

        for dirpath, fromFilename in mutils.osWalkSkip(srcFolder, excludeDirs, excludeFiles):
            # construct the destination file path for the copy
            # leave off the root part of the filepath and append it to the dest drive
            #assert fromFilename.find(rootFolder) != -1

            toFilename = os.path.join(toDrive, os.path.sep, fromFilename[2:])

            logger.debug("fromFilename='%s'" % fromFilename)
            logger.debug("toFilename='%s'" % toFilename)

            # create the destination dir if it doesn't already exist
            # (it may not if we are restoring user data, but should exist if restoring config files)
            targetDir = os.path.split(toFilename)[0]
            logger.debug("targetDir='%s'" % targetDir)

            if not os.path.isdir(targetDir):
                logger.info("Creating '%s' on new Win7 boot drive since it does not exist." % targetDir)
                os.makedirs(targetDir)

            # We intentionally do not catch any file copy exceptions. The
            # last copy message in the log will indicate which file it
            # barfed on if the copy fails.
            # copy2 retains the last access and modification times as well as permissions
            logger.info("Copying '%s' to '%s'" % (fromFilename, toFilename))
            shutil.copy2(fromFilename, toFilename)

    logger.info("Successfully restored WinXP configuration files.")


def repairConfigFiles(instDrive):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Repairing known issues in config files restored from WinXP, drive='%s'." % instDrive)

    """
    # Repair Coordinators (min and max calls from numpy lib require square
    # brackets around arguments if there is more than one)
    # C:\Picarro\g2000\AppConfig\Config\Coordinator
    #
    # Warning: this function currently doesn't work correctly so commenting it out.
    logger.info("Repairing Coordinators")
    repairList = mutils.fixMinMaxSyntax("C:\Picarro\g2000\AppConfig\Config\Coordinator",
                                        ".ini")

    if len(repairList) > 0:
        logger.info("Coordinators repaired: %r" % repairList)
    """

    # Repair DataManager scripts
    # 
    # Exact debug line in analyze_CFKADS.py that creates a file in C:
    # that Win7 won't allow
    badSubstr = 'file("C:/logfile.txt","w",0)'

    logger.info("Repairing DataManager scripts that contain '%s'" % badSubstr)
    repairList = mutils.DeleteBadLine("C:\Picarro\g2000\AppConfig\Scripts\DataManager",
                                      badSubstr, ".py")

    if len(repairList) > 0:
        logger.info("DataManager scripts repaired: %r" % repairList)

    # Fix the ATF parameters in the hot box cal file. False is returned on error,
    # True indicates either no change required or successful update.
    fRet = mutils.fixHotBoxCalIni()

    if fRet is False:
        logger.error("Hot box cal file update failed!")

    logger.info("Repair config files done.")


def getAnalyzerInfo(winXPDrive, instDrive):
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.info("Getting analyzer information.")
    haveAnalyzerType = False
    analyzerType = None
    analyzerSerial = None

    # first look on the WinXP drive for installerSignature.txt which contains the analyzer type
    # then we won't have to prompt the user for it
    installerSigFilepath = winXPDrive[:1] + ":/Picarro/g2000/installerSignature.txt"

    if os.path.isfile(installerSigFilepath):
        with open(installerSigFilepath, "r") as f:
            anTypeTmp = f.readline()

        logger.info("Analyzer type read from '%s': '%r'" % (installerSigFilepath, anTypeTmp))

        # if there is an installer dir with the same name then we have the analyzer type
        installerDir = os.path.join(instDrive, os.path.sep,
                                    mdefs.MIGRATION_TOOLS_FOLDER_NAME,
                                    mdefs.INSTALLER_FOLDER_ROOT_NAME,
                                    anTypeTmp)

        if os.path.isdir(installerDir):
            analyzerType = anTypeTmp
            haveAnalyzerType = True

            # set the serial to an empty string, it's not used for anything right now anyway
            analyzerSerial = ""

    if not haveAnalyzerType:
        logger.info("Prompting user for analyzer information.")
        re_type = re.compile("[A-Z]*")
        re_serial = re.compile("[0-9]*")

        while not haveAnalyzerType:
            print ""
            print ""
            print "Please type your analyzer name and serial, then hit the Return key."
            print "Examples: CFKADS2001  hids2007"
            print ""
            inputStr = raw_input("Or type Q to quit: ")
            inputStr = inputStr.upper()
            print ""

            analyzerType = None
            analyzerSerial = None

            if inputStr == "Q":
                logger.info("Win7 migration aborted by user (analyzer name and serial not entered).")
                break

            # separate out the analyzer name and the serial
            m = re_type.match(inputStr)
            analyzerType = m.group()

            if analyzerType == "":
                analyzerType = None

            # hmmm, I can't seem to figure out how to get the first
            # occurrence of digits in a string without iterating
            for p in re_serial.findall(inputStr):
                if p != "":
                    analyzerSerial = p
                    break

            if analyzerType is not None and analyzerSerial is not None:
                haveAnalyzerType = True
            else:
                # prompt again
                print ""

    return analyzerType, analyzerSerial


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
    timeStr = ""
    if options.logFilename is None:
        if options.localTime is True:
            timeBase = time.localtime()
            timeStr = time.strftime("%Y_%m_%d_%H_%M_%S", timeBase)
            logFilename = time.strftime(mdefs.MIGRATION_TOOLS_LOGFILENAME_BASE_2, timeBase)
            logFilename = logFilename + ".log"
        else:
            timeBase = time.gmtime()
            timeStr = time.strftime("%Y_%m_%d_%H_%M_%SZ", timeBase)
            logFilename = time.strftime(mdefs.MIGRATION_TOOLS_LOGFILENAME_BASE_2, timeBase)
            logFilename = logFilename + "Z.log"

        # TODO: append this base filename to a drive and folder
        #       should this go on the new drive partition 1? or partition 2?
    else:
        # Filename specified on the command line, we still run it through strftime
        # but leave timeStr empty
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

    root.info("***** Win7 field migration (install software and restore configurations and data) started. *****")
    root.info("Running %s version %s" % (AppPath, mdefs.MIGRATION_TOOLS_VERSION))

    if options.debug is True:
        mutils.pauseForUserResponse("continue")

    # ==== Validation =====
    # Find and validate the instrument main drive and the WinXP image partition
    instDrive, winXPDrive = findAndValidateDrives()

    root.info("Drive validation: instrument drive='%s', WinXP drive ='%s'" %
              (instDrive, winXPDrive))

    if instDrive is None or winXPDrive is None:
        # error should already have been logged, bail out
        # TODO: pop an error dialog and direct user to the error log
        errMsg = "Drive validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        mutils.pauseForUserResponse("exit")
        sys.exit(1)

    if options.debug is True:
        mutils.pauseForUserResponse("continue")

    # TODO: software should not be running
    anInfo = mutils.AnalyzerInfo()
    if anInfo.isInstrumentRunning():
        root.warning("Instrument is running, attempting to stop the software and driver.")
        ret = anInfo.stopAnalyzerAndDriver()

        if ret is not None:
            root.error("Instrument is still running, failed to stop software and driver!")
            mutils.pauseForUserResponse("exit")
            sys.exit(1)

    # Windows validation (6= Win7)
    ret = mutils.validateWindowsVersion(6, options.debug)

    if not ret:
        errMsg = "Windows OS validation failed. See log results in '%s'" % logFilename
        root.error(errMsg)
        #showErrorDialog(errMsg)
        mutils.pauseForUserResponse("exit")
        sys.exit(1)

    if options.debug is True:
        mutils.pauseForUserResponse("continue")

    # Python validation (should be Python 2.7)
    # Skipping this, irrelevant check when running this
    # as a compiled script.
    #ret = mutils.validatePythonVersion("2.7", options.debug)
    #if not ret:
    #    errMsg = "Python validation failed. See log results in '%s'" % logFilename
    #    root.error(errMsg)
    #    #showErrorDialog(errMsg)
    #    mutils.pauseForUserResponse("exit")
    #    sys.exit(1)

    # this script is running from the backup partition, so we can use its drive letter as the source drive
    # the C: drive is the Windows and main partition


    # Get the volume name, analyzer name, and analyzer type from the config file
    # if it's there.
    # The config file is currently expected to be in the same folder as we are running
    # but this may change if the part1 tool is built on WinXP/Python 2.5 and this
    # part2 tool is built on Win7/Python 2.7.
    # If no config file then prompt the user for the instrument type and ID

    # look for the config file in the main migration tools folder
    configFilepath = os.path.join(instDrive,
                                  os.path.sep,
                                  mdefs.MIGRATION_TOOLS_FOLDER_NAME,
                                  mdefs.MIGRATION_CONFIG_FILENAME)

    if not os.path.isfile(configFilepath):
        root.info("Migration part 1 instrument config file '%s' not found." % configFilepath)
        #mutils.pauseForUserResponse("exit")
        #sys.exit(1)

        # prompt for instrument type and ID
        analyzerType, analyzerId = getAnalyzerInfo(winXPDrive, instDrive)

        if analyzerType is None or analyzerId is None:
            # either/both are None if user quit so log this and exit
            root.info("User quit migration script during entry of analyzer type and serial.")
            sys.exit(0)

        # construct names
        #analyzerName = analyzerType + analyzerId
        analyzerName = analyzerType

        # for now don't set the computer name
        #computerName = "Picarro - %s" % analyzerName
        computerName = ""

    else:
        defaults = {}
        cp = ConfigParser.ConfigParser(defaults)
        cp.read(configFilepath)

        if not cp.has_section(mdefs.MIGRATION_CONFIG_SECTION):
            root.error("Format problem with generated file '%s', aborting." % mdefs.MIGRATION_CONFIG_FILENAME)

        analyzerName = cp.get(mdefs.MIGRATION_CONFIG_SECTION, mdefs.ANALYZER_NAME)
        analyzerType = cp.get(mdefs.MIGRATION_CONFIG_SECTION, mdefs.ANALYZER_TYPE)
        #volumeName = cp.get(mdefs.MIGRATION_CONFIG_SECTION, mdefs.VOLUME_NAME)
        computerName = cp.get(mdefs.MIGRATION_CONFIG_SECTION, mdefs.COMPUTER_NAME)

        #print "analyzerName=", analyzerName
        #print "analyzerType=", analyzerType
        #print "computerName=", computerName

        analyzerName = analyzerType

        # TODO: get mdefs.COMPUTER_NAME, mdefs.MY_COMPUTER_ICON_NAME so we can set them below
        #root.warning("Set computer name and name for My Computer from saved configuration needs to be implemented!")

    root.info("Instrument info: analyzerType='%s'" % analyzerType)

    if options.debug is True:
        mutils.pauseForUserResponse("continue")

    # Prompt for AddOns to install?

    # ==== Install Analyzer Software ====

    # it's a virgin install if no config folders or HostExe on the Win7 drive
    isClean = isCleanInstall()

    # Warn user if installing over an existing host software installation, but allow it to proceed anyway
    if isClean is True:
        root.info("Clean analyzer software install on Win7 boot drive, newly installed config files will be backed up.")
    else:
        root.info("Not a clean analyzer software install on Win7 boot drive, "
                  "one or more config folders already exist. Config files will "
                  "not be backed up without --forceBackup option.")

    # run the installer (use analyzer type to determine which one)
    # installers are in subfolders in the PicarroInstallers folder on this drive
    # (instDrive)
    installerName = findInstaller(instDrive, analyzerType)
    root.debug("Installer is '%r'." % installerName)

    if options.debug is True:
        mutils.pauseForUserResponse("continue")

    if not options.skipInstall:
        if installerName is None:
            # no installer found, already logged an error so bail out now
            mutils.pauseForUserResponse("exit")
            sys.exit(1)

        root.info("Running analyzer installer '%s'." % installerName)
        ret = runInstaller(installerName)

        if not ret:
            root.error("Installer failed or was canceled, aborting remainder of migration.")
            mutils.pauseForUserResponse("exit")
            sys.exit(1)

    else:
        root.warning("Skipping software installation, --skipInstall option was set.")


    # if this was a virgin install (config folders did not exist), backup
    # the config folders so they can be compared later in case there is
    # a problem getting the system running so Customer Support can compare them
    if isClean is True:
        """
        # The Win7ConfigBackup folder should not yet exist on the current instrument
        # migration drive, it's an error if it does.
        backupFolder = os.path.join(instDrive,
                                    os.path.sep,
                                    mdefs.BACKUP_WIN7_CONFIG_FOLDER_ROOT_NAME)

        root.info("Checking whether Win7 config backup folder exists: '%s'" % backupFolder)

        if os.path.isdir(backupFolder):
            errMsg = "Win7 config backup folder '%s' exists! Either rename or delete it and run this program again."
            root.error(errMsg)
            mutils.pauseForUserResponse("exit")
            sys.exit(1)
        """

        # back up the installed config folders to this drive
        # this will attempt to delete the backup folder if it exists
        # before backing up the configs
        #
        # timeStr is the log filename date/time suffix to append to the diff filenames
        if options.debug is True:
            mutils.pauseForUserResponse("continue", "next: backupWin7ConfigFiles")
        backupWin7ConfigFiles(instDrive, instDrive)

        if options.skipCompare is False or options.forceCompare is True:
            if options.debug is True:
                mutils.pauseForUserResponse("continue", "next: compareXPandWin7Configs")

            root.info("--forceCompare set, comparing Win7 and WinXP configuration files.")
            compareXPandWin7Configs(instDrive, winXPDrive, timeStr)

    else:
        # backup Win7 configs if forceBackup option set (useful for debugging)
        if options.forceBackup is True:
            # this will delete the backup folder first if it exists
            root.info("--forceBackup set, backing up Win7 configuration files.")
            backupWin7ConfigFiles(instDrive, instDrive)

        # do a compare if forceCompare option set (useful for debugging)
        if options.forceCompare is True:
            root.info("--forceCompare set, comparing Win7 and WinXP configuration files.")
            compareXPandWin7Configs(instDrive, winXPDrive, timeStr)

    # set the volume name (use saved volume name)
    # #695: remove handling of Win7 boot drive name
    """
    if volumeName != "":
        root.info("Setting C: drive name to '%s'" % volumeName)
        ret = mutils.setVolumeName("C:", volumeName)

        # TODO: there already is an error logged, don't need to do it again
        #       but maybe we need to keep track of this so user can be directed to look in the log file?
        if not ret:
            root.error("Setting C: drive name to '%s' failed! It will need to be set manually, ignoring error and continuing with migration." % volumeName)
        #else:
        #    root.info("C: drive name successfully set to '%s'" % volumeName)
    """

    # set the computer name
    """
    if computerName != "":
        if options.debug is True:
            mutils.pauseForUserResponse("continue", "next: setComputerName to '%s'" % computerName)
        mutils.setComputerName(computerName)
    """

    # TODO: show the My Computer icon on the desktop (how do I do this?)

    # ==== Restore Configs ====
    # restore config folders
    root.info("Restoring configuration files from WinXP folders.")

    if options.debug is True:
        mutils.pauseForUserResponse("continue")
    restoreXPFolders(winXPDrive, instDrive, mdefs.CONFIG_FOLDERS_TO_RESTORE_LIST)

    # ==== Repair known issues in config files ====
    if options.debug is True:
        mutils.pauseForUserResponse("continue", "next: repairConfigFiles")
    repairConfigFiles(instDrive)

    """
    # restore specific named config files
    root.info("Restoring specific WinXP configuration files.")
    restoreXPFiles(migBackupDrive, instDrive, mdefs.CONFIG_FILES_TO_RESTORE_LIST)
    """

    """
    # TODO: restore specific autosampler config files (only configs not DLLs or EXEs)
    root.warning("Restoring specific autosampler files needs to be implemented")
    """

    # restore user data
    if options.skipRestoreUserData is False:
        root.info("Restoring user data from WinXP.")
        restoreXPFolders(winXPDrive, instDrive, mdefs.DATA_FOLDERS_TO_RESTORE_LIST)

    else:
        root.warning("Skipping restore of backed up user data, --skipRestoreUserData option was set.")

    # HIDS needs a manual upgrade to InstrConfig\Calibration\InstrCal\FitterConfig.ini:
    #   http://redmine.blueleaf.com/projects/software/wiki/140-22InternalChangelog

    # ==== Start the instrument ====
    # TODO: start up the instrument? reboot so it is started? or give instructions?

    # Done!
    root.info("***** Win7 field migration (install software and restore configurations and data) DONE! *****")

    # Print a message since this is being run from a cmd /K shortcut
    print ""
    print ""
    print "*****************************************************"
    print "  Windows 7 user migration completed successfully!"
    print "*****************************************************"
    print ""
    print ""


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

    parser.add_option('--skipRestoreUserData', dest="skipRestoreUserData",
                      action='store_true', default=False,
                      help=('Skip restoring backed up user data files and logs.'))

    parser.add_option('--skipInstall', dest="skipInstall",
                      action='store_true', default=False,
                      help=('Skip installing the Win7 analyzer software.'))

    parser.add_option('--skipCompare', dest="skipCompare",
                      action='store_true', default=False,
                      help=('Skip comparison of Win7 config files vs. WinXP.'))

    parser.add_option('--forceCompare', dest="forceCompare",
                      action='store_true', default=False,
                      help=('Force comparison of backed up Win7 config files vs. WinXP. '
                            'This flag overrides --skipCompare.'))

    parser.add_option('--forceBackup', dest="forceBackup",
                      action='store_true', default=False,
                      help=('Forces backup of Win7 config files.'))

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

    """
    # test code to validate and restore config files
    # basic logger
    logLevel = logging.INFO
    #logLevel = logging.DEBUG

    #logFilename = time.strftime(mdefs.MIGRATION_TOOLS_LOGFILENAME_BASE_2)
    #logFilename = logFilename + ".log"
    logFilename = "TestLog.log"
    mode = "w"

    root = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    root.setLevel(logLevel)
    handlerFile = logging.FileHandler(logFilename, mode)
    #handlerFile.setFormatter(fmt)
    root.addHandler(handlerFile)

    instDrive, winXPDrive = findAndValidateDrives()

    print "new instrument drive='%s', WinXP partition ='%s'" % (instDrive, winXPDrive)
    if instDrive is None:
        print "error: instDrive is None"
        sys.exit(1)
    if  winXPDrive is None:
        print "winXPDrive is None"
        sys.exit(1)

    # restore config files from the WinXP drive to instrument drive
    restoreXPFolders(winXPDrive, instDrive, mdefs.CONFIG_FOLDERS_TO_RESTORE_LIST)

    repairConfigFiles(instDrive)

    # restore data files from the WinXP drive to the instrument drive
    restoreXPFolders(winXPDrive, instDrive, mdefs.DATA_FOLDERS_TO_RESTORE_LIST)
    """


    """
    # test code for compare

    # basic logger
    logLevel = logging.INFO

    #logFilename = time.strftime(mdefs.MIGRATION_TOOLS_LOGFILENAME_BASE_2)
    #logFilename = logFilename + ".log"
    logFilename = "TestLog.log"
    mode = "w"

    root = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    root.setLevel(logLevel)
    handlerFile = logging.FileHandler(logFilename, mode)
    #handlerFile.setFormatter(fmt)
    root.addHandler(handlerFile)

    root.info("***** Win7 migration test compare started. *****")

    backupDrive = "K:"
    timeBase = time.gmtime()
    timeStr = time.strftime("%Y_%m_%d_%H_%M_%SZ", timeBase)
    logfileSuffix = None
    compareXPandWin7Configs(backupDrive, logfileSuffix)
    """

    """
    # test code for hot box cal file fix
    print "testing fixHotBoxCalIni"

    # basic logger
    logLevel = logging.INFO

    #logFilename = time.strftime(mdefs.MIGRATION_TOOLS_LOGFILENAME_BASE_2)
    #logFilename = logFilename + ".log"
    logFilename = "TestLog.log"
    mode = "w"

    root = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    root.setLevel(logLevel)
    handlerFile = logging.FileHandler(logFilename, mode)
    #handlerFile.setFormatter(fmt)
    root.addHandler(handlerFile)

    root.info("***** Win7 migration test hot box cal started. *****")

    fRet = mutils.fixHotBoxCalIni()

    print "fixHotBoxCalIni returned %s" % fRet
    """
