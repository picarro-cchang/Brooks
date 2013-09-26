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


def backupFile(opts, backupName, backupMode, updateDirList, filename):
    """
    Create a zipped backup of the existing file. Arguments:
        opts          = options object (need ops.rootDir and opts.backupDir)

        backupName    = backup zip filename

        backupMode    = 'w' to write to a new zip file, 'a' to append to existing

        updateDirList = list of relative dirs to join with the root install dir
                         e.g. pass ('AppConfig' 'Config','Fitter')
                         for AppConfig/Config/Fitter

        filename      = file to back up
    """

    assert opts.backupDir is not None
    assert opts.rootDir is not None
    assert backupName is not None
    assert backupMode is not None
    assert updateDirList is not None
    assert type(updateDirList) is tuple

    if not os.path.isdir(opts.backupDir):
        os.makedirs(opts.backupDir)

    updateDir = opts.rootDir
    for d in updateDirList:
        updateDir = os.path.join(updateDir, d)

    updateFilename = os.path.join(updateDir, filename)

    logging.debug("Backup dir is '%s'", opts.backupDir)
    logging.debug("Backing up '%s' to '%s', mode = '%s'", updateFilename, backupName, backupMode)

    with contextlib.closing(zipfile.ZipFile(os.path.join(opts.backupDir,
                                                         backupName),
                                            backupMode, zipfile.ZIP_DEFLATED)) as zipFp:
        fullFilename = updateFilename
        zipFilename = fullFilename[len(updateDir) + len(os.sep):]
        logging.debug("zip: %s -> %s", fullFilename, zipFilename)
        zipFp.write(fullFilename, fullFilename)


def backupFolder(opts, backupName, backupMode, updateDirList):
    """
    Create a zipped backup of the existing folder. Arguments:
        opts          = options object (need ops.rootDir and opts.backupDir)

        backupName    = backup zip filename

        backupMode    = 'w' to write to a new zip file, 'a' to append to existing

        updateDirList  = list of relative dirs to join with the root install dir
                         e.g. pass ('AppConfig' 'Config','Fitter')
                         for AppConfig/Config/Fitter
    """

    assert opts.backupDir is not None
    assert opts.rootDir is not None
    assert backupName is not None
    assert backupMode is not None
    assert updateDirList is not None
    assert type(updateDirList) is tuple

    if not os.path.isdir(opts.backupDir):
        os.makedirs(opts.backupDir)

    updateDir = opts.rootDir
    for d in updateDirList:
        updateDir = os.path.join(updateDir, d)

    logging.debug("Starting backup of '%s' to '%s', mode = '%s'", updateDir, backupName, backupMode)

    with contextlib.closing(zipfile.ZipFile(os.path.join(opts.backupDir,
                                                         backupName),
                                            backupMode, zipfile.ZIP_DEFLATED)) as zipFp:
        for root, dirs, files in os.walk(updateDir):
            for f in files:
                fullFilename = os.path.join(root, f)
                zipFilename = fullFilename[len(updateDir) + len(os.sep):]
                logging.debug("zip: %s -> %s", fullFilename, zipFilename)
                zipFp.write(fullFilename, zipFilename)


def computeFolderDiffs(opts, updateDirList, newDir, logDir):
    """
    Log the diffs between the existing dir and the new one.
        updateDirList  = list of relative dirs to join with the root install dir
                         e.g. pass ('AppConfig' 'Config','Fitter')
                         for AppConfig/Config/Fitter

        newDir         = folder containing new files to install
    """

    assert newDir is not None
    assert updateDirList is not None
    assert type(updateDirList) is tuple

    origDir = opts.rootDir
    for d in updateDirList:
        os.path.join(origDir, d)

    dirCmp = filecmp.dircmp(origDir, newDir)

    origStdout = sys.stdout
    sys.stdout = open(os.path.join(logDir, 'diff.log'), 'wb')

    logging.debug("Comparing '%s' and '%s'", origDir, newDir)

    dirCmp.report_full_closure()

    sys.stdout.close()
    sys.stdout = origStdout


def copyNewFolder(opts, newDir, updateDirList):
    """
    Copy the new folder over the existing one. (Preserve any
    custom files the user may have added.)
    """
    assert updateDirList is not None

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
    assert missingToAddDict is not None

    filepath = opts.rootDir
    for d in updateDirList:
        filepath = os.path.join(filepath, d)
    filepath = os.path.join(filepath, filename)

    fChanged = False

    if os.path.isfile(filepath):
        co = CustomConfigObj(filepath)

        for key in missingToAddDict:
            try:
                # see if the key-value pair is already there
                # generates a KeyError exception if not
                co.get(section, key)

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
        appData = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
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

    """
    # AppConfig/Config/Fitter
    updateDirList = ('AppConfig', 'Config', 'Fitter')
    newDir = os.path.join(options.newFolder, 'AppConfig', 'Config', 'Fitter')
    copyNewFolder(options, newDir, updateDirList)

    # AppConfig/Scripts/DataManager
    updateDirList = ('AppConfig', 'Scripts', 'DataManager')
    newDir = os.path.join(options.newFolder, 'AppConfig', 'Scripts', 'DataManager')
    copyNewFolder(options, newDir, updateDirList)

    # AppConfig/Scripts/Fitter
    updateDirList = ('AppConfig', 'Scripts', 'Fitter')
    newDir = os.path.join(options.newFolder, 'AppConfig', 'Scripts', 'Fitter')
    copyNewFolder(options, newDir, updateDirList)
    """

    # copy all of AppConfig
    updateDirList = ('AppConfig',)
    newDir = os.path.join(options.newFolder, 'AppConfig')
    copyNewFolder(options, newDir, updateDirList)

    # InstrConfig changes
    updateDirList = ('InstrConfig', 'Calibration', 'InstrCal')
    newDir = os.path.join(options.newFolder, 'InstrConfig', 'Calibration', 'InstrCal')
    updateFilename = "InstrCal.ini"

    # back up InstrConfig/Calibration/InstrCal folder (even though we're only
    # touching a single file it contains) and log the differences
    #backupFolder(options, backupName, 'w', updateDirList)
    #computeFolderDiffs(options, updateDirList, newDir, logDir)

    backupFile(options, backupName, 'w', updateDirList, updateFilename)

    # update the InstrCal.ini file with new key-value pairs in [Data] if missing
    setupItemsToAdd = {"h2o_selfbroadening_linear":         "0.772",
                       "h2o_selfbroadening_quadratic":      "0.02525",
                       "ch4_watercorrection_linear":       "-0.0101",
                       "ch4_watercorrection_quadratic":     "0.0",
                       "ch4_hp_watercorrection_linear":    "-0.0087473",
                       "ch4_hp_watercorrection_quadratic": "-0.0002429"}

    fixupIni(options, updateDirList, updateFilename, "Data", setupItemsToAdd)


if __name__ == '__main__':
    main()
