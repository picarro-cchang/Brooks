##  G2000 isotopic water fitter 
##  Translated from R:\LV8_Development\rella\Releases\batch file inis\CGxx\20090826\Release 2_451\CGDS-xx release 2_451 20090826.txt
##  Added import of instrument-specific fit parameters from ini file -- hoffnagle 28 June 2010

import numpy
import os.path
import time
#from EventManagerProxy import Log

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
    fname = os.path.join(BASEPATH,r"./CBDS/CBDS-7 spectral library v20090410.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"./CBDS/fitter_config.ini")
    instrParams = getInstrParams(fname)

    anC12O2 = []
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./CBDS/C12 only v1_0.ini")))
    anC12O2.append(Analysis(os.path.join(BASEPATH,r"./CBDS/C12 only v1_1.ini")))
    
    anC13O2 = []
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./CBDS/C13 only dev v1_1.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./CBDS/C13 only VC VY v1_0.ini")))
    anC13O2.append(Analysis(os.path.join(BASEPATH,r"./CBDS/polynomial fit C13.ini")))

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CBDS/6250_4 water fitter v1_0.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CBDS/6250_4 water fitter FC v1_0.ini")))

    c12_base_ave = instrParams['C12_baseline']  # Set this to be close to the cavity baseline
    c13_base_ave = instrParams['C13_baseline']  # Set this to be close to the cavity baseline
    y_oxygen = instrParams['y_oxygen']
    y_corr_12 = instrParams['y_corr_12']
    y_corr_13 = instrParams['y_corr_13']
    y_corr_13_quad = instrParams['y_corr_13_quad']
    conc_corr_13 = instrParams['conc_corr_13']
    c13_offset = instrParams['C13_offset']
    counter = -25
    lastgood_shift_87 = 0
    lastgood_strength_87 = 0
    lastgood_y_87 = 0.0136
    lastgood_z_87 = 0.00438
    lastgood_y_88 = 0.01515
    lastgood_z_88 = 0.00488
    
    delta_y = 0.0

    y_87 = 0.0
    z_87 = 0.0
    peak_87 = 0.0
    shift_87 = 0.0
    str_87 = 0.0
    base_87 = 0.0
    c12_base_ave = 0.0
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
    c13_base_ave = 0.0
    c12_fit_quality = 0.0
    c13_fit_quality = 0.0
    
    cm_adjust = 0.0
    initial_galratio = 0.0
    baseave_galratio = 0.0
    polybaseave_galratio = 0.0
    peak88_baseave = 0.0
    peak87_baseave = 0.0
    polypeak88 = 0.0
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
d.defineFitData(freq=d.groupMedians["waveNumber"],loss=1000*d.groupMedians["uncorrectedAbsorbance"],sdev=1/numpy.sqrt(d.groupSizes))
P = d["cavitypressure"]
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]
#species = (d.subSchemeId & 0x3FF)[0]
tstart = time.clock()
RESULT = {}
r = None

if d["spectrumId"] == 105:  # C12O2
    init[87,"scaled_y"] = 0.0136
    r = anC12O2[0](d,init,deps)
    ANALYSIS.append(r)
    vy_87 = r[87,"y"]
    pre_peak_87 = r[87,"peak"]
    cm_shift = r["base",3]
    
    init["base",3] = cm_shift

    r = anC12O2[1](d,init,deps)
    ANALYSIS.append(r)
    base_87 = r[87,"base"]
    peak_87 = r[87,"peak"]
    c12_res  = r["std_dev_res"]
    c12_fit_quality = fitQuality(c12_res,peak_87,50,1)
    c12_base_ave_temp = initExpAverage(c12_base_ave,base_87,3,50,counter)
    peak87_baseave_uncorr = peak_87 + base_87 - c12_base_ave_temp
    y_87 = r[87,"y"]
    z_87 = r[87,"z"]
    str_87 = r[87,"strength"]        
    slope_87 = r["base",1]
    shift_87 = r["base",3]
    delta_y = y_87 - y_oxygen
    correction = 1.0+delta_y*y_corr_12
    peak87_baseave = peak87_baseave_uncorr*correction

    if (c12_fit_quality <= 1) and abs(r["base",3]) <= 0.07:
        c12_base_ave = c12_base_ave_temp
        if  peak_87 >= 20:
            lastgood_shift_87 = shift_87
            lastgood_strength_87 = str_87/P
            lastgood_y_87 = y_87/P
            lastgood_z_87 = z_87/P
            lastgood_y_88 = 1.114 * (y_87/P)
            lastgood_z_88 = 1.114 * (z_87/P)
            cm_adjust = shift_87
        else:
            cm_adjust = 0.0
    else:
        cm_adjust = 0.0
        
    try:
        initial_galratio = peak_88/peak_87
    except:
        initial_galratio = 0.0
    try:
        baseave_galratio = peak88_baseave/peak87_baseave
        polybaseave_galratio = polypeak88_baseave/peak87_baseave
    except:
        baseave_galratio = 0.0
        polybaseave_galratio = 0.0
        
