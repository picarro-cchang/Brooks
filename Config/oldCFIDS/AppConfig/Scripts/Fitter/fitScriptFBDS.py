#  G2000 isotopic methane fitter
#  Spectral IDs
#    105 -- (12)CO2 at 6251.758
#    106 -- (13)CO3 at 6251.315
#    150 -- (12)CH4 at 6028.5
#    151 -- (13)CH4 at 6029.1
#    152 -- H2O and NH3 at 6028.8
#    153 -- CO2 and ethylene at 6028.2 - 6028.5
#    154 -- Reserved for CH_3D at 6028.25

#  10 May 2011:  Corrected blunder in initialization of methane(12) spline (factor 1000 from ppb/ppm conventions)
#  16 May 2011:  Added fitter for water line at 6028.8 wvn
#  6 Jun 2011:   Start to merge with CFF iso-CO2 fitter (6251 wvn)
#  17 Nov 2011:  Fixed a bad bug in the peak 5 WLM adjust logic.

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

def initialize_CO2_Baseline(sine_index):
    init["base",1] = co2_baseline_slope
    init[sine_index,0] = co2_A0
    init[sine_index,1] = co2_Nu0
    init[sine_index,2] = co2_Per0
    init[sine_index,3] = co2_Phi0
    init[sine_index+1,0] = co2_A1
    init[sine_index+1,1] = co2_Nu1
    init[sine_index+1,2] = co2_Per1
    init[sine_index+1,3] = co2_Phi1

def initialize_CH4_Baseline():
    init["base",1] = ch4_baseline_slope
    init[1000,0] = ch4_A0
    init[1000,1] = ch4_Nu0
    init[1000,2] = ch4_Per0
    init[1000,3] = ch4_Phi0
    init[1001,0] = ch4_A1
    init[1001,1] = ch4_Nu1
    init[1001,2] = ch4_Per1
    init[1001,3] = ch4_Phi1

if INIT:
    fname = os.path.join(BASEPATH,r"./FBDS/spectral library FBDS v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/iCH4_C12only_v1_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/iCH4_C12only_FC_FY_v1_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/iCH4_C13only_v1_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/iCH4_C13only_FC_FY_v1_1.ini")))
    #anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/C12interferences_v1_1.ini")))

    anC12O2 = []
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C12 + CH4 v1_1_20100709.ini")))
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C12 only FC FY v1_2.ini")))

    anC13O2 = []
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_3.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_31+methane 20110217.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_31+CH4+18O 20110217.ini")))

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./FBDS/H2O_v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./FBDS/H2O_FC_FY_v1_1.ini")))

    #  Import calibration constants from fitter_config.ini at initialization
    P87_off = instrParams['Peak87_offset']
    P87_H1 = instrParams['Peak87_water']
    P88_off = instrParams['Peak88_offset']
    P88_off = instrParams['Peak88_offset']
    P88_H1 = instrParams['Peak88_water_linear']
    P88_H1A1 = instrParams['Peak88_bilinear']
    P88_H2A1 = instrParams['Peak88_quad_linear']
    P88_M1 = instrParams['Peak88_methane_linear']
    P88_M2 = instrParams['Peak88_methane_quadratic']
    P88_M1H1 = instrParams['Peak88_methane_H2O_bilinear']
    M1 = instrParams['Methane_lin']
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
    P0_off = instrParams['Peak0_offset']
    P5_off = instrParams['Peak5_offset']
    P30_off = instrParams['Peak30_offset']
    H1 = instrParams['Water_lin']
    H2 = instrParams['Water_quad']
    H1_wd = instrParams['Water_lin_wd']
    H2_wd = instrParams['Water_quad_wd']
    C12_conc_lin = instrParams['C12_lin']
    C13_conc_lin = instrParams['C13_lin']


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
    adjust_87 = 0.0
    str_87 = 0.0
    base_87 = 0.0
    y_88 = 0.0
    z_88 = 0.0
    peak_88 = 0.0
    shift_88 = 0.0
    adjust_88 = 0.0
    str_88 = 0.0
    base_88 = 0.0
    y87_ave = 1.708
    ch4_conc_12CO2 = 0.0

    cm_adjust = 0.0
    peak88_baseave = 0.0
    peak88_baseave_spec = 0.0
    peak87_baseave = 0.0
    peak87_baseave_spec = 0.0
    polypeak88_baseave = 0.0
    CO2_12_ppm_wet = 0.0
    CO2_13_ppm_wet = 0.0

#    ignore_count = 5

