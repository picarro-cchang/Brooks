# Win7Migrate_GetHostInstallers.py
#
# By default grabs the released host installers from the network and
# copies them to the expected folder on the C: drive.
#
# There are command line options to specify a different target drive
# and to grab staged installers instead.
# 
# This is an internal tool only, not distributed as an exe so
# it is separately versioned.
#
# Notes:
#
# History
#
# 2014-03-28  tw  Initial version.
from __future__ import with_statement

import os
import sys
import shutil
import time
import logging
import ConfigParser
#import wx

from distutils import dir_util
from optparse import OptionParser

import Win7UserMigrationToolsDefs as mdefs
import Win7UserMigrationUtils as mutils

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]


APP_VERSION = "1.0.0.1"

STAGED_INSTALLERS_BASE = 'S:/CRDS/CRD Engineering/Software/G2000/Installer_Staging/g2000_win7'
RELEASED_INSTALLERS_BASE = 'S:/CRDS/CRD Engineering/Software/G2000/Installer/g2000_win7'



def doCopyInstallers(options):
    # source dir for grabbing installers from
    srcBaseDir = RELEASED_INSTALLERS_BASE
    bRelease = True

    if options.stagedInstallers is True:
        bRelease = False
        srcBaseDir = STAGED_INSTALLERS_BASE

    # destination dir for copying them to
    # default is the current drive (result looks like 'C:')
    destDrive = os.path.splitdrive(os.getcwd())[0]

    if options.destDrive is not None:
        destDrive = options.destDrive[:1] + ':'

    installerBaseDir = os.path.join(destDrive, os.path.sep,
                                    mdefs.MIGRATION_TOOLS_FOLDER_NAME,
                                    mdefs.INSTALLER_FOLDER_ROOT_NAME)
    installerBaseDir = os.path.normpath(installerBaseDir)

    # report settings before continuing
    print "Copying installers"
    print "Release:", bRelease
    print "  Debug:", options.debug
    print "   From: %s" % srcBaseDir
    print "     To: %s" % installerBaseDir
    print ""
    inputStr = raw_input("Hit Return to continue, or Q to quit: ")
    inputStr = inputStr.upper()

    # bail if user wants to exit now
    if inputStr == "Q":
        print "Copying host installers aborted, exiting."
        sys.exit(0)

    # --------------------
    # Copy the installers

    # clean the destination folder
    if options.debug is False:
        if os.path.isdir(installerBaseDir):
            shutil.rmtree(installerBaseDir)
        os.makedirs(installerBaseDir)

    # folder structure of the release installers is different than staged
    if bRelease is True:
        # release installers - copy the installer setup_xxx.exe file that is in
        # the Current folder for the instrument; need to put it under the
        # instrument type folder
        #
        # returns a list of files and folders (just the name, not a full path)
        installerFiles = os.listdir(srcBaseDir)

        print "installerFiles=", installerFiles

        for fn in installerFiles:
            path = os.path.join(srcBaseDir, fn)
            if os.path.isdir(path):
                srcDir = os.path.join(path, "Current")
                destDir = os.path.join(installerBaseDir, fn)

                if options.debug is False:
                    os.mkdir(destDir)
                else:
                    "print mkdir(%s)" % destDir

                setupFiles = os.listdir(srcDir)
                assert len(setupFiles) == 1
                setupFile = setupFiles[0]

                # validate the filename
                # example is setup_AEDS_NH3_g2000_win7-1.5.0-23.exe
                assert setupFile.find("setup_%s" % fn) == 0
                assert setupFile.find("g2000_win7") > 0

                fromFilename = os.path.join(srcDir, setupFile)
                toFilename = os.path.join(destDir, setupFile)

                # copy the setup file
                print ""
                print "Copying '%s'" % fromFilename
                print "     to '%s'" % toFilename

                if options.debug is False:
                    shutil.copy2(fromFilename, toFilename)

    else:
        # staged installers - just copy the folder because each instrument folder
        # contains its installer setup_xxx.exe file
        print "Copy folder '%s'" % srcBaseDir
        print "         to '%s'" % installerBaseDir

        if options.debug is False:
            dir_util.copy_tree(srcBaseDir, installerBaseDir)


    # Reiterate paths (may have scrolled off the top of any output)
    if options.debug is False:
        print ""
        print "Copying host installers completed!"
        print "From: %s" % srcBaseDir
        print "  To: %s" % installerBaseDir
    else:
        print ""
        print "Debug, no files actually copied"


def main():
    usage = """
%prog [options]

Win7 migration utility to copy network installers to local drive.
"""

    parser = OptionParser(usage=usage)

    parser.add_option('-v', '--version', dest='version', action='store_true',
                      default=False, help=('Report the version number.'))

    parser.add_option('--debug', dest='debug', action='store_true',
                      default=False, help=('Enables debugging.'))

    parser.add_option('--stagedInstallers', dest="stagedInstallers",
                      action='store_true', default=False,
                      help=('Copies the staged installers instead of released. '
                      'Default is to copy the released installers.'))

    parser.add_option('--drive', dest='destDrive',
                      default=None, help=('Set destination drive letter. '
                                          'Default is current drive letter.'))

    options, _ = parser.parse_args()

    if options.version is True:
        print APP_VERSION
        sys.exit(0)

    doCopyInstallers(options)


if __name__ == "__main__":
    main()

