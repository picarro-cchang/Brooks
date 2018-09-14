#  Fit script for ammonia based on the AADS fitter and using LCT data acquisition
#  2018 0425:  First draft of a DCRDS fitter for AMADS NH3 in LCT mode.  Branched from
#              v4 of conventional AMADS NH3 (LCT) and DCRDS data set definition from SADS v1.4.
# 2018-07-10:  Added post-fit with acetylene and propyne to address
# problem with contaminated FOUP
#  2018-07-24:  Remeasured hydrocarbon splines with AMBDS2073

from numpy import any, argmin, diff, amin, amax, mean, std, sqrt, round_
import numpy as np
import os.path
import time
from Host.Common.EventManagerProxy import Log

def expAverage(xavg, x, n, dxMax):
    if xavg is None:
        return x
    y = (x + (n - 1) * xavg) / n
    if abs(y - xavg) < dxMax:
        return y
    elif y > xavg:
        return xavg + dxMax
    else:
        return xavg - dxMax


def initExpAverage(xavg, x, hi, dxMax, count):
    if xavg is None:
        return x
    n = min(max(count, 1), hi)
    y = (x + (n - 1) * xavg) / n
    if abs(y - xavg) < dxMax:
        return y
    elif y > xavg:
        return xavg + dxMax
    else:
        return xavg - dxMax


def initialize_Baseline():
    init["base", 1] = baseline_slope
    init[1000, 0] = A0
    init[1000, 1] = Nu0
    init[1000, 2] = Per0
    init[1000, 3] = Phi0
    init[1001, 0] = A1
    init[1001, 1] = Nu1
    init[1001, 2] = Per1
    init[1001, 3] = Phi1


def setBitFlag(flag, index):
    flag |= (1 << index)
    return flag


