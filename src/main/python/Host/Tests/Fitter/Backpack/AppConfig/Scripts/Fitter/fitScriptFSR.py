#  Fit script for low cost methane analyzer development
#  Version to explore use of FSR scale and clustering algorithm as sole frequency reference
#  Version 1 started 22 Sep 2011 by hoffnagle
#  First try never went anywhere; restart 4 Aug 2014
#  Major modification to use Sze's new FSR assigning algorithm
#  2014 0821:  Start work on a new fitter to use the strong methane line at 6047 wvn

from numpy import angle, asarray, arange, diff, exp, max, mean, median, pi, std, sqrt, digitize, polyfit, polyval, real, imag, round_
from numpy.linalg import solve
import os.path
import time

def initialize_CH4_Baseline():
    init["base",0] = CH4_baseline_level
    init["base",1] = CH4_baseline_slope
    init[1000,0] = CH4_A0
    init[1000,1] = CH4_Nu0
    init[1000,2] = CH4_Per0
    init[1000,3] = CH4_Phi0
    init[1001,0] = CH4_A1
    init[1001,1] = CH4_Nu1
    init[1001,2] = CH4_Per1
    init[1001,3] = CH4_Phi1

if INIT:
    fname = os.path.join(BASEPATH,r"./CH4/spectral library v2_1.ini")
    loadSpectralLibrary(fname)
    spectrParams = getInstrParams(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_FSR.ini")
    instrParams = getInstrParams(fname)
    
    fsr = 0.02063087
    pcoef = asarray([11.45,74.69])
    frac = 0
    twist = 0
    
    CH4_baseline_level = instrParams['CH4_Baseline_level']
    CH4_baseline_slope = instrParams['CH4_Baseline_slope']
    CH4_A0 = instrParams['CH4_Sine0_ampl']
    CH4_Nu0 = instrParams['CH4_Sine0_freq']
    CH4_Per0 = instrParams['CH4_Sine0_period']
    CH4_Phi0 = instrParams['CH4_Sine0_phase']
    CH4_A1 = instrParams['CH4_Sine1_ampl']
    CH4_Nu1 = instrParams['CH4_Sine1_freq']
    CH4_Per1 = instrParams['CH4_Sine1_period']
    CH4_Phi1 = instrParams['CH4_Sine1_phase']
    
    center10 = spectrParams['peak10']['center']
    y10lib = spectrParams['peak10']['y']
    y31lib = spectrParams['peak31']['y']
    
    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CH4/ch4+h2o_6047_VCVY.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CH4/ch4+h2o_6047_VCFY31.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CH4/ch4_noh2o_6047_VCFY.ini")))
    
    last_time = None
    ignore = 5
    last_shift = 1.0

tstart = time.clock()
init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

if d["spectrumId"] in [23,24]:
    #  New FSR assignment code starts here
    Ifine = asarray(d.fineLaserCurrent,float)/65536.0 - 0.5
    theta = 2*pi*polyval([pcoef[0],pcoef[1],0], Ifine)
    eit = exp(1j*theta)
    s = sum(eit)
    sI = sum(Ifine*eit)
    sI2 = sum((Ifine**2)*eit)

    # Calculate first derivative
    grad_ana = 4*pi*asarray([imag(s)*real(sI2)-real(s)*imag(sI2), 
                             imag(s)*real(sI)-real(s)*imag(sI)])
    dp = 5e-8*grad_ana
    pcoef = pcoef + dp

    fsr_indices = polyval([pcoef[0],pcoef[1],0],Ifine)
    rot = sum(exp(2j*pi*fsr_indices))
    rot = rot/abs(rot)
    twist = 0.0*twist + 1.0*rot # Slowly varying angle
    fracNew = angle(twist)/(2*pi)
    frac = fracNew + round(frac-fracNew)
    fsr_indices = polyval([pcoef[0],pcoef[1],-frac],Ifine)
    fsr_indices = round_(fsr_indices)
    #  New FSR assignment code ends here
    d.pztValue = -fsr_indices

    d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=15.0)
    d.sparse(maxPoints=200,width=0.5,height=100000.0,xColumn="pztValue",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
    d.evaluateGroups(["pztValue","uncorrectedAbsorbance"])
    d.defineFitData(freq=d.groupMeans["pztValue"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
    offset = frac
    d.fitData["freq"] = 6046.95+(d.fitData["freq"]-offset)*fsr
    
    inRange = (d.fitData["freq"] >= 6046.55) & (d.fitData["freq"] <= 6047.35)
    pointsInRange = sum(inRange)

    P = d["cavitypressure"]
    T = d["cavitytemperature"]
    center11 = center10 - 0.02172 + 5.8e-6*P
    init[11,"center"] = center11
    init[12,"center"] = center11 + 0.0093
    initialize_CH4_Baseline()
    good = True

    r = None

    if pointsInRange < 8:
        ignore += 1
        
    if ignore:
        ignore -= 1

    else:
        if abs(last_shift) > 0.5:
            res_min = 10000
            freq_locked = 0
            for i in range(11):
                init["base",3] = 0.1*i-0.5
                r = anCH4[0](d,init,deps)
                ANALYSIS.append(r)
                if r["std_dev_res"] < res_min:
                    res_min = r["std_dev_res"]
                    ch4_shift = r["base",3]
            init["base",3] = ch4_shift
            r = anCH4[0](d,init,deps)
            ANALYSIS.append(r)
            peakPoint = abs(d.fitData["freq"] + r["base",3] - 6046.95) < 0.04
            peakPoints = sum(peakPoint)
        elif abs(last_shift) > 0.05:
            freq_locked = 0
            init["base",3] = last_shift
            r = anCH4[0](d,init,deps)
            ANALYSIS.append(r)
            y31ratio = r[31,"y"]/(y31lib*P)
            if y31ratio > 1.5 or y31ratio < 0.6 or r[31,"peak"] < -5 or r[31,"peak"] > 300:
                r = anCH4[1](d,init,deps)  
                ANALYSIS.append(r)
            peakPoint = abs(d.fitData["freq"] + r["base",3] - 6046.95) < 0.04
            peakPoints = sum(peakPoint)
            if not peakPoints:
                y10nominal = y10lib*P
                y31nominal = y31lib*P
                init[10,"y"] = y10nominal
                init[31,"y"] = y31nominal
                r = anCH4[2](d,init,deps)  
                ANALYSIS.append(r)
        else:
            freq_locked = 1
            r = anCH4[0](d,init,deps)  
            ANALYSIS.append(r)
            y31ratio = r[31,"y"]/(y31lib*P)
            if y31ratio > 1.5 or y31ratio < 0.6 or r[31,"peak"] < -5 or r[31,"peak"] > 300:
                r = anCH4[1](d,init,deps)  
                ANALYSIS.append(r)
            peakPoint = abs(d.fitData["freq"] + r["base",3] - 6046.95) < 0.04
            peakPoints = sum(peakPoint)
            if not peakPoints:
                y10nominal = y10lib*P
                y31nominal = y31lib*P
                init[10,"y"] = y10nominal
                init[31,"y"] = y31nominal
                r = anCH4[2](d,init,deps)  
                ANALYSIS.append(r)
        ch4_shift = r["base",3]
        str10 = r[10,"strength"]
        peak10 = r[10,"peak"]
        y10 = r[10,"y"]
        str10_norm = str10/y10
        str31 = r[31,"strength"]
        peak31 = r[31,"peak"]
        y31 = r[31,"y"]
        base = r["base",0]
        slope = r["base",1]
        ch4_res = r["std_dev_res"]
        
        ch4_conc_raw = 0.548*(str10/P)
        h2o_conc_raw = 1.523*(str31/P)
        
        y10nominal = y10lib*P*(1.0 + 7.56e-6*r[31,"strength"])
        if y10/y10nominal > 1.6 or y10/y10nominal < 0.6:
            msg = "Bad y-parameter"
            good = False
        if base < 500:
            msg = "Bad baseline"
            good = False
        if abs(ch4_shift) > 1.0:
            msg = "Shift > 1 wvn"
            good = False
        if ch4_res > 2000:
            msg = "Residual > 2000 ppb/cm"
            good = False
        
        now = time.clock()
        fit_time = now-tstart
        if last_time != None:
            interval = r["time"]-last_time
        else:
            interval = 0
        last_time = r["time"]

        if good:
            last_shift = ch4_shift
            RESULT = {"ch4_res":ch4_res,"ch4_conc_raw":ch4_conc_raw,
                      "str10":str10,"peak_10":peak10,"y10":y10,"str10_norm":str10_norm,
                      "ch4_base":base,"ch4_slope":slope,
                      "ch4_shift":ch4_shift,"freq_locked":freq_locked,
                      "ch4_groups":d["ngroups"],"ch4_rds":d["datapoints"],"peakPoints":peakPoints,
                      "ch4_fit_time":fit_time,"ch4_interval":interval,"pointsInRange":pointsInRange,
                      "h2o_conc_raw":h2o_conc_raw,"str31":str31,"peak31":peak31,"y31":y31,
                      "i2f_quad":pcoef[0],"i2f_lin":pcoef[1],"i2f_offset":-frac,
                      "spectrumId":d["spectrumId"]
                      }
            RESULT.update(d.sensorDict)
            RESULT.update({"cavity_pressure":P,"cavity_temperature":T})
        else:
            print msg      