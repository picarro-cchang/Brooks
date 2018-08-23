#  Fit script for CFADS water fitter in the presence of high methane levels
#  Adapted from the CFFDS (iCO2 with high methane) by Hoffnagle on 14 July 2011

from numpy import any, mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library_CBDS+CFADS6057_20110308.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 v1_2 2011 0328.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 FC v1_1 2011 0309.ini")))

    pzt_mean = 0.0
    pzt_stdev = 0.0
    shift_75 = 0

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=100,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=1.8)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.clock()
if d["spectrumId"]==11 and d["ngroups"]>6:
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    if abs(r["base",3]) >= 0.01 or abs(r[75,"y"]-0.83)>0.3:
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
    h2o_res = r["std_dev_res"]
    h2o_peak = r[75,"peak"]
    h2o_quality = fitQuality(h2o_res,h2o_peak,50,1)
    h2o_shift = r["base",3]
    ch4_from_h2o = 100.0*r[1002,2]

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = mean(d.pztValue[cal])
        pzt_stdev = std(d.pztValue[cal])

    h2o_str = r[75,"strength"]
    h2o_y = r[75,"y"]
    h2o_z = r[75,"z"]
    h2o_base = r[75,"base"]
    h2o_conc = h2o_peak * 0.01002
    if h2o_peak > 3.0 and abs(shift_75) < 0.03 and h2o_quality < 1.5:
        h2o_adjust = h2o_shift
    else:
        h2o_adjust = 0.0
    RESULT = {"h2o_res":h2o_res, "h2o_peak":h2o_peak, "h2o_str":h2o_str,"ch4_from_h2o":ch4_from_h2o,
              "h2o_conc_precal":h2o_conc, "h2o_y":h2o_y, "h2o_z":h2o_z,"h2o_adjust":h2o_adjust,
              "h2o_shift":h2o_shift, "h2o_tuner_mean":tunerMean,"h2o_pzt_mean":pzt_mean,
              "h2o_tuner_std":std(d.tunerValue),"h2o_pzt_std":pzt_stdev, "h2o_ngroups":d["ngroups"]}
    RESULT.update({"species":3,"h2o_fittime":time.clock()-tstart, "h2o_quality":h2o_quality,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
