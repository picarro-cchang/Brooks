#
# Utility to patch the coordinators affected by ticket #689.
#
# Copyright 2012-2013 Picarro Inc.
#

from __future__ import with_statement

import os
import sys
import optparse
import logging
import pprint
import time
import zipfile
import contextlib
import filecmp
import shutil
import os.path
from Host.Common.CustomConfigObj import CustomConfigObj

# When built, the file will exist in the local dir
#pylint: disable=F0401
try:
    import Path
except ImportError:
    from Host.Common import Path
#pylint: enable=F0401


DEFAULT_INSTALL_DIR = r'c:\Picarro\G2000'
DEFAULT_BACKUP_DIR = r'c:\Backup'


def backupFile(opts, backupName, updateDirList, filename, fAppend=False):
    """
    Create a zipped backup of the existing file. Arguments:
        opts          = options object (need ops.rootDir and opts.backupDir)

        backupName    = backup zip filename

        updateDirList = list of relative dirs to join with the root install dir
                         e.g. pass ('AppConfig' 'Config','Fitter')
                         for AppConfig/Config/Fitter

        filename      = file to back up

        fAppend        = if True, appends to the existing ZIP file
                         (optional, default is False)
    """

    assert opts.backupDir is not None
    assert opts.rootDir is not None
    assert backupName is not None
    assert updateDirList is not None
    assert type(updateDirList) is list

    if not os.path.isdir(opts.backupDir):
        os.makedirs(opts.backupDir)

    updateDir = opts.rootDir
    for d in updateDirList:
        updateDir = os.path.join(updateDir, d)

    updateFilename = os.path.join(updateDir, filename)
    backupFilename = os.path.join(opts.backupDir, backupName)

    mode = 'w'
    if fAppend is True and os.path.exists(updateFilename):
        mode = 'a'

    logging.debug("Backing up '%s' to '%s', mode = '%s'", updateFilename, backupFilename, mode)

    with contextlib.closing(zipfile.ZipFile(backupFilename,
                                            mode,
                                            zipfile.ZIP_DEFLATED)) as zipFp:
        fullFilename = updateFilename
        zipFilename = fullFilename[len(updateDir) + len(os.sep):]
        logging.debug("zip: %s -> %s", fullFilename, zipFilename)

        # 2nd arg MUST be the full path, if it is zipFilename the path info is not stored in the zip
        zipFp.write(fullFilename, fullFilename)


def backupFolder(opts, backupName, updateDirList, fAppend=False):
    """
    Create a zipped backup of the existing folder. Arguments:
        opts          = options object (need ops.rootDir and opts.backupDir)

        backupName    = backup zip filename

        updateDirList  = list of relative dirs to join with the root install dir
                         e.g. pass ('AppConfig' 'Config','Fitter')
                         for AppConfig/Config/Fitter

        fAppend        = if True, appends to the existing ZIP file
                         (optional, default is False)
    """

    assert opts.backupDir is not None
    assert opts.rootDir is not None
    assert backupName is not None
    assert updateDirList is not None
    assert type(updateDirList) is list

    if not os.path.isdir(opts.backupDir):
        os.makedirs(opts.backupDir)

    updateDir = opts.rootDir
    for d in updateDirList:
        updateDir = os.path.join(updateDir, d)

    backupFilename = os.path.join(opts.backupDir, backupName)

    mode = 'w'
    if fAppend is True and os.path.exists(backupFilename):
        mode = 'a'

    logging.debug("Starting backup of '%s' to '%s', mode = '%s'", updateDir, backupFilename, mode)

    with contextlib.closing(zipfile.ZipFile(backupFilename,
                                            mode,
                                            zipfile.ZIP_DEFLATED)) as zipFp:
        for root, dirs, files in os.walk(updateDir):
            for f in files:
                fullFilename = os.path.join(root, f)
                zipFilename = fullFilename[len(updateDir) + len(os.sep):]
                logging.debug("zip: %s -> %s", fullFilename, zipFilename)

                # 2nd arg MUST be the full path, if it is zipFilename the path info is not stored in the zip
                zipFp.write(fullFilename, fullFilename)


