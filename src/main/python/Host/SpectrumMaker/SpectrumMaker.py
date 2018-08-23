#!/usr/bin/python
#
"""
File Name: SpectrumMaker.py
Purpose: Makes synthetic spectrum files to test the fitter

File History:
    01-Jun-2011  sze       Initial version
Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "SpectrumMaker"

import sys
import getopt
import inspect
import operator
import os
from numpy import *
from pylab import *
from matplotlib.ticker import ScalarFormatter

from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, Listener, Broadcaster
from Host.Common.SchemeProcessor import Scheme
from Host.Common.SharedTypes import Singleton
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.timestamp import getTimestamp
from Host.Fitter.fitterCoreWithFortran import *

INCR_FLAG_MASK       = interface.SUBSCHEME_ID_IncrMask   # 32768 - Bit 15 is used for special increment flag
SPECTRUM_IGNORE_MASK = interface.SUBSCHEME_ID_IgnoreMask # 16384 - Bit 14 is used to indicate the point should be ignored
SPECTRUM_RECENTER_MASK = interface.SUBSCHEME_ID_RecenterMask # 8192 - Bit 13 is used to indicate that the virtual laser tuner offset is to be adjusted
SPECTRUM_ISCAL_MASK  = interface.SUBSCHEME_ID_IsCalMask  #  4096 - Bit 12 is used to flag a point as a cal point to be collected
SPECTRUM_SUBSECTION_ID_MASK = interface.SUBSCHEME_ID_SpectrumSubsectionMask
SPECTRUM_ID_MASK     = interface.SUBSCHEME_ID_SpectrumMask # Bottom 8 bits of schemeStatus are the spectrum id/name
EventManagerProxy_Init(APP_NAME)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

class Spectrum(object):
    def __init__(self,name,config,basePath,env):
        self.name = name
        libName = os.path.join(basePath,eval(config["Library"],env))
        self.spectralLibrary = loadSpectralLibrary(libName)
        self.splineLibrary = loadSplineLibrary(libName)
        self.physicalConstants = loadPhysicalConstants(libName)
        self.config = config
        self.spectrumIds = asarray(eval(config["SpectrumId"]+",",env))

    def setupModel(self, env):
        config = self.config
        self.basisArray = asarray(eval(config["identification"]+",",env))
        self.centerFrequency = eval(config["center"],env) if "center" in config else 0
        self.basisFunctions = {}
        m = Model()
        m.setAttributes(x_center=self.centerFrequency)
        if "pressure" in env: m.setAttributes(pressure = env["pressure"])
        if "temperature" in env: m.setAttributes(temperature = env["temperature"])
        m.addToModel(Quadratic(offset=0.0,slope=0.0,curvature=0.0),index=None)
        m.registerXmodifier(FrequencySquish(offset=0.0,squish=0.0))
        m.addDummyParameter(sum(self.basisArray<1000))
        for basisName in config:
            if basisName.startswith("function"):
                self.basisFunctions[basisName] = dict(config[basisName])
        for i in self.basisArray:
            if i<1000:
                m.addToModel(Galatry(peakNum=i,physicalConstants=self.physicalConstants,spectralLibrary=self.spectralLibrary),index=i)
            else: # We need to get details of the basis function
                basisParams = self.basisFunctions["function%d" % i]
                # Local function to construct a basis function with parameters "a%d" from the ini file
                def FP(basisFunc,extra={}):
                    nParams = basisFunc.numParams()
                    a = []
                    for j in range(nParams): a.append(eval(basisParams["a%d" % j],env))
                    return basisFunc(params=asarray(a),**extra)

                form = eval(basisParams["functional_form"],env)
                if form == "sinusoid":
                    m.addToModel(FP(Sinusoid),index=i)
                elif form[:6] == "spline":
                    m.addToModel(FP(Spline,dict(splineLibrary=self.splineLibrary,splineIndex=int(form[6:]))),index=i)
                elif form[:8] == "bispline":
                    ndx = form[8:].split("_")
                    m.addToModel(FP(BiSpline,dict(splineLibrary=self.splineLibrary,
                                                  splineIndexA=int(ndx[0]),
                                                  splineIndexB=int(ndx[1]))),index=i)
                else:
                    raise ValueError("Unimplemented functional form: %s" % form)
        self.model = m
        self.updateModel(env)

    def updateModel(self, env):
        config = self.config
        m = self.model
        if "pressure" in env:
            m.setAttributes(pressure = env["pressure"])
        if "temperature" in env:
            m.setAttributes(temperature = env["temperature"])
        m.createParamVector()
        # Modify parameter values according to [base] and [peak] sections
        for basisName in config:
            if basisName in ["base"]:
                for var in config["base"]:
                    try:
                        if var[0] != 'a': raise ValueError
                        index = int(var[1:])
                    except:
                        print "Invalid argument name %s for base" % var
                        raise
                    m["base",index] = eval(config["base"][var],env)
            elif basisName.startswith("peak"):
                pkNum = int(basisName[4:])
                for var in config[basisName]:
                    done = False
                    if var[0] == 'a':
                        try:
                            index = int(var[1:])
                            m[pkNum,index] = eval(config[basisName][var],env)
                            done = True
                        except:
                            pass
                    if not done:
                        m[pkNum,var] = eval(config[basisName][var],env)
        self.model = m

class SpectrumMaker(Singleton):
    rdfIndex = 0
    initialized = False
    def __init__(self, configPath=None,env={}):
        self.startTime = getTimestamp()
        self.variables = [],[]
        basePath = os.path.split(configPath)[0]
        if not self.initialized:
            if configPath != None:
                # Process INI file
                cp = CustomConfigObj(configPath)
                self.spectra = {}
                self.libraries = {}
                self.spectrumNamesById = {}
                for secName in cp:
                    if secName.startswith("CODE"):
                        code = compile(cp[secName]["code"],secName,"exec")
                        exec code in env
                    elif secName in ["VARIABLES"]:
                        self.variables = self.findVariables(cp[secName],env)
                    elif secName.startswith("SPECTRUM"):
                        sp = Spectrum(secName,cp[secName],basePath,env)
                        for id in sp.spectrumIds:
                            if id not in self.spectrumNamesById:
                                self.spectrumNamesById[id] = []
                            self.spectrumNamesById[id].append(secName)
                        self.spectra[secName] = sp
                self.baseEnv = env.copy()
                self.config = cp
                self.schemeCount = eval(cp.get("SCHEME_CONFIG", "schemeCount", "1"),env)
                self.schemePaths = []
                self.schemes = []
                for i in range(self.schemeCount):
                    path = eval(cp.get("SCHEME_CONFIG", "Scheme_%d_Path" % (i+1,)),env)
                    self.schemePaths.append(path)
                    s = Scheme(path)
                    self.schemes.append(s)
            else:
                raise ValueError("Configuration file must be specified to initialize SpectrumMaker")
            self.initialized = True

    def genSpectra(self):
        """Generator yielding model spectra. For each set of parameter values, we get a dictionary
        of spectra which may be used to synthesize data at a collection of frequencies."""
        for env in self.genEnv():
            env.update(self.baseEnv)
            for name in self.spectra:
                self.spectra[name].setupModel(env)
            yield self.spectra

    def genEnv(self):
        """Generator yielding environment dictionaries with variables as keys and
            values drawn from constants and the outer product of sequences"""
        constants, sequences = self.variables
        def _genEnv(*sequences):
            if len(sequences) == 0: yield ()
            else:
                for y in _genEnv(*(sequences[:-1])):
                    name, seq = sequences[-1]
                    for x in seq: yield y+(x,)
        for values in _genEnv(*sequences):
            names = [name for name,s in sequences]
            envDict = dict(constants)
            for name,v in zip(names,values): envDict[name]=v
            self.currentEnv = envDict
            yield envDict

    def findVariables(self,variables,env={}):
        # Find entries in the variables dictionary which have values that evaluate to sequences
        #  and those which evaluate to constants. The result is the pair constants, sequences
        #  where constants is a list with (name,value) pairs and sequences is a list of
        #  (name,sequence) pairs, where name is the name of the variable and sequence is a
        #  tuple of values that the variable must assume
        constants, sequences = [], []
        for k in variables:
            v = variables[k]
            e = eval(v,env)
            if operator.isSequenceType(e):
                sequences.append((k,e))
            else:
                constants.append((k,e))
        return constants, sequences

    def collectSpectrum(self,spectra,scheme):
        s = scheme
        #for i in range(s.numEntries):
        #    print "%11.5f,%6d,%6d, %1d,%6d,%6d,%8.4f, %d, %d, %d, %d" % (s.setpoint[i],\
        #            s.dwell[i],s.subschemeId[i],s.virtualLaser[i],s.threshold[i],s.pztSetpoint[i],\
        #            s.laserTemp[i],s.extra1[i],s.extra2[i],s.extra3[i],s.extra4[i])
        nu = asarray(s.setpoint)
        spectrumId = asarray(s.subschemeId) & SPECTRUM_ID_MASK
        tot = zeros(nu.shape)
        # We need to do calculations for each spectrumId separately and combine them,
        #  since different spectra may be involved
        for id in unique(spectrumId):
            rows = spectrumId == id
            if id not in self.spectrumNamesById: continue
            for spectrum in [spectra[name] for name in self.spectrumNamesById[id]]:
                tot[rows] += spectrum.model(nu[rows])

        rdfDict = {"rdData": dict(waveNumber=[], waveNumberSetpoint=[], uncorrectedAbsorbance=[],correctedAbsorbance=[],
                                       subschemeId=[], timestamp=[], tunerValue=[], pztValue=[],
                                       cavityPressure=[], fineLaserCurrent=[], laserUsed=[], laserTemperature=[],
                                       extra1=[], extra2=[], extra3=[], extra4=[], ratio1=[], ratio2=[], wlmAngle=[]),
                        "sensorData": dict(timestamp=[], SpectrumID=[], CavityPressure=[], CavityTemp=[],
                                           ValveMask=[], DasTemp=[], EtalonTemp=[], WarmBoxTemp=[],
                                           InletValve=[], OutletValve=[], MPVPosition=[]),
                        "tagalongData":{},
                        "controlData": dict(RDDataSize=[],SpectrumQueueSize=[])}

        rdData = rdfDict["rdData"]
        sensorData = rdfDict["sensorData"]
        controlData = rdfDict["controlData"]
        rowsInSpectrum = 0
        # Go through the scheme rows and fill up rdfDict appropriately
        for i in range(s.numEntries):
            for d in range(s.dwell[i]):
                rdData["waveNumber"].append(nu[i])
                rdData["waveNumberSetpoint"].append(nu[i])
                rdData["uncorrectedAbsorbance"].append(0.001*tot[i])
                rdData["correctedAbsorbance"].append(0.001*tot[i])
                rdData["subschemeId"].append(s.subschemeId[i])
                rdData["timestamp"].append(self.startTime)
                self.startTime += 5
                rdData["tunerValue"].append(32768.0)
                rdData["pztValue"].append(32768.0)
                rdData["cavityPressure"].append(self.currentEnv.get("pressure",140.0))
                rdData["fineLaserCurrent"].append(36000)
                rdData["laserUsed"].append(0)
                rdData["extra1"].append(0L)
                rdData["extra2"].append(0L)
                rdData["extra3"].append(0L)
                rdData["extra4"].append(0L)
                rdData["ratio1"].append(2000)
                rdData["ratio2"].append(20000)
                rdData["wlmAngle"].append(2)
                rdData["laserTemperature"].append(22)
                rowsInSpectrum += 1
            if s.subschemeId[i] & INCR_FLAG_MASK:
                controlData["RDDataSize"].append(rowsInSpectrum)
                controlData["SpectrumQueueSize"].append(0)
                sensorData["timestamp"].append(self.startTime)
                sensorData["SpectrumID"].append(s.subschemeId[i] & SPECTRUM_ID_MASK)
                sensorData["CavityPressure"].append(self.currentEnv.get("pressure",140.0))
                sensorData["CavityTemp"].append(self.currentEnv.get("temperature",45.0))
                sensorData["ValveMask"].append(1)
                sensorData["DasTemp"].append(40.0)
                sensorData["EtalonTemp"].append(45.0)
                sensorData["WarmBoxTemp"].append(45.0)
                sensorData["InletValve"].append(32768)
                sensorData["OutletValve"].append(32768)
                sensorData["MPVPosition"].append(0)
                rowsInSpectrum = 0
        return rdfDict

    def makeRDF(self,rdfDict, destination):
        SpectrumMaker.rdfIndex += 1
        filename = "RD_%013d.h5" % SpectrumMaker.rdfIndex
        if len(destination) > 0:
            filename = os.path.join(destination, filename)
        h5 = openFile(filename,"w")
        for dataKey in rdfDict.keys():
            subDataDict = rdfDict[dataKey]
            if len(subDataDict) > 0:
                keys,values = zip(*sorted(subDataDict.items()))
                if isinstance(values[0], ndarray):
                    # Array
                    dataRec = rec.fromarrays(values, names=keys)
                elif isinstance(values[0], list) or isinstance(values[0], tuple):
                    # Convert list or tuple to array
                    dataRec = rec.fromarrays([asarray(v) for v in values], names=keys)
                else:
                    raise ValueError("Non-lists or non-arrays are unsupported")
                # Either append dataRec to an existing table, or create a new one
                h5.createTable("/", dataKey, dataRec, dataKey, filters=Filters(complevel=1,fletcher32=True))
        h5.close()

    def run(self, destination = ""):
        for spectra in self.genSpectra():
            #figure()
            for s in self.schemes:
                rdfDict = self.collectSpectrum(spectra,s)
                self.makeRDF(rdfDict, destination)
                #plot(rdfDict["rdData"]["waveNumber"],rdfDict["rdData"]["uncorrectedAbsorbance"],'.')

        #nu = linspace(6237.0,6238.0,1000)
        #nu = linspace(6056.0,6058.0,1000)
        #tot = 0
        #spectrumId = 10
        #for spectra in self.genSpectra():
        #    tot = 0
        #    for s in [spectra[name] for name in self.spectrumNamesById[spectrumId]]:
        #        tot += s.model(nu)
        #    plot(nu,tot)
        #    gca().xaxis.set_major_formatter(ScalarFormatter(useOffset=False))
        #    gca().yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
        #    xlabel('Wavenumber (cm$^{-1}$)')
        #    ylabel('Loss (ppb/cm)')
        #    grid(True)
        #show()

HELP_STRING = """SpectrumMaker.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./SpectrumMaker.ini"
-d                   specify the destination folder for output
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:d:'
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
    if "-d" in options:
        destination = options["-d"]
    return configFile, destination, options

if __name__ == "__main__":
    configFile, destination, options = handleCommandSwitches()
    spectrumMakerApp = SpectrumMaker(configFile,{})
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    spectrumMakerApp.run(destination)
    Log("Exiting program")