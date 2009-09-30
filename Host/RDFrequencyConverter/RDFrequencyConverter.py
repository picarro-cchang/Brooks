#!/usr/bin/python
#
# FILE:
#   RDFrequencyConverter.py
#
# DESCRIPTION:
#   Converts between WLM angle and frequencies using autocal structures
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   30-Sep-2009  alex/sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
from Host.autogen import interface
import Queue
from Host.Common import Autocal1
import numpy
import time

from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common import SharedTypes
from Host.Common.SharedTypes import BROADCAST_PORT_RD_RECALC, BROADCAST_PORT_RDRESULTS
from Host.Common import Listener, Broadcaster
from Host.Common import CmdFIFO, StringPickler

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
EventManagerProxy_Init("RDFrequencyConverter")

class RDFrequencyConverterRpcHandler(object):
    def __init__(self):
        self.server = CmdFIFO.CmdFIFOServer(("", SharedTypes.RPC_PORT_FREQ_CONVERTER),
                                            ServerName = "FrequencyConverter",
                                            ServerDescription = "Frequency Converter for CRDS hardware",
                                            threaded = True)
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

class RDFrequencyConverter(object):
    def __init__(self):
        self.rdQueue = Queue.Queue()
        self.rdListener = Listener.Listener(self.rdQueue,
                                    BROADCAST_PORT_RDRESULTS,
                                    interface.RingdownEntryType,
                                    retry = True,
                                    name = "Ringdown frequency converter listener",logFunc = Log)
        self.processedRdBroadcaster = Broadcaster.Broadcaster(
                                    port=BROADCAST_PORT_RD_RECALC,
                                    name="Ringdown frequency converter broadcaster",logFunc = Log)
        self.rpcHandler = RDFrequencyConverterRpcHandler()


    def run(self):
        rdProcessedData = interface.ProcessedRingdownEntryType()
        daemon = self.rpcHandler.server.daemon
        try:
            while not daemon.mustShutdown:
                while not self.rdQueue.empty():
                    try:
                        rdData = self.rdQueue.get(False)
                        for f in rdData._fields_:
                            if f != "wlmAngle":
                                setattr(rdProcessedData, f, getattr(rdData,f))
                            else:
                                rdProcessedData.frequency = 10000*abs(rdData.wlmAngle)
                        self.processedRdBroadcaster.send(StringPickler.ObjAsString(rdProcessedData))   
                    except Queue.Empty:
                        break
                daemon.handleRequests(0.1)
            Log("RD Frequency Converter RPC handler shut down")

        except:
            type,value,trace = sys.exc_info()
            Log("Unhandled Exception in main loop: %s: %s" % (str(type),str(value)),
                Verbose=traceback.format_exc(),Level=3)

if __name__ == "__main__":
    rdFrequencyConverterApp = RDFrequencyConverter()
    Log("RDFrequencyConverter starting")
    rdFrequencyConverterApp.run()
    Log("RDFrequencyConverter exiting")
    
if 0:            
    class RDFrequencyConverter(object):
        def __init__(self, WarmboxCalFilePath):
            ##Load up the frequency converters for each laser in the DAS...
            cp = CustomConfigObj(WarmboxCalFilePath)  
            for i in range(1, MAX_LASERS + 1): # N.B. In Autocal1, laser indices are 1 based
                ac = Autocal1.AutoCal()
                try:
                    ac.getFromIni(cp, i)
                    self._FreqConverter[i-1] = ac
                except KeyError:
                    #No such laser
                    pass
            self.RdQueue = Queue.Queue()
            rdElementType = HostRdResultsType
            self.RdListener = Listener.Listener(self.RdQueue,
                                        BROADCAST_PORT_RDRESULTS,
                                        rdElementType,
                                        retry = True,
                                        name = "Ringdown frequency converter listener",logFunc = Log)
            self.rdCache = []
            
        def _batchConvert(self):
            """Convert WLM angles and laser temperatures to wavenumbers in a vectorized way, using
            thetaCalAndLaserTemp2WaveNumber"""

            if self.rdCache:
                raise RuntimeError("_batchConvert called while cache is not empty")
            thetaCal = []
            laserTemp = []
            cacheIndex = []
            for laserIndex in range(MAX_LASERS):
                thetaCal.append([])
                laserTemp.append([])
                cacheIndex.append([])
            # Get data from the queue into the cache
            index = 0
            while not self.RdQueue.empty():
                try:
                    rdData = self.RdQueue.get(False)
                    self.rdCache.append(rdData)
                    laserIndex = rdData.laserSelect
                    thetaCal[laserIndex].append(rdData.thetaCal)
                    laserTemp[laserIndex].append(rdData.laserTemp)
                    cacheIndex[laserIndex].append(index)
                    index += 1
                except Queue.Empty:
                    break
            # Do the angle to wavenumber conversions for each laser
            for laserIndex in range(MAX_LASERS):
                if cacheIndex[laserIndex]: # There are angles to convert for this laser
                    fc = self._FreqConverter[laserIndex]
                    waveNo = fc.thetaCalAndLaserTemp2WaveNumber(numpy.array(thetaCal[laserIndex]), numpy.array(laserTemp[laserIndex]))
                    for i,w in enumerate(waveNo):
                        index = cacheIndex[laserIndex][i]
                        rdData = self.rdCache[index][0]
                        dasScheme = self.rdCache[index][2]
                        rdData.wavenum = int(100000.0 * w)
                        try:
                            rdData.wavenumSetpoint = dasScheme._OriginalScheme.schemeEntry[rdData.schemeRow].setpoint.asUint32
                        except Exception, e:
                            rdData.wavenumSetpoint = 0
                            print "ERROR: Scheme number: %d, row: %d, exception: %s" % (rdData.schemeTableIndex,rdData.schemeRow,e)

        def _GetRingdownData(self,timeout):
            """Calls batchConvert to get ringdown data from self.RdQueue, having converted WLM angles to
            wavenumbers if necessary. For efficiency, the conversions are batched, vectorized and cached
            in the FIFO self.rdCache. If the cache is non-empty, immediately return data from it. Otherwise,
            check RdQueue to see if there are already enough data to make it worth doing a batch conversion.
            If the amount of data are insufficient, wait for the timeout duration (for more data to accumulate)
            and then do the conversion. Raises Queue.Empty if no data are available."""

            MIN_SIZE = 50
            if not self.rdCache: # i.e. cache is Empty
                if self.RdQueue.qsize() < MIN_SIZE:
                    time.sleep(timeout)
                self._batchConvert()
                if not self.rdCache:
                    raise Queue.Empty
            return self.rdCache.pop(0)
