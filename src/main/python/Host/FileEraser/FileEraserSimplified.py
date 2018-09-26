#!/home/picarro/miniconda2/bin/python
# -*- coding: utf-8 -*-
# The above let's us put special characters in the comments.

"""
This is a simplied version of the FileEraser that complements the refactored
Archiver.   Its purpose is to delete old data in the Archive directory
to manage SSD space.

All output files are put into /home/picarro/I2000/Log.

Within in Log we have the most recent output files in
Log/DataLogger
Log/RDF
Log/Transient

The files in these directories are owned by the DataLogger, SpectrumCollector,
and EventManager processes and are open for writing.  When a file has reached
a size or time threshold, they are closed and the Archiver is instructed to
move the file to Log/Archive.

Some files, like the EventManager log files, are immediately copied to their
final destination.  Others, like RDFs, are appended to a growing zip file.
This zip file is eventually moved to its final destination.

The Archive files are now sorted first by date then type.  The old way was sort
by type and then date.  You'll notice that under Log/Archive we have dated
directories in the format YYYY-MM-DD or YYYY-MM-DD-RDF.  This facilitates
finding all the output files associated with an event.  See the diagram below
for an example.

Log/
├── Archive
│   ├── 2018-09-19
│   │   ├── DataLog_Private
│   │   │   └── DataLog_Private_20180919_191010.zip
│   │   ├── DataLog_Private_Text
│   │   │   └── DataLog_Private_Text_20180919_191010.zip
│   │   ├── DataLog_User
│   │   │   ├── SADS2001-20180919-013642-DataLog_User.dat
│   │   │   └── SADS2001-20180919-121221-DataLog_User.dat
│   │   ├── EventLogs
│   │   │   └── EventLog_2018_09_19_08_34_24Z.txt
│   │   └── WBCAL
│   │       └── Beta2000_WarmBoxCal_active_20180919_020447.ini
│   ├── 2018-09-19-RDF
│   │   └── RDF
│   │       ├── RDF_20180919_084433.zip
│   │       ├── RDF_20180919_085227.zip
│   │       ├── RDF_20180919_090022.zip
│   │       ├── RDF_20180919_090815.zip
│   │       ├── RDF_20180919_191010.zip
│   │       ├── RDF_20180919_192013.zip
│   │       └── RDF_20180919_192807.zip
│   ├── DataLog_Private_Text.zip
│   ├── DataLog_Private.zip
│   ├── DataLog_User_Backup.zip
│   └── RDF.zip
├── DataLogger
│   ├── DataLog_Private
│   │   └── SADS2001-20180919-121225-DataLog_Private.h5
│   ├── DataLog_Private_Text
│   │   └── SADS2001-20180919-121225-DataLog_Private_Text.dat
│   └── DataLog_User
│       ├── backup_copy
│       ├── mailbox_copy
│       │   └── SADS2001-20180919-013642-DataLog_User.dat
│       └── SADS2001-20180919-121221-DataLog_User.dat
├── RDF
│   └── RD_1537348335131.h5
└── TransientData
    └── EventLog_2018_09_19_19_10_03Z.txt

The algorithm for deleting files is simple.
1. Set the number of days of data to retain.
2. Periodically get a list of directories in Log/Archive.
3. Sort the list numerically.
4. If the list size exceeds the number of days to retain, delete the
    oldest directory or directories.

What this code won't do.
1. Monitor the size of files or directories.
2. Erase the zip files or temporary files outside of Log/Archive.  These need
    to be managed by the Archiver or originating processes.

The number of days of data to retain is determined empirically by running an
analyzer continuously and measuring the typical size for one day's worth of data
and comparing to how much disk space we will have available.  As the RDFs
are are the largest files, YYYY-MM-DD and YYYY-MM-DD-RDF directories can
have different thresholds for file deletion to maximize the number of days of
data and event logs saved.

"""

import sys
import os
import shutil
import re
import time
import glob
import getopt
import threading

from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_FILE_ERASER
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

APP_NAME = "FileEraser"
CONFIG_DIR = os.environ["PICARRO_CONF_DIR"]
LOG_DIR = os.environ["PICARRO_LOG_DIR"]

EventManagerProxy_Init(APP_NAME, DontCareConnection=True)

class FileEraserSimplified(object):
    def __init__(self, config):
        # Set defaults
        #
        # Retain 1 year of dat files
        # Retain 2 months of RDFs
        #
        self.days_of_dat_files_to_keep = \
            config["dat_days"] if "dat_days" in config else 365
        self.days_of_rdf_files_to_keep = \
            config["rdf_days"] if "rdf_days" in config else 60
        self.root_dir = "/home/picarro/I2000/Log/Archive"

        #Now set up the RPC server...
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_FILE_ERASER),
                                                ServerName = APP_NAME,
                                                ServerDescription = "",
                                                ServerVersion = 1.0,
                                                threaded = True)

    def keepErasingOldFiles(self):
        while True:
            print("Checking for things to erase", str(time.time()))
            self.deleteOldestDirectories()
            time.sleep(60)

    def generateDirectoryList(self):
        """
        Inspect /home/picarro/I2000/Log/Archive and create two sorted lists
        of directories that fit the format YYYY-MM-DD or YYYY-MM-DD-RDF.
        :return:
        """
        noRDF = []
        RDF = []
        if os.path.exists(self.root_dir):
            list1 = os.listdir(self.root_dir)
            for dir in list1:
                if re.match(r'.*\d{4}-\d{2}-\d{2}$', dir):
                    noRDF.append(os.path.join(self.root_dir, dir))
                if re.match(r'.*\d{4}-\d{2}-\d{2}-RDF$', dir):
                    RDF.append(os.path.join(self.root_dir, dir))
        return (sorted(noRDF), sorted(RDF))

    def deleteOldestDirectories(self):
        noRDF = []
        RDF = []
        noRDF_deletion_count = 0
        RDF_deletion_count  = 0
        noRDF, RDF = self.generateDirectoryList()
        while len(noRDF) > self.days_of_dat_files_to_keep:
            noRDF_deletion_count += 1
            shutil.rmtree(noRDF[0])
            noRDF, RDF = self.generateDirectoryList()
        while len(RDF) > self.days_of_rdf_files_to_keep:
            RDF_deletion_count += 1
            shutil.rmtree(RDF[0])
            noRDF, RDF = self.generateDirectoryList()
        print("Deleted {} dat directories and {} RDF directories.".format(noRDF_deletion_count, RDF_deletion_count))

    def runApp(self):
        rpcThread = threading.Thread(target = self.keepErasingOldFiles)
        rpcThread.setDaemon(True)
        rpcThread.start()
        self.RpcServer.serve_forever()


def HandleCommandSwitches():
    config = {}
    shortOpts = ''
    longOpts = ["dat_days=", "rdf_days="]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError as data:
        print "%s %r" % (data, data)
        sys.exit(1)

    # assemble a dictionary where the keys are the switches and values are
    # switch args...
    options = {}
    for o, a in switches:
        options[o] = a
    configFile = ""
    if "--dat_days" in options:
        config["dat_days"] = int(options["--dat_days"])
    if "--rdf_days" in options:
        config["rdf_days"] = int(options["--rdf_days"])
    return (config)

def main():
    #Get and handle the command line options...
    config = HandleCommandSwitches()
    Log("%s started." % APP_NAME, config, Level = 0)
    try:
        fEraser = FileEraserSimplified(config)
        fEraser.runApp()
        Log("Exiting program")
    except Exception, E:
        # if DEBUG: raise
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))

if __name__ == "__main__":
    # DEBUG = __debug__
    main()