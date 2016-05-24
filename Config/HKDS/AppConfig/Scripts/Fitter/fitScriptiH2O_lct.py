#  Fit script for isotopic water lines at 7200 wavenumbers merged with fit for O17/O18 ratio from spectroscopy at 7193 wavenumbers
#  2011 1104:  Merge HIDS release 1.1 fitter with developmental fitter for 7193 wvn
#  2011 1010:  Preset peak 12 y based on peak 11 fit
#  2011 1122:  Removed data points on peak 12 from prefit and adjust peak 14 center and y based on FSR data from HB2132
#  2011 1128:  Major changes to try to improve precision.  Remove quadratic term from peak 11 baseline and use the peak-base trick for 11 and 13
#  2011 1208:  Minor change to tighten constraints when converting shifts to adjusts.  Attempt to remove outliers when [H2O] -> 0.
#  2011 1212:  Remove baseline curvature from O-18 fit.
#  2011 1214:  Merge the 7193 and 7200 wvn regions into a single spectral id to allow rapid and symmetric scanning of all lines
#  2012 0117:  Change spectroscopic corrections to reference all water concentration to peak 2
#  2012 0118:  Changed water cross-talk correction to methane concentration to depend on carrier gas (had been correct for N2 only)
#  2013 0115:  Changed reporting of strengths to come from variable y fits.
#              Added strength offsets in an ad hoc way for HBDS2171 ("seventino").
#  2013 0124:  Preset 7193 wvn y-parameters from 7200 wvn fit.  Add strength ratio reporting.
#  2013 0129:  Start preparations for laser current tuning
#  2013 0205:  Add condition to use of cavity FSR for frequency scale -- pzt must first be locked
#  2013 0207:  Add separate fitting procedures for WLM and PZT adjustment to improve turn-on when PZT is initially inaccurate
#  2013 0311:  Remove unnecessary peak height fitting pieces
#  2013 0318:  Change fitting at low concentration to better accomodate dry gas
#  2013 0408:  Changed y preset on peak12 to use (161) strength instead of (181) peak for self-broadening

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

def initialize_7193_Baseline():
    init["base",1] = baseline_slope_7193
    init[1000,0] = A0_7193
    init[1000,1] = Nu0_7193
    init[1000,2] = Per0_7193
    init[1000,3] = Phi0_7193
    init[1001,0] = A1_7193
    init[1001,1] = Nu1_7193
    init[1001,2] = Per1_7193
    init[1001,3] = Phi1_7193

def initialize_7200_Baseline():
    init["base",1] = baseline_slope_7200
    init[1000,0] = A0_7200
    init[1000,1] = Nu0_7200
    init[1000,2] = Per0_7200
    init[1000,3] = Phi0_7200
    init[1001,0] = A1_7200
    init[1001,1] = Nu1_7200
    init[1001,2] = Per1_7200
    init[1001,3] = Phi1_7200

def outlierFilter(x,threshold,minPoints=2):
    """ Return Boolean array giving points in the vector x which lie
    within +/- threshold * std_deviation of the mean. The filter is applied iteratively
    until there is no change or unless there are minPoints or fewer remaining"""
    good = ones(x.shape,bool_)
    order = list(x.argsort())
    while len(order)>minPoints:
        maxIndex = order.pop()
        good[maxIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[maxIndex]-mu)>=(threshold*sigma):
            continue
        good[maxIndex] = 1
        minIndex = order.pop(0)
        good[minIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[minIndex]-mu)>=(threshold*sigma):
            continue
        good[minIndex] = 1
        break
    return good

