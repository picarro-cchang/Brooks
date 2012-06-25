#!/usr/bin/python
#
# FILE:
#   MakeCalFromEeproms.py
#
# DESCRIPTION:
#   Create a warm box calibration file from the contents of the EEPROMs
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   29-Mar-2010  sze  Initial version.
#
#  Copyright (c) 2010 Picarro, Inc. All rights reserved
#
import cPickle
import sys
import getopt
from numpy import *
import os
import socket
import time

from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.WlmCalUtilities import bestFitCentered, WlmFile, AutoCal

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("CalFileFromEepromsMaker")

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="CalibrateSystem")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc

class CalFileFromEepromsMaker(object):
    def __init__(self,configFile,options):
        self.config = ConfigObj(configFile)
        # Output file
        if "-f" in options:
            fname = options["-f"]
        else:
            fname = self.config["FILES"]["OUTPUT"]
        self.outfname = fname + ".ini"

        if "-d" in options:
            self.dTheta = float(options["-d"])
        else:
            self.dTheta = float(self.config["SETTINGS"]["DTHETA"])
        if self.dTheta < 0.01:
            raise ValueError("Angle between knots should be >= 0.01 radians")
        
        # Input files
        if "-i" in options:
            self.infile = options["-i"]
        elif "INPUT" in self.config["FILES"]:
            self.infile = self.config["FILES"]["INPUT"]
        else:
            self.infile = None

        virtualList = [{} for i in range(NUM_VIRTUAL_LASERS)]
        for key in self.config:
            if key.startswith("VIRTUAL"):
                vLaserNum = int(key[8:])
                aLaserNum = int(self.config[key]["ACTUAL"])
                virtualList[vLaserNum-1]["ACTUAL"] = aLaserNum
                if "WMIN" in self.config[key]:
                    virtualList[vLaserNum-1]["WMIN"] = float(self.config[key]["WMIN"])
                else:
                    virtualList[vLaserNum-1]["WMIN"] = None
                if "WMAX" in self.config[key]:
                    virtualList[vLaserNum-1]["WMAX"] = float(self.config[key]["WMAX"])
                else:
                    virtualList[vLaserNum-1]["WMAX"] = None
        self.virtualList = virtualList

    # def filenameFromPath(self,path):
    #    return os.path.splitext(os.path.split(path)[1])[0]
    
    def run(self):
        self.op = ConfigObj()
        if self.infile:
            fp = file(self.infile,"rb")
            self.eepromContents = cPickle.load(fp)
            fp.close()
        else:
            laserEepromContents = []
            for aLaserNum in range(1,5):
                ident = "LASER%d_EEPROM" % aLaserNum
                try:
                    laserEepromContents.append(Driver.fetchObject(ident)[0])
                    print "Read %s" % ident
                except ValueError:
                    laserEepromContents.append(None)
            wlmEepromContents = Driver.fetchWlmCal()
            print "Read WLM_EEPROM"
            self.eepromContents = {"laserEeproms":laserEepromContents,
                                   "wlmEeprom":wlmEepromContents}
        
        laserEeproms = self.eepromContents["laserEeproms"]
        wlmEeprom    = self.eepromContents["wlmEeprom"]
        
        # Write the actual laser sections
        for i,aLaserDict in enumerate(laserEeproms):
            laserNum = i + 1
            if aLaserDict is not None:
                self.op["ACTUAL_LASER_%d" % laserNum] = {}
                for k in sorted(aLaserDict["parameters"]):
                    self.op["ACTUAL_LASER_%d" % laserNum][k] = aLaserDict["parameters"][k]
                    
        # Next report the mapping between virtual and actual lasers
        self.op["LASER_MAP"] = {}
        lmSec = self.op["LASER_MAP"]
        for i,v in enumerate(self.virtualList):
            vLaserNum = i + 1
            if v:
                aLaserNum = int(v["ACTUAL"])
                lmSec["ACTUAL_FOR_VIRTUAL_%d" % vLaserNum] = aLaserNum
                if laserEeproms[aLaserNum-1] is None:
                    raise ValueError("Actual laser %d is not available." % aLaserNum)
        
        # For each virtual laser, we need to create an Autocal object
        for i,v in enumerate(self.virtualList):
            vLaserNum = i + 1
            if v:
                aLaserNum = int(v["ACTUAL"])
                ac = AutoCal()
                ac.loadFromEepromDict(wlmEeprom,dTheta=self.dTheta,wMin=v["WMIN"],wMax=v["WMAX"])
                ac.updateIni(self.op,vLaserNum)
        self.op.filename = self.outfname
        self.op.write()

HELP_STRING = """makeCalFromEeproms.py [options]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./makeCalFromEeproms.ini"
-d                   the angle increment for B-spline knots
-i                   input file (omit to read directly from EEPROMS)
-f                   name of output file (without extension)
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:d:f:'
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
    configFile = os.path.splitext(AppPath)[0] + ".ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile, options

if __name__ == "__main__":
    configFile, options = handleCommandSwitches()
    m = CalFileFromEepromsMaker(configFile, options)
    m.run()

    
    


