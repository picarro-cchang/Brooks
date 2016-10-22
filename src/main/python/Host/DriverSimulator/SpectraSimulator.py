#!/usr/bin/python
#
"""
File Name: SpectraSimulator.py
Purpose: Simulate the absorption spectrum from a description in an INI file.

File History:
    21-Oct-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""
import math
import operator
import os

import numpy as np

from Host.autogen import interface
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Fitter.fitterCoreWithFortran import (BiSpline, FrequencySquish,
                                               Galatry, Model, Quadratic,
                                               Sinusoid, Spline,
                                               loadPhysicalConstants,
                                               loadSpectralLibrary,
                                               loadSplineLibrary)


class Spectrum(object):
    def __init__(self,name,config,basePath,env):
        self.name = name
        libName = os.path.join(basePath,eval(config["Library"],env))
        self.spectralLibrary = loadSpectralLibrary(libName)
        self.splineLibrary = loadSplineLibrary(libName)
        self.physicalConstants = loadPhysicalConstants(libName)
        self.config = config
        self.spectrumIds = np.asarray(eval(config["SpectrumId"]+",",env))

    def setupModel(self, env):
        config = self.config
        self.basisArray = np.asarray(eval(config["identification"]+",",env))
        self.centerFrequency = eval(config["center"],env) if "center" in config else 0
        self.basisFunctions = {}
        m = Model()
        m.setAttributes(x_center=self.centerFrequency)
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
                    return basisFunc(params=np.asarray(a),**extra)

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


class SpectraSimulator(object):
    def __init__(self, filename):
        self.basePath = os.path.split(os.path.normpath(os.path.abspath(filename)))[0]
        self.config = CustomConfigObj(filename)
        self.env = {}
        if "CODE" in self.config:
            code = compile(self.config["CODE"]["code"], "CODE", "exec")
            exec code in self.env
        if "VARIABLES" in self.config:
            constants, sequences = self.findVariables(self.config["VARIABLES"])
        self.env.update(dict(constants))
        self.spectra = []
        for secName in self.config:
            if secName.startswith("SPECTRUM"):
                sp = Spectrum(secName, self.config[secName], self.basePath, self.env)
                self.spectra.append(sp)
        for spectrum in self.spectra:
            spectrum.setupModel(self.env)
        self.centerWavenumbers = np.asarray([spectrum.centerFrequency for spectrum in self.spectra])

    def findVariables(self, variables):
        # Find entries in the variables dictionary which have values that evaluate to sequences
        #  and those which evaluate to constants. The result is the pair constants, sequences
        #  where constants is a list with (name,value) pairs and sequences is a list of
        #  (name,sequence) pairs, where name is the name of the variable and sequence is a
        #  tuple of values that the variable must assume
        constants, sequences = [], []
        for k in variables:
            v = variables[k]
            e = eval(v, self.env)
            if operator.isSequenceType(e):
                sequences.append((k,e))
            else:
                constants.append((k,e))
        return constants, sequences

    def __call__(self, wavenumber, pressure, temperature):
        """Find the spectrum whose center wavenumber is closest to the value given
            and evaluate it for the specified pressure and temperature"""
        spectrum = self.spectra[np.argmin(abs(np.mean(wavenumber) - self.centerWavenumbers))]
        if pressure != self.env["pressure"] or temperature != self.env["temperature"]:
            self.env["pressure"] = pressure
            self.env["temperature"] = temperature
            spectrum.updateModel(self.env)
        if np.isscalar(wavenumber):
            return spectrum.model(np.asarray([wavenumber]))[0]
        else:
            return spectrum.model(np.asarray(wavenumber))
