#  Baseline ripple fitter for isotopic CO2 region at 6152 wvn
#  Initial fitter based on G1000 fit definition
#   8 Mar 2012:  first attempt to improve initial estimate of ripple frequencies using autocorrrelation of baseline

from numpy import *
import os.path
import time
import cPickle
from struct import pack
from Host.Common.EventManagerProxy import Log

def autoCorr2(f,l,df):
    N = len(l)
    lr = polyfit(f,l,1)
    r = l - polyval(lr,f)
    minA = 1e12
    ds = int(0.01/df)
    shift = int(0.1/df)
    while shift < N/2:
        l[0:shift] = 0.0
        l[shift:N] = r[0:N-shift]
        A = sum(l*r)/(N-(shift+1))
        if A < minA:
            minA = A
            s0 = shift
        shift += ds

    l[0:s0] = 0.0
    l[s0:N] = r[0:N-s0]

    r = r+l
    minA = 1e12
    shift = int(0.15/df)
    while shift < (N-s0)/2:
        l[0:s0+shift] = 0.0
        l[s0+shift:N] = r[s0:N-shift]
        A = sum(l*r)/(N-(s0+shift+1))
        if A < minA:
            minA = A
            s1 = shift
        shift += ds
    return (2.0*s0*df,2.0*s1*df)

if INIT:
    fname = os.path.join(BASEPATH,r"./CBDS-5 spectral library + CBDS65 methane + CBDS52 HDO + 18O - v20100630.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    analysis = []
    analysis.append(Analysis(os.path.join(BASEPATH,r"./CBDS-xx baseline ripple CBDS-01.ini")))

    oname = os.path.join(BASEPATH,time.strftime("FitterOutput.dat",time.localtime()))
    file(oname,"wb").close()
    first_fit = 1
    p0 = 1.2
    p1 = 0.6

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=1.5)
d.sparse(maxPoints=20000,width=0.0025,height=400000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.8)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))

if first_fit:
    f = copy(d.fitData["freq"])
    l = copy(d.fitData["loss"])
    df = (f[-1]-f[0])/(len(f)-1)
    print df
    p = autoCorr2(f,l,df)
    print p
    if p[0] < 1.5:
        p0 = p[0]
    if p[1] < 1.5:
        p1 = p[1]
    first_fit = 0

#  THE INITIAL GUESSES FOR RIPPLE PERIOICITIES GO HERE
init[1000,2] = p0
init[1001,2] = p1

init[88,"strength"] = 0.0
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
h2o_peak = r[91,"peak"]
peak87 = r[87,"peak"]
base87 = r[87,"base"]
base88 = r[88,"base"]

if amp_ripp_1 < 0:
    amp_ripp_1 = -amp_ripp_1
    phase_ripp_1 += pi
while phase_ripp_1 < -pi:
    phase_ripp_1 += 2*pi
while phase_ripp_1 > pi:
    phase_ripp_1 -= 2*pi

if amp_ripp_2 < 0:
    amp_ripp_2 = -amp_ripp_2
    phase_ripp_2 += pi
while phase_ripp_2 < -pi:
    phase_ripp_2 += 2*pi
while phase_ripp_2 > pi:
    phase_ripp_2 -= 2*pi

RESULT = {'amp_ripp_1':amp_ripp_1, 'amp_ripp_2':amp_ripp_2,
          'phase_ripp_1':phase_ripp_1, 'phase_ripp_2':phase_ripp_2,
          'freq_ripp_1':freq_ripp_1, 'freq_ripp_2':freq_ripp_2,
          'center_ripp_1':center_ripp_1, 'center_ripp_2':center_ripp_2,
          'base0':base0, 'base1':base1,'h2o_peak':h2o_peak,
          'peak87':peak87,'base87':base87,'base88':base88,
          'cm_shift':cm_shift,'stddevres':r["std_dev_res"]}
op = file(oname,"ab")
s = cPickle.dumps(RESULT)
op.write(pack('i',len(s)))
op.write(s)
op.close()
