#  2010-05-07  hoffnagle  Translated from HADS-yy pressure calibration v1_0.txt
#  2010-08-08  sze        Use lastShift as initial value for next shift to work better for etalon temperature sensitivity
#  2011-07-26  hoffnagle  Adapted to use new spectral region near 7200 wvn

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./isoH2O7000/spectral library v3_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./isoH2O7000/HIDS-xx H2O pressure fit v1_0.ini")))
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
peak2 = r[2,"peak"]
str2 = r[2,"strength"]
shift = r["base",3]
y2 = r[2,"y"]
now = time.clock()
fit_time = now-tstart
lastShift = shift

RESULT = {"peak2":peak2,"str2":str2,"y2":y2,"shift":shift,
           "tuner_mean":tunerMean,"pzt_mean":pztMean,"points":d["datapoints"],"y_parameter":y2,
           "freq_shift":shift,'stddevres':r["std_dev_res"],
           "tuner_std":std(d.tunerValue),"pzt_mean":std(d.pztValue),
           "h2o_fittime":fit_time}
RESULT.update({"species":3,"fittime":fit_time,
               "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
               "das_temp":dasTemp})
RESULT.update(d.sensorDict)
print "H2O Fit time: %.3f" % (RESULT["h2o_fittime"],) 
