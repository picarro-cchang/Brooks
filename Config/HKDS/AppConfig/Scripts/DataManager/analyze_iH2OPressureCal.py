from numpy import polyfit, polyval
import time
        
try:
    _REPORT_["wlm1_offset"] = _OLD_DATA_["wlm1_offset"][-1].value
except:
    pass

try:
    _NEW_DATA_["avg_h2o_shift"] = 0.95*_OLD_DATA_["avg_h2o_shift"][-1].value + 0.05*_DATA_["h2o_shift"]
except:
    try:
        _NEW_DATA_["avg_h2o_shift"] = _DATA_["h2o_shift"]
    except:
        pass
        
t = time.gmtime(_MEAS_TIME_)
t1 = float("%04d%02d%02d" % t[0:3])
t2 = "%02d%02d%02d.%03.0f" % (t[3],t[4],t[5],1000*(_MEAS_TIME_-int(_MEAS_TIME_)),)
#print t2
_REPORT_["time"] = _MEAS_TIME_
_REPORT_["ymd"] = t1
_REPORT_["hms"] = t2
    
for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]
    
for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]