#  G2000 isotopic methane and CO2 fitter

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

def initialize_CO2_Baseline():
    init["base",1] = co2_baseline_slope
    init[1000,0] = co2_A0
    init[1000,1] = co2_Nu0
    init[1000,2] = co2_Per0
    init[1000,3] = co2_Phi0
    init[1001,0] = co2_A1
    init[1001,1] = co2_Nu1
    init[1001,2] = co2_Per1
    init[1001,3] = co2_Phi1

def initialize_CH4_Baseline(sine_index):
    init["base",1] = ch4_baseline_slope
    init[sine_index,0] = ch4_A0
    init[sine_index,1] = ch4_Nu0
    init[sine_index,2] = ch4_Per0
    init[sine_index,3] = ch4_Phi0
    init[sine_index+1,0] = ch4_A1
    init[sine_index+1,1] = ch4_Nu1
    init[sine_index+1,2] = ch4_Per1
    init[sine_index+1,3] = ch4_Phi1

if INIT:
    fname = os.path.join(BASEPATH,r"./CFEDS/spectral library v7_isomethane_20100427.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anC12O2 = []
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./CFEDS/C12 only v1_0.ini")))
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./CFEDS/C12 only v1_1.ini")))

    anC13O2 = []
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./CFEDS/C13 only dev v1_1.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./CFEDS/C13 only VC VY v1_0.ini")))

    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFEDS/Isomethane_C12_C13_v7.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFEDS/Isomethane_CH3D_v6b.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFEDS/Isomethane_h2oregion_v1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFEDS/Isomethane_h2oregion_FY_v1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFEDS/Isomethane_C12_C13_H2O_v1.ini")))

    #  Import calibration constants from fitter_config.ini at initialization
    P88_off = instrParams['Peak88_offset']
    c12_base_ave = instrParams['C12_baseline']
    c13_base_ave = instrParams['C13_baseline']
    co2_baseline_slope = instrParams['CO2_Baseline_slope']
    co2_A0 = instrParams['CO2_Sine0_ampl']
    co2_Nu0 = instrParams['CO2_Sine0_freq']
    co2_Per0 = instrParams['CO2_Sine0_period']
    co2_Phi0 = instrParams['CO2_Sine0_phase']
    co2_A1 = instrParams['CO2_Sine1_ampl']
    co2_Nu1 = instrParams['CO2_Sine1_freq']
    co2_Per1 = instrParams['CO2_Sine1_period']
    co2_Phi1 = instrParams['CO2_Sine1_phase']
    ch4_baseline_slope = instrParams['CH4_Baseline_slope']
    ch4_A0 = instrParams['CH4_Sine0_ampl']
    ch4_Nu0 = instrParams['CH4_Sine0_freq']
    ch4_Per0 = instrParams['CH4_Sine0_period']
    ch4_Phi0 = instrParams['CH4_Sine0_phase']
    ch4_A1 = instrParams['CH4_Sine1_ampl']
    ch4_Nu1 = instrParams['CH4_Sine1_freq']
    ch4_Per1 = instrParams['CH4_Sine1_period']
    ch4_Phi1 = instrParams['CH4_Sine1_phase']

#   Globals for the isotopic CO2 fit
    counter = -25
    lastgood_shift_87 = 0
    lastgood_strength_87 = 0
    lastgood_y_87 = 0.0136
    lastgood_z_87 = 0.00438
    lastgood_y_88 = 0.01515
    lastgood_z_88 = 0.00488

    y_87 = 0.0
    z_87 = 0.0
    peak_87 = 0.0
    shift_87 = 0.0
    str_87 = 0.0
    base_87 = 0.0
    y_88 = 0.0
    z_88 = 0.0
    peak_88 = 0.0
    shift_88 = 0.0
    str_88 = 0.0
    base_88 = 0.0
    c13_base_ave = 0.0

    cm_adjust = 0.0
    initial_galratio = 0.0
    baseave_galratio = 0.0
    polybaseave_galratio = 0.0
    peak88_baseave = 0.0
    peak87_baseave = 0.0
    polypeak88_baseave = 0.0

#    ignore_count = 5

#   Globals for the isotopic methane fit
    ch4_res = 0
    ch3d_res = 0
    last_time = None
    Ilaserfine = 0
    peak2 = 0
    peak3 = 1e-10
    peak5 = 0
    peak12spline = 0
    peak13spline = 0
    c13toc12 = 0
    y2 = 0
    y3 = 0
    y5 = 0
    y12spline = 0
    base2 = 0
    base3 = 0
    base5 = 0
    str12spline = 0
    str13spline =0
    ch4_shift = 0
    ch4_adjust = 0
    ch3d_shift = 0
    ch3d_adjust = 0
    shift5 = 0
    h2o_shift = 0
    h2o_adjust = 0
    str31 = 0
    str12 = 0
    str24 = 0
    str33 = 0

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.0007,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.0007,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=3)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])

