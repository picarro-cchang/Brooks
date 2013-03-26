#!/usr/bin/python
#
# FILE:
#   TestPowerBoardValveDriver.py tests the G2000 power board valve PWM driver 
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
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="TestPowerBoardValveDriver")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc

class TestPowerBoardValveDriver(object):
    def __init__(self,tp,valve):
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
        self.valve = valve
        
    def run(self):
        valve = self.valve
        # Check that the driver can communicate
        id = self.sourcemeter.ask("*IDN?")
        if not id.startswith("KEITHLEY INSTRUMENTS INC.,MODEL 2400"):
            raise ValueError,"Incorrect identification string from sourcemeter: %s" % id
        block = "FPGA_DYNAMICPWM_%s" % valve.upper()
        try:
            regVault = Driver.saveRegValues(["VALVE_CNTRL_STATE_REGISTER",
                                             "VALVE_CNTRL_USER_INLET_VALVE_REGISTER",
                                             "VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER",
                                             "VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER",
                                             "VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER",
                                             "VALVE_CNTRL_INLET_VALVE_MIN_REGISTER",
                                             "VALVE_CNTRL_INLET_VALVE_MAX_REGISTER",
                                             "VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER",
                                             "VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER",
                                             (block,"DYNAMICPWM_CS"),
                                             (block,"DYNAMICPWM_DELTA"),
                                             (block,"DYNAMICPWM_HIGH"),
                                             (block,"DYNAMICPWM_LOW"),
                                             (block,"DYNAMICPWM_SLOPE"),
                                             ])
            quiescentValue = 0
            Driver.wrDasReg("VALVE_CNTRL_STATE_REGISTER","VALVE_CNTRL_ManualControlState")
            Driver.wrDasReg("VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER",0)
            Driver.wrDasReg("VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER",0)
            Driver.wrDasReg("VALVE_CNTRL_INLET_VALVE_MIN_REGISTER",0)
            Driver.wrDasReg("VALVE_CNTRL_INLET_VALVE_MAX_REGISTER",65536)
            Driver.wrDasReg("VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER",0)
            Driver.wrDasReg("VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER",65536)
            setPoints = arange(0.0,66000.0,2000.0)
            sweepMon = []
            self.sourcemeter.sendString(":SOURCE:VOLTAGE 0.0")
            self.sourcemeter.ask(":MEAS:CURR:DC?")
            cs = (1<<DYNAMICPWM_CS_RUN_B) | (1<<DYNAMICPWM_CS_CONT_B) | (1<<DYNAMICPWM_CS_PWM_ENABLE_B)
            Driver.wrFPGA(block,"DYNAMICPWM_CS",cs)            
            Driver.wrFPGA(block,"DYNAMICPWM_DELTA",750)
            Driver.wrFPGA(block,"DYNAMICPWM_SLOPE",1000)
            time.sleep(1.0)
            print "%s valve PWM sweep" % valve
            # Step upper and lower limits of dynamic PWM ramp
            for s in setPoints:
                Driver.wrDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER",int(s))
                Driver.wrDasReg("VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER",int(s))
                Driver.wrFPGA(block,"DYNAMICPWM_HIGH",int(s))
                Driver.wrFPGA(block,"DYNAMICPWM_LOW",int(s))
                time.sleep(0.25)
                r = float(self.sourcemeter.ask("READ?").split(",")[1])
                print s,r
                sweepMon.append(r)
            s = quiescentValue
            Driver.wrDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER",int(s))
            Driver.wrDasReg("VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER",int(s))
            Driver.wrFPGA(block,"DYNAMICPWM_HIGH",int(s))
            Driver.wrFPGA(block,"DYNAMICPWM_LOW",int(s))
            time.sleep(0.25)
            disabledValue = float(self.sourcemeter.ask("READ?").split(",")[1])
            self.sourcemeter.sendString(":OUTPUT:STATE OFF")
            sweepMon = array(sweepMon)
        finally:
            Driver.restoreRegValues(regVault)
            self.ser.close()
            
        p,res,fittedValues = best_fit(setPoints[1:],sweepMon[1:],1)
        
        result1 = CsvData()
        tp = self.testParameters
        result1.parameters = {"EngineName":tp.parameters["EngineName"],
                              "DateTime":tp.parameters["DateTime"],
                              "TestCode":'"%s"' % (tp.parameters["TestCode"],),
                             }
        result1.columnTitles = ["%s valve PWM" % valve,"Current"]
        result1.columnUnits  = ["digU","Amps"]
        result1.writeOut(self.csv1Fp)
        
        for s,r in zip(setPoints,sweepMon):
            print >> self.csv1Fp,",,%g,%g" % (s,r,)
        self.csv1Fp.close()    
        
        figure(1)
        plot(setPoints,sweepMon,'ro',setPoints[1:],fittedValues)
        grid(True)
        xlabel(result1.columnTitles[0])
        ylabel(result1.columnTitles[1])
        savefig(tp.absoluteTestDirectory + self.graph1Name)
        close(1)
        
        print >> tp.rstFile, "\n%s valve PWM stepping" % valve
        print >> tp.rstFile, "\nData `directory <%s>`__, " % (tp.relativeTestDirectory,)
        print >> tp.rstFile, "CSV formatted `datafile <%s>`__, " % (tp.relativeTestDirectory+self.csv1Name,)
        print >> tp.rstFile, "PNG `graph <%s>`__" % (tp.relativeTestDirectory+self.graph1Name,)
                
        vt = VerdictTable(30)
        slopeOpt = 2.5/(4700.0/470.0)/1.0/65536.0
        vt.setEntries([("%s valve Current Slope" % valve,p[0],0.95*slopeOpt,1.05*slopeOpt,"%.3g"),
                       ("%s valve Current Intercept" % valve,p[1]+quiescentValue*p[0],-5e-3,5e-3,"%.3g"),
                       ("%s valve Current Residual" % valve,sqrt(res),0,5e-3,"%.3g"),
                       ("Disabled value",disabledValue,-10.0e-3,10.0e-3,"%.3g"),
                       ])
        vt.writeOut(tp.rstFile)
        print "Overall result: %s" % vt.giveVerdict()
