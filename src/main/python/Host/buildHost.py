# buildHost.py
#
# Set up the build environment and build Host components. Use this
# for building Host from the command line.
#
# This executes python PicarroExeSetup.py py2exe and ensures PYTHONPATH is properly
# set to pull local libs from its own folder tree instead of what is
# in Picarro.pth.
#
# This script can be run from a cmd window. PicarroExeSetup.py should NOT be run
# from a cmd window unless PYTHONPATH or Picarro.pth is pointing to this tree.
# Otherwise, there is the risk of pulling Picarro libs from the wrong folder
# into the build.

import os
import sys
import subprocess
import textwrap
import time
import platform

from optparse import OptionParser

try:
    import simplejson as json
except ImportError:
    import json

versionConfig = "version.json"

VERSION = {}


def _getOsType():
    """ Returns 'win7', 'winxp' or 'unknown'. """

    osType = platform.uname()[2]

    if osType == '7':
        osType = 'win7'
    elif osType == 'XP':
        osType = 'winxp'
    elif (platform.uname()[3]).startswith("6.2"):
        osType = 'win10'
    else:
        osType = 'unknown'
        print "Unexpected OS type!"
        sys.exit(1)

    return osType


def _generateBuildVersion(product, osType, ver):
    """
    Create a file ('build_version.py') containing the version metadata used 
    for building the executables
    """

    contents = textwrap.dedent("""\
    # autogenerated by buildHost.py, %s
    
    def versionString():
        return '%s'
    
    def versionNumString():
        return '%s'
    
    def buildType():
        return 'INTERNAL'
    """)

    with open('build_version.py', 'w') as fp:
        fp.write(contents % (time.asctime(), _verAsString(product, ver, osType), _verAsNumString(ver)))


def _verAsNumString(ver):
    """
    Convert a version dict into a string of numbers in this format:
        <major>.<minor>.<revision>.<build>
    """
    number = "%(major)s.%(minor)s.%(revision)s.%(build)s" % ver
    return number


def _verAsString(product, ver, osType=None):
    """
    Convert a version dict into a human-readable string.
    """

    number = _verAsNumString(ver)

    if osType is not None:
        return "%s-%s-%s" % (product, osType, number)
    else:
        return "%s-%s" % (product, number)


def buildExes():
    # Get the current dir. Expect that we are in the Host folder.
    curDirPath = os.getcwd()
    curDir = os.path.split(curDirPath)[1]

    # Windows dirs are not case-sensitive.
    # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
    if curDir.lower() != "host":
        print "Not running in expected folder 'Host'!"
        sys.exit(1)

    # Set the PYTHONPATH environment variable so the current folder tree is used to
    # pull local libraries from.
    parentDir = os.path.normpath(os.path.join(curDirPath, ".."))
    firmwareDir = os.path.normpath(os.path.join(curDirPath, "..", "Firmware"))

    # for a sanity check -- not needed in PYTHONPATH as the parent dir will already be there
    commonDir = os.path.join(parentDir, "Host", "Common")

    # folders must exist
    folders = [parentDir, commonDir, firmwareDir]
    for folder in folders:
        print "folder=", folder
        if not os.path.isdir(folder):
            print "Expected folder '%s' does not exist!", folder
            sys.exit(1)

    buildEnv = dict(os.environ)
    buildEnv.update({'PYTHONPATH': "%s;%s" % (parentDir, firmwareDir)})

    # run "python PicarroExeSetup.py py2exe"
    retCode = subprocess.call(['python.exe', 'PicarroExeSetup.py', 'py2exe'], env=buildEnv)

    if retCode != 0:
        print "Error building Host. retCode=%d" % retCode
        sys.exit(retCode)


def main():
    usage = """
%prog [options]

Builds a local HostExe.
"""

    parser = OptionParser(usage=usage)

    # default is g2000, so fetch version number from g2000_version.json
    parser.add_option('--product',
                      dest='product',
                      metavar='PRODUCT',
                      default='g2000',
                      help=('The product to use the JSON version number from '
                            'for an internal build. Default is "g2000".'))

    options, _ = parser.parse_args()

    versionConfig = options.product + "_version.json"

    # folder containing version file
    versionConfig = os.path.normpath(os.path.join(os.getcwd(), "..", "Tools", "Release", versionConfig))

    # construct json filename from the product
    # get version from the json file
    with open(versionConfig, 'r') as ver:
        VERSION.update(json.load(ver))

    # use the OS type to construct a product name for the version
    # this script is for internal builds only so tacking on
    # 'internal' in the product name
    osType = _getOsType()
    product = "%s-INTERNAL" % options.product

    if not os.path.exists('build_version.py'):
        _generateBuildVersion(product, osType, VERSION)

    # build the executables
    buildExes()


if __name__ == "__main__":
    main()
