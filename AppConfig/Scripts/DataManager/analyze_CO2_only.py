def applyLinear(value,xform):
    return xform[0]*value + xform[1]
    
CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])

try:
    co2_conc = applyLinear(_DATA_["co2_conc_precal"],CO2)
    _NEW_DATA_["co2_conc"] = co2_conc
except:
    try:
        _NEW_DATA_["co2_conc"] = _DATA_["co2_conc_precal"]
    except:
        _NEW_DATA_["co2_conc"] = 0.0

for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]
    
for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]

try:
    _REPORT_["wlm1_offset"] = _OLD_DATA_["wlm1_offset"][-1].value
except:
    pass

try:
    _NEW_DATA_["avg_co2_shift"] = 0.95*_OLD_DATA_["avg_co2_shift"][-1].value + 0.05*_DATA_["co2_shift"]
except:
    try:
        _NEW_DATA_["avg_co2_shift"] = _DATA_["co2_shift"]
    except:
        pass
