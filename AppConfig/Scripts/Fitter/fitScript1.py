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
    fname = os.path.join(BASEPATH,r"./CFBDS/spectral library v1_043_CFADS-1_0220.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFBDS/CADS-3 9_PNT VW VC VB F89 v1_1.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFBDS/CADS-3 9_PNT FW FC FB F89 v1_1.ini")))
    
    base0_avg = None
    co2_cen_avg = None
    co2_str_avg = 0
    co2_y_avg = None
    co2_peak_avg = None
    str89_avg = None
    avg_count = 1
    co2_shift = 0
    last_time = None
    ignore_count = 20
    
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.5)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMedians["waveNumber"],loss=1000*d.groupMedians["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]+140.0
T = d["cavitytemperature"]
species = (d.subschemeId & 0x3FF)[0]
#print "SpectrumId", d["spectrumId"]
init["base",0] = 800

tstart = time.clock()
RESULT = {}
if species==26 or species==514 or species==0:
    if True: # base0_avg == None or (avg_count % 5) == 1: 
        init[89,"scaled_strength"] = 2.0/P
        init[14,"scaled_y"] = 0.01357
        init[14,"scaled_z"] = 0.00442
        r = anCO2[0](d,init,deps)
        ANALYSIS.append(r)
        base = r["base",0]
        co2_y = r[14,"y"]
        str89 = r[89,"strength"]
        co2_cen = r[14,"center"]
    base0_avg = initExpAverage(base0_avg,base,500,100,avg_count)
    co2_y_avg = initExpAverage(co2_y_avg,co2_y,500,0.02,avg_count)
    str89_avg = initExpAverage(str89_avg,str89,100,0.2,avg_count)
    co2_cen_avg = initExpAverage(co2_cen_avg,co2_cen,500,0.0002,avg_count)
    # Preset to average values
    init["base",0] = base0_avg
    init[89,"scaled_strength"] = str89_avg/P
    init[14,"center"] = co2_cen_avg
    init[14,"scaled_y"] = co2_y_avg/P
    init[14,"scaled_z"] = 0.3287*co2_y_avg/P
    co2_shift = 6237.408 - co2_cen_avg
    # Fit using only strength as adjustable parameter
    r = anCO2[1](d,init,deps)
    ANALYSIS.append(r)
    co2_res = r["std_dev_res"]
    
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
        RESULT = {"co2_res":co2_res,
                "co2_conc":0.7052*r[14,"peak"],"co2_str":r[14,"strength"],"co2_y_raw":co2_y,"co2_y_avg":co2_y_avg,
                "str89":str89_avg,"co2_shift":co2_shift,"cavity_pressure":P,
                "cavity_temperature":T,"species":1,"co2_fit_time":fit_time,
                "co2_interval":interval}
    print "CO2 Fit time: %.3f" % fit_time 
