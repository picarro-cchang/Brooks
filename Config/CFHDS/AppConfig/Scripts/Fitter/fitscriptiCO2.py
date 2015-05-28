#  Fitter for isotopic CO2 merging CBDS for CO2 with CFADS for water and methane
#  John Hoffnagle 26 January 2011
#  Rella 2011 0217 - added init = InitialValues() in each SID, modified 13C inis so that sinusoid is always in 1000 and 1001
#  Hoffnagle 2011 0309 - changed flow of peak 87 fit to report pre-peak unless weak or suspicious
#  Hoffnagle 2011 0314 - fixed logical error in calculation of ch4_conc_diff
#  Hoffnagle 2011 0323 - report separate shift & adjust for methane SIDs 25 and 29
#  Hoffnagle 2011 0328 - removed fit quality condition for reporting of H2O conc from 6057.8 wvn line
#                        changed standard (first step) water fit to have variable y (old y was bad)
#  Hoffnagle 2011 0329 - added old CFADS water fitter reporting to private log
#  2011-04-28:  Replaced numgroups (deprecated) with ngroups.
#  2011-06-15:  Reinstated variable y in first stage CFADS methane fitter
#  2011-12-01:  Added condition ngroups>6 to spectrum id 29 fitter
#  2013-07-30:  Added water interference to fit of methane "shoulder peak" (high range).  Preset from CFADS water line based on Hitran strengths.

import numpy
import os.path
import time

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
    fname = os.path.join(BASEPATH,r"./spectral library_CBDS+CFADS6057_v2.ini")
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
    #anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_3+methane 20100709.ini")))
    #anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_3+CH4+18O 20100709.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_31+methane 20110217.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_31+CH4+18O 20110217.ini")))

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/6250_4 2_H2O + 2_HDO + CO2 spline_20100915.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/6250_4 FC 2_H2O + 2_HDO + CO2 spline_20100915.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/Methane dev 1_1 20100709.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 v1_2 2011 0328.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 FC v1_1 2011 0309.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 v1_1 2011 0309.ini")))

    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 v2_1 2008 0304.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC VY v2_0 2008 0304.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC FY v2_0 2008 0304.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 v4_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC FY v4_1.ini")))

    #  Import calibration constants from fitter_config.ini at initialization
    P88_off = instrParams['Peak88_offset']
    P88_H1 = instrParams['Peak88_water_linear']
    P88_H1A1 = instrParams['Peak88_bilinear']
    P88_H2A1 = instrParams['Peak88_quad_linear']
    P88_M1 = instrParams['Peak88_methane_linear']
    P88_M2 = instrParams['Peak88_methane_quadratic']
    try:
        P88_M1H1 = instrParams['Peak88_methane_H2O_bilinear']
    except:
        P88_M1H1 = 0.0
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
    CH4_splinemax_offset = instrParams['Methane_spline_offset']
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

    #  Initialize static variables used to hold fit results and pass between fit sections
    counter = -25
    lastgood_shift_87 = 0
    lastgood_strength_87 = 0
    lastgood_y_87 = 0.0136
    lastgood_z_87 = 0.00438
    lastgood_y_88 = 0.01515
    lastgood_z_88 = 0.00488

    #  rella 2011 0303 - added pre_peak_87, pre_base_87, and peak88_ch4 to GUI outputs
    #  hoffnagle 2011 0309 - added ch4 from spline under 6057.8 water peak

    y87_ave = 0.0
    z87_ave = 0.0
    peak_87 = 0.0
    slope_87 = 0.0
    pre_peak_87 = 0.0
    pre_base_87 = 0.0
    shift_87 = 0.0
    str_87 = 0.0
    base_87 = 0.0
    y88 = 0.0
    z88 = 0.0
    peak_88 = 0.0
    peak88_ch4 = 0.0
    shift_88 = 0.0
    slope_88 = 0.0
    c13_fit_quality = 0.0
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
    ch4_conc_13CO2 = 0.0

    adjust_75 = 0.0
    adjust_87 = 0.0
    adjust_88 = 0.0
    adjust_91 = 0.0
    ch4_low_adjust = 0.0
    ch4_high_adjust = 0.0

    peak88_baseave = 0.0
    peak87_baseave = 0.0
    polypeak88_baseave = 0.0

    c12_pzt_ave = 0.0
    c12_pzt_stdev = 0.0
    c13_pzt_ave = 0.0
    c13_pzt_stdev = 0.0

    peak_75 = 0.0
    base_75 = 0.0
    str_75 = 0.0
    y_75 = 0.0
    shift_75 = 0.0
    h2o_conc = 0.0
    CFADS_h2o_conc = 0.0

    CFADS_counter = -25
    CFADS_base = 0.0
    CFADS_base_avg = instrParams['C12_baseline']
    ch4_low_shift = 0.0
    ch4_high_shift = 0.0
    CFADS_ch4_amp = 0.0
    ch4_splinemax = 0.0
    ch4_splinemax_for_correction = 0.0
    ch4_vy = 0.0
    ch4_y_avg = 1.08
    ch4_conc_ppmv_final = 0.0
    ch4_conc_for_correction = 0.0
    ch4_conc_diff = 0.0
    ch4_from_h2o = 0.0

    ignore_count = 5
    last_time = None

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.15,maxVal=20.0)
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
    init = InitialValues()
    initialize_Baseline(1001)
    r = anC12O2[0](d,init,deps)
    ANALYSIS.append(r)
    ch4_conc_12CO2 = M1*r[1000,2]
    vy_87 = r[87,"y"]
    pre_peak_87 = r[87,"peak"]
    pre_base_87 = r[87,"base"]
    cm_shift = r["base",3]

    initialize_Baseline(1000)
    if abs(cm_shift) > 0.07 or abs(vy_87-1.568) > 0.5 or pre_peak_87 < 10:
        init["base",3] = 0.0
        r = anC12O2[2](d,init,deps)
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

