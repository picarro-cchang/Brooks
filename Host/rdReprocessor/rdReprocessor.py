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

APP_NAME = "rdReprocessor"
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

#dirName = r"s:\for John\CFADS_RDFs\Picarro\G2000\Log\RDF"

#AddPath and Def Config Name copied from ReadMemUsage.py
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)
DEFAULT_CONFIG_NAME = "..\..\AppConfig\Config\rdReprocessor\rdReprocessor.ini"

def convHdf5ToDict(h5Filename):
    h5File = openFile(h5Filename, "r")
    retDict = {}
    for tableName in h5File.root._v_children.keys():
        table = h5File.root._v_children[tableName]
        retDict[tableName] = {}
        r = table.read()
        for colKey in table.colnames:
            retDict[tableName][colKey] = r[colKey] # table.read(field=colKey)
    h5File.close()
    return retDict

class rdReprocessor(object):
    def __init__(self, configFile):
        config = CustomConfigObj(configFile)  # 2nd argument (list_values=True) removed
#       self.dirName = config.get("File", "targetDir", "C:/UserData")
        self.dirName = config.get("Main", "dirName")

    def run(self):
        broadcaster =  Broadcaster.Broadcaster(
                    port=BROADCAST_PORT_SPECTRUM_COLLECTOR,
                    name="Spectrum Collector broadcaster",logFunc = Log)
        self.files = sorted(glob(self.dirName + r'\*.h5'))
        time.sleep(5)
        ## raw_input("Press <Enter> to start sending")
        for f in self.files:
            print f
            rdfDict = convHdf5ToDict(f)
            # raw_input("Press <Enter> to send %s" % f)
            broadcaster.send(StringPickler.PackArbitraryObject(rdfDict))
            time.sleep(1.0)
       
HELP_STRING = \
""" rdReprocessor.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help.
-c                   Specify a config file.  Default = "./rdReprocessor.ini"
"""

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
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME # this is not working...
    #configFile = DEFAULT_CONFIG_NAME
    print "Name of DEFAULT configFile is %s" % configFile
    
    
    if '-h' in options:
        PrintUsage()
        sys.exit()

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return (configFile)
  
if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    print  "The name of configFile is %s" % configFile
    app = rdReprocessor(configFile)
    app.run()