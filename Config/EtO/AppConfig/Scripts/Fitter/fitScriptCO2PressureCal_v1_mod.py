#  G2000 fit script for carbon dioxide, modified for CFADS pressure calibration
#  Version 1 started 2 Sep 2010 by hoffnagle
#  2011-02-08:  Removed tuner ensemble filter -- makes no sense for fine scan

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./ETO/Spectral library for ETO 6080 wvn v2.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"test_instr_params.ini")
    #instrParams = getInstrParams(fname)
    #locals().update(instrParams)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_sgdbr.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']

    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./ETO/CO2_R4_VCVY_v1.ini")))
    lastShift = None
    co2_adjust = 0
    
#   Globals
    last_time = None
    f_eto = 6080.0630    #  Target for "0th mode" frequency
      
#   Baseline parameters

    baseline_level = instrParams['Baseline_level']
    baseline_slope = instrParams['Baseline_slope']
    baseline_curvature = instrParams['Baseline_curvature']
    A0 = instrParams['Sine0_ampl']
    Nu0 = instrParams['Sine0_freq']
    Per0 = instrParams['Sine0_period']
    Phi0 = instrParams['Sine0_phase']
    A1 = instrParams['Sine1_ampl']
    Nu1 = instrParams['Sine1_freq']
    Per1 = instrParams['Sine1_period']
    Phi1 = instrParams['Sine1_phase']
    

init = InitialValues()
if lastShift is not None:
    init["base",3] = lastShift

deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
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

tstart = time.clock()
if d["spectrumId"]==181:
    init["base",0] = 500
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    co2_shift = r["base",3]
    peak_24 = r[24,"peak"]
    base_24 = r[24,"base"]
    str_24 = r[24,"strength"]
    y_24 = r[24,"y"]
    base = r["base",0]
    slope = r["base",1]
    co2_res = r["std_dev_res"]
    if peak_24 > 10 and abs(co2_shift) < 0.02:
        co2_adjust = co2_shift
    lastShift = co2_adjust

    RESULT = {"co2_res":co2_res,"co2_str":str_24,
        "y_parameter":abs(y_24),"co2_baseline":base,"co2_baseline_slope":slope,
        "co2_base":base_24,"co2_shift":co2_shift,"freq_offset":co2_adjust,"co2_peak":peak_24,
        "co2_tuner_mean":tunerMean,"co2_tuner_std": std(d.tunerValue),
        "co2_pzt_mean":pztMean,"co2_pzt_std":std(d.pztValue)}

    RESULT.update({"species":1,"co2_fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp})
    RESULT.update(d.sensorDict)
