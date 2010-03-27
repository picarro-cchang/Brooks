#!/usr/bin/python
#
# FILE:
#   writeLaserEeprom.py
#
# DESCRIPTION:
#   Write to laser EEPROM from a WLM file
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   26-March-2010  sze  Initial version.
#
#  Copyright (c) 2010 Picarro, Inc. All rights reserved
#
import sys
import getopt
from configobj import ConfigObj
import numpy as np
import os
import cPickle
import socket
import struct
import time
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.hostDasInterface import Operation, OperationGroup
from Host.Common.StringPickler import StringAsObject, ObjAsString
from Host.Common.WlmCalUtilities import WlmFile

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

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

class WriteLaserEeprom(object):
    """Write parameters from WLM file to laser EEPROM"""
    def __init__(self,configFile,options):
        self.config = ConfigObj(configFile)
        # Analyze options
        if "-l" in options:
            self.laserNum = int(options["-l"])
        else:
            self.laserNum = int(self.config["SETTINGS"]["LASER"])
        if self.laserNum<=0 or self.laserNum>MAX_LASERS:
            raise ValueError("LASER must be in range 1..4")

        if "-f" in options:
            fname = options["-f"]
        else:
            fname = self.config["SETTINGS"]["FILENAME"]
        self.fname = fname.strip() + ".wlm"
        self.fp = file(self.fname,"r")
        
        if "-s" in options:
            self.serialNo = options["-s"]
        else:
            self.serialNo = self.config["SETTINGS"]["SERIAL"]
        
    def run(self):
        # Check that the driver can communicate
        try:
            print "Driver version: %s" % Driver.allVersions()
        except:
            raise ValueError,"Cannot communicate with driver, aborting"
    
        eepromId = "LASER%d_EEPROM" % self.laserNum
        wlmFile = WlmFile(self.fp)
        sec = {}
        sec["COARSE_CURRENT"] = float(wlmFile.parameters["laser_current"])
        sec["WAVENUM_CEN"]    = wlmFile.WtoT.xcen
        sec["WAVENUM_SCALE"]  = wlmFile.WtoT.xscale
        sec["W2T_0"],sec["W2T_1"],sec["W2T_2"],sec["W2T_3"] = wlmFile.WtoT.coeffs
        sec["TEMP_CEN"]    = wlmFile.TtoW.xcen
        sec["TEMP_SCALE"]  = wlmFile.TtoW.xscale
        sec["T2W_0"],sec["T2W_1"],sec["T2W_2"],sec["T2W_3"] = wlmFile.TtoW.coeffs
        sec["TEMP_ERMS"] = np.sqrt(wlmFile.WtoT.residual)
        sec["WAVENUM_ERMS"] = np.sqrt(wlmFile.TtoW.residual)
        
        header = []
        self.fp.seek(0)
        while True:
            line = self.fp.readline()
            if line.strip() == "[Data]": break
            header.append(line)
        hdrDict = ConfigObj(header)
        self.fp.close()
        laserDat = dict(parameters=sec,
                        serialNo="%s" % self.serialNo,
                        date=hdrDict["CRDS Header"]["Date"],
                        time=hdrDict["CRDS Header"]["Time"],
                        laserTemperature = wlmFile.TLaser,
                        waveNumber = wlmFile.WaveNumber)
        print "Starting to write to EEPROM"                
        Driver.shelveObject(eepromId,laserDat)
        raw_input("Writing to EEPROM complete. <Enter> to continue.")
        print "Verification %s" % "succeeded." if Driver.verifyObject(eepromId,laserDat) else "FAILED."
        
HELP_STRING = """writeLaserEeprom.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./writeLaserEeprom.ini"
-f                   name of input WLM file (without extension)
-l                   actual laser (1-origin) EEPROM to write to
-s                   serial number of laser
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:f:l:s:'
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
    m = WriteLaserEeprom(configFile, options)
    m.run()