if INIT:
    fname = os.path.join(BASEPATH,r"./HIDS/HIDS spectral library v4_3.ini")
    spectrParams = getInstrParams(fname)
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig_with_7193.ini")
    instrParams = getInstrParams(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_lct.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_lct.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']

    optDict = eval("dict(%s)" % OPTION)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/Full_range_7200+HC_v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/Full_range_7200_FC_FY_v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/O18_VC_FY_v1_2.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/O18_FC_FY_v1_2.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/O17_VC_FY_v2_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/O17_FC_FY_v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/Full_range_7200+HC_v1_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/O18_VC_FY_v1_2.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HIDS/O17_VC_FY_v2_1.ini")))

#   Globals for the isotopic H2O fit
    last_time = None
    pzt_ave = 0.0
    pzt_stdev = 0.0
    auto_mode_flag =  optDict.get('autodetect',instrParams['Autodetect_enable'])     #  Set to 1 for automatic switching between air and N2 fitters
    n2_flag = instrParams['N2_flag']                                                 #  Set to 0 for air and 1 for N2
    try:
        if optDict['carrier'].upper() == 'N2':
            n2_flag = 1
        elif optDict['carrier'].upper() == 'AIR':
            n2_flag = 0
    except:
        pass
    peak1 = 0
    peak2 = 0
    peak3 = 0
    h2o_vy = 0
    h2o_ppm = 0
    str1 = 0
    str2 = 0
    str3 = 0
    str1_offset = 0
    str2_offset = 0
    str3_offset = 0
    str11_offset = 0
    str13_offset = 0
    base1 = 0
    base2 = 0
    base3 = 0
    h2o_adjust = 0
    h2o_shift = 0
    o18_adjust = 0
    o18_shift = 0
    hdo_adjust = 0
    hdo_shift = 0
    baseline0 = 0
    baseline1 = 0
    baseline2 = 0
    ch4_ppm = 0
    h2o_residuals = 0
    peak_11 = 0
    str_11 = 0
    vy_11 = 0
    vz_11 = 0
    shift_11 = 0
    adjust_11 = 0
    base_11 = 0
    res_11 = 0
    str_12 = 0
    vy_12 = 0
    peak_13 = 0
    str_13 = 0
    vy_13 = 0
    vz_13 = 0
    str_14 = 0
    shift_13 = 0
    adjust_13 = 0
    base_13 = 0
    res_13 = 0

    pzt1_adjust = 0.0
    pzt2_adjust = 0.0
    pzt3_adjust = 0.0
    pzt4_adjust = 0.0
    pzt5_adjust = 0.0

#   Spectroscopic parameters

    center1 = spectrParams['peak1']['center']
    y1_nominal = 50*spectrParams['peak1']['y']
    y2_nominal = 50*spectrParams['peak2']['y']
    center3 = spectrParams['peak3']['center']
    y3_nominal = 50*spectrParams['peak3']['y']
    y11_nominal = 50*spectrParams['peak11']['y']
    y13_nominal = 50*spectrParams['peak13']['y']

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
    water_quad = instrParams['Water_quadratic']
    M_off = [instrParams['AIR_Methane_offset'],instrParams['N2_Methane_offset']]
    M_H1 = [instrParams['AIR_Methane_water_linear'],instrParams['N2_Methane_water_linear']]
    offset11 = [instrParams['AIR_offset11'],instrParams['N2_offset11']]
    offset13 = [instrParams['AIR_offset13'],instrParams['N2_offset13']]
    G11_H2 = [instrParams['AIR_G11_quadratic'],instrParams['N2_G11_quadratic']]
    G13_H2 = [instrParams['AIR_G13_quadratic'],instrParams['N2_G13_quadratic']]
    y11_at_zero = [instrParams['AIR_y11_at_zero'],instrParams['N2_y11_at_zero']]
    y11_self = [instrParams['AIR_y11_self'],instrParams['N2_y11_self']]
    y12_at_zero = [instrParams['AIR_y12_at_zero'],instrParams['N2_y12_at_zero']]
    y12_self = [instrParams['AIR_y12_self'],instrParams['N2_y12_self']]
    y13_at_zero = [instrParams['AIR_y13_at_zero'],instrParams['N2_y13_at_zero']]
    y13_self = [instrParams['AIR_y13_self'],instrParams['N2_y13_self']]
    baseline_level_7193 = instrParams['7193_Baseline_level']
    baseline_slope_7193 = instrParams['7193_Baseline_slope']
    A0_7193 = instrParams['7193_Sine0_ampl']
    Nu0_7193 = instrParams['7193_Sine0_freq']
    Per0_7193 = instrParams['7193_Sine0_period']
    Phi0_7193 = instrParams['7193_Sine0_phase']
    A1_7193 = instrParams['7193_Sine1_ampl']
    Nu1_7193 = instrParams['7193_Sine1_freq']
    Per1_7193 = instrParams['7193_Sine1_period']
    Phi1_7193= instrParams['7193_Sine1_phase']
    baseline_level_7200 = instrParams['7200_Baseline_level']
    baseline_slope_7200 = instrParams['7200_Baseline_slope']
    A0_7200 = instrParams['7200_Sine0_ampl']
    Nu0_7200 = instrParams['7200_Sine0_freq']
    Per0_7200 = instrParams['7200_Sine0_period']
    Phi0_7200 = instrParams['7200_Sine0_phase']
    A1_7200 = instrParams['7200_Sine1_ampl']
    Nu1_7200 = instrParams['7200_Sine1_freq']
    Per1_7200 = instrParams['7200_Sine1_period']
    Phi1_7200 = instrParams['7200_Sine1_phase']

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
#d.wlmSetpointFilter(maxDev=0.002,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.001,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
#d.calcGroupStats()
#d.calcSpectrumStats()

d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))

