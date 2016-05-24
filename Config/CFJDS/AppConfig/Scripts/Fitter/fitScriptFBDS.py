#  G2000 isotopic methane fitter for special-purpose Caltech/PEER instrument
#  Measures D/H as well as C-13/C12 and accepts very high methane concentration
#  Spectral IDs
#    105 -- (12)CO2 at 6251.758
#    106 -- (13)CO3 at 6251.315
#    150 -- Isomethane and water vapor from 6028.4 to 6029.4
#    154 -- CH_3D at 6028.25

#  14 Aug 2011:  Adapted from standard C-13/C-12 fitter using the 6029 wvn lines
#  31 Oct 2011:  Major change -- use bispline for methane instead of spline to deal with self-broadening over large concentration range.
#    1 Nov 2011:  Added offset and quadratic corrections for 13CH4 and CH3D splines (self-broadening)
#  17 Nov 2011:  Fixed a bad bug in the peak 5 WLM adjust logic.
#  17 Nov 2011:  Changed sigma filter on WLM setpoint from 3 to 10
#  14 Feb 2012:  Added spectral ID 109 for water measurement in CH3D mode
#  17 Feb 2012:  Changed quad corr for both CH3D and 13CH4 to bilinear

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

def initialize_CH4_Baseline_6023():
    init["base",1] = ch4_6023_baseline_slope
    init[1000,0] = ch4_6023_A0
    init[1000,1] = ch4_6023_Nu0
    init[1000,2] = ch4_6023_Per0
    init[1000,3] = ch4_6023_Phi0
    init[1001,0] = ch4_6023_A1
    init[1001,1] = ch4_6023_Nu1
    init[1001,2] = ch4_6023_Per1
    init[1001,3] = ch4_6023_Phi1

