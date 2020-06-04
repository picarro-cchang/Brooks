#  Experimental fit script to test Laser Current Tuning with the CFADS CO2 line at 6237.4 wvn
#  2012 1108:  First draft
#  2013 0301:  Major revision to include lessons learned from "seventino"
#  2013 0619:  Major revision to add water vapor measurement at 6057.8 wvn
#  2013 0709:  Major revision to add methane measurment (bispline!)
#  2013 0724:  Major revision -- change methane model from bispline to Galatry!
#  2014 0326:  Change algorithm for longitudinal mode assignment to increase capture range
#  2018 0806:  Special-purpose script to measure y-parameters of CO2 lines 6058.2 and 6237.4 with simultaneous Baratron data
#  2018 0919:  Added real-time "spectroscopic manometer"
#  2018 1016:  Fitter for CFADS instrument again, incorporating lessons learned with Baratron

import os.path
import time
from numpy import *
from copy import copy
    
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
    
def initialize_CO2_Baseline():
    init["base",0] = CO2_baseline_level
    init["base",1] = CO2_baseline_slope
    init[1000,0] = CO2_A0
    init[1000,1] = CO2_Nu0
    init[1000,2] = CO2_Per0
    init[1000,3] = CO2_Phi0
    init[1001,0] = CO2_A1
    init[1001,1] = CO2_Nu1
    init[1001,2] = CO2_Per1
    init[1001,3] = CO2_Phi1

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
    
if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library CFADS-xx high methane v4.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_CFADS.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']
    
    optDict = eval("dict(%s)" % OPTION)

    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CH4_std_galatry VCVY v1_2.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CH4_std_galatry VCVY v1_2.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CH4_std_galatry FCFY v1_1.ini")))    
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/Peak14_only_VY.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/Peak14_only_FC_FY.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/Peak14_only_VY.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/Peak14_only_FC_FY.ini")))

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-xx H2O clean v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-xx H2O clean FCFY v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-xx H2O clean v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-xx H2O clean FCFY v1_1.ini")))
    
#   Globals
    last_time = None
      
#   Baseline parameters

    CH4_baseline_level = instrParams['CH4_Baseline_level']
    CH4_baseline_slope = instrParams['CH4_Baseline_slope']
    CH4_A0 = instrParams['CH4_Sine0_ampl']
    CH4_Nu0 = instrParams['CH4_Sine0_freq']
    CH4_Per0 = instrParams['CH4_Sine0_period']
    CH4_Phi0 = instrParams['CH4_Sine0_phase']
    CH4_A1 = instrParams['CH4_Sine1_ampl']
    CH4_Nu1 = instrParams['CH4_Sine1_freq']
    CH4_Per1 = instrParams['CH4_Sine1_period']
    CH4_Phi1 = instrParams['CH4_Sine1_phase']
    
    CO2_baseline_level = instrParams['CO2_Baseline_level']
    CO2_baseline_slope = instrParams['CO2_Baseline_slope']
    CO2_A0 = instrParams['CO2_Sine0_ampl']
    CO2_Nu0 = instrParams['CO2_Sine0_freq']
    CO2_Per0 = instrParams['CO2_Sine0_period']
    CO2_Phi0 = instrParams['CO2_Sine0_phase']
    CO2_A1 = instrParams['CO2_Sine1_ampl']
    CO2_Nu1 = instrParams['CO2_Sine1_freq']
    CO2_Per1 = instrParams['CO2_Sine1_period']
    CO2_Phi1 = instrParams['CO2_Sine1_phase']
    
#   Collisional broadening parameters

    D14 = instrParams['peak14_Doppler']
    A14 = instrParams['peak14_gamma_air']
    C14 = instrParams['peak14_crossbroadening']
    Y0_14 = instrParams['peak14_y0']
    D61 = instrParams['peak61_Doppler']
    A61 = instrParams['peak61_gamma_air']
    C61 = instrParams['peak61_crossbroadening']
    D75 = instrParams['peak75_Doppler']
    A75 = instrParams['peak75_gamma_air']
    S75 = instrParams['peak75_selfbroadening']
    
    M1 = instrParams['methane_linear']
    
