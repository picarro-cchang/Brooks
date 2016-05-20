#   Major revision of the CHADS fitter for isotopic CO2 and isotopic water
#   Isotopic CO2 changed to alternate region near 6228 wvn.
#   Isotopic water at 6434 wvn.
#   John Hoffnagle started end of Dec 2012 using existing CHADS fitter for water and new CO2
#   Spectral IDs:
#       160 -- both water isotopologues
#       164 -- both CO2 isotopologues

#   2013 0301:  Added bilinear (h2o*co2) correction to Peak13.  Is this physical?
#   2013 0320:  Added cubic (peak12^2*peak13) correction to correct for reflection over 4.5%H2O (JY)


from numpy import *
import os.path
import time

def fitQuality(sdFit,maxPeak,normPeak,sdTau):
    return sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

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

def initialize_H2O_Baseline(sine_index):
    init["base",1] = h2o_baseline_slope
    init[sine_index,0] = h2o_A0
    init[sine_index,1] = h2o_Nu0
    init[sine_index,2] = h2o_Per0
    init[sine_index,3] = h2o_Phi0
    init[sine_index+1,0] = h2o_A1
    init[sine_index+1,1] = h2o_Nu1
    init[sine_index+1,2] = h2o_Per1
    init[sine_index+1,3] = h2o_Phi1

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

