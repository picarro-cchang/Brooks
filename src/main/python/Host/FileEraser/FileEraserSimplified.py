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
2. Erase the zip files or temporary files outside of Log/Archive/ComboLogger.
    These need to be managed by the Archiver or originating processes.

The number of days of data to retain is determined empirically by running an
analyzer continuously and measuring the typical size for one day's worth of data
and comparing to how much disk space we will have available.  As the RDFs
are are the largest files, YYYY-MM-DD and YYYY-MM-DD-RDF directories can
have different thresholds for file deletion to maximize the number of days of
data and event logs saved.

Usage:

    FileEraserSimplified.py --dat_days=N --rdf_days=M

    N = number of days of dat files to retain
    M = number of days of RDF files to retain

    Both arguments are optional.  The default retention is 365 days of dat
    files and 60 days of RDF/ComboLog files.
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
from Host.Common.SingleInstance import SingleInstance

APP_NAME = "FileEraserSimplified"
CONFIG_DIR = os.environ["PICARRO_CONF_DIR"]
LOG_DIR = os.environ["PICARRO_LOG_DIR"]
ROOT_DIR = os.getenv("I2000_LOG_ARCHIVE_DIR", "/home/picarro/I2000/Log/Archive")
COMBO_LOG_ROOT_DIR = os.path.join(os.getenv("HOME"), ".combo_logger")

EventManagerProxy_Init(APP_NAME, DontCareConnection=True)


class FileEraserSimplified(object):
    def __init__(self, config):
        # Set defaults
        #
        # Retain 1 year of dat files
        # Retain 2 months of RDFs
        # Retain 2 months of ComboLogger logs
        #
        self.days_of_dat_files_to_keep = \
            config["dat_days"] if "dat_days" in config else 365
        self.days_of_rdf_files_to_keep = \
            config["rdf_days"] if "rdf_days" in config else 60
        self.days_of_combo_logs_to_keep = \
            config["combo_log_days"] if "combo_log_days" in config else 60
        #self.root_dir = ROOT_DIR

        #Now set up the RPC server...
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_FILE_ERASER),
                                               ServerName=APP_NAME,
                                               ServerDescription="",
                                               ServerVersion=1.0,
                                               threaded=True)

    def keepErasingOldFiles(self):
        """
        Check every 5 minutes if we should delete a directory.
        :return:
        """
        while True:
            print("Checking for things to erase", str(time.time()))
            self.deleteOldestDirectories()
            time.sleep(300)
        return

    def generateDirectoryList(self, root_dir=ROOT_DIR):
        """
        Inspect root_dir and create three sorted lists
        of directories that fit the formats YYYY-MM-DD, YYYY-MM-DD-RDF
        or YYYYMMDD/YYYYDDMM.
        :return:
        """
        noRDF = []
        RDF = []
        combo_logs = []
        if os.path.exists(root_dir):
            list1 = os.listdir(root_dir)
            for dir in list1:
                if re.match(r'.*\d{4}-\d{2}-\d{2}$', dir):
                    noRDF.append(os.path.join(root_dir, dir))
                if re.match(r'.*\d{4}-\d{2}-\d{2}-RDF$', dir):
                    RDF.append(os.path.join(root_dir, dir))
                if re.match(r'.*\d{8}$', dir):
                    combo_logs.append(os.path.join(root_dir, dir))
        return (sorted(noRDF), sorted(RDF), sorted(combo_logs))

    def deleteOldestDirectories(self):
        noRDF = []
        RDF = []
        combo_logs = []
        noRDF_deletion_count = 0
        RDF_deletion_count = 0
        combo_log_deletion_count = 0
        noRDF, RDF, _ = self.generateDirectoryList()
        _, _, combo_logs = self.generateDirectoryList(root_dir=COMBO_LOG_ROOT_DIR)
        while len(noRDF) > self.days_of_dat_files_to_keep:
            noRDF_deletion_count += 1
            shutil.rmtree(noRDF[0])
            noRDF, RDF, _ = self.generateDirectoryList()
        while len(RDF) > self.days_of_rdf_files_to_keep:
            RDF_deletion_count += 1
            shutil.rmtree(RDF[0])
            noRDF, RDF, _ = self.generateDirectoryList()
        while len(combo_logs) > self.days_of_combo_logs_to_keep:
            combo_log_deletion_count += 1
            shutil.rmtree(combo_logs[0])
            _, _, combo_logs = self.generateDirectoryList(root_dir=COMBO_LOG_ROOT_DIR)
        print("Deleted {} dat directories, {} RDF directories, and {} ComboLog directories.".format(noRDF_deletion_count, RDF_deletion_count, combo_log_deletion_count))
        return

    def runApp(self):
        rpcThread = threading.Thread(target=self.keepErasingOldFiles)
        rpcThread.setDaemon(True)
        rpcThread.start()
        self.RpcServer.serve_forever()


def HandleCommandSwitches():
    config = {}
    shortOpts = ''
    longOpts = ["dat_days=", "rdf_days=", "combo_log_days="]
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
    if "--combo_log_days" in options:
        config["combo_log_days"] = int(options["--combo_log_days"])
    return (config)


def main():
    my_instance = SingleInstance(APP_NAME)
    if my_instance.alreadyrunning():
        Log("Instance of %s already running" % APP_NAME, Level=2)
    else:
        #Get and handle the command line options...
        config = HandleCommandSwitches()
        Log("%s started." % APP_NAME, config, Level=1)
        try:
            fEraser = FileEraserSimplified(config)
            fEraser.runApp()
            Log("Exiting program")
        except Exception, E:
            # if DEBUG: raise
            msg = "Exception trapped outside execution"
            print msg + ": %s %r" % (E, E)
            Log(msg, Level=3, Verbose="Exception = %s %r" % (E, E))


if __name__ == "__main__":
    main()
