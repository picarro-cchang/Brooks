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
from Host.Fitter.fitterCoreWithFortran import *

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
    def setupModel(self,env):
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
    initialized = False
    def __init__(self, configPath=None,env={}):
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
        """Generator yielding model spectra"""
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

    def run(self):
        nu = linspace(6237.0,6238.0,1000)
        #nu = linspace(6056.0,6058.0,1000)
        tot = 0
        spectrumId = 10
        for spectra in self.genSpectra():
            tot = 0
            for s in [spectra[name] for name in self.spectrumNamesById[spectrumId]]:
                tot += s.model(nu)
            plot(nu,tot)
        gca().xaxis.set_major_formatter(ScalarFormatter(useOffset=False))
        gca().yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
        xlabel('Wavenumber (cm$^{-1}$)')
        ylabel('Loss (ppb/cm)')
        grid(True)
        show()

HELP_STRING = """SpectrumMaker.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./SpectrumMaker.ini"
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
    spectrumMakerApp = SpectrumMaker(configFile,{})
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    spectrumMakerApp.run()
    Log("Exiting program")