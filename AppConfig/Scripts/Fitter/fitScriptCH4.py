from numpy import mean, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library v1_043_CFADS-1_0220.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 v2_0 0402.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC FY v2_0 0402.ini")))

    ch4_amp = 0
    ch4_y = 0
    ch4_shift = 0
    ch4_conc = 0
    ch4_adjconc = 0
    ch4_conc_peak = 0
    y_avg = 1.2
    base_avg = 1000
    shift_avg = 0
    avg_count = 1
    Ilaserfine = 0
   
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=2.5)
d.sparse(maxPoints=1000,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.5)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
species = (d.subschemeId & 0x3FF)[0]
init["base",0] = 800
print d["filterHistory"]
tstart = time.clock()
if species==25:
    try:
        Ilaserfine = 0.01*mean(d.fineLaserCurrent) + 0.99*Ilaserfine
    except:
        pass
    r = anCH4[0](d,init,deps)
    ANALYSIS.append(r)
    if d["datapoints"] >= 5:
        if r[1002,2] <= 0.005:
            r = anCH4[1](d,init,deps)
        ch4_amp = r[1002,2]
        ch4_conc = 10*r[1002,2]
        ch4_y = r[1002,5]
        ch4_adjconc = ch4_y*ch4_conc*(140.0/P)
        ch4_conc_peak = r[1002,"peak"]/216.3
        if ch4_conc > 0.1:
            ch4_shift = r["base",3]
        else:
            ch4_shift = 0
    ch4_res = r["std_dev_res"]
    RESULT = {"ch4_res":ch4_res, "ch4_conc_peak":ch4_conc_peak,
              "ch4_conc":ch4_conc,"ch4_y":ch4_y,"ch4_adjconc":ch4_adjconc,
              "ch4_shift":ch4_shift,"cavity_pressure":P,"species":2,
              "ch4_fittime":time.clock()-tstart,"ch4_Ilaserfine":Ilaserfine}
    avg_count += 1
    print "CH4 Fit time: %.3f" % (RESULT["ch4_fittime"],) 
else:
    RESULT = {}
