#!/usr/bin/python
#
# FILE:
#   RDFrequencyConverter.py
#
# DESCRIPTION:
#   Converts between WLM angle and frequencies using AutoCal structures
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   30-Sep-2009  alex/sze  Initial version.
#   02-Oct-2009  alex      Add RPC functions.
#   09-Oct-2009  sze       Supporting new warm box calibration files and uploading of virtual laser parameters to DAS
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
import inspect
import numpy
import os
import Queue
import threading
import time
import traceback
from cStringIO import StringIO
from binascii import crc32
from Host.autogen import interface
from Host.Common.WlmCalUtilities import AutoCal
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.SharedTypes import BROADCAST_PORT_RD_RECALC, BROADCAST_PORT_RDRESULTS
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER
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
        
        self.freqScheme = {}
        self.angleScheme = {}
        self.isAngleSchemeConverted = {}
        self.freqConverter = {}
        self.calFilePath = ""


    def run(self):
        #start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.RPC_shutdown)
        self.rpcThread.start()
        
        while not self._shutdownRequested:
            try:
                if self.rdQueue.qsize() > MIN_SIZE:
                    self._batchConvert()
                else:
                    time.sleep(1.0)
                    continue
                while self.rdProcessedCache:
                    try:
                        rdProcessedData = self.rdProcessedCache.pop(0)
                        self.processedRdBroadcaster.send(StringPickler.ObjAsString(rdProcessedData))   
                    except:
                        break
            except:
                type,value,trace = sys.exc_info()
                Log("Error: %s: %s" % (str(type),str(value)),Verbose=traceback.format_exc(),Level=3)
                while not self.rdQueue.empty(): self.rdQueue.get(False)
                self.rdProcessedCache = []
                time.sleep(1.0)
        Log("RD Frequency Converter RPC handler shut down")


    def _batchConvert(self):
        """Convert WLM angles and laser temperatures to wavenumbers in a vectorized way, using
        wlmAngleAndlaserTemperature2WaveNumber"""

        if self.rdProcessedCache:
            raise RuntimeError("_batchConvert called while cache is not empty")
        wlmAngle = [[] for i in range(self.numLasers)]
        laserTemperature = [[] for i in range(self.numLasers)]
        cacheIndex = [[] for i in range(self.numLasers)]
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
                vLaserNum = 1 + ((rdData.laserUsed >> 2) & 0x7) # 1-based virtual laser number
                wlmAngle[vLaserNum-1].append(rdData.wlmAngle)
                laserTemperature[vLaserNum-1].append(rdData.laserTemperature)
                cacheIndex[vLaserNum-1].append(index)
                index += 1
            except Queue.Empty:
                break
        # Do the angle to wavenumber conversions for each available laser
        for vLaserNum in range(1,self.numLasers+1):
            if cacheIndex[vLaserNum-1]: # There are angles to convert for this laser
                if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
                    raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
                fc = self.freqConverter[vLaserNum-1]
                waveNo = fc.thetaCalAndLaserTemp2WaveNumber(numpy.array(wlmAngle[vLaserNum-1]), numpy.array(laserTemperature[vLaserNum-1]))
                for i,w in enumerate(waveNo):
                    index = cacheIndex[vLaserNum-1][i]
                    rdProcessedData = self.rdProcessedCache[index]
                    rdProcessedData.frequency = int(100000.0 * w)
            
    def RPC_wrFreqScheme(self, schemeNum, freqScheme):
        self.freqScheme[schemeNum] = freqScheme
        self.angleScheme[schemeNum] = freqScheme.makeAngleTemplate()
        self.isAngleSchemeConverted[schemeNum] = False

    def RPC_convertScheme(self, schemeNum):
        # Convert scheme from frequency (wave number) to angle
        scheme = self.freqScheme[schemeNum]
        angleScheme = self.angleScheme[schemeNum]
        numEntries = scheme.numEntries
        dataByLaser = {}
        for i in xrange(numEntries):
            vLaserNum = scheme.virtualLaser[i] + 1
            waveNum = float(scheme.setpoint[i])
            if vLaserNum not in dataByLaser:
                dataByLaser[vLaserNum] = ([],[])
            dataByLaser[vLaserNum][0].append(i)
            dataByLaser[vLaserNum][1].append(waveNum)
        for vLaserNum in dataByLaser:
            if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
                raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
            fc = self.freqConverter[vLaserNum-1]
            waveNum = numpy.array(dataByLaser[vLaserNum][1])
            wlmAngle = fc.waveNumber2ThetaCal(waveNum)
            laserTemp = fc.thetaCal2LaserTemp(wlmAngle)
            for j,i in enumerate(dataByLaser[vLaserNum][0]):
                angleScheme.setpoint[i] = wlmAngle[j]
                angleScheme.laserTemp[i]= laserTemp[j]
        self.isAngleSchemeConverted[schemeNum] = True

    def RPC_uploadSchemeToDAS(self, schemeNum):
        # Upload angle scheme to DAS
        if not self.isAngleSchemeConverted[schemeNum]:
            raise Exception("Scheme not converted to angle yet.")
        angleScheme = self.angleScheme[schemeNum]
        Driver.wrScheme(schemeNum, *(angleScheme.repack()))
        
    def RPC_getCalFilePath(self):
        return self.calFilePath
    
    def RPC_loadCal(self, calFilePath):
        # Load up the frequency converters for each laser in the DAS...
        self.calFilePath = os.path.abspath(calFilePath)
        ini = CustomConfigObj(self.calFilePath)
        for vLaserNum in range(1, self.numLasers + 1): # N.B. In AutoCal, laser indices are 1 based
            ac = AutoCal()
            self.freqConverter[vLaserNum-1] = ac.loadFromIni(ini, vLaserNum)
            # Send the virtual laser information to the DAS
            paramSec = "VIRTUAL_PARAMS_%d" % vLaserNum
            if paramSec in ini:
                p = ini[paramSec]
                aLaserNum = int(ini["LASER_MAP"]["ACTUAL_FOR_VIRTUAL_%d" % vLaserNum])
                laserParams = { 'actualLaser':     aLaserNum-1, 
                                'ratio1Center':    float(p['RATIO1_CENTER']),
                                'ratio1Scale':     float(p['RATIO1_SCALE']),
                                'ratio2Center':    float(p['RATIO2_CENTER']),
                                'ratio2Scale':     float(p['RATIO1_SCALE']),
                                'phase':           float(p['PHASE']),
                                'tempSensitivity': float(p['TEMP_SENSITIVITY']),
                                'calTemp':         float(p['CAL_TEMP']),
                                'calPressure':     float(p['CAL_PRESSURE']),
                                'pressureC0':      float(p['PRESSURE_C0']),
                                'pressureC1':      float(p['PRESSURE_C1']),
                                'pressureC2':      float(p['PRESSURE_C2']),
                                'pressureC3':      float(p['PRESSURE_C3'])}
                Driver.wrVirtualLaserParams(vLaserNum,laserParams)
        
    def RPC_updateCal(self):
        """
        Write calibration back to the file with a new checksum.
        """
        cp = CustomConfigObj(self.calFilePath)
        for i in self.freqConverter.keys():
            ac = self.freqConverter[i]
            if ac is not None:
                ac.updateIni(cp, i+1) # Note: In Autocal1, laser indices are 1 based
        try:
            calStrIO = StringIO()
            cp.write(calStrIO)
            calStr = calStrIO.getvalue()
            calStr = calStr[:calStr.find("#checksum=")]
            checksum = crc32(calStr, 0)
            calStr += "#checksum=%d" % checksum
            fp = file(self.calFilePath, "wb")
            fp.write(calStr)
        finally:
            calStrIO.close()
            fp.close()
                
    def RPC_shutdown(self):
        self._shutdownRequested = True
        
if __name__ == "__main__":
    rdFreqConvertApp = RDFrequencyConverter()
    #rdFreqConvertApp.RPC_loadCal("WarmBoxCal.ini")
    #rdFreqConvertApp.RPC_wrFreqScheme(0, Scheme("sample2.sch"))
    #rdFreqConvertApp.RPC_convertScheme(0)
    #rdFreqConvertApp.RPC_uploadSchemeToDAS(0)
    #rdFreqConvertApp.RPC_updateCal()
    Log("RDFrequencyConverter starting")
    rdFreqConvertApp.run()
    Log("RDFrequencyConverter exiting")
