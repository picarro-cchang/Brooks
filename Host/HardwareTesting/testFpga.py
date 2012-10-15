import logging
import unittest
import sys
from Host.autogen import usbdefs, interface
from Host.Common.analyzerUsbIf import AnalyzerUsb
from ctypes import c_byte, c_uint, c_int, c_ushort, c_short, sizeof
from time import sleep, clock

usbFile  = "../../Firmware/CypressUSB/analyzer/analyzerUsb.hex"
fpgaFile = "../../Firmware/MyHDL/Spartan3/top_io_map.bit"

analyzerUsb = None

def loadUsbIfCode():
    global analyzerUsb
    analyzerUsb = AnalyzerUsb(usbdefs.INITIAL_VID,usbdefs.INITIAL_PID)
    try: # connecting to a blank FX2 chip
        analyzerUsb.connect()
        logging.info("Downloading USB code to Cypress FX2")
        analyzerUsb.loadHexFile(file(usbFile,"r"))
        analyzerUsb.disconnect()
    except: # Assume code has already been loaded
        logging.info("Cypress FX2 is not blank")
    # Wait for renumeration
    while True:
        analyzerUsb = AnalyzerUsb(usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        try:
            analyzerUsb.connect()
            break
        except:
            sleep(1.0)

def programFPGA():
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

RDMEM_BASE = 0xA0000000
FPGA_REG_MULT = 4

def readFPGA(analyzerUsb,offset):
    analyzerUsb.hpiaWrite(interface.FPGA_REG_BASE_ADDRESS+FPGA_REG_MULT*offset)
    result = c_uint(0)
    analyzerUsb.hpidRead(result)
    return result.value
def writeFPGA(analyzerUsb,offset,value):
    analyzerUsb.hpiaWrite(interface.FPGA_REG_BASE_ADDRESS+FPGA_REG_MULT*offset)
    analyzerUsb.hpidWrite(c_uint(value))
def rdRingdownMemArray(analyzerUsb,offset,nwords=1):
    """Reads multiple words from ringdown memory into a c_uint array"""
    analyzerUsb.hpiaWrite(RDMEM_BASE+offset)
    result = (c_uint*nwords)()
    analyzerUsb.hpidRead(result)
    return result
def rdRingdownMem(analyzerUsb,offset):
    """Reads single uint from ringdown memory"""
    analyzerUsb.hpiaWrite(RDMEM_BASE+offset)
    result = c_uint(0)
    analyzerUsb.hpidRead(result)
    return result.value
def wrRingdownMem(analyzerUsb,offset,value):
    """Reads single uint value to ringdown memory"""
    analyzerUsb.hpiaWrite(RDMEM_BASE+offset)
    result = c_uint(value)
    analyzerUsb.hpidWrite(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Loading USB code")
    loadUsbIfCode()
    programFPGA()
