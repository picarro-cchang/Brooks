"""
File Name: ReadMemUsage.py
Purpose:
    Dectects and records virtual memory usage for processes

File History:
    07-12-11 Alex  Created

Copyright (c) 2011 Picarro, Inc. All rights reserved
"""
import sys
import psutil
import time
import os.path
from Host.Common.CustomConfigObj import CustomConfigObj

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

DEFAULT_CONFIG_NAME = "ReadMemUsage.ini"

def differenceFound(a,b):
    return len(set(a).symmetric_difference(set(b))) > 0

class ReadMemUsage(object):
    def __init__(self, configFile):
        config = CustomConfigObj(configFile, list_values=True)
        try:
            self.procNameList = config.get("Setup", "processes")
        except:
            self.procNameList = []
            raise Exception, "No process will be monitored"
        self.intervalS = config.getfloat("Setup", "intervalS", 60)
        self.procList = [p for p in psutil.get_process_list() if p.name in self.procNameList]
        self.targetDir = config.get("File", "targetDir", "C:/UserData")
        if not os.path.isdir(self.targetDir):
            os.makedirs(self.targetDir)
        self.maxLines = config.getint("File", "maxLines", 500)
        self.colWidth = 26
        self.createNewFile()

    def verifyProcList(self):
        newProcList = [p for p in psutil.get_process_list() if p.name in self.procNameList]
        newList = [(p.name, p.pid) for p in newProcList]
        try:
            currentList = [(p.name, p.pid) for p in self.procList]
        except:
            currentList = []
        if differenceFound(currentList, newList):
            self.procList = newProcList
            self.createNewFile()

    def createNewFile(self):
        self.cnt = 0
        filename = "MemLog-%s.dat" % (time.strftime("%Y%m%d-%H%M%S",time.localtime()))
        self.filepath = os.path.abspath(os.path.join(self.targetDir, filename))
        print "%s Created" % self.filepath
        self._writeHeader()

    def _writeEntry(self, fp, string):
        fp.write((string[:self.colWidth-1]).ljust(self.colWidth))

    def _writeHeader(self):
        fp = open(self.filepath, "a")
        self._writeEntry(fp, "timestamp")
        for p in self.procList:
            self._writeEntry(fp, "%s_%d" % (p.name, p.pid))
        fp.write("\n")
        fp.close()
        self.cnt += 1

    def _writeData(self, dataDict):
        fp = open(self.filepath, "a")
        self._writeEntry(fp, dataDict["timestamp"])
        for p in self.procList:
            self._writeEntry(fp, dataDict["%s_%d" % (p.name, p.pid)])
        fp.write("\n")
        fp.close()
        self.cnt += 1

    def read(self):
        while True:
            self.verifyProcList()
            output = {}
            try:
                for p in self.procList:
                    output["%s_%d" % (p.name, p.pid)] = "%s %s" % p.get_memory_info()
                output["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
                self._writeData(output)
                if self.cnt > self.maxLines:
                    self.createNewFile()
            except Exception, errMsg:
                print errMsg
            time.sleep(self.intervalS)

HELP_STRING = \
""" ReadMemUsage.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help.
-c                   Specify a config file.  Default = "./ReadMemUsage.ini"
"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt

    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)

    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if '-h' in options:
        PrintUsage()
        sys.exit()

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return (configFile)

if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    app = ReadMemUsage(configFile)
    app.read()