#   Globals for the isotopic methane fit
    ch4_res = 0
    last_time = None
    peak_0 = 1e-10
    peak0_spec = 1e-10
    peak_5 = 0
    peak5_spec = 0
    peak_20 = 0
    peak_30 = 0
    peak30_spec = 0
    c13toc12 = 0
    y_0 = 0
    vy_0 = 0
    y_5 = 0
    vy_5 = 0
    y_20 = 0
    vy_20 = 0
    y_30 = 0
    vy_30 = 0
    base_0 = 0
    base_5 = 0
    base_20 = 0
    base_30 = 0
    shift_0 = 0
    adjust_0 = 0
    shift_5 = 0
    adjust_5 = 0
    shift_20 = 0
    adjust_20 = 0
    shift_30 = 0
    adjust_30 = 0
    str_0 = 0
    C12H4_conc_raw = 0
    C13H4_conc_raw = 0
    delta_no_bookend = 0
    h2o_conc_pct = 0

    ntopper_12 = 0
    tiptop_12 = 0
    tipstd_12 = 0
    ntopper_13 = 0
    tiptop_13 = 0
    tipstd_13 = 0
    peakheight_5 = 0
    peakheight_ratio = 0
    delta_from_height = 0

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.30,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))

P = d["cavitypressure"]
T = d["cavitytemperature"]
dasTemp = d.sensorDict["DasTemp"]

species = (d.subschemeId & 0x1FF)[0]

tstart = time.clock()
RESULT = {}
r = None

if species == 105:  # C12O2
    init = InitialValues()
    initialize_CO2_Baseline(1001)
    r = anC12O2[0](d,init,deps)
    ANALYSIS.append(r)
    ch4_conc_12CO2 = M1*r[1000,2]
    vy_87 = r[87,"y"]
    pre_peak_87 = r[87,"peak"]
    pre_base_87 = r[87,"base"]
    cm_shift = r["base",3]

    initialize_CO2_Baseline(1000)
    if abs(cm_shift) > 0.07 or abs(vy_87-1.568) > 0.5 or pre_peak_87 < 10:
        init["base",3] = 0.0
        r = anC12O2[1](d,init,deps)
        ANALYSIS.append(r)
    peak_87 = r[87,"peak"]
    base_87 = r[87,"base"]
    y_87 = r[87,"y"]
    z_87 = r[87,"z"]
    c12_res  = r["std_dev_res"]
    c12_fit_quality = fitQuality(c12_res,peak_87,50,1)

    if abs(cm_shift) <= 0.07:
        c12_base_ave = initExpAverage(c12_base_ave,r[87,"base"],1,50,counter)
        base_87 = r[87,"base"]
        str_87 = r[87,"strength"]
        slope_87 = r["base",1]
        shift_87 = r["base",3]
        #y87_ave = initExpAverage(y87_ave,y_87,4,1,counter) - rella 2011 0301 changed source of y averaging to vy_87 to avoid CH4 crosstalk
        y87_ave = initExpAverage(y87_ave,vy_87,4,1,counter)
        z87_ave = y87_ave*0.3215
        peak_value_87 = peak_87 + base_87
        peak87_baseave = peak_value_87 - c12_base_ave

        lastgood_shift_87 = shift_87
        lastgood_strength_87 = str_87/P
        lastgood_y_87 = y87_ave/P
        lastgood_z_87 = z87_ave/P

        lastgood_y_88 = 1.114 * (y87_ave/P)
        lastgood_z_88 = 1.114 * (z87_ave/P)

        if peak_87 >= 20:
            adjust_87 = shift_87
        else:
            adjust_87 = 0.0
    else:
        adjust_87 = 0.0

    peak_value_87 = peak_87 + base_87
    peak87_baseave = peak_value_87 - c12_base_ave
    peak87_baseave_spec = peak87_baseave + P87_off + P87_H1*peak_30
    CO2_12_ppm_wet = C12_conc_lin*peak87_baseave_spec

