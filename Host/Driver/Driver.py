#!/usr/bin/python
#
# FILE:
#   Driver.py
#
# DESCRIPTION:
#   Low-level communication with hardware via USB interface
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   07-Jan-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import ctypes
import getopt
import inspect
import os
import sys
import tables
import threading
import time
import types
import traceback
from configobj import ConfigObj

from Host.autogen import interface
from Host.Common import SharedTypes, version
from Host.Common import CmdFIFO, StringPickler, timestamp
from Host.Common.Broadcaster import Broadcaster
from Host.Common.hostDasInterface import DasInterface, HostToDspSender
from Host.Common.SingleInstance import SingleInstance
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from DasConfigure import DasConfigure

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
EventManagerProxy_Init("Driver")
#
# The driver provides a serialized RPC interface for accessing the DAS hardware.
#
class DriverRpcHandler(SharedTypes.Singleton):
    def __init__(self,config,dasInterface):
        self.server = CmdFIFO.CmdFIFOServer(("", SharedTypes.RPC_PORT_DRIVER),
                                             ServerName = "Driver",
                                             ServerDescription = "Driver for CRDS hardware",
                                             threaded = True)
        self.config = config
        self.dasInterface = dasInterface
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
                #if __debug__: print "registering", s
                self.server.register_function(attr,DefaultMode=CmdFIFO.CMD_TYPE_Blocking)

    def _register_rpc_functions(self):
        """ Registers the functions accessible by XML-RPC """
        #register the functions contained in this file...
        self._register_rpc_functions_for_object( self )
        #register some priority functions that can be used even while the Driver
        #is performing a lengthy upload...
        # server._register_priority_function(self.rdDasReg, "HP_rdDasReg")
        # server._register_priority_function(self._getLockStatus, NameSlice = 1)
        Log("Registered RPC functions")

    def allVersions(self):
        versionDict = {}
        versionDict["interface"] = interface.interface_version
        versionDict["host"] = version.versionString()
        return versionDict

    def _reg_index(self,indexOrName):
        """Convert a name or index into an integer index, raising an exception if the name is not found"""
        if isinstance(indexOrName,types.IntType):
            return indexOrName
        else:
            try:
                return interface.registerByName[indexOrName.strip().upper()]
            except KeyError:
                raise SharedTypes.DasException("Unknown register name %s" % (indexOrName,))

    def rdDasReg(self,regIndexOrName):
        """Reads a DAS register, using either its index or symbolic name"""
        index = self._reg_index(regIndexOrName)
        ri = interface.registerInfo[index]
        if not ri.readable:
            raise SharedTypes.DasAccessException("Register %s is not readable" % (regIndexOrName,))
        if ri.type == ctypes.c_float:
            return self.dasInterface.hostToDspSender.rdRegFloat(index)
        else:
            return self.dasInterface.hostToDspSender.rdRegUint(index)

    def rdDasRegList(self,regList):
        return [self.rdDasReg(reg) for reg in regList]

    def _value(self,valueOrName):
        """Convert valueOrName into an value, raising an exception if the name is not found"""
        if isinstance(valueOrName,types.StringType):
            try:
                valueOrName = getattr(interface,valueOrName)
            except AttributeError:
                raise AttributeError("Value identifier not recognized %r" % valueOrName)
        return valueOrName

    def wrDasRegList(self,regList,values):
        for r,value in zip(regList,values):
            self.wrDasReg(r,value)

    def wrDasReg(self,regIndexOrName,value,convert=True):
        """Writes to a DAS register, using either its index or symbolic name. If convert is True,
            value is a symbolic string that is looked up in the interface definition file. """
        if convert:
            value = self._value(value)
        index = self._reg_index(regIndexOrName)
        ri = interface.registerInfo[index]
        if not ri.writable:
            raise SharedTypes.DasAccessException("Register %s is not writable" % (regIndexOrName,))
        if ri.type == ctypes.c_uint:
            return self.dasInterface.hostToDspSender.wrRegUint(index,value)
        elif ri.type == ctypes.c_float:
            return self.dasInterface.hostToDspSender.wrRegFloat(index,value)
        else:
            raise SharedTypes.DasException("Type %s of register %s is not known" % (ri.type,regIndexOrName,))

    def loadIniFile(self):
        """Loads state from instrument configuration file"""
        config = InstrumentConfig()
        config.reloadFile()
        config.loadPersistentRegistersFromConfig()
        Log("Loaded instrument configuration from file %s" % \
            config.filename,Level=1)

    def writeIniFile(self,filename=None):
        """Writes out the current instrument configuration to the
            specified filename, or to the one specified in the driver
            configuration file"""
        config = InstrumentConfig()
        config.savePersistentRegistersToConfig()
        name = config.writeConfig(filename)
        Log("Saved instrument configuration to file %s" % (name,),Level=1)


