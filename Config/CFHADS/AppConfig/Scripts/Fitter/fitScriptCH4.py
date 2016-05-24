#  Fit script for CFADS Super-flux, 60 C cavity temperature
#  New spectral library and fit ini files:  removed a bogus baseline
#  2011 0324:  Version 2 uses new, tricky high-speed schemes with RD recycle
#  2011 0627:  Remove RD recycle to see if noise spectrum becomes flat

from numpy import mean, std, sqrt, unique
from copy import deepcopy
import os.path
import time

def expAverage(xavg,x,n,dxMax):
    if xavg is None: return x
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)<dxMax: return y
    elif y>xavg: return xavg+dxMax
    else: return xavg-dxMax
def initExpAverage(xavg,x,hi,dxMax,count):
    if xavg is None: return x
    n = min(max(count,1),hi)
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)<dxMax: return y
    elif y>xavg: return xavg+dxMax
    else: return xavg-dxMax
def fitQuality(sdFit,maxPeak,normPeak,sdTau):
    return sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library 60C_CFADS-xx_v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-xx CH4 v2_0.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-xx CH4 FC FY v2_0.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-xx CH4 3_PNT v1_0.ini")))

    ch4_shift = 0
    ch4_conc_raw = 0
    ch4_conc_peak = 0
    ch4_conc_precal = 0
    ch4_adjust = 0
    ch4_amp = 0
    ch4_10pt_amp = 0
    ch4_y = 0
    y_avg = 1.025
    base_avg = 800
    avg_count = 1
    ignore_count = 1
    ch4_res = 0

    dList = []
    fitFlag = 0

ANALYSIS = []
d = DATA
if d["spectrumId"]==25:
    init = InitialValues()
    deps = Dependencies()
    d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
    d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3.5)
    d.sparse(maxPoints=1000,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
    d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
    d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
    P = d["cavitypressure"]
    T = d["cavitytemperature"]
    tunerMean = mean(d.tunerValue)
    pztMean = mean(d.pztValue)
    solValves = d.sensorDict["ValveMask"]
    dasTemp = d.sensorDict["DasTemp"]

    tstart = time.clock()
    r = None

    if d["ngroups"] >= 8:
        r = anCH4[0](d,init,deps)
        if len(unique(r.xData)) >= 8:
            ANALYSIS.append(r)
            base  = r["base",0]
            ch4_y = r[1002,5]
            ch4_shift = r["base",3]
            ch4_10pt_amp = r[1002,2]
            ch4_res = r["std_dev_res"]
            if r[1002,2] > 0.005:
                base_avg  = initExpAverage(base_avg,base,500,100,avg_count)
                y_avg     = initExpAverage(y_avg,ch4_y,500,0.02,avg_count)
                avg_count += 1
            if ch4_conc_raw > 0.1 and ch4_shift < 0.03:
                ch4_adjust = ch4_shift
            else:
                ch4_adjust = 0
        else:
            r = None
    if d["ngroups"] >= 3:
        init["base",0] = base_avg
        init[1002,5]   = y_avg
        r = anCH4[2](d,init,deps)
        if len(unique(r.xData)) >= 3:
            ANALYSIS.append(r)
            ch4_amp = r[1002,2]
            ch4_conc_raw = 9.8932*r[1002,2]
            ch4_conc_peak = 4.7176e-3*r[1002,"peak"]
            ch4_conc_precal = ch4_conc_peak
            ch4_res = r["std_dev_res"]
        else:
            r = None

    now = time.clock()
    fit_time = now-tstart


    ignore_count = max(0,ignore_count-1)
    if ignore_count == 0 and r:
        RESULT = {"ch4_res":ch4_res,"ch4_conc_raw":ch4_conc_raw,"ch4_y":ch4_y,
                  "ch4_conc_peak":ch4_conc_peak,"ch4_adjust":ch4_adjust,
                  "ch4_10pt_amp":ch4_10pt_amp,"ch4_amp":ch4_amp,
                  "ch4_baseline_avg":base_avg,
                  "ch4_tuner_mean": tunerMean, "ch4_tuner_std": std(d.tunerValue),
                  "ch4_pzt_mean": pztMean, "ch4_pzt_std": std(d.pztValue),
                  "ch4_conc_precal":ch4_conc_precal,"ch4_shift":ch4_shift,
                  "ringdowns":d["datapoints"],"datagroups":d["ngroups"],
                  "ch4_fit_time":fit_time}
        RESULT.update(d.sensorDict)
        RESULT.update({"species":d["spectrumId"],"cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                  "das_temp":dasTemp})
    else:
        RESULT = {}
else:
    RESULT = {}
