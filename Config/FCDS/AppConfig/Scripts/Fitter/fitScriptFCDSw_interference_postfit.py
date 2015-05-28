#  G2000 isotopic methane fitter for the FCDS variation -- C-13/C-12 only with CFADS spectroscopy for C-12 measurement
#  Spectral IDs
#      11 -- H2O at 6057.8 (CFADS)
#    150 -- Isomethane and water vapor from 6028.4 to 6029.4 combined with CFADS methane at 6057 wvn.
#    153 -- (12)CO2 at 6056.7

#  09 Sep 2011:  Adapted from earlier CBDS and CFIDS fitters
#  07 Nov 2011:  New variant for potential PG&E application with different schemes:  6029 and 6057 regions collected as 1 SID
#  17 Nov 2011:  Fixed a bad bug in the peak 5 WLM adjust logic.  Consolidated concentration calibration factors and adjusted to match CFADS on FCDS2003.
#  17 Nov 2011:  Changed sigma filter on WLM setpoint from 3 to 10
#  18 Nov 2011:  Changed VC water fit to fix methane y-parameter and increased minimum peak requirement for water WLM adjust.
#  01 Dec 2011:  Major change -- merged with the fitter  variant developed for PG&E(R:\crd_G2000\FCDS\1061-FCDS2003\Config\20111122)
#  02 Dec 2011:  Fixed major bug in initialization of 6057 methane (high precision) fit for merged fitter.
#  06 Dec 2011:  Removed base average from CFADS CH4 fitter
#  10 Jan 2012:  Fixed y-parameter of C-13 triplet fit based on y of C-12 singlet (more stable at low concentration)
#  20 Jan 2012:  Include neighboring CO2 peaks in methane region fits to improve WLM tracking for low methane and high [CO2]
#  27 Apr 2012:  Incorporated improvements from CFIDS fitter:  (1) CO2 lines in spectral model for 6029 region;
#                (2) W/D calculation; (3) initialization of y_5 based on y_0; (4) newer spectral library
#  29 May 2012:  Removed bogus factor 0.84 from methane conc conversion in 6029 wvn region (messed up 6056 spline)
#  28 Feb 2013:  Fixed logic in shift/adjust of SID 153 (CO2 at 6056.5)
#   7 Jun 2013:  Fixed bug in HP methane -- WLM adjust was stuck when measurement 6057 wvn inactive
#  17 Sep 2013:  Added post-fit for ethylene, ammonia, and hydrogen sulfide.
#  19 Nov 2013:  Fixed minor bug in logic for adjust_0 = 0 and adjust_5 = 0.
#  27 Jan 2014:  Initialized methane amplitude in water fit (peak8) using peak0 amplitude

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