elif d["spectrumId"] == 106 and d["ngroups"] >= 8:  # C13O2
    init = InitialValues()
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


    initialize_Baseline(1000)

    #init[1000,2] = ch4_ampl
    #  rella - 2011 0216 - piping in the CH4 measurement from the methane region 6057.8 wvn
    #  hoffnagle - 2011 0307 - change name of CH4 to distinguish correction from high-precision CH4
    init[1002,2] = ch4_conc_for_correction*1e-4/M1

    r = anC13O2[1](d,init,deps)
    ANALYSIS.append(r)
    peak88_ch4 = r[88,"peak"]
    ch4_conc_13CO2 = M1*r[1002,2]

    f = numpy.array(d.fitData["freq"])
    l = numpy.array(d.fitData["loss"])
    good = (f >= 6251.312) & (f <= 6251.318)
    if len(l[good]) > 0:
        polypeak88 = numpy.average(l[good])
    else:
        polypeak88 = 0.0
    polypeak88_baseave = polypeak88 - c13_base_ave


    initialize_Baseline(1000)

    # methane initialization was here - rella 2011 0303

    r = anC13O2[2](d,init,deps)
    ANALYSIS.append(r)
    agalbase_88 = r[88,"base"]
    apeak88 = r[88,"peak"]
    shift_88 = r["base",3]
    ay_88 = r[88,"y"]
    abase1 = r["base",1]
    h2_18o = r[1003,2]
    #if (c13_fit_quality <= 0.6) and (ch4_conc_12CO2 <= 0.05) and (ch4_raw <= 0.01) and (apeak88 >= 2) and (abs(shift_88) <= 0.02):
    if (c13_fit_quality <= 10) and (ch4_conc_12CO2 <= 0.5) and (ch4_raw <= 0.5) and (apeak88 >= 2) and (abs(shift_88) <= 0.02) and (ch4_conc_diff <= 5):
        adjust_88 = shift_88
    else:
        adjust_88 = 0.0

