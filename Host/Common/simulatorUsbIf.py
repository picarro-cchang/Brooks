#!/usr/bin/python
#
# FILE:
#   simulatorUsbIf.py
#
# DESCRIPTION:
#   Simulation of USB connection to Picarro CRDS instrument
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   06-Sep-2008  sze  Initial version.
#
#  Copyright (c) 2008 Picarro, Inc. All rights reserved
#
from sys import platform
from ctypes import byref, create_string_buffer, c_ubyte, c_ushort, c_short, c_uint, c_int, c_float
from ctypes import sizeof, addressof, Union
from hexfile import HexFile
import logging
from Host.autogen import usbdefs
from Host.Common.SharedTypes import Singleton

class DataType(Union):
    _fields_ = [("asUint",  c_uint),
                ("asInt",   c_int),
                ("asFloat", c_float)]

class UsbConnectionError(Exception):
    pass

class ClaimInterfaceError(Exception):
    pass

class UsbPacketLengthError(Exception):
    pass

class SimulatorUsb(Singleton):
    """Represents the simulated USB connection between host and analyzer"""
    def __init__(self,vid,pid):
        self.vid = vid
        self.pid = pid
        # Variables to simulate DSP memory
        self.hpicReg = 0
        self.hpiaReg = 0
        self.hpiMem = {}
        self.dspSimulator = None
        #
        self.interfaceClaimed = False
        if platform == "linux2":
            self.CLAIM_PER_USE = False
        elif platform == "win32":
            self.CLAIM_PER_USE = True
    def setSimulator(self,sim):
        self.dspSimulator = sim
    def connect(self):
        self.checkHandleAndClose()
        logging.debug("SimulatorUsb: connect called, VID = %d, PID = %d" % (self.vid,self.pid,))

    def controlInTransaction(self,var,cmd,value=0,index=0):
        sv = sizeof(var)
        logging.debug("SimulatorUsb: controlInTransaction called, cmd = 0x%x, value = 0x%x, index = 0x%x, sizeof(var) = %d" % (cmd,value,index,sv))

    def controlOutTransaction(self,msg,cmd,value=0,index=0):
        sm = sizeof(msg)
        logging.debug("SimulatorUsb: controlOutTransaction called, cmd = 0x%x, value = 0x%x, index = 0x%x, sizeof(msg) = %d" % (cmd,value,index,sm))

    def getUsbVersion(self):
        version = c_ushort()
        logging.debug("SimulatorUsb: getUsbVersion called")
        return "999.99"

    def _claimInterfaceWrapper(self,func,*args,**kwargs):
        """Wraps function call between claim interface and release interface."""
        if not self.interfaceClaimed:
            logging.debug("Claiming interface")
        try:
            return func(*args,**kwargs)
        finally:
            if self.CLAIM_PER_USE:
                logging.debug("Releasing interface")
                self.interfaceClaimed = False

    def checkHandleAndClose(self):
        logging.debug("Closing USB")

    def disconnect(self):
        if self.interfaceClaimed:
            logging.debug("Releasing interface")
            self.interfaceClaimed = False
        self.checkHandleAndClose()

    def startFpgaProgram(self):
        """Use vendor command to start FPGA programming"""
        def _startFpgaProgram():
            result = c_ubyte(0x0)
            self.controlInTransaction(result,usbdefs.VENDOR_FPGA_CONFIGURE,usbdefs.FPGA_START_PROGRAM)
        self._claimInterfaceWrapper(_startFpgaProgram)

    def getFpgaStatus(self):
        """Use vendor command to read FPGA status information. Returns one byte with
        INIT in b0 and DONE in b1"""
        def _getFpgaStatus():
            status = c_ubyte()
            self.controlInTransaction(status,usbdefs.VENDOR_FPGA_CONFIGURE,usbdefs.FPGA_GET_STATUS)
            return status.value
        return self._claimInterfaceWrapper(_getFpgaStatus)

    def sendToFpga(self,string):
        """Use vendor command to send string to FPGA. Characters are sent MSB first. """
        def _sendToFpga():
            self.controlOutTransaction(create_string_buffer(bitReverse(string),len(string)),
                usbdefs.VENDOR_FPGA_CONFIGURE,usbdefs.FPGA_SEND_DATA)
        self._claimInterfaceWrapper(_sendToFpga)

    def getUsbSpeed(self):
        """Returns if USB has enumerated in high-speed mode (True) or full-speed mode (False)"""
        logging.debug("SimulatorUsb: getUsbSpeed called, returning True")
        return True
    def getGpifTrig(self):
        """Returns current value of the GPIFTRIG register"""
        logging.debug("SimulatorUsb: getGpifTrig called, returning 0")
        return 0
    def getGpifTc(self):
        """Returns current value of the GPIF transaction count"""
        logging.debug("SimulatorUsb: getGpifTc called, returning 0")
        return 0
    def hpicRead(self):
        """Use vendor command to read a 32 bit word from the HPIC register"""
        logging.debug("Calling Simulator: hpicRead, returning 0x%x" % self.hpicReg)
        return self.hpicReg

    def hpicWrite(self,w):
        """Use vendor command to send a 32 bit word to HPIC register"""
        logging.debug("Calling Simulator: hpicWrite with data 0x%x" % w)
        self.hpicReg = w
        if w & 0x20002:
            # This signals a DSPINT
            self.dspSimulator.hwiHpiInterrupt(0,0)

    def hpiaRead(self):
        """Use vendor command to read a 32 bit word from the HPIA register"""
        logging.debug("Calling Simulator: hpiaRead, returning 0x%x" % self.hpiaReg)
        return self.hpiaReg
    def hpiaWrite(self,w):
        """Use vendor command to send a 32 bit word to HPIA register"""
        self.hpiaReg = w
        logging.debug("Calling Simulator: hpiaWrite, returning 0x%x" % self.hpiaReg)
        return self.hpiaReg
    def hpidWriteString(self,string):
        self.hpidWrite(create_string_buffer(string,len(string)))

    def hpidWrite(self,data):
        """Use bulk write to send block of 32 bit words (stored as a string in data) to HPID"""
        dataLength = sizeof(data)
        if 0 != dataLength & 0x3 or 0 == dataLength or 1024 < dataLength:
            raise ValueError("Invalid data length %d in hpidWrite" % (dataLength,))
        logging.debug("Calling Simulator: hpidWrite with %d byte message" % dataLength)
        numInt = dataLength/4
        self.dspSimulator.writeMem(self.hpiaReg,(c_uint*numInt).from_address(addressof(data)))
        self.hpiaReg += dataLength
    def hpidRead(self,result):
        """Use bulk read to acquire block of 32 bit words from HPID"""
        nBytes = sizeof(result)
        if 0 != nBytes & 0x3 or 0 >= nBytes or 1024 < nBytes:
            raise UsbPacketLengthError("Invalid data length %d in hpidRead" % (nBytes,))
        logging.debug("Calling Simulator: hpidRead with %d byte result" % nBytes)
        numInt = nBytes/4
        self.dspSimulator.readMem(self.hpiaReg,(c_uint*numInt).from_address(addressof(result)))
        self.hpiaReg += nBytes

    def resetHpidInFifo(self):
        """Use vendor command to reset input FIFO from HPID"""
        logging.debug("Calling SimulatorUsb: resetHpidInFifo")

    def setDspControl(self,value):
        """Use vendor command to reset DSP or send HINT"""
        logging.debug("Calling SimulatorUsb: setDspControl with value = 0x%x" % value)
    def dspWrite(self,addrValueList):
        """Write a list of (address,value) pairs to the DSP"""
        self.hpicWrite(0x00010001)
        for addr,value in addrValueList:
            self.hpiaWrite(addr)
            self.hpidWrite(c_int(value))

    def loadDspFile(self,fp):
        """Use the HPI to send a file to the DSP"""
        hexFile = HexFile(fp)
        regions = hexFile.process()
        block = 128 # Maximum length for download
        for r in regions:
            # r.data contains the data as a list of bytes.
            n = len(r.data)
            addr = r.address
            start = 0
            # Split into chunks of size at most "block"
            while n > block:
                self.hpicWrite(0x00010001)
                self.hpiaWrite(addr+start)
                self.hpidWrite(create_string_buffer("".join(r.data[start:start+block]),block))
                #rbuff = (c_ubyte*block)()
                #self.hpidWrite(rbuff)
                # Read back
                #recvArray = (c_ubyte*block)()
                #self.hpiaWrite(addr+start)
                #self.hpidRead(recvArray)
                #for i in range(block):
                #    print "%s, %s" % (recvArray[i],ord(r.data[start+i]))
                n -= block
                start += block
            if n>0:
                self.hpicWrite(0x00010001)
                self.hpiaWrite(addr+start)
                self.hpidWrite(create_string_buffer("".join(r.data[start:start+n]),n))

    def loadHexFile(self,fp):
        """Use vendor command 0xA0 to load hex file to device and renumerate"""
        def _loadHexFile():
            # Hold the 8051 in reset during download
            self.controlOutTransaction(c_ubyte(0x1),0xA0,0xE600)

            # Use the vendor command to download the hexadecimal data
            hexFile = HexFile(fp)
            regions = hexFile.process()

            block = 128 # Maximum length for download
            for r in regions:
                # r.data contains the data as a list of bytes.
                n = len(r.data)
                addr = r.address
                start = 0
                # Split into chunks of size at most "block" for sending to the FX2
                while n > block:
                    self.controlOutTransaction(create_string_buffer("".join(r.data[start:start+block]),block),0xA0,addr+start)
                    n -= block
                    start += block
                if n>0:
                    self.controlOutTransaction(create_string_buffer("".join(r.data[start:start+n]),n),0xA0,addr+start)
            # Release the 8051 reset, allowing it to renumerate
            self.controlOutTransaction(c_ubyte(0x0),0xA0,0xE600)
        return self._claimInterfaceWrapper(_loadHexFile)


