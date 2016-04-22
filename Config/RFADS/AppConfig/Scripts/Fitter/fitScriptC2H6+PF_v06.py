#  Fit script for experimental log-wavelength ethane analyzer.
#  Started Feb 2014; resumed May 2015
#   2 Jun 2015:  Added fitter for the CFADS methane line for two-laser instrument.

from numpy import * 
import os.path
import time
import cPickle
from struct import pack
from Host.Common.EventManagerProxy import Log

def outlierFilter(x,threshold,minPoints=2):
    """ Return Boolean array giving points in the vector x which lie
    within +/- threshold * std_deviation of the mean. The filter is applied iteratively
    until there is no change or unless there are minPoints or fewer remaining"""
    good = ones(x.shape,bool_)
    order = list(x.argsort())
    while len(order)>minPoints:
        maxIndex = order.pop()
        good[maxIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[maxIndex]-mu)>=(threshold*sigma):
            continue
        good[maxIndex] = 1
        minIndex = order.pop(0)
        good[minIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[minIndex]-mu)>=(threshold*sigma):
            continue
        good[minIndex] = 1
        break
    return good
    
def expAverage(xavg,x,n,dxMax):
    if xavg is None: return x
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)<dxMax: return y
    elif y>xavg: return xavg+dxMax
    else: return xavg-dxMax

def initialize_CH4_Baseline():
    init["base",0] = CH4_baseline_level
    init["base",1] = CH4_baseline_slope
    init[1000,0] = CH4_A0
    init[1000,1] = CH4_Nu0
    init[1000,2] = CH4_Per0
    init[1000,3] = CH4_Phi0
    init[1001,0] = CH4_A1
    init[1001,1] = CH4_Nu1
    init[1001,2] = CH4_Per1
    init[1001,3] = CH4_Phi1

    
def initialize_C2H6_Baseline():
    init["base",0] = C2H6_baseline_level
    init["base",1] = C2H6_baseline_slope
    init[1000,0] = C2H6_A0
    init[1000,1] = C2H6_Nu0
    init[1000,2] = C2H6_Per0
    init[1000,3] = C2H6_Phi0
    init[1001,0] = C2H6_A1
    init[1001,1] = C2H6_Nu1
    init[1001,2] = C2H6_Per1
    init[1001,3] = C2H6_Phi1

if INIT:
    fname = os.path.join(BASEPATH,r"./Ethane/spectral library 5950wvn v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./Ethane/cFADS-1 CH4 v2_1 2008 0304.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./Ethane/cFADS-1 CH4 FC VY v2_0 2008 0304.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./Ethane/cFADS-1 CH4 FC FY v2_0 2008 0304.ini")))    
    
    anC2H6 = []
    anC2H6.append(Analysis(os.path.join(BASEPATH,r"./Ethane/c2h6_wide_v2_1.ini")))
    anC2H6.append(Analysis(os.path.join(BASEPATH,r"./Ethane/c2h6_wide_FCFY_v2_1.ini")))
    anC2H6.append(Analysis(os.path.join(BASEPATH,r"./Ethane/c2h6_only_FCFY_v2_1.ini")))
    anC2H6.append(Analysis(os.path.join(BASEPATH,r"./Ethane/c2h6+c2h4+nh3_wide_v2_1.ini")))

#  Baseline parameters
    
    CH4_baseline_level = instrParams['CFADS_Baseline_level']
    CH4_baseline_slope = instrParams['CFADS_Baseline_slope']
    CH4_A0 = instrParams['CFADS_Sine0_ampl']
    CH4_Nu0 = instrParams['CFADS_Sine0_freq']
    CH4_Per0 = instrParams['CFADS_Sine0_period']
    CH4_Phi0 = instrParams['CFADS_Sine0_phase']
    CH4_A1 = instrParams['CFADS_Sine1_ampl']
    CH4_Nu1 = instrParams['CFADS_Sine1_freq']
    CH4_Per1 = instrParams['CFADS_Sine1_period']
    CH4_Phi1 = instrParams['CFADS_Sine1_phase']
    
    C2H6_baseline_level = instrParams['C2H6_Baseline_level']
    C2H6_baseline_slope = instrParams['C2H6_Baseline_slope']
    C2H6_A0 = instrParams['C2H6_Sine0_ampl']
    C2H6_Nu0 = instrParams['C2H6_Sine0_freq']
    C2H6_Per0 = instrParams['C2H6_Sine0_period']
    C2H6_Phi0 = instrParams['C2H6_Sine0_phase']
    C2H6_A1 = instrParams['C2H6_Sine1_ampl']
    C2H6_Nu1 = instrParams['C2H6_Sine1_freq']
    C2H6_Per1 = instrParams['C2H6_Sine1_period']
    C2H6_Phi1 = instrParams['C2H6_Sine1_phase']
    
