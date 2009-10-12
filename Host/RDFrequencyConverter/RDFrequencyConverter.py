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
#   11-Oct-2009  sze       Added routines to support CalibrateSystem
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
        self.warmBoxCalFilePath = ""
        self.hotBoxCalFilePath = ""
        self.hotBoxCal = None

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
        
    def RPC_restoreOriginalWlmCal(self,vLaserNum):
        # Replace current spline coefficients with original spline coefficients
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        self.freqConverter[vLaserNum-1].replaceCurrent()
        
    def RPC_replaceOriginalWlmCal(self,vLaserNum):
        # Copy current spline coefficients to original coefficients
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        self.freqConverter[vLaserNum-1].replaceOriginal()

    def RPC_waveNumberToAngle(self,vLaserNum,waveNumbers):
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        return self.freqConverter[vLaserNum-1].waveNumber2ThetaCal(waveNumbers)

    def RPC_angleToWaveNumber(self,vLaserNum,angles):
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        return self.freqConverter[vLaserNum-1].thetaCal2WaveNumber(angles)
    
    def RPC_angleToLaserTemperature(self,vLaserNum,angles):
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        return self.freqConverter[vLaserNum-1].thetaCal2LaserTemp(angles)
    
    def RPC_updateWlmCal(self,vLaserNum,thetaCal,waveNumbers,weights,relax=5e-3,relative=True,relaxDefault=5e-3,relaxZero=5e-5):
        """Updates the wavelength monitor calibration using the information that angles specified as "thetaCal"
           map to the specified list of waveNumbers. Also relax the calibration towards the default using
           Laplacian regularization and the specified value of relaxDefault."""
        if (vLaserNum-1 not in self.freqConverter) or self.freqConverter[vLaserNum-1] is None:
            raise ValueError("No frequency converter is present for virtual laser %d." % vLaserNum)
        self.freqConverter[vLaserNum-1].updateWlmCal(thetaCal,waveNumbers,weights,relax,relative,relaxDefault,relaxZero)
        
    def RPC_getHotBoxCalFilePath(self):
        return self.hotBoxCalFilePath

    def RPC_getWarmBoxCalFilePath(self):
        return self.warmBoxCalFilePath
    
    def RPC_loadHotBoxCal(self, hotBoxCalFilePath):
        self.hotBoxCalFilePath = os.path.abspath(hotBoxCalFilePath)
        self.hotBoxCal = CustomConfigObj(self.hotBoxCalFilePath)
        if "AUTOCAL" not in self.hotBoxCal:
            raise ValueError("No AUTOCAL section in hot box calibration.")
        if ("CAVITY_LENGTH_TUNING" not in self.hotBoxCal) and \
           ("LASER_CURRENT_TUNING" not in self.hotBoxCal):
            raise ValueError("Hot box calibration must contain at least one of CAVITY_LENGTH_TUNING or LASER_CURRENT_TUNING sections.")
    
    def RPC_loadWarmBoxCal(self, warmBoxCalFilePath):
        # Load up the frequency converters for each laser in the DAS...
        self.warmBoxCalFilePath = os.path.abspath(warmBoxCalFilePath)
        ini = CustomConfigObj(self.warmBoxCalFilePath)
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

    def RPC_getHotBoxCalParam(self,secName,optName):
        return self.hotBoxCal[secName][optName]
    
    def RPC_setHotBoxCalParam(self,secName,optName,optValue):
        self.hotBoxCal[secName][optName] = optValue
        
    def RPC_updateHotBoxCal(self,fileName=None):
        """
        Write calibration back to the file with a new checksum.
        """
        fp = None
        if self.hotBoxCal is None:
            raise ValueError("Hot box calibration has not been loaded")
        try:
            calStrIO = StringIO()
            self.hotBoxCal.write(calStrIO)
            calStr = calStrIO.getvalue()
            calStr = calStr[:calStr.find("#checksum=")]
            checksum = crc32(calStr, 0)
            calStr += "#checksum=%d" % checksum
            if fileName is not None:
                fp = file(fileName, "wb")
            else:
                fp = file(self.hotBoxCalFilePath, "wb")
            fp.write(calStr)
        finally:
            calStrIO.close()
            if fp is not None: fp.close()
    
    def RPC_updateWarmBoxCal(self,fileName=None):
        """
        Write calibration back to the file with a new checksum.
        """
        fp = None
        cp = CustomConfigObj(self.warmBoxCalFilePath)
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
            if fileName is not None:
                fp = file(fileName, "wb")
            else:
                fp = file(self.warmBoxCalFilePath, "wb")
            fp.write(calStr)
        finally:
            calStrIO.close()
            if fp is not None: fp.close()
                
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
