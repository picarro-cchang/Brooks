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

    buildEnv = os.environ.update({'PYTHONPATH' : "%s;%s" %(parentDir, firmwareDir)})

    # run "python PicarroExeSetup.py py2exe"
    retCode = subprocess.call(['python.exe', 'PicarroExeSetup.py', 'py2exe'], env=buildEnv)

    if retCode != 0:
            print "Error building Host. retCode=%d" % retCode
            sys.exit(retCode)

def main():
    buildExes()


if __name__ == "__main__":
    main()