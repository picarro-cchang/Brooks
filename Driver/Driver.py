#!/usr/bin/python
#
"""
File Name: Driver.py
Purpose: Low-level communication with hardware via USB interface

File History:
    07-Jan-2009  sze  Initial version.

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "Driver"

import cPickle
import ctypes
import getopt
import inspect
import os
import struct
import sys
import tables
import threading
import time
import types
import traceback
from numpy import array, transpose

from DasConfigure import DasConfigure
from DriverAnalogInterface import AnalogInterface
from Host.autogen import interface
from Host.Common import SharedTypes, version
from Host.Common import CmdFIFO, StringPickler, timestamp
from Host.Common.SharedTypes import RPC_PORT_DRIVER, ctypesToDict
from Host.Common.Broadcaster import Broadcaster
from Host.Common.hostDasInterface import DasInterface, HostToDspSender, StateDatabase
from Host.Common.SingleInstance import SingleInstance
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.hostDasInterface import Operation
from Host.Common.InstErrors import *
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.StringPickler import StringAsObject, ObjAsString
from Host.Common.ctypesConvert import ctypesToDict, dictToCtypes

try:
    from Host.hostBzrVer import version_info as hostBzrVer
except:
    hostBzrVer = None
try:
    from Host.srcBzrVer import version_info as srcBzrVer
except:
    srcBzrVer = None
    
EventManagerProxy_Init(APP_NAME)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
#
# The driver provides a serialized RPC interface for accessing the DAS hardware.
#
class DriverRpcHandler(SharedTypes.Singleton):
    def __init__(self,driver):
        self.server = CmdFIFO.CmdFIFOServer(("", RPC_PORT_DRIVER),
                                            ServerName = "Driver",
                                            ServerDescription = "Driver for CRDS hardware",
                                            threaded = True)
        self.config = driver.config
        self.dasInterface = driver.dasInterface
        self.analogInterface = driver.analogInterface
        self.ver = driver.ver
        self.driver = driver
        self._register_rpc_functions()

    def _register_rpc_functions_for_object(self, obj):
        """ Registers the functions in DriverRpcHandler class which are accessible by XML-RPC

        NOTE - this automatically registers ALL member functions that don't start with '_'.

        i.e.:
          - if adding new rpc calls, just define them (with no _) and you're done
          - if putting helper calls in the class for some reason, use a _ prefix
        """
        classDir = dir(obj)
        for s in classDir:
            attr = obj.__getattribute__(s)
            if callable(attr) and (not s.startswith("_")) and (not inspect.isclass(attr)):
                #if __debug__: print "registering", s
                self.server.register_function(attr,DefaultMode=CmdFIFO.CMD_TYPE_Blocking)

    def _register_rpc_functions(self):
        """ Registers the functions accessible by XML-RPC """
        #register the functions contained in this file...
        self._register_rpc_functions_for_object( self )
        #register some priority functions that can be used even while the Driver
        #is performing a lengthy upload...
        # server._register_priority_function(self.rdDasReg, "HP_rdDasReg")
        # server._register_priority_function(self._getLockStatus, NameSlice = 1)
        Log("Registered RPC functions")

    #
    # These functions need to be implemented to support Instrument Manager
    #
    # These should be added to interface???
    # Enumerated definitions for DASCNTRL_StateType
    #DASCNTRL_StateType = c_ushort
    #DASCNTRL_Reset = 0 # DASCNTRL Reset state.
    #DASCNTRL_Ready = 1 # DASCNTRL Ready state.
    #DASCNTRL_Startup = 2 # DASCNTRL Startup state.
    #DASCNTRL_Diagnostic = 3 # DASCNTRL Diagnostic state.
    #DASCNTRL_Error = 4 # DASCNTRL Error state.
    #DASCNTRL_DspNotBooted = 5 # DASCNTRL Dsp Not Booted.

    def DAS_GetState(self, stateMachineIndex):
        """Need to be implemented"""
        return 1
    
    def getLockStatus(self):
        """Need to be implemented"""
        hardwarePresent = self.rdDasReg("HARDWARE_PRESENT_REGISTER")
        lockStatus = self.rdDasReg("DAS_STATUS_REGISTER")
        allLasersTempLocked = True
        if hardwarePresent & (1<< interface.HARDWARE_PRESENT_Laser1Bit):
            allLasersTempLocked = allLasersTempLocked and (lockStatus & (1<< interface.DAS_STATUS_Laser1TempCntrlLockedBit))
        if hardwarePresent & (1<< interface.HARDWARE_PRESENT_Laser2Bit):
            allLasersTempLocked = allLasersTempLocked and (lockStatus & (1<< interface.DAS_STATUS_Laser2TempCntrlLockedBit))
        if hardwarePresent & (1<< interface.HARDWARE_PRESENT_Laser3Bit):
            allLasersTempLocked = allLasersTempLocked and (lockStatus & (1<< interface.DAS_STATUS_Laser3TempCntrlLockedBit))
        if hardwarePresent & (1<< interface.HARDWARE_PRESENT_Laser4Bit):
            allLasersTempLocked = allLasersTempLocked and (lockStatus & (1<< interface.DAS_STATUS_Laser4TempCntrlLockedBit))
        
        laserTempLockStatus = "Locked" if allLasersTempLocked else "Unlocked"
        warmChamberTempLockStatus = "Locked" if (lockStatus & (1<< interface.DAS_STATUS_WarmBoxTempCntrlLockedBit)) else "Unlocked"
        cavityTempLockStatus = "Locked" if (lockStatus & (1<< interface.DAS_STATUS_CavityTempCntrlLockedBit)) else "Unlocked"
        result = dict(laserTempLockStatus=laserTempLockStatus, warmChamberTempLockStatus=warmChamberTempLockStatus, cavityTempLockStatus = cavityTempLockStatus)
        return result
        
    def startTempControl(self):
        """Need to be implemented"""
        return INST_ERROR_OKAY

    def startLaserControl(self):
        """Need to be implemented"""
        return INST_ERROR_OKAY
        
    def hostReady(self, ready):
        """Set or clear HOST_READY register"""
        pass

    def getPressureReading(self):
        """Fetches the current cavity pressure.
        """
        return self.rdDasReg("CAVITY_PRESSURE_REGISTER")

    def getProportionalValves(self):
        """Fetches settings of inlet and output proportional valves.
        """
        return self.rdDasReg("VALVE_CNTRL_INLET_VALVE_REGISTER"),self.rdDasReg("VALVE_CNTRL_OUTLET_VALVE_REGISTER")

    def getCavityTemperatureAndSetpoint(self):
        """Fetches cavity temperature and setpoint
        """
        return self.rdDasReg("CAVITY_TEMPERATURE_REGISTER"),self.rdDasReg("CAVITY_TEMP_CNTRL_SETPOINT_REGISTER")
        
    def getValveCtrlState(self):
        """Get the current valve control state. Valid values are:
            0: Disabled (=VALVE_CNTRL_DisabledState)
            1: Outlet control (=VALVE_CNTRL_OutletControlState)
            2: Inlet control (=VALVE_CNTRL_InletControlState)
            3: Manual control (=VALVE_CNTRL_ManualControlState)
        """
        return self.rdDasReg("VALVE_CNTRL_STATE_REGISTER")
   
    def startOutletValveControl(self, pressureSetpoint=None, inletValve=None):
        """ Start outlet valve control with the specified pressure setpoint and inlet valve settings, or using values in the configuration registers if the parameters are omitted """
        result = {}
        if pressureSetpoint is not None:
            self.wrDasReg("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER",pressureSetpoint)
        else:
            pressureSetpoint = self.rdDasReg("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER")
        if self.rdDasReg("VALVE_CNTRL_STATE_REGISTER") != interface.VALVE_CNTRL_OutletControlState:
            self.wrDasReg("VALVE_CNTRL_STATE_REGISTER","VALVE_CNTRL_DisabledState")
        self.wrDasReg("VALVE_CNTRL_STATE_REGISTER","VALVE_CNTRL_OutletControlState")
        if inletValve is not None:
            self.wrDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER",inletValve)
        else:
            inletValve = self.rdDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER")
        result["cavityPressureSetpoint"] = pressureSetpoint
        result["inletValve"] = inletValve
        return result

    def startInletValveControl(self, pressureSetpoint=None, outletValve=None):
        """ Start inlet valve control with the specified pressure setpoint and outlet valve settings, or using values in the configuration registers if the parameters are omitted """
        result = {}
        if pressureSetpoint is not None:
            self.wrDasReg("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER",pressureSetpoint)
        else:
            pressureSetpoint = self.rdDasReg("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER")
        if self.rdDasReg("VALVE_CNTRL_STATE_REGISTER") != interface.VALVE_CNTRL_InletControlState:
            self.wrDasReg("VALVE_CNTRL_STATE_REGISTER","VALVE_CNTRL_DisabledState")
        self.wrDasReg("VALVE_CNTRL_STATE_REGISTER","VALVE_CNTRL_InletControlState")
        if outletValve is not None:
            self.wrDasReg("VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER",outletValve)
        else:
            outletValve = self.rdDasReg("VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER")
        result["cavityPressureSetpoint"] = pressureSetpoint
        result["outletValve"] = outletValve
        return result
        
    def allVersions(self):
        versionDict = {}
        versionDict["interface"] = interface.interface_version
        versionDict["host release"] = version.versionString()
        if hostBzrVer:
            versionDict["host version id"] = hostBzrVer['revision_id']
            versionDict["host version no"] = hostBzrVer['revno']
        if srcBzrVer:
            versionDict["src version id"] = srcBzrVer['revision_id']
            versionDict["src version no"] = srcBzrVer['revno']
        try:
            versionDict["config - app version no"] = self.ver["appVer"]
            versionDict["config - instr version no"] = self.ver["instrVer"]
        except Exception, err:
            print err
        return versionDict
    
    def saveRegValues(self,regList):
        # Save the values of the registers specified in regList into a "vault" which can later
        #  be used to restore them with restoreRegValues. The elements of regList can be integers
        #  representing DSP registers or tuples of integers representing FPGA registers in 
        #  (block,offset) pairs. These integers may be referred to symbolically by passing strings
        #  which are looked up in the interface file.
        vault = []
        for reg in regList:
            if isinstance(reg,(tuple,list)):
                if len(reg) != 2:
                    raise ValueError("An FPGA register description tuple must have two elements")
                else:
                    vault.append((reg,self.rdFPGA(*reg)))
            else:
                vault.append((reg,self.rdDasReg(reg)))
        return vault
    
    def restoreRegValues(self,vault):
        # Restore register values stored in the vault (produced by saveRegValues)
        for reg,value in vault:
            if isinstance(reg,(tuple,list)):
                if len(reg) != 2:
                    raise ValueError("An FPGA register description tuple must have two elements")
                else:
                    self.wrFPGA(reg[0],reg[1],value)
            else:
                self.wrDasReg(reg,value)

    def _reg_index(self,indexOrName):
        """Convert a name or index into an integer index, raising an exception if the name is not found"""
        if isinstance(indexOrName,types.IntType):
            return indexOrName
        else:
            try:
                return interface.registerByName[indexOrName.strip().upper()]
            except KeyError:
                raise SharedTypes.DasException("Unknown register name %s" % (indexOrName,))

    def rdDasReg(self,regIndexOrName):
        """Reads a DAS register, using either its index or symbolic name"""
        index = self._reg_index(regIndexOrName)
        ri = interface.registerInfo[index]
        if not ri.readable:
            raise SharedTypes.DasAccessException("Register %s is not readable" % (regIndexOrName,))
        if ri.type == ctypes.c_float:
            return self.dasInterface.hostToDspSender.rdRegFloat(index)
        elif ri.type == ctypes.c_uint:
            return self.dasInterface.hostToDspSender.rdRegUint(index)
        else:
            return ctypes.c_int32(self.dasInterface.hostToDspSender.rdRegUint(index)).value

    def rdDasRegList(self,regList):
        return [self.rdDasReg(reg) for reg in regList]

    def rdFPGA(self,base,reg):
        return self.dasInterface.hostToDspSender.rdFPGA(base,reg)

    def rdRegList(self,regList):
        result = []
        for regLoc,reg in regList:
            if regLoc == "dsp": result.append(self.rdDasReg(reg))
            elif regLoc == "fpga": result.append(self.rdFPGA(0,reg))
            else: result.append(None)
        return result

    def wrFPGA(self,base,reg,value,convert=True):
        if convert:
            value = self._value(value)
        return self.dasInterface.hostToDspSender.wrFPGA(base,reg,value)

    def _value(self,valueOrName):
        """Convert valueOrName into an value, raising an exception if the name is not found"""
        if isinstance(valueOrName,types.StringType):
            try:
                valueOrName = getattr(interface,valueOrName)
            except AttributeError:
                raise AttributeError("Value identifier not recognized %r" % valueOrName)
        return valueOrName

    def wrDasRegList(self,regList,values):
        for r,value in zip(regList,values):
            self.wrDasReg(r,value)

    def wrRegList(self,regList,values):
        for (regLoc,reg),value in zip(regList,values):
            if regLoc == "dsp": self.wrDasReg(reg,value)
            elif regLoc == "fpga": self.wrFPGA(0,reg,value)

    def wrDasReg(self,regIndexOrName,value,convert=True):
        """Writes to a DAS register, using either its index or symbolic name. If convert is True,
            value is a symbolic string that is looked up in the interface definition file. """
        if convert:
            value = self._value(value)
        index = self._reg_index(regIndexOrName)
        ri = interface.registerInfo[index]
        if not ri.writable:
            raise SharedTypes.DasAccessException("Register %s is not writable" % (regIndexOrName,))
        if ri.type in [ctypes.c_uint,ctypes.c_int,ctypes.c_long]:
            return self.dasInterface.hostToDspSender.wrRegUint(index,value)
        elif ri.type == ctypes.c_float:
            return self.dasInterface.hostToDspSender.wrRegFloat(index,value)
        else:
            raise SharedTypes.DasException("Type %s of register %s is not known" % (ri.type,regIndexOrName,))

    def rdRingdown(self,bank):
        """Fetches the contents of ringdown memory from the specified bank"""
        dataBase = (0x0, 0x4000)
        metaBase = (0x1000, 0x5000)
        paramBase = (0x3000, 0x7000)
        base = dataBase[bank]
        data = [x for x in self.dasInterface.hostToDspSender.rdRingdownMemArray(base,4096)]
        base = metaBase[bank]
        meta = [x for x in self.dasInterface.hostToDspSender.rdRingdownMemArray(base,4096)]
        base = paramBase[bank]
        paramsAsUint = self.dasInterface.hostToDspSender.rdRingdownMemArray(base,12)
        param = interface.RingdownParamsType.from_address(ctypes.addressof(paramsAsUint))
        return (array(data),array(meta).reshape(512,8).transpose(),ctypesToDict(param))
    def rdRingdownBuffer(self,buffNum):
        """Fetches contents of ringdown buffer which is QDMA transferred from the FPGA to DSP memory"""
        RINGDOWN_BUFFER_BASE = interface.SHAREDMEM_ADDRESS + 4*interface.RINGDOWN_BUFFER_OFFSET
        base = RINGDOWN_BUFFER_BASE if buffNum == 0 else RINGDOWN_BUFFER_BASE+4*interface.RINGDOWN_BUFFER_SIZE
        bufferAsUint = self.dasInterface.hostToDspSender.rdDspMemArray(base,interface.RINGDOWN_BUFFER_SIZE)
        rdBuffer = interface.RingdownBufferType.from_address(ctypes.addressof(bufferAsUint))
        data = [(x&0xFFFF) for x in rdBuffer.ringdownWaveform]
        meta = [(x>>16) for x in rdBuffer.ringdownWaveform]
        return (array(data),array(meta).reshape(512,8).transpose(),ctypesToDict(rdBuffer.parameters))
    def rdScheme(self,schemeNum):
        """Reads a scheme from table number schemeNum"""
        return self.dasInterface.hostToDspSender.rdScheme(schemeNum)

    def wrScheme(self,schemeNum,numRepeats,schemeRows):
        """Writes a scheme to table number schemeNum consisting of numRepeats repeats of the list schemeRows"""
        self.dasInterface.hostToDspSender.wrScheme(schemeNum,numRepeats,schemeRows)

    def getValveMask(self):
        """Read the valve mask - the lower 6 bits represent the binary code of the solenoid valves.
        """
        return self.rdDasReg("VALVE_CNTRL_SOLENOID_VALVES_REGISTER") & 0x3F
    
    def setValveMask(self, mask):
        self.wrDasReg("VALVE_CNTRL_SOLENOID_VALVES_REGISTER", mask & 0x3F)

    def getMPVPosition(self):
        """Read the multi-position valve (MPV) position.
        """
        return self.rdDasReg("VALVE_CNTRL_MPV_POSITION_REGISTER")
    
    def setMPVPosition(self, pos):
        self.wrDasReg("VALVE_CNTRL_MPV_POSITION_REGISTER", pos)
        
    def closeValves(self,valveMask=0x3F):
        """ Close the valves specified by the valveMask. This is a bitmask with bits 0 through 5 corresponding with solenoid valves 1 through 6. 
        A "1" bit causes the valve to close, a "0" bit leaves the valve state unchanged.
        """
        currValveMask = self.getValveMask()
        newValveMask = currValveMask & ~valveMask
        self.setValveMask(newValveMask)

    def openValves(self,valveMask=0x0):
        """ Open the valves specified by the valveMask. This is a bitmask with bits 0 through 5 corresponding with solenoid valves 1 through 6. 
        A "1" bit causes the valve to open, a "0" bit leaves the valve state unchanged.
        """
        currValveMask = self.getValveMask()
        newValveMask = currValveMask | valveMask
        self.setValveMask(newValveMask)
        
    def rdValveSequence(self):
        """Reads the valve sequence"""
        return self.dasInterface.hostToDspSender.rdValveSequence()

    def wrValveSequence(self,sequenceRows):
        """Writes a valve sequence"""
        self.dasInterface.hostToDspSender.wrValveSequence(sequenceRows)

    def rdVirtualLaserParams(self,vLaserNum):
        """Returns the virtual laser parameters associated with virtual laser vLaserNum (ONE-based)as 
           a dictionary.
           N.B. The "actualLaser" field within the VirtualLaserParams structure is ZERO-based
           for compatibility with the DAS software
           """
        return SharedTypes.ctypesToDict(self.dasInterface.hostToDspSender.rdVirtualLaserParams(vLaserNum))

    def wrVirtualLaserParams(self,vLaserNum,laserParams):
        """Wites the virtual laser parameters (specified as a dictionary) associated with 
           virtual laser vLaserNum (ONE-based).
           N.B. The "actualLaser" field within the VirtualLaserParams structure is ZERO-based
           for compatibility with the DAS software
           """
        p = interface.VirtualLaserParamsType()
        SharedTypes.dictToCtypes(laserParams,p)
        self.dasInterface.hostToDspSender.wrVirtualLaserParams(vLaserNum,p)

    def loadIniFile(self):
        """Loads state from instrument configuration file"""
        config = InstrumentConfig()
        config.reloadFile()
        config.loadPersistentRegistersFromConfig()
        Log("Loaded instrument configuration from file %s" % \
            config.filename,Level=1)

    def writeIniFile(self,filename=None):
        """Writes out the current instrument configuration to the
            specified filename, or to the one specified in the driver
            configuration file"""
        config = InstrumentConfig()
        config.savePersistentRegistersToConfig()
        name = config.writeConfig(filename)
        Log("Saved instrument configuration to file %s" % (name,),Level=1)

    def getHistory(self,streamNum):
        """Get historical data associated with streamNum from the database"""
        return StateDatabase().getHistory(streamNum)

    def getHistoryByCommand(self, command, args=None):
        """Get historical data associated with given command from the database"""
        return StateDatabase().getHistoryByCommand(command, args)
        
    def saveWlmHist(self,wlmHist):
        """Save WLM history in database"""
        StateDatabase().saveWlmHist(wlmHist)
        
    def getConfigFile(self):
        configFile = os.path.abspath(InstrumentConfig().filename)
        return configFile

    def wrDac(self,channel,value):
        """Writes "value" to the specified analog interface DAC channel. """
        self.dasInterface.hostToDspSender.wrDac(channel,value)

    #def wrAuxiliary(self,data):
    #    """Writes the "data" string to the auxiliary board"""
    #    self.dasInterface.hostToDspSender.wrAuxiliary(ctypes.create_string_buffer(data,len(data)))
        
    #def getDacQueueFreeSlots(self):
    #    return self.dasInterface.hostToDspSender.getDacQueueFreeSlots()

    #def getDacQueueErrors(self):
    #    return self.dasInterface.hostToDspSender.getDacQueueErrors()

    #def setDacQueuePeriod(self,channel,period):
    #    return self.dasInterface.hostToDspSender.setDacQueuePeriod(channel,period)

    #def resetDacQueues(self):
    #    return self.dasInterface.hostToDspSender.resetDacQueues()

    #def serveDacQueues(self):
    #    return self.dasInterface.hostToDspSender.serveDacQueues()
       
    def rdDspTimerRegisters(self):
        return self.dasInterface.hostToDspSender.rdDspTimerRegisters()

    def resetDacQueue(self):
        return self.dasInterface.hostToDspSender.resetDacQueue()

    def setDacTimestamp(self,timestamp):
        return self.dasInterface.hostToDspSender.setDacTimestamp(timestamp)

    def setDacReloadCount(self,reloadCount):
        return self.dasInterface.hostToDspSender.setDacReloadCount(reloadCount)
    
    def getDacTimestamp(self):
        return self.dasInterface.hostToDspSender.getDacTimestamp()

    def getDacReloadCount(self):
        return self.dasInterface.hostToDspSender.getDacReloadCount()
        
    def getDacQueueFree(self):
        return self.dasInterface.hostToDspSender.getDacQueueFree()

    def getDacQueueErrors(self):
        return self.dasInterface.hostToDspSender.getDacQueueErrors()
        
    def enqueueDacSamples(self,data):
        return self.dasInterface.hostToDspSender.enqueueDacSamples(ctypes.create_string_buffer(data,len(data)))
        
    #def disableLaserCurrent(self,laserNum):
    #    # Turn off laser current for laserNum (0-index)
    #    if laserNum<0 or laserNum>=interface.MAX_LASERS:
    #        raise ValueError("Invalid laser number in enableLaserCurrent")
    #    enableSource = 1 << (interface.INJECT_CONTROL_LASER_CURRENT_ENABLE_B + laserNum)
    #    removeShort  = 1 << (interface.INJECT_CONTROL_MANUAL_LASER_ENABLE_B + laserNum)
    #    injControl = self.rdFPGA("FPGA_INJECT","INJECT_CONTROL")
    #    injControl &= ~(enableSource |removeShort)
    #    self.wrFPGA("FPGA_INJECT","INJECT_CONTROL",injControl)
    
    #def enableLaserCurrent(self,laserNum):
    #    # Turn on laser current for laserNum (0-index)
    #    if laserNum<0 or laserNum>=interface.MAX_LASERS:
    #        raise ValueError("Invalid laser number in enableLaserCurrent")
    #    enableSource = 1 << (interface.INJECT_CONTROL_LASER_CURRENT_ENABLE_B + laserNum)
    #    removeShort  = 1 << (interface.INJECT_CONTROL_MANUAL_LASER_ENABLE_B + laserNum)
    #    injControl = self.rdFPGA("FPGA_INJECT","INJECT_CONTROL")
    #    injControl |= enableSource | removeShort
    #    self.wrFPGA("FPGA_INJECT","INJECT_CONTROL",injControl)
    
    def startEngine(self):
        # Turn on lasers, warm box and cavity thermal control followed by
        #  laser current sources
        for laserNum in range(1,interface.MAX_LASERS+1):
            if DasConfigure().installCheck("LASER%d_PRESENT" % laserNum) or \
               (laserNum == 4 and DasConfigure().installCheck("SOA_PRESENT")):
                self.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % laserNum,interface.TEMP_CNTRL_EnabledState)
        self.wrDasReg("WARM_BOX_TEMP_CNTRL_STATE_REGISTER",interface.TEMP_CNTRL_EnabledState)
        self.wrDasReg("CAVITY_TEMP_CNTRL_STATE_REGISTER",interface.TEMP_CNTRL_EnabledState)
        if DasConfigure().heaterControlMode in [interface.HEATER_CONTROL_MODE_DELTA_TEMP,interface.HEATER_CONTROL_MODE_TEC_TARGET]:
            self.wrDasReg("HEATER_TEMP_CNTRL_STATE_REGISTER",interface.TEMP_CNTRL_EnabledState)
        elif DasConfigure().heaterControlMode in [interface.HEATER_CONTROL_MODE_HEATER_FIXED]:
            self.wrDasReg("HEATER_TEMP_CNTRL_STATE_REGISTER",interface.TEMP_CNTRL_ManualState)        
        self.wrDasReg("TEC_CNTRL_REGISTER",interface.TEC_CNTRL_Enabled)
        for laserNum in range(1,interface.MAX_LASERS+1):
            if DasConfigure().installCheck("LASER%d_PRESENT" % laserNum):
                self.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % laserNum,interface.LASER_CURRENT_CNTRL_ManualState)
                
    def selectActualLaser(self,aLaserNum):
        # Select laserNum, placing it under automatic control and activating the optical switch. The value
        #  of aLaserNum is ONE-based
        injControl = self.rdFPGA("FPGA_INJECT","INJECT_CONTROL")
        if aLaserNum <= 0 or aLaserNum > interface.MAX_LASERS:
            raise ValueError("aLaserNum must be in range 1..4 for selectActualLaser")
        laserSel = (aLaserNum-1) << interface.INJECT_CONTROL_LASER_SELECT_B
        laserMask = (interface.MAX_LASERS-1) << interface.INJECT_CONTROL_LASER_SELECT_B
        injControl = (injControl & (~laserMask)) | laserSel
        self.wrFPGA("FPGA_INJECT","INJECT_CONTROL",injControl)
    
    def dasGetTicks(self):
        sender = self.dasInterface.hostToDspSender
        sender.doOperation(Operation("ACTION_GET_TIMESTAMP",["TIMESTAMP_LSB_REGISTER","TIMESTAMP_MSB_REGISTER"]))
        return self.rdDasReg("TIMESTAMP_MSB_REGISTER")<<32L | self.rdDasReg("TIMESTAMP_LSB_REGISTER")
        
    def hostGetTicks(self):
        return timestamp.getTimestamp()

    def resyncDas(self):
        sender = self.dasInterface.hostToDspSender
        ts = timestamp.getTimestamp()
        sender.doOperation(Operation("ACTION_SET_TIMESTAMP",[ts&0xFFFFFFFF,ts>>32]))
        
    def setSingleScan(self):
        self.wrDasReg(interface.SPECT_CNTRL_MODE_REGISTER,interface.SPECT_CNTRL_SchemeSingleMode)

    def setRepeatingScan(self):
        self.wrDasReg(interface.SPECT_CNTRL_MODE_REGISTER,interface.SPECT_CNTRL_SchemeMultipleMode)
        
    def startScan(self):
        self.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER,interface.SPECT_CNTRL_StartingState)

    def stopScan(self):
        self.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER,interface.SPECT_CNTRL_IdleState)

    def scanIdle(self):
        return self.rdDasReg(interface.SPECT_CNTRL_STATE_REGISTER) == interface.SPECT_CNTRL_IdleState
    
    def rdEnvToString(self,index,envClass):
        return ObjAsString(self.dasInterface.hostToDspSender.rdEnv(index,envClass))
        
    def wrEnvFromString(self,index,envClass,envAsString):
        return self.dasInterface.hostToDspSender.wrEnv(index,StringAsObject(envAsString,envClass))
        
    def rdBlock(self,offset,numInt):
        # Performs a host read of numInt unsigned integers from
        #  the communications region starting at offset
        return self.dasInterface.hostToDspSender.rdBlock(offset,numInt)

    def doOperation(self,op):
        """Perform an operation"""
        return self.dasInterface.hostToDspSender.doOperation(op)
        
    def rdEeprom(self,whichEeprom,startAddress,nBytes,chunkSize=64):
        """Read nBytes from whichEeprom starting at startAddress (which must be a multiple 
        of 4). Memory acccesses are done in multiples of chunkSize (<=64 in bytes) for 
        efficiency. Returns result as a list of bytes."""
        if startAddress % 4:
            raise ValueError("startAddress must be a multiple of 4 in rdEeprom")
        if chunkSize <= 0 or chunkSize > 64:
            raise ValueError("chunkSize must lie between 1 and 64")
        myEnv = interface.Byte64EnvType()
        i2cIndex = interface.i2cByIdent[whichEeprom][0]
        ctypesObject = (ctypes.c_ubyte*nBytes)()
        ctypesObjectBase = ctypes.addressof(ctypesObject)
        objPtr = 0
        while nBytes > 0:
            bytesRead = min(4*((nBytes+3)//4),chunkSize)
            op = Operation("ACTION_EEPROM_READ",[i2cIndex,startAddress,bytesRead],"BYTE64_ENV")
            self.doOperation(op)
            result = StringAsObject(self.rdEnvToString("BYTE64_ENV",interface.Byte64EnvType),
                                    interface.Byte64EnvType)
            ctypes.memmove(ctypesObjectBase+objPtr,result.buffer,min(nBytes,bytesRead))
            startAddress += bytesRead
            objPtr += bytesRead
            nBytes -= bytesRead
        return ctypesObject[:]

    def rdEepromLowLevel(self,chain,mux,i2cAddr,startAddress,nBytes,chunkSize=64):
        """Read nBytes from I2C EEPROM starting at startAddress (which must be a multiple 
        of 4). Memory acccesses are done in multiples of chunkSize (<=64 in bytes) for 
        efficiency. Returns result as a list of bytes."""
        if startAddress % 4:
            raise ValueError("startAddress must be a multiple of 4 in rdEeprom")
        if chunkSize <= 0 or chunkSize > 64:
            raise ValueError("chunkSize must lie between 1 and 64")
        myEnv = interface.Byte64EnvType()
        ctypesObject = (ctypes.c_ubyte*nBytes)()
        ctypesObjectBase = ctypes.addressof(ctypesObject)
        objPtr = 0
        while nBytes > 0:
            bytesRead = min(4*((nBytes+3)//4),chunkSize)
            op = Operation("ACTION_EEPROM_READ_LOW_LEVEL",[chain,mux,i2cAddr,startAddress,bytesRead],"BYTE64_ENV")
            self.doOperation(op)
            result = StringAsObject(self.rdEnvToString("BYTE64_ENV",interface.Byte64EnvType),
                                    interface.Byte64EnvType)
            ctypes.memmove(ctypesObjectBase+objPtr,result.buffer,min(nBytes,bytesRead))
            startAddress += bytesRead
            objPtr += bytesRead
            nBytes -= bytesRead
        return ctypesObject[:]
    
    def rdEepromBoardTestLowLevel(self,chain,mux,i2cAddr,startAddress,nBytes,chunkSize=64):
        """Read nBytes from I2C EEPROM starting at startAddress (which must be a multiple 
        of 4). Memory acccesses are done in multiples of chunkSize (<=64 in bytes) for 
        efficiency. Returns result as a list of bytes."""
        if startAddress % 4:
            raise ValueError("startAddress must be a multiple of 4 in rdEeprom")
        if chunkSize <= 0 or chunkSize > 64:
            raise ValueError("chunkSize must lie between 1 and 64")
        myEnv = interface.Byte64EnvType()
        ctypesObject = (ctypes.c_ubyte*nBytes)()
        ctypesObjectBase = ctypes.addressof(ctypesObject)
        objPtr = 0
        while nBytes > 0:
            bytesRead = min(4*((nBytes+3)//4),chunkSize)
            op = Operation("ACTION_EEPROM_READ_LOW_LEVEL",[chain,mux,i2cAddr,startAddress,-bytesRead],"BYTE64_ENV")
            self.doOperation(op)
            result = StringAsObject(self.rdEnvToString("BYTE64_ENV",interface.Byte64EnvType),
                                    interface.Byte64EnvType)
            ctypes.memmove(ctypesObjectBase+objPtr,result.buffer,min(nBytes,bytesRead))
            startAddress += bytesRead
            objPtr += bytesRead
            nBytes -= bytesRead
        return ctypesObject[:]
        
    def wrEeprom(self,whichEeprom,startAddress,byteList,pageSize=32):
        """Writes bytes from byteList into whichEeprom starting at startAddress (which must 
        be a multiple of 4).  The pageSize (<=64, in bytes) is used to perform the writing 
        in chunks, being careful not to cross page boundaries."""
        if startAddress % 4:
            raise ValueError("startAddress must be a multiple of 4 in wrEeprom")
        if pageSize <= 0 or pageSize > 64:
            raise ValueError("pageSize must lie between 1 and 64")

        myEnv = interface.Byte64EnvType()
        i2cIndex = interface.i2cByIdent[whichEeprom][0]
        bytesLeft = len(byteList)
        ctypesObject = (ctypes.c_ubyte*bytesLeft)(*byteList)
        ctypesObjectBase = ctypes.addressof(ctypesObject)
        objPtr = 0
        while bytesLeft>0:
            pageEnd = pageSize * ((startAddress + pageSize) // pageSize)
            nBytes = min(pageEnd - startAddress, 4*((bytesLeft+3)//4))
            ctypes.memmove(myEnv.buffer,ctypesObjectBase+objPtr,min(nBytes,bytesLeft))
            self.wrEnvFromString("BYTE64_ENV",interface.Byte64EnvType,ObjAsString(myEnv))
            op = Operation("ACTION_EEPROM_WRITE",[i2cIndex,startAddress,nBytes],"BYTE64_ENV")
            self.doOperation(op)
            startAddress = pageEnd
            objPtr += nBytes
            bytesLeft -= nBytes
            while not self.doOperation(Operation("ACTION_EEPROM_READY",[i2cIndex])):
                time.sleep(0.1)
        
    def wrEepromLowLevel(self,chain,mux,i2cAddr,startAddress,byteList,pageSize=32):
        """Writes bytes from byteList into I2c EEPROM starting at startAddress (which must 
        be a multiple of 4).  The pageSize (<=64, in bytes) is used to perform the writing 
        in chunks, being careful not to cross page boundaries."""
        if startAddress % 4:
            raise ValueError("startAddress must be a multiple of 4 in wrEeprom")
        if pageSize <= 0 or pageSize > 64:
            raise ValueError("pageSize must lie between 1 and 64")

        myEnv = interface.Byte64EnvType()
        bytesLeft = len(byteList)
        ctypesObject = (ctypes.c_ubyte*bytesLeft)(*byteList)
        ctypesObjectBase = ctypes.addressof(ctypesObject)
        objPtr = 0
        while bytesLeft>0:
            pageEnd = pageSize * ((startAddress + pageSize) // pageSize)
            nBytes = min(pageEnd - startAddress, 4*((bytesLeft+3)//4))
            ctypes.memmove(myEnv.buffer,ctypesObjectBase+objPtr,min(nBytes,bytesLeft))
            self.wrEnvFromString("BYTE64_ENV",interface.Byte64EnvType,ObjAsString(myEnv))
            op = Operation("ACTION_EEPROM_WRITE_LOW_LEVEL",[chain,mux,i2cAddr,startAddress,nBytes],"BYTE64_ENV")
            self.doOperation(op)
            startAddress = pageEnd
            objPtr += nBytes
            bytesLeft -= nBytes
            while not self.doOperation(Operation("ACTION_EEPROM_READY_LOW_LEVEL",[chain,mux,i2cAddr])):
                time.sleep(0.1)
                
    def wrEepromBoardTestLowLevel(self,chain,mux,i2cAddr,startAddress,byteList,pageSize=32):
        """Writes bytes from byteList into I2c EEPROM starting at startAddress (which must 
        be a multiple of 4).  The pageSize (<=64, in bytes) is used to perform the writing 
        in chunks, being careful not to cross page boundaries."""
        if startAddress % 4:
            raise ValueError("startAddress must be a multiple of 4 in wrEeprom")
        if pageSize <= 0 or pageSize > 64:
            raise ValueError("pageSize must lie between 1 and 64")

        myEnv = interface.Byte64EnvType()
        bytesLeft = len(byteList)
        ctypesObject = (ctypes.c_ubyte*bytesLeft)(*byteList)
        ctypesObjectBase = ctypes.addressof(ctypesObject)
        objPtr = 0
        while bytesLeft>0:
            pageEnd = pageSize * ((startAddress + pageSize) // pageSize)
            nBytes = min(pageEnd - startAddress, 4*((bytesLeft+3)//4))
            ctypes.memmove(myEnv.buffer,ctypesObjectBase+objPtr,min(nBytes,bytesLeft))
            self.wrEnvFromString("BYTE64_ENV",interface.Byte64EnvType,ObjAsString(myEnv))
            op = Operation("ACTION_EEPROM_WRITE_LOW_LEVEL",[chain,mux,i2cAddr,startAddress,-nBytes],"BYTE64_ENV")
            self.doOperation(op)
            startAddress = pageEnd
            objPtr += nBytes
            bytesLeft -= nBytes
            while not self.doOperation(Operation("ACTION_EEPROM_READY_LOW_LEVEL",[chain,mux,i2cAddr])):
                time.sleep(0.1)
                
    def i2cCheckLowLevel(self,chain,mux,i2cAddr):
        """Check for an I2C device on the specified chain, multiplexer channel and I2C address"""
        status = self.doOperation(Operation("ACTION_I2C_CHECK",[chain,mux,i2cAddr]))
        return status >= 0
    
    def fetchObject(self,whichEeprom,startAddress=0):
        """Fetch a pickled object from the specified EEPROM, starting at "startAddress".
        The first four bytes contains the length of the pickled string. Returns the 
        object and the address of the next object."""
        if not DasConfigure().i2cConfig[whichEeprom]:
            raise ValueError("%s is not available" % whichEeprom)
        nBytes, = struct.unpack("I","".join([chr(c) for c in self.rdEeprom(whichEeprom,startAddress,4)]))
        return (cPickle.loads("".join([chr(c) for c in self.rdEeprom(whichEeprom,startAddress+4,nBytes)])),
                startAddress + 4*((nBytes+3)//4))
                
    def fetchInstrInfo(self, option="all"):
        option = option.lower()
        try:
            curVal = self.fetchObject("LOGIC_EEPROM")
            curValDict = curVal[0]
            chassis = curValDict["Chassis"]
            analyzerType = curValDict["Analyzer"]
            analyzerNum = curValDict["AnalyzerNum"]
        except:
            return None
        if option == "chassis":
            return chassis
        elif option == "analyzer":
            return analyzerType
        elif option == "analyzernum":
            return analyzerNum
        elif option == "analyzername":
            return "%s%s" % (analyzerType, analyzerNum)
        elif option == "all":
            return "%s-%s%s" % (chassis, analyzerType, analyzerNum)
        else:
            return None
    
    def verifyInstallerId(self):
        return (self.driver.validInstallerId, self.driver.analyzerType, self.driver.installerId)
        
    def verifyObject(self,whichEeprom,object,startAddress=0):
        """Verify that the pickled object was written correctly to specified EEPROM, starting at 
        "startAddress". Returns True iff successful. """
        if not DasConfigure().i2cConfig[whichEeprom]:
            raise ValueError("%s is not available" % whichEeprom)
        s = cPickle.dumps(object,-1)
        nBytes, = struct.unpack("I","".join([chr(c) for c in self.rdEeprom(whichEeprom,startAddress,4)]))
        if nBytes != len(s): return False
        r = "".join([chr(c) for c in self.rdEeprom(whichEeprom,startAddress+4,nBytes)])
        return r == s
    
    def shelveObject(self,whichEeprom,object,startAddress=0):
        """Store a pickled object from to specified EEPROM, starting at "startAddress".
        The first four bytes contains the length of the pickled string. Returns the 
        address of the next object."""
        if not DasConfigure().i2cConfig[whichEeprom]:
            raise ValueError("%s is not available" % whichEeprom)
        s = cPickle.dumps(object,-1)
        nBytes = len(s)
        self.wrEeprom(whichEeprom,startAddress,[ord(c) for c in struct.pack("I",nBytes)+s])
        return startAddress + 4*((nBytes+7)//4)

    def fetchLogicEEPROM(self):
        """Fetch the instrument information from LOGIC_EEPROM.
        The first four bytes contains the length of the pickled string. Returns the 
        object and the address of the next object.
        """
        if not DasConfigure().i2cConfig["LOGIC_EEPROM"]:
            raise ValueError("LOGIC_EEPROM is not available")
        nBytes, = struct.unpack("I","".join([chr(c) for c in self.rdEeprom("LOGIC_EEPROM",0,4)]))
        # Try to avoid EEPROM error
        if nBytes > 100:
            raise ValueError("LOGIC_EEPROM returns wrong size (%d bytes)" % nBytes)
        return (cPickle.loads("".join([chr(c) for c in self.rdEeprom("LOGIC_EEPROM",4,nBytes)])),
               4*((nBytes+3)//4))
                
    def fetchWlmCal(self):
        """Fetch the WLM calibration data as a dictionary from WLM_EEPROM"""
        if not DasConfigure().i2cConfig["WLM_EEPROM"]:
            raise ValueError("WLM_EEPROM is not available")
        wlmCal = interface.WLMCalibrationType()
        if ctypes.sizeof(wlmCal) != 4096:
            raise ValueError("WLMCalibrationType has wrong size (%d bytes)" % ctypes.sizeof(wlmCal))
        ctypes.memmove(ctypes.addressof(wlmCal),"".join([chr(c) for c in self.rdEeprom("WLM_EEPROM",0,4096)]),4096)
        return ctypesToDict(wlmCal)

    def fetchWlmHdr(self):
        """Fetch the WLM calibration header from WLM_EEPROM"""
        if not DasConfigure().i2cConfig["WLM_EEPROM"]:
            raise ValueError("WLM_EEPROM is not available")
        wlmHdr = interface.WLMHeaderType()
        if ctypes.sizeof(wlmHdr) != 64:
            raise ValueError("WLMHeaderType has wrong size (%d bytes)" % ctypes.sizeof(wlmHdr))
        ctypes.memmove(ctypes.addressof(wlmHdr),"".join([chr(c) for c in self.rdEeprom("WLM_EEPROM",0,64)]),64)
        return ctypesToDict(wlmHdr)
        
    def shelveWlmCal(self,wlmCalDict):
        """Save the WLM calibration data as a dictionary to the WLM_EEPROM"""
        if not DasConfigure().i2cConfig["WLM_EEPROM"]:
            raise ValueError("WLM_EEPROM is not available" % whichEeprom)
        wlmCal = interface.WLMCalibrationType()
        dictToCtypes(wlmCalDict,wlmCal)
        if ctypes.sizeof(wlmCal) != 4096:
            raise ValueError("WLMCalibrationType has wrong size (%d bytes)" % ctypes.sizeof(wlmCal))
        self.wrEeprom("WLM_EEPROM",0,[ord(c) for c in buffer(wlmCal)])
    
    def readWlmDarkCurrents(self):
        """Read dark current values from WLM EEPROM (if possible) and update registers"""
        hdrDict = self.fetchWlmHdr()
        self.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_ETA1_OFFSET",int(hdrDict['etalon1_offset']+0.5))
        self.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_REF1_OFFSET",int(hdrDict['reference1_offset']+0.5))
        self.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_ETA2_OFFSET",int(hdrDict['etalon2_offset']+0.5))
        self.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_REF2_OFFSET",int(hdrDict['reference2_offset']+0.5))
    
    def resetDas(self):
        Log("Reset DAS called",Level=3)
        return INST_ERROR_OKAY
        
    def stopLaserControl(self):
        Log("Stop laser control called",Level=3)
        return INST_ERROR_OKAY
        
    def sendDacSamples(self,samples):
        """Sends a list of samples of the form [(timestamp,channel,voltage),...]
        to the analog interface card"""
        for timestamp,channel,voltage in samples:
            self.analogInterface.enqueueSample(timestamp,channel,voltage)        
            
    def writeDacSample(self,channel,voltage):
        """Sends a voltage immediately to the specified DAC channel"""
        self.analogInterface.writeSample(channel,voltage)
        
    def getParameterForms(self):
        """Returns the dictionary of parameter forms for the controller GUI"""
        return DasConfigure().parameter_forms
 
    def shutDown(self):
        '''Place instrument in idle state for shutdown'''
        # Disable spectrum controller
        self.wrDasReg('SPECT_CNTRL_STATE_REGISTER','SPECT_CNTRL_IdleState')
        # Wait for all current controllers to leave automatic state
        auto = interface.LASER_CURRENT_CNTRL_AutomaticState
        while True:
            if self.rdDasReg('LASER1_CURRENT_CNTRL_STATE_REGISTER')!=auto and \
               self.rdDasReg('LASER2_CURRENT_CNTRL_STATE_REGISTER')!=auto and \
               self.rdDasReg('LASER3_CURRENT_CNTRL_STATE_REGISTER')!=auto and \
               self.rdDasReg('LASER4_CURRENT_CNTRL_STATE_REGISTER')!=auto:
                break
            else:
                time.sleep(0.1)
        # Close all solenoid valves        
        self.wrDasReg('VALVE_CNTRL_SOLENOID_VALVES_REGISTER',0)
        # Close proportional valves
        self.wrDasReg('VALVE_CNTRL_STATE_REGISTER','VALVE_CNTRL_DisabledState')
        # Disable laser current control loops
        self.wrDasReg('LASER1_CURRENT_CNTRL_STATE_REGISTER','LASER_CURRENT_CNTRL_DisabledState')
        self.wrDasReg('LASER2_CURRENT_CNTRL_STATE_REGISTER','LASER_CURRENT_CNTRL_DisabledState')
        self.wrDasReg('LASER3_CURRENT_CNTRL_STATE_REGISTER','LASER_CURRENT_CNTRL_DisabledState')
        self.wrDasReg('LASER4_CURRENT_CNTRL_STATE_REGISTER','LASER_CURRENT_CNTRL_DisabledState')
        # Ensure SOA is shorted and turn off laser currents in FPGA
        self.wrFPGA('FPGA_INJECT','INJECT_CONTROL',0)
        # Disable all temperature controllers
        self.wrDasReg('LASER1_TEMP_CNTRL_STATE_REGISTER','TEMP_CNTRL_DisabledState')
        self.wrDasReg('LASER2_TEMP_CNTRL_STATE_REGISTER','TEMP_CNTRL_DisabledState')
        self.wrDasReg('LASER3_TEMP_CNTRL_STATE_REGISTER','TEMP_CNTRL_DisabledState')
        self.wrDasReg('LASER4_TEMP_CNTRL_STATE_REGISTER','TEMP_CNTRL_DisabledState')
        self.wrDasReg('HEATER_TEMP_CNTRL_STATE_REGISTER','TEMP_CNTRL_DisabledState')
        # Disable drive to warm box and hot box TECs
        self.wrDasReg('TEC_CNTRL_REGISTER','TEC_CNTRL_Disabled')
        # Disable proportional valve PWM 
        self.wrFPGA('FPGA_DYNAMICPWM_INLET','DYNAMICPWM_CS',0)
        self.wrFPGA('FPGA_DYNAMICPWM_OUTLET','DYNAMICPWM_CS',0)
        # Turn off voltage to PZT
        self.wrDasReg('ANALYZER_TUNING_MODE_REGISTER','ANALYZER_TUNING_LaserCurrentTuningMode')
        self.wrFPGA('FPGA_TWGEN','TWGEN_PZT_OFFSET',0)
 
class StreamTableType(tables.IsDescription):
    time = tables.Int64Col()
    streamNum = tables.Int32Col()
    value = tables.Float32Col()
    
class StreamSaver(SharedTypes.Singleton):
    initialized = False
    def __init__(self,config=None, basePath=""):
        if not self.initialized:
            self.fileName = ""
            self.table = None
            self.h5 = None
            self.config = config
            self.basePath = basePath
            self.lastWrite = 0
            self.initialized = True
            self.observerAccess = {}

    def registerStreamStatusObserver(self,observerRpcPort,observerToken):
        if not(observerRpcPort in self.observerAccess):
            serverURI = "http://%s:%d" % ("localhost",observerRpcPort)
            proxy = CmdFIFO.CmdFIFOServerProxy(serverURI,
                                               ClientName="StreamStatusNotifier")
        else:
            proxy = self.observerAccess[observerRpcPort][0]
        self.observerAccess[observerRpcPort] = (proxy,observerToken)
        proxy.SetFunctionMode("notify",CmdFIFO.CMD_TYPE_VerifyOnly)

    def unregisterStreamStatusObserver(self,observerRpcPort):
        del self.observerAccess[observerRpcPort]

    def _informObservers(self):
        for o in self.observerAccess:
            proxy,observerToken = self.observerAccess[o]
            proxy.notify(observerToken)

    def openStreamFile(self):
        if self.h5:
            self.closeStreamFile()
        try:
            f = time.strftime(self.config["Files"]["streamFileName"])
        except:
            Log("Config option streamFileName not found in [Files] section. Using default.",Level=2)
            f = time.strftime("Sensors_%Y%m%d_%H%M%S.h5")
        self.fileName = os.path.join(self.basePath,f)
        Log("Opening stream file %s" % self.fileName)
        self.lastWrite = 0
        handle = tables.openFile(self.fileName,mode="w",title="CRDS Sensor Stream File")
        filters = tables.Filters(complevel=1,fletcher32=True)
        self.table = handle.createTable(handle.root,"sensors",StreamTableType,filters=filters)
        if handle:
            self.h5 = handle
        else:
            self.fileName = ""
        self._informObservers()
        return self.fileName

    def closeStreamFile(self):
        if self.h5:
            self.table.flush()
            self.h5.close()
            Log("Closing stream file %s" % self.fileName)
            self.h5, self.fileName = None, ""
        self._informObservers()

    def getStreamFileStatus(self):
        status = "open" if self.h5 else "closed"
        return dict(status=status,filename=self.fileName)

    def _writeData(self,data):
        if self.h5:
            row = self.table.row
            row["time"] = data.timestamp
            row["streamNum"] = data.streamNum
            row["value"] = data.value
            row.append()
            if data.timestamp-self.lastWrite > 5000:
                self.table.flush()
                self.lastWrite = data.timestamp

class Driver(SharedTypes.Singleton):
    def __init__(self,sim,configFile):
        self.config = CustomConfigObj(configFile)
        basePath = os.path.split(configFile)[0]
        self.stateDbFile = os.path.join(basePath, self.config["Files"]["instrStateFileName"])
        self.instrConfigFile = os.path.join(basePath, self.config["Files"]["instrConfigFileName"])
        self.usbFile  = os.path.join(basePath, self.config["Files"]["usbFileName"])
        self.dspFile  = os.path.join(basePath, self.config["Files"]["dspFileName"])
        self.fpgaFile = os.path.join(basePath, self.config["Files"]["fpgaFileName"])
        self.dasInterface = DasInterface(self.stateDbFile,self.usbFile,
                                         self.dspFile,self.fpgaFile,sim)
        self.analogInterface = AnalogInterface(self,self.config)
        # Get appConfig and instrConfig version number
        self.ver = {}
        for ver in ["appVer", "instrVer"]:
            try:
                fPath = os.path.join(basePath, self.config["Files"][ver])
                co = CustomConfigObj(fPath)
                self.ver[ver] = co["Version"]["revno"]
            except Exception, err:
                print err
                self.ver[ver] = "N/A"
        # Get installer ID     
        try:
            signaturePath = os.path.join(basePath, self.config.get("Files", "SignaturePath", "../../../installerSignature.txt"))
        except:
            signaturePath = os.path.join(basePath, "../../../installerSignature.txt")
        try:
            sigFd = open(signaturePath, "r")
            self.installerId = sigFd.readline()
            sigFd.close()
        except Exception, err:
            print "%r" % err
            self.installerId = None
        self.analyzerType = None # Will be retrieved from EEPROM in run() function
        self.validInstallerId = True
            
        self.rpcHandler = DriverRpcHandler(self)
        InstrumentConfig(self.instrConfigFile)
        self.streamSaver = StreamSaver(self.config, basePath)
        self.rpcHandler._register_rpc_functions_for_object(self.streamSaver)
        self.streamCast = Broadcaster(
            port=SharedTypes.BROADCAST_PORT_SENSORSTREAM,
            name="CRDI Stream Broadcaster",logFunc=Log)
        self.resultsCast = Broadcaster(
            port=SharedTypes.BROADCAST_PORT_RDRESULTS,
            name="CRDI RD Results Broadcaster",logFunc=Log)
        self.lastSaveDasState = 0

    def nudgeDasTimestamp(self):
        """Makes incremental change in DAS timestamp to bring it closer to the host timestamp,
        if the two timestamps are within NUDGE_LIMIT. Otherwise the DAS timestamp is set equal
        to that of the host."""
        sender = self.dasInterface.hostToDspSender
        ts = timestamp.getTimestamp()
        sender.doOperation(Operation("ACTION_NUDGE_TIMESTAMP",[ts&0xFFFFFFFF,ts>>32]))
        
    def run(self):
        def messageProcessor(data):
            ts, msg = data
            if len(msg)>2 and msg[1] == ':':
                level = int(msg[0])
                Log("%s" % (msg[2:],),Level=level)
            else:
                Log("%s" % (msg,))
        def sensorProcessor(data):
            self.streamCast.send(StringPickler.ObjAsString(data))
            self.streamSaver._writeData(data)
        def ringdownProcessor(data):
            # TODO: Normalize the data format here
            self.resultsCast.send(StringPickler.ObjAsString(data))
        messageHandler  = SharedTypes.makeHandler(self.dasInterface.getMessage,    messageProcessor)
        sensorHandler   = SharedTypes.makeHandler(self.dasInterface.getSensorData,  sensorProcessor)
        ringdownHandler = SharedTypes.makeHandler(self.dasInterface.getRingdownData,ringdownProcessor)
        try:
            try:
                usbSpeed = self.dasInterface.startUsb()
                Log("USB enumerated at %s speed" % (("full","high")[usbSpeed]))
                self.dasInterface.upload()
                time.sleep(1.0) # For DSP code to initialize
                # Restore state from INI file
                ic = InstrumentConfig()
                ic.loadPersistentRegistersFromConfig()
                # self.dasInterface.loadDasState() # Restore DAS state
                Log("Configuring scheduler",Level=1)
                DasConfigure(self.dasInterface,ic.config).run()                
                try:
                    self.rpcHandler.readWlmDarkCurrents()
                except:
                    Log("Cannot read dark currents from WLM EEPROM",Level=2)                
                daemon = self.rpcHandler.server.daemon
                Log("DAS firmware uploaded",Level=1)
            except:
                # type,value,trace = sys.exc_info()
                Log("Cannot connect to instrument - please check hardware",Verbose=traceback.format_exc(),Level=3)
                raise
            # Initialize the analog interface
            analogInterfacePresent = 0 != (self.dasInterface.hostToDspSender.rdRegUint("HARDWARE_PRESENT_REGISTER") & (1 << interface.HARDWARE_PRESENT_AnalogInterface))
            print "Analog interface present: %s" % analogInterfacePresent
            if analogInterfacePresent: 
                self.analogInterface.initializeClock()
            
            # Compare Analyzer Type from EEPROM with Software Installer ID
            self.validInstallerId = True
            if self.installerId != None:
                try:
                    self.analyzerType = self.rpcHandler.fetchInstrInfo("analyzer")
                except Exception, err:
                    print "%r" % err
                    self.analyzerType = None
                    
                if self.analyzerType != None:
                    if self.installerId != self.analyzerType:
                        Log("EEPROM ID (%s) does not match Software Installer ID (%s) - please correct EEPROM or re-install software" % (self.analyzerType,self.installerId),Level=3)
                        self.validInstallerId = False
                    else:
                        Log("EEPROM ID matches Software Installer ID (%s)" % (self.analyzerType,),Level=1)
            
            # Here follows the main loop.
            Log("Starting main driver loop",Level=1)
            try:
                while not daemon.mustShutdown:
                    startPoll = time.time()
                    timeSoFar = 0
                    timeSoFar += messageHandler.process(0.02)
                    timeSoFar += sensorHandler.process(max(0.02,0.2-timeSoFar))
                    timeSoFar += ringdownHandler.process(max(0.02,0.5-timeSoFar))
                    daemon.handleRequests(0.02)
                    #timeSoFar += messageHandler.process(0.01)
                    #timeSoFar += sensorHandler.process(max(0.01,0.04-timeSoFar))
                    #timeSoFar += ringdownHandler.process(max(0.01,0.1-timeSoFar))
                    #daemon.handleRequests(max(0.005,0.1-timeSoFar))
                    # Periodically save the state of the DAS and nudge the DAS timestamp
                    if analogInterfacePresent: 
                        self.analogInterface.serve()
                    now = time.time()
                    #print "Poll Time", now-startPoll
                    if now > self.lastSaveDasState + 30.0:
                        self.nudgeDasTimestamp()
                        self.dasInterface.saveDasState()
                        self.lastSaveDasState = now
                Log("Driver RPC handler shut down")
            except:
                type,value,trace = sys.exc_info()
                Log("Unhandled Exception in main loop: %s: %s" % (str(type),str(value)),
                    Verbose=traceback.format_exc(),Level=3)
        finally:
            try:
                self.dasInterface.saveDasState()
            except:
                pass
            self.dasInterface.analyzerUsb.disconnect()
            self.rpcHandler.shutDown()
                
        
class InstrumentConfig(SharedTypes.Singleton):
    """Configuration of instrument."""
    def __init__(self,filename=None):
        if filename is not None:
            self.config = CustomConfigObj(filename)
            self.filename = filename

    def reloadFile(self):
        self.config = CustomConfigObj(self.filename)

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
            fp.close
        return filename

HELP_STRING = """Driver.py [-s|--simulation] [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-s, --simulation     run in simulation mode
-c                   specify a config file:  default = "./Driver.ini"
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hsc:'
    longOpts = ["help", "simulation"]
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
    configFile = os.path.dirname(AppPath) + "/Driver.ini"
    simulation = False
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    if "-s" in options or "--simulation" in options:
        simulation = True
    return (simulation, configFile)

if __name__ == "__main__":
    driverApp = SingleInstance("PicarroDriver")
    if driverApp.alreadyrunning():
        Log("Instance of driver us already running",Level=3)
    else:
        sim, configFile = handleCommandSwitches()
        Log("%s started." % APP_NAME, dict(Sim = sim, ConfigFile = configFile), Level = 0)
        d = Driver(sim,configFile)
        d.run()
    Log("Exiting program")
    time.sleep(1)
