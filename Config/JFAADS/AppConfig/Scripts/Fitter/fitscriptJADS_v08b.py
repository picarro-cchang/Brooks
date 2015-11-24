#  Fit script for N2O concentration measurement at 6562.6 wavenumbers
#  Spectrum IDs taken from older JA analyzer;  added SID 48 for WLM flattening only
#  12 Jul 2012:  Merge prototype N2O fitter with ammonia fitter for water concentration and interference
#  27 Jul 2012:  Add spline for ammonia in N2O region to deal with potential interference
#  31 Jul 2012:  V2 adds water vapor -- HDO doublet at 6562.5 wvn
#   6 Aug 2012:  Try reporting [N2O] from SID 47 instead of 45
#   7 Aug 2012:  Preset baseline slope for 2nd stage N2O fit
#   8 Aug 2012:  Tweak H2O concentration coefficient to get agreement with HBDS
#  27 Nov 2012:  Major change -- merge with CFADS methane fitter
#  28 Feb 2013:  Major change -- merge with 6056.5 CO2 measurement from FCDS
#   6 Mar 2013:  Soil chamber suggests fit inis should have NH3 spline adjusted a0=-0.001 for better agreement with N2O spectrum
#  14 Mar 2013:  Drop 6056.5 CO2 line because of ammonia interference;  try 6058.2 wvn instead
#  26 Mar 2013:  Merge SIDs 2 and 4 from AADS spectroscopy
#  13 May 2103:  Several tweaks during prototype development.  Next major change is to add N2O peak to ammonia fits.
#  29 May 2013:  Fixed bug in NH3 fitter (probably affects all NH3 fitters).  Baseline slope was not initialized correctly.
#  31 May 2013:  Changed N2O preset factor in NH3 region from 0.4813 to 0.4358 based on cross-talk test. 
#  23 Jul 2013:  Adjusted dependency between HDO line strengths based on low-pressure test.
#  21 Jan 2014:  Adjusted frequency of NH3 spline based on new finescans; let WLM track off NH3

#  SIDs:
#    2  Ammonia and water from AADS (V6 modifies schemes to unify NH3 and H2O measurements)
#    3  "Big water" from AADS (not used)
#    4  Ammonia only from AADS (not used starting with V6)
#   25  CH4 from CFADS
#   45  N2O only
#   46  CO2 at 6058.2 wvn developed for JADS
#   47  N2O, CO2, and HDO

from numpy import any, mean, std, sqrt
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
    return sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

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
    
def initialize_NH3_Baseline():
    init["base",0] = NH3_baseline_level
    init["base",1] = NH3_baseline_slope
    init[1000,0] = NH3_A0
    init[1000,1] = NH3_Nu0
    init[1000,2] = NH3_Per0
    init[1000,3] = NH3_Phi0
    init[1001,0] = NH3_A1
    init[1001,1] = NH3_Nu1
    init[1001,2] = NH3_Per1
    init[1001,3] = NH3_Phi1

