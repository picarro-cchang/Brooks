#  Fit script for spectroscopic calibration of the cavity FSR using C2H2 lines in the 6565 wvn range
#  Frequency assignments are from the measurements of Madei et al.
#  Version 1 started 8 Sep 2011 by hoffnagle
#  2012 1025:  Initialize line centers to match max absorption.  Try to increase capture range.

from numpy import arange, mean, std, sqrt, digitize, polyfit, argmax
import os.path

if INIT:
    fname = os.path.join(BASEPATH,r"./JADS/spectral library N2O_comb v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anN2O = []
    #anC2H2.append(Analysis(os.path.join(BASEPATH,r"./JADS/R2.ini")))
    #anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P6.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P7.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P8.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P9.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P10.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P11.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P12.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P13.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P14.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P15.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P16.ini")))
    anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P17.ini")))
    #anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P18.ini")))
    #anN2O.append(Analysis(os.path.join(BASEPATH,r"./JADS/P19.ini")))

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

#N2O_refs = [6575.51446,6574.55202,6573.56886,6572.56499,6571.54040,6570.49511,6569.42912,6568.34243,6567.23504,6566.10697,6564.95821,6563.78877,6562.59866,6561.38788]
N2O_refs = [6574.55202,6573.56886,6572.56499,6571.54040,6570.49511,6569.42912,6568.34243,6567.23504,6566.10697,6564.95821,6563.78877]
fitted_refs = []
fitted_centers = []
residuals = []
i = digitize(N2O_refs,fa)
good = (i>0) & (i<len(fa))
k = arange(len(N2O_refs))
i = i[good]
k = k[good]

for j in range(len(i)):
    if (d.fsr_indices[i[j]] > 10) and (d.fsr_indices[i[j]] < (d.fsr_indices[-1] - 10)):
        d.fitData["freq"] -= d.fsr_indices[i[j]]
        current_range = abs(d.fitData["freq"])<9
        current_index = d.fitData["freq"][current_range]
        current_loss = d.fitData["loss"][current_range]
        init[0,"center"] = argmax(current_loss)-8
        r = anN2O[k[j]](d,init,deps)
        ANALYSIS.append(r)
        fitted_refs.append(N2O_refs[k[j]])
        fitted_centers.append(d.fsr_indices[i[j]]+r[0,"center"])
        residuals.append(r["std_dev_res"])
        d.fitData["freq"] += d.fsr_indices[i[j]]

N = len(fitted_centers)
if N > 1:
    lr = polyfit(fitted_centers,fitted_refs,1)

rms = 0
print2("Fitted %d N2O reference lines" % N)
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
