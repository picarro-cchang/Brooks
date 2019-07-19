#  Fit script for HF at 7823 wvn with LCT data acquisition
#  2018 0425:  First draft of a DCRDS fitter for AMADS HF in LCT mode.  Branched from
#              v5 of conventional AMADS HF (LCT) and DCRDS data set definition from SADS v1.4.

from numpy import any, amin, amax, mean, std, sqrt, argmin, round_
import numpy as np
import os.path
import time
from Host.Common.EventManagerProxy import Log

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

def initialize_Baseline():
    init[1000,0] = A0
    init[1000,1] = Nu0
    init[1000,2] = Per0
    init[1000,3] = Phi0
    init[1001,0] = A1
    init[1001,1] = Nu1
    init[1001,2] = Per1
    init[1001,3] = Phi1

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./MADS/spectral library MADSxx_v2_4.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_lct.ini")
    cavityParams = getInstrParams(fname)
    #fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR_VLASER_1']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']

    anHF = []
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - HF doublet FC v1_0 20080512.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - HF doublet VC v1_0 20080512.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - HF doublet FC v1_0 20080512.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet VC v2_1.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet FC v1_1 20160523.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet VC v2_1.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet FC v1_1 20160523.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/Dummy v1_1.ini")))


    #  Baseline parameters
    A0 = instrParams['HF_Sine0_ampl']
    Nu0 = instrParams['HF_Sine0_freq']
    Per0 = instrParams['HF_Sine0_period']
    Phi0 = instrParams['HF_Sine0_phase']
    A1 = instrParams['HF_Sine1_ampl']
    Nu1 = instrParams['HF_Sine1_freq']
    Per1 = instrParams['HF_Sine1_period']
    Phi1 = instrParams['HF_Sine1_phase']

    #  Globals to pass between spectral regions

    goodLCT = 0
    i0 = 5
    f0 = 7823.84945
    sigma0 = 0.0
    adjust_81 = 0.0
    pzt1_adjust = 0.0
    base0 = 0.0
    base1 = 0.0
    adjust_77=0.0
    shift_77 = 0.0
    peak_77 = 0.0
    str_77 = 0.0
    base_77 = 0.0
    y_77 = 0.0
    shift_77 = 0.0
    base77_ave = instrParams['HF_Baseline_level']
    peak77_baseave = 0.0
    peak_79 = 0.0
    str_79 = 0.0
    base_79 = 0.0
    y_79 = 0.0
    shift_81 = 0.0
    peak_81 = 0.0
    str_81 = 0.0
    base_81 = 0.0
    y_81 = 0.0
    peak_82 = 0.0
    str_82 = 0.0
    base_82 = 0.0
    y_82 = 0.0
    h2o_conc_60 = 0.0
    h2o_conc_61 = 0.0
    o2_conc = 0.0
    hf_ppbv = 0.0
    hf_ppbv_ave = 0.0
    hf_res = 0.0
    o2_res = 0.0
    tuner60mean = 32768
    tuner60stdev = 0
    tuner61mean = 32768
    tuner61stdev = 0

    incomplete_hf_spectrum = 0
    """
    Placeholder until conditions are agreed upon
    """
    degraded_hf_performance = 0
    """
    End placeholder
    """
    hf_noBaseline = 0
    hf_baseMean = instrParams['HF_Baseline_level']
    hf_baseStdev = 0.0
    hf_baseLinIntercept = 0.0
    hf_baseLinSlope = 0.0
    hf_baseQuadIntercept = 0.0
    hf_baseQuadSlope = 0.0
    hf_baseQuadCurvature = 0.0
    hf_minBasePoints = 0
    hf_maxBasePoints = 0
    hf_meanBasePoints = 0

    counter = -20
    ignore_count = 8

    last_time = None

    # The degraded_hf_performance flag is set if any of the specified concentrations or base values
    #  exceed their respective thresholds. The flag is held for "degraded_hf_performance_hold"
    #  samples after all concentrations drop below the thresholds.

    if "hf_baseMean_thresh" in instrParams:
        hf_baseMean_thresh = instrParams["hf_baseMean_thresh"]
    else:
        hf_baseMean_thresh = 2.0

    if "degraded_hf_performance_hold" in instrParams:
        degraded_hf_performance_hold = instrParams[
            "degraded_hf_performance_hold"]
    else:
        degraded_hf_performance_hold = 5

    degraded_hf_performance_counter = 0

    Log("Setting degraded_hf_performance_threshold parameters", 
        Data=dict(hf_baseMean_thresh=hf_baseMean_thresh,
                  degraded_hf_performance_hold=degraded_hf_performance_hold))



init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

#  Point-by-point baseline subtraction and spectrum generation starts here

