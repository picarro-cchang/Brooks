#!/usr/bin/python
#
# FILE:
#   TestLogicBoardLaserDriver.py tests the G2000 logic board laser current drive
#
# DESCRIPTION:
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   13-Dec-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
import getopt
import os
from Queue import Queue, Empty
import serial
import socket
import time

from numpy import *
from pylab import *
from TestUtilities import *
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

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

class TestLogicBoardLaserDriver(object):
    def __init__(self,tp,aLaserNum):
        self.testParameters = tp
        self.csv1Name = "data1.csv"
        self.csv1Fp = open(tp.absoluteTestDirectory + self.csv1Name,"w")
        self.graph1Name = "graph1.png"
        self.csv2Name = "data2.csv"
        self.csv2Fp = open(tp.absoluteTestDirectory + self.csv2Name,"w")
        self.graph2Name = "graph2.png"
        try:
            print "Driver version: %s" % Driver.allVersions()
        except:
            raise ValueError,"Cannot communicate with driver, aborting"

        # Open serial port to source meter for non-blocking read
        try:
            self.ser = serial.Serial(0,9600,timeout=0)
            self.sourcemeter = KeithleyReply(self.ser,0.02)
        except:
            raise Exception("Cannot open serial port - aborting")
        self.serialTimeout = 10.0
        self.aLaserNum = aLaserNum

    def run(self):
        aLaserNum = self.aLaserNum
        # Check that the driver can communicate
        id = self.sourcemeter.ask("*IDN?")
        if not id.startswith("KEITHLEY INSTRUMENTS INC.,MODEL 2400"):
            raise ValueError,"Incorrect identification string from sourcemeter: %s" % id
        try:
            regVault = Driver.saveRegValues(["LASER%d_MANUAL_FINE_CURRENT_REGISTER" % aLaserNum,
                                             "LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % aLaserNum,
                                             "LASER%d_CURRENT_CNTRL_STATE_REGISTER" % aLaserNum,
                                             ])
    
            setPoints = arange(0.0,65000,2000.0)
            coarseSweepMon = []
            Driver.wrDasReg("LASER%d_MANUAL_FINE_CURRENT_REGISTER" % aLaserNum,0)
            self.sourcemeter.sendString(":SOURCE:CURRENT 0.0")
            self.sourcemeter.ask(":MEAS:VOLT:DC?")
            Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % aLaserNum,LASER_CURRENT_CNTRL_DisabledState)
            time.sleep(0.25)
            print "Disabled",float(self.sourcemeter.ask("READ?").split(",")[0])
            print "Coarse current sweep"
            # Step coarse current DAC
            Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % aLaserNum,LASER_CURRENT_CNTRL_ManualState)
            for s in setPoints:
                Driver.wrDasReg("LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % aLaserNum,s)
                time.sleep(0.25)
                r = float(self.sourcemeter.ask("READ?").split(",")[0])
                print s,r
                coarseSweepMon.append(r)
            print "Fine current sweep"
            # Step fine current DAC
            Driver.wrDasReg("LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % aLaserNum,30000)
            Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % aLaserNum,LASER_CURRENT_CNTRL_AutomaticState)
            time.sleep(0.25)
            ringdownValue = float(self.sourcemeter.ask("READ?").split(",")[0])
            Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % aLaserNum,LASER_CURRENT_CNTRL_ManualState)
            fineSweepMon = []
            aLaserNum = self.aLaserNum
            for s in setPoints:
                Driver.wrDasReg("LASER%d_MANUAL_FINE_CURRENT_REGISTER" % aLaserNum,s)
                time.sleep(0.25)
                r = float(self.sourcemeter.ask("READ?").split(",")[0])
                print s,r
                fineSweepMon.append(r)
            Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % aLaserNum,LASER_CURRENT_CNTRL_DisabledState)
            time.sleep(0.25)
            disabledValue = float(self.sourcemeter.ask("READ?").split(",")[0])
            self.sourcemeter.sendString(":OUTPUT:STATE OFF")
            coarseSweepMon = array(coarseSweepMon)
        finally:
            Driver.restoreRegValues(regVault)
            self.ser.close()
            
            
        pCoarse,res,fittedCoarseSweepMonValues = best_fit(setPoints[10:-5],coarseSweepMon[10:-5],1)
        
        result1 = CsvData()
        tp = self.testParameters
        result1.parameters = {"EngineName":tp.parameters["EngineName"],
                              "DateTime":tp.parameters["DateTime"],
                              "TestCode":'"%s"' % (tp.parameters["TestCode"],),
                              "Section":"Coarse Sweep"}
        result1.columnTitles = ["Laser %d coarse current DAC" % aLaserNum,"Voltage across 10 ohm load"]
        result1.columnUnits  = ["digU","Volts"]
        result1.writeOut(self.csv1Fp)
        
        for s,r in zip(setPoints,coarseSweepMon):
            print >> self.csv1Fp,",,%g,%g" % (s,r,)
        self.csv1Fp.close()    
        
        figure(1)
        plot(setPoints,coarseSweepMon,'ro',setPoints[10:-5],fittedCoarseSweepMonValues)
        grid(True)
        xlabel(result1.columnTitles[0])
        ylabel(result1.columnTitles[1])
        savefig(tp.absoluteTestDirectory + self.graph1Name)
        close(1)
        
        print >> tp.rstFile, "\nCoarse current stepping, Fine current setpoint = 0"
        print >> tp.rstFile, "\nData `directory <%s>`__, " % (tp.relativeTestDirectory,)
        print >> tp.rstFile, "CSV formatted `datafile <%s>`__, " % (tp.relativeTestDirectory+self.csv1Name,)
        print >> tp.rstFile, "PNG `graph <%s>`__" % (tp.relativeTestDirectory+self.graph1Name,)

        result2 = CsvData()
        tp = self.testParameters
        result2.parameters = {"EngineName":tp.parameters["EngineName"],
                              "DateTime":tp.parameters["DateTime"],
                              "TestCode":'"%s"' % (tp.parameters["TestCode"],),
                              "Section":"Fine Sweep"}
        result2.columnTitles = ["Laser %d fine current DAC" % aLaserNum,"Voltage across 10 ohm load"]
        result2.columnUnits  = ["digU","Volts"]
        result2.writeOut(self.csv2Fp)
        
        for s,r in zip(setPoints,fineSweepMon):
            print >> self.csv2Fp,",,%g,%g" % (s,r,)
        self.csv2Fp.close()    

        pFine,res,fittedFineSweepMonValues = best_fit(setPoints,fineSweepMon,1)
        
        figure(2)
        plot(setPoints,fineSweepMon,'ro',setPoints,fittedFineSweepMonValues)
        grid(True)
        xlabel(result2.columnTitles[0])
        ylabel(result2.columnTitles[1])
        savefig(tp.absoluteTestDirectory + self.graph2Name)
        close(2)
        intercept = polyval(pCoarse,[30000.0])[0]
        
        print >> tp.rstFile, "\nFine current stepping, Coarse current setpoint = 30000"
        print >> tp.rstFile, "\nData `directory <%s>`__, " % (tp.relativeTestDirectory,)
        print >> tp.rstFile, "CSV formatted `datafile <%s>`__, " % (tp.relativeTestDirectory+self.csv2Name,)
        print >> tp.rstFile, "PNG `graph <%s>`__" % (tp.relativeTestDirectory+self.graph2Name,)
                
        vt = VerdictTable(30)
        vt.setEntries([("Coarse Current Slope",pCoarse[0],3.4e-5,3.8e-5,"%.3g"),
                       ("Coarse Current Intercept",pCoarse[1],-0.05,0.05,"%.3g"),
                       ("Coarse Current Residual",sqrt(res),0,0.001,"%.3g"),
                       ("Fine Current Slope",pFine[0],6.8e-6,7.6e-6,"%.3g"),
                       ("Fine Current Intercept",pFine[1],0.95*intercept,1.05*intercept,"%.3g"),
                       ("Fine Current Residual",sqrt(res),0,0.001,"%.3g"),
                       ("Disabled value",disabledValue,0,0.05,"%.3g"),
                       ("Value during ringdown",ringdownValue,0,0.25,"%.3g"),
                       ])
        vt.writeOut(tp.rstFile)
        print "Overall result: %s" % vt.giveVerdict()

if __name__ == "__main__":
    pname = sys.argv[0]
    bname = os.path.basename(pname)
    if len(sys.argv) < 2:
        engineName = raw_input("Engine name? ")
    else:
        engineName = sys.argv[1]
    assert bname[:4].upper() == "TEST", "Test program name %s is invalid (should start with Test)" % (bname,)
    tp = TestParameters(engineName,bname[4:10])
    tst = TestLogicBoardLaserDriver(tp,2)
    tst.run()
    tp.appendReport()
    tp.makeHTML()
