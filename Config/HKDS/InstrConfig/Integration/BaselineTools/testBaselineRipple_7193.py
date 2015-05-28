import numpy
import os.path
import time
import cPickle
from struct import pack
from Host.Common.EventManagerProxy import Log
import math

def initialize_Baseline():
    init["base",0] = baseline_level
    init["base",1] = baseline_slope
    init[1000,0] = A0
    init[1000,1] = Nu0
    init[1000,2] = Per0
    init[1000,3] = Phi0
    init[1001,0] = A1
    init[1001,1] = Nu1
    init[1001,2] = Per1
    init[1001,3] = Phi1


if INIT:
    fname = os.path.join(BASEPATH,r"./HIDS spectral library v4_2.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"./FitterConfig_iH2O7193.ini")
    instrParams = getInstrParams(fname)

    analysis = []
    analysis.append(Analysis(os.path.join(BASEPATH,r"./Baseline ripple 7193 test.ini")))

    baseline_level = instrParams['7193_Baseline_level']
    baseline_slope = instrParams['7193_Baseline_slope']
    A0 = instrParams['7193_Sine0_ampl']
    Nu0 = instrParams['7193_Sine0_freq']
    Per0 = instrParams['7193_Sine0_period']
    Phi0 = instrParams['7193_Sine0_phase']
    A1 = instrParams['7193_Sine1_ampl']
    Nu1 = instrParams['7193_Sine1_freq']
    Per1 = instrParams['7193_Sine1_period']
    Phi1 = instrParams['7193_Sine1_phase']

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.5,maxVal=10)
d.sparse(maxPoints=50000,width=0.0005,height=1000000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/numpy.sqrt(d.groupSizes))

initialize_Baseline()
r = analysis[0](d,init,deps)
ANALYSIS.append(r)

base_shift = r["base",0] - baseline_level
slope_shift = r["base",1] - baseline_slope
cm_shift = r["base",3]
peak_15 = r[15,"peak"]
y_15 = r[15,"y"]
h2o_conc = 14.47*r[15,"strength"]

RESULT = {'base_shift':base_shift, 'slope_shift':slope_shift,
          'peak_15':peak_15,'y_15':y_15,"h2o_conc":h2o_conc,
          'cm_shift':cm_shift,'stddevres':r["std_dev_res"]}
