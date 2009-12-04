import time
from numpy import mean
AVE_TIME_SEC = 300

def applyLinear(value,xform):
    return xform[0]*value + xform[1]
    
CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])

try:
    co2_conc = applyLinear(_DATA_["co2_conc_precal"],CO2)
    _NEW_DATA_["co2_conc"] = co2_conc
except:
    pass
    
try:
    ch4_conc = applyLinear(_DATA_["ch4_conc_precal"],CH4)
    _NEW_DATA_["ch4_conc"] = ch4_conc
except:
    pass
    
# Averaging concentration of CO2 and CH4
cutoffTime = time.time() - AVE_TIME_SEC
try:
    co2_list = []
    idx = -1
    co2_conc_time = _OLD_DATA_["co2_conc"][idx].time
    while co2_conc_time > cutoffTime:
        co2_list.append(_OLD_DATA_["co2_conc"][idx].value)
        idx -= 1
        try:
            co2_conc_time = _OLD_DATA_["co2_conc"][idx].time
        except:
            break
    co2_list.append(co2_conc)
    co2_conc_ave = mean(co2_list)
    _NEW_DATA_["co2_conc_ave"] = applyLinear(co2_conc_ave,_USER_CAL_["co2_conc"]) 
except:
    pass
    
try:
    ch4_list = []
    idx = -1
    ch4_conc_time = _OLD_DATA_["ch4_conc"][idx].time
    while ch4_conc_time > cutoffTime:
        ch4_list.append(_OLD_DATA_["ch4_conc"][idx].value)
        idx -= 1
        try:
            ch4_conc_time = _OLD_DATA_["ch4_conc"][idx].time
        except:
            break
    ch4_list.append(ch4_conc)
    ch4_conc_ave = mean(ch4_list)
    _NEW_DATA_["ch4_conc_ave"] = applyLinear(ch4_conc_ave,_USER_CAL_["ch4_conc"]) 
except:
    pass
        
for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]
    
for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]
    
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