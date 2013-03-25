# Fetch contents of all lasers and WLM EEPROMs from an analyzer

import sys
import getopt
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
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="CalibrateSystem")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc

if __name__ == "__main__":
    fname = "EEPROM_dump.pic"
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
    cPickle.dump({"laserEeproms":laserEepromContents,"wlmEeprom":wlmEepromContents},file(fname,"wb"),-1)
    