species = (d.subschemeId & 0x3FF)[0]
#print "SpectrumId", d["spectrumId"]

tstart = time.clock()
RESULT = {}
r = None

in17 = (d.fitData["freq"] >= 7192.98) & (d.fitData["freq"] <= 7193.22)
good17 = sum(in17)
in18 = (d.fitData["freq"] >= 7192.76) & (d.fitData["freq"] <= 7192.92)
good18 = sum(in18)
in7200 = (d.fitData["freq"] >= 7199.85) & (d.fitData["freq"] <= 7200.40)
good7200 = sum(in7200)
pzt1_adjust = 0.0
pzt2_adjust = 0.0
pzt3_adjust = 0.0
pzt4_adjust = 0.0
pzt5_adjust = 0.0

if (species == 123) and (good7200 > 25):         #  First fit spectrum as always with frequency from WLM
    initialize_7200_Baseline()
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    h2o_vy = r[2,"y"]
    o18_shift = h2o_shift-r[1,"center"]+center1
    hdo_shift = h2o_shift-r[3,"center"]+center3
    peak1 = r[1,"peak"]
    peak2 = r[2,"peak"]
    peak3 = r[3,"peak"]
    str1 = r[1,"strength"]
    str2 = r[2,"strength"]
    str3 = r[3,"strength"]
    baseline0 = r["base",0]
    baseline1 = r["base",1]
    baseline2 = r["base",2]
    #ch4_amp = r[1002,2]
    #ch4_ppm = 10000*(ch4_amp + M_H1[n2_flag]*peak2)
    shiftsOK = abs(h2o_shift) < 0.05 and abs(o18_shift) < 0.05 and abs(hdo_shift) < 0.05

    if peak2 > 10 and shiftsOK and abs(h2o_vy-y2_nominal) < 0.25:
        h2o_adjust = h2o_shift
    else:
        h2o_adjust = 0.0

    if peak1 > 10 and shiftsOK and abs(r[1,"y"]-y1_nominal) < 0.25:
        o18_adjust = o18_shift
    else:
        o18_adjust = 0.0

    if peak3 > 2 and shiftsOK and abs(r[3,"y"]-y3_nominal) < 0.25:
        hdo_adjust = hdo_shift
    else:
        hdo_adjust = 0.0

if (species == 123 and good17 > 9 and good18 > 6):
    initialize_7193_Baseline()          #  O-18 line at 7192.8 wavenumbers
    init[11,"y"] = 0.01306 + 0.7268*h2o_vy
    r = anH2O[2](d,init,deps)
    ANALYSIS.append(r)
    shift_11 = r["base",3]
    vy_11 = r[11,"y"]
    vz_11 = r[11,"z"]
    peak_11 = r[11,"peak"]
    base_level_11 = r["base",0]
    base_slope_11 = r["base",1]
    res_11 = r["std_dev_res"]
    str_11 = r[11,"strength"]

    if peak_11 > 10 and abs(shift_11) < 0.05 and abs(vy_11-y11_nominal) < 0.2:
        adjust_11 = shift_11
    else:
        adjust_11 = 0.0

    init[12,"strength"] = 0.1270*str_11     #  O-17 peak at 7193.1 wavenumbers
    init[12,"y"] = y12_at_zero[n2_flag]+y12_self[n2_flag]*peak_11
    init[13,"y"] = 0.03535 + 0.5432*h2o_vy
    r = anH2O[4](d,init,deps)
    ANALYSIS.append(r)
    shift_13 = r["base",3]
    vy_13 = r[13,"y"]
    vz_13 = r[13,"z"]
    peak_13 = r[13,"peak"]
    str_13 = r[13,"strength"]
    base_level_13 = r["base",0]
    base_slope_13 = r["base",1]
    str_12 = r[12,"strength"]
    str_14 = r[14,"strength"]
    vy_12  = r[12,"y"]
    res_13 = r["std_dev_res"]

    if peak_13 > 10 and abs(shift_13) < 0.05 and abs(vy_13-y13_nominal) < 0.2:
        adjust_13 = shift_13
    else:
        adjust_13 = 0.0

