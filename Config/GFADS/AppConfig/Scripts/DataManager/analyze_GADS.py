#  Analysis script for G2000 GADS ethylene analyzer

import inspect
import os
import sys
import time
from numpy import mean
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
# Need to find path to the translation table
here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)
from translate import newname

AVE_TIME_SEC = 300

def applyLinear(value,xform):
    return xform[0]*value + xform[1]

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm4_offset"] = 0.0
    _PERSISTENT_["wlm6_offset"] = 0.0
    _PERSISTENT_["ignore_count"] = 7
    _PERSISTENT_["init"] = False

###############
# Calibration of WLM offsets
###############

max_adjust = 1.0e-5

# Check instrument status and do not do any updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if not good:
    print "Updating WLM offset not done because of bad instrument status"
else:
    if _DATA_["species"] == 31: # Update the offset for virtual laser 6 (C2H4)
        try:
            adjust = _DATA_["c2h4_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(6) + adjust
            _PERSISTENT_["wlm6_offset"] = newOffset
            _NEW_DATA_["wlm6_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(6,float(newOffset))
        except:
            pass
    elif _DATA_["species"] == 25: # Update the offset for virtual laser 2 (CH4)
        try:
            adjust = _DATA_["ch4_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(2) + adjust
            _PERSISTENT_["wlm2_offset"] = newOffset
            _NEW_DATA_["wlm2_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(2,float(newOffset))
        except:
            pass
    elif _DATA_["species"] == 11: # Update the offset for virtual laser 4 (H2O 6057.8)
        try:
            adjust = _DATA_["h2o_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(4) + adjust
            _NEW_DATA_["wlm4_offset"] = newOffset
            _PERSISTENT_["wlm4_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(4,float(newOffset))
        except:
            pass

###############
# Apply instrument calibration
###############

C2H4 = (_INSTR_["c2h4_conc_slope"],_INSTR_["c2h4_conc_intercept"])
CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])

if _DATA_["SpectrumID"] in [30,31]:
    try:
        _NEW_DATA_["C2H4"] = applyLinear(_DATA_["c2h4_conc_ppbv"],C2H4)
        _NEW_DATA_["CH4"] = applyLinear(_DATA_["ch4_conc_from_c2h4"],CH4)
        _NEW_DATA_["CO2"] = applyLinear(_DATA_["co2_conc_from_c2h4"],CO2)
        _NEW_DATA_["H2O"] = applyLinear(_DATA_["h2o_conc"],H2O)
    except:
        pass


t = time.gmtime(_MEAS_TIME_)
t1 = float("%04d%02d%02d" % t[0:3])
t2 = "%02d%02d%02d.%03.0f" % (t[3],t[4],t[5],1000*(_MEAS_TIME_-int(_MEAS_TIME_)),)

if _PERSISTENT_["ignore_count"] > 0:
    _PERSISTENT_["ignore_count"] = _PERSISTENT_["ignore_count"] - 1
else:
    #print t2
    _REPORT_["time"] = _MEAS_TIME_
    _REPORT_["ymd"] = t1
    _REPORT_["hms"] = t2

    for k in _DATA_.keys():
        if k in newname:
            _REPORT_[newname[k]] = _DATA_[k]
        else:
            _REPORT_[k] = _DATA_[k]

    for k in _NEW_DATA_.keys():
        if k in newname:
            _REPORT_[newname[k]] = _NEW_DATA_[k]
        else:
            _REPORT_[k] = _NEW_DATA_[k]

    _REPORT_["wlm6_offset"] = _PERSISTENT_["wlm6_offset"]
    #_REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    #_REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
