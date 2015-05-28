#  Fit script for ethylene in the 6182 wavenumber region
#  21 Sep 2012:  Translated from G1000 script

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

def initialize_Baseline():
    init["base",1] = baseline_slope
    init[1000,0] = A0
    init[1000,1] = Nu0
    init[1000,2] = Per0
    init[1000,3] = Phi0
    init[1001,0] = A1
    init[1001,1] = Nu1
    init[1001,2] = Per1
    init[1001,3] = Phi1

if INIT:
    fname = os.path.join(BASEPATH,r"./GADS/spectral library GFADS v1_1.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anC2H4 = []
    anC2H4.append(Analysis(os.path.join(BASEPATH,r"./GADS/GADS-xx E_FY M_FY Cent_F 0406.ini")))
    anC2H4.append(Analysis(os.path.join(BASEPATH,r"./GADS/GADS-xx E_VY M_FY C_FY 0406.ini")))
    anC2H4.append(Analysis(os.path.join(BASEPATH,r"./GADS/GADS-xx E_FY M_FY C_FY W_FY 0406.ini")))
    anC2H4.append(Analysis(os.path.join(BASEPATH,r"./GADS/GADS-xx E_FY M_FY Cent_F BASEAVE 0406.ini")))
    anC2H4.append(Analysis(os.path.join(BASEPATH,r"./GADS/GADS-xx E_VY M_FY C_FY BASEAVE 0406.ini")))

    #  Import instrument specific baseline constants
    baseline_level = instrParams['C2H4_Baseline_level']
    baseline_slope = instrParams['C2H4_Baseline_slope']
    A0 = instrParams['C2H4_Sine0_ampl']
    Nu0 = instrParams['C2H4_Sine0_freq']
    Per0 = instrParams['C2H4_Sine0_period']
    Phi0 = instrParams['C2H4_Sine0_phase']
    A1 = instrParams['C2H4_Sine1_ampl']
    Nu1 = instrParams['C2H4_Sine1_freq']
    Per1 = instrParams['C2H4_Sine1_period']
    Phi1 = instrParams['C2H4_Sine1_phase']

#   Globals
    base_avg = baseline_level
    c2h4_shift=0
    c2h4_adjust=0
    c2h4_conc_ppbv=0
    ch4_conc_from_c2h4=0
    co2_conc_from_c2h4=0
    c2h4_yeff=0
    ch4_yeff=0
    co2_yeff=0
    co2_amp=0
    peak_76=0
    str_76=0
    y_76=0
    h2o_conc=0
    base_level=0
    base_slope=0
    c2h4_res=0
    c2h4_conc_ppbv_a=0
    ch4_conc_from_c2h4_a=0
    c2h4_yeff_a=0
    ch4_yeff_a=0

    counter = -10
    last_time = None
    pzt_ave = 0.0
    pzt_stdev = 0.0

# For offline analysis and output to file
    #out = open("Fit_results.txt","w")
    #first_fit = 1

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=10.0)
d.wlmSetpointFilter(maxDev=0.0007,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])

d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))

species = (d.subschemeId & 0x3FF)[0]
solValves = d.sensorDict["ValveMask"]

tstart = time.clock()
RESULT = {}
r = None

if species == 30:
    initialize_Baseline()
    init[1004,2] = co2_amp
    r = anC2H4[0](d,init,deps)
    ANALYSIS.append(r)
    if r[1002,2] > 0.5:
        r = anC2H4[1](d,init,deps)
        ANALYSIS.append(r)
        base_avg  = initExpAverage(base_avg,r["base",0],3,20,counter)
        init["base",0] = base_avg
        r = anC2H4[4](d,init,deps)
        ANALYSIS.append(r)
    else:
        base_avg  = initExpAverage(base_avg,r["base",0],3,20,counter)
        init["base",0] = base_avg
        r = anC2H4[3](d,init,deps)
        ANALYSIS.append(r)

    c2h4_conc_ppbv = 1000*r[1002,2]
    c2h4_yeff = r[1002,5]              #  G1000 script has an average pressure adjustment here
    ch4_conc_from_c2h4 = 20*r[1003,2]
    ch4_yeff = r[1003,5]
    co2_conc_from_c2h4 = 50000*r[1004,2]
    co2_yeff = r[1004,5]
    base_level = r["base",0]
    base_slope = r["base",1]
    c2h2_shift = r["base",3]
    counter += 1
    c2h4_res = r["std_dev_res"]

if species == 31:
    initialize_Baseline()
    init[1004,2] = co2_amp
    r = anC2H4[2](d,init,deps)
    ANALYSIS.append(r)
    c2h4_conc_ppbv_a = 1000*r[1002,2]
    c2h4_yeff_a = r[1002,5]
    ch4_conc_from_c2h4_a = 20*r[1003,2]
    ch4_yeff_a = r[1003,5]
    co2_conc_from_c2h4 = 50000*r[1004,2]
    co2_yeff = r[1004,5]
    co2_amp = r[1004,2]
    base_level = r["base",0]
    base_slope = r["base",1]
    c2h4_shift = r["base",3]
    peak_76 = r[76,"peak"]
    str_76 = r[76,"strength"]
    y_76 = r[76,"y"]
    h2o_conc = 0.4034*peak_76
    if ((co2_conc_from_c2h4 > 150) or (c2h4_conc_ppbv > 200) or (ch4_conc_from_c2h4 > 10)):
        c2h4_adjust = c2h4_shift
    else:
        c2h4_adjust = 0.0

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
    RESULT = {"c2h4_shift":c2h4_shift,"c2h4_adjust":c2h4_adjust,"c2h4_res":c2h4_res,
            "c2h4_conc_ppbv":c2h4_conc_ppbv,"ch4_conc_from_c2h4":ch4_conc_from_c2h4,
            "co2_conc_from_c2h4":co2_conc_from_c2h4,
            "c2h4_yeff":c2h4_yeff,"ch4_yeff":ch4_yeff,"co2_yeff":co2_yeff,"co2_amp":co2_amp,
            "c2h4_conc_ppbv_a":c2h4_conc_ppbv_a,"ch4_conc_from_c2h4_a":ch4_conc_from_c2h4_a,
            "c2h4_yeff_a":c2h4_yeff_a,"ch4_yeff_a":ch4_yeff_a,
            "peak_76":peak_76,"str_76":str_76,"y_76":y_76,"h2o_conc":h2o_conc,
            "base_level":base_level,"base_slope":base_slope,"base_avg":base_avg,
            "dataGroups":d["ngroups"],"dataPoints":d["datapoints"],"solenoid_valves":solValves,
            "species":species,"interval":interval,"fit_time":fit_time
            }
    RESULT.update(d.sensorDict)