d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))
P = d["cavitypressure"]
T = d["cavitytemperature"]
dasTemp = d.sensorDict["DasTemp"]

species = (d.subschemeId & 0x1FF)[0]
#print "SpectrumId", d["spectrumId"]
init["base",0] = 750

tstart = time.clock()
RESULT = {}
r = None
species_code = 0
print "fitScript1 species = ", species

if species == 105:  # C12O2
    init[87,"scaled_y"] = 0.0136
    initialize_CO2_Baseline()
    r = anC12O2[0](d,init,deps)
    ANALYSIS.append(r)
    c12_y = r[87,"y"]
    pre_peak_87 = r[87,"peak"]
    cm_shift = r["base",3]
    c12_peak = r[87,"peak"]
    c12_res  = r["std_dev_res"]
    c12_fit_quality = fitQuality(c12_res,c12_peak,50,1)
    if (c12_fit_quality <= 1) and (peak_87 >= 20) and abs(r["base",3]) <= 0.07:
        init[87,"y"] = c12_y
        init["base",3] = cm_shift

    else:
        init[87,"y"] = lastgood_y_87*P
        init["base",3] = 0.0

    initialize_CO2_Baseline()
    r = anC12O2[1](d,init,deps)
    ANALYSIS.append(r)
    ini_used = 6
    c12_base = r[87,"base"]
    c12_peak = r[87,"peak"]
    c12_res  = r["std_dev_res"]
    c12_fit_quality = fitQuality(c12_res,c12_peak,50,1)
    peak_87 = r[87,"peak"]
    str_87 = r[87,"strength"]

    if (c12_fit_quality <= 1) and (peak_87 >= 20) and abs(r["base",3]) <= 0.07:
        c12_base_ave = initExpAverage(c12_base_ave,c12_base,3,50,counter)

        y_87 = r[87,"y"]
        z_87 = r[87,"z"]
        base_87 = r[87,"base"]
        slope_87 = r["base",1]
        shift_87 = r["base",3]
        lastgood_shift_87 = shift_87
        lastgood_strength_87 = str_87/P
        lastgood_y_87 = y_87/P
        lastgood_z_87 = z_87/P

        lastgood_y_88 = 1.114 * (y_87/P)
        lastgood_z_88 = 1.114 * (z_87/P)

        cm_adjust = cm_shift
    else:
        cm_adjust = 0.0

    peak_value_87 = peak_87 + base_87
    peak87_baseave = peak_value_87 - c12_base_ave
    c12_peak = peak87_baseave
    species_code = 5

elif species == 106:  # C13O2
    init["base",3] = lastgood_shift_87
    init[87,"scaled_strength"] = lastgood_strength_87
    init[87,"scaled_y"] = lastgood_y_87
    init[87,"scaled_z"] = lastgood_z_87
    init[88,"scaled_y"] = lastgood_y_88
    init[88,"scaled_z"] = lastgood_z_88
    initialize_CO2_Baseline()
    r = anC13O2[0](d,init,deps)
    ANALYSIS.append(r)
    ini_used = 1
    c13_base = r[88,"base"]
    c13_peak = r[88,"peak"]
    c13_res  = r["std_dev_res"]
    c13_fit_quality = fitQuality(c13_res,c13_peak,50,1)
    str_88 = r[88,"strength"]

    if (c13_fit_quality <= 1) and (peak_87 >= 20):
        shift_88 = r["base",3]
        y_88 = r[88,"y"]
        z_88 = r[88,"z"]
        slope_88 = r["base",1]
        quad_88 = r["base",2]
        base_88 = r[88,"base"]

        c13_base_ave = initExpAverage(c13_base_ave,c13_base,5,50,counter)

        initialize_CO2_Baseline()
        r = anC13O2[1](d,init,deps)
        ANALYSIS.append(r)
        abase2 = r["base",2]
        agalbase_88 = r[88,"base"]
        apeak88 = r[88,"peak"]
        acm_shift88 = r["base",3]
        ay_88 = r[88,"y"]
        abase1 = r["base",1]
    peak_88 = c13_peak + P88_off
    peak_value_88 = peak_88 + base_88
    peak88_baseave = peak_value_88 - c13_base_ave

