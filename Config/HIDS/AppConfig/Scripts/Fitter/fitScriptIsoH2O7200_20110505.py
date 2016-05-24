#  First fit script for isotopic water lines at 7200 wavenumbers
#  2011 0503:  Changed spectral library to 50 Torr, 80 C version
#  2011 0503:  Ugly nomenclaure is from the installation on 740-HBDS2171
#  2011 0504:  Added RD statistics for development.  Tweaked line params in library & fit ini, excise points at jct 18/16

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

if INIT:
    fname = os.path.join(BASEPATH,r"./isoH2O7000/spectral library v1_3.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_iH2O7200.ini")
    instrParams = getInstrParams(fname)
    
    optDict = eval("dict(%s)" % OPTION)
    
    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./isoH2O7000/Full_range_v1_4.ini")))
    
#   Globals for the isotopic H2O fit
    last_time = None
    pzt_ave = 0.0
    pzt_stdev = 0.0
    
#   Spectroscopic parameters

    center1 = spectrParams['peak1']['center']
    y1_nominal = 50*spectrParams['peak1']['y']
    y2_nominal = 50*spectrParams['peak2']['y']
    center3 = spectrParams['peak3']['center']
    y3_nominal = 50*spectrParams['peak3']['y']

#   Parameters used in the fits

    offset1 = instrParams['offset1']
    offset2 = instrParams['offset2']
    offset3 = instrParams['offset3']
    baseline_slope = instrParams['Baseline_slope']
    A0 = instrParams['Sine0_ampl']
    Nu0 = instrParams['Sine0_freq']
    Per0 = instrParams['Sine0_period']
    Phi0 = instrParams['Sine0_phase']
    A1 = instrParams['Sine1_ampl']
    Nu1 = instrParams['Sine1_freq']
    Per1 = instrParams['Sine1_period']
    Phi1 = instrParams['Sine1_phase']

init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.0007,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
#d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.calcGroupStats()
d.calcSpectrumStats()

d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))

species = (d.subschemeId & 0x3FF)[0]
#print "SpectrumId", d["spectrumId"]

tstart = time.clock()
RESULT = {}
r = None

if ((species == 123) or (species == 124) or (species == 0)) and (d["ngroups"] > 10):
    initialize_Baseline()
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    h2o_squish = r["base",4]
    h2o_y = r[2,"y"]
    o18_shift = h2o_shift-r[1,"center"]+center1
    hdo_shift = h2o_shift-r[3,"center"]+center3
    peak1 = r[1,"peak"]
    peak2 = r[2,"peak"]
    peak3 = r[3,"peak"]
    raw_18 = peak1/peak2
    raw_D = peak3/peak2
    str1 = r[1,"strength"]
    str2 = r[2,"strength"]
    str3 = r[3,"strength"]
    base1 = r[1,"base"]
    base2 = r[2,"base"]
    base3 = r[3,"base"]
    
    if peak2 > 4 and abs(h2o_shift) < 0.05 and abs(h2o_y-y2_nominal) < 0.25:
        h2o_adjust = h2o_shift
    else:
        h2o_adjust = 0.0

    if peak1 > 4 and abs(o18_shift) < 0.05 and abs(r[1,"y"]-y1_nominal) < 0.25:
        o18_adjust = o18_shift
    else:
        o18_adjust = 0.0
        
    if peak3 > 4 and abs(hdo_shift) < 0.05 and abs(r[3,"y"]-y3_nominal) < 0.25:
        hdo_adjust = hdo_shift
    else:
        hdo_adjust = 0.0
    
#   Spectroscopic adjustments
    peak1_offset = peak1-offset1
    peak2_offset = peak2-offset2
    peak3_offset = peak3-offset3
    h2o_ppm = 7.248*peak2_offset
    
# elif d["spectrumId"] == 121:  # Calibration scan
#     pzt_ave = mean(d.pztValue)
#     pzt_stdev =  std(d.pztValue) 

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
    RESULT = {"peak1":peak1,"peak2":peak2,"peak3":peak3,"h2o_y":h2o_y,
            "peak1_offset":peak1_offset,"peak2_offset":peak2_offset,
            "peak3_offset":peak3_offset,"h2o_ppm":h2o_ppm,
            "strength1":str1,"strength2":str2,"strength3":str3,
            "base1":base1,"base2":base2,"base3":base3,
            "h16oh_adjust":h2o_adjust,"h16oh_shift":h2o_shift,"h2o_squish":h2o_squish,
            "h18oh_adjust":o18_adjust,"h18oh_shift":o18_shift,
            "h16od_adjust":hdo_adjust,"h16od_shift":hdo_shift,
            "raw18":raw_18,"raw_D":raw_D,"dataGroups":d["ngroups"],
            "spectrum":species,"interval":interval,"fit_time":fit_time
            }
    RESULT.update(d.sensorDict)
    RESULT.update(d.selectGroupStats([("base_low",7199.85),("base_high",7200.25),("peak_18",7199.96046),("peak_16",7200.13384),("peak_D",7200.30261)]))
    RESULT.update(d.getSpectrumStats())