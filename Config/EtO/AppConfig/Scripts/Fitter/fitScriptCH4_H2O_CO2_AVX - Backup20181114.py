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
#  2018-09-04:  Rella - added BroadbandControl class to manage PZT and WLM locking in conjunction with the scheme definition

from numpy import any, mean, std, sqrt, round_, loadtxt, median
import os.path
import time

from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER
from Host.Utilities.MFCControl import RS232_Accessory_Module as RS232
# SCHEME_INFO gets metadata from schemes

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

class BroadbandControl (object):
    def __init__(self,pzt_per_fsr,fsr,verbose=True):
        self.resetTargetValues()
        self.pztAdjustGuy = 0.0
        self.overallTargetAdjust = 0.0
        self.pzt_per_fsr = pzt_per_fsr
        self.fsr = fsr
        self.verbose=verbose
        self.maxPZT = 55000
        self.minPZT = 5000
        self.newDataAddedToTarget = False
        self.peakProximity = 0.03 #within about 1 FSR
    
    def resetTargetValues(self):
        self.targetMemory, self.targetMemorySquared, self.targetCounter = {},{},{}
    
    def processData(self, d):
        targeting = d.waveNumber - d.waveNumberSetpoint
        goodT = (abs(targeting) < fsr/2.0*1.1)

        self.targetingMean, self.targetingStd = mean(targeting[goodT]), std(targeting[goodT])
        goodN = len(targeting[goodT])
        allN = len(targeting)
        
        self.e1 = mean(d.extra1) #mode
        self.e2 = mean(d.extra2) #spectral region
        self.e3 = mean(d.extra3) #pzt setpoint
        self.e4 = mean(d.extra4) #freq. offset of points relative to center
        self.targetIndex = int(round(self.e2))
        self.processMode()
        
        if self.pztMode == 1: #add data to targetMemory
            try:
                self.targetMemory[self.targetIndex] += self.targetingMean*goodN
                self.targetMemorySquared[self.targetIndex] += self.targetingMean**2 * goodN
                self.targetCounter[self.targetIndex] += goodN
            except KeyError:
                self.targetMemory[self.targetIndex]  = self.targetingMean*goodN
                self.targetMemorySquared[self.targetIndex] = self.targetingMean**2 * goodN
                self.targetCounter[self.targetIndex] = goodN
            self.newDataAddedToTarget = True
            if self.verbose:
                self.printTargets()

        if self.verbose:
            print '%.4f +/- %.4f (%d of %d)' % (self.targetingMean, self.targetingStd, goodN, allN)
            print '%.1f %.1f, %.1f %.1f' % (self.e1, self.e2, self.e3, self.e4)
            print 'mode: wlm = %d ; pzt = %d' % (self.wlmMode, self.pztMode)

    def printTargets(self):
        K = self.targetMemory.keys()
        K.sort()
        print 'Current Targets:'
        for k in K:
            v = self.targetMemory[k]
            v2 = self.targetMemorySquared[k]
            n = self.targetCounter[k]
            print '  %d: %.5f +/- %.6f (%.4f / %d)' % (k, v/n, sqrt((v2/n - (v/n)**2)), v, n)
            
    def processMode(self):
        self.wlmMode = int(self.e1) & 3 # first two bits : bit0 - lock WLM to spectroscopy
                                           # bit1 - lock nu target for PZT to spectroscopy
        self.pztMode = (int(self.e1) & 28) / 4    #  convert to a number from 0 to 7:
                                         # 0: do nothing
                                         # 1: collect data for nu targeting
                                         # 2: use nu targeting to lock PZT
                                         # 3: use spectroscopy to lock PZT directly
                                         # 4: no locking; reset nu target data
                                         # 5: set PZT directly from scheme using extra3
                                         # 6: set PZT as an offset from scheme using extra3 (32768 = no change)
                                         
    def checkPZTinRange(self,value):
        while value > self.maxPZT:
            value -= self.pzt_per_fsr
        while value < self.minPZT:
            value += self.pzt_per_fsr
        return int(round(value))
        
    def adjustParam(self,errorValue, gain,maxAdjust,direction=1):
        adjust = direction * errorValue * gain
        adjust = min(maxAdjust,max(-maxAdjust, adjust))
        return adjust
        
    def movePZT(self, pztadjust):
        oldPZToffset = Driver.rdFPGA("FPGA_TWGEN", "TWGEN_PZT_OFFSET")
        newPZToffset = int(oldPZToffset + pztadjust)
        newPZToffset = self.checkPZTinRange(newPZToffset)
        Driver.wrFPGA("FPGA_TWGEN", "TWGEN_PZT_OFFSET", newPZToffset)
        #Driver.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1",newPZToffset)
        return oldPZToffset, newPZToffset
        
    def adjustPZTtoNuTarget(self, param=None):
        if self.pztMode == 2: #lock to target
            #param[0] is PZTgain, param[1] is maxadjust
            thisTarget = self.targetMemory[self.targetIndex] / self.targetCounter[self.targetIndex]
            thisDifference = self.targetingMean - thisTarget
            self.pztAdjustGuy =  -(thisDifference  - self.overallTargetAdjust) * self.pzt_per_fsr / self.fsr
            finalPZTadjust =self.adjustParam(self.pztAdjustGuy, param[0], param[1], direction=1)
            oldPZToffset, newPZToffset = self.movePZT(finalPZTadjust)

            if self.verbose:
                if self.newDataAddedToTarget:
                    self.saveTargetsToFile()
                self.newDataAddedToTarget = False
                print '(%.5f (%d): PZT %d ==> %d' % (thisDifference, self.pztAdjustGuy, oldPZToffset, newPZToffset)
                print '-- '*30
        elif self.pztMode == 4: #reset targets
            self.saveTargetsToFile()
            self.resetTargetValues()
            if self.verbose: print 'Target values reset'
    
    def adjustPZTtoNuSpectrum(self, param=None):
        #param[0] is PZTgain, param[1] is maxadjust, frequency shift for adjustment on param[2], centerfrequency is param[3]
        if (self.pztMode == 3) and (abs(self.getFreqTarget() - param[3]) < self.peakProximity): #lock by spectroscopy and check that this line is the target of the scheme
            self.pztAdjustGuy = -param[2] * self.pzt_per_fsr / self.fsr
            finalPZTadjust = self.adjustParam(self.pztAdjustGuy, param[0], param[1], direction=1)
            oldPZToffset, newPZToffset = self.movePZT(finalPZTadjust)
            if self.verbose:
                print '(%d: PZT %d ==> %d' % (self.pztAdjustGuy, oldPZToffset, newPZToffset)

    def setPZTValue(self, param=None):
        if self.pztMode == 5: #set by scheme
            oldPZToffset = Driver.rdFPGA("FPGA_TWGEN", "TWGEN_PZT_OFFSET")
            Driver.wrFPGA("FPGA_TWGEN", "TWGEN_PZT_OFFSET", int(round(self.e3)))
            if self.verbose:
                print 'PZT %d ==> %d' % (oldPZToffset, int(self.e3))
        if self.pztMode == 6: #shift PZT by scheme
            oldPZToffset = Driver.rdFPGA("FPGA_TWGEN", "TWGEN_PZT_OFFSET")
            pztShift = (int(round(self.e3)) - 32768)
            newPZToffset = oldPZToffset + pztShift
            newPZToffset = self.checkPZTinRange(newPZToffset)
            Driver.wrFPGA("FPGA_TWGEN", "TWGEN_PZT_OFFSET", newPZToffset)
            if self.verbose:
                print 'PZT shifted by %d:  %d ==> %d' % (pztShift, oldPZToffset, newPZToffset)
    
    def saveTargetsToFile(self):
        K = self.targetMemory.keys()
        K.sort()
        if len(K) > 0:
            homeDIR = r'C:\Picarro\G2000\InstrConfig\Calibration\InstrCal'
            targetfn = os.path.join(homeDIR, 'TargetValuesForPZT_%d.txt' % time.time())
            with open(targetfn, 'w') as outfile:
                outfile.write('index, sumTargetValues, sumTargetValuesSquared, targetCounter\n')
                for k in K:
                    rowtxt = '%d, %.6f, %.6f, %d\n' % (k, self.targetMemory[k], self.targetMemorySquared[k], self.targetCounter[k])
                    outfile.write(rowtxt)
            if self.verbose: print 'target file saved as %s' % targetfn
    
    def adjustWLM_OFFSET(self,param):
        gain = param[0]
        maxAdjust = param[1]
        error_param = param[2]
        center_nu = param[3] 
        vlaserNum = param[4] #starts with 1
        oldOffset = FreqConv.getWlmOffset(vlaserNum) 
        if (abs(self.getFreqTarget() - center_nu) < self.peakProximity) and (self.wlmMode & 1 == 1): #adjust wlm_offset only when wlmMode allows it
            adjust = self.adjustParam(error_param, gain, maxAdjust, direction=1)
            newOffset = oldOffset + adjust
            FreqConv.setWlmOffset(vlaserNum,float(newOffset))
            if self.verbose: print 'adjusted wlm_offset: %.5f --> %.5f' % (oldOffset, newOffset)
        else:
            newOffset = oldOffset
        return oldOffset, newOffset

    def getFreqTarget(self):
        # Extra4 is set as int(round(nu_center/2e-6))
        return self.e4 * 2e-6

    def adjustNuTarget(self,param=None):
        if self.wlmMode & 2 == 2: #lock nu targeting offset to spectroscopy
            #param[0] is gain, param[1] is maxadjust, param[2] is lock parameter, param[3] is center frequency
            oldTarget = self.overallTargetAdjust 
            if abs(self.getFreqTarget() - param[3]) < self.peakProximity: 
                self.overallTargetAdjust += self.adjustParam(param[2],param[0],param[1],direction=-1)
                if self.verbose:
                    print 'Error: %.5f  NuTarget: %.6f --> %.6f' % (param[2], oldTarget, self.overallTargetAdjust)