def computeFolderDiffs(opts, updateDirList, newDir, logDir, fAppend=False):
    """
    Log the diffs between the existing dir and the new one to a file
    named diff.log.
        updateDirList  = list of relative dirs to join with the root install dir
                         e.g. pass ('AppConfig' 'Config','Fitter')
                         for AppConfig/Config/Fitter

        newDir         = folder containing new files to install

        logDir         = folder to log the differences to

        fAppend        = if True, appends to the existing file
                         (optional, default is False)
    """

    assert newDir is not None
    assert updateDirList is not None
    assert type(updateDirList) is list

    origDir = opts.rootDir
    for d in updateDirList:
        origDir = os.path.join(origDir, d)

    dirCmp = filecmp.dircmp(origDir, newDir)
    logFilename = os.path.join(logDir, 'diff.log')

    mode = 'wb'
    if fAppend is True and os.path.exists(logFilename):
        mode = 'ab'

    # dirCmp only outputs to stdout, redirect it to a file
    origStdout = sys.stdout     # save stdout
    sys.stdout = open(logFilename, mode)

    logging.debug("Comparing '%s' and '%s', logging diffs to '%s'",
                  origDir, newDir, logFilename)

    dirCmp.report_full_closure()

    sys.stdout.close()
    sys.stdout = origStdout     # restore stdout


def copyNewFolder(opts, newDir, updateDirList):
    """
    Copy the new folder over the existing one. (Preserve any
    custom files the user may have added.)
    """
    assert updateDirList is not None
    assert type(updateDirList) is list

    newDirs = Path.splitToDirs(os.path.abspath(newDir))

    logging.debug("newDirs = '%s'",
                  pprint.pformat(newDirs))

    for root, dirs, files in os.walk(newDir):
        logging.debug("Copying '%s'", root)

        if '.bzr' in dirs:
            logging.debug('Removing .bzr from traversal list')
            dirs.remove('.bzr')

        relativePathDirs = Path.splitToDirs(os.path.abspath(root))
        relativePath = [d for d in relativePathDirs if d not in newDirs]

        if not relativePath:
            # At first level, root will be empty path.
            relativePath = ['']

        relativePath = os.path.join(*relativePath)

        destDir = opts.rootDir
        for d in updateDirList:
            destDir = os.path.join(destDir, d)

        for f in files:
            logging.debug("Move '%s' -> '%s'", os.path.join(root, f),
                          os.path.join(destDir, relativePath))

            # shutil.copy2() also copies last access and modification times as well
            # as retaining the file permissions
            shutil.copy2(os.path.join(root, f),
                         os.path.join(destDir, relativePath))


def fixupIni(opts, updateDirList, filename, section, missingToAddDict):
    """
    Repair an ini file.

        missingToAddDict = dictionary of keys and values to add to [section] if not present
    """
    assert opts.rootDir is not None
    assert updateDirList is not None
    assert filename is not None

    filepath = opts.rootDir
    for d in updateDirList:
        filepath = os.path.join(filepath, d)
    filepath = os.path.join(filepath, filename)

    fChanged = False

    if os.path.isfile(filepath):
        logging.debug("Fixing file '%s'", filepath)
        co = CustomConfigObj(filepath)

        if missingToAddDict is not None:
            for key in missingToAddDict:
                try:
                    # see if the key-value pair is already there
                    # generates a KeyError exception if not
                    val = co.get(section, key)
                    logging.debug("Found key '%s', leaving current value as is (=%s)", key, val)

                except KeyError:
                    # not present, add it and set the update flag
                    logging.debug("Key not found, adding '%s = %s' to '%s'", key, missingToAddDict[key], filepath)
                    co.set(section, key, missingToAddDict[key])
                    fChanged = True

        # write out the INI file only if something changed
        if fChanged is True:
            co.write()

    else:
        logging.debug("File not found: '%s", filepath)


