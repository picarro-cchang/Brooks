from numpy import mean, std, sqrt
import os.path
import time

if INIT:
    fname = os.path.join(BASEPATH,r".\NH3\spectral library v1_045_AADS4_D5.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    an = []
    an.append(Analysis(os.path.join(BASEPATH,r".\NH3\CO2 pressure fit #74 v0_0.ini")))
    lastShift = 0.0

init = InitialValues()
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
r = an[0](d,init,deps)
ANALYSIS.append(r)
peak74 = r[74,"peak"]
str74 = r[74,"strength"]
offset = r["base",3]
y74 = r[74,"y"]
z74 = r[74,"z"]
v74 = r[74,"v"]
now = time.clock()
fit_time = now-tstart
lastShift = 0.95*offset + 0.05*lastShift
if lastShift > 0.04: lastShift = 0.04
if lastShift < -0.04: lastShift = -0.04

RESULT = {"y_parameter":y74,"peak74":peak74,"str74":str74,"freq_offset":offset,"y74":y74,"z74":z74,"v74":v74,
           "tuner_mean":tunerMean,"pzt_mean":pztMean,
           "tuner_std":std(d.tunerValue),"pzt_mean":std(d.pztValue),
           "fittime":fit_time}
RESULT.update({"species":1,"fittime":fit_time,
               "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
               "das_temp":dasTemp})
RESULT.update(d.sensorDict)
print "12CO2 Fit time: %.3f" % (RESULT["fittime"],)
