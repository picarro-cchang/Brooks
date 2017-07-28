#  Fit script for ammonia based on the AADS fitter, which models the ammonia lines with Galatry profiles
#  Translated from R:\LV8_Development\rella\Releases\batch file inis\AADS-20\2009 0713\Release AA0.214\AADS-20 Release AA0_214 20090713.txt
#  by hoffnagle.  Begun 26 October 2010.  
#  Note that the Python core has not implemented the "quadlimit" function used in the fit definition; resolution remains open.
#  2011-04-28:  Replaced numgroups (deprecated) with ngroups.
#  2012-12-23:  Move pzt statistics to SID 2 (otherwise pointless)
#  2013-02-14:  Fixed bug in "badshot" logic that generated error messages when fit was bad
#  2013-05-30:  Fixed bug in baseline initialization:  slope was not initialized
#  2015-02-20:  New application to trace ammonia in pure CO2

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
    fname = os.path.join(BASEPATH,r"./NH3/spectral library for CO2 v1_0.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_forCO2.ini")
    instrParams = getInstrParams(fname)
    
    anNH3 = []
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/NH3+pureCO2 FY v1_1.ini")))
    
    #  Import instrument specific baseline constants
    
    baseline_slope = instrParams['Baseline_slope']
    A0 = instrParams['Sine0_ampl']
    Nu0 = instrParams['Sine0_freq']
    Per0 = instrParams['Sine0_period']
    Phi0 = instrParams['Sine0_phase']
    A1 = instrParams['Sine1_ampl']
    Nu1 = instrParams['Sine1_freq']
    Per1 = instrParams['Sine1_period']
    Phi1 = instrParams['Sine1_phase']
    
    nh3_lin = instrParams['NH3_linear']
    co2_lin = instrParams['CO2_linear']
    co2_nh3_lin = instrParams['NH3_to_CO2_linear']
    
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

tstart = time.clock()
if d["spectrumId"]==4 and d["ngroups"]>18:
    initialize_Baseline()
    init[20,"strength"] = 75.7      #  CO2 peak 20 from finescans of pure CO2
    r = anNH3[0](d,init,deps)
    ANALYSIS.append(r)
    res = r["std_dev_res"]
    baseline_level = r["base",0]
    baseline_slope = r["base",1]
    baseline_curvature = r["base",2]
    baseline_at_center = baseline_level-0.17*baseline_slope+0.0289*baseline_curvature
    shift = r["base",3]
    peak11 = r[11,"peak"]
    str11 = r[11,"strength"]
    y11 = r[11,"y"]    
    peak12 = r[12,"peak"]  
    str12 = r[12,"strength"]
    peak20 = r[20,"peak"]
    str20 = r[20,"strength"]    
 
    nh3_conc_ave = nh3_lin*0.5*(peak11+peak12)
    co2_conc_raw = co2_lin*peak20
    co2_conc = co2_conc_raw + co2_nh3_lin*nh3_conc_ave

    if abs(co2_conc - 1.0) < 0.1 and abs(shift) < 0.05:
        cm_adjust = shift
    else:
        cm_adjust = 0.0
        
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
    else:
        IgnoreThis = True

    if not IgnoreThis:     
        RESULT = {"res":res,"baseline_level":baseline_level,"baseline_slope":baseline_slope,"baseline_curvature":baseline_curvature,
                  "peak11":peak11,"str11":str11,"y11":y11,"peak12":peak12,"str12":str12,"peak20":peak20,"str20":str20,
                  "co2_conc":co2_conc,"co2_conc_raw":co2_conc_raw,"shift":shift,"cm_adjust":cm_adjust,"nh3_conc_ave":nh3_conc_ave,
                  "ngroups":d["ngroups"],"numRDs":d["datapoints"],"baseline_at_center":baseline_at_center,"interval":interval,          
                  "pzt_mean":pzt_mean,"pzt_stdev":pzt_stdev}
        RESULT.update({"species":d["spectrumId"],"fittime":time.clock()-tstart,
                       "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                       "das_temp":dasTemp})
        RESULT.update(d.sensorDict)