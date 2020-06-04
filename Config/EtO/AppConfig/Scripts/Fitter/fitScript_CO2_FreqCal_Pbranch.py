#  First fit script for spectroscopic calibration of the cavity FSR using CO2 comb in the 6180-6220 wavenumber region
#   9 Sep 2018:  Branched from methane region fit script

from numpy import arange, mean, std, sqrt, digitize, polyfit, argmax
import os.path

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library CO2_comb v1_1.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P44.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P42.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P40.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P38.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P36.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P34.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P32.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P30.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P28.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P26.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P24.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P22.ini")))	
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P20.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FSR_30013_P18.ini")))
    
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

CO2_refs = [6186.855869,6189.028960,6191.171727,6193.284375,6195.367107,6197.420116,6199.443591,6201.437710,6203.402644,6205.338555,6207.245593,6209.123898,6210.973600,6212.794814]
CO2_shifts = [-0.007489,-0.007440,-0.005880,-0.006740,-0.006750,-0.006280,-0.006610,-0.006770,-0.006750,-0.006680,-0.006380,-0.006340,-0.006320,-0.006290]
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
        current_range = abs(d.fitData["freq"])<9
        current_index = d.fitData["freq"][current_range]
        current_loss = d.fitData["loss"][current_range]
        init[0,"center"] = argmax(current_loss)-8
        init[0,'v'] = 0.367
        r = anCO2[k[j]](d,init,deps)
        ANALYSIS.append(r)
        fitted_refs.append(CO2_refs[k[j]]+(P/760.0)*CO2_shifts[k[j]])
        fitted_centers.append(d.fsr_indices[i[j]]+r[0,"center"])
        residuals.append(r["std_dev_res"])
        d.fitData["freq"] += d.fsr_indices[i[j]]

N = len(fitted_centers)
if N > 1:
    lr = polyfit(fitted_centers,fitted_refs,1)

rms = 0        
print2("Fitted %d CO2 reference lines" % N)
print2("t = %f min" % mean(d.timestamp/60000))
print2("Wavenumber    FSR     rms")
for j in range(N):    
    print2("%10.5f %8.3f %7.3f" % (fitted_refs[j],fitted_centers[j],residuals[j]))
    df = lr[1]+lr[0]*fitted_centers[j]-fitted_refs[j]
    rms += df**2
    
if N > 1:
    print2("FSR = %.8f wvn" % lr[0])
    print2("f(0) = %.5f wvn" % lr[1])
    print2("RMS residual = %.5f wvn" % sqrt(rms/N))
else:
    print2("No FSR calibration possible with only %d fitted reference" % N)
    
#print2(" %.6f  %6.0f  %.6f  %.4f  %.8f" % (mean(d.timestamp/60000), mean(d.pztValue), fitted_refs[8], fitted_centers[8], lr[0]))  # For PZT creep experiment

#out.close()    
RESULT = { }