#!/usr/bin/python
"""
File Name: SpectrumCollector.py
Purpose: Collects spectrum and related information to save in HDF5 files. Spectrum will be stored in a queue if specified.

File History:
    12-Oct-2009  alex  Initial version.
    05-Feb-2010  sze   Removed relative timestamps, make HDF5 files contain data corresponding to a scheme file.
    17-Mar-2010  sze   Make all the dictionaries in a spectrum (rdData, sensorData and controlData) have values which
                        are lists or arrays. This improves compatibility with HDF5 storage of RdfData (spectrum) objects
                        in which these dictionaries map to tables. For a normal spectrum, sensorData and controlData
                        contain lists with only one element each.
    19-Oct-2013  sze   Remove use of numpy record arrays, as this was causing a memory leak
    15-Dec-2013  sze   Remove support for saving individual spectra and refactor code for writing out HDF5 files

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""
from __future__ import with_statement

import sys
import os
import getopt
import inspect
import multiprocessing
import numpy
import Queue
import shutil
import threading
import time
import ctypes

from Host.autogen import interface
from Host.autogen.interface import ProcessedRingdownEntryType
from Host.autogen.interface import RingdownEntryType
from Host.Common import CmdFIFO, Broadcaster, Listener, StringPickler
from Host.Common.SharedTypes import BROADCAST_PORT_SENSORSTREAM, BROADCAST_PORT_RD_RECALC, BROADCAST_PORT_RDRESULTS
from Host.Common.SharedTypes import BROADCAST_PORT_SPECTRUM_COLLECTOR
from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR, RPC_PORT_DRIVER, RPC_PORT_ARCHIVER, RPC_PORT_SUPERVISOR
from Host.Common.SharedTypes import CrdsException
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.AppRequestRestart import RequestRestart
from Host.Common.timestamp import getTimestamp
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.SpectrumCollector.Sequencer import Sequencer
from Host.SpectrumCollector.RdfFileOutput import writeSpectrumFile

APP_NAME = "SpectrumCollector"

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
INCR_FLAG_MASK       = interface.SUBSCHEME_ID_IncrMask   # 32768 - Bit 15 is used for special increment flag
SPECTRUM_IGNORE_MASK = interface.SUBSCHEME_ID_IgnoreMask # 16384 - Bit 14 is used to indicate the point should be ignored
SPECTRUM_RECENTER_MASK = interface.SUBSCHEME_ID_RecenterMask # 8192 - Bit 13 is used to indicate that the virtual laser tuner offset is to be adjusted
SPECTRUM_ISCAL_MASK  = interface.SUBSCHEME_ID_IsCalMask  #  4096 - Bit 12 is used to flag a point as a cal point to be collected
SPECTRUM_SUBSECTION_ID_MASK = interface.SUBSCHEME_ID_SpectrumSubsectionMask
SPECTRUM_ID_MASK     = interface.SUBSCHEME_ID_SpectrumMask # Bottom 8 bits of schemeStatus are the spectrum id/name

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
                                    IsDontCareConnection = False)

class SpectrumCollectionTimeout(CrdsException):
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

    streamDir is specified to store the output file.
    On creation of an instance, a file header is written.
    """

    def __init__(self, configPath):
        # Read from .ini file
        cp = CustomConfigObj(configPath)
        basePath = os.path.split(configPath)[0]
        self.ringdownSource = cp.get("MainConfig", "ringdownSource", "processed")
        self.ringdownSource = self.ringdownSource.lower()
        if self.ringdownSource not in ["raw","processed"]:
            raise ValueError("Unknown ringdownSource type: %s" % self.ringdownSource)
        if self.ringdownSource == 'raw':
            self.rdEntryType = RingdownEntryType
            self.rdBroadcastPort = BROADCAST_PORT_RDRESULTS
        else:
            self.rdEntryType = ProcessedRingdownEntryType
            self.rdBroadcastPort = BROADCAST_PORT_RD_RECALC
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
                self.rpcServer.register_function(attr, name=s, NameSlice = 4)


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
                                            self.rdBroadcastPort,
                                            self.rdEntryType,
                                            retry = True,
                                            name = "Spectrum collector listener",logFunc = Log)


        # Broadcaster for spectra
        self.spectrumBroadcaster = Broadcaster.Broadcaster(
                            port=BROADCAST_PORT_SPECTRUM_COLLECTOR,
                            name="Spectrum Collector broadcaster",logFunc = Log)

        self.enableSpectrumFiles = True
        self.closeSpectrumWhenDone = False
        self.tempRdDataBuffer = None
        self.spectrumID = 0
        self.schemeTable = 0
        self.schemeVersion = 0
        self.lastSpectrumID = 0
        self.lastSchemeTable = 0
        self.lastSchemeVersion = 0
        self.tagalongData = {}
        self.controlData = {}
        self.numPts = 0
        self.emptyCount = 0
        self.startWaitTime = 0
        self.rdQueueGetLastTime = 0
        self.maxRdQueueGetRtt = 0
        self.lastSchemeCount = -1
        self.streamFP = None
        self.tableDict = {}
        self.auxSpectrumFile = ""
        self.sensorAvgCount = 0
        self.avgSensors = {}
        self.sumSensors = {}
        self.rdBuffer = {}

        self.useSequencer = True
        self.sequencer = None
        self.schemesUsed = {}

        self.fsrModeBoundaries = {}

    def run(self):
        try:
            self.sequencer = Sequencer()
            # start the rpc server on another thread...
            self.rpcThread = RpcServerThread(self.rpcServer, self.RPC_shutdown)
            self.rpcThread.start()
            # start the sequencer on another thread
            self.sequencer.runInThread()
            # The following count "spectra" which are delimited by scheme rows which have bit-15 set in the subschemeId
            lastCount = -1
            thisCount = -1
            MAXLOOPS = 500
            loops = 0

            endOfSpectrum = False
            endOfScheme = False
            spectraInScheme = []
            self.prepareForNewSpectrum()

            while not self._shutdownRequested:
                #Pull a spectral point from the RD queue...
                try:
                    rdData = self.getSpectralDataPoint(timeToRetry=0.5)
                    if rdData is None:
                        time.sleep(0.5)
                        loops = 0
                        continue
                    now = TimeStamp()
                    if self.rdQueueGetLastTime != 0:
                        rtt = now - self.rdQueueGetLastTime
                        if rtt > 10:
                            Log("Processed Ringdowns loop RTT: %.3f" % (rtt,))
                        if rtt > self.maxRdQueueGetRtt:
                            Log("Maximum Processed Ringdowns loop RTT so far: %.3f" % (self.maxRdQueueGetRtt,))
                            self.maxRdQueueGetRtt = rtt
                    self.rdQueueGetLastTime = now

                    #localRdTime = Driver.hostGetTicks()
                    thisSubSchemeID = rdData.subschemeId
                    self.lastSpectrumID = self.spectrumID
                    self.spectrumID = thisSubSchemeID & SPECTRUM_ID_MASK
                    self.lastSchemeVersion = self.schemeVersion
                    self.schemeVersion = (rdData.schemeVersionAndTable & interface.SCHEME_VersionMask) >> interface.SCHEME_VersionShift
                    thisCount = rdData.count

                    # The schemeCount is changed when a SCHEME starts, i.e. it tracks entire schemes, including the
                    #  repeat count. We make an HDF5 file each time a scheme is run
                    schemeStatus = rdData.status
                    schemeCount = schemeStatus & interface.RINGDOWN_STATUS_SequenceMask

                    if self.lastSchemeCount != schemeCount:
                        if self.lastSchemeCount >= 0:
                            endOfSpectrum = True
                            endOfScheme = True
                        self.lastSchemeCount = schemeCount
                    else:
                        self.lastSchemeTable = self.schemeTable
                        self.schemeTable = (rdData.schemeVersionAndTable & interface.SCHEME_TableMask) >> interface.SCHEME_TableShift
                        self.schemesUsed[self.schemeTable] = self.sequencer.inDas.get(self.schemeTable, None)

                    # When the "count" is different (set by DSP when bit-15, the fit flag is set in the scheme file),
                    #  we know a new SPECTRUM is coming and we have to process whatever we currently have.
                    if thisCount != lastCount:
                        # We "push back" the last data point so that it is fetched again next time as part
                        #  of the next spectrum
                        self.tempRdDataBuffer = rdData
                        endOfSpectrum = True
                    else: #still collecting the same spectrum
                        if not (thisSubSchemeID & SPECTRUM_IGNORE_MASK):
                            self.appendRingdownToSpectrum(rdData)

                except SpectrumCollectionTimeout:
                    if self.numPts > 0:
                        Log("Closing spectrum and scheme due to data timeout (count = %d)" % thisCount, Level = 0)
                        endOfSpectrum = True
                        endOfScheme = True

                # A spectrum is composed of one or more sub-schemes.
                # As each spectrum is collected, broadcast them to the fitters, collecting them
                # into spectraInScheme as the code works its way through a scheme.
                # After all the sub-schemes of the scheme have been collected, save the
                # scheme's worth of RD and sensor data to a RD*.h5 file for reprocessing.
                #
                # If the *.h5 is reprocessed, the fitter will split it into individual
                # spectra and fit them in order.
                #
                if endOfSpectrum:
                    spectrum = self.packageSpectrum()
                    self.spectrumBroadcaster.send(StringPickler.PackArbitraryObject(spectrum))
                    spectraInScheme.append(spectrum)
                    if endOfScheme:
                        if self.enableSpectrumFiles and spectraInScheme:
                            fileName = os.path.join(self.streamDir, "RD_%013d.h5" % (int(time.time()*1000),))
                            self.writeOut(fileName, spectraInScheme)
                            self.lastSchemeCount = -1
                        endOfScheme = False
                        self.schemesUsed = {}
                        spectraInScheme = []
                    endOfSpectrum = False
                    self.prepareForNewSpectrum()

                lastCount = thisCount
                loops += 1
                if loops >= MAXLOOPS:
                    loops = 0
                    time.sleep(0.01)
        except Exception:
            LogExc("Unhandled exception in SpectrumCollector main loop", Level=3)
            # Request a restart from Supervisor via RPC call
            restart = RequestRestart(APP_NAME)
            if restart.requestRestart(APP_NAME) is True:
                print("Restart True")
                Log("Restart request to supervisor sent")
            else:
                print("Restart False")
                Log("Restart request to supervisor not sent")

            Log("Spectrum Collector RPC handler shut down")

    def getSpectralDataPoint(self, timeToRetry, timeout = 10):
        """Pops rdData out of the local ringdown queue and returns it. If there are no ringdowns
        within the timeToRetry interval, return None. If we have been trying for duration timeout
        and there are no ringdowns, raise SpectrumCollectionTimeout.
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
                rdData = self.rdQueue.get(True, timeToRetry)
                self.emptyCount = 0
            except Queue.Empty:
                rdData = None
                self.emptyCount += 1
                if time.time() - self.startWaitTime > timeout:
                    self.emptyCount = 0
                    raise SpectrumCollectionTimeout("No ringdown in %s seconds" % timeout)
        return rdData

    def prepareForNewSpectrum(self):
        self.numPts = 0
        #Initialize the sensor averaging...
        self.sensorAvgCount = 0
        self.avgSensors = {}
        self.sumSensors = {}
        for key in self.latestSensors.keys():
            self.avgSensors[key] = 0.0
            self.sumSensors[key] = 0.0

        #Initialize the rdBuffer with the names and types of fields in (Processed)RingdownEntryType
        # The values in rdBuffer consist of a tuple, the first element is a list of data for that
        #  field in the spectrum and the second element is the ctypes object indicating the type
        #  of the data in the list
        self.rdBuffer = {}
        for fname, ftype in self.rdEntryType._fields_:
            self.rdBuffer[fname] = ([], ftype)

    def appendRingdownToSpectrum(self, rdData):
        """Adds data from the current RingdownEntryType object to self.rdBuffer.
        """
        for fname, ftype in self.rdEntryType._fields_:
            if fname in self.rdBuffer:
                self.rdBuffer[fname][0].append(getattr(rdData, fname))
        self.numPts += 1

        sensorData = self.getLatestSensors()
        self.doSensorAveraging(sensorData)

    def _sensorFilter(self, entry):
        """Updates the latest sensor readings.

        This is executed for every sensor value picked up from the sensor stream
        broadcast.
        """
        self.latestSensors["timestamp"] = entry.timestamp
        self.latestSensors[interface.STREAM_MemberTypeDict[entry.streamNum][7:]] = entry.value
        self.sensorsUpdated = True

    def getLatestSensors(self):
        """Get a copy of the dictionary of most recent sensor values.
        """
        if self.sensorsUpdated:
            self.sensorsUpdated = False
            self.cachedSensors = self.latestSensors.copy()
        return self.cachedSensors

    def doSensorAveraging(self, sensorData):
        """Append sensorData into the variables for computing statistics.
        """
        self.sensorAvgCount += 1.
        for k in self.avgSensors:
            self.sumSensors[k] += sensorData[k]
            newAvg = self.sumSensors[k] / self.sensorAvgCount
            self.avgSensors[k] = newAvg

    def packageSpectrum(self):
        """Package a spectrum by adjoining sensor, control and tagalong data.

        Returns: Dictionary with keys:
            rdData: Ring down data
            sensorData: Sensor data averaged over the collection time of the spectrum
            tagalongData: Data from external devices that are to tag-along with the spectrum
            controlData: Indicates number of ringdowns in spectrum and latency from ringdown collection time to
                spectrum assembly time
        """
        spectrumDict = {"rdData":{}, "sensorData":{}, "tagalongData":{}, "controlData":{}}
        # Convert the contents of self.rdBuffer lists into numpy arrays
        for fname in self.rdBuffer:
            data, dtype = self.rdBuffer[fname]
            spectrumDict["rdData"][fname] = numpy.asarray(data, ctypes2numpy[dtype])
        spectrumDict["rdData"]["pztValue"] = numpy.asarray(spectrumDict["rdData"]["pztValue"], dtype='float32')
        spectrumDict["rdData"]["tunerValue"] = numpy.asarray(spectrumDict["rdData"]["tunerValue"], dtype='float32')
        # Append a mode number to each ringdown if the mode boundaries have been set up for the laser in
        # FSR hopping mode
        if self.fsrModeBoundaries:
            laserUsed = (spectrumDict["rdData"]["laserUsed"] & 3) + 1
            fineLaserCurrent = spectrumDict["rdData"]["fineLaserCurrent"]
            modeNum = -999999 * numpy.ones_like(fineLaserCurrent, dtype=int)
            for aLaserNum in range(1, interface.MAX_LASERS + 1):
                sel = (laserUsed == aLaserNum)
                if numpy.any(sel):
                    if aLaserNum in self.fsrModeBoundaries:
                        bins = self.fsrModeBoundaries[aLaserNum].copy()
                        modeNum[sel] = numpy.digitize(fineLaserCurrent[sel], bins)
            spectrumDict["rdData"]["fsrIndex"] = modeNum
        else:
            spectrumDict["rdData"]["fsrIndex"] = -999999 * numpy.ones_like(spectrumDict["rdData"]["timestamp"], dtype=int)

        # Append averaged sensor data
        for s in self.avgSensors:
            spectrumDict["sensorData"][s] = [self.avgSensors[s]]

        # Add more sensor data
        spectrumDict["sensorData"]["SchemeTable"] = [self.lastSchemeTable]
        spectrumDict["sensorData"]["SpectrumID"] = [self.lastSpectrumID]
        spectrumDict["sensorData"]["SchemeVersion"] = [self.lastSchemeVersion]

        #Write the tagalong data values...
        for t in self.tagalongData:
            spectrumDict["tagalongData"][t] = [self.tagalongData[t][0]]

        #Write control data dictionary
        qsize = 0
        # Latency is seconds between the current time and the average time of ringdowns in file
        ts = spectrumDict["rdData"]["timestamp"]
        latency = 0.0
        if len(ts)>0:
            latency = 0.001*(getTimestamp() - float(sum(ts))/len(ts))
        spectrumDict["controlData"] = {"RDDataSize":[self.numPts], "SpectrumQueueSize":[qsize], "Latency":[latency]}

        return spectrumDict

    def writeOut(self, fileName, spectraInScheme):
        """Write out the spectra collected for a scheme file to an HDF5 file.

        Args:
            fileName: Name of HDF5 to receive spectrum
            spectraInScheme: Spectral data collected
        """
        # Create HDF5 file
        numSchemes = len(self.schemesUsed)
        attrs = {}

        if numSchemes == 1:
            scheme = self.schemesUsed.values()[0]
            if scheme is not None:
                attrs["schemeFile"] = scheme[3]
                attrs["modeName"] = scheme[0]
        else:
            Log("Only one scheme (not %d) was expected in file %s" % (numSchemes, os.path.split(fileName)[-1]),
                Data=self.schemesUsed)

        writeSpectrumFile(fileName, spectraInScheme, attrs, self.auxSpectrumFile)
        self.auxSpectrumFile = None


    def archiveSpectrumFile(self, fileName, auxSpectrumFile):
        # Archive HDF5 file
        archiveThread = threading.Thread(target = self._archiveFile, args = (fileName, auxSpectrumFile))
        archiveThread.setDaemon(True)
        archiveThread.start()

    def _archiveFile(self, streamPath, auxSpectrumFile):
        time.sleep(1.0)
        # Copy to auxiliary spectrum file and reset filename to empty
        if auxSpectrumFile:
            try:
                shutil.copyfile(streamPath, auxSpectrumFile)
            except:
                LogExc("Error copying to auxiliary spectrum file %s" % auxSpectrumFile)
        time.sleep(1.0)
        try:
            Archiver.ArchiveFile(self.archiveGroup, streamPath, True)
        except:
            LogExc("Archiver call error")

    # RPC functions which are handled by the sequencer

    @CmdFIFO.rpc_wrap
    def RPC_addNamedSequenceOfSchemeConfigs(self,name,schemeConfigs):
        self.sequencer.addNamedSequenceOfSchemeConfigs(name,schemeConfigs)

    @CmdFIFO.rpc_wrap
    def RPC_reloadSequences(self):
        self.sequencer.reloadSequences()

    @CmdFIFO.rpc_wrap
    def RPC_getSequenceNames(self):
        return self.sequencer.getSequenceNames()

    @CmdFIFO.rpc_wrap
    def RPC_setSequence(self,seq=None):
        if seq is not None:
            if self.sequencer.loadSequencePending:
                raise ValueError("Cannot set sequence while another load is pending.")
            if seq not in self.sequencer.sequences:
                raise ValueError("Invalid sequence name: %s" % seq)
            self.sequencer.loadSequenceLock.acquire()
            self.sequencer.loadSequencePending = True
            self.sequencer.pendingSequence = str(seq)
            self.sequencer.loadSequenceLock.release()
        self.useSequencer = True

    @CmdFIFO.rpc_wrap
    def RPC_startSequence(self,seq=None):
        self.RPC_setSequence(seq)
        self.sequencer.startSequence()

    @CmdFIFO.rpc_wrap
    def RPC_getSequence(self):
        return self.sequencer.getSequenceName()

    @CmdFIFO.rpc_wrap
    def RPC_setSequencerMode(self,useSequencer):
        self.useSequencer = useSequencer

    @CmdFIFO.rpc_wrap
    def RPC_startScan(self):
        if self.useSequencer:
            self.sequencer.startSequence()
        else:
            Driver.startScan()

    @CmdFIFO.rpc_wrap
    def RPC_sequencerGetCurrent(self):
        return self.sequencer.getCurrent()

    @CmdFIFO.rpc_wrap
    def RPC_closeSpectrum(self):
        self.closeSpectrumWhenDone = True

    @CmdFIFO.rpc_wrap
    def RPC_disableSpectrumFiles(self):
        self.enableSpectrumFiles = False

    @CmdFIFO.rpc_wrap
    def RPC_enableSpectrumFiles(self):
        self.enableSpectrumFiles = True

    @CmdFIFO.rpc_wrap
    def RPC_setTagalongData(self, Name, Value):
        """Sets RDF tagalong data (and timestamp) with the given token Name."""
        self.tagalongData[Name] = (Value, time.time())

    @CmdFIFO.rpc_wrap
    def RPC_getTagalongData(self, Name):
        """Returns a [DataValue, DataTime] array for the specified token Name.
        If no data for the given name, an empty array [] is returned.
        """
        try:
            dataValue, dataTime = self.tagalongData[Name]
            return [dataValue, dataTime]
        except KeyError:
            return []

    @CmdFIFO.rpc_wrap
    def RPC_deleteTagalongData(self, Name):
        """Deletes the RDF tagalong data with the specified token Name.

        On success, returns the [DataValue, DataTime] that was last recorded.
        On failure (no data with Name), an empty array [] is returned.

        """
        return list(self.tagalongData.pop(Name, []))

    @CmdFIFO.rpc_wrap
    def RPC_getSensorData(self):
        sensorData = self.getLatestSensors()
        return sensorData.copy()

    @CmdFIFO.rpc_wrap
    def RPC_shutdown(self):
        self._shutdownRequested = True

    @CmdFIFO.rpc_wrap
    def RPC_setAuxiliarySpectrumFile(self,fileName):
        self.auxSpectrumFile = fileName

    @CmdFIFO.rpc_wrap
    def RPC_archiveSpectrumFile(self, fileName, auxSpectrumFile):
        self.archiveSpectrumFile(fileName, auxSpectrumFile)

    @CmdFIFO.rpc_wrap
    def RPC_setFsrModeBoundaries(self, aLaserNum, modeBoundaries):
        Log("Received mode boundaries for laser %d" % aLaserNum)
        self.fsrModeBoundaries[aLaserNum] = modeBoundaries.copy()


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
    multiprocessing.freeze_support()
    try:
        configFile, options = handleCommandSwitches()
        spCollectorApp = SpectrumCollector(configFile)
        Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
        spCollectorApp.run()
        # cProfile.run('spCollectorApp.run()','c:/spectrumCollectorProfile')
        Log("Exiting program")
    except Exception:
        LogExc("Unhandled exception in SpectrumCollector", Level=3)
