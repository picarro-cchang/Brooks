#  Translated from Silverstone script Cv1_54 Kv1_005 2010 0726.txt
#  on analyzer 423-CKADS017 -- 16 Sept 2010 hoffnagle
#  2010-12-02:  Added post-fit with varaible squish and reporting of squish when both water and CO2 are present
#               Added reporting of yeff paramters for both water and CO2 splines
#               Constrained yeff of water spline to be in range 0-2, to suppress bogus results with dry gas
#  2011-04-28:  Replaced numgroups (deprecated) with ngroups.
#  2011-10-14:  Implement new release V1.007 from Chris Rella
#  2011-12-14:  Add version id to FitterConfig.ini and InstrCal._CKADS.ini
#  2012-03-26:  Fixed bug in fit definition file for variable squish
#  2013-01-22:  Changed lower limit on bad ringdown filter from 0.5 to 0.2 ppm/cm

from numpy import mean, std, sqrt
import os.path
import time

def initialize_Baseline():
    init["base",1] = baseline_slope
    init[1002,0] = A0
    init[1002,1] = Nu0
    init[1002,2] = Per0
    init[1002,3] = Phi0
    init[1003,0] = A1
    init[1003,1] = Nu1
    init[1003,2] = Per1
    init[1003,3] = Phi1

tstart = time.clock()

