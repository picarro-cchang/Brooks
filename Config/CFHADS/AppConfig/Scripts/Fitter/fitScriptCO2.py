#  Fitter for super-flux CO2, adapted from CFADS CO2 flux with new spectral library for 60 C
#  Removed peak 89 (indistinguishable from peak 14) from fit definition
#  Removed bogus baseline slope
#  2011 0323 - Version 2 uses new, fancy schemes with RD recycling for high speed
#  2011 0627:  Remove RD recycle to see if noise spectrum becomes flat

from numpy import mean, std, sqrt, unique
from copy import deepcopy
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library 60C_CFADS-xx_v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CADS-xx 9_PNT VW VC VB v1_0.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CADS-xx 9_PNT FW FC FB v1_0.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/CADS-xx CO2 3_PNT v1_0.ini")))

    co2_base_avg = 800
    co2_y_avg = 1.89
    avg_count = 1
    co2_shift = 0
    co2_peak = 0
    co2_base = 0
    co2_adjust = 0
    co2_9ptpeak = 0
    co2_9ptbase = 0
    co2_res = 0

    dList = []
    fitFlag = 0

ANALYSIS = []
d = DATA
if d["spectrumId"] in [10,12]:
    init = InitialValues()
    deps = Dependencies()
    d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
    d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3.5)
    d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=3)
    d.sparse(maxPoints=1000,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
    d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
    d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
    P = d["cavitypressure"]
    T = d["cavitytemperature"]
    tunerMean = mean(d.tunerValue)
    pztMean = mean(d.pztValue)
    solValves = d.sensorDict["ValveMask"]
    dasTemp = d.sensorDict["DasTemp"]
    spectrumId = d.sensorDict["SpectrumID"]
    etalonTemp = d.sensorDict["EtalonTemp"]
    #heaterCurrent = d.sensorDict["Heater_I_mA"]
    inletValvePos = d.sensorDict["InletValve"]
    outletValvePos = d.sensorDict["OutletValve"]

    #print d.filterHistory
    #init["base",0] = 800
    tstart = time.clock()
    r = None

    if d["ngroups"] >= 7:
        r = anCO2[0](d,init,deps)
        if len(unique(r.xData)) >= 7:
            ANALYSIS.append(r)
            co2_shift = r["base",3]
            co2_9ptpeak = r[14,"peak"]
            co2_9ptbase = r[14,"base"]
            co2_res = r["std_dev_res"]
            co2_base_avg = initExpAverage(co2_base_avg,r["base",0],30,100,avg_count)
            if r[14,"peak"] >= 10.0 and abs(co2_shift) < 0.03:
                co2_y_avg = initExpAverage(co2_y_avg,r[14,"y"],30,0.02,avg_count)
                co2_adjust = co2_shift
            else:
                co2_adjust = 0.0
            avg_count += 1
        else:
            r = None
    if d["ngroups"] >= 3:
        init["base",0] = co2_base_avg
        init[14,"y"] = co2_y_avg
        r = anCO2[2](d,init,deps)
        if len(unique(r.xData)) >= 3:
            ANALYSIS.append(r)
            co2_peak = r[14,"peak"]
            co2_base = r[14,"base"]
            co2_res = r["std_dev_res"]
        else:
            r = None

    if r:
        RESULT = {"co2_res":co2_res,"co2_conc_precal":0.713*co2_peak,"co2_str":r[14,"strength"],
                "co2_y":r[14,"y"],"co2_peak":co2_peak,"co2_baseline":r["base",0],
                "co2_base":co2_base,"co2_base_avg":co2_base_avg,
                "co2_9ptpeak":co2_9ptpeak,"co2_9ptbase":co2_9ptbase,
                "co2_y_avg":co2_y_avg,"co2_shift":co2_shift,"co2_adjust":co2_adjust,
                "ringdowns":d["datapoints"],"datagroups":d["ngroups"],
                "co2_tuner_mean":tunerMean,"co2_tuner_std": std(d.tunerValue),
                "co2_pzt_mean":pztMean,"co2_pzt_std":std(d.pztValue)}

        RESULT.update({"species":d["spectrumId"],"co2_fittime":time.clock()-tstart,
                           "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                           "das_temp":dasTemp})
        RESULT.update(d.sensorDict)
    else:
        RESULT = {}
else:
    RESULT = {}
