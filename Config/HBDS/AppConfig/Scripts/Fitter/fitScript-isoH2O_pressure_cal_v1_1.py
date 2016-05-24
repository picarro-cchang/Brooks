#  2010-05-07  hoffnagle  Translated from HADS-yy pressure calibration v1_0.txt
#  2010-08-08  sze        Use lastShift as initial value for next shift to work better for etalon temperature
#                          sensitivity

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./HBDS/spectral library v1_047_HADS1_1005.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HBDS/HADS-01 H2O pressure fit v0_0 1005.ini")))
    lastShift = None

init = InitialValues()

if lastShift is not None:
    init["base",3] = lastShift

deps = Dependencies()
ANALYSIS = []
d = DATA
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
r = anH2O[0](d,init,deps)
ANALYSIS.append(r)
peak85 = r[85,"peak"]
str85 = r[85,"strength"]
cm_center85 = r[85,"center"]
offset = r["base",3]
y85 = r[85,"y"]
z85 = r[85,"z"]
v85 = r[85,"v"]
now = time.clock()
fit_time = now-tstart
lastShift = offset

RESULT = {"peak85":peak85,"str85":str85,"y85":y85,"z85":z85,"v85":v85,
           "tuner_mean":tunerMean,"pzt_mean":pztMean,"points":d["datapoints"],"y_parameter":y85,
           "freq_offset":offset,
           "tuner_std":std(d.tunerValue),"pzt_mean":std(d.pztValue),
           # "cm_center85":cm_center85,
           "h2o_fittime":fit_time}
RESULT.update({"species":3,"fittime":fit_time,
               "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
               "das_temp":dasTemp})
RESULT.update(d.sensorDict)
print "H2O Fit time: %.3f" % (RESULT["h2o_fittime"],)