def initialize_N2O_Baseline():
    init["base",0] = N2O_baseline_level
    init[1000,0] = N2O_A0
    init[1000,1] = N2O_Nu0
    init[1000,2] = N2O_Per0
    init[1000,3] = N2O_Phi0
    init[1001,0] = N2O_A1
    init[1001,1] = N2O_Nu1
    init[1001,2] = N2O_Per1
    init[1001,3] = N2O_Phi1

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./JADS/JADS spectral library v3_8.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CFJADS-xx CH4 v2_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CFJADS-xx CH4 FC VY v2_0.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CFJADS-xx CH4 FC FY v2_0.ini")))
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./JADS/CO2 6058 VC VY v1_1.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./JADS/CO2 6058 FC FY v1_1.ini")))       
    
    anN2O = []
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/N2O+CO2+HDO+CH4_VC_FY_v3_3.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/N2O_only_w_HDO+CH4_v3_3.ini")))
    
    anNH3 = []
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/AADS-xx water + ammonia + CH4+N2O v1_1.ini")))
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/AADS-xx peak 11 + CH4+N2O v1_1.ini")))
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/AADS-xx peak 12 + CH4+N2O v1_1.ini")))
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/big water #25 v2_0 VY.ini")))
    
    #  Import instrument specific baseline constants

    CFADS_baseline_level = instrParams['CFADS_Baseline_level']
    CFADS_baseline_slope = instrParams['CFADS_Baseline_slope']
    CFADS_A0 = instrParams['CFADS_Sine0_ampl']
    CFADS_Nu0 = instrParams['CFADS_Sine0_freq']
    CFADS_Per0 = instrParams['CFADS_Sine0_period']
    CFADS_Phi0 = instrParams['CFADS_Sine0_phase']
    CFADS_A1 = instrParams['CFADS_Sine1_ampl']
    CFADS_Nu1 = instrParams['CFADS_Sine1_freq']
    CFADS_Per1 = instrParams['CFADS_Sine1_period']
    CFADS_Phi1 = instrParams['CFADS_Sine1_phase']
    
    N2O_baseline_level = instrParams['N2O_Baseline_level']
    N2O_baseline_slope = instrParams['N2O_Baseline_slope']
    N2O_A0 = instrParams['N2O_Sine0_ampl']
    N2O_Nu0 = instrParams['N2O_Sine0_freq']
    N2O_Per0 = instrParams['N2O_Sine0_period']
    N2O_Phi0 = instrParams['N2O_Sine0_phase']
    N2O_A1 = instrParams['N2O_Sine1_ampl']
    N2O_Nu1 = instrParams['N2O_Sine1_freq']
    N2O_Per1 = instrParams['N2O_Sine1_period']
    N2O_Phi1 = instrParams['N2O_Sine1_phase']
    
    NH3_baseline_level = instrParams['NH3_Baseline_level']
    NH3_baseline_slope = instrParams['NH3_Baseline_slope']
    NH3_A0 = instrParams['NH3_Sine0_ampl']
    NH3_Nu0 = instrParams['NH3_Sine0_freq']
    NH3_Per0 = instrParams['NH3_Sine0_period']
    NH3_Phi0 = instrParams['NH3_Sine0_phase']
    NH3_A1 = instrParams['NH3_Sine1_ampl']
    NH3_Nu1 = instrParams['NH3_Sine1_freq']
    NH3_Per1 = instrParams['NH3_Sine1_period']
    NH3_Phi1 = instrParams['NH3_Sine1_phase']
    
    CO2_on_N2O_off = instrParams['co2_on_n2o_offset']
    CO2_on_N2O_lin = instrParams['co2_on_n2o_linear']
    P41_off = instrParams['CO2_offset']
    P41_M1 = instrParams['CO2_methane_linear']
    
    #  Globals to pass between spectral regions
    
    str15 = 0.0
    str17 = 0.0
    shift_avg = 0.0
    last_h2o = 0.0
    badshot_h2o = 0
    last_base_11 = 0.0
    last_base_12 = 0.0
    badshot_nh3 = 0
    counter = -10
    
    peak11a = 0.0
    peak15 = 0.0
    peak17 = 0.0
    
    res_a = 0.0
    res_11 = 0.0
    res_12 = 0.0
    peak25 = 0.0
    str25 = 0.0
    shift25 = 0.0
    shift_a = 0.0
    cm_adjust = 0.0
    h2o_adjust = 0.0
    h2o_conc = 0.0
    co2_conc = 0.0
    co2_from_nh3 = 0.0
    nh3_peak_11 = 0.0
    nh3_base_11 = 0.0
    nh3_slope_11 = 0.0
    nh3_peak_12 = 0.0
    nh3_base_12 = 0.0
    nh3_slope_12 = 0.0
    nh3_conc_ave = 0.0
    nh3_conc_smooth = 0.0   
    nh3_pzt_mean = 0.0
    nh3_pzt_stdev = 0.0
    
    shift_n2o = 0
    adjust_n2o = 0
    peak_1 = 0
    peak_2 = 0
    str_2 = 0
    base_level_n2o = 0
    base_slope_n2o = 0
    peak_1a = 0
    base_1a = 0
    n2o_conc = 0
    res = 0
    n2o_pzt_mean = 0.0
    n2o_pzt_stdev = 0.0
    
    y_25 = 0
    nh3_shift_11 = 0
    nh3_shift_12 = 0
    splineamp = 0
    
    peak_4 = 0
    str_4 = 0

    ch4_vy = 1.06
    vch4_conc_ppmv = 0.0
    ch4_shift = 0.0
    ch4_adjust = 0.0
    ch4_amp = 0.0
    ch4_splinemax = 0.0
    ch4_conc_raw = 0.0
    ch4_y = 1.06
    ch4_base = 800
    ch4_conc_ppmv_final = 0.0
    ch4_res = 0.0
    ch4_pzt_mean = 0.0
    ch4_pzt_stdev = 0.0
    
