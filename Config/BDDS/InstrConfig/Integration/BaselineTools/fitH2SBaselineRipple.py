import numpy
import os.path
import time
import cPickle
from struct import pack
from Host.Common.EventManagerProxy import Log


def fitQuality(sdFit,maxPeak,normPeak,sdTau):
    return numpy.sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

if INIT:
    fname = os.path.join(BASEPATH,r"./spectral library H2S pressure cal.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    analysis = []
    analysis.append(Analysis(os.path.join(BASEPATH,r"./H2S_baseline.ini")))

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
amp_ripp_3 = r[1002,0]
phase_ripp_1 = r[1000,3]
phase_ripp_2 = r[1001,3]
phase_ripp_3 = r[1002,3]
freq_ripp_1 = r[1000,2]
freq_ripp_2 = r[1001,2]
freq_ripp_3 = r[1002,2]
center_ripp_1 = r[1000,1]
center_ripp_2 = r[1001,1]
center_ripp_3 = r[1002,1]
base0 = r["base",0]
base1 = r["base",1]
cm_shift = r["base",3]

RESULT = {'amp_ripp_1':amp_ripp_1, 'amp_ripp_2':amp_ripp_2, 'amp_ripp_3':amp_ripp_3,
          'phase_ripp_1':phase_ripp_1, 'phase_ripp_2':phase_ripp_2, 'phase_ripp_3':phase_ripp_3,
          'freq_ripp_1':freq_ripp_1, 'freq_ripp_2':freq_ripp_2,  'freq_ripp_3':freq_ripp_3,
          'center_ripp_1':center_ripp_1, 'center_ripp_2':center_ripp_2,  'center_ripp_3':center_ripp_3,
          'base0':base0, 'base1':base1,
          'cm_shift':cm_shift,'stddevres':r["std_dev_res"]}
op = file(oname,"ab")
s = cPickle.dumps(RESULT)
op.write(pack('i',len(s)))
op.write(s)
op.close()
