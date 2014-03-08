#  Experimental fit script for O2 concentration using corrected strength measurement of 7823 line
#  2012 1128:  Start work
#  2013 0104:  Added empirical y- and z-dependencies; dry mole fraction
#  2013 0110:  Adjusted y and z for 140 Torr operation
#  2013 0111:  Tweaked [O2] scale factor to get better agreement with standard atmosphere 

import os.path
import time
from numpy import *
from copy import copy
    
def initialize_Baseline():
    init["base",0] = Base
    init[1000,0] = A0
    init[1000,1] = Nu0
    init[1000,2] = Per0
    init[1000,3] = Phi0
    init[1001,0] = A1
    init[1001,1] = Nu1
    init[1001,2] = Per1
    init[1001,3] = Phi1

def outlierFilter(x,threshold,minPoints=2):
    """ Return Boolean array giving points in the vector x which lie
    within +/- threshold * std_deviation of the mean. The filter is applied iteratively
    until there is no change or unless there are minPoints or fewer remaining"""
    good = ones(x.shape,bool_)
    order = list(x.argsort())
    while len(order)>minPoints:
        maxIndex = order.pop()
        good[maxIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[maxIndex]-mu)>=(threshold*sigma):
            continue
        good[maxIndex] = 1
        minIndex = order.pop(0)
        good[minIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[minIndex]-mu)>=(threshold*sigma):
            continue
        good[minIndex] = 1
        break
    return good
    
if INIT:
    fname = os.path.join(BASEPATH,r"./MADS/spectral library v2_1_AADS4_MA_20110601.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']
    
    anO2 = []
    anO2.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet VC VY with offsets.ini")))
    
#   Globals
    last_time = None
      
    #  Baseline parameters
    Base = instrParams['Baseline_level']
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
d = copy(DATA)
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.sparseByVlaser(maxPoints=1000,width=0.01,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance","laserUsed"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)),
                vlaser=(d.groupMeans["laserUsed"].astype(int)&0x1C)//4)
T = d["cavitytemperature"] + 273.15
pzt = mean(d.pztValue)

species = (d.subschemeId & 0x3FF)[0]

tstart = time.time()
RESULT = {}
r = None
#deps.setDep(("base",17),("base",16),0.35,0.0)
deps.setDep((81,"z"),(81,"y"),0.35,0.0)
#deps.setDep((82,"strength"),(81,"strength"),0.1,0.0)

if species == 61:
    initialize_Baseline()      #  Standard fit taken from 70 Torr MADS
    r = anO2[0](d,init,deps)
    ANALYSIS.append(r)
    o2_shift = r["base",3]
    o2_y = r[81,"y"]
    peak81 = r[81,"peak"]
    str81 = r[81,"strength"]
    y_nominal = 0.3374 + 1.74e-6*str81
    z_nominal = 0.136 - 1.79e-5*str81
    corrected_strength = str81*y_nominal/o2_y
    base = r[81,"base"]
    h2o_y = r[82,"y"]
    peak82 = r[82,"peak"]
    str82 = r[82,"strength"]
    o2_residuals = r["std_dev_res"]
    o2_conc = 742.2*peak81
    h2o_conc = 403.5*peak82
   
    RESULT = {"o2_shift":o2_shift,"peak81":peak81,"o2_y":o2_y,"o2_residuals":o2_residuals,
            "str81":str81,"h2o_y":h2o_y,"peak82":peak82,"str82":str82,"o2_conc":o2_conc,"h2o_conc":h2o_conc,
            "base":base,"corrected_strength":corrected_strength,"y_nominal":y_nominal,"z_nominal":z_nominal,
            "species":species,"dataGroups":d["ngroups"],"dataPoints":d["datapoints"]
            }