#  Cross-talk and offset parameters from step tests
    ch4_H1 = instrParams['CH4_water_linear']
    ch4_H1M1 = instrParams['CH4_methane_water_bilinear']
    c2h6_off = instrParams['C2H6_offset']
    c2h6_M1 = instrParams['C2H6_methane_linear']
    c2h6_H1 = instrParams['C2H6_water_linear']
    c2h6_H1M1 = instrParams['C2H6_methane_water_bilinear']
    
#  Globals
    ch4_avg = 0.0
    c2h6_avg = 0.0
    ratio_avg = 0.0

    last_time = None
    
init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.30,maxVal=20.0)
#d.wlmSetpointFilter(maxDev=0.001,sigmaThreshold=4)
d.sparse(maxPoints=20000,width=0.005,height=400000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))

tstart = time.clock()
RESULT = {}
r = None

inCFADS = (d.fitData["freq"] >= 6056.8) & (d.fitData["freq"] <= 6057.4)
goodCFADS = sum(inCFADS)
inLong = (d.fitData["freq"] >= 5946.4) & (d.fitData["freq"] <= 5947.0)
goodLong = sum(inLong)
P = d["cavitypressure"]

if d["spectrumId"]==170 and goodCFADS>9 and goodLong>12:
    initialize_CH4_Baseline()               #  First fit methane high speed, high precision CFADS line
    r = anCH4[0](d,init,deps)
    ANALYSIS.append(r)
    ch4_vy = r[1002,5]
    vch4_conc_ppmv = 10*r[1002,2]
    ch4_shift = r["base",3]
#  Polishing step with fixed center, variable y if line is strong and shift is small
    if (r[1002,2] > 0.005) and (abs(ch4_shift) <= 0.07):
        init["base",3] = ch4_shift
        ch4_adjust = ch4_shift
        r = anCH4[1](d,init,deps)
        ANALYSIS.append(r)
#  Polishing step with fixed center and y if line is weak or shift is large
    else:    
        init["base",3] = 0.0
        ch4_adjust = 0.0
        init[1002,5] = 1.08
        r = anCH4[2](d,init,deps)
        ANALYSIS.append(r)
    
    CFADS_ch4_amp = r[1002,2]
    ch4_conc_raw = 10*r[1002,2]
    CFADS_ch4_y = r[1002,5]
    CFADS_base = r["base",0]
    ch4_adjconc_ppmv = CFADS_ch4_y*ch4_conc_raw*(140.0/P)
    ch4_splinemax = r[1002,"peak"]
    ch4_peakvalue = ch4_splinemax+CFADS_base
    ch4_peak_base = ch4_peakvalue-CFADS_base
    ch4_conc_ppmv_final = ch4_peak_base/216.3
    
    #wd_ratio_CFADS_CH4 = 1.0 + h2o_conc_pct*(H1_wd_CFADS_CH4 + H2_wd_CFADS_CH4*h2o_conc_pct)
    #ch4_splinemax_dry = ch4_splinemax/wd_ratio_CFADS_CH4
    #ch4_conc_ppmv_final_dry = ch4_conc_ppmv_final/wd_ratio_CFADS_CH4 
    
    ch4_res = r["std_dev_res"]

    init = InitialValues()
    initialize_C2H6_Baseline()     #  Next fit water and ethane with methane preset from CFADS region
    init[1002,2] = 0.009601*ch4_conc_ppmv_final
    r = anC2H6[0](d,init,deps)
    ANALYSIS.append(r)

    c2h6_adjust = c2h6_shift = r["base",3]
    vy_h2o = r[1,"y"]

    if (r[1,"peak"]<3 and r[1002,2]<0.03 and r[1003,2]<0.002) or abs(c2h6_shift)>0.05:
        r = anC2H6[1](d,init,deps)
        ANALYSIS.append(r)
        c2h6_adjust = 0.0

    if (r[1002,2]>0.03 or r[1003,2]>0.002) and (r[1,"peak"]<3 or abs(vy_h2o-0.523)>0.2):
        c2h6_adjust = c2h6_shift
        init["base",3] = c2h6_adjust
        r = anC2H6[1](d,init,deps)
        ANALYSIS.append(r)

    baseline_shift = r["base",0]-C2H6_baseline_level
    slope_shift = r["base",1]-C2H6_baseline_slope
    y_h2o = r[1,"y"]
    h2o_peak = r[1,"peak"]
    str_1 = r[1,"strength"]
    residuals = r["std_dev_res"]
    #ch4_from_c2h6 = 100*r[1002,2]

    init["base",0] = r["base",0]
    init["base",3] = c2h6_adjust
    init[1,"strength"] = str_1
    init[1,"y"] = y_h2o
    r = anC2H6[2](d,init,deps)
    ANALYSIS.append(r)
    
    h2o_conc = 38.7*h2o_peak
    c2h6_conc = 100*r[1003,2]
    