def main():
    usage = """
%prog [options]

Copies new coordinators to the existing installation.
"""

    try:
        from win32com.shell import shell, shellcon
        appData = shell.SHGetFolderPath(0, shellcon.CSIDL_LOCAL_APPDATA, 0, 0)
    except:
        appData = os.path.expanduser('~')

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-b', '--backup', dest='backupDir', metavar='BACKUP_DIR',
                      default=DEFAULT_BACKUP_DIR,
                      help='Directory to store folder backups in.')
    parser.add_option('-r', '--root', dest='rootDir',
                      metavar='ROOT_DIR', default=DEFAULT_INSTALL_DIR,
                      help=('Root installation directory of the Picarro G2000'
                            'package.'))
    parser.add_option('-n', '--new-folder', dest='newFolder',
                      metavar='NEW_FOLDER_DIR',
                      help='Top level directory where the new config files are stored.')

    options, _ = parser.parse_args()

    # Technically this folder should really be Local not Roaming
    # Currently it is: C:\Users\twalder\AppData\Roaming\Picarro\G2000\Log\Special\20130925
    logDir = os.path.join(appData, 'Picarro', 'G2000', 'Log', 'Special', '20130925')

    #print "logDir=", logDir

    if not os.path.isdir(logDir):
        os.makedirs(logDir)

    logging.basicConfig(level=logging.DEBUG,
                        format=('%(asctime)s [%(levelname)s] (%(funcName)s, '
                                '%(lineno)d) %(message)s'),
                        filename=os.path.join(logDir, 'patch.log'),
                        filemode='w')

    # ZIP file we're backing up to
    backupName = "Patch20130925-%s.zip" % time.strftime("%Y%m%d-%H%M%SZ", time.gmtime())

    # initially create new zip and diff files from scratch
    fAppendZip = False
    fAppendDiffs = False

    # AppConfig/Config/Fitter
    updateDirList = ['AppConfig', 'Config', 'Fitter']
    newDir = os.path.join(options.newFolder, 'AppConfig', 'Config', 'Fitter')

    # backup to the zip file and copy the new folder contents
    backupFolder(options, backupName, updateDirList, fAppendZip)
    computeFolderDiffs(options, updateDirList, newDir, logDir, fAppendDiffs)
    copyNewFolder(options, newDir, updateDirList)

    # appending to zip file and diff file from here on out
    fAppendZip = True
    fAppendDiffs = True

    # AppConfig/Scripts/DataManager
    updateDirList = ['AppConfig', 'Scripts', 'DataManager']
    newDir = os.path.join(options.newFolder, 'AppConfig', 'Scripts', 'DataManager')
    backupFolder(options, backupName, updateDirList, fAppendZip)
    computeFolderDiffs(options, updateDirList, newDir, logDir, fAppendDiffs)
    copyNewFolder(options, newDir, updateDirList)

    # AppConfig/Scripts/Fitter
    updateDirList = ['AppConfig', 'Scripts', 'Fitter']
    newDir = os.path.join(options.newFolder, 'AppConfig', 'Scripts', 'Fitter')
    backupFolder(options, backupName, updateDirList, fAppendZip)
    computeFolderDiffs(options, updateDirList, newDir, logDir, fAppendDiffs)
    copyNewFolder(options, newDir, updateDirList)

    #####################
    # InstrConfig changes
    updateDirList = ['InstrConfig', 'Calibration', 'InstrCal']
    newDir = os.path.join(options.newFolder, 'InstrConfig', 'Calibration', 'InstrCal')

    # INI files that are getting updated (same changes to all)
    updateFilename = ["InstrCal.ini", "InstrCal_Air.ini"]

    # back up InstrConfig/Calibration/InstrCal folder (even though we're only
    # touching a single file it contains) and log the differences
    #backupFolder(options, backupName, 'w', updateDirList)
    #computeFolderDiffs(options, updateDirList, newDir, logDir)

    # back up the ini files we're touching
    for f in updateFilename:
        backupFile(options, backupName, updateDirList, f, fAppendZip)

    # update the INI files with new key-value pairs in [Data] if missing
    setupItemsToAdd = {"h2o_selfbroadening_linear":         "0.772",
                       "h2o_selfbroadening_quadratic":      "0.02525",
                       "ch4_watercorrection_linear":       "-0.0101",
                       "ch4_watercorrection_quadratic":     "0.0",
                       "ch4_hp_watercorrection_linear":    "-0.0087473",
                       "ch4_hp_watercorrection_quadratic": "-0.0002429"}

    for f in updateFilename:
        fixupIni(options, updateDirList, f, "Data", setupItemsToAdd)


if __name__ == '__main__':
    main()
