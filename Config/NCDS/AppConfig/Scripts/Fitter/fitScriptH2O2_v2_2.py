#  Fit script for NBDS hydrogen peroxide fitter
#  Translated from R:\LV8_Development\rella\Releases\batch file inis\NBDS-xx\NBDS-04\20090908\Release 2.0021\NBDS-04 2_0021 20090908.txt
#  by Hoffnagle starting 7 June 2011
#  Spectral library adds 1 isolated water line for pressure cal; fit ini files are renamed and reformatted but not changed
#  2012 0720:  new splines acquired with much less water in the peroxide spectrum; added baseline parameters
#  2012 0723:  new water splines appear to have been contaminated with H2O2 -- replace them
#  2013 0523:  adjust concentration coefficients to agree with new calibrations

from numpy import any, mean, std, sqrt
import os.path
import time

def expAverage(xavg,x,n,dxMax):
    if xavg is None: return x
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)<dxMax: return y
    elif y>xavg: return xavg+dxMax
    else: return xavg-dxMax
def initExpAverage(xavg,x,hi,dxMax,count):
    if xavg is None: return x
    n = min(max(count,1),hi)
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)<dxMax: return y
    elif y>xavg: return xavg+dxMax
    else: return xavg-dxMax
def fitQuality(sdFit,maxPeak,normPeak,sdTau):
    return sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

def initialize_Baseline():
    init["base",0] = baseline_level
    init["base",1] = baseline_slope
    init[1002,0] = A0
    init[1002,1] = Nu0
    init[1002,2] = Per0
    init[1002,3] = Phi0
    init[1003,0] = A1
    init[1003,1] = Nu1
    init[1003,2] = Per1
    init[1003,3] = Phi1

if INIT:
    fname = os.path.join(BASEPATH,r"./NBDS/spectral library NBDS-xx v2_2.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    anH2O2 = []
    anH2O2.append(Analysis(os.path.join(BASEPATH,r"./NBDS/NBDSxx H2O2 ONLY V-slope v2.ini")))
    anH2O2.append(Analysis(os.path.join(BASEPATH,r"./NBDS/NBDSxx H2O + H2O2 basic FY VC v2.ini")))
    anH2O2.append(Analysis(os.path.join(BASEPATH,r"./NBDS/NBDSxx H2O + H2O2 basic VY VC v2.ini")))
    anH2O2.append(Analysis(os.path.join(BASEPATH,r"./NBDS/NBDSxx H2O + H2O2 basic v2 FC FY.ini")))

#  Import calibration constants from fitter_config.ini at initialization
    H2O2_off = instrParams['H2O2_offset']
    H2O2_H1 = instrParams['H2O2_water_linear']
    H2O2_H2 = instrParams['H2O2_water_quadratic']
    H2O2_Hconc = instrParams['H2O2_water_conc_linear']
    H2O_H2O2_conc = instrParams['H2O_peroxide_conc_linear']
    H2O_scale = instrParams['H2O_scale']

#  Import baseline parameters
    baseline_level = instrParams['Baseline_level']
    baseline_slope = instrParams['Baseline_slope']
    A0 = instrParams['Sine0_ampl']
    Nu0 = instrParams['Sine0_freq']
    Per0 = instrParams['Sine0_period']
    Phi0 = instrParams['Sine0_phase']
    A1 = instrParams['Sine1_ampl']
    Nu1 = instrParams['Sine1_freq']
    Per1 = instrParams['Sine1_period']
    Phi1 = instrParams['Sine1_phase']

#  Globals
    counter = -10
    last_time = None
    pzt_mean = 0.0
    pzt_stdev = 0.0

    h2o2_res = 0
    h2o2_shift = 0
    h2o2_adjust = 0
    h2o_y_eff = 1.0
    h2o_y_ave = 1.0
    h2o_amp = 0
    h2o_conc = 0
    h2o2_ppmv = 0
    vh2o2_ppmv = 0
    h2o2_amp = 0
    vh2o2_amp = 0

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
#d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=3.5)
d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

r = None

tstart = time.clock()
if (d["spectrumId"]==65) and (d["ngroups"]>4):
    initialize_Baseline()
    init[1000,5] = h2o_y_ave
    init[1000,2] = h2o_amp
    r = anH2O2[0](d,init,deps)
    ANALYSIS.append(r)
    h2o2_res = r["std_dev_res"]
    base0 = r["base",0]
    base1 = r["base",1]
    h2o2_amp = r[1001,2]
    h2o2_ppmv = 7.58*r[1001,2]
    #  Water corrections go here
    h2o2_ppmv += H2O2_off + H2O2_H1*h2o_amp + H2O2_H2*h2o_amp**2
    h2o2_ppmv += H2O2_Hconc*h2o_conc

elif (d["spectrumId"]==66) and (d["ngroups"]>4):
    initialize_Baseline()
    r = anH2O2[1](d,init,deps)
    ANALYSIS.append(r)

    if abs(r["base",3])<0.03 and (r[1000,2]>0.035 or r[1001,2]>0.015):
        r = anH2O2[2](d,init,deps)
        ANALYSIS.append(r)

    elif abs(r["base",3])>0.03 or (r[1000,2]<0.003 and r[1001,2]<0.015):
        r = anH2O2[3](d,init,deps)
        ANALYSIS.append(r)

    h2o2_res = r["std_dev_res"]
    base0 = r["base",0]
    base1 = r["base",1]
    h2o2_shift = h2o2_adjust = r["base",3]
    h2o_y_eff = r[1000,5]
    h2o_y_ave = initExpAverage(h2o_y_ave,h2o_y_eff,2,1,counter)
    counter += 1
    h2o_amp = r[1000,2]
    vh2o2_amp = r[1001,2]
    h2o_conc = 1.48*h2o_amp
    vh2o2_ppmv = 7.58*r[1001,2]
    h2o_conc += H2O_H2O2_conc*vh2o2_ppmv
    h2o_conc *= H2O_scale

cal = (d.subschemeId & 4096) != 0
if any(cal):
    pzt_mean = mean(d.pztValue[cal])
    pzt_stdev = std(d.pztValue[cal])

now = time.clock()
fit_time = now-tstart
if r != None:
    IgnoreThis = False
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]
else:
    IgnoreThis = True

if not IgnoreThis:
    RESULT = {"h2o2_ppmv":h2o2_ppmv,"h2o2_shift":h2o2_shift,"h2o2_adjust":h2o2_adjust,
              "h2o2_base":base0,"h2o2_slope":base1,"h2o2_amp":h2o2_amp,"h2o2_res":h2o2_res,
              "h2o_conc":h2o_conc,"h2o_amp":h2o_amp,"h2o_y_eff":h2o_y_eff,"h2o_y_ave":h2o_y_ave,
              "pzt_mean":pzt_mean,"pzt_std":pzt_stdev,"vh2o2_ppmv":vh2o2_ppmv,"vh2o2_amp":vh2o2_amp,
              "ngroups":d["ngroups"],"rds":d["datapoints"],
              "fit_time":fit_time,"interval":interval}
    RESULT.update(d.sensorDict)
    RESULT.update({"species":d["spectrumId"],"cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
              "das_temp":dasTemp})
