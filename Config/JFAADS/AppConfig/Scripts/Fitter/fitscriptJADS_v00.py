#  Fit script for N2O concentration measurement at 6562.6 wavenumbers
#  Spectrum IDs taken from older JA analyzer;  added SID 48 for WLM flattening only
#  12 Jul 2012:  Merge prototype N2O fitter with ammonia fitter for water concentration and interference

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

def initialize_NH3_Baseline():
    init[1000,0] = NH3_A0
    init[1000,1] = NH3_Nu0
    init[1000,2] = NH3_Per0
    init[1000,3] = NH3_Phi0
    init[1001,0] = NH3_A1
    init[1001,1] = NH3_Nu1
    init[1001,2] = NH3_Per1
    init[1001,3] = NH3_Phi1

def initialize_N2O_Baseline():
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
    fname = os.path.join(BASEPATH,r"./JADS/JADS spectral library v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anN2O = []
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/N2O_VC_FY_v1_1.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/N2O_only_v1_1.ini")))
    
    anNH3 = []
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/AADS-xx water + ammonia v1_1.ini")))
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/AADS-xx peak 11 v1_1.ini")))
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/AADS-xx peak 12 v1_1.ini")))
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/big water #25 v2_0.ini")))
    
    #  Import instrument specific baseline constants
    
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
    shift25 = 0.0
    shift_a = 0.0
    cm_adjust = 0.0
    h2o_adjust = 0.0
    h2o_conc = 0.0
    co2_conc = 0.0
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
    base_level_n2o = 0
    base_slope_n2o = 0
    peak_1a = 0
    base_1a = 0
    no2_pzt_mean = 0.0
    no2_pzt_stdev = 0.0
    
    last_time = None
   
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.0007,sigmaThreshold=3)
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
    r = anNH3[0](d,init,deps)
    ANALYSIS.append(r)
    peak11a = r[11,"peak"]
    peak15 = r[15,"peak"]
    peak17 = r[17,"peak"]
    str15 = r[15,"strength"]
    str17 = r[17,"strength"]
    shift_a = r["base",3]
    res_a = r["std_dev_res"]
    h2o_conc = 0.02*peak15
    co2_conc = 81.3*peak17
    if peak15 > 2.0 or peak11a > 2.0:
        cm_adjust = shift_a
        shift_avg = expAverage(shift_avg, shift_a, 2, 0.001)
        dh2o = h2o_conc - last_h2o
        last_h2o = h2o_conc
        if abs(dh2o)>1:
            badshot_h2o = 1
        else:
            badshot_h2o = 0
    else:
        cm_adjust = 0.0
    
if (species==1 or species==4) and d["ngroups"]>18:
#   Ammonia region:  fit peaks 11 and 12 separately    
    initialize_NH3_Baseline()
    init["base",3] = shift_avg
    init[15,"strength"] = str15
    init[17,"strength"] = str17
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

    #nh3_conc_ave = 0.5*(nh3_conc_11 + nh3_conc_12)
    nh3_conc_ave = 0.5*(nh3_conc_11 + nh3_conc_12)
    nh3_conc_smooth = initExpAverage(nh3_conc_smooth, nh3_conc_ave, 50, 1, counter)
    counter += 1    

if species==3:
#   Big water region
    init["base",0] = 0.0 
    r = anNH3[3](d,init,deps)
    ANALYSIS.append(r)
    peak25 = r[25,"peak"]
    str25 = r[25,"strength"]
    shift25 = r["base",3]
    res_25 = r["std_dev_res"]
    if peak25 > 5 and abs(shift25) < 0.07:
        h2o_adjust = shift25
    else:
        h2o_adjust = 0.0

if (species == 47 and d["ngroups"] > 6):  #  fit N2O and CO2
    initialize_N2O_Baseline()
    r = anN2O[0](d,init,deps)
    ANALYSIS.append(r)
    shift_n2o = r["base",3]
    peak_1 = r[1,"peak"]
    peak_2 = r[2,"peak"]
    base_level_n2o = r["base",0]
    base_slope_n2o = r["base",1]
    res = r["std_dev_res"]
    
    if peak_2 > 1 and abs(shift_n2o) < 0.05:
        adjust_n2o = shift_n2o
    else:
        adjust_n2o = 0.0
      
if (species == 45 or species == 47):  #  fit N2O only
    initialize_N2O_Baseline()      
    r = anN2O[1](d,init,deps)
    ANALYSIS.append(r)
    peak_1a = r[1,"peak"]   
    base_1a = r[1,"base"]

if species == 48:  # Calibration scan
    n2o_pzt_mean = mean(d.pztValue)
    n2o_pzt_stdev =  std(d.pztValue)
    
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
              "h2o_conc":h2o_conc,"co2_conc":co2_conc,"shift_a":shift_a,"cm_adjust":cm_adjust,
              "peak25":peak25,"shift25":shift25,"h2o_adjust":h2o_adjust,
              "nh3_peak_11":nh3_peak_11,"nh3_base_11":nh3_base_11,"nh3_slope_11":nh3_slope_11,
              "nh3_base_12":nh3_base_12,"nh3_peak_12":nh3_peak_12,"nh3_slope_12":nh3_slope_12,
              "nh3_conc_ave":nh3_conc_ave,"nh3_conc_smooth":nh3_conc_smooth,
              "peak_1":peak_1,"peak_1a":peak_1a,"peak_2":peak_2,"base_1a":base_1a,
              "shift_n2o":shift_n2o,"adjust_n2o":adjust_n2o,
              "base_level_n2o":base_level_n2o,"base_slope_n2o":base_slope_n2o,
              "ngroups":d["ngroups"],"numRDs":d["datapoints"],
              "no2_pzt_mean":no2_pzt_mean,"no2_pzt_stdev":no2_pzt_stdev,          
              "nh3_pzt_mean":nh3_pzt_mean,"nh3_pzt_stdev":nh3_pzt_stdev}
    RESULT.update({"species":species,"fittime":fit_time,"interval":interval,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)