if INIT:
    fname = os.path.join(BASEPATH,r"./FBDS/spectral library FBDS+D v2_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/iCH4_C12only_v2_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/iCH4_C12only_FC_FY_v2_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/iCH4_C13only_v2_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/iCH4_C13only_FC_FY_v2_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/CH4+C2H6+H2O_FC_v2_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/iCH4_deuterium_bispline.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FBDS/iCH4_deuterium_bispline_FC.ini")))

    anC12O2 = []
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C12 + CH4 v1_1_20100709.ini")))
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C12 only FC FY v1_2.ini")))

    anC13O2 = []
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_3.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_31+methane 20110217.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_31+CH4+18O 20110217.ini")))

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./FBDS/H2O_v2_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./FBDS/H2O_FC_FY_v2_1.ini")))

    an109 = []
    an109.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/6250_4 2_H2O + 2_HDO + CO2 spline_20100915.ini")))
    an109.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/6250_4 FC 2_H2O + 2_HDO + CO2 spline_20100915.ini")))
    an109.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/Methane dev 1_1 20100709.ini")))

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
    ch4_baseline_level = instrParams['CH4_Baseline_level']
    ch4_baseline_slope = instrParams['CH4_Baseline_slope']
    ch4_A0 = instrParams['CH4_Sine0_ampl']
    ch4_Nu0 = instrParams['CH4_Sine0_freq']
    ch4_Per0 = instrParams['CH4_Sine0_period']
    ch4_Phi0 = instrParams['CH4_Sine0_phase']
    ch4_A1 = instrParams['CH4_Sine1_ampl']
    ch4_Nu1 = instrParams['CH4_Sine1_freq']
    ch4_Per1 = instrParams['CH4_Sine1_period']
    ch4_Phi1 = instrParams['CH4_Sine1_phase']
    ch4_6023_baseline_level = instrParams['CH4_6023_Baseline_level']
    ch4_6023_baseline_slope = instrParams['CH4_6023_Baseline_slope']
    ch4_6023_A0 = instrParams['CH4_6023_Sine0_ampl']
    ch4_6023_Nu0 = instrParams['CH4_6023_Sine0_freq']
    ch4_6023_Per0 = instrParams['CH4_6023_Sine0_period']
    ch4_6023_Phi0 = instrParams['CH4_6023_Sine0_phase']
    ch4_6023_A1 = instrParams['CH4_6023_Sine1_ampl']
    ch4_6023_Nu1 = instrParams['CH4_6023_Sine1_freq']
    ch4_6023_Per1 = instrParams['CH4_6023_Sine1_period']
    ch4_6023_Phi1 = instrParams['CH4_6023_Sine1_phase']
    P0_off = instrParams['Peak0_offset']
    P5_off = instrParams['Peak5_offset']
    P5_quad = instrParams['Peak5_quad']
    P5_A1 = instrParams['Peak5_CO2_lin']
    P5_H1 = instrParams['Peak5_water_lin']
    P5_Et1 = instrParams['Peak5_ethane_lin']
    P30_off = instrParams['Peak30_offset']
    P30_M1 = instrParams['Peak30_methane_linear']
    S13_off = instrParams['C13spline_offset']
    S13_quad = instrParams['C13spline_quad']
    SD_off = instrParams['Dspline_offset']
    SD_quad = instrParams['Dspline_quad']
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
    ch4_res12 = 0
    ch4_res13 = 0
    ch4_res_w = 0
    HC_res = 0
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
    str_30 = 0
    C12H4_conc_raw = 0
    C13H4_conc_raw = 0
    delta_no_bookend = 0
    h2o_conc_pct = 0
    ch4_conc_diff = 0
    C12H4_conc_raw_old = 0
    ch4_from_h2o = 0

    ntopper_12 = 0
    tiptop_12 = 0
    tipstd_12 = 0
    ntopper_13 = 0
    tiptop_13 = 0
    tipstd_13 = 0
    peakheight_0 = 0
    peakheight_5 = 0
    peakheight_ratio = 0
    delta_from_height = 0

    HC_base_offset = 0
    HC_slope_offset = 0
    HC_shift = 0
    HC_CH4_conc = 0
    HC_C12_conc = 0
    HC_H2O_conc = 0
    HC_C2H6_conc = 0

    shift154 = 0
    adjust154 = 0
    y_eff = 0
    ch4_squish = 0
    amp_CH4_spline = 0
    amp_CH3D_spline = 0
    amp_13CH4_spline = 0
    CH3D_spline_corrected = 0
    C13_spline_corrected = 0
    CH4_6023_conc = 0
    ch4_res_6023 = 0

    peak_91 = 0.0
    shift_91 = 0.0
    adjust_91 = 0.0
    h2o_6250_reg = 0.0
    co2_water_reg = 0.0
    ch4_conc_h2o = 0.0

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.30,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=10)
d.sparse(maxPoints=1000,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
#d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.calcGroupStats()
d.calcSpectrumStats()

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
    #if (c13_fit_quality <= 10) and (ch4_conc_12CO2 <= 0.5) and (apeak88 >= 2) and (abs(shift_88) <= 0.02):
    if (c13_fit_quality <= 10) and (ch4_conc_12CO2 <= 0.5) and (apeak88 >= 2) and (abs(shift_88) <= 0.02) and (ch4_conc_diff <= 5):
        adjust_88 = shift_88
    else:
        adjust_88 = 0.0

    #  Spectral adjustments moved to here
    peak88_baseave_spec = peak88_baseave + P88_off + P88_H1*peak30_spec + P88_H1A1*peak30_spec*peak87_baseave_spec + P88_H2A1*peak87_baseave_spec*peak30_spec**2
    peak88_baseave_spec += (P88_M1*peak_0 + P88_M2*peak_0**2 + P88_M1H1*peak_0*peak30_spec)
    CO2_13_ppm_wet = C13_conc_lin*peak88_baseave_spec

elif d["spectrumId"] == 109:  # H2O at 6250.4 wvn
    #  Variable peak water fitter
    initialize_CO2_Baseline(1002)
    r = an109[0](d,init,deps)
    ANALYSIS.append(r)
    shift_91 = r["base",3]
    adjust_91 = shift_91
    if (abs(shift_91) > 0.03) or (r[91,"peak"] < 7):
        #  Fixed peak water fitter
        r = an109[1](d,init,deps)
        ANALYSIS.append(r)
        shift_91 = r["base",3]
        adjust_91 = 0.0
    peak_91 = r[91,"peak"]
    y_91 = r[91,"y"]
    z_91 = r[91,"z"]
    peak_96 = r[96,"peak"]
    h2o_6250_reg = 0.0148*peak_91
    co2_water_reg = 5064*r[1000,2]
    ch4_conc_h2o = M1*r[1001,2]
    #  CO2 and CH4 fitter
    # r = anH2O[2](d,init,deps)
    # ANALYSIS.append(r)
    # shift_91 = r["base",3]
    # ch4_raw = r[1001,2]
    # c2h4_conc = 0.4*r[1000,2]
    # peak_92 = r[92,"peak"]
    # ch4_ampl = r[1001,2]

elif species == 150:
    initialize_CH4_Baseline()
    r = anCH4[0](d,init,deps)   #  First fit (12)CH4
    ANALYSIS.append(r)
    shift_0 = r["base",3]
    vy_0 = r[0,"y"]

    if (peak_0 > 2) and (abs(shift_0) < 0.04) and (abs(vy_0-1.18) < 0.3):
        adjust_0 = shift_0
        init["base",3] = shift_0
        init[0,"y"] = vy_0
    else:
        adjust_0 = 0.0

    r = anCH4[1](d,init,deps)
    ANALYSIS.append(r)

    ch4_res12 = r["std_dev_res"]
    y_0 = r[0,"y"]
    base_0 = r[0,"base"]
    peak_0 = r[0,"peak"]
    str_0 = r[0,"strength"]

    #peak0_spec = peak_0 + P0_off
    #C12H4_conc_raw = 0.40148*peak_0
    C12H4_conc_raw = 0.40148*peak_0/0.84

    ch4_conc_diff = abs(C12H4_conc_raw_old - C12H4_conc_raw)
    C12H4_conc_raw_old = C12H4_conc_raw

    f = d.waveNumber
    l = 1000*d.uncorrectedAbsorbance

    topper_12 = (f >= 6028.552) & (f <= 6028.554)
    top_loss_12 = l[topper_12]
    ntopper_12 = len(l[topper_12])
    if ntopper_12 > 0:
        good_topper_12 = outlierFilter(top_loss_12,3)
        tiptop_12 = mean(top_loss_12[good_topper_12])
        tipstd_12 = std(top_loss_12[good_topper_12])
        ntopper_12 = len(top_loss_12[good_topper_12])
        peakheight_0 = (tiptop_12 - base_0)
    else:
        tiptop_12 = tipstd_12 = peakheight_0 = 0.0

    peak0_spec = peakheight_0 + P0_off

    init["base",3] = 0
    r = anH2O[0](d,init,deps)   #  Next fit the water region with overlaping methane
    ANALYSIS.append(r)
    shift_30 = r["base",3]
    vy_30 = r[30,"y"]

    if (r[30,"peak"] > 5) and (abs(shift_30) < 0.04) and (abs(vy_30-1.35) < 0.5):
        #  If the water peak is strong and believeable, use it as is
        adjust_30 = shift_30
    elif (r[8,"peak"] > 5) and (abs(shift_30) < 0.04):
        #  If water is weak but methane is strong, use methane centration and fixed nominal ys
        adjust_30 = shift_30
        init["base",3] = shift_30
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
    else:
        #  If water and methane are both weak, use FY FC at nominal center frequency to estimate water
        adjust_30 = 0.0
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)

    ch4_res_w = r["std_dev_res"]
    y_30 = r[30,"y"]
    base_30 = r[30,"base"]
    peak_30 = r[30,"peak"]
    str_30 = r[30,"strength"]
    peak30_spec = peak_30 + P30_off + P30_M1*peak_0
    h2o_conc_pct = peak_30/61.0
    ch4_from_h2o = 1.5621*r[8,"peak"]

    init["base",3] = 0
    init[1002,2] = str_0   #  Now initialize (12)CH4 spline and fit the (13)CH4 triplet
    r = anCH4[2](d,init,deps)
    ANALYSIS.append(r)
    shift_5 = r["base",3]
    vy_5 = r[5,"y"]

    if (peak_5 > 2) and (abs(shift_5) < 0.04) and (abs(vy_5-1.14) < 0.3):
        adjust_5 = shift_5
        init["base",3] = shift_5
        init[5,"y"] = vy_5
    else:
        adjust_5 = 0.0

    r = anCH4[3](d,init,deps)
    ANALYSIS.append(r)

    ch4_res13 = r["std_dev_res"]
    y_5 = r[5,"y"]
    base_5 = r[5,"base"]
    peak_5 = r[5,"peak"]

    topper_13 = (f >= 6029.102) & (f <= 6029.104)
    top_loss_13 = l[topper_13]
    ntopper_13 = len(l[topper_13])
    if ntopper_13 > 0:
        good_topper_13 = outlierFilter(top_loss_13,3)
        tiptop_13 = mean(top_loss_13[good_topper_13])
        tipstd_13 = std(top_loss_13[good_topper_13])
        ntopper_13 = len(top_loss_13[good_topper_13])
        peakheight_5 = 0.9655*(tiptop_13 - base_5)  #Conversion from global peak to peak5 component
    else:
        tiptop_13 = tipstd_13 = peakheight_5 = 0.0

