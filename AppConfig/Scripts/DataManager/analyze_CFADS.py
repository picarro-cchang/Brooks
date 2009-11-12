import sys
import os

def applyLinear(value,xform):
    return xform[0]*value + xform[1]
    
for k in _DATA_.keys():
  _REPORT_[k] = _DATA_[k]
    
try:
    _REPORT_["wlm1_offset"] = _OLD_DATA_["wlm1_offset"][-1].value
except:
    pass

try:
    _REPORT_["wlm2_offset"] = _OLD_DATA_["wlm2_offset"][-1].value
except:
    pass

try:
    _NEW_DATA_["avg_co2_shift"] = 0.5*_OLD_DATA_["avg_co2_shift"][-1].value + 0.5*_DATA_["co2_shift"]
except:
    try:
        _NEW_DATA_["avg_co2_shift"] = _DATA_["co2_shift"]
    except:
        pass
try:
    _NEW_DATA_["avg_ch4_shift"] = 0.5*_OLD_DATA_["avg_ch4_shift"][-1].value + 0.5*_DATA_["ch4_shift"]
except:
    try:
        _NEW_DATA_["avg_ch4_shift"] = _DATA_["ch4_shift"]
    except:
        pass