#  Fit script for spectroscopic calibration of the cavity FSR using O2 comb in the 7820 wavenumber region
#  Version 1 started 25 April 2011 by hoffnagle
#  2011 0513 -  Version 2.1 changes the way in which FSR indices are handled

from numpy import arange, mean, std, sqrt, digitize, polyfit
import os.path

if INIT:
    fname = os.path.join(BASEPATH,r"./BCDS/spectral library CO2_comb_6350 v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)

    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_P8.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_P6.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_P4.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_P2.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_R0.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_R2.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_R4.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_R6.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_R8.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_R10.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_R12.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_R14.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./BCDS/FSR_R16.ini")))

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

CO2_refs = [6341.39705,6343.05555,6344.68407,6346.28255,6348.62386,6350.14709,6351.64019,6353.10316,6354.53604,6355.93884,6357.31161,6358.65441,6359.96732]
fitted_refs = []
fitted_centers = []
residuals = []
i = digitize(CO2_refs,fa)
good = (i>0) & (i<len(fa))
k = arange(len(CO2_refs))
i = i[good]
k = k[good]

for j in range(len(i)):
    if (d.fsr_indices[i[j]] > 10) and (d.fsr_indices[i[j]] < (d.fsr_indices[-1] - 10)):
        d.fitData["freq"] -= d.fsr_indices[i[j]]
        r = anCO2[k[j]](d,init,deps)
        ANALYSIS.append(r)
        fitted_refs.append(CO2_refs[k[j]])
        fitted_centers.append(d.fsr_indices[i[j]]+r[0,"center"])
        residuals.append(r["std_dev_res"])
        d.fitData["freq"] += d.fsr_indices[i[j]]

N = len(fitted_centers)
if N > 1:
    lr = polyfit(fitted_centers,fitted_refs,1)

rms = 0
print2("Fitted %d CO2 reference lines" % N)
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
