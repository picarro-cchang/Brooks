#!/usr/bin/python
#
"""
File Name: rdReprocessor.py
Purpose:
    Reprocess a collection of H5 files specified in an INI file

File History:
    11-07-18 sze   In progress
    11-07-26 Shige   moved the definition of dirName to rdReprocessor.ini file
                     added the rdReprocessor class, HandleCommandSwitches function,
                     'if __name__' lines, etc (copied from ReadMemUsage.py)
                     Put the broadcaster lines into the run(self) function
                     Changed the time.sleep value to 5 sec from 20.
"""
from glob import glob
import os
import sys
import time
import os.path
from Host.Common.SharedTypes import BROADCAST_PORT_SPECTRUM_COLLECTOR
from Host.Common import Broadcaster, Listener, StringPickler
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from tables import openFile
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.timestamp import getTimestamp

APP_NAME = "rdReprocessor"
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

#AddPath and Def Config Name copied from ReadMemUsage.py
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)
DEFAULT_CONFIG_NAME = "..\..\AppConfig\Config\rdReprocessor\rdReprocessor.ini"

def convHdf5ToDict(h5Filename, selfTiming):
    h5File = openFile(h5Filename, "r")
    retDict = {}
    for tableName in h5File.root._v_children.keys():
        table = h5File.root._v_children[tableName]
        retDict[tableName] = {}
        r = table.read()
        for colKey in table.colnames:
            if colKey == "timestamp":
                if selfTiming > 0:
                    length = len(r[colKey])
                    currTime = getTimestamp()
                    r[colKey] = [currTime - 5*i for i in range(length)]
            retDict[tableName][colKey] = r[colKey] # table.read(field=colKey)
    h5File.close()
    return retDict

class rdReprocessor(object):
    def __init__(self, configFile, loop=0):
        config = CustomConfigObj(configFile)  # 2nd argument (list_values=True) removed
        self.dirName = config.get("Main", "dirName")
        self.loop = loop

    def run(self):
        broadcaster =  Broadcaster.Broadcaster(
                    port=BROADCAST_PORT_SPECTRUM_COLLECTOR,
                    name="Spectrum Collector broadcaster",logFunc = Log)
        self.files = sorted(glob(self.dirName + r'\*.h5'))
        fnum = len(self.files)
        index = 0
        step = 1
        time.sleep(5)
        #raw_input("Press <Enter> to start sending")
        while index < fnum:
            f = self.files[index]
            print f
            rdfDict = convHdf5ToDict(f, self.loop)
            # raw_input("Press <Enter> to send %s" % f)
            broadcaster.send(StringPickler.PackArbitraryObject(rdfDict))
            if self.loop == 1:  # loop2
                if index == fnum-1:
                    step = -1
                elif index == 0:
                    step = 1
            elif self.loop == 2:    # loop
                if index == fnum-1:
                    index = -1
            index += step
            time.sleep(1.0)

HELP_STRING = \
""" rdReprocessor.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help.
-c                   Specify a config file.  Default = "./rdReprocessor.ini"
--loop2              process data files from the first to the last then back to the first. Repeat this procedure forever
--loop               loop processing data files forever
"""
def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt

    shortOpts = 'hc:'
    longOpts = ["help", "loop2", "loop"]
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
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME # this is not working...
    #configFile = DEFAULT_CONFIG_NAME
    loop = 0

    if '-h' in options:
        PrintUsage()
        sys.exit()

    if "-c" in options:
        configFile = options["-c"]
    if "--loop2" in options:
        loop = 1
    elif "--loop" in options:
        loop = 2

    return (configFile, loop)

if __name__ == "__main__":
    configFile, loop = HandleCommandSwitches()
    print  "The name of configFile is %s" % configFile
    app = rdReprocessor(configFile, loop)
    app.run()