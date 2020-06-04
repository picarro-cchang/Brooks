#  Bare-bones analysis script to operate the CFADS analyzer in laser current tuning mode
#  2013 0620:  Add water vapor to CO2 and incorporate structure of other lct analyses
#  2013 0711:  Add CH4 with w/d correction
#  2014 0325:  Increase max_adjust for WLM offset from 2e-5 to 5e-5 to try to improve tracking when warm box temp is badly off
#  2018 0927:  First cut at an analysis script specifically for a CFADS "spectroscopic manometer"

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
    _PERSISTENT_["init"] = False

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
    except:
        pass

    try:
        _NEW_DATA_["CO2"] = 0.2*_DATA_["corrected_fsr_strength14"]
        last_h2o_conc = 0.000041725*_DATA_["corrected_fsr_strength75"]
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
        _NEW_DATA_["H2O"] = _OLD_DATA_["H2O"][-1].value
    except:
        _NEW_DATA_["H2O"] = 0.0
        
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
        _NEW_DATA_["H2O"] = 0.0041725*_DATA_["corrected_fsr_strength75"]
    except:
        _NEW_DATA_["H2O"] = 0.0
    try:
        _NEW_DATA_["CO2"] = _OLD_DATA_["CO2"][-1].value
    except:
        _NEW_DATA_["CO2"] = 0.0
        
if _DATA_["species"] in [12,13]: 
    try:
        adjust = _DATA_["ch4_adjust"]*WLMgain
        adjust = min(max_adjust,max(-max_adjust,adjust))
        newOffset = _FREQ_CONV_.getWlmOffset(2) + adjust
        _PERSISTENT_["wlm2_offset"] = newOffset
        _FREQ_CONV_.setWlmOffset(2,float(newOffset))
    except:
        pass
        
    try:
        _NEW_DATA_["CO2"] = _OLD_DATA_["CO2"][-1].value
    except:
        _NEW_DATA_["CO2"] = 0.0
    try:
        _NEW_DATA_["H2O"] = _OLD_DATA_["H2O"][-1].value
    except:
        _NEW_DATA_["H2O"] = 0.0

if _DATA_["species"] == 12:        
    try:
        adjust = _DATA_["pzt2_adjust"]*PZTgain                          #  For water self-broadening only use pzt4_adjust, otherwise pzt2_adjust
        newPZToffset = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER2") + adjust
        while newPZToffset > 45768:
            newPZToffset -= _DATA_["pzt_per_fsr"]
        while newPZToffset < 19768:
            newPZToffset += _DATA_["pzt_per_fsr"]
        _PERSISTENT_["pzt2_offset"] = newPZToffset
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER2",newPZToffset)
        _PERSISTENT_["pzt4_offset"] = newPZToffset                       #  CO2 line drives all PZTs
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER4",newPZToffset)
    except:
        pass
        
if _DATA_["species"] in [25]:                                            #  For line shape experiment only
    try:
        adjust = _DATA_["ch4_adjust"]*WLMgain
        adjust = min(max_adjust,max(-max_adjust,adjust))
        newOffset = _FREQ_CONV_.getWlmOffset(2) + adjust
        _PERSISTENT_["wlm2_offset"] = newOffset
        _FREQ_CONV_.setWlmOffset(2,float(newOffset))
        adjust = _DATA_["pzt2_adjust"]*PZTgain
        newPZToffset = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER2") + adjust
        while newPZToffset > 45768:
            newPZToffset -= _DATA_["pzt_per_fsr"]
        while newPZToffset < 19768:
            newPZToffset += _DATA_["pzt_per_fsr"]
        _PERSISTENT_["pzt2_offset"] = newPZToffset
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER2",newPZToffset)
        _PERSISTENT_["pzt4_offset"] = newPZToffset                       #  CH4 line drives both PZTs
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER4",newPZToffset)
    except:
        pass
        
    try:
        _NEW_DATA_["CO2"] = _OLD_DATA_["CO2"][-1].value
    except:
        _NEW_DATA_["CO2"] = 0.0
    try:
        _NEW_DATA_["H2O"] = _OLD_DATA_["H2O"][-1].value
    except:
        _NEW_DATA_["H2O"] = 0.0        
        
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