#  G2000 fit script for pressure calibration in H2O2 region using strong water line
#  Version 1 started 5 Jan 2012 by hoffnagle

from numpy import mean, std, sqrt
import os.path
import time

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"./NBDS/spectral library NBDS-xx v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    #fname = os.path.join(BASEPATH,r"test_instr_params.ini")
    #instrParams = getInstrParams(fname)
    #locals().update(instrParams)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/H2O2_PressureCal_v1.ini")))
    lastShift = None

init = InitialValues()
if lastShift is not None:
    init["base",3] = lastShift

deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.30,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]

tstart = time.clock()
if d["spectrumId"] == 0:
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    peak_74 = r[74,"peak"]
    base_74 = r[74,"base"]
    y_74 = r[74,"y"]
    z_74 = r[74,"z"]
    base = r["base",0]
    slope = r["base",1]
    h2o_res = r["std_dev_res"]
    if peak_74 > 10 and abs(h2o_shift) < 0.02:
        h2o_adjust = h2o_shift
    else:
        h2o_adjust = 0
    lastShift = h2o_adjust

    RESULT = {"h2o_res":h2o_res,"y_parameter":abs(y_74),"z_parameter":abs(z_74),
        "baseline":base,"baseline_slope":slope,"h2o_peak":peak_74,
        "h2o_shift":h2o_shift,"freq_offset":h2o_adjust}

    RESULT.update({"species":0,"fittime":time.clock()-tstart,
                   "cavity_pressure":P,"cavity_temperature":T})
    RESULT.update(d.sensorDict)
