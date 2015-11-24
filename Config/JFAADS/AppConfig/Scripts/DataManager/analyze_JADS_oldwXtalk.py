xp = _GLOBALS_["xProcessor"]
xh = xp.xHistory

from numpy import *
from numpy.linalg import inv, norm

# Forward analysis script for interference removal
if _PERSISTENT_["init"]:
    influence_of = {"peak_1a":{}, "peak_41":{}, "peak15":{}, "peak_4":{}, "ch4_splinemax":{}, "nh3_conc_ave":{}} 

    test1 = influence_of["peak_1a"]
    test1["peak_1a"] = 1
    test1["peak_41"] = -4.4341E-4
    test1["peak15"] = -0.10495
    test1["peak_4"] = -0.01043
    test1["ch4_splinemax"] = 0
    test1["nh3_conc_ave"] = 0.0277

    test1 = influence_of["peak_41"]
    test1["peak_1a"] = -3.397E-5
    test1["peak_41"] = 1
    test1["peak15"] = 0.01109
    test1["peak_4"] = -2.0774E-6
    test1["ch4_splinemax"] = 6.482E-4
    test1["nh3_conc_ave"] = -2.63E-4

    test1 = influence_of["peak15"]
    test1["peak_1a"] = 0
    test1["peak_41"] = -7.177E-4
    test1["peak15"] = 1
    test1["peak_4"] = 0
    test1["ch4_splinemax"] = -0.00428
    test1["nh3_conc_ave"] = 0
    
    test1 = influence_of["peak_4"]
    test1["peak_1a"] = -0.01409
    test1["peak_41"] = 0
    test1["peak15"] = 0
    test1["peak_4"] = 1
    test1["ch4_splinemax"] = 0
    test1["nh3_conc_ave"] = 0

    test1 = influence_of["ch4_splinemax"]
    test1["peak_1a"] = -1.164E-7
    test1["peak_41"] = -3.5455E-5
    test1["peak15"] = -1.906E-5
    test1["peak_4"] = -1.77E-7
    test1["ch4_splinemax"] = 1
    test1["nh3_conc_ave"] = -1.986E-6

    test1 = influence_of["nh3_conc_ave"]
    test1["peak_1a"] = -1.521e-5
    test1["peak_41"] = 1.5709E-5
    test1["peak15"] = 0.00236
    test1["peak_4"] = 1.959E-5
    test1["ch4_splinemax"] = -3.66E-5
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
        corr[xs.indexByName["peak_1a"]] = 0.00757 * actual[xs.indexByName["peak_4"]]**2
        return corr

    _PERSISTENT_["nonLinCorr"] = nonLinCorr
    _PERSISTENT_["Ainv"] = inv(A)
    print 'Reset averages'
    _PERSISTENT_["average30"]  = []
    _PERSISTENT_["average60"] = []
    _PERSISTENT_["average300"] = []
    _PERSISTENT_["plot"] = False
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
    
def boxAverage(buffer, x, t, tau):
    buffer.append((x,t))  
    while t-buffer[0][1] > tau:
        buffer.pop(0)
    return mean([d for (d,t) in buffer])


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
#now = newValues[xs.indexByName["peak_1a"]][-1].time
n2oConc = applyLinear(n2o,N2O)
timestamp = xs.timestamp
print "timestamp = %s" % timestamp

_REPORT_["N2O"] = applyLinear(n2o,N2O)
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
n2oconcDry = applyLinear(n2o_dry,N2O)

_REPORT_["N2O_dry"] = applyLinear(n2o_dry,N2O)
_REPORT_["CO2_dry"] = applyLinear(co2_dry,CO2)
_REPORT_["CH4_dry"] = applyLinear(ch4_dry,CH4)

newN2O30s = boxAverage(_PERSISTENT_["average30"],n2oConc,timestamp,30.0 * 1000.0)
_REPORT_["N2O_30s"] = newN2O30s

newN2O1m = boxAverage(_PERSISTENT_["average60"],n2oConc,timestamp,60.0 * 1000.0)
_REPORT_["N2O_1min"] = newN2O1m


newN2O5m = boxAverage(_PERSISTENT_["average300"],n2oConc,timestamp,300.0 * 1000.0)
_REPORT_["N2O_5min"] = newN2O5m


newN2O30sdry = boxAverage(_PERSISTENT_["average30"],n2oconcDry,timestamp,30.0 * 1000.0)
_REPORT_["N2O_dry30s"] = newN2O30sdry


newN2O1mdry = boxAverage(_PERSISTENT_["average60"],n2oconcDry,timestamp,60.0 * 1000.0)
_REPORT_["N2O_dry1min"] = newN2O1mdry

newN2O5mdry = boxAverage(_PERSISTENT_["average300"],n2oconcDry,timestamp,300.0 * 1000.0)
_REPORT_["N2O_dry5min"] = newN2O5mdry





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
