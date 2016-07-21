import unittest
import logging
import sys
from Host.autogen import usbdefs
from Host.Common.analyzerUsbIf import AnalyzerUsb
from ctypes import c_byte, c_uint, c_int, c_ushort, c_short, sizeof
from time import sleep, clock

usbFile = "../../CypressUSB/analyzer/analyzerUsb.hex"

class TestVendorCommands(unittest.TestCase):
    def setUp(self):
        self.analyzerUsb = AnalyzerUsb(usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        self.analyzerUsb.connect()
    def testGetVersion(self):
        ver = self.analyzerUsb.getUsbVersion()
        self.assertEqual(ver,usbdefs.USB_VERSION)
    def testClaimInterface(self):
        self.analyzerUsb.getUsbVersion()
        self.assertEqual(self.analyzerUsb.interfaceClaimed,not self.analyzerUsb.CLAIM_PER_USE)
    def tearDown(self):
        self.analyzerUsb.disconnect()
        self.assertFalse(self.analyzerUsb.interfaceClaimed)
        self.assertEqual(self.analyzerUsb.handle,None)

def loadUsbIfCode():
    analyzerUsb = AnalyzerUsb(usbdefs.INITIAL_VID,usbdefs.INITIAL_PID)
    try: # connecting to a blank FX2 chip
        analyzerUsb.connect()
    except: # Assume code has already been loaded
        logging.info("No blank Cypress FX2 detected, assuming already programmed.")
        return
    logging.info("Downloading USB code to Cypress FX2")
    analyzerUsb.loadHexFile(usbFile)
    analyzerUsb.disconnect()
    # Wait for renumeration
    while True:
        analyzerUsb = AnalyzerUsb(usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        try:
            analyzerUsb.connect()
            break
        except:
            sleep(1.0)
    logging.info("After download, USB high-speed mode: %d" % (analyzerUsb.getUsbSpeed(),))
    analyzerUsb.disconnect()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loadUsbIfCode()
    unittest.main()

