import os
#import sys
import subprocess

dest = r"c:\temp\Templates"
#dest = r"C:\Users\twalder\Documents\Testing\TemplateResults"

# Find all the bzr repositories under root
#root = r"s:\CrdsRepositoryNew\Releases\G2000\1.3\Config"
root = r"s:\CrdsRepositoryNew\trunk\G2000\Config"

for base, dirs, files in os.walk(root):
    if '.bzr' in dirs:
        # This is a bzr directory, find the portion
        #  which excludes root
        destDir = os.path.join(dest, base[len(root)+1:])
        try:
            os.makedirs(destDir)
        except:  # Already exists
            pass

        os.chdir(destDir)
        subprocess.call(["bzr", "branch", "--use-existing-dir", base, "."])

    if base.endswith('.bzr'):
        del dirs