def resetBitFlag(flag, index):
    flag &= ~ (1 << index)
    return flag

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH, r"./NH3/spectral library NH3 v4_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(
        BASEPATH, r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(
        BASEPATH, r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_lct.ini")
    cavityParams = getInstrParams(fname)
    fsr = cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(
        BASEPATH, r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr = masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']

    anNH3 = []
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx water + co2 VC v1_2.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx water + co2 FC v1_2.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx water + co2 VC v1_2.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx water + co2 FC v1_2.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx peak 11 v1_1.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx peak 12 v1_1.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx peak 11 v1_1.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx peak 12 v1_1.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/big water #25 v2_0.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/big water #25 v2_0.ini")))
    anNH3.append(Analysis(os.path.join(BASEPATH, r"./NH3/Dummy v1_1.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx water + co2 + HC FC v1_2.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx water + co2 + ammonia + HC FC v1_2.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx peak 11 + HC v1_2.ini")))
    anNH3.append(Analysis(os.path.join(
        BASEPATH, r"./NH3/AADS-xx peak 12 + HC v1_2.ini")))

    #  Import instrument specific baseline constants

    baseline_slope = instrParams['NH3_Baseline_slope']
    A0 = instrParams['NH3_Sine0_ampl']
    Nu0 = instrParams['NH3_Sine0_freq']
    Per0 = instrParams['NH3_Sine0_period']
    Phi0 = instrParams['NH3_Sine0_phase']
    A1 = instrParams['NH3_Sine1_ampl']
    Nu1 = instrParams['NH3_Sine1_freq']
    Per1 = instrParams['NH3_Sine1_period']
    Phi1 = instrParams['NH3_Sine1_phase']

    #  Globals to pass between spectral regions

    goodLCT = 0
    i0 = 5
    f0 = 6548.618
    sigma0 = 0.0
    str15 = 0.0
    str17 = 0.0
    shift_avg = 0.0
    last_h2o = 0.0
    badshot_h2o = 0
    last_base_11 = 0.0
    last_base_12 = 0.0
    badshot_nh3 = 0
    counter = -10

    peak11a = 0.0
    peak15 = 0.0
    peak17 = 0.0

    res_a = 0.0
    res_11 = 0.0
    res_12 = 0.0
    peak25 = 0.0
    shift25 = 0.0
    shift_a = 0.0
    cm_adjust = 0.0
    nh3_peak_11 = 0.0
    nh3_base_11 = 0.0
    nh3_slope_11 = 0.0
    nh3_conc_11 = 0.0
    nh3_peak_12 = 0.0
    nh3_base_12 = 0.0
    nh3_slope_12 = 0.0
    nh3_conc_12 = 0.0
    nh3_conc_ave = 0.0
    nh3_conc_smooth = 0.0
    h2o_conc = 0.0
    co2_conc = 0.0
    pzt2_adjust = 0.0
    tuner2mean = 32768
    tuner2stdev = 0
    tuner4mean = 32768
    tuner4stdev = 0

    incomplete_nh3_spectrum = 0
    """
    Placeholder until conditions are agreed upon
    """
    degraded_nh3_performance = 0
    """
    End placeholder
    """
    nh3_noBaseline = 0
    nh3_baseMean = 0
    nh3_baseStdev = 0.0
    nh3_baseLinIntercept = 0.0
    nh3_baseLinSlope = 0.0
    nh3_baseQuadIntercept = 0.0
    nh3_baseQuadSlope = 0.0
    nh3_baseQuadCurvature = 0.0
    nh3_minBasePoints = 0
    nh3_maxBasePoints = 0
    nh3_meanBasePoints = 0

    PF_a_shift = 0.0
    PF_res_a = 0.0
    PF_a_co2_conc = 0.0
    PF_a_h2o_conc = 0.0
    PF_a_c3h4_conc = 0.0
    PF_a_c2h2_conc = 0.0
    PF_shift = 0.0
    PF_res = 0.0
    PF_base0 = 0.0
    PF_nh3_conc = 0.0
    PF_c3h4_conc = 0.0
    PF_c2h2_conc = 0.0
    PF_peak11 = 0.0
    PF_peak12 = 0.0
    PF_res_11 = 0.0
    PF_nh3_peak_11 = 0.0
    PF_res_12 = 0.0
    PF_nh3_peak_12 = 0.0
    PF_nh3_conc_ave = 0.0

    # The degraded_nh3_performance flag is set if any of the specified concentrations
    #  exceed their respective thresholds. The flag is held for "degraded_nh3_performance_hold"
    #  samples after all concentrations drop below the thresholds.

    if "c2h2_thresh" in instrParams:
        c2h2_thresh = instrParams["c2h2_thresh"]
    else:
        c2h2_thresh = 50.0

    if "c3h4_thresh" in instrParams:
        c3h4_thresh = instrParams["c3h4_thresh"]
    else:
        c3h4_thresh = 10.0

    if "nh3_baseMean_thresh" in instrParams:
        nh3_baseMean_thresh = instrParams["nh3_baseMean_thresh"]
    else:
        nh3_baseMean_thresh = 2.0

    if "degraded_nh3_performance_hold" in instrParams:
        degraded_nh3_performance_hold = instrParams[
            "degraded_nh3_performance_hold"]
    else:
        degraded_nh3_performance_hold = 5

    degraded_nh3_performance_counter = 0

    Log("Setting degraded_nh3_performance_threshold parameters", 
        Data=dict(c2h2_thresh=c2h2_thresh, c3h4_thresh=c3h4_thresh,
                  nh3_baseMean_thresh=nh3_baseMean_thresh,
                  degraded_nh3_performance_hold=degraded_nh3_performance_hold))

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

#  Point-by-point baseline subtraction and spectrum generation starts here

validBase = (d.extra2 == 1) & (d.uncorrectedAbsorbance > 0.1)
t0 = np.mean(d.timestamp)
ts = d.timestamp - t0
loss = d.uncorrectedAbsorbance
nh3_baseMean = np.mean(loss[validBase])
nh3_baseStdev = np.std(loss[validBase])
p = np.polyfit(ts[validBase], loss[validBase], 1)
nh3_baseLinIntercept = 1000 * p[1]
nh3_baseLinSlope = 1e6 * p[0]
p = np.polyfit(ts[validBase], loss[validBase], 2)
nh3_baseQuadIntercept = 1000 * p[2]
nh3_baseQuadSlope = 1e6 * p[1]
nh3_baseQuadCurvature = 1e9 * p[0]

N = len(d.extra2)
nWindow = 100  # Window size (HW) for baseline measurement
tWindow = 400  # Time window for baseline measurement in ms
goodPoints = []
nh3_noBaseline = 0
minBase = 1000
maxBase = -1000
basePoints = []
for i, ext2 in enumerate(d.extra2):
    if ext2 == 0:
        win = slice(max(0, i - nWindow), min(N, i + nWindow + 1))
        lwin = loss[win]
        twin = ts[win]
        select = (d.extra2[win] == 1) & (abs(ts[win] - ts[i])
                                         < tWindow) & (d.uncorrectedAbsorbance[win] > 0.1)
        if sum(select) > 1:
            basePoints.append(sum(select))
            p = np.polyfit(twin[select], lwin[select], 1)
            loss[i] -= np.polyval(p, ts[i])
            loss[i] += nh3_baseMean
            goodPoints.append(i)
            if np.polyval(p, ts[i]) < minBase:
                minBase = np.polyval(p, ts[i])
            if np.polyval(p, ts[i]) > maxBase:
                maxBase = np.polyval(p, ts[i])
        else:
            loss[i] = 0.0
            nh3_noBaseline += 1
d.indexVector = np.asarray(goodPoints)
if len(basePoints) > 0:
    nh3_minBasePoints = amin(basePoints)
    nh3_maxBasePoints = amax(basePoints)
    nh3_meanBasePoints = mean(basePoints)
else:
    nh3_minBasePoints = nh3_maxBasePoints = nh3_meanBasePoints = 0

d.badRingdownFilter("uncorrectedAbsorbance", minVal=0.20, maxVal=20.0)
# d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000, width=0.005, height=100000.0, xColumn="waveNumber",
         yColumn="uncorrectedAbsorbance", outlierThreshold=4.0)
d.evaluateGroups(["waveNumber", "uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"], loss=1000 * d.groupMeans[
                "uncorrectedAbsorbance"], sdev=1 / sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
tunerStdev = std(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.clock()
RESULT = {}
r = None
badshot_nh3 = 0
if d["spectrumId"] == 2 and d["ngroups"] > 5:
    incomplete_nh3_spectrum = 0
#   Fit CO2 and water lines
    initialize_Baseline()
    r = anNH3[0](d, init, deps)
    ANALYSIS.append(r)
    shift_a = r["base", 3]
    if (r[15, "peak"] > 10.0 or r[17, "peak"] > 10.0) and abs(shift_a) < 0.05:
        cm_adjust = shift_a
        dh2o = h2o_conc - last_h2o
        last_h2o = h2o_conc
        if abs(dh2o) > 1:
            badshot_h2o = 1
        else:
            badshot_h2o = 0
    else:
        r = anNH3[1](d, init, deps)
        ANALYSIS.append(r)
        cm_adjust = 0.0
    goodLCT = abs(cm_adjust) < 0.005 and sigma0 < 0.005 and badshot_h2o == 0
    tuner2mean = tunerMean
    tuner2stdev = tunerStdev
    if goodLCT:
        d.waveNumber = f0 + fsr * round_((d.waveNumber - f0) / fsr)
        d.badRingdownFilter("uncorrectedAbsorbance", minVal=0.20, maxVal=20.0)
        d.sparse(maxPoints=1000, width=0.003, height=100000.0, xColumn="waveNumber",
                 yColumn="uncorrectedAbsorbance", outlierThreshold=4.0)
        d.evaluateGroups(["waveNumber", "uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["waveNumber"], loss=1000 * d.groupMeans[
                        "uncorrectedAbsorbance"], sdev=1 / sqrt(d.groupSizes))
        if (r[15, "peak"] < 10 and r[17, "peak"] < 10) or abs(shift_a) > 0.05:
            r = anNH3[3](d, init, deps)
            ANALYSIS.append(r)
        else:
            r = anNH3[2](d, init, deps)
            ANALYSIS.append(r)

    peak15 = r[15, "peak"]
    peak17 = r[17, "peak"]
    str15 = r[15, "strength"]
    str17 = r[17, "strength"]
    shift_a = r["base", 3]
    res_a = r["std_dev_res"]
    h2o_conc = 0.02 * peak15
    co2_conc = 81.3 * peak17

    #  Post-fit with acetylene and propyne in the spectral model

    init[1003, 2] = PF_c3h4_conc / 19.94
    r = anNH3[11](d, init, deps)
    ANALYSIS.append(r)
    PF_a_shift = r["base", 3]
    PF_res_a = r["std_dev_res"]
    PF_a_h2o_conc = 0.02 * r[15, "peak"]
    PF_a_co2_conc = 81.3 * r[17, "peak"]
    PF_a_c3h4_conc = 19.94 * r[1003, 2]
    PF_a_c2h2_conc = 19.38 * r[1002, 2]
    if abs(PF_a_c3h4_conc) > 1 or abs(PF_a_c2h2_conc) > 1:
        cm_adjust = 0

    if goodLCT:
        pzt2_adjust = (6548.618 - f0) * pzt_per_fsr / fsr
    else:
        pzt2_adjust = 0.0

if d["spectrumId"] == 2 and d["ngroups"] < 6:
    incomplete_nh3_spectrum = 1
    r = anNH3[10](d, init, deps)
    ANALYSIS.append(r)
    goodLCT = 0
    pzt2_adjust = 0.0
    cm_adjust = 0.0

if d["spectrumId"] == 4 and d["ngroups"] > 13:
    incomplete_nh3_spectrum = 0
#   Ammonia region:  fit peaks 11 and 12 separately
    initialize_Baseline()
    init[15, "strength"] = str15
    init[17, "strength"] = str17
    r = anNH3[4](d, init, deps)
    ANALYSIS.append(r)
    res_11 = r["std_dev_res"]
    nh3_peak_11 = r[11, "peak"]
    nh3_str_11 = r[11, "strength"]
    if not goodLCT:
        nh3_quality_11 = fitQuality(res_11, nh3_peak_11, 50, 0.2)
        if nh3_quality_11 <= 15:
            nh3_base_11 = r["base", 0]
            nh3_slope_11 = r["base", 1]
            nh3_shift_11 = r["base", 3]
            nh3_conc_11 = 8.75 * nh3_peak_11
        else:
            badshot_nh3 = 1
        dbase = r[11, "base"] - last_base_11
        last_base_11 = r[11, "base"]
        if abs(dbase) > 3:
            badshot_nh3 = 1

    r = anNH3[5](d, init, deps)
    ANALYSIS.append(r)
    res_12 = r["std_dev_res"]
    # NH3 conc is expressed in terms of peak 11, but fit uses peak 12 through
    # dependency
    nh3_peak_12 = r[11, "peak"]
    nh3_str_12 = r[11, "strength"]
    if not goodLCT:
        nh3_quality_12 = fitQuality(res_12, nh3_peak_12, 50, 0.2)
        if nh3_quality_12 <= 15:
            nh3_base_12 = r["base", 0]
            nh3_slope_12 = r["base", 1]
            nh3_shift_12 = r["base", 3]
            nh3_conc_12 = 8.75 * nh3_peak_12
        else:
            badshot_nh3 = 1
        dbase = r[12, "base"] - last_base_12
        last_base_12 = r[12, "base"]
        if abs(dbase) > 3:
            badshot_nh3 = 1
    tuner4mean = tunerMean
    tuner4stdev = tunerStdev
    if goodLCT:
        i0 = argmin(abs(d.fitData["freq"] - 6548.618))
        f0 = d.fitData["freq"][i0]
        while (f0 - 6548.618) < -0.5 * fsr:
            f0 += fsr
        while (f0 - 6548.618) > 0.5 * fsr:
            f0 -= fsr
        sigma0 = d.groupStdDevs["waveNumber"][i0]
        # print "%2d %8.5f %8.5f" % (i0, f0 - 6548.618, sigma0)
        d.waveNumber = f0 + fsr * round_((d.waveNumber - f0) / fsr)
        d.badRingdownFilter("uncorrectedAbsorbance", minVal=0.20, maxVal=20.0)
        d.sparse(maxPoints=1000, width=0.003, height=100000.0, xColumn="waveNumber",
                 yColumn="uncorrectedAbsorbance", outlierThreshold=4.0)
        d.evaluateGroups(["waveNumber", "uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["waveNumber"], loss=1000 * d.groupMeans[
                        "uncorrectedAbsorbance"], sdev=1 / sqrt(d.groupSizes))

    r = anNH3[6](d, init, deps)
    ANALYSIS.append(r)
    res_11 = r["std_dev_res"]
    nh3_peak_11 = r[11, "peak"]
    nh3_str_11 = r[11, "strength"]
    nh3_quality_11 = fitQuality(res_11, nh3_peak_11, 50, 0.2)
    if nh3_quality_11 <= 15:
        nh3_base_11 = r["base", 0]
        nh3_slope_11 = r["base", 1]
        nh3_shift_11 = r["base", 3]
        nh3_conc_11 = 8.75 * nh3_peak_11
    else:
        badshot_nh3 = 1
    dbase = nh3_base_11 - last_base_11
    last_base_11 = nh3_base_11
    if abs(dbase) > 3:
        badshot_nh3 = 1

    r = anNH3[7](d, init, deps)
    ANALYSIS.append(r)
    res_12 = r["std_dev_res"]
    # NH3 conc is expressed in terms of peak 11, but fit uses peak 12 through
    # dependency
    nh3_peak_12 = r[11, "peak"]
    nh3_str_12 = r[11, "strength"]
    nh3_quality_12 = fitQuality(res_12, nh3_peak_12, 50, 0.2)
    if nh3_quality_12 <= 15:
        nh3_base_12 = r["base", 0]
        nh3_slope_12 = r["base", 1]
        nh3_shift_12 = r["base", 3]
        nh3_conc_12 = 8.75 * nh3_peak_12
    else:
        badshot_nh3 = 1
    dbase = nh3_base_12 - last_base_12
    last_base_12 = nh3_base_12
    if abs(dbase) > 3:
        badshot_nh3 = 1

    nh3_conc_ave = 0.5 * (nh3_conc_11 + nh3_conc_12)
    nh3_conc_smooth = initExpAverage(
        nh3_conc_smooth, nh3_conc_ave, 50, 1, counter)
    counter += 1

    #  Post-fit with acetylene and propyne in the spectral model

    init[1002, 2] = PF_a_c2h2_conc / 19.38
    r = anNH3[12](d, init, deps)
    ANALYSIS.append(r)
    PF_base0 = r["base", 0]
    PF_shift = r["base", 3]
    PF_res = r["std_dev_res"]
    PF_nh3_conc = 8.75 * r[11, "peak"]
    PF_c3h4_conc = 19.94 * r[1003, 2]
    PF_c2h2_conc = 19.38 * r[1002, 2]
    PF_peak11 = r[11, "peak"]
    PF_peak12 = r[12, "peak"]
    init[1003, 2] = r[1003, 2]
    r = anNH3[13](d, init, deps)
    ANALYSIS.append(r)
    PF_res_11 = r["std_dev_res"]
    PF_nh3_peak_11 = r[11, "peak"]
    r = anNH3[14](d, init, deps)
    ANALYSIS.append(r)
    PF_res_12 = r["std_dev_res"]
    PF_nh3_peak_12 = r[11, "peak"]
    PF_nh3_conc_ave = 0.5 * (8.75 * PF_nh3_peak_11 + 8.75 * PF_nh3_peak_12)

if d["spectrumId"] == 4 and d["ngroups"] < 14:
    incomplete_nh3_spectrum = 1
    r = anNH3[10](d, init, deps)
    ANALYSIS.append(r)
    goodLCT = 0

if d["spectrumId"] == 3:
    #   Big water region
    init["base", 0] = 0.0
    r = anNH3[8](d, init, deps)
    ANALYSIS.append(r)
    shift25 = r["base", 3]
    if peak25 > 5 and abs(shift25) < 0.07:
        cm_adjust = shift25
    else:
        cm_adjust = 0.0

    goodLCT = abs(shift25) < 0.002
    if goodLCT:
        d.waveNumber = 6548.618 + fsr * round_((d.waveNumber - 6548.618) / fsr)
        d.badRingdownFilter("uncorrectedAbsorbance", minVal=0.20, maxVal=20.0)
        d.sparse(maxPoints=1000, width=0.003, height=100000.0, xColumn="waveNumber",
                 yColumn="uncorrectedAbsorbance", outlierThreshold=4.0)
        d.evaluateGroups(["waveNumber", "uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["waveNumber"], loss=1000 * d.groupMeans[
                        "uncorrectedAbsorbance"], sdev=1 / sqrt(d.groupSizes))

        r = anNH3[9](d, init, deps)
        ANALYSIS.append(r)

    shift25 = r["base", 3]
    peak25 = r[25, "peak"]
    str25 = r[25, "strength"]
    res_25 = r["std_dev_res"]
    h2o_conc = 0.000248 * peak25
    str15 = 0.00812 * str25
    if goodLCT and peak25 > 10:
        pzt2_adjust = -shift25 * pzt_per_fsr / fsr
    else:
        pzt2_adjust = 0.0


# Set the degraded_performance flag and implement hold algorithm

if (PF_c2h2_conc >= c2h2_thresh) or (PF_c3h4_conc >= c3h4_thresh) or (nh3_baseMean >= nh3_baseMean_thresh):
    degraded_nh3_performance_counter = degraded_nh3_performance_hold
else:
    degraded_nh3_performance_counter = max(
        degraded_nh3_performance_counter - 1, 0)

if degraded_nh3_performance_counter > 0:
    degraded_nh3_performance = 1
else:
    degraded_nh3_performance = 0


RESULT = {"res_a": res_a, "res_11": res_11, "res_12": res_12,
          "peak15": peak15, "peak17": peak17, "badshot_h2o": badshot_h2o,
          "h2o_conc": h2o_conc, "co2_conc": co2_conc, "shift_a": shift_a, "cm_adjust": cm_adjust,
          "peak25": peak25, "shift25": shift25, "goodLCT": goodLCT,
          "nh3_peak_11": nh3_peak_11, "nh3_base_11": nh3_base_11, "nh3_slope_11": nh3_slope_11,
          "nh3_base_12": nh3_base_12, "nh3_peak_12": nh3_peak_12, "nh3_slope_12": nh3_slope_12,
          "nh3_conc_ave": nh3_conc_ave, "nh3_conc_smooth": nh3_conc_smooth,
          "pzt2_adjust": pzt2_adjust, "pzt_per_fsr": pzt_per_fsr,
          "tuner2mean": tuner2mean, "tuner2stdev": tuner2stdev, "tuner4mean": tuner4mean, "tuner4stdev": tuner4stdev,
          "incomplete_nh3_spectrum": incomplete_nh3_spectrum, "nh3_noBaseline": nh3_noBaseline, "nh3_baseMean": nh3_baseMean,
          "nh3_baseStdev": nh3_baseStdev, "nh3_baseLinIntercept": nh3_baseLinIntercept, "nh3_baseLinSlope": nh3_baseLinSlope,
          "nh3_baseQuadIntercept": nh3_baseQuadIntercept, "nh3_baseQuadSlope": nh3_baseQuadSlope,
          "nh3_baseQuadCurvature": nh3_baseQuadCurvature, "nh3_minBasePoints": nh3_minBasePoints,
          "nh3_maxBasePoints": nh3_maxBasePoints, "nh3_meanBasePoints": nh3_meanBasePoints,
          "PF_shift": PF_shift, "PF_c3h4_conc": PF_c3h4_conc, "PF_c2h2_conc": PF_c2h2_conc, "PF_nh3_conc": PF_nh3_conc,
          "PF_base0": PF_base0, "PF_a_shift": PF_a_shift, "PF_a_co2_conc": PF_a_co2_conc, "PF_a_h2o_conc": PF_a_h2o_conc,
          "PF_a_c3h4_conc": PF_a_c3h4_conc, "PF_a_c2h2_conc": PF_a_c2h2_conc, "PF_peak11": PF_peak11, "PF_peak12": PF_peak12,
          "PF_res_a": PF_res_a, "PF_res": PF_res, "PF_res_11": PF_res_11, "PF_res_12": PF_res_12,
          "PF_nh3_peak_11": PF_nh3_peak_11, "PF_nh3_peak_12": PF_nh3_peak_12, "PF_nh3_conc_ave": PF_nh3_conc_ave,
          "ngroups": d["ngroups"], "numRDs": d["datapoints"], "degraded_nh3_performance": degraded_nh3_performance}
RESULT.update({"species": d["spectrumId"], "fittime": time.clock() - tstart,
               "cavity_pressure": P, "cavity_temperature": T, "solenoid_valves": solValves,
               "das_temp": dasTemp})
RESULT.update(d.sensorDict)