#  Apply corrections to isotopic peak height here
    peak5_spec = peakheight_5 + P5_off + P5_quad*peak_0 + P5_A1*peak_88 + P5_H1*peak30_spec
    C13H4_conc_raw = 0.007772*peakheight_5/0.84

#  Calculate isotopic ratio and delta
    c13toc12 = peak_5/peak_0
    delta_no_bookend = 1723.1*c13toc12 - 1000
    peakheight_ratio = peakheight_5/peakheight_0
    delta_from_height = 1723.1*peakheight_ratio - 1000

    init["base",3] = 0
    init[0,"strength"] = 0
    init[0,"y"] = y_0
    init[30,"strength"] = str_30
    init[30,"y"] = y_30
    init[1002,2] = 0.001*str_0   #  Finally fit the entire spectrum looking for ethane on top of methane and water
    r = anCH4[4](d,init,deps)
    ANALYSIS.append(r)
    HC_res = r["std_dev_res"]
    HC_base_offset = r["base",0]-ch4_baseline_level
    HC_slope_offset = r["base",1]-ch4_baseline_slope
    HC_shift = r["base",3]
    HC_CH4_conc = 100*r[1002,2]
    HC_C12_conc = 0.40148*r[0,"peak"]/0.84
    HC_H2O_conc = r[30,"peak"]/61.0
    HC_C2H6_conc = 400*r[1003,2]

    peak5_spec += P5_Et1*HC_C2H6_conc   #  2011 Aug 10 added ethane crosstalk correction, hoffnagle

