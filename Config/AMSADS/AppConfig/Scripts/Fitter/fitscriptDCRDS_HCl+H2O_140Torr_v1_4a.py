#  Fit script HCl using the 5739.26 wavenumber line, with water and methane as reference lines
#  2015-07-23:  Started
#  2015-08-14:  Added second spectrum ID with stronger water line for WLM offset
#  2015-09-01:  Ignore first few points for H2O to settle
#  2016-04-04:  Changed scheme trying to smooth Allan variance
#  2016-04-06:  Removed reporting made superfluous by new scheme
#  2016-04-08:  Modification to operate at 140 Torr
#  2016-05-17:  Changed again to operate at 140 Torr and 80 C
#  2016-06-15:  Added extra testing for baseline jumps to exclude bogus measurements when hydrocarbon solvents are used in fab
#  2016-08-18:  Changed reporting of contaminated samples to report with flag
#  2016-12-12:  Changed logic leading to VCFY fit for better performance with dry, high concentration methane
#  2017-02-22:  Completely new approach to organic suppression:  Differential CRDS interleaving baseline and data measurements
#  2018-03-30:  Resume DCRDS experiments.  I will skip some attempts from 2017 to place the "baseline" points on the HCl peak
#               Merge multiple changes made to conventional HCl analysis from Fall 2017 through Spring 2018

from numpy import any, amin, amax, mean, std, sqrt, log10
import numpy as np
import os.path
import time

def initialize_Baseline():
    init[1000,0] = A0
    init[1000,1] = Nu0
    init[1000,2] = Per0
    init[1000,3] = Phi0
    init[1001,0] = A1
    init[1001,1] = Nu1
    init[1001,2] = Per1
    init[1001,3] = Phi1

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./HCl/spectral library HCl v2_2.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_HCl_140Torr.ini")
    instrParams = getInstrParams(fname)
    
    anHCl = []
    anHCl.append(Analysis(os.path.join(BASEPATH,r"./HCl/HCl+H2O 140 Torr VC VY v1_1.ini")))
    anHCl.append(Analysis(os.path.join(BASEPATH,r"./HCl/HCl+H2O 140 Torr FC FY v1_1.ini")))
    anHCl.append(Analysis(os.path.join(BASEPATH,r"./HCl/HCl+H2O 140 Torr VC FY v1_1.ini")))
    anHCl.append(Analysis(os.path.join(BASEPATH,r"./HCl/HCl+H2O+HC 140 Torr VC FY v1_1.ini")))
    anHCl.append(Analysis(os.path.join(BASEPATH,r"./HCl/Dummy v1_1.ini")))
    
    #  Import instrument specific baseline constants and cross-talk corrections for HCl
    
    baseline_level = instrParams['HCl_Baseline_level']
    baseline_slope = instrParams['HCl_Baseline_slope']
    A0 = instrParams['HCl_Sine0_ampl']
    Nu0 = instrParams['HCl_Sine0_freq']
    Per0 = instrParams['HCl_Sine0_period']
    Phi0 = instrParams['HCl_Sine0_phase']
    A1 = instrParams['HCl_Sine1_ampl']
    Nu1 = instrParams['HCl_Sine1_freq']
    Per1 = instrParams['HCl_Sine1_period']
    Phi1 = instrParams['HCl_Sine1_phase']
    
    hcl_lin = instrParams['HCl_linear']
    h2o_lin = instrParams['H2O_linear']
    h2o_slin = instrParams['H2O_strength_linear']
    ch4_hcl_lin = instrParams['CH4_to_HCl_linear']
    h2o_hcl_lin = instrParams['H2O_to_HCl_linear']
    
    #  Globals for communication between spectral regions
    
    hcl_shift = 0.0
    hcl_adjust = 0.0
    baseline_level = 0.0
    baseline_slope = baseline_slope
    hcl_adjust = 0.0
    peak62 = 0.0
    str62 = 0.0
    y62 = 1.396
    base70 = 0.0    
    peak70 = 0.0
    str70 = 0.0
    y70 = 1.508
    ch4_ampl = 0.0
    res = 0.0
    y62lib = 140*spectrParams['peak62']['y']
    
    hcl_conc_raw = 0.0
    hcl_conc = 0.0
    h2o_conc_raw = 0.0
    ch4_conc_raw = 0.0
    
    PF_shift = 0.0
    PF_h2o_conc = 0.0
    PF_ch4_conc = 0.0
    PF_hcl_conc = 0.0
    PF_ch3oh_conc = 0.0
    PF_c2h4_conc = 0.0
    PF_res = 0.0
    
    pzt_mean = 32768
    pzt_stdev = 0
    
    incomplete_spectrum = 0
    noBaseline = 0
    baseMean = instrParams['HCl_Baseline_level']
    baseStdev = 0.0
    minBasePoints = 0
    maxBasePoints = 0
    meanBasePoints = 0
    spectrum_Score = 0.0
    
    ignore_count = 3
    last_time = None
    