elif d["spectrumId"] == 106:  # C13O2
    init["base",3] = lastgood_shift_87
    init[87,"scaled_strength"] = lastgood_strength_87
    init[87,"scaled_y"] = lastgood_y_87
    init[87,"scaled_z"] = lastgood_z_87
    init[88,"scaled_y"] = lastgood_y_88
    init[88,"scaled_z"] = lastgood_z_88
    r = anC13O2[0](d,init,deps)
    ANALYSIS.append(r)
    c13_base = r[88,"base"]
    c13_peak = r[88,"peak"]
    c13_res  = r["std_dev_res"]
    c13_fit_quality = fitQuality(c13_res,c13_peak,50,1)
    
    if (c13_fit_quality <= 1) and (peak_87 >= 20):
        peak_88 = c13_peak + c13_offset
        shift_88 = r["base",3]
        y_88 = r[88,"y"]
        z_88 = r[88,"z"]
        str_88 = r[88,"strength"]        
        slope_88 = r["base",1]
        quad_88 = r["base",2]    # ?  should always = 0 ?
        peakvalue88 = c13_peak + c13_base + c13_offset
        uncorr_peak88_baseave = peakvalue88 - c13_base_ave
        c13_base_ave = initExpAverage(c13_base_ave,c13_base,5,50,counter)
        
        ##  "Polynomial" fit for C-13 peak.
        ##  Note that this is really just a simple average which can be done w/o invoking fitter
        f = numpy.array(d.fitData["freq"])
        l = numpy.array(d.fitData["loss"])
        good = (f >= 6251.312) & (f <= 6251.318)
        if len(l[good]) > 0:
            polypeak88 = numpy.average(l[good]) + c13_offset
        else:
            polypeak88 = 0.0
        ## init = InitialValues()
        ## r = anC13O2[2](d,init,deps)
        ## ANALYSIS.append(r)
        ## polypeak88 = r["base",0] + c13_offset
        uncorr_polypeak88_baseave = polypeak88 - c13_base_ave
    
        ##  Fit with variable center and y for C-13 peak
        ##  Need to check whether this fit is initialized correctly!
        ##  Note:  at present these results are not reported to higher-level routines!
        r = anC13O2[1](d,init,deps)
        ANALYSIS.append(r)
        abase2 = r["base",2]
        agalbase_88 = r[88,"base"]
        apeak88 = r[88,"peak"]
        acm_shift88 = r["base",3]
        ay_88 = r[88,"y"]
        abase1 = r["base",1]
        
        correction = 1.0 + y_corr_13*delta_y + y_corr_13_quad*delta_y**2 + conc_corr_13*peak87_baseave
        peak88_baseave = uncorr_peak88_baseave*correction
        polypeak88_baseave = uncorr_polypeak88_baseave*correction
        
        if apeak88 >= 3.0 and abs(acm_shift88) <= 0.02:
            acm_adjust88 = acm_shift88
        else:
            acm_adjust88 = 0.0
        
    try:
        initial_galratio = peak_88/peak_87
    except:
        initial_galratio = 0.0
    try:
        baseave_galratio = peak88_baseave/peak87_baseave
        polybaseave_galratio = polypeak88_baseave/peak87_baseave
    except:
        baseave_galratio = 0.0
        polybaseave_galratio = 0.0
        
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


counter += 1

now = time.clock()
fit_time = now-tstart    
if r != None:
    ignoreThis = False
    last_time = r["time"]
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0    
else:
    ignoreThis = True    

ignore_count = max(0,ignore_count-1)
if (ignore_count == 0) and (not ignoreThis):
    RESULT = {"y_87":y_87,"z_87":z_87,"shift_87":shift_87,"str_87":str_87,"peak87_baseave":peak87_baseave,
              "y_88":y_88,"z_88":z_88,"shift_88":shift_88,"str_88":str_88,"peak88_baseave":peak88_baseave,"peak_88":peak_88,
              "y_91":y_91,"z_91":z_91,"shift_91":shift_91,"peak_91":peak_91,"delta_y":delta_y,"polypeak88":polypeak88,
              "cm_adjust":cm_adjust,"c12_fit_quality":c12_fit_quality,"c13_fit_quality":c13_fit_quality,
              "ratio_i":initial_galratio,"ratio_b":baseave_galratio,"ratio_p":polybaseave_galratio,
              "cavity_pressure":P,"species":d["spectrumId"],"fit_time":fit_time,
              "interval":interval,"solenoid_valves":solValves,"dasTemp":dasTemp}