elif species == 150:
    init[31,"strength"] = 0.2985*str33
    init[20,"strength"] = 0.0006321*str_87
    init[21,"strength"] = 0.00007838*str_87
    init[2,"y"] = 0.3790
    initialize_CH4_Baseline(1000)
    r = anCH4[0](d,init,deps)
    ANALYSIS.append(r)
    base3 = r[3,"base"]
    base2 = r[2,"base"]
    y2 = r[2,"y"]
    y3 = r[3,"y"]
    peak2 = r[2,"peak"]
    peak3 = r[3,"peak"]
    c13toc12 = peak2/peak3
    #c13toc12 = (1.767*peak2-0.546*r[2,"strength"])/(1.767*peak3-0.553*r[3,"strength"])
    ch4_shift = r["base",3]
    ch4_res = r["std_dev_res"]
    str31 = r[31,"strength"]

    if (peak3 > 4) and (abs(r["base",3]) < 0.07):   #  Center frequency used for WLM calibration if methane conc > 2 ppm
        ch4_adjust = ch4_shift
    elif (str33 > 10):
        init[31,"strength"] = 0.2985*str33
        init[20,"strength"] = 0.0006321*str_87
        init[21,"strength"] = 0.00007838*str_87
        init[2,"y"] = 0.3790
        initialize_CH4_Baseline(1000)
        r = anCH4[4](d,init,deps)
        ANALYSIS.append(r)
        ch4_adjust = ch4_shift = r["base",3]
    else:
        ch4_adjust = 0.0

    species_code = 1


elif species == 153:
    initialize_CO2_Baseline()
    r = anCH4[2](d,init,deps)
    ANALYSIS.append(r)
    if abs(r[33,"y"]-0.64) > 0.15:
        init[33,"y"] = 0.64
        initialize_CO2_Baseline()
        r = anCH4[3](d,init,deps)
        ANALYSIS.append(r)
    str12 = r[12,"strength"]
    str24 = r[24,"strength"]
    str33 = r[33,"strength"]
    h2o_shift = r["base",3]
    if r[12,"peak"] > 5 or r[24,"peak"] > 5 or r[33,"peak"] > 5:
       h2o_adjust = h2o_shift
    else:
       h2o_adjust = 0
    species_code = 3

elif species == 152:
    deps.setDep((1001,2),(1000,2),0.2555*c13toc12-0.4917,0) # set dependency from spectrumID150
    initialize_CH4_Baseline(1002)
    init[5,1] = 0.0
    init[5,"y"] = 0.51663 # set fixed Y value
    init[1001,2] = 0.0
    init[22,"strength"] = 0.001316*str_87
    r = anCH4[1](d,init,deps)
    ANALYSIS.append(r)
    base5 = r[5,"base"]
    y12spline = r[1000,5]
    y5 = r[5,"y"]
    peak12spline = r[1000,"peak",6055.30,6055.32]
    #peak13spline = r[1001,"peak"]
    str12spline = r[1000,2]
    str13spline = r[1001,2]
    peak5 = r[5,"peak"]
    ch3d_shift = r["base",3]
    shift5 = r[5,0]
    ch3d_res = r["std_dev_res"]
    if (peak12spline > 1) and (abs(r["base",3]) < 0.07):
        ch3d_adjust = ch3d_shift
    else:
        ch3d_adjust = 0.0
    species_code = 2

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
    RESULT = {"ch4_res":ch4_res,
            "peak3":peak3,"peak2":peak2,"c-13toc-12":c13toc12,"y3":y3,"y2":y2,"base3":base3,"base2":base2,
            "ch4_Ilaserfine":Ilaserfine,"ch4_shift":ch4_shift,"ch4_adjust":ch4_adjust,
            "str31":str31,"str12":str12,"str24":str24,"str33":str33,"h2o_shift":h2o_shift,"h2o_adjust":h2o_adjust,
            "ch3d_res":ch3d_res,"peak12spline":peak12spline,"peak13spline":peak13spline,"peak5":peak5,
            "base5":base5,"str12spline":str12spline,"str13spline":str13spline,
            "y12spline":y12spline,"y5":y5,"ch3d_shift":ch3d_shift,"ch3d_adjust":ch3d_adjust,"shift5":shift5,
            "interval":interval,"spectrum":species%4096,"datapoints":d["datapoints"],"datagroups":len(d.fitData["freq"]),
            "y_87":y_87,"z_87":z_87,"shift_87":shift_87,"str_87":str_87,"peak87_baseave":peak87_baseave,
            "y_88":y_88,"z_88":z_88,"shift_88":shift_88,"str_88":str_88,"peak88_baseave":peak88_baseave,"peak_88":peak_88,
            "cm_adjust":cm_adjust,"ratio_i":initial_galratio,"ratio_b":baseave_galratio,
            "species":species_code,"ch4_fittime":fit_time,
            "cavity_pressure":P,"cavity_temperature":T,"das_temp":dasTemp
            }
    RESULT.update(d.sensorDict)
