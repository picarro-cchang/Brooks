#  Fit script for HF at 7823 wvn with LCT data acquisition
#  2016 0707:  started from most recent MADS fitter
#  2016 1110:  removed redundant code defining ntopper
#  2016 1118:  modified water concentration calibration based on comparison with CFADS done 17. Nov. 2016
#  2017 0109:  major change to frequency assignment and pzt feedback to deal with switching between room air and dry nitrogen
#              also changed fit definition ini for H2O-O2 VC to make it less prone to misidentify water as oxygen
#  2017-09-05:  added reporting of tuner statistics for LCT diagnosis

from numpy import any, mean, std, sqrt, argmin, round_
import os.path
import time

# Need to initialize as there is a fall through case where the
# variable can never be declared and causes an exception.
# RSF
pzt1_adjust = 0

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
    fname = os.path.join(BASEPATH,r"./MADS/spectral library MADSxx_v2_4.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_lct.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']
    
    anHF = []
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - HF doublet FC v1_0 20080512.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - HF doublet VC v1_0 20080512.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - HF doublet FC v1_0 20080512.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet VC v2_1.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet FC v1_1 20160523.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet VC v2_1.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet FC v1_1 20160523.ini")))

    
    #  Baseline parameters
    A0 = instrParams['HF_Sine0_ampl']
    Nu0 = instrParams['HF_Sine0_freq']
    Per0 = instrParams['HF_Sine0_period']
    Phi0 = instrParams['HF_Sine0_phase']
    A1 = instrParams['HF_Sine1_ampl']
    Nu1 = instrParams['HF_Sine1_freq']
    Per1 = instrParams['HF_Sine1_period']
    Phi1 = instrParams['HF_Sine1_phase']
    
    #  Globals to pass between spectral regions
    
    goodLCT = 0
    i0 = 5
    f0 = 7823.84945
    sigma0 = 0.0
    adjust_81 = 0.0
    base0 = 0.0
    base1 = 0.0
    adjust_77=0.0
    shift_77 = 0.0
    peak_77 = 0.0
    str_77 = 0.0
    base_77 = 0.0
    y_77 = 0.0
    shift_77 = 0.0
    base77_ave = instrParams['HF_Baseline_level']
    peak77_baseave = 0.0
    peak_79 = 0.0
    str_79 = 0.0
    base_79 = 0.0
    y_79 = 0.0
    shift_81 = 0.0
    peak_81 = 0.0
    str_81 = 0.0
    base_81 = 0.0
    y_81 = 0.0
    peak_82 = 0.0
    str_82 = 0.0
    base_82 = 0.0
    y_82 = 0.0
    h2o_conc_60 = 0.0
    h2o_conc_61 = 0.0
    o2_conc = 0.0
    hf_ppbv = 0.0
    hf_ppbv_ave = 0.0
    hf_res = 0.0
    o2_res = 0.0
    tuner60mean = 32768
    tuner60stdev = 0
    tuner61mean = 32768
    tuner61stdev = 0
    
    counter = -20
    ignore_count = 8
    
    last_time = None
    
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
#d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=4.5)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
tunerStdev = std(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.clock()
RESULT = {}
r = None
if d["spectrumId"]==60 and d["ngroups"]>8:
    #  Fit water-HF doublet at 7823.8
    r = anHF[0](d,init,deps)
    ANALYSIS.append(r)
    if r[77,"peak"]>10:
        # fit with variable center and y if either H2O or HF peak is strong.
        r = anHF[1](d,init,deps)
        ANALYSIS.append(r)
    tuner60mean = tunerMean
    tuner60stdev = tunerStdev    
    if goodLCT:
        i0 = argmin(abs(d.fitData["freq"] - 7823.84945))
        f0 = d.fitData["freq"][i0]
        sigma0 = d.groupStdDevs["waveNumber"][i0]
        #print "%2d %8.5f %8.5f" % (i0, f0 - 7823.84945, sigma0)
        d.waveNumber = f0 + fsr*round_((d.waveNumber - f0)/fsr)
        d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
        d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
        d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes)) 
        
        r = anHF[2](d,init,deps)   #  Cavity-based frequency scale comes from O2 only
        ANALYSIS.append(r)
        
    peak_77 = r[77,"peak"]
    str_77 = r[77,"strength"]
    y_77 = r[77,"y"]
    base_77 = r[77,"base"]
    peak_79 = r[79,"peak"]
    str_79 = r[79,"strength"]
    y_79 = r[79,"y"]
    base_79 = r[79,"base"]
    base0 = r["base",0]
    base1 = r["base",1]
    shift_77 = r["base",3]
    peakvalue = peak_77+base_77
    base77_ave = initExpAverage(base77_ave,base_77,3,100,counter)
    peak77_baseave = peakvalue-base77_ave
    hf_ppbv = 0.2041*peak_77
    hf_ppbv_ave = 0.2041*peak77_baseave
    counter += 1
    hf_res = r["std_dev_res"]
    
