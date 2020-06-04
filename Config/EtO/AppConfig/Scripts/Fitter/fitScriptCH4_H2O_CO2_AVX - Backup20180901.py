#  Fit script for standard CFADS methane fitter (spectrum id = 25) as of June 2010
#  Translated from R:\LV8_Development\rella\Releases\batch file inis\CFADS-xx\2010 0528\Release C1.56 F0.73\Cv1_56 Fv0_73 2010 0528.txt
#  by hoffnagle on 22 June 2010
#  10 Aug 2010:  changed ch4_shift and ch4_adjust definitions to match other fitter naming conventions, i.e. shift is from variable center fit
#                regardless of line strength; adjust is conditional on line strength and abs(shift)  -- hoffnagle
#  2010-09-03:  Added reporting of PZT mean and standard deviation for calibration points (hoffnagle)
#  2010-12-06:  Changed condition on minimum number of data groups from 4 to 14 (hoffnagle).  Note that this
#               is appropriate to normal CFADS but NOT CFADS flux.
#  2011-04-28:  Replaced numgroups (deprecated) with ngroups.
#  2013-01-22:  Changed lower limit on bad ringdown filter from 0.5 to 0.2 ppm/cm
#  2018-08-21:  Rella - simple changes to run on AVX80-9001

from numpy import any, mean, std, sqrt, round_, loadtxt
import os.path
import time

from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER

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
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library v1_043_CFADS-xx_2009_0813.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
    
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini")
    cavityParams = getInstrParams(fname)
    fsr =  cavityParams['AUTOCAL']['CAVITY_FSR']
    

    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/Master_sgdbr.ini")
    masterParams = getInstrParams(fname)
    pzt_per_fsr =  masterParams['DAS_REGISTERS']['PZT_INCR_PER_CAVITY_FSR']

    Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                        "FitScript", IsDontCareConnection=False)
    
    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 v2_1 2011 0713.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC VY v2_0 2011 0713.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC FY v2_0 2011 0713.ini")))

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O v1_1 2008 0304.ini")))     #standard fit with WLM
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O FC v1_1 2008 0304.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O v1_1 2008 0304.ini")))     #fit with FSR scale
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O FC v1_1 2008 0304.ini")))
    
    # preset values for RESULTS

    ch4_res = 0.0
    vch4_conc_ppmv = 0.0
    ch4_vy = 0.0
    ch4_adjconc_ppmv = 0.0
    ch4_conc_ppmv_final = 0.0
    base = 0.0
    splinemax = 0.0
    tunerMean = 0.0
    ch4_tuner_std = 0.0
    pzt_mean = 0.0
    pzt_stdev = 0.0
    ch4_shift = 0.0
    ch4_adjust = 0.0
    ch4_y = 0.0
    fit_time = 0.0
    interval = 0.0

    h2o_res = 0.0
    h2o_peak = 0.0
    h2o_str = 0.0
    h2o_conc = 0.0
    h2o_y = 0.0
    h2o_z = 00
    h2o_adjust = 0.0
    h2o_shift = 0.0
    tunerMean = 0.0
    pzt_mean = 0.0
    h2o_quality = 0.0
    h2o_pzt_adjust = 0.0

    base_avg = 800
    counter = -25
    last_time = None
    pzt_mean = 0.0
    pzt_stdev = 0.0
    h2o_pzt_adjust = 0.0
    overallTargetAdjust = 0.0
    fsr_h2o_adjust = 0.0
    pztAdjustGuy = 0.0
    PZTgain = 0.5
    max_pzt_adjust = 10000
    thisDifference = 0.0
    extra1val = 0.0
    extra2val = 0.0
    extra3val = 0.0

    loadTargetFromFile = True #set to False to record data 
    
    homeDIR = r'C:\Picarro\G2000\InstrConfig\Calibration\InstrCal'
    targetfn = os.path.join(homeDIR, 'TargetValuesForPZT.txt')
    print targetfn
    if loadTargetFromFile:
        loadedArray = loadtxt(targetfn, delimiter=",")
        targetMemory = list(loadedArray[:,0])
        targetCounter = [int(n) for n in loadedArray[:,1]]
        print 'loaded Target data from file!'
        print targetMemory
        print targetCounter
        print '-----   '*5
        targetFileSaved = True
        targetAve = targetCounter[0]
    else:
        targetAve = 5
        targetMemory = [0.0 for j in range(10)]
        targetCounter = [0 for j in range(10)]
        targetFileSaved = False

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