class MFC_Control(object):
    def __init__ (self):
        self.MFC1 = RS232.device(dtype = 'Alicat MFC', name = 'Alicat 500 sccm', query = 'A', response = 'A +', nickname = 'MFC1')
        self.MFC2 = RS232.multiAlicat(port=self.MFC1.port, serialDevice=self.MFC1.serialDevice, dtype = 'Alicat MFC', name = 'Alicat 1slm' , query = 'C', response = 'C +', nickname = 'MFC2')
        self.iteration = 0
        self.mfcOutputs = {}
        try:
            res1 = self.MFC1.sendAndParse(self.MFC1.query)          # read MFC and valve states
            time.sleep(0.1)
            res2 = self.MFC2.sendAndParse(self.MFC2.query)
            self.MFCsFound = True
        except:
            self.MFCsFound = False
    
    def readFlows (self, verbose=False):
        if self.MFCsFound:
            res1 = self.MFC1.sendAndParse(self.MFC1.query)          # read MFC and valve states
            time.sleep(0.1)
            res2 = self.MFC2.sendAndParse(self.MFC2.query)
            self.mfcOutputs = dict(res1.items() + res2.items())
            if verbose: print self.mfcOutputs
        
    def setFlows(self, setFlowList, verbose=False):
        if self.MFCsFound:
            # setFlowList is a list of flow setpoints for MFC1 and MFC2.  The i_th element is set, where i = self.iteration % len(setFlowList)
            j = self.iteration % len(setFlowList)
            f1, f2 = setFlowList[j]
            if verbose: print 'step %d: setting MFC flows to %.3f and %.3f' % (j, f1, f2)
            command1 = '%sS%.3f' % (self.MFC1.query,f1)
            command2 = '%sS%.3f' % (self.MFC2.query,f2)
            self.MFC1.sendAndParse(command1)
            time.sleep(0.1)
            self.MFC2.sendAndParse(command2)
            self.iteration += 1


