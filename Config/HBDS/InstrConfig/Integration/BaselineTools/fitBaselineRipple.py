import numpy
import os.path
import time
import cPickle
from struct import pack
from Host.Common.EventManagerProxy import Log

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
    return numpy.sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

if INIT:
    fname = os.path.join(BASEPATH,r"./spectral library v1_045_HBDS02_20080226.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    analysis = []
    analysis.append(Analysis(os.path.join(BASEPATH,r"./HBDS-xx baseline ripple HBDS-21.ini")))

    cm_shift_ave = 0.0
    galpeak_11_ave = 0.0
    oname = os.path.join(BASEPATH,time.strftime("FitterOutput.dat",time.localtime()))
    file(oname,"wb").close()
    last_time = None

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.sparse(maxPoints=20000,width=0.0025,height=400000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.8)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/numpy.sqrt(d.groupSizes))

r = analysis[0](d,init,deps)
ANALYSIS.append(r)

amp_ripp_1 = r[1000,0]
amp_ripp_2 = r[1001,0]
amp_ripp_3 = r[1002,0]
phase_ripp_1 = r[1000,3]
phase_ripp_2 = r[1001,3]
phase_ripp_3 = r[1002,3]
freq_ripp_1 = r[1000,2]
freq_ripp_2 = r[1001,2]
freq_ripp_3 = r[1002,2]
base0 = r["base",0]
base1 = r["base",1]
base3 = r["base",3]
h2o_spline_amp = r[1002,2]
splinemax = r[1002,"peak",7183.62,7183.72]
h2o_ppmv = 7.546*splinemax

RESULT = {'amp_ripp_1':amp_ripp_1, 'amp_ripp_2':amp_ripp_2, 'amp_ripp_3':amp_ripp_3,
          'phase_ripp_1':phase_ripp_1, 'phase_ripp_2':phase_ripp_2, 'phase_ripp_3':phase_ripp_3,
          'freq_ripp_1':freq_ripp_1, 'freq_ripp_2':freq_ripp_2, 'freq_ripp_3':freq_ripp_3,
          'base0':base0, 'base1':base1, 'base3':base3, 'h2o_spline_amp':h2o_spline_amp,
          'splinemax':splinemax, 'h2o_ppmv':h2o_ppmv, 'stddevres':r["std_dev_res"]}
op = file(oname,"ab")
s = cPickle.dumps(RESULT)
op.write(pack('i',len(s)))
op.write(s)
op.close()
