import logging
import unittest
import sys
from Host.autogen import usbdefs, interface
from Host.Common.analyzerUsbIf import AnalyzerUsb
from ctypes import c_byte, c_uint, c_int, c_ushort, c_short, sizeof
from time import sleep, time
from random import randrange

usbFile  = "../../Firmware/CypressUSB/analyzer/analyzerUsb.hex"
fpgaFile = "../../Firmware/MyHDL/Spartan3/top_io_map.bit"
dspFile  = "../../Firmware/DSP/checkDsp/Debug/checkDsp.hex"

SHAREDMEM_BASE   = interface.SHAREDMEM_ADDRESS
REG_BASE         = interface.SHAREDMEM_ADDRESS
SENSOR_BASE      = interface.SHAREDMEM_ADDRESS + \
                       4*interface.SENSOR_OFFSET
MESSAGE_BASE     = interface.SHAREDMEM_ADDRESS + \
                       4*interface.MESSAGE_OFFSET
GROUP_BASE       = interface.SHAREDMEM_ADDRESS + \
                       4*interface.GROUP_OFFSET
OPERATION_BASE   = interface.SHAREDMEM_ADDRESS + \
                       4*interface.OPERATION_OFFSET
OPERAND_BASE     = interface.SHAREDMEM_ADDRESS + \
                       4*interface.OPERAND_OFFSET
ENVIRONMENT_BASE = interface.SHAREDMEM_ADDRESS + \
                       4*interface.ENVIRONMENT_OFFSET
HOST_BASE        = interface.SHAREDMEM_ADDRESS + \
                       4*interface.HOST_OFFSET

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
    analyzerUsb.resetHpidInFifo()
    logging.info("Holding DSP in reset...")
    analyzerUsb.setDspControl(usbdefs.VENDOR_DSP_CONTROL_RESET)
    logging.info("Starting to program FPGA...")
    logging.info(
        "USB high-speed mode: %d" % (analyzerUsb.getUsbSpeed(),))
    analyzerUsb.startFpgaProgram()
    logging.info("Fpga status: %d" % analyzerUsb.getFpgaStatus())
    while 0 == (1 & analyzerUsb.getFpgaStatus()):
        pass
    fp = file(fpgaFile,"rb")
    s = fp.read(128)
    f = s.find("\xff\xff\xff\xff\xaa\x99\x55\x66")
    if f<0:
        raise ValueError("Invalid FPGA bit file")
    s = s[f:]
    tStart = time()
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
    logging.info("Time to load: %.1fs" % (time() - tStart,))
    sleep(0.2)

def initEmif():
    EMIF_GCTL      = 0x01800000
    EMIF_CE1       = 0x01800004
    EMIF_CE0       = 0x01800008
    EMIF_CE2       = 0x01800010
    EMIF_CE3       = 0x01800014
    EMIF_SDRAMCTL  = 0x01800018
    EMIF_SDRAMTIM  = 0x0180001C
    EMIF_SDRAMEXT  = 0x01800020
    EMIF_CCFG      = 0x01840000     # Cache configuration register
    CHIP_DEVCFG    = 0x019C0200     # Chip configuration register

    def writeMem(addr,value):
        analyzerUsb.hpiaWrite(addr)
        analyzerUsb.hpidWrite(c_int(value))
    analyzerUsb.hpicWrite(0x00010001)
    writeMem(EMIF_GCTL,0x00000068)
    writeMem(EMIF_CE0,0xffffbf33)     # CE0 SDRAM
    writeMem(EMIF_CE1,0x02208802)     # CE1 Flash 8-bit
    writeMem(EMIF_CE2,0x22a28a22)     # CE2 Daughtercard 32-bit async
    writeMem(EMIF_CE3,0x22a28a22)     # CE3 Daughtercard 32-bit async
    writeMem(EMIF_SDRAMCTL,0x57115000) # SDRAM control (16 Mb)
    writeMem(EMIF_SDRAMTIM,0x00000578) # SDRAM timing (refresh)
    writeMem(EMIF_SDRAMEXT,0x000a8529) # SDRAM Extension register
    # Set up ECLK to 90MHz
    writeMem(CHIP_DEVCFG,0x03)         # Chip configuration register

