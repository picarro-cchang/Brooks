#!/usr/bin/python
#
# FILE:
#   writeDacs.py
#
# DESCRIPTION:
#   Test program to write waveforms to G2000 DACs
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   20-April-2010  sze  Initial version.
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
    Driver.resetDacQueues()
    Driver.setDacQueuePeriod(0,5)
    Driver.setDacQueuePeriod(1,5)
    freq = 1.0
    x = 0.0
    dx = 2*pi*freq*0.05
    started = False
    while True:
        free = Driver.getDacQueueFreeSlots()
        nReqd = min(free[0],free[1])
        if nReqd>0:
            sendStr = ["\x03"]
            for i in range(nReqd):
                sendStr.append(struct.pack("HH",int(32768+32767*cos(x)),int(32768+32767*sin(x))))
                x += dx
            Driver.wrAuxiliary("".join(sendStr))
            if not started:
                started = True
                Driver.serveDacQueues()
            sys.stdout.write('.')
        time.sleep(0.25)