elif d["spectrumId"] == 106 and d["ngroups"] >= 8:  # C13O2
    init = InitialValues()
    init[87,"scaled_strength"] = lastgood_strength_87
    init[87,"scaled_y"] = lastgood_y_87
    init[87,"scaled_z"] = lastgood_z_87
    init[88,"scaled_y"] = lastgood_y_88
    init[88,"scaled_z"] = lastgood_z_88
    initialize_CO2_Baseline(1000)
    r = anC13O2[0](d,init,deps)
    ANALYSIS.append(r)

    peak_88 = r[88,"peak"]
    c13_res  = r["std_dev_res"]
    c13_fit_quality = fitQuality(c13_res,peak_88,50,0.5)

    shift_88 = r["base",3]
    y88 = r[88,"y"]
    z88 = r[88,"z"]
    str_88 = r[88,"strength"]
    slope_88 = r["base",1]
    base_88 = r[88,"base"]
    c13_base_ave = initExpAverage(c13_base_ave,base_88,1,50,counter)
    peak_value_88 = peak_88 + base_88
    peak88_baseave = peak_value_88 - c13_base_ave

    init[1002,2] = C12H4_conc_raw*1e-4/M1
    initialize_CO2_Baseline(1000)
    r = anC13O2[2](d,init,deps)
    ANALYSIS.append(r)
    agalbase_88 = r[88,"base"]
    apeak88 = r[88,"peak"]
    shift_88 = r["base",3]
    ay_88 = r[88,"y"]
    abase1 = r["base",1]
    h2_18o = r[1003,2]
    #if (c13_fit_quality <= 0.6) and (ch4_conc_12CO2 <= 0.05) and (ch4_raw <= 0.01) and (apeak88 >= 2) and (abs(shift_88) <= 0.02):
    #if (c13_fit_quality <= 10) and (ch4_conc_12CO2 <= 0.5) and (ch4_raw <= 0.5) and (apeak88 >= 2) and (abs(shift_88) <= 0.02) and (ch4_conc_diff <= 5):
    if (c13_fit_quality <= 10) and (ch4_conc_12CO2 <= 0.5) and (apeak88 >= 2) and (abs(shift_88) <= 0.02):
        adjust_88 = shift_88
    else:
        adjust_88 = 0.0

    #  Spectral adjustments moved to here
    peak88_baseave_spec = peak88_baseave + P88_off + P88_H1*peak_30 + P88_H1A1*peak_30*peak87_baseave_spec + P88_H2A1*peak87_baseave_spec*peak_30**2
    peak88_baseave_spec += (P88_M1*peak0_spec + P88_M2*peak0_spec**2 + P88_M1H1*peak0_spec*peak_30)
    CO2_13_ppm_wet = C13_conc_lin*peak88_baseave_spec

elif species == 150:
    initialize_CH4_Baseline()
    r = anCH4[0](d,init,deps)
    ANALYSIS.append(r)
    shift_0 = r["base",3]
    vy_0 = r[0,"y"]

    if (peak_0 > 2) and (abs(shift_0) < 0.04) and (abs(vy_0-1.04) < 0.4):
        adjust_0 = shift_0
        init["base",3] = shift_0
        init[0,"y"] = vy_0
    else:
        adjust_0 = 0.0

    r = anCH4[1](d,init,deps)
    ANALYSIS.append(r)

    ch4_res = r["std_dev_res"]
    y_0 = r[0,"y"]
    base_0 = r[0,"base"]
    peak_0 = r[0,"peak"]
    str_0 = r[0,"strength"]

    peak0_spec = peak_0 + P0_off
    C12H4_conc_raw = 0.40148*peak_0
    c13toc12 = peak_5/peak_0
    delta_no_bookend = 1723.1*c13toc12 - 1000
    peakheight_ratio = peakheight_5/peak_0
    delta_from_height = 1723.1*peakheight_ratio - 1000

    f = d.waveNumber
    l = 1000*d.uncorrectedAbsorbance

    topper = (f >= 6028.552) & (f <= 6028.554)
    top_loss = l[topper]
    ntopper_12 = len(l[topper])
    if ntopper_12 > 0:
        good_topper = outlierFilter(top_loss,3)
        tiptop_12 = mean(top_loss[good_topper])
        tipstd_12 = std(top_loss[good_topper])
        ntopper_12 = len(top_loss[good_topper])
    else:
        tiptop = tipstd = 0.0

