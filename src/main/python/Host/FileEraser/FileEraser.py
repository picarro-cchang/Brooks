#!/usr/bin/python
#
"""
File Name: FileEraser.py
Purpose:
    To erase obsolete files in specified directories, if they have the
    specified extensions and are older than a specific time

File History:
    08-09-29  alex  Created
    09-02-25  alex  Only remove empty directories if they are older than specified time (in case we want to keep some empty directories for future file storage)

Notes:
    In general this application is only used in Gen 1 platform (Python + LabVIEW).

    This application removes old files and empty directories periodically with configurable time interval.
    It can be supervised by Supervisor just like other applications. Below is an example .ini file:

    [MAIN]
    runtime_interval_hrs = 10 The time interval between each run of this application
                              (i.e. it will sleep for 10 hours before it removes old files again)

    [DIR1]
    path = ../../../Log/Archive/DataLog_Private The target directory that contains log files
    extension = dat, txt Any file with the listed extensions will be monitored and erased when it gets too old.
                         If this is blank then any file will be monitored.
    delete_time_hrs = 24 Any monitored file older than the specified hours will be removed.

    [DIR2]
    path = ../../../Log/Archive/DataLog_RemotePublic
    extension =
    delete_time_hrs = 16

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "FileEraser"
APP_DESCRIPTION = "Erase obsolete files"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "FileEraser.ini"

import sys
import os
import re
import time
import stat
import threading

from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_FILE_ERASER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import *

DEFAULT_DELETE_TIME_HRS = 1.0
SECONDS_PER_HOUR = 3600

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

class FileEraser(object):
    def __init__(self, configFile):
        co = CustomConfigObj(configFile)
        basePath = os.path.split(configFile)[0]
        self.policyDict = {}
        self.dirSections = co.list_sections()
        self.dirSections.remove("MAIN")
        self.interval = co.getfloat("MAIN", "runtime_interval_hrs") * SECONDS_PER_HOUR

        for dir in self.dirSections:
            path = os.path.abspath(os.path.join(basePath, co.get(dir, "path")))
            self.policyDict[dir] = {"path": path, "delete_time_hrs": co.getfloat(dir, "delete_time_hrs", DEFAULT_DELETE_TIME_HRS)}
            extension = co.get(dir, "extension", "")
            extensionList = re.split('\s*\s',extension.replace(',',' ').strip())
            if extensionList[0] == '':
                extensionList = ['*']
            self.policyDict[dir]["extension"] = extensionList
            self.policyDict[dir]["numExtensions"] = len(extensionList)

        #Now set up the RPC server...
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_FILE_ERASER),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True)

    def eraseOldFiles(self):
        for dir in self.policyDict.keys():
            pathToClean = self.policyDict[dir]["path"]
            deleteTimeHrs = self.policyDict[dir]["delete_time_hrs"]
            extensionList = self.policyDict[dir]["extension"]
            numExtensions = self.policyDict[dir]["numExtensions"]

            Log("Removing " + "\"*.%s\", "*numExtensions % tuple(extensionList)
                + "in %s that are older than %.1f hours" % (pathToClean, deleteTimeHrs))
            print("Removing " + "\"*.%s\", "*numExtensions % tuple(extensionList)
                + "in %s that are older than %.1f hours" % (pathToClean, deleteTimeHrs))

            # Remove files with specified extensions that are older than the specified time
            _removeOldFiles(pathToClean, extensionList, deleteTimeHrs)

            # Removre empty directories after file cleaning
            # Repeat this until all empty directories are removed
            newEmptyDirsExist = _removeEmptyDirs(pathToClean, deleteTimeHrs)
            while newEmptyDirsExist:
                newEmptyDirsExist = _removeEmptyDirs(pathToClean, deleteTimeHrs)

    def keepErasingOldFiles(self):
        while True:
            self.eraseOldFiles()
            time.sleep(self.interval)

    def runApp(self):
        rpcThread = threading.Thread(target = self.keepErasingOldFiles)
        rpcThread.setDaemon(True)
        rpcThread.start()
        self.RpcServer.serve_forever()

def _removeOldFiles(pathToClean, extensionList, deleteTimeHrs):
    for root, dirs, files in os.walk(pathToClean):
        for filename in files:
            filepath = os.path.join(root,filename)
            if (((os.path.basename(filename).split('.')[-1] in extensionList) or (extensionList[0] == '*')) and
                (os.path.getmtime(filepath) < (time.time() - deleteTimeHrs * SECONDS_PER_HOUR))):
                try:
                    os.chmod(filepath, stat.S_IREAD | stat.S_IWRITE)
                    os.remove(filepath)
                except OSError,errorMsg:
                    Log('%s' % (errorMsg))

def _removeEmptyDirs(rootPath, deleteTimeHrs):
    emptyDirFound = False
    for root, dirs, files in os.walk(rootPath):
        for dirname in dirs:
            dirpath = os.path.join(root, dirname)
            if os.path.getctime(dirpath) < (time.time() - deleteTimeHrs * SECONDS_PER_HOUR):
                try:
                    os.chmod(dirpath, stat.S_IREAD | stat.S_IWRITE)
                    os.rmdir(dirpath)
                    emptyDirFound = True
                except:
                    pass

    return emptyDirFound


HELP_STRING = \
"""

FileEraser.py [-h] [-c <FILENAME>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.

"""

def PrintUsage():
    print HELP_STRING

def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:", ["help"])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile

def main():
    #Get and handle the command line options...
    configFile = HandleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    try:
        fEraser = FileEraser(configFile)
        fEraser.runApp()
        Log("Exiting program")
    except Exception, E:
        if DEBUG: raise
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))

if __name__ == "__main__":
    DEBUG = __debug__
    main()