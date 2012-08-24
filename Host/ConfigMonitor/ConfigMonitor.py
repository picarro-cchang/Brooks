#!/usr/bin/python
#
# File Name: ConfigMonitor.py
# Purpose: Monitor Picarro instrument configuration changes using BZR commands
#
# File History:
# 2011-04-22 Alex  Created

APP_NAME = "Configuration Monitor"
APP_DESCRIPTION = "Commit all the configuration changes in repository"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "ConfigMonitor.ini"

import os
import sys
import time
import threading
from Host.Common import CmdFIFO
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SharedTypes import RPC_PORT_CONFIG_MONITOR
from Host.Common.EventManagerProxy import *

try:
    # Release build
    from Host.Common import release_version as version
except ImportError:
    try:
        # Internal build
        from Host.Common import setup_version as version
    except ImportError:
        # Internal dev
        from Host.Common import version


EventManagerProxy_Init(APP_NAME,DontCareConnection = False)

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

def makePath(fn):
    def wrapper(self, dir, *args):
        if not os.path.isdir(dir):
            os.makedirs(dir)
        return fn(self, dir, *args)
    return wrapper

def toAbsPath(fn):
    def wrapper(self, dir, *args):
        dir = os.path.abspath(dir)
        return fn(self, dir, *args)
    return wrapper

class BzrHelper(object):
    @makePath
    @toAbsPath
    def __init__(self, repo):
        if not self.isRepo(repo):
            os.system(r"bzr init-repo --no-trees %s" % repo)
        self.repo = repo
        self.basePath = os.getcwd()

    @toAbsPath
    def isBranch(self, dir):
        info = os.popen(r"bzr info %s" % dir, "r").read()
        if "branch" not in info:
            return False
        else:
            return True

    @toAbsPath
    def isRepo(self, repo):
        info = os.popen(r"bzr info %s" % repo, "r").read()
        if "repository" not in info:
            return False
        else:
            return True

    @makePath
    @toAbsPath
    def init(self, dir, ignore=""):
        os.chdir(dir)
        os.system(r"bzr init")
        if ignore:
            os.system(r"bzr ignore %s" % ignore)
        self._addCommit("Created initial branch")
        os.system(r"bzr push %s" % os.path.join(self.repo, os.path.basename(dir)))
        os.chdir(self.basePath)

    @toAbsPath
    def updateIgnore(self, dir, ignore=""):
        # Only keep "ignore" pattern if it is not in .bzrignnore
        ignoreFile = os.path.join(dir, ".bzrignore")
        ignoreList = [i for i in ignore.split() if i not in open(ignoreFile, "r").read()]
        ignoreStr = " ".join(ignoreList)
        if ignoreStr:
            os.chdir(dir)
            os.system(r"bzr ignore %s" % ignoreStr)
            self._addCommit("Update .bzrignore file")
            os.system(r"bzr push %s" % os.path.join(self.repo, os.path.basename(dir)))
            os.chdir(self.basePath)

    @toAbsPath
    def st(self, dir):
        ret = os.popen(r"bzr st %s" % dir, "r").read()
        return ret

    @toAbsPath
    def commit(self, dir, comment=""):
        if not comment:
            comment = time.strftime("Configuration changes found and committed: %Y-%m-%d %H:%M:%S", time.localtime())
        os.chdir(dir)
        self._addCommit(comment)
        os.system(r"bzr push")
        os.chdir(self.basePath)

    def _addCommit(self, comment):
        os.system(r"bzr add")
        os.system(r'bzr commit -m "%s" --unchanged' % comment)
        Log(comment)

class RpcServerThread(threading.Thread):
    def __init__(self, rpcServer, exitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.rpcServer = rpcServer
        self.exitFunction = exitFunction
    def run(self):
        self.rpcServer.serve_forever()
        try: #it might be a threading.Event
            self.exitFunction()
            Log("RpcServer exited and no longer serving.")
            print "RpcServer exited and no longer serving."
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")
            print "Exception raised when calling exit function at exit of RPC server."

class ConfigMonitor(object):
    def __init__(self, configFile):
        self.co = CustomConfigObj(configFile)
        self.enabled = self.co.getboolean("Main", "Enabled")
        repo = self.co.get("Main", "Repository")
        self.bzr = BzrHelper(repo)
        self.swHistFile = self.co.get("Main", "SoftwareHistory")
        # Create the software history file if it does not exist
        fd = open(self.swHistFile, "a")
        fd.close()
        dirList = self.co.keys()
        dirList.remove("Main")
        self.monitoredDirs = []
        for dir in dirList:
            dirPath = self.co.get(dir, "Path")
            ignore = self.co.get(dir, "IgnoreRules")
            self.monitoredDirs.append((dirPath, ignore))
        # Get Host and SrcCode version numbers
        self.releaseVer = version.versionString()
        try:
            from Host.repoBzrVer import version_info
            self.hostVer = str(version_info['revno'])
        except:
            self.hostVer = ""
        try:
            from Host.repoBzrVer import version_info
            self.srcVer = str(version_info['revno'])
        except:
            self.srcVer = ""

        if self.enabled:
            # Check Host and srcCode versions
            self.checkSoftwareVer()
            # Check configurations and initialize branches if necessary
            for dir, ignore in self.monitoredDirs:
                if not self.bzr.isBranch(dir):
                     # Initialize
                    self.bzr.init(dir, ignore)
                if self.bzr.st(dir):
                    self.bzr.commit(dir)
        self.startServer()

    def startServer(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_CONFIG_MONITOR),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True)
        self.rpcServer.register_function(self.monitor)
        self.rpcServer.register_function(self.enable)
        self.rpcServer.register_function(self.disable)
        self.rpcServer.serve_forever()

    def checkSoftwareVer(self):
        swHistCo = CustomConfigObj(self.swHistFile)
        swVerList = swHistCo.list_sections()
        swVerList.sort()
        if swVerList:
            lastSwVer = swVerList[-1]
            if self.releaseVer == swHistCo.get(lastSwVer, "Release") and \
               self.hostVer == swHistCo.get(lastSwVer, "Host") and \
               self.srcVer == swHistCo.get(lastSwVer, "SrcCode"):
                return
        timestamp = time.time()
        timeKey = str(timestamp)
        swHistCo.add_section(timeKey)
        swHistCo.set(timeKey, "Release", self.releaseVer)
        swHistCo.set(timeKey, "Host", self.hostVer)
        swHistCo.set(timeKey, "SrcCode", self.srcVer)
        swHistCo.set(timeKey, "Time", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)))
        swHistCo.write()

    def monitor(self, comment=""):
        """
        Track changes in configuration files and host/srcCode versions
        """
        if not self.enabled:
            return
        # Check Host and srcCode versions
        self.checkSoftwareVer()
        # Check configurations
        for dir, ignore in self.monitoredDirs:
            if self.bzr.st(dir):
                self.bzr.commit(dir, comment)

    def enable(self):
        self.enabled = True
        self.co.set("Main", "Enabled", "True")
        self.co.write()

    def disable(self):
        self.enabled = False
        self.co.set("Main", "Enabled", "False")
        self.co.write()
HELP_STRING = \
"""

ConfigMonitor.py [-h] [-c <FILENAME>]

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

if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    ConfigMonitor(configFile)
