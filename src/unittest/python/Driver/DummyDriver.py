import os
import types
import ctypes
from Host.Common import SharedTypes
from Host.autogen import interface

class Driver(object):
    def __init__(self, fileDasRegValue=None):
        self.EEPROM = {"HardwareCapabilities": {}}
        self.DasRegValue = {}
        if fileDasRegValue:
            if os.path.exists(fileDasRegValue):
                self.DasRegValue = self.loadDasRegValue(fileDasRegValue)
            else:
                raise("File of DAS register values not found: %s" % fileDasRegValue)

    def _reg_index(self,indexOrName):
        """Convert a name or index into an integer index, raising an exception if the name is not found"""
        if isinstance(indexOrName,types.IntType):
            return indexOrName
        else:
            try:
                return interface.registerByName[indexOrName.strip().upper()]
            except KeyError:
                raise SharedTypes.DasException("Unknown register name %s" % (indexOrName,))

    def rdDasReg(self, regIndexOrName):
        """Reads a DAS register, using either its index or symbolic name"""
        index = self._reg_index(regIndexOrName)
        if index in self.DasRegValue:
            return self.DasRegValue[index]
        else:
            ri = interface.registerInfo[index]
            if not ri.readable:
                raise SharedTypes.DasAccessException("Register %s is not readable" % (regIndexOrName,))
            if ri.type == ctypes.c_float:
                return 0.0
            elif ri.type == ctypes.c_uint:
                return 0
            else:
                return ""

    def wrDasReg(self,regIndexOrName,value,convert=True):
        """Writes to a DAS register, using either its index or symbolic name. If convert is True,
            value is a symbolic string that is looked up in the interface definition file. """
        index = self._reg_index(regIndexOrName)
        ri = interface.registerInfo[index]
        if not ri.writable:
            raise SharedTypes.DasAccessException("Register %s is not writable" % (regIndexOrName,))
        if ri.type in [ctypes.c_uint,ctypes.c_int,ctypes.c_long]:
            self.DasRegValue[index] = int(value)
        elif ri.type == ctypes.c_float:
            self.DasRegValue[index] = float(value)
        else:
            raise SharedTypes.DasException("Type %s of register %s is not known" % (ri.type,regIndexOrName,))
            
    def fetchHardwareCapabilities(self):
        """Fetch hardware capabilities from LOGIC_EEPROM.
        Returns a dictionary.
        """
        try:
            return self.EEPROM["HardwareCapabilities"]
        except:
            return None