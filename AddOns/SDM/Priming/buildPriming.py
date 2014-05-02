# buildPriming.py
#
# Set up the build environment and build Host components. Use this
# for building CentrisPumpPriming.exe from the command line.
#
# This executes python primingSetup.py py2exe and ensures PYTHONPATH is properly
# set to pull local libs from its own folder tree instead of what is
# in Picarro.pth.
#
# This script can be run from a cmd window. primingSetup.py should NOT be run
# from a cmd window unless PYTHONPATH or Picarro.pth is pointing to this tree.
# Otherwise, there is the risk of pulling Picarro libs from the wrong folder
# into the build.

import os
import sys
import subprocess
import time
import platform

try:
    import simplejson as json
except ImportError:
    import json


# set these to avoid customizing the rest of the script
folderName = "Priming"
buildScriptName = "buildPriming.py"   # this script name
setupScriptName = "primingSetup.py"   # setup script for running py2exe
productName = "CentrisPumpPriming"    # for the internal name string shown for non-release builds

versionConfig = "version.json"

VERSION = {}


def _getOsType():
    osType = platform.uname()[2]

    if osType == '7':
        osType = 'win7'
    elif osType == 'XP':
        osType = 'winxp'
    else:
        osType = 'unknown'
        print "Unexpected OS type!"
        sys.exit(1)

    return osType


def buildExes():
    # Get the current dir.
    curDirPath = os.getcwd()
    curDir = os.path.split(curDirPath)[1]

    # Windows dirs are not case-sensitive. 
    # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
    if curDir.lower() != folderName.lower():
        print "Not building from expected folder '%s'!" % folderName
        sys.exit(1)
    
    # Set the PYTHONPATH environment variable so the current folder tree is used for Host.Common libraries.
    parentDir = os.path.normpath(os.path.join(curDirPath, "..", "..", ".."))

    # for a sanity check -- not needed in PYTHONPATH as the parent dir will already be there
    commonDir = os.path.join(parentDir, "Host", "Common")

    # folders that must exist
    folders = [parentDir, commonDir]
    for folder in folders:
        print "folder=", folder
        if not os.path.isdir(folder):
            print "Expected folder '%s' does not exist!", folder
            sys.exit(1)

    buildEnv = dict(os.environ)
    buildEnv.update({'PYTHONPATH' : "%s" % parentDir})

    # run "python primingSetup.py py2exe"
    retCode = subprocess.call(['python.exe', setupScriptName, 'py2exe'], env=buildEnv)

    if retCode != 0:
            print "Error building %s, retCode=%d" % (productName, retCode)
            sys.exit(retCode)


def _generateBuildVersion(product, osType, ver):
    """
    Create the version metadata used by the executables and update the
    pretty version string. File is created in the local directory
    since this script is for command line builds intended for testing.
    """

    # filename is setup_version.py even though it is created by this
    # build script.
    with open('setup_version.py', 'w') as fp:
        fp.writelines(
            ["# autogenerated by %s, %s\n" % (buildScriptName, time.asctime()),
             "\n",
             "def versionString():\n",
             "    return '%s'\n" % _verAsString(product, ver, osType),
             "\n",
             "def versionNumString():\n",
             "    return '%s'\n" % _verAsNumString(ver),
             "\n",
             "def versionNumStringUI():\n",
             "    return '%s'\n" % _verAsNumStringUI(ver),
             "\n",
             "def buildType():\n",
             "    return 'INTERNAL'\n",
             "\n"
            ])


def _verAsString(product, ver, osType=None):
    """
    Convert a version dict into a human-readable string.
    """

    number = "%(major)s.%(minor)s.%(revision)s-%(build)s" % ver

    if osType is not None:
        return "%s-%s-%s" % (product, osType, number)
    else:
        return "%s-%s" % (product, number)


def _verAsNumString(ver):
    """
    Convert a version dict into a string of numbers in this format:
        <major>.<minor>.<revision>.<build>
    """

    number = "%(major)s.%(minor)s.%(revision)s.%(build)s" % ver
    return number


def _verAsNumStringUI(ver):
    """
    Convert a version dict into a string of numbers in this format:
        <major>.<minor>.<revision>-<build>
    """

    number = "%(major)s.%(minor)s.%(revision)s-%(build)s" % ver
    return number


def main():

    # get version from the json file (in the parent SDM folder)
    sdmFolder = os.path.split(os.getcwd())[0]
    verConfigFile = os.path.join(sdmFolder, versionConfig)

    with open(verConfigFile, 'r') as ver:
            VERSION.update(json.load(ver))

    # use the OS type to construct a product name for the version
    # this script is for internal builds only so tacking on
    # 'internal' in the product name
    osType = _getOsType()
    product = "%s-%s-INTERNAL" % (productName, osType)

    _generateBuildVersion(product, osType, VERSION)

    buildExes()


if __name__ == "__main__":
    main()