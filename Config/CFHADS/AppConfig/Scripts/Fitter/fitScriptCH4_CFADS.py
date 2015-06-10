#  Fit script for standard CFADS methane fitter (spectrum id = 25) as of June 2010
#  Translated from R:\LV8_Development\rella\Releases\batch file inis\CFADS-xx\2010 0528\Release C1.56 F0.73\Cv1_56 Fv0_73 2010 0528.txt
#  by hoffnagle on 22 June 2010
#  10 Aug 2010:  changed ch4_shift and ch4_adjust definitions to match other fitter naming conventions, i.e. shift is from variable center fit
#                regardless of line strength; adjust is conditional on line strength and abs(shift)  -- hoffnagle
#  2010-09-03:  Added reporting of PZT mean and standard deviation for calibration points (hoffnagle)
#  2010-12-06:  Changed condition on minimum number of data groups from 4 to 14 (hoffnagle).  Note that this
#               is appropriate to normal CFADS but NOT CFADS flux.
#  2011-03-16:  Aadpted to super-flux by changing spectral library to 60 C version

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

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library 60C_CFADS-xx_v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 v2_1 2008 0304.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC VY v2_0 2008 0304.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC FY v2_0 2008 0304.ini")))

    base_avg = 800
    counter = -25
    last_time = None
    pzt_mean = 0.0
    pzt_stdev = 0.0

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
if (d["spectrumId"]==25) and (d["ngroups"]>13):
    r = anCH4[0](d,init,deps)
    ANALYSIS.append(r)
    ch4_vy = r[1002,5]
    vch4_conc_ppmv = 10*r[1002,2]
    ch4_shift = r["base",3]
#  Polishing step with fixed center, variable y if line is strong and shift is small
    if (r[1002,2] > 0.005) and (abs(ch4_shift) <= 0.07):
        init["base",3] = ch4_shift
        ch4_adjust = ch4_shift
        r = anCH4[1](d,init,deps)
        ANALYSIS.append(r)
#  Polishing step with fixed center and y if line is weak or shift is large
    else:
        init["base",3] = 0.0
        ch4_adjust = 0.0
        init[1002,5] = 1.08
        r = anCH4[2](d,init,deps)
        ANALYSIS.append(r)

    ch4_amp = r[1002,2]
    ch4_conc_raw = 10*r[1002,2]
    ch4_y = r[1002,5]
    base = r["base",0]
    ch4_adjconc_ppmv = ch4_y*ch4_conc_raw*(140.0/P)
    splinemax = r[1002,"peak"]
    ch4_peakvalue = splinemax+base
    base_avg  = initExpAverage(base_avg,base,10,100,counter)
    ch4_peak_baseavg = ch4_peakvalue-base_avg
    ch4_conc_ppmv_final = ch4_peak_baseavg/216.3
    ch4_res = r["std_dev_res"]

    now = time.clock()
    fit_time = now-tstart
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]

    counter += 1

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = mean(d.pztValue[cal])
        pzt_stdev = std(d.pztValue[cal])

    RESULT = {"ch4_res":ch4_res,"vch4_conc_ppmv":vch4_conc_ppmv,"ch4_vy":ch4_vy,
              "ch4_adjconc_ppmv":ch4_adjconc_ppmv,"ch4_conc_ppmv_final":ch4_conc_ppmv_final,
              "ch4_base":base,"ch4_base_avg":base_avg,"ch4_splinemax":splinemax,
              "ch4_tuner_mean": tunerMean, "ch4_tuner_std": std(d.tunerValue),
              "ch4_pzt_mean": pzt_mean, "ch4_pzt_std": pzt_stdev,
              "ch4_shift":ch4_shift,"ch4_adjust":ch4_adjust,"ch4_y":ch4_y,
              "ch4_groups":d["ngroups"],"ch4_rds":d["datapoints"],
              "ch4_fit_time":fit_time,"ch4_interval":interval}
    RESULT.update(d.sensorDict)
    RESULT.update({"species":2,"cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
              "das_temp":dasTemp})

