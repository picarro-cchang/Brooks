#  G2000 fit script for pressure calibration in HF region
#  Version 1 started 20 April 2011 by hoffnagle

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.time()

if INIT:
    fname = os.path.join(BASEPATH, r"./MADS/spectral library v2_1_AADS4_MA_20110601.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"test_instr_params.ini")
    #instrParams = getInstrParams(fname)
    #locals().update(instrParams)

    anO2 = []
    anO2.append(Analysis(os.path.join(BASEPATH, r"./MADS/HF_PressureCal_VZ_v1.ini")))
    lastShift = None

    # For offline analysis and output to file
    out = open("Fit_results.txt", "w")
    first_fit = 1

init = InitialValues()
if lastShift is not None:
    init["base", 3] = lastShift

deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance", minVal=0.30, maxVal=20.0)
#d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000, width=0.003, height=100000.0, xColumn="waveNumber", yColumn="uncorrectedAbsorbance", outlierThreshold=4)
d.evaluateGroups(["waveNumber", "uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"], loss=1000 * d.groupMeans["uncorrectedAbsorbance"], sdev=1 / sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]

tstart = time.time()
if d["spectrumId"] == 0:
    r = anO2[0](d, init, deps)
    ANALYSIS.append(r)
    hf_shift = r["base", 3]
    peak_81 = r[81, "peak"]
    base_81 = r[81, "base"]
    str_81 = r[81, "strength"]
    y_81 = r[81, "y"]
    z_81 = r[81, "z"]
    peak_82 = r[82, "peak"]
    base = r["base", 0]
    slope = r["base", 1]
    hf_res = r["std_dev_res"]
    if peak_81 > 10 and abs(hf_shift) < 0.02:
        hf_adjust = hf_shift
    else:
        hf_adjust = 0
    lastShift = hf_adjust

    RESULT = {
        "hf_res": hf_res,
        "y_parameter": abs(y_81),
        "o2_peak": peak_81,
        "str_81": str_81,
        "baseline": base,
        "baseline_slope": slope,
        "h2o_peak": peak_82,
        "z_parameter": abs(z_81),
        "hf_shift": hf_shift,
        "freq_offset": hf_adjust
    }

    RESULT.update({"species": 0, "fittime": time.time() - tstart, "cavity_pressure": P, "cavity_temperature": T})
    RESULT.update(d.sensorDict)

    # ---------  This section goes to end of file  ----------
    if first_fit:
        keys = sorted([k for k in RESULT])
        print >> out, " ".join(keys)
        first_fit = 0
    print >> out, " ".join(["%s" % RESULT[k] for k in keys])
