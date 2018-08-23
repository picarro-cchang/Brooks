#!/usr/bin/python
"""
FILE:
  AuxAccessor.py

DESCRIPTION:
  Low level interface to auxiliary (electrical interface) board

SEE ALSO:
  Specify any related information.

HISTORY:
  29-Nov-2013  sze  Extracted from analyzerUsbIf

 Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
from ctypes import Array, c_ubyte, c_ushort, create_string_buffer, sizeof
import struct
from Host.autogen import usbdefs
from Host.Common.SharedTypes import UsbPacketLengthError

USB_ENDPOINT_IN = 0x80
USB_ENDPOINT_OUT = 0x00

AUXILIARY_OUT_ENDPOINT = USB_ENDPOINT_OUT | 4
AUXILIARY_IN_ENDPOINT = USB_ENDPOINT_IN | 8

def usbLockProtect(func):
    """Decorator for serializing USB access.
    
    Uses usbLock to serialize calls to func from different threads.
    """
    def wrapper(self, *a, **k):
        """Wrapper for usbLockProtect
        """
        self.deviceUsb.usbLock.acquire()
        try:
            return func(self, *a, **k)
        finally:
            self.deviceUsb.usbLock.release()
    return wrapper

class AuxAccessor(object):
    """Access the auxiliary (electrical interface) board via the Cypress USB Controller.

    Args:
      deviceUsb: Instance of an AnalyzerUsb object
    """
    def __init__(self, deviceUsb):
        self.deviceUsb = deviceUsb

    @usbLockProtect
    def wrAuxiliary(self, data):
        """Send block of data to auxiliary board.
        Args:
            data: ctypes object containing block of 16-bit words
        """
        assert isinstance(data, Array)
        dataLength = sizeof(data)
        def _wrAuxiliary():
            """Low-level function to be wrapped.
            """
            self.deviceUsb.handle.bulkWrite(
                AUXILIARY_OUT_ENDPOINT, buffer(data)[:], 5000)

        if 0 == dataLength or 512 < dataLength:
            raise UsbPacketLengthError(
                "Invalid data length %d in auxiliaryWrite" % (dataLength,))
        self.deviceUsb.claimInterfaceWrapper(_wrAuxiliary)

    @usbLockProtect
    def wrDac(self, channel, value):
        """Write to DAC on auxiliary board.
        Args:
            channel: DAC channel to write to
            value: 16-bit value to write
        """
        assert isinstance(channel, int)
        assert isinstance(value, int)
        def _wrDac():
            """Low-level function to be wrapped.
            """
            self.deviceUsb.controlOutTransaction(create_string_buffer(
                struct.pack(">H", value), 2), usbdefs.VENDOR_SET_DAC, channel)
        self.deviceUsb.claimInterfaceWrapper(_wrDac)

    @usbLockProtect
    def resetDacQueue(self):
        """Reset DAC queue and clear error flags.
        """
        def _resetDacQueue():
            """Low-level function to be wrapped.
            """
            self.deviceUsb.controlOutTransaction(c_ubyte(0),
                                       usbdefs.VENDOR_DAC_QUEUE_CONTROL, usbdefs.DAC_QUEUE_RESET)
        self.deviceUsb.claimInterfaceWrapper(_resetDacQueue)

    @usbLockProtect
    def setDacTimestamp(self, timestamp):
        """Set DAC timestamp (resolution = 10ms).
        Args:
            timestamp: Timestamp to write
        """
        timestamp = int(timestamp)
        if timestamp < 0 or timestamp >= 65536:
            raise ValueError('Only timestamps in range 0..65535 are valid')

        def _setDacTimestamp():
            """Low-level function to be wrapped.
            """
            data = (c_ushort)(timestamp)
            self.deviceUsb.controlOutTransaction(data,
                                       usbdefs.VENDOR_DAC_QUEUE_CONTROL, usbdefs.DAC_SET_TIMESTAMP)
        self.deviceUsb.claimInterfaceWrapper(_setDacTimestamp)

    @usbLockProtect
    def setDacReloadCount(self, reloadCount):
        """Sets DAC timestamp clock divsor.
        Args:
            reloadCount: Value used to reload counter (65536 - divisor)
        """
        assert isinstance(reloadCount, int)
        if reloadCount < 0 or reloadCount >= 65536:
            raise ValueError('Only reloadCount in range 0..65535 are valid')

        def _setDacReloadCount():
            """Low-level function to be wrapped.
            """
            data = (c_ushort)(reloadCount)
            self.deviceUsb.controlOutTransaction(data,
                                       usbdefs.VENDOR_DAC_QUEUE_CONTROL, usbdefs.DAC_SET_RELOAD_COUNT)
        self.deviceUsb.claimInterfaceWrapper(_setDacReloadCount)

    @usbLockProtect
    def getDacTimestamp(self):
        """Gets current value of DAC timestamp.
        Returns:
            DAC timestamp (10ms resolution)
        """
        def _getDacTimestamp():
            """Low-level function to be wrapped.
            """
            data = (c_ushort)(0)
            self.deviceUsb.controlInTransaction(
                data, usbdefs.VENDOR_DAC_QUEUE_STATUS, usbdefs.DAC_GET_TIMESTAMP)
            return data.value
        return self.deviceUsb.claimInterfaceWrapper(_getDacTimestamp)

    @usbLockProtect
    def getDacReloadCount(self):
        """Gets DAC timestamp clock divisor reload count.
        
        Retuns: reload count (65536 - divisor)
        """
        def _getDacReloadCount():
            """Low-level function to be wrapped.
            """
            data = (c_ushort)(0)
            self.deviceUsb.controlInTransaction(
                data, usbdefs.VENDOR_DAC_QUEUE_STATUS, usbdefs.DAC_GET_RELOAD_COUNT)
            return data.value
        return self.deviceUsb.claimInterfaceWrapper(_getDacReloadCount)

    @usbLockProtect
    def getDacQueueFree(self):
        """Get number of bytes available in DAC queue.

        Retuns: Number of bytes available
        """
        def _getDacQueueFree():
            """Low-level function to be wrapped.
            """
            data = (c_ushort)(0)
            self.deviceUsb.controlInTransaction(
                data, usbdefs.VENDOR_DAC_QUEUE_STATUS, usbdefs.DAC_QUEUE_GET_FREE)
            return data.value
        return self.deviceUsb.claimInterfaceWrapper(_getDacQueueFree)

    @usbLockProtect
    def getDacQueueErrors(self):
        """Get error bit mask for DAC queue.

        Retuns: Error bit mask (DAC_QUEUE_OVERFLOW, DAC_QUEUE_UNDERFLOW)

        """
        def _getDacQueueErrors():
            """Low-level function to be wrapped.
            """
            errors = c_ubyte()
            self.deviceUsb.controlInTransaction(
                errors, usbdefs.VENDOR_DAC_QUEUE_STATUS, usbdefs.DAC_QUEUE_GET_ERRORS)
            return errors.value
        return self.deviceUsb.claimInterfaceWrapper(_getDacQueueErrors)

    @usbLockProtect
    def enqueueDacSamples(self, data):
        """Enqueue block of 16-bit words to write to DAC on auxiliary board.
        
        Args:
            data: ctypes object containing words to write
        """
        assert isinstance(data, Array)
        dataLength = sizeof(data)
        def _enqueueDacSamples():
            """Low-level function to be wrapped.
            """
            self.deviceUsb.controlOutTransaction(data, usbdefs.VENDOR_DAC_ENQUEUE_DATA)
        if 0 == dataLength or 64 < dataLength:
            raise UsbPacketLengthError(
                "Invalid data length %d in enqueueDacSamples" % (dataLength,))
        return self.deviceUsb.claimInterfaceWrapper(_enqueueDacSamples)