if INIT:
    #fname = os.path.join(BASEPATH,r"./CFADS/spectral library v1_043_CFADS-xx_2009_0813.ini")
    #fname = os.path.join(BASEPATH,r"./FCDS/spectral library FCDS v2_2.ini")
    fname = os.path.join(BASEPATH,r"./FCDS/spectral library HybridCFADS and FCDS v2_2.ini")
    
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
    FreqConv = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,
                                        "FitScript", IsDontCareConnection=False)
    
    BroadbandLocker = BroadbandControl(pzt_per_fsr,fsr,verbose=True)
    FlowGuy = MFC_Control()
    
    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 v2_1 2011 0713.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC VY v2_0 2011 0713.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC FY v2_0 2011 0713.ini")))

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O v1_1 20180922.ini")))     #standard fit with WLM
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O FC v1_1 2008 0304.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O v1_1 20180922.ini")))     #fit with FSR scale
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O FC v1_1 2008 0304.ini")))
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./FCDS/CO2 6056 VC VY v1_1.ini")))            #standard fit with WLM
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./FCDS/CO2 6056 FC FY v1_1.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./FCDS/CO2 6056 VC VY v1_1.ini")))            #fit with FSR scale
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./FCDS/CO2 6056 FC FY v1_1.ini")))
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
    h2o_quality = 0.0
    h2o_pzt_adjust = 0.0

    base_avg = 800
    counter = -25
    last_time = None
    pzt_mean = 0.0
    pzt_median = 0.0
    pzt_stdev = 0.0
    h2o_pzt_adjust = 0.0
    fsr_h2o_adjust = 0.0
    wlm_offset = 0.0
    
