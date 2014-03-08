#!/usr/bin/python
#
# FILE:
#   writeDacs2.py
#
# DESCRIPTION:
#   Test program to write waveforms to G2000 DACs using 
# timestamp-based protocol.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   22-April-2010  sze  Initial version.
#
#  Copyright (c) 2010 Picarro, Inc. All rights reserved
#
import sys
import time
import socket
import struct
from math import pi, cos, sin
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="writeWlmEeprom")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc

if __name__ == "__main__":
    Driver.resetDacQueue()
    timestamp = Driver.dasGetTicks() # ms resolution
    Driver.setDacTimestamp((timestamp // 10) & 0xFFFF)
    # Fill up buffer with samples up to 500ms in advance of present
    tSamp = 10                           # 20ms sampling
    tLast = tSamp*((timestamp + tSamp)//tSamp)    # Round up to next sample interval
    freq = 1.0
    x = 0.0
    dx = 0.002*pi*freq*tSamp 
    while True:
        timestamp = Driver.dasGetTicks()
        usbStr = []
        usbLen = 0
        while tLast < timestamp + 1500:
            sendStr = []
            sendStr.append("\xD2")
            sendStr.append(struct.pack("=H",(tLast//10) & 0xFFFF))
            sendStr.append("\x03")
            sendStr.append(struct.pack("=HH",int(32768+32767*cos(x)),int(32768+32767*sin(x))))
            sendStr = "".join(sendStr)
            if usbLen + len(sendStr) >= 512:
                Driver.wrAuxiliary("".join(usbStr))
                usbStr = []
                usbLen = 0
            usbLen += len(sendStr)
            usbStr.append(sendStr)
            x += dx
            tLast += tSamp
        if usbStr:    
            Driver.wrAuxiliary("".join(usbStr))
        time.sleep(0.5)    
