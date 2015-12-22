#  22 Sep 2015:  Added correction from oxygen sensor -- renamed old results "preO2" and report O2-corrected results as final (jah)

xp = _GLOBALS_["xProcessor"]
xh = xp.xHistory

from numpy import *
from numpy.linalg import inv, norm

# Forward analysis script for interference removal
if _PERSISTENT_["init"]:
    influence_of = {"peak_1a":{}, "peak_41":{}, "peak_2":{},"peak15":{}, "peak_4":{}, "ch4_splinemax":{}, "nh3_conc_ave":{}} 

    test1 = influence_of["peak_1a"]
    test1["peak_1a"] = 1
    test1["peak_41"] = _INSTR_["peak1a_on_peak41"]
    test1["peak_2"] = _INSTR_["peak1a_on_peak2"]
    test1["peak15"] = _INSTR_["peak1a_on_peak15"]
    test1["peak_4"] = _INSTR_["peak1a_on_peak4"]
    test1["ch4_splinemax"] = _INSTR_["peak1a_on_ch4splinemax"]
    test1["nh3_conc_ave"] = _INSTR_["peak1a_on_nh3concave"]

    test1 = influence_of["peak_41"]
    test1["peak_1a"] = _INSTR_["peak41_on_peak1a"]
    test1["peak_41"] = 1
    test1["peak_2"] = 0
    test1["peak15"] = _INSTR_["peak41_on_peak15"]
    test1["peak_4"] = _INSTR_["peak41_on_peak4"]
    test1["ch4_splinemax"] = _INSTR_["peak41_on_ch4splinemax"]
    test1["nh3_conc_ave"] = _INSTR_["peak41_on_nh3concave"]
    
    test1 = influence_of["peak_2"]
    test1["peak_1a"] = 0
    test1["peak_41"] = 0
    test1["peak_2"] = 1
    test1["peak15"] = 0
    test1["peak_4"] = 0
    test1["ch4_splinemax"] = 0
    test1["nh3_conc_ave"] = 0
    
    test1 = influence_of["peak15"]
    test1["peak_1a"] = _INSTR_["peak15_on_peak1a"]
    test1["peak_41"] = _INSTR_["peak15_on_peak41"]
    test1["peak_2"] = 0
    test1["peak15"] = 1
    test1["peak_4"] = 0
    test1["ch4_splinemax"] = _INSTR_["peak15_on_ch4splinemax"]
    test1["nh3_conc_ave"] = 0
    
    test1 = influence_of["peak_4"]
    test1["peak_1a"] = _INSTR_["peak4_on_peak1a"]
    test1["peak_41"] = 0
    test1["peak_2"] = _INSTR_["peak4_on_peak2"]
    test1["peak15"] = 0
    test1["peak_4"] = 1
    test1["ch4_splinemax"] = 0
    test1["nh3_conc_ave"] = 0

    test1 = influence_of["ch4_splinemax"]
    test1["peak_1a"] = _INSTR_["ch4splinemax_on_peak1a"]
    test1["peak_41"] = _INSTR_["ch4splinemax_on_peak41"]
    test1["peak_2"] = _INSTR_["ch4splinemax_on_peak2"]
    test1["peak15"] = _INSTR_["ch4splinemax_on_peak15"]
    test1["peak_4"] = _INSTR_["ch4splinemax_on_peak4"]
    test1["ch4_splinemax"] = 1
    test1["nh3_conc_ave"] = _INSTR_["ch4splinemax_on_nh3concave"]

    test1 = influence_of["nh3_conc_ave"]
    test1["peak_1a"] = _INSTR_["nh3concave_on_peak1a"]
    test1["peak_41"] = _INSTR_["nh3concave_on_peak41"]
    test1["peak_2"] = _INSTR_["nh3concave_on_peak2"]
    test1["peak15"] = _INSTR_["nh3concave_on_peak15"]
    test1["peak_4"] = _INSTR_["nh3concave_on_peak4"]
    test1["ch4_splinemax"] = _INSTR_["nh3concave_on_ch4splinemax"]
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
        corr[xs.indexByName["peak_1a"]] = _INSTR_["nh3concave_peak15_on_peak1a"] * actual[xs.indexByName["nh3_conc_ave"]]*actual[xs.indexByName["peak15"]]+_INSTR_["nh3concave_Quad_peak15_on_peak1a"] * actual[xs.indexByName["nh3_conc_ave"]]*actual[xs.indexByName["peak15"]]*actual[xs.indexByName["peak15"]]
        return corr

    _PERSISTENT_["nonLinCorr"] = nonLinCorr
    _PERSISTENT_["Ainv"] = inv(A)
    print 'Reset averages'
    _PERSISTENT_["average30"]  = []
    _PERSISTENT_["average60"] = []
    _PERSISTENT_["average300"] = []
    _PERSISTENT_["average30dry"]  = []
    _PERSISTENT_["average60dry"] = []
    _PERSISTENT_["average300dry"] = []
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
# Define linear transformations for post-processing

    
    
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
O2 = (_INSTR_["concentration_o2_slope"],_INSTR_["concentration_o2_intercept"])

