import os
#import sys
import subprocess
import bzrUtils as bu

dest = r"c:\temp\Templates"
#dest = r"C:\Users\twalder\Documents\Testing\TemplateResults"

# Find all the bzr repositories under root
#root = r"s:\CrdsRepositoryNew\Releases\G2000\1.3\Config"
root = r"s:\CrdsRepositoryNew\trunk\G2000\Config"
excludeDirs = ("Backup", "oldCFIDSTemplates")

# create generator to enumerate the bzr folders
gbf = bu.getBzrFolder(root, excludeDirs)

for bzrDir, destDirName in gbf:
    destDir = os.path.join(dest, destDirName)

    print ""
    print "bzrDir=", bzrDir
    print "destDir=", destDir

    try:
        os.makedirs(destDir)
    except:  # Already exists
        pass

    os.chdir(destDir)
    subprocess.call(["bzr", "branch", "--use-existing-dir", bzrDir, "."])