bitrevList = \
[ 0x00, 0x80, 0x40, 0xC0, 0x20, 0xA0, 0x60, 0xE0, 0x10, 0x90, 0x50, 0xD0, 0x30, 0xB0, 0x70, 0xF0,
  0x08, 0x88, 0x48, 0xC8, 0x28, 0xA8, 0x68, 0xE8, 0x18, 0x98, 0x58, 0xD8, 0x38, 0xB8, 0x78, 0xF8,
  0x04, 0x84, 0x44, 0xC4, 0x24, 0xA4, 0x64, 0xE4, 0x14, 0x94, 0x54, 0xD4, 0x34, 0xB4, 0x74, 0xF4,
  0x0C, 0x8C, 0x4C, 0xCC, 0x2C, 0xAC, 0x6C, 0xEC, 0x1C, 0x9C, 0x5C, 0xDC, 0x3C, 0xBC, 0x7C, 0xFC,
  0x02, 0x82, 0x42, 0xC2, 0x22, 0xA2, 0x62, 0xE2, 0x12, 0x92, 0x52, 0xD2, 0x32, 0xB2, 0x72, 0xF2,
  0x0A, 0x8A, 0x4A, 0xCA, 0x2A, 0xAA, 0x6A, 0xEA, 0x1A, 0x9A, 0x5A, 0xDA, 0x3A, 0xBA, 0x7A, 0xFA,
  0x06, 0x86, 0x46, 0xC6, 0x26, 0xA6, 0x66, 0xE6, 0x16, 0x96, 0x56, 0xD6, 0x36, 0xB6, 0x76, 0xF6,
  0x0E, 0x8E, 0x4E, 0xCE, 0x2E, 0xAE, 0x6E, 0xEE, 0x1E, 0x9E, 0x5E, 0xDE, 0x3E, 0xBE, 0x7E, 0xFE,
  0x01, 0x81, 0x41, 0xC1, 0x21, 0xA1, 0x61, 0xE1, 0x11, 0x91, 0x51, 0xD1, 0x31, 0xB1, 0x71, 0xF1,
  0x09, 0x89, 0x49, 0xC9, 0x29, 0xA9, 0x69, 0xE9, 0x19, 0x99, 0x59, 0xD9, 0x39, 0xB9, 0x79, 0xF9,
  0x05, 0x85, 0x45, 0xC5, 0x25, 0xA5, 0x65, 0xE5, 0x15, 0x95, 0x55, 0xD5, 0x35, 0xB5, 0x75, 0xF5,
  0x0D, 0x8D, 0x4D, 0xCD, 0x2D, 0xAD, 0x6D, 0xED, 0x1D, 0x9D, 0x5D, 0xDD, 0x3D, 0xBD, 0x7D, 0xFD,
  0x03, 0x83, 0x43, 0xC3, 0x23, 0xA3, 0x63, 0xE3, 0x13, 0x93, 0x53, 0xD3, 0x33, 0xB3, 0x73, 0xF3,
  0x0B, 0x8B, 0x4B, 0xCB, 0x2B, 0xAB, 0x6B, 0xEB, 0x1B, 0x9B, 0x5B, 0xDB, 0x3B, 0xBB, 0x7B, 0xFB,
  0x07, 0x87, 0x47, 0xC7, 0x27, 0xA7, 0x67, 0xE7, 0x17, 0x97, 0x57, 0xD7, 0x37, 0xB7, 0x77, 0xF7,
  0x0F, 0x8F, 0x4F, 0xCF, 0x2F, 0xAF, 0x6F, 0xEF, 0x1F, 0x9F, 0x5F, 0xDF, 0x3F, 0xBF, 0x7F, 0xFF ]

bitrevStr = "".join([chr(b) for b in bitrevList])

def bitReverse(str):
    return str.translate(bitrevStr)
