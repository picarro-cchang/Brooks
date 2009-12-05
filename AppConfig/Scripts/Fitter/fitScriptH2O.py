from numpy import mean, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library v1_043_CFADS-1_0220.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O v1_1 0619.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O FC v1_1 0619.ini")))

    h2o_strength = 0
    h2o_y = 0
    h2o_base = 0
    h2o_conc = 0
    h2o_shift = 0
    h2o_quality = 0
    Ilaserfine = 0
   
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=2.5)
d.sparse(maxPoints=100,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=1.8)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]
spectrumId = d.sensorDict["SpectrumID"]
etalonTemp = d.sensorDict["EtalonTemp"]
#heaterCurrent = d.sensorDict["Heater_I_mA"]
inletValvePos = d.sensorDict["InletValve"]
outletValvePos = d.sensorDict["OutletValve"]

species = (d.subschemeId & 0x3FF)[0]
init["base",0] = 800
print d["filterHistory"]
tstart = time.clock()
if species==26:
    try:
        Ilaserfine = 0.01*mean(d.fineLaserCurrent) + 0.99*Ilaserfine
    except:
        pass
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    if abs(r["base",3]) >= 0.01:
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
    h2o_res = r["std_dev_res"]
    h2o_peak = r[75,"peak"]
    h2o_quality = fitQuality(h2o_res,h2o_peak,50,1)
    if h2o_quality < 1.5:
        h2o_strength = r[75,"strength"]
        h2o_y = r[75,"y"]
        h2o_base = r[75,"base"]                    
        h2o_conc = h2o_peak * 0.01002
        h2o_shift = r["base",3]
    RESULT = {"h2o_res":h2o_res, "h2o_peak":h2o_peak, "h2o_strength":h2o_peak,
              "h2o_conc":h2o_conc, "h2o_y":h2o_y, "h2o_quality":h2o_quality,
              "h2o_shift":h2o_shift}
              
    RESULT.update({"species":3,"h2o_fittime":time.clock()-tstart,"h2o_Ilaserfine":Ilaserfine,
                   "cavity_pressure":P,"cavity_temperature":T,
                   "solenoid_valves":solValves,"das_temp":dasTemp,
                   "spectrum_id":spectrumId,"etalon_temp":etalonTemp,#"heater_current":heaterCurrent,
                   "inlet_valve_pos":inletValvePos,"outlet_valve_pos":outletValvePos}
                  )
    print "H2O Fit time: %.3f" % (RESULT["h2o_fittime"],) 
else:
    RESULT = {}
