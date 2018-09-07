#  Fit script HCl using the 5739.26 wavenumber line, with water and methane as reference lines
#  2015-07-23:  Started
#  2015-08-14:  Added second spectrum ID with stronger water line for WLM offset
#  2015-09-01:  Ignore first few points for H2O to settle
#  2016-04-04:  Changed scheme trying to smooth Allan variance
#  2016-04-06:  Removed reporting made superfluous by new scheme
#  2016-05-27:  Added extra testing for baseline jumps to exclude bogus measurements when hydrocarbon solvents are used in fab

from numpy import any, mean, std, sqrt
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
    fname = os.path.join(BASEPATH,r"./HCl/spectral library HCl v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_HCl.ini")
    instrParams = getInstrParams(fname)
    
    anHCl = []
    anHCl.append(Analysis(os.path.join(BASEPATH,r"./HCl/HCl+H2O VC VY v1_1.ini")))
    anHCl.append(Analysis(os.path.join(BASEPATH,r"./HCl/HCl+H2O FC FY v1_1.ini")))
    anHCl.append(Analysis(os.path.join(BASEPATH,r"./HCl/HCl+H2O VC FY v1_1.ini")))
    
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
    baseline_level = baseline_level
    baseline_slope = baseline_slope
    hcl_adjust = 0.0
    peak62 = 0.0
    str62 = 0.0
    y62 = 0.698
    base70 = baseline_level    
    peak70 = 0.0
    str70 = 0.0
    y70 = 0.754
    ch4_ampl = 0.0
    
    hcl_conc_raw = 0.0
    hcl_conc = 0.0
    h2o_conc_raw = 0.0
    ch4_conc_raw = 0.0
    
    pzt_mean = 32768
    pzt_stdev = 0
    
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
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=200,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]
r = None

tstart = time.clock()
if d["spectrumId"]==63 and d["ngroups"]>25:
    initialize_Baseline()
    r = anHCl[0](d,init,deps)          #  Fit wide spectrum with water, methane and HCl 
    ANALYSIS.append(r)
    hcl_shift = r["base",3]
    if (r[62,"peak"] < 4 and r[70,"peak"] < 4 and r[1002,2] < 0.004) or abs(r["base",3]) > 0.05:
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
    ch4_conc_raw = 500*ch4_ampl            
    hcl_conc_raw = hcl_lin*str70
    hcl_conc = hcl_conc_raw + ch4_hcl_lin*ch4_ampl + h2o_hcl_lin*peak62
    
    f = d.waveNumber
    l = 1000*d.uncorrectedAbsorbance
    
    base1 = (f >= 5739.170) & (f <= 5739.190) & (d.extra1 == 0)
    base1_loss = l[base1]
    base2 = (f >= 5739.170) & (f <= 5739.190) & (d.extra1 == 1)
    base2_loss = l[base2]
    bad_baseline = 0
    if len(base1_loss)*len(base2_loss) == 0:
        bad_baseline = 1
    delta_loss = mean(base2_loss)-mean(base1_loss)
    if abs(delta_loss) > 1:
        bad_baseline = 1
    
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

    
if (ignore_count ==0) and not IgnoreThis and not bad_baseline:     
    RESULT = {"res":res,"baseline_level":baseline_level,"baseline_slope":baseline_slope,"base70":base70,
              "peak62":peak62,"str62":str62,"y62":y62,"peak70":peak70,"str70":str70,"y70":y70,"ch4_ampl":ch4_ampl,
              "hcl_shift":hcl_shift,"hcl_adjust":hcl_adjust,"hcl_conc_raw":hcl_conc_raw,"hcl_conc":hcl_conc,
              "h2o_conc_raw":h2o_conc_raw,"ch4_conc_raw":ch4_conc_raw,"delta_loss":delta_loss,
              "ngroups":d["ngroups"],"numRDs":d["datapoints"],"interval":interval,          
              "pzt_mean":pzt_mean,"pzt_stdev":pzt_stdev}
    RESULT.update({"species":d["spectrumId"],"fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)