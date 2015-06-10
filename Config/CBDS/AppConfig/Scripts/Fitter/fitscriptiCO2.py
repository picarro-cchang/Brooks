#  Translation of Version 1.57 of the CBDS fitter from Silverstone format to Python
#  John Hoffnagle 15 July 2010
#  1 Sep 2010:  added reporting of PZT averages and standard deviations from the calibration fits
#  3 Sep 2010:  added baseline and sinusoids to the FitterConfig.ini file
#  14 Sep 2010: changed sparsing to use outlierFilter instead of sigmaFilter
#               changed C-12 fit to use FC FY when variable fit gives unreasonable y
#               (this avoids wild peak height-y combination when fitting noise)
#               added fit ini for FC FY, cleaned up and renamed FC VY fit ini
#  15 Sep 2010: changed H2O fit ini to find center before baseline
#               added initialization of baseline slope from FitterConfig.ini
#  30 Sep 2010: changed initialization of FC FY for weak C-12 to require shift = 0;
#               suppresses outliers when concentration -> 0
#  13 Dec 2010: add condition on number of data groups for SID 105 and 106
#  02 Mar 2011: Fixed a bad bug in the initialization of splines and sinusoids
#  2011-04-28:  Replaced numgroups (deprecated) with ngroups.

import numpy
import os.path
import time
#from EventManagerProxy import Log

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
    return numpy.sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

def initialize_Baseline(sine_index):
    init["base",1] = baseline_slope
    init[sine_index,0] = A0
    init[sine_index,1] = Nu0
    init[sine_index,2] = Per0
    init[sine_index,3] = Phi0
    init[sine_index+1,0] = A1
    init[sine_index+1,1] = Nu1
    init[sine_index+1,2] = Per1
    init[sine_index+1,3] = Phi1

if INIT:
    fname = os.path.join(BASEPATH,r"./isoCO2/CBDS-5 spectral library + CBDS65 methane + CBDS52 HDO + 18O - v20100630.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anC12O2 = []
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C12 + CH4 v1_1_20100709.ini")))
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C12 only FC VY v1_2.ini")))
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C12 only FC FY v1_2.ini")))

    anC13O2 = []
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_3.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_3+methane 20110302.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_3+CH4+18O 20110302.ini")))

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/6250_4 2_H2O + 2_HDO + CO2 spline_20100915.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/6250_4 FC 2_H2O + 2_HDO + CO2 spline_20100915.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/Methane dev 1_1 20100709.ini")))

    ##  Import calibration constants from fitter_config.ini at initialization
    P88_off = instrParams['Peak88_offset']
    P88_H1 = instrParams['Peak88_water_linear']
    P88_H1A1 = instrParams['Peak88_bilinear']
    P88_H2A1 = instrParams['Peak88_quad_linear']
    P88_M1 = instrParams['Peak88_methane_1']
    P88_M2 = instrParams['Peak88_methane_2']
    CH4_off = instrParams['Methane_offset']
    CH4_A1 = instrParams['Methane_co2']
    CH4_H1 = instrParams['Methane_water']
    CH4_H1A1 = instrParams['Methane_bilinear']
    P87_off = instrParams['Peak87_offset']
    P87_H1 = instrParams['Peak87_water']
    P96_off = instrParams['Peak96_offset']
    P96_H2 = instrParams['Peak96_water']
    P91_off = instrParams['Peak91_offset']
    H1 = instrParams['Water_lin']
    H2 = instrParams['Water_quad']
    H1_wd = instrParams['Water_lin_wd']
    H2_wd = instrParams['Water_quad_wd']
    C12_conc_lin = instrParams['C12_lin']
    C13_conc_lin = instrParams['C13_lin']
    M1 = instrParams['Methane_lin']
    c12_base_ave = instrParams['C12_baseline']
    c13_base_ave = instrParams['C13_baseline']
    baseline_slope = instrParams['Baseline_slope']
    A0 = instrParams['Sine0_ampl']
    Nu0 = instrParams['Sine0_freq']
    Per0 = instrParams['Sine0_period']
    Phi0 = instrParams['Sine0_phase']
    A1 = instrParams['Sine1_ampl']
    Nu1 = instrParams['Sine1_freq']
    Per1 = instrParams['Sine1_period']
    Phi1 = instrParams['Sine1_phase']

    ##  Initialize static variables used to hold fit results and pass between fit sections
    counter = -25
    lastgood_shift_87 = 0
    lastgood_strength_87 = 0
    lastgood_y_87 = 0.0136
    lastgood_z_87 = 0.00438
    lastgood_y_88 = 0.01515
    lastgood_z_88 = 0.00488

    y87_ave = 0.0
    z87_ave = 0.0
    peak_87 = 0.0
    shift_87 = 0.0
    str_87 = 0.0
    base_87 = 0.0
    y88 = 0.0
    z88 = 0.0
    peak_88 = 0.0
    shift_88 = 0.0
    str_88 = 0.0
    y_91 = 0.0
    z_91 = 0.0
    shift_91 = 0.0
    peak_91 = 0.0
    peak_92 = 0.0
    peak_96 = 0.0
    base_88 = 0.0
    ch4_ampl = 0.0
    ch4_raw = 0.0
    h2_18o = 0.0
    co2_water_reg = 0.0
    ch4_conc_h2o = 0.0
    c2h4_conc = 0.0
    ch4_conc_12CO2 = 0.0

    adjust_87 = 0.0
    adjust_88 = 0.0
    adjust_91 = 0.0
    initial_galratio = 0.0
    baseave_galratio = 0.0
    polybaseave_galratio = 0.0
    peak88_baseave = 0.0
    peak87_baseave = 0.0
    polypeak88_baseave = 0.0

    c12_pzt_ave = 0.0
    c12_pzt_stdev = 0.0
    c13_pzt_ave = 0.0
    c13_pzt_stdev = 0.0

    ignore_count = 5
    last_time = None

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.30,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/numpy.sqrt(d.groupSizes))