#   Initialize values
    co2_shift = 0
    co2_adjust = 0
    y14 = Y0_14
    peak14 = 0
    str14 = 0
    base14 = 0
    co2_residuals = 0
    fsr_shift_co2 = 0
    fsr_y14 = 1.8785
    fsr_z14 = 0.7499
    fsr_peak14 = 0
    fsr_str14 = 0
    corrected_fsr_strength14 = 0
    normalized_fsr_strength14 = 0
    fsr_base14 = 0
    co2_residuals_fsr = 0
    pzt1_adjust = 0.0
    pzt1 = 0
    pspec = 140
    paveraged = 140
    
    ch4_shift = 0
    ch4_adjust = 0
    y61 = 0.96929
    peak61 = 0
    str61 = 0
    base61 = 0
    ch4_residuals = 0
    fsr_shift_ch4 = 0
    fsr_y61 = 0.96929
    fsr_peak61 = 0
    fsr_str61 = 0
    corrected_fsr_strength61 = 0
    normalized_fsr_strength61 = 0
    scaled_fsr_strength61 = 0
    fsr_base61 = 0
    ch4_residuals_fsr = 0
    ch4_conc_precal = 0
    pzt2_adjust = 0.0
    pzt2 = 0
    ch4_interval = 0

    h2o_shift = 0
    h2o_adjust = 0
    y75 = 0.83324
    peak75 = 0
    str75 = 0
    base75 = 0
    h2o_residuals = 0
    fsr_shift_h2o = 0
    fsr_y75 = 0.83324
    fsr_peak75 = 0
    fsr_str75 = 0
    corrected_fsr_strength75 = 0
    normalized_fsr_strength75 = 0
    fsr_base75 = 0
    h2o_residuals_fsr = 0
    pzt4_adjust = 0.0
    pzt4 = 0
 
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = copy(DATA)
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.sparse(maxPoints=1000,width=0.01,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])

d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))
T = d["cavitytemperature"] + 273.15
species = (d.subschemeId & 0x3FF)[0]
tstart = time.clock()
RESULT = {}
r = None

if species == 10:
    pzt1 = mean(d.pztValue)
    initialize_CO2_Baseline()
    init[76,"strength"] = 0.0047*fsr_str75
    init[1002,2] = 0.0001*ch4_conc_precal 
    r = anCO2[0](d,init,deps)                  #  Fit with frequency from WLM.  CFADS+methane spline+peak76
    ANALYSIS.append(r)
    co2_shift = r["base",3]
    y14 = r[14,"y"]
    peak14 = r[14,"peak"]
    str14 = r[14,"strength"]
    if peak14 < 10 or abs(co2_shift) > 0.05:
        r = anCO2[1](d,init,deps)
        ANALYSIS.append(r)
    co2_adjust = r["base",3]
    base14 = r[14,"base"]
    co2_residuals = r["std_dev_res"]
    
    if r[14,"peak"] < -10 or r[14,"peak"] > 20000  > 0.5: 
        goodLCT = False
    else:
        goodLCT = True
    if goodLCT:
        d.fitData["freq"] = 6237.408 + fsr*round_((d.fitData["freq"] + co2_adjust - 6237.408)/fsr)
        
        if peak14 > 10:
            r = anCO2[2](d,init,deps)
        else:
            r = anCO2[3](d,init,deps)
        ANALYSIS.append(r)
        fsr_shift_co2 = r["base",3]
        pzt1_adjust = -fsr_shift_co2*pzt_per_fsr/fsr
        fsr_y14 = r[14,"y"]
        fsr_z14 = r[14,"z"]
        fsr_peak14 = r[14,"peak"]
        fsr_str14 = r[14,"strength"]
        fsr_base14 = r[14,"base"]
        co2_residuals_fsr = r["std_dev_res"]
        
        str75_140 = (140.0/paveraged)*fsr_str75
        ydry = fsr_y14 - (140.0/760.0)*(C14*str75_140)/D14
        pspec = 140.0*ydry/Y0_14
        paveraged = expAverage(paveraged,pspec,100,0.2)
        y14_nominal = (pspec/760.0)*(A14 + C14*fsr_str75)/D14
        normalized_fsr_strength14 = fsr_str14*y14_nominal/fsr_y14
        corrected_fsr_strength14 = (140.0/pspec)*normalized_fsr_strength14
        normalized_fsr_strength14 = (paveraged/pspec)*normalized_fsr_strength14   #  Reduces measurement and fitting noise

