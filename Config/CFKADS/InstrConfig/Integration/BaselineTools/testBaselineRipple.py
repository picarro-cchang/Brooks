#  Baseline ripple tester for CKADS CO region at 6380 wvn

from numpy import *
import os.path
import time
import cPickle
from struct import pack
from Host.Common.EventManagerProxy import Log

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
    fname = os.path.join(BASEPATH,r"./spectral library CFKADS Galatry v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"./FitterConfig.ini")
    instrParams = getInstrParams(fname)

    analysis = []
    analysis.append(Analysis(os.path.join(BASEPATH,r"./CKADS-xx baseline test.ini")))

    baseline_level = instrParams['Baseline_level']
    baseline_slope = instrParams['Baseline_slope']
    A0 = instrParams['Sine0_ampl']
    Nu0 = instrParams['Sine0_freq']
    Per0 = instrParams['Sine0_period']
    Phi0 = instrParams['Sine0_phase']
    A1 = instrParams['Sine1_ampl']
    Nu1 = instrParams['Sine1_freq']
    Per1 = instrParams['Sine1_period']
    Phi1 = instrParams['Sine1_phase']

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.15,maxVal=1.5)
d.sparse(maxPoints=20000,width=0.0025,height=400000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.8)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))


initialize_Baseline()
init[32,"strength"] = 0.0
init[84,"strength"] = 0.0
r = analysis[0](d,init,deps)
ANALYSIS.append(r)

base0 = r["base",0]
base1 = r["base",1]
cm_shift = r["base",3]
peak84 = r[84,"peak"]

RESULT = {'base0':base0, 'base1':base1,'peak84':peak84,
          'cm_shift':cm_shift,'stddevres':r["std_dev_res"]}
