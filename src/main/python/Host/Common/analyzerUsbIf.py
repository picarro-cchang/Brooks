#!/usr/bin/python
"""
FILE:
  analyzerUsbIf.py

DESCRIPTION:
  Interface to USB FX2 firmware for Picarro gas analyzer

SEE ALSO:
  Specify any related information.

HISTORY:
  07-May-2008  sze  Initial version.
  28-Sep-2010  sze  Set CLAIM_PER_USE to False in Windows to be consistent with Linux.
                    This requires us to reset the USB interface if we cannot claim it.
  04-Oct-2013  sze  Compatibility with libusb-1.0
  15-Dec-2013  sze  Corrected position of USB_MAX_PACKET_SIZE global which was causing the
                     wrong packet size (64 bytes instead of 512 bytes) to be used.

 Copyright (c) 2008 Picarro, Inc. All rights reserved
"""
from sys import platform
import usb1
import libusb1

from ctypes import create_string_buffer, c_ubyte, c_ushort, memmove, sizeof, addressof

from Host.Common.hexfile import HexFile
from Host.autogen import usbdefs
from Host.Common.SharedTypes import Singleton
from Host.Common.SharedTypes import ClaimInterfaceError, UsbConnectionError, UsbPacketLengthError
import struct
import threading
import time


