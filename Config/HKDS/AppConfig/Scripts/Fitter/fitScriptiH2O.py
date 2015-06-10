#  Fit script for isotopic water lines at 7200 wavenumbers
#  2011 0503:  Changed spectral library to 50 Torr, 80 C version
#  2011 0503:  Ugly nomenclaure is from the installation on 740-HBDS2171
#  2011 0504:  Added RD statistics for development.  Tweaked line params in library & fit ini, excise points at jct 18/16
#  2001 0505:  V2.1 adds second-stage fit to peaks only with fixed centers and y-parameters from step 1 concentration
#  2001 0511:  V2.2 adds offset and quadratic correction to Galatry peaks based on concentration step test of 10 May
#                     Note that all y parameters and corrections are for AIR only so far.  N2 remains to be done!
#  2011 0617:  V3.1 removes RD statistics and adds hydrocarbon splines.
#  2011 0623:  V3.2 adds correction to the methane concentration to account for water cross-talk
#  2011 0801:  V4.1 (provisional) adds fitter configuration parameters for N2 as well as air carrier.  Auto-detect provided for but not implemented.
#  2011 0822:  Fixed a bad bug in the second-stage line centers for very dry gas
#  2012 0118:  Changed water cross-talk correction to methane concentration to depend on carrier gas (had been correct for N2 only)
#  2012 0216:  Added reporting of PZT average and standard deviation from calibration scans
#  2012 0227:  Changed self-broadening correction to be bilinear in rare and common isotopologues (see note book).  Introduced scaling
#                      factor in the fitter to keep test procedure and fitterConfig.ini unchanged.
#  2012 0327:  Added offset to methane concentration
#  2012 0503:  Experimental --  lines 158,159,236 report isotopic ratios based on line strengths
#  2012 0329:  Changed reporting of PZTs to discriminate between VLs

import os.path
import time
from numpy import *

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
    init["base",1] = baseline_slope
    init[1000,0] = A0
    init[1000,1] = Nu0
    init[1000,2] = Per0
    init[1000,3] = Phi0
    init[1001,0] = A1
    init[1001,1] = Nu1
    init[1001,2] = Per1
    init[1001,3] = Phi1

if INIT:
    fname = os.path.join(BASEPATH,r"./HIDS/HIDS spectral library v3_1.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)

    optDict = eval("dict(%s)" % OPTION)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/Full_range+HC_v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/Full_range_FC_FY_v1_1.ini")))

#   Globals for the isotopic H2O fit
    last_time = None
    pzt2_mean = 0.0
    pzt2_stdev = 0.0
    pzt3_mean = 0.0
    pzt3_stdev = 0.0
    pzt4_mean = 0.0
    pzt4_stdev = 0.0
    auto_mode_flag =  optDict.get('autodetect',instrParams['Autodetect_enable'])     #  Set to 1 for automatic switching between air and N2 fitters
    n2_flag = instrParams['N2_flag']                                                 #  Set to 0 for air and 1 for N2
    try:
        if optDict['carrier'].upper() == 'N2':
            n2_flag = 1
        elif optDict['carrier'].upper() == 'AIR':
            n2_flag = 0
    except:
        pass

#   Spectroscopic parameters

    center1 = spectrParams['peak1']['center']
    y1_nominal = 50*spectrParams['peak1']['y']
    y2_nominal = 50*spectrParams['peak2']['y']
    center3 = spectrParams['peak3']['center']
    y3_nominal = 50*spectrParams['peak3']['y']

#   Parameters used in the fits

    offset1 = [instrParams['AIR_offset1'],instrParams['N2_offset1']]
    offset2 = [instrParams['AIR_offset2'],instrParams['N2_offset2']]
    offset3 = [instrParams['AIR_offset3'],instrParams['N2_offset3']]
    G1_H2 = [instrParams['AIR_G1_quadratic'],instrParams['N2_G1_quadratic']]
    G2_H2 = [instrParams['AIR_G2_quadratic'],instrParams['N2_G2_quadratic']]
    G3_H2 = [instrParams['AIR_G3_quadratic'],instrParams['N2_G3_quadratic']]
    y1_at_zero = [instrParams['AIR_y1_at_zero'],instrParams['N2_y1_at_zero']]
    y1_self = [instrParams['AIR_y1_self'],instrParams['N2_y1_self']]
    y2_at_zero = [instrParams['AIR_y2_at_zero'],instrParams['N2_y2_at_zero']]
    y2_self = [instrParams['AIR_y2_self'],instrParams['N2_y2_self']]
    y3_at_zero = [instrParams['AIR_y3_at_zero'],instrParams['N2_y3_at_zero']]
    y3_self = [instrParams['AIR_y3_self'],instrParams['N2_y3_self']]
    water_lin = instrParams['Water_linear']
    M_off = [instrParams['AIR_Methane_offset'],instrParams['N2_Methane_offset']]
    M_H1 = [instrParams['AIR_Methane_water_linear'],instrParams['N2_Methane_water_linear']]
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

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.0007,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
#d.calcGroupStats()
#d.calcSpectrumStats()

d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))

species = (d.subschemeId & 0x3FF)[0]

tstart = time.clock()
RESULT = {}
r = None

