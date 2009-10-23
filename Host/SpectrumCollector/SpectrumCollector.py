# SpectrumCollector.py
#
# DESCRIPTION:
#   Collects spectrum and related information to save in HDF5 files. Spectrum will be stored in a queue if specified.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   12-Oct-2009  alex  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved

APP_NAME = "SpectrumCollector"

import sys
import os
import getopt
import inspect
import numpy
import Queue
import threading
import time
import ctypes
import cPickle
from tables import *

from Host.autogen import interface
from Host.autogen.interface import ProcessedRingdownEntryType
from Host.Common import CmdFIFO, Listener
from Host.Common.SharedTypes import BROADCAST_PORT_SENSORSTREAM, BROADCAST_PORT_RD_RECALC
from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR, RPC_PORT_DRIVER, RPC_PORT_ARCHIVER 
from Host.Common.SharedTypes import CrdsException
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.timestamp import unixTime
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
EventManagerProxy_Init(APP_NAME)

if sys.platform == 'win32':
    from time import clock as TimeStamp
else:
    from time import time as TimeStamp
    
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
    
# Some masks for interpreting the "subSchemeID" info (subSchemeID is basically
# a pass through, with the exception of the special increment bit 15)...
# !!! NOTE: Bit 15 is reserved for increment flag in firmware, so never use it for other purposes!!!
INCR_FLAG_MASK       = 0x8000 # 32768 - Bit 15 is used for special increment flag
SPECTRUM_IGNORE_MASK = 0x4000 # 16384 - Bit 14 is used to indicate the point should be ignored
SPECTRUM_ISCAL_MASK  = 0x1000 #  4096 - Bit 12 is used to flag a point as a cal point to be collected
SPECTRUM_SUBSECTION_ID_MASK = 0x0300
SPECTRUM_ID_MASK    = 0x00FF #Bottom 8 bits of schemeStatus are the spectrum id/name

# Type conversion dictionary for ctypes to numpy
ctypes2numpy = {ctypes.c_byte:numpy.byte, ctypes.c_char:numpy.byte, ctypes.c_double:numpy.float_,
                ctypes.c_float:numpy.single, ctypes.c_int:numpy.intc, ctypes.c_int16:numpy.int16,
                ctypes.c_int32:numpy.int32, ctypes.c_int64:numpy.int64, ctypes.c_int8:numpy.int8,
                ctypes.c_long:numpy.int_, ctypes.c_longlong:numpy.longlong, ctypes.c_short:numpy.short,
                ctypes.c_ubyte:numpy.ubyte, ctypes.c_uint:numpy.uintc, ctypes.c_uint16:numpy.uint16,
                ctypes.c_uint32:numpy.uint32, ctypes.c_uint64:numpy.uint64, ctypes.c_uint8:numpy.uint8,
                ctypes.c_ulong:numpy.uint, ctypes.c_ulonglong:numpy.ulonglong, ctypes.c_ushort:numpy.ushort}

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                     APP_NAME, IsDontCareConnection = False)

Archiver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ARCHIVER,
                                    APP_NAME,
                                    IsDontCareConnection = True)
                                    
class RingdownTimeout(CrdsException):
    """Timed out while waiting for a ringdown to arrive."""
    
