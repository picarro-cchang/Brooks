#  Fit script to measure width of the CO2 line at 6058.2 wvn
#  2019 0108:  First draft derived from old pressure sensor test script modified for new laser
#  2019 0415:  Adapted from script written for AVX system at 80 C to use with 45 C G2000
#  2019 0423:  New variant to measure the 6547.69 wvn line in a sample of 1% CO2 in nitrogen
#  2019 0426:  Adjusted linewidth-to-pressure calibration factor based on intercomparison with
#              6058.2 wvn manometer using JFAADS2157 (Log book XII, p. 145)
#  2019 0501:  New variant to measure the 7823 wvn oxygen line width in dried air
#  2019 0809:  Adjusted linewidth-to-pressure calibration factor based on intercomparison with
#              6547.7 wvn manometer using AMADS2009 (Log book XIII, p. 13)

import os.path
import time
from numpy import *
from copy import copy


def initialize_Baseline():
    init[1000, 0] = A0
    init[1000, 1] = Nu0
    init[1000, 2] = Per0
    init[1000, 3] = Phi0
    init[1001, 0] = A1
    init[1001, 1] = Nu1
    init[1001, 2] = Per1
    init[1001, 3] = Phi1


def outlierFilter(x, threshold, minPoints=2):
    """ Return Boolean array giving points in the vector x which lie
    within +/- threshold * std_deviation of the mean. The filter is applied iteratively
    until there is no change or unless there are minPoints or fewer remaining"""
    good = ones(x.shape, bool_)
    order = list(x.argsort())
    while len(order) > minPoints:
        maxIndex = order.pop()
        good[maxIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[maxIndex] - mu) >= (threshold * sigma):
            continue
        good[maxIndex] = 1
        minIndex = order.pop(0)
        good[minIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[minIndex] - mu) >= (threshold * sigma):
            continue
        good[minIndex] = 1
        break
    return good


def expAverage(xavg, x, n, dxMax):
    if xavg is None: return x
    y = (x + (n - 1) * xavg) / n
    if abs(y - xavg) < dxMax: return y
    elif y > xavg: return xavg + dxMax
    else: return xavg - dxMax


