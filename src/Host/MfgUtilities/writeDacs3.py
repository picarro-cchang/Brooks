from math import pi, cos, sin
import sys
import time
import socket
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes

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
    timestamp = Driver.dasGetTicks()    # ms resolution
    # Fill up buffer with samples up to 2000ms in advance of present
    tSamp = 20                          # 10ms sampling
    tLast = tSamp*((timestamp + tSamp)//tSamp)    # Round up to next sample interval
    freq = 1.0
    x = 0.0
    dx = 0.002*pi*freq*tSamp
    while True:
        timestamp = Driver.dasGetTicks()
        samples = []
        while tLast < timestamp + 3000:
            samples.append((tLast,0,5.0+5.0*cos(x)))
            samples.append((tLast,1,5.0+5.0*sin(x)))
            x += dx
            tLast += tSamp
        Driver.sendDacSamples(samples)
        print Driver.getDacQueueFree()
        time.sleep(0.5)