class RpcServerThread(threading.Thread):
    def __init__(self, rpcServer, exitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.rpcServer = rpcServer
        self.exitFunction = exitFunction
    def run(self):
        self.rpcServer.serve_forever()
        try: #it might be a threading.Event
            self.exitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")
            
class SpectrumCollector(object):
    """A class for collecting spectrum and related information and 
    writing them to files.

    firstRdTime is the clock time of the first RD read from DAS. 
    All subsequent RDs added to the spectrum will be recorded as
    relative times from this value.

    streamDir is specified to store the output file.
    On creation of an instance, a file header is written.
    """

    def __init__(self, configPath):
        # Read from .ini file
        cp = CustomConfigObj(configPath)
        basePath = os.path.split(configPath)[0]
        self.useHDF5 = cp.getboolean("MainConfig", "useHDF5", "True")
        self.archiveGroup = cp.get("MainConfig", "archiveGroup", "RDF")
        self.streamDir = os.path.abspath(os.path.join(basePath, cp.get("MainConfig", "streamDir", "../../../Log/RDF")))
        # Make directory if not exist
        if not os.path.isdir(self.streamDir):
            os.makedirs(self.streamDir)
        Log("Created streamDir in %s" % self.streamDir)
            
        # RPC server
        self.rpcThread = None
        self._shutdownRequested = False
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_SPECTRUM_COLLECTOR),
                                                ServerName = "SpectrumCollector",
                                                ServerDescription = "Collect spectrum and related information",
                                                threaded = True)

        # Register the rpc functions...
        for s in dir(self):
            attr = self.__getattribute__(s)
            if callable(attr) and s.startswith("RPC_") and (not inspect.isclass(attr)):
                self.rpcServer.register_function(attr, NameSlice = 4)
                
        # Sensor data handling
        self.sensorListener = Listener.Listener(None, # no queuing, we'll just be tracking the latest
                                                BROADCAST_PORT_SENSORSTREAM,
                                                interface.SensorEntryType,
                                                self._sensorFilter,
                                                retry = True,
                                                name = "Spectrum collector listener",logFunc = Log)
        self.latestSensors = {}
        self.latestSensors["timestamp"] = 0.0
        for key in interface.STREAM_MemberTypeDict:
            self.latestSensors[interface.STREAM_MemberTypeDict[key][7:]] = 0.0
        self.sensorsUpdated = True
        self.cachedSensors = None 
        
        # Processed RD data (frequency-based) handling
        self.rdQueue = Queue.Queue()
        self.processedRdListener = Listener.Listener(self.rdQueue,
                                            BROADCAST_PORT_RD_RECALC,
                                            ProcessedRingdownEntryType,
                                            retry = True,
                                            name = "Spectrum collector listener",logFunc = Log)
        
        #Initialize the sensor averaging...
        self.sensorAvgCount = 0
        self.avgSensors = {}
        self.sumSensors = {}
        for key in self.latestSensors.keys():
            self.avgSensors[key] = 0.0
            self.sumSensors[key] = 0.0

        #Initialize the rdBuffer with the names and types of fields in ProcessedRingdownEntryType
        self.rdBuffer = {}
        for fname,ftype in ProcessedRingdownEntryType._fields_:
            self.rdBuffer[fname] = ([],ftype)
        
        # Compression filter for HDF5
        self.hdf5Filters = Filters(complevel=1,fletcher32=True)

        self.firstRdTime = Driver.hostGetTicks()
        self.storedFirstRdTime = Driver.hostGetTicks()
        self.enableSpectrumFiles = True
        self.spectrumQueue = None
        self.maxSpectrumQueueSize = 0
        self.closeSpectrumWhenDone = False
        self.tempRdDataBuffer = None
        self.spectrumID = 0
        self.schemeTable = 0
        self.tagalongData = {}
        self.controlData = {}            
        self.numPts = 0
        self.emptyCount = 0
        self.startWaitTime = 0
        
    def run(self):
        #start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.RPC_shutdown)
        self.rpcThread.start()
        
        lastCount = -1
        thisCount = -1
        while not self._shutdownRequested:
            #Pull a spectral point from the RD queue...
            try:
                rdData = self.getSpectralDataPoint(timeToRetry=0.5)
                if rdData is None: continue
                localRdTime = Driver.hostGetTicks()
                self.schemeTable = rdData.schemeTable
                thisSubSchemeID = rdData.subschemeId
                self.spectrumID = thisSubSchemeID & SPECTRUM_ID_MASK
                thisCount = rdData.count
                schemeStatus = rdData.status
                errDataDict = dict(schemeTable = self.schemeTable,
                                   schemeRow = rdData.schemeRow,
                                   ssID = thisSubSchemeID,
                                   spectrumID = self.spectrumID,
                                   count = thisCount,
                                   schemeStatus = schemeStatus)

                # When the "count" is different (set by DSP when bit-15 is set in the scheme file), we know a new spectrum is coming and we have to close whatever we currently have.
                if thisCount != lastCount:
                    Log("New spectrum found on ringdown (new count = %d)" % thisCount, errDataDict)
                    self.storedFirstRdTime = self.firstRdTime # Save first RD time to be used in spectrum collection of the "last" spectrum
                    self.firstRdTime = localRdTime
                    #Set aside the point we just read for the next time a spectrum is collected...
                    self.tempRdDataBuffer = rdData
                    # Close what we have collected so far
                    self.closeSpectrumWhenDone = True
                else: #still collecting the same spectrum
                    relativeRdTime = localRdTime - self.firstRdTime
                    if not (thisSubSchemeID & SPECTRUM_IGNORE_MASK):
                        self.appendPoint(rdData, relativeRdTime)
            except RingdownTimeout:
                if self.numPts > 0: 
                    Log("Closing spectrum due to ringdown timeout (count = %d)" % thisCount, Level = 0)
                    self.closeSpectrumWhenDone = True

            if self.closeSpectrumWhenDone:
                self.finish()

            lastCount = thisCount
 
        Log("Spectrum Collector RPC handler shut down")

    def getSpectralDataPoint(self, timeToRetry, timeout = 10):
        """Pops rdData out of the local ringdown queue and returns it. If there are no ringdowns
        within the timeToRetry interval, return None. Raise RingdownTimeout
        """
        if self.emptyCount == 0: 
            self.startWaitTime = time.time()
        if self.tempRdDataBuffer:
            #The last time a spectrum was read it read one too many points, and this is it.
            rdData = self.tempRdDataBuffer
            self.tempRdDataBuffer = None
            self.emptyCount = 0
        else:
            try:
                rdData = self.rdQueue.get(True,timeToRetry)
                self.emptyCount = 0
            except Queue.Empty:
                rdData = None
                self.emptyCount += 1
                if time.time() - self.startWaitTime > timeout:
                    self.emptyCount = 0
                    raise RingdownTimeout("No ringdown in %s seconds" % timeout)
        return rdData

    def reset(self):
        self.closeSpectrumWhenDone = False
        self.numPts = 0
        #Initialize the sensor averaging...
        self.sensorAvgCount = 0
        for key in self.latestSensors.keys():
            self.avgSensors[key] = 0.0
            self.sumSensors[key] = 0.0
        #Initialize the rdBuffer with the names and types of fields in ProcessedRingdownEntryType
        self.rdBuffer = {}
        for fname,ftype in ProcessedRingdownEntryType._fields_:
            self.rdBuffer[fname] = ([],ftype)
        
    def _sensorFilter(self, entry):
        """Updates the latest sensor readings.

        This is executed for every sensor value picked up from the sensor stream
        broadcast.
        """
        self.latestSensors["timestamp"] = entry.timestamp
        self.latestSensors[interface.STREAM_MemberTypeDict[entry.streamNum][7:]] = entry.value
        self.sensorsUpdated = True
    
    def getLatestSensors(self):
        if self.sensorsUpdated:
            self.sensorsUpdated = False
            self.cachedSensors = self.latestSensors.copy()
        return self.cachedSensors

    def doSensorAveraging(self, sensorData):
        self.sensorAvgCount += 1.
        for k in self.avgSensors:
            self.sumSensors[k] += sensorData[k]
            newAvg = self.sumSensors[k] / self.sensorAvgCount
            self.avgSensors[k] = newAvg

    def addToSpectrumQueue(self, rdfDict):
        """Adds self.rdfDict to self.spectrumQueue and maintains
        a valid queue size.
        """
        try:
            if self.spectrumQueue.qsize() == self.maxSpectrumQueueSize:
                self.spectrumQueue.get()
            self.spectrumQueue.put(rdfDict)
        except:
            LogExc("Failed to add data in spectrum queue.")
                
    def appendPoint(self, rdData, relativeRdTime):
        """Adds a single set of Data to the spectrum (at a single relativeRdTime)
        """
        for fname,ftype in ProcessedRingdownEntryType._fields_:
            if fname in self.rdBuffer:
                self.rdBuffer[fname][0].append(getattr(rdData,fname))
        self.numPts += 1

        sensorData = self.getLatestSensors()
        #Sneak in the local ringdown time for sensor averaging...
        # Replace "entry.timestamp" with "relativeRdTime"
        sensorData["timestamp"] = relativeRdTime
        self.doSensorAveraging(sensorData)

    def finish(self):
        """Closes off the acquisition of the spectrum and creates an output file
        with data stored in rdfDict.
        """
        self.rdfDict = {"rdData":{}, "sensorData":{}, "tagalongData":{}, "controlData":{}}
        # Convert the contents of self.rdBuffer lists into numpy arrays
        for fname in self.rdBuffer:
            data,dtype = self.rdBuffer[fname]
            self.rdfDict["rdData"][fname] = numpy.array(data,ctypes2numpy[dtype])
        self.rdfDict["rdData"]["pztValue"] = self.rdfDict["rdData"]["pztValue"] + 0.0 # Convert integer to floating-point
        self.rdfDict["rdData"]["tunerValue"] = self.rdfDict["rdData"]["tunerValue"] + 0.0

        # Append averaged sensor data
        # "timestamp" is the averaged absolute DAS time
        self.avgSensors["timestamp"] += self.storedFirstRdTime
        self.rdfDict["sensorData"] = self.avgSensors.copy()

        # Add more sensor data
        self.rdfDict["sensorData"]["SchemeID"] = self.schemeTable
        self.rdfDict["sensorData"]["SpectrumID"] = self.spectrumID
        self.rdfDict["sensorData"]["SensorTime"] = unixTime(self.rdfDict["sensorData"]["timestamp"])
        #self.rdfDict["sensorData"]["SpectrumStartTime"] = unixTime(self.firstRdTime)

        #Write the tagalong data values...
        self.rdfDict["tagalongData"] = self.tagalongData

        #Write control data dictionary for pacing, etc...
        if self.spectrumQueue:
            qsize = self.spectrumQueue.qsize()
        else:
            qsize = 0
        self.rdfDict["controlData"] = {"RDDataSize":self.numPts, "SpectrumQueueSize":qsize}
        
        # Process spectrum files (HDF5 or RDF)
        if self.enableSpectrumFiles:
            if self.useHDF5:
                # Create HDF5 table file
                filename = "%03d_%013d.h5" % (self.spectrumID, int(time.time()*1000))
                streamPath = os.path.join(self.streamDir, filename)
                streamFP = openFile(streamPath, "w")
                for dataKey in self.rdfDict.keys():
                    subDataDict = self.rdfDict[dataKey]
                    if len(subDataDict) > 0:
                        sortedKeys = sorted(subDataDict.keys())
                        if isinstance(subDataDict.values()[0], numpy.ndarray):
                            # Array
                            sortedValues = [subDataDict.values()[i] for i in numpy.argsort(subDataDict.keys())]
                            dataRec = numpy.rec.fromarrays(sortedValues, names=sortedKeys)
                        elif isinstance(subDataDict.values()[0], list) or isinstance(subDataDict.values()[0], tuple):
                            # Convert list or tuple to array
                            sortedValues = [numpy.array(subDataDict.values()[i]) for i in numpy.argsort(subDataDict.keys())]
                            dataRec = numpy.rec.fromarrays(sortedValues, names=sortedKeys)
                        else:
                            # Non-array
                            sortedValues = [subDataDict.values()[i] for i in numpy.argsort(subDataDict.keys())]
                            dataRec = numpy.rec.fromrecords([sortedValues], names=sortedKeys)
                        streamFP.createTable("/", dataKey, dataRec, dataKey, filters=self.hdf5Filters)
            else:
                # Pickle the rdfDict 
                filename = "%03d_%013d.rdf" % (self.spectrumID, int(time.time()*1000))
                streamPath = os.path.join(self.streamDir, filename)
                streamFP = file(streamPath, "wb")
                streamFP.write(cPickle.dumps(self.rdfDict,cPickle.HIGHEST_PROTOCOL)) 
            streamFP.close()
            # Archive spectrum files
            Archiver.ArchiveFile(self.archiveGroup, streamPath, True)
            
        # Store spectrum in a queue if required
        if self.spectrumQueue:
            self.addToSpectrumQueue(self.rdfDict.copy())

        self.reset()

    def RPC_setMaxSpectrumQueueSize(self, maxSize):
        if self.spectrumQueue:
            self.spectrumQueue = None
        if maxSize > 0:
            self.spectrumQueue = Queue.Queue(maxSize)
        self.maxSpectrumQueueSize = maxSize
        return "OK"

    def RPC_getMaxSpectrumQueueSize(self):
        return self.maxSpectrumQueueSize
        
    def RPC_getCurrentSpectrumQueueSize(self):
        if self.spectrumQueue:
            return self.spectrumQueue.qsize()
        else:
            return 0
        
    def RPC_getFromSpectrumQueue(self, timeout=0):
        try:
            return self.spectrumQueue.get(timeout = timeout)
        except:
            raise
        
    def RPC_closeSpectrum(self):
        self.closeSpectrumWhenDone = True

    def RPC_disableSpectrumFiles(self):
        self.enableSpectrumFiles = False
        
    def RPC_enableSpectrumFiles(self):
        self.enableSpectrumFiles = True
        
    def RPC_setTagalongData(self, Name, Value):
        """Sets RDF tagalong data (and timestamp) with the given token Name."""
        self.tagalongData[Name] = (Value, time.time())

    def RPC_getTagalongData(self, Name):
        """Returns a [DataValue, DataTime] array for the specified token Name.
        If no data for the given name, an empty array [] is returned.
        """
        try:
            dataValue, dataTime = self.tagalongData[Name]
            return [dataValue, dataTime]
        except KeyError:
            return []

    def RPC_deleteTagalongData(self, Name):
        """Deletes the RDF tagalong data with the specified token Name.

        On success, returns the [DataValue, DataTime] that was last recorded.
        On failure (no data with Name), an empty array [] is returned.

        """
        return list(self.tagalongData.pop(Name, []))
    
    def RPC_getSensorData(self):
        sensorData = self.getLatestSensors()
        return sensorData.copy()
        
    def RPC_shutdown(self):
        self._shutdownRequested = True

HELP_STRING = """SpectrumCollector.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./SpectrumCollector.ini"
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
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
    #Start with option defaults...
    configFile = os.path.splitext(AppPath)[0] + ".ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile, options

if __name__ == "__main__":                          
    configFile, options = handleCommandSwitches()
    spCollectorApp = SpectrumCollector(configFile)
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    spCollectorApp.run()
    Log("Exiting program")
