#!/usr/bin/python
#
"""
File Name: DriverSimulator.py
Purpose: Simulation of Driver for diagnostic purposes

File History:
    18-Sep-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""

from configobj import ConfigObj
import ctypes
import getopt
import inspect
import os
import pprint
import sys
import tables
import time
import traceback
import types

from Host.autogen import interface
from Host.Common import (
    CmdFIFO, SchemeProcessor, SharedTypes, StringPickler, timestamp)
from Host.Common.Broadcaster import Broadcaster
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.SharedTypes import getSchemeTableClass, Operation, RPC_PORT_DRIVER
from Host.Common.SingleInstance import SingleInstance
from Host.Driver.DasConfigure import DasConfigure
from Host.DriverSimulator.DasSimulator import DasSimulator
from Host.DriverSimulator.SpectraSimulator import SpectraSimulator

# If we are using python 2.x on Linux, use the subprocess32
# module which has many bug fixes and can prevent
# subprocess deadlocks.
#
if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess

APP_NAME = "DriverSimulator"
try:
    # Release build
    from Host.Common import release_version as version
except ImportError:
    try:
        # Internal build
        from Host.Common import setup_version as version
    except ImportError:
        # Internal dev
        from Host.Common import version

EventManagerProxy_Init(APP_NAME)

if hasattr(sys, "frozen"):  # we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

if __debug__:
    print("Loading rpdb2")
    import rpdb2
    rpdb2.start_embedded_debugger("hostdbg",timeout=0)
    print("rpdb2 loaded")


def _reg_index(indexOrName):
    """Convert a name or index into an integer index, raising an exception if the name is not found"""
    if isinstance(indexOrName, types.IntType):
        return indexOrName
    else:
        try:
            return interface.registerByName[indexOrName.strip().upper()]
        except KeyError:
            raise SharedTypes.DasException("Unknown register name %s" % (indexOrName,))


def _value(valueOrName):
    """Convert valueOrName into an value, raising an exception if the name is not found"""
    if isinstance(valueOrName, types.UnicodeType):
        valueOrName = str(valueOrName)
    if isinstance(valueOrName, types.StringType):
        try:
            valueOrName = getattr(interface,valueOrName)
        except AttributeError:
            raise AttributeError("Value identifier not recognized %r" % valueOrName)
    return valueOrName


#
# The driver provides a serialized RPC interface for accessing the DAS hardware.
#
class DriverRpcHandler(SharedTypes.Singleton):
    def __init__(self, driver):
        self.server = CmdFIFO.CmdFIFOServer(("", RPC_PORT_DRIVER),
                                            ServerName="Driver",
                                            ServerDescription="Driver for CRDS hardware",
                                            threaded=True)
        self.config = driver.config
        self.ver = driver.ver
        self.driver = driver
        self.dasSimulator = driver.dasSimulator
        self._register_rpc_functions()

    def _register_rpc_functions_for_object(self, obj):
        """ Registers the functions in DriverRpcHandler class which are accessible by XML-RPC

        NOTE - this automatically registers ALL member functions that don't start with '_'.

        i.e.:
          - if adding new rpc calls, just define them (with no _) and you're done
          - if putting helper calls in the class for some reason, use a _ prefix
        """
        classDir = dir(obj)
        for s in classDir:
            attr = obj.__getattribute__(s)
            if callable(attr) and (not s.startswith("_")) and (not inspect.isclass(attr)):
                self.server.register_function(attr, DefaultMode=CmdFIFO.CMD_TYPE_Blocking)

    def _register_rpc_functions(self):
        """ Registers the functions accessible by XML-RPC """
        # register the functions contained in this file...
        self._register_rpc_functions_for_object(self)
        Log("Registered RPC functions")

    def allVersions(self):
        versionDict = {}
        versionDict["interface"] = interface.interface_version
        try:
            versionDict["host release"] = version.versionString()
        except:
            versionDict["host release"] = "Experimental"
        try:
            versionDict["config - app version no"] = self.ver["appVer"]
            versionDict["config - instr version no"] = self.ver["instrVer"]
            versionDict["config - common version no"] = self.ver["commonVer"]
        except Exception, err:
            print err
        Log("version = %s" % pprint.pformat(versionDict))
        return versionDict

    def dasGetTicks(self):
        sender = self.dasSimulator.hostToDspSender
        sender.doOperation(Operation("ACTION_GET_TIMESTAMP", ["TIMESTAMP_LSB_REGISTER","TIMESTAMP_MSB_REGISTER"]))
        return self.rdDasReg("TIMESTAMP_MSB_REGISTER")<<32L | self.rdDasReg("TIMESTAMP_LSB_REGISTER")

    def getConfigFile(self):
        configFile = os.path.normpath(os.path.abspath(self.driver.instrConfig.filename))
        return configFile

    def getParameterForms(self):
        """Returns the dictionary of parameter forms for the controller GUI"""
        return interface.parameter_forms

    def getSpectCntrlMode(self):
        return self.rdDasReg(interface.SPECT_CNTRL_MODE_REGISTER)

    def hostGetTicks(self):
        return timestamp.getTimestamp()

    def interfaceValue(self, valueOrName):
        """Ask Driver to lookup a symbol in the context of the current interface"""
        try:
            return self._value(valueOrName)
        except:
            return "undefined"

    def loadIniFile(self):
        """Loads state from instrument configuration file"""
        SchemeProcessor.clearMemo()
        config = self.driver.instrConfig
        config.reloadFile()
        config.loadPersistentRegistersFromConfig()
        Log("Loaded instrument configuration from file %s" %
            config.filename, Level=1)

    def rdDasReg(self, regIndexOrName):
        return self.driver.rdDasReg(regIndexOrName)

    def rdDasRegList(self, regList):
        return [self.rdDasReg(reg) for reg in regList]

    def rdFPGA(self, base, reg):
        return self.driver.rdFPGA(base, reg)

    def rdRegList(self, regList):
        result = []
        for regLoc, reg in regList:
            if regLoc == "dsp":
                result.append(self.rdDasReg(reg))
            elif regLoc == "fpga":
                result.append(self.rdFPGA(0, reg))
            else:
                result.append(None)
        return result

    def rdScheme(self, schemeNum):
        """Read a scheme into a scheme table in the DSP.

        Args:
            schemeNum: Scheme table number (0 origin)
        Returns:
            A dictionary with numRepeats as the number of repetitions and schemeRows as a list of
            7-tuples containing:
            (setpoint, dwellCount, subschemeId, virtualLaser, threshold, pztSetpoint, laserTemp)

        """
        assert isinstance(schemeNum, (int, long))
        schemeTable = self.driver.schemeTables[schemeNum]
        # Read from scheme table schemeNum
        return {"numRepeats": schemeTable.numRepeats,
                "schemeRows": [(row.setpoint, row.dwellCount, row.subschemeId, row.virtualLaser,
                               row.threshold, row.pztSetpoint, 0.001 * row.laserTemp) for row in schemeTable.rows]}

    def restoreRegValues(self,vault):
        # Restore register values stored in the vault (produced by saveRegValues)
        for reg, value in vault:
            if isinstance(reg, (tuple, list)):
                if len(reg) != 2:
                    raise ValueError("An FPGA register description tuple must have two elements")
                else:
                    self.wrFPGA(reg[0], reg[1], value)
            else:
                self.wrDasReg(reg, value)

    def saveRegValues(self, regList):
        # Save the values of the registers specified in regList into a "vault" which can later
        #  be used to restore them with restoreRegValues. The elements of regList can be integers
        #  representing DSP registers or tuples of integers representing FPGA registers in
        #  (block,offset) pairs. These integers may be referred to symbolically by passing strings
        #  which are looked up in the interface file.
        vault = []
        for reg in regList:
            if isinstance(reg, (tuple, list)):
                if len(reg) != 2:
                    raise ValueError("An FPGA register description tuple must have two elements")
                else:
                    vault.append((reg, self.rdFPGA(*reg)))
            else:
                vault.append((reg, self.rdDasReg(reg)))
        return vault

    def saveWlmHist(self, wlmHist):
        pass

    def scanIdle(self):
        return self.rdDasReg(interface.SPECT_CNTRL_STATE_REGISTER) == interface.SPECT_CNTRL_IdleState

    def selectActualLaser(self,aLaserNum):
        # Select laserNum, placing it under automatic control and activating the optical switch. The value
        #  of aLaserNum is ONE-based
        injControl = self.rdFPGA("FPGA_INJECT", "INJECT_CONTROL")
        if aLaserNum <= 0 or aLaserNum > interface.MAX_LASERS:
            raise ValueError("aLaserNum must be in range 1..4 for selectActualLaser")
        laserSel = (aLaserNum-1) << interface.INJECT_CONTROL_LASER_SELECT_B
        laserMask = (interface.MAX_LASERS-1) << interface.INJECT_CONTROL_LASER_SELECT_B
        injControl = (injControl & (~laserMask)) | laserSel
        self.wrFPGA("FPGA_INJECT", "INJECT_CONTROL",injControl)

    def setMultipleNoRepeatScan(self):
        self.wrDasReg(interface.SPECT_CNTRL_MODE_REGISTER, interface.SPECT_CNTRL_SchemeMultipleNoRepeatMode)

    def setMultipleScan(self):
        self.wrDasReg(interface.SPECT_CNTRL_MODE_REGISTER, interface.SPECT_CNTRL_SchemeMultipleMode)

    def setSingleScan(self):
        self.wrDasReg(interface.SPECT_CNTRL_MODE_REGISTER, interface.SPECT_CNTRL_SchemeSingleMode)

    def startScan(self):
        self.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER, interface.SPECT_CNTRL_StartingState)

    def startEngine(self):
        # Turn on lasers, warm box and cavity thermal control followed by
        #  laser current sources
        for laserNum in xrange(1, interface.MAX_LASERS + 1):
            if self.driver.dasConfigure.installCheck("LASER%d_PRESENT" % laserNum) or \
               (laserNum == 4 and self.driver.dasConfigure.installCheck("SOA_PRESENT")):
                self.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % laserNum,interface.TEMP_CNTRL_EnabledState)
        self.wrDasReg("WARM_BOX_TEMP_CNTRL_STATE_REGISTER",interface.TEMP_CNTRL_EnabledState)
        self.wrDasReg("CAVITY_TEMP_CNTRL_STATE_REGISTER",interface.TEMP_CNTRL_EnabledState)
        if self.driver.dasConfigure.heaterCntrlMode in [interface.HEATER_CNTRL_MODE_DELTA_TEMP,interface.HEATER_CNTRL_MODE_TEC_TARGET]:
            self.wrDasReg("HEATER_TEMP_CNTRL_STATE_REGISTER",interface.TEMP_CNTRL_EnabledState)
        elif self.driver.dasConfigure.heaterCntrlMode in [interface.HEATER_CNTRL_MODE_HEATER_FIXED]:
            self.wrDasReg("HEATER_TEMP_CNTRL_STATE_REGISTER",interface.TEMP_CNTRL_ManualState)
        self.wrDasReg("TEC_CNTRL_REGISTER", interface.TEC_CNTRL_Enabled)
        for laserNum in xrange(1, interface.MAX_LASERS+1):
            if self.driver.dasConfigure. installCheck("LASER%d_PRESENT" % laserNum):
                self.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % laserNum,interface.LASER_CURRENT_CNTRL_ManualState)

    def stopScan(self):
        self.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER,interface.SPECT_CNTRL_IdleState)

    def wrDasReg(self, regIndexOrName, value, convert=True):
        return self.driver.wrDasReg(regIndexOrName, value, convert)

    def wrDasRegList(self, regList, values):
        for r, value in zip(regList,values):
            self.wrDasReg(r, value)

    def wrFPGA(self, base, reg, value, convert=True):
        return self.driver.wrFPGA(base, reg, value, convert)

    def writeIniFile(self, filename=None):
        """Writes out the current instrument configuration to the
            specified filename, or to the one specified in the driver
            configuration file"""
        config = self.driver.instrConfig
        config.savePersistentRegistersToConfig()
        name = config.writeConfig(filename)
        Log("Saved instrument configuration to file %s" % (name,),Level=1)

    def wrRegList(self, regList, values):
        for (regLoc, reg), value in zip(regList, values):
            if regLoc == "dsp":
                self.wrDasReg(reg, value)
            elif regLoc == "fpga":
                self.wrFPGA(0, reg, value)

    def wrScheme(self, schemeNum, numRepeats, schemeRows):
        """Write a scheme into a scheme table.
            Args:
            schemeNum: Scheme table number (0 origin)
            numRepeats: Number of repetitions of the scheme
            schemeRows: A list of rows, where each row has up to 7 entries
        """
        assert isinstance(schemeNum, (int, long))
        assert isinstance(numRepeats, (int, long))
        assert hasattr(schemeRows, '__iter__')
        schemeTable = getSchemeTableClass(len(schemeRows))()
        schemeTable.numRepeats = numRepeats
        schemeTable.numRows = len(schemeRows)
        for i, row in enumerate(schemeRows):
            schemeTable.rows[i].setpoint = float(row[0])
            schemeTable.rows[i].dwellCount = int(row[1])
            schemeTable.rows[i].subschemeId = int(row[2]) if len(row) >= 3 else 0
            schemeTable.rows[i].virtualLaser = int(row[3]) if len(row) >= 4 else 0
            schemeTable.rows[i].threshold = int(row[4]) if len(row) >= 5 else 0
            schemeTable.rows[i].pztSetpoint = int(row[5]) if len(row) >= 6 else 0
            schemeTable.rows[i].laserTemp = int(1000 * row[6]) if len(row) >= 7 else 0
        self.driver.schemeTables[schemeNum] = schemeTable

    def wrVirtualLaserParams(self, vLaserNum, laserParams):
        """Wites the virtual laser parameters (specified as a dictionary) associated with
           virtual laser vLaserNum (ONE-based).
           N.B. The "actualLaser" field within the VirtualLaserParams structure is ZERO-based
           for compatibility with the DAS software
        """
        self.driver.virtualLaserParams[vLaserNum] = laserParams
        Log("Virtual laser %d" % vLaserNum, Data=laserParams)


class DriverSimulator(SharedTypes.Singleton):
    def __init__(self, configFile):
        self.looping = True
        self.config = ConfigObj(configFile)
        self.dasSimulator = DasSimulator(self)
        basePath = os.path.split(os.path.normpath(os.path.abspath(configFile)))[0]
        # Set up automatic streaming file for sensors, if startStreamFile
        # option in the [Config] section is present. Also allow the maximum
        # number of lines in the stream file to be set
        self.autoStreamFile = False
        maxStreamLines = 0
        try:
            if int(self.config["Config"]["startStreamFile"]):
                self.autoStreamFiledasConfigure = True
            maxStreamLines = int(self.config["Config"]["maxStreamLines"])
        except KeyError:
            pass
        # Get appConfig and instrConfig version number
        self.ver = {}
        for ver in ["appVer", "instrVer", "commonVer"]:
            try:
                fPath = os.path.join(basePath, self.config["Files"][ver])
                co = ConfigObj(fPath)
                self.ver[ver] = co["Version"]["revno"]
            except Exception, err:
                self.ver[ver] = "N/A"
        self.instrConfigFile = os.path.join(basePath, self.config["Files"]["instrConfigFileName"])
        self.dasConfigure = None
        self.schemeTables = {}
        self.virtualLaserParams = {}
        # Set up RPC handler
        self.rpcHandler = DriverRpcHandler(self)
        # Set up object to access master.ini file
        self.instrConfig = InstrumentConfig(self.instrConfigFile, self.rdDasReg,
                                            self.wrDasReg, self.rdFPGA, self.wrFPGA)
        # Set up object for streaming sensor data
        self.streamSaver = StreamSaver(self.config, basePath, maxStreamLines)
        self.rpcHandler._register_rpc_functions_for_object(self.streamSaver)
        # Set up the broadcasters for the sensor stream and the ringdown result stream
        self.streamCast = Broadcaster(
            port=SharedTypes.BROADCAST_PORT_SENSORSTREAM,
            name="CRDI Stream Broadcaster", logFunc=Log)
        self.resultsCast = Broadcaster(
            port=SharedTypes.BROADCAST_PORT_RDRESULTS,
            name="CRDI RD Results Broadcaster", logFunc=Log)
        self.lastSaveDasState = 0
        if self.autoStreamFile:
            self.streamSaver.openStreamFile()
        # Process the spectra simulator definition file
        self.spectraFile = os.path.join(basePath, self.config["Files"]["spectraFileName"])
        self.spectraSimulator = SpectraSimulator(self.spectraFile)

    def rdDasReg(self, regIndexOrName):
        """Reads a DAS register, using either its index or symbolic name"""
        index = _reg_index(regIndexOrName)
        ri = interface.registerInfo[index]
        if not ri.readable:
            raise SharedTypes.DasAccessException("Register %s is not readable" % (regIndexOrName,))
        return self.dasSimulator.rdDasReg(regIndexOrName)

    def rdFPGA(self, base, reg):
        return self.dasSimulator.rdFPGA(base, reg)

    def run(self):
        def messageProcessor(data):
            ts, msg = data
            if len(msg) > 2 and msg[1] == ':':
                level = int(msg[0])
                Log("%s" % (msg[2:],), Level=level)
            else:
                Log("%s" % (msg,))

        def sensorProcessor(data):
            self.streamCast.send(StringPickler.ObjAsString(data))

        def ringdownProcessor(data):
            self.resultsCast.send(StringPickler.ObjAsString(data))

        messageHandler = SharedTypes.makeHandler(self.dasSimulator.getMessage, messageProcessor)
        sensorHandler = SharedTypes.makeHandler(self.dasSimulator.getSensorData,  sensorProcessor)
        ringdownHandler = SharedTypes.makeHandler(self.dasSimulator.getRingdownData, ringdownProcessor)

        self.instrConfig.loadPersistentRegistersFromConfig()
        self.dasConfigure = DasConfigure(self.dasSimulator, self.instrConfig.config, self.config)
        self.dasConfigure.run()
        try:
            daemon = self.rpcHandler.server.daemon
            Log("Starting main driver loop", Level=1)
            maxRpcTime = 0.5
            rpcTime = 0.0
            sim = self.dasSimulator
            try:
                while self.looping and not daemon.mustShutdown:
                    timeSoFar = 0
                    messages = messageHandler.process(0.02)
                    timeSoFar += messages.duration
                    sensors = sensorHandler.process(max(0.02, 0.2 - timeSoFar))
                    timeSoFar += sensors.duration
                    ringdowns = ringdownHandler.process(max(0.02, 0.5 - timeSoFar))
                    timeSoFar += ringdowns.duration
                    # Adjust the time spent doing rpc calls for the next iteration
                    #  so that we just finish handling all the streams
                    if sensors.finished and ringdowns.finished and messages.finished:
                        rpcTime += 0.01
                        if rpcTime > maxRpcTime:
                            rpcTime = maxRpcTime
                    else:
                        rpcTime = 0.9 * rpcTime
                        if rpcTime < 0.01:
                            rpcTime = 0.01
                    requestTimeout = rpcTime
                    now = time.time()
                    doneTime = now + rpcTime
                    rpcLoops = 0
                    # Keep handling RPC requests for a duration up to "rpcTime"
                    while now < doneTime:
                        rpcLoops += 1
                        daemon.handleRequests(requestTimeout)
                        now = time.time()
                        requestTimeout = doneTime - now
                    sim.scheduler.execUntil(sim.getDasTimestamp())
                Log("Driver RPC handler shut down")
            except:
                type, value, trace = sys.exc_info()
                Log("Unhandled Exception in main loop: %s: %s" % (str(type), str(value)),
                    Verbose=traceback.format_exc(), Level=3)
        finally:
            self.rpcHandler.shutDown()

    def wrDasReg(self, regIndexOrName, value, convert=True):
        """Writes to a DAS register, using either its index or symbolic name. If convert is True,
            value is a symbolic string that is looked up in the interface definition file. """
        if convert:
            value = _value(value)
        index = _reg_index(regIndexOrName)
        ri = interface.registerInfo[index]
        if not ri.writable:
            raise SharedTypes.DasAccessException("Register %s is not writable" % (regIndexOrName,))
        return self.dasSimulator.wrDasReg(regIndexOrName, value, convert)

    def wrFPGA(self, base, reg, value, convert=True):
        return self.dasSimulator.wrFPGA(base, reg, value, convert)


class InstrumentConfig(object):
    """Configuration of instrument (typically defined by a master.ini file)"""
    def __init__(self, filename, rdDasReg, wrDasReg, rdFPGA, wrFPGA):
        self.config = ConfigObj(filename)
        self.filename = os.path.abspath(os.path.normpath(filename))
        self.rdDasReg = rdDasReg
        self.wrDasReg = wrDasReg
        self.rdFPGA = rdFPGA
        self.wrFPGA = wrFPGA

    def reloadFile(self):
        self.config = ConfigObj(self.filename)

    def savePersistentRegistersToConfig(self):
        if "DAS_REGISTERS" not in self.config:
            self.config["DAS_REGISTERS"] = {}
        for ri in interface.registerInfo:
            if ri.persistence:
                self.config["DAS_REGISTERS"][ri.name]=self.rdDasReg(ri.name)
        for fpgaMap, regList in interface.persistent_fpga_registers:
            self.config[fpgaMap] = {}
            for r in regList:
                try:
                    self.config[fpgaMap][r] = self.rdFPGA(fpgaMap, r)
                except:
                    Log("Error reading FPGA register %s in %s" % (r, fpgaMap), Level=2)

    def loadPersistentRegistersFromConfig(self):
        if "DAS_REGISTERS" not in self.config:
            self.config["DAS_REGISTERS"] = {}
        for name in self.config["DAS_REGISTERS"]:
            if name not in interface.registerByName:
                Log("Unknown register %s ignored during config file load" % name, Level=2)
            else:
                index = interface.registerByName[name]
                ri = interface.registerInfo[index]
                if ri.writable:
                    if ri.type == ctypes.c_float:
                        value = float(self.config["DAS_REGISTERS"][name])
                    else:
                        value = int(self.config["DAS_REGISTERS"][name])
                    self.wrDasReg(ri.name, value)
                else:
                    Log("Unwritable register %s ignored during config file load" % name, Level=2)
        for fpgaMap in self.config:
            if fpgaMap.startswith("FPGA"):
                for name in self.config[fpgaMap]:
                    value = int(self.config[fpgaMap][name])
                    try:
                        self.wrFPGA(fpgaMap, name, value)
                    except:
                        Log("Error writing FPGA register %s in %s" % (name,fpgaMap), Level=2)

    def writeConfig(self, filename=None):
        if filename is None:
            filename = self.filename
            self.config.write()
        else:
            fp = file(filename, "w")
            self.config.write(fp)
            fp.close
        return filename


class StreamTableType(tables.IsDescription):
    time = tables.Int64Col()
    streamNum = tables.Int32Col()
    value = tables.Float32Col()


class StreamSaver(SharedTypes.Singleton):
    initialized = False

    def __init__(self, config=None, basePath="", maxStreamLines=0):
        if not self.initialized:
            self.fileName = ""
            self.table = None
            self.h5 = None
            self.config = config
            self.basePath = basePath
            self.lastWrite = 0
            self.initialized = True
            self.observerAccess = {}
            self.streamLines = 0
            self.maxStreamLines = maxStreamLines

    # Observers can register to be notified whenever a stream file is opened or
    #  closed. On such an event an RPC call is made to the "notify" method
    #  of an RPC handler at "observerRpcPort", passing the "observerToken"
    #  to this method.
    def registerStreamStatusObserver(self, observerRpcPort, observerToken):
        if not(observerRpcPort in self.observerAccess):
            serverURI = "http://%s:%d" % ("localhost", observerRpcPort)
            proxy = CmdFIFO.CmdFIFOServerProxy(serverURI,
                                               ClientName="StreamStatusNotifier")
        else:
            proxy = self.observerAccess[observerRpcPort][0]
        self.observerAccess[observerRpcPort] = (proxy, observerToken)
        proxy.SetFunctionMode("notify", CmdFIFO.CMD_TYPE_VerifyOnly)

    def unregisterStreamStatusObserver(self, observerRpcPort):
        del self.observerAccess[observerRpcPort]

    def _informObservers(self):
        for o in self.observerAccess:
            proxy, observerToken = self.observerAccess[o]
            proxy.notify(observerToken)

    def openStreamFile(self):
        if self.h5:
            self.closeStreamFile()
        try:
            f = time.strftime(self.config["Files"]["streamFileName"])
        except:
            Log("Config option streamFileName not found in [Files] section. Using default.", Level=2)
            f = time.strftime("Sensors_%Y%m%d_%H%M%S.h5")
        self.fileName = os.path.join(self.basePath, f)
        Log("Opening stream file %s" % self.fileName)
        self.streamLines = 0
        self.lastWrite = 0
        handle = tables.openFile(self.fileName, mode="w", title="CRDS Sensor Stream File")
        filters = tables.Filters(complevel=1, fletcher32=True)
        self.table = handle.createTable(handle.root, "sensors", StreamTableType, filters=filters)
        if handle:
            self.h5 = handle
        else:
            self.fileName = ""
        self._informObservers()
        return self.fileName

    def closeStreamFile(self):
        if self.h5:
            self.table.flush()
            self.h5.close()
            Log("Closing stream file %s" % self.fileName)
            self.h5, self.fileName = None, ""
        self._informObservers()

    def getStreamFileStatus(self):
        status = "open" if self.h5 else "closed"
        return dict(status=status,filename=self.fileName)

    def _writeData(self,data):
        if self.h5:
            row = self.table.row
            row["time"] = data.timestamp
            row["streamNum"] = data.streamNum
            row["value"] = data.value
            row.append()
            self.streamLines += 1
            if data.timestamp-self.lastWrite > 5000:
                self.table.flush()
                self.lastWrite = data.timestamp
            if self.maxStreamLines > 0 and self.streamLines >= self.maxStreamLines:
                self.closeStreamFile()
                self.openStreamFile()


HELP_STRING = """DriverSimulator.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-c                   specify a config file:  default = "./Driver.ini"
"""


def printUsage():
    print HELP_STRING


def handleCommandSwitches():
    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    # assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h', "")
    # Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/DriverSimulator.ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile

if __name__ == "__main__":
    try:
        print "Hello from DriverSimulator"
        driverApp = SingleInstance("DriverSimulator")
        if driverApp.alreadyrunning():
            Log("Instance of driver simulator us already running", Level=3)
        else:
            configFile = handleCommandSwitches()
            Log("%s started." % APP_NAME, dict(ConfigFile=configFile), Level=0)
            d = DriverSimulator(configFile)
            d.run()
        Log("Exiting program")
    except Exception, e:
        LogExc("Unhandled exception trapped by last chance handler",
               Data=dict(Source="DriverSimulator"), Level=3)
    time.sleep(1)