#  New CO2 in CFADS methane region (6058.2 wvn)
    adjust_41 = 0.0
    shift_41 = 0.0
    strength_41 = 0.0
    vy_41 = 1.60
    y_41 = 1.60
    base_41 = 0.0
    peak_41 = 0.0
    peak41_spec = 0.0
    co2_conc_6058 = 0.0
    co2_conc_6562 = 0.0
    co2_res = 0.0
    
    y_4 = 0.0
    y_5 = 0.0
    peak4_center = 0.0
    peak5_center = 0.0
    
    last_time = None
    
   
    
   
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.002,sigmaThreshold=5)
d.sparse(maxPoints=200,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

species = (d.subschemeId & 0x3FF)[0]

tstart = time.clock()
RESULT = {}
r = None

if species==2 and d["ngroups"]>29:            #  spectrumId historically was 0 
#   Fit ammonia, CO2, and water lines
    initialize_NH3_Baseline()
    init[15,"strength"] = 0.0001  #  Probably not necessary
    init[17,"strength"] = 0.0001
    init[1002,2] = 0.00108*ch4_amp
    init[80,"strength"] = 0.4358*n2o_conc
    r = anNH3[0](d,init,deps)
    ANALYSIS.append(r)
    peak11a = r[11,"peak"]
    peak15 = r[15,"peak"]
    peak17 = r[17,"peak"]
    str15 = r[15,"strength"]
    str17 = r[17,"strength"]
    shift_a = r["base",3]
    res_a = r["std_dev_res"]
    h2o_conc = 0.0177*peak15
    co2_from_nh3 = 81.3*peak17
    #if peak15 > 2.0 or peak11a > 2.0:
    if peak15 > 20.0 or peak11a > 2.0:
        h2o_adjust = shift_a
        shift_avg = expAverage(shift_avg, shift_a, 2, 0.001)
        dh2o = h2o_conc - last_h2o
        last_h2o = h2o_conc
        if abs(dh2o)>1:
            badshot_h2o = 1
        else:
            badshot_h2o = 0
    else:
        h2o_adjust = 0.0
               
#   Next fit ammonia peaks 11 and 12 separately    
    init["base",3] = shift_avg
    init[15,"strength"] = str15
    init[17,"strength"] = str17
    init[80,"strength"] = 0.4358*n2o_conc
    r = anNH3[1](d,init,deps)
    ANALYSIS.append(r)
    res_11 = r["std_dev_res"]
    nh3_peak_11 = r[11,"peak"]
    nh3_str_11 = r[11,"strength"] 
    nh3_quality_11 = fitQuality(res_11,nh3_peak_11,50,0.2)
    if nh3_quality_11 <= 15:
        nh3_base_11 = r["base",0]
        nh3_slope_11 = r["base",1]
        nh3_shift_11 = r["base",3]
        nh3_conc_11 = 8.75*nh3_peak_11
    dbase = nh3_base_11 - last_base_11
    last_base_11 = nh3_base_11
    if abs(dbase) > 3:
        badshot_nh3 = 1
    else:
        badshot_nh3 = 0
 
    initialize_NH3_Baseline()
    init["base",3] = shift_avg
    init[15,"strength"] = str15
    init[17,"strength"] = str17
    init[80,"strength"] = 0.4358*n2o_conc
    r = anNH3[2](d,init,deps)
    ANALYSIS.append(r)
    res_12 = r["std_dev_res"]
    nh3_peak_12 = r[11,"peak"]   #  NH3 conc is expressed in terms of peak 11, but fit uses peak 12 through dependency
    nh3_str_12 = r[11,"strength"] 
    nh3_quality_12 = fitQuality(res_12,nh3_peak_12,50,0.2)
    if nh3_quality_12 <= 15:
        nh3_base_12 = r["base",0]
        nh3_slope_12 = r["base",1]
        nh3_shift_12 = r["base",3]
        nh3_conc_12 = 8.75*nh3_peak_12
    dbase = nh3_base_12 - last_base_12
    last_base_12 = nh3_base_12
    if abs(dbase) > 3:
        badshot_nh3 = 1
    else:
        badshot_nh3 = 0
 
    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        nh3_pzt_mean = mean(d.pztValue[cal])
        nh3_pzt_stdev = std(d.pztValue[cal])    

    nh3_conc_ave = 0.5*(nh3_conc_11 + nh3_conc_12)
    nh3_conc_smooth = initExpAverage(nh3_conc_smooth, nh3_conc_ave, 50, 1, counter)
    counter += 1    

if species==3:                          #   Big water region
    initialize_NH3_Baseline()
    init["base",0] = 0.0 
    r = anNH3[3](d,init,deps)
    ANALYSIS.append(r)
    peak25 = r[25,"peak"]
    str25 = r[25,"strength"]
    shift25 = r["base",3]
    res_25 = r["std_dev_res"]
    h2o_conc = 2.685*peak25
    y_25 = r[25,"y"]
    if peak25 > 1 and abs(shift25) < 0.07:
        h2o_adjust = shift25
    else:
        h2o_adjust = 0.0

if (species == 47 and d["ngroups"] > 6):  #  fit N2O, CO2, and HDO
    initialize_N2O_Baseline()
    init[1002,2] = 0.000955*nh3_conc_ave
    init[1003,2] = 0.00108*ch4_amp
    init[4, "y"] = 0.7922 + 0.0402*h2o_conc  #FOR INSTRUMENTS WITH INCORRECT PRESSURE CAL
    init[5, "y"] = 0.7844 + 0.0393*h2o_conc
    # init[4, "y"] = 0.8402 + 0.0426*h2o_conc   #FOR INSTRUMENTS WITH current PRESSURE CAL
    # init[5, "y"] = 0.8319 + 0.0417*h2o_conc
    r = anN2O[0](d,init,deps)
    ANALYSIS.append(r)
    shift_n2o = r["base",3]
    peak_1 = r[1,"peak"]
    peak_2 = r[2,"peak"]
    peak_4 = r[4,"peak"]
    str_2 = r[2,"strength"]
    str_4 = r[4,"strength"]
    co2_conc_6562 = 252.9*peak_2
    base_level_n2o = r["base",0]
    base_slope_n2o = r["base",1]
    res = r["std_dev_res"]
    splineamp = r[1002,2]
    y_4 = r[4,"y"]
    y_5 = r[5,"y"]
    peak4_center = r[4, "center"]
    peak5_center = r[5, "center"]
    #n2o_conc = peak_1/1.82
    
    #if (peak_1 > 1 or peak_2 > 1) and abs(shift_n2o) < 0.05:
    if (peak_1 > 1.5 or peak_2 > 1 or peak_4 > 1.5 or nh3_conc_ave > 100) and abs(shift_n2o) < 0.05:    
        adjust_n2o = shift_n2o
    else:
        adjust_n2o = 0.0
        
elif (species == 47 and d["ngroups"] < 7):
    print d["ngroups"]
    print d.filterHistory
      
if (species == 45 or species == 47):  #  fit N2O only with preset HDO and ammonia
    initialize_N2O_Baseline()
    init["base",1] = base_slope_n2o
    init[2,"strength"] = str_2
    init[4,"strength"] = str_4
    init[5,"strength"] = 0.57*str_4
    init[1002,2] = 0.000955*nh3_conc_ave
    init[1003,2] = 0.00108*ch4_amp    
    init[4, "y"] = 0.7922 + 0.0402*h2o_conc  #FOR INSTRUMENTS WITH INCORRECT PRESSURE CAL
    init[5, "y"] = 0.7844 + 0.0393*h2o_conc
    # init[4, "y"] = 0.8402 + 0.0426*h2o_conc   #FOR INSTRUMENTS WITH current PRESSURE CAL
    # init[5, "y"] = 0.8319 + 0.0417*h2o_conc
    r = anN2O[1](d,init,deps)
    ANALYSIS.append(r)
    peak_1a = r[1,"peak"]   
    base_1a = r[1,"base"]
    n2o_conc = (peak_1a + CO2_on_N2O_off + CO2_on_N2O_lin*peak_2)/1.82

if species == 48:  # Calibration scan
    n2o_pzt_mean = mean(d.pztValue)
    n2o_pzt_stdev =  std(d.pztValue)
    
if (species==25) and (d["ngroups"]>6):
    initialize_CFADS_Baseline()
    r = anCH4[0](d,init,deps)
    ANALYSIS.append(r)
    ch4_vy = r[1002,5]
    vch4_conc_ppmv = 10*r[1002,2]
    ch4_shift = r["base",3]
#  Polishing step with fixed center, variable y if line is strong and shift is small
    if (r[1002,2] > 0.005) and (abs(ch4_shift) <= 0.07) and (abs(ch4_vy-1.08) < 0.3):
        init["base",3] = ch4_shift
        ch4_adjust = ch4_shift
        r = anCH4[1](d,init,deps)
        ANALYSIS.append(r)
#  Polishing step with fixed center and y if line is weak or shift is large
    else:    
        init["base",3] = 0.0
        ch4_adjust = 0.0
        init[1002,5] = 1.08
        r = anCH4[2](d,init,deps)
        ANALYSIS.append(r)
    
    ch4_amp = r[1002,2]
    ch4_conc_raw = 10*r[1002,2]
    ch4_y = r[1002,5]
    ch4_base = r["base",0]
    ch4_splinemax = r[1002,"peak"]
    ch4_conc_ppmv_final = ch4_splinemax/216.3
    ch4_res = r["std_dev_res"]

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        ch4_pzt_mean = mean(d.pztValue[cal])
        ch4_pzt_stdev = std(d.pztValue[cal])
        
if species == 46:                                # CO2 at 6058.2 
    initialize_CFADS_Baseline()
    init[1002,2] = 0.2*h2o_conc
    init[1003,2] = 0.01*ch4_conc_raw
    init[1004,2] = 0.00002*nh3_conc_ave
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    shift_41 = r["base",3]
    vy_41 = r[41,"y"]
 
    if (r[41,"peak"] > 5) and (abs(shift_41) < 0.04) and (abs(vy_41-1.6) < 0.5):   
        adjust_41 = shift_41
        init[41,"y"] = vy_41
    else:
        adjust_41 = 0.0
    
    init["base",3] = adjust_41
    r = anCO2[1](d,init,deps)
    r = anCO2[1](d,init,deps)
    ANALYSIS.append(r)    
    y_41 = r[41,"y"]
    strength_41 = r[41,"strength"]
    base_41 = r[41,"base"]
    peak_41 = r[41,"peak"]
    peak41_spec = peak_41 + P41_off + P41_M1*ch4_conc_ppmv_final
    co2_conc_6058 = 8.442*peak41_spec
    co2_res = r["std_dev_res"]
    
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
    RESULT = {"res_a":res_a,"res_11":res_11,"res_12":res_12,"badshot_nh3":badshot_nh3,
              "peak11a":peak11a,"peak15":peak15,"peak17":peak17,"badshot_h2o":badshot_h2o,
              "h2o_conc":h2o_conc,"co2_conc_6562":co2_conc_6562,"shift_a":shift_a,"cm_adjust":cm_adjust,
              "peak25":peak25,"str25":str25,"shift25":shift25,"h2o_adjust":h2o_adjust,
              "nh3_peak_11":nh3_peak_11,"nh3_base_11":nh3_base_11,"nh3_slope_11":nh3_slope_11,
              "nh3_base_12":nh3_base_12,"nh3_peak_12":nh3_peak_12,"nh3_slope_12":nh3_slope_12,
              "nh3_conc_ave":nh3_conc_ave,"nh3_conc_smooth":nh3_conc_smooth,"co2_from_nh3":co2_from_nh3,
              "n2o_conc":n2o_conc,"peak_1":peak_1,"peak_1a":peak_1a,"peak_2":peak_2,"base_1a":base_1a,
              "shift_n2o":shift_n2o,"adjust_n2o":adjust_n2o,"res":res,
              "base_level_n2o":base_level_n2o,"base_slope_n2o":base_slope_n2o,
              "peak_4":peak_4,"str_4":str_4,
              "ngroups":d["ngroups"],"numRDs":d["datapoints"],
              "nh3_shift_11":nh3_shift_11,"nh3_shift_12":nh3_shift_11,"y_25":y_25,
              "splineamp":splineamp,"ch4_splinemax":ch4_splinemax,
              "ch4_shift":ch4_shift,"ch4_adjust":ch4_adjust,"ch4_vy":ch4_vy,
              "vch4_conc_ppmv":vch4_conc_ppmv,"ch4_amp":ch4_amp,"ch4_conc_raw":ch4_conc_raw,"ch4_y":ch4_y,
              "ch4_base":ch4_base,"ch4_conc_ppmv_final":ch4_conc_ppmv_final,"ch4_res":ch4_res,
              "vy_41":vy_41,"y_41":y_41,"base_41":base_41,"shift_41":shift_41,"adjust_41":adjust_41,
              "peak_41":peak_41,"peak41_spec":peak41_spec,"co2_conc_6058":co2_conc_6058,"co2_res":co2_res,
              "ch4_pzt_mean":ch4_pzt_mean,"ch4_pzt_stdev":ch4_pzt_stdev,
              "n2o_pzt_mean":n2o_pzt_mean,"n2o_pzt_stdev":n2o_pzt_stdev,          
              "nh3_pzt_mean":nh3_pzt_mean,"nh3_pzt_stdev":nh3_pzt_stdev,"y_4":y_4, "y_5":y_5, "peak4_center":peak4_center, "peak5_center":peak5_center}
    RESULT.update({"species":species,"fittime":fit_time,"interval":interval,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
    