if ((species == 123) or (species == 124)) and (d["ngroups"] > 27):
    initialize_Baseline()
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    h2o_squish = r["base",4]
    h2o_vy = r[2,"y"]
    o18_shift = h2o_shift-r[1,"center"]+center1
    hdo_shift = h2o_shift-r[3,"center"]+center3
    peak1 = r[1,"peak"]
    peak2 = r[2,"peak"]
    peak3 = r[3,"peak"]
    baseline0 = r["base",0]
    baseline1 = r["base",1]
    baseline2 = r["base",2]
    ch4_amp = r[1002,2]
    ch4_ppm = 10000*(ch4_amp + M_H1[n2_flag]*peak2)+M_off[n2_flag]
    h2o_residuals = r["std_dev_res"]
    str18 = r[1,"strength"]/r[2,"strength"]
    strD = r[3,"strength"]/r[2,"strength"]

    if peak2 > 10 and abs(h2o_shift) < 0.05 and abs(h2o_vy-y2_nominal) < 0.25:
        h2o_adjust = h2o_shift
    else:
        h2o_adjust = 0.0

    if peak1 > 10 and abs(o18_shift) < 0.05 and abs(r[1,"y"]-y1_nominal) < 0.25:
        o18_adjust = o18_shift
    else:
        o18_adjust = 0.0

    if peak3 > 10 and abs(hdo_shift) < 0.05 and abs(r[3,"y"]-y3_nominal) < 0.25:
        hdo_adjust = hdo_shift
    else:
        hdo_adjust = 0.0

#  Preset center and ys for second stage fit

    init["base",3] = h2o_adjust
    init[1,"center"] = h2o_adjust+center1-o18_adjust
    init[3,"center"] = h2o_adjust+center3-hdo_adjust
    if peak2 > 10 and abs(h2o_shift) < 0.05 and abs(h2o_vy-y2_nominal) < 0.25:
        init[1,"y"] = y1_at_zero[n2_flag]+y1_self[n2_flag]*peak2
        init[2,"y"] = y2_at_zero[n2_flag]+y2_self[n2_flag]*peak2
        init[3,"y"] = y3_at_zero[n2_flag]+y3_self[n2_flag]*peak2
    r = anH2O[1](d,init,deps)
    ANALYSIS.append(r)
    peak1 = r[1,"peak"]
    peak2 = r[2,"peak"]
    peak3 = r[3,"peak"]
    raw_18 = peak1/peak2
    raw_D = peak3/peak2
    str1 = r[1,"strength"]
    str2 = r[2,"strength"]
    str3 = r[3,"strength"]
    base1 = r[1,"base"]
    base2 = r[2,"base"]
    base3 = r[3,"base"]

#   Spectroscopic adjustments
    peak1_offset = peak1+offset1[n2_flag]+G1_H2[n2_flag]*0.5754*peak1*peak2
    peak2_offset = peak2+offset2[n2_flag]+G2_H2[n2_flag]*peak2**2
    peak3_offset = peak3+offset3[n2_flag]+G3_H2[n2_flag]*6.173*peak3*peak2
    h2o_ppm = water_lin*peak2_offset

    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        VL = d.laserUsed>>2
        VL2 = (VL == 2)
        VL3 = (VL == 3)
        VL4 = (VL == 4)
        pzt2_mean = mean(d.pztValue[VL2])
        pzt2_stdev = std(d.pztValue[VL2])
        pzt3_mean = mean(d.pztValue[VL3])
        pzt3_stdev = std(d.pztValue[VL3])
        pzt4_mean = mean(d.pztValue[VL4])
        pzt4_stdev = std(d.pztValue[VL4])

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
    RESULT = {"peak1":peak1,"peak2":peak2,"peak3":peak3,"h2o_vy":h2o_vy,
            "peak1_offset":peak1_offset,"peak2_offset":peak2_offset,
            "peak3_offset":peak3_offset,"h2o_ppm":h2o_ppm,
            "strength1":str1,"strength2":str2,"strength3":str3,
            "base1":base1,"base2":base2,"base3":base3,
            "h16oh_adjust":h2o_adjust,"h16oh_shift":h2o_shift,"h2o_squish":h2o_squish,
            "h18oh_adjust":o18_adjust,"h18oh_shift":o18_shift,
            "h16od_adjust":hdo_adjust,"h16od_shift":hdo_shift,
            "raw18":raw_18,"raw_D":raw_D,"baseline_curvature":baseline2,
            "baseline_shift":baseline0-baseline_level,"slope_shift":baseline1-baseline_slope,
            "ch4_ppm":ch4_ppm,"n2_flag":n2_flag,"residuals":h2o_residuals,
            "str18":str18,"strD":strD,
            "dataGroups":d["ngroups"],"dataPoints":d["datapoints"],
            "pzt2_ave":pzt2_mean,"pzt2_stdev":pzt2_stdev,"pzt3_ave":pzt3_mean,"pzt3_stdev":pzt3_stdev,
            "pzt4_ave":pzt4_mean,"pzt4_stdev":pzt4_stdev,
            "spectrum":species,"interval":interval,"fit_time":fit_time
            }
    RESULT.update(d.sensorDict)