#  Compute self-broadening for second-stage fit
    if peak2 > 10 and abs(h2o_shift) < 0.05 and abs(h2o_vy-y2_nominal) < 0.25:
        y1_nominal = y1_at_zero[n2_flag]+y1_self[n2_flag]*peak2
        y2_nominal = y2_at_zero[n2_flag]+y2_self[n2_flag]*peak2
        y3_nominal = y3_at_zero[n2_flag]+y3_self[n2_flag]*peak2
        y11_nominal = y11_at_zero[n2_flag]+y11_self[n2_flag]*peak_11
        y13_nominal = y13_at_zero[n2_flag]+y13_self[n2_flag]*peak_13

#  LCT fits with frequencies on FSR grid IF all frequency targeting is locked

    VL = d.laserUsed>>2
    VL0 = (VL == 0)
    VL1 = (VL == 1)
    VL2 = (VL == 2)
    VL3 = (VL == 3)
    VL4 = (VL == 4)
    goodLCT = abs(h2o_shift)<0.002 and abs(o18_shift)<0.002 and abs(hdo_shift)<0.003 and abs(shift_11)<0.002 and abs(shift_13)<0.002
    if goodLCT:
        d.waveNumber[VL0] = 7192.8388 + fsr*round_((d.waveNumber[VL0] - 7192.8388)/fsr)
        d.waveNumber[VL1] = 7193.1288 + fsr*round_((d.waveNumber[VL1] - 7193.1288)/fsr)
        d.waveNumber[VL2] = 7200.13384 + fsr*round_((d.waveNumber[VL2] - 7200.13384)/fsr)
        d.waveNumber[VL3] = 7199.96047 + fsr*round_((d.waveNumber[VL3] - 7199.96047)/fsr)
        d.waveNumber[VL4] = 7200.30265 + fsr*round_((d.waveNumber[VL4] - 7200.30265)/fsr)

        d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
        d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
        d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
        d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))

        initialize_7200_Baseline()
        r = anH2O[6](d,init,deps)
        ANALYSIS.append(r)
        h2o_shift = r["base",3]
        h2o_vy = r[2,"y"]
        o18_shift = h2o_shift-r[1,"center"]+center1
        hdo_shift = h2o_shift-r[3,"center"]+center3
        base1 = r[1,"base"]
        base2 = r[2,"base"]
        base3 = r[3,"base"]
        peak1 = r[1,"peak"]
        peak2 = r[2,"peak"]
        peak3 = r[3,"peak"]
        str1 = r[1,"strength"]
        str2 = r[2,"strength"]
        str3 = r[3,"strength"]
        baseline0 = r["base",0]
        baseline1 = r["base",1]
        baseline2 = r["base",2]
        ch4_amp = r[1002,2]
        ch4_ppm = 10000*(ch4_amp + M_off[n2_flag] + M_H1[n2_flag]*str2)
        h2o_residuals = r["std_dev_res"]

