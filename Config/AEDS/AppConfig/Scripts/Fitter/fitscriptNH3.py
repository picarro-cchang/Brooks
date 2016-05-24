#  Fit script for ammonia based on the AADS fitter, which models the ammonia lines with Galatry profiles
#  Translated from R:\LV8_Development\rella\Releases\batch file inis\AADS-20\2009 0713\Release AA0.214\AADS-20 Release AA0_214 20090713.txt
#  by hoffnagle.  Begun 26 October 2010.
#  Note that the Python core has not implemented the "quadlimit" function used in the fit definition; resolution remains open.
#  2011-04-28:  Replaced numgroups (deprecated) with ngroups.
#  2012-12-23:  Move pzt statistics to SID 2 (otherwise pointless)
#  2013-02-14:  Fixed bug in "badshot" logic that generated error messages when fit was bad
#  2013-05-30:  Fixed bug in baseline initialization:  slope was not initialized

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

def initialize_Baseline():
    init["base",1] = baseline_slope
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
    fname = os.path.join(BASEPATH,r"./NH3/spectral library v1_045_AADS12_E2 0219.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anNH3 = []
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/AADS-xx water + ammonia v1_1.ini")))
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/AADS-xx peak 11 v1_1.ini")))
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/AADS-xx peak 12 v1_1.ini")))
    anNH3.append(Analysis(os.path.join(BASEPATH,r"./NH3/big water #25 v2_0.ini")))

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
    cm_adjust = 0.0
    h2o_adjust = 0.0
    nh3_peak_11 = 0.0
    nh3_base_11 = 0.0
    nh3_slope_11 = 0.0
    nh3_conc_11 = 0.0
    nh3_peak_12 = 0.0
    nh3_base_12 = 0.0
    nh3_slope_12 = 0.0
    nh3_conc_12 = 0.0
    nh3_conc_ave = 0.0
    nh3_conc_smooth = 0.0

    pzt_mean = 0.0
    pzt_stdev = 0.0

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
#d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
#d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=200,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.clock()
badshot_nh3 = 0
if d["spectrumId"]==2 and d["ngroups"]>29:            #  spectrumId historically was 0
#   Fit ammonia, CO2, and water lines
    initialize_Baseline()
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

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = mean(d.pztValue[cal])
        pzt_stdev = std(d.pztValue[cal])

if (d["spectrumId"]==1 or d["spectrumId"]==4) and d["ngroups"]>18:
#   Ammonia region:  fit peaks 11 and 12 separately
    initialize_Baseline()
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
    else:
        badshot_nh3 = 1
    dbase = nh3_base_11 - last_base_11
    last_base_11 = nh3_base_11
    if abs(dbase) > 3:
        badshot_nh3 = 1

    initialize_Baseline()
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
    else:
        badshot_nh3 = 1
    dbase = nh3_base_12 - last_base_12
    last_base_12 = nh3_base_12
    if abs(dbase) > 3:
        badshot_nh3 = 1

    if badshot_nh3 == 0:
        nh3_conc_ave = 0.5*(nh3_conc_11 + nh3_conc_12)
        nh3_conc_smooth = initExpAverage(nh3_conc_smooth, nh3_conc_ave, 50, 1, counter)
        counter += 1

if d["spectrumId"]==3:
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

if badshot_nh3 == 0:
    RESULT = {"res_a":res_a,"res_11":res_11,"res_12":res_12,
              "peak11a":peak11a,"peak15":peak15,"peak17":peak17,"badshot_h2o":badshot_h2o,
              "h2o_conc":h2o_conc,"co2_conc":co2_conc,"shift_a":shift_a,"cm_adjust":cm_adjust,
              "peak25":peak25,"shift25":shift25,"h2o_adjust":h2o_adjust,
              "nh3_peak_11":nh3_peak_11,"nh3_base_11":nh3_base_11,"nh3_slope_11":nh3_slope_11,
              "nh3_base_12":nh3_base_12,"nh3_peak_12":nh3_peak_12,"nh3_slope_12":nh3_slope_12,
              "nh3_conc_ave":nh3_conc_ave,"nh3_conc_smooth":nh3_conc_smooth,
              "ngroups":d["ngroups"],"numRDs":d["datapoints"],
              "pzt_mean":pzt_mean,"pzt_stdev":pzt_stdev}
    RESULT.update({"species":d["spectrumId"],"fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