if d["spectrumId"]==11 and d["ngroups"]>5:
    pzt4 = mean(d.pztValue)
    initialize_CH4_Baseline()
    init[1002,2] = 0.01*ch4_conc_precal
    r = anH2O[0](d,init,deps)                  #  Standard CFADS fit with methane spline
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    y75 = r[75,"y"]
    if r[75,"peak"] < 10 or abs(r["base",3]) >= 0.05:
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
    h2o_residuals = r["std_dev_res"]
    base75 = r[75,"base"]
    peak75 = r[75,"peak"]
    str75 = r[75,"strength"]
    h2o_adjust = r["base",3]
    h2o_conc = peak75 * 0.01002

    if r[75,"peak"] < -10 or r[75,"peak"] > 10000: 
        goodLCT = False
    else:
        goodLCT = True
    
    if goodLCT:
        d.fitData["freq"] = 6057.8 + fsr*round_((d.fitData["freq"] + h2o_adjust - 6057.8)/fsr)
        
        if peak75>10:
            r = anH2O[2](d,init,deps)
        else:
            r = anH2O[3](d,init,deps)
        ANALYSIS.append(r)
        fsr_shift_h2o = r["base",3]
        pzt4_adjust = -fsr_shift_h2o*pzt_per_fsr/fsr
        fsr_y75 = r[75,"y"]
        fsr_peak75 = r[75,"peak"]
        fsr_str75 = r[75,"strength"]
        fsr_base75 = r[75,"base"]
        h2o_residuals_fsr = r["std_dev_res"]
        
        str75_140 = (140.0/paveraged)*fsr_str75
        y75_nominal = (pspec/760.0)*(A75 + S75*str75_140)/D75
        normalized_fsr_strength75 = fsr_str75*y75_nominal/fsr_y75
        corrected_fsr_strength75 = (140.0/pspec)*normalized_fsr_strength75
        normalized_fsr_strength75 = (paveraged/pspec)*normalized_fsr_strength75
 
if d["spectrumId"]==25 and d["ngroups"]>5:
    pzt2 = mean(d.pztValue)
    initialize_CH4_Baseline()
    r = anCH4[0](d,init,deps)
    ANALYSIS.append(r)
    y61 = r[61,"y"]
    ch4_shift = r["base",3]
    str61 = r[61,"strength"]
    peak61 = r[61,"peak"]
    ch4_conc_precal = 0.00320*str61
    base61 = r[61,"base"]
    ch4_residuals = r["std_dev_res"]
    if (peak61 > 5) and (abs(ch4_shift) <= 0.07) and (abs(y61-0.95) < 0.2):
        ch4_adjust = ch4_shift
    else:
        ch4_adjust = 0.0

    if r[61,"peak"] < -10 or r[61,"peak"] > 10000: 
        goodLCT = False
    else:
        goodLCT = True

    if goodLCT:
        d.fitData["freq"] = 6057.0863 + fsr*round_((d.fitData["freq"] + ch4_adjust - 6057.0863)/fsr)
        
        if (peak61 > 5) and (abs(ch4_shift) <= 0.07) and (abs(y61-0.95) < 0.2):
            r = anCH4[1](d,init,deps)
        else:
            r = anCH4[2](d,init,deps)
        ANALYSIS.append(r)
        fsr_y61 = r[61,"y"]
        fsr_shift_ch4 = r["base",3]
        pzt2_adjust = -fsr_shift_ch4*pzt_per_fsr/fsr
        fsr_str61 = r[61,"strength"]
        fsr_peak61 = r[61,"peak"]
        fsr_base61 = r[61,"base"]
        ch4_residuals_fsr = r["std_dev_res"]
        
        str75_140 = (140.0/paveraged)*fsr_str75
        y61_nominal = (pspec/760.0)*(A61 + C61*str75_140)/D61
        normalized_fsr_strength61 = fsr_str61*y61_nominal/fsr_y61
        corrected_fsr_strength61 = (140.0/pspec)*normalized_fsr_strength61
        normalized_fsr_strength61 = (paveraged/pspec)*normalized_fsr_strength61
        scaled_fsr_strength61 = (140.0/paveraged)*fsr_str61
        ch4_conc_precal = M1*corrected_fsr_strength61
       