targeting = d.waveNumber - d.waveNumberSetpoint
goodT = (abs(targeting) < fsr/2.0*1.1)

targetingMean, targetingStd = mean(targeting[goodT]), std(targeting[goodT])
goodN = len(targeting[goodT])
allN = len(targeting)

TargetIndex = int(mean(d.extra1))
extra1val = TargetIndex
extra2val = mean(d.extra2)
extra3val = mean(d.extra3)

if targetCounter[TargetIndex] < targetAve and not(loadTargetFromFile):
    targetMemory[TargetIndex] += targetingMean
    targetCounter[TargetIndex] += 1
    pztAdjustGuy = 0.0
    pztAdjustFlag = False
    targetFileSaved = False
    print 'new data loaded into target array at location %d' % TargetIndex
else:
    if not(targetFileSaved) and not(loadTargetFromFile):
        if all(tcount == targetAve for tcount in targetCounter): #averages are ready
            with open(targetfn,'w') as targetFile:
                for tarV, tarN in zip(targetMemory, targetCounter):
                    targetFile.write('%.6f, %d\n' % (tarV,tarN))
            print 'Target File Saved successfully!'
            targetFileSaved = True
    pztAdjustFlag = True
    thisDifference = targetingMean - targetMemory[TargetIndex] / targetCounter[TargetIndex]
    pztAdjustGuy =  -(thisDifference  + overallTargetAdjust) * pzt_per_fsr/fsr
    print 'adjusting PZT'

print 'Target: %.2e +/- %.2e [%d] (mean nu = %.2f; N = %d / %d)' % (targetingMean, targetingStd, mean(d.extra1), mean(d.waveNumber[goodT]), goodN, allN)
#print targetMemory
#print targetCounter
#print overallTargetAdjust
#print thisDifference, pztAdjustGuy
#print '*- -*'*10

finalPZTadjust =pztAdjustGuy*PZTgain
finalPZTadjust = min(max_pzt_adjust,max(-max_pzt_adjust,finalPZTadjust))

oldPZToffset = Driver.rdFPGA("FPGA_TWGEN", "TWGEN_PZT_OFFSET")
newPZToffset = int(oldPZToffset + finalPZTadjust)

while newPZToffset > 50000:
    newPZToffset -= pzt_per_fsr
while newPZToffset < 10000:
    newPZToffset += pzt_per_fsr

print 'PZT %d ==> %d' % (oldPZToffset, newPZToffset)
Driver.wrFPGA("FPGA_TWGEN", "TWGEN_PZT_OFFSET", newPZToffset)
#Driver.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1",newPZToffset)


d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.03,sigmaThreshold=3)
d.tunerEnsembleFilter(maxDev=500000,sigmaThreshold=3.5)
d.sparse(maxPoints=1000,width=0.003,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
tunerMean = mean(d.tunerValue)
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]

r = None

if len(targeting) == 0:
    print targeting
    print '-----  '*4

goodCH4 = sum((d.groupMeans["waveNumber"] < 6057.5) & (d.groupMeans["waveNumber"] > 6056.5))
goodH2O = sum((d.groupMeans["waveNumber"] < 6058.01) & (d.groupMeans["waveNumber"] > 6057.69))

tstart = time.clock()
RESULT = {}
if goodCH4 > 5:
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
    base_avg  = initExpAverage(base_avg,base,1,1000,counter)
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

    #cal = (d.subschemeId & 4096) != 0
    #if any(cal):
    pzt_mean = mean(d.pztValue)
    pzt_stdev = std(d.pztValue)
    ch4_tuner_std = std(d.tunerValue)

    #print splinemax, ch4_conc_ppmv_final, ch4_adjust, ch4_shift