if d["spectrumId"]==61 and d["ngroups"]>9:
    #  Fit water-O2 doublet at 7822.95
    initialize_Baseline()
    r = anHF[3](d,init,deps)
    ANALYSIS.append(r)
    shift_81 = r["base",3]
    if (r[81,"peak"]<10 and r[82,"peak"]<10) or abs(r["base",3])>0.04:
        # Repeat with FC if both peaks weak or shift large
        r = anHF[4](d,init,deps)
        ANALYSIS.append(r)
    adjust_81 = r["base",3]
    goodLCT = abs(adjust_81)<0.005 and sigma0 < 0.005
    tuner61mean = tunerMean
    tuner61stdev = tunerStdev
    if goodLCT:
        d.waveNumber = f0 + fsr*round_((d.waveNumber - f0)/fsr)
        d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
        d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
        d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes)) 
        if r[81,"peak"]<10 and r[82,"peak"]<10:
            r = anHF[6](d,init,deps)
            ANALYSIS.append(r)
        else: 
            r = anHF[5](d,init,deps)
            ANALYSIS.append(r)
    
    base0 = r["base",0]
    base1 = r["base",1]
    shift_81 = r["base",3]
    peak_81 = r[81,"peak"]
    str_81 = r[81,"strength"]
    base_81 = r[81,"base"]
    y_81 = r[81,"y"]
    peak_82 = r[82,"peak"]
    str_82 = r[82,"strength"]
    base_82= r[82,"base"]
    y_82 = r[82,"y"]
    o2_conc = 0.04801*peak_81
    h2o_conc_61 = 0.025*peak_82
    o2_res = r["std_dev_res"]
    
    if goodLCT:
        pzt1_adjust = (7823.84945-f0)*pzt_per_fsr/fsr
    else:
        pzt1_adjust = 0.0
     
now = time.clock()
fit_time = now-tstart
if r != None:
    IgnoreThis = False
    if last_time != None:
        hf_interval = r["time"]-last_time
    else:
        hf_interval = 0
    if d["spectrumId"]==60:
        last_time = r["time"]    

ignore_count = max(0,ignore_count-1)
if (ignore_count == 0) and (not IgnoreThis):      
    RESULT = {"base0":base0,"base1":base1,"base77_ave":base77_ave,"y_77":y_77,"y_79":y_79,
          "peak_77":peak_77,"str_77":str_77,"base_77":base_77,"shift_77":shift_77,
          "peak_79":peak_79,"str_79":str_79,"base_79":base_79,"pzt1_adjust":pzt1_adjust,
          "peak_81":peak_81,"str_81":str_81,"base_81":base_81,"shift_81":shift_81,
          "adjust_81":adjust_81,"peak_82":peak_82,"str_82":str_82,"base_82":base_82,
          "h2o_conc_61":h2o_conc_61,"o2_conc":o2_conc,
          "hf_ppbv":hf_ppbv,"hf_ppbv_ave":hf_ppbv_ave,"hf_res":hf_res,"o2_res":o2_res,
          "ngroups":d["ngroups"],"numRDs":d["datapoints"],"fit_time":fit_time,"hf_interval":hf_interval,
          "tuner60mean":tuner60mean,"tuner60stdev":tuner60stdev,"tuner61mean":tuner61mean,"tuner61stdev":tuner61stdev,       
          "pzt_per_fsr":pzt_per_fsr,"goodLCT":goodLCT}
    RESULT.update({"species":d["spectrumId"],"fittime":time.clock()-tstart,
               "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
               "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