now = time.clock()
fit_time = now-tstart
if r != None:
    IgnoreThis = False
    if (last_time != None) and (d["spectrumId"]==25):
        ch4_interval = r["time"]-last_time
    if d["spectrumId"]==25 :
        last_time = r["time"]
else:
    IgnoreThis = True
   
if not IgnoreThis:    
    RESULT = {"co2_shift":co2_shift,"co2_adjust":co2_adjust,"peak14":peak14,"y14":y14,"co2_residuals":co2_residuals,
            "str14":str14,"fsr_str14":fsr_str14,"co2_residuals_fsr":co2_residuals_fsr,
            "fsr_shift_co2":fsr_shift_co2,"fsr_peak14":fsr_peak14,"fsr_y14":fsr_y14,"fsr_z14":fsr_z14,
            "base14":base14,"fsr_base14":fsr_base14,"pspec":pspec,
            "corrected_fsr_strength14":corrected_fsr_strength14,"normalized_fsr_strength14":normalized_fsr_strength14,
            "pzt1_adjust":pzt1_adjust,"pzt1":pzt1,"species":species,"goodLCT":goodLCT,
            "h2o_shift":h2o_shift,"h2o_adjust":h2o_adjust,"peak75":peak75,"y75":y75,"h2o_residuals":h2o_residuals,
            "str75":str75,"fsr_str75":fsr_str75,"h2o_residuals_fsr":h2o_residuals_fsr,
            "fsr_shift_h2o":fsr_shift_h2o,"fsr_peak75":fsr_peak75,"fsr_y75":fsr_y75,
            "base75":base75,"fsr_base75":fsr_base75,"normalized_fsr_strength75":normalized_fsr_strength75,
            "corrected_fsr_strength75":corrected_fsr_strength75,"pzt4_adjust":pzt4_adjust,"pzt4":pzt4,
            "ch4_shift":ch4_shift,"y61":y61,"peak61":peak61,"str61":str61,"scaled_fsr_strength61":scaled_fsr_strength61,
            "ch4_adjust":ch4_adjust,"ch4_residuals":ch4_residuals,"fsr_shift_ch4":fsr_shift_ch4,
            "fsr_peak61":fsr_peak61,"fsr_str61":fsr_str61,"normalized_fsr_strength61":normalized_fsr_strength61,
            "corrected_fsr_strength61":corrected_fsr_strength61,"ch4_residuals_fsr":ch4_residuals_fsr,
            "ch4_conc_precal":ch4_conc_precal,"pzt2_adjust":pzt2_adjust,"pzt2":pzt2,"fsr_y61":fsr_y61,
            "dataGroups":d["ngroups"],"dataPoints":d["datapoints"],"pzt_per_fsr":pzt_per_fsr,
            "ch4_interval":ch4_interval,"fit_time":fit_time
            }
    RESULT.update(d.sensorDict)