if goodH2O>5: # fit H2O spectrum
    r = anH2O[0](d,init,deps)
    ANALYSIS.append(r)
    h2o_shift = r["base",3]
    if r[75,"peak"] < 3 or abs(r["base",3]) >= 0.04:
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
    h2o_res = r["std_dev_res"]
    h2o_peak = r[75,"peak"]
    h2o_quality = fitQuality(h2o_res,h2o_peak,50,1)
    h2o_adjust = 0.0
    h2o_str = r[75,"strength"]
    h2o_y = r[75,"y"]
    h2o_z = r[75,"z"]
    h2o_base = r[75,"base"]
    h2o_conc = h2o_peak * 0.01002

    if h2o_peak > 3.0:
        h2o_adjust = h2o_shift
    else:
        h2o_adjust = 0.0
    cal = (d.subschemeId & 4096) != 0
    if any(cal):
        pzt_mean = mean(d.pztValue[cal])
        pzt_stdev = std(d.pztValue[cal])
    
    # int((nu_center - nu_h2o)*32768 + 32768) : how extra3 is set in the scheme
    h20_75_center = 6057.8000
    e3 = int(mean(d.extra3))
    peak75_center = (e3 - 32768.0)/32768.0 + h20_75_center
    print peak75_center, e3
    if abs(peak75_center - h20_75_center) > 0.03:
        peak75_center = h20_75_center
        print 'using library value of peak75_center'
    indexguy = round_((d.fitData["freq"] - peak75_center)/fsr)
    d.fitData["freq"] = peak75_center + indexguy*fsr
    
    r = anH2O[2](d,init,deps)
    ANALYSIS.append(r)
    fsr_h2o_shift = r["base",3]
    if r[75,"peak"] < 3 or abs(r["base",3]) >= 0.04:
        r = anH2O[3](d,init,deps)
        ANALYSIS.append(r)
    fsr_h2o_res = r["std_dev_res"]
    fsr_h2o_peak = r[75,"peak"]
    fsr_h2o_quality = fitQuality(fsr_h2o_res,fsr_h2o_peak,50,1)
    fsr_h2o_adjust = 0.0
    fsr_h2o_str = r[75,"strength"]
    fsr_h2o_y = r[75,"y"]
    fsr_h2o_z = r[75,"z"]
    fsr_h2o_base = r[75,"base"]
    fsr_h2o_conc = fsr_h2o_peak * 0.01002
    if fsr_h2o_peak > 3.0:
        fsr_h2o_adjust = fsr_h2o_shift
    
    maxH2OAdjust = 1e-5
    if pztAdjustFlag:
        overallTargetAdjust += min(maxH2OAdjust,max(-maxH2OAdjust,fsr_h2o_adjust))

    h2o_pzt_adjust = -fsr_h2o_adjust*pzt_per_fsr/fsr

if r == None:
    r = anH2O[0](d,init,deps) #just fit something
    pzt_mean = mean(d.pztValue)
if r != None:
    try:
        RESULT.update({"ch4_res":ch4_res,"vch4_conc_ppmv":vch4_conc_ppmv,"ch4_vy":ch4_vy,
                       "ch4_adjconc_ppmv":ch4_adjconc_ppmv,"ch4_conc_ppmv_final":ch4_conc_ppmv_final,
                       "ch4_base":base,"ch4_base_avg":base_avg,"ch4_splinemax":splinemax,
                       "ch4_tuner_mean": tunerMean, "ch4_tuner_std": ch4_tuner_std,
                       "ch4_pzt_mean": pzt_mean, "ch4_pzt_std": pzt_stdev,
                       "ch4_shift":ch4_shift,"ch4_adjust":ch4_adjust,"ch4_y":ch4_y,
                       "ch4_fit_time":fit_time,"ch4_interval":interval})

        RESULT.update({"h2o_res":h2o_res, "h2o_peak":h2o_peak, "h2o_str":h2o_str,
                       "h2o_conc_precal":h2o_conc, "h2o_y":h2o_y, "h2o_z":h2o_z,"h2o_adjust":h2o_adjust,
                       "h2o_shift":h2o_shift, "h2o_tuner_mean":tunerMean,"h2o_pzt_mean":pzt_mean,
                       "h2o_pzt_std":pzt_stdev, "h2o_quality":h2o_quality})
        RESULT.update({"fsr_h2o_res":fsr_h2o_res, "fsr_h2o_peak":fsr_h2o_peak, "fsr_h2o_str":fsr_h2o_str,
                       "fsr_h2o_conc_precal":fsr_h2o_conc, "fsr_h2o_y":fsr_h2o_y, "fsr_h2o_z":fsr_h2o_z,"fsr_h2o_adjust":fsr_h2o_adjust,
                       "fsr_h2o_shift":fsr_h2o_shift, "fsr_h2o_quality":fsr_h2o_quality, "h2o_pzt_adjust":h2o_pzt_adjust})
    except:
        pass
    RESULT.update({"overallTargetAdjust":overallTargetAdjust,"pztAdjustGuy":pztAdjustGuy,"pztMean":pzt_mean})
    RESULT.update(d.sensorDict)
    RESULT.update({"species":88,"cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp, "goodCH4":goodCH4, "goodH2O":goodH2O, "pzt_per_fsr":pzt_per_fsr,
                   "extra1val":extra1val, "extra2val":extra2val, "extra3val":extra3val,})
    #for key in RESULT:
    #    print key, RESULT[key]


