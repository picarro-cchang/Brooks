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
#   02-Oct-2009  alex  Add RPC functions.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
import traceback
import numpy
import time
import threading
import Queue
import inspect
from Host.autogen import interface
from Host.Common import Autocal1
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.SharedTypes import BROADCAST_PORT_RD_RECALC, BROADCAST_PORT_RDRESULTS, RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER
from Host.Common.SharedTypes import Scheme
from Host.Common import Listener, Broadcaster
from Host.Common import CmdFIFO, StringPickler

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
EventManagerProxy_Init("RDFrequencyConverter")

MIN_SIZE = 30
Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                         ClientName="RDFrequencyConverter")
                                         
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
            
class RDFrequencyConverter(object):
    def __init__(self):
        self.numLasers = interface.NUM_VIRTUAL_LASERS
        self.rdQueue = Queue.Queue()
        self.rdProcessedCache = []
        self.rpcThread = None
        self._shutdownRequested = False
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_FREQ_CONVERTER),
                                                ServerName = "FrequencyConverter",
                                                ServerDescription = "Frequency Converter for CRDS hardware",
                                                threaded = True)
        #Register the rpc functions...
        for s in dir(self):
            attr = self.__getattribute__(s)
            if callable(attr) and s.startswith("RPC_") and (not inspect.isclass(attr)):
                self.rpcServer.register_function(attr, NameSlice = 4)
                
        self.rdListener = Listener.Listener(self.rdQueue,
                                    BROADCAST_PORT_RDRESULTS,
                                    interface.RingdownEntryType,
                                    retry = True,
                                    name = "Ringdown frequency converter listener",logFunc = Log)
        self.processedRdBroadcaster = Broadcaster.Broadcaster(
                                    port=BROADCAST_PORT_RD_RECALC,
                                    name="Ringdown frequency converter broadcaster",logFunc = Log)
        
        self._freqScheme = {}
        self._angleScheme = {}
        self._isAngleSchemeConverted = {}
        self._freqConverter = {}

    def run(self):
        #start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.RPC_shutdown)
        self.rpcThread.start()
        
        try:
            while not self._shutdownRequested:
                if self.rdQueue.qsize() > MIN_SIZE:
                    self._batchConvert()
                while self.rdProcessedCache:
                    try:
                        rdProcessedData = self.rdProcessedCache.pop(0)
                        self.processedRdBroadcaster.send(StringPickler.ObjAsString(rdProcessedData))   
                    except:
                        break
            Log("RD Frequency Converter RPC handler shut down")

        except:
            type,value,trace = sys.exc_info()
            Log("Unhandled Exception in main loop: %s: %s" % (str(type),str(value)),
                Verbose=traceback.format_exc(),Level=3)

    def _batchConvert(self):
        """Convert WLM angles and laser temperatures to wavenumbers in a vectorized way, using
        wlmAngleAndlaserTemperature2WaveNumber"""

        if self.rdProcessedCache:
            raise RuntimeError("_batchConvert called while cache is not empty")
        wlmAngle = []
        laserTemperature = []
        cacheIndex = []
        for laserIndex in range(self.numLasers):
            wlmAngle.append([])
            laserTemperature.append([])
            cacheIndex.append([])
        # Get data from the queue into the cache
        index = 0
        while not self.rdQueue.empty():
            try:
                rdProcessedData = interface.ProcessedRingdownEntryType()
                rdData = self.rdQueue.get(False)
                for name,ctype in rdData._fields_:
                    if name != "wlmAngle":
                        setattr(rdProcessedData, name, getattr(rdData,name))
                self.rdProcessedCache.append(rdProcessedData)
                laserIndex = (rdData.laserUsed >> 2) & 0x7 # 0-based
                wlmAngle[laserIndex].append(rdData.wlmAngle)
                laserTemperature[laserIndex].append(rdData.laserTemperature)
                cacheIndex[laserIndex].append(index)
                index += 1
            except Queue.Empty:
                break
        # Do the angle to wavenumber conversions for each available laser
        for laserIndex in range(self.numLasers):
            if cacheIndex[laserIndex]: # There are angles to convert for this laser
                fc = self._freqConverter[laserIndex]
                waveNo = fc.thetaCalAndLaserTemp2WaveNumber(numpy.array(wlmAngle[laserIndex]), numpy.array(laserTemperature[laserIndex]))
                for i,w in enumerate(waveNo):
                    index = cacheIndex[laserIndex][i]
                    rdProcessedData = self.rdProcessedCache[index]
                    rdProcessedData.frequency = int(100000.0 * w)
        
    def RPC_wrFreqScheme(self, schemeNum, schFilePath):
        self._freqScheme[schemeNum] = Scheme(schFilePath)
        self._angleScheme[schemeNum] = Scheme(schFilePath)
        self._isAngleSchemeConverted[schemeNum] = False

    def RPC_convertScheme(self, schemeNum):
        # Convert scheme from frequency (wave number) to angle
        scheme = self._freqScheme[schemeNum]
        angleScheme = self._angleScheme[schemeNum]
        numEntries = scheme.numEntries
        dataByLaser = {}
        for i in xrange(numEntries):
            laserNum = scheme.virtualLaser[i]
            waveNum = float(scheme.setpoint[i])
            if laserNum not in dataByLaser:
                dataByLaser[laserNum] = ([],[])
            dataByLaser[laserNum][0].append(i)
            dataByLaser[laserNum][1].append(waveNum)
        for laserNum in dataByLaser:
            fc = self._freqConverter[laserNum]
            waveNum = numpy.array(dataByLaser[laserNum][1])
            wlmAngle = fc.waveNumber2ThetaCal(waveNum)
            laserTemp = fc.thetaCal2LaserTemp(wlmAngle)
            for j,i in enumerate(dataByLaser[laserNum][0]):
                angleScheme.setpoint[i] = wlmAngle[j]
                angleScheme.laserTemp[i]= laserTemp[j]
        self._isAngleSchemeConverted[schemeNum] = True

    def RPC_uploadSchemeToDAS(self, schemeNum):
        # Upload angle scheme to DAS
        if not self._isAngleSchemeConverted[schemeNum]:
            raise Exception("Scheme not converted to angle yet.")
        angleScheme = self._angleScheme[schemeNum]
        Driver.wrScheme(schemeNum, *(angleScheme.repack()))
        
    def RPC_loadCal(self, calFilePath):
        ##Load up the frequency converters for each laser in the DAS...
        cp = CustomConfigObj(calFilePath)
        for i in range(1, self.numLasers + 1): # N.B. In Autocal1, laser indices are 1 based
            ac = Autocal1.AutoCal()
            try:
                ac.getFromIni(cp, i)
                self._freqConverter[i-1] = ac
            except KeyError:
                #No such laser
                pass
                
    def RPC_shutdown(self):
        self._shutdownRequested = True
        
if __name__ == "__main__":
    rdFreqConvertApp = RDFrequencyConverter()
    rdFreqConvertApp.RPC_loadCal("Warmbox_Factory.ini")
    rdFreqConvertApp.RPC_wrFreqScheme(0, "sample1.sch")
    rdFreqConvertApp.RPC_convertScheme(0)
    rdFreqConvertApp.RPC_uploadSchemeToDAS(0)
    Log("RDFrequencyConverter starting")
    rdFreqConvertApp.run()
    Log("RDFrequencyConverter exiting")
