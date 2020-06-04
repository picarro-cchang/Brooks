#  Fit script to detect ethylene oxide using wide-band laser and the strong feature at 6080 wvn
#  2019 0418:  First draft
#  2019 0506:  V1.2 experiments with hybrid Galatry-spline model for water and CO2
#  2019 0904:  Add ethylene spline to spectral model
#  2019 0917:  Try modification to water model in CO2 and H2O regions
#  2019 0918:  Add methanol and methylene chloride to spectral model based on application input
#  2019 0925:  Add reporting of "tiptop"
#  2019 0927:  V1.9 tests "clutter avoidance" strategy
#  2019 1004:  Start a new branch of fit scripts for 450 Torr operation
#  2019 1113:  Tweaks to water line shapes based on steps with AVX80-9004 and zero air
#  2019 1115:  Tweaks to water cross-broadening based on tests with AVX80-9004 and CH4,CO2
#  2020 0121:  Adds some lessons learned at 140 Torr -- test for RD loss outliers, change pzt control to use WLM
#              Also adds ethylene to all fits, based on experience with 140 Torr
#  2020 0127:  Removed incorrect self-broadening of R0 from fit definiton in methane region

import os.path
import time
from numpy import *
from copy import copy
    
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
    fname = os.path.join(BASEPATH,r"./ETO_450Torr/Spectral library for ETO 6080 wvn 80 C 450 Torr v3.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_450torr.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_450torr.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_sgdbr.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']
    
    optDict = eval("dict(%s)" % OPTION)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./ETO_450Torr/H2O_6080_VCVY_v5.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./ETO_450Torr/H2O_6080_FCFY_v5.ini")))
    
    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./ETO_450Torr/CH4_R6_VCVY_v7.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./ETO_450Torr/CH4_R6_FCFY_v6.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./ETO_450Torr/CH4_R6_VCFY_v7.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./ETO_450Torr/CH4_R6_VCFY2_v7.ini")))
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./ETO_450Torr/CO2_R6_VCVY_v6.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./ETO_450Torr/CO2_R6_FCFY_v6.ini")))
    
    anETO = []
    anETO.append(Analysis(os.path.join(BASEPATH,r"./ETO_450Torr/ETOwide_v11_FCFY.ini")))
    
#   Globals
    last_time = None
    f_eto = 6080.0600    #  Target for "0th mode" frequency for 450 Torr (had been 6080.0630 at 140 Torr)
      
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
    
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = copy(DATA)

d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.sparse(maxPoints=1000,width=0.01,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))
bogus = d.groupStdDevs["uncorrectedAbsorbance"] > 0.004
badGroups = sum(bogus)

#  Recast frequencies to lie on FSR comb
i0 = argmin(abs(d.fitData["freq"] - f_eto))
f0 = d.fitData["freq"][i0]
while (f0 - f_eto) < -0.5*fsr:
    f0 += fsr
while (f0 - f_eto) > 0.5*fsr:
    f0 -= fsr
d.fitData["freq"] = f0 + fsr*round_((d.fitData["freq"] - f0)/fsr)
for i in range(len(d.fitData["freq"])):
    if bogus[i] > 0:
        d.fitData["freq"][i] = 0.0

T = d["cavitytemperature"] + 273.15
species = (d.subschemeId & 0x3FF)[0]
tstart = time.clock()
RESULT = {}
r = None

