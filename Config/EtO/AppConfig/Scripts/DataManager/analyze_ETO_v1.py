#  Bare-bones analysis script to operate the AVX-9000 analyzer in laser current tuning mode
#  2019 0419:  First draft

import inspect
import os
import sys

def applyLinear(value,xform):
    return xform[0]*value + xform[1]
    
if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm_offset"] = 0.0
    _PERSISTENT_["pzt_offset"] = 32768
    _PERSISTENT_["init"] = False

max_adjust = 5e-5
WLMgain = 0.1
PZTgain = 0.05

# Define linear transformations for post-processing
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])
ETO = (_INSTR_["eto_conc_slope"],_INSTR_["eto_conc_intercept"])
        
if _DATA_["species"] == 181:        
    try:
        _NEW_DATA_["CH4"] = applyLinear(_DATA_["ch4_ppm"],CH4)
        _NEW_DATA_["CO2"] = applyLinear(_DATA_["co2_ppm"],CO2)
        _NEW_DATA_["H2O"] = applyLinear(_DATA_["h2o_pct"],H2O) 
        _NEW_DATA_["ETO"] = applyLinear(_DATA_["eto_ppb"],ETO)         
    
        adjust = _DATA_["wlm_adjust"]*WLMgain #* 0.0
        adjust = min(max_adjust,max(-max_adjust,adjust))
        newOffset = _FREQ_CONV_.getWlmOffset(1) + adjust
        _PERSISTENT_["wlm_offset"] = newOffset
        _FREQ_CONV_.setWlmOffset(1,float(newOffset))
        
        adjust = _DATA_["pzt_adjust"]*PZTgain #* 0.0
        newPZToffset = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER1") + adjust
        while newPZToffset > 45768:
            newPZToffset -= _DATA_["pzt_per_fsr"]
        while newPZToffset < 19768:
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