init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA

BroadbandLocker.processData(d)
BroadbandLocker.setPZTValue()  #sets to scheme value, only for pztMode = 5
BroadbandLocker.adjustPZTtoNuTarget(param=[0.75,10000])

FlowGuy.readFlows(verbose=False)

if SCHEME_INFO is not None:
    flows = SCHEME_INFO['setFlowList']
    FlowGuy.setFlows(flows, verbose=True)

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
pzt_mean = mean(d.pztValue)
pzt_median = median(d.pztValue)
pzt_stdev = std(d.pztValue)
r = None

goodCH4 = sum((d.groupMeans["waveNumber"] < 6057.5) & (d.groupMeans["waveNumber"] > 6056.5))
goodH2O = sum((d.groupMeans["waveNumber"] < 6058.01) & (d.groupMeans["waveNumber"] > 6057.69))
goodCO2 = sum((d.groupMeans["waveNumber"] < 6056.61) & (d.groupMeans["waveNumber"] > 6056.39))

tstart = time.clock()
RESULT = {}

if goodCH4 > 5:
    init = InitialValues()
    deps = Dependencies()
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
    ch4_tuner_std = std(d.tunerValue)

    
if goodH2O>5: # fit H2O spectrum
    init = InitialValues()
    deps = Dependencies()
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
    
    h2o_75_center = 6057.79180
    combCenter = BroadbandLocker.getFreqTarget()
    rawFreqData = d.fitData["freq"]*1.0
    indexguy = round_((d.fitData["freq"] - combCenter)/fsr)
    d.fitData["freq"] = combCenter + indexguy*fsr
    
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
        
    BroadbandLocker.adjustNuTarget(param=[0.1, 1e-5, fsr_h2o_adjust, h2o_75_center]) 
    BroadbandLocker.adjustPZTtoNuSpectrum(param=[0.3,1000, fsr_h2o_adjust, h2o_75_center])
    old_wlm_offset, wlm_offset = BroadbandLocker.adjustWLM_OFFSET(param=[0.05, 2e-3, h2o_adjust, h2o_75_center, 1])

