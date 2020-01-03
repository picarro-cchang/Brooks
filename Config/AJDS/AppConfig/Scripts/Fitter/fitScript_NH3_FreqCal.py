#  Fit script for spectroscopic calibration of the isotopic water cavity FSR using H2O lines in the 7200 wvn range
#  Frequency assignments are from the measurements of Toth reported on the JPL website.
#  Best frequency measurements are for extremely strong lines => water concentration must be < 20 ppm .
#  Version 1 started 23 Aug 2011 by hoffnagle
#  2012 01 20:  Added lines at lower frequency
#  2012 04 20:  Initialize line centers to match max absorption (to increase capture range with bad wlm cal)
#  2012 12 13:  Adapted to ammonia region
#  2013 07 01:  Modified water frequency assignments based on Hitran 2012 edition (much better uncertainty)

from numpy import arange, mean, std, sqrt, digitize, polyfit, argmax
import os.path

if INIT:
    fname = os.path.join(BASEPATH,r"./NH3/spectral library H2O_comb v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NH3/FSR_4.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NH3/FSR_5.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NH3/FSR_6.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NH3/FSR_7.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NH3/FSR_8.ini")))

    out = file("FSR_calibration.txt","w")

    def print2(str):
        print str
        print >> out,str

ANALYSIS = []
d = DATA
d.cluster(xColumn='waveNumber',minSize=3)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
# fa is approximate wavenumber, fs is wavenumber regridded with estimated FSR
fa = d.groupMeans["waveNumber"]
fsr_est = (fa[-1]-fa[0])/(len(d.fsr_indices)-1)

d.defineFitData(freq=d.fsr_indices.copy(),loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))

init = InitialValues()
deps = Dependencies()

H2O_refs = [6541.28677,6547.16085,6549.76182,6553.93897,6557.38362]
fitted_refs = []
fitted_centers = []
residuals = []
i = digitize(H2O_refs,fa)
good = (i>0) & (i<len(fa))
k = arange(len(H2O_refs))
i = i[good]
k = k[good]

for j in range(len(i)):
    if (d.fsr_indices[i[j]] > 10) and (d.fsr_indices[i[j]] < (d.fsr_indices[-1] - 10)):
        d.fitData["freq"] -= d.fsr_indices[i[j]]
        current_range = abs(d.fitData["freq"])<9
        current_index = d.fitData["freq"][current_range]
        current_loss = d.fitData["loss"][current_range]
        init[0,"center"] = argmax(current_loss)-8
        r = anH2O[k[j]](d,init,deps)
        ANALYSIS.append(r)
        fitted_refs.append(H2O_refs[k[j]])
        fitted_centers.append(d.fsr_indices[i[j]]+r[0,"center"])
        residuals.append(r["std_dev_res"])
        d.fitData["freq"] += d.fsr_indices[i[j]]

N = len(fitted_centers)
if N > 1:
    lr = polyfit(fitted_centers,fitted_refs,1)

rms = 0
print2("Fitted %d H2O reference lines" % N)
print2("Wavenumber    FSR     rms")
for j in range(N):
    print2("%10.5f %8.3f %7.3f" % (fitted_refs[j],fitted_centers[j],residuals[j]))
    df = lr[1]+lr[0]*fitted_centers[j]-fitted_refs[j]
    rms += df**2

if N > 1:
    print2("FSR = %.7f wvn" % lr[0])
    print2("f(0) = %.5f wvn" % lr[1])
    print2("RMS residual = %.5f wvn" % sqrt(rms/N))
else:
    print2("No FSR calibration possible with only %d fitted reference" % N)

out.close()
RESULT = { }
