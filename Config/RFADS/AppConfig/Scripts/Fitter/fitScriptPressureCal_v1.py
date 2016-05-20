#  G2000 fit script for pressure calibration using the 6053 wavenumber water line

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library v1_043_CFADS-xx_2009_0813.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"test_instr_params.ini")
    #instrParams = getInstrParams(fname)
    #locals().update(instrParams)
    
    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FCDS_PressureCal_VZ_v1_1.ini")))

init = InitialValues()    
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
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
if d["spectrumId"] == 0:
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    peak_92 = r[92,"peak"]
    base_92 = r[92,"base"]
    str_92 = r[92,"strength"]
    y_92 = r[92,"y"]
    z_92 = r[92,"z"]
    co2_peak = r[93,"peak"]
    co2_y = r[93,"y"]
    base = r["base",0]
    slope = r["base",1]
    h2o_res = r["std_dev_res"]
    if peak_92 > 10 and abs(h2o_shift) < 0.04:
        h2o_adjust = h2o_shift
    else:
        h2o_adjust = 0.0
    
    RESULT = {"h2o_res":h2o_res,"h2o_str":str_92,"z_parameter":abs(z_92),
        "y_parameter":abs(y_92),"h2o_baseline":base,"h2o_baseline_slope":slope,
        "h22_base":base_92,"h2o_shift":h2o_shift,"freq_offset":h2o_adjust,"h2o_peak":peak_92,
        "co2_peak":co2_peak,"co2_y":co2_y}
         
    RESULT.update({"species":1,"h2o_fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T})
    RESULT.update(d.sensorDict)