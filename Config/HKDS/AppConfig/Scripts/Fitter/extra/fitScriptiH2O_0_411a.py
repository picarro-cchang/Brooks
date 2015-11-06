#  First cut at a fitter for isotopic water at 7183
#  Translated from Chris's Silverstone release of 16 June 2010 by hoffnagle

import os.path
import time
from numpy import *

def expAverage(xavg,x,n,dxMax):
    if xavg is None: return x
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)<dxMax: return y
    elif y>xavg: return xavg+dxMax
    else: return xavg-dxMax

def initExpAverage(xavg,x,hi,dxMax,count):
    if xavg is None: return x
    n = min(max(count,1),hi)
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)<dxMax: return y
    elif y>xavg: return xavg+dxMax
    else: return xavg-dxMax

def fitQuality(sdFit,maxPeak,normPeak,sdTau):
    return sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

if INIT:
    fname = os.path.join(BASEPATH,r"./HBDS/spectral library v1_045_HBDS11_alcohols - CH4 - C2H6_20100416.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HBDS/HBDSxx combo v0_2 20090402.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HBDS/HBDSxx Wd combo v0_2 20090402.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HBDS/HBDSxx combo v0_2 - methanol - CH4 - C2H6-off 20100416.ini")))
    
#   Globals for the isotopic H2O fit
    counter = -25
    last_time = None
    h2o_squish_avg = 0.25
    h2o_y_trigger = 0.950
    old_splinemax = 0.0
    old_splinemax_vy = 0.0
    d_splinemax = 0.0
    d_splinemax_bound = 100.0
    auto_mode_flag = 0
    n2_flag = 0
    
#   Parameters that go into the fits --  for later consideration:  should these be imported from an instrument configuration ini?    

    intercept77 = [-0.38, -0.38]
    intercept82 = [-0.314, -0.314]
    y_0 = [0.916, 0.985]
    G77_A2 = [-5.75E-7, -5.75E-7]
    G77_A3 = [7.67E-11,7.67E-11]
    G82_A2 = [-2.55E-7, -2.55E-7]
    G82_A3 = [2.5E-11, 2.5E-11]
    h2o_cal_lin = [7.45, 7.45]
    h2o_cal_quad = [0.0, 0.0]
    y_self = 1.76E-5

init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
#d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
#d.wlmSetpointFilter(maxDev=0.0007,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.5)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))
P = d["cavitypressure"]
T = d["cavitytemperature"]

species = (d.subschemeId & 0x3FF)[0]
#print "SpectrumId", d["spectrumId"]

tstart = time.clock()
RESULT = {}
r = None

if (species == 120) and (len(d.fitData["freq"]) > 11):
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    h2o_squish_a = r[1002,3]
    h2o_y_eff_a = r[1002,5]
    splinemax_vy = r[1002,"peak",7183.65,7183.71]
    d_squish_max = 0.0002*splinemax_vy
    if (splinemax_vy >= 10) and (abs(h2o_shift) <= 0.03):
        h2o_squish_avg = initExpAverage(h2o_squish_avg,h2o_squish_a,2,d_squish_max,counter)
        counter += 1
    else:
        h2o_shift = 0.0
