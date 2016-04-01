import numpy 
import os.path
import time
from Host.Common.EventManagerProxy import Log

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
    return numpy.sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

if INIT:
    fname = os.path.join(BASEPATH,r"./isoCO2/CBDS-5 spectral library v20080627.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anC12O2 = []
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C12 only v1_0.ini")))
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C12 only v1_1.ini")))
    
    anC13O2 = []
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only dev v1_1.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/C13 only VC VY v1_0.ini")))
#    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/polynomial fit C13.ini")))

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/6250_4 water fitter v1_0.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./isoCO2/6250_4 water fitter FC v1_0.ini")))

    c12_base_ave = 894  # Set this to be close to the cavity baseline
    c13_base_ave = 894  # Set this to be close to the cavity baseline
    counter = -25
    lastgood_shift_87 = 0
    lastgood_strength_87 = 0
    lastgood_y_87 = 0.0136
    lastgood_z_87 = 0.00438
    lastgood_y_88 = 0.01515
    lastgood_z_88 = 0.00488
    c13_offset = 0.0    # This is added to the C13 peak. Units are ppb/cm    

    y_87 = 0.0
    z_87 = 0.0
    peak_87 = 0.0
    shift_87 = 0.0
    str_87 = 0.0
    base_87 = 0.0
    y_88 = 0.0
    z_88 = 0.0
    peak_88 = 0.0
    shift_88 = 0.0
    str_88 = 0.0
    y_91 = 0.0
    z_91 = 0.0
    shift_91 = 0.0
    peak_91 = 0.0
    base_88 = 0.0
    
    adjust_87 = 0.0
    adjust_88 = 0.0
    adjust_91 = 0.0
    initial_galratio = 0.0
    baseave_galratio = 0.0
    polybaseave_galratio = 0.0
    peak88_baseave = 0.0
    peak87_baseave = 0.0
    polypeak88_baseave = 0.0
        
    ignore_count = 5
    last_time = None

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.8)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/numpy.sqrt(d.groupSizes))
#pass### "Freq",d.fitData["freq"]
#pass### "Loss",d.fitData["loss"]
#pass### "SDev",d.fitData["sdev"]
#pass### d.sensorDict
P = d["cavitypressure"]
T = d["cavitytemperature"]
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]
etalonTemp = d.sensorDict["EtalonTemp"]
tstart = time.clock()
RESULT = {}
r = None

if d["spectrumId"] == 105:  # C12O2
    init[87,"scaled_y"] = 0.0136
    r = anC12O2[0](d,init,deps)
    ANALYSIS.append(r)
    c12_y = r[87,"y"]
    pre_peak_87 = r[87,"peak"]
    cm_shift = r["base",3]
    
    init["base",3] = cm_shift

    r = anC12O2[1](d,init,deps)
    ANALYSIS.append(r)
    ini_used = 6
    c12_base = r[87,"base"]
    c12_peak = r[87,"peak"]
    c12_res  = r["std_dev_res"]
    c12_fit_quality = fitQuality(c12_res,c12_peak,50,1)
    peak_87 = r[87,"peak"]

    if (c12_fit_quality <= 1) and (peak_87 >= 20) and abs(r["base",3]) <= 0.07:
        c12_base_ave = initExpAverage(c12_base_ave,c12_base,3,50,counter)
    
        y_87 = r[87,"y"]
        z_87 = r[87,"z"]
        base_87 = r[87,"base"]
        str_87 = r[87,"strength"]        
        slope_87 = r["base",1]
        shift_87 = r["base",3]
        lastgood_shift_87 = shift_87
        lastgood_strength_87 = str_87/P
        lastgood_y_87 = y_87/P
        lastgood_z_87 = z_87/P

        lastgood_y_88 = 1.114 * (y_87/P)
        lastgood_z_88 = 1.114 * (z_87/P)

        adjust_87 = shift_87
    else:
        adjust_87 = 0.0

    peak_value_87 = peak_87 + base_87
    #peak87_baseave = peak_value_87 - c12_base_ave
    peak87_baseave = peak_value_87 - c12_base
    c12_peak = peak87_baseave
        
