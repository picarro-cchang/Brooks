#!/usr/bin/python
#
# FILE:
#   FX2Interface.py
#
# DESCRIPTION:
#   Code which communicates between the Host and the Cypress FX2 board
#    for developing analog output buffering
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
from time import sleep
import logging
from ctypes import byref, c_short, c_int, c_byte
from Host.Common.SharedTypes import Singleton
from Host.Common.analyzerUsbIf  import AnalyzerUsb
from Host.autogen import usbdefs, interface

class FX2Interface(Singleton):
    initialized = False
    def __init__(self,usbFile=None):
        if not self.initialized:
            self.usbFile = usbFile
            self.analyzerUsb = None
            self.initialized = True
    def loadUsbIfCode(self,usbCodeFilename):
        """Downloads file to USB Cypress FX2 chip, if not already downloaded"""
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
        analyzerUsb.loadHexFile(usbCodeFilename)
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
    def startUsb(self):
        self.loadUsbIfCode(self.usbFile)
        self.analyzerUsb = AnalyzerUsb(
            usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        self.analyzerUsb.connect()
        return self.analyzerUsb.getUsbSpeed()

if __name__ == "__main__":
    myFX2 = FX2Interface("../CypressUSB/fx2DevelKit/develKit.hex")
    myFX2.startUsb()
    i = 0
    while True:
        raw_input("Send a byte")
        myFX2.analyzerUsb.auxiliaryWrite(c_byte(i))
        i += 1