# For offline analysis and output to file    
    # out = open("Fit_results.txt","w")
    # first_fit = 1

# ---------  This section goes to end of file  ----------
        # if first_fit:
            # keys = sorted([k for k in RESULT])
            # print>>out," ".join(keys)
            # first_fit = 0
        # print>>out," ".join(["%s" % RESULT[k] for k in keys])
    
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
#  Point-by-point baseline subtraction and spectrum generation starts here
ts = d.timestamp
loss = d.uncorrectedAbsorbance

validBase = (d.extra2 ==1) & (d.uncorrectedAbsorbance > 0.1)
baseMean = np.mean(d.uncorrectedAbsorbance[validBase])
baseStdev = np.std(d.uncorrectedAbsorbance[validBase])

N = len(d.extra2)
nWindow = 10  #  Window size (HW) for baseline measurement
tWindow = 50   #  Time window for baseline measurement in ms
goodPoints = []
noBaseline = 0
minBase = 1000
maxBase = -1000
basePoints = []
for i, ext2 in enumerate(d.extra2):
    if ext2 == 0:
        win = slice(max(0,i-nWindow), min(N,i+nWindow+1))
        lwin = loss[win]
        twin = ts[win]
        select = (d.extra2[win] == 1) & (abs(ts[win] - ts[i]) < tWindow) & (d.uncorrectedAbsorbance[win] > 0.1)
        if sum(select) > 1:
            basePoints.append(sum(select))
            p = np.polyfit(twin[select], lwin[select], 1)
            loss[i] -= np.polyval(p, ts[i])
            loss[i] += baseMean
            goodPoints.append(i)
            if np.polyval(p, ts[i]) < minBase: minBase = np.polyval(p, ts[i])
            if np.polyval(p, ts[i]) > maxBase: maxBase = np.polyval(p, ts[i])
        else:
            loss[i] = 0.0
            noBaseline += 1
d.indexVector = np.asarray(goodPoints)
if len(basePoints) > 0:
    minBasePoints = amin(basePoints)
    maxBasePoints = amax(basePoints)
    meanBasePoints = mean(basePoints)
else:
    minBasePoints = 0
    maxBasePoints = 0
    meanBasePoints = 0
#print (minBase, maxBase)

d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.1,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=2000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]
r = None

