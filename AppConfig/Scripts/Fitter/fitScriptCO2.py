from numpy import mean, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library v1_043_CFADS-1_0220.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CADS-3 9_PNT VW VC VB F89 v1_1.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CADS-3 9_PNT FW FC FB F89 v1_1.ini")))
    
    base0_avg = None
    cen14_avg = None
    co2_str_avg = 0
    co2_y_avg = None
    peak14_avg = None
    str89_avg = None
    avg_count = 1
    co2_shift = 0
    Ilaserfine = 0
    
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
print d.nrows
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=2.5)
d.sparse(maxPoints=1000,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.5)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
species = (d.subschemeId & 0x3FF)[0]
#print "SpectrumId", d["spectrumId"]
init["base",0] = 800
tstart = time.clock()
if species==10:
    try:
        Ilaserfine = 0.01*mean(d.fineLaserCurrent) + 0.99*Ilaserfine
    except:
        pass
    init[89,"scaled_strength"] = 2.0/P
    init[14,"scaled_y"] = 0.01357
    init[14,"scaled_z"] = 0.00442
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    if d["datapoints"] >= 2:
        if r[14,"peak"] >= 10.0:
            str_diff = r[14,"strength"] - co2_str_avg
            if abs(str_diff) > 50.0:
                co2_str_avg = r[14,"strength"]
                peak14_avg = r[14,"peak"]
            base0_avg = initExpAverage(base0_avg,r["base",0],30,100,avg_count)
            co2_y_avg = initExpAverage(co2_y_avg,r[14,"y"],30,0.02,avg_count)
            str89_avg = initExpAverage(str89_avg,r[89,"strength"],30,0.2,avg_count)
            cen14_avg = initExpAverage(cen14_avg,r[14,"center"],10,0.0002,avg_count)
            # Preset to average values
            init["base",0] = base0_avg
            init[89,"scaled_strength"] = str89_avg/P
            init[14,"center"] = cen14_avg
            init[14,"scaled_y"] = co2_y_avg/P
            init[14,"scaled_z"] = 0.3287*co2_y_avg/P
            co2_shift = 6237.408 - cen14_avg
        else:
            init[14,"center"] = 6237.408
        # Fit using only strength as adjustable parameter
        r = anCO2[1](d,init,deps)
        ANALYSIS.append(r)
        co2_str_avg = initExpAverage(co2_str_avg,r[14,"strength"],15,10000,avg_count)
        peak14_avg = initExpAverage(peak14_avg,r[14,"peak"],15,2000,avg_count)
        co2_res = r["std_dev_res"]
        print "co2_y=", co2_y_avg
        RESULT = {"co2_res":co2_res,"co2_conc_peak":0.713*r[14,"peak"],"co2_str":r[14,"strength"],
            "co2_y":co2_y_avg,"str89":str89_avg,"co2_shift":co2_shift,"cavity_pressure":P}
        avg_count += 1
    else:
        RESULT = {}
    RESULT["co2_fittime"] = time.clock()-tstart
    RESULT["species"] = 1
    RESULT["co2_Ilaserfine"] = Ilaserfine
    
    print "CO2 Fit time: %.3f" % (RESULT["co2_fittime"],) 
else:
    RESULT = {}        