def initialize_CFADS_Baseline():
    init["base",1] = CFADS_baseline_slope
    init[1000,0] = CFADS_A0
    init[1000,1] = CFADS_Nu0
    init[1000,2] = CFADS_Per0
    init[1000,3] = CFADS_Phi0
    init[1001,0] = CFADS_A1
    init[1001,1] = CFADS_Nu1
    init[1001,2] = CFADS_Per1
    init[1001,3] = CFADS_Phi1

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
    fname = os.path.join(BASEPATH,r"./FCDS/spectral library FCDS v2_2.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/iCH4_C12only_v3_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/iCH4_C12only_FC_FY_v3_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/iCH4_C13only_v3_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/iCH4_C13only_FC_FY_v3_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/CH4+C2H6+H2O+CO2_v1_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/C12interferences_v1_1.ini")))

    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./FCDS/CO2 6056 VC VY v1_1.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./FCDS/CO2 6056 FC FY v1_1.ini")))

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./FCDS/H2O_v3_2.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./FCDS/H2O_FC_FY_v3_1.ini")))

    an12CH4 = []
    an12CH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 v2_1 2008 0304.ini")))
    an12CH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC VY v2_0 2008 0304.ini")))
    an12CH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC FY v2_0 2008 0304.ini")))

    anH2OCFADS = []
    anH2OCFADS.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 v1_2 2011 0328.ini")))
    anH2OCFADS.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 FC v1_1 2011 0309.ini")))
    anH2OCFADS.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 v1_1 2011 0309.ini")))

    #  Import calibration constants from fitter_config.ini at initialization
    CFADS_baseline_level = instrParams['CFADS_baseline']
    CFADS_baseline_slope = instrParams['CFADS_Baseline_slope']
    CFADS_A0 = instrParams['CFADS_Sine0_ampl']
    CFADS_Nu0 = instrParams['CFADS_Sine0_freq']
    CFADS_Per0 = instrParams['CFADS_Sine0_period']
    CFADS_Phi0 = instrParams['CFADS_Sine0_phase']
    CFADS_A1 = instrParams['CFADS_Sine1_ampl']
    CFADS_Nu1 = instrParams['CFADS_Sine1_freq']
    CFADS_Per1 = instrParams['CFADS_Sine1_period']
    CFADS_Phi1 = instrParams['CFADS_Sine1_phase']
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

    H1_wd = instrParams['Water_lin_wd']
    H2_wd = instrParams['Water_quad_wd']

    H1_wd_CFADS_CH4 = instrParams['Water_lin_wd_CFADS_CH4']
    H2_wd_CFADS_CH4 = instrParams['Water_quad_wd_CFADS_CH4']

    H1_wd_iCH4 = instrParams['Water_lin_wd_iCH4']
    H2_wd_iCH4 = instrParams['Water_quad_wd_iCH4']

    P0_off = instrParams['Peak0_offset']
    P5_off = instrParams['Peak5_offset']
    P5_quad = instrParams['Peak5_quad']
    P5_A1 = instrParams['Peak5_CO2_lin']
    P5_H1 = instrParams['Peak5_water_lin']
    P5_M1H1 = instrParams['Peak5_water_CH4_bilin']
    P30_off = instrParams['Peak30_offset']
    P30_M1 = instrParams['Peak30_methane_linear']
    P24_off = instrParams['Peak24_offset']
    P24_M1 = instrParams['Peak24_methane_linear']
    H1 = instrParams['Water_lin']
    H2 = instrParams['Water_quad']
    C12_conc_lin = instrParams['C12_lin']

#   Globals for the isotopic methane fit
    ch4_res12 = 0
    ch4_res13 = 0
    ch4_res_w = 0
    HC_res = 0
    last_time = None
    peak_0 = 1e-10
    peak0_spec = 1e-10
    peak0_spec_dry = 1e-10
    peak_5 = 0
    peak5_spec = 0
    peak5_spec_dry = 0
    peak_20 = 0
    peak_30 = 0
    peak24_spec = 0
    peak30_spec = 0
    c13toc12 = 0
    y_0 = 0
    vy_0 = 0
    y_5 = 0
    vy_5 = 0
    y_24 = 0
    vy_24 = 0
    y_30 = 0
    vy_30 = 0
    base_0 = 0
    base_5 = 0
    base_24 = 0
    base_30 = 0
    shift_0 = 0
    adjust_0 = 0
    shift_5 = 0
    adjust_5 = 0
    shift_24 = 0
    adjust_24 = 0
    shift_30 = 0
    adjust_30 = 0
    str_0 = 0
    str_30 = 0
    C12H4_conc_raw = 0
    C12H4_conc_raw_dry = 0
    C12H4_conc_up = 0
    C12H4_conc_down = 0
    C12H4_time_separation = 0
    C13H4_conc_raw = 0
    C13H4_conc_raw_dry = 0
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

    PPF_res = 0
    PPF_base_offset = 0
    PPF_slope_offset = 0
    PPF_shift = 0
    PPF_CH4_conc = 0
    PPF_C12_conc = 0
    PPF_H2O_conc = 0
    PPF_C2H6_conc = 0
    PPF_C2H4_conc = 0
    PPF_NH3_conc = 0
    PPF_H2S_conc = 0