class StreamTableType(tables.IsDescription):
    time = tables.Int64Col()
    streamNum = tables.Int32Col()
    value = tables.Float32Col()
class StreamSaver(SharedTypes.Singleton):
    initialized = False
    def __init__(self,config=None):
        if not self.initialized:
            self.fileName = ""
            self.table = None
            self.h5 = None
            self.config = config
            self.lastWrite = 0
            self.initialized = True
            self.observerAccess = {}

    def registerStreamStatusObserver(self,observerRpcPort,observerToken):
        if not(observerRpcPort in self.observerAccess):
            serverURI = "http://%s:%d" % ("localhost",observerRpcPort)
            proxy = CmdFIFO.CmdFIFOServerProxy(serverURI,
                        ClientName="StreamStatusNotifier")
        else:
            proxy = self.observerAccess[observerRpcPort][0]
        self.observerAccess[observerRpcPort] = (proxy,observerToken)
        proxy.SetFunctionMode("notify",CmdFIFO.CMD_TYPE_VerifyOnly)

    def unregisterStreamStatusObserver(self,observerRpcPort):
        del self.observerAccess[observerRpcPort]

    def _informObservers(self):
        for o in self.observerAccess:
            proxy,observerToken = self.observerAccess[o]
            proxy.notify(observerToken)

    def openStreamFile(self):
        if self.h5:
            self.closeStreamFile()
        try:
            f = time.strftime(self.config["Files"]["streamFileName"])
        except:
            Log("Config option streamFileName not found in [Files] section. Using default.",Level=2)
            f = time.strftime("Sensors_%Y%m%d_%H%M%S.h5")
        self.fileName = os.path.join(os.path.dirname(AppPath),f)
        Log("Opening stream file %s" % self.fileName)
        self.lastWrite = 0
        handle = tables.openFile(self.fileName,mode="w",title="CRDS Sensor Stream File")
        filters = tables.Filters(complevel=1,fletcher32=True)
        self.table = handle.createTable(handle.root,"sensors",StreamTableType,filters=filters)
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
            row["value"] = data.value.asFloat
            row.append()
            if data.timestamp-self.lastWrite > 5000:
                self.table.flush()
                self.lastWrite = data.timestamp

