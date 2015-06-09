#!/usr/bin/python
#
# FILE:
#   usbTransferTests.py
#
# DESCRIPTION:
#   Test how low it takes to read data from the Logic Board via the USB port
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   26-Nov-2013  sze  Initial coding
#
#  Copyright (c) 2013 Picarro, Inc. All rights reserved
#

import configobj
import ctypes
from optparse import OptionParser
import os
import sys
import time

from Host.Driver.DasConfigure import DasConfigure
from Host.Common import hostDasInterface
from InstrumentConfig import InstrumentConfig

if hasattr(sys, "frozen"):  # we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]


class UsbTransferTests (object):

    def __init__(self, configFile):
        self.config = configobj.ConfigObj(configFile)
        basePath = os.path.split(configFile)[0]
        self.stateDbFile = os.path.join(basePath, self.config["Files"]["instrStateFileName"])
        self.instrConfigFile = os.path.join(basePath, self.config["Files"]["instrConfigFileName"])
        self.usbFile = os.path.join(basePath, self.config["Files"]["usbFileName"])
        self.dspFile = os.path.join(basePath, self.config["Files"]["dspFileName"])
        self.fpgaFile = os.path.join(basePath, self.config["Files"]["fpgaFileName"])
        self.dasInterface = hostDasInterface.DasInterface(self.stateDbFile, self.usbFile, self.dspFile, self.fpgaFile, False)

    def run(self):
        try:
            try:
                usbSpeed = self.dasInterface.startUsb()
                print "USB enumerated at %s speed" % (("full", "high")[usbSpeed])
                self.dasInterface.programAll()
                time.sleep(1.0)  # For DSP code to initialize
                # Restore state from INI file
                ic = InstrumentConfig(self.instrConfigFile)
                ic.loadPersistentRegistersFromConfig()
                # self.dasInterface.loadDasState() # Restore DAS state
                print "Configuring scheduler"
                DasConfigure(self.dasInterface, ic.config, self.config).run()
                usb = self.dasInterface.analyzerUsb
                # Perform some USB transfers and time them
                byte16Array = (ctypes.c_byte * 16)()
                start = time.time()
                for _ in range(100):
                    usb.hpiRead(hostDasInterface.SENSOR_BASE, byte16Array)
                print "Time to read 16 element byte array %f ms" % (1000.0 * ((time.time() - start) / 100.0),)
                byte256Array = (ctypes.c_byte * 256)()
                for _ in range(100):
                    usb.hpiRead(hostDasInterface.SENSOR_BASE, byte256Array)
                print "Time to read 256 element byte array %f ms" % (1000.0 * ((time.time() - start) / 100.0),)
                byte4096Array = (ctypes.c_byte * 4096)()
                for _ in range(100):
                    usb.hpiRead(hostDasInterface.SENSOR_BASE, byte4096Array)
                print "Time to read 4096 element byte array %f ms" % (1000.0 * ((time.time() - start) / 100.0),)
            finally:
                pass
        finally:
            pass


def handleCommandSwitches():
    parser = OptionParser()
    defaultConfig = os.path.join(os.path.dirname(AppPath), "Driver.ini")
    parser.add_option("-c", dest="configFile", default=defaultConfig, help="Configuration file [%s]" % defaultConfig)
    return parser.parse_args()

if __name__ == "__main__":
    options, args = handleCommandSwitches()
    utt = UsbTransferTests(options.configFile)
    utt.run()

# Initial test results:
# Time to read 16 element byte array 0.879796 ms = 55.0 us/byte
# Time to read 256 element byte array 4.517244 ms = 17.6 us/byte
# Time to read 4096 element byte array 61.379809 ms = 14.99us/byte

# Changed MAX_PACKET_SIZE to 512:
# Time to read 16 element byte array 0.879869 ms = 55.0 us/byte
# Time to read 256 element byte array 1.768613 ms = 6.9 us/byte
# Time to read 4096 element byte array 8.784720 ms = 2.1 us/byte