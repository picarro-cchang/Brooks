# Bzr utilities

import os
#import sys
#import subprocess


# Folder structure examples
#
# Backup
#
# CommonConfig
#
# ...
#
# FDDSTemplates
#     AppConfig
#     InstrConfig
#
# MidIR
#     AppConfig
#     InstrConfig
#
# oldCFIDSTemplates
#     AppConfig
#     InstrConfig


def getBzrFolder(root, excludeDirs):
    """
    This function is a generator that returns the bzr repository path, and a suggested
    directory name for creating a local repository.

    Arguments are:

    root          Root folder containing the bzr configuration repos. Currently this is
                  s:\CrdsRepositoryNew\trunk\G2000\Config

    excludeDirs   Folders directly under the root folder that should be skipped because
                  they are obsolete.

    For the AppConfig and InstrConfig folders, the suggested name is the parent folder
    name (sans "Template"), followed by an underscore, and then either AppConfig or InstrConfig.

    For example,

    ...\FDDSTemplates\AppConfig returns FDDS_AppConfig for the suggested folder name.
    ...\MidIR\InstrConfig returns MidIR_InstrConfig for the suggested folder name.
    ...\CommonConfig returns CommonConfig for the suggested folder name.

    Known limitations: folder name comparisons currently are case-sensitive (for exclude
    folders, and config folder names such as CommonConfig and AppConfig).
    """

    # build list of folder paths to exclude
    excludes = []
    for d in excludeDirs:
        excludes.append(os.path.join(root, d))

    for dirpath, dirnames, filenames in os.walk(root):
        if '.bzr' in dirnames:
            dirName = os.path.split(dirpath)[1]

            # go up one level to check whether this is a dir to skip
            parentDirName = os.path.split(dirpath)[0]
            parentDirName = os.path.split(parentDirName)[1]

            fExclude = False

            for d in excludes:
                if dirpath.find(d) != -1:
                    fExclude = True
                    break

            if fExclude is True:
                # skip this dir
                pass

            elif dirName == "CommonConfig":
                # handle CommonConfig dir specially
                yield dirpath, dirName

            else:
                # build a destination folder name to return
                destName = parentDirName    # default to parent folder name

                if dirName == "AppConfig" or dirName == "InstrConfig":
                    # strip off the Templates suffix on the parent folder name if there is one
                    ix = parentDirName.find("Templates")

                    if ix != -1:
                        destName = parentDirName[0:ix]

                    destName = "".join([destName, "_", dirName])

                    yield dirpath, destName

        # no need to go any farther down if this is a .bzr folder (cannot nest bzr repos)
        if dirpath.endswith('.bzr'):
            del dirnames


if __name__ == "__main__":
    excludeDirs = ("Backup", "oldCFIDSTemplates")
    root = r"s:\CrdsRepositoryNew\trunk\G2000\Config"

    gbf = getBzrFolder(root, excludeDirs)

    for bzrDir, destDirName in gbf:
        print "bzrDir=", bzrDir
        print "    destDirName=", destDirName
        print ""