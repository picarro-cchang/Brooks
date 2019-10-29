from numpy import polyfit, polyval
import time

gain = 0.2
max_adjust = 1e-4

try:
    adjust = gain*_OLD_DATA_["freq_offset"][-1].value
    adjust = min(max_adjust,max(-max_adjust,adjust))
    newOffset0 = _FREQ_CONV_.getWlmOffset(3) + adjust
    _NEW_DATA_["wlm3_offset"] = newOffset0
    _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
except:
    pass

for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]
    
for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]