tstart = time.clock()
if d["spectrumId"]==63 and d["ngroups"]>24:
    incomplete_spectrum = 0
    initialize_Baseline()
    r = anHCl[0](d,init,deps)          #  Fit wide spectrum with water, methane and HCl 
    ANALYSIS.append(r)
    hcl_shift = r["base",3]
    if (r[62,"peak"] < 4 and r[70,"peak"] < 4 and r[1002,2] < 0.02) or abs(r["base",3]) > 0.05:
        r = anHCl[1](d,init,deps)
        ANALYSIS.append(r)
    elif r[62,"peak"] < 4:
        r = anHCl[2](d,init,deps)
        ANALYSIS.append(r)        
    res = r["std_dev_res"]
    baseline_level = r["base",0]
    baseline_slope = r["base",1]
    hcl_adjust = r["base",3]
    peak62 = r[62,"peak"]
    str62 = r[62,"strength"]
    y62 = r[62,"y"]
    base70 = r[70,"base"]    
    peak70 = r[70,"peak"]  
    str70 = r[70,"strength"]
    r[70,"base"]
    y70 = r[70,"y"]
    ch4_ampl = r[1002,2] 

    h2o_conc_raw = h2o_slin*str62
    ch4_conc_raw = 100*ch4_ampl            
    hcl_conc_raw = hcl_lin*str70
    hcl_conc = hcl_conc_raw + ch4_hcl_lin*ch4_ampl + h2o_hcl_lin*peak62
    
    data_vector = d.fitData["loss"] - (r.model.funcList[0](r.model.xModifier(d.fitData["freq"]))+r.model.funcList[4](r.model.xModifier(d.fitData["freq"]))+r.model.funcList[5](r.model.xModifier(d.fitData["freq"])))
    model_vector = r.model.funcList[1](r.model.xModifier(d.fitData["freq"]))+r.model.funcList[2](r.model.xModifier(d.fitData["freq"]))+r.model.funcList[3](r.model.xModifier(d.fitData["freq"]))+r.model.funcList[6](r.model.xModifier(d.fitData["freq"]))
    normalized_data_vector = data_vector/sqrt(sum(data_vector**2))
    normalized_model_vector = model_vector/sqrt(sum(model_vector**2))
    spectrum_Score = sum(normalized_data_vector*normalized_model_vector)
    spectrum_Score = -1*log10(1-spectrum_Score)    

    r = anHCl[3](d,init,deps)          #  Post-fit wide spectrum with water, methane, HCl and non-methane hydrocarbons (VOCs!)
    ANALYSIS.append(r)    
    PF_shift = r["base",3]
    PF_h2o_conc = h2o_slin*r[62,"strength"]
    PF_ch4_conc = 100*r[1002,2]
    PF_hcl_conc = hcl_lin*r[70,"strength"] + ch4_hcl_lin*r[1002,2] + h2o_hcl_lin*r[62,"peak"]
    PF_ch3oh_conc = 13*r[1003,2]
    PF_c2h4_conc = 100*r[1004,2]
    PF_res = r["std_dev_res"]
    
if d["spectrumId"]==63 and d["ngroups"]<25:
    incomplete_spectrum = 1
    r = anHCl[4](d,init,deps)
    ANALYSIS.append(r)
    
cal = (d.subschemeId & 4096) != 0
if any(cal):
    pzt_mean = mean(d.pztValue[cal])
    pzt_stdev = std(d.pztValue[cal])
    
if r != None:
    IgnoreThis = False
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]
    ignore_count = max(0, ignore_count - 1)
else:
    IgnoreThis = True

    
if (ignore_count ==0) and not IgnoreThis:   # and not bad_baseline:     
    RESULT = {"res":res,"baseline_level":baseline_level,"baseline_slope":baseline_slope,"base70":base70,
              "peak62":peak62,"str62":str62,"y62":y62,"peak70":peak70,"str70":str70,"y70":y70,"ch4_ampl":ch4_ampl,
              "hcl_shift":hcl_shift,"hcl_adjust":hcl_adjust,"hcl_conc_raw":hcl_conc_raw,"hcl_conc":hcl_conc,
              "h2o_conc_raw":h2o_conc_raw,"ch4_conc_raw":ch4_conc_raw,
              "ngroups":d["ngroups"],"numRDs":d["datapoints"],"interval":interval,
              "baseMean":1000*baseMean,"baseStdev":1000*baseStdev,"spectrum_Score":spectrum_Score,
              "noBaseline":noBaseline,"incomplete_spectrum":incomplete_spectrum,
              "minBasePoints":minBasePoints,"maxBasePoints":maxBasePoints,"meanBasePoints":meanBasePoints,
              "PF_shift":PF_shift,"PF_h2o_conc":PF_h2o_conc,"PF_ch4_conc":PF_ch4_conc,"PF_hcl_conc":PF_hcl_conc,
              "PF_ch3oh_conc":PF_ch3oh_conc,"PF_c2h4_conc":PF_c2h4_conc,"PF_res":PF_res,              
              "pzt_mean":pzt_mean,"pzt_stdev":pzt_stdev}
    RESULT.update({"species":d["spectrumId"],"fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
