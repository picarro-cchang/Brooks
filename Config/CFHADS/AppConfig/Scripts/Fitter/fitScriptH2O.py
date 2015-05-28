#  Fitter for super-flux water line at 6053 wavenumbers.
#  2011 0324:  Version 2 uses new, tricky high-speed schemes with RD recycle
#  2011 0627:  Remove RD recycle to see if noise spectrum becomes flat

from numpy import mean, std, sqrt, unique
from copy import deepcopy
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
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CFBDS-xx H2O 3_PNT 2L v1_0.ini")))

    h2o_y_avg = 1.3
    avg_count = 1
    h2o_shift = 0
    h2o_peak = 0
    h2o_adjust = 0
    h2o_9ptpeak = 0
    peak10_9pt = 0
    h2o_res = 0

    dList = []
    fitFlag = 0

ANALYSIS = []
d = DATA

if d["spectrumId"]==28:
    init = InitialValues()
    deps = Dependencies()
    d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
    d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3.5)
    d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=3.5)
    d.sparse(maxPoints=100,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
    d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
    d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
    P = d["cavitypressure"]
    T = d["cavitytemperature"]
    tunerMean = mean(d.tunerValue)
    pztMean = mean(d.pztValue)
    solValves = d.sensorDict["ValveMask"]
    dasTemp = d.sensorDict["DasTemp"]

    #print d["filterHistory"]
    tstart = time.clock()
    r = None

    if d["ngroups"]>=7:
        r = anH2O[1](d,init,deps)
        if len(unique(r.xData)) >= 7:
            ANALYSIS.append(r)
            h2o_shift = r["base",3]
            h2o_9ptpeak = r[12,"peak"]
            peak10_9pt = r[10,"peak"]
            h2o_res = r["std_dev_res"]
            if h2o_9ptpeak > 5 and abs(r["base",3]) < 0.04 and abs(r[12,"y"]-1.3) < 0.25:
                h2o_adjust = h2o_shift
                h2o_y = r[12,"y"]
                h2o_y_avg = initExpAverage(h2o_y_avg,h2o_y,30,0.05,avg_count)
                avg_count += 1
            else:
                h2o_adjust = 0
        else:
            r = None

    if d["ngroups"]>=3:
        init[12,"y"] = h2o_y_avg
        r = anH2O[2](d,init,deps)
        if len(unique(r.xData)) >= 3:
            ANALYSIS.append(r)
            h2o_peak = r[12,"peak"]
            h2o_conc = h2o_peak * 0.001164
            h2o_res = r["std_dev_res"]
            peak_10 = r[10,"peak"]
        else:
            r = None

    if r:
        RESULT = {"h2o_res":h2o_res,"h2o_peak":h2o_peak,
                  "h2o_conc_precal":h2o_conc,"h2o_y_avg":h2o_y_avg,"h2o_adjust":h2o_adjust,
                  "h2o_shift":h2o_shift,"h2o_tuner_mean":tunerMean,"h2o_pzt_mean":pztMean,
                  "ringdowns":d["datapoints"],"datagroups":d["ngroups"],
                  "fit_flag":fitFlag,
                  "peak_10":peak_10,"h2o_y_avg":h2o_y_avg,"h2o_9ptpeak":h2o_9ptpeak,
                  "peak10_9pt":peak10_9pt}
        RESULT.update({"species":d["spectrumId"],"h2o_fittime":time.clock()-tstart,
                       "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                       "das_temp":dasTemp})
        RESULT.update(d.sensorDict)

    else:
        RESULT = {}
else:
    RESULT = {}