##  This next section of code implements the auto-detection of ambient gas = air or N2
    if (auto_mode_flag) and (splinemax_vy >= 500):
        d_splinemax_vy = abs(splinemax_vy - old_splinemax_vy)
        old_splinemax_vy = splinemax_vy
        if (d_splinemax_vy < d_splinemax_bound):
            h2o_y_setpoint = y_0[n2_flag] * (1.0 + (1.76E-5)*splinemax_vy)
            h2o_y_eff_0 = h2o_y_eff_a/(1.0 + (1.76E-5)*splinemax_vy)
            y_diff = h2o_y_setpoint - h2o_y_eff_a
            if (h2o_y_eff_0 > h2o_y_trigger):
                n2_flag = 1
            else:
                n2_flag = 0

    h2o_y_setpoint = y_0[n2_flag] * (1.0 + (1.76E-5)*splinemax_vy)
    init["base",3] = h2o_shift
    init[1002,3] = h2o_squish_avg
    init[1002,5] = h2o_y_setpoint
    r = anH2O[1](d,init,deps)
    ANALYSIS.append(r)
    h2o_res = r["std_dev_res"]
    h2o_y_eff = r[1002,5]
    baseline = r["base",0]
    baseline_slope = r["base",1]
    h2o_spline_amp = r[1002,2]
    h2o_squish = r[1002,3]
    splinemax_a = r[1002,"peak",7183.65,7183.71]
    Galpeak77_raw = r[77,"peak"]
    Galpeak79 = r[79,"peak"]
    Galpeak82_raw = r[82,"peak"]
    splinemax = splinemax_a
    splinepeak_a = splinemax_a + baseline
    if (abs(splinemax_a - old_splinemax) < d_splinemax_bound) and (splinemax_a >= 30) and (abs(r["base",3]) <= 0.03):
        h2o_adjust = r["base",3]
    else:
        h2o_adjust = 0.0
    old_splinemax = splinemax_a
    Galpeak77_offsetonly = Galpeak77_raw - intercept77[n2_flag]
    Galpeak82_offsetonly = Galpeak82_raw - intercept82[n2_flag]
    spm2 = splinemax**2
    spm3 = spm2*splinemax
    Galpeak77 = Galpeak77_offsetonly+G77_A2[n2_flag]*spm2*G77_A3[n2_flag]*spm3
    Galpeak82 = Galpeak82_offsetonly+G82_A2[n2_flag]*spm2*G82_A3[n2_flag]*spm3
    h2o_ppmv = h2o_cal_lin[n2_flag]*splinemax + h2o_cal_quad[n2_flag]*spm2
    
    r = anH2O[2](d,init,deps)
    ANALYSIS.append(r)
    ch4_c2h6_res = r["std_dev_res"]
    ch4_c2h6_77 = r[77,"peak"]
    ch4_c2h6_82 = r[82,"peak"]
    ch4_c2h6_base = r["base",0]
    ch4_c2h6_slope = r["base",1]
    ch4_c2h6_ch4conc = r[1003,2]
    ch4_c2h6_c2h6conc = r[1004,2]
    ch4_c2h6_MeOHampl = r[1005,2]
                
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

#print DATA.filterHistory
    
if not IgnoreThis:    
    RESULT = {
            "h2o_adjust":h2o_adjust,"h2o_shift":h2o_shift,"baseline":baseline,
            "baseline_slope":baseline_slope,"h2o_spline_amp":h2o_spline_amp,
            "h2o_ppmv":h2o_ppmv,"h2o_spline_max":splinemax,"galpeak77":Galpeak77,
            "galpeak77_offsetonly":Galpeak77_offsetonly,"galpeak79":Galpeak79,
            "galpeak82":Galpeak82,"galpeak82_offsetonly":Galpeak82_offsetonly,
            "h2o_res":h2o_res,"ch4_c2h6_res":ch4_c2h6_res,"n2_flag":n2_flag,
            "h2o_y_eff":h2o_y_eff,"h2o_y_eff_a":h2o_y_eff_a,
            "h2o_squish":h2o_squish,"h2o_squish_a":h2o_squish_a,
            "ch4_c2h6_77":ch4_c2h6_77,"ch4_c2h6_82":ch4_c2h6_82,
            "ch4_c2h6_base":ch4_c2h6_base,"ch4_c2h6_slope":ch4_c2h6_slope,
            "ch4_c2h6_ch4conc":ch4_c2h6_ch4conc,"ch4_c2h6_c2h6conc":ch4_c2h6_c2h6conc,
            "ch4_c2h6_MeOHampl":ch4_c2h6_MeOHampl
            }
    RESULT.update({"species":species,"interval":interval,
                   "cavity_pressure":P,"cavity_temperature":T}
                  )
    RESULT.update(d.sensorDict)