if INIT:
    fname = os.path.join(BASEPATH,r"./CHADS/CHADS_N2_spectral_library_v2_1.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anC12O2 = []
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./CHADS/C12 only VC VY v2_1.ini")))
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./CHADS/C12 only FC FY v2_1.ini")))

    anC13O2 = []
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./CHADS/C13 only VC VY v2_1.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./CHADS/C13 only FC FY v2_1.ini")))

    anHDO = []
    anHDO.append(Analysis(os.path.join(BASEPATH,r"./CHADS/Water region VC VY VA v4_1.ini")))
    anHDO.append(Analysis(os.path.join(BASEPATH,r"./CHADS/Water_only FC FY v4_1.ini")))

    #  Import spectroscopic parameters from spectral library
    center13 = spectrParams['peak13']['center']
    y12_nominal = 100*spectrParams['peak12']['y']
    y13_nominal = 100*spectrParams['peak13']['y']
    y20_nominal = 100*spectrParams['peak20']['y']
    y24_nominal = 100*spectrParams['peak24']['y']

    #  Import calibration constants from fitter_config.ini at initialization
    P24_off = instrParams['Peak24_offset']
    P24_H1 = instrParams['Peak24_water_linear']
    P24_H1A1 = instrParams['Peak24_bilinear']
    P24_H2A1 = instrParams['Peak24_quad_linear']
    P24_A2 = instrParams['Peak24_quad']
    P20_off = instrParams['Peak20_offset']
    P20_H1 = instrParams['Peak20_water_linear']
    C12_conc_lin = instrParams['C12_lin']
    C13_conc_lin = instrParams['C13_lin']
    P12_off = instrParams['Peak12_offset']
    P13_off = instrParams['Peak13_offset']
    P13_A1 = instrParams['Peak13_CO2_linear']
    P13_A1H1 = instrParams['Peak13_CO2_bilinear']
    P13_H2 = instrParams['Peak13_water_quad']
    P13_H3 = instrParams['Peak13_water_cubic']
    HHO_conc_lin = instrParams['HHO_lin']
    HDO_conc_lin = instrParams['HDO_lin']
    co2_baseline_slope = instrParams['CO2_Baseline_slope']
    co2_A0 = instrParams['CO2_Sine0_ampl']
    co2_Nu0 = instrParams['CO2_Sine0_freq']
    co2_Per0 = instrParams['CO2_Sine0_period']
    co2_Phi0 = instrParams['CO2_Sine0_phase']
    co2_A1 = instrParams['CO2_Sine1_ampl']
    co2_Nu1 = instrParams['CO2_Sine1_freq']
    co2_Per1 = instrParams['CO2_Sine1_period']
    co2_Phi1 = instrParams['CO2_Sine1_phase']
    h2o_baseline_slope = instrParams['H2O_Baseline_slope']
    h2o_A0 = instrParams['H2O_Sine0_ampl']
    h2o_Nu0 = instrParams['H2O_Sine0_freq']
    h2o_Per0 = instrParams['H2O_Sine0_period']
    h2o_Phi0 = instrParams['H2O_Sine0_phase']
    h2o_A1 = instrParams['H2O_Sine1_ampl']
    h2o_Nu1 = instrParams['H2O_Sine1_freq']
    h2o_Per1 = instrParams['H2O_Sine1_period']
    h2o_Phi1 = instrParams['H2O_Sine1_phase']

    #  Initialize static variables used to hold fit results and pass between fit sections

    peak_20 = 0.0
    peak20_spec = 0.0
    shift_20 = 0.0
    str_20 = 0.0
    base_20 = 0.0
    slope_20 = 0.0
    vy_20 = 2.3203
    y_20 = 2.3203
    peak_24 = 0.0
    peak24_spec = 0.0
    shift_24 = 0.0
    str_24 = 0.0
    base_24 = 0.0
    slope_24 = 0.0
    vy_24 = 1.8718
    y_24 = 1.8718
    tiptop = 0
    peakheight_24 = 0

    adjust_20 = 0.0
    adjust_20 = 0.0
    CO2_12_ppm = 0.0
    CO2_13_ppm = 0.0

    c12_pzt_ave = 0.0
    c12_pzt_stdev = 0.0
    c13_pzt_ave = 0.0
    c13_pzt_stdev = 0.0

    str_5 = 0.0
    adjust_12 = 0.0
    adjust_13 = 0.0
    shift_12 = 0.0
    str_12 = 0.0
    peak_12 = 0.0
    base_12 = 0.0
    y_12 = 0.599
    y_13 = 1.174
    shift_13 = 0.0
    str_13 = 0.0
    peak_13 = 0.0
    base_13 = 0.0
    peak12_spec = 0.0
    peak13_spec = 0.0
    H2O_ppm = 0.0
    HDO_ppm = 0.0
    DH_ratio_raw = 0.0
    DH_ratio_spec = 0.0
    vp_ratio_h2o = 0.0
    p_ratio_h2o = 0.0
    h2o_pzt_ave = 0.0
    h2o_pzt_stdev = 0.0
    hdo_pzt_ave = 0.0
    hdo_pzt_stdev = 0.0
    vy_12 = 0.599
    vy_13 = 1.174

    ignore_count = 5
    last_time = None

# For offline analysis and output to file
    out = open("Fit_results.txt","w")
    first_fit = 1

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
#d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=3)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))

P = d["cavitypressure"]
dasTemp = d.sensorDict["DasTemp"]
tstart = time.clock()
RESULT = {}
r = None

species = (d.subschemeId & 0x3FF)[0]
cal = (d.subschemeId & 4096) != 0
VL = d.laserUsed >> 2

if species == 164 and d["ngroups"]>6:  # Isotopic carbon lines at 6228 wvn
    initialize_CO2_Baseline(1000)              # Fit the strong 12CO2 line first
    init[1002,2] = 0.00345*str_12
    r = anC12O2[0](d,init,deps)
    ANALYSIS.append(r)
    vy_20 = r[20,"y"]
    shift_20 = r["base",3]

    if abs(shift_20) < 0.05 and abs(vy_20-y20_nominal) < 0.5 and r[20,"peak"] > 10:
        init["base",3] = shift_20
        init[20,"y"] = vy_20
        adjust_20 = shift_20
    else:
        init["base",3] = 0.0
        adjust_20 = 0.0
    r = anC12O2[1](d,init,deps)
    ANALYSIS.append(r)
    peak_20 = r[20,"peak"]
    y_20 = r[20,"y"]
    c12_res  = r["std_dev_res"]
    c12_fit_quality = fitQuality(c12_res,peak_20,50,1)

    base_20 = r[20,"base"]
    str_20 = r[20,"strength"]
    slope_20 = r["base",1]
    co2_water_amp = r[1002,2]
    peak20_spec = peak_20 + P20_off + P20_H1*peak12_spec
    CO2_12_ppm = C12_conc_lin*(peak20_spec)

    init[20,"strength"] = str_20
    init[20,"y"] = y_20
    init[1002,2] = co2_water_amp
    r = anC13O2[0](d,init,deps)
    ANALYSIS.append(r)
    vy_24 = r[24,"y"]
    shift_24 = r["base",3]

    if abs(shift_24) < 0.05 and abs(vy_24-y24_nominal) < 0.5 and r[24,"peak"] > 3:
        init["base",3] = shift_24
        init[24,"y"] = vy_24
        adjust_24 = shift_24
    else:
        init["base",3] = 0.0
        adjust_24 = 0.0
    r = anC13O2[1](d,init,deps)
    ANALYSIS.append(r)
    peak_24 = r[24,"peak"]
    y_24 = r[24,"y"]
    c13_res  = r["std_dev_res"]
    c13_fit_quality = fitQuality(c13_res,peak_24,50,1)

    base_24 = r[24,"base"]
    str_24 = r[24,"strength"]
    slope_24 = r["base",1]

    f = d.waveNumber
    l = 1000*d.uncorrectedAbsorbance

    topper = (f >= 6228.428) & (f <= 6228.438)  #  Measure peak 24 height
    top_loss = l[topper]
    ntopper = len(l[topper])
    if ntopper > 0:
        good_topper = outlierFilter(top_loss,4)
        tiptop = mean(top_loss[good_topper])
        tipstd = std(top_loss[good_topper])
        ntopper = len(top_loss[good_topper])
        peakheight_24 = tiptop - base_24
    else:
        tiptop = 0.0
        tipstd = 0.0
        peakheight = peak_24


    #  Apply corrections derived from 2D step test in same way as for 6251 wvn spectroscopy
    peak24_offset = peak_24 + P24_off
    peak24_spec = peak24_offset + P24_H1*peak_12 + P24_H1A1*peak_12*peak24_offset + P24_H2A1*peak24_offset*peak_12**2
    peak24_spec += P24_A2*peak20_spec*peak24_offset
    CO2_13_ppm = C13_conc_lin*peak24_spec
    p_ratio_co2_spec = peak24_spec/peak20_spec

    if any(cal):
        #  Compute tuner statistics
        VL0 = (VL == 0)
        c12_pzt_ave = mean(d.tunerValue[VL0])
        c12_pzt_stdev = std(d.tunerValue[VL0])
        VL1 = (VL == 1)
        c13_pzt_ave = mean(d.tunerValue[VL1])
        c13_pzt_stdev = std(d.tunerValue[VL1])

elif species == 160 and d["ngroups"]>12:   # Isotopic water lines at 6434
    initialize_H2O_Baseline(1000)
    init[5,"strength"] = 6.93e-4*str_20
    r = anHDO[0](d,init,deps)     #  First fit the entire spectral region
    ANALYSIS.append(r)
    shift_12 = r["base",3]
    shift_13 = shift_12-(r[13,"center"]-center13)
    str_12 = r[12,"strength"]
    str_13 = r[13,"strength"]
    vy_12 = r[12,"y"]
    vy_13 = r[13,"y"]
    vp_ratio_h2o = r[13,"peak"]/r[12,"peak"]
    if r[12,"peak"] > 5 and abs(shift_12) < 0.05 and abs(vy_12 - y12_nominal) < 0.3 and abs(shift_13) < 0.05 and abs(vy_13 - y13_nominal) < 0.3:
        adjust_12 = shift_12
        adjust_13 = shift_13
        init[12,"y"] = vy_12
        init[13,"y"] = vy_13
    else:
        adjust_12 = 0.0
        adjust_13 = 0.0
    str_5 = r[5,"strength"]

    #init[5,"strength"] = str_5      #  UNNECESSARY IF STR 5 IS PRESET FROM CO2 REGION
    init["base",3] = adjust_12
    init[13,"center"] = center13 - (adjust_13 - adjust_12)
    r = anHDO[1](d,init,deps)   #  Fit water peaks only with fixed center and y
    ANALYSIS.append(r)
    peak_12 = r[12,"peak"]
    base_12 = r[12,"base"]
    peak_13 = r[13,"peak"]
    base_13 = r[13,"base"]
    DH_ratio_raw = 4.081e-4*peak_13/peak_12
    p_ratio_h2o = peak_13/peak_12
    #  Apply corrections based on 2D step test
    peak12_spec = peak_12 + P12_off
    peak13_spec = peak_13 + P13_off + P13_H2*peak_12*peak_13 + P13_H3*peak_12*peak_12*peak_13
    peak13_spec += P13_A1*peak20_spec + P13_A1H1*peak_13*peak20_spec
    H2O_ppm = HHO_conc_lin*peak12_spec
    HDO_ppm = HDO_conc_lin*peak13_spec
    DH_ratio_spec = HDO_ppm/H2O_ppm

    if any(cal):
        #  Compute tuner statistics
        VL3 = (VL == 3)
        h2o_pzt_ave = mean(d.tunerValue[VL3])
        h2o_pzt_stdev = std(d.tunerValue[VL3])
        VL4 = (VL == 4)
        hdo_pzt_ave = mean(d.tunerValue[VL4])
        h2o_pzt_stdev = std(d.tunerValue[VL4])

now = time.clock()
fit_time = now-tstart
if r != None:
    ignoreThis = False
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]
else:
    ignoreThis = True

