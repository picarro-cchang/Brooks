#  Fit script to measure width of the CO2 line at 6058.2 wvn
#  2019 0108:  First draft derived from old pressure sensor test script modified for new laser
#  2019 0415:  Adapted from script written for AVX system at 80 C to use with 45 C G2000
#  2019 0423:  New variant to measure the 6547.69 wvn line in a sample of 1% CO2 in nitrogen
#  2019 0426:  Adjusted linewidth-to-pressure calibration factor based on intercomparison with
#              6058.2 wvn manometer using JFAADS2157 (Log book XII, p. 145)
#  2019 0501:  Prepared translation with correct VL assignments for AMADS
#  2019 0807:  Changed spectal library to match JFAADS2157 for CO2 peak

import os.path
import time
from numpy import *
from copy import copy
    
def initialize_NH3_Baseline():
    init["base",0] = NH3_baseline_level
    init["base",1] = NH3_baseline_slope
    init[1000,0] = NH3_A0
    init[1000,1] = NH3_Nu0
    init[1000,2] = NH3_Per0
    init[1000,3] = NH3_Phi0
    init[1001,0] = NH3_A1
    init[1001,1] = NH3_Nu1
    init[1001,2] = NH3_Per1
    init[1001,3] = NH3_Phi1
    
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
    fname = os.path.join(BASEPATH,r"./NH3/spectral library NH3 v2_0.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_lct.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']
    
    optDict = eval("dict(%s)" % OPTION)
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./NH3/Peak74_only_VY.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./NH3/Peak74_only_VY.ini")))
    
#   Globals
    last_time = None
    
#   Spectroscopic parameters
    fCO2 = 6547.688              # library center for Galatry peak 90
      
#   Baseline parameters

    NH3_baseline_level = instrParams['NH3_Baseline_level']
    NH3_baseline_slope = instrParams['NH3_Baseline_slope']
    NH3_A0 = instrParams['NH3_Sine0_ampl']
    NH3_Nu0 = instrParams['NH3_Sine0_freq']
    NH3_Per0 = instrParams['NH3_Sine0_period']
    NH3_Phi0 = instrParams['NH3_Sine0_phase']
    NH3_A1 = instrParams['NH3_Sine1_ampl']
    NH3_Nu1 = instrParams['NH3_Sine1_freq']
    NH3_Per1 = instrParams['NH3_Sine1_period']
    NH3_Phi1 = instrParams['NH3_Sine1_phase']
    
#   Initialize values
    
    co2_adjust = 0
    co2_ppm = 10000
    y74 = 1.8366
    peak74 = 0
    str74 = 0
    base74 = 0
    co2_residuals = 0
    fsr_shift_co2 = 0
    fsr_y74 = 1.8366
    fsr_z74 = 0.6702
    fsr_peak74 = 0
    fsr_str74 = 0
    fsr_base74 = 0
    co2_residuals_fsr = 0
    pzt2_adjust = 0.0
    pzt2 = 0
    pspec = 140
    
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

if d["spectrumId"]==1:
    pzt2 = mean(d.pztValue)
    initialize_NH3_Baseline()
    r = anCO2[0](d,init,deps)                  #  Fit with frequency from WLM.
    ANALYSIS.append(r)
    co2_shift = r["base",3]
    co2_adjust = r["base",3]
    y74 = r[74,"y"]
    peak74 = r[74,"peak"]
    str74 = r[74,"strength"]
    base74 = r[74,"base"]
    co2_ppm = 23.757*str74
    co2_residuals = r["std_dev_res"]
    
    if r[74,"peak"] < -10 or r[74,"peak"] > 10000: 
        goodLCT = False
    else:
        goodLCT = True
    if goodLCT:
        d.fitData["freq"] = fCO2 + fsr*round_((d.fitData["freq"] + co2_adjust - fCO2)/fsr)
        
        r = anCO2[1](d,init,deps)
        ANALYSIS.append(r)
        fsr_shift_co2 = r["base",3]
        pzt2_adjust = -fsr_shift_co2*pzt_per_fsr/fsr
        fsr_y74 = r[74,"y"]
        fsr_z74 = r[74,"z"]
        fsr_peak74 = r[74,"peak"]
        fsr_str74 = r[74,"strength"]
        fsr_base74 = r[74,"base"]
        co2_residuals_fsr = r["std_dev_res"]
        co2_ppm = 23.757*fsr_str74
        
        pspec =  140.0*fsr_y74/1.84827
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
    RESULT = {"goodLCT":goodLCT,"pspec":pspec,"paveraged":paveraged,"pzt2_adjust":pzt2_adjust,"pzt2":pzt2,
            "dataGroups":d["ngroups"],"dataPoints":d["datapoints"],"pzt_per_fsr":pzt_per_fsr,
            "co2_shift":co2_shift,"co2_adjust":co2_adjust,"fsr_peak74":fsr_peak74,"fsr_y74":fsr_y74,
            "fsr_base74":fsr_base74,"fsr_str74":fsr_str74,"fsr_shift_co2":fsr_shift_co2,"co2_ppm":co2_ppm,
            "co2_residuals_fsr":co2_residuals_fsr,
            "interval":interval,"fit_time":fit_time,"species":species
            }
    RESULT.update(d.sensorDict)