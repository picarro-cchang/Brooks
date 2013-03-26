#  This version of the data analysis script uses bookending to try to improve water correction when water concentration
#  is rapidly changing.  Also reports the average of the two CO2 measurements within one scheme, spectrum IDs 10 and 12.
#  This should reduce noise on the CO2 measurement and also align the average measurment time with that of CH4.
#  Sequence of measurements is ... CO2 CH4 CO2 H2O ... with corresponding spectrum IDs ... 10 25 12 11 ...
#  Note indices of _OLD_DATA_ in the water correction calculation

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
from syncList import syncList

AVE_TIME_SEC = 300

def applyLinear(value,xform):
    return xform[0]*value + xform[1]
    
if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm4_offset"] = 0.0
    _PERSISTENT_["ignore_count"] = 7
    _PERSISTENT_["init"] = False
    for newCol in _PERIPH_INTRF_COLS_:
        syncList.append((newCol, newCol+"_sync", None, None))
    _PERSISTENT_["sync"] = Synchronizer("SYNC1", 
                                        syncList,
                                        syncInterval=1000,
                                        syncLatency=5000,
                                        processInterval=500,
                                        maxDelay=20000)
    try:
        _DATA_LOGGER_.DATALOGGER_stopLogRpc("DataLog_Sensor_Minimal")
    except Exception, err:
        print "_DATA_LOGGER_ Error: %r" % err


optDict = eval("dict(%s)" % _OPTIONS_)
print "Inside data manager script, optdict: %s" % (optDict,)


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
    if _DATA_["species"] == 1: # Update the offset for virtual laser 1
        try:
            adjust = _DATA_["co2_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(1) + adjust
            _PERSISTENT_["wlm1_offset"] = newOffset
            _NEW_DATA_["wlm1_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(1,float(newOffset))
        except:
            pass
    elif _DATA_["species"] == 2: # Update the offset for virtual laser 2
        try:
            adjust = _DATA_["ch4_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(2) + adjust
            _PERSISTENT_["wlm2_offset"] = newOffset
            _NEW_DATA_["wlm2_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(2,float(newOffset))
        except:
            pass
    elif _DATA_["species"] == 3: # Update the offset for virtual laser 4
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
        
CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])

try:
    if _DATA_["SpectrumID"] == 12:
        co2_conc = applyLinear(0.5*(_DATA_["galpeak14_final"]+_OLD_DATA_["galpeak14_final"][-3].value),CO2)
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

if _DATA_["SpectrumID"] != 10:      
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

        try:    
            if _PERIPH_INTRF_:
                try:
                    interpData = _PERIPH_INTRF_( _DATA_["timestamp"], _PERIPH_INTRF_COLS_)
                    for i in range(len(_PERIPH_INTRF_COLS_)):
                        if interpData[i] is not None:
                            _NEW_DATA_[_PERIPH_INTRF_COLS_[i]] = interpData[i]
                except Exception, err:
                    print "%r" % err
        except:
            pass
            
     
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
            
        _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
        _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
        _REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]

_PERSISTENT_["sync"].dispatch(_MEAS_TIMESTAMP_,_ANALYZE_)

_REPORT_["ALARM_STATUS"] = 128 + 64