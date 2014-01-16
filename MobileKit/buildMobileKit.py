# buildMobileKit.py
#
# Set up the build environment and build MobileKit components. Use this
# for building MobileKit from the command line.
#
# This executes python setup.py py2exe and ensures PYTHONPATH is properly
# set to pull local libs from its own folder tree instead of what is
# in Picarro.pth.
#
# This script can be run from a cmd window. setup.py should NOT be run
# from a cmd window unless PYTHONPATH or Picarro.pth is pointing to this tree.
# Otherwise, there is the risk of pulling Picarro libs from the wrong folder
# into the build.

import os
import sys
import subprocess


def buildExes():
    # Get the current dir. Expect that we are in the MobileKit folder.
    curDirPath = os.getcwd()
    curDir = os.path.split(curDirPath)[1]

    # Windows dirs are not case-sensitive. 
    # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
    if curDir.lower() != "mobilekit":
        print "Not running in expected folder 'MobileKit'!"
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

    print os.environ["PYTHONPATH"]
    import time
    time.sleep(10)

    # run "python setup.py py2exe"
    retCode = subprocess.call(['python.exe', 'setup.py', 'py2exe'], env=buildEnv)
                                  
    if retCode != 0:
            print "Error building MobileKit. retCode=%d" % retCode
            sys.exit(retCode)

def main():
    buildExes()


if __name__ == "__main__":
    main()