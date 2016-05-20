#  Fitter for super-flux water line at 6053 wavenumbers.

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library 60C_CFADS-xx_v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CFBDS-xx H2O FC FY v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CFBDS-xx H2O v1_1.ini")))

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3.5)
#d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=3.5)
d.sparse(maxPoints=100,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
pztMean = mean(d.pztValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

init["base",0] = 800
#print d["filterHistory"]
tstart = time.clock()
if d["spectrumId"]==28 and d["ngroups"] > 1:
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    h2o_res = r["std_dev_res"]
    h2o_adjust = r["base",3]
    h2o_peak = r[12,"peak"]
    h2o_strength = r[12,"strength"]
    h2o_y = r[12,"y"]
    h2o_base = r[12,"base"]
    peak_10 = r[10,"peak"]
    if r[12,"peak"] > 5 and d["ngroups"] > 6:
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
        h2o_shift = r["base",3]
        if abs(r["base",3]) < 0.04 and abs(r[12,"y"]-1.3) < 0.25:
            h2o_res = r["std_dev_res"]
            h2o_adjust = r["base",3]
            h2o_peak = r[12,"peak"]
            h2o_strength = r[12,"strength"]
            h2o_y = r[12,"y"]
            h2o_base = r[12,"base"]
            peak_10 = r[10,"peak"]

    h2o_conc = h2o_peak * 0.001164

    RESULT = {"h2o_res":h2o_res, "h2o_peak":h2o_peak, "h2o_strength":h2o_strength,
              "h2o_conc_precal":h2o_conc, "h2o_y":h2o_y,"h2o_adjust":h2o_adjust,
              "h2o_shift":h2o_shift, "h2o_tuner_mean":tunerMean,"h2o_pzt_mean":pztMean,
              "ringdowns":d["datapoints"],"datagroups":d["ngroups"],
              "peak_10":peak_10}
    RESULT.update({"species":3,"h2o_fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)

    #print "H2O Fit time: %.3f" % (RESULT["h2o_fittime"],)
else:
    RESULT = {}
