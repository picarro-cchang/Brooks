#  G2000 fit script for carbon dioxide, modified for CFADS pressure calibration
#  Version 1 started 2 Sep 2010 by hoffnagle

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./isoCO2/CBDS-5 spectral library v20080627.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"test_instr_params.ini")
    #instrParams = getInstrParams(fname)
    #locals().update(instrParams)

    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/CFEDS_PressureCal_v1_1.ini")))
    lastShift = None
    co2_adjust = 0

init = InitialValues()
if lastShift is not None:
    init["base",3] = lastShift
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=2.5)
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
if d["spectrumId"] in [0,10,12]:
    init["base",0] = 500
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    co2_shift = r["base",3]
    peak_87 = r[87,"peak"]
    base_87 = r[87,"base"]
    str_87 = r[87,"strength"]
    y_87 = r[87,"y"]
    base = r["base",0]
    slope = r["base",1]
    co2_res = r["std_dev_res"]
    if peak_87 > 10 and abs(co2_shift) < 0.02:
        co2_adjust = co2_shift

    lastShift = co2_adjust
    RESULT = {"co2_res":co2_res,"co2_str":str_87,
        "y_parameter":abs(y_87),"co2_baseline":base,"co2_baseline_slope":slope,
        "co2_base":base_87,"co2_shift":co2_shift,"freq_offset":co2_adjust,"co2_peak":peak_87,
        "co2_tuner_mean":tunerMean,"co2_tuner_std": std(d.tunerValue),
        "co2_pzt_mean":pztMean,"co2_pzt_std":std(d.pztValue)}

    RESULT.update({"species":1,"co2_fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