P = d["cavitypressure"]
dasTemp = d.sensorDict["DasTemp"]
tstart = time.clock()
RESULT = {}
r = None

if d["spectrumId"] == 105 and d["ngroups"] >= 6:  # C12O2
    initialize_Baseline(1001)
    r = anC12O2[0](d,init,deps)
    ANALYSIS.append(r)
    ch4_conc_12CO2 = M1*r[1000,2]
    vy_87 = r[87,"y"]
    pre_peak_87 = r[87,"peak"]
    cm_shift = r["base",3]

    initialize_Baseline(1000)
    if abs(cm_shift) < 0.07 and abs(vy_87-1.568) < 0.5 and pre_peak_87 > 10:
        init["base",3] = cm_shift
        r = anC12O2[1](d,init,deps)
        ANALYSIS.append(r)
    else:
        init["base",3] = 0.0
        r = anC12O2[2](d,init,deps)
        ANALYSIS.append(r)
    peak_87 = r[87,"peak"]
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
        y87_ave = initExpAverage(y87_ave,y_87,4,1,counter)
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

elif d["spectrumId"] == 106 and d["ngroups"] >= 8:  # C13O2
    init[87,"scaled_strength"] = lastgood_strength_87
    init[87,"scaled_y"] = lastgood_y_87
    init[87,"scaled_z"] = lastgood_z_87
    init[88,"scaled_y"] = lastgood_y_88
    init[88,"scaled_z"] = lastgood_z_88
    initialize_Baseline(1000)
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

    r = anC13O2[1](d,init,deps)
    ANALYSIS.append(r)
    peak88_ch4 = r[88,"peak"]
    ch4_conc_13CO2 = M1*r[1002,2]

    #init = InitialValues()
    #r = anC13O2[2](d,init,deps)
    #ANALYSIS.append(r)
    #polypeak88 = r["base",0] + c13_offset
    #polypeak88_baseave = polypeak88 - c13_base_ave
    f = numpy.array(d.fitData["freq"])
    l = numpy.array(d.fitData["loss"])
    good = (f >= 6251.312) & (f <= 6251.318)
    if len(l[good]) > 0:
        polypeak88 = numpy.average(l[good])
    else:
        polypeak88 = 0.0
    polypeak88_baseave = polypeak88 - c13_base_ave

    init[1002,2] = ch4_ampl
    r = anC13O2[2](d,init,deps)
    ANALYSIS.append(r)
    agalbase_88 = r[88,"base"]
    apeak88 = r[88,"peak"]
    shift_88 = r["base",3]
    ay_88 = r[88,"y"]
    abase1 = r["base",1]
    h2_18o = r[1003,2]
    if (c13_fit_quality <= 0.6) and (ch4_conc_12CO2 <= 0.05) and (ch4_raw <= 0.01) and (apeak88 >= 3) and (abs(shift_88) <= 0.02):
        adjust_88 = shift_88
    else:
        adjust_88 = 0.0