WD_P1a_linear = _INSTR_["wd_n2o_linear"]
WD_P1a_quad = _INSTR_["wd_n2o_quad"]
WD_P41_linear = _INSTR_["wd_co2_linear"]
WD_P41_quad = _INSTR_["wd_co2_quad"]
WD_CH4_linear = _INSTR_["wd_ch4_linear"]
WD_CH4_quad = _INSTR_["wd_ch4_quad"]

CH4_O2_linear = _INSTR_["ch4_o2_lin"]
CO2_O2_linear = _INSTR_["co2_o2_lin"]
H2O_O2_linear = _INSTR_["h2o_o2_lin"]
N2O_O2_linear = _INSTR_["n2o_o2_lin"]
NH3_O2_linear = _INSTR_["nh3_o2_lin"]
WD_o2_linear = _INSTR_["wd_o2_linear"]
WD_o2_quad = _INSTR_["wd_o2_quad"]
O2_RANGE_MIN = 0.5
O2_RANGE_MAX = 110.0

# Handle options from command line
optDict = eval("dict(%s)" % _OPTIONS_)
g2308 = optDict.get("g2308", True)



n2o = newValues[xs.indexByName["peak_1a"]] / 1.82
h2o_spec = newValues[xs.indexByName["peak15"]] * 0.0177
ch4 = newValues[xs.indexByName["ch4_splinemax"]] / 216.3
nh3 = newValues[xs.indexByName["nh3_conc_ave"]]
n2oConc = applyLinear(n2o,N2O)
timestamp = xs.timestamp
h2o_actual = _INSTR_["h2o_broadening_linear"]*h2o_spec + _INSTR_["h2o_broadening_quad"]*h2o_spec**2

if "O2_CONC" in xs.data:
    o2 = xs.data["O2_CONC"]
    o2 = applyLinear(o2,O2)
    o2_dry = o2 / (1 + WD_o2_linear * h2o_actual + WD_o2_quad * h2o_actual**2)
else:
    o2 = 20.947
    o2_dry = 20.947
if o2 > O2_RANGE_MAX or o2 < O2_RANGE_MIN:
    o2 = 20.947

if g2308:
    co2 = newValues[xs.indexByName["peak_2"]] * 252.9
    
else:
    co2 = newValues[xs.indexByName["peak_41"]] * 8.442
    peak_41_dry = newValues[xs.indexByName["peak_41"]]  / (1 + WD_P41_linear * h2o_spec + WD_P41_quad * h2o_spec**2)
    co2_dry = peak_41_dry * 8.442
    _REPORT_["CO2_dry_preO2"] = applyLinear(co2_dry,CO2)
    _REPORT_["CO2_dry"] = applyLinear(co2_dry,CO2)*(1.0 + CO2_O2_linear*(o2 - 20.947))