def initPll():
    PLL_BASE_ADDR   = 0x01b7c000
    PLL_PID         = ( PLL_BASE_ADDR + 0x000 )
    PLL_CSR         = ( PLL_BASE_ADDR + 0x100 )
    PLL_MULT        = ( PLL_BASE_ADDR + 0x110 )
    PLL_DIV0        = ( PLL_BASE_ADDR + 0x114 )
    PLL_DIV1        = ( PLL_BASE_ADDR + 0x118 )
    PLL_DIV2        = ( PLL_BASE_ADDR + 0x11C )
    PLL_DIV3        = ( PLL_BASE_ADDR + 0x120 )
    PLL_OSCDIV1     = ( PLL_BASE_ADDR + 0x124 )

    CSR_PLLEN       =   0x00000001
    CSR_PLLPWRDN    =   0x00000002
    CSR_PLLRST      =   0x00000008
    CSR_PLLSTABLE   =   0x00000040
    DIV_ENABLE      =   0x00008000
    def writeMem(addr,value):
        analyzerUsb.hpiaWrite(addr)
        analyzerUsb.hpidWrite(c_int(value))
    def readMem(addr):
        analyzerUsb.hpiaWrite(addr)
        result = c_int(0)
        analyzerUsb.hpidRead(result)
        return result.value

    analyzerUsb.hpicWrite(0x00010001)
    # When PLLEN is off DSP is running with CLKIN clock
    #   source, currently 50MHz or 20ns clk rate.
    writeMem(PLL_CSR,readMem(PLL_CSR) &~CSR_PLLEN)

    # Reset the pll.  PLL takes 125ns to reset.
    writeMem(PLL_CSR,readMem(PLL_CSR) | CSR_PLLRST)

    # PLLOUT = CLKIN/(DIV0+1) * PLLM
    # 450    = 50/1 * 9

    writeMem(PLL_DIV0,DIV_ENABLE + 0)
    writeMem(PLL_MULT,9)
    writeMem(PLL_OSCDIV1,DIV_ENABLE + 4)

    # Program in reverse order.
    # DSP requires that pheripheral clocks be less then
    # 1/2 the CPU clock at all times.

    writeMem(PLL_DIV3,DIV_ENABLE + 4)
    writeMem(PLL_DIV2,DIV_ENABLE + 3)
    writeMem(PLL_DIV1,DIV_ENABLE + 1)
    writeMem(PLL_CSR,readMem(PLL_CSR) & ~CSR_PLLRST)

    # Now enable pll path and we are off and running at
    # 225MHz with 90 MHz SDRAM.
    writeMem(PLL_CSR,readMem(PLL_CSR) | CSR_PLLEN)

def checkRam(startAddr,endAddr,nTrials):
    """Do random memory writes followed by reads to check memory"""
    def writeMem(addr,value):
        analyzerUsb.hpiaWrite(addr)
        analyzerUsb.hpidWrite(c_int(value))
    def readMem(addr):
        analyzerUsb.hpiaWrite(addr)
        result = c_int(0)
        analyzerUsb.hpidRead(result)
        return result.value
    logging.info("Memory test of region %x to %x" % (startAddr,endAddr))
    nErrors = 0
    refData = {}
    for t in range(nTrials):
        while True:
            addr = randrange(startAddr,endAddr) & 0xFFFFFFFC
            if addr>=startAddr: break
        data = randrange(1<<32)
        writeMem(addr,data)
        refData[addr]=data
        if t%1000==0: sys.stderr.write("w")
    print
    for t,addr in enumerate(refData):
        readBack = readMem(addr) & 0xFFFFFFFF
        data = refData[addr]
        if data != readBack:
            logging.error("Address: %8x, Wrote: %8x, Read: %8x" % (addr,data,readBack))
            nErrors += 1
        if t%1000==0: sys.stderr.write("v")
    print
    logging.info("Memory test done: %d trials, %d errors" % (nTrials,nErrors))