# CFADS 12CH4 and H2O
    peak_75 = 0.0
    base_75 = 0.0
    str_75 = 0.0
    y_75 = 0.0
    shift_75 = 0.0
    h2o_conc = 0.0
    CFADS_h2o_conc = 0.0
    adjust_75 = 0.0

    CFADS_counter = -25
    CFADS_base = 0.0
    CFADS_base_avg = instrParams['CFADS_baseline']
    ch4_low_shift = 0.0
    ch4_high_shift = 0.0
    ch4_high_adjust = 0.0
    CFADS_ch4_amp = 0.0
    ch4_splinemax = 0.5
    ch4_splinemax_dry = 0.5
    ch4_splinemax_for_correction = 0.0
    ch4_vy = 0.0
    ch4_y_avg = 1.08
    ch4_conc_ppmv_final = 0.0
    ch4_conc_ppmv_final_dry = 0.0
    ch4_conc_for_correction = 0.0
    ch4_conc_diff = 0.0
    ch4_from_h2o = 0.0
    CFADS_ch4_y = 0.0

#  New CO2 in CFADS methane region (6056.6 wvn)
    adjust_24 = 0.0
    shift_24 = 0.0
    strength_24 = 0.0
    y_24 = 0.0
    base_24 = 0.0
    peak_24 = 0.0
    co2_conc = 0.0

    ignore_count = 5
    last_time = None

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.30,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=10)
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

in25 = (d.fitData["freq"] >= 6056.81) & (d.fitData["freq"] <= 6057.39)
good25 = sum(in25)
in150 = (d.fitData["freq"] >= 6028.4) & (d.fitData["freq"] <= 6029.2)
good150 = sum(in150)