elif d["spectrumId"] == 109:  # H2O
    #  Variable peak water fitter
    initialize_Baseline(1002)
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    shift_91 = r["base",3]
    adjust_91 = shift_91
    if (abs(shift_91) > 0.03) or (r[91,"peak"] < 7):
        #  Fixed peak water fitter
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
        shift_91 = r["base",3]
        adjust_91 = 0.0
    peak_91 = r[91,"peak"]
    y_91 = r[91,"y"]
    z_91 = r[91,"z"]
    peak_96 = r[96,"peak"]
    co2_water_reg = 5064*r[1000,2]
    ch4_conc_h2o = M1*r[1001,2]
    #  CO2 and CH4 fitter
    r = anH2O[2](d,init,deps)
    ANALYSIS.append(r)
    shift_91 = r["base",3]
    ch4_raw = r[1001,2]
    c2h4_conc = 0.4*r[1000,2]
    peak_92 = r[92,"peak"]
    ch4_ampl = r[1001,2]

elif d["spectrumId"] == 155:  #C12 calibration scan
    c12_pzt_ave = numpy.mean(d.pztValue)
    c12_pzt_stdev =  numpy.std(d.pztValue)

elif d["spectrumId"] == 156:  #C13 calibration scan
    c13_pzt_ave = numpy.mean(d.pztValue)
    c13_pzt_stdev =  numpy.std(d.pztValue)

if ((d["spectrumId"] == 105) or (d["spectrumId"] == 106)) and (peak_87 >= 20):
    eps = 1e-14
    initial_galratio = (peak_88+eps)/(peak_87+eps)
    baseave_galratio = (peak88_baseave+eps)/(peak87_baseave+eps)
    polybaseave_galratio = (polypeak88_baseave+eps)/(peak87_baseave+eps)

