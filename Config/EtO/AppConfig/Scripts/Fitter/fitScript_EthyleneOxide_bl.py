#  Fit script to detect ethylene oxide using wide-band laser and the strong feature at 6080 wvn
#  2019 0418:  First draft
#  2019 0506:  V1.2 experiments with hybrid Galatry-spline model for water and CO2

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
    # init[1007,0] = 0.3656
    # init[1007,2] = 99.34
    # init[1007,3] = 0.0
    
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
    fname = os.path.join(BASEPATH,r"./ETO/Spectral library for ETO 6080 wvn v2.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_sgdbr.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']
    
    optDict = eval("dict(%s)" % OPTION)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./ETO/H2O_6080_VCVY_v3.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./ETO/H2O_6080_FCFY_v3.ini")))
    
    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./ETO/CH4_R6_VCVY_v4.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./ETO/CH4_R6_FCFY_v4.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./ETO/CH4_R6_VCFY_v4.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./ETO/CH4_R6_VCFY2_v4.ini")))
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./ETO/CO2_R6_VCVY_v3.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./ETO/CO2_R6_FCFY_v3.ini")))
    
    anETO = []
#    anETO.append(Analysis(os.path.join(BASEPATH,r"./ETO/ETOwide_FCFY.ini"))) ##single region (old)
##    anETO.append(Analysis(os.path.join(BASEPATH,r"./ETO/ETOwide_v7js_FCFY.ini"))) ##single region (new)
#    anETO.append(Analysis(os.path.join(BASEPATH,r"./ETO/ETOwide_v7js1_FCFY.ini"))) ##single region (new)
#    anETO.append(Analysis(os.path.join(BASEPATH,r"./ETO/ETOwide_v7js2_FCFY.ini"))) ##single region (new)

##    anETO.append(Analysis(os.path.join(BASEPATH,r"./ETO/ETOwide_v7js10_FCFY.ini"))) ##single region (new)
    anETO.append(Analysis(os.path.join(BASEPATH,r"./ETO/ETOwide_bl_FCFY.ini"))) ##single region (new)
    
#    anETO.append(Analysis(os.path.join(BASEPATH,r"./ETO/ETOwide_v7j2_FCFY.ini"))) ##single region (new)

#    anETO.append(Analysis(os.path.join(BASEPATH,r"./ETO/ETOwide_v7j_FCFY.ini"))) ##multiple regions (w/ John's new mods)
#    anETO.append(Analysis(os.path.join(BASEPATH,r"./ETO/ETOwide_v7_FCFY.ini"))) ##multiple regiosn
    
#   Globals
    last_time = None
    f_eto = 6080.0630    #  Target for "0th mode" frequency
    
# # For offline analysis and output to file
    # out = open("Fit_EtO9006_bl_03102020a.txt","w")
    # first_fit = 1
      
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
    
    rp00 = A0
    rp02 = Per0
    rp03 = Phi0
    rp10 = A1
    rp12 = Per1
    rp13 = Phi1
    
    
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = copy(DATA)

d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.sparse(maxPoints=1000,width=0.01,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))
bogus = d.groupStdDevs["uncorrectedAbsorbance"] > 0.001
badGroups = sum(bogus)

#  Recast frequencies to lie on FSR comb
i0 = argmin(abs(d.fitData["freq"] - f_eto))
f0 = d.fitData["freq"][i0]
while (f0 - f_eto) <= -0.5*fsr:
    f0 += fsr
while (f0 - f_eto) > 0.5*fsr:
    f0 -= fsr
d.fitData["freq"] = f0 + fsr*round_((d.fitData["freq"] - f0)/fsr)
for i in range(len(d.fitData["freq"])):
    if bogus[i] > 0:
        d.fitData["freq"][i] = 0.0

T = d["cavitytemperature"] + 273.15
Pcavity = mean(d.cavityPressure)
stdPcavity = std(d.cavityPressure)

print "T & P+/-dP ", T, Pcavity,stdPcavity
species = (d.subschemeId & 0x3FF)[0]
tstart = time.clock()
RESULT = {}
r = None
print "species = ", species

