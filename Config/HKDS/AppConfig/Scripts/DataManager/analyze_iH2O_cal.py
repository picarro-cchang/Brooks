from numpy import mean, polyfit, polyval
import time

# Static variables for averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["init"] = False
    
for k in _DATA_.keys():
    if k.startswith('cal_') or k in ['species']:
        _REPORT_[k] = _DATA_[k]
