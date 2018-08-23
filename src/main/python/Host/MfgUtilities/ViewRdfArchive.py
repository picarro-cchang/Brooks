#!/usr/bin/python
#
# File Name: ViewRdfArchive.py
# Purpose:
#   This application allows the user to extract information from zipped H5 files
# which contain ring-down information from a G2000 instrument.
#
# Notes:
#
# ToDo:
#
# File History:
# 2010-03-03 sze   First release

APP_NAME = "Archiver"
__version__ = 1.0
_DEFAULT_CONFIG_NAME = "Archiver.ini"
_MAIN_CONFIG_SECTION = "MainConfig"

import sys
import os
import zipfile
import tables
import numpy
from tempfile import mkdtemp

def sortByName(top,nameList):
    nameList.sort()
    return nameList

def sortByMtime(top,nameList):
    """Sort a list of files by modification time"""
    # Decorate with the modification time of the file for sorting
    fileList = [(os.path.getmtime(os.path.join(top,name)),name) for name in nameList]
    fileList.sort()
    return [name for t,name in fileList]

def walkTree(top,onError=None,sortDir=None,sortFiles=None):
    """Generator which traverses a directory tree rooted at "top" in bottom to top order (i.e., the children are visited
    before the parent, and directories are visited before files.) The order of directory traversal is determined by
    "sortDir" and the order of file traversal is determined by "sortFiles". If "onError" is defined, exceptions during
    directory listings are passed to this function. When the function yields a result, it is either the pair
    ('file',fileName)  or ('dir',directoryName)"""
    try:
        names = os.listdir(top)
    except OSError, err:
        if onError is not None:
            onError(err)
        return
    # Obtain lists of directories and files which are not links
    dirs, nondirs = [], []
    for name in names:
        fullName = os.path.join(top,name)
        if not os.path.islink(fullName):
            if os.path.isdir(fullName):
                dirs.append(name)
            else:
                nondirs.append(name)
    # Sort the directories and nondirectories (in-place)
    if sortDir is not None:
        dirs = sortDir(top,dirs)
    if sortFiles is not None:
        nondirs = sortFiles(top,nondirs)
    # Recursively call walkTree on directories
    for dir in dirs:
        for x in walkTree(os.path.join(top,dir),onError,sortDir,sortFiles):
            yield x
    # Yield up files
    for file in nondirs:
        yield 'file', os.path.join(top,file)
    # Yield up the current directory
    yield 'dir', top

if __name__ == "__main__":
    dirName = raw_input("Directory containing files to analyze: ")
    tempDirname  = mkdtemp()
    tempFilename = os.path.join(tempDirname,"tempFile.h5")
    nDecim = 100
    start = 0
    result = []
    for what,name in walkTree(dirName,onError=None,sortDir=sortByMtime,sortFiles=sortByMtime):
        if what == 'dir': continue
        # Go through zip files looking for H5 files
        if not zipfile.is_zipfile(name):
            print "Skipping non-zip file: %s" % name
            continue
        # Sort entries within zip file into order of ascending time
        zip = zipfile.ZipFile(name,"r")
        zipInfoList = zip.infolist()
        decZipInfoList = [(zipInfo.date_time,zipInfo.filename) for zipInfo in zipInfoList]
        decZipInfoList.sort()
        # Iterate over the H5 files
        for dateTime,name in decZipInfoList:
            if os.path.splitext(name)[-1] != ".h5":
                print "Skipping non-HDF5 file: %s" % name
                continue
            # Make a file-like object from the string in the ZIP file
            tp = file(tempFilename,"wb")
            tp.write(zip.read(name))
            tp.close()
            h5 = tables.openFile(tempFilename)
            table = h5.root.rdData
            result.append(table.read(field="timestamp",start=start,stop=table.nrows,step=nDecim))
            start = start + nDecim*(1+(table.nrows-start-1)//nDecim) - table.nrows
            h5.close()
            print name
    os.remove(tempFilename)
    os.rmdir(tempDirname)
    result = numpy.concatenate(result)