scanningMode = _ARGS_[0]

def applyLinear(value,xform):
    return xform[0]*value + xform[1]
    
if "CO2" in scanningMode:
    CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
    try:
        _REPORT_["co2_conc_slow"] = applyLinear(_OLD_DATA_["co2_conc"][-1].value,CO2)
    except Exception, err:
        print "%s %r" % (err, err)
    
if "CH4" in scanningMode:
    CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
    try:
        _REPORT_["ch4_conc_slow"] = applyLinear(_OLD_DATA_["ch4_conc"][-1].value,CH4)
    except Exception, err:
        print "%s %r" % (err, err)
    
if "H2O" in scanningMode:
    H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])
    try:
        _REPORT_["h2o_conc_slow"] = applyLinear(_OLD_DATA_["h2o_conc"][-1].value,H2O)
    except Exception, err:
        print "%s %r" % (err, err)
    

    

