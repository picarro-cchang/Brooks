#!/usr/bin/python
"""
FILE:
  DspAccessor.py

DESCRIPTION:
  Low level interface to and programming of the DSP via HPI

SEE ALSO:
  Specify any related information.

HISTORY:
  29-Nov-2013  sze  Extracted from analyzerUsbIf

 Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
import time
from ctypes import addressof, c_int, c_short, c_ubyte, c_uint, create_string_buffer, memmove, sizeof
from Host.autogen import usbdefs
from Host.Common.hexfile import HexFile
from Host.Common.SharedTypes import UsbPacketLengthError

USB_ENDPOINT_IN = 0x80
USB_ENDPOINT_OUT = 0x00

DEFAULT_OUT_ENDPOINT = USB_ENDPOINT_OUT | 2
DEFAULT_IN_ENDPOINT = USB_ENDPOINT_IN | 6

EMIF_GCTL = 0x01800000
EMIF_CE1 = 0x01800004
EMIF_CE0 = 0x01800008
EMIF_CE2 = 0x01800010
EMIF_CE3 = 0x01800014
EMIF_SDRAMCTL = 0x01800018
EMIF_SDRAMTIM = 0x0180001C
EMIF_SDRAMEXT = 0x01800020
EMIF_CCFG = 0x01840000     # Cache configuration register
CHIP_DEVCFG = 0x019C0200     # Chip configuration register

PLL_BASE_ADDR = 0x01b7c000
PLL_PID = (PLL_BASE_ADDR + 0x000)
PLL_CSR = (PLL_BASE_ADDR + 0x100)
PLL_MULT = (PLL_BASE_ADDR + 0x110)
PLL_DIV0 = (PLL_BASE_ADDR + 0x114)
PLL_DIV1 = (PLL_BASE_ADDR + 0x118)
PLL_DIV2 = (PLL_BASE_ADDR + 0x11C)
PLL_DIV3 = (PLL_BASE_ADDR + 0x120)
PLL_OSCDIV1 = (PLL_BASE_ADDR + 0x124)

CSR_PLLEN = 0x00000001
CSR_PLLPWRDN = 0x00000002
CSR_PLLRST = 0x00000008
CSR_PLLSTABLE = 0x00000040
DIV_ENABLE = 0x00008000


class DspAccessor(object):

    """Access the TI DSP via the HPI using the Cypress USB Controller.

    Args:
      deviceUsb: Instance of an AnalyzerUsb object
    """

    def __init__(self, deviceUsb):
        self.deviceUsb = deviceUsb

    def getGpifTrig(self):
        """Returns current value of the GPIFTRIG register.
        """
        def _getGpifTrig():
            """Low-level routine to be wrapped by claimInterfaceWrapper
            """
            gpiftrig = c_ubyte()
            self.deviceUsb.controlInTransaction(
                gpiftrig, usbdefs.VENDOR_GET_STATUS, usbdefs.USB_STATUS_GPIFTRIG)
            return gpiftrig.value
        return self.deviceUsb.claimInterfaceWrapper(_getGpifTrig)

    def getGpifTc(self):
        """Returns current value of the GPIF transaction count.
        """
        def _getGpifTc():
            """Low-level routine to be wrapped by claimInterfaceWrapper
            """
            transCount = c_uint()
            self.deviceUsb.controlInTransaction(
                transCount, usbdefs.VENDOR_GET_STATUS, usbdefs.USB_STATUS_GPIFTC)
            return transCount.value
        return self.deviceUsb.claimInterfaceWrapper(_getGpifTc)

    def hpicRead(self):
        """Read a 32 bit word from the HPIC register.

        This uses a vendor command to perfotm the read
        """
        def _hpicRead():
            """Low-level routine to be wrapped by claimInterfaceWrapper
            """
            data = c_uint(0)
            self.deviceUsb.controlInTransaction(data, usbdefs.VENDOR_READ_HPIC)
            return data.value
        return self.deviceUsb.claimInterfaceWrapper(_hpicRead)

    def hpicWrite(self, word):
        """Write a 32 bit word to HPIC register

        This uses a vendor command to perfotm the write
        """
        def _hpicWrite():
            """Low-level routine to be wrapped by claimInterfaceWrapper
            """
            data = c_uint(word)
            self.deviceUsb.controlOutTransaction(data, usbdefs.VENDOR_WRITE_HPIC)
        self.deviceUsb.claimInterfaceWrapper(_hpicWrite)

    def hpiaRead(self):
        """Read a 32 bit word from the HPIA register

        This uses a vendor command to perfotm the read
        """
        def _hpiaRead():
            """Low-level routine to be wrapped by claimInterfaceWrapper
            """
            data = c_uint(0)
            self.deviceUsb.controlInTransaction(data, usbdefs.VENDOR_READ_HPIA)
            return data.value
        return self.deviceUsb.claimInterfaceWrapper(_hpiaRead)

    def hpiaWrite(self, word):
        """Write a 32 bit word to HPIA register

        This uses a vendor command to perfotm the write
        """
        def _hpiaWrite():
            """Low-level routine to be wrapped by claimInterfaceWrapper
            """
            data = c_uint(word)
            self.deviceUsb.controlOutTransaction(data, usbdefs.VENDOR_WRITE_HPIA)
        self.deviceUsb.claimInterfaceWrapper(_hpiaWrite)

    def hpidWrite(self, data):
        """Write a block of 32-bit words (max length 512 bytes) to HPID

        Use bulk write to send block of 32 bit words (stored as a ctypes object) to HPID.
        The maximum length of the block is 128 32-bit words or 512 bytes. Note that the address
        should previously have been set up.

        Args:
            data: Data stored as a ctypes object (length must be a multiple of 4 bytes)
        """
        dataLength = sizeof(data)

        def _hpidWrite():
            """Low-level routine to be wrapped by claimInterfaceWrapper
            """
            self.deviceUsb.handle.bulkWrite(DEFAULT_OUT_ENDPOINT, buffer(data)[:], self.deviceUsb.timeout)
        if 0 != dataLength & 0x3 or 0 == dataLength or 512 < dataLength:
            raise UsbPacketLengthError("Invalid data length %d in hpidWrite" % (dataLength,))
        self.deviceUsb.claimInterfaceWrapper(_hpidWrite)

    def hpiWrite(self, address, data):
        """Write an arbitrary block of data (multiple of 4 bytes) to DSP address.

        A long block is automatically chunked for transfer.

        Args:
            address: (Byte) address in DSP space to write data
            data: A ctypes object containing data. The length must be a multiple of 4 bytes, but can 
                otherwise be arbitrary.
        """
        dataLength = sizeof(data)
        chunkSize = self.deviceUsb.usbMaxPacketSize
        dataAddress = addressof(data)
        while dataLength > chunkSize:
            dataBuffer = (c_ubyte * chunkSize).from_address(dataAddress)
            self.hpiaWrite(address)
            self.hpidWrite(dataBuffer)
            address += chunkSize
            dataAddress += chunkSize
            dataLength -= chunkSize
            time.sleep(0)  # to yield processor when transferring a large block
        if dataLength > 0:
            dataBuffer = (c_ubyte * dataLength).from_address(dataAddress)
            self.hpiaWrite(address)
            self.hpidWrite(dataBuffer)

    def hpidRead(self, result):
        """Read a block of 32-bit words (max length 512 bytes) from HPID

        Use bulk read to get block of 32 bit words (placed in a ctypes object) from HPID.
        The maximum length of the block is 128 32-bit words or 512 bytes. Note that the address
        should previously have been set up.

        Args:
            result: ctypes object to receive data (length must be a multiple of 4 bytes)
        """
        nBytes = sizeof(result)
        if 0 != nBytes & 0x3 or 0 >= nBytes or 512 < nBytes:
            raise UsbPacketLengthError("Invalid data length %d in hpidRead" % (nBytes,))

        def _hpidRead():
            """Low-level routine to be wrapped by claimInterfaceWrapper
            """
            data = c_short(nBytes)
            self.deviceUsb.controlOutTransaction(data, usbdefs.VENDOR_SET_HPID_IN_BYTES)
            temp = self.deviceUsb.handle.bulkRead(DEFAULT_IN_ENDPOINT, nBytes, self.deviceUsb.timeout)
            memmove(addressof(result), temp, nBytes)

        self.deviceUsb.claimInterfaceWrapper(_hpidRead)

    def hpiRead(self, address, data):
        """Read an arbitrary block of data (multiple of 4 bytes) from a DSP address.

        A long block is automatically chunked for transfer.

        Args:
            address: (Byte) address in DSP space to read data
            data: A ctypes object to contain the data. The length must be a multiple of 4 bytes, but can 
                otherwise be arbitrary.
        """
        dataLength = sizeof(data)
        chunkSize = self.deviceUsb.usbMaxPacketSize
        dataAddress = addressof(data)
        while dataLength > chunkSize:
            dataBuffer = (c_ubyte * chunkSize).from_address(dataAddress)
            self.hpiaWrite(address)
            self.hpidRead(dataBuffer)
            address += chunkSize
            dataAddress += chunkSize
            dataLength -= chunkSize
            time.sleep(0)  # to yield processor when transferring a large block
        if dataLength > 0:
            dataBuffer = (c_ubyte * dataLength).from_address(dataAddress)
            self.hpiaWrite(address)
            self.hpidRead(dataBuffer)

    def resetHpidInFifo(self):
        """Reset HPID input FIFO.
        """
        def _resetHpidInFifo():
            """Low-level routine to be wrapped by claimInterfaceWrapper
            """
            result = c_ubyte(0x0)
            self.deviceUsb.controlInTransaction(
                result, usbdefs.VENDOR_RESET_HPID_IN_FIFO)
            if result.value != 1:
                raise ValueError("Invalid response in resetHpidInFifo")
        self.deviceUsb.claimInterfaceWrapper(_resetHpidInFifo)

    def initEmif(self):
        """Initializes EMIF on DSP using HPI interface
        """
        def writeMem(addr, value):
            """Write value as 32-bit word to DSP address

            Args:
                addr: Address at which to write value
                value: Integer to be written as a 32-bit quantity
            """
            self.hpiWrite(addr, c_int(value))

        self.hpicWrite(0x00010001)
        writeMem(EMIF_GCTL, 0x00000060)     # Disable CLKOUT2 signal
        writeMem(EMIF_CE0, 0xffffbf33)      # CE0 SDRAM
        writeMem(EMIF_CE1, 0x02208802)      # CE1 Flash 8-bit
        writeMem(EMIF_CE2, 0x22a28a22)      # CE2 Daughtercard 32-bit async
        writeMem(EMIF_CE3, 0x22a28a22)      # CE3 Daughtercard 32-bit async
        writeMem(EMIF_SDRAMCTL, 0x57115000)  # SDRAM control (16 Mb)
        writeMem(EMIF_SDRAMTIM, 0x00000578)  # SDRAM timing (refresh)
        writeMem(EMIF_SDRAMEXT, 0x000a8529)  # SDRAM Extension register
        writeMem(CHIP_DEVCFG, 0x13)          # Chip configuration register

    def initPll(self):
        """Initialize the DSP phase-locked loop
        """
        def writeMem(addr, value):
            """Write value as 32-bit word to DSP address

            Args:
                addr: Address at which to write value
                value: Integer to be written as a 32-bit quantity
            """
            self.hpiWrite(addr, c_int(value))

        def readMem(addr):
            """Read a 32-bit word from DSP address

            Args:
                addr: Address at which to write value
                value: Integer to be written as a 32-bit quantity
            """
            result = c_int(0)
            self.hpiRead(addr, result)
            return result.value

        self.hpicWrite(0x00010001)
        # When PLLEN is off DSP is running with CLKIN clock
        #   source, currently 50MHz or 20ns clk rate.
        writeMem(PLL_CSR, readMem(PLL_CSR) & ~CSR_PLLEN)

        # Reset the pll.  PLL takes 125ns to reset.
        writeMem(PLL_CSR, readMem(PLL_CSR) | CSR_PLLRST)

        # PLLOUT = CLKIN/(DIV0+1) * PLLM
        # 450    = 50/1 * 9

        writeMem(PLL_DIV0, DIV_ENABLE + 0)
        writeMem(PLL_MULT, 9)
        writeMem(PLL_OSCDIV1,0) # Disable 10MHz CLKOUT3

        # Program in reverse order.
        # DSP requires that pheripheral clocks be less then
        # 1/2 the CPU clock at all times.

        writeMem(PLL_DIV3, DIV_ENABLE + 4)
        writeMem(PLL_DIV2, DIV_ENABLE + 3)
        writeMem(PLL_DIV1, DIV_ENABLE + 1)
        writeMem(PLL_CSR, readMem(PLL_CSR) & ~CSR_PLLRST)

        # Now enable pll path and we are off and running at
        # 225MHz with 90 MHz SDRAM.
        writeMem(PLL_CSR, readMem(PLL_CSR) | CSR_PLLEN)

    def loadDspFile(self, fileName):
        """Use the HPI to send a file to the DSP
        """
        with file(fileName, "r") as dspFp:
            hexFile = HexFile(dspFp)
            regions = hexFile.process()
        for region in regions:
            # region.data contains the data as a list of bytes.
            self.hpiWrite(
                region.address, create_string_buffer("".join(region.data), len(region.data)))

    def program(self, fileName):
        """Initialize DSP and external memory interface, then send DSP program.
        """
        self.initPll()
        self.initEmif()
        #raw_input("Press <Enter> to download DSP code")
        self.loadDspFile(fileName)
        self.hpicWrite(0x00010001)
        #raw_input("DSP code downloaded. Press <Enter> to send DSPINT")
        self.hpicWrite(0x00010003)
        # print "hpic after DSPINT: %08x" % self.analyzerUsb.hpicRead()
        time.sleep(0.5)
        #raw_input("DSPINT sent. Press <Enter> to continue")
        self.hpicWrite(0x00010001)