validBase = (d.extra2 ==1) & (d.uncorrectedAbsorbance > 0.1)
t0 = np.mean(d.timestamp)
ts = d.timestamp - t0
loss = d.uncorrectedAbsorbance
hf_baseMean = np.mean(loss[validBase])
hf_baseStdev = np.std(loss[validBase])
p = np.polyfit(ts[validBase],loss[validBase],1)
hf_baseLinIntercept = 1000*p[1]
hf_baseLinSlope = 1e6*p[0]
p = np.polyfit(ts[validBase],loss[validBase],2)
hf_baseQuadIntercept = 1000*p[2]
hf_baseQuadSlope = 1e6*p[1]
hf_baseQuadCurvature = 1e9*p[0]

N = len(d.extra2)
nWindow = 100    #  Window size (HW) for baseline measurement
tWindow = 400    #  Time window for baseline measurement in ms
goodPoints = []
hf_noBaseline = 0
minBase = 1000
maxBase = -1000
basePoints = []
for i, ext2 in enumerate(d.extra2):
    if ext2 == 0:
        win = slice(max(0,i-nWindow), min(N,i+nWindow+1))
        lwin = loss[win]
        twin = ts[win]
        select = (d.extra2[win] == 1) & (abs(ts[win] - ts[i]) < tWindow) & (d.uncorrectedAbsorbance[win] > 0.1)
        if sum(select) > 1:
            basePoints.append(sum(select))
            p = np.polyfit(twin[select], lwin[select], 1)
            loss[i] -= np.polyval(p, ts[i])
            loss[i] += hf_baseMean
            goodPoints.append(i)
            if np.polyval(p, ts[i]) < minBase: minBase = np.polyval(p, ts[i])
            if np.polyval(p, ts[i]) > maxBase: maxBase = np.polyval(p, ts[i])
        else:
            loss[i] = 0.0
            hf_noBaseline += 1
d.indexVector = np.asarray(goodPoints)
if len(basePoints) > 0:
    hf_minBasePoints = amin(basePoints)
    hf_maxBasePoints = amax(basePoints)
    hf_meanBasePoints = mean(basePoints)
else:
    hf_minBasePoints = hf_maxBasePoints = hf_meanBasePoints = 0

d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
#d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=4.5)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
tunerStdev = std(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.clock()
RESULT = {}
r = None
if d["spectrumId"]==60 and d["ngroups"]>6:
    incomplete_hf_spectrum = 0
    #  Fit water-HF doublet at 7823.8
    r = anHF[0](d,init,deps)
    ANALYSIS.append(r)
    if r[77,"peak"]>10:
        # fit with variable center and y if either H2O or HF peak is strong.
        r = anHF[1](d,init,deps)
        ANALYSIS.append(r)
    tuner60mean = tunerMean
    tuner60stdev = tunerStdev
    if goodLCT:
        i0 = argmin(abs(d.fitData["freq"] - 7823.84945))
        f0 = d.fitData["freq"][i0]
        while (f0 - 7823.84945) < -0.5*fsr:
            f0 += fsr
        while (f0 - 7823.84945) > 0.5*fsr:
            f0 -= fsr
        sigma0 = d.groupStdDevs["waveNumber"][i0]
        #print "%2d %8.5f %8.5f" % (i0, f0 - 7823.84945, sigma0)
        d.waveNumber = f0 + fsr*round_((d.waveNumber - f0)/fsr)
        d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
        d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
        d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))

        r = anHF[2](d,init,deps)   #  Cavity-based frequency scale comes from O2 only
        ANALYSIS.append(r)

    peak_77 = r[77,"peak"]
    str_77 = r[77,"strength"]
    y_77 = r[77,"y"]
    base_77 = r[77,"base"]
    peak_79 = r[79,"peak"]
    str_79 = r[79,"strength"]
    y_79 = r[79,"y"]
    base_79 = r[79,"base"]
    base0 = r["base",0]
    base1 = r["base",1]
    shift_77 = r["base",3]
    peakvalue = peak_77+base_77
    base77_ave = initExpAverage(base77_ave,base_77,3,100,counter)
    peak77_baseave = peakvalue-base77_ave
    hf_ppbv = 0.2041*peak_77
    hf_ppbv_ave = 0.2041*peak77_baseave
    counter += 1
    hf_res = r["std_dev_res"]
    if (d["ngroups"] < 10) and (hf_ppbv > 500):
        hf_ppbv *= 0.94697
        hf_ppbv_ave *= 0.94697

