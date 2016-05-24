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

# When built, the file will exist in the local dir
#pylint: disable=F0401
try:
    import Path
except ImportError:
    from Host.Common import Path
#pylint: enable=F0401


DEFAULT_INSTALL_DIR = r'c:\Picarro\G2000'
DEFAULT_BACKUP_DIR = r'c:\Backup'


def backupCoordinator(opts):
    """
    Create a zipped backup of the existing Coordinator directory.
    """

    assert opts.backupDir is not None
    assert opts.rootDir is not None

    if not os.path.isdir(opts.backupDir):
        os.makedirs(opts.backupDir)

    backupName = "Coordinator-%s.zip" % time.strftime("%Y%m%d-%H%M%SZ",
                                                    time.gmtime())
    coordinatorDir = os.path.join(opts.rootDir, 'AppConfig', 'Config',
                                  'Coordinator')

    logging.debug("Starting backup of '%s' to '%s'", coordinatorDir, backupName)

    with contextlib.closing(zipfile.ZipFile(os.path.join(opts.backupDir,
                                                         backupName),
                                            'w', zipfile.ZIP_DEFLATED)) as zipFp:
        for root, dirs, files in os.walk(coordinatorDir):
            for f in files:
                fullFilename = os.path.join(root, f)
                zipFilename = fullFilename[len(coordinatorDir) + len(os.sep):]
                logging.debug("zip: %s -> %s", fullFilename, zipFilename)
                zipFp.write(fullFilename, zipFilename)

def computeCoordinatorDiffs(opts, logDir):
    """
    Log the diffs between the existing Coordinator dir and the new one.
    """

    assert opts.newCoordinator is not None

    origCoordinator = os.path.join(opts.rootDir, 'AppConfig', 'Config',
                                   'Coordinator')
    dirCmp = filecmp.dircmp(origCoordinator, opts.newCoordinator)

    origStdout = sys.stdout
    sys.stdout = open(os.path.join(logDir, 'diff.log'), 'wb')

    logging.debug("Comparing '%s' and '%s'", origCoordinator,
                  opts.newCoordinator)

    dirCmp.report_full_closure()

    sys.stdout.close()
    sys.stdout = origStdout


def copyNewCoordinator(opts):
    """
    Copy the new Coordinator over the existing one. (Preserve any
    custom files the user may have added.)
    """

    newCoordinatorDirs = Path.splitToDirs(os.path.abspath(opts.newCoordinator))

    logging.debug("newCoordinatorDirs = '%s'",
                  pprint.pformat(newCoordinatorDirs))

    for root, dirs, files in os.walk(opts.newCoordinator):
        logging.debug("Copying '%s'", root)

        if '.bzr' in dirs:
            logging.debug('Removing .bzr from traversal list')
            dirs.remove('.bzr')

        relativePathDirs = Path.splitToDirs(os.path.abspath(root))
        relativePath = [d for d in relativePathDirs if d not in newCoordinatorDirs]

        if not relativePath:
            # At first level, root will be empty path.
            relativePath = ['']

        relativePath = os.path.join(*relativePath)

        for f in files:
            logging.debug("Move '%s' -> '%s'", os.path.join(root, f),
                          os.path.join(opts.rootDir, 'AppConfig', 'Config',
                                       'Coordinator', relativePath))
            shutil.copy2(os.path.join(root, f),
                         os.path.join(opts.rootDir, 'AppConfig', 'Config',
                                      'Coordinator', relativePath))

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
                      help='Directory to store coordinator backups in.')
    parser.add_option('-r', '--root', dest='rootDir',
                      metavar='ROOT_DIR', default=DEFAULT_INSTALL_DIR,
                      help=('Root installation directory of the Picarro G2000'
                            'package.'))
    parser.add_option('-n', '--new-coordinator', dest='newCoordinator',
                      metavar='NEW_COORDINATOR_DIR',
                      help='Directory where the new Coordinator is stored.')

    options, _ = parser.parse_args()

    logDir = os.path.join(appData, 'Picarro', 'G2000', 'Log', 'Special', '698')

    if not os.path.isdir(logDir):
        os.makedirs(logDir)

    logging.basicConfig(level=logging.DEBUG,
                        format=('%(asctime)s [%(levelname)s] (%(funcName)s, '
                                '%(lineno)d) %(message)s'),
                        filename=os.path.join(logDir, 'patch.log'),
                        filemode='w')

    backupCoordinator(options)
    computeCoordinatorDiffs(options, logDir)
    copyNewCoordinator(options)


if __name__ == '__main__':
    main()
