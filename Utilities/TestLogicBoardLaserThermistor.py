#!/usr/bin/python
#
# FILE:
#   TestLogicBoardLaserThermistor.py tests the G2000 logic board thermistor processing 
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

class TestLogicBoardLaserThermistor(object):
    def __init__(self,tp,aLaserNum):
        self.testParameters = tp
        self.csv1Name = "data1.csv"
        self.csv1Fp = open(tp.absoluteTestDirectory + self.csv1Name,"w")
        self.graph1Name = "graph1.png"
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
            regVault = Driver.saveRegValues(["LASER%d_TEMP_CNTRL_STATE_REGISTER" % aLaserNum,
                                            ])
    
            setPoints = arange(-40.0,60.0,5.0)
            sweepMon = []
            self.sourcemeter.sendString(":SOURCE:FUNC CURR")
            self.sourcemeter.sendString(":SOURCE:CURRENT 0.0")
            self.sourcemeter.ask(":MEAS:VOLT:DC?")
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % aLaserNum,TEMP_CNTRL_DisabledState)
            time.sleep(0.25)
            print "Thermistor sweep"
            # Step injected current
            Rseries = 30000
            for s in setPoints:
                self.sourcemeter.sendString(":SOURCE:CURRENT %.6f" % (1.0e-6*s,))
                self.sourcemeter.ask(":MEAS:VOLT:DC?")
                time.sleep(0.25)
                v = float(self.sourcemeter.ask("READ?").split(",")[0])
                R = Driver.rdDasReg("LASER%d_RESISTANCE_REGISTER" % aLaserNum)
                vf = R/(R+Rseries)
                print s,v,vf
                sweepMon.append(vf)
            self.sourcemeter.sendString(":SOURCE:CURRENT 0")
            self.sourcemeter.sendString(":SOURCE:CLEAR:IMMEDIATE")
            self.sourcemeter.sendString(":OUTPUT:STATE OFF")
            sweepMon = array(sweepMon)
        finally:
            Driver.restoreRegValues(regVault)
            self.ser.close()
            
        p,res,fittedValues = best_fit(setPoints[:],sweepMon[:],1)
        
        result1 = CsvData()
        tp = self.testParameters
        result1.parameters = {"EngineName":tp.parameters["EngineName"],
                              "DateTime":tp.parameters["DateTime"],
                              "TestCode":'"%s"' % (tp.parameters["TestCode"],),
                             }
        result1.columnTitles = ["Current injected into Laser %d thermistor leads" % aLaserNum,"ADC reading"]
        result1.columnUnits  = ["uA",""]
        result1.writeOut(self.csv1Fp)
        
        for s,r in zip(setPoints,sweepMon):
            print >> self.csv1Fp,",,%g,%g" % (s,r,)
        self.csv1Fp.close()    
        
        figure(1)
        plot(setPoints,sweepMon,'ro',setPoints[:],fittedValues)
        grid(True)
        xlabel(result1.columnTitles[0])
        ylabel(result1.columnTitles[1])
        savefig(tp.absoluteTestDirectory + self.graph1Name)
        close(1)
        
        print >> tp.rstFile, "\nTEC PWM stepping"
        print >> tp.rstFile, "\nData `directory <%s>`__, " % (tp.relativeTestDirectory,)
        print >> tp.rstFile, "CSV formatted `datafile <%s>`__, " % (tp.relativeTestDirectory+self.csv1Name,)
        print >> tp.rstFile, "PNG `graph <%s>`__" % (tp.relativeTestDirectory+self.graph1Name,)
                
        vt = VerdictTable(30)
        vt.setEntries([("TEC Current Slope",p[0],0.0029,0.0031,"%.3g"),
                       ("TEC Current Intercept",p[1],0.24,0.26,"%.3g"),
                       ("TEC Current Residual",sqrt(res),0,1e-4,"%.3g"),
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
    tst = TestLogicBoardLaserThermistor(tp,2)
    tst.run()
    tp.appendReport()
    tp.makeHTML()
