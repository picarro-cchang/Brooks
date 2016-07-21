#!/usr/bin/python
#
# FILE:
#   InstrumentConfig.py
#
# DESCRIPTION:
#   Load instrument configuration from a file
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   26-Nov-2013  sze  Initial coding
#
#  Copyright (c) 2013 Picarro, Inc. All rights reserved
#
from Host.autogen import interface
from Host.Common import SharedTypes
from Host.Common.hostDasInterface import DasInterface, HostToDspSender

from configobj import ConfigObj
import ctypes

class InstrumentConfig(SharedTypes.Singleton):
    """Configuration of instrument."""
    def __init__(self,filename=None):
        if filename is not None:
            self.config = ConfigObj(filename)
            self.filename = filename

    def reloadFile(self):
        self.config = ConfigObj(self.filename)

    def savePersistentRegistersToConfig(self):
        s = HostToDspSender()
        if "DAS_REGISTERS" not in self.config:
            self.config["DAS_REGISTERS"] = {}
        for ri in interface.registerInfo:
            if ri.persistence:
                if ri.type == ctypes.c_float:
                    self.config["DAS_REGISTERS"][ri.name]= \
                        s.rdRegFloat(ri.name)
                else:
                    self.config["DAS_REGISTERS"][ri.name]= \
                        ri.type(s.rdRegUint(ri.name)).value
        for fpgaMap,regList in interface.persistent_fpga_registers:
            self.config[fpgaMap] = {}
            for r in regList:
                try:
                    self.config[fpgaMap][r] = s.rdFPGA(fpgaMap,r)
                except:
                    Log("Error reading FPGA register %s in %s" % (r,fpgaMap),Level=2)

    def loadPersistentRegistersFromConfig(self):
        s = HostToDspSender()
        if "DAS_REGISTERS" not in self.config:
            self.config["DAS_REGISTERS"] = {}
        for name in self.config["DAS_REGISTERS"]:
            if name not in interface.registerByName:
                Log("Unknown register %s ignored during config file load" % name,Level=2)
            else:
                index = interface.registerByName[name]
                ri = interface.registerInfo[index]
                if ri.writable:
                    if ri.type == ctypes.c_float:
                        value = float(self.config["DAS_REGISTERS"][ri.name])
                        s.wrRegFloat(ri.name,value)
                    else:
                        value = ctypes.c_uint(
                            int(self.config["DAS_REGISTERS"][ri.name])).value
                        s.wrRegUint(ri.name,value)
                else:
                    Log("Unwritable register %s ignored during config file load" % name,Level=2)
        for fpgaMap in self.config:
            if fpgaMap.startswith("FPGA"):
                for name in self.config[fpgaMap]:
                    value = int(self.config[fpgaMap][name])
                    try:
                        s.wrFPGA(fpgaMap,name,value)
                    except:
                        Log("Error writing FPGA register %s in %s" % (name,fpgaMap),Level=2)

    def writeConfig(self,filename=None):
        if filename is None:
            filename = self.filename
            self.config.write()
        else:
            fp = file(filename,"w")
            self.config.write(fp)
            fp.close()
        return filename
        