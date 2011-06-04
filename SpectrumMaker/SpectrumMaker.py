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
    def __init__(self,name,config,basePath):
        self.name = name
        libName = os.path.join(basePath,config["Library"])
        self.spectralLibrary = loadSpectralLibrary(libName)
        self.splineLibrary = loadSplineLibrary(libName)
        self.physicalConstants = loadPhysicalConstants(libName)
        self.basisArray = asarray([int(i) for i in config["identification"].split(",")])
        self.basisFunctions = {}
        m = Model()
        # m.setAttributes(x_center=self.centerFrequency)
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
                    for j in range(nParams): a.append(float(basisParams["a%d" % j]))
                    return basisFunc(params=asarray(a),**extra)

                form = basisParams["functional_form"]
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
        self.model = m
        
class SpectrumMaker(Singleton):
    initialized = False
    def __init__(self, configPath=None):        
        if not self.initialized:
            if configPath != None:
                # Process INI file
                cp = CustomConfigObj(configPath)
                basePath = os.path.split(configPath)[0]
                self.schemeCount = cp.getint("SCHEME_CONFIG", "schemeCount", "1")
                self.schemePaths = []
                self.schemes = []
                for i in range(self.schemeCount):
                    path = cp.get("SCHEME_CONFIG", "Scheme_%d_Path" % (i+1,))
                    self.schemePaths.append(path)
                    s = Scheme(path)
                    self.schemes.append(s)
                self.spectra = []
                self.libraries = {}
                for secName in cp:
                    if secName.startswith("SPECTRUM"):
                        self.spectra.append(Spectrum(secName,cp[secName],basePath))
            else:
                raise ValueError("Configuration file must be specified to initialize SpectrumMaker")
            self.initialized = True
    def run(self):
        nu = linspace(6235.0,6240.0,1000)
        tot = 0
        for s in self.spectra:
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
    spectrumMakerApp = SpectrumMaker(configFile)
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    spectrumMakerApp.run()
    Log("Exiting program")
    