if species == 150 and good150 > 35:
    initialize_CH4_Baseline()
    init[20,"strength"] = 0.07726*strength_24
    r = anCH4[0](d,init,deps)   #  First fit (12)CH4
    ANALYSIS.append(r)
    shift_0 = r["base",3]
    vy_0 = r[0,"y"]
    if (r[0,"peak"] > 2) and (abs(shift_0) < 0.04) and (abs(vy_0-1.18) < 0.3):
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

    C12H4_conc_raw = 0.40148*peak_0
    ch4_conc_diff = abs(C12H4_conc_raw_old - C12H4_conc_raw)
    C12H4_conc_raw_old = C12H4_conc_raw

    f = d.waveNumber
    l = 1000*d.uncorrectedAbsorbance
    up_flag = (d.extra1 > 0)
    down_flag = (d.extra1 == 0)
    t = d.timestamp

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

    topper_12u = topper_12 & up_flag
    top_loss_12u = l[topper_12u]
    t_12u = t[topper_12u]
    ntopper_12u = len(l[topper_12u])
    if ntopper_12u > 0:
        good_topper_12u = outlierFilter(top_loss_12u,3)
        tiptop_12u = mean(top_loss_12u[good_topper_12u])
        time_12u = mean(t_12u[good_topper_12u])
        peakheight_0u = (tiptop_12u - base_0)
    else:
        tiptop_12u = peakheight_0u = time_12u = 0.0
    topper_12d = topper_12 & down_flag
    top_loss_12d = l[topper_12d]
    t_12d = t[topper_12d]
    ntopper_12d = len(l[topper_12d])
    if ntopper_12d > 0:
        good_topper_12d = outlierFilter(top_loss_12d,3)
        tiptop_12d = mean(top_loss_12d[good_topper_12d])
        time_12d = mean(t_12d[good_topper_12d])
        peakheight_0d = (tiptop_12d - base_0)
    else:
        tiptop_12d = peakheight_0d = time_2d = 0.0

    C12H4_conc_raw = 0.4581*peak0_spec
    C12H4_conc_up = 0.4581*peakheight_0u
    C12H4_conc_down = 0.4581*peakheight_0d
    if ntopper_12u > 0 and ntopper_12d > 0:
        C12H4_time_separation = 0.001*(time_12d - time_12u)
    else:
        C12H4_time_separation = 0

    wd_ratio_iCH4 = 1.0 + h2o_conc_pct*(H1_wd_iCH4 + H2_wd_iCH4*h2o_conc_pct)
    peak0_spec_dry = peak0_spec/wd_ratio_iCH4
    C12H4_conc_raw_dry = C12H4_conc_raw/wd_ratio_iCH4

    init["base",3] = 0
    init[8,"strength"] = 0.1556*str_0
    init[20,"strength"] = 0.07726*strength_24
    init[21,"strength"] = 0.08073*strength_24
    r = anH2O[0](d,init,deps)   #  Next fit the water region with overlaping methane
    ANALYSIS.append(r)
    shift_30 = r["base",3]
    vy_30 = r[30,"y"]

    if (r[30,"peak"] > 10) and (abs(shift_30) < 0.04) and (abs(vy_30-1.35) < 0.5):
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
    peak30_spec = peak_30 + P30_off + P30_M1*peak0_spec
    h2o_conc_pct = peak30_spec/61.0
    ch4_from_h2o = 1.5621*r[8,"peak"]

    init["base",3] = 0
    init[21,"strength"] = 0.08073*strength_24
    init[1002,2] = str_0   #  Now initialize (12)CH4 spline and fit the (13)CH4 triplet
    r = anCH4[2](d,init,deps)
    ANALYSIS.append(r)
    shift_5 = r["base",3]
    vy_5 = r[5,"y"]

    if (r[5,"peak"] > 2) and (abs(shift_5) < 0.04) and (abs(vy_5-1.14) < 0.3):
        adjust_5 = shift_5
        init["base",3] = shift_5
        init[5,"y"] =  0.966*y_0
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

    init["base",3] = 0
    init[0,"strength"] = 0
    init[0,"y"] = y_0
    init[30,"strength"] = str_30
    init[30,"y"] = y_30
    init[20,"strength"] = 0.07726*strength_24
    init[21,"strength"] = 0.08073*strength_24
    init[1002,2] = str_0   #  Finally fit the entire spectrum looking for ethane on top of methane and water
    r = anCH4[4](d,init,deps)
    ANALYSIS.append(r)
    HC_res = r["std_dev_res"]
    HC_base_offset = r["base",0]-ch4_baseline_level
    HC_slope_offset = r["base",1]-ch4_baseline_slope
    HC_shift = r["base",3]
    HC_CH4_conc = 100*r[1002,2]
    HC_C12_conc = 0.40148*r[0,"peak"]
    HC_H2O_conc = r[30,"peak"]/61.0
    HC_C2H6_conc = 400*r[1003,2]

    #  17 Sep 2013 -- add another postfit with more interfering species
    r = anCH4[5](d,init,deps)
    ANALYSIS.append(r)
    PPF_res = r["std_dev_res"]
    PPF_base_offset = r["base",0]-ch4_baseline_level
    PPF_slope_offset = r["base",1]-ch4_baseline_slope
    PPF_shift = r["base",3]
    PPF_CH4_conc = 100*r[1002,2]
    PPF_C12_conc = 0.40148*r[0,"peak"]
    PPF_H2O_conc = r[30,"peak"]/61.0
    PPF_C2H6_conc = 400*r[1003,2]
    PPF_C2H4_conc = r[1004,2]
    PPF_NH3_conc = 50*r[1005,2]
    PPF_H2S_conc = 1000*r[1006,2]

    if good25>9:     #high precision CH4 at 6057.09
        init = InitialValues()
        initialize_CFADS_Baseline()
        r = an12CH4[0](d,init,deps)
        ANALYSIS.append(r)
        ch4_vy = r[1002,5]
        vch4_conc_ppmv = 10*r[1002,2]
        ch4_high_shift = r["base",3]
    #  Polishing step with fixed center, variable y if line is strong and shift is small
        if (r[1002,2] > 0.005) and (abs(ch4_high_shift) <= 0.07):
            init["base",3] = ch4_high_shift
            ch4_high_adjust = ch4_high_shift
            r = an12CH4[1](d,init,deps)
            ANALYSIS.append(r)
    #  Polishing step with fixed center and y if line is weak or shift is large
        else:
            init["base",3] = 0.0
            ch4_high_adjust = 0.0
            init[1002,5] = 1.08
            r = an12CH4[2](d,init,deps)
            ANALYSIS.append(r)

        CFADS_ch4_amp = r[1002,2]
        ch4_conc_raw = 10*r[1002,2]
        CFADS_ch4_y = r[1002,5]
        CFADS_base = r["base",0]
        ch4_adjconc_ppmv = CFADS_ch4_y*ch4_conc_raw*(140.0/P)
        ch4_splinemax = r[1002,"peak"]
        ch4_peakvalue = ch4_splinemax+CFADS_base
        CFADS_base_avg  = initExpAverage(CFADS_base_avg,CFADS_base,1,100,CFADS_counter)
        ch4_peak_baseavg = ch4_peakvalue-CFADS_base_avg
        ch4_conc_ppmv_final = ch4_peak_baseavg/216.3

        wd_ratio_CFADS_CH4 = 1.0 + h2o_conc_pct*(H1_wd_CFADS_CH4 + H2_wd_CFADS_CH4*h2o_conc_pct)
        ch4_splinemax_dry = ch4_splinemax/wd_ratio_CFADS_CH4
        ch4_conc_ppmv_final_dry = ch4_conc_ppmv_final/wd_ratio_CFADS_CH4

        ch4_res = r["std_dev_res"]
        CFADS_counter += 1
        cal = (d.subschemeId & 4096) != 0
        if any(cal):
            pzt_mean = mean(d.pztValue[cal])
            pzt_stdev = std(d.pztValue[cal])
    else:
        ch4_high_adjust = 0.0

