#  Fit script HCl using the 5739.26 wavenumber line, with water and methane as reference lines
#  2015-07-23:  Started
#  2015-08-14:  Added second spectrum ID with stronger water line for WLM offset
#  2015-09-01:  Ignore first few points for H2O to settle
#  2016-04-04:  Changed scheme trying to smooth Allan variance
#  2016-04-06:  Removed reporting made superfluous by new scheme
#  2016-04-08:  Modification to operate at 140 Torr
#  2016-05-17:  Changed again to operate at 140 Torr and 80 C
#  2016-06-15:  Added extra testing for baseline jumps to exclude bogus measurements when hydrocarbon solvents are used in fab
#  2016-08-18:  Changed reporting of contaminated samples to report with flag
#  2016-12-12:  Changed logic leading to VCFY fit for better performance with dry, high concentration methane
#  2017-02-22:  Completely new approach to organic suppression:  Differential CRDS interleaving baseline and data measurements
#  2018-03-30:  Resume DCRDS experiments.  I will skip some attempts from 2017 to place the "baseline" points on the HCl peak
#               Merge multiple changes made to conventional HCl analysis from Fall 2017 through Spring 2018
#  2018-04-16:  Changes to reported statistics of base and pzt to exclude ringdowns that timed out
#  2018-04-30:  Added condition to suppress wlm adjust when high ethylene is present
#  2018-06-19:  Added bad_baseline flags and modified incomplete_spectrum
#                for DCRDS
#  2018-06-21:  Added spectrum_min_groups parameter to indicate number of points below which the spectrun is
#                deemed to be incomplete
#  2018-07-11:  Major change -- include ethylene in spectral model for standard fit and do away with post-fit
#               Remove spectrum score, which does not appear to be useful (jah)
#  2018-07-17:  Replaced bad_baseline flags with degraded_performance flag for when the threshold is dynamically set
#               to a value other than the original threshold setting in Master.ini
#  2019-05-03:  Changed cavity temperature back to 45 C.
#  2019-05-10:  Branched new version for LCT mode
#  2019_05-11:  HCl is in virtual laser 3 for dual cavities; H2O is H2O_a

from numpy import any, amin, amax, argmin, mean, std, sqrt, log10, round_
import numpy as np
import os.path
import time
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER
from Host.Common.EventManagerProxy import Log

def initialize_Baseline():
    init[1000, 0] = A0
    init[1000, 1] = Nu0
    init[1000, 2] = Per0
    init[1000, 3] = Phi0
    init[1001, 0] = A1
    init[1001, 1] = Nu1
    init[1001, 2] = Per1
    init[1001, 3] = Phi1

tstart = time.clock()
spectrum_min_groups = 25

