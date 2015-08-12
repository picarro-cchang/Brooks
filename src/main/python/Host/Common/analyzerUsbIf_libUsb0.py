#!/usr/bin/python
#
# FILE:
#   analyzerUsbIf.py
#
# DESCRIPTION:
#   Interface to USB FX2 firmware for Picarro gas analyzer
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   07-May-2008  sze  Initial version.
#   28-Sep-2010  sze  Set CLAIM_PER_USE to False in Windows to be consistent with Linux.
#                     This requires us to reset the USB interface if we cannot claim it.
#   15-Dec-2013  sze  Corrected position of USB_MAX_PACKET_SIZE global which was causing the
#                      wrong packet size (64 bytes instead of 512 bytes) to be used.
#
#  Copyright (c) 2008 Picarro, Inc. All rights reserved
#
from sys import platform
from Host.Common.usb import LibUSB, USB_ENDPOINT_OUT, USB_ENDPOINT_IN
from ctypes import byref, create_string_buffer, c_ubyte, c_ushort, c_short, c_uint, sizeof, addressof
from Host.Common.hexfile import HexFile
from Host.autogen import usbdefs
from Host.Common.SharedTypes import Singleton
import struct
import time

DEFAULT_OUT_ENDPOINT = USB_ENDPOINT_OUT | 2
DEFAULT_IN_ENDPOINT  = USB_ENDPOINT_IN  | 6
AUXILIARY_OUT_ENDPOINT = USB_ENDPOINT_OUT | 4
AUXILIARY_IN_ENDPOINT = USB_ENDPOINT_IN  | 8

USB_MAX_PACKET_SIZE = 64

class UsbConnectionError(Exception):
    pass

class ClaimInterfaceError(Exception):
    pass

class UsbPacketLengthError(Exception):
    pass

