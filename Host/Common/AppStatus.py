#!/usr/bin/python
#
# File Name: AppStatus.py
# Purpose:
#   A shared functionality program that is used by CRDS applications for
#   managing application status changes.
#   Broadcasted the status info when changed is included.
#
# Notes:
#   The map for the status information is as follows:
#     - 32 bits long
#     - bits 0->3 (mask = 0xF) are for the 4 bit application state
#        - 15 is reserved for ERROR_STATE
#        - 0 is INIT_STATE
#     - bits 4->30 can be used however you like
#     - MSB not used to avoid +/- issues
#
# ToDo:
#
# File History:
# 06-11-30 russ  First release
# 06-12-04 russ  Added ToggleStatusBit
# 06-12-14 Al    Fixed ToggleStatusBit.  Was using undefined variable, instead of parameter being passed in.

from threading import RLock
import Broadcaster
from StringPickler import ObjAsString
from ctypes import Structure, c_uint

STATUS_STATE_MASK       = 0x0000000F
STATUS_MASK_FULL_LENGTH = 0x7FFFFFFF #avoiding MSB to avoid +/- confusion

class STREAM_Status(Structure):
    _fields_ = [
      ("status",c_uint), #32 bits
    ]

class AppStatus(object):
    def __init__(self, InitialStatus, BroadcastPort, AppName):
        self._Status = InitialStatus
        self._StatusLock = RLock()
        self.StatusBroadcaster = Broadcaster.Broadcaster(BroadcastPort, AppName)
        if __debug__:
            print "Opening status broadcast on port %d" % BroadcastPort

    def __AdjustStatusBit(self, SingleBitMask, BoolVal):
        if BoolVal:
            #Set the bit...
            self._Status |= SingleBitMask
        else:
            #Clear the bit...
            self._Status &= ~SingleBitMask
        #Clear the status down to size...
        self._Status &= STATUS_MASK_FULL_LENGTH

    def _SendStatus(self):
        obj = STREAM_Status()
        obj.status = self._Status
        msg = ObjAsString(obj)
        self.StatusBroadcaster.send(msg)

    def UpdateState(self, State):
        """Updates the status register according to what is given.

        The state must be a number < 15, with 15 reserved for ERROR_STATE.

        On completion of an update the status is broadcasted.

        """
        assert State <= 0xF, "State values must be < 0xF since only 4 bits are allocated."
        self._StatusLock.acquire()
        try:
            oldStatus = self._Status
            self._Status &= ~STATUS_STATE_MASK
            self._Status |= State
            self._Status &= STATUS_MASK_FULL_LENGTH
            if self._Status != oldStatus:
                self._SendStatus()
        finally:
            self._StatusLock.release()

    def UpdateStatusBit(self, BitMaskToUpdate, Value):
        """Updates the status register according to what is given.

        This function assumes that BitMaskToUpdate is a single bit mask for the
        bit to be modified. The bit must also be higher than the bottom 4 bits.

        Value can be anything that will evaluate as a boolean.

        On completion of an update the status is broadcasted.

        """
        assert BitMaskToUpdate > 0xF, "WhatToUpdate must be a bit > the 4 allocated bits for process state."
        self._StatusLock.acquire()
        try:
            oldStatus = self._Status
            self.__AdjustStatusBit(BitMaskToUpdate, Value)
            if self._Status != oldStatus:
                self._SendStatus()
        finally:
            self._StatusLock.release()

    def ToggleStatusBit(self, BitMaskToUpdate):
        """Toggles the given bit to 0 if currently 1 and vice versa.

        This essentially just XORs the status with the provided mask so more than
        one bit can be toggled at a time.

        The bit(s) must be higher than the bottom 4 bits (state) which can't be
        toggled.

        On completion of an update the status is broadcasted.

        """
        assert BitMaskToUpdate > 0xF, "WhatToUpdate must be a bit > the 4 allocated bits for process state."
        self._StatusLock.acquire()
        try:
            oldStatus = self._Status
            self._Status ^= BitMaskToUpdate #xor
            self._SendStatus()
        finally:
            self._StatusLock.release()
