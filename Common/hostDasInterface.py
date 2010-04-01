#!/usr/bin/python
#
# FILE:
#   hostDasInterface.py
#
# DESCRIPTION:
#   Code which communicates between the Host and the DAS
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   22-December-2008  sze  Initial version.
#
#  Copyright (c) 2008 Picarro, Inc. All rights reserved
#
import sys
import logging
import thread
import threading
import time
from ctypes import addressof
from ctypes import c_char, c_byte, c_float, c_int, c_longlong
from ctypes import c_short, c_uint, c_ushort, sizeof, Structure
from configobj import ConfigObj
from time import sleep, clock
from numpy import *
import sqlite3
import Queue
import copy

from Host.autogen import usbdefs, interface
from Host.Common.crc import calcCrc32
from Host.Common.SharedTypes    import Singleton, getSchemeTableClass, DasCommsException
from Host.Common.simulatorUsbIf import SimulatorUsb
from Host.Common.DspSimulator   import DspSimulator
from Host.Common.analyzerUsbIf  import AnalyzerUsb

# The 6713 has 192KB of internal memory from 0 through 0x2FFFF
#  With the allocation below, the register area contains 16128 4-byte
#   registers. The host area occupies the top 1KB of internal memory

SHAREDMEM_BASE   = interface.SHAREDMEM_ADDRESS
REG_BASE         = interface.SHAREDMEM_ADDRESS
SENSOR_BASE      = interface.SHAREDMEM_ADDRESS + \
                       4*interface.SENSOR_OFFSET
MESSAGE_BASE     = interface.SHAREDMEM_ADDRESS + \
                       4*interface.MESSAGE_OFFSET
GROUP_BASE       = interface.SHAREDMEM_ADDRESS + \
                       4*interface.GROUP_OFFSET
OPERATION_BASE   = interface.SHAREDMEM_ADDRESS + \
                       4*interface.OPERATION_OFFSET
OPERAND_BASE     = interface.SHAREDMEM_ADDRESS + \
                       4*interface.OPERAND_OFFSET
ENVIRONMENT_BASE = interface.SHAREDMEM_ADDRESS + \
                       4*interface.ENVIRONMENT_OFFSET
HOST_BASE        = interface.SHAREDMEM_ADDRESS + \
                       4*interface.HOST_OFFSET
RINGDOWN_BASE    = interface.DSP_DATA_ADDRESS

ValveSequenceType = (interface.ValveSequenceEntryType * interface.NUM_VALVE_SEQUENCE_ENTRIES)

class Operation(object):
    def __init__(self,opcode,operandList=[],env=0):
        self.opcode = lookup(opcode)
        self.env = lookup(env)
        self.operandList = [lookup(opr) for opr in operandList]

class OperationGroup(object):
    def __init__(self,priority,period,operationList=None):
        if priority<0 or priority>=16:
            raise ValueError,"Priority out of range (0-15)"
        if period<0 or period>=4096:
            raise ValueError,"Period out of range (0-4095)"
        self.priority = priority
        self.period = period
        if operationList == None:
            self.operationList = []
        else:
            self.operationList = operationList
    def addOperation(self,operation):
        self.operationList.append(operation)
    def  __len__(self):
        return len(self.operationList)