def writeRead(addr,value):
    def writeMem(addr,value):
        analyzerUsb.hpiaWrite(addr)
        analyzerUsb.hpidWrite(c_int(value))
    def readMem(addr):
        analyzerUsb.hpiaWrite(addr)
        result = c_int(0)
        analyzerUsb.hpidRead(result)
        return result.value
    raw_input("Writing %x to address %x" % (value,addr))
    writeMem(addr,value)
    raw_input("Reading address %x" % addr)
    result = readMem(addr) & 0xFFFFFFFF
    print "Result: %x" % result

def rdRegUint(reg):
    # Performs a host read of a single unsigned integer from
    #  the software register "reg" which may be specified as
    #  an integer or a string (defined in the interface module).
    analyzerUsb.hpiaWrite(REG_BASE+4*reg)
    data = c_uint(0)
    analyzerUsb.hpidRead(data)
    return data.value

def upload():
    #
    # TODO: Handle errors by returning an error code.
    #  If this routine fails, it is not possible
    #  to continue
    #
    logging.info("Loading USB code")
    loadUsbIfCode()
    #
    analyzerUsb.connect()
    analyzerUsb.resetHpidInFifo()
    logging.info("Holding DSP in reset...")
    analyzerUsb.setDspControl(usbdefs.VENDOR_DSP_CONTROL_RESET)
    logging.info("Starting to program FPGA...")
    programFPGA()
    analyzerUsb.setDspControl(0)
    sleep(0.5)
    logging.info("Removed DSP reset, downloading code...")
    initPll()
    initEmif()

    # Check internal memory. There is 256KB of memory at this stage, since
    #  the L2 cache is not set up until the DSP starts running
    checkRam(0,0x40000,10000)

    # Check SDRAM
    checkRam(0x80000000,0x81000000,10000)

    raw_input("Press <Enter> to download DSP code")
    fp = file(dspFile,"rb")
    analyzerUsb.loadDspFile(fp)
    fp.close()
    analyzerUsb.hpicWrite(0x00010001)
    raw_input("DSP code downloaded. Press <Enter> to send DSPINT")
    analyzerUsb.hpicWrite(0x00010003)
    print "hpic after DSPINT: %08x" % analyzerUsb.hpicRead()
    sleep(0.5)
    logging.info("Starting DSP code...")
    raw_input("DSPINT sent. Press <Enter> to continue")
    analyzerUsb.hpicWrite(0x00010001)
    # Try accessing some memory via HPI
    HOST_BASE = interface.SHAREDMEM_ADDRESS + 4096
    analyzerUsb.hpicWrite(0x00010001)
    analyzerUsb.hpiaWrite(HOST_BASE)
    hostMsg = (c_uint*8)()
    for i in range(len(hostMsg)):
        hostMsg[i] = 5*i
    analyzerUsb.hpidWrite(hostMsg)
    # Read it back
    reply = (c_uint*8)()
    analyzerUsb.hpicWrite(0x00010001)
    analyzerUsb.hpiaWrite(HOST_BASE)
    analyzerUsb.hpidRead(reply)
    for i in range(len(reply)):
        print reply[i]
    # See if we can receive DSPINTs from the host
    for i in range(100):
        print "EXT4 Interrupt count %d" % rdRegUint(13)
        print "HPI Interrupt count %d" % rdRegUint(12)
        analyzerUsb.hpicWrite(0x00010003)
        sleep(0.5)

    # Read back register 11 which should be updated by a PRD
    while True:
        print "EXT4 Interrupt count %d" % rdRegUint(13)
        print "PRD count %d" % rdRegUint(11)
        sleep(0.5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upload()