if (d["spectrumId"]==181 or d["spectrumId"]==10) and stdPcavity < 0.1:
    init[1002,2] = 0.0
    init[1002,3] = 0.0
    init[1002,4] = 0.0
    init[1002,5] = 0.0
    init[1002,6] = 0.0
    
    pzt = mean(d.pztValue)
    pzt_adjust = wlm_adjust = 0.0
    initialize_Baseline()
    r = anCH4[0](d,init,deps)
    ANALYSIS.append(r)
    ch4_shift = r["base",3]
    ch4_vy = r[1002,5]
    if (r[1002,2] < 0.003 and r[2,"peak"] < 10) or abs(ch4_shift) > 0.05:
        initialize_Baseline()
        r = anCH4[1](d,init,deps)
        ANALYSIS.append(r)
    ch4_adjust = r["base",3]
    ch4_y = r[1002,5]
    ch4_ppm = 10*r[1002,2]
    nh3_ppb = 50000*r[1003,2]
    str2 = r[2,"strength"]
    y2 = r[2,"y"]
    str8 = r[8,"strength"]
    str20 = r[20,"strength"]
    ch4_residuals = r["std_dev_res"]

    init[1002,2] = 0.1*ch4_ppm
    init[1002,5] = ch4_y
    init[1003,2] = 0.0014794*str2
    init[1004,2] = 0.0
    init[13,"strength"] = 0.003280*str2               # From water step test 11. Sep 2019
    init[26,"y"] = 1.83446 + 0.00580*0.0014794*str2   # From water step test 11. Sep 2019
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    co2_shift = r["base",3]
    if r[26,"peak"] < 10 or abs(co2_shift) > 0.05 or (r[26,"y"]/1.8345) < 0.75 or (r[26,"y"]/1.8345) > 1.25:
        r = anCO2[1](d,init,deps)
        ANALYSIS.append(r)
    co2_adjust = r["base",3]
    y26 = r[26,"y"]
    str26 = r[26,"strength"]
    peak26 = r[26,"peak"]
    base26 = r[26,"base"]
    co2_ppm = 3.9915*str26             #  From fits to 3000 ppm CO2 acquired 19 Dec 2018
    co2_residuals = r["std_dev_res"]

    init[24,"strength"] = 0.72981*str26 
    init[1004,2] = co2_ppm/400
    init[1005,2] = 0.0
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    if r[4,"peak"] < 10 or abs(r["base",3]) > 0.05 or r[4,"y"] < 0.6 or r[4,"y"] > 1.0:
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
    h2o_adjust = r["base",3]
    y4 = r[4,"y"]
    str4 = r[4,"strength"]
    peak4 = r[4,"peak"]
    base4 = r[4,"base"]
    h2o_residuals = r["std_dev_res"]
    h2o_pct = 0.0051678*str4           # From Hitran (class 7, 1-2%)   

    #init = InitialValues()
    
    if peak4 > 10:
        wlm_adjust = h2o_adjust
        init["base",3] = h2o_adjust
    elif peak26 > 10: 
        wlm_adjust = co2_adjust
        init["base",3] = co2_adjust        
    elif ch4_ppm > 0.001: 
        wlm_adjust = ch4_adjust
        init["base",3] = ch4_adjust
    pzt_adjust = -(f0 + wlm_adjust - f_eto)*pzt_per_fsr/fsr        

    initialize_Baseline()
    init[4,"strength"] = str4
    init[4,"y"] = y4
    init[2,"strength"] = str2
    init[2,"y"] = y2
    init[3,"y"] = 1.4092 + 0.0500*h2o_pct
    init[1002,2] = 0.1*ch4_ppm # ch4
    init[1002,5] = ch4_y
    init[1003,2] = 0.0 #nh3_ppb/50000
    #init[1004,2] = 0.0 # eto
    #init[1005,2] = h2o_pct  # h2o          #  Hitran model for all weak lines not modeled by Galatry functions
    #init[1006,2] = co2_ppm/400 # co2
    r = anETO[0](d,init,deps)
    ANALYSIS.append(r)
    eto_ppb = 0.0 #1000*r[1004,2] 
    eto_residuals = r["std_dev_res"]
    base0 = r["base",0]   
    base1 = r["base",1]
    base2 = r["base",2]    
    base3 = r["base",3]    
    rp00 = r[1000,0]
    rp02 = r[1000,2]
    rp03 = r[1000,3]
    rp10 = r[1001,0]
    rp12 = r[1001,2]
    rp13 = r[1001,3]
    ch4_ppm = 10*r[1002,2]
    ch4_y = r[1002,5]
    str4 = r[4,"strength"]
    peak4 = r[4,"peak"]
    base4 = r[4,"base"]
    h2o_pct = 0.0051678*str4           # From Hitran (class 7, 1-2%)   
    peak2 = r[2,"peak"]
    str2 = r[2,"strength"]
    if peak4 > 1 or ch4_ppm > 0.005: 
        wlm_adjust = base3
    pzt_adjust = -(f0 + wlm_adjust - f_eto)*pzt_per_fsr/fsr        
    
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

#if rp00 > -0.010 :
#    IgnoreThis = True
if not IgnoreThis:    
    RESULT = {"pzt_adjust":pzt_adjust,"pzt":pzt,"wlm_adjust":wlm_adjust,"tiptop":d.fitData["loss"][i0],"badGroups":badGroups,
            "Baseline_level":base0,"Baseline_slope":base1,"Baseline_curvature":base2,"base3":base3,"nh3_ppb":nh3_ppb,"tipstd":1000*d.groupStdDevs["uncorrectedAbsorbance"][i0],
            "ch4_shift":ch4_shift,"ch4_adjust":ch4_adjust,"ch4_vy":ch4_vy,"ch4_y":ch4_y,"ch4_ppm":ch4_ppm,
            "str2":str2,"y2":y2,"str8":str8,"str20":str20,"ch4_residuals":ch4_residuals,
            "co2_shift":co2_shift,"co2_adjust":co2_adjust,"str26":str26,"peak26":peak26,"base26":base26,"y26":y26,"co2_residuals":co2_residuals,
            "h2o_shift":h2o_shift,"h2o_adjust":h2o_adjust,"str4":str4,"peak4":peak4,"base4":base4,"y4":y4,"h2o_residuals":h2o_residuals,
            "co2_ppm":co2_ppm,"h2o_pct":h2o_pct,"eto_ppb":eto_ppb,"eto_residuals":eto_residuals,
            "dataGroups":d["ngroups"],"dataPoints":d["datapoints"],"pzt_per_fsr":pzt_per_fsr,    
            "Tcavity":T, "Pcavity":Pcavity,"stdPcavity":stdPcavity,
            "Sine0_ampl":rp00,"Sine0_period":rp02,"Sine0_phase":rp03,
            "Sine1_ampl":rp10,"Sine1_period":rp12,"Sine1_phase":rp13,
            "interval":interval,"fit_time":fit_time,"species":species
            }
    RESULT.update(d.sensorDict)
    

# if first_fit:
    # keys = sorted([k for k in RESULT])
    # st = " ".join(keys)
    # #print st
    # print>>out, st
    # first_fit = 0
# st1 = " ".join(["%s" % RESULT[k] for k in keys])
# #print st1
# print>>out, st1