elif d["spectrumId"] == 109:  # H2O at 6250.4
    #  Variable peak water fitter
    init = InitialValues()
    initialize_Baseline(1002)
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    shift_91 = r["base",3]
    adjust_91 = shift_91
    if (abs(shift_91) > 0.03) or (r[91,"peak"] < 7):
        #  Fixed peak water fitter
        initialize_Baseline(1002)
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
    initialize_Baseline(1002)
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

elif d["spectrumId"]==11 and d["ngroups"]>9:   #H2O at 6057.8
    init = InitialValues()
    r = anH2O[3](d,init,deps)
    ANALYSIS.append(r)
    if abs(r["base",3]) >= 0.01 or abs(r[75,"y"]-0.83)>0.3:
        r = anH2O[4](d,init,deps)
        ANALYSIS.append(r)
    h2o_res = r["std_dev_res"]
    peak_75 = r[75,"peak"]
    h2o_quality = fitQuality(h2o_res,peak_75,50,1)
    shift_75 = r["base",3]
    ch4_from_h2o = 100.0*r[1002,2]

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = numpy.mean(d.pztValue[cal])
        pzt_stdev = numpy.std(d.pztValue[cal])

    str_75 = r[75,"strength"]
    y_75 = r[75,"y"]
    z_75 = r[75,"z"]
    base_75 = r[75,"base"]
    h2o_conc = peak_75 * 0.01002
    if peak_75 > 3.0 and abs(shift_75) < 0.03 and h2o_quality < 1.5:
        adjust_75 = shift_75
    else:
        adjust_75 = 0.0

    r = anH2O[5](d,init,deps)     #  Original CFADS fit included for comparison
    ANALYSIS.append(r)
    if abs(r["base",3]) >= 0.01:
        r = anH2O[4](d,init,deps)
        ANALYSIS.append(r)
    CFADS_h2o_conc = r[75,"peak"] * 0.01002


elif (d["spectrumId"]==25) and (d["ngroups"]>13):
    init = InitialValues()
    r = anCH4[0](d,init,deps)
    ANALYSIS.append(r)
    ch4_vy = r[1002,5]
    vch4_conc_ppmv = 10*r[1002,2]
    ch4_high_shift = r["base",3]
#  Polishing step with fixed center, variable y if line is strong and shift is small
    if (r[1002,2] > 0.005) and (abs(ch4_high_shift) <= 0.07):
        init["base",3] = ch4_high_shift
        ch4_high_adjust = ch4_high_shift
        r = anCH4[1](d,init,deps)
        ANALYSIS.append(r)
#  Polishing step with fixed center and y if line is weak or shift is large
    else:
        init["base",3] = 0.0
        ch4_high_adjust = 0.0
        init[1002,5] = 1.08
        r = anCH4[2](d,init,deps)
        ANALYSIS.append(r)

    CFADS_ch4_amp = r[1002,2]
    ch4_conc_raw = 10*r[1002,2]
    CFADS_ch4_y = r[1002,5]
    CFADS_base = r["base",0]
    ch4_adjconc_ppmv = CFADS_ch4_y*ch4_conc_raw*(140.0/P)
    ch4_splinemax = r[1002,"peak"]
    ch4_peakvalue = ch4_splinemax+CFADS_base
    CFADS_base_avg  = initExpAverage(CFADS_base_avg,CFADS_base,10,100,CFADS_counter)
    ch4_peak_baseavg = ch4_peakvalue-CFADS_base_avg
    ch4_conc_ppmv_final = ch4_peak_baseavg/216.3
    ch4_res = r["std_dev_res"]
    CFADS_counter += 1

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = numpy.mean(d.pztValue[cal])
        pzt_stdev = numpy.std(d.pztValue[cal])