class Driver(SharedTypes.Singleton):
    def __init__(self,sim,configFile):
        self.config = ConfigObj(configFile)
        self.appDir = os.path.dirname(AppPath)
        self.stateDbFile = os.path.join(self.appDir,
            self.config["Files"]["instrStateFileName"])
        self.instrConfigFile = os.path.join(self.appDir,
            self.config["Files"]["instrConfigFileName"])
        self.usbFile  = "../../CypressUSB/analyzer/analyzerUsb.hex"
        self.dspFile  = "../../DSP/registerTest/Debug/registerTest.hex"
        self.fpgaFile = "../../MyHDL/Spartan3/top_io_map.bit"
        self.dasInterface = DasInterface(self.stateDbFile,self.usbFile,
                                self.dspFile,self.fpgaFile,sim)
        self.rpcHandler = DriverRpcHandler(self.config,self.dasInterface)
        InstrumentConfig(self.instrConfigFile)
        self.streamSaver = StreamSaver(self.config)
        self.rpcHandler._register_rpc_functions_for_object(self.streamSaver)
        self.streamCast = Broadcaster(
            port=SharedTypes.BROADCAST_PORT_SENSORSTREAM,
            name="CRDI Stream Broadcaster",logFunc=Log)
        self.lastSaveDasState = 0
    def run(self):
        try:
            # Ensure that we connect in high speed mode
            for attempts in range(10):
                usbSpeed = self.dasInterface.startUsb()
                Log("USB enumerated at %s speed" % (("full","high")[usbSpeed]))
                if usbSpeed: break
                self.dasInterface.analyzerUsb.reconnectUsb()
                time.sleep(2.0)
            self.dasInterface.upload()
            time.sleep(1.0) # For DSP code to initialize
            self.dasInterface.loadDasState() # Restore DAS state
            DasConfigure(self.dasInterface).run()
            daemon = self.rpcHandler.server.daemon
            Log("DAS firmware uploaded",Level=1)
            while not daemon.mustShutdown:
                daemon.handleRequests(0.2)
                for data in self.dasInterface.getSensorData():
                    self.streamCast.send(StringPickler.ObjAsString(data))
                    self.streamSaver._writeData(data)
                for ts,msg in self.dasInterface.getMessages():
                    Log("%s %s" % (ts,msg))
                now = time.time()
                # Periodically save the state of the DAS
                if now > self.lastSaveDasState + 30.0:
                    self.dasInterface.saveDasState()
                    self.lastSaveDasState = now
            Log("Driver RPC handler shut down")
        except:
            type,value,trace = sys.exc_info()
            Log("Unhandled Exception: %s: %s" % (str(type),str(value)),
                Verbose=traceback.format_exc(),Level=3)
        finally:
            self.dasInterface.saveDasState()

class InstrumentConfig(SharedTypes.Singleton):
    """Configuration of instrument. Note that the DAS state is NOT loaded
    automatically from the configuration."""
    def __init__(self,filename=None):
        if filename is not None:
            self.config = ConfigObj(filename)
            self.filename = filename

    def reloadFile(self):
        self.config = ConfigObj(self.filename)

    def savePersistentRegistersToConfig(self):
        s = HostToDspSender()
        if "DASregisters" not in self.config:
            self.config["DASregisters"] = {}
        for ri in interface.registerInfo:
            if ri.persistence:
                if ri.type == ctypes.c_float:
                    self.config["DASregisters"][ri.name]= \
                        s.rdRegFloat(ri.name)
                else:
                    self.config["DASregisters"][ri.name]= \
                        ri.type(s.rdRegUint(ri.name)).value

    def loadPersistentRegistersFromConfig(self):
        s = HostToDspSender()
        if "DASregisters" not in self.config:
            self.config["DASregisters"] = {}
        for name in self.config["DASregisters"]:
            if name not in interface.registerByName:
                Log("Unknown register %s ignored during config file load" % name,Level=2)
            else:
                index = interface.registerByName[name]
                ri = interface.registerInfo[index]
                if ri.writable:
                    if ri.type == ctypes.c_float:
                        value = float(self.config["DASregisters"][ri.name])
                        s.wrRegFloat(ri.name,value)
                    else:
                        value = ctypes.c_uint(
                            int(self.config["DASregisters"][ri.name])).value
                        s.wrRegUint(ri.name,value)
                else:
                    Log("Unwritable register %s ignored during config file load" % name,Level=2)

    def writeConfig(self,filename=None):
        if filename is None:
            filename = self.filename
            self.config.write()
        else:
            fp = file(filename,"wa")
            self.config.write(fp)
            fp.close
        return filename


HELP_STRING = """Driver.py [-s|--simulation] [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-s, --simulation     run in simulation mode
-c                   specify a config file:  default = "./Driver.ini"
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hsc:'
    longOpts = ["help", "simulation"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/Driver.ini"
    simulation = False
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    if "-s" in options or "--simulation" in options:
        simulation = True
    return (simulation, configFile)

if __name__ == "__main__":
    driverApp = SingleInstance("PicarroDriver")
    if driverApp.alreadyrunning():
        Log("Instance of driver us already running",Level=3)
    else:
        sim, configFile = handleCommandSwitches()
        Log("Driver starting, sim: %d, configFile: %s" % (sim,configFile))
        d = Driver(sim,configFile)
        d.run()
    Log("Driver exiting")
    time.sleep(1)