if d["spectrumId"]==61 and d["ngroups"]>6:
    incomplete_hf_spectrum = 0
    #  Fit water-O2 doublet at 7822.95
    initialize_Baseline()
    r = anHF[3](d,init,deps)
    ANALYSIS.append(r)
    shift_81 = r["base",3]
    if (r[81,"peak"]<10 and r[82,"peak"]<10) or abs(r["base",3])>0.04:
        # Repeat with FC if both peaks weak or shift large
        r = anHF[4](d,init,deps)
        ANALYSIS.append(r)
    adjust_81 = r["base",3]
    goodLCT = abs(adjust_81)<0.005 and sigma0 < 0.005
    tuner61mean = tunerMean
    tuner61stdev = tunerStdev
    if goodLCT:
        d.waveNumber = f0 + fsr*round_((d.waveNumber - f0)/fsr)
        d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
        d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
        d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
        if r[81,"peak"]<10 and r[82,"peak"]<10:
            r = anHF[6](d,init,deps)
            ANALYSIS.append(r)
        else:
            r = anHF[5](d,init,deps)
            ANALYSIS.append(r)

    base0 = r["base",0]
    base1 = r["base",1]
    shift_81 = r["base",3]
    peak_81 = r[81,"peak"]
    str_81 = r[81,"strength"]
    base_81 = r[81,"base"]
    y_81 = r[81,"y"]
    peak_82 = r[82,"peak"]
    str_82 = r[82,"strength"]
    base_82= r[82,"base"]
    y_82 = r[82,"y"]
    o2_conc = 0.04801*peak_81
    h2o_conc_61 = 0.025*peak_82
    o2_res = r["std_dev_res"]

    if goodLCT:
        pzt1_adjust = (7823.84945-f0)*pzt_per_fsr/fsr
    else:
        pzt1_adjust = 0.0

if d["spectrumId"] in [60,61] and d["ngroups"]<7:
    incomplete_hf_spectrum = 1
    r = anHF[7](d,init,deps)
    ANALYSIS.append(r)
    goodLCT = 0
    pzt1_adjust = 0.0
    adjust_81 = 0.0

now = time.clock()
fit_time = now-tstart
if r != None:
    IgnoreThis = False
    if last_time != None:
        hf_interval = r["time"]-last_time
    else:
        hf_interval = 0
    if d["spectrumId"]==60:
        last_time = r["time"]

if (hf_baseMean >= hf_baseMean_thresh):
    degraded_hf_performance_counter = degraded_hf_performance_hold
else:
    degraded_hf_performance_counter = max(
        degraded_hf_performance_counter - 1, 0)

if degraded_hf_performance_counter > 0:
    degraded_hf_performance = 1
else:
    degraded_hf_performance = 0

ignore_count = max(0,ignore_count-1)
if (ignore_count == 0) and (not IgnoreThis):
    RESULT = {"base0":base0,"base1":base1,"base77_ave":base77_ave,"y_77":y_77,"y_79":y_79,
          "peak_77":peak_77,"str_77":str_77,"base_77":base_77,"shift_77":shift_77,
          "peak_79":peak_79,"str_79":str_79,"base_79":base_79,"pzt1_adjust":pzt1_adjust,
          "peak_81":peak_81,"str_81":str_81,"base_81":base_81,"shift_81":shift_81,
          "adjust_81":adjust_81,"peak_82":peak_82,"str_82":str_82,"base_82":base_82,
          "h2o_conc_61":h2o_conc_61,"o2_conc":o2_conc,
          "hf_ppbv":hf_ppbv,"hf_ppbv_ave":hf_ppbv_ave,"hf_res":hf_res,"o2_res":o2_res,
          "ngroups":d["ngroups"],"numRDs":d["datapoints"],"fit_time":fit_time,"hf_interval":hf_interval,
          "tuner60mean":tuner60mean,"tuner60stdev":tuner60stdev,"tuner61mean":tuner61mean,"tuner61stdev":tuner61stdev,
          "incomplete_hf_spectrum":incomplete_hf_spectrum,"hf_noBaseline":hf_noBaseline,"hf_baseMean":hf_baseMean,
          "hf_baseStdev":hf_baseStdev,"hf_baseLinIntercept":hf_baseLinIntercept,"hf_baseLinSlope":hf_baseLinSlope,
          "hf_baseQuadIntercept":hf_baseQuadIntercept,"hf_baseQuadSlope":hf_baseQuadSlope,
          "hf_baseQuadCurvature":hf_baseQuadCurvature,"hf_minBasePoints":hf_minBasePoints,
          "hf_maxBasePoints":hf_maxBasePoints,"hf_meanBasePoints":hf_meanBasePoints,
          "pzt_per_fsr":pzt_per_fsr,"goodLCT":goodLCT,"degraded_hf_performance":degraded_hf_performance}
    RESULT.update({"species":d["spectrumId"],"fittime":time.clock()-tstart,
               "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
               "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
