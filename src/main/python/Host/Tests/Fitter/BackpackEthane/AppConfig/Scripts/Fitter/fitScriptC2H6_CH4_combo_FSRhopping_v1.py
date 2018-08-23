#  Fit script for backpack methane + ethane analyzer development
#  Version 1 started 6 Jul 2016 by hoffnagle based on latest "Albatross" aka "Nomad" + G2000 ethane
#  2016 0824:  Major modification for pressure stabilized operation
#  2016 0831:  Added temperature calculation to the dependencies in the Galatry model for water at 5947 wvn
#  2016 0908:  Changed test for gaps in accumulated array for clustering to exclude first point

from numpy import angle, asarray, arange, argsort, array, concatenate, diff, exp, max, mean, median, pi, std, sqrt, digitize, polyfit, polyval, real, imag, round_
from numpy.linalg import solve
from collections import deque
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
    
def initialize_C2H6_Baseline():
    init["base",0] = C2H6_baseline_level
    init["base",1] = C2H6_baseline_slope
    init[1000,0] = C2H6_A0
    init[1000,1] = C2H6_Nu0
    init[1000,2] = C2H6_Per0
    init[1000,3] = C2H6_Phi0
    init[1001,0] = C2H6_A1
    init[1001,1] = C2H6_Nu1
    init[1001,2] = C2H6_Per1
    init[1001,3] = C2H6_Phi1

def initialize_H2O_dependencies():    
    deps.setDep((2,1),(1,1),0.259*exp(-264.245*Tfactor),0.0)
    deps.setDep((3,1),(1,1),0.0191*exp(833.211*Tfactor),0.0)
    deps.setDep((4,1),(1,1),0.0118*exp(1870.689*Tfactor),0.0)
    deps.setDep((6,1),(1,1),0.0022*exp(-962.849*Tfactor),0.0)
    
def cluster(x,d):
    """Given a set of points x, and a maximum diameter d, partition
    x into clusters of size no larger than d"""
    N = len(x)
    p = argsort(x)
    xs = x[p]
    groups = []
    
    
    # For each point in x, compute the number of points in the set lying 
    #  in the range [x,x+d]
    left = arange(N,dtype=int)
    
    while len(left)>0:
        g = digitize(xs[left]+d,xs[left])-arange(len(left))
        which, score = [], []
        for i,j in enumerate(digitize(xs[left]-d,xs[left])):
            score.append(g[j:i+1].max())
            which.append(j + g[j:i+1].argmax())
        sel = asarray(score).argmax()
        groups.append((left[which[sel]],g[sel]))
        #print groups
        left = concatenate((left[:which[sel]],left[which[sel]+g[sel]:]))
        #print left        
    clusters = [p[s:s+n] for s,n in groups]
    xmeans = asarray([x[c].mean() for c in clusters])
    return [clusters[q] for q in argsort(xmeans)]
    
def expAverage(xavg,x,n,dxMax):
    if xavg is None: return x
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)<dxMax: return y
    elif y>xavg: return xavg+dxMax
    else: return xavg-dxMax