_REPORT_["N2O_preO2"] = applyLinear(n2o,N2O)
_REPORT_["CO2_preO2"] = applyLinear(co2,CO2)
_REPORT_["h2o_spec"] = applyLinear(h2o_spec,H2O)
_REPORT_["H2O_preO2"] = applyLinear(h2o_actual,H2O)
_REPORT_["CH4_preO2"] = applyLinear(ch4,CH4)
_REPORT_["NH3_preO2"] = applyLinear(nh3,NH3)

_REPORT_["N2O"] = applyLinear(n2o,N2O)*(1.0 + N2O_O2_linear*(o2 - 20.947))
_REPORT_["CO2"] = applyLinear(co2,CO2)*(1.0 + CO2_O2_linear*(o2 - 20.947))
_REPORT_["H2O"] = applyLinear(h2o_actual,H2O)*(1.0 + H2O_O2_linear*(o2 - 20.947))
_REPORT_["CH4"] = applyLinear(ch4,CH4)*(1.0 + CH4_O2_linear*(o2 - 20.947))
_REPORT_["NH3"] = applyLinear(nh3,NH3)*(1.0 + NH3_O2_linear*(o2 - 20.947))
_REPORT_["O2"] = o2
_REPORT_["O2_dry"] = o2_dry

peak_1a_dry = newValues[xs.indexByName["peak_1a"]] / (1 + WD_P1a_linear * h2o_spec + WD_P1a_quad * h2o_spec**2)
ch4_splinemax_dry = newValues[xs.indexByName["ch4_splinemax"]] / (1 + WD_CH4_linear * 1.20439 * h2o_spec + WD_CH4_quad * 1.20439**2 * h2o_spec**2)
# factor of 1.20439 is to calibrate H2O to CFADS and use Chris' WD values for CH4


n2o_dry = peak_1a_dry / 1.82
ch4_dry = ch4_splinemax_dry / 216.3
n2oconcDry = applyLinear(n2o_dry,N2O)

_REPORT_["N2O_dry_preO2"] = applyLinear(n2o_dry,N2O)
_REPORT_["CH4_dry_preO2"] = applyLinear(ch4_dry,CH4)

_REPORT_["N2O_dry"] = applyLinear(n2o_dry,N2O)*(1.0 + N2O_O2_linear*(o2 - 20.947))
_REPORT_["CH4_dry"] = applyLinear(ch4_dry,CH4)*(1.0 + CH4_O2_linear*(o2 - 20.947))

newN2O30s = boxAverage(_PERSISTENT_["average30"],n2oConc*(1.0 + N2O_O2_linear*(o2 - 20.947)),timestamp,30.0 * 1000.0)
_REPORT_["N2O_30s"] = newN2O30s

newN2O1m = boxAverage(_PERSISTENT_["average60"],n2oConc*(1.0 + N2O_O2_linear*(o2 - 20.947)),timestamp,60.0 * 1000.0)
_REPORT_["N2O_1min"] = newN2O1m


newN2O5m = boxAverage(_PERSISTENT_["average300"],n2oConc*(1.0 + N2O_O2_linear*(o2 - 20.947)),timestamp,300.0 * 1000.0)
_REPORT_["N2O_5min"] = newN2O5m


newN2O30sdry = boxAverage(_PERSISTENT_["average30dry"],n2oconcDry*(1.0 + N2O_O2_linear*(o2 - 20.947)),timestamp,30.0 * 1000.0)
_REPORT_["N2O_dry30s"] = newN2O30sdry


newN2O1mdry = boxAverage(_PERSISTENT_["average60dry"],n2oconcDry*(1.0 + N2O_O2_linear*(o2 - 20.947)),timestamp,60.0 * 1000.0)
_REPORT_["N2O_dry1min"] = newN2O1mdry

newN2O5mdry = boxAverage(_PERSISTENT_["average300dry"],n2oconcDry*(1.0 + N2O_O2_linear*(o2 - 20.947)),timestamp,300.0 * 1000.0)
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

