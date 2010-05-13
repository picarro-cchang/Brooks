#!/usr/bin/python
#
"""
File Name: DriverAnalogInterface.py
Purpose: Communicates with analog interface card. 

1. Enqueues timestamped voltage data for output. These are ordered by timestamp,
    and coalasced so that all channels for a specified time are grouped together.
2. Applies calibration constants from the [ANALOG_OUTPUT] section of the 
    Master.ini file to convert voltages to DAC values.
3. Provides facilities for keeping timestamps on Cypress and on DSP in 
    synchronization.

File History:
    28-Apr-2010  sze  Initial version.

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""
import sys
import heapq
import struct
import time
import threading
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.timestamp import getTimestamp
from Host.Common.CustomConfigObj import CustomConfigObj

NCHANNELS = 8

class AnalogInterface(object):
    def __init__(self,driver,config):
        self.config = config
        self.driver = driver
        
        self.scale  = [6553.6 for i in range(NCHANNELS)]
        self.offset = [0.0 for i in range(NCHANNELS)]
        if "ANALOG_OUTPUT" in config:
            sec = config["ANALOG_OUTPUT"]
            for key in sec:
                if key.startswith("SCALE"):
                    chan = int(key[5:])
                    self.scale[chan] = float(sec[key])
                elif key.startswith("OFFSET"):
                    chan = int(key[6:])
                    self.offset[chan] = float(sec[key])

        self.clockPeriodms = 10
        clockFreq = 1000/self.clockPeriodms
        self.divisor = int(4000000//clockFreq)
        self.sampleHeap = []
        # List of strings to send to DACs
        self.dacStr = []
        self.dacStrLen = 0
        
    def initializeClock(self):
        #timestamp = self.driver.rpcHandler.dasGetTicks()
        timestamp = getTimestamp()
        self.driver.rpcHandler.setDacTimestamp(int(timestamp // self.clockPeriodms) & 0xFFFF)
        reloadCount = 65536 - self.divisor
        self.driver.rpcHandler.setDacReloadCount(reloadCount)
        self.driver.rpcHandler.resetDacQueue()
        # Samples which are enqueued with timestamps before 
        #  self.lastClk*self.clockPeriodms are discarded
        # self.lastClk = int((self.driver.rpcHandler.dasGetTicks()+1000)//self.clockPeriodms)
        self.lastClk = int((getTimestamp()+1000)//self.clockPeriodms)
        
    def nudgeClock(self):
        ts1 = self.driver.rpcHandler.dasGetTicks()
        clk = self.driver.rpcHandler.getDacTimestamp()
        ts2 = self.driver.rpcHandler.dasGetTicks()
        if ts2-ts1 < 25:    # Perform nudge if RTT is small enough
            ts = int((ts1+ts2)//2)
            eClk = int(ts//self.clockPeriodms) & 0xFFFF
            # print "Clock error ", clk-eClk
            diff = (clk - eClk) & 0xFFFF
            if diff & 0x8000:   # eClk > clk
                diff = 0x10000 - diff # This is now eClk - clk
                if diff > 30:   # Error more than 0.3s, speed up clk by 1/32
                    reloadCount = 65536 - (self.divisor - (self.divisor >> 5))
                elif diff > 2:  # Speed up clk by 1/4096
                    reloadCount = 65536 - (self.divisor - (self.divisor >> 12))
                else:
                    reloadCount = 65536 - self.divisor
            else:   # eClk < clk
                if diff > 30:   # Error more than 0.3s, slow down clk by 1/32
                    reloadCount = 65536 - (self.divisor + (self.divisor >> 5))
                elif diff > 2:  # Slow down clk by 1/4096
                    reloadCount = 65536 - (self.divisor + (self.divisor >> 12))
                else:
                    reloadCount = 65536 - self.divisor
            # print "Updated reload count", reloadCount
            if self.driver.rpcHandler.getDacReloadCount() != reloadCount:
                self.driver.rpcHandler.setDacReloadCount(reloadCount)

    def enqueueSample(self,timestamp,channel,voltage):
        if channel<0 or channel>=NCHANNELS: return
        if timestamp <= self.lastClk*self.clockPeriodms: return
        dacCounts = int(voltage*self.scale[channel] + self.offset[channel] + 0.5)
        dacCounts = max(min(dacCounts,65535),0)
        heapq.heappush(self.sampleHeap,(timestamp,channel,dacCounts))

    def writeSample(self,channel,voltage):
        if channel<0 or channel>=NCHANNELS: return
        dacCounts = int(voltage*self.scale[channel] + self.offset[channel] + 0.5)
        dacCounts = max(min(dacCounts,65535),0)
        self.driver.rpcHandler.wrDac(channel,dacCounts)
        
    def serve(self):
        """Send all enqueued samples which have to be output before now + bufferTime"""
        bufferTime = 1000 # In milliseconds
        # timestamp = self.driver.rpcHandler.dasGetTicks()
        timestamp = getTimestamp()
        # Round horizon up to a multiple of the clock period
        horizon = int((timestamp + bufferTime + self.clockPeriodms - 1)//self.clockPeriodms) * self.clockPeriodms
        samplesToSend = {}
        while self.sampleHeap and self.sampleHeap[0][0] <= horizon:       # We need to send the sample to the DAC
            ts,channel,dacCounts = heapq.heappop(self.sampleHeap)
            clk = int(ts // self.clockPeriodms)
            if clk < self.lastClk: print "Discarding" # Discard late samples
            elif clk == self.lastClk:
                samplesToSend[channel] = dacCounts
            else:
                if samplesToSend:
                    self.sendToDacs(self.lastClk,samplesToSend)
                samplesToSend = {channel:dacCounts}
                self.lastClk = clk
        if samplesToSend:
            self.sendToDacs(self.lastClk,samplesToSend)
        self.flush()
        self.nudgeClock()
        
    def sendToDacs(self,clk,samplesToSend):
        """Encode data to send to DACs and slices them into USB packet sized chunks (64 bytes).
            At each time, we send the 10ms timestamp, a channel bitmask, and then the actual
            channel data."""
        sendStr = []
        sendStr.append(struct.pack("H",clk & 0xFFFF))
        chanMask = 0
        dacCounts = []
        for c in sorted(samplesToSend.keys()):
            chanMask += (1<<c)
            dacCounts.append(samplesToSend[c])
        sendStr.append(struct.pack("B",chanMask))
        sendStr.append(struct.pack("%dH" % len(dacCounts),*dacCounts))
        sendStr = "".join(sendStr)
        if self.dacStrLen + len(sendStr) >= 64:
            self.driver.rpcHandler.enqueueDacSamples("".join(self.dacStr))
            self.dacStr = []
            self.dacStrLen = 0
        self.dacStrLen += len(sendStr)
        self.dacStr.append(sendStr)
        
    def flush(self):
        """Flush the USB auxiliary message buffer"""
        if self.dacStr:    
            self.driver.rpcHandler.enqueueDacSamples("".join(self.dacStr))
            self.dacStr = []
            self.dacStrLen = 0
    
    def serveForever(self,period_ms):
        while True:
            try:
                self.serve()
            except:
                raise
            time.sleep(0.001*period_ms)
                
from math import pi, cos, sin
        
if __name__ == "__main__":
    config = CustomConfigObj("../../InstrConfig/Calibration/InstrCal/Master.ini")
    a = AnalogInterface(config)
    a.initializeClock()
    serviceThread = threading.Thread(target = a.serveForever,args=(1000,))
    serviceThread.setDaemon(True)
    serviceThread.start()

    timestamp = getTimestamp()    # ms resolution
    # Fill up buffer with samples up to 2000ms in advance of present
    tSamp = 10                          # 10ms sampling
    tLast = tSamp*int((timestamp + tSamp)//tSamp)    # Round up to next sample interval
    freq = 1.0
    x = 0.0
    dx = 0.002*pi*freq*tSamp 
    while True:
        try:
            timestamp = getTimestamp()
            while tLast < timestamp + 3000:
                a.enqueueSample(tLast,0,5.0+5.0*cos(x))
                a.enqueueSample(tLast,1,5.0+5.0*sin(x))
                x += dx
                tLast += tSamp
        except:
            pass
        time.sleep(0.5)
            