if INIT:
    fname = os.path.join(BASEPATH,r"./Ethane/spectral library 5950 high pressure v1_1.ini")
    loadSpectralLibrary(fname)
    spectrParams = getInstrParams(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_FSR.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini")
    cavityParams = getInstrParams(fname)
    fsr_cal =  cavityParams['AUTOCAL']['CAVITY_FSR']
    
    maxIlas = 1000                   #  max number of laser currents to send to the cluster algorithm
    ch4_count = 0                    #  keeps track of additions to buffer for clustering algorithm
    c2h6_count = 0
    clusterCount = 8                 #  Number of spectra to add to buffer before invoking clustering algorithm
    Ich4 = deque()
    Pch4 = deque()
    Ic2h6 = deque()
    Pc2h6 = deque()
    ch4_coef = [0,0,0,0]
    c2h6_coef = [0,0,0,0]
    ch4_offset = 0
    c2h6_offset = 0
    ch4_fineLaserCurrent = 0.0
    c2h6_fineLaserCurrent = 0.0
    
    
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
    
    C2H6_baseline_level = instrParams['C2H6_Baseline_level']
    C2H6_baseline_slope = instrParams['C2H6_Baseline_slope']
    C2H6_A0 = instrParams['C2H6_Sine0_ampl']
    C2H6_Nu0 = instrParams['C2H6_Sine0_freq']
    C2H6_Per0 = instrParams['C2H6_Sine0_period']
    C2H6_Phi0 = instrParams['C2H6_Sine0_phase']
    C2H6_A1 = instrParams['C2H6_Sine1_ampl']
    C2H6_Nu1 = instrParams['C2H6_Sine1_freq']
    C2H6_Per1 = instrParams['C2H6_Sine1_period']
    C2H6_Phi1 = instrParams['C2H6_Sine1_phase']
       
    y1_lib = spectrParams['peak1']['y']
    
    center10 = spectrParams['peak10']['center']
    center31 = spectrParams['peak31']['center']
    y10lib = spectrParams['peak10']['y']
    y31lib = spectrParams['peak31']['y']

    ch4_freq_locked = 0
    ch4_peakPoints = 4
    ch4_pointsInRange = 50
    ch4_base = CH4_baseline_level
    ch4_slope = CH4_baseline_slope
    ch4_res = 0
    ch4_conc_raw = 0
    str10 = 0
    str10_norm = 0
    peak10 = 0
    y10 = 4.517
    h2o_conc_raw = 0
    str31 = 0
    peak31 = 0
    y31 = 7.0
    ch4_shift = 1.0
    ch4_fit_time = 0
    ch4_interval = 0
    ch4_gaps = 0
    ch4_max_gap = 0
    ch4_max_loss = 0.0
    ch4_dImin = 0.0
    ch4_start = 5
    goodCH4 = 1
    
    shift31 = 0
    
    c2h6_freq_locked = 0
    c2h6_peakPoints = 4
    c2h6_pointsInRange = 50
    c2h6_base = C2H6_baseline_level
    c2h6_slope = C2H6_baseline_slope
    c2h6_res = 0
    h2o_peak = 0
    str_1 = 0
    y_h2o = 0
    vy_h2o = 0
    h2o_from_c2h6 = 0
    ch4_from_c2h6 = 0.0001
    c2h6_conc = 0
    c2ratio = 0
    c2h6_shift = 1.0
    c2h6_fit_time = 0
    c2h6_gaps = 0
    c2h6_max_gap = 0
    c2h6_max_loss = 0.0
    c2h6_dImin = 0.0
    c2h6_start = 5
    goodC2H6 = 1    
    
    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFXDS/ch4+h2o+co2_6047_VCVY.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFXDS/ch4+h2o+co2_6047_VCFY31_v1_2.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFXDS/ch4+h2o+co2_6047_VCFY_v1_2.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFXDS/ch4_noh2o_6047_VCFY.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFXDS/ch4+h2o+co2_6047_FCFY_v1_2.ini")))
 
    anC2H6 = []
    anC2H6.append(Analysis(os.path.join(BASEPATH,r"./Ethane/c2h6+ch4+h2o_v2.ini")))
    anC2H6.append(Analysis(os.path.join(BASEPATH,r"./Ethane/c2h6+ch4_FY_v1_1.ini")))
    anC2H6.append(Analysis(os.path.join(BASEPATH,r"./Ethane/c2h6+ch4+h2o_FY_v2_1.ini")))

    last_time = None
    ignore = 5
    last_ch4_shift = 1.0
    last_c2h6_shift = 1.0

tstart = time.clock()
init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
msg = ""
P = d["cavitypressure"]
T = d["cavitytemperature"]
TK = T + 273.15
fsr = fsr_cal/(1.0 + 0.000247*(P - 140.0)/760.0)               #  Correct fsr for index of air, for high pressure operation

if d["spectrumId"] in [23,24]:
    #  New FSR assignment code starts here
    Ifine = asarray(d.fineLaserCurrent,float)
    Ich4.extend(Ifine)
    Pressure = asarray(d.cavityPressure,float)
    Pch4.extend(Pressure)
    while (len(Ich4) > maxIlas):
        Ich4.popleft()
        Pch4.popleft()
    ch4_count += 1
    
    # Calculate transform if there are enough points and clustered spectra are clean
    if (len(Ich4) == maxIlas):
        if (ch4_count % clusterCount == 0):
            ch4_count = 0
            Ilong = array(Ich4)
            clusters = cluster(Ilong,300)
            Ic = array([Ilong[c].mean() for c in clusters])
            #print "%f %f" % (min(diff(Ic)),max(diff(Ic)))
            if ch4_start:
                ch4_dImin = min(diff(Ic))
                ch4_start -= 1
            xc = Ic/65536.0 - 0.5
            cindex = array(range(len(xc)))
            DP = max(Pch4)-min(Pch4)
            good_cluster = ((ch4_max_loss < 5000) or (ch4_peakPoints > 0 and ch4_max_gap < 6)) and (max(diff(Ic[1:])) < 2*ch4_dImin) and (DP < 0.2)
            if good_cluster or ch4_start:
                ch4_coef = polyfit(xc, cindex, 3)
                ch4_offset = ch4_coef[3] - int(ch4_coef[3])
                ch4_dImin = expAverage(ch4_dImin,min(diff(Ic)),100,10)
            if ch4_offset > 0.5:
                ch4_offset -= 1.0            
        xfine = Ifine/65536.0 - 0.5        
        fsr_indices = polyval([ch4_coef[0],ch4_coef[1],ch4_coef[2], ch4_offset],xfine)
        fsr_remainder = fsr_indices - round_(fsr_indices)
        #print (mean(fsr_remainder), std(fsr_remainder))
        if (not ch4_peakPoints) or (ch4_max_gap > 5):
            ch4_offset -= mean(fsr_remainder)    #  To correct for drift when methane conc very high
        fsr_indices = round_(fsr_indices)
        #  New FSR assignment code ends here
        d.pztValue = -fsr_indices
        centerMode = (d.pztValue == 0)
        if sum(centerMode) > 0:
            ch4_fineLaserCurrent = mean(Ifine[centerMode])
        else:
            ch4_fineLaserCurrent = 0.0
        for i in range(len(d.pztValue)):
            if abs(fsr_remainder[i]) > 0.25:
                d.uncorrectedAbsorbance[i] = 0
                
        d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=30.0)
        d.sparse(maxPoints=200,width=0.5,height=100000.0,xColumn="pztValue",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
        d.evaluateGroups(["pztValue","uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["pztValue"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
        ch4_max_loss = max(d.fitData["loss"])
        if len(d.fitData["freq"])>1:
            ch4_gaps = sum(diff(d.fitData["freq"])-1)
            ch4_max_gap = max(diff(d.fitData["freq"])-1)
        d.fitData["freq"] = 6046.95+(d.fitData["freq"]+ch4_offset)*fsr
        
        inRange = (d.fitData["freq"] >= 6046.55) & (d.fitData["freq"] <= 6047.35)
        ch4_pointsInRange = sum(inRange)

        center11 = center10 - 0.02172 + 5.8e-6*P*(318.15/TK)
        init[11,"center"] = center11
        init[12,"center"] = center11 + 0.0093
        init[23,"strength"] = 0.0#0295*str40
        init[31,"center"] = center31 + 1.32e-5*(P-700)*(318.15/TK)
        initialize_CH4_Baseline()
        goodCH4 = 1

        r = None

        if ch4_pointsInRange < 8:
            ignore += 1
            
        if ignore:
            ignore -= 1

        else:
            if abs(last_ch4_shift) > 0.5:
                res_min = 10000
                ch4_freq_locked = 0
                for i in range(11):
                    init["base",3] = 0.1*i-0.5
                    r = anCH4[3](d,init,deps)
                    ANALYSIS.append(r)
                    if r["std_dev_res"] < res_min:
                        res_min = r["std_dev_res"]
                        ch4_shift = r["base",3]
                init["base",3] = ch4_shift
                r = anCH4[0](d,init,deps)
                ANALYSIS.append(r)
                peakPoint = abs(d.fitData["freq"] + r["base",3] - 6046.95) < 0.04
                ch4_peakPoints = sum(peakPoint)
                shift31 = r[31,"center"] - center31
            elif abs(last_ch4_shift) > 0.05:
                ch4_freq_locked = 0
                init["base",3] = last_ch4_shift
                r = anCH4[0](d,init,deps)
                ANALYSIS.append(r)
                y31ratio = r[31,"y"]/(y31lib*P)
                if y31ratio > 1.5 or y31ratio < 0.6 or r[31,"peak"] < 2 or r[31,"peak"] > 300:
                    r = anCH4[1](d,init,deps)  
                    ANALYSIS.append(r)
                peakPoint = abs(d.fitData["freq"] + r["base",3] - 6046.95) < 0.04
                ch4_peakPoints = sum(peakPoint)
                shift31 = r[31,"center"] - center31
                if not ch4_peakPoints:
                    y10nominal = y10lib*P
                    y31nominal = y31lib*P
                    init[10,"y"] = y10nominal
                    init[31,"y"] = y31nominal
                    r = anCH4[2](d,init,deps)  
                    ANALYSIS.append(r)
                if r[10,"peak"] < 10 and r[31,"peak"] < 10:
                    y10nominal = y10lib*P*(318.15/TK)**1.25
                    init[10,"y"] = y10nominal
                    init[31,"y"] = y31nominal
                    r = anCH4[4](d,init,deps)  
                    ANALYSIS.append(r)
            else:
                ch4_freq_locked = 1
                r = anCH4[0](d,init,deps)  
                ANALYSIS.append(r)
                y31nominal = y31lib*P*(1.0 + 5.93e-5*str31)*(318.15/TK)**1.19
                y31ratio = r[31,"y"]/y31nominal
                if y31ratio > 1.5 or y31ratio < 0.6 or r[31,"peak"] < 10 or r[31,"peak"] > 300:
                    init[31,"y"] = y31nominal
                    r = anCH4[1](d,init,deps)  
                    ANALYSIS.append(r)
                peakPoint = abs(d.fitData["freq"] + r["base",3] - 6046.95) < 0.04
                ch4_peakPoints = sum(peakPoint)
                shift31 = r[31,"center"] - center31
                if (not ch4_peakPoints) or (ch4_max_gap > 5):
                    y10nominal = y10lib*P*(318.15/TK)**1.25
                    init[10,"y"] = y10nominal
                    init[31,"y"] = y31nominal
                    r = anCH4[2](d,init,deps)  
                    ANALYSIS.append(r)
                if r[10,"peak"] < 10 and r[31,"peak"] < 10:
                    y10nominal = y10lib*P*(318.15/TK)**1.25
                    init[10,"y"] = y10nominal
                    init[31,"y"] = y31nominal
                    r = anCH4[4](d,init,deps)  
                    ANALYSIS.append(r)
            ch4_shift = r["base",3]
            str10 = r[10,"strength"]
            peak10 = r[10,"peak"]
            y10 = r[10,"y"]
            str10_norm = str10/y10
            str31 = r[31,"strength"]
            peak31 = r[31,"peak"]
            y31 = r[31,"y"]
            ch4_base = r["base",0]
            ch4_slope = r["base",1]
            ch4_res = r["std_dev_res"]
            
            ch4_conc_raw = 0.548*(str10/P)
            h2o_conc_raw = 2.035*(str31/P)
            
            y10nominal = y10lib*P*(1.0 + 3.65e-6*str31)*(318.15/TK)**1.25
            y31nominal = y31lib*P*(1.0 + 5.93e-5*str31)*(318.15/TK)**1.19
            if y10/y10nominal > 1.5 or y10/y10nominal < 0.6:
                msg = "Bad y-parameter for CH4"
                goodCH4 = 0
            if ch4_base < 500:
                msg = "Bad CH4 baseline"
                goodCH4 = 0
            if abs(ch4_shift) > 1.0:
                msg = "CH4 shift > 1 wvn"
                good = 0
            if ch4_res > 150:
                msg = "CH4 residual > 100 ppb/cm"
                goodCH4 = 0
            
            now = time.clock()
            ch4_fit_time = now-tstart
            if last_time != None:
                ch4_interval = r["time"]-last_time
            else:
                ch4_interval = 0
            last_time = r["time"]

        
if d["spectrumId"] == 170:
    #  New FSR assignment code starts here
    Ifine = asarray(d.fineLaserCurrent,float)
    Ic2h6.extend(Ifine)
    Pressure = asarray(d.cavityPressure,float)
    Pc2h6.extend(Pressure)
    while (len(Ic2h6) > maxIlas):
        Ic2h6.popleft()
        Pc2h6.popleft()
    c2h6_count += 1
    
    # Calculate transform if there are enough points and clustered spectra are clean
    if (len(Ic2h6) == maxIlas):
        if (c2h6_count % clusterCount == 0):
            c2h6_count = 0
            Ilong = array(Ic2h6)
            clusters = cluster(Ilong,300)
            Ic = array([Ilong[c].mean() for c in clusters])
            if c2h6_start:
                c2h6_dImin = min(diff(Ic))
                c2h6_start -= 1
            xc = Ic/65536.0 - 0.5
            cindex = array(range(len(xc)))
            DP = max(Pc2h6)-min(Pc2h6)
            good_cluster = ((c2h6_max_loss < 5000) or (c2h6_peakPoints > 0 and c2h6_max_gap < 6)) and (max(diff(Ic[1:])) < 2*c2h6_dImin) and (DP < 0.2)
            if good_cluster or c2h6_start:
                c2h6_coef = polyfit(xc, cindex, 3)
                c2h6_offset = c2h6_coef[3] - int(c2h6_coef[3])
                c2h6_dImin = expAverage(c2h6_dImin,min(diff(Ic)),100,10)
            if c2h6_offset > 0.5:
                c2h6_offset -= 1.0
        xfine = Ifine/65536.0 - 0.5        
        fsr_indices = polyval([c2h6_coef[0],c2h6_coef[1],c2h6_coef[2],c2h6_offset],xfine)
        fsr_remainder = fsr_indices - round_(fsr_indices)
        #print good_cluster
        #print (min(fsr_remainder), max(fsr_remainder), mean(fsr_remainder), std(fsr_remainder))
        fsr_indices = round_(fsr_indices)
        #  New FSR assignment code ends here
        d.pztValue = -fsr_indices
        centerMode = (d.pztValue == 0)
        if sum(centerMode) > 0:
            c2h6_fineLaserCurrent = mean(Ifine[centerMode])
        else:
            c2h6_fineLaserCurrent = 0.0
        for i in range(len(d.pztValue)):
            if abs(fsr_remainder[i]) > 0.25:
                d.uncorrectedAbsorbance[i] = 0

        d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=30.0)
        d.sparse(maxPoints=200,width=0.5,height=100000.0,xColumn="pztValue",yColumn="uncorrectedAbsorbance",outlierThreshold=4.0)
        d.evaluateGroups(["pztValue","uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["pztValue"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
        c2h6_max_loss = max(d.fitData["loss"])
        if len(d.fitData["freq"])>1:
            c2h6_gaps = sum(diff(d.fitData["freq"])-1)
            c2h6_max_gap = max(diff(d.fitData["freq"])-1)
        d.fitData["freq"] = 5946.65+(d.fitData["freq"]+c2h6_offset)*fsr
        
        inRange = (d.fitData["freq"] >= 5946.4) & (d.fitData["freq"] <= 5947.0)
        c2h6_pointsInRange = sum(inRange)

        P = d["cavitypressure"]
        T = d["cavitytemperature"]
        Tfactor = 0.003143 - 1.0/(T + 273.15)
        initialize_C2H6_Baseline()
        init[1002,5] = init[1003,5] = T-10.0
        y1_nominal = P*y1_lib
        goodC2H6 = 1

        r = None

        if c2h6_pointsInRange < 8:
            ignore += 1
            
        if ignore:
            ignore -= 1

        else:
            if abs(last_c2h6_shift) > 0.5:
                res_min = 10000
                c2h6_freq_locked = 0
                initialize_H2O_dependencies()
                for i in range(11):
                    init["base",3] = 0.1*i-0.5
                    r = anC2H6[0](d,init,deps)
                    ANALYSIS.append(r)
                    vy_h2o = r[1,"y"]
                    if r["std_dev_res"] < res_min:
                        res_min = r["std_dev_res"]
                        c2h6_shift = r["base",3]
                init["base",3] = c2h6_shift
                r = anC2H6[0](d,init,deps)
                ANALYSIS.append(r)
                peakPoint = abs(d.fitData["freq"] + r["base",3] - 5946.7388) < 0.04
                c2h6_peakPoints = sum(peakPoint)
            elif abs(last_c2h6_shift) > 0.05:
                c2h6_freq_locked = 0
                init["base",3] = last_c2h6_shift
                initialize_H2O_dependencies()
                r = anC2H6[0](d,init,deps)
                ANALYSIS.append(r)
                vy_h2o = r[1,"y"]
                
                if r[1002,2] > 40:
                    deps = Dependencies()
                    initialize_C2H6_Baseline()
                    r = anC2H6[1](d,init,deps)
                    ANALYSIS.append(r)
                
                elif r[1,"peak"] < 5 or r[1,"peak"] > 2000 or abs(r[1,"y"] - y1_nominal) > 0.5 or r[1002,2] > 10:
                    initialize_H2O_dependencies()
                    r = anC2H6[2](d,init,deps)
                    ANALYSIS.append(r)
        
                peakPoint = abs(d.fitData["freq"] + r["base",3] - 5946.7388) < 0.04
                c2h6_peakPoints = sum(peakPoint)                
            else:
                c2h6_freq_locked = 1
                initialize_H2O_dependencies()
                r = anC2H6[0](d,init,deps)  
                ANALYSIS.append(r)
                vy_h2o = r[1,"y"]
                
                if r[1002,2] > 40:
                    deps = Dependencies()
                    initialize_C2H6_Baseline()
                    r = anC2H6[1](d,init,deps)
                    ANALYSIS.append(r)
                
                elif r[1,"peak"] < 5 or r[1,"peak"] > 2000 or abs(r[1,"y"] - y1_nominal) > 0.5 or r[1002,2] > 10:
                    initialize_H2O_dependencies()
                    r = anC2H6[2](d,init,deps)
                    ANALYSIS.append(r)                
                
                peakPoint = abs(d.fitData["freq"] + r["base",3] - 5946.7388) < 0.04
                c2h6_peakPoints = sum(peakPoint)                
            c2h6_shift = r["base",3]
            c2h6_base = r["base",0]
            c2h6_slope = r["base",1]
            c2h6_res = r["std_dev_res"]

            try:
                y_h2o = r[1,"y"]
                h2o_peak = r[1,"peak"]
                str_1 = r[1,"strength"]
            except:
                y_h2o = y1_nominal
                h2o_peak = 0.0
                str_1 = 0.0
            
            h2o_from_c2h6 = 8.52*str_1
            c2h6_conc = 10*r[1003,2]
            ch4_from_c2h6 = 100*r[1002,2]
            
            c2ratio = c2h6_conc/ch4_from_c2h6
            
            if c2h6_base < 500:
                msg = "Bad baseline"
                goodC2H6 = 0
            if abs(c2h6_shift) > 1.0:
                msg = "Shift > 1 wvn"
                goodC2H6 = 0
            if c2h6_res > 500:
                msg = "C2H6 residual > 500 ppb/cm"
                goodC2H6 = 0
            
            now = time.clock()
            c2h6_fit_time = now-tstart
                
if (len(Ich4) == maxIlas) or (len(Ic2h6) == maxIlas):
    last_ch4_shift = ch4_shift
    last_c2h6_shift = c2h6_shift
    #print d.filterHistory
    if goodC2H6 and goodCH4:
        RESULT = {"ch4_res":ch4_res,"ch4_conc_raw":ch4_conc_raw,"goodCH4":goodCH4,
                  "str10":str10,"peak_10":peak10,"y10":y10,"str10_norm":str10_norm,
                  "ch4_base":ch4_base,"ch4_slope":ch4_slope,"ch4_gaps":ch4_gaps,"ch4_max_gap":ch4_max_gap,
                  "ch4_shift":ch4_shift,"ch4_freq_locked":ch4_freq_locked,"ch4_dImin":ch4_dImin,
                  "ch4_peakPoints":ch4_peakPoints,"shift31":shift31,
                  "ch4_fit_time":ch4_fit_time,"ch4_interval":ch4_interval,"ch4_pointsInRange":ch4_pointsInRange,
                  "h2o_conc_raw":h2o_conc_raw,"str31":str31,"peak31":peak31,"y31":y31,
                  "ch4_i2f_cubic":ch4_coef[0],"ch4_i2f_quad":ch4_coef[1],"ch4_i2f_lin":ch4_coef[2],"ch4_i2f_offset":ch4_offset,
                  "h2o_peak":h2o_peak,"str_1":str_1,"y_h2o":y_h2o,"vy_h2o":vy_h2o,
                  "h2o_from_c2h6":h2o_from_c2h6,"ch4_from_c2h6":ch4_from_c2h6,"c2h6_conc":c2h6_conc,"c2ratio":c2ratio,
                  "c2h6_res":c2h6_res,"goodC2H6":goodC2H6,
                  "c2h6_base":c2h6_base,"c2h6_slope":c2h6_slope,"c2h6_gaps":c2h6_gaps,"c2h6_max_gap":c2h6_max_gap,
                  "c2h6_shift":c2h6_shift,"c2h6_freq_locked":c2h6_freq_locked,
                  "c2h6_peakPoints":c2h6_peakPoints,"c2h6_dImin":c2h6_dImin,
                  "c2h6_fit_time":c2h6_fit_time,"c2h6_pointsInRange":c2h6_pointsInRange,
                  "c2h6_i2f_cubic":c2h6_coef[0],"c2h6_i2f_quad":c2h6_coef[1],"c2h6_i2f_lin":c2h6_coef[2],"c2h6_i2f_offset":c2h6_offset,
                  "ch4_fineLaserCurrent":ch4_fineLaserCurrent,"c2h6_fineLaserCurrent":c2h6_fineLaserCurrent,
                  "groups":d["ngroups"],"rds":d["datapoints"],"spectrumId":d["spectrumId"]
                  }
        RESULT.update(d.sensorDict)
        RESULT.update({"cavity_pressure":P,"cavity_temperature":T})
    else:
        print msg      