if INIT:
    fname = os.path.join(BASEPATH, r"./HCl/spectral library HCl v1_2.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(
        BASEPATH, r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_HCl_140Torr_45C.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_lct.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']

    Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                        "FitScript", IsDontCareConnection=False)

    anHCl = []
    anHCl.append(Analysis(os.path.join(
        BASEPATH, r"./HCl/HCl+H2O+HC 140 Torr VC VY v1_2.ini")))
    anHCl.append(Analysis(os.path.join(
        BASEPATH, r"./HCl/HCl+H2O+HC 140 Torr FC FY v1_2.ini")))
    anHCl.append(Analysis(os.path.join(
        BASEPATH, r"./HCl/HCl+H2O+HC 140 Torr VC FY v1_2.ini")))
    anHCl.append(Analysis(os.path.join(
        BASEPATH, r"./HCl/HCl+H2O+HC 140 Torr VC VY v1_2.ini")))
    anHCl.append(Analysis(os.path.join(
        BASEPATH, r"./HCl/HCl+H2O+HC 140 Torr FC FY v1_2.ini")))
    anHCl.append(Analysis(os.path.join(
        BASEPATH, r"./HCl/HCl+H2O+HC 140 Torr VC FY v1_2.ini")))
    anHCl.append(Analysis(os.path.join(BASEPATH, r"./HCl/Dummy v1_1.ini")))

    # Import instrument specific baseline constants and cross-talk corrections
    # for HCl

    baseline_level = instrParams['HCl_Baseline_level']
    baseline_slope = instrParams['HCl_Baseline_slope']
    A0 = instrParams['HCl_Sine0_ampl']
    Nu0 = instrParams['HCl_Sine0_freq']
    Per0 = instrParams['HCl_Sine0_period']
    Phi0 = instrParams['HCl_Sine0_phase']
    A1 = instrParams['HCl_Sine1_ampl']
    Nu1 = instrParams['HCl_Sine1_freq']
    Per1 = instrParams['HCl_Sine1_period']
    Phi1 = instrParams['HCl_Sine1_phase']

    hcl_lin = instrParams['HCl_linear']
    h2o_lin = instrParams['H2O_linear']
    h2o_slin = instrParams['H2O_strength_linear']
    ch4_hcl_lin = instrParams['CH4_to_HCl_linear']
    h2o_hcl_lin = instrParams['H2O_to_HCl_linear']

    # Import quantities for dynamic switching of ringdown threshold
    # If average ring-down rate for a spectrum falls below "min_rd_rate",
    #  the threshold is set to "min_rd_threshold". Once all reported
    #  losses are less than "safe_loss_level", the threshold is 
    #  reset to "original_rd_threshold"

    if "original_rd_threshold" in instrParams:
        original_rd_threshold = instrParams['original_rd_threshold']
    else:
        original_rd_threshold = Driver.rdDasReg("SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER")
    
    if "min_rd_threshold" in instrParams:
        min_rd_threshold = instrParams['min_rd_threshold']
    else:
        min_rd_threshold = 5000

    if "safe_loss_level" in instrParams:
        safe_loss_level = instrParams['safe_loss_level']
    else:
        safe_loss_level = 1500.0  # In ppb/cm

    if "min_rd_rate" in instrParams:
        min_rd_rate = instrParams['min_rd_rate']
    else:
        min_rd_rate = 65

    if "disable_dynamic_threshold" in instrParams:
        disable_dynamic_threshold = int(instrParams['disable_dynamic_threshold'])
    else:
        disable_dynamic_threshold = 0

    Log("Setting dynamic ringdown threshold parameters", 
        Data=dict(original_rd_threshold=original_rd_threshold,
                  min_rd_threshold=min_rd_threshold,
                  safe_loss_level=safe_loss_level,
                  min_rd_rate=min_rd_rate,
                  disable_dynamic_threshold=disable_dynamic_threshold))

    #  Globals for communication between spectral regions

    hcl_shift = 0.0
    hcl_adjust = 0.0
    baseline_level = 0.0
    baseline_slope = baseline_slope
    hcl_adjust = 0.0
    peak62 = 0.0
    str62 = 0.0
    y62 = 1.396
    base70 = 0.0
    peak70 = 0.0
    str70 = 0.0
    y70 = 1.508
    ch4_ampl = 0.0
    res = 0.0
    y62lib = 140 * spectrParams['peak62']['y']
    f70 = spectrParams['peak70']['center']
    f0 = f70

    hcl_conc_raw = 0.0
    hcl_conc = 0.0
    h2o_a_conc_raw = 0.0
    ch4_conc_raw = 0.0

    ch3oh_conc = 0.0
    c2h4_conc = 0.0

    pzt3_mean = 32768
    pzt3_stdev = 0
    pzt3_adjust = 0
    sigma0 = 0

    goodLCT = 0
    incomplete_spectrum = 0
    noBaseline = 0
    degraded_performance = 0
    baseMean = instrParams['HCl_Baseline_level']
    baseStdev = 0.0
    baseLinIntercept = 0.0
    baseLinSlope = 0.0
    baseQuadIntercept = 0.0
    baseQuadSlope = 0.0
    baseQuadCurvature = 0.0
    minBasePoints = 0
    maxBasePoints = 0
    meanBasePoints = 0

    ignore_count = 3
    last_time = None

    # Keep unsued keys for Pfieffer's APA so that they
    # don't have to reprogram their system for the beta test
    # RSF 26JUN2018
    delta_loss_hcl = 0
    delta_loss_h2o = 0

# For offline analysis and output to file
    # out = open("Fit_results.txt","w")
    # first_fit = 1

# ---------  This section goes to end of file  ----------
    # if first_fit:
    # keys = sorted([k for k in RESULT])
    # print>>out," ".join(keys)
    # first_fit = 0
    # print>>out," ".join(["%s" % RESULT[k] for k in keys])

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

current_threshold = Driver.rdFPGA("FPGA_RDMAN", "RDMAN_THRESHOLD")
# If ringdown rate is less than 75rd/s lower the threshold and return empty result
rd_rate = 0
if len(d.timestamp) > 1:
    ms_between_rds = d.timestamp.ptp() / (len(d.timestamp) - 1)  # Ringdowns / second
    rd_rate = 1000.0 / ms_between_rds

if not(disable_dynamic_threshold) and (rd_rate < min_rd_rate) and (current_threshold > min_rd_threshold):
    degraded_performance = 1
    Driver.wrDasReg("SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER", min_rd_threshold)
    Driver.wrFPGA("FPGA_RDMAN", "RDMAN_THRESHOLD", min_rd_threshold)
    Log("Fitter changes threshold to %d" % min_rd_threshold)
    RESULT = {}
