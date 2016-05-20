from numpy import polyfit, polyval
pressureSetpoint = 140.0

def applyLinear(value,xform):
    return xform[0]*value + xform[1]

def polyInterp(conc,lagTime):
    vList = [_OLD_DATA_[conc][-6].value, _OLD_DATA_[conc][-4].value, _OLD_DATA_[conc][-2].value, _OLD_DATA_[conc][-1].value]
    tList = [_OLD_DATA_[conc][-6].time, _OLD_DATA_[conc][-4].time, _OLD_DATA_[conc][-2].time, _OLD_DATA_[conc][-1].time]
    fitFunc = polyfit(tList,vList,2)
    return polyval(fitFunc,_OLD_DATA_[conc][-1].time-lagTime)

try:
    CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
except:
    CO2 = (1.0, 0.0)
try:
    CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
except:
    CH4 = (1.0, 0.0)
try:
    H2OA = (_INSTR_["h2oa_conc_slope"],_INSTR_["h2oa_conc_intercept"])
except:
    H2OA = (1.0, 0.0)
try:
    H2OB = (_INSTR_["h2ob_conc_slope"],_INSTR_["h2ob_conc_intercept"])
except:
    H2OB = (1.0, 0.0)

try:
    _REPORT_["wlm1_offset"] = _OLD_DATA_["wlm1_offset"][-1].value
except:
    pass

try:
    _REPORT_["wlm2_offset"] = _OLD_DATA_["wlm2_offset"][-1].value
except:
    pass

try:
    _NEW_DATA_["avg_co2_shift"] = 0.95*_OLD_DATA_["avg_co2_shift"][-1].value + 0.05*_DATA_["co2_shift"]
except:
    try:
        _NEW_DATA_["avg_co2_shift"] = _DATA_["co2_shift"]
    except:
        pass
try:
    _NEW_DATA_["avg_ch4_shift"] = 0.95*_OLD_DATA_["avg_ch4_shift"][-1].value + 0.05*_DATA_["ch4_shift"]
except:
    try:
        _NEW_DATA_["avg_ch4_shift"] = _DATA_["ch4_shift"]
    except:
        pass
try:
    _NEW_DATA_["avg_h2o_shift"] = 0.95*_OLD_DATA_["avg_h2o_shift"][-1].value + 0.05*_DATA_["h2o_shift"]
except:
    try:
        _NEW_DATA_["avg_h2o_shift"] = _DATA_["h2o_shift"]
    except:
        pass

try:
    _NEW_DATA_["avg_cavity_pressure"] = 0.95*_OLD_DATA_["avg_cavity_pressure"][-1].value + 0.05*_DATA_["cavity_pressure"]
except:
    try:
        _NEW_DATA_["avg_cavity_pressure"] = _DATA_["cavity_pressure"]
    except:
        pass

try:
    #delta_pressure = _DATA_["cavity_pressure"] - _OLD_DATA_["avg_cavity_pressure"][-1].value
    delta_pressure = _DATA_["cavity_pressure"] - pressureSetpoint
    co2_corr_factor = 0.002*delta_pressure
    ch4_corr_factor = 0.004*delta_pressure
    h2o_corr_factor = 0.0
except Exception, err:
    co2_corr_factor = 0.0
    ch4_corr_factor = 0.0
    h2o_corr_factor = 0.0
    print err

forwardDict = {"co2_corr_factor":co2_corr_factor, "ch4_corr_factor":ch4_corr_factor, "h2o_corr_factor":h2o_corr_factor, "species":_DATA_["species"]}
try:
    time_corr = _OLD_DATA_["co2_conc_precal"][-5].time
except:
    try:
        time_corr = _OLD_DATA_["h2oa_conc_precal"][-5].time
    except:
        time_corr = None

ave_h2o_precorr = None

if time_corr != None:
    time_diff = _MEAS_TIME_ - time_corr
    forwardDict.update({"time_corr":time_corr, "time_diff":time_diff})
    try:
        if _DATA_["h2o_id"] == 0:
            h2o_reported = applyLinear(_OLD_DATA_["h2oa_conc_precal"][-5].value,H2OA)
            try:
                h2o_actual = _INSTR_["h2o_selfbroadening_linear"]*(h2o_reported+_INSTR_["h2o_selfbroadening_quadratic"]*h2o_reported**2)
            except:
                h2o_actual = h2o_reported
            ave_h2o_precorr = applyLinear((_OLD_DATA_["h2oa_conc_precal"][-6].value+_OLD_DATA_["h2oa_conc_precal"][-4].value)/2,H2OA)
            forwardDict.update({"h2o_reported_precorr": h2o_reported})
            forwardDict.update({"h2o_actual": h2o_actual})
        elif _DATA_["h2o_id"] == 1:
            h2o_reported = applyLinear(_OLD_DATA_["h2ob_conc_precal"][-5].value,H2OB)
            try:
                h2o_actual = _INSTR_["h2o_selfbroadening_linear"]*(h2o_reported+_INSTR_["h2o_selfbroadening_quadratic"]*h2o_reported**2)
            except:
                h2o_actual = h2o_reported
            ave_h2o_precorr = applyLinear((_OLD_DATA_["h2ob_conc_precal"][-6].value+_OLD_DATA_["h2ob_conc_precal"][-4].value)/2,H2OB)
            forwardDict.update({"h2o_reported_precorr": h2o_reported})
            forwardDict.update({"h2o_actual": h2o_actual})
        else:
            pass
    except:
        pass

    try:
        co2_conc_precorr = applyLinear(_OLD_DATA_["co2_conc_precal"][-5].value,CO2)
        if ave_h2o_precorr != None:
            co2_conc_dry_precorr = co2_conc_precorr/(1.0+ave_h2o_precorr*(_INSTR_["co2_watercorrection_linear"]+ave_h2o_precorr*_INSTR_["co2_watercorrection_quadratic"]))
        else:
            co2_conc_dry_precorr = co2_conc_precorr
        forwardDict.update({"co2_conc_precorr": co2_conc_precorr})
        forwardDict.update({"co2_conc_dry_precorr": co2_conc_dry_precorr})
    except:
        pass
    try:
        ch4_conc_precorr = applyLinear(_OLD_DATA_["ch4_conc_precal"][-5].value,CH4)
        if ave_h2o_precorr != None:
            ch4_conc_dry_precorr = ch4_conc_precorr/(1.0+ave_h2o_precorr*(_INSTR_["ch4_watercorrection_linear"]+ave_h2o_precorr*_INSTR_["ch4_watercorrection_quadratic"]))
        else:
            ch4_conc_dry_precorr = ch4_conc_precorr
        forwardDict.update({"ch4_conc_precorr": ch4_conc_precorr})
        forwardDict.update({"ch4_conc_dry_precorr": ch4_conc_dry_precorr})
    except:
        pass

    _ANALYZE_["CORR_FLUX"] = forwardDict

for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]
