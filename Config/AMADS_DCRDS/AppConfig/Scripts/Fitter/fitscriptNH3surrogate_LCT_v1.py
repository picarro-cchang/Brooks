#  Fit script for N2O "surrogate" line to validate ammonia analyzer
#  2016-11-08:  started based on AMADS ammonia fitter

from numpy import any, mean, std, sqrt, round_
import os.path
import time


def initialize_Baseline():
    init["base",1] = baseline_slope
    init[1000,0] = A0
    init[1000,1] = Nu0
    init[1000,2] = Per0
    init[1000,3] = Phi0
    init[1001,0] = A1
    init[1001,1] = Nu1
    init[1001,2] = Per1
    init[1001,3] = Phi1

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./NH3/spectral library NH3 v2_0.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_lct.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']

    anN2O = []
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./NH3/N2O surrogate VC v1_1.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./NH3/N2O surrogate FC v1_1.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./NH3/N2O surrogate VC v1_1.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./NH3/N2O surrogate FC v1_1.ini")))

    #  Import instrument specific baseline constants

    baseline_slope = instrParams['NH3_Baseline_slope']
    A0 = instrParams['NH3_Sine0_ampl']
    Nu0 = instrParams['NH3_Sine0_freq']
    Per0 = instrParams['NH3_Sine0_period']
    Phi0 = instrParams['NH3_Sine0_phase']
    A1 = instrParams['NH3_Sine1_ampl']
    Nu1 = instrParams['NH3_Sine1_freq']
    Per1 = instrParams['NH3_Sine1_period']
    Phi1 = instrParams['NH3_Sine1_phase']

    #  Globals
    
    last_time = None

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
#d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.clock()
RESULT = {}
r = None
if d["spectrumId"]==5 and d["ngroups"]>10:
#   Fit N2O lines
    initialize_Baseline()
    r = anN2O[0](d,init,deps)
    ANALYSIS.append(r)
    shift = r["base",3]
    if r[84,"peak"] > 10.0 and abs(shift) < 0.05 :
        cm_adjust = shift
    else:
        r = anN2O[1](d,init,deps)
        ANALYSIS.append(r)
        cm_adjust = 0.0
        
    goodLCT = abs(cm_adjust)<0.01
    if goodLCT:
        d.waveNumber = 6548.85160 + fsr*round_((d.waveNumber - 6548.85160)/fsr)
        d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
        d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
        d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes)) 
        if r[84,"peak"]<10:
            r = anN2O[3](d,init,deps)
            ANALYSIS.append(r)
        else: 
            r = anN2O[2](d,init,deps)
            ANALYSIS.append(r)
    
    peak12 = r[12,"peak"]    
    peak84 = r[84,"peak"]
    str84 = r[84,"strength"]
    shift_a = r["base",3]
    residual = r["std_dev_res"]
    nh3_conc = 8.75*peak12
    n2o_conc = 6.83*peak84
    
    if goodLCT and peak84 > 10:
        pzt2_adjust = -shift_a*pzt_per_fsr/fsr
    else:
        pzt2_adjust = 0.0

    if r != None:
        if last_time != None:
            interval = r["time"]-last_time
        else:
            interval = 0
        last_time = r["time"]     
        
    RESULT = {"residual":residual,"peak12":peak12,"peak84":peak84,"str84":str84,
              "nh3_conc":nh3_conc,"n2o_conc":n2o_conc,"shift":shift,"cm_adjust":cm_adjust,
              "pzt2_adjust":pzt2_adjust,"pzt_per_fsr":pzt_per_fsr,"interval":interval,
              "ngroups":d["ngroups"],"numRDs":d["datapoints"]}
    RESULT.update({"species":d["spectrumId"],"fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
