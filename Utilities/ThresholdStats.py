#!/usr/bin/env python
#
# File Name: ThresholdStats.py
# Purpose: Test program for measuring ringdown statistics vs threshold
#
# Notes:
#
# File History:
# 07-11-28 sze   Initial version
# 10-02-22 sze   Modified for G2000

import sys
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes, Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
import Queue
import os
import shutil
import socket
import time
from numpy import *
from ctypes import *

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="MakeWlmFile1")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc

class CsvData(object):
    "Class for writing to a comma separated value file"
    def __init__(self):
        self.parameters = {}
        self.columnTitles = []
        self.columnUnits = []

    def protectComma(self,s):
        if s.find(",") < 0: return s
        else: return '"%s"' % s

    def writeOut(self,fp):
        keys = self.parameters.keys()
        keys.sort()
        for key in keys:
            print >> fp, "# %s,%s" % tuple([self.protectComma(s) for s in [key,self.parameters[key]]])
        print
        print >> fp, "# Units,,%s"  % (",".join([self.protectComma(s) for s in self.columnUnits]),)
        print >> fp, "# Titles,,%s" % (",".join([self.protectComma(s) for s in self.columnTitles]),)

class StreamData(object):
    pass

class ThresholdStats(object):
    def __init__(self,instrName,thMin,thMax,thIncr):
        # Remove the .flag file to indicate routine has not finished yet
        [basename,ext] = os.path.splitext(sys.argv[0])
        self.flagname = basename + ".flag"
        try:
            os.remove(self.flagname)
        except:
            pass
        self.startTime = time.strftime("%Y%m%d_%H%M%S",time.localtime())
        self.csvName = "ThresholdStats_%s.csv" % self.startTime
        self.csvFp = open(self.csvName,"w")
        self.instrName = instrName
        self.thMin = thMin
        self.thMax = thMax
        self.thIncr = thIncr
        # Set up a listener for the streaming data
        self.queue = Queue.Queue(0)

    def collectStats(self,nRingdowns=100,tMax=10):
        """ Determine the rate by timing nRingdowns ringdowns or measuring the ringdowns in tMax, whichever
        takes less time """
        MIN_LOSS = 0.1
        MAX_LOSS = 100
        self.sumLoss = 0
        self.sumSquareLoss = 0
        self.sumWavenumber = 0
        self.nRingdowns = nRingdowns
        while not self.queue.empty():
            self.queue.get()    # Flush the queue to start
        tBegin = time.clock()
        try:
            e = self.queue.get(timeout=tMax)
        except Queue.Empty:
            print "No ringdowns - check if scheme is running"
            return (0,0,0,0)
        tStart = 0.001*e.timestamp
        t = tStart + tMax
        nRd = 0
        while True:
            try:
                e = self.queue.get(time.clock()-tBegin-tMax)
                t = 0.001*e.timestamp
                loss = float(e.uncorrectedAbsorbance)
                waveNumber = e.waveNumber
                fitStatus = e.status
                if 0 == (fitStatus & RINGDOWN_STATUS_RingdownTimeout):
                    self.sumWavenumber += waveNumber
                    self.sumLoss += loss
                    self.sumSquareLoss += loss**2
                    nRd += 1
                if t >= tStart+tMax or nRd >= self.nRingdowns:
                    return (nRd/(t-tStart),self.sumLoss/nRd,self.sumSquareLoss/nRd-(self.sumLoss/nRd)**2,self.sumWavenumber/nRd)
            except Queue.Empty:
                return (nRd/(t-tStart),self.sumLoss/nRd,self.sumSquareLoss/nRd-(self.sumLoss/nRd)**2,self.sumWavenumber/nRd)
            sys.stderr.write(".")

    def flushQueue(self):
        # Flush the queue
        try:
            while True: t,d = self.queue.get(False)
        except:
            pass

    def setTuner(self,threshold):
        Driver.wrDasReg("SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER",threshold)
        Driver.wrFPGA("FPGA_RDMAN","RDMAN_THRESHOLD",int(threshold))

    def done(self):
        # Create the .flag file to indicate completion
        of = file(self.flagname,"w")
        print >>of, "%s" % " ".join(sys.argv)
        print >>of, time.strftime("Completed at %H:%M:%S on %Y-%m-%d",time.localtime())
        of.close()

    def run(self):
        regVault = Driver.saveRegValues(["SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER"])
        self.listener = Listener.Listener(self.queue,SharedTypes.BROADCAST_PORT_RD_RECALC,ProcessedRingdownEntryType)
        self.thresh_list = arange(self.thMin,self.thMax+1,self.thIncr)
        self.rd_rates = zeros(len(self.thresh_list),float_)
        self.shot_to_shot = zeros(len(self.thresh_list),float_)
        self.mean_loss = zeros(len(self.thresh_list),float_)
        self.mean_wavenumber = zeros(len(self.thresh_list),float_)
        try:
            for l in range(len(self.thresh_list)):
                thresh = float(self.thresh_list[l])
                self.setTuner(thresh)
                rate,meanLoss,varLoss,meanWavenumber = self.collectStats(200,10)
                shot2shot = 0
                if meanLoss != 0: shot2shot = 100*sqrt(varLoss)/meanLoss
                print "\nThreshold: %6.0f Ringdown rate: %6.2f Shot-to-shot: %6.3f Mean loss: %6.3f Mean wavenumber: %10.4f" % (thresh,rate,shot2shot,meanLoss,meanWavenumber)
                self.rd_rates[l] = rate
                self.shot_to_shot[l] = shot2shot
                self.mean_loss[l] = meanLoss
                self.mean_wavenumber[l] = meanWavenumber
        finally:
            self.listener.stop()
            Driver.restoreRegValues(regVault)

        regs = ["TUNER_SWEEP_RAMP_HIGH_REGISTER",
                "TUNER_SWEEP_RAMP_LOW_REGISTER",
                "TUNER_WINDOW_RAMP_HIGH_REGISTER",
                "TUNER_WINDOW_RAMP_LOW_REGISTER",
                "TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER",
                "TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER",
                "TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER",
                "TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER",
                "TUNER_DITHER_MEDIAN_COUNT_REGISTER",
                ("FPGA_TWGEN","TWGEN_SLOPE_DOWN"),
                ("FPGA_TWGEN","TWGEN_SLOPE_UP")]

        # Write data out

        csvOut = CsvData()
        csvOut.parameters = {"DateTime":self.startTime,
                             "Description":"%s" % ("Variation of ringdown statistics with threshold",),
                             "InstrumentName":self.instrName
                            }
        for r in regs:
            if isinstance(r,str):
                csvOut.parameters[r] = "%s" % Driver.rdDasReg(r)
            else:
                csvOut.parameters[r[1]] = "%s" % Driver.rdFPGA(r[0],r[1])
                
        csvOut.columnTitles = ["Threshold", "Rate", "Shot-to-shot", "Mean loss", "Mean wavenumber"]
        csvOut.columnUnits  = ["digU", "rd/s", "%", "ppm/cm", "cm^-1"]
        csvOut.writeOut(self.csvFp)

        for l in range(len(self.thresh_list)):
            thresh = self.thresh_list[l]
            rate = self.rd_rates[l]
            shot2shot = self.shot_to_shot[l]
            meanLoss = self.mean_loss[l]
            meanWavenumber = self.mean_wavenumber[l]
            print >> self.csvFp,",,%.0f,%.2f,%.4f,%.4f,%.4f" % (thresh,rate,shot2shot,meanLoss,meanWavenumber)
        self.csvFp.close()

if __name__ == "__main__":
    pname = sys.argv[0]
    bname = os.path.basename(pname)
    instrName = None
    thMin = 2000
    thMax = 16380
    thIncr = 500
    if len(sys.argv)>1: instrName = sys.argv[1]
    if len(sys.argv)>2: thMin = int(sys.argv[2])
    if len(sys.argv)>3: thMax = int(sys.argv[3])
    if len(sys.argv)>4: thIncr = int(sys.argv[4])
    if instrName == None:
        instrName = raw_input("Name of instrument? ")
    tst = ThresholdStats(instrName,thMin,thMax,thIncr)
    tst.run()
    tst.done()
