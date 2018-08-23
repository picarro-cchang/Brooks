#  G2000 fit script for pressure calibration in H2S region
#  Version 1 started 7 June 2011 by Hoffnagle
#  2011 0801:  Removed perturber from fit

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./BXDS/spectral library H2S pressure cal.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"test_instr_params.ini")
    #instrParams = getInstrParams(fname)
    #locals().update(instrParams)

    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BXDS/H2S_PressureCal_v1.ini")))
    lastShift = None

init = InitialValues()
if lastShift is not None:
    init["base",3] = lastShift

deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.30,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.0005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=3)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]

tstart = time.clock()
if d["spectrumId"] == 0:
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    h2s_shift = r["base",3]
    peak_0 = r[0,"peak"]
    base_0 = r[0,"base"]
    y_0 = r[0,"y"]
    base = r["base",0]
    slope = r["base",1]
    h2s_res = r["std_dev_res"]
    if peak_0 > 10 and abs(h2s_shift) < 0.04:
        h2s_adjust = h2s_shift
    else:
        h2s_adjust = 0

    RESULT = {"h2s_res":h2s_res,"y_parameter":abs(y_0),"co2_peak":peak_0,
        "baseline":base,"baseline_slope":slope,
        "h2s_shift":h2s_shift,"freq_offset":h2s_adjust}

    RESULT.update({"species":0,"fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T})
    RESULT.update(d.sensorDict)