if INIT:
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    #  Import instrument specific baseline constants
    try:
        ver = instrParams['Version']
    except:
        ver = 0
    baseline_slope = instrParams['Baseline_slope']
    A0 = instrParams['Sine0_ampl']
    Nu0 = instrParams['Sine0_freq']
    Per0 = instrParams['Sine0_period']
    Phi0 = instrParams['Sine0_phase']
    A1 = instrParams['Sine1_ampl']
    Nu1 = instrParams['Sine1_freq']
    Per1 = instrParams['Sine1_period']
    Phi1 = instrParams['Sine1_phase']

    if ver < 1.7:
        fname = os.path.join(BASEPATH,r"./CKADS/spectral library v1_043_CKADS01_20090301.ini")
    else:
        fname = os.path.join(BASEPATH,r"./CKADS/spectral library v1_043_CKADS01_SPLfromGAL_20110625.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anCO = []
    if ver < 1.7:
        anCO.append(Analysis(os.path.join(BASEPATH,r"./CKADS/basic 6380 v1 VC VY 20090719.ini")))
        anCO.append(Analysis(os.path.join(BASEPATH,r"./CKADS/basic 6380 v1 FC FY 20090315.ini")))
        anCO.append(Analysis(os.path.join(BASEPATH,r"./CKADS/basic 6380 v1 FC FY - CO only 20100527.ini")))
        anCO.append(Analysis(os.path.join(BASEPATH,r"./CKADS/basic 6380 v1 VC VY VS 20101130.ini")))

    else:
        anCO.append(Analysis(os.path.join(BASEPATH,r"./CKADS/basic 6380 v1 VC FY 20090315.ini")))
        anCO.append(Analysis(os.path.join(BASEPATH,r"./CKADS/basic 6380 v1_1 FC FY 20110625.ini")))
        anCO.append(Analysis(os.path.join(BASEPATH,r"./CKADS/basic 6380 v1_1 FC FY - CO only 20110625.ini")))
        anCO.append(Analysis(os.path.join(BASEPATH,r"./CKADS/basic 6380 v2 VC VY VS 20120326.ini")))

    pzt_mean = 0.0
    pzt_stdev = 0.0

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=50.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=2000,width=0.001,height=20000000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
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
inletValvePos = d.sensorDict["InletValve"]
outletValvePos = d.sensorDict["OutletValve"]

species = (d.subschemeId & 0x3FF)[0]
tstart = time.clock()
if species in [145]:
    initialize_Baseline()
    r = anCO[0](d,init,deps)          #  Variable center fit
    ANALYSIS.append(r)
    if d["ngroups"] >= 4:
        vb_h2o_pct = 3.125*r[1001,2]
        vb_co2_pct = 0.6*r[1000,2]
        vpeak84 = r[84,"peak"]
        vco_ppmv = 0.427*vpeak84
        vbase84 = r[84,"base"]
        vb_co_shift = r["base",3]
        h2o_shift = r[1001,0]
        co_shift_var = vb_co_shift

        if (abs(r["base",3])>0.03) or ((r[1000,2]<0.03) and (r[1001,2]<0.15) and (r[84,"peak"]<15.0)):
            initialize_Baseline()
            r = anCO[1](d,init,deps)  #  Fixed center fit if shift large or all peaks small
            ANALYSIS.append(r)

        # if (r[1001,5] < 0.0) or (r[1001,5] > 2.0):
            # initialize_Baseline()
            # r = anCO[3](d,init,deps)  #  Fixed yeff for water if first pass is unreasonable, not used in V1.007
            # ANALYSIS.append(r)

        b_amp_h2o = r[1001,2]
        new_b_h2o_pct = 3.125*b_amp_h2o
        if ver < 1.7:
            b_h2o_pct = new_b_h2o_pct
        else:
            b_h2o_pct = new_b_h2o_pct*(1.25281 - 0.04929*new_b_h2o_pct)
        b_amp_co2 = r[1000,2]
        b_co2_pct = 0.6*0.89445*b_amp_co2
        bpeak84 = r[84,"peak"]
        bco_ppmv = 0.427*bpeak84
        bbase84 = r[84,"base"]
        co_shift = r["base",3]
        co_adjust = r["base",3]
        b_base0 = r["base",0]
        b_base1 = r["base",1]
        bpeak1000 = 60.0*r[1000,2]
        bpeak1001 = 200.0*r[1001,2]
        bpeak_sum = bpeak84+bpeak1000+bpeak1001
        co_res = r["std_dev_res"]
        co_quality = fitQuality(co_res,bpeak_sum,2000,0.1)
        co2_yeff = r[1000,5]
        h2o_yeff = r[1001,5]

        if (r[1000,2]>0.03) and (r[1001,2]>0.15):
            initialize_Baseline()
            r = anCO[3](d,init,deps)  #  Keep track of the squish when peaks are not too small
            ANALYSIS.append(r)
        co_squish = r["base",4]

        init[1000,2] = b_amp_co2
        init[1001,2] = b_amp_h2o
        initialize_Baseline()
        r = anCO[2](d,init,deps)      #  Fit CO region only
        ANALYSIS.append(r)
        h2o_pct = 3.125*r[1001,2]
        co2_pct = 0.6*0.89445*r[1000,2]

        peak84_raw = r[84,"peak"]
        # Final corrections are computed in the data manager as for other G2000 CFADS analyzers
        # peak84_offset = peak84_raw+CO_OFF
        # peak84_spec = peak84_offset + CO_H1*b_h2o_pct + CO_H1A1*b_h2o_pct*CO_P14(****) + CO_H2*b_h2o_pct^2 + CO_A1*CO_P14
        # final_co_ppmv = 0.427*peak84_spec
        final_base84 = r[84,"base"]
        final_base0 = r["base",0]
        final_base1 = r["base",1]

        cal = (d.subschemeId & 4096) != 0
        if any(cal):
            pzt_mean = mean(d.pztValue[cal])
            pzt_stdev = std(d.pztValue[cal])

        RESULT = {"co_res":co_res, "co_quality":co_quality,"peak84_raw":peak84_raw,"final_base84":final_base84,
                  "final_base0":final_base0,"final_base1":final_base1,"h2o_pct":h2o_pct,"b_h2o_pct":b_h2o_pct,"co2_pct":co2_pct,
                  "vco_ppmv":vco_ppmv,"bco_ppmv":bco_ppmv,"co_shift":co_shift,"co_adjust":co_adjust,"co_points":d["ngroups"],
                  "co2_yeff":co2_yeff,"h2o_yeff":h2o_yeff,"co_squish":co_squish,"new_b_h2o_pct":new_b_h2o_pct,
                  "co_tuner_mean":tunerMean,"co_tuner_std": std(d.tunerValue),"fitter_version":ver,
                  "co_pzt_mean":pzt_mean,"co_pzt_std":pzt_stdev}
        RESULT.update({"species":4,"co_fittime":time.clock()-tstart,
                       "cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                       "das_temp":dasTemp})
        #RESULT.update(d.sensorDict)
        #print "CO Fit time: %.3f" % (RESULT["co_fittime"],)
    else:
        RESULT = {}
else:
    RESULT = {}