elif species == 151:
    initialize_CH4_Baseline()
    init[1002,2] = 0.001*str_0
    r = anCH4[2](d,init,deps)
    ANALYSIS.append(r)
    shift_5 = r["base",3]
    vy_5 = r[5,"y"]

    if (peak_5 > 2) and (abs(shift_5) < 0.04) and (abs(vy_5-0.87) < 0.4):
        adjust_5 = shift_5
        init["base",3] = shift_5
        init[5,"y"] = vy_5
    else:
        adjust_5 = 0.0

    r = anCH4[3](d,init,deps)
    ANALYSIS.append(r)

    ch4_res = r["std_dev_res"]
    y_5 = r[5,"y"]
    base_5 = r[5,"base"]
    peak_5 = r[5,"peak"]

    f = d.waveNumber
    l = 1000*d.uncorrectedAbsorbance

    topper = (f >= 6029.102) & (f <= 6029.104)
    top_loss = l[topper]
    ntopper_13 = len(l[topper])
    if ntopper_13 > 0:
        good_topper = outlierFilter(top_loss,3)
        tiptop_13 = mean(top_loss[good_topper])
        tipstd_13 = std(top_loss[good_topper])
        ntopper_13 = len(top_loss[good_topper])
        peakheight_5 = 0.9655*(tiptop_13 - base_5)  #Conversion from global peak to peak5 component
    else:
        tiptop = tipstd = peakheight_5 = 0.0

    peak5_spec = peakheight_5 + P5_off
    C13H4_conc_raw = 0.007772*peakheight_5

elif species == 152:
    initialize_CH4_Baseline()
    #init[1002,2] = 0.001*str_0
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    shift_30 = r["base",3]
    vy_30 = r[30,"y"]

    if (peak_30 > 2) and (abs(shift_30) < 0.04) and (abs(vy_30-1.09) < 0.4):
        adjust_30 = shift_30
    else:
        adjust_30 = 0.0
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)

    shift_30 = r["base",3]
    y_30 = r[30,"y"]
    base_30 = r[30,"base"]
    peak_30 = r[30,"peak"]
    peak30_spec = peak_30 + P30_off
    h2o_conc_pct = peak_30/61.0

elif species == 153:
    initialize_CH4_Baseline()
    initialize[0,"strength"] = 0.001*str_0
    initialize[0,"y"] = y0
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    shift_20 = r["base",3]
    vy_20 = r[20,"y"]

    if (peak_20 > 2) and (abs(shift_20) < 0.04) and (abs(vy_20-1.09) < 0.4):
        adjust_20 = shift_20
    else:
        adjust_20 = 0.0

    y_20 = r[20,"y"]
    base_20 = r[20,"base"]
    peak_20 = r[20,"peak"]

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
    RESULT = {"ch4_res":ch4_res,"12CH4_raw":C12H4_conc_raw,"13CH4_raw":C13H4_conc_raw,
            "peak0_spec":peak0_spec,"peak5_spec":peak5_spec,"peak30_spec":peak30_spec,
            "delta_no_bookend":delta_no_bookend,"c-13toc-12":c13toc12,
            "vy_0":vy_0,"y_0":y_0,"base_0":base_0,"shift_0":shift_0,"adjust_0":adjust_0,
            "vy_5":vy_5,"y_5":y_5,"base_5":base_5,"shift_5":shift_5,"adjust_5":adjust_5,
            "vy_20":vy_20,"y_20":y_20,"base_20":base_20,"shift_20":shift_20,"adjust_20":adjust_20,
            "vy_30":vy_30,"y_30":y_30,"base_30":base_30,"shift_30":shift_30,"adjust_30":adjust_30,
            "peak_0":peak_0,"str_0":str_0,"peak_5":peak_5,"peak_20":peak_20,"peak_30":peak_30,
            "interval":interval,"datapoints":d["datapoints"],"datagroups":d["ngroups"],
            "y_87":y_87,"z_87":z_87,"shift_87":shift_87,"str_87":str_87,"peak87_baseave":peak87_baseave,
            "y_88":y_88,"z_88":z_88,"shift_88":shift_88,"str_88":str_88,"peak88_baseave":peak88_baseave,
            "peak_88":peak_88,"peak87_baseave_spec":peak87_baseave_spec,"peak88_baseave_spec":peak88_baseave_spec,
            "adjust_87":adjust_87,"adjust_88":adjust_88,"12CO2_ppm_wet":CO2_12_ppm_wet,"13CO2_ppm_wet":CO2_13_ppm_wet,
            "cm_adjust":cm_adjust,"h2o_conc_pct":h2o_conc_pct,"peak30_spec":peak30_spec,
            "ntopper_12":ntopper_12,"tiptop_12":tiptop_12,"tipstd_12":tipstd_12,
            "ntopper_13":ntopper_13,"tiptop_13":tiptop_13,"tipstd_13":tipstd_13,
            "peakheight_5":peakheight_5,"peakheight_ratio":peakheight_ratio,
            "delta_from_height":delta_from_height,
            "species":species,"fittime":fit_time,
            "cavity_pressure":P,"cavity_temperature":T,"das_temp":dasTemp
            }
    RESULT.update(d.sensorDict)