#  Apply corrections to isotopic peak height here for high conc mode
#  C. Rella & Y. He 20111006 changed H2O-CH4 bilinear term to P5_M1H1*peak30_spec*peakheight_5 to address enriched 13C cases
    peak5_spec = peakheight_5 + P5_off + P5_quad*peak0_spec + P5_A1*peak24_spec + P5_H1*peak30_spec + P5_M1H1*peak30_spec*peakheight_5
    C13H4_conc_raw = 0.007772*peakheight_5


#  Calculate isotopic ratio and delta
    try:
        c13toc12 = peakheight_5/peakheight_0
    except:
        pass
    delta_no_bookend = 1723.1*c13toc12 - 1000
    try:
        c13toCFADS = peakheight_5/ch4_splinemax
    except:
        pass

elif species == 153:                # CO2 at 6056.5
    initialize_CFADS_Baseline()
    init[1002,2] = 0.5*h2o_conc_pct
    init[1003,2] = 0.009041*C12H4_conc_raw
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    shift_24 = r["base",3]
    vy_24 = r[24,"y"]

    if (r[24,"peak"] > 5) and (abs(shift_24) < 0.04) and (abs(vy_24-1.86) < 0.5):
        adjust_24 = shift_24
        init[24,"y"] = vy_24
    else:
        adjust_24 = 0.0

    init["base",3] = adjust_24
    r = anCO2[1](d,init,deps)
    ANALYSIS.append(r)
    y_24 = r[24,"y"]
    strength_24 = r[24,"strength"]
    base_24 = r[24,"base"]
    peak_24 = r[24,"peak"]
    peak24_spec = peak_24 + P24_off + P24_M1*peak0_spec
    #co2_conc = 7.718*peak_24
    co2_conc = 7.718*peak24_spec

