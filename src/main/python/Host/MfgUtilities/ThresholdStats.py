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
from Host.Common import CmdFIFO, SharedTypes, Listener, SchemeProcessor
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

class RDFreqConvProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_FREQ_CONVERTER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="MakeWlmFile1")
            self.initialized = True

# For convenience in calling driver functions
RDFreqConv = RDFreqConvProxy().rpc

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
    def __init__(self,instrName,thMin,thMax,thIncr,schemeName):
        # Remove the .flag file to indicate routine has not finished yet
        [basename,ext] = os.path.splitext(sys.argv[0])
        self.flagname = basename + ".flag"
        try:
            os.remove(self.flagname)
        except:
            pass
        self.startTime = time.strftime("%Y%m%d_%H%M%S",time.localtime())
        self.schemeName = schemeName
        try:
            schemeType = os.path.basename(schemeName).split('.')[0]
            if schemeType:
                self.csvName = "ThresholdStats_%s_%s.csv" % (schemeType, self.startTime)
            else:
                self.csvName = "ThresholdStats_%s.csv" % self.startTime
        except:
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
        self.sumSqWavenumber = 0
        offset = None
        self.nRingdowns = nRingdowns
        while not self.queue.empty():
            self.queue.get()    # Flush the queue to start
        tBegin = time.time()
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
                e = self.queue.get(time.time()-tBegin-tMax)
                t = 0.001*e.timestamp
                loss = float(e.uncorrectedAbsorbance)
                waveNumber = e.waveNumber
                if offset==None: offset = waveNumber
                fitStatus = e.status
                if 0 == (fitStatus & RINGDOWN_STATUS_RingdownTimeout):
                    self.sumWavenumber += waveNumber
                    self.sumSqWavenumber += (waveNumber-offset)**2
                    self.sumLoss += loss
                    self.sumSquareLoss += loss**2
                    nRd += 1
                if t >= tStart+tMax or nRd >= self.nRingdowns:
                    waveNumberMean = self.sumWavenumber/nRd
                    waveNumberSdev = sqrt((self.sumSqWavenumber/nRd) - (waveNumberMean-offset)**2)
                    return (nRd/(t-tStart),self.sumLoss/nRd,self.sumSquareLoss/nRd-(self.sumLoss/nRd)**2,waveNumberMean,waveNumberSdev)
            except Queue.Empty:
                waveNumberMean = self.sumWavenumber/nRd
                waveNumberSdev = sqrt((self.sumSqWavenumber/nRd) - (waveNumberMean-offset)**2)
                return (nRd/(t-tStart),self.sumLoss/nRd,self.sumSquareLoss/nRd-(self.sumLoss/nRd)**2,waveNumberMean,waveNumberSdev)
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
        # Stop spectrum collection
        if self.schemeName:
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_IdleState")
            time.sleep(1)
            scheme = SchemeProcessor.Scheme(self.schemeName)
            RDFreqConv.wrFreqScheme(1,scheme)
            RDFreqConv.convertScheme(1)
            RDFreqConv.uploadSchemeToDAS(1)
            time.sleep(1)
            Driver.wrDasReg("SPECT_CNTRL_NEXT_SCHEME_REGISTER",1)
            Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER","SPECT_CNTRL_SchemeMultipleMode")
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER","SPECT_CNTRL_StartingState")
            print>>sys.stderr, "Loaded scheme file: %s" % (self.schemeName,)
            print "Loaded scheme file: %s" % (self.schemeName,)
        self.thresh_list = arange(self.thMin,self.thMax+1,self.thIncr)
        self.rd_rates = zeros(len(self.thresh_list),float_)
        self.shot_to_shot = zeros(len(self.thresh_list),float_)
        self.mean_loss = zeros(len(self.thresh_list),float_)
        self.std_loss = zeros(len(self.thresh_list),float_)
        self.mean_wavenumber = zeros(len(self.thresh_list),float_)
        self.std_frequency = zeros(len(self.thresh_list),float_)
        self.sensitivity = zeros(len(self.thresh_list),float_)
        try:
            for l in range(len(self.thresh_list)):
                thresh = float(self.thresh_list[l])
                self.setTuner(thresh)
                time.sleep(1)
                rate,meanLoss,varLoss,meanWavenumber,sdevWavenumber = self.collectStats(1000,20)
                shot2shot = 0
                stdLoss = 1000.0*sqrt(varLoss)
                if meanLoss != 0: shot2shot = 100*stdLoss/(1000.0*meanLoss)
                sensitivity = stdLoss/sqrt(rate) if rate != 0 else 0.0
                sdevFrequency = 30000.0*sdevWavenumber
                msg = "\nThreshold: %6.0f Ringdown rate: %6.2f Shot-to-shot: %6.3f Mean loss: %6.3f Mean wavenumber: %10.4f Sdev freq (MHz): %10.4f StdDev loss: %10.4f Sensitivity: %10.5f" % \
                      (thresh,rate,shot2shot,meanLoss,meanWavenumber,sdevFrequency,stdLoss,sensitivity)
                print>>sys.stderr, msg
                print msg
                self.rd_rates[l] = rate
                self.shot_to_shot[l] = shot2shot
                self.mean_loss[l] = meanLoss
                self.mean_wavenumber[l] = meanWavenumber
                self.std_frequency[l] = sdevFrequency
                self.std_loss[l] = stdLoss
                self.sensitivity[l] = sensitivity
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
                             "InstrumentName":self.instrName,
                             "SchemeFile":"%s" % (self.schemeName,)
                            }
        for r in regs:
            if isinstance(r,str):
                csvOut.parameters[r] = "%s" % Driver.rdDasReg(r)
            else:
                csvOut.parameters[r[1]] = "%s" % Driver.rdFPGA(r[0],r[1])

        csvOut.columnTitles = ["Threshold", "Rate", "Shot-to-shot", "Mean loss", "Mean wavenumber", "StdDev freq", "StdDev loss", "Sensitivity"]
        csvOut.columnUnits  = ["digU", "rd/s", "%", "ppm/cm", "cm^-1", "MHz", "ppb/cm", "ppb/cm/sqrt(Hz)" ]
        csvOut.writeOut(self.csvFp)

        for l in range(len(self.thresh_list)):
            thresh = self.thresh_list[l]
            rate = self.rd_rates[l]
            shot2shot = self.shot_to_shot[l]
            meanLoss = self.mean_loss[l]
            meanWavenumber = self.mean_wavenumber[l]
            stdFrequency = self.std_frequency[l]
            stdLoss = self.std_loss[l]
            sensitivity = self.sensitivity[l]
            print >> self.csvFp,",,%.0f,%.2f,%.4f,%.4f,%.4f,%.2f,%.4f,%.5f" % (thresh,rate,shot2shot,meanLoss,meanWavenumber,stdFrequency,stdLoss,sensitivity)
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
    schemeName = None
    if len(sys.argv)>5: schemeName= sys.argv[5].strip()
    if instrName == None:
        instrName = raw_input("Name of instrument? ")
    tst = ThresholdStats(instrName,thMin,thMax,thIncr,schemeName)
    tst.run()
    tst.done()