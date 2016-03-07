#  G2000 fit script for pressure calibration in HCl region
#  Version 1 started 20 July 2015 by hoffnagle

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./HCl/spectral library HCl v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"test_instr_params.ini")
    #instrParams = getInstrParams(fname)
    #locals().update(instrParams)
    
    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HCl/HCl_PressureCal_v1.ini")))
    lastShift = None

init = InitialValues()
if lastShift is not None:
    init["base",3] = lastShift
    
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.30,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]

tstart = time.clock()
if d["spectrumId"] == 0:
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    cm_shift = r["base",3]
    peak_60 = r[60,"peak"]
    base_60 = r[60,"base"]
    y_60 = r[60,"y"]
    peak_61 = r[61,"peak"]
    base = r["base",0]
    slope = r["base",1]
    residuals = r["std_dev_res"]
    if peak_60 > 10 and abs(cm_shift) < 0.02:
        cm_adjust = cm_shift
    else:
        cm_adjust = 0
    lastShift = cm_adjust
    
    RESULT = {"residuals":residuals,"y_parameter":abs(y_60),"h2o_peak":peak_60,
        "baseline":base,"baseline_slope":slope,"perturber_peak":peak_61,
        "cm_shift":cm_shift,"freq_offset":cm_adjust}
         
    RESULT.update({"species":0,"fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T})
    RESULT.update(d.sensorDict)
