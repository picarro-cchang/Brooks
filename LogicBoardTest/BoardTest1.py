#!/usr/bin/python
#
"""
File Name: BoardTest1.py
Purpose: Tester for Logic Board via USB interface

File History:
    02-Jun-2010  sze  Initial version.

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "BoardTest1"

from ctypes import addressof
from ctypes import c_char, c_byte, c_float, c_int, c_longlong
from ctypes import c_short, c_uint, c_ushort, sizeof, Structure
import getopt
import os
from random import randrange
import sys
import threading
import time

from Host.Common.CustomConfigObj import CustomConfigObj
from Host.autogen import usbdefs, interface
from Host.Common.analyzerUsbIf import AnalyzerUsb

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

def lookup(sym):
    if isinstance(sym,(str,unicode)): sym = getattr(interface,sym)
    return sym
    
def usbLockProtect(f):
    # Decorator for serializing access to the method f from different
    #  threads by using the usbLock
    def wrapper(self,*a,**k):
        self.usbLock.acquire()
        try:
            return f(self,*a,**k)
        finally:
            self.usbLock.release()
    return wrapper

class HostToDspSender(object):
    # Object that keeps track of sequence numbers, and packages
    #  data for host to Dsp communications
    def __init__(self,analyserUsb,timeout):
        self.seqNum = None
        self.usb = analyserUsb
        # Used to ensure only one thread accesses USB at a time
        self.usbLock = threading.RLock()
        self.initStatus = None
        self.timeout = timeout
    @usbLockProtect
    def rdFPGA(self,base,reg):
        # Performs a host read of a single unsigned integer from
        #  the FPGA register which may be specified as
        #  the sum of a block base and the register index
        data = c_uint(0)
        self.usb.hpiRead(interface.FPGA_REG_BASE_ADDRESS+4*(lookup(base)+lookup(reg)),data)
        return data.value
    @usbLockProtect
    def wrFPGA(self,base,reg,value):
        # Performs a host write of a single unsigned integer from
        #  the FPGA register which may be specified as
        #  the sum of a block base and the register index
        self.usb.hpiWrite(interface.FPGA_REG_BASE_ADDRESS+4*(lookup(base)+lookup(reg)),c_uint(value))
    @usbLockProtect
    def writeDspMem(self,addr,data):
        # Write contents of a ctypes object to DSP byte address addr
        return self.usb.hpiWrite(addr,data)
    @usbLockProtect
    def readDspMem(self,addr,data):
        # Read a ctypes object from DSP byte address addr
        return self.usb.hpiRead(addr,data)

        
class BoardTest1(object):
    def __init__(self,configFile):
        self.config = CustomConfigObj(configFile)
        basePath = os.path.split(configFile)[0]
        self.usbFile  = os.path.abspath(os.path.join(basePath, self.config["Files"]["usbFileName"]))
        self.dspFile  = os.path.abspath(os.path.join(basePath, self.config["Files"]["dspFileName"]))
        self.fpgaFile = os.path.abspath(os.path.join(basePath, self.config["Files"]["fpgaFileName"]))
        self.sender = None
        # print self.usbFile, self.dspFile, self.fpgaFile
        # for k in self.__dict__:
        #     print "%20s: %s" % (k,self.__dict__[k])
        
    def loadUsbIfCode(self,usbCodeFilename):
        """Downloads file to USB Cypress FX2 chip, if not already downloaded"""
        analyzerUsb = AnalyzerUsb(usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        try: # connecting to a programmed Picarro instrument
            analyzerUsb.connect()
            analyzerUsb.disconnect()
            print "Detected a programmed Picarro USB interface"
            return
        except:
            try: # connecting to an unprogrammed Picarro instrument
                analyzerUsb = AnalyzerUsb(usbdefs.INITIAL_VID,usbdefs.INITIAL_PID)
                analyzerUsb.connect()
                print "Detected an unprogrammed Picarro USB interface"
            except:
                try: # connecting to a blank Cypress FX2
                    analyzerUsb = AnalyzerUsb(usbdefs.CYPRESS_FX2_VID,usbdefs.CYPRESS_FX2_PID)
                    analyzerUsb.connect()
                    print "Detected an unprogrammed Cypress FX2 device"
                except:
                    raise "Cannot connect to USB"
        print "Downloading Picarro USB code to device"
        analyzerUsb.loadHexFile(file(usbCodeFilename,"r"))
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

    def startUsb(self):
        self.loadUsbIfCode(self.usbFile)
        self.analyzerUsb = AnalyzerUsb(usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        self.analyzerUsb.connect()
        return self.analyzerUsb.getUsbSpeed()
        
    def programFPGA(self,fileName):
        self.analyzerUsb.startFpgaProgram()
        print "Fpga status: %d" % self.analyzerUsb.getFpgaStatus()
        while 0 == (1 & self.analyzerUsb.getFpgaStatus()):
            pass
        fp = file(fileName,"rb")
        s = fp.read(128)
        f = s.find("\xff\xff\xff\xff\xaa\x99\x55\x66")
        if f<0:
            raise ValueError("Invalid FPGA bit file")
        s = s[f:]
        tStart = time.clock()
        lTot = 0
        while len(s)>0:
            lTot += len(s)
            self.analyzerUsb.sendToFpga(s)
            s = fp.read(64)
        stat = self.analyzerUsb.getFpgaStatus()
        if 0 != (2 & self.analyzerUsb.getFpgaStatus()):
            print "FPGA programming done"
            print "Bytes sent: %d" % lTot
        elif 0 == (1 & self.analyzerUsb.getFpgaStatus()):
            print "CRC error during FPGA load, bytes sent: %d" % (lTot,)
        print "Time to load FPGA: %.1fs" % (time.clock() - tStart,)
        time.sleep(0.2)
        
    def initEmif(self):
        """Initializes EMIF on DSP using HPI interface"""
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
            self.analyzerUsb.hpiaWrite(addr)
            self.analyzerUsb.hpidWrite(c_int(value))
        self.analyzerUsb.hpicWrite(0x00010001)
        writeMem(EMIF_GCTL,0x00000068)
        writeMem(EMIF_CE0,0xffffbf33)      # CE0 SDRAM
        writeMem(EMIF_CE1,0x02208802)      # CE1 Flash 8-bit
        writeMem(EMIF_CE2,0x22a28a22)      # CE2 Daughtercard 32-bit async
        writeMem(EMIF_CE3,0x22a28a22)      # CE3 Daughtercard 32-bit async
        writeMem(EMIF_SDRAMCTL,0x57115000) # SDRAM control (16 Mb)
        writeMem(EMIF_SDRAMTIM,0x00000578) # SDRAM timing (refresh)
        writeMem(EMIF_SDRAMEXT,0x000a8529) # SDRAM Extension register
        writeMem(CHIP_DEVCFG,0x13)         # Chip configuration register

    def initPll(self):
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
            self.analyzerUsb.hpiWrite(addr,c_int(value))
        def readMem(addr):
            result = c_int(0)
            self.analyzerUsb.hpiRead(addr,c_int(0))
            return result.value

        self.analyzerUsb.hpicWrite(0x00010001)
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

    def checkRam(self,startAddr,endAddr,nTrials):
        """Do random memory writes followed by reads to check memory"""
        print "Memory test of region %x to %x" % (startAddr,endAddr)
        nErrors = 0
        refData = {}
        for t in range(nTrials):
            while True:
                addr = randrange(startAddr,endAddr) & 0xFFFFFFFC
                if addr>=startAddr: break
            data = randrange(1<<32)
            self.sender.writeDspMem(addr,c_uint(data))
            refData[addr]=data
            if t%1000==0: sys.stderr.write("w")
        print
        for t,addr in enumerate(refData):
            data = c_uint(0)
            self.sender.readDspMem(addr,data)
            readBack = data.value & 0xFFFFFFFF
            data = refData[addr]
            if data != readBack:
                print "Address: %8x, Wrote: %8x, Read: %8x" % (addr,data,readBack)
                nErrors += 1
            if t%1000==0: sys.stderr.write("v")
        print
        print "Memory test done: %d trials, %d errors" % (nTrials,nErrors)
        
    def run(self):
        usbSpeed = self.startUsb()
        print "USB enumerated at %s speed" % (("full","high")[usbSpeed])
        print "Holding DSP in reset while programming FPGA"
        self.analyzerUsb.setDspControl(usbdefs.VENDOR_DSP_CONTROL_RESET)
        self.programFPGA(self.fpgaFile)
        self.analyzerUsb.setDspControl(0)
        time.sleep(0.5)
        print "Removed DSP reset, starting DSP..."
        self.initPll()
        self.initEmif()
        # At this stage we should be able to talk to the FPGA registers
        self.sender = HostToDspSender(self.analyzerUsb,timeout=5) 
        print "Magic code: %x" % self.sender.rdFPGA("FPGA_KERNEL","KERNEL_MAGIC_CODE")

        # Read the output of the high-speed ADC
        self.sender.wrFPGA("FPGA_RDMAN","RDMAN_CONTROL",(1<<interface.RDMAN_CONTROL_RUN_B) | (1<<interface.RDMAN_CONTROL_CONT_B))
        self.sender.wrFPGA("FPGA_RDMAN","RDMAN_OPTIONS",(1<<interface.RDMAN_OPTIONS_SIM_ACTUAL_B))
        
        while True:
            print "Ringdown ADC: %d" % self.sender.rdFPGA("FPGA_RDMAN","RDMAN_RINGDOWN_DATA")
            r = raw_input("q to quit, <Enter> to read again")
            if r and r=="q": break
            
        # Do some reads and writes to DSP memory
        
        # Check internal memory. There is 256KB of memory at this stage, since
        #  the L2 cache is not set up until the DSP starts running
        self.checkRam(0,0x40000,10000)

        # Check SDRAM
        self.checkRam(0x80000000,0x81000000,10000)
        
        self.sender.wrFPGA("FPGA_KERNEL","KERNEL_CONTROL",1<<interface.KERNEL_CONTROL_DOUT_MAN_B)
        
        while True:
            # Read from FPGA digital inputs
            print "FPGA digital in: %08x" % self.sender.rdFPGA("FPGA_KERNEL","KERNEL_DIN")
            # Write to FPGA digital outputs
            x = raw_input("FPGA digital outputs: ")
            if not x.strip(): break
            x = int(eval(x))
            self.sender.wrFPGA("FPGA_KERNEL","KERNEL_DOUT_HI",(x&0xFF00000000)>>32)
            self.sender.wrFPGA("FPGA_KERNEL","KERNEL_DOUT_LO",(x&0xFFFFFFFF))
        
def handleCommandSwitches():
    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/BoardTest1.ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile

if __name__ == "__main__":
    configFile = handleCommandSwitches()
    d = BoardTest1(configFile)
    d.run()
    print "Exiting program"