elif species ==11 and d["ngroups"]>9:   #H2O at 6057.8
    initialize_CFADS_Baseline()
    r = anH2OCFADS[0](d,init,deps)
    ANALYSIS.append(r)
    if abs(r["base",3]) >= 0.01 or abs(r[75,"y"]-0.83)>0.3:
        r = anH2OCFADS[1](d,init,deps)
        ANALYSIS.append(r)
    h2o_res = r["std_dev_res"]
    peak_75 = r[75,"peak"]
    h2o_quality = fitQuality(h2o_res,peak_75,50,1)
    shift_75 = r["base",3]
    ch4_from_h2o_CFADS = 100.0*r[1002,2]
    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = mean(d.pztValue[cal])
        pzt_stdev = std(d.pztValue[cal])

    str_75 = r[75,"strength"]
    y_75 = r[75,"y"]
    z_75 = r[75,"z"]
    base_75 = r[75,"base"]
    h2o_conc = peak_75 * 0.01002
    if peak_75 > 3.0 and abs(shift_75) < 0.03 and h2o_quality < 1.5:
        adjust_75 = shift_75
    else:
        adjust_75 = 0.0

    r = anH2OCFADS[2](d,init,deps)     #  Original CFADS fit included for comparison
    ANALYSIS.append(r)
    if abs(r["base",3]) >= 0.01:
        r = anH2OCFADS[1](d,init,deps)
        ANALYSIS.append(r)
    CFADS_h2o_conc = r[75,"peak"] * 0.01002

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
    RESULT = {"ch4_res12":ch4_res12,"ch4_res13":ch4_res13,"ch4_res_w":ch4_res_w,
            "12CH4_raw":C12H4_conc_raw,"12CH4_raw_dry":C12H4_conc_raw_dry,
            "13CH4_raw":C13H4_conc_raw,"HC_res":HC_res,"C12H4_time_separation":C12H4_time_separation,
            "12CH4_up":C12H4_conc_up,"12CH4_down":C12H4_conc_down,
            "peak0_spec":peak0_spec,"peak5_spec":peak5_spec,"peak30_spec":peak30_spec,
            "delta_no_bookend":delta_no_bookend,"c-13toc-12":c13toc12,
            "vy_0":vy_0,"y_0":y_0,"base_0":base_0,"shift_0":shift_0,"adjust_0":adjust_0,
            "vy_5":vy_5,"y_5":y_5,"base_5":base_5,"shift_5":shift_5,"adjust_5":adjust_5,
            "vy_24":vy_24,"y_24":y_24,"base_24":base_24,"shift_24":shift_24,"adjust_24":adjust_24,
            "vy_30":vy_30,"y_30":y_30,"base_30":base_30,"shift_30":shift_30,"adjust_30":adjust_30,
            "peak_0":peak_0,"str_0":str_0,"peak_5":peak_5,"peak_24":peak_24,"peak24_spec":peak24_spec,"peak_30":peak_30,
            "interval":interval,"datapoints":d["datapoints"],"datagroups":d["ngroups"],
            "h2o_conc_pct":h2o_conc_pct,"peak30_spec":peak30_spec,
            "ntopper_12":ntopper_12,"tiptop_12":tiptop_12,"tipstd_12":tipstd_12,
            "ntopper_13":ntopper_13,"tiptop_13":tiptop_13,"tipstd_13":tipstd_13,
            "peakheight_5":peakheight_5,"peakheight_ratio":peakheight_ratio,
            "delta_from_height":delta_from_height,"ch4_from_h2o":ch4_from_h2o,
            "species":species,"fittime":fit_time,"peakheight_0":peakheight_0,
            "HC_base_offset":HC_base_offset,"HC_slope_offset":HC_slope_offset,
            "HC_shift":HC_shift,"HC_CH4_conc":HC_CH4_conc,"HC_C12_conc":HC_C12_conc,
            "HC_H2O_conc":HC_H2O_conc,"HC_C2H6_conc":HC_C2H6_conc,
            "PPF_res":PPF_res,"PPF_base_offset":PPF_base_offset,"PPF_slope_offset":PPF_slope_offset,
            "PPF_shift":PPF_shift,"PPF_CH4_conc":PPF_CH4_conc,"PPF_H2O_conc":PPF_H2O_conc,
            "PPF_C2H6_conc":PPF_C2H6_conc,"PPF_C2H4_conc":PPF_C2H4_conc,
            "PPF_NH3_conc":PPF_NH3_conc,"PPF_H2S_conc":PPF_H2S_conc,
            "ch4_vy":ch4_vy,"ch4_high_shift":ch4_high_shift,"ch4_high_adjust":ch4_high_adjust,"CFADS_ch4_amp":CFADS_ch4_amp,
            "CFADS_ch4_y":CFADS_ch4_y,"CFADS_base":CFADS_base,"ch4_splinemax":ch4_splinemax,
            "CFADS_base_avg":CFADS_base_avg,"ch4_conc_ppmv_final":ch4_conc_ppmv_final,
            "ch4_splinemax_dry":ch4_splinemax_dry,"ch4_conc_ppmv_final_dry":ch4_conc_ppmv_final_dry,
            "peak_75":peak_75,"shift_75":shift_75,"str_75":str_75,
            "y_75":y_75,"base_75":base_75,"h2o_conc":h2o_conc,"adjust_75":adjust_75,"CFADS_h2o_conc":CFADS_h2o_conc,"co2_conc":co2_conc,
            "cavity_pressure":P,"cavity_temperature":T,"das_temp":dasTemp
            }
    RESULT.update(d.sensorDict)
    RESULT["solenoid_valves"] = RESULT["ValveMask"]
