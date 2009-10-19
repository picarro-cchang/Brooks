from numpy import sqrt
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

if INIT:
    fname = os.path.join(BASEPATH,r"./Alpha/spectral library alpha.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anAlpha = []
    anAlpha.append(Analysis(os.path.join(BASEPATH,r"./Alpha/AlphaAnalysis.ini")))
    
    base0_avg = None
    alpha_y_avg = None
    alpha_str_avg = None
    alpha_cen_avg = None
    avg_count = 1
    alpha_shift = 0
    last_time = None
    ignore_count = 2
    
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.5)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
species = (d.subschemeId & 0x3FF)[0]
#print "SpectrumId", d["spectrumId"]
init["base",0] = 800

tstart = time.clock()
RESULT = {}
if species==20:
    if True: # base0_avg == None or (avg_count % 5) == 1: 
        init[1,"scaled_strength"] = 10
        init[1,"scaled_y"] = 0.01
        init[1,"scaled_z"] = 0.003
        r = anAlpha[0](d,init,deps)
        ANALYSIS.append(r)
        base = r["base",0]
        alpha_y = r[1,"y"]
        alpha_str = r[1,"strength"]
        alpha_cen = r[1,"center"]
    base0_avg = initExpAverage(base0_avg,base,500,100,avg_count)
    alpha_y_avg = initExpAverage(alpha_y_avg,alpha_y,500,0.02,avg_count)
    alpha_str_avg = initExpAverage(alpha_str_avg,alpha_str,100,0.2,avg_count)
    alpha_cen_avg = initExpAverage(alpha_cen_avg,alpha_cen,500,0.0002,avg_count)
    alpha_res = r["std_dev_res"]
    
    now = time.clock()
    fit_time = now-tstart
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]
    avg_count += 1
    ignore_count = max(0,ignore_count-1)
    if ignore_count == 0:
        RESULT = {"alpha_res":alpha_res,
                  "apha_peak":r[1,"peak"],"alpha_str":alpha_str,"alpha_y":alpha_y,
                  "alpha_y_avg":alpha_y_avg,
                  "alpha_str_avg":alpha_str_avg,
                  "alpha_cen_avg":alpha_cen_avg,
                  "cavity_pressure":P,
                  "cavity_temperature":T,
                  "species":1,"fit_time":fit_time,
                  "interval":interval}
    print "Fit time: %.3f" % fit_time 
