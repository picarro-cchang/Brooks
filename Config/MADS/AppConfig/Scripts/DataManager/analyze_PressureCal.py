from numpy import polyfit, polyval
import time

max_adjust = 1e-5

try:
    adjust = _OLD_DATA_["freq_offset"][-1].value
    adjust = min(max_adjust,max(-max_adjust,adjust))
    newOffset0 = _FREQ_CONV_.getWlmOffset(1) + adjust
    _NEW_DATA_["wlm1_offset"] = newOffset0
    _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
except:
    pass

for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]
