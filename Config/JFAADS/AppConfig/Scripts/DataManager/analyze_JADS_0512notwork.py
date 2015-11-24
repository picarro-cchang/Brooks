xp = _GLOBALS_["xProcessor"]
xh = xp.xHistory

import os  # for ChemDetect
import sys # for ChemDetect
import inspect # for ChemDetect
from numpy import *
from numpy.linalg import inv, norm

here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)
from Chemdetect.instructionprocess import InstructionProcess # for ChemDetect
from Host.Common.CustomConfigObj import CustomConfigObj # for ChemDetect

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
    print 'Reset averages'
    _PERSISTENT_["average30"]  = []
    _PERSISTENT_["average60"] = []
    _PERSISTENT_["average300"] = []
    _PERSISTENT_["plot"] = False
    _PERSISTENT_["init"] = False
    
        # For ChemDetect
    _PERSISTENT_["chemdetect_inst"] = InstructionProcess()
    configFile = os.path.join(here,"..\..\..\InstrConfig\Calibration\InstrCal\ChemDetect\ChemDetect.ini")
    configPath = os.path.split(configFile)[0]
    config = CustomConfigObj(configFile) 
    ChemDetect_FileName = config.get("Main", "ChemDetect_FileName") # Get the ChemDetect excel file name from the ini file
    print "ChemDetect_FileName = ", ChemDetect_FileName
    _PERSISTENT_["chemdetect_inst"].load_set_from_csv(os.path.join(configPath,ChemDetect_FileName))
                                                       # need to replace with self.instruction_path
    _PERSISTENT_["ChemDetect_previous"] = 0.0 


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
_NEW_DATA_["N2O_raw"] = applyLinear(n2o,N2O)
_REPORT_["N2O_raw"] = applyLinear(n2o,N2O)
_REPORT_["CO2"] = applyLinear(co2,CO2)
_REPORT_["H2O"] = applyLinear(h2o,H2O)
_REPORT_["CH4"] = applyLinear(ch4,CH4)
_REPORT_["NH3"] = applyLinear(nh3,NH3)
print 'nh3_conc_ave from fitter = ', newValues[xs.indexByName["nh3_conc_ave"]]
#peak_1a_dry = newValues[xs.indexByName["peak_1a"]] / (1 + (-0.017011) * h2o + (-3.54611e-4) * h2o**2)
peak_1a_dry = newValues[xs.indexByName["peak_1a"]] / (1 + (-0.0204) * h2o + (-7.986e-4) * h2o**2)
peak_41_dry = newValues[xs.indexByName["peak_41"]]  / (1 + (-0.01589) * h2o + (-5.087e-4) * h2o**2)
ch4_splinemax_dry = newValues[xs.indexByName["ch4_splinemax"]] / (1 + (-0.01155) * h2o + (-4.636E-4) * h2o**2)

n2o_dry = peak_1a_dry / 1.82
co2_dry = peak_41_dry * 8.442
ch4_dry = ch4_splinemax_dry / 216.3
n2oconcDry = applyLinear(n2o_dry,N2O)

_REPORT_["N2O_raw_dry"] = applyLinear(n2o_dry,N2O)
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

print 'N2O  res = ',  _DATA_["res"]
try: # new ChemDetect section    
    Cor_res_CO2 = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_res_CO2']
    Cor_res_H2O = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_res_H2O']
    #_NEW_DATA_["res2"] = _DATA_["res"] - Cor_res_CO2*_NEW_DATA_["CO2"] - Cor_res_H2O*_NEW_DATA_["H2O"]
    _NEW_DATA_["res2"] = _DATA_["res"] # there is no H2O here. use res2=res
    a0_res2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a0_res2']
    a1_res2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a1_res2']

    res2_fit = a0_res2 + _NEW_DATA_["N2O_raw"] * a1_res2
    _NEW_DATA_["res2_diff"] = _NEW_DATA_["res2"] - res2_fit
    _NEW_DATA_["res2_a1"] = (_NEW_DATA_["res2"] - a0_res2) / _NEW_DATA_["N2O_raw"]    
    print 'res2_diff = ', _NEW_DATA_["res2_diff"]
    #print 'res2_a1=', _NEW_DATA_["res2_a1] 
except:
    pass
# Save all the variables defined in the _OLD_DATA_  and  _NEW_DATA_ arrays in the
# _PERSISTENT_ arrays so that they can be used in the ChemDetect spreadsheet.
for colname in _OLD_DATA_:    #  new ChemDetect section
    _PERSISTENT_["chemdetect_inst"].current_var_values[colname] = _OLD_DATA_[colname][-1].value     
print 'Line 193  N2O_raw = ', _NEW_DATA_["N2O_raw"]   # _REPORT_["N2O_raw"]     
for colname in _NEW_DATA_:    
    _PERSISTENT_["chemdetect_inst"].current_var_values[colname] = _NEW_DATA_[colname]
     
#if _OLD_DATA_["species"][-1].value == 47:
_PERSISTENT_["chemdetect_inst"].process_set()
  
if _PERSISTENT_["chemdetect_inst"].current_var_values['RED'] == True:
    print "WARNING: ChemDetect Status is RED"

#if _DATA_["species"] in TARGET_SPECIES:
  #if _OLD_DATA_["species"][-1].value == 47:
print ' '
print 'line 206 N2O_raw = ', _NEW_DATA_["N2O_raw"]
print 'ChemDetect: NOTOK_res2         = ', _PERSISTENT_["chemdetect_inst"].current_var_values['NOTOK_res2']
    
if _PERSISTENT_["chemdetect_inst"].current_var_values['RED'] == True:
    _REPORT_["ChemDetect"] = 1.0  # BAD data
else:
        _REPORT_["ChemDetect"] = 0.0  # Good data 
  #else:
  #  _REPORT_["ChemDetect"] = _PERSISTENT_["ChemDetect_previous"]

print "_REPORT_[ChemDetect] = ", _REPORT_["ChemDetect"]    
_PERSISTENT_["ChemDetect_previous"] = _REPORT_["ChemDetect"]    


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
