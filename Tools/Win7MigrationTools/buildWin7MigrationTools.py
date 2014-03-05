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
import platform
import shutil
import time

from distutils import dir_util
from optparse import OptionParser

import Win7MigrationToolsDefs as mdefs


MIGRATION_TOOLS_DISTRIB_BASE = 's:/CRDS/CRD Engineering/Software/G2000/Installer_Staging'


def _buildExes(scriptName, toolsList):
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

    # pass a semicolon-separated list of the tools to build in the environment
    # I don't the setup script can have command line arguments because py2exe will try to interpret them
    isFirst = True
    toolsStr = ""

    for tool in toolsList:
        if not isFirst:
            toolsStr = toolsStr + ";" + tool
        else:
            toolsStr = tool
            isFirst = False

    buildEnv = os.environ.update({'TOOLSBUILDLIST' : toolsStr})

    # run "python <scriptName> py2exe"
    retCode = subprocess.call(['python.exe', scriptName, 'py2exe'], env=buildEnv)

    if retCode != 0:
            print "Error running %s. retCode=%d" % (scriptName, retCode)
            sys.exit(retCode)


def _copyBuild():
    destDir = MIGRATION_TOOLS_DISTRIB_BASE

    print "copying build to ", destDir

    # Clean the folder if it exists, and make sure the folder tree exists
    if os.path.isdir(destDir):
        shutil.rmtree(destDir)

    assert not os.path.isdir(destDir)
    os.makedirs(destDir)

    # source folder path is the dist folder under this folder
    sourceDir = os.path.join(os.getcwd(), 'dist')

    #print "sourceDir = '%s'" % sourceDir
    #print "destDir   = '%s'" % destDir

    # do the copy
    dir_util.copy_tree(sourceDir, destDir)


def _printSummary(options, toolsList):
    print ""
    if options.local:
        print "local build:      YES"
    else:
        print "local build:      NO"

    if options.product is not None:
        print "build product:    %s" % options.product
    else:
        print "build product:    both"

    print ""
    print "building tools:  %s" % toolsList
    print ""
    print "MIGRATION_TOOLS_DISTRIB_BASE: %s" % MIGRATION_TOOLS_DISTRIB_BASE

    print ""


def _getOSType():
    # this is either 'XP' (WinXP) or '7' (Win7)
    osType = platform.uname()[2]

    if osType == '7':
        osType = 'win7'
    elif osType == 'XP':
        osType = 'winxp'
    else:
        osType = 'unknown'
        print "Unsupported OS type!"
        sys.exit(1)

    return osType


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

    parser.add_option('--product', dest='product',
                      default='both', choices=['part1', 'part2', 'both'],
                      help=('The migration tool to build on this platform. Valid arguments are: '
                            'part1, part2, both. '
                            'Default is to build both Part 1 and Part 2 tools.'))

    parser.add_option('--no-confirm', dest='skipConfirm',
                      action='store_true', default=False,
                      help=('Don\'t ask for confirmation of build settings before '
                            'proceeding with the build.'))


    options, _ = parser.parse_args()


    if options.version:
        print mdefs.MIGRATION_TOOLS_VERSION
        sys.exit(0)

    # use the current OS to set the destination folder for copy to staging area
    # MigrationTools_win7
    osType = _getOSType()

    global MIGRATION_TOOLS_DISTRIB_BASE

    if options.local:
        # replace S: with C: for local builds
        MIGRATION_TOOLS_DISTRIB_BASE = 'C' + MIGRATION_TOOLS_DISTRIB_BASE[1:]

    # list of apps to build, to be passed in the environment
    toolsList = ["Win7Migrate_Part1.py", "Win7Migrate_Part2.py"]
    toolsFolder = "MigrationTools"

    if options.product is not None:
        if options.product == "part1":
            toolsList = ["Win7Migrate_Part1.py"]
            toolsFolder = "MigrationPart1"

        elif options.product == "part2":
            toolsList = ["Win7Migrate_Part2.py"]
            toolsFolder = "MigrationPart2"

    toolsFolder = "%s_%s" % (toolsFolder, osType)
    MIGRATION_TOOLS_DISTRIB_BASE = os.path.normpath(os.path.join(MIGRATION_TOOLS_DISTRIB_BASE, toolsFolder))

    _printSummary(options, toolsList)

    # ask user for build confirmation before proceeding
    if not options.skipConfirm:
        print ""
        response = raw_input("OK to continue? Y or N: ")

        if response == "Y" or response == "y":
            print "Y typed, continuing"
        else:
            print "Win7 Migration Tools build canceled"
            sys.exit(0)

    # delete the dist folder
    distDir = os.path.join(os.getcwd(), "dist")
    if os.path.isdir(distDir):
            shutil.rmtree(distDir)

    _buildExes("setupWin7MigrationTools.py", toolsList)

    _copyBuild()


if __name__ == "__main__":
    main()