else:
    # Ringdown rate is appropriate for correct operation
    #  Point-by-point baseline subtraction and spectrum generation starts here
    validBase = (d.extra2 == 1) & (d.uncorrectedAbsorbance > 0.1)
    t0 = np.mean(d.timestamp)
    ts = d.timestamp - t0
    loss = d.uncorrectedAbsorbance
    baseMean = np.mean(loss[validBase])
    baseStdev = np.std(loss[validBase])
    p = np.polyfit(ts[validBase], loss[validBase], 1)
    baseLinIntercept = 1000 * p[1]
    baseLinSlope = 1e6 * p[0]
    p = np.polyfit(ts[validBase], loss[validBase], 2)
    baseQuadIntercept = 1000 * p[2]
    baseQuadSlope = 1e6 * p[1]
    baseQuadCurvature = 1e9 * p[0]

    N = len(d.extra2)
    nWindow = 100  # Window size (HW) for baseline measurement
    tWindow = 400  # Time window for baseline measurement in ms
    goodPoints = []
    noBaseline = 0
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
                loss[i] += baseMean
                goodPoints.append(i)
                if np.polyval(p, ts[i]) < minBase:
                    minBase = np.polyval(p, ts[i])
                if np.polyval(p, ts[i]) > maxBase:
                    maxBase = np.polyval(p, ts[i])
            else:
                loss[i] = 0.0
                noBaseline += 1
    d.indexVector = np.asarray(goodPoints)
    if len(basePoints) > 0:
        minBasePoints = amin(basePoints)
        maxBasePoints = amax(basePoints)
        meanBasePoints = mean(basePoints)
    else:
        minBasePoints = maxBasePoints = meanBasePoints = 0
    #print (minBase, maxBase)

    d.badRingdownFilter("uncorrectedAbsorbance", minVal=0.1, maxVal=20.0)
    d.sparse(maxPoints=2000, width=0.005, height=100000.0, xColumn="waveNumber",
            yColumn="uncorrectedAbsorbance", outlierThreshold=4.0)
    d.evaluateGroups(["waveNumber", "uncorrectedAbsorbance"])
    d.defineFitData(freq=d.groupMeans["waveNumber"], loss=1000 * d.groupMeans[
                    "uncorrectedAbsorbance"], sdev=1 / sqrt(d.groupSizes))
    P = d["cavitypressure"]
    T = d["cavitytemperature"]
    tunerMean = mean(d.tunerValue)
    solValves = d.sensorDict["ValveMask"]
    dasTemp = d.sensorDict["DasTemp"]
    r = None

    tstart = time.clock()
    if (d["spectrumId"] == 63) and (d["ngroups"] >= spectrum_min_groups):
        incomplete_spectrum = 0
        initialize_Baseline()
        # Fit wide spectrum with water, methane and HCl using frequencies from WLM
        r = anHCl[0](d, init, deps)
        ANALYSIS.append(r)
        hcl_shift = r["base", 3]
        if (r[62, "peak"] < 4 and r[70, "peak"] < 4 and r[1002, 2] < 0.02) or abs(r["base", 3]) > 0.05:
            r = anHCl[1](d, init, deps)
            ANALYSIS.append(r)
        elif r[62, "peak"] < 4:
            r = anHCl[2](d, init, deps)
            ANALYSIS.append(r)
        hcl_adjust = r["base", 3]
        
        goodLCT = abs(hcl_adjust) < 0.01 and sigma0 < 0.005
        
        #  Reassign frequency axis to lie on FSR-spaced comb
        if goodLCT:
            i0 = argmin(abs(d.fitData["freq"] - f70))
            f0 = d.fitData["freq"][i0]
            while (f0 - f70) < -0.5*fsr:
                f0 += fsr
            while (f0 - f70) > 0.5*fsr:
                f0 -= fsr
            sigma0 = d.groupStdDevs["waveNumber"][i0]
            #print "%2d %8.5f %8.5f" % (i0, f0 - f70, sigma0)
            d.waveNumber = f0 + fsr*round_((d.waveNumber - f0)/fsr)
            d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
            d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
            d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
            d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes)) 

            if (r[62, "peak"] < 4 and r[70, "peak"] < 4 and r[1002, 2] < 0.02) or abs(r["base", 3]) > 0.05:
                r = anHCl[4](d, init, deps)
                ANALYSIS.append(r)
            elif r[62, "peak"] < 4:
                r = anHCl[5](d, init, deps)
                ANALYSIS.append(r) 
            else:
                r = anHCl[3](d, init, deps)
                ANALYSIS.append(r) 
            
        res = r["std_dev_res"]
        baseline_level = r["base", 0]
        baseline_slope = r["base", 1]
        hcl_adjust = r["base", 3]
        peak62 = r[62, "peak"]
        str62 = r[62, "strength"]
        y62 = r[62, "y"]
        base70 = r[70, "base"]
        peak70 = r[70, "peak"]
        str70 = r[70, "strength"]
        r[70, "base"]
        y70 = r[70, "y"]
        ch4_ampl = r[1002, 2]

        h2o_a_conc_raw = h2o_slin * str62
        ch4_conc_raw = 100 * ch4_ampl
        hcl_conc_raw = hcl_lin * str70
        hcl_conc = hcl_conc_raw + ch4_hcl_lin * ch4_ampl + h2o_hcl_lin * peak62
        #ch3oh_conc = 13 * r[1003, 2]    Removed 3 May 2019
        c2h4_conc = 998 * r[1003, 2]   # 140 Torr, 45 C ethylene spline created 2 May 2019
        if abs(c2h4_conc) > 2.0 or abs(ch3oh_conc) > 1.0:
            hcl_adjust = 0.0
            
        if goodLCT and sigma0 < 0.005:
            pzt3_adjust = (f70-f0)*pzt_per_fsr/fsr
        else:
            pzt3_adjust = 0.0

    if (d["spectrumId"] == 63) and (d["ngroups"] < spectrum_min_groups):
        incomplete_spectrum = 1
        r = anHCl[6](d, init, deps)
        ANALYSIS.append(r)
        hcl_adjust = 0.0

    cal = ((d.subschemeId & 4096) != 0) & (d.uncorrectedAbsorbance > 0.1)
    if any(cal):
        pzt3_mean = mean(d.pztValue[cal])
        pzt3_stdev = std(d.pztValue[cal])

    if r != None:
        IgnoreThis = False
        if last_time != None:
            interval = r["time"] - last_time
        else:
            interval = 0
        last_time = r["time"]
        ignore_count = max(0, ignore_count - 1)
    else:
        IgnoreThis = True


    if (ignore_count ==0) and not IgnoreThis:   # and not bad_baseline:
        RESULT = {"res":res,"degraded_performance":degraded_performance,"baseline_level":baseline_level,"baseline_slope":baseline_slope,"base70":base70,
                "peak62":peak62,"str62":str62,"y62":y62,"peak70":peak70,"str70":str70,"y70":y70,"ch4_ampl":ch4_ampl,
                "hcl_shift":hcl_shift,"hcl_adjust":hcl_adjust,"hcl_conc_raw":hcl_conc_raw,"hcl_conc":hcl_conc,
                "h2o_a_conc_raw":h2o_a_conc_raw,"ch4_conc_raw":ch4_conc_raw,
                "delta_loss_hcl":delta_loss_hcl, "delta_loss_h2o":delta_loss_h2o,
                "ngroups":d["ngroups"],"numRDs":d["datapoints"],"interval":interval,
                "baseMean":1000*baseMean,"baseStdev":1000*baseStdev,
                "baseLinIntercept":baseLinIntercept,"baseLinSlope":baseLinSlope,
                "baseQuadIntercept":baseQuadIntercept,"baseQuadSlope":baseQuadSlope,"baseQuadCurvature":baseQuadCurvature,
                "noBaseline":noBaseline,"incomplete_spectrum":incomplete_spectrum,
                "minBasePoints":minBasePoints,"maxBasePoints":maxBasePoints,"meanBasePoints":meanBasePoints,
                "ch3oh_conc":ch3oh_conc,"c2h4_conc":c2h4_conc,
                "pzt3_adjust":pzt3_adjust,"pzt_per_fsr":pzt_per_fsr,"goodLCT":goodLCT,
                "pzt3_mean":pzt3_mean,"pzt3_stdev":pzt3_stdev,# "threshold":current_threshold
                }
        RESULT.update({"species":d["spectrumId"],"fittime":time.clock()-tstart,
                    "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                    "das_temp":dasTemp})
        RESULT.update(d.sensorDict)

    # Determine if we can raise the threshold to the original value
    if not(disable_dynamic_threshold) and (rd_rate >= min_rd_rate) and np.all(d.uncorrectedAbsorbance > 0.0) and np.all(d.uncorrectedAbsorbance < 0.001*safe_loss_level):
        if current_threshold != original_rd_threshold:
            degraded_performance = 0
            Driver.wrDasReg("SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER", original_rd_threshold)
            Driver.wrFPGA("FPGA_RDMAN", "RDMAN_THRESHOLD", original_rd_threshold)
            Log("Fitter changes threshold to %d" % original_rd_threshold)

