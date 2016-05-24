#  Fit script for standard CFADS carbon dioxide fitter (spectrum id = 10 or 12) as of June 2010
#  Translated from R:\LV8_Development\rella\Releases\batch file inis\CFADS-xx\2010 0528\Release C1.56 F0.73\Cv1_56 Fv0_73 2010 0528.txt
#  by hoffnagle on 24 June 2010
#  Modified 10 Aug 2010:  added peak height condition when reporting h2o_adjust to prevent WLM wandering when h2o conc -> 0
#                         current threshold for h2o_adjust reporting = 2 ppb/cm or 0.02% -- hoffnagle
#  2010-09-03:  Added reporting of PZT mean and standard deviation for calibration points (hoffnagle)
#  2011-01-26:  Added condition on number of data groups
#  2011-04-28:  Replaced numgroups (deprecated) with ngroups.
#  2013-01-18:  Changed condition on shift for FC fit from 0.01 to 0.04 wvn
#  2013-01-22:  Changed lower limit on bad ringdown filter from 0.5 to 0.2 ppm/cm
#  2013-02-12:  Fixed bug that allowed adjust to be non-zero when quality condition not met
#  2014-02-26:  Changed shift reporting to agree with our other instruments.  No changed needed for adjust

from numpy import any, mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library v1_043_CFADS-xx_2009_0813.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O v1_1 2008 0304.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O FC v1_1 2008 0304.ini")))

    pzt_mean = 0.0
    pzt_stdev = 0.0

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=100,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=1.8)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

tstart = time.clock()
if d["spectrumId"]==11 and d["ngroups"]>5:
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    if r[75,"peak"] < 3 or abs(r["base",3]) >= 0.04:
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
    h2o_res = r["std_dev_res"]
    h2o_peak = r[75,"peak"]
    h2o_quality = fitQuality(h2o_res,h2o_peak,50,1)
    h2o_adjust = 0.0

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = mean(d.pztValue[cal])
        pzt_stdev = std(d.pztValue[cal])

    if h2o_quality < 1.5:
        h2o_str = r[75,"strength"]
        h2o_y = r[75,"y"]
        h2o_z = r[75,"z"]
        h2o_base = r[75,"base"]
        h2o_conc = h2o_peak * 0.01002
        if h2o_peak > 3.0:
            h2o_adjust = h2o_shift
        else:
            h2o_adjust = 0.0
        RESULT = {"h2o_res":h2o_res, "h2o_peak":h2o_peak, "h2o_str":h2o_str,
                  "h2o_conc_precal":h2o_conc, "h2o_y":h2o_y, "h2o_z":h2o_z,"h2o_adjust":h2o_adjust,
                  "h2o_shift":h2o_shift, "h2o_tuner_mean":tunerMean,"h2o_pzt_mean":pzt_mean,
                  "h2o_tuner_std":std(d.tunerValue),"h2o_pzt_std":pzt_stdev}
    RESULT.update({"species":3,"h2o_fittime":time.clock()-tstart, "h2o_quality":h2o_quality,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