if goodCO2 > 5:                # CO2 at 6056.5
    init = InitialValues()
    deps = Dependencies()
    #wlm fitting
    d.fitData["freq"] = rawFreqData #reset data to original frequency axis
    init[1002,2] = 0.5*h2o_conc
    init[1003,2] = 0.009041*ch4_conc_ppmv_final
    
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    shift_24 = r["base",3]
    vy_24 = r[24,"y"]

    if (r[24,"peak"] > 5) and (abs(shift_24) < 0.04) and (abs(vy_24-1.86) < 0.5):
        adjust_24 = shift_24
        init[24,"y"] = vy_24
    else:
        adjust_24 = 0.0

    init["base",3] = adjust_24
    r = anCO2[1](d,init,deps)
    ANALYSIS.append(r)
    y_24 = r[24,"y"]
    strength_24 = r[24,"strength"]
    base_24 = r[24,"base"]
    peak_24 = r[24,"peak"]
    #peak24_spec = peak_24 + P24_off + P24_M1*peak0_spec
    co2_conc = 7.718*peak_24
    
    #fsr scale fitting
    init = InitialValues()
    deps = Dependencies()
    co2_24_center = 6056.50640
    combCenter = BroadbandLocker.getFreqTarget()
    indexguy = round_((d.fitData["freq"] - combCenter)/fsr)
    d.fitData["freq"] = combCenter + indexguy*fsr

    init[1002,2] = 0.5*h2o_conc
    init[1003,2] = 0.009041*ch4_conc_ppmv_final
    r = anCO2[2](d,init,deps)
    ANALYSIS.append(r)
    fsr_shift_24 = r["base",3]
    fsr_vy_24 = r[24,"y"]

    if (r[24,"peak"] > 5) and (abs(fsr_shift_24) < 0.04) and (abs(fsr_vy_24-1.86) < 0.5):
        fsr_adjust_24 = fsr_shift_24
        init[24,"y"] = fsr_vy_24
    else:
        fsr_adjust_24 = 0.0

    init["base",3] = fsr_adjust_24
    r = anCO2[3](d,init,deps)
    ANALYSIS.append(r)
    fsr_y_24 = r[24,"y"]
    fsr_strength_24 = r[24,"strength"]
    fsr_base_24 = r[24,"base"]
    fsr_peak_24 = r[24,"peak"]

    fsr_co2_conc = 7.718*fsr_peak_24

    BroadbandLocker.adjustNuTarget(param=[0.1, 1e-5, fsr_adjust_24, co2_24_center]) 
    BroadbandLocker.adjustPZTtoNuSpectrum(param=[0.3,1000, fsr_adjust_24, co2_24_center])
    old_wlm_offset, wlm_offset = BroadbandLocker.adjustWLM_OFFSET(param=[0.05, 2e-3, adjust_24, co2_24_center, 1])


    
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
        RESULT.update({"co2_conc":co2_conc, "y_24":y_24, "strength_24":strength_24, "base_24":base_24,"peak_24":peak_24,
                       "shift_24":shift_24, "vy_24":vy_24, "adjust_24":adjust_24})
        RESULT.update({"fsr_co2_conc":fsr_co2_conc, "fsr_y_24":fsr_y_24, "fsr_strength_24":fsr_strength_24, "fsr_base_24":fsr_base_24,"fsr_peak_24":fsr_peak_24,
                       "fsr_shift_24":fsr_shift_24, "fsr_vy_24":fsr_vy_24, "fsr_adjust_24":fsr_adjust_24})
    except:
        pass
    RESULT.update({"overallTargetAdjust":BroadbandLocker.overallTargetAdjust,"pztMean":pzt_mean, 'pztMedian':pzt_median, 'pztStd':pzt_stdev, 'wlm_offset':wlm_offset})
    RESULT.update({"Extra1":BroadbandLocker.e1, "Extra2":BroadbandLocker.e2, "Extra3":BroadbandLocker.e3, "Extra4":BroadbandLocker.e4, 'CombCenter':BroadbandLocker.getFreqTarget(),
                   "wlmMode":BroadbandLocker.wlmMode, "pztMode":BroadbandLocker.pztMode})
    RESULT.update(d.sensorDict)
    RESULT.update({"species":88,"cavity_pressure":P,"cavity_temperature":T,"solenoid_valves":solValves,
                   "das_temp":dasTemp, "goodCH4":goodCH4, "goodH2O":goodH2O, "goodCO2":goodCO2, "pzt_per_fsr":pzt_per_fsr})
    RESULT.update(FlowGuy.mfcOutputs)
    #for key in RESULT:
    #    print key, RESULT[key]


