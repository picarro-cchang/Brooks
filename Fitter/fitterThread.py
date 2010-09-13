#!/usr/bin/python
#
"""
File Name: FitterThread.py
Purpose:
    The fitterThread carries out spectral fitting using instructions contained in a fit script
    and is launched by the fitter in a separate thread

File History:
    07-02-xx sze   In progress
    07-05-07 sze   Added time.sleep(0.01) to prevent overuse of CPU
    07-05-08 sze   Renamed fitter to fitterThread and fitViewer to fitter
    07-05-11 sze   Corrected handling of listening socket for TCP
    07-09-02 sze   For Python 2.5, creating a generator in one thread and using it in another can
                   cause problems. Repository creation has been moved into one thread to avoid this.
    07-10-04 sze   Support multiple fitters in a pool using "Port" and "RPCport" options
    07-10-04 sze   Introduce FITTER_ERROR reply to indicated
    08-09-18 alex  Replaced SortedConfigParser with CustomConfigObj
    08-10-13 alex  Replaced TCP by RPC
    09-06-30 alex  Support HDF5 format for spectra data
    10-05-21 sze   Allow multiple fitter scripts, each with a distinct environment that are run in
                    succession with the same data. The results directories from all are combined.
    10-06-24 sze   Added getInstrParams to allow instrument-specific parameters to be read into a 
                    fitter script

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "Fitter"
APP_VERSION = 1.0
_DEFAULT_CONFIG_NAME = "Fitter.ini"
_MAIN_CONFIG_SECTION = "Setup"

import os
import sys
from sys import argv
from Host.Common.CmdFIFO import CmdFIFOServer
from Host.Common.CustomConfigObj import CustomConfigObj
from copy import deepcopy
from cStringIO import StringIO
from Queue import Queue, Empty, Full
from threading import Thread, Event
from time import sleep
from traceback import format_exc
from cPickle import dumps

from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log
from fitterCoreWithFortran import loadPhysicalConstants, loadSpectralLibrary, loadSplineLibrary
from fitterCoreWithFortran import pickledRepository, pickledRepositoryFromList, hdf5RepositoryFromList
from fitterCoreWithFortran import RdfData, Analysis, InitialValues, Dependencies
from Host.Common.FitterScriptFunctions import expAverage, initExpAverage, fitQuality
from Host.Common.SharedTypes import RPC_PORT_FITTER, TCP_PORT_FITTER

EventManagerProxy_Init(APP_NAME,DontCareConnection = True)
FITTER_STATE_IDLE = 0
FITTER_STATE_PROC = 1
FITTER_STATE_READY = 2
FITTER_STATE_FITTING = 3
FITTER_STATE_COMPLETE = 4

DATA_AVAIL_EVENT_TIMEOUT = 10.0
RESULTS_AVAIL_EVENT_TIMEOUT = 10.0

def evalLeaves(d):
    for k in d:
        if isinstance(d[k],dict): 
            evalLeaves(d[k])
        else:
            try:
                d[k] = eval(d[k])
            except:
                pass
    return d
    
def getInstrParams(fname):
    fp = file(fname,"rb")
    try:
        return evalLeaves(CustomConfigObj(fp,list_values=False).copy())
    finally:
        fp.close()
        
class Fitter(object):
    def __init__(self,configFile):
        self.stopOnError = 1 # Show modal dialog (and stop fitter) on error
        configFile = os.path.abspath(configFile)
        self.iniBasePath = os.path.split(configFile)[0]
        self.config = CustomConfigObj(configFile) 
        # Iterate through all script files, specified by keys which start with "script"
        self.scriptNames = []
        for key in self.config[_MAIN_CONFIG_SECTION]:
            if key.lower().startswith("script"):
                self.scriptNames.append(os.path.join(self.iniBasePath,self.config[_MAIN_CONFIG_SECTION][key]))
        self.rpcPort = self.config.getint("Setup","RPCport",RPC_PORT_FITTER)
        self.stopOnError = self.config.getint("Setup","StopOnError",self.stopOnError)
        self.exitFlag = False
        self.spectrum = None
        self.compiledScriptsAndEnvironments = []
        self.state = FITTER_STATE_IDLE
        self.repository = None  # Generator for processing spectra from a list of files
        self.procMode = True
        self.loadRepository = False
        self.fitSpectrum = False
        self.singleMode = False
        self.spectrumFileName = ""
        self.showViewer = False
        self.updateViewer = True
        self.data = None        
        self.dataAvailEvent = Event()
        self.dataAvailEvent.clear() 
        self.resultString = ""        
        self.resultsAvailEvent = Event()
        self.resultsAvailEvent.clear()
              
    def registerRpc(self):
        self.rpcServer.register_function(self.FITTER_fitSpectrumRpc)
        self.rpcServer.register_function(self.FITTER_setProcModeRpc)
        self.rpcServer.register_function(self.FITTER_setSingleModeRpc)
        self.rpcServer.register_function(self.FITTER_makeHdf5RepositoryRpc)
        self.rpcServer.register_function(self.FITTER_makeRdqRepositoryRpc)
        self.rpcServer.register_function(self.FITTER_makePickledRepositoryRpc)
        self.rpcServer.register_function(self.FITTER_getFitterStateRpc)
        self.rpcServer.register_function(self.FITTER_updateViewer)
        self.rpcServer.register_function(self.FITTER_showViewer)
        self.rpcServer.register_function(self.FITTER_initialize)      
        self.rpcServer.register_function(self.FITTER_setSpectra)
        self.rpcServer.register_function(self.FITTER_getResults)   
        self.rpcServer.register_function(self.FITTER_maximizeViewer)          
        
    def _rpcServerExit(self):
        self.exitFlag = True
        self.rpcServer.stop_server()

    def FITTER_showViewer(self):
        self.showViewer = True
        return {"status":"ok"}

    def FITTER_fitSpectrumRpc(self):
        """Call to start fitting spectra"""
        self.fitSpectrum = True
        return {"status":"ok"}

    def FITTER_setProcModeRpc(self,mode):
        """Call with mode=True to place fitter in non-interactive processing mode.
        After setting the PROC mode, fitter is placed in the idle state"""
        self.procMode = mode
        self.state = FITTER_STATE_IDLE
        return {"status":"ok"}

    def FITTER_setSingleModeRpc(self,mode):
        """Call with mode=True to process one spectrum each time fitSpectrumRpc() is
        called. Call with mode=False to keep processing spectra continuously"""
        self.singleMode = mode
        return {"status":"ok"}

    def FITTER_makeHdf5RepositoryRpc(self,fileList):
        """Pass a list of HDF5 file names (.h5) to the fitter to construct a repository which is
        attached to self.repository"""
        self.makeRepository = hdf5RepositoryFromList
        self.makeRepositoryArgs = (fileList,)
        self.loadRepository = True

    def FITTER_makeRdqRepositoryRpc(self,fileList):
        """Pass a list of Rdq file names to the fitter to construct a repository which is
        attached to self.repository"""
        self.makeRepository = rdqRepositoryFromList
        self.makeRepositoryArgs = (fileList,)
        self.loadRepository = True

    def FITTER_makePickledRepositoryRpc(self,fileList):
        """Pass a list of pickled rdf file names to the fitter to construct a repository which is
        attached to self.repository"""
        self.makeRepository = pickledRepositoryFromList
        self.makeRepositoryArgs = (fileList,)
        self.loadRepository = True

    def FITTER_getFitterStateRpc(self):
        return self.state

    def FITTER_updateViewer(self,update):
        self.updateViewer = update

    def FITTER_initialize(self):    
        self.compiledScriptsAndEnvironments = [(self.compileScript(name),self.setupEnvironment()) for name in self.scriptNames]
        return "Fitter Initialized"

    def FITTER_setSpectra(self, spectra):
        self.data = spectra
        self.dataAvailEvent.set() 
                
    def FITTER_getResults(self):
        self.resultsAvailEvent.wait(RESULTS_AVAIL_EVENT_TIMEOUT)      
        if self.resultsAvailEvent.isSet():  
            self.resultsAvailEvent.clear()
            return self.resultString
        else:
            # resultsAvailEvent timeout
            self.state = FITTER_STATE_IDLE
            return ""
    def FITTER_maximizeViewer(self, max=True):
        try:
            self.fitQueue.put((4, max), False)
        except:
            pass
   
    def compileScript(self,scriptName):
        try:
            fp = file(scriptName,"r")
            string = fp.read().strip()
            if sys.platform != 'win32':
                string = string.replace("\r", "")
            fp.close()
        except IOError:
            Log("Fitter script file %s cannot be processed" % (scriptName,))
            raise
        return compile(string,scriptName,"exec")

    def setupEnvironment(self):
        dataEnviron = {}
        dataEnviron["loadPhysicalConstants"] = loadPhysicalConstants
        dataEnviron["loadSpectralLibrary"] = loadSpectralLibrary
        dataEnviron["loadSplineLibrary"] = loadSplineLibrary
        dataEnviron["Analysis"] = Analysis
        dataEnviron["InitialValues"] = InitialValues
        dataEnviron["Dependencies"] = Dependencies
        dataEnviron["RdfData"] = RdfData
        dataEnviron["INIT"] = True
        dataEnviron["expAverage"] = expAverage
        dataEnviron["initExpAverage"] = initExpAverage
        dataEnviron["fitQuality"] = fitQuality
        dataEnviron["getInstrParams"] = getInstrParams
        return dataEnviron

    def fitViewer(self,dataAnalysisResult):
        """ Send results to viewer if requested. dataAnalysisResult is a list consisting of the DATA, ANALYSIS
        and RESULT objects from the fitter script. The data is sent to the fit viewer via the fitQueue.
        For data sources other than TCP, hang around until the put succeeds, or until someone tells us not to 
        update the viewer """
        
        while self.updateViewer:
            if self.state == FITTER_STATE_PROC:
                # We cannot wait for the viewer, just discard data if the queue is full and leave quickly
                try:
                    self.fitQueue.put((1,(deepcopy(dataAnalysisResult),self.spectrumFileName)),False)
                except:
                    pass
                break
            else: # Wait until we can put something on
                try:
                    self.fitQueue.put((1,(deepcopy(dataAnalysisResult),self.spectrumFileName)),timeout=1.0)
                    break
                except Full:
                    continue
                    
    def startup(self):
        self.rpcServer = CmdFIFOServer(("", self.rpcPort),
                                        ServerName = APP_NAME,
                                        ServerDescription = "The fitter.",
                                        ServerVersion = APP_VERSION,
                                        threaded = True)
        self.registerRpc()
        #start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self._rpcServerExit)
        self.rpcThread.start()

    def stateMachine(self):
        # Handle unconditional changes of state
        if self.showViewer:
            try:
                self.fitQueue.put((0,None),False)
                self.showViewer = False
            except Full:
                pass
            
        if self.procMode:
            self.state = FITTER_STATE_PROC
        elif self.loadRepository:
            # The repository needs to be initialized and placed in self.repository.
            # Restart scripts from the beginning
            self.repository = self.makeRepository(*self.makeRepositoryArgs)
            # Reinitialize the fitter, setting INIT to True in the script environment
            self.FITTER_initialize()
            Analysis.resetIndex()
            self.state = FITTER_STATE_READY
            self.loadRepository = False
            
        # Here follows the state transition table
        if self.state == FITTER_STATE_READY:
            if self.fitSpectrum:
                self.state = FITTER_STATE_FITTING
                
        if self.state == FITTER_STATE_FITTING:
            if self.singleMode: 
                self.fitSpectrum = False
            try:
                self.spectrum,self.spectrumFileName = self.repository.next()
                t,r,spectrumId = self.execScripts()
                if not self.fitSpectrum:
                    self.state = FITTER_STATE_READY
            except StopIteration:
                print "Repository empty"
                self.fitSpectrum = False
                self.state = FITTER_STATE_READY # Repository has been exhausted
                
        if self.state == FITTER_STATE_PROC:      
            self.dataAvailEvent.wait(DATA_AVAIL_EVENT_TIMEOUT)      
            if self.dataAvailEvent.isSet():
                if self.compiledScriptsAndEnvironments:
                    try:
                        # Get data past the \r, then iterate over the list of spectra
                        #  which make up self.data
                        fitResults = []
                        for spectra in self.data:
                            if not spectra["controlData"]:
                                #Empty spectrum
                                continue
                            for self.spectrum in RdfData.getSpectraDict(spectra):
                                fitResults.append(self.execScripts())
                        self.resultString = "FIT COMPLETE\r" + dumps(fitResults)
                    except:
                        self.resultString = "FITTER ERROR\r" # Send back error string, log reason locally
                        tbMsg = format_exc()
                        Log("Error in FIT_DATA while executing fitter script",
                            Data = dict(Note = "<See verbose for debug info>"),
                            Level = 3,
                            Verbose = tbMsg)
                else:
                    self.resultString = "ERR: initialize fitter first\r"
                self.resultsAvailEvent.set()
                self.dataAvailEvent.clear()
            else:
                # Data not ready yet
                self.state = FITTER_STATE_IDLE               

    def execScripts(self):
        # Returns tuple of (time,resultsDict,spectrumId) from fitting
        # All scripts are run in sequence and the results from all of them
        # are combined
        DATA = self.spectrum
        RESULTS = {}
        ANALYSES = []
        for code,env in self.compiledScriptsAndEnvironments:
            env["DATA"] = DATA
            env["RESULT"] = {}
            env["BASEPATH"] = self.iniBasePath
            exec code in env
            env["INIT"] = False
            ANALYSES += env["ANALYSIS"]
            RESULTS.update(env["RESULT"])
        self.fitViewer([DATA,ANALYSES,RESULTS])
        return (DATA.getTime(),RESULTS,DATA["spectrumid"])

    def main(self,queue,useViewer):
        self.fitQueue = queue
        self.showViewer = useViewer
        self.startup()
        while not self.exitFlag:
            try:
                self.stateMachine()
                sleep(0.01)
            except:
                tbMsg = format_exc()
                Log("Exception during fitter script execution",
                    Data = dict(Note = "<See verbose for debug info>"),
                    Level = 3,
                    Verbose = tbMsg)
                if self.stopOnError:
                    self.fitQueue.put((3,tbMsg))
                    self.loadRepository = True
                    self.fitSpectrum = False

    def debug(self,configFile):
        self.fitQueue = None
        self.showViewer = False
        self.iniBasePath = os.path.split(configFile)[0]
        self.config = CustomConfigObj(configFile, file_error=True)
        print "Call stateMachine() function on fitter object"

class RpcServerThread(Thread):
    def __init__(self, RpcServer, ExitFunction):
        Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.RpcServer = RpcServer
        self.ExitFunction = ExitFunction
    def run(self):
        self.RpcServer.serve_forever()
        try: #it might be a threading.Event
            self.ExitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            tbMsg = format_exc()
            Log("Exception raised when calling exit function at exit of RPC server.",
                Data = dict(Note = "<See verbose for debug info>"),
                Level = 3,
                Verbose = tbMsg)

def main(configFile,queue,useViewer):
    fitter = Fitter(configFile)
    try:
        try:
            fitter.main(queue,useViewer)
        except:
            tbMsg = format_exc()
            Log("Unhandled exception trapped by last chance handler",
                Data = dict(Note = "<See verbose for debug info>"),
                Level = 3,
                Verbose = tbMsg)
            fitter.fitQueue.put((3,tbMsg))
    finally:
        fitter.fitQueue.put((2,None)) # Shut down the fit viewer
        sys.exit()

if __name__ == "__main__":

    def testFitter():
        F = Fitter()
        F.debug("fitter.ini")
        F.FITTER_makePickledRepositoryRpc([r"R:\crd\CFBDS01\Integration\SampleSpectra\Expt\002_1190138204000.rdf",
                                           r"R:\crd\CFBDS01\Integration\SampleSpectra\Expt\002_1190138205500.rdf"])
        F.FITTER_updateViewer(False)
        F.FITTER_fitSpectrumRpc()
        F.FITTER_setProcModeRpc(False)
        while F.fitSpectrum:
            F.stateMachine()

    testFitter()
    #import profile
    #profile.run("testFitter()","c:/temp/fitterProfile")
