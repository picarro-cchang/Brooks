# Define linear transformtions for post-processing
CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])

def applyLinear(value,xform):
    return xform[0]*value + xform[1]
    
try:
    _REPORT_["co2_conc_slow"] = applyLinear(_OLD_DATA_["co2_conc"][-1].value,CO2)
except Exception, err:
    print "%s %r" % (err, err)
    
try:
    _REPORT_["ch4_conc_slow"] = applyLinear(_OLD_DATA_["ch4_conc"][-1].value,CH4)
except Exception, err:
    print "%s %r" % (err, err)