ignore_count = max(0,ignore_count-1)
if (ignore_count == 0) and (not ignoreThis):
    RESULT = {"shift_20":shift_20,"adjust_20":adjust_20,"base_20":base_20,"slope_20":slope_20,
              "peak20_spec":peak20_spec,"vy_20":vy_20,"y_20":y_20,"peak_20":peak_20,"str_20":str_20,
              "datapoints":d["datapoints"],"datagroups":d["ngroups"],"co2_water_amp":co2_water_amp,
              "shift_24":shift_24,"adjust_24":adjust_24,"base_24":base_24,"slope_24":slope_24,
              "peak24_spec":peak24_spec,"vy_24":vy_24,"y_24":y_24,"peak_24":peak_24,"str_24":str_24,
              "CO2_626_ppm":CO2_12_ppm,"CO2_636_ppm":CO2_13_ppm,"p_ratio_co2_spec":p_ratio_co2_spec,
              "c12_pzt_ave":c12_pzt_ave,"c12_pzt_stdev":c12_pzt_stdev,"c13_pzt_ave":c13_pzt_ave,"c13_pzt_stdev":c13_pzt_stdev,
              "c12_res":c12_res,"c13_res":c13_res,"tiptop":tiptop,"peakheight_24":peakheight_24,
              "peak_12":peak_12,"base_12":base_12,"shift_12":shift_12,"adjust_12":adjust_12,"str_12":str_12,"y_12":y_12,"y_13":y_13,
              "peak_13":peak_13,"base_13":base_13,"shift_13":shift_13,"adjust_13":adjust_13,"str_13":str_13,"vy_12":vy_12,"vy_13":vy_13,
              "H2O_ppm":H2O_ppm,"HDO_ppm":HDO_ppm,"DH_ratio_raw":DH_ratio_raw,"DH_ratio_spec":DH_ratio_spec,
              "vp_ratio_h2o":vp_ratio_h2o,"p_ratio_h2o":p_ratio_h2o,"str_5":str_5,
              "peak12_spec":peak12_spec,"peak13_spec":peak13_spec,
              "h2o_pzt_ave":h2o_pzt_ave,"h2o_pzt_stdev":h2o_pzt_stdev,"hdo_pzt_ave":hdo_pzt_ave,"hdo_pzt_stdev":hdo_pzt_stdev,
              "cavity_pressure":P,"species":species,"fit_time":fit_time,
              "interval":interval,"dasTemp":dasTemp,
              "solenoid_valves":d.sensorDict["ValveMask"],
              "MPVPosition":d.sensorDict["MPVPosition"]}
    RESULT.update(d.sensorDict)

    if first_fit:
        keys = sorted([k for k in RESULT])
        print>>out," ".join(keys)
        first_fit = 0
    print>>out," ".join(["%s" % RESULT[k] for k in keys])
