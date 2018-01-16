from numpy import mean, std, sqrt
import os.path
import time

if INIT:
    fname = os.path.join(BASEPATH,r".\NH3\spectral library v1_045_AADS4_D5.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    an = []
    an.append(Analysis(os.path.join(BASEPATH,r".\NH3\H2O pressure fit #72 v0_0.ini")))
    lastShift = None
   
init = InitialValues()
if lastShift is not None:
    init["base",3] = lastShift
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
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
r = an[0](d,init,deps)
ANALYSIS.append(r)
peak72 = r[72,"peak"]
str72 = r[72,"strength"]
offset = r["base",3]
y72 = r[72,"y"]
z72 = r[72,"z"]
v72 = r[72,"v"]
now = time.clock()
fit_time = now-tstart
lastShift = offset

RESULT = {"y_parameter":y72,"peak72":peak72,"str72":str72,"freq_offset":offset,"y72":y72,"z72":z72,"v72":v72,
           "tuner_mean":tunerMean,"pzt_mean":pztMean,
           "tuner_std":std(d.tunerValue),"pzt_mean":std(d.pztValue),
           "fittime":fit_time}
RESULT.update({"species":3,"fittime":fit_time,
               "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
               "das_temp":dasTemp})
RESULT.update(d.sensorDict)
print "12CO2 Fit time: %.3f" % (RESULT["fittime"],) 