elif d["spectrumId"]==29 and (d["ngroups"]>6):
    init = InitialValues()
    init[70,"strength"] = 0.0345*str_75
    r = anCH4[3](d,init,deps)
    ANALYSIS.append(r)
    CFADS_base  = r["base",0]
    ch4_vy = r[1002,5]
    ch4_low_shift = r["base",3]
    ch4_low_adjust = 0.0

    # moved baseave outside of condition
    CFADS_base_avg  = initExpAverage(CFADS_base_avg,CFADS_base,2,100,CFADS_counter)

    if r[1002,2] > 0.150 and abs(ch4_low_shift) < 0.03:
    #    CFADS_base_avg  = initExpAverage(CFADS_base_avg,CFADS_base,2,100,CFADS_counter)
        ch4_y_avg  = initExpAverage(ch4_y_avg,ch4_vy,10,0.02,CFADS_counter)
        ch4_low_adjust = ch4_low_shift
        CFADS_counter += 1
    init["base",0] = CFADS_base_avg
    init[1002,5] = ch4_y_avg
    r = anCH4[4](d,init,deps)
    ANALYSIS.append(r)
    CFADS_ch4_amp = r[1002,2]
    CFADS_base = r["base",0]
    ch4_conc_raw = 9.8932*r[1002,2]
    ch4_adjconc_ppmv = 0.9157*ch4_y_avg*ch4_conc_raw*(140.0/P)
    ch4_splinemax_for_correction = r[1002,"peak"]
    ch4_peak_baseavg = ch4_splinemax_for_correction+CFADS_base-CFADS_base_avg
    ch4_conc_diff = abs(ch4_conc_for_correction - ch4_peak_baseavg/216.3)
    ch4_conc_for_correction = ch4_peak_baseavg/216.3
    ch4_res = r["std_dev_res"]

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = numpy.mean(d.pztValue[cal])
        pzt_stdev = numpy.std(d.pztValue[cal])


#  Corrections and calibrations added 12 July 2010 (Chris)
#  Hoffnagle 2011 0307:  changed corrections to use CFADS water lines
#  Hoffnagle 2011 0309:  added methane from SID 29
#  (1) Correct offsets first
peak87_baseave_offset = peak87_baseave + P87_off
peak88_baseave_offset = peak88_baseave + P88_off
ch4_offset = ch4_raw + CH4_off
peak91_offset = peak_91 + P91_off
peak96_offset = peak_96 + P96_off
ch4_splinemax_spec = ch4_splinemax_for_correction + CH4_splinemax_offset + CH4_H1*peak_75
#  (2) Fitting cross-talk corrections come next
#  Methane correction
ch4_spec = ch4_offset + CH4_A1*peak87_baseave_offset + CH4_H1*peak91_offset + CH4_H1A1*peak87_baseave_offset*peak91_offset
#  HDO correction
peak96_spec = peak_96 + P96_H2*peak96_offset**2
#  H2O correction
peak91_spec = peak91_offset
#  12CO2 correction -- 20110307 hoffnagle changed to use CFADS spectroscopy
peak87_baseave_spec = peak87_baseave_offset + P87_H1*peak_75
#  13CO2 correction -- 20110307 hoffnagle changed to use CFADS spectroscopy -- 20110309 added methane
#  13CO2 correction -- 20110321 Chris/Yonggang added H2O-CH4 bi-linear corr term
peak88_baseave_spec = peak88_baseave_offset + P88_H1*peak_75 + P88_H1A1*peak_75*peak87_baseave_spec + P88_H2A1*peak87_baseave_spec*peak_75**2
peak88_baseave_spec += (P88_M1*ch4_splinemax_spec + P88_M2*ch4_splinemax_spec**2 + P88_M1H1*ch4_splinemax_spec*peak_75)
#  (3) Provide corrected outputs based on the spectroscopic values
#  Water concentration
h2o_actual = H1*peak91_spec + H2*peak91_spec**2
#  Methane calibration
ch4_conc = M1*ch4_spec
#  Water correction to CO2 concentration -- 20110307 hoffnagle changed to conform to CFADS
wd_ratio = 1.0 + h2o_conc*(H1_wd + H2_wd*h2o_conc)
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
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]
else:
    ignoreThis = True