#  Apply cross-talk and offset corrections

    c2h6_conc_corrected = c2h6_conc + c2h6_off + c2h6_M1*ch4_conc_ppmv_final + c2h6_H1*h2o_conc  + c2h6_H1M1*h2o_conc*ch4_conc_ppmv_final
    c2ratio = c2h6_conc_corrected/ch4_conc_ppmv_final
    ch4_avg = expAverage(ch4_avg,ch4_conc_ppmv_final,3,0.1)
    c2h6_avg = expAverage(c2h6_avg,c2h6_conc_corrected,3,0.1)
    ratio_avg = expAverage(ratio_avg,c2ratio,3,0.1)

#  Statistics
    
    f = d.waveNumber
    l = 1000*d.uncorrectedAbsorbance
    
    topper = (f >= 5946.52) & (f <= 5946.54)  #  Measure ethane peak height
    top_loss = l[topper]
    freq = f[topper]
    ntopper = len(l[topper])
    if ntopper > 0:
        good_topper = outlierFilter(top_loss,4)
        tiptop = mean(top_loss[good_topper])
        tipstd = std(top_loss[good_topper])
        ntopper = len(top_loss[good_topper])
        ftopper = mean(freq[good_topper])
    else:
        tiptop = 0.0
        tipstd = 0.0

    topper = (f >= 5946.436) & (f <= 5946.456)  #  Measure low frequency baseline
    top_loss = l[topper]
    freq = f[topper]
    nbase1 = len(l[topper])
    if nbase1 > 0:
        good_topper = outlierFilter(top_loss,4)
        base1 = mean(top_loss[good_topper])
        base1std = std(top_loss[good_topper])
        nbase1 = len(top_loss[good_topper])
        fbase1 = mean(freq[good_topper])
    else:
        base1 = 0.0
        base1std = 0.0
        
    r = anC2H6[3](d,init,deps)   #  Post-fit for interferences
    ANALYSIS.append(r)
    c2h4_conc = 100*r[1004,2]
    nh3_conc = 50*r[1005,2]
    c2h6_PF = 100*r[1003,2] + c2h6_off + c2h6_M1*ch4_conc_ppmv_final + c2h6_H1*h2o_conc  + c2h6_H1M1*h2o_conc*ch4_conc_ppmv_final
    c2ratio_PF = c2h6_PF/ch4_conc_ppmv_final
        
now = time.clock()
fit_time = now-tstart    
if r != None:
    ignoreThis = False
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]        
else:
    ignoreThis = True

if not ignoreThis:     
    RESULT = {"baseline_shift":baseline_shift,"slope_shift":slope_shift,"species":d["spectrumId"],
              "h2o_peak":h2o_peak,"str_1":str_1,"y_h2o":y_h2o,"vy_h2o":vy_h2o,
              "h2o_conc":h2o_conc,"c2h6_conc":c2h6_conc,"c2ratio":c2ratio,
              "c2h6_conc_corrected":c2h6_conc_corrected,#"ch4_from_c2h6":ch4_from_c2h6,
              "ntopper":ntopper,"tiptop":tiptop,"tipstd":tipstd,"nbase1":nbase1,"base1":base1,"base1std":base1std,
              "ch4_vy":ch4_vy,"ch4_shift":ch4_shift,"ch4_adjust":ch4_adjust,"CFADS_ch4_amp":CFADS_ch4_amp,"ch4_avg":ch4_avg,
              "CFADS_ch4_y":CFADS_ch4_y,"CFADS_base":CFADS_base,"ch4_splinemax":ch4_splinemax,"ch4_res":ch4_res,
              "ch4_conc_ppmv_final":ch4_conc_ppmv_final,"cavity_pressure":P,"c2h6_avg":c2h6_avg,"ratio_avg":ratio_avg,
              #"ch4_splinemax_dry":ch4_splinemax_dry,"ch4_conc_ppmv_final_dry":ch4_conc_ppmv_final_dry,            
              "fit_time":fit_time,"interval":interval,"groups":d["ngroups"],"points":d["datapoints"],
              "ch4_avg":ch4_avg,"c2h6_avg":c2h6_avg,"ratio_avg":ratio_avg,
              "PF_c2h4_conc":c2h4_conc,"PF_nh3_conc":nh3_conc,"PF_c2h6_conc":c2h6_PF,"PF_c2_ratio":c2ratio_PF,
              "c2h6_shift":c2h6_shift,"c2h6_adjust":c2h6_adjust,"residuals":residuals}
    RESULT.update(d.sensorDict)