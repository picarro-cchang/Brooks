#  Fit script to measure width of the CO2 ine at 6058.2 wvn
#  2019 0108:  First draft derived from old pressure sensor test script modified for new laser

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
    
def initialize_Baseline():
    init["base",0] = baseline_level
    init["base",1] = baseline_slope
    init["base",2] = baseline_curvature
    init[1000,0] = A0
    init[1000,1] = Nu0
    init[1000,2] = Per0
    init[1000,3] = Phi0
    init[1001,0] = A1
    init[1001,1] = Nu1
    init[1001,2] = Per1
    init[1001,3] = Phi1
    
    
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
    fname = os.path.join(BASEPATH,r"./CFADS/Spectral library for CFADS 80 C.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_Manometer.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']
    
    optDict = eval("dict(%s)" % OPTION)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-xx H2O clean v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-xx H2O clean FCFY v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-xx H2O clean v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-xx H2O clean FCFY v1_1.ini")))
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/Peak90_only_VY.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/Peak90_only_FC_FY.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/Peak90_only_VY.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/Peak90_only_FC_FY.ini")))
    
#   Globals
    last_time = None
      
#   Baseline parameters

    baseline_level = instrParams['Baseline_level']
    baseline_slope = instrParams['Baseline_slope']
    baseline_curvature = instrParams['Baseline_curvature']
    A0 = instrParams['Sine0_ampl']
    Nu0 = instrParams['Sine0_freq']
    Per0 = instrParams['Sine0_period']
    Phi0 = instrParams['Sine0_phase']
    A1 = instrParams['Sine1_ampl']
    Nu1 = instrParams['Sine1_freq']
    Per1 = instrParams['Sine1_period']
    Phi1 = instrParams['Sine1_phase']
    
#   Presistent outputs

    paveraged = 140
          
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

if d["spectrumId"]==12:
    pzt = mean(d.pztValue)
    pzt_adjust = fsr_shift_co2 = 0.0
    initialize_Baseline()
    r = anCO2[0](d,init,deps)                  #  Fit with frequency from WLM.  CO2+methane spline.
    ANALYSIS.append(r)
    co2_shift = r["base",3]
    if r[90,"peak"] < 10 or abs(co2_shift) > 0.05:
        r = anCO2[1](d,init,deps)
        ANALYSIS.append(r)
    co2_adjust = r["base",3]
    
    if r[90,"peak"] < -10 or r[90,"peak"] > 10000:   #  Continue with FSR-based frequency axis unless 
        goodLCT = False                              #  spectrum is very badly corrupted
    else:
        goodLCT = True
    if goodLCT:
        d.fitData["freq"] = 6058.19127 + fsr*round_((d.fitData["freq"] + co2_adjust - 6058.19127)/fsr)
        
        if r[90,"peak"] > 10:
            r = anCO2[2](d,init,deps)
        else:
            r = anCO2[3](d,init,deps)
        ANALYSIS.append(r)
        fsr_shift_co2 = r["base",3]
        pzt_adjust = -fsr_shift_co2*pzt_per_fsr/fsr
        
    y90 = r[90,"y"]
    peak90 = r[90,"peak"]
    str90 = r[90,"strength"]
    base90 = r[90,"base"]
    ch4_conc_lowPrecision = 10*r[1002,2]
    co2_ppm = 2.6113*str90
    co2_residuals = r["std_dev_res"]
        
        # y90_nominal = (pspec/760.0)*(0.0687660 + 0.05105*4.1725e-5*str75)/0.0070080
        # normalized_fsr_strength90 = fsr_str90*y90_nominal/fsr_y90
        # corrected_fsr_strength90 = (140.0/pspec)*normalized_fsr_strength90
        # ydry = fsr_y90 - (140.0/760.0)*(0.05105*4.1725e-5*fsr_str75)/0.0070080
        # pspec90 =  140.0*ydry/1.8076

    fsr_shift_h2o = 0.0
    init[1002,2] = 0.1*ch4_conc_lowPrecision  
    r = anH2O[0](d,init,deps)                 #  Standard CFADS water line with methane spline
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    if r[75,"peak"] < 10 or abs(r["base",3]) >= 0.05:
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)

    if goodLCT:
        if r[75,"peak"]>10:
            r = anH2O[2](d,init,deps)
        else:
            r = anH2O[3](d,init,deps)
        ANALYSIS.append(r)
        fsr_shift_h2o = r["base",3]
        
    y75 = r[75,"y"]
    peak75 = r[75,"peak"]
    str75 = r[75,"strength"]
    base75 = r[75,"base"]
    h2o_residuals = r["std_dev_res"]
    h2o_pct = 0.0020941*str75                                      # Changed from Hitran value 0.0020834 to match 
                                                                   # Chris's CFADS intercomparison
    ydry = y90 - (140.0/760.0)*(8.607e-7*str75)/0.0073826          # From 80 C Baratron experiment 30.8.2018
    pspec = 140.0*ydry/1.5954                                      # Book XII, pp. 2-3
    paveraged = expAverage(paveraged,pspec,100,0.2)
    
    
        
now = time.clock()
fit_time = now-tstart
if r != None:
    IgnoreThis = False
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]
else:
    IgnoreThis = True
   
if not IgnoreThis:    
    RESULT = {"goodLCT":goodLCT,"pspec":pspec,"paveraged":paveraged,"pzt_adjust":pzt_adjust,"pzt":pzt,
            "h2o_shift":h2o_shift,"peak75":peak75,"y75":y75,"h2o_residuals":h2o_residuals,
            "str75":str75,"fsr_shift_h2o":fsr_shift_h2o,"base75":base75,"h2o_pct":h2o_pct,
            "dataGroups":d["ngroups"],"dataPoints":d["datapoints"],"pzt_per_fsr":pzt_per_fsr,
            "co2_shift":co2_shift,"co2_adjust":co2_adjust,"peak90":peak90,"y90":y90,
            "base90":base90,"str90":str90,"fsr_shift_co2":fsr_shift_co2,"co2_ppm":co2_ppm,
            #"corrected_fsr_strength90":corrected_fsr_strength90,"normalized_fsr_strength90":normalized_fsr_strength90,
            "co2_residuals":co2_residuals,"ch4_conc_lowPrecision":ch4_conc_lowPrecision,
            "interval":interval,"fit_time":fit_time,"species":species
            }
    RESULT.update(d.sensorDict)