class DasInterface(Singleton):
    initialized = False
    def __init__(self,stateDbFile=None,usbFile=None,dspFile=None,
                    fpgaFile=None,simulate=True):
        if not self.initialized:
            self.stateDatabase = StateDatabase(stateDbFile)
            self.sensorHistory = SensorHistory()
            self.usbFile = usbFile
            self.dspFile = dspFile
            self.fpgaFile = fpgaFile
            self.analyzerUsb = None
            self.hostToDspSender = None
            self.stateDb = None
            self.simulate = simulate
            self.lastMessageTime = 0
            self.lastSensorTime = 0
            self.lastRingdownTime = 0
            self.messageIndex = 0
            self.sensorIndex = 0
            self.ringdownIndex = 0
            self.initialized = True
        elif stateDbFile is not None:
            raise ValueError("DasInterface has already been initialized")
    def loadUsbIfCode(self,usbCodeFilename):
        """Downloads file to USB Cypress FX2 chip,
        if not already downloaded"""
        analyzerUsb = AnalyzerUsb(usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        try: # connecting to a programmed Picarro instrument
            analyzerUsb.connect()
            analyzerUsb.disconnect()
            return
        except:
            try: # connecting to an unprogrammed Picarro instrument
                analyzerUsb = AnalyzerUsb(usbdefs.INITIAL_VID,usbdefs.INITIAL_PID)
                analyzerUsb.connect()
            except:
                try: # connecting to a blank Cypress FX2
                    analyzerUsb = AnalyzerUsb(usbdefs.CYPRESS_FX2_VID,usbdefs.CYPRESS_FX2_PID)
                    analyzerUsb.connect()
                except:
                    raise "Cannot connect to USB"
        logging.info("Downloading USB code to Picarro USB device")
        analyzerUsb.loadHexFile(file(usbCodeFilename,"r"))
        analyzerUsb.disconnect()
        # Wait for renumeration
        while True:
            analyzerUsb = AnalyzerUsb(
                usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
            try:
                analyzerUsb.connect()
                break
            except:
                sleep(1.0)
        analyzerUsb.disconnect()
    def programFPGA(self,fileName):
        logging.info(
            "USB high-speed mode: %d" % (self.analyzerUsb.getUsbSpeed(),))
        self.analyzerUsb.startFpgaProgram()
        logging.info("Fpga status: %d" % self.analyzerUsb.getFpgaStatus())
        while 0 == (1 & self.analyzerUsb.getFpgaStatus()):
            pass
        fp = file(fileName,"rb")
        s = fp.read(128)
        f = s.find("\xff\xff\xff\xff\xaa\x99\x55\x66")
        if f<0:
            raise ValueError("Invalid FPGA bit file")
        s = s[f:]
        tStart = clock()
        lTot = 0
        while len(s)>0:
            lTot += len(s)
            self.analyzerUsb.sendToFpga(s)
            s = fp.read(64)
        stat = self.analyzerUsb.getFpgaStatus()
        if 0 != (2 & self.analyzerUsb.getFpgaStatus()):
            logging.info("FPGA programming done")
            logging.info("Bytes sent: %d" % lTot)
        elif 0 == (1 & self.analyzerUsb.getFpgaStatus()):
            logging.error(
                "CRC error during FPGA load, bytes sent: %d" % (lTot,))
        logging.info("Time to load: %.1fs" % (clock() - tStart,))
        sleep(0.2)
    def initEmif(self):
        """Initializes EMIF on DSP using HPI interface"""
        EMIF_GCTL      = 0x01800000
        EMIF_CE1       = 0x01800004
        EMIF_CE0       = 0x01800008
        EMIF_CE2       = 0x01800010
        EMIF_CE3       = 0x01800014
        EMIF_SDRAMCTL  = 0x01800018
        EMIF_SDRAMTIM  = 0x0180001C
        EMIF_SDRAMEXT  = 0x01800020
        EMIF_CCFG      = 0x01840000     # Cache configuration register
        CHIP_DEVCFG    = 0x019C0200     # Chip configuration register

        def writeMem(addr,value):
            self.analyzerUsb.hpiaWrite(addr)
            self.analyzerUsb.hpidWrite(c_int(value))
        self.analyzerUsb.hpicWrite(0x00010001)
        writeMem(EMIF_GCTL,0x00000068)
        writeMem(EMIF_CE0,0xffffbf33)      # CE0 SDRAM
        writeMem(EMIF_CE1,0x02208802)      # CE1 Flash 8-bit
        writeMem(EMIF_CE2,0x22a28a22)      # CE2 Daughtercard 32-bit async
        writeMem(EMIF_CE3,0x22a28a22)      # CE3 Daughtercard 32-bit async
        writeMem(EMIF_SDRAMCTL,0x57115000) # SDRAM control (16 Mb)
        writeMem(EMIF_SDRAMTIM,0x00000578) # SDRAM timing (refresh)
        writeMem(EMIF_SDRAMEXT,0x000a8529) # SDRAM Extension register
        writeMem(CHIP_DEVCFG,0x13)         # Chip configuration register

    def initPll(self):
        PLL_BASE_ADDR   = 0x01b7c000
        PLL_PID         = ( PLL_BASE_ADDR + 0x000 )
        PLL_CSR         = ( PLL_BASE_ADDR + 0x100 )
        PLL_MULT        = ( PLL_BASE_ADDR + 0x110 )
        PLL_DIV0        = ( PLL_BASE_ADDR + 0x114 )
        PLL_DIV1        = ( PLL_BASE_ADDR + 0x118 )
        PLL_DIV2        = ( PLL_BASE_ADDR + 0x11C )
        PLL_DIV3        = ( PLL_BASE_ADDR + 0x120 )
        PLL_OSCDIV1     = ( PLL_BASE_ADDR + 0x124 )

        CSR_PLLEN       =   0x00000001
        CSR_PLLPWRDN    =   0x00000002
        CSR_PLLRST      =   0x00000008
        CSR_PLLSTABLE   =   0x00000040
        DIV_ENABLE      =   0x00008000
        def writeMem(addr,value):
            self.analyzerUsb.hpiWrite(addr,c_int(value))
        def readMem(addr):
            result = c_int(0)
            self.analyzerUsb.hpiRead(addr,c_int(0))
            return result.value

        self.analyzerUsb.hpicWrite(0x00010001)
        # When PLLEN is off DSP is running with CLKIN clock
        #   source, currently 50MHz or 20ns clk rate.
        writeMem(PLL_CSR,readMem(PLL_CSR) &~CSR_PLLEN)

        # Reset the pll.  PLL takes 125ns to reset.
        writeMem(PLL_CSR,readMem(PLL_CSR) | CSR_PLLRST)

        # PLLOUT = CLKIN/(DIV0+1) * PLLM
        # 450    = 50/1 * 9

        writeMem(PLL_DIV0,DIV_ENABLE + 0)
        writeMem(PLL_MULT,9)
        writeMem(PLL_OSCDIV1,DIV_ENABLE + 4)

        # Program in reverse order.
        # DSP requires that pheripheral clocks be less then
        # 1/2 the CPU clock at all times.

        writeMem(PLL_DIV3,DIV_ENABLE + 4)
        writeMem(PLL_DIV2,DIV_ENABLE + 3)
        writeMem(PLL_DIV1,DIV_ENABLE + 1)
        writeMem(PLL_CSR,readMem(PLL_CSR) & ~CSR_PLLRST)

        # Now enable pll path and we are off and running at
        # 225MHz with 90 MHz SDRAM.
        writeMem(PLL_CSR,readMem(PLL_CSR) | CSR_PLLEN)

    def startUsb(self):
        if self.simulate:
            self.analyzerUsb = SimulatorUsb(
                usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
            self.analyzerUsb.setSimulator(
                DspSimulator(SHAREDMEM_BASE,HOST_BASE))
        else:
            self.loadUsbIfCode(self.usbFile)
            self.analyzerUsb = AnalyzerUsb(
                usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        #
        self.analyzerUsb.connect()
        return self.analyzerUsb.getUsbSpeed()

    def upload(self):
        # TODO: Handle errors by returning an error code.
        #  If this routine fails, it is not possible
        #  to continue
        #
        logging.info("Holding DSP in reset...")
        self.analyzerUsb.setDspControl(usbdefs.VENDOR_DSP_CONTROL_RESET)
        #raw_input("Press <Enter> to program FPGA")
        if not self.simulate:
            logging.info("Starting to program FPGA...")
            self.programFPGA(self.fpgaFile)
        self.analyzerUsb.setDspControl(0)
        sleep(0.5)
        logging.info("Removed DSP reset, downloading code...")
        self.initPll()
        self.initEmif()
        #raw_input("Press <Enter> to download DSP code")
        fp = file(self.dspFile,"rb")
        self.analyzerUsb.loadDspFile(fp)
        fp.close()
        self.analyzerUsb.hpicWrite(0x00010001)
        #raw_input("DSP code downloaded. Press <Enter> to send DSPINT")
        self.analyzerUsb.hpicWrite(0x00010003)
        # print "hpic after DSPINT: %08x" % self.analyzerUsb.hpicRead()
        time.sleep(0.5)
        logging.info("Starting DSP code...")
        #raw_input("DSPINT sent. Press <Enter> to continue")
        self.analyzerUsb.hpicWrite(0x00010001)
        #
        self.hostToDspSender = HostToDspSender(self.analyzerUsb,5.0)
    def getMessages(self):
        """Generator which retrieves messages from the analyzer"""
        while True:
            ts = self.hostToDspSender.rdMessageTimestamp(
                  self.messageIndex)
            if ts!=0 and ts>=self.lastMessageTime:
                msg = self.hostToDspSender.rdMessage(self.messageIndex)
                self.lastMessageTime = ts
                self.messageIndex += 1
                if self.messageIndex >= interface.NUM_MESSAGES:
                    self.messageIndex = 0
                yield ts,msg
            else:
                break
    def getSensorData(self):
        """Generator which retrieves sensor data from the analyzer"""
        while True:
            data = self.hostToDspSender.rdSensorData(self.sensorIndex)
            if data.timestamp!=0 and data.timestamp>=self.lastSensorTime:
                self.lastSensorTime = data.timestamp
                self.sensorIndex += 1
                if self.sensorIndex >= interface.NUM_SENSOR_ENTRIES:
                    self.sensorIndex = 0
                self.sensorHistory.record(data)
                yield data
            else:
                break
    def getRingdownData(self):
        """Generator which retrieves sensor data from the analyzer"""
        while True:
            data = self.hostToDspSender.rdRingdownData(
                  self.ringdownIndex)
            if data.timestamp!=0 and data.timestamp>=self.lastRingdownTime:
                self.lastRingdownTime = data.timestamp
                self.ringdownIndex += 1
                if self.ringdownIndex >= interface.NUM_RINGDOWN_ENTRIES:
                    self.ringdownIndex = 0
                yield data
            else:
                break
    def uploadSchedule(self,operationGroups):
        """Upload all operation groups to the instrument"""
        def shorts2int(x,y):
            return int(((y<<16) | x) & 0xFFFFFFFF)
        groupTable = []
        operationTable = []
        operandTable = []
        for g in operationGroups:
            operationAddress = len(operationTable)
            priority_and_period = (g.priority<<12) + g.period
            groupTable.append(
                shorts2int(priority_and_period,operationAddress))
            for op in g.operationList:
                operandAddress = len(operandTable)
                operationTable.append(
                    (shorts2int(op.opcode,len(op.operandList)),
                    shorts2int(operandAddress,op.env))
                )
                for opr in op.operandList:
                    operandTable.append(int(opr))
            operationTable.append((0,0))
        groupTable.append(0)
        if len(groupTable) > interface.GROUP_TABLE_SIZE:
            raise ValueError(
                "%d operation groups needed, only %d available" % \
                (len(groupTable),interface.GROUP_TABLE_SIZE))
        if len(operationTable) > interface.NUM_OPERATIONS:
            raise ValueError(
                "%d operations needed, only %d available" % \
                (len(operationTable),interface.OPERATION_TABLE_SIZE))
        if len(operandTable) > interface.OPERAND_TABLE_SIZE:
            raise ValueError(
                "%d operands needed, only %d available" % \
                (len(operandTable),interface.OPERAND_TABLE_SIZE))
        self.hostToDspSender.wrBlock(interface.GROUP_OFFSET,
                                     *groupTable)
        # Flatten the tuples in the operation table to send it to the
        #  analyzer
        flatOperations = []
        for op in operationTable: flatOperations += op
        self.hostToDspSender.wrBlock(interface.OPERATION_OFFSET,
                                     *flatOperations)
        self.hostToDspSender.wrBlock(interface.OPERAND_OFFSET,
                                     *operandTable)
    def getSchedule(self):
        """Returns the group, operation and operand tables, mainly for
        diagnostic purposes"""
        return dict(
            groupTable=self.hostToDspSender.rdBlock(
                interface.GROUP_OFFSET,interface.GROUP_TABLE_SIZE),
            operationTable=self.hostToDspSender.rdBlock(
                interface.OPERATION_OFFSET,
                interface.OPERATION_TABLE_SIZE),
            operandTable=self.hostToDspSender.rdBlock(
                interface.OPERAND_OFFSET,interface.OPERAND_TABLE_SIZE))
    def saveDasState(self):
        """Write out all register contents to an SQLite database"""
        floatRegList = []
        intRegList = []
        for ri in interface.registerInfo:
            if ri.type == c_float:
                floatRegList.append((ri.name,
                    self.hostToDspSender.rdRegFloat(ri.name)))
            else:
                value = self.hostToDspSender.rdRegUint(ri.name)
                if ri.type == c_int:
                    if value >= 1<<31: value -= 1<<32
                intRegList.append((ri.name,value))
        self.stateDatabase.saveFloatRegList(floatRegList)
        self.stateDatabase.saveIntRegList(intRegList)
    def loadDasState(self):
        """Read in all register contents from an SQLite database"""
        return
        floatRegList = self.stateDatabase.getFloatRegList()
        intRegList = self.stateDatabase.getIntRegList()
        for name,value in floatRegList:
            try:
                regNum = interface.registerByName[name]
                if interface.registerInfo[regNum].writable:
                    self.hostToDspSender.wrRegFloat(name,value)
            except:
                print "Register %s in database is unrecognized" % name
        for name,value in intRegList:
            try:
                regNum = interface.registerByName[name]
                if interface.registerInfo[regNum].writable:
                    self.hostToDspSender.wrRegUint(name,value)
            except:
                print "Register %s in database is unrecognized" % name

def lookup(sym):
    if isinstance(sym,(str,unicode)): sym = getattr(interface,sym)
    return sym
def usbLockProtect(f):
    # Decorator for serializing access to the method f from different
    #  threads by using the usbLock
    def wrapper(self,*a,**k):
        self.usbLock.acquire()
        try:
            return f(self,*a,**k)
        finally:
            self.usbLock.release()
    return wrapper

class HostToDspSender(Singleton):
    initialized = False
    # Object that keeps track of sequence numbers, and packages
    #  data for host to Dsp communications
    def __init__(self,analyserUsb=None,timeout=None):
        if not self.initialized:
            self.seqNum = None
            self.usb = analyserUsb
            # Used to ensure only one thread accesses USB at a time
            self.usbLock = threading.RLock()
            self.initStatus = None
            self.timeout = timeout
            self.initialized = True
    def setTimeout(self,timeout=None):
        self.timeout = timeout
    @usbLockProtect
    def send(self,command,data,env=0):
        # Send the command and the associated data to the DSP. Data is an
        #  enumerable object whose elements are either integers or floats.
        #  This function adds a sequence number and CRC32 checksum before
        #  sending it. It then issues a DSPINT call.
        # Format of message:
        # HOST[0]: Command in bits 15-0, len(data) in bits 23-16,
        #          SeqNum in bits 31-24
        # HOST[1]: Environment address in bits 15-0
        # HOST[2] through HOST[len(data)+1]: Data (int or float)
        # HOST[len(data)+2]: CRC32

        # The total host area is 1KB in size
        #while True:
        #    self.initStatus = self.rdRegUint(interface.COMM_STATUS_REGISTER)
        #    if 0 != self.initStatus & interface.COMM_STATUS_CompleteMask:
        #        break
        #    print "Waiting for COMM_STATUS complete before USB communication"
        #    time.sleep(0.1)            
        self.initStatus = self.rdRegUint(interface.COMM_STATUS_REGISTER)
        if self.seqNum == None:
            self.seqNum = (self.getSequenceNumber() + 1) & 0xFF
        numInt = len(data)
        hostMsg = ((numInt+3)*c_uint)()
        hostMsg[0] = ((self.seqNum&0xFF) << 24) | \
            ((numInt&0xFF) << 16) | (command&0xFFFF)
        hostMsg[1] = env & 0xFFFF
        i = 2
        for d in data:
            if isinstance(d,int) or isinstance(d,long):
                hostMsg[i] = c_uint(d & 0xFFFFFFFF)
            elif isinstance(d,float):
                f = c_float(d)
                hostMsg[i] = c_uint.from_address(addressof(f))
            else:
                raise ValueError("Data type %s is unknown in send" % type(d))
            i += 1
        hostMsg[i] = calcCrc32(0,hostMsg,4*(numInt+2))
        # logging.info("CRC = %x" % hostMsg[numInt+2])
        self.usb.hpiWrite(HOST_BASE,hostMsg)
        sleep(0.003) # Necessary to ensure hpiWrite completes before signalling interrupt
        # Assert DSPINT
        self.usb.hpicWrite(0x00010003)
        # print "hpic after DSPINT: %08x" % self.usb.hpicRead()
        return self.getStatusWhenDone() # or throw SharedTypes.DasCommsException on error
    @usbLockProtect
    def getSequenceNumber(self):
        # Get the sequence number from the COMM_STATUS_REGISTER
        ntries = 0
        retVal = 0
        startTime = clock()
        while self.timeout==None or clock()<startTime+self.timeout:
            self.status = self.rdRegUint(interface.COMM_STATUS_REGISTER)
            ntries += 1
            done = (0 != (self.status & \
                interface.COMM_STATUS_CompleteMask))
            if done:
                seqNum = (self.status & \
                    interface.COMM_STATUS_SequenceNumberMask)>> \
                    interface.COMM_STATUS_SequenceNumberShift
                if self.seqNum==None or self.seqNum==seqNum:
                    #self.seqNum = seqNum
                    return seqNum
            # If not done, sleep and try again
            sleep(0.1)
            now = clock()
        seqNum = self.seqNum
        self.seqNum = None
        raise RuntimeError,("Timeout getting status after %s tries." +
            "Initial status: 0x%x, Final status: 0x%x," +
            "Expected sequence number: %s") % \
            (ntries,self.initStatus,self.status,seqNum)
    @usbLockProtect
    def getStatusWhenDone(self):
        # Read done bit from COMM_STATUS_REGISTER
        seqNum = self.getSequenceNumber()
        try:
            if 0 != (self.status & interface.COMM_STATUS_BadCrcMask):
                raise DasCommsException("Bad CRC detected")
            if 0 != (self.status & \
                    interface.COMM_STATUS_BadSequenceNumberMask):
                raise DasCommsException("DSP unexpected sequence number: %d, %d" % (seqNum,self.seqNum))
            if seqNum != self.seqNum:
                raise DasCommsException("Host unexpected sequence number: %d, %d" % (seqNum,self.seqNum))
            retVal = (
                self.status & interface.COMM_STATUS_ReturnValueMask)>> \
                    interface.COMM_STATUS_ReturnValueShift
            retVal = c_short(retVal).value # Sign extend 16-bits
            return retVal
        finally:
            # Prepare for next send
            self.seqNum = (seqNum + 1) & 0xFF
    @usbLockProtect
    def wrBlock(self,*args):
        argList = []
        for a in args:
            argList.append(lookup(a))
        return self.send(interface.ACTION_WRITE_BLOCK,argList)
    def wrRegFloat(self,reg,value):
        return self.wrBlock(reg,float(value))
    def wrRegUint(self,reg,value):
        return self.wrBlock(reg,int(value))
    def wrEnv(self,index,env):
        # Write the environment structure env to the environment
        #  table at the specified index (integer offset)
        numInt =sizeof(env)/sizeof(c_uint)
        envAsArray = (c_uint*numInt).from_address(addressof(env))
        return self.wrBlock(interface.ENVIRONMENT_OFFSET+lookup(index),*envAsArray)
    @usbLockProtect
    def rdBlock(self,offset,numInt):
        # Performs a host read of numInt unsigned integers from
        #  the communications region starting at offset
        addr = SHAREDMEM_BASE+4*lookup(offset)
        result = (c_uint*numInt)()
        self.usb.hpiRead(addr,result)
        return list(result)
    
    @usbLockProtect
    def rdRegFloat(self,reg):
        # Performs a host read of a single floating point number
        #  from the software register "reg" which may be specified
        #  as an integer or a string (defined in the interface module).
        data = c_float(0)
        self.usb.hpiRead(REG_BASE+4*lookup(reg),data)
        return data.value
    @usbLockProtect
    def rdRegUint(self,reg):
        # Performs a host read of a single unsigned integer from
        #  the software register "reg" which may be specified as
        #  an integer or a string (defined in the interface module).
        data = c_uint(0)
        self.usb.hpiRead(REG_BASE+4*lookup(reg),data)
        return data.value
    @usbLockProtect
    def rdFPGA(self,base,reg):
        # Performs a host read of a single unsigned integer from
        #  the FPGA register which may be specified as
        #  the sum of a block base and the register index
        data = c_uint(0)
        self.usb.hpiRead(interface.FPGA_REG_BASE_ADDRESS+4*(lookup(base)+lookup(reg)),data)
        return data.value
    @usbLockProtect
    def wrFPGA(self,base,reg,value):
        # Performs a host write of a single unsigned integer from
        #  the FPGA register which may be specified as
        #  the sum of a block base and the register index
        self.usb.hpiWrite(interface.FPGA_REG_BASE_ADDRESS+4*(lookup(base)+lookup(reg)),c_uint(value))
    @usbLockProtect
    def rdDspMemArray(self,byteAddr,nwords=1):
        """Reads multiple words from DSP memory into a c_uint array"""
        result = (c_uint*nwords)()
        self.usb.hpiRead(byteAddr,result)
        return result
    @usbLockProtect
    def rdRingdownMemArray(self,offset,nwords=1):
        """Reads multiple words from ringdown memory into a c_uint array"""
        result = (c_uint*nwords)()
        self.usb.hpiRead(interface.RDMEM_ADDRESS+4*offset,result)
        return result
    @usbLockProtect
    def rdRingdownMem(self,offset):
        """Reads single uint from ringdown memory"""
        result = c_uint(0)
        self.usb.hpiRead(interface.RDMEM_ADDRESS+4*offset,result)
        return result.value
    @usbLockProtect
    def wrRingdownMem(self,offset,value):
        """Reads single uint value to ringdown memory"""
        result = c_uint(value)
        self.usb.hpiWrite(interface.RDMEM_ADDRESS+4*offset,result)
    @usbLockProtect
    def rdSensorData(self,index):
        # Performs a host read of the data in the specified sensor stream
        #  entry. Note that the index is the entry number, and each entry
        #  is of size 16 bytes (64 bit timestamp, 32 bit stream index
        #  and 32 bit data)
        data = interface.SensorEntryType()
        self.usb.hpiRead(SENSOR_BASE + 16*index,data)
        return data
    @usbLockProtect
    def rdRingdownData(self,index):
        # Performs a host read of the data in the specified ringdown
        #  entry. Note that the index is the entry number, and each entry
        #  is of size 4*RINGDOWN_ENTRY_SIZE bytes
        data = interface.RingdownEntryType()
        self.usb.hpiRead(RINGDOWN_BASE + 4*interface.RINGDOWN_ENTRY_SIZE*index,data)
        return data
    @usbLockProtect
    def rdMessageTimestamp(self,index):
        # Performs a host read of the timestamp associated with
        #  the specified message
        data = c_longlong(0)
        self.usb.hpiRead(MESSAGE_BASE + 128*index,data)
        return data.value
    @usbLockProtect
    def rdMessage(self,index):
        # Performs a host read of the specified message
        data = (c_char*120)()
        self.usb.hpiRead(MESSAGE_BASE + 128*index + 8,data)
        return data.value
    @usbLockProtect
    def rdEnv(self,index,envClass):
        # reads an environment at the specified index into an object 
        #  of type envClass
        env = envClass()
        self.usb.hpiRead(ENVIRONMENT_BASE+4*lookup(index),env)
        return env
    @usbLockProtect
    def doOperation(self,op):
        return self.send(op.opcode,op.operandList,op.env)
    @usbLockProtect
    def wrScheme(self,schemeNum,numRepeats,schemeRows):
        # Write schemeRows into scheme table schemeNum. For speed, this is done
        #  directly via the HPI interface into DSP memory rather than through
        #  the host area. We need to declare the scheme areas as volatile in the 
        #  DSP code so that they are always read from memory.
        SCHEME_BASE = interface.DSP_DATA_ADDRESS + 4*interface.SCHEME_OFFSET
        if schemeNum >= interface.NUM_SCHEME_TABLES:
            raise ValueError("Maximum number of schemes available is %d" % interface.NUM_SCHEME_TABLES)
        
        schemeTableAddr = SCHEME_BASE + 4*schemeNum*interface.SCHEME_TABLE_SIZE
        self.doOperation(Operation("ACTION_WB_INV_CACHE",[schemeTableAddr,4*interface.SCHEME_TABLE_SIZE]))
        schemeTable = getSchemeTableClass(len(schemeRows))()
        schemeTable.numRepeats = numRepeats
        schemeTable.numRows = len(schemeRows)
        for i,row in enumerate(schemeRows):
            schemeTable.rows[i].setpoint = float(row[0])
            schemeTable.rows[i].dwellCount = int(row[1])
            schemeTable.rows[i].subschemeId = int(row[2])    if len(row)>=3 else 0
            schemeTable.rows[i].virtualLaser = int(row[3])   if len(row)>=4 else 0
            schemeTable.rows[i].threshold = int(row[4])      if len(row)>=5 else 0
            schemeTable.rows[i].pztSetpoint = int(row[5])    if len(row)>=6 else 0
            schemeTable.rows[i].laserTemp = int(1000*row[6]) if len(row)>=7 else 0
        self.usb.hpiWrite(schemeTableAddr,schemeTable)

    @usbLockProtect
    def rdScheme(self,schemeNum):
        # Read from scheme table schemeNum
        SCHEME_BASE = interface.DSP_DATA_ADDRESS + 4*interface.SCHEME_OFFSET
        if schemeNum >= interface.NUM_SCHEME_TABLES:
            raise ValueError("Maximum number of schemes available is %d" % interface.NUM_SCHEME_TABLES)
        
        schemeTableAddr = SCHEME_BASE + 4*schemeNum*interface.SCHEME_TABLE_SIZE
        self.doOperation(Operation("ACTION_WB_CACHE",[schemeTableAddr,4*interface.SCHEME_TABLE_SIZE]))
        schemeHeader = interface.SchemeTableHeaderType()
        self.usb.hpiRead(schemeTableAddr,schemeHeader)
        schemeTable = getSchemeTableClass(schemeHeader.numRows)()
        self.usb.hpiRead(schemeTableAddr,schemeTable)
        return {"numRepeats":schemeTable.numRepeats,
                "schemeRows":[(row.setpoint,row.dwellCount,row.subschemeId,row.virtualLaser, \
                               row.threshold,row.pztSetpoint,0.001*row.laserTemp) for row in schemeTable.rows]}

    @usbLockProtect
    def wrSchemeSequence(self,schemeIndices,restartFlag=0,loopFlag=1):
        # Write scheme sequence
        SCHEME_SEQUENCE_BASE = interface.SHAREDMEM_ADDRESS + 4*interface.SCHEME_SEQUENCE_OFFSET
        schemeSequence = interface.SchemeSequenceType()
        maxIndex = sizeof(schemeSequence.schemeIndices)/sizeof(c_ushort)
        # Get the current scheme sequence information
        self.usb.hpiRead(SCHEME_SEQUENCE_BASE,schemeSequence)
        # Modify the structure using the input arguments
        if len(schemeIndices) > maxIndex:
            raise ValueError,"Scheme sequence is too long"
        schemeSequence.loopFlag = loopFlag
        schemeSequence.restartFlag = restartFlag
        # Restart by setting current index to zero, otherwise retain current value
        if restartFlag: schemeSequence.currentIndex = 0
        schemeSequence.numberOfIndices = len(schemeIndices)
        for i,s in enumerate(schemeIndices):
            schemeSequence.schemeIndices[i] = s
        i += 1
        while i < maxIndex:
            schemeSequence.schemeIndices[i] = 0
            i += 1
        self.usb.hpiWrite(SCHEME_SEQUENCE_BASE,schemeSequence)
    
    @usbLockProtect
    def rdSchemeSequence(self):
        SCHEME_SEQUENCE_BASE = interface.SHAREDMEM_ADDRESS + 4*interface.SCHEME_SEQUENCE_OFFSET
        schemeSequence = interface.SchemeSequenceType()
        self.usb.hpiRead(SCHEME_SEQUENCE_BASE,schemeSequence)
        return {"schemeIndices":schemeSequence.schemeIndices[:schemeSequence.numberOfIndices],
                "loopFlag":schemeSequence.loopFlag,"currentIndex":schemeSequence.currentIndex}

    @usbLockProtect
    def wrValveSequence(self,sequenceRows):
        # Write the valve sequence - sequenceRows is a list of triples (mask,value,duration)
        #  where mask and value are each 8 bits wide and duration is 16 bits wide
        VALVE_SEQUENCE_BASE = interface.SHAREDMEM_ADDRESS + 4*interface.VALVE_SEQUENCE_OFFSET
        valveSequence = (ValveSequenceType)()
        if len(sequenceRows) > interface.NUM_VALVE_SEQUENCE_ENTRIES:
            raise ValueError,"Maximum number of rows in a valve sequence is %d" % interface.NUM_VALVE_SEQUENCE_ENTRIES
        for i,(mask,value,dwell) in enumerate(sequenceRows):
            if mask<0 or mask>0xFF:
                raise ValueError,"Mask in valve sequence is eight bits wide"
            if value<0 or value>0xFF:
                raise ValueError,"Value in valve sequence is eight bits wide"
            if dwell<0 or dwell>0xFFFF:
                raise ValueError,"Dwell in valve sequence is sixteen bits wide"
            valveSequence[i].maskAndValue = (mask << 8) | (value & 0xFF)
            valveSequence[i].dwell = dwell
        self.usb.hpiWrite(VALVE_SEQUENCE_BASE,valveSequence)
    
    @usbLockProtect
    def rdValveSequence(self):
        # Reads the valve sequence as a list of triples (mask,value,duration)
        VALVE_SEQUENCE_BASE = interface.SHAREDMEM_ADDRESS + 4*interface.VALVE_SEQUENCE_OFFSET
        valveSequence = (ValveSequenceType)()
        self.usb.hpiRead(VALVE_SEQUENCE_BASE,valveSequence)
        sequenceRows = []
        for i in range(interface.NUM_VALVE_SEQUENCE_ENTRIES):
            entry = valveSequence[i]
            sequenceRows.append(((entry.maskAndValue >> 8)&0xFF,entry.maskAndValue & 0xFF,entry.dwell))
        return sequenceRows
    
    @usbLockProtect
    def wrVirtualLaserParams(self,vLaserNum,vLaserParams):
        # Write virtual laser parameters for vLaserNum (ONE-based index)
        VIRTUAL_LASER_PARAMS_BASE = interface.DSP_DATA_ADDRESS + 4*interface.VIRTUAL_LASER_PARAMS_OFFSET
        if vLaserNum > interface.NUM_VIRTUAL_LASERS:
            raise ValueError("Maximum number of virtual lasers available is %d" % interface.NUM_VIRTUAL_LASERS)
        if not isinstance(vLaserParams,interface.VirtualLaserParamsType):
            raise ValueError("Invalid object to write in wrVirtualLaserParams")
        virtualLaserParamsAddr = VIRTUAL_LASER_PARAMS_BASE + 4*(vLaserNum-1)*interface.VIRTUAL_LASER_PARAMS_SIZE
        self.doOperation(Operation("ACTION_WB_INV_CACHE",[virtualLaserParamsAddr,4*interface.VIRTUAL_LASER_PARAMS_SIZE]))
        self.usb.hpiWrite(virtualLaserParamsAddr,vLaserParams)

    @usbLockProtect
    def rdVirtualLaserParams(self,vLaserNum):
        # Read virtual laser parameters for vLaserNum (ONE-based index)
        VIRTUAL_LASER_PARAMS_BASE = interface.DSP_DATA_ADDRESS + 4*interface.VIRTUAL_LASER_PARAMS_OFFSET
        if vLaserNum > interface.NUM_VIRTUAL_LASERS:
            raise ValueError("Maximum number of virtual lasers available is %d" % interface.NUM_VIRTUAL_LASERS)
        vLaserParams = interface.VirtualLaserParamsType()
        virtualLaserParamsAddr = VIRTUAL_LASER_PARAMS_BASE + 4*(vLaserNum-1)*interface.VIRTUAL_LASER_PARAMS_SIZE
        self.doOperation(Operation("ACTION_WB_CACHE",[virtualLaserParamsAddr,4*interface.VIRTUAL_LASER_PARAMS_SIZE]))
        self.usb.hpiRead(virtualLaserParamsAddr,vLaserParams)
        return vLaserParams
    
class SensorHistory(Singleton):
    """Stores latest values of all sensor streams in a dictionary
    so that snapshots of these quantities may be written to the state
    database at different intervals"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            # Dictionary indexed by sensor stream ID
            self.latestSensors = {}
            self.periods = StateDatabase().periodByLevel
            # Dictionary indexed by history "level", each level having a
            #  collation period (1s, 10s, 100s, 1000s, 10000s)
            self.lastArchived = [0 for p in self.periods]
            self.maxIdx = [-1 for p in self.periods]
            self.mostRecent = 0
            # Following dictionaries are indexed by level and then by sensor
            #  stream ID
            self.minSensors = [{} for p in self.periods]
            self.maxSensors = [{} for p in self.periods]
            self.sumSensors = [{} for p in self.periods]
            self.pointsInSum = [{} for p in self.periods]
            self.initialized = True
    def needToArchive(self,last,now,period):
        """Return true if there is an exact multiple of period between
        last and now"""
        return (now//period)*period > last
    def record(self,data):
        if data.timestamp != self.mostRecent:
            # This point occured at a new time. Need to check if we
            #  need to write out snapshot at the various levels
            for i,p in enumerate(self.periods):
                period_ms = int(1000*p)
                if self.needToArchive(
                        self.lastArchived[i],data.timestamp,period_ms):
                    stateDatabase = StateDatabase()
                    stateDatabase.writeSnapshot(i,self.latestSensors,
                                                self.minSensors[i],
                                                self.maxSensors[i],
                                                self.sumSensors[i],
                                                self.pointsInSum[i],
                                                self.maxIdx)
                    self.lastArchived[i] = data.timestamp
                    self.minSensors[i] = {}
                    self.maxSensors[i] = {}
                    self.sumSensors[i] = {}
                    self.pointsInSum[i] = {}
            self.mostRecent = data.timestamp
        self.latestSensors[data.streamNum]=(data.timestamp,data.value)
        # Update the sensor statistics
        for i,p in enumerate(self.periods):
            minSensors = self.minSensors[i]
            maxSensors = self.maxSensors[i]
            sumSensors = self.sumSensors[i]
            pointsInSum = self.pointsInSum[i]
            if data.streamNum in minSensors:
                minSensors[data.streamNum] = min(
                    minSensors[data.streamNum],data.value)
            else:
                minSensors[data.streamNum] = data.value
            if data.streamNum in maxSensors:
                maxSensors[data.streamNum] = max(
                    maxSensors[data.streamNum],data.value)
            else:
                maxSensors[data.streamNum] = data.value
            if data.streamNum in sumSensors:
                sumSensors[data.streamNum] = sumSensors[data.streamNum] + data.value
            else:
                sumSensors[data.streamNum] = data.value
            if data.streamNum in pointsInSum:
                pointsInSum[data.streamNum] = pointsInSum[data.streamNum] + 1
            else:
                pointsInSum[data.streamNum] = 1

# We are not allowed to access an sqlite3 database for write from multiple threads in NTFS.
#  We thus create a handler running in a single thread which services requests enqueued
#  from multiple clients. On the read side, we make the function block until the data are
#  available. In order to maintain the correct sequence of reads, a lock is used to serialize them.

def protectedRead(func):
    """This decorator protects reads from the database by using a Lock. The decorated function is
        executed in the txHandler thread so that all database access is from one thread."""
    def wrapper(self,*args):
        def _func(*args):
            return func(self,*args)
        self.dbLock.acquire()
        txId = self.getId()
        self.txQueue.put((txId,_func,args))
        while True:
            rxId, exc, result = self.rxQueue.get()
            self.dbLock.release()
            if rxId == txId:
                break
        if exc:
            raise exc
        return result
    return wrapper

class StateDatabase(Singleton):
    periodByLevel = [1.0,10.0,100.0,1000.0,10000.0]
    initialized = False
    txId = 0
    def __init__(self,fileName=None):
        if not self.initialized:
            self.fileName = fileName
            self.dbLock = threading.Lock()
            self.txQueue = Queue.Queue(0)
            self.rxQueue = Queue.Queue(0)
            self.stopThread = threading.Event()
            self.hThread = threading.Thread(target = self.txQueueHandler)
            self.hThread.setDaemon(True)
            self.hThread.start()
            self.initialized = True
        elif fileName is not None:
            raise ValueError("StateDatabase has already been initialized")
    def getId(self):
        StateDatabase.txId += 1
        return StateDatabase.txId
            
    def saveFloatRegList(self,floatList):
        """Save a list of (name,value) pairs in the floating point register table."""
        def _saveFloatRegList(floatList):
            self.con.executemany("insert or replace into dasRegFloat values (?,?)",floatList)
            self.con.commit()
        self.txQueue.put((self.getId(),_saveFloatRegList,[copy.copy(floatList)]))

    def saveIntRegList(self,intList):
        """Save a list of (name,value) pairs in the integer register table"""
        def _saveIntRegList(intList):
            self.con.executemany("insert or replace into dasRegInt values (?,?)",intList)
            self.con.commit()
        self.txQueue.put((self.getId(),_saveIntRegList,[copy.copy(intList)]))

    def saveRegList(self,regList):
        """Save a list of (name,value) pairs in the appropriate register table"""
        floatList = []
        intList = []
        for r,v in regList:
            r = lookup(r)
            ri = interface.registerInfo[r]
            if ri.type == c_float:
                floatList.append((ri.name,v))
            else:
                intList.append((ri.name,v))
        self.saveFloatRegList(floatList)
        self.saveIntRegList(intList)

    def writeSnapshot(self,level,sensors,minSensors,maxSensors,sumSensors,pointsInSum,maxIdx):
        def _writeSnapshot(level,sensors,minSensors,maxSensors,sumSensors,pointsInSum,maxIdx):
            maxRows = 1024
            if maxIdx[level] < 0:
                values = self.con.execute(
                    "select max(idx) from history where level=?",
                    (level,)).fetchall()
                maxIdx[level] = values[0][0]
                if maxIdx[level] is None:
                    maxIdx[level] = -1
            if sensors:
                maxIdx[level] += 1
                dataList = []
                for streamNum in sensors:
                    time,value = sensors[streamNum]
                    minVal = minSensors.get(streamNum,value)
                    maxVal = maxSensors.get(streamNum,value)
                    average = sumSensors.get(streamNum,value)/pointsInSum.get(streamNum,1)
                    dataList.append((level,time,streamNum,average,minVal,
                                      maxVal,maxIdx[level]))
                self.con.executemany(
                    "insert into history values (?,?,?,?,?,?,?)",dataList)
    
                if maxIdx[level] % 10 == 0:
                    self.con.execute("delete from history where level=? and idx<=?",
                                 (level,maxIdx[level]-maxRows))
                self.con.commit()
        self.txQueue.put((self.getId(),_writeSnapshot,[level,sensors.copy(),minSensors.copy(),maxSensors.copy(),
                                                       sumSensors.copy(),pointsInSum.copy(),copy.copy(maxIdx)]))
        
    @protectedRead
    def getFloatRegList(self):
        "Fetch all floating point registers in the database"
        return self.con.execute("select * from dasRegFloat").fetchall()

    @protectedRead
    def getFloatReg(self,regName):
        values = self.con.execute(
            "select value from dasRegFloat where name=?",(regName,)).fetchall()
        if len(values) != 1:
            raise IndexError("Cannot access %s" % regName)
        else:
            return values[0][0]

    @protectedRead
    def getIntRegList(self):
        "Fetch all integer registers in the database"
        return self.con.execute("select * from dasRegInt").fetchall()

    @protectedRead
    def getIntReg(self,regName):
        values = self.con.execute(
            "select value from dasRegInt where name=?",
            (regName,)).fetchall()
        if len(values) != 1:
            raise KeyError("Cannot access %s" % regName)
        else:
            return values[0][0]

    @protectedRead
    def getHistory(self,streamNum):
        values = self.con.execute(
            "select time,value,level,minVal,maxVal from history" +
            " where streamNum=?",
            (streamNum,)).fetchall()
        return values
        
    def txQueueHandler(self):
        """Creates the connection to the database and services the queue of requests"""
        self.con = sqlite3.connect(self.fileName)
        tableNames = [s[0] for s in self.con.execute("select tbl_name from sqlite_master where type='table'").fetchall()]
        if not tableNames:
            self.con.execute("pragma auto_vacuum=FULL")
        if "dasRegInt" not in tableNames:
            self.con.execute("create table dasRegInt (name text primary key,value integer)")
        if "dasRegFloat" not in tableNames:
            self.con.execute("create table dasRegFloat (name text primary key,value real)")
        if "history" not in tableNames:
            self.con.execute(
                "create table history (level integer," +
                "time integer,streamNum integer,value real," +
                "minVal real,maxVal real,idx integer)")
        self.con.commit()
        while not self.stopThread.isSet():
            txId,func,args = self.txQueue.get()
            # Place a response on rxQueue if there is a return value or if an error occurs
            #  N.B. If a tx request does not return a value but throws an exception, this will
            #  be sent back. It is up to the rxQueue handler to check that the id of the response
            #  matches that of the request, and to ignore exceptions from tx requests without
            #  responses. This is done for speed, so that tx requests can return without waiting
            #  for the database commit.
            try:
                r = func(*args)
                e = None
            except Exception,e:
                pass
            if (r is not None) or (e is not None):
                self.rxQueue.put((txId,e,r))