if d["spectrumId"]==181 and d["ngroups"] > 150 : # and d["ngroups"] < 206:
    pzt = mean(d.pztValue)
    pzt_adjust = wlm_adjust = 0.0
    initialize_Baseline()
    r = anCH4[0](d,init,deps)
    ANALYSIS.append(r)
    ch4_shift = r["base",3]
    ch4_vy = r[1002,5]
    if (r[1002,2] < 0.003 and r[2,"peak"] < 30 and r[20,"peak"] < 30) or abs(ch4_shift) > 0.05:
        r = anCH4[1](d,init,deps)
        ANALYSIS.append(r)
    elif (r[1002,2] < 0.003 or ch4_vy < 0.5 or ch4_vy > 1.5) and (r[2,"peak"] > 30 and r[2,"y"] > 2 and r[2,"y"] < 5):
        r = anCH4[2](d,init,deps)
        ANALYSIS.append(r)
    elif (r[2,"peak"] < 10 or r[2,"y"] < 2 or r[2,"y"] > 5):
        r = anCH4[3](d,init,deps)
        ANALYSIS.append(r)
    ch4_adjust = r["base",3]
    ch4_y = r[1002,5]
    ch4_ppm = 10*r[1002,2]
    nh3_ppb = 50000*r[1003,2]
    c2h4_ppb = 10000*r[1005,2] 
    str2 = r[2,"strength"]
    y2 = r[2,"y"]
    str8 = r[8,"strength"]
    str20 = r[20,"strength"]
    ch4_residuals = r["std_dev_res"]

    init[1002,2] = 0.1*ch4_ppm
    init[1002,5] = ch4_y
    init[1003,2] = 0.0004495*str2
    init[1005,2] = nh3_ppb/50000
    init[1006,2] = 0.0001*c2h4_ppb
    init[13,"strength"] = 0.00405*str2                # Updated from water step test 24. Jan 2020
    init[26,"y"] = 5.8328 + 5.645e-6*str2             # From water step test 15. Nov 2019
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    co2_shift = r["base",3]
    if r[26,"peak"] < 20 or abs(co2_shift) > 0.05 or (r[26,"y"]/5.8328) < 0.75 or (r[26,"y"]/5.8328) > 1.25:
        r = anCO2[1](d,init,deps)
        ANALYSIS.append(r)
    co2_adjust = r["base",3]
    y26 = r[26,"y"]
    str26 = r[26,"strength"]
    peak26 = r[26,"peak"]
    base26 = r[26,"base"]
    co2_ppm = 1.2486*str26                             #  From fits to 3000 ppm CO2 acquired 22 Aug 2019
    co2_residuals = r["std_dev_res"]
    str13 = r[13,"strength"]

    init[24,"strength"] = 0.73438*str26
    init[24,"y"] = 1.0192*y26    
    init[1004,2] = co2_ppm/3000    
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    if r[4,"peak"] < 30 or abs(r["base",3]) > 0.05 or r[4,"y"] < 1 or r[4,"y"] > 4:
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
    h2o_adjust = r["base",3]
    y4 = r[4,"y"]
    str4 = r[4,"strength"]
    peak4 = r[4,"peak"]
    base4 = r[4,"base"]
    h2o_residuals = r["std_dev_res"]
    h2o_pct = 0.0016078*str4                           # From Hitran (class 7, 1-2%)   

    init = InitialValues()
    
    if peak4 > 30:
        wlm_adjust = h2o_adjust
        init["base",3] = h2o_adjust
    elif peak26 > 30: 
        wlm_adjust = co2_adjust
        init["base",3] = co2_adjust        
    elif ch4_ppm > 0.03: 
        wlm_adjust = ch4_adjust
        init["base",3] = ch4_adjust        
    pzt_adjust = -(f0 + wlm_adjust - f_eto)*pzt_per_fsr/fsr
    
    initialize_Baseline()
    init[4,"strength"] = str4
    init[4,"y"] = y4
    init[2,"strength"] = str2
    init[2,"y"] = y2
    init[3,"y"] = 4.4983 + 0.0002900*str4
    init[11,"y"] = 2.3798 + 0.0001615*str4
    init[12,"y"] = 1.3139 + 0.0001231*str4
    init[26,"strength"] = str26
    init[26,"y"] = y26
    init[1002,2] = 0.1*ch4_ppm
    init[1002,5] = ch4_y
    init[1003,2] = nh3_ppb/50000
    init[1005,2] = h2o_pct            #  Hitran model for all weak lines not modeled by Galatry functions
    init[1006,2] = co2_ppm/3000
    init[1007,2] = 0.0001*c2h4_ppb
    r = anETO[0](d,init,deps)
    ANALYSIS.append(r)
    eto_ppb = 1000*r[1004,2] 
    eto_residuals = r["std_dev_res"]
    base0 = r["base",0]   
    base1 = r["base",1]
    base2 = r["base",2] 
    c2h4_ppb = 10000*r[1007,2]       
    #ch3oh_ppm = 700*r[1008,2]       #  These splines do not exist for 450 Torr as of January 2020 
    #ch2cl2_ppb = 100000*r[1009,2]    
       
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
    RESULT = {"pzt_adjust":pzt_adjust,"pzt":pzt,"wlm_adjust":wlm_adjust,"tiptop":d.fitData["loss"][i0],"badGroups":badGroups,
            "base0":base0,"base1":base1,"base2":base2,"nh3_ppb":nh3_ppb,"tipstd":1000*d.groupStdDevs["uncorrectedAbsorbance"][i0],
            "ch4_shift":ch4_shift,"ch4_adjust":ch4_adjust,"ch4_vy":ch4_vy,"ch4_y":ch4_y,"ch4_ppm":ch4_ppm,
            "str2":str2,"y2":y2,"str8":str8,"str20":str20,"ch4_residuals":ch4_residuals,"str13":str13,
            "co2_shift":co2_shift,"co2_adjust":co2_adjust,"str26":str26,"peak26":peak26,"base26":base26,"y26":y26,"co2_residuals":co2_residuals,
            "h2o_shift":h2o_shift,"h2o_adjust":h2o_adjust,"str4":str4,"peak4":peak4,"base4":base4,"y4":y4,"h2o_residuals":h2o_residuals,
            "co2_ppm":co2_ppm,"h2o_pct":h2o_pct,"eto_ppb":eto_ppb,"eto_residuals":eto_residuals,
            "c2h4_ppb":c2h4_ppb,#"ch3oh_ppm":ch3oh_ppm,"ch2cl2_ppb":ch2cl2_ppb,
            "dataGroups":d["ngroups"],"dataPoints":d["datapoints"],"pzt_per_fsr":pzt_per_fsr,
            "interval":interval,"fit_time":fit_time,"species":species
            }
    RESULT.update(d.sensorDict)