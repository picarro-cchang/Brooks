# RunTool.py
#
# For running a Win7 migration tool from the command line. Useful for developing code
# to run from sources on an instrument.
#
# Usage: python RunTool.py <toolname>.py
#
#        toolname is the filename of the Python script to run
#
# It is expected that this code is running from Tools\Win7MigrationTools folder.

import os
import sys
import subprocess


def runPythonScript(scriptName):
    assert scriptName

    # Get the current dir. Expect that we are in the Tools\Win7MigrationTools folder.
    curDirPath = os.getcwd()
    curDir = os.path.split(curDirPath)[1]

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

    print "parentDir=", parentDir
    print "firmwareDir=", firmwareDir
    print "commonDir=", commonDir
    
    # folders must exist
    folders = [parentDir, commonDir, firmwareDir]
    for folder in folders:
        print "folder=", folder
        if not os.path.isdir(folder):
            print "Expected folder '%s' does not exist!", folder
            sys.exit(1)

    buildEnv = os.environ.update({'PYTHONPATH' : "%s;%s" %(parentDir, firmwareDir)})

    #print "PYTHONPATH=", os.environ["PYTHONPATH"]
    #sys.exit(1)

    retCode = subprocess.call(['python.exe', scriptName], env=buildEnv)

    if retCode != 0:
            print "Error running '%s'. retCode=%d" % (scriptName, retCode)
            sys.exit(retCode)


def main():
    scriptName = sys.argv[1]
    runPythonScript(scriptName)


if __name__ == "__main__":
    main()