class AnalyzerUsb(Singleton):
    """Represents USB connection between host and analyzer at specified VID and PID"""
    def __init__(self,vid,pid):
        self.usb = LibUSB()
        self.usbDict = {}
        self.handle = None
        self.vid = vid
        self.pid = pid
        self.interfaceClaimed = False
        if platform == "linux2":
            self.CLAIM_PER_USE = False
        elif platform == "win32":
            # self.CLAIM_PER_USE = True
            self.CLAIM_PER_USE = False
        self.usb.usbInit()

    def connect(self):
        def _connect():
            self.checkHandleAndClose()
            self.usbDict["busses"] = []
            self.usb.usbFindBusses()
            self.usb.usbFindDevices()
            for bus in self.usb.usbBusses():
                busDict = dict(dirname=bus.dirname,devices=[])
                self.usbDict["busses"].append(busDict)
                for pDev in self.usb.usbDevices(bus):
                    dev = pDev.contents
                    devDict = dict(filename=dev.filename,vendorId=dev.descriptor.idVendor,productId=dev.descriptor.idProduct)
                    busDict["devices"].append(devDict)
                    if devDict["vendorId"] == self.vid and devDict["productId"] == self.pid:
                        self.handle = self.usb.usbOpen(pDev)
                        break
            if self.handle == None:
                raise UsbConnectionError("Cannot connect to device with VID: 0x%x, PID: 0x%x" % (self.vid,self.pid))
            if self.usb.usbSetConfiguration(self.handle,1) < 0:
                raise UsbConnectionError("Setting configuration 1 failed")
        _connect()
        # Try to claim interface
        stat = self.usb.usbClaimInterface(self.handle,0)
        if stat < 0:
            self.usb.usbReset(self.handle)
            time.sleep(2.0)
            _connect()
        else:
            self.interfaceClaimed = True

    def controlInTransaction(self,var,cmd,value=0,index=0):
        sv = sizeof(var)
        actual = self.usb.usbControlMsg(self.handle,0xC0,cmd,value,index,byref(var),sv,5000)
        if actual != sv:
            raise UsbPacketLengthError("Unexpected packet length %d [%d] in controlIn transaction 0x%2x" % (actual,sv,cmd))
        return

    def controlOutTransaction(self,msg,cmd,value=0,index=0):
        sm = sizeof(msg)
        actual = self.usb.usbControlMsg(self.handle,0x40,cmd,value,index,byref(msg),sm,5000)
        if actual != sm:
            raise UsbPacketLengthError("Unexpected packet length %d [%d] in controlOut transaction 0x%2x" % (actual,sm,cmd))
        return

    def controlOutBlock(self,cmd,address,data):
        """Write an arbitrarily sized (but must be a multiple of 4) block of data to the USB control port
            with command cmd, splitting the block up if necessary"""
        dataLength = sizeof(data)
        chunkSize = USB_MAX_PACKET_SIZE
        a = addressof(data)
        while dataLength > chunkSize:
            dataBuffer = (c_ubyte*chunkSize).from_address(a)
            self.controlOutTransaction(dataBuffer,cmd,address)
            address += chunkSize
            a += chunkSize
            dataLength -= chunkSize
            time.sleep(0) # to yield processor when transferring a large block
        if dataLength > 0:
            dataBuffer = (c_ubyte*dataLength).from_address(a)
            self.controlOutTransaction(dataBuffer,cmd,address)

    def getUsbVersion(self):
        def _getUsbVersion():
            version = c_ushort()
            self.controlInTransaction(version,usbdefs.VENDOR_GET_VERSION)
            return version.value
        return self._claimInterfaceWrapper(_getUsbVersion)

    def _claimInterfaceWrapper(self,func,*args,**kwargs):
        """Wraps function call between claim interface and release interface."""
        if not self.interfaceClaimed:
            stat = self.usb.usbClaimInterface(self.handle,0)
            if stat < 0:
                raise ClaimInterfaceError("Error %s (%d) while claiming interface for %s" % (self.usb.usbStrerror(),stat,func.__name__))
            else:
                self.interfaceClaimed = True
        try:
            return func(*args,**kwargs)
        finally:
            if self.CLAIM_PER_USE:
                stat = self.usb.usbReleaseInterface(self.handle,0)
                if stat < 0:
                    raise ClaimInterfaceError("Error %s (%d) while releasing interface for %s" % (self.usb.usbStrerror(),stat,func.__name__))
                self.interfaceClaimed = False

    def checkHandleAndClose(self):
        if self.handle != None:
            stat = self.usb.usbClose(self.handle)
            if stat < 0:
                raise UsbConnectionError("Error %s (%d) while closing USB" % (self.usb.usbStrerror(),stat))
            self.handle = None

    def disconnect(self):
        if self.interfaceClaimed:
            stat = self.usb.usbReleaseInterface(self.handle,0)
            if stat < 0:
                raise ClaimInterfaceError("Error %s (%d) while releasing interface." % (self.usb.usbStrerror(),stat))
            self.interfaceClaimed = False
        self.checkHandleAndClose()

    def startFpgaProgram(self):
        """Use vendor command to start FPGA programming"""
        def _startFpgaProgram():
            result = c_ubyte(0x0)
            self.controlInTransaction(result,usbdefs.VENDOR_FPGA_CONFIGURE,usbdefs.FPGA_START_PROGRAM)
            if result.value != 1:
                raise ValueError("Invalid response in startFpgaProgram")
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
        """Returns if USB has enumerated in high-speed mode (True) or full-speed mode (False).
            Also sets up module variable USB_MAX_PACKET_SIZE."""
        def _getUsbSpeed():
            global USB_MAX_PACKET_SIZE
            speed = c_ubyte()
            self.controlInTransaction(speed,usbdefs.VENDOR_GET_STATUS,usbdefs.USB_STATUS_SPEED)
            USB_MAX_PACKET_SIZE = 512 if speed.value else 64
            return speed.value
        return self._claimInterfaceWrapper(_getUsbSpeed)

    def getGpifTrig(self):
        """Returns current value of the GPIFTRIG register"""
        def _getGpifTrig():
            gpiftrig = c_ubyte()
            self.controlInTransaction(gpiftrig,usbdefs.VENDOR_GET_STATUS,usbdefs.USB_STATUS_GPIFTRIG)
            return gpiftrig.value
        return self._claimInterfaceWrapper(_getGpifTrig)

    def getGpifTc(self):
        """Returns current value of the GPIF transaction count"""
        def _getGpifTc():
            tc = c_uint()
            self.controlInTransaction(tc,usbdefs.VENDOR_GET_STATUS,usbdefs.USB_STATUS_GPIFTC)
            return tc.value
        return self._claimInterfaceWrapper(_getGpifTc)

    def hpicRead(self):
        """Use vendor command to read a 32 bit word from the HPIC register"""
        def _hpicRead():
            data = c_uint(0)
            self.controlInTransaction(data,usbdefs.VENDOR_READ_HPIC)
            return data.value
        return self._claimInterfaceWrapper(_hpicRead)

    def hpicWrite(self,w):
        """Use vendor command to send a 32 bit word to HPIC register"""
        def _hpicWrite():
            data = c_uint(w)
            self.controlOutTransaction(data,usbdefs.VENDOR_WRITE_HPIC)
        self._claimInterfaceWrapper(_hpicWrite)

    def hpiaRead(self):
        """Use vendor command to read a 32 bit word from the HPIA register"""
        def _hpiaRead():
            data = c_uint(0)
            self.controlInTransaction(data,usbdefs.VENDOR_READ_HPIA)
            return data.value
        return self._claimInterfaceWrapper(_hpiaRead)

    def hpiaWrite(self,w):
        """Use vendor command to send a 32 bit word to HPIA register"""
        def _hpiaWrite():
            data = c_uint(w)
            self.controlOutTransaction(data,usbdefs.VENDOR_WRITE_HPIA)
        self._claimInterfaceWrapper(_hpiaWrite)

    def hpidWriteString(self,string):
        self.hpidWrite(create_string_buffer(string,len(string)))

    def hpidWrite(self,data):
        """Use bulk write to send block of 32 bit words (stored as a string in data) to HPID"""
        dataLength = sizeof(data)
        def _hpidWrite():
            self.usb.usbBulkWrite(self.handle,DEFAULT_OUT_ENDPOINT,byref(data),dataLength,5000)
        if 0 != dataLength & 0x3 or 0 == dataLength or 512 < dataLength:
            raise UsbPacketLengthError("Invalid data length %d in hpidWrite" % (dataLength,))
        self._claimInterfaceWrapper(_hpidWrite)

    def hpiWrite(self,address,data):
        """Write an arbitrarily sized (but must be a multiple of 4) block of data to address,
            splitting the block up if necessary"""
        dataLength = sizeof(data)
        chunkSize = USB_MAX_PACKET_SIZE
        a = addressof(data)
        while dataLength > chunkSize:
            dataBuffer = (c_ubyte*chunkSize).from_address(a)
            self.hpiaWrite(address)
            self.hpidWrite(dataBuffer)
            address += chunkSize
            a += chunkSize
            dataLength -= chunkSize
            time.sleep(0) # to yield processor when transferring a large block
        if dataLength > 0:
            dataBuffer = (c_ubyte*dataLength).from_address(a)
            self.hpiaWrite(address)
            self.hpidWrite(dataBuffer)

    def hpidRead(self,result):
        """Use bulk read to acquire block of 32 bit words from HPID"""
        nBytes = sizeof(result)
        if 0 != nBytes & 0x3 or 0 >= nBytes or 512 < nBytes:
            raise UsbPacketLengthError("Invalid data length %d in hpidRead" % (nBytes,))
        def _hpidRead():
            data = c_short(nBytes)
            self.controlOutTransaction(data,usbdefs.VENDOR_SET_HPID_IN_BYTES)
            self.usb.usbBulkRead(self.handle,DEFAULT_IN_ENDPOINT,byref(result),nBytes,5000)
        self._claimInterfaceWrapper(_hpidRead)

    def hpiRead(self,address,data):
        """Read an arbitrarily sized (but must be a multiple of 4) block of data from address,
            splitting the block up if necessary"""
        dataLength = sizeof(data)
        chunkSize = USB_MAX_PACKET_SIZE
        a = addressof(data)
        while dataLength > chunkSize:
            dataBuffer = (c_ubyte*chunkSize).from_address(a)
            self.hpiaWrite(address)
            self.hpidRead(dataBuffer)
            address += chunkSize
            a += chunkSize
            dataLength -= chunkSize
            time.sleep(0) # to yield processor when transferring a large block
        if dataLength > 0:
            dataBuffer = (c_ubyte*dataLength).from_address(a)
            self.hpiaWrite(address)
            self.hpidRead(dataBuffer)

    def resetHpidInFifo(self):
        """Use vendor command to reset input FIFO from HPID"""
        def _resetHpidInFifo():
            result = c_ubyte(0x0)
            self.controlInTransaction(result,usbdefs.VENDOR_RESET_HPID_IN_FIFO)
            if result.value != 1:
                raise ValueError("Invalid response in resetHpidInFifo")
        self._claimInterfaceWrapper(_resetHpidInFifo)

    def wrAuxiliary(self,data):
        """Use bulk write to send block of 16 bit words (stored as a string in data) to auxiliary board"""
        dataLength = sizeof(data)
        def _wrAuxiliary():
            self.usb.usbBulkWrite(self.handle,AUXILIARY_OUT_ENDPOINT,byref(data),dataLength,5000)
        if 0 == dataLength or 512 < dataLength:
            raise UsbPacketLengthError("Invalid data length %d in auxiliaryWrite" % (dataLength,))
        self._claimInterfaceWrapper(_wrAuxiliary)

    def pingWatchdog(self):
        """Use vendor command to ping watchdog"""
        def _pingWatchdog():
            result = c_ubyte(0)
            self.controlInTransaction(result,usbdefs.VENDOR_PING_WATCHDOG)
        self._claimInterfaceWrapper(_pingWatchdog)

    def setDspControl(self,value):
        """Use vendor command to reset DSP or send HINT"""
        def _setDspControl():
            result = c_ubyte(0)
            self.controlInTransaction(result,usbdefs.VENDOR_DSP_CONTROL,value)
            if result.value != value:
                raise ValueError("Invalid response in setDspControl")
        self._claimInterfaceWrapper(_setDspControl)

    def wrDac(self,channel,value):
        """Use vendor command to write to DAC on analog interface board"""
        def _wrDac():
            self.controlOutTransaction(create_string_buffer(struct.pack(">H",value),2),usbdefs.VENDOR_SET_DAC,channel)
        self._claimInterfaceWrapper(_wrDac)

    # def getDacQueueFreeSlots(self):
        # """Returns list with the number of slots available for each DAC queue"""
        # def _getDacQueueFreeSlots():
            # freeSlots = (c_ubyte*8)()
            # self.controlInTransaction(freeSlots,usbdefs.VENDOR_DAC_QUEUE_STATUS,usbdefs.DAC_QUEUE_GET_FREE)
            # return [f for f in freeSlots]
        # return self._claimInterfaceWrapper(_getDacQueueFreeSlots)

    # def getDacQueueErrors(self):
        # """Returns bit masks of underflows and overflows in the DAC queues"""
        # def _getDacQueueErrors():
            # errors = (c_ubyte*4)()
            # self.controlInTransaction(errors,usbdefs.VENDOR_DAC_QUEUE_STATUS,usbdefs.DAC_QUEUE_GET_ERRORS)
            # return dict(underflows = errors[0], overflows = errors[1], now = (errors[3]<<8) + errors[2])
        # return self._claimInterfaceWrapper(_getDacQueueErrors)

    # def setDacQueuePeriod(self,channel,period):
        # """Sets service period (in hundredth's of a second) of a DAC queue"""
        # if channel<0 or channel>=8:
            # raise ValueError('Only channels 0..7 are available')
        # if period<0 or period>=65535:
            # raise ValueError('Period must be in range 0..65535')
        # def _setDacQueuePeriod():
            # data = (c_ubyte*3)()
            # data[0] = channel
            # data[1] = period & 0xFF
            # data[2] = (period>>8) & 0xFF
            # self.controlOutTransaction(data,
                # usbdefs.VENDOR_DAC_QUEUE_CONTROL,usbdefs.DAC_QUEUE_SET_PERIOD)
        # self._claimInterfaceWrapper(_setDacQueuePeriod)

    # def resetDacQueues(self):
        # """Stop serving from DAC queues and set them all to empty"""
        # def _resetDacQueues():
            # self.controlOutTransaction(c_ubyte(0),
                # usbdefs.VENDOR_DAC_QUEUE_CONTROL,usbdefs.DAC_QUEUE_RESET)
        # self._claimInterfaceWrapper(_resetDacQueues)

    # def serveDacQueues(self):
        # """Start serving from DAC queues"""
        # def _serveDacQueues():
            # self.controlOutTransaction(c_ubyte(0),
                # usbdefs.VENDOR_DAC_QUEUE_CONTROL,usbdefs.DAC_QUEUE_SERVE)
        # self._claimInterfaceWrapper(_serveDacQueues)

    def resetDacQueue(self):
        """Reset DAC queue and clear error flags"""
        def _resetDacQueue():
            self.controlOutTransaction(c_ubyte(0),
                usbdefs.VENDOR_DAC_QUEUE_CONTROL,usbdefs.DAC_QUEUE_RESET)
        self._claimInterfaceWrapper(_resetDacQueue)

    def setDacTimestamp(self,timestamp):
        """Set DAC timestamp (resolution = 10ms)"""
        if timestamp<0 or timestamp>=65536:
            raise ValueError('Only timestamps in range 0..65535 are valid')
        def _setDacTimestamp():
            data = (c_ushort)(timestamp)
            self.controlOutTransaction(data,
                usbdefs.VENDOR_DAC_QUEUE_CONTROL,usbdefs.DAC_SET_TIMESTAMP)
        self._claimInterfaceWrapper(_setDacTimestamp)

    def setDacReloadCount(self,reloadCount):
        """Sets reload count for DAC timestamp clock divsor"""
        if reloadCount<0 or reloadCount>=65536:
            raise ValueError('Only reloadCount in range 0..65535 are valid')
        def _setDacReloadCount():
            data = (c_ushort)(reloadCount)
            self.controlOutTransaction(data,
                usbdefs.VENDOR_DAC_QUEUE_CONTROL,usbdefs.DAC_SET_RELOAD_COUNT)
        self._claimInterfaceWrapper(_setDacReloadCount)

    def getDacTimestamp(self):
        """Returns current value of DAC timestamp"""
        def _getDacTimestamp():
            data = (c_ushort)(0)
            self.controlInTransaction(data,usbdefs.VENDOR_DAC_QUEUE_STATUS,usbdefs.DAC_GET_TIMESTAMP)
            return data.value
        return self._claimInterfaceWrapper(_getDacTimestamp)

    def getDacReloadCount(self):
        """Returns current value of DAC timestamp clock divisor reload count"""
        def _getDacReloadCount():
            data = (c_ushort)(0)
            self.controlInTransaction(data,usbdefs.VENDOR_DAC_QUEUE_STATUS,usbdefs.DAC_GET_RELOAD_COUNT)
            return data.value
        return self._claimInterfaceWrapper(_getDacReloadCount)

    def getDacQueueFree(self):
        """Returns number of bytes available in DAC queue"""
        def _getDacQueueFree():
            data = (c_ushort)(0)
            self.controlInTransaction(data,usbdefs.VENDOR_DAC_QUEUE_STATUS,usbdefs.DAC_QUEUE_GET_FREE)
            return data.value
        return self._claimInterfaceWrapper(_getDacQueueFree)

    def getDacQueueErrors(self):
        """Returns error bit mask"""
        def _getDacQueueErrors():
            errors = c_ubyte()
            self.controlInTransaction(errors,usbdefs.VENDOR_DAC_QUEUE_STATUS,usbdefs.DAC_QUEUE_GET_ERRORS)
            return errors.value
        return self._claimInterfaceWrapper(_getDacQueueErrors)

    def enqueueDacSamples(self,data):
        """Use vendor command to send block of 16 bit words (stored as a string in data) to auxiliary board"""
        dataLength = sizeof(data)
        def _enqueueDacSamples():
            self.controlOutTransaction(data,usbdefs.VENDOR_DAC_ENQUEUE_DATA)
        if 0 == dataLength or 64 < dataLength:
            raise UsbPacketLengthError("Invalid data length %d in enqueueDacSamples" % (dataLength,))
        return self._claimInterfaceWrapper(_enqueueDacSamples)

    def dspWrite(self,addrValueList):
        """Write a list of (address,value) pairs to the DSP"""
        self.hpicWrite(0x00010001)
        for addr,value in addrValueList:
            self.hpiaWrite(addr)
            self.hpidWrite(c_uint(value))

    def loadDspFile(self,fp):
        """Use the HPI to send a file to the DSP"""
        hexFile = HexFile(fp)
        regions = hexFile.process()
        for r in regions:
            # r.data contains the data as a list of bytes.
            self.hpiWrite(r.address,create_string_buffer("".join(r.data),len(r.data)))

    def loadHexFile(self,fp):
        """Use vendor command 0xA0 to load hex file to device and renumerate"""
        def _loadHexFile():
            # Hold the 8051 in reset during download
            self.controlOutTransaction(c_ubyte(0x1),0xA0,0xE600)

            # Use the vendor command to download the hexadecimal data
            hexFile = HexFile(fp)
            regions = hexFile.process()

            for r in regions:
                # r.data contains the data as a list of bytes.
                self.controlOutBlock(0xA0,r.address,create_string_buffer("".join(r.data),len(r.data)))

            # Release the reset to renumerate
            self.controlOutTransaction(c_ubyte(0x0),0xA0,0xE600)
            self.disconnect()
        # Do not wrap function, since it disconnects on completion
        return _loadHexFile()

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

def bitReverse(inputStr):
    return inputStr.translate(bitrevStr)