from ctypes import cdll, c_uint, c_int, c_float, c_char_p, Union, POINTER, sizeof
from Host.Common.simulatorUsbIf import DataType
import logging
import time
from threading import Thread

class DspSimulator(object):
    def __init__(self,regBase,hostBase):
        self.regBase = regBase
        self.hostBase = hostBase

        dspDll = cdll.LoadLibrary("../../DSP/src/depMainSim.dll")

        #self.writeRegister = dspDll._writeRegister
        #self.writeRegister.argtypes = [c_uint,DataType]
        #self.writeRegister.restype  = c_int

        #self.readRegister = dspDll._readRegister
        #self.readRegister.argtypes = [c_uint,POINTER(DataType)]
        #self.readRegister.restype  = c_int

        #self.writeBlock = dspDll._writeBlock
        #self.writeBlock.argtypes = [c_uint,c_uint,POINTER(DataType)]
        #self.writeBlock.restype  = c_int

        self.hwiHpiInterrupt = dspDll._hwiHpiInterrupt
        self.hwiHpiInterrupt.argtypes = [c_uint,c_uint]

        self.simReadRegMem = dspDll._simReadRegMem
        self.simReadRegMem.argtypes = [c_uint,c_uint,POINTER(c_uint)]

        self.simWriteHostMem = dspDll._simWriteHostMem
        self.simWriteHostMem.argtypes = [c_uint,c_uint,POINTER(c_uint)]

        self.simReadUser = dspDll._simReadUser
        self.simReadUser.argtypes = []
        self.simReadUser.restype = c_int

        self.main = dspDll._main
        self.main.argtypes = [c_int,POINTER(c_char_p)]

        self.scheduler = dspDll._scheduler

        self.main(0,POINTER(c_char_p)())
        self.prdThread = Thread(target = self.runPrd)
        self.prdThread.setDaemon(True)
        self.prdThread.start()

    def runPrd(self):
        while True:
            time.sleep(0.1)
            self.scheduler()

    def readMem(self,address,uintArray):
        if self.regBase <= address < self.hostBase:
            self.simReadRegMem((address-self.regBase)/4,sizeof(uintArray)/4,uintArray)
        else:
            logging.debug("Reading from outside register region. Address = %x" % address)

    def writeMem(self,address,uintArray):
        if self.hostBase <= address < self.hostBase + 1024:
            self.simWriteHostMem((address-self.hostBase)/4,sizeof(uintArray)/4,uintArray)
        else:
            logging.debug("Writing to outside host region. Address = %x" % address)

