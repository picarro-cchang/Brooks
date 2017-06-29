#  Fit script for H2S based on the BCDS fitter.
#  Translated from R:\LV8_Development\rella\Releases\batch file inis\BFADS-2\2011 0217\Release 1.01 0.72\BCv1_01 Fv0_72 2011 0217.txt
#  by hoffnagle.  Begun 3 June 2011.
#  2012 0510:  Second instrument.  Removed 3rd sinusoid from baseline (kluge for 1st analyzer only)
#  2017 0320:  Small change to water splines to remove trace of H2S contamination causing cross-talk (jah)

from numpy import *
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

def initialize_Baseline():
    init["base",0] = baseline_level
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
    fname = os.path.join(BASEPATH,r"./BXDS/spectral library BXDS-xx_v2.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    
    anH2S = []
    anH2S.append(Analysis(os.path.join(BASEPATH,r"./BXDS/BXDS-xx Spline VC NH3 v1_1.ini")))
    anH2S.append(Analysis(os.path.join(BASEPATH,r"./BXDS/BXDS-xx Spline FC NH3 v1_1.ini")))
    anH2S.append(Analysis(os.path.join(BASEPATH,r"./BXDS/BXDS-xx Spline 9-point NH3 v1_1.ini")))
    
    #  Globals 
    
    splinebase_ave = 800.0
    counter = -20
    ignore_count = 8
    
    pzt_mean = 0.0
    pzt_stdev = 0.0
    
    baseline_level = instrParams['H2S_Baseline_level']
    baseline_slope = instrParams['H2S_Baseline_slope']
    A0 = instrParams['H2S_Sine0_ampl']
    Nu0 = instrParams['H2S_Sine0_freq']
    Per0 = instrParams['H2S_Sine0_period']
    Phi0 = instrParams['H2S_Sine0_phase']
    A1 = instrParams['H2S_Sine1_ampl']
    Nu1 = instrParams['H2S_Sine1_freq']
    Per1 = instrParams['H2S_Sine1_period']
    Phi1 = instrParams['H2S_Sine1_phase']
    
    #out = open("Fit_results.txt","w")
    #first_fit = 1
   
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
#d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=2.5)
d.wlmSetpointFilter(maxDev=0.004,sigmaThreshold=2.5)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
#d.calcGroupStats()
#d.calcSpectrumStats()
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.clock()
if (d["spectrumId"] in [125,126]) and (d["ngroups"]>5):
    initialize_Baseline()
    r = anH2S[0](d,init,deps)
    ANALYSIS.append(r)
    if (abs(r["base",3])<0.05 and (r[1003,2]>0.005 or r[1004,2]>0.008 or r[1005,2]>0.1)):
        h2s_adjust = r["base",3]
    else:
        init["base",3] = 0.0
        h2s_adjust = 0.0
        r = anH2S[1](d,init,deps)
        ANALYSIS.append(r)
    h2s_shift = r["base",3]
    h2s_amp = r[1003,2]
    y_eff = r[1003,5]
    h2s_peak = r[1003,"peak"]    #Check to make sure frequency is specified correctly!!
    h2s_amp_ppbv = 60000*h2s_amp
    h2s_peak_ppbv = 79.575*h2s_peak
    co2_amp = r[1004,2]
    co2_ppmv = 30000*co2_amp
    h2o_amp = r[1005,2]
    h2o_conc = 1.7*h2o_amp
    nh3_amp = r[1006,2]
    nh3_ppmv = 5000*nh3_amp
    base0 = r["base",0]
    v_rms_residual = r["std_dev_res"]
    if h2s_peak_ppbv>300 or co2_ppmv>300 or h2o_conc>0.2:
        ok = 1
    else:
        ok = 0
    
    init[1004,2] = co2_amp  
    init[1005,2] = h2o_amp
    init[1006,2] = nh3_amp    
    r = anH2S[2](d,init,deps)
    ANALYSIS.append(r)
    
    f_h2s_amp = r[1003,2]
    f_h2s_peak = r[1003,"peak"]
    f_h2s_amp_ppbv = 60000*f_h2s_amp
    f_h2s_peak_ppbv = 79.575*f_h2s_peak
    f_base0 = r["base",0]
    f_rms_residual = r["std_dev_res"]
    
    f = d.waveNumber
    l = 1000*d.uncorrectedAbsorbance

    topper = (f >= 6350.99) & (f <= 6351.01)
    top_loss = l[topper]
    ntopper = len(l[topper])
    if ntopper > 0:
        good_topper = outlierFilter(top_loss,3)
        tiptop = mean(top_loss[good_topper])
        tipstd = std(top_loss[good_topper])
        ntopper = len(top_loss[good_topper])
    else:
        tiptop = tipstd = 0.0
    
    splinebase = tiptop - f_h2s_peak
    splinebase_ave = initExpAverage(splinebase_ave,splinebase,4,100,counter)
    counter += 1
    f_h2s_baseave = tiptop - splinebase_ave
    f_h2s_ppbv_baseave = 79.575*f_h2s_baseave
    diffbase = f_base0 - base0
    diffppbv = f_h2s_peak_ppbv - h2s_peak_ppbv
 
    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = mean(d.pztValue[cal])
        pzt_stdev = std(d.pztValue[cal])    

    ignore_count = max(0,ignore_count-1)
    if (ignore_count == 0):      
        RESULT = {"base0":base0,"h2s_shift":h2s_shift,"h2s_adjust":h2s_adjust,"y_eff":y_eff,
              "h2s_amp":h2s_amp,"h2s_peak":h2s_peak,"co2_amp":co2_amp,"h2o_amp":h2o_amp,"nh3_amp":nh3_amp,
              "h2s_amp_ppbv":h2s_amp_ppbv,"h2s_peak_ppbv":h2s_peak_ppbv,"co2_ppmv":co2_ppmv,
              "h2o_from_h2s":h2o_conc,"nh3_ppmv":nh3_ppmv,"f_base0":f_base0,
              "f_h2s_amp":f_h2s_amp,"f_h2s_peak":f_h2s_peak,"f_h2s_amp_ppbv":f_h2s_amp_ppbv,
              "f_h2s_peak_ppbv":f_h2s_peak_ppbv,"splinebase":splinebase,"splinebase_ave":splinebase_ave,
              "f_h2s_baseave":f_h2s_baseave,"f_h2s_ppbv_baseave":f_h2s_ppbv_baseave,
              "diffbase":diffbase,"diffppbv":diffppbv,"f_rms_residual":f_rms_residual,
              "ntopper":ntopper,"tiptop":tiptop,"tipstd":tipstd,"v_rms_residual":v_rms_residual,
              "numgroups":d["ngroups"],"numRDs":d["datapoints"],          
              "pzt_mean":pzt_mean,"pzt_stdev":pzt_stdev}
        RESULT.update({"species":1,"fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
        RESULT.update(d.sensorDict)
        #RESULT.update(d.selectGroupStats([("base_high",7823.91),("hf_peak",7823.85),("O2_peak",7822.9835),("O2_flank",7823.005)]))
        #RESULT.update(d.getSpectrumStats())
        #if first_fit:
        #    keys = sorted([k for k in RESULT])
        #    print>>out," ".join(keys)
        #    first_fit = 0
        #print>>out," ".join(["%s" % RESULT[k] for k in keys])
    else:
        RESULT = {}