# buildWin7MigrationTools.py
#
# Set up the build environment and builds Win7 migration tools. Use this
# for building the apps from the command line.
#
# This executes python setupWin7MigrationTools.py py2exe and ensures PYTHONPATH is properly
# set to pull local libs from its own folder tree instead of what is
# in Picarro.pth.

import os
import sys
import subprocess

from distutils import dir_util
from optparse import OptionParser

import Win7MigrationToolsDefs as mdefs


MIGRATION_TOOLS_DISTRIB_BASE = 's:/CRDS/CRD Engineering/Software/G2000/Win7MigrationTools_Staging'


def _buildExes():
    # Get the current dir. Expect that we are in the Host folder.
    curDirPath = os.getcwd()
    curDir = os.path.split(curDirPath)[1]

    print curDir

    # Windows dirs are not case-sensitive. 
    # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
    if curDir.lower() != "win7migrationtools":
        print "Not running in expected folder 'Win7MigrationTools'!"
        sys.exit(1)
    
    # Set the PYTHONPATH environment variable so the current folder tree is used to
    # pull local libraries from.
    parentDir = os.path.normpath(os.path.join(curDirPath, "..", ".."))
    firmwareDir = os.path.normpath(os.path.join(curDirPath, "..", "..", "Firmware"))
    
    # for a sanity check -- not needed in PYTHONPATH as the parent dir will already be there
    commonDir = os.path.join(parentDir, "Host", "Common")
    
    # folders must exist
    folders = [parentDir, commonDir, firmwareDir]
    for folder in folders:
        print "folder=", folder
        if not os.path.isdir(folder):
            print "Expected folder '%s' does not exist!", folder
            sys.exit(1)

    buildEnv = os.environ.update({'PYTHONPATH' : "%s;%s" %(parentDir, firmwareDir)})

    # run "python setupWin7MigrationTools.py py2exe"
    retCode = subprocess.call(['python.exe', 'setupWin7MigrationTools.py', 'py2exe'], env=buildEnv)

    if retCode != 0:
            print "Error building Host. retCode=%d" % retCode
            sys.exit(retCode)


def _copyBuild():
    # Destination folder is named with the version number (for now)
    destDir = os.path.join(MIGRATION_TOOLS_DISTRIB_BASE, mdefs.MIGRATION_TOOLS_VERSION)

    # Clean the folder if it exists, and make sure the folder tree exists
    if os.path.isdir(destDir):
        os.rmdir(destDir)
    assert not os.path.isdir(destDir)
    os.makedirs(destDir)

    # source folder path is the dist folder under this folder
    sourceDir = os.path.join(os.getcwd(), 'dist')

    print "sourceDir = '%s'" % sourceDir
    print "destDir   = '%s'" % destDir

    # do the copy
    dir_util.copy_tree(sourceDir, destDir)


def main():
    usage = """
%prog [options]

Builds the Win7 migration tools.
"""

    parser = OptionParser(usage=usage)

    parser.add_option('--debug-local', dest='local',
                      action='store_true', default=False,
                      help=("Don't copy migration tools to the network after building them."))

    parser.add_option('-v', '--version', dest='version',
                      action='store_true', default=False,
                      help=('Report the current version number that will be used building the migration tools.'))

    options, _ = parser.parse_args()


    if options.version:
        print mdefs.MIGRATION_TOOLS_VERSION
        sys.exit(0)

    _buildExes()

    if not options.local:
        _copyBuild()


if __name__ == "__main__":
    main()