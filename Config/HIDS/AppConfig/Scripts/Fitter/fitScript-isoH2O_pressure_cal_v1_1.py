#  2010-05-07  hoffnagle  Translated from HADS-yy pressure calibration v1_0.txt
#  2010-08-08  sze        Use lastShift as initial value for next shift to work better for etalon temperature sensitivity
#  2011-07-26  hoffnagle  Adapted to use new spectral region near 7200 wvn
#  2011-07-29  hoffnagle  Removed last shift as initial value -- bad at high pressure

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./HIDS/HIDS spectral library v3_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/HIDS-xx H2O pressure fit v1_1.ini")))
    lastShift = None
# For offline analysis and output to file
#    out = open("Fit_results.txt","w")
#    first_fit = 1

init = InitialValues()

#if lastShift is not None:
#    init["base",3] = lastShift




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
init[2,"strength"] = 0
r = anH2O[0](d,init,deps)
ANALYSIS.append(r)
peak2 = r[2,"peak"]
str2 = r[2,"strength"]
offset = r["base",3]
y2 = r[2,"y"]
now = time.clock()
fit_time = now-tstart
#lastShift = shift

RESULT = {"peak2":peak2,"str2":str2,"y2":y2,"offset":offset,
           "tuner_mean":tunerMean,"pzt_mean":pztMean,"points":d["datapoints"],"y_parameter":y2,
           "freq_offset":offset,'stddevres':r["std_dev_res"],
           "tuner_std":std(d.tunerValue),"pzt_mean":std(d.pztValue),
           "h2o_fittime":fit_time}
RESULT.update({"species":3,"fittime":fit_time,
               "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
               "das_temp":dasTemp})
RESULT.update(d.sensorDict)

# if first_fit:
    # keys = sorted([k for k in RESULT])
    # print>>out," ".join(keys)
    # first_fit = 0
# print>>out," ".join(["%s" % RESULT[k] for k in keys])
