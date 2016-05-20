#  20100628:  hoffnagle:  this script adds the quadratic water correction to the quantities reported in
#  flux mode.  The nomenclature is as follows:  h2o_reported is derived from the spectroscopic data without
#  correction for self broadening, h2o_conc is corrected for self-broadening (quadratic correction); co2_conc
#  and ch4_conc have no water correction;  co2_conc_dry and ch4_conc_dry have the quadratic correction for effect
#  of water concentration.  The water concentration used for the correction is the avrage of the two
#  measurements made before and after the CO2 or CH4 measurement.

import inspect
import os
import sys
# Need to find path to the translation table
here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)
from translate import newname
from syncList import syncList
from numpy import polyfit, polyval
from collections import deque
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED


def applyLinear(value,xform):
    return xform[0]*value + xform[1]

def polyInterp(conc,lagTime):
    vList = [_OLD_DATA_[conc][-6].value, _OLD_DATA_[conc][-4].value, _OLD_DATA_[conc][-2].value, _OLD_DATA_[conc][-1].value]
    tList = [_OLD_DATA_[conc][-6].time, _OLD_DATA_[conc][-4].time, _OLD_DATA_[conc][-2].time, _OLD_DATA_[conc][-1].time]
    fitFunc = polyfit(tList,vList,2)
    return polyval(fitFunc,_OLD_DATA_[conc][-1].time-lagTime)

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm3_offset"] = 0.0
    _PERSISTENT_["ignore_count"] = 7
    _PERSISTENT_["lastMeasTimeBySpecies"]     = {10:deque(), 25:deque(), 28:deque()}
    _PERSISTENT_["rate"] = 0
    _PERSISTENT_["init"] = False
    for newCol in _PERIPH_INTRF_COLS_:
        syncList.append((newCol, newCol+"_sync", None, None))
    _PERSISTENT_["sync"] = Synchronizer("SYNCFLUX",
                                        syncList,
                                        syncInterval=100,
                                        syncLatency=500,
                                        processInterval=500,
                                        maxDelay=20000)

species = _DATA_["species"]
lastMeasTimeBySpecies = _PERSISTENT_["lastMeasTimeBySpecies"]
MAX_MEAS_TIME = 20

##################
# Calculate data rate
#################
if species in lastMeasTimeBySpecies:
    lastMeasTime = lastMeasTimeBySpecies[species]
    lastMeasTime.append(_MEAS_TIME_)
    if len(lastMeasTime) > MAX_MEAS_TIME:
        lastMeasTime.popleft()
    npts = len(lastMeasTime)
    if npts>2:
        interval = (lastMeasTime[-1] - lastMeasTime[0])/(npts-1)
        if interval > 0: _PERSISTENT_["rate"] = 1/interval
_NEW_DATA_["rate"] = _PERSISTENT_["rate"]

###############
# Calibration of WLM offsets
###############

max_adjust = 2.0e-6

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
    if _DATA_["species"] == 10: # Update the offset for virtual laser 1
        try:
            adjust = _DATA_["co2_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(1) + adjust
            _PERSISTENT_["wlm1_offset"] = newOffset
            _NEW_DATA_["wlm1_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(1,float(newOffset))
        except:
            pass
    elif _DATA_["species"] == 28: # Update the offset for virtual laser 2
        try:
            adjust = _DATA_["h2o_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(2) + adjust
            _PERSISTENT_["wlm2_offset"] = newOffset
            _NEW_DATA_["wlm2_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(2,float(newOffset))
        except:
            pass
    elif _DATA_["species"] == 25: # Update the offset for virtual laser 3
        try:
            adjust = _DATA_["ch4_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(3) + adjust
            _NEW_DATA_["wlm3_offset"] = newOffset
            _PERSISTENT_["wlm3_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(3,float(newOffset))
        except:
            pass

try:
    CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
except:
    CO2 = (1.0, 0.0)
try:
    CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
except:
    CH4 = (1.0, 0.0)
try:
    H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])
except:
    H2O = (1.0, 0.0)


ave_h2o = None
try:
    h2o_reported = applyLinear(_DATA_["h2o_conc_precal"],H2O)
    try:
        h2o_actual = _INSTR_["h2o_selfbroadening_linear"]*(h2o_reported+_INSTR_["h2o_selfbroadening_quadratic"]*h2o_reported**2)
    except:
        h2o_actual = h2o_reported
    _NEW_DATA_["h2o_reported"] = h2o_reported
    _NEW_DATA_["h2o_conc"] = h2o_actual
    ave_h2o = applyLinear((_OLD_DATA_["h2o_conc_precal"][-2].value+_DATA_["h2o_conc_precal"])/2,H2O)
except:
    pass

try:
    co2_conc = applyLinear(_DATA_["co2_conc_precal"],CO2)
    if ave_h2o != None:
        co2_conc_dry = co2_conc/(1.0+ave_h2o*(_INSTR_["co2_watercorrection_linear"]+ave_h2o*_INSTR_["co2_watercorrection_quadratic"]))
    else:
        co2_conc_dry = co2_conc
    _NEW_DATA_["co2_conc"] = co2_conc
    _NEW_DATA_["co2_conc_dry"] = co2_conc_dry
except:
    pass

try:
    ch4_conc = applyLinear(_DATA_["ch4_conc_precal"],CH4)
    if ave_h2o != None:
        ch4_conc_dry = ch4_conc/(1.0+ave_h2o*(_INSTR_["ch4_watercorrection_linear"]+ave_h2o*_INSTR_["ch4_watercorrection_quadratic"]))
    else:
        ch4_conc_dry = ch4_conc
    _NEW_DATA_["ch4_conc"] = ch4_conc
    _NEW_DATA_["ch4_conc_dry"] = ch4_conc_dry
except:
    pass

try:
    if _PERIPH_INTRF_:
        try:
            interpData = _PERIPH_INTRF_( _DATA_["timestamp"], _PERIPH_INTRF_COLS_)
            for i in range(len(_PERIPH_INTRF_COLS_)):
                if interpData[i]:
                    _NEW_DATA_[_PERIPH_INTRF_COLS_[i]] = interpData[i]
        except Exception, err:
            print "%r" % err
except:
    pass

for k in _DATA_:
    if k in newname:
        _REPORT_[newname[k]] = _DATA_[k]
    else:
        _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_:
    if k in newname:
        _REPORT_[newname[k]] = _NEW_DATA_[k]
    else:
        _REPORT_[k] = _NEW_DATA_[k]

_REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
_REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
_REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]

_PERSISTENT_["sync"].dispatch(_MEAS_TIMESTAMP_,_ANALYZE_)
