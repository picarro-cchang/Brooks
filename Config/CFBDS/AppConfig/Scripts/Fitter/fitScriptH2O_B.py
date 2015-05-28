#  2010-04-19  Added condition to report h20_shift = 0 if peak height is < 10 ppb/cm

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library v1_043_CFADS-1_0220.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O v1_1 0619.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O FC v1_1 0619.ini")))

    h2o_strength = 0
    h2o_y = 0
    h2o_base = 0
    h2o_conc = 0
    h2o_shift = 0
    h2o_quality = 0
    Ilaserfine = 0

ANALYSIS = []
d = DATA
if d["spectrumId"]==11:
    init = InitialValues()
    deps = Dependencies()
    d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
    d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3.5)
    d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=3.5)
    d.sparse(maxPoints=100,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.5)
    d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
    d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
    P = d["cavitypressure"]
    T = d["cavitytemperature"]
    tunerMean = mean(d.tunerValue)
    pztMean = mean(d.pztValue)
    solValves = d.sensorDict["ValveMask"]
    dasTemp = d.sensorDict["DasTemp"]

    #species = (d.subschemeId & 0x3FF)[0]
    init["base",0] = 800
    print d["filterHistory"]
    tstart = time.clock()

    h2o_shift = 0.0
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    if r[75,"peak"] < 10 or abs(r["base",3]) >= 0.01:
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
    h2o_res = r["std_dev_res"]
    h2o_peak = r[75,"peak"]
    h2o_quality = fitQuality(h2o_res,h2o_peak,50,1)
    if h2o_quality < 1.5:
        h2o_strength = r[75,"strength"]
        h2o_y = r[75,"y"]
        h2o_base = r[75,"base"]
        h2o_conc = h2o_peak * 0.01002
        if r[75,"peak"] > 10:
            h2o_shift = r["base",3]
    RESULT = {"h2o_res":h2o_res, "h2o_peak":h2o_peak, "h2o_strength":h2o_strength,
              "h2ob_conc_precal":h2o_conc, "h2o_y":h2o_y, "h2o_quality":h2o_quality,
              "h2o_shift":h2o_shift, "h2o_tuner_mean":tunerMean,"h2o_pzt_mean":pztMean,
              "h2o_tuner_std":std(d.tunerValue),"h2o_pzt_mean":std(d.pztValue),"h2o_id":1}
    RESULT.update({"species":3,"h2o_fittime":time.clock()-tstart,"h2o_Ilaserfine":Ilaserfine,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)

    print "H2O Fit time: %.3f" % (RESULT["h2o_fittime"],)
else:
    RESULT = {}
