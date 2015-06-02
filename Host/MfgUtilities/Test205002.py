#!/usr/bin/python
#
# FILE:
#   Test205002.py tests the G2000 power board PWM drive for the cavity
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
from Host.MfgUtilities.TestUtilities import *
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
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="TestPowerBoardCavityTecDriver")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc

class TestPowerBoardCavityTecDriver(object):
    def __init__(self,tp):
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

    def run(self):
        # Check that the driver can communicate
        id = self.sourcemeter.ask("*IDN?")
        if not id.startswith("KEITHLEY INSTRUMENTS INC.,MODEL 2400"):
            raise ValueError,"Incorrect identification string from sourcemeter: %s" % id
        try:
            regVault = Driver.saveRegValues(["CAVITY_MANUAL_TEC_REGISTER",
                                             "CAVITY_TEMP_CNTRL_STATE_REGISTER",
                                             "CAVITY_TEMP_CNTRL_AMIN_REGISTER",
                                             "CAVITY_TEMP_CNTRL_AMAX_REGISTER",
                                             "TEC_CNTRL_REGISTER",
                                             ])

            quiescentValue = 32768
            setPoints = arange(4000.0,61000.0,2000.0)
            sweepMon = []
            self.sourcemeter.sendString(":SOURCE:FUNC CURR")
            self.sourcemeter.sendString(":SOURCE:CURRENT 0.0")
            self.sourcemeter.ask(":MEAS:VOLT:DC?")
            Driver.wrDasReg("CAVITY_TEMP_CNTRL_AMIN_REGISTER",setPoints[0])
            Driver.wrDasReg("CAVITY_TEMP_CNTRL_AMAX_REGISTER",setPoints[-1])
            Driver.wrDasReg("CAVITY_MANUAL_TEC_REGISTER",quiescentValue)
            Driver.wrDasReg("CAVITY_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_ManualState)
            Driver.wrDasReg("TEC_CNTRL_REGISTER",TEC_CNTRL_Enabled)
            time.sleep(5.0)
            print "Cavity TEC sweep"
            # Step coarse current DAC
            for s in setPoints:
                Driver.wrDasReg("CAVITY_MANUAL_TEC_REGISTER",s)
                Driver.wrFPGA("FPGA_PWM_HOTBOX","PWM_PULSE_WIDTH",int(s))
                time.sleep(0.25)
                r = float(self.sourcemeter.ask("READ?").split(",")[0])
                print s,r
                sweepMon.append(r)
            Driver.wrDasReg("CAVITY_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_DisabledState)
            Driver.wrFPGA("FPGA_PWM_HOTBOX","PWM_PULSE_WIDTH",quiescentValue)
            time.sleep(0.25)
            disabledValue = float(self.sourcemeter.ask("READ?").split(",")[0])
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
        result1.columnTitles = ["Cavity TEC PWM","Voltage across 5 ohm load"]
        result1.columnUnits  = ["digU","Volts"]
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
        slopeOpt = 22.0/65536.0
        vt.setEntries([("TEC Current Slope",p[0],0.9*slopeOpt,1.0*slopeOpt,"%.3g"),
                       ("TEC Current Intercept",p[1]+quiescentValue*p[0],-0.05,0.05,"%.3g"),
                       ("TEC Current Residual",sqrt(res),0,0.3,"%.3g"),
                       ("Disabled value",disabledValue,-0.02,0.02,"%.3g"),
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
    tst = TestPowerBoardCavityTecDriver(tp)
    tst.run()
    tp.appendReport()
    tp.makeHTML()