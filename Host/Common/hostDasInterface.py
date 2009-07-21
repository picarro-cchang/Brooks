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

from Host.autogen import usbdefs, interface
from Host.Common.crc import calcCrc32
from Host.Common.SharedTypes    import Singleton
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
FPGA_REG_BASE    = interface.RDMEM_ADDRESS + \
                       (1<<(interface.EMIF_ADDR_WIDTH+1))
RINGDOWN_BASE    = interface.DSP_DATA_ADDRESS

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
        analyzerUsb = AnalyzerUsb(usbdefs.INITIAL_VID,usbdefs.INITIAL_PID)
        try: # connecting to a blank FX2 chip
            analyzerUsb.connect()
        except: # Assume code has already been loaded
            return
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
            self.analyzerUsb.hpiaWrite(addr)
            self.analyzerUsb.hpidWrite(c_int(value))
        def readMem(addr):
            self.analyzerUsb.hpiaWrite(addr)
            result = c_int(0)
            self.analyzerUsb.setHpidInBytes(sizeof(result))
            self.analyzerUsb.hpidRead(result)
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
        self.analyzerUsb.resetHpidInFifo()
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
            data = self.hostToDspSender.rdSensorData(
                  self.sensorIndex)
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
        self.usb.hpiaWrite(HOST_BASE)
        self.usb.hpidWrite(hostMsg)
        sleep(0.003) # Necessary to ensure hpidWrite completes before signalling interrupt
        # Assert DSPINT
        self.usb.hpicWrite(0x00010003)
        # print "hpic after DSPINT: %08x" % self.usb.hpicRead()
        return self.getStatusWhenDone()
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
                    self.seqNum=seqNum
                    return seqNum
            # If not done, sleep and try again
            sleep(0.1)
            now = clock()
        seqNum = self.seqNum
        self.seqNum = None
        raise RuntimeError,("Timeout getting status after %d tries." +
            "Initial status: 0x%x, Final status: 0x%x," +
            "Expected sequence number: 0x%x") % \
            (ntries,self.initStatus,self.status,seqNum)
    @usbLockProtect
    def getStatusWhenDone(self):
        # Read done bit from COMM_STATUS_REGISTER
        seqNum = self.getSequenceNumber()
        try:
            if 0 != (self.status & interface.COMM_STATUS_BadCrcMask):
                return interface.ERROR_CRC_BAD
            if 0 != (self.status & \
                    interface.COMM_STATUS_BadSequenceNumberMask):
                print "seqNum = %d, self.seqNum = %d" % (seqNum,self.seqNum)
                return interface.ERROR_DSP_UNEXPECTED_SEQUENCE_NUMBER
            if seqNum != self.seqNum:
                print "seqNum = %d, self.seqNum = %d" % (seqNum,self.seqNum)
                return interface.ERROR_HOST_UNEXPECTED_SEQUENCE_NUMBER
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
        status = self.send(interface.ACTION_WRITE_BLOCK,argList)
        if interface.STATUS_OK != status:
            raise RuntimeError(interface.error_messages[-status])
    def wrRegFloat(self,reg,value):
        self.wrBlock(reg,float(value))
    def wrRegUint(self,reg,value):
        self.wrBlock(reg,int(value))
    def wrEnv(self,index,env):
        # Write the environment structure env to the environment
        #  table at the specified index (integer offset)
        numInt =sizeof(env)/sizeof(c_uint)
        self.wrBlock(interface.ENVIRONMENT_OFFSET+lookup(index),
            *(c_uint*numInt).from_address(addressof(env)))
    @usbLockProtect
    def rdBlock(self,offset,numInt):
        # Performs a host read of numInt unsigned integers from
        #  the communications region starting at offset
        addr = SHAREDMEM_BASE+4*lookup(offset)
        result = []
        while numInt>0:
            self.usb.hpiaWrite(addr)
            numToRead = min(numInt,128)
            data = (c_uint*numToRead)(0)
            self.usb.hpidRead(data)
            result += [int(x) for x in data]
            addr += 4*numToRead
            numInt -= numToRead
        return result
    @usbLockProtect
    def rdRegFloat(self,reg):
        # Performs a host read of a single floating point number
        #  from the software register "reg" which may be specified
        #  as an integer or a string (defined in the interface module).
        self.usb.hpiaWrite(REG_BASE+4*lookup(reg))
        data = c_float(0)
        self.usb.hpidRead(data)
        return data.value
    @usbLockProtect
    def rdRegUint(self,reg):
        # Performs a host read of a single unsigned integer from
        #  the software register "reg" which may be specified as
        #  an integer or a string (defined in the interface module).
        self.usb.hpiaWrite(REG_BASE+4*lookup(reg))
        data = c_uint(0)
        self.usb.hpidRead(data)
        return data.value
    @usbLockProtect
    def rdFPGA(self,base,reg):
        # Performs a host read of a single unsigned integer from
        #  the FPGA register which may be specified as
        #  the sum of a block base and the register index
        self.usb.hpiaWrite(FPGA_REG_BASE+4*(lookup(base)+lookup(reg)))
        data = c_uint(0)
        self.usb.hpidRead(data)
        return data.value
    @usbLockProtect
    def wrFPGA(self,base,reg,value):
        # Performs a host write of a single unsigned integer from
        #  the FPGA register which may be specified as
        #  the sum of a block base and the register index
        self.usb.hpiaWrite(FPGA_REG_BASE+4*(lookup(base)+lookup(reg)))
        self.usb.hpidWrite(c_uint(value))
    @usbLockProtect
    def readRdMemArray(self,offset,nwords=1):
        """Reads multiple words from ringdown memory into a c_uint array"""
        self.usb.hpiaWrite(interface.RDMEM_ADDRESS+4*offset)
        result = (c_uint*nwords)()
        self.usb.hpidRead(result)
        return result
    @usbLockProtect
    def readRdMem(self,offset):
        """Reads single uint from ringdown memory"""
        self.usb.hpiaWrite(interface.RDMEM_ADDRESS+4*offset)
        result = c_uint(0)
        self.usb.hpidRead(result)
        return result.value
    @usbLockProtect
    def writeRdMem(self,offset,value):
        """Reads single uint value to ringdown memory"""
        self.usb.hpiaWrite(interface.RDMEM_ADDRESS+4*offset)
        result = c_uint(value)
        self.usb.hpidWrite(result)
    @usbLockProtect
    def rdSensorData(self,index):
        # Performs a host read of the data in the specified sensor stream
        #  entry. Note that the index is the entry number, and each entry
        #  is of size 16 bytes (64 bit timestamp, 32 bit stream index
        #  and 32 bit data)
        self.usb.hpiaWrite(SENSOR_BASE + 16*index)
        data = interface.SensorEntryType()
        self.usb.hpidRead(data)
        return data
    @usbLockProtect
    def rdRingdownData(self,index):
        # Performs a host read of the data in the specified ringdown
        #  entry. Note that the index is the entry number, and each entry
        #  is of size 64 bytes
        self.usb.hpiaWrite(RINGDOWN_BASE + 64*index)
        data = interface.RingdownEntryType()
        self.usb.hpidRead(data)
        return data
    @usbLockProtect
    def rdMessageTimestamp(self,index):
        # Performs a host read of the timestamp associated with
        #  the specified message
        self.usb.hpiaWrite(MESSAGE_BASE + 128*index)
        data = c_longlong(0)
        self.usb.hpidRead(data)
        return data.value
    @usbLockProtect
    def rdMessage(self,index):
        # Performs a host read of the specified message
        self.usb.hpiaWrite(MESSAGE_BASE + 128*index + 8)
        data = (c_char*120)()
        self.usb.hpidRead(data)
        return data.value
    @usbLockProtect
    def doOperation(self,op):
        status = self.send(op.opcode,op.operandList,op.env)
        if interface.STATUS_OK != status:
            raise RuntimeError(interface.error_messages[-status])

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
                                                self.maxIdx)
                    self.lastArchived[i] = data.timestamp
                    self.minSensors[i] = {}
                    self.maxSensors[i] = {}
            self.mostRecent = data.timestamp
        self.latestSensors[data.streamNum]=(data.timestamp,data.value.asFloat)
        # Update minimum and maximum values of sensors
        for i,p in enumerate(self.periods):
            minSensors = self.minSensors[i]
            maxSensors = self.maxSensors[i]
            if data.streamNum in minSensors:
                minSensors[data.streamNum] = min(
                    minSensors[data.streamNum],data.value.asFloat)
            else:
                minSensors[data.streamNum] = data.value.asFloat
            if data.streamNum in maxSensors:
                maxSensors[data.streamNum] = max(
                    maxSensors[data.streamNum],data.value.asFloat)
            else:
                maxSensors[data.streamNum] = data.value.asFloat


