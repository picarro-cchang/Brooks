#  Fit script for standard CFADS carbon dioxide fitter (spectrum id = 10 or 12) as of June 2010
#  Translated from R:\LV8_Development\rella\Releases\batch file inis\CFADS-xx\2010 0528\Release C1.56 F0.73\Cv1_56 Fv0_73 2010 0528.txt
#  by hoffnagle on 22 June 2010
#  10 Aug 2010: changed ch4_shift and ch4_adjust definitions to match other fitter naming conventions, i.e. shift is from variable center fit
#               regardless of line strength; adjust is conditional on line strength and abs(shift)  -- hoffnagle
#  2010-09-03:  Added reporting of PZT mean and standard deviation for calibration points (hoffnagle)
#  2010-09-17:  Fixed condition on number of sparsed groups
#  2010-10-08:  Fixed bug in reporting of variable center results
#  2011-02-08:  Fixed bug in filtering:  tuner ensemble filter rejected fine scan points
#                Changed sigma filter to outlier filter.
#  2011-04-28:  Replaced numgroups (deprecated) with ngroups.

from numpy import any, mean, std, sqrt
from copy import copy
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library v1_043_CFADS-1_0220.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CADS 11_PNT VW VC VB v2_1 2008 0304.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CADS 11_PNT VW FC VB v2_1 2008 0304.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CADS 11_PNT FW FC VB v2_1 2008 0304.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CADS PeakTopper v1_0 2008 0304.ini")))

    base_avg = 800
    counter = -20
    pzt_mean = 0.0
    pzt_stdev = 0.0

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = copy(DATA)
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]
spectrumId = d.sensorDict["SpectrumID"]
etalonTemp = d.sensorDict["EtalonTemp"]
#heaterCurrent = d.sensorDict["Heater_I_mA"]
inletValvePos = d.sensorDict["InletValve"]
outletValvePos = d.sensorDict["OutletValve"]

tstart = time.clock()
if (d["spectrumId"] in [10,12]) and (d["ngroups"] > 9):
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    co2_shift = r["base",3]
    vpeak_14 = r[14,"peak"]
    vstr_14 = r[14,"strength"]
    vy_14 = r[14,"y"]
    vbase = r["base",0]
# Fit with fixed center and variable y if peak is strong
    if (vpeak_14 >= 10) and (abs(co2_shift) <= 0.07):
        init["base",3] = co2_shift
        r = anCO2[1](d,init,deps)
        ANALYSIS.append(r)
# Fit with fixed center and y if peak is weak or shift large
    else:
        init["base",3] = 0.0
        init[14,"y"] = 1.85
        r = anCO2[2](d,init,deps)
        ANALYSIS.append(r)
    base_14 = r[14,"base"]
    str_14 = r[14,"strength"]
    y_14 = r[14,"y"]
    base = r["base",0]
    co2_res = r["std_dev_res"]

    peak_14 = r[14,"peak"]
    co2_peakvalue = peak_14+base
    base_avg  = initExpAverage(base_avg,base,10,100,counter)
    co2_peak_baseavg = co2_peakvalue-base_avg
    galpeak14_final = co2_peak_baseavg
    counter += 1
    if peak_14 > 3.0 and abs(co2_shift) < 0.07:
        co2_adjust = co2_shift
    else:
        co2_adjust = 0.0

#  Quadratic fit to peak if it is larger than 200 ppb/cm
    if co2_peak_baseavg > 200:
        quadset = -4673*co2_peak_baseavg
        init["base",3] = 0.0
        init["base",2] = quadset
        d = copy(DATA)
        d.wlmSetpointFilter(maxDev=0.001,sigmaThreshold=5)
        d.sparse(maxPoints=1000,width=0.00025,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
        d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
        toppers = len([freq for freq in d.fitData["freq"] if (freq > 6237.398) and (freq < 6237.418)])
        if (toppers > 4) and (abs(co2_shift) <= 0.0006):
            r = anCO2[3](d,init,deps)
            ANALYSIS.append(r)
            quadshift = -0.5*r["base",1]/r["base",2]
            quadmax = r["base",0] + 0.5*quadshift*r["base",1]
            galpeak14_quad_avg = quadmax-base_avg
            galpeak14_final = galpeak14_quad_avg

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = mean(d.pztValue[cal])
        pzt_stdev = std(d.pztValue[cal])

    RESULT = {"co2_res":co2_res,"galpeak14_final":galpeak14_final,"co2_str":str_14,"vpeak_14":vpeak_14,"vy_14":vy_14,
        "co2_y":y_14,"co2_peak_baseavg":co2_peak_baseavg,"co2_baseline":base,"co2_baseline_avg":base_avg,
        "co2_base":base_14,"co2_shift":co2_shift,"co2_adjust":co2_adjust,"peak_14":peak_14,
        "co2_Points":d["datapoints"],"co2_Groups":d["ngroups"],
        "co2_tuner_mean":tunerMean,"co2_tuner_std": std(d.tunerValue),
        "co2_pzt_mean":pzt_mean,"co2_pzt_std":pzt_stdev}

    RESULT.update({"species":1,"co2_fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
