#  Fit script for spectroscopic calibration of the cavity FSR using water lines in the 5740 wavenumber region (for HCl)
#  Version 1 started 17 July 2015 by hoffnagle
#  2016 0223:  Initialize line centers to match max absorption (to increase capture range with bad wlm cal)
#              Added outputs of WLM interpolated to fitted line centers for information only

from numpy import arange, mean, std, sqrt, digitize, polyfit, argmax, floor
import os.path

if INIT:
    fname = os.path.join(BASEPATH,r"./HCl/spectral library FSRcal v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HCl/FSR_1.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HCl/FSR_2.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HCl/FSR_3.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HCl/FSR_4.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HCl/FSR_5.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HCl/FSR_6.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./HCl/FSR_7.ini")))
    
    out = file("FSR_calibration.txt","w")
    
    def print2(str):
        print str
        print >> out,str

ANALYSIS = []
d = DATA
d.cluster(xColumn='waveNumber',minSize=1)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
# fa is approximate wavenumber, fs is wavenumber regridded with estimated FSR
fa = d.groupMeans["waveNumber"]
fsr_est = (fa[-1]-fa[0])/(len(d.fsr_indices)-1)

d.defineFitData(freq=d.fsr_indices.copy(),loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]

init = InitialValues()
deps = Dependencies()

H2O_refs = [5722.45737,5723.18457,5723.77987,5724.95156,5732.47312,5742.90234,5747.71390]
H2O_shifts = [-0.00821,-0.00129,-0.00716,-0.00160,-0.00573,-0.00555,-0.00890]
fitted_refs = []
fitted_centers = []
residuals = []
wlm_centers = []
dWLM = []
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
        fitted_refs.append(H2O_refs[k[j]]+(P/760.0)*H2O_shifts[k[j]])
        fitted_centers.append(d.fsr_indices[i[j]]+r[0,"center"])
        residuals.append(r["std_dev_res"])
        d.fitData["freq"] += d.fsr_indices[i[j]]

N = len(fitted_centers)
if N > 1:
    lr = polyfit(fitted_centers,fitted_refs,1)

rms = 0        
print2("Fitted %d water reference lines" % N)
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