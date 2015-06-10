#  Baseline ripple fitter for N2O region at 6562 wvn

from numpy import *
import os.path
import time
import cPickle
from struct import pack

#   Define some frequencies (in wavenumbers) for the autocorellation routine that sets initial periodicities

minPeriod = 0.25
maxPeriod = 1.3
dPeriod = 0.01

def autoCorr2(f,l,df):
    N = len(l)
    lr = polyfit(f,l,1)
    r = l - polyval(lr,f)
    minA = 1e12
    ds = int(dPeriod/df)
    shift = int(minPeriod/df)
    maxShift = int(0.5*maxPeriod/df)
    if maxShift > (N/2):
        maxShift = N/2
    while shift < maxShift:
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
    shift = int(minPeriod/df)
    maxShift = int(0.5*maxPeriod/df)
    if maxShift > (N-s0)/2:
        maxShift = (N-s0)/2
    while shift < maxShift:
        l[0:s0+shift] = 0.0
        l[s0+shift:N] = r[s0:N-shift]
        A = sum(l*r)/(N-(s0+shift+1))
        if A < minA:
            minA = A
            s1 = shift
        shift += ds
    return (2.0*s0*df,2.0*s1*df)

if INIT:
    fname = os.path.join(BASEPATH,r"./JADS spectral library v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    analysis = []
    analysis.append(Analysis(os.path.join(BASEPATH,r"./JADS-xx baseline ripple 1frequency.ini")))
    analysis.append(Analysis(os.path.join(BASEPATH,r"./JADS-xx baseline ripple v1_1.ini")))

    oname = os.path.join(BASEPATH,time.strftime("FitterOutput.dat",time.localtime()))
    file(oname,"wb").close()
    first_fit = 1
    p0 = 1.2
    p1 = 0.6

init = InitialValues()
deps = Dependencies()
ANALYSIS = []
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.20,maxVal=5.0)
d.sparse(maxPoints=20000,width=0.0025,height=400000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=3)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))

P = d["cavitypressure"]
T = d["cavitytemperature"]

if first_fit:
    f = copy(d.fitData["freq"])
    l = copy(d.fitData["loss"])
    df = (f[-1]-f[0])/(len(f)-1)
    p = autoCorr2(f,l,df)
    if p[0] < 1.5:
        p0 = p[0]
    if p[1] < 1.5:
        p1 = p[1]
    first_fit = 0

    init[30,"strength"] = init[31,"strength"] = 0.0
    init[1000,2] = p0
    r = analysis[0](d,init,deps)
    ANALYSIS.append(r)
    if r["std_dev_res"] < 0.05:
        full_fit = False
    else:
        full_fit = True

#  THE INITIAL GUESSES FOR RIPPLE PERIOICITIES GO HERE
init[1000,2] = p0
init[1001,2] = p1
init[30,"strength"] = init[31,"strength"] = 0.0
if full_fit:
    r = analysis[1](d,init,deps)
    ANALYSIS.append(r)
else:
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
h2o_peak = r[31,"peak"]

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
          'base0':base0, 'base1':base1,'h2o_peak':h2o_peak,'cm_shift':cm_shift,
          'stddevres':r["std_dev_res"],'cavity_pressure':P,'cavity_temperature':T}
op = file(oname,"ab")
s = cPickle.dumps(RESULT)
op.write(pack('i',len(s)))
op.write(s)
op.close()
