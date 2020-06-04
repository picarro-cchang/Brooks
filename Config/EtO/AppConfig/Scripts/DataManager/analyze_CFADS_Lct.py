#  Bare-bones analysis script to operate the CFADS analyzer in laser current tuning mode
#  2013 0620:  Add water vapor to CO2 and incorporate structure of other lct analyses
#  2013 0711:  Add CH4 with w/d correction
#  2014 0325:  Increase max_adjust for WLM offset from 2e-5 to 5e-5 to try to improve tracking when warm box temp is badly off
#  2018 1016:  Incorporate lessons from Baratron experiments, lock all pzts to 6237.4 wvn to mitigate creep

import inspect
import os
import sys

def applyLinear(value,xform):
    return xform[0]*value + xform[1]
    
if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm4_offset"] = 0.0
    _PERSISTENT_["pzt1_offset"] = 32768
    _PERSISTENT_["pzt2_offset"] = 32768
    _PERSISTENT_["pzt4_offset"] = 32768
    _PERSISTENT_["ignore_count"] = 10
    _PERSISTENT_["init"] = False
    
###############
# Get instrument calibration 
###############

CH4spec = _INSTR_["ch4_conc_spec"] 
CO2spec = _INSTR_["co2_conc_spec"] 
H2Ospec = _INSTR_["h2o_conc_spec"] 
       
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])

max_adjust = 5e-5
WLMgain = 0.1
PZTgain = 0.05

if _DATA_["species"] == 10: 
    try:
        adjust = _DATA_["co2_adjust"]*WLMgain
        adjust = min(max_adjust,max(-max_adjust,adjust))
        newOffset = _FREQ_CONV_.getWlmOffset(1) + adjust
        _PERSISTENT_["wlm1_offset"] = newOffset
        _FREQ_CONV_.setWlmOffset(1,float(newOffset))
        adjust = _DATA_["pzt1_adjust"]*PZTgain
        newPZToffset = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER1") + adjust
        while newPZToffset > 45768:
            newPZToffset -= _DATA_["pzt_per_fsr"]
        while newPZToffset < 19768:
            newPZToffset += _DATA_["pzt_per_fsr"]
        _PERSISTENT_["pzt1_offset"] = newPZToffset
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1",newPZToffset)
        _PERSISTENT_["pzt2_offset"] = newPZToffset                       #  CO2 line drives all PZTs
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER2",newPZToffset)
        _PERSISTENT_["pzt4_offset"] = newPZToffset                      
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER4",newPZToffset)
    except:
        pass

    try:
        co2_spec = CO2spec*_DATA_["corrected_fsr_strength14"]
        _NEW_DATA_["CO2"] = applyLinear(co2_spec,CO2)
        last_h2o_conc = _OLD_DATA_["H2O"][-1].value
        _NEW_DATA_["CO2_dry"] = applyLinear(co2_spec,CO2)/(1.0 - 0.01*last_h2o_conc)
    except:
        pass
    try:
        _NEW_DATA_["H2O"] = _OLD_DATA_["H2O"][-1].value
    except:
        _NEW_DATA_["H2O"] = 0.0
    try:
        _NEW_DATA_["CH4"] = _OLD_DATA_["CH4"][-1].value
    except:
        _NEW_DATA_["CH4"] = 0.0
    try:
        _NEW_DATA_["CH4_dry"] = _OLD_DATA_["CH4_dry"][-1].value
    except:
        _NEW_DATA_["CH4_dry"] = 0.0
        
if _DATA_["species"] == 11: 
    try:
        adjust = _DATA_["h2o_adjust"]*WLMgain
        adjust = min(max_adjust,max(-max_adjust,adjust))
        newOffset = _FREQ_CONV_.getWlmOffset(4) + adjust
        _PERSISTENT_["wlm4_offset"] = newOffset
        _FREQ_CONV_.setWlmOffset(4,float(newOffset))
    except:
        pass

    try:
        h2o_spec = H2Ospec*_DATA_["corrected_fsr_strength75"]
        _NEW_DATA_["H2O"] = applyLinear(h2o_spec,H2O)
    except:
        pass
    try:
        _NEW_DATA_["CO2"] = _OLD_DATA_["CO2"][-1].value
    except:
        _NEW_DATA_["CO2"] = 0.0
    try:
        _NEW_DATA_["CO2_dry"] = _OLD_DATA_["CO2_dry"][-1].value
    except:
        _NEW_DATA_["CO2_dry"] = 0.0
    try:
        _NEW_DATA_["CH4"] = _OLD_DATA_["CH4"][-1].value
    except:
        _NEW_DATA_["CH4"] = 0.0
    try:
        _NEW_DATA_["CH4_dry"] = _OLD_DATA_["CH4_dry"][-1].value
    except:
        _NEW_DATA_["CH4_dry"] = 0.0
        
if _DATA_["species"] == 25: 
    try:
        adjust = _DATA_["ch4_adjust"]*WLMgain
        adjust = min(max_adjust,max(-max_adjust,adjust))
        newOffset = _FREQ_CONV_.getWlmOffset(2) + adjust
        _PERSISTENT_["wlm2_offset"] = newOffset
        _FREQ_CONV_.setWlmOffset(2,float(newOffset))
    except:
        pass
        
    try:
        ch4_spec = CH4spec*_DATA_["corrected_fsr_strength61"]
        _NEW_DATA_["CH4"] = applyLinear(ch4_spec,CH4)
        last_h2o_conc = _OLD_DATA_["H2O"][-1].value
        _NEW_DATA_["CH4_dry"] = applyLinear(ch4_spec,CH4)/(1.0 - 0.01*last_h2o_conc)
    except:
        pass
        
    try:
        _NEW_DATA_["CO2"] = _OLD_DATA_["CO2"][-1].value
    except:
        _NEW_DATA_["CO2"] = 0.0
    try:
        _NEW_DATA_["CO2_dry"] = _OLD_DATA_["CO2_dry"][-1].value
    except:
        _NEW_DATA_["CO2_dry"] = 0.0
    try:
        _NEW_DATA_["H2O"] = _OLD_DATA_["H2O"][-1].value
    except:
        _NEW_DATA_["H2O"] = 0.0

if _PERSISTENT_["ignore_count"] > 0:
    _PERSISTENT_["ignore_count"] = _PERSISTENT_["ignore_count"] - 1
    
else:   
    for k in _DATA_.keys():
        _REPORT_[k] = _DATA_[k]

    for k in _NEW_DATA_.keys():
        _REPORT_[k] = _NEW_DATA_[k]

    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
    _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    _REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
    _REPORT_["pzt1_offset"] = _PERSISTENT_["pzt1_offset"]
    _REPORT_["pzt2_offset"] = _PERSISTENT_["pzt2_offset"]
    _REPORT_["pzt4_offset"] = _PERSISTENT_["pzt4_offset"]