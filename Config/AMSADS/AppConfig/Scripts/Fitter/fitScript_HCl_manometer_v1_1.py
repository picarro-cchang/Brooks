#  Fit script to measure width of the very strong water line at 5732.5 wvn
#  2019 1021:  First draft branched from spectroscopic manometer for methane region in JFADS
#              Correction for self-broadening from Hitran (unc class 5 for gammas) simulation for 140 Torr and 45 C

import os.path
import time
from numpy import *
from copy import copy
    
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
    fname = os.path.join(BASEPATH,r"./HCl/spectral library HCl v1_3.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_Manometer.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_lct.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR_VLASER_3']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']
    
    optDict = eval("dict(%s)" % OPTION)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HCl/Peak60_only_VY.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HCl/Peak60_only_VY.ini")))
    
#   Globals
    last_time = None
    
#   Spectroscopic parameters
    fH2O = 5732.47312               # library center for Galatry peak 60
    h2o_lin = instrParams['H2O_linear']
      
#   Baseline parameters

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
    
#   Initialize values

    h2o_shift = 0
    h2o_adjust = 0
    h2o_ppm = 0
    ch4_ppm = 0
    y60 = 1.3476
    peak60 = 0
    str60 = 0
    base60 = 0
    h2o_residuals = 0
    fsr_shift_h2o = 0
    fsr_y60 =1.3476
    fsr_peak60 = 0
    fsr_str60 = 0
    fsr_base60 = 0
    h2o_residuals_fsr = 0
    pzt_adjust = 0.0
    pzt = 0
    pzt_stdev = 0
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

if d["spectrumId"]==63 and d["ngroups"]>20:
    timeout = d.pztValue == 0
    pzt = mean(d.pztValue[timeout == 0])
    pzt_stdev = std(d.pztValue[timeout == 0])
    initialize_Baseline()
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    y60 = r[60,"y"]
    h2o_residuals = r["std_dev_res"]
    base60 = r[60,"base"]
    peak60 = r[60,"peak"]
    str60 = r[60,"strength"]
    h2o_adjust = r["base",3]
    h2o_ppm = h2o_lin*str60
    ch4_ppm = 100*r[1002,2]

    if r[60,"peak"] < -10 or r[60,"peak"] > 10000: 
        goodLCT = False
    else:
        goodLCT = True
    
    if goodLCT:
        d.fitData["freq"] = fH2O + fsr*round_((d.fitData["freq"] + h2o_adjust - fH2O)/fsr)

        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
        fsr_shift_h2o = r["base",3]
        pzt_adjust = -fsr_shift_h2o*pzt_per_fsr/fsr
        fsr_y60 = r[60,"y"]
        fsr_peak60 = r[60,"peak"]
        fsr_str60 = r[60,"strength"]
        fsr_base60 = r[60,"base"]
        h2o_residuals_fsr = r["std_dev_res"]

        ydry = fsr_y60 - 6.402e-7*fsr_str60          #  Correction for self-broadening
        pspec =  140.0*ydry/1.3476
        paveraged = expAverage(paveraged,pspec,100,0.2)
        h2o_ppm = h2o_lin*fsr_str60*(140.0/pspec)
        ch4_ppm = 100*r[1002,2]*(140.0/pspec)
            
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
        RESULT = {"goodLCT":goodLCT,"pspec":pspec,"paveraged":paveraged,"pzt_adjust":pzt_adjust,"pzt":pzt,"pzt_stdev":pzt_stdev,
                "h2o_adjust":h2o_adjust,"h2o_shift":h2o_shift,"fsr_peak60":fsr_peak60,"fsr_y60":fsr_y60,
                "fsr_str60":fsr_str60,"fsr_shift_h2o":fsr_shift_h2o,"base60":base60,"h2o_ppm":h2o_ppm,"ch4_ppm":ch4_ppm,
                "dataGroups":d["ngroups"],"dataPoints":d["datapoints"],"pzt_per_fsr":pzt_per_fsr,"h2o_residuals_fsr":h2o_residuals_fsr,
                "interval":interval,"fit_time":fit_time,"species":species
                }
        RESULT.update(d.sensorDict)