#!/usr/bin/python
"""
FILE:
  selectCalRDFs.py

DESCRIPTION:
  Utility to go through a collection of RDF files in a directory and move those files
  which have no ringdown calibration rows into a subdirectory

SEE ALSO:
  Specify any related information.

HISTORY:
  11-Dec-2013  sze  Initial version

 Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
from tables import openFile
from glob import glob
from shutil import move
import os

if __name__ == "__main__":
    dirName = r"C:\temp\CorruptingRDFS\RDF"
    try:
        subDir = os.path.join(dirName, "nocal")
        os.makedirs(subDir)
    except WindowsError:  # If directory already exists
        pass
    fileNames = glob(os.path.join(dirName, "*.h5"))
    for fileName in fileNames:
        with openFile(fileName, "r") as h5:
            ssid = h5.root.rdData.col("subschemeId")
        cal = any(ssid & 4096)
        if not cal:
            newName = os.path.join(subDir, os.path.split(fileName)[-1])
            print "Moving %s to %s" % (fileName, newName)
            move(fileName, newName)