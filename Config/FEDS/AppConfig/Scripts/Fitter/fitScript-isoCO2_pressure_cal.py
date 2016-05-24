from numpy import mean, std, sqrt
import os.path
import time

if INIT:
    fname = os.path.join(BASEPATH,r"./CBDS/CBDS-5 spectral library v20080627.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CBDS/C12 only v1_0.ini")))
    lastShift = None
   
init = InitialValues()
if lastShift is not None:
    init["base",3] = lastShift
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3.5)
d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=3.5)
d.sparse(maxPoints=100,width=0.0001,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.0)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
pztMean = mean(d.pztValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.clock()
r = anCO2[0](d,init,deps)
ANALYSIS.append(r)
peak87 = r[87,"peak"]
str87 = r[87,"strength"]
offset = r["base",3]
y87 = r[87,"y"]
z87 = r[87,"z"]
v87 = r[87,"v"]
now = time.clock()
fit_time = now-tstart
lastShift = offset

RESULT = {"y_parameter":y87,"peak87":peak87,"str87":str87,"freq_offset":offset,"y87":y87,"z87":z87,"v87":v87,
           "tuner_mean":tunerMean,"pzt_mean":pztMean,
           "tuner_std":std(d.tunerValue),"pzt_mean":std(d.pztValue),
           "fittime":fit_time}
RESULT.update({"species":3,"fittime":fit_time,
               "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
               "das_temp":dasTemp})
RESULT.update(d.sensorDict)
pass### "12CO2 Fit time: %.3f" % (RESULT["fittime"],) 
