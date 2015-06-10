#  G2000 fit script for carbon dioxide, modified for DFADS pressure calibration
#  Version 1 started 2 Sep 2010 by hoffnagle

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./DFADS/spectral library v1_043_ABFJADS-1_A.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"test_instr_params.ini")
    #instrParams = getInstrParams(fname)
    #locals().update(instrParams)

    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./DFADS/CO2 pressure fit #74 v0_0.ini")))
    lastShift = None

init = InitialValues()
if lastShift is not None:
    init["base",3] = lastShift
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
pztMean = mean(d.pztValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]
spectrumId = d.sensorDict["SpectrumID"]
etalonTemp = d.sensorDict["EtalonTemp"]
#heaterCurrent = d.sensorDict["Heater_I_mA"]
inletValvePos = d.sensorDict["InletValve"]
outletValvePos = d.sensorDict["OutletValve"]

tstart = time.clock()
if d["spectrumId"] in [0]:
    peakNum = 74
    init["base",0] = 700
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    shift = r["base",3]
    peak = r[peakNum,"peak"]
    base = r[peakNum,"base"]
    str = r[peakNum,"strength"]
    y = r[peakNum,"y"]
    base = r["base",0]
    slope = r["base",1]
    res = r["std_dev_res"]
    if peak > 10 and abs(shift) < 0.02:
        adjust = shift

    lastShift = adjust
    RESULT = {"res":res,"str":str,
        "y_parameter":abs(y),"baseline":base,"baseline_slope":slope,
        "base":base,"shift":shift,"freq_offset":adjust,"peak":peak,
        "tuner_mean":tunerMean,"tuner_std": std(d.tunerValue),
        "pzt_mean":pztMean,"pzt_std":std(d.pztValue)}

    RESULT.update({"species":1,"fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
