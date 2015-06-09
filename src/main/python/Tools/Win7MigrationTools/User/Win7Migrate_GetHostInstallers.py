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

from distutils import dir_util
from optparse import OptionParser

#import Win7UserMigrationToolsDefs as mdefs


if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]


APP_VERSION = "1.0.0.3"

STAGED_INSTALLERS_BASE = 'S:/CRDS/CRD Engineering/Software/G2000/Installer_Staging/g2000_win7'
RELEASED_INSTALLERS_BASE = 'S:/CRDS/CRD Engineering/Software/G2000/Installer/g2000_win7'

# defined here so this script can run standalone
MIGRATION_TOOLS_FOLDER_NAME = "Win7UserMigrationTools"
INSTALLER_FOLDER_ROOT_NAME = "PicarroInstallers"


def doCopyInstallers(options):
    # source dir for grabbing installers from
    srcBaseDir = RELEASED_INSTALLERS_BASE
    bRelease = True

    if options.stagedInstallers is True:
        bRelease = False
        srcBaseDir = STAGED_INSTALLERS_BASE
        
    srcBaseDir = os.path.normpath(srcBaseDir)

    # destination dir for copying them to
    # default to the C drive
    destDrive = "C:"

    if options.destDrive is not None:
        destDrive = options.destDrive[:1] + ':'

    installerBaseDir = os.path.join(destDrive, os.path.sep,
                                    MIGRATION_TOOLS_FOLDER_NAME,
                                    INSTALLER_FOLDER_ROOT_NAME)
    installerBaseDir = os.path.normpath(installerBaseDir)

    # report settings before continuing
    print ""
    print "**** Win7Migrate_GetHostInstallers %s ****" % APP_VERSION
    print "Copying installers"
    print "Release:", bRelease
    print "  Debug:", options.debug
    print "   From: %s" % srcBaseDir
    print "     To: %s" % installerBaseDir
    print ""
    inputStr = raw_input("Hit Return to continue, or Q to quit: ")
    print ""
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
    else:
        print "rmtree and makedirs '%s'" % installerBaseDir
        print ""


    # folder names in dir expected to be analyzer type names
    installerFiles = os.listdir(srcBaseDir)

    if options.debug is True:
        print "installerFiles=", installerFiles
        print ""

    for fn in installerFiles:
        # skip AddOns dir
        if fn.lower() == "addons":
            continue

        path = os.path.join(srcBaseDir, fn)
        if os.path.isdir(path):

            # latest released installer is in the Current folder
            if bRelease is True:
                srcDir = os.path.join(path, "Current")
            else:
                srcDir = path
            destDir = os.path.join(installerBaseDir, fn)

            if options.debug is False:
                os.mkdir(destDir)
            else:
                print "mkdir(%s)" % destDir

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
            print "Copying '%s'" % fromFilename
            print "     to '%s'" % toFilename
            print ""

            if options.debug is False:
                shutil.copy2(fromFilename, toFilename)


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

