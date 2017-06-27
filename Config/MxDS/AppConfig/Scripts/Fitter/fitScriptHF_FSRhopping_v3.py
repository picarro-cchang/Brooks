#  Fit script for experimental low cost HF analyzer using FSR hopping and no WLM
#  Version 1 started 13 May 2015 by hoffnagle
#  2015 0714:  resumed with new provision for HF cell to provide stable absolute frequency reference
#  2016 0407:  change frequency assignment to use Sze's new targetted fsr hopping

from numpy import angle, asarray, argmin, argsort, array, arange, concatenate, diff, exp, max, mean, median, pi, std, sqrt, digitize, polyfit, polyval, real, imag, round_
from numpy.linalg import solve
from collections import deque
import os.path
import time

def initialize_Baseline():
    init["base",0] = baseline_level
    init["base",1] = baseline_slope
    init[1000,0] = A0
    init[1000,1] = Nu0
    init[1000,2] = Per0
    init[1000,3] = Phi0
    init[1001,0] = A1
    init[1001,1] = Nu1
    init[1001,2] = Per1
    init[1001,3] = Phi1
    
def initialize_Reference_Baseline():
    init[1000,0] = RA0
    init[1000,1] = RNu0
    init[1000,2] = RPer0
    init[1000,3] = RPhi0
    init[1001,0] = RA1
    init[1001,1] = RNu1
    init[1001,2] = RPer1
    init[1001,3] = RPhi1
    
