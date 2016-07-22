#!/usr/bin/python
"""
FILE:
    hostDasInterface.py

DESCRIPTION:
    Code which communicates between the Host and the DAS

SEE ALSO:
    Specify any related information.

HISTORY:
    22-Dec-2008  sze  Initial version.
     1-Dec-2013  sze  Split into several modules

    Copyright (c) 2008 Picarro, Inc. All rights reserved
"""
APP_NAME = "hostDasInterface"

from ctypes import c_float, c_int
import logging
import time

from Host.autogen import interface, usbdefs
from Host.Common.analyzerUsbIf import AnalyzerUsb
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log
from Host.Common.FpgaProgrammer import FpgaProgrammer
from Host.Common.HostToDspSender import HostToDspSender
from Host.Common.SharedTypes import Singleton
from Host.Common.SharedTypes import UsbConnectionError
from Host.Common.StateDatabase import SensorHistory, StateDatabase

EventManagerProxy_Init(APP_NAME)

class DasInterface(Singleton):
    initialized = False

    def __init__(self, stateDbFile=None, usbFile=None, dspFile=None, fpgaFile=None):
        if not self.initialized:
            self.stateDatabase = StateDatabase(stateDbFile, Log)
            self.sensorHistory = SensorHistory()
            self.usbFile = usbFile
            self.dspFile = dspFile
            self.fpgaFile = fpgaFile
            self.analyzerUsb = None
            self.hostToDspSender = None
            self.stateDb = None
            self.lastMessageTime = 0
            self.lastSensorTime = 0
            self.lastRingdownTime = 0
            self.messageIndex = 0
            self.sensorIndex = 0
            self.ringdownIndex = 0
            self.initialized = True
        elif stateDbFile is not None:
            raise ValueError("DasInterface has already been initialized")

    def loadUsbIfCode(self,usbCodeFilename):
        """Downloads file to USB Cypress FX2 chip,
        if not already downloaded"""
        analyzerUsb = AnalyzerUsb(usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        try: # connecting to a programmed Picarro instrument
            analyzerUsb.connect()
            analyzerUsb.disconnect()
            return
        except UsbConnectionError:
            try:  # connecting to an unprogrammed Picarro instrument. This will be useful when we get our own VID.
                analyzerUsb = AnalyzerUsb(usbdefs.INITIAL_VID,usbdefs.INITIAL_PID)
                analyzerUsb.connect(claim=False)
            except UsbConnectionError:
                try: # connecting to a blank Cypress FX2
                    analyzerUsb = AnalyzerUsb(usbdefs.CYPRESS_FX2_VID,usbdefs.CYPRESS_FX2_PID)
                    analyzerUsb.connect(claim=False)
                except UsbConnectionError:
                    raise RuntimeError("Cannot connect to USB")
        logging.info("Downloading USB code to Picarro USB device")
        analyzerUsb.loadHexFile(usbCodeFilename)
        analyzerUsb.disconnect()
        # Wait for renumeration
        while True:
            analyzerUsb = AnalyzerUsb(
                usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
            try:
                analyzerUsb.connect()
                break
            except UsbConnectionError:
                time.sleep(1.0)
        analyzerUsb.disconnect()

    def startUsb(self):
        """Connect to USB interface on logic board.
        """
        self.loadUsbIfCode(self.usbFile)
        self.analyzerUsb = AnalyzerUsb(
                usbdefs.INSTRUMENT_VID,usbdefs.INSTRUMENT_PID)
        self.analyzerUsb.connect()
        return self.analyzerUsb.getUsbSpeed()

    def programAll(self):
        """Program all processors on logic board.
        """
        Log("Holding DSP in reset...")
        self.analyzerUsb.setDspControl(usbdefs.VENDOR_DSP_CONTROL_RESET)
        #raw_input("Press <Enter> to program FPGA")
        Log("Starting to program FPGA...")
        fpgaProgrammer = FpgaProgrammer(self.analyzerUsb, Log)
        fpgaProgrammer.program(self.fpgaFile)
        self.analyzerUsb.setDspControl(0)
        time.sleep(0.5)
        self.hostToDspSender = HostToDspSender(self.analyzerUsb,5.0)
        self.hostToDspSender.program(self.dspFile)
        
    def getMessage(self):
        """Retrieves message from the analyzer or None if nothing is available"""
        timestamp = self.hostToDspSender.rdMessageTimestamp(self.messageIndex)
        if timestamp != 0 and timestamp >= self.lastMessageTime:
            msg = self.hostToDspSender.rdMessage(self.messageIndex)
            self.lastMessageTime = timestamp
            self.messageIndex += 1
            if self.messageIndex >= interface.NUM_MESSAGES:
                self.messageIndex = 0
            return timestamp, msg
                
    def getSensorData(self):
        """Retrieves sensor data from the analyzer or None if nothing is available"""
        data = self.hostToDspSender.rdSensorData(self.sensorIndex)
        if data.timestamp != 0 and data.timestamp >= self.lastSensorTime:
            self.lastSensorTime = data.timestamp
            self.sensorIndex += 1
            if self.sensorIndex >= interface.NUM_SENSOR_ENTRIES:
                self.sensorIndex = 0
            self.sensorHistory.record(data)
            return data

    def getSensorDataBlock(self):
        """Retrieves a block of sensor data from the analyzer. If there are valid entries in the block, the number  is 
        computed and returned together with the block itself. If there are no valid entries, return None."""
        block = self.hostToDspSender.rdSensorDataBlock(self.sensorIndex)
        validEntries = 0
        for data in block:
            if data.timestamp != 0 and data.timestamp >= self.lastSensorTime:
                self.lastSensorTime = data.timestamp
                validEntries += 1
                self.sensorIndex += 1
                if self.sensorIndex >= interface.NUM_SENSOR_ENTRIES:
                    self.sensorIndex = 0
                self.sensorHistory.record(data)
            else:
                break
        return { 'block': block, 'validEntries': validEntries } if validEntries > 0 else None
                
    def getRingdownData(self):
        """Retrieves ringdown data from the analyzer or None if nothing is available"""
        data = self.hostToDspSender.rdRingdownData(
              self.ringdownIndex)
        if data.timestamp != 0 and data.timestamp >= self.lastRingdownTime:
            self.lastRingdownTime = data.timestamp
            self.ringdownIndex += 1
            if self.ringdownIndex >= interface.NUM_RINGDOWN_ENTRIES:
                self.ringdownIndex = 0
            return data

    def getRingdownDataBlock(self):
        """Retrieves a block of ringdown data from the analyzer. If there are valid entries in the block, 
        the number is computed and returned together with the block itself. If there are no valid entries, 
        return None."""
        block = self.hostToDspSender.rdRingdownDataBlock(
              self.ringdownIndex)
        validEntries = 0
        for data in block:
            if data.timestamp != 0 and data.timestamp >= self.lastRingdownTime:
                self.lastRingdownTime = data.timestamp
                validEntries += 1
                self.ringdownIndex += 1
                if self.ringdownIndex >= interface.NUM_RINGDOWN_ENTRIES:
                    self.ringdownIndex = 0
            else:
                break
        return { 'block': block, 'validEntries': validEntries } if validEntries > 0 else None

    def uploadSchedule(self,operationGroups):
        """Upload all operation groups to the scheduler in the instrument.
        """
        def shorts2int(lsw, msw):
            """Convert two shorts into an int.
            """
            return int(((msw << 16) | lsw) & 0xFFFFFFFF)
        groupTable = []
        operationTable = []
        operandTable = []
        for group in operationGroups:
            operationAddress = len(operationTable)
            priority_and_period = (group.priority << 12) + group.period
            groupTable.append(
                shorts2int(priority_and_period,operationAddress))
            for operation in group.operationList:
                operandAddress = len(operandTable)
                operationTable.append(
                    (shorts2int(operation.opcode, len(operation.operandList)),
                                     shorts2int(operandAddress, operation.env))
                )
                for opr in operation.operandList:
                    operandTable.append(int(opr))
            operationTable.append((0,0))
        groupTable.append(0)
        if len(groupTable) > interface.GROUP_TABLE_SIZE:
            raise ValueError(
                "%d operation groups needed, only %d available" %
                (len(groupTable),interface.GROUP_TABLE_SIZE))
        if len(operationTable) > interface.NUM_OPERATIONS:
            raise ValueError(
                "%d operations needed, only %d available" %
                (len(operationTable),interface.OPERATION_TABLE_SIZE))
        if len(operandTable) > interface.OPERAND_TABLE_SIZE:
            raise ValueError(
                "%d operands needed, only %d available" %
                (len(operandTable),interface.OPERAND_TABLE_SIZE))
        self.hostToDspSender.wrBlock(interface.GROUP_OFFSET, *groupTable)
        # Flatten the tuples in the operation table to send it to the
        #  analyzer
        flatOperations = []
        for operation in operationTable:
            flatOperations += operation
        self.hostToDspSender.wrBlock(interface.OPERATION_OFFSET, *flatOperations)
        self.hostToDspSender.wrBlock(interface.OPERAND_OFFSET, *operandTable)

    def getSchedule(self):
        """Returns the group, operation and operand tables, mainly for
        diagnostic purposes"""
        return dict(
            groupTable=self.hostToDspSender.rdBlock(
                interface.GROUP_OFFSET,interface.GROUP_TABLE_SIZE),
            operationTable=self.hostToDspSender.rdBlock(
                interface.OPERATION_OFFSET,
                interface.OPERATION_TABLE_SIZE),
            operandTable=self.hostToDspSender.rdBlock(
                interface.OPERAND_OFFSET,interface.OPERAND_TABLE_SIZE))

    def saveDasState(self):
        """Write out all register contents to an SQLite database"""
        floatRegList = []
        intRegList = []
        for regInfo in interface.registerInfo:
            if regInfo.type == c_float:
                floatRegList.append((regInfo.name,
                                     self.hostToDspSender.rdRegFloat(regInfo.name)))
            else:
                value = self.hostToDspSender.rdRegUint(regInfo.name)
                if regInfo.type == c_int:
                    if value >= 1 << 31:
                        value -= 1 << 32
                intRegList.append((regInfo.name, value))
        self.stateDatabase.saveFloatRegList(floatRegList)
        self.stateDatabase.saveIntRegList(intRegList)

    def loadDasState(self):
        """Read in all register contents from an SQLite database"""
        floatRegList = self.stateDatabase.getFloatRegList()
        intRegList = self.stateDatabase.getIntRegList()
        for name,value in floatRegList:
            try:
                regNum = interface.registerByName[name]
                if interface.registerInfo[regNum].writable:
                    self.hostToDspSender.wrRegFloat(name,value)
            except AttributeError:
                print "Register %s in database is unrecognized" % name
        for name,value in intRegList:
            try:
                regNum = interface.registerByName[name]
                if interface.registerInfo[regNum].writable:
                    self.hostToDspSender.wrRegUint(name,value)
            except AttributeError:
                print "Register %s in database is unrecognized" % name

    def pingWatchdog(self):
        self.analyzerUsb.pingWatchdog()
