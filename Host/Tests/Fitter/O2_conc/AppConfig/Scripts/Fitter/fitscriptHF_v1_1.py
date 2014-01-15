#  Fit script for HF based on the MADS fitter.
#  Translated from R:\crd\485_MA010_v1.0\Config\20100726\MADS10\GUI\MADSxx Release 1_12 2008 08 12.txt
#  by hoffnagle.  Begun 3 February 2011. 
#  2011 0512:  added code to ignore first 10 measurements while baseline average is equilibrating.  Also changed line
#                     centers in spectral library to match spectra acquired with MADS2015,  with spectroscopic WLM calibration.

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


tstart = time.time()

if INIT:
    fname = os.path.join(BASEPATH,r"./MADS/spectral library v2_1_AADS4_MA_20110601.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    #instrParams = getInstrParams(fname)
    
    anHF = []
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O peak #80 VC v1_0 20080512.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O peak #80 FC v1_0 20080512.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - HF doublet FC v1_0 20080512.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - HF doublet VC VY77 v1_0 20110531.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet VC VY v1_1.ini")))
    anHF.append(Analysis(os.path.join(BASEPATH,r"./MADS/H2O - O2 doublet FC v1_0 20080512.ini")))
    
    #  Globals to pass between spectral regions
    
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
    base77_ave = 800.0
    peak77_baseave = 800.0
    peak_79 = 0.0
    str_79 = 0.0
    base_79 = 0.0
    y_79 = 0.0
    shift_80 = 0.0
    peak_80 = 0.0
    str_80 = 0.0
    base_80 = 0.0
    y_80 = 0.0
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
    ntopper = tiptop = tipstd = tip_base = 0.0
    
    counter = -20
    ignore_count = 8
    
    pzt_mean = 0.0
    pzt_stdev = 0.0
    
    out = open("Fit_results.txt","w")
    first_fit = 1
   
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
#d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
#d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=3.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=3.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
#d.calcGroupStats()
#d.calcSpectrumStats()
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.time()
if d["spectrumId"]==60 and d["numgroups"]>8:
#   Fit water at 7824.07 wvn, VC
    r = anHF[0](d,init,deps)
    ANALYSIS.append(r)
    if r[80,"peak"]<2.5 or abs(r["base",3])>0.04:
        # fit with fixed center if peak is weak or highly shifted
        r = anHF[1](d,init,deps)
        ANALYSIS.append(r)
    shift_80 = r["base",3]
    peak_80 = r[80,"peak"]
    str_80 = r[80,"strength"]
    base_80 = r[80,"base"]
    y_80 = r[80,"y"]
    
    #  Fit water-HF doublet at 7823.8 with centration from previous step
    #init["base",3] = shift_80
    #init[77,"strength"] = 1.99*str_80
    r = anHF[2](d,init,deps)
    ANALYSIS.append(r)
    if r[77,"peak"]>10:
        # fit with variable center and y if either H2O or HF peak is strong.
        r = anHF[3](d,init,deps)
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
    adjust_77 = shift_77
    peakvalue = peak_77+base_77
    base77_ave = initExpAverage(base77_ave,base_77,3,100,counter)
    peak77_baseave = peakvalue-base77_ave
    h2o_conc_60 = 0.2364*peak_80
    hf_ppbv = 0.2727*peak_77
    hf_ppbv_ave = 0.2727*peak77_baseave
    counter += 1
    
    f = d.waveNumber
    l = 1000*d.uncorrectedAbsorbance

    topper = (f >= 7823.845) & (f <= 7823.855)
    top_loss = l[topper]
    ntopper = len(l[topper])
    if ntopper > 0:
        good_topper = outlierFilter(top_loss,3)
        tiptop = mean(top_loss[good_topper])
        tipstd = std(top_loss[good_topper])
        ntopper = len(top_loss[good_topper])
        tip_base = tiptop - base_77
    else:
        tiptop = tipstd = tip_base = 0.0
    
if d["spectrumId"]==61 and d["numgroups"]>9:
#   Wide range fit with VC 
    r = anHF[4](d,init,deps)
    ANALYSIS.append(r)
    if (r[81,"peak"]<10 and r[82,"peak"]<10) or abs(r["base",3])>0.04:
        # Repeat with FC if both peaks weak or shift large
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
    o2_conc = 0.07422*peak_81
    h2o_conc_61 = 0.04*peak_82
    
    adjust_81 = shift_81
 
cal = (d.subschemeId & 4096) != 0
if any(cal):
    pzt_mean = mean(d.pztValue[cal])
    pzt_stdev = std(d.pztValue[cal])    

ignore_count = max(0,ignore_count-1)
if (ignore_count == 0):      
    RESULT = {"base0":base0,"base1":base1,"base77_ave":base77_ave,"y_77":y_77,"y_79":y_79,
          "peak_77":peak_77,"str_77":str_77,"base_77":base_77,"shift_77":shift_77,
          "peak_79":peak_79,"str_79":str_79,"base_79":base_79,"adjust_77":adjust_77,
          "peak_80":peak_80,"str_80":str_80,"base_80":base_80,"shift_80":shift_80,
          "peak_81":peak_81,"str_81":str_81,"base_81":base_81,"shift_81":shift_81,
          "adjust_81":adjust_81,"peak_82":peak_82,"str_82":str_82,"base_82":base_82,
          "h2o_conc_60":h2o_conc_60,"h2o_conc_61":h2o_conc_61,"o2_conc":o2_conc,
          "hf_ppbv":hf_ppbv,"hf_ppbv_ave":hf_ppbv_ave,
          "ntopper":ntopper,"tiptop":tiptop,"tipstd":tipstd,"tip_base":tip_base,
          "numgroups":d["numgroups"],"numRDs":d["datapoints"],          
          "pzt_mean":pzt_mean,"pzt_stdev":pzt_stdev}
    RESULT.update({"species":d["spectrumId"],"fittime":time.time()-tstart,
               "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
               "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
    #RESULT.update(d.selectGroupStats([("base_high",7823.91),("hf_peak",7823.85),("O2_peak",7822.9835),("O2_flank",7823.005)]))
    #RESULT.update(d.getSpectrumStats())
    if first_fit:
        keys = sorted([k for k in RESULT])
        print>>out," ".join(keys)
        first_fit = 0
    print>>out," ".join(["%s" % RESULT[k] for k in keys])
else:
    RESULT = {}