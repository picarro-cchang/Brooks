#!/usr/bin/python
#
# File Name: FitterPool.py
# Purpose:
#   This application manages a pool of fitter processes, sends data to them and amalgamates the
#    results
#
# Notes:
#
# File History:
# 07-09-26 sze   First release
# 08-05-08 sze   Corrected error handling from pool of fitters, ensuring sockets are properly closed
# 08-10-13  alex  Replaced TCP by RPC

import sys
if "../Common" not in sys.path: sys.path.append("../Common")
from SharedTypes import CrdsException
import time
import threading
from cPickle import loads
from EventManagerProxy import *
import CmdFIFO

EventManagerProxy_Init("FitterPool", PrintEverything = __debug__)
DEFAULT_FITTER_TIMEOUT_s = 300
APP_NAME = "FitterPool"

if sys.platform == 'win32':
    from time import clock as TimeStamp
else:
    from time import time as TimeStamp

class FitterPoolErr(CrdsException):
    """Base exception for errors with the Fitter Proxy."""

class FitterTimeout(FitterPoolErr):
    """Timed out while waiting for Fitter."""

class FitterInterrupted(FitterPoolErr):
    """A fit operation was intentionaly interrupted somehow."""

class FitterError(FitterPoolErr):
    """Fitter raised an error during operation."""

class FitterProxy(object):
    def __init__(self, RpcPort, IpAddress = "localhost", FitterTimeout_s = DEFAULT_FITTER_TIMEOUT_s):
        self.fitterProxy = CmdFIFO.CmdFIFOServerProxy("http://%s:%d" % (IpAddress, RpcPort),
                                                       APP_NAME,
                                                       IsDontCareConnection = False)                            
        self.FitterTimeout_s = FitterTimeout_s
        self.EnabledFlag_Event = None
        
    def setEnableEvent(self,eventObject):
        self.EnabledFlag_Event = eventObject
        
    def init(self):
        return self.fitterProxy.FITTER_initialize()

    def setSpectra(self, spectra): 
        self.fitterProxy.FITTER_setSpectra(spectra)
        
    def getResults(self):
        """Get and convert Fitter result string into a dictionary."""
        startTime = TimeStamp()
        ResultString = ""
        while ResultString == "":
            ResultString = self.fitterProxy.FITTER_getResults()
            if ResultString != "":
                break
            else:
                self.checkAbort(startTime)
                
        if ResultString[:12] == "FIT COMPLETE":
            return loads(ResultString[13:])
        elif ResultString[:12] == "FITTER ERROR":
            raise FitterError("Fitter error during operation")        
        else:
            raise ValueError("Bad result string from fitter: %s..." % ResultString[:20])
            
    def ping(self):
        return self.fitterProxy.CmdFIFO.PingFIFO()    

    def checkAbort(self, startTime):
        if (TimeStamp() - startTime) > self.FitterTimeout_s:
            raise FitterTimeout("Fitter timeout after %s" % (self.FitterTimeout_s,))
        if self.EnabledFlag_Event and not self.EnabledFlag_Event.isSet():
            raise FitterInterrupted("Fitter EnabledFlag_Event cleared while waiting for Fitter response.")
            
class FitterPool(object):
    def __init__(self, RpcPortList, IpAddressList, FitterTimeout_s = DEFAULT_FITTER_TIMEOUT_s):
        """Defines the members of the fitter pool. The number of members specifies the lengths
        of RpcPortList and IpAddressList"""
        self.fitters = []
        # Used for zero-order hold of previous fit values, since each fitter may not update
        #  all keys
        self.cachedFitValues = {}
        if len(RpcPortList) != len(IpAddressList):
            raise ValueError("Fitter pool port and address lists are of different lengths")
        for port, address in zip(RpcPortList,IpAddressList):
            #Log("Added FitterProxy address: %s, port: %d" % (address, port))
            self.fitters.append(FitterProxy(port, address, FitterTimeout_s))

    def SetEnableEvent(self,eventObject):
        # Pass an Event object to all fitters so that they may be interrupted (by
        #  clearing the event)
        for f in self.fitters:
            f.setEnableEvent(eventObject)

    def FitSpectra(self, spectra):
        # Send the data to all the fitters and collect the results
        for f in self.fitters:
            f.setSpectra(spectra)
        return self._CollectResults()

    def _CollectResults(self):
        # Collect up the data
        fitResults = []
        allResults = []
        allOk = True
        for f in self.fitters:
            try:
                fitResults += f.getResults()
            except Exception,e:
                Log("Exception while reading response from fitter %s: %r (%s)" % (f,e,e))
                allOk = False
        if not allOk:
            raise e
        # Sort into time order and update the cached values. Write out a list
        # [(t1,rDict1),(t2,rDict2),...] of results from all fitters put together
        # where t's are distinct and in ascending order
        fitResults.sort()
        tPrev = None
        rDict = None
        for t,rDict,spectrumId in fitResults:
            if rDict:
                if t != tPrev and tPrev != None:
                    allResults.append((tPrev,self.cachedFitValues.copy(),spectrumId))
                tPrev = t
                self.cachedFitValues.update(rDict)
        if rDict: allResults.append((tPrev,self.cachedFitValues.copy(),spectrumId))
        # if fitResults is empty, the tPrev will remain None, and an error will be reported in MeasSystem      
        return allResults

    def Ping(self):
        for f in self.fitters:
            f.ping()

    def Init(self):
        self.cachedFitValues = {}
        for f in self.fitters:
            f.init()
