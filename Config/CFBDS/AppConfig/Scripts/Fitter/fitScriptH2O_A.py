#  Adapted from fitScriptH2O.py to use SpectrumID 13 and Chris's LabView flow

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFBDS/spectral library v1_043_CFADS-xx_2009_0813.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFBDS/SID13 H2O VC v1_1 2009 0813.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFBDS/SID13 H2O FC v1_0 2009 0813.ini")))

    h2o_strength = 0
    h2o_y = 0
    h2o_base = 0
    h2o_conc = 0
    h2o_shift = 0
    h2o_quality = 0
    co2_peak = 0
    Ilaserfine = 0

ANALYSIS = []
d = DATA
if d["spectrumId"]==26:
    init = InitialValues()
    deps = Dependencies()
    d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
    d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
    d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=2.5)
    d.sparse(maxPoints=100,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=1.8)
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
    print "fitScriptH2O spectrum id = ", d["spectrumId"]

    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    if (abs(h2o_shift) > 0.03) or (r[90,"peak"] < 10.00):
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
        h2o_shift = 0.0
    h2o_res = r["std_dev_res"]
    h2o_peak = r[90,"peak"]
    h2o_base = r[90,"base"]
    co2_peak = r[91,"peak"]
    h2o_conc = h2o_peak * 0.04882
    h2o_quality = fitQuality(h2o_res,h2o_peak,50,1)
    RESULT = {"h2o_res":h2o_res, "h2o_peak":h2o_peak, "h2o_strength":h2o_peak,
              "h2oa_conc_precal":h2o_conc, "h2o_y":h2o_y, "h2o_quality":h2o_quality,
              "h2o_shift":h2o_shift, "h2o_tuner_mean":tunerMean,"h2o_pzt_mean":pztMean,
              "h2o_tuner_std":std(d.tunerValue),"h2o_pzt_mean":std(d.pztValue),"h2o_id":0}
    RESULT.update({"species":3, "h2o_fittime":time.clock()-tstart,"h2o_Ilaserfine":Ilaserfine,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)

    #print "H2O Conc = ", h2o_conc
    #print "H2O Fit time: %.3f" % (RESULT["h2o_fittime"],)
else:
    RESULT = {}