#   Adjustments based on concentration step tests
        str1_offset = str1 + offset1[n2_flag] + G1_H2[n2_flag]*str1*str2
        str2_offset = str2 + offset2[n2_flag] + G2_H2[n2_flag]*str2**2
        str3_offset = str3 + offset3[n2_flag] + G3_H2[n2_flag]*str3*str2
        h2o_ppm = water_lin*str2_offset + water_quad*str2_offset**2

        if peak1 > 5 and peak2 > 5 and peak3 > 2:
            pzt3_adjust = -h2o_shift*pzt_per_fsr/fsr
            pzt4_adjust = -o18_shift*pzt_per_fsr/fsr
            pzt5_adjust = -hdo_shift*pzt_per_fsr/fsr
        else:
            pzt3_adjust = 0.0
            pzt4_adjust = 0.0
            pzt5_adjust = 0.0

        initialize_7193_Baseline()
        init[11,"y"] = 0.01306 + 0.7268*h2o_vy
        r = anH2O[7](d,init,deps)
        ANALYSIS.append(r)
        shift_11 = r["base",3]
        vy_11 = r[11,"y"]
        vz_11 = r[11,"z"]
        peak_11 = r[11,"peak"]
        base_11 = r["base",0]
        base_slope_11 = r["base",1]
        res_11 = r["std_dev_res"]
        str_11 = r[11,"strength"]
        str11_offset = str_11 + offset11[n2_flag] + G11_H2[n2_flag]*str_11*str2

        if peak_11 > 5:
            pzt1_adjust = -shift_11*pzt_per_fsr/fsr
        else:
            pzt1_adjust = 0.0

        init[12,"strength"] = 0.1270*str_11
        init[12,"y"] = y12_at_zero[n2_flag]+y12_self[n2_flag]*str2
        init[13,"y"] = 0.03535 + 0.5432*h2o_vy
        r = anH2O[8](d,init,deps)
        ANALYSIS.append(r)
        shift_13 = r["base",3]
        vy_13 = r[13,"y"]
        vz_13 = r[13,"z"]
        peak_13 = r[13,"peak"]
        str_13 = r[13,"strength"]
        str13_offset = str_13 + offset13[n2_flag] + G13_H2[n2_flag]*str_13*str2
        base_13 = r["base",0]
        base_slope_13 = r["base",1]
        str_12 = r[12,"strength"]
        str_14 = r[14,"strength"]
        vy_12  = r[12,"y"]
        res_13 = r["std_dev_res"]

        if peak_13 > 5:
            pzt2_adjust = -shift_13*pzt_per_fsr/fsr
        else:
            pzt2_adjust = 0.0

#  Calculate corrected strength ratios
    try:
        str_17_16 = str13_offset/str2_offset
        str_18_16 = str11_offset/str2_offset
        str_18_18 = str11_offset/str1_offset
    except:
        str_17_16 = 0
        str_18_16 = 0
        str_18_18 = 0

now = time.clock()
fit_time = now-tstart
if r != None:
    IgnoreThis = False
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]
if (good7200>25) and (good17>9) and (good18>6):
    IgnoreThis = False
else:
    IgnoreThis = True

#print DATA.filterHistory

if not IgnoreThis:
    RESULT = {"peak1":peak1,"peak2":peak2,"peak3":peak3,"h2o_vy":h2o_vy,"h2o_ppm":h2o_ppm,
            "strength1":str1,"strength2":str2,"strength3":str3,
            "str1_offset":str1_offset,"str2_offset":str2_offset,"str3_offset":str3_offset,
            "str11_offset":str11_offset,"str13_offset":str13_offset,
            "str_17_16":str_17_16,"str_18_16":str_18_16,"str_18_18":str_18_18,
            "base1":base1,"base2":base2,"base3":base3,
            "h16oh_adjust":h2o_adjust,"h16oh_shift":h2o_shift,
            "h18oh_adjust":o18_adjust,"h18oh_shift":o18_shift,
            "h16od_adjust":hdo_adjust,"h16od_shift":hdo_shift,
            "baseline_curvature":baseline2,
            "baseline_shift":baseline0-baseline_level_7200,
            "slope_shift":baseline1-baseline_slope_7200,
            "ch4_ppm":ch4_ppm,"n2_flag":n2_flag,"residuals":h2o_residuals,
            "peak_11":peak_11,"peak_13":peak_13,"vy_11":vy_11,"vy_13":vy_13,
            "strength_11":str_11,"strength_13":str_13,"base_11":base_11,"base_13":base_13,
            "O18a_adjust":adjust_11,"shift_11":shift_11,"str_12":str_12,"vy_12":vy_12,
            "O17_adjust":adjust_13,"shift_13":shift_13,"vz_11":vz_11,"vz_13":vz_13,
            "fit11_residuals":res_11,"fit13_residuals":res_13,"str_14":str_14,
            "dataGroups":d["ngroups"],"dataPoints":d["datapoints"],"goodLCT":goodLCT,
            "pzt_per_fsr":pzt_per_fsr,"pzt1_adjust":pzt1_adjust,"pzt2_adjust":pzt2_adjust,
            "pzt3_adjust":pzt3_adjust,"pzt4_adjust":pzt4_adjust,"pzt5_adjust":pzt5_adjust,
            "spectrum":species,"interval":interval,"fit_time":fit_time
            }
    RESULT.update(d.sensorDict)
