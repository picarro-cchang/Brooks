#!/usr/bin/python
#
# FILE:
#   MakeNoWlmCalFile.py
#
# DESCRIPTION:
#   Create a warm box calibration file for an analyzer with no wavelength monitor
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   7-Oct-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
import getopt
from numpy import *
import os
import pylab
import time

from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.WlmCalUtilities import bestFitCentered, NoWlmFile, AutoCal
from scipy import interpolate

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("WarmBoxCalFileMaker")

class WarmBoxCalFileMaker(object):
    def __init__(self,configFile,options):
        self.config = ConfigObj(configFile)
        self.noWlmFiles = []
        # Output file
        if "-f" in options:
            fname = options["-f"]
        else:
            fname = self.config["FILES"]["OUTPUT"]
        self.outfname = fname + ".ini"
        
        # Input files
        try:
            if "--laser1" in options:
                fname = options["--laser1"]
            else:
                fname = self.config["FILES"]["LASER1"]
            self.noWlmFiles.append(file(fname + ".nowlm","r"))
        except KeyError:
            self.noWlmFiles.append(None)
        try:
            if "--laser2" in options:
                fname = options["--laser2"]
            else:
                fname = self.config["FILES"]["LASER2"]
            self.noWlmFiles.append(file(fname + ".nowlm","r"))
        except KeyError:
            self.noWlmFiles.append(None)
        try:
            if "--laser3" in options:
                fname = options["--laser3"]
            else:
                fname = self.config["FILES"]["LASER3"]
            self.noWlmFiles.append(file(fname + ".nowlm","r"))
        except KeyError:
            self.noWlmFiles.append(None)
        try:
            if "--laser4" in options:
                fname = options["--laser4"]
            else:
                fname = self.config["FILES"]["LASER4"]
            self.noWlmFiles.append(file(fname + ".nowlm","r"))
        except KeyError:
            self.noWlmFiles.append(None)

        virtualList = [{} for i in range(NUM_VIRTUAL_LASERS)]
        for key in self.config:
            if key.startswith("VIRTUAL"):
                vLaserNum = int(key[8:])
                aLaserNum = int(self.config[key]["ACTUAL"])
                virtualList[vLaserNum-1]["ACTUAL"] = aLaserNum
                if self.noWlmFiles[aLaserNum-1] is None:
                    raise ValueError("Actual laser %d requested by virtual laser %d is undefined" % (aLaserNum,vLaserNum))
        self.virtualList = virtualList

    def filenameFromPath(self,path):
        return os.path.splitext(os.path.split(path)[1])[0]
    
    def run(self):
        self.op = ConfigObj()
        self.noWlmFileList = []
        # First step is to obtain wavenumber vs temperature relations for all actual lasers
        for i,fp in enumerate(self.noWlmFiles):
            laserNum = i + 1
            if fp is not None:
                noWlmFile = NoWlmFile(fp)
                self.noWlmFileList.append(noWlmFile)
                self.op["ACTUAL_LASER_%d" % laserNum] = {}
                sec = self.op["ACTUAL_LASER_%d" % laserNum]
                sec["COARSE_CURRENT"] = noWlmFile.parameters["laser_current"]
                sec["WAVENUM_CEN"]    = noWlmFile.WtoT.xcen
                sec["WAVENUM_SCALE"]  = noWlmFile.WtoT.xscale
                sec["W2T_0"],sec["W2T_1"],sec["W2T_2"],sec["W2T_3"] = noWlmFile.WtoT.coeffs
                sec["TEMP_CEN"]    = noWlmFile.TtoW.xcen
                sec["TEMP_SCALE"]  = noWlmFile.TtoW.xscale
                sec["T2W_0"],sec["T2W_1"],sec["T2W_2"],sec["T2W_3"] = noWlmFile.TtoW.coeffs
                sec["TEMP_ERMS"] = sqrt(noWlmFile.WtoT.residual)
                sec["WAVENUM_ERMS"] = sqrt(noWlmFile.TtoW.residual)
                pylab.figure(); pylab.plot(noWlmFile.TLaser,noWlmFile.WaveNumber,'r.',noWlmFile.TLaser,noWlmFile.TtoW(noWlmFile.TLaser))
                pylab.grid(True)
                pylab.xlabel("Laser Temperature")
                pylab.ylabel("Wavenumber")
                pylab.title('Laser %s, Coarse current %s: %s' % (laserNum,sec["COARSE_CURRENT"],self.outfname))
                pylab.savefig("%s_Laser%02d_Tuning.png" % (self.filenameFromPath(self.outfname),laserNum))
            else:
                self.noWlmFileList.append(None)

        # Next report the mapping between virtual and actual lasers
        self.op["LASER_MAP"] = {}
        lmSec = self.op["LASER_MAP"]
        for i,vDict in enumerate(self.virtualList):
            vLaserNum = i + 1
            if vDict:
                lmSec["ACTUAL_FOR_VIRTUAL_%d" % vLaserNum] = vDict["ACTUAL"]
        # Finally iterate through the virtual laser information
        #  creating Autocal objects for each and updating the output INI file
        for i,v in enumerate(self.virtualList):
            vLaserNum = i + 1
            #if v:
            #    aLaserNum = int(v["ACTUAL"])
            #    ac = AutoCal()
            #    ac.loadFromWlmFile(self.wlmFileList[aLaserNum-1],dTheta=self.dTheta,
            #                       wMin=v["WMIN"],wMax=v["WMAX"])
            #    ac.updateIni(self.op,vLaserNum)
                
        self.op.filename = self.outfname
        self.op.write()

HELP_STRING = """MakeWarmBoxCal_NoWlm.py [options]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./MakeWarmBoxCal_NoWlm.ini"
-f                   name of output file (without extension)
--laser1             wlm file for laser1 (without extension)
--laser2             wlm file for laser2 (without extension)
--laser3             wlm file for laser3 (without extension)
--laser4             wlm file for laser4 (without extension)
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:d:f:'
    longOpts = ["help","laser1=","laser2=","laser3=","laser4="]
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
    m = WarmBoxCalFileMaker(configFile, options)
    m.run()
