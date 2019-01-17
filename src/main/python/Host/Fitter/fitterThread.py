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
    10-12-07 sze   Make copies of DATA when passing them to multiple fitter scripts executed in
                    distinct environments so that filtering operations done in one script do not
                    affect the others
    11-06-04 sze   Use a Listener to get spectra from the spectrum collector instead of getting spectra from
                    the measurement system
    13-10-19 sze   Add spectral duration for each spectrum to RESULTS dictionary

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "Fitter"
APP_VERSION = 1.0
_DEFAULT_CONFIG_NAME = "Fitter.ini"
_MAIN_CONFIG_SECTION = "Setup"

import os
import sys
from sys import argv
from Host.Common.CmdFIFO import CmdFIFOServer, CmdFIFOServerProxy
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.timestamp import getTimestamp
from copy import copy, deepcopy
from cStringIO import StringIO
from Queue import Queue, Empty, Full
from threading import Thread, Event
from time import sleep
from traceback import format_exc
from cPickle import dumps

from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log
from Host.Fitter.fitterCoreWithFortran import loadPhysicalConstants, loadSpectralLibrary, loadSplineLibrary
from Host.Fitter.fitterCoreWithFortran import pickledRepository, pickledRepositoryFromList, hdf5RepositoryFromList
from Host.Fitter.fitterCoreWithFortran import RdfData, Analysis, InitialValues, Dependencies
from Host.Common.FitterScriptFunctions import expAverage, initExpAverage, fitQuality
from Host.Common.SharedTypes import RPC_PORT_FITTER_BASE, RPC_PORT_SUPERVISOR, BROADCAST_PORT_FITTER_BASE, BROADCAST_PORT_SPECTRUM_COLLECTOR
from Host.Common import Broadcaster, Listener, StringPickler
from Host.Common.AppRequestRestart import RequestRestart

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
    def __init__(self,configFile, readyEvent = None):
        self.supervisor = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME,
                                                     IsDontCareConnection=False)
        self.stopOnError = 1 # Show modal dialog (and stop fitter) on error
        configFile = os.path.abspath(configFile)
        self.readyEvent = readyEvent
        self.iniBasePath = os.path.split(configFile)[0]
        self.config = CustomConfigObj(configFile)
        # Iterate through all script files, specified by keys which start with "script"
        self.scriptNames = []
        for key in self.config[_MAIN_CONFIG_SECTION]:
            if key.lower().startswith("script"):
                self.scriptNames.append(os.path.join(self.iniBasePath,self.config[_MAIN_CONFIG_SECTION][key]))
        self.rpcPort = self.config.getint("Setup","RPCport",RPC_PORT_FITTER_BASE)
        self.broadcastPort = self.rpcPort - RPC_PORT_FITTER_BASE + BROADCAST_PORT_FITTER_BASE
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
        self.fitterOption = ""
        self.inputFile = None
        self.FITTER_initialize()
        self.fitBroadcaster = Broadcaster.Broadcaster(self.broadcastPort, APP_NAME, logFunc=Log)
        self.spectQueue = Queue(200)
        self.spectListener = Listener.Listener(self.spectQueue,
                                          BROADCAST_PORT_SPECTRUM_COLLECTOR,
                                          StringPickler.ArbitraryObject,
                                          retry = True,
                                          name = "Fitter listener")

    def registerRpc(self):
        self.rpcServer.register_function(self.FITTER_fitSpectrumRpc)
        self.rpcServer.register_function(self.FITTER_setProcModeRpc)
        self.rpcServer.register_function(self.FITTER_setSingleModeRpc)
        self.rpcServer.register_function(self.FITTER_makeHdf5RepositoryRpc)
        self.rpcServer.register_function(self.FITTER_makePickledRepositoryRpc)
        self.rpcServer.register_function(self.FITTER_getFitterStateRpc)
        self.rpcServer.register_function(self.FITTER_updateViewer)
        self.rpcServer.register_function(self.FITTER_showViewer)
        self.rpcServer.register_function(self.FITTER_initialize)
        self.rpcServer.register_function(self.FITTER_maximizeViewer)
        self.rpcServer.register_function(self.FITTER_setOption)
        self.rpcServer.register_function(self.FITTER_setInputFile)

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

    def FITTER_maximizeViewer(self, max=True):
        try:
            self.fitQueue.put((4, max), False)
        except:
            pass

    def FITTER_setOption(self,option):
        self.fitterOption = option
        self.FITTER_initialize()

    def FITTER_setInputFile(self,inputFile):
        self.inputFile = inputFile

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
        dataEnviron["OPTION"] = self.fitterOption
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

        if self.inputFile:
            self.repository = hdf5RepositoryFromList([self.inputFile])
            # Reinitialize the fitter, setting INIT to True in the script environment
            self.loadRepository = False
            self.FITTER_initialize()
            Analysis.resetIndex()
            self.fitSpectrum = True
            self.singleMode = False
            self.procMode = False
            self.inputFile = ""
            self.state = FITTER_STATE_READY
        elif self.procMode:
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
                # Carry out the fitting and broadcast results
                ts,results,spectrumId = self.execScripts()
                latency = 0.001*(getTimestamp() - ts)
                if results: self.fitBroadcaster.send(StringPickler.PackArbitraryObject((ts,results,spectrumId,latency)))
                if not self.fitSpectrum:
                    self.state = FITTER_STATE_READY
            except StopIteration:
                print "Repository empty"
                self.fitSpectrum = False
                if self.inputFile is not None:
                    self.exitFlag = True
                    self.state = FITTER_STATE_IDLE
                else:
                    self.state = FITTER_STATE_READY # Repository has been exhausted

        if self.state == FITTER_STATE_PROC:
            # You can get here if you are reprocessing ringdown *.h5 files
            # with the VirtualAnalyzer.
            # This goes through one scheme's worth of ringdown data, fitting
            # any and all spectra in it.
            #
            try:
                spect = self.spectQueue.get(timeout=DATA_AVAIL_EVENT_TIMEOUT)
                if self.compiledScriptsAndEnvironments:
                    try:
                        if spect["controlData"]:
                            for self.spectrum in RdfData.getSpectraDict(spect):
                                # Carry out the fitting and broadcast results
                                ts,results,spectrumId = self.execScripts()
                                latency = 0.001*(getTimestamp() - ts)
                                if results: self.fitBroadcaster.send(StringPickler.PackArbitraryObject((ts,results,spectrumId,latency)))
                    except:
                        tbMsg = format_exc()
                        Log("Error in FIT_DATA while executing fitter script",
                            Data = dict(Note = "<See verbose for debug info>"),
                            Level = 3,
                            Verbose = tbMsg)
                        print tbMsg
                else:
                    Log("Error fitter is not initialized")
            except:
                self.state = FITTER_STATE_IDLE

    def execScripts(self):
        # Returns tuple of (timestamp,resultsDict,spectrumId) from fitting
        # All scripts are run in sequence and the results from all of them
        # are combined
        DATA = self.spectrum
        RESULTS = {}
        ANALYSES = []
        for code,env in self.compiledScriptsAndEnvironments:
            env["DATA"] = copy(DATA)
            env["RESULT"] = {}
            env["BASEPATH"] = self.iniBasePath
            exec code in env
            env["INIT"] = False
            ANALYSES += env["ANALYSIS"]
            RESULTS.update(env["RESULT"])
            try:
                if RESULTS:
                    RESULTS["spect_latency"] = getattr(self.spectrum,"spectLatency")
                    RESULTS["spect_duration"] = getattr(self.spectrum,"spectDuration")
            except:
                print "Warning: spectrum does not have spectLatency or spectDuration attributes"
        self.fitViewer([DATA,ANALYSES,RESULTS])
        return (DATA.avgTimestamp,RESULTS,DATA["spectrumid"])

    def main(self,queue,useViewer):
        self.fitQueue = queue
        self.showViewer = useViewer
        self.startup()
        # lets wait foe some time so rpc server starts and initialize properly
        # during startup call
        sleep(0.2)
        # lets check if event is not none
        # if event is not none then lets notify parent thread
        # that clild thread is all setup
        if self.readyEvent is not None:
            self.readyEvent.set()
        while not self.exitFlag:
            try:
                self.stateMachine()
                sleep(0.001)
            except:
                tbMsg = format_exc()
                Log("Exception during fitter script execution",
                    Data = dict(Note = "<See verbose for debug info>"),
                    Level = 3,
                    Verbose = tbMsg)
                print tbMsg
                if self.stopOnError:
                    self.fitQueue.put((3,tbMsg))
                    self.loadRepository = True
                    self.fitSpectrum = False
        self.spectListener.stop()
        self.fitBroadcaster.stop()
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
            print tbMsg

def main(configFile,queue,useViewer,readyEvent = None):
    fitter = Fitter(configFile, readyEvent)
    try:
        try:
            fitter.main(queue,useViewer)
        except:
            tbMsg = format_exc()
            Log("Unhandled exception trapped by last chance handler",
                Data = dict(Note = "<See verbose for debug info>"),
                Level = 3,
                Verbose = tbMsg)
            # Request a restart from Supervisor via RPC call
            restart = RequestRestart(APP_NAME)
            if restart.requestRestart(APP_NAME) is True:
                Log("Restart request to supervisor sent", Level=0)
            else:
                Log("Restart request to supervisor not sent", Level=2)
            print tbMsg
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
