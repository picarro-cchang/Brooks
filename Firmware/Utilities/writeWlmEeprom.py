#!/usr/bin/python
#
# FILE:
#   writeWlmEeprom.py
#
# DESCRIPTION:
#   Write wavelemgth monitor EEPROM from a set of WLM files
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
from Host.Common.ctypesConvert import ctypesToDict, dictToCtypes

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
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="writeWlmEeprom")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc

class WriteWlmEeprom(object):
    """Write parameters from a collection of WLM files to the WLM EEPROM"""
    def __init__(self,configFile,options):
        self.config = ConfigObj(configFile)
        self.wlmFiles = []
        # Input files
        try:
            if "--laser1" in options:
                fname = options["--laser1"]
            else:
                fname = self.config["FILES"]["LASER1"]
            self.wlmFiles.append(file(fname + ".wlm","r"))
        except KeyError:
            self.wlmFiles.append(None)
        try:
            if "--laser2" in options:
                fname = options["--laser2"]
            else:
                fname = self.config["FILES"]["LASER2"]
            self.wlmFiles.append(file(fname + ".wlm","r"))
        except KeyError:
            self.wlmFiles.append(None)
        try:
            if "--laser3" in options:
                fname = options["--laser3"]
            else:
                fname = self.config["FILES"]["LASER3"]
            self.wlmFiles.append(file(fname + ".wlm","r"))
        except KeyError:
            self.wlmFiles.append(None)
        try:
            if "--laser4" in options:
                fname = options["--laser4"]
            else:
                fname = self.config["FILES"]["LASER4"]
            self.wlmFiles.append(file(fname + ".wlm","r"))
        except KeyError:
            self.wlmFiles.append(None)

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

        wlmCal = WLMCalibrationType()
        etalon1_offset, etalon2_offset, reference1_offset, reference2_offset = [], [], [], []
        waveNumber, ratio1, ratio2, etalon_temperature = [], [], [], []
        for i,fp in enumerate(self.wlmFiles):
            laserNum = i + 1
            if fp is not None:
                wlmFile = WlmFile(fp)
                etalon1_offset.append(float(wlmFile.parameters["etalon1_offset"]))
                etalon2_offset.append(float(wlmFile.parameters["etalon2_offset"]))
                reference1_offset.append(float(wlmFile.parameters["reference1_offset"]))
                reference2_offset.append(float(wlmFile.parameters["reference2_offset"]))
                waveNumber.append(wlmFile.WaveNumber)
                ratio1.append(wlmFile.Ratio1)
                ratio2.append(wlmFile.Ratio2)
                etalon_temperature.append(wlmFile.TEtalon)
        waveNumber = np.concatenate(waveNumber)
        ratio1 = np.concatenate(ratio1)
        ratio2 = np.concatenate(ratio2)
        etalon_temperature = np.concatenate(etalon_temperature)
        # Calculate means and standard deviations
        wlmCal.header.etalon_temperature = np.mean(etalon_temperature)
        if np.std(etalon_temperature) > 0.010:
            print "WARNING: Etalon temperature std dev: %.3f" % (np.std(etalon_temperature),)
        wlmCal.header.etalon1_offset = np.mean(etalon1_offset)
        if np.std(etalon1_offset) > 5:
            print "WARNING: Etalon1 offset std dev: %.1f" % (np.std(etalon1_offset),)
        wlmCal.header.etalon2_offset = np.mean(etalon2_offset)
        if np.std(etalon2_offset) > 5:
            print "WARNING: Etalon2 offset std dev: %.1f" % (np.std(etalon2_offset),)
        wlmCal.header.reference1_offset = np.mean(reference1_offset)
        if np.std(reference1_offset) > 5:
            print "WARNING: Reference1 offset std dev: %.1f" % (np.std(reference1_offset),)
        wlmCal.header.reference2_offset = np.mean(reference2_offset)
        if np.std(reference2_offset) > 5:
            print "WARNING: Reference2 offset std dev: %.1f" % (np.std(reference2_offset),)
        # Sort the wavenumbers into order and use same permutation for ratios
        perm = waveNumber.argsort()
        waveNumber = waveNumber[perm]
        ratio1 = ratio1[perm]
        ratio2 = ratio2[perm]
        if len(waveNumber) > len(wlmCal.wlmCalRows):
            print "WARNING: Too many measurements in WLM files: %d" % len(waveNumber)
        for i in range(len(waveNumber)):
            wlmCal.wlmCalRows[i].waveNumberAsUint = int(100000*waveNumber[i]+0.5)
            wlmCal.wlmCalRows[i].ratio1 = ratio1[i]
            wlmCal.wlmCalRows[i].ratio2 = ratio2[i]
        for j,c in enumerate("%s" % self.serialNo):
            wlmCal.header.identifier[j] = ord(c) 
        # Write to the EEPROM
        print "Writing WLM data to EEPROM"
        Driver.shelveWlmCal(ctypesToDict(wlmCal))
        # Read back the data
        print "Writing complete. Starting verification"
        wlmCalReadback = WLMCalibrationType()
        dictToCtypes(Driver.fetchWlmCal(),wlmCalReadback)
        if buffer(wlmCalReadback) == buffer(wlmCal):
            print "EEPROM contents verified"
        else:
            print "ERROR: WLMCAL read back incorrectly."
        
HELP_STRING = """writeWlmEeprom.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./writeWlmEeprom.ini"
--laser1             wlm file for laser1 (without extension)
--laser2             wlm file for laser2 (without extension)
--laser3             wlm file for laser3 (without extension)
--laser4             wlm file for laser4 (without extension)
-s                   serial number of wavelength monitor
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:'
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
    m = WriteWlmEeprom(configFile, options)
    m.run()