class AnalyzerUsb(Singleton):
    """Represents USB connection between host and analyzer at specified VID and PID.

    Args:
        vid: Vendor ID of USB device
        pid: Product ID of USB device
        timeout: Timeout (ms) for synchronous calls to USB
    """

    def __init__(self, vid, pid, timeout=5000):
        self.context = usb1.USBContext()
        self.device = None
        self.handle = None
        self.vid = vid
        self.pid = pid
        self.timeout = timeout
        self._usbLock = threading.RLock()
        self.usbMaxPacketSize = 64
        self.interfaceClaimed = False
        if platform == "linux2":
            self.CLAIM_PER_USE = False
        elif platform == "win32":
            # self.CLAIM_PER_USE = True
            self.CLAIM_PER_USE = False

    @property
    def usbLock(self):
        """Used to restrict access to the USB interface to a single thread.

        This is used by higher-level functions to control access to groups of USB calls
        """
        return self._usbLock

    def connect(self, claim=True):
        """Connect to the specified USB device.

        The actual low-level connection is done by _connect. This function wraps _connect so that
            it is retried, if it does not at first succeed.

        Args:
            claim: Whether to claim interface. Under Linux, an unprogrammed Cypress device hangs if 
                we try to claim the interface.
        """
    def connect(self, claim = True):
        def _connect():
            """Low-level connect to USB.
            """
            self.checkHandleAndClose()
            self.device = self.context.getByVendorIDAndProductID(self.vid, self.pid)
            if self.device is None:
                raise UsbConnectionError(
                    "Cannot connect to device with VID: 0x%x, PID: 0x%x" % (self.vid, self.pid))
            self.handle = self.device.open()
            if claim:
                self.handle.setConfiguration(1)

        _connect()
        # Try to claim interface, retrying once more if it initially fails
        if claim:
            try:
                self.handle.claimInterface(0)
            except libusb1.USBError:
                self.handle.resetDevice()
                time.sleep(2.0)
                _connect()
                self.handle.claimInterface(0)
            self.interfaceClaimed = True

    def controlInTransaction(self, var, cmd, value=0, index=0):
        """Performs a control transfer from the USB device to the host.

        Args:
            var: ctypes object into which result is to be placed. (Size of this 
                determines number of bytes to transfer)
            cmd: Command identifying transfer type
            value: Parameter for transfer
            index: Parameter for transfer

        Raises:
            UsbPacketLengthError: If bytes transferred does not match size of var
            libusb1.USBError: On low-level USB error (e.g. timeout)
        """
        sv = sizeof(var)
        result = self.handle.controlRead(0xC0, cmd, value, index, sv, self.timeout)
        if len(result) != sv:
            raise UsbPacketLengthError(
                "Unexpected packet length %d [%d] in controlIn transaction 0x%2x" % (len(result), sv, cmd))
        memmove(addressof(var), result, sv)

    def controlOutTransaction(self, msg, cmd, value=0, index=0):
        """Performs a control transfer from the host to the USB device.

        Args:
            msg: ctypes object containing data to send to be device. (Size of this 
                determines number of bytes to transfer)
            cmd: Command identifying transfer type
            value: Parameter for transfer
            index: Parameter for transfer
            timeout: Timeout in ms

        Raises:
            UsbPacketLengthError: If bytes transferred does not match size of msg
            libusb1.USBError: On low-level USB error (e.g. timeout)
        """
        sm = sizeof(msg)
        actual = self.handle.controlWrite(0x40, cmd, value, index, buffer(msg)[:], self.timeout)
        if actual != sm:
            raise UsbPacketLengthError(
                "Unexpected packet length %d [%d] in controlOut transaction 0x%2x" % (actual, sm, cmd))

    def controlOutBlock(self, cmd, address, data):
        """Performs a control transfer of a big block of data to the USB device.

            Calls controlOutTransaction repeatedly as needed to send the block in chunks. Typically
                used when programming the FPGA via USB.

        Args:
            cmd: Command identifying transfer type
            address: Used to identify bytes sent in payload. The start address of each block
                of the payload is sent as the value parameter to the underlying controlOutTransaction
            data: The payload to send as a ctypes object. This is broken up into chunks as needed.
        """
        dataLength = sizeof(data)
        chunkSize = self.usbMaxPacketSize
        a = addressof(data)
        while dataLength > chunkSize:
            dataBuffer = (c_ubyte * chunkSize).from_address(a)
            self.controlOutTransaction(dataBuffer, cmd, address)
            address += chunkSize
            a += chunkSize
            dataLength -= chunkSize
            time.sleep(0)  # to yield processor when transferring a large block
        if dataLength > 0:
            dataBuffer = (c_ubyte * dataLength).from_address(a)
            self.controlOutTransaction(dataBuffer, cmd, address)

    def loadHexFile(self, fileName):
        """Use vendor command to load hex file to USB controller and renumerate.

        Args:
            fileName: Name of hex file to send to USB controller
        """
        def _loadHexFile():
            """Low-level routine to load hex file to USB controller and renumerate.
            """
            # Hold the 8051 in reset during download
            self.controlOutTransaction(c_ubyte(0x1), 0xA0, 0xE600)

            with file(fileName, "r") as fp:
                # Use the vendor command to download the hexadecimal data
                hexFile = HexFile(fp)
                regions = hexFile.process()

                for r in regions:
                    # r.data contains the data as a list of bytes.
                    self.controlOutBlock(
                        0xA0, r.address, create_string_buffer("".join(r.data), len(r.data)))

            # Release the reset to renumerate
            self.controlOutTransaction(c_ubyte(0x0), 0xA0, 0xE600)
            self.disconnect()
        # Do not wrap function, since it disconnects on completion
        return _loadHexFile()

    def checkHandleAndClose(self):
        """Close USB connection.
        """
        if self.handle != None:
            try:
                self.handle.close()
            except Exception as e:
                raise UsbConnectionError("Error %s while closing USB" % (e,))
            self.handle = None

    def disconnect(self):
        """Release interface and close USB connection.
        """
        if self.interfaceClaimed:
            try:
                self.handle.releaseInterface(0)
            except Exception as e:
                raise ClaimInterfaceError(
                    "Error %s while releasing interface" % (e,))
            self.interfaceClaimed = False
        self.checkHandleAndClose()


    def claimInterfaceWrapper(self, func, *args, **kwargs):
        """Wraps function call between claim interface and release interface.

        Do not use with unprogrammed Cypress device in Linux

        Args:
            func: USB access function to wrap
            args: Positional arguments for func
            kwargs: Keyword arguments for func

        Returns:
            Result of calling func

        Raises:
            ClaimInterfaceError: If claim or release fail.
            Any exception that can be raised by func.
        """
        if not self.interfaceClaimed:
            try:
                self.handle.claimInterface(0)
            except Exception as e:
                raise ClaimInterfaceError(
                    "Error %s while claiming interface for %s" % (e, func.__name__))
            self.interfaceClaimed = True
        try:
            return func(*args, **kwargs)
        finally:
            if self.CLAIM_PER_USE:
                try:
                    self.handle.releaseInterface(0)
                except Exception as e:
                    raise ClaimInterfaceError(
                        "Error %s while releasing interface for %s" % (e, func.__name__))
                self.interfaceClaimed = False

    def getUsbVersion(self):
        """Gets version number of the USB software.

        Performs VENDOR_GET_VERSION command using controlInTransaction.
        """
        def _getUsbVersion():
            """Low-level function wrapped by claimInterfaceWrapper.
            """
            version = c_ushort()
            self.controlInTransaction(version, usbdefs.VENDOR_GET_VERSION)
            return version.value
        return self.claimInterfaceWrapper(_getUsbVersion)

    def getUsbSpeed(self):
        """Returns if USB has enumerated in high-speed mode (True) or full-speed mode (False).
            Also sets up usbMaxPacketSize."""
        def _getUsbSpeed():
            speed = c_ubyte()
            self.controlInTransaction(
                speed, usbdefs.VENDOR_GET_STATUS, usbdefs.USB_STATUS_SPEED)
            self.usbMaxPacketSize = 512 if speed.value else 64
            return speed.value
        return self.claimInterfaceWrapper(_getUsbSpeed)

    def setDspControl(self, value):
        """Use vendor command to reset DSP or send HINT"""
        def _setDspControl():
            result = c_ubyte(0)
            self.controlInTransaction(
                result, usbdefs.VENDOR_DSP_CONTROL, value)
            if result.value != value:
                raise ValueError("Invalid response in setDspControl")
        self.claimInterfaceWrapper(_setDspControl)