class StateDatabase(Singleton):
    fileName = None
    periodByLevel = [1.0,10.0,100.0,1000.0,10000.0]
    def __init__(self,fileName=None):
        """On the first invocation, the fileName must be specified.
        Subsequently, the fileName can be omitted, since this is a
        Singleton and the existing object will be returned. It is also
        valid to change the database by calling the constructor with a
        new filename"""
        if fileName is not None:
            self.fileName = fileName
            try:
                con = sqlite3.connect(fileName)
                self.con = {thread.get_ident():con}
                tableNames = [s[0] for s in con.execute("select tbl_name from sqlite_master where type='table'").fetchall()]
                if not tableNames:
                    con.execute("pragma auto_vacuum=FULL")
                if "dasRegInt" not in tableNames:
                    con.execute("create table dasRegInt (name text primary key,value integer)")
                if "dasRegFloat" not in tableNames:
                    con.execute("create table dasRegFloat (name text primary key,value real)")
                if "history" not in tableNames:
                    con.execute(
                        "create table history (level integer," +
                        "time integer,streamNum integer,value real," +
                        "minVal real,maxVal real,idx integer)")
                con.commit()
            except:
                import traceback
                traceback.print_exc()
                self.fileName = None
                raise ValueError("Unable to connect to database %s" % fileName)
        elif self.fileName is None:
            raise ValueError("Empty filename invalid for state database")

    def getCon(self,id):
        if id not in self.con:
            self.con[id] = sqlite3.connect(self.fileName)
            print "New thread: %d, Total threads: %d" % (id,len(self.con))
        return self.con[id]

    def saveFloatRegList(self,floatList):
        """Save a list of (name,value) pairs in the floating point
        register table"""
        con = self.getCon(thread.get_ident())
        con.executemany(
            "insert or replace into dasRegFloat values (?,?)",floatList)
        con.commit()

    def saveIntRegList(self,intList):
        """Save a list of (name,value) pairs in the integer register table"""
        con = self.getCon(thread.get_ident())
        con.executemany(
            "insert or replace into dasRegInt values (?,?)",intList)
        con.commit()

    def saveRegList(self,regList):
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

    def getFloatRegList(self):
        con = self.getCon(thread.get_ident())
        return con.execute("select * from dasRegFloat").fetchall()

    def getFloatReg(self,regName):
        con = self.getCon(thread.get_ident())
        values = con.execute(
            "select value from dasRegFloat where name=?",(regName,)).fetchall()
        if len(values) != 1:
            raise KeyError("Cannot access %s" % regName)
        else:
            return values[0][0]

    def getIntRegList(self):
        con = self.getCon(thread.get_ident())
        return con.execute("select * from dasRegInt").fetchall()

    def getIntReg(self,regName):
        con = self.getCon(thread.get_ident())
        values = con.execute(
            "select value from dasRegInt where name=?",
            (regName,)).fetchall()
        if len(values) != 1:
            raise KeyError("Cannot access %s" % regName)
        else:
            return values[0][0]

    def writeSnapshot(self,level,sensors,minSensors,maxSensors,maxIdx):
        maxRows = 1024
        con = self.getCon(thread.get_ident())
        if maxIdx[level] < 0:
            values = con.execute(
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
                dataList.append((level,time,streamNum,value,minVal,
                                  maxVal,maxIdx[level]))
            con.executemany(
                "insert into history values (?,?,?,?,?,?,?)",dataList)

            if maxIdx[level] % 10 == 0:
                con.execute("delete from history where level=? and idx<=?",
                             (level,maxIdx[level]-maxRows))
            con.commit()

    def getHistory(self,level,streamNum):
        con = self.getCon(thread.get_ident())
        values = con.execute(
            "select time,value,minVal,maxVal from history" +
            " where level=? and streamNum=?",
            (level,streamNum)).fetchall()
        return values