elif d["spectrumId"] == 106:  # C13O2
    init["base",3] = lastgood_shift_87
    init[87,"scaled_strength"] = lastgood_strength_87
    init[87,"scaled_y"] = lastgood_y_87
    init[87,"scaled_z"] = lastgood_z_87
    init[88,"scaled_y"] = lastgood_y_88
    init[88,"scaled_z"] = lastgood_z_88
    r = anC13O2[0](d,init,deps)
    ANALYSIS.append(r)
    ini_used = 1
    c13_base = r[88,"base"]
    c13_peak = r[88,"peak"]
    c13_res  = r["std_dev_res"]
    c13_fit_quality = fitQuality(c13_res,c13_peak,50,1)
    
    if (c13_fit_quality <= 1) and (peak_87 >= 20):
        shift_88 = r["base",3]
        y_88 = r[88,"y"]
        z_88 = r[88,"z"]
        str_88 = r[88,"strength"]        
        slope_88 = r["base",1]
        quad_88 = r["base",2]
        base_88 = r[88,"base"]
        
        c13_base_ave = initExpAverage(c13_base_ave,c13_base,5,50,counter)
        
        #init = InitialValues()
        #r = anC13O2[2](d,init,deps)
        #ANALYSIS.append(r)
        #polypeak88 = r["base",0] + c13_offset
        #polypeak88_baseave = polypeak88 - c13_base_ave
        f = numpy.array(d.fitData["freq"])
        l = numpy.array(d.fitData["loss"])
        good = (f >= 6251.312) & (f <= 6251.318)
        if len(l[good]) > 0:
            polypeak88 = numpy.average(l[good]) + c13_offset
        else:
            polypeak88 = 0.0
        #polypeak88_baseave = polypeak88 - c13_base_ave
        polypeak88_baseave = polypeak88 - c13_base
        
        r = anC13O2[1](d,init,deps)
        ANALYSIS.append(r)
        abase2 = r["base",2]
        agalbase_88 = r[88,"base"]
        apeak88 = r[88,"peak"]
        acm_shift88 = r["base",3]
        ay_88 = r[88,"y"]
        abase1 = r["base",1]
        shift_88 = acm_shift88
        if apeak88 > 2 and abs(shift_88) < 0.07:
            adjust_88 = shift_88
        else:
            adjust_88 = 0.0
    peak_88 = c13_peak + c13_offset
    peak_value_88 = peak_88 + base_88
    #peak88_baseave = peak_value_88 - c13_base_ave
    peak88_baseave = peak_value_88 - c13_base
    #pass### DATA.filterHistory    
        
elif d["spectrumId"] == 109:  # H2O
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    shift_91 = r["base",3]
    if abs(shift_91) > 0.02:
        r = anH2O[1](d,init,deps)
        shift_91 = r["base",3]
    peak_91 = r[91,"peak"]
    y_91 = r[91,"y"]
    z_91 = r[91,"z"]
    adjust_91 = shift_91

eps = 1e-14
initial_galratio = (peak_88+eps)/(peak_87+eps)
baseave_galratio = (peak88_baseave+eps)/(peak87_baseave+eps)
polybaseave_galratio = (polypeak88_baseave+eps)/(peak87_baseave+eps)

counter += 1

now = time.clock()
fit_time = now-tstart    
if r != None:
    ignoreThis = False
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]        
else:
    ignoreThis = True    

ignore_count = max(0,ignore_count-1)
if (ignore_count == 0) and (not ignoreThis):
    RESULT = {"y_87":y_87,"z_87":z_87,"shift_87":shift_87,"str_87":str_87,"peak87_baseave":peak87_baseave,
              "y_88":y_88,"z_88":z_88,"shift_88":shift_88,"str_88":str_88,"peak88_baseave":peak88_baseave,"peak_88":peak_88,
              "y_91":y_91,"z_91":z_91,"shift_91":shift_91,"peak_91":peak_91,"c12_base_ave":c12_base_ave,"c13_base_ave":c13_base_ave,
              "adjust_87":adjust_87,"adjust_88":adjust_88,"adjust_91":adjust_91,"polypeak88_baseave":polypeak88_baseave,
              "polypeak88":polypeak88,"c13_base":c13_base,"c12_base":c12_base,
              "ratio_i":initial_galratio,"ratio_b":baseave_galratio,"ratio_p":polybaseave_galratio,
              "cavity_pressure":P,"cavity_temperature":T,"etalon_temp":etalonTemp,
              "species":d["spectrumId"],"fit_time":fit_time,
              "interval":interval,"solenoid_valves":solValves,"das_temp":dasTemp}