elif species == 154 or species == 0:
    initialize_CH4_Baseline_6023()
    init[1005,2] = CO2_12_ppm_wet/3003
    r = anCH4[5](d,init,deps)
    ANALYSIS.append(r)
    shift154 = r["base",3]
    y_eff = r[1002,5]
    ch4_squish = r["base",4]

    if (r[1002,2] > 0.5) and (abs(shift_20) < 0.05):
        adjust154 = shift154
        init[1002,5] = y_eff
        init["base",4] = ch4_squish
    else:
        adjust154 = 0.0
        init[1002,5] = 1.057

    init["base",3] = adjust154
    r = anCH4[6](d,init,deps)
    ANALYSIS.append(r)

    amp_CH4_spline = r[1002,2]
    amp_CH3D_spline = r[1003,2]
    amp_13CH4_spline = r[1004,2]
    CH4_6023_conc = 100*amp_CH4_spline
    ch4_res_6023 = r["std_dev_res"]
    #CH3D_spline_corrected = amp_CH3D_spline + SD_off + SD_quad*amp_CH4_spline**2
    #C13_spline_corrected = amp_CH3D_spline + S13_off + S13_quad*amp_CH4_spline**2
    CH3D_spline_corrected = amp_CH3D_spline + SD_off + SD_quad*amp_CH4_spline*amp_CH3D_spline
    C13_spline_corrected = amp_13CH4_spline + S13_off + S13_quad*amp_CH4_spline*amp_13CH4_spline

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
    RESULT = {"ch4_res12":ch4_res13,"ch4_res13":ch4_res12,"ch4_res_w":ch4_res_w,
            "12CH4_raw":C12H4_conc_raw,"13CH4_raw":C13H4_conc_raw,"HC_res":HC_res,
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
            "delta_from_height":delta_from_height,"ch4_from_h2o":ch4_from_h2o,
            "species":species,"fittime":fit_time,"peakheight_0":peakheight_0,
            "HC_base_offset":HC_base_offset,"HC_slope_offset":HC_slope_offset,
            "HC_shift":HC_shift,"HC_CH4_conc":HC_CH4_conc,"HC_C12_conc":HC_C12_conc,
            "HC_H2O_conc":HC_H2O_conc,"HC_C2H6_conc":HC_C2H6_conc,"y_eff":y_eff,"ch4_squish":ch4_squish,
            "adjust154":adjust154,"shift154":shift154,"ch4_res_6023":ch4_res_6023,"CH4_6023_conc":CH4_6023_conc,
            "amp_CH4_spline":amp_CH4_spline,"amp_13CH4_spline":amp_13CH4_spline,"amp_CH3D_spline":amp_CH3D_spline,
            "C13_spline_corrected":C13_spline_corrected,"CH3D_spline_corrected":CH3D_spline_corrected,
            "peak_91":peak_91,"shift_91":shift_91,"adjust_91":adjust_91,
            "h2o_6250_reg":h2o_6250_reg,"co2_water_reg":co2_water_reg,"ch4_conc_h2o":ch4_conc_h2o,
            "cavity_pressure":P,"cavity_temperature":T,"das_temp":dasTemp
            }
    RESULT.update(d.sensorDict)
    RESULT.update(d.selectGroupStats([("peak12",6022.7490),("peakD",6022.624),("peak13",6022.411)]))
    RESULT.update(d.getSpectrumStats())
