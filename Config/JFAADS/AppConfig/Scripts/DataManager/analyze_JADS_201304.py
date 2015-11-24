xp = _GLOBALS_["xProcessor"]
xh = xp.xHistory

from numpy import *
from numpy.linalg import inv, norm

# Forward analysis script for interference removal
if _PERSISTENT_["init"]:
    influence_of = {"peak_1a":{}, "peak_41":{}, "peak15":{}, "ch4_splinemax":{}, "nh3_conc_ave":{}} 

    test1 = influence_of["peak_1a"]
    test1["peak_1a"] = 1
    test1["peak_41"] = 2.66e-4
    test1["peak15"] = -0.10495
    test1["ch4_splinemax"] = 0
    test1["nh3_conc_ave"] = -0.24003

    test1 = influence_of["peak_41"]
    test1["peak_1a"] = -3.51e-5
    test1["peak_41"] = 1
    test1["peak15"] = 0.01217
    test1["ch4_splinemax"] = 6.35E-4
    test1["nh3_conc_ave"] = -2.15292E-4

    test1 = influence_of["peak15"]
    test1["peak_1a"] = -3.21E-4
    test1["peak_41"] = -5.07E-4
    test1["peak15"] = 1
    test1["ch4_splinemax"] = -0.00425
    test1["nh3_conc_ave"] = 0

    test1 = influence_of["ch4_splinemax"]
    test1["peak_1a"] = -1.363e-7
    test1["peak_41"] = -3.924e-5
    test1["peak15"] = -2.796e-5
    test1["ch4_splinemax"] = 1
    test1["nh3_conc_ave"] = -5.22e-6

    test1 = influence_of["nh3_conc_ave"]
    test1["peak_1a"] = -1.521e-5
    test1["peak_41"] = 4.571e-5
    test1["peak15"] = 0.00236
    test1["ch4_splinemax"] = -2.998e-5
    test1["nh3_conc_ave"] = 1

    n = len(xp.crossList)
    A = zeros((n,n),dtype=float)
    for i,(c1,_,_) in enumerate(xp.crossList):
        for j,(c2,_,_) in enumerate(xp.crossList):
            A[i,j] = influence_of[c2][c1]
    # Define correction to linear transformation between actual and measured values
    #  as a function acting on the vector of actual values

    def nonLinCorr(actual):
        corr = zeros_like(actual)
        corr[xs.indexByName["peak15"]] = 0.00132 * actual[xs.indexByName["peak_1a"]]**2
        corr[xs.indexByName["peak_1a"]] = 3.22489E-6 * actual[xs.indexByName["peak15"]]**2
        return corr

    _PERSISTENT_["nonLinCorr"] = nonLinCorr
    _PERSISTENT_["Ainv"] = inv(A)
    _PERSISTENT_["init"] = False


xs = xh.popleft()

newValues = asarray(xs.valueArray)
for iter in range(5):
    next = dot(_PERSISTENT_["Ainv"],asarray(xs.valueArray)-_PERSISTENT_["nonLinCorr"](newValues))
    #print iter, norm(next-newValues)/norm(newValues)
    newValues = next

for i,(c,f,v) in enumerate(xp.crossList):
    _REPORT_[c + '_raw'] = xs.valueArray[xs.indexByName[c]]
    _REPORT_[c + '_corr'] = newValues[xs.indexByName[c]]

# Convert corrected peak heights to concentrations
# Define linear transformtions for post-processing
def applyLinear(value,xform):
    return xform[0]*value + xform[1]

CH4 = (_INSTR_["concentration_ch4_slope"],_INSTR_["concentration_ch4_intercept"])
CO2 = (_INSTR_["concentration_co2_slope"],_INSTR_["concentration_co2_intercept"])
H2O = (_INSTR_["concentration_h2o_slope"],_INSTR_["concentration_h2o_intercept"])
N2O = (_INSTR_["concentration_n2o_slope"],_INSTR_["concentration_n2o_intercept"])
NH3 = (_INSTR_["concentration_nh3_slope"],_INSTR_["concentration_nh3_intercept"])
    
n2o = newValues[xs.indexByName["peak_1a"]] / 1.82
co2 = newValues[xs.indexByName["peak_41"]] * 8.442
h2o = newValues[xs.indexByName["peak15"]] * 0.0177
ch4 = newValues[xs.indexByName["ch4_splinemax"]] / 216.3
nh3 = newValues[xs.indexByName["nh3_conc_ave"]]
print nh3
_REPORT_["N2O_raw"] = applyLinear(n2o,N2O)
_REPORT_["CO2"] = applyLinear(co2,CO2)
_REPORT_["H2O"] = applyLinear(h2o,H2O)
_REPORT_["CH4"] = applyLinear(ch4,CH4)
_REPORT_["NH3"] = applyLinear(nh3,NH3)

#peak_1a_dry = newValues[xs.indexByName["peak_1a"]] / (1 + (-0.017011) * h2o + (-3.54611e-4) * h2o**2)
peak_1a_dry = newValues[xs.indexByName["peak_1a"]] / (1 + (-0.0204) * h2o + (-7.986e-4) * h2o**2)
peak_41_dry = newValues[xs.indexByName["peak_41"]]  / (1 + (-0.01589) * h2o + (-5.087e-4) * h2o**2)
ch4_splinemax_dry = newValues[xs.indexByName["ch4_splinemax"]] / (1 + (-0.01155) * h2o + (-4.636E-4) * h2o**2)

n2o_dry = peak_1a_dry / 1.82
co2_dry = peak_41_dry * 8.442
ch4_dry = ch4_splinemax_dry / 216.3

_REPORT_["N2O_raw_dry"] = applyLinear(n2o_dry,N2O)
_REPORT_["CO2_dry"] = applyLinear(co2_dry,CO2)
_REPORT_["CH4_dry"] = applyLinear(ch4_dry,CH4)


_REPORT_["timestamp"] = int(xs.timestamp)

# The following two for loops copy all variables into the forwarded script
for d in xs.data:
    if d == "timestamp": continue
    _REPORT_[d] = xs.data[d]
for d in xs.new_data:
    if d == "timestamp": continue
    _REPORT_[d] = xs.new_data[d]

if xh and xh[0].ready:
    _ANALYZE_[xp.forward_id] = {"new_timestamp":xh[0].timestamp}
