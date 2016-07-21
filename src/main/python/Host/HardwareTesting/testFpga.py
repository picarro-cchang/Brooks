import logging
import unittest
import sys
from Host.autogen import usbdefs, interface
from Host.Common.analyzerUsbIf import AnalyzerUsb
from Host.Common.FpgaProgrammer import FpgaProgrammer
from ctypes import c_byte, c_uint, c_int, c_ushort, c_short, sizeof
from time import sleep, time

usbFile  = "../../Firmware/CypressUSB/analyzer/analyzerUsb.hex"
fpgaFile = "../../Firmware/MyHDL/Spartan3/top_io_map.bit"

analyzerUsb = None

def loadUsbIfCode():
    global analyzerUsb
    analyzerUsb = AnalyzerUsb(usbdefs.INITIAL_VID,usbdefs.INITIAL_PID)
    try: # connecting to a blank FX2 chip
        analyzerUsb.connect()
        logging.info("Downloading USB code to Cypress FX2")
        analyzerUsb.loadHexFile(usbFile)
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
    fpgaProgrammer = FpgaProgrammer(analyzerUsb, logging.info)
    fpgaProgrammer.program(fpgaFile)
