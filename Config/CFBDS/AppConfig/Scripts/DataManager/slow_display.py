scanningMode = _ARGS_[0]

def applyLinear(value,xform):
    return xform[0]*value + xform[1]

if "CO2" in scanningMode:
    try:
        _REPORT_["co2_conc_slow"] = applyLinear(_OLD_DATA_["co2_conc"][-1].value,_USER_CAL_["co2_conc"])
    except Exception, err:
        print "%s %r" % (err, err)

if "CH4" in scanningMode:
    try:
        _REPORT_["ch4_conc_slow"] = applyLinear(_OLD_DATA_["ch4_conc"][-1].value,_USER_CAL_["ch4_conc"])
    except Exception, err:
        print "%s %r" % (err, err)

if "H2O" in scanningMode:
    try:
        _REPORT_["h2o_conc_slow"] = applyLinear(_OLD_DATA_["h2o_conc"][-1].value,_USER_CAL_["h2o_conc"])
    except Exception, err:
        print "%s %r" % (err, err)




