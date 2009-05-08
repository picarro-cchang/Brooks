import logging
import unittest
import sys
from Host.autogen import usbdefs
from Host.Common.analyzerUsbIf import AnalyzerUsb
from ctypes import c_byte, c_uint, c_int, c_ushort, c_short, sizeof
from time import sleep, clock

usbFile  = "../../CypressUSB/analyzer/analyzerUsb.hex"
fpgaFile = "../../MyHDL/Spartan3/top_io_map.bit"
#usbFile  = "C:/work/CostReducedPlatform/Software/CypressUSB/analyzer/analyzerUsb.hex"
#fpgaFile = "C:/work/CostReducedPlatform/Software/FPGA/SpartanStarter/top_io_map.bit"

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
        logging.info("Cypress FX2 is not blank")
        return
    logging.info("Downloading USB code to Cypress FX2")
    analyzerUsb.loadHexFile(file(usbFile,"r"))
    analyzerUsb.disconnect()
    # Wait for renumeration
    while True:
        analyzerUsb = AnalyzerUsb(usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        try:
            analyzerUsb.connect()
            break
        except:
            sleep(1.0)
    analyzerUsb.disconnect()

def programFPGA():
    analyzerUsb = AnalyzerUsb(usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
    analyzerUsb.connect()
    analyzerUsb.resetHpidInFifo()
    logging.info("Holding DSP in reset...")
    analyzerUsb.setDspControl(usbdefs.VENDOR_DSP_CONTROL_RESET)
    logging.info("Starting to program FPGA...")
    logging.info(
        "USB high-speed mode: %d" % (analyzerUsb.getUsbSpeed(),))
    analyzerUsb.startFpgaProgram()
    analyzerUsb.setDspControl(0)
    logging.info("Fpga status: %d" % analyzerUsb.getFpgaStatus())
    while 0 == (1 & analyzerUsb.getFpgaStatus()):
        pass
    fp = file(fpgaFile,"rb")
    s = fp.read(128)
    f = s.find("\xff\xff\xff\xff\xaa\x99\x55\x66")
    if f<0:
        raise ValueError("Invalid FPGA bit file")
    s = s[f:]
    tStart = clock()
    lTot = 0
    while len(s)>0:
        lTot += len(s)
        analyzerUsb.sendToFpga(s)
        s = fp.read(64)
    stat = analyzerUsb.getFpgaStatus()
    if 0 != (2 & analyzerUsb.getFpgaStatus()):
        logging.info("FPGA programming done")
        logging.info("Bytes sent: %d" % lTot)
    elif 0 == (1 & analyzerUsb.getFpgaStatus()):
        logging.error(
            "CRC error during FPGA load, bytes sent: %d" % (lTot,))
    logging.info("Time to load: %.1fs" % (clock() - tStart,))
    sleep(0.2)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Loading USB code")
    loadUsbIfCode()
    programFPGA()
