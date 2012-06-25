#!/usr/bin/python
#
# FILE:
#   TestSOACurrent.py tests the G2000 SOA current drive
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

class TestSOACurrent(object):
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
            regVault = Driver.saveRegValues([("FPGA_INJECT","INJECT_CONTROL")])
            self.sourcemeter.sendString(":SOURCE:FUNC CURR")
            self.sourcemeter.sendString(":SOURCE:CURRENT 0.0")
            cs = 0
            Driver.wrFPGA("FPGA_INJECT","INJECT_CONTROL",cs)            
            time.sleep(0.25)
            self.sourcemeter.ask(":MEAS:VOLT:DC?")
            time.sleep(0.25)
            offVoltage = float(self.sourcemeter.ask("READ?").split(",")[0])
            print "Voltage across SOA while off: %.3f" % offVoltage
            cs = (1 << INJECT_CONTROL_MANUAL_SOA_ENABLE_B)
            Driver.wrFPGA("FPGA_INJECT","INJECT_CONTROL",cs)            
            time.sleep(0.25)
            self.sourcemeter.ask(":MEAS:VOLT:DC?")
            time.sleep(0.25)
            onVoltage = float(self.sourcemeter.ask("READ?").split(",")[0])
            print "Voltage across SOA while on:  %.3f" % onVoltage
            self.sourcemeter.sendString(":OUTPUT:STATE OFF")

        finally:
            Driver.restoreRegValues(regVault)
            self.ser.close()
            
        result1 = CsvData()
        tp = self.testParameters
        result1.parameters = {"EngineName":tp.parameters["EngineName"],
                              "DateTime":tp.parameters["DateTime"],
                              "TestCode":'"%s"' % (tp.parameters["TestCode"],),
                              "offVoltage":"%.3f" % (offVoltage,),
                              "onVoltage":"%.3f" % (onVoltage,),
                             }

        result1.columnTitles = []
        result1.columnUnits  = []
        result1.writeOut(self.csv1Fp)

        print >> tp.rstFile, "\nSOA current measurement"
        print >> tp.rstFile, "\nData `directory <%s>`__, " % (tp.relativeTestDirectory,)
        print >> tp.rstFile, "CSV formatted `datafile <%s>`__, " % (tp.relativeTestDirectory+self.csv1Name,)
                
        vt = VerdictTable(30)
        vt.setEntries([("On Voltage",onVoltage,2.3,2.7,"%.3f"),
                       ("Off Voltage",offVoltage,-0.2,0.2,"%.3f")])
        vt.writeOut(tp.rstFile)
        print "Overall result: %s" % vt.giveVerdict()
