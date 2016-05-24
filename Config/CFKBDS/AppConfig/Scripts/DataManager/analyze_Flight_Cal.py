#  This version of the data analysis script uses bookending to try to improve water correction when water concentration
#  is rapidly changing.  Also reports the average of the two CO2 measurements within one scheme, spectrum IDs 10 and 12.
#  This should reduce noise on the CO2 measurement and also align the average measurment time with that of CH4.
#  Sequence of measurements is ... CO2 CH4 CO2 H2O ... with corresponding spectrum IDs ... 10 25 12 11 ...
#  Note indices of _OLD_DATA_ in the water correction calculation

import time
from numpy import mean
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

AVE_TIME_SEC = 300

def applyLinear(value,xform):
    return xform[0]*value + xform[1]

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm4_offset"] = 0.0
    _PERSISTENT_["wlm5_offset"] = 0.0
    _PERSISTENT_["init"] = False

try:
    newOffset = _FREQ_CONV_.getWlmOffset(1)
    _PERSISTENT_["wlm1_offset"] = newOffset
    _NEW_DATA_["wlm1_offset"] = newOffset
except:
    pass

try:
    newOffset = _FREQ_CONV_.getWlmOffset(2)
    _PERSISTENT_["wlm2_offset"] = newOffset
    _NEW_DATA_["wlm2_offset"] = newOffset
except:
    pass

try:
    newOffset = _FREQ_CONV_.getWlmOffset(4)
    _PERSISTENT_["wlm4_offset"] = newOffset
    _NEW_DATA_["wlm4_offset"] = newOffset
except:
    pass
try:
    newOffset = _FREQ_CONV_.getWlmOffset(5)
    _PERSISTENT_["wlm5_offset"] = newOffset
    _NEW_DATA_["wlm5_offset"] = newOffset
except:
    pass

###############
# Apply instrument calibration
###############

CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])
CO = (_INSTR_["co_conc_slope"],_INSTR_["co_conc_intercept"])

try:
    if _DATA_["SpectrumID"] == 10:
        co2_conc = applyLinear(_DATA_["galpeak14_final"],CO2)
        _NEW_DATA_["co2_conc"] = co2_conc
        #try:
        #    h2o_precorr = applyLinear(_OLD_DATA_["h2o_conc_precal"][-1].value,H2O)
        #    co2_conc_dry = co2_conc/(1.0+h2o_precorr*(_INSTR_["co2_watercorrection_linear"]+h2o_precorr*_INSTR_["co2_watercorrection_quadratic"]))
        #    _NEW_DATA_["co2_conc_dry"] = co2_conc_dry
        #except:
        #    _NEW_DATA_["co2_conc_dry"] = 0.0
    else:
        _NEW_DATA_["co2_conc"] = _OLD_DATA_["co2_conc"][-1].value
except:
    #_NEW_DATA_["co2_conc_dry"] = 0.0
    _NEW_DATA_["co2_conc"] = 0.0

try:
    ch4_conc = applyLinear(_DATA_["ch4_conc_ppmv_final"],CH4)
    _NEW_DATA_["ch4_conc"] = ch4_conc
    #try:
    #    h2o_precorr = applyLinear(_OLD_DATA_["h2o_conc_precal"][-1].value,H2O)
    #    ch4_conc_dry = ch4_conc/(1.0+h2o_precorr*(_INSTR_["ch4_watercorrection_linear"]+h2o_precorr*_INSTR_["ch4_watercorrection_quadratic"]))
    #    _NEW_DATA_["ch4_conc_dry"] = ch4_conc_dry
    #except:
    #    _NEW_DATA_["ch4_conc_dry"] = 0.0
except:
    _NEW_DATA_["ch4_conc"] = 0.0
    #_NEW_DATA_["ch4_conc_dry"] = 0.0

try:
    h2o_reported = applyLinear(_DATA_["h2o_conc_precal"],H2O)
    h2o_precorr = 0.5*(h2o_reported+_OLD_DATA_["h2o_reported"][-4].value)  # average of current and last uncorrected h2o measurements

    try:
        ch4_conc_dry = _OLD_DATA_["ch4_conc"][-2].value/(1.0+h2o_precorr*(_INSTR_["ch4_watercorrection_linear"]+h2o_precorr*_INSTR_["ch4_watercorrection_quadratic"]))
        _NEW_DATA_["ch4_conc_dry"] = ch4_conc_dry
        co2_conc_dry = _OLD_DATA_["co2_conc"][-1].value/(1.0+h2o_precorr*(_INSTR_["co2_watercorrection_linear"]+h2o_precorr*_INSTR_["co2_watercorrection_quadratic"]))
        _NEW_DATA_["co2_conc_dry"] = co2_conc_dry
    except:
        _NEW_DATA_["ch4_conc_dry"] = 0.0
        _NEW_DATA_["co2_conc_dry"] = 0.0

    try:
        h2o_actual = _INSTR_["h2o_selfbroadening_linear"]*(h2o_reported+_INSTR_["h2o_selfbroadening_quadratic"]*h2o_reported**2)
        _NEW_DATA_["h2o_reported"] = h2o_reported
        _NEW_DATA_["h2o_conc"] = h2o_actual
    except:
        _NEW_DATA_["h2o_reported"] = h2o_reported
        _NEW_DATA_["h2o_conc"] = h2o_reported
except:
    _NEW_DATA_["h2o_conc"] = 0.0
    _NEW_DATA_["h2o_reported"] = 0.0
try:
    co_conc = applyLinear(_DATA_["co_conc_precal"],CO)
    _NEW_DATA_["co_conc"] = co_conc
except:
    try:
        _NEW_DATA_["co_conc"] = _DATA_["co_conc_precal"]
    except:
        _NEW_DATA_["co_conc"] = 0.0

for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]

_REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
_REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
_REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
_REPORT_["wlm5_offset"] = _PERSISTENT_["wlm5_offset"]