ignore_count = max(0,ignore_count-1)
if (ignore_count == 0) and (not ignoreThis):
    RESULT = {"y87_ave":y87_ave,"z87_ave":z87_ave,"shift_87":shift_87,"str_87":str_87,"peak87_baseave":peak87_baseave,"base_87":base_87,"slope_87":slope_87,
              "y88":y88,"z88":z88,"shift_88":shift_88,"c13_fit_quality":c13_fit_quality,"str_88":str_88,"peak88_baseave":peak88_baseave,"peak_88":peak_88,"base_88":base_88,"slope_88":slope_88,
              "y_91":y_91,"z_91":z_91,"shift_91":shift_91,"peak_91":peak_91,"ch4_conc_12CO2":ch4_conc_12CO2,"ch4_conc_13CO2":ch4_conc_13CO2,"peak_87":peak_87,
              "adjust_87":adjust_87,"h2_18o":h2_18o,"adjust_88":adjust_88,"peak_96":peak_96,"co2_water_reg":co2_water_reg,"ch4_conc_h2o":ch4_conc_h2o,
              "peak_92":peak_92,"c2h4_conc":c2h4_conc,"datapoints":d["datapoints"],"datagroups":d["ngroups"],"y_87":y_87,
              "polypeak88_baseave":polypeak88_baseave,"ch4_conc_ppmv_final":ch4_conc_ppmv_final,
              "peak88_ch4":peak88_ch4,"ch4_conc_for_correction":ch4_conc_for_correction,"ch4_from_h2o":ch4_from_h2o,
              "ch4_raw":ch4_raw,"ch4_spec":ch4_spec,"peak91_spec":peak91_spec,"peak96_spec":peak96_spec,"peak87_baseave_spec":peak87_baseave_spec,
              "peak88_baseave_spec":peak88_baseave_spec,"pre_peak_87":pre_peak_87,"pre_base_87":pre_base_87,
              "h2o_actual":h2o_actual,"ch4_conc":ch4_conc,"12CO2_ppm_wet":CO2_12_ppm_wet,"12CO2_ppm_dry":CO2_12_ppm_dry,
              "13CO2_ppm_wet":CO2_13_ppm_wet,"13CO2_ppm_dry":CO2_13_ppm_dry,"adjust_91":adjust_91,
              "c12_pzt_ave":c12_pzt_ave,"c12_pzt_stdev":c12_pzt_stdev,"c13_pzt_ave":c13_pzt_ave,"c13_pzt_stdev":c13_pzt_stdev,
              "peak_75":peak_75,"base_75":base_75,"str_75":str_75,"y_75":y_75,"shift_75":shift_75,"adjust_75":adjust_75,"h2o_conc":h2o_conc,
              "ch4_low_adjust":ch4_low_adjust,"ch4_low_shift":ch4_low_shift,"CFADS_ch4_amp":CFADS_ch4_amp,
              "ch4_high_adjust":ch4_high_adjust,"ch4_high_shift":ch4_high_shift,
              "CFADS_base":CFADS_base,"CFADS_base_avg":CFADS_base_avg,"ch4_splinemax_spec":ch4_splinemax_spec,
              "ch4_vy":ch4_vy,"ch4_y_avg":ch4_y_avg,"ch4_splinemax":ch4_splinemax,"ch4_splinemax_for_correction":ch4_splinemax_for_correction,
              "cavity_pressure":P,"species":d["spectrumId"],"fit_time":fit_time,
              "CFADS_h2o_conc":CFADS_h2o_conc,
              "interval":interval,"dasTemp":dasTemp,
              "solenoid_valves":d.sensorDict["ValveMask"],
              "MPVPosition":d.sensorDict["MPVPosition"]}
    RESULT.update(d.sensorDict)
