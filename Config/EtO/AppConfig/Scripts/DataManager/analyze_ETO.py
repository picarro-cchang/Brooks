#  Bare-bones analysis script to operate the AVX-9000 analyzer in laser current tuning mode
#  2019 0419:  First draft
#  2019 1202:  Added cross-talk corrections based on 1D tests with AVX80-9004
#  2019 1203:  Added time averages for ethylene oxide; changed keyword "ETO" to "EtO"
#  2020 0114:  Added cross-talk correction for ammonia to EtO based on measurments of 13 Jan 2020
#  2020 0409:  Added many more cross-talk correction terms based on 2D tests

import inspect
import os
import sys
from numpy import mean

def applyLinear(value,xform):
    return xform[0]*value + xform[1]
    
def boxAverage(buffer,x,t,tau):
    buffer.append((x,t))
    while t-buffer[0][1] > tau:
        buffer.pop(0)
    return mean([d for (d,t) in buffer])
    
if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm_offset"] = 0.0
    _PERSISTENT_["pzt_offset"] = 32768
    _PERSISTENT_["buffer30"]  = []
    _PERSISTENT_["buffer120"] = []
    _PERSISTENT_["buffer300"] = []
    _PERSISTENT_["init"] = False

max_adjust = 5e-5
WLMgain = 0.1
PZTgain = 0.05

O2_RANGE_MIN = -0.1
O2_RANGE_MAX = 110.0

if "O2_CONC" in _DATA_:
    o2 = _DATA_["O2_CONC"]
    o2_dry = o2 / (1 + _DATA_["h2o_pct"])
else:
    o2 = 20.947
    o2_dry = 20.947
if o2 > O2_RANGE_MAX or o2 < O2_RANGE_MIN:
    o2 = 20.947

if "O2_CONC" in _DATA_:
    o2 = _DATA_["O2_CONC"]
    o2_dry = o2 / (1 + _DATA_["h2o_pct"])
    _NEW_DATA_["O2"] = o2
    _NEW_DATA_["O2_dry"] = o2_dry


# Define linear transformations for post-processing
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])
ETO = (_INSTR_["eto_conc_slope"],_INSTR_["eto_conc_intercept"])
NH3 = (_INSTR_["nh3_conc_slope"],_INSTR_["nh3_conc_intercept"])

# Import cross-talk and parameters
H2O_to_ETO_lin = _INSTR_["H2O_to_ETO_linear"]
H2O_to_ETO_quad = _INSTR_["H2O_to_ETO_quadratic"]
CH4_to_ETO_lin = _INSTR_["CH4_to_ETO_linear"]
CH4_to_ETO_quad = _INSTR_["CH4_to_ETO_quadratic"]
CH4_water_bilin = _INSTR_["CH4_water_bilinear"]
M2H_to_ETO = _INSTR_["CH4_quadratic_water_linear"]
MH2_to_ETO = _INSTR_["CH4_linear_water_quadratic"]
CO2_to_ETO_lin = _INSTR_["CO2_to_ETO_linear"]
CO2_to_ETO_quad = _INSTR_["CO2_to_ETO_quadratic"]
CO2_water_bilin = _INSTR_["CO2_water_bilinear"]
CH2_to_ETO = _INSTR_["CO2_linear_water_quadratic"]
NH3_to_ETO_lin = _INSTR_["NH3_to_ETO_linear"]

H2O_to_NH3_lin = _INSTR_["H2O_to_NH3_linear"]
H2O_to_NH3_quad = _INSTR_["H2O_to_NH3_quadratic"]
CH4_to_NH3_lin = _INSTR_["CH4_to_NH3_linear"]
CO2_to_NH3_lin = _INSTR_["CO2_to_NH3_linear"]
        
if _DATA_["species"] == 181:        
    try:
        eto_crosstalk_corrected = _DATA_["eto_ppb"] + _DATA_["ch4_ppm"]*CH4_to_ETO_lin + _DATA_["ch4_ppm"] * _DATA_["ch4_ppm"]*CH4_to_ETO_quad + _DATA_["h2o_pct"]*H2O_to_ETO_lin + _DATA_["h2o_pct"] * _DATA_["h2o_pct"]*H2O_to_ETO_quad + _DATA_["co2_ppm"]*CO2_to_ETO_lin + _DATA_["co2_ppm"] * _DATA_["co2_ppm"]*CO2_to_ETO_quad + _DATA_["ch4_ppm"]*_DATA_["h2o_pct"]*CH4_water_bilin + _DATA_["co2_ppm"]*_DATA_["h2o_pct"]*CO2_water_bilin + _DATA_["nh3_ppb"]*NH3_to_ETO_lin
        eto_crosstalk_corrected = eto_crosstalk_corrected + _DATA_["ch4_ppm"]*_DATA_["ch4_ppm"]*_DATA_["h2o_pct"]*M2H_to_ETO + _DATA_["ch4_ppm"]*_DATA_["h2o_pct"]*_DATA_["h2o_pct"]*MH2_to_ETO + _DATA_["co2_ppm"]*_DATA_["h2o_pct"]*_DATA_["h2o_pct"]*CH2_to_ETO
        temp = applyLinear(eto_crosstalk_corrected,ETO)
        _NEW_DATA_["EtO"] = temp
        
        nh3_crosstalk_corrected = _DATA_["nh3_ppb"] + _DATA_["h2o_pct"]*H2O_to_NH3_lin + _DATA_["h2o_pct"] * _DATA_["h2o_pct"]*H2O_to_NH3_quad + _DATA_["ch4_ppm"]*CH4_to_NH3_lin + _DATA_["co2_ppm"]*CO2_to_ETO_lin
        _NEW_DATA_["NH3"] = applyLinear(nh3_crosstalk_corrected,NH3)
        
        _NEW_DATA_["CH4"] = applyLinear(_DATA_["ch4_ppm"],CH4)
        _NEW_DATA_["CO2"] = applyLinear(_DATA_["co2_ppm"],CO2)
        _NEW_DATA_["H2O"] = applyLinear(_DATA_["h2o_pct"],H2O)
        
        now = _OLD_DATA_["EtO"][-2].time
        _NEW_DATA_["EtO_30s"] = boxAverage(_PERSISTENT_["buffer30"],temp,now,30)
        _NEW_DATA_["EtO_2min"] = boxAverage(_PERSISTENT_["buffer120"],temp,now,120)
        _NEW_DATA_["EtO_5min"] = boxAverage(_PERSISTENT_["buffer300"],temp,now,300)
        
        adjust = _DATA_["wlm_adjust"]*WLMgain
        adjust = min(max_adjust,max(-max_adjust,adjust))
        newOffset = _FREQ_CONV_.getWlmOffset(1) + adjust
        _PERSISTENT_["wlm_offset"] = newOffset
        _FREQ_CONV_.setWlmOffset(1,float(newOffset))
        
        adjust = _DATA_["pzt_adjust"]*PZTgain
        newPZToffset = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER1") + adjust
        while newPZToffset > 32768 + 1.2 * _DATA_["pzt_per_fsr"]: #45768:
            newPZToffset -= _DATA_["pzt_per_fsr"]
        while newPZToffset < 32768 - 1.2 * _DATA_["pzt_per_fsr"]: #19768:
            newPZToffset += _DATA_["pzt_per_fsr"]
        _PERSISTENT_["pzt_offset"] = newPZToffset
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1",newPZToffset)
    except:
        pass
        
for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]

_REPORT_["wlm_offset"] = _PERSISTENT_["wlm_offset"]
_REPORT_["pzt_offset"] = _PERSISTENT_["pzt_offset"]