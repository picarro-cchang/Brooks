#  G2000 fit script for pressure calibration using the 6053 wavenumber water line
#  2011 1115:  Removed variable y on neighboring CO2 line 
#  2011 1116:  New start with 6058.19229 wvn CO2 line -- 6053 water has mysterious change in Galatry parameters (lineshape)

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./FCDS/spectral library FCDS v2_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"test_instr_params.ini")
    #instrParams = getInstrParams(fname)
    #locals().update(instrParams)
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FCDS_PressureCal_v2_1.ini")))

    # For offline analysis and output to file    
    out = open("Fit_results.txt","w")
    first_fit = 1
    
init = InitialValues()    
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.002,sigmaThreshold=3)
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
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    co2_shift = r["base",3]
    peak_25 = r[25,"peak"]
    base_25 = r[25,"base"]
    str_25 = r[25,"strength"]
    y_25 = r[25,"y"]
    z_25 = r[25,"z"]
    base = r["base",0]
    slope = r["base",1]
    co2_res = r["std_dev_res"]
    if peak_25 > 5 and abs(co2_shift) < 0.04:
        co2_adjust = co2_shift
    else:
        co2_adjust = 0.0
        
    RESULT = {"co2_res":co2_res,"co2_str":str_25,"z_parameter":abs(z_25),
        "y_parameter":abs(y_25),"co2_baseline":base,"co2_baseline_slope":slope,
        "co2_base":base_25,"co2_shift":co2_shift,"freq_offset":co2_adjust,"co2_peak":peak_25}
    RESULT.update({"species":1,"co2_fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T})
    RESULT.update(d.sensorDict)
              
    if first_fit:
        keys = sorted([k for k in RESULT])
        print>>out," ".join(keys)
        first_fit = 0
    print>>out," ".join(["%s" % RESULT[k] for k in keys])