if INIT:
    fname = os.path.join(BASEPATH,r"./MADS/spectral library MADS v3_2.ini")
    loadSpectralLibrary(fname)
    spectrParams = getInstrParams(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_FSR.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_fsr_hopping.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']
    
    center77 = spectrParams['peak77']['center']
    
    baseline_level = instrParams['Baseline_level']
    baseline_slope = instrParams['Baseline_slope']
    A0 = instrParams['Sine0_ampl']
    Nu0 = instrParams['Sine0_freq']
    Per0 = instrParams['Sine0_period']
    Phi0 = instrParams['Sine0_phase']
    A1 = instrParams['Sine1_ampl']
    Nu1 = instrParams['Sine1_freq']
    Per1 = instrParams['Sine1_period']
    Phi1 = instrParams['Sine1_phase']

    Ra0 = instrParams['Reference_Baseline_level']
    Ra1 = instrParams['Reference_Baseline_slope']
    Ra2 = instrParams['Reference_Baseline_curvature']
    RA0 = instrParams['Reference_Sine0_ampl']
    RNu0 = instrParams['Reference_Sine0_freq']
    RPer0 = instrParams['Reference_Sine0_period']
    RPhi0 = instrParams['Reference_Sine0_phase']
    RA1 = instrParams['Reference_Sine1_ampl']
    RNu1 = instrParams['Reference_Sine1_freq']
    RPer1 = instrParams['Reference_Sine1_period']
    RPhi1 = instrParams['Reference_Sine1_phase']
    
    sigma_ref = instrParams['Reference_Gaussian']
    y_ref = instrParams['Reference_y']
    z_ref = instrParams['Reference_z']
    ref_offset = instrParams["Reference_offset"]
        
    anHF = []
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/HFonly.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/HF+H2O FC FY.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/HF+H2O FC VY.ini")))
    
    last_time = None
    ignore = 5
    last_shift = 1.0

tstart = time.clock()
init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
P = d["cavitypressure"]
T = d["cavitytemperature"]

if d["spectrumId"] == 60:                
        d.badRingdownFilter("ratio1",minVal=0.1,maxVal=65535)
        d.sparse(maxPoints=400,width=0.1,height=50000000.0,xColumn="fsrIndex",yColumn="ratio1",outlierThreshold=3.0)
        d.evaluateGroups(["fsrIndex","ratio1","fineLaserCurrent"])
        d.defineFitData(freq=d.groupMeans["fsrIndex"],loss=d.groupMeans["ratio1"],sdev=1/sqrt(d.groupSizes))
        modeLaserCurrent = d.groupMeans["fineLaserCurrent"]
        i0 = argmin(abs(modeLaserCurrent-32768))
        j0 = argmin(d.fitData["loss"])
        gaps = sum(diff(d.fitData["freq"])-1)
        mode_span = 1 + d.fitData["freq"][-1]
        d.fitData["freq"] = center77+(d.fitData["freq"][i0]-d.fitData["freq"])*fsr
        
        inRange = (d.fitData["freq"] >= 7823.5) & (d.fitData["freq"] <= 7824.0)
        pointsInRange = sum(inRange)
        good = True

        r = None

        if pointsInRange < 6:
            ignore += 1
            
        if ignore:
            ignore -= 1

        else:
            initialize_Reference_Baseline()
            init[76,4] = sigma_ref                #  Fit reference cell spectrum with empirical line shape
            init[76,3] = z_ref
            init[76,2] = y_ref
            init["base",0] = Ra0
            init["base",1] = Ra1
            init["base",2] = Ra2
            init["base",3] = fsr*(j0-i0)
            #deps.setDep(("base",1),("base",0),Ra1/Ra0,0)
            #deps.setDep(("base",2),("base",0),Ra2/Ra0,0)
            if abs(last_shift) > 0.01:
                freq_locked = 0
                r = anHF[0](d,init,deps)
                ANALYSIS.append(r)
            else:
                freq_locked = 1
                r = anHF[0](d,init,deps)  
                ANALYSIS.append(r)
            ref_shift = r["base",3]-ref_offset
            ref_peak = r[76,"peak"]
            ref_base = r["base",0]
            ref_slope = r["base",1]
            ref_res = r["std_dev_res"]
            
            if freq_locked and abs(ref_shift) < 0.011:
                pzt1_adjust = -ref_shift*pzt_per_fsr/fsr
            else:
                pzt1_adjust = 0.0

            d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=15.0)
            d.sparse(maxPoints=200,width=0.1,height=100000.0,xColumn="fsrIndex",yColumn="uncorrectedAbsorbance",outlierThreshold=3.0)
            d.evaluateGroups(["fsrIndex","uncorrectedAbsorbance"])
            d.defineFitData(freq=d.groupMeans["fsrIndex"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
            d.fitData["freq"] = center77+(d.fitData["freq"][i0]-d.fitData["freq"])*fsr
            deps = Dependencies()
            init = InitialValues()
            initialize_Baseline()
            init["base",3] = ref_shift
     
            r = anHF[1](d,init,deps)  
            ANALYSIS.append(r)
            if r[77,"peak"] > 10:
                r = anHF[2](d,init,deps)  
                ANALYSIS.append(r)
            hf_shift = r["base",3]
            str77 = r[77,"strength"]
            peak77 = r[77,"peak"]
            str79 = r[79,"strength"]
            peak79 = r[79,"peak"]
            y77 = r[77,"y"]
            hf_base = r["base",0]
            hf_slope = r["base",1]
            hf_res = r["std_dev_res"]
     
            hf_conc_raw = 0.1554*(70.0/P)*str77
            h2o_conc_raw = 0.2835*(70.0/P)*str79
            
            if hf_res > 10:
                msg = "HF residual > 10 ppb/cm"
                good = False
            
            if ref_res > 300:
                msg = "Reference residual > 300 ppb/cm"
                good = False            
            
            now = time.clock()
            fit_time = now-tstart
            if last_time != None:
                interval = r["time"]-last_time
            else:
                interval = 0
            last_time = r["time"]

            if good:
                last_shift = ref_shift
                RESULT = {"hf_res":hf_res,"hf_conc_raw":hf_conc_raw,
                          "str77":str77,"peak77":peak77,"y77":y77,
                          "hf_base":hf_base,"hf_slope":hf_slope,
                          "hf_shift":hf_shift,"freq_locked":freq_locked,
                          "gaps":gaps,"mode_span":mode_span,
                          "ref_shift":ref_shift,"ref_peak":ref_peak,"ref_base":ref_base,"ref_slope":ref_slope,"ref_res":ref_res,
                          "hf_groups":d["ngroups"],"hf_rds":d["datapoints"],
                          "hf_fit_time":fit_time,"hf_interval":interval,"pointsInRange":pointsInRange,
                          "h2o_conc_raw":h2o_conc_raw,"str79":str79,"peak79":peak79,
                          "pzt_per_fsr":pzt_per_fsr,"pzt1_adjust":pzt1_adjust,"spectrumId":d["spectrumId"]
                          }
                RESULT.update(d.sensorDict)
                RESULT.update({"cavity_pressure":P,"cavity_temperature":T})
            else:
                print msg      