#  Corrections and calibrations added 12 July 2010 (Chris)
#  (1) Correct offsets first
peak87_baseave_offset = peak87_baseave + P87_off
peak88_baseave_offset = peak88_baseave + P88_off
ch4_offset = ch4_raw + CH4_off
peak91_offset = peak_91 + P91_off
peak96_offset = peak_96 + P96_off
#  (2) Fitting cross-talk corrections come next
#  Methane correction
ch4_spec = ch4_offset + CH4_A1*peak87_baseave_offset + CH4_H1*peak91_offset + CH4_H1A1*peak87_baseave_offset*peak91_offset
#  HDO correction
peak96_spec = peak_96 + P96_H2*peak96_offset**2
#  H2O correction
peak91_spec = peak91_offset
#  12CO2 correction
peak87_baseave_spec = peak87_baseave_offset + P87_H1*peak91_spec
#  13CO2 correction
peak88_baseave_noch4 = peak88_baseave_offset + P88_H1*peak91_spec + P88_H1A1*peak91_spec*peak87_baseave_spec + P88_H2A1*peak87_baseave_spec*peak91_spec**2
peak88_baseave_spec = peak88_baseave_noch4 + P88_M1*ch4_spec
#  (3) Provide corrected outputs based on the spectroscopic values
#  Water concentration
h2o_actual = H1*peak91_spec + H2*peak91_spec**2
#  Methane calibration
ch4_conc = M1*ch4_spec
#  Water correction to CO2 concentration
wd_ratio = 1.0 + H1_wd*peak91_spec + H2_wd*peak91_spec**2
peak87_baseave_dry = peak87_baseave_spec/wd_ratio
peak88_baseave_dry = peak88_baseave_spec/wd_ratio
#  Final concentration values for 12CO2 and 13CO2
CO2_12_ppm_wet = C12_conc_lin*peak87_baseave_spec
CO2_12_ppm_dry = C12_conc_lin*peak87_baseave_dry
CO2_13_ppm_wet = C13_conc_lin*peak88_baseave_spec
CO2_13_ppm_dry = C13_conc_lin*peak88_baseave_dry

counter += 1

now = time.clock()
fit_time = now-tstart
if r != None:
    ignoreThis = False
    last_time = r["time"]
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
else:
    ignoreThis = True

ignore_count = max(0,ignore_count-1)
if (ignore_count == 0) and (not ignoreThis):
    RESULT = {"y87_ave":y87_ave,"z87_ave":z87_ave,"shift_87":shift_87,"str_87":str_87,"peak87_baseave":peak87_baseave,"base_87":base_87,"slope_87":slope_87,
              "y88":y88,"z88":z88,"shift_88":shift_88,"str_88":str_88,"peak88_baseave":peak88_baseave,"peak_88":peak_88,"base_88":base_88,"slope_88":slope_88,
              "y_91":y_91,"z_91":z_91,"shift_91":shift_91,"peak_91":peak_91,"ch4_conc_12CO2":ch4_conc_12CO2,"ch4_conc_13CO2":ch4_conc_13CO2,"peak_87":peak_87,
              "adjust_87":adjust_87,"h2_18o":h2_18o,"adjust_88":adjust_88,"peak_96":peak_96,"co2_water_reg":co2_water_reg,"ch4_conc_h2o":ch4_conc_h2o,
              "peak_92":peak_92,"c2h4_conc":c2h4_conc,"datapoints":d["datapoints"],"datagroups":d["ngroups"],"y_87":y_87,
              "ratio_i":initial_galratio,"ratio_b":baseave_galratio,"ratio_p":polybaseave_galratio,"polypeak88_baseave":polypeak88_baseave,
              "ch4_raw":ch4_raw,"ch4_spec":ch4_spec,"peak91_spec":peak91_spec,"peak96_spec":peak96_spec,"peak87_baseave_spec":peak87_baseave_spec,
              "peak88_baseave_noch4":peak88_baseave_noch4,"peak88_baseave_spec":peak88_baseave_spec,
              "h2o_actual":h2o_actual,"ch4_conc":ch4_conc,"12CO2_ppm_wet":CO2_12_ppm_wet,"12CO2_ppm_dry":CO2_12_ppm_dry,
              "13CO2_ppm_wet":CO2_13_ppm_wet,"13CO2_ppm_dry":CO2_13_ppm_dry,"adjust_91":adjust_91,
              "c12_pzt_ave":c12_pzt_ave,"c12_pzt_stdev":c12_pzt_stdev,"c13_pzt_ave":c13_pzt_ave,"c13_pzt_stdev":c13_pzt_stdev,
              "cavity_pressure":P,"species":d["spectrumId"],"fit_time":fit_time,
              "interval":interval,"dasTemp":dasTemp,
              "solenoid_valves":d.sensorDict["ValveMask"],
              "MPVPosition":d.sensorDict["MPVPosition"]}
    RESULT.update(d.sensorDict)
