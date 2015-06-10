#  Fit script for acetylene based on the DFADS fitter.
#  Translated from R:\LV8_Development\rella\Releases\batch file inis\DFADS-02\2009 1229\Release D3.11 F0.72\Dv3_11 Fv0_72 2009 1228.txt
#  by hoffnagle.  Begun 1 February 2011.

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

def initialize_Baseline(sine_index):
    init[sine_index,0] = A0
    init[sine_index,1] = Nu0
    init[sine_index,2] = Per0
    init[sine_index,3] = Phi0
    init[sine_index+1,0] = A1
    init[sine_index+1,1] = Nu1
    init[sine_index+1,2] = Per1
    init[sine_index+1,3] = Phi1

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./DFADS/spectral library DFADS-xx_2009_1208.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anC2H2 = []
    anC2H2.append(Analysis(os.path.join(BASEPATH,r"./DFADS/DFADS-XX H2O_C2H2_NH3_H2S vB 20091207.ini")))
    anC2H2.append(Analysis(os.path.join(BASEPATH,r"./DFADS/DFADS-XX H2O_C2H2_NH3_H2S vB FC FY 20091218.ini")))
    anC2H2.append(Analysis(os.path.join(BASEPATH,r"./DFADS/DFADS-XX H2O_C2H2_NH3_H2S vC C2H2 only 20091228.ini")))
    anC2H2.append(Analysis(os.path.join(BASEPATH,r"./DFADS/DFADS-XX H2O_C2H2_NH3_H2S vC C2H2 only vNH3 20091228.ini")))

    #  Import instrument specific baseline constants

    baseline_level = instrParams['Baseline_level']
    baseline_slope = instrParams['Baseline_slope']
    A0 = instrParams['Sine0_ampl']
    Nu0 = instrParams['Sine0_freq']
    Per0 = instrParams['Sine0_period']
    Phi0 = instrParams['Sine0_phase']
    A1 = instrParams['Sine1_ampl']
    Nu1 = instrParams['Sine1_freq']
    Per1 = instrParams['Sine1_period']
    Phi1 = instrParams['Sine1_phase']

    #  Globals to pass between spectral regions

    base0 = 0.0
    base1 = 0.0
    adjust_94 = 0.0
    shift_94 = 0.0
    peak_94 = 0.0
    base_94 = 0.0
    baseave = baseline_level
    y_94 = 0.0
    h2o_yeff = 0.0
    h2o_yeff_ave = 1.0
    base0_ave = baseline_level
    res_a = 0.0
    ampl_h2o = 0.0
    ampl_nh3 = 0.0
    ampl_h2s = 0.0
    h2o_conc = 0.0
    nh3_conc = 0.0
    nh3_conc_var = 0.0
    h2s_conc = 0.0
    c2h2_conc = 0.0
    c2h2_baseave_conc = 0.0
    counter = -20

    pzt_mean = 0.0
    pzt_stdev = 0.0

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
#d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=4.5)
d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.clock()
if d["spectrumId"]==200 and d["ngroups"]>4:
#   Fit acetylene, ammonia, H2S, and water lines with adjustable center and y
    initialize_Baseline(1003)
    r = anC2H2[0](d,init,deps)
    ANALYSIS.append(r)
    if (abs(r[1000,5]-0.95)>0.55) or (r[1000,2]<0.05 and abs(r["base",3])>0.03):
        # fit with fixed center and y if prefit does not look good
        r = anC2H2[1](d,init,deps)
        ANALYSIS.append(r)
    base0 = r["base",0]
    base1 = r["base",1]
    shift_94 = r["base",3]
    peak_94 = r[94,"peak"]
    base_94 = r[94,"base"]
    y_94 = r[94,"y"]
    h2o_yeff = r[1000,5]
    h2o_yeff_ave = initExpAverage(h2o_yeff_ave,h2o_yeff,3,2,counter)
    res_a = r["std_dev_res"]
    ampl_h2o = r[1000,2]
    ampl_nh3 = r[1001,2]
    ampl_h2s = r[1002,2]
    h2o_conc = 3.1*ampl_h2o
    nh3_conc = 50*ampl_nh3
    h2s_conc = 75*ampl_h2s
    c2h2_conc = 1.077*peak_94

    adjust_94 = shift_94
    counter += 1

if d["spectrumId"]==201 and d["ngroups"]>4:
#   Acetylene only in narrow range
    initialize_Baseline(1003)
    init["base",3] = shift_94
    init[1000,5] = h2o_yeff_ave
    init[1001,2] = ampl_nh3
    r = anC2H2[2](d,init,deps)
    ANALYSIS.append(r)
    base0 = r["base",0]
    peak_94 = r[94,"peak"]
    base_94 = r[94,"base"]
    c2h2_conc = 1.077*peak_94
    peakvalue_94 = peak_94+base_94
    baseave = initExpAverage(baseave,base_94,1.5,1000,counter)
    peak94_baseave = peakvalue_94 - baseave
    c2h2_baseave_conc = 1.077*peak94_baseave
    h2o_conc = 3.1*ampl_h2o
    nh3_conc = 50*ampl_nh3
    h2s_conc = 75*ampl_h2s

    init["base",3] = shift_94
    init[1000,5] = h2o_yeff_ave
    init[1001,2] = 0.0
    r = anC2H2[3](d,init,deps)
    ANALYSIS.append(r)
    nh3_conc_var = 50*ampl_nh3
    counter += 1

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = mean(d.pztValue[cal])
        pzt_stdev = std(d.pztValue[cal])

RESULT = {"res_a":res_a,"base0":base0,"base1":base1,"baseave":baseave,"y_94":y_94,
          "peak_94":peak_94,"base_94":base_94,"shift_94":shift_94,"adjust_94":adjust_94,
          "h2o_yeff":h2o_yeff,"h2o_yeff_ave":h2o_yeff_ave,"base0_ave":base0_ave,
          "ampl_h2o":ampl_h2o,"ampl_nh3":ampl_nh3,"ampl_h2s":ampl_h2s,
          "h2o_conc_precal_c2h2":h2o_conc,"nh3_conc":nh3_conc,"nh3_conc_var":nh3_conc_var,
          "h2s_conc":h2s_conc,"c2h2_conc_precal":c2h2_conc,"c2h2_baseave_conc":c2h2_baseave_conc,
          "ngroups":d["ngroups"],"numRDs":d["datapoints"],
          "pzt_mean":pzt_mean,"pzt_stdev":pzt_stdev}
RESULT.update({"species":d["spectrumId"],"fittime":time.clock()-tstart,
               "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
               "das_temp":dasTemp})
RESULT.update(d.sensorDict)
