#  Fit script for N2O line at 6562.6 wavenumbers
#  Spectrum IDs taken from older JA analyzer;  added SID 48 for WLM flattening only

import os.path
import time
from numpy import *

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
    
# def initialize_Baseline():
    # init["base",1] = baseline_slope
    # init[1000,0] = A0
    # init[1000,1] = Nu0
    # init[1000,2] = Per0
    # init[1000,3] = Phi0
    # init[1001,0] = A1
    # init[1001,1] = Nu1
    # init[1001,2] = Per1
    # init[1001,3] = Phi1

if INIT:
    fname = os.path.join(BASEPATH,r"./JADS/JADS spectral library v1_1.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    #instrParams = getInstrParams(fname)
    
    optDict = eval("dict(%s)" % OPTION)
    
    anN2O = []
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/N2O_VC_FY_v1_1.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/N2O_only_v1_1.ini")))
    
#   Globals 
    shift_n2o = 0
    adjust_n2o = 0
    peak_1 = 0
    peak_2 = 0
    base_level = 0
    base_slope = 0
    peak_1a = 0
    base_1a = 0
    last_time = None
    pzt_ave = 0.0
    pzt_stdev = 0.0
    
# For offline analysis and output to file    
    #out = open("Fit_results.txt","w")
    #first_fit = 1

init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.10,maxVal=10.0)
d.wlmSetpointFilter(maxDev=0.0007,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
#d.calcGroupStats()
#d.calcSpectrumStats()

d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))

species = (d.subschemeId & 0x3FF)[0]
#print "SpectrumId", d["spectrumId"]

tstart = time.clock()
RESULT = {}
r = None

if (species == 47 and d["ngroups"] > 6):  #  fit N2O and CO2
    #initialize_Baseline()
    r = anN2O[0](d,init,deps)
    ANALYSIS.append(r)
    shift_n2o = r["base",3]
    peak_1 = r[1,"peak"]
    peak_2 = r[2,"peak"]
    base_level = r["base",0]
    base_slope = r["base",1]
    res = r["std_dev_res"]
    
    if peak_2 > 1 and abs(shift_n2o) < 0.05:
        adjust_n2o = shift_n2o
    else:
        adjust_n2o = 0.0
      
if (species == 45 or species == 47):  #  fit N2O only       
    r = anN2O[1](d,init,deps)
    ANALYSIS.append(r)
    peak_1a = r[1,"peak"]   
    base_1a = r[1,"base"]

if species == 48:  # Calibration scan
    pzt_ave = mean(d.pztValue)
    pzt_stdev =  std(d.pztValue)
    
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

#print DATA.filterHistory
    
if not IgnoreThis:    
    RESULT = {"peak_1":peak_1,"peak_1a":peak_1a,"peak_2":peak_2,"base_1a":base_1a,
            "shift_n2o":shift_n2o,"adjust_n2o":adjust_n2o,
            "Base_level":base_level,"base_slope":base_slope,
            "pzt_ave":pzt_ave,"pzt_stdev":pzt_stdev,
            "dataGroups":d["ngroups"],"dataPoints":d["datapoints"],
            "species":species,"interval":interval,"fit_time":fit_time
            }
    RESULT.update(d.sensorDict)

