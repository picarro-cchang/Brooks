#  Fit script for spectroscopic calibration of the isotopic water cavity FSR using H2O lines in the 7200 wvn range
#  Frequency assignments are from the measurements of Toth reported on the JPL website.
#  Best frequency measurements are for extremely strong lines => water concentration must be < 100 ppm .
#  Version 1 started 23 Aug 2011 by hoffnagle

from numpy import arange, mean, std, sqrt, digitize, polyfit
import os.path

if INIT:
    fname = os.path.join(BASEPATH,r"./NBDS/spectral library H2O_comb v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_3.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_4.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_5.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_6.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_8.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_9.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_10.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_11.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_12.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_13.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_14.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./NBDS/FSR_15.ini")))

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

H2O_refs = [6998.80973,6999.59049,6999.97685,7000.64216,7003.73160,7004.22714,7006.12692,7007.03576,7010.54760,7012.69463,7013.17203,7014.56502]
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
    print2("No FSR calibration possible with only %d fitted reference(s)" % N)

out.close()
RESULT = { }
