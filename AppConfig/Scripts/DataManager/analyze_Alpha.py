import time

for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]

try:
    _REPORT_["wlm1_offset"] = _OLD_DATA_["wlm1_offset"][-1].value
except:
    pass