if INIT:
    fname = os.path.join(BASEPATH, r"./MADS/spectral library MADSxx_v2_4.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(
        BASEPATH,
        r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(
        BASEPATH,
        r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_lct.ini"
    )
    cavityParams = getInstrParams(fname)
    fsr = cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(
        BASEPATH, r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr = masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']

    optDict = eval("dict(%s)" % OPTION)

    anO2 = []
    anO2.append(Analysis(os.path.join(BASEPATH, r"./MADS/Peak81_only_VY.ini")))
    anO2.append(Analysis(os.path.join(BASEPATH, r"./MADS/Peak81_only_VY.ini")))

    #   Globals
    last_time = None

    #   Spectroscopic parameters
    fO2 = 7822.9838  # library center for Galatry peak 81

    #   Baseline parameters

    A0 = instrParams['HF_Sine0_ampl']
    Nu0 = instrParams['HF_Sine0_freq']
    Per0 = instrParams['HF_Sine0_period']
    Phi0 = instrParams['HF_Sine0_phase']
    A1 = instrParams['HF_Sine1_ampl']
    Nu1 = instrParams['HF_Sine1_freq']
    Per1 = instrParams['HF_Sine1_period']
    Phi1 = instrParams['HF_Sine1_phase']

    #   Initialize values

    o2_adjust = 0
    o2_pct = 20.9
    h2o_ppm = 0
    y81 = 0.6678
    peak81 = 0
    str81 = 0
    base81 = 0
    peak82 = 0
    o2_residuals = 0
    fsr_shift_o2 = 0
    fsr_y81 = 0.6678
    fsr_z81 = 0.2618
    fsr_peak81 = 0
    fsr_str81 = 0
    fsr_base81 = 0
    fsr_peak82 = 0
    fsr_str82 = 0
    o2_residuals_fsr = 0
    pzt1_adjust = 0.0
    pzt1 = 0
    pspec = 140

    #   Presistent outputs

    paveraged = 140

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = copy(DATA)
d.badRingdownFilter("uncorrectedAbsorbance", minVal=0.20, maxVal=20.0)
d.sparse(maxPoints=1000,
         width=0.01,
         height=100000.0,
         xColumn="waveNumber",
         yColumn="uncorrectedAbsorbance",
         outlierThreshold=4)
d.evaluateGroups(["waveNumber", "uncorrectedAbsorbance"])

d.defineFitData(freq=d.groupMeans["waveNumber"],
                loss=1000 * d.groupMeans["uncorrectedAbsorbance"],
                sdev=1 / sqrt(array(d.groupSizes)))
T = d["cavitytemperature"] + 273.15
species = (d.subschemeId & 0x3FF)[0]
tstart = time.clock()
RESULT = {}
r = None

if d["spectrumId"] == 62:
    pzt1 = mean(d.pztValue)
    initialize_Baseline()
    r = anO2[0](d, init, deps)  #  Fit with frequency from WLM.
    ANALYSIS.append(r)
    o2_shift = r["base", 3]
    o2_adjust = r["base", 3]
    y81 = r[81, "y"]
    peak81 = r[81, "peak"]
    str81 = r[81, "strength"]
    base81 = r[81, "base"]
    peak82 = r[82, "peak"]
    o2_pct = 0.04801 * peak81
    h2o_ppm = 250 * peak82
    o2_residuals = r["std_dev_res"]

    if r[81, "peak"] < -10 or r[81, "peak"] > 10000:
        goodLCT = False
    else:
        goodLCT = True
    if goodLCT:
        d.fitData["freq"] = fO2 + fsr * round_(
            (d.fitData["freq"] + o2_adjust - fO2) / fsr)

        r = anO2[1](d, init, deps)
        ANALYSIS.append(r)
        fsr_shift_o2 = r["base", 3]
        pzt1_adjust = -fsr_shift_o2 * pzt_per_fsr / fsr
        fsr_y81 = r[81, "y"]
        fsr_z81 = r[81, "z"]
        fsr_peak81 = r[81, "peak"]
        fsr_str81 = r[81, "strength"]
        fsr_base81 = r[81, "base"]
        fsr_peak82 = r[82, "peak"]
        fsr_str82 = r[82, "strength"]
        o2_residuals_fsr = r["std_dev_res"]

        pspec = 140.0 * fsr_y81 / 0.70421
        paveraged = expAverage(paveraged, pspec, 100, 0.2)

        o2_pct = 0.025838 * fsr_str81 * (
            140 / pspec)  #  From dry air calibration 9. Aug. 2019
        h2o_ppm = 107.1 * fsr_str82 * (140 / pspec)  #  From Hitran 2016

now = time.clock()
fit_time = now - tstart
if r != None:
    IgnoreThis = False
    if last_time != None:
        interval = r["time"] - last_time
    else:
        interval = 0
    last_time = r["time"]
else:
    IgnoreThis = True

if not IgnoreThis:
    RESULT = {
        "goodLCT": goodLCT,
        "pspec": pspec,
        "paveraged": paveraged,
        "pzt1_adjust": pzt1_adjust,
        "pzt1": pzt1,
        "dataGroups": d["ngroups"],
        "dataPoints": d["datapoints"],
        "pzt_per_fsr": pzt_per_fsr,
        "fsr_str82": fsr_str82,
        "o2_shift": o2_shift,
        "o2_adjust": o2_adjust,
        "fsr_peak81": fsr_peak81,
        "fsr_y81": fsr_y81,
        "fsr_base81": fsr_base81,
        "fsr_str81": fsr_str81,
        "fsr_shift_o2": fsr_shift_o2,
        "o2_pct": o2_pct,
        "o2_residuals_fsr": o2_residuals_fsr,
        "o2_pct": o2_pct,
        "h2o_ppm": h2o_ppm,
        "fsr_peak82": fsr_peak82,
        "interval": interval,
        "fit_time": fit_time,
        "species": species
    }
    RESULT.update(d.sensorDict)
