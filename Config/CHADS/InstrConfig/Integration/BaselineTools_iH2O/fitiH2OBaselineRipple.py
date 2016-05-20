import numpy
import os.path
import time
import cPickle
from struct import pack
from Host.Common.EventManagerProxy import Log


def fitQuality(sdFit,maxPeak,normPeak,sdTau):
    return numpy.sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

if INIT:
    fname = os.path.join(BASEPATH,r"./CHADS_N2_spectral_library_v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    analysis = []
    analysis.append(Analysis(os.path.join(BASEPATH,r"./CHADS_iH2O_baseline.ini")))

    oname = os.path.join(BASEPATH,time.strftime("FitterOutput.dat",time.localtime()))
    file(oname,"wb").close()

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.30,maxVal=20.0)
d.sparse(maxPoints=20000,width=0.0025,height=400000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/numpy.sqrt(d.groupSizes))

r = analysis[0](d,init,deps)
ANALYSIS.append(r)

amp_ripp_1 = r[1000,0]
amp_ripp_2 = r[1001,0]
phase_ripp_1 = r[1000,3]
phase_ripp_2 = r[1001,3]
freq_ripp_1 = r[1000,2]
freq_ripp_2 = r[1001,2]
center_ripp_1 = r[1000,1]
center_ripp_2 = r[1001,1]
base0 = r["base",0]
base1 = r["base",1]
cm_shift = r["base",3]
peak10 = r[10,"peak"]
peak12 = r[12,"peak"]
peak13 = r[13,"peak"]
y10 = r[10,"y"]
h2o_ppm = 32.4*peak10

RESULT = {'amp_ripp_1':amp_ripp_1, 'amp_ripp_2':amp_ripp_2,
          'phase_ripp_1':phase_ripp_1, 'phase_ripp_2':phase_ripp_2,
          'freq_ripp_1':freq_ripp_1, 'freq_ripp_2':freq_ripp_2,
          'center_ripp_1':center_ripp_1, 'center_ripp_2':center_ripp_2,
          'base0':base0, 'base1':base1,'peak10':peak10,'y10':y10,
          'peak12':peak12,'peak13':peak13,'h2o_ppm':h2o_ppm,
          'cm_shift':cm_shift,'stddevres':r["std_dev_res"]}
op = file(oname,"ab")
s = cPickle.dumps(RESULT)
op.write(pack('i',len(s)))
op.write(s)
op.close()
