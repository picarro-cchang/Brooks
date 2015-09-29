#  This version of the data analysis script uses bookending to try to improve water correction when water concentration
#  is rapidly changing.  Also reports the average of the two CO2 measurements within one scheme, spectrum IDs 10 and 12.
#  This should reduce noise on the CO2 measurement and also align the average measurment time with that of CH4.
#  Sequence of measurements is ... CO2 CH4 CO2 H2O ... with corresponding spectrum IDs ... 10 25 12 11 ...
#  Note indices of _OLD_DATA_ in the water correction calculation
#  2015 0623:  Changed logic for WLM1 adjust to apply adjust on SID 200 (correct) instead of 201 (old data)

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
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm3_offset"] = 0.0
    _PERSISTENT_["ignore_count"] = 10
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
    if _DATA_["species"] == 200: # Update the offset for virtual laser 1
        try:
            adjust = _DATA_["adjust_94"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(1) + adjust
            _PERSISTENT_["wlm1_offset"] = newOffset
            _NEW_DATA_["wlm1_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(1,float(newOffset))
        except:
            pass
    elif _DATA_["species"] == 25: # Update the offset for virtual laser 2
        try:
            adjust = _DATA_["ch4_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(2) + adjust
            _PERSISTENT_["wlm2_offset"] = newOffset
            _NEW_DATA_["wlm2_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(2,float(newOffset))
        except:
            pass
    elif _DATA_["species"] == 11: # Update the offset for virtual laser 3
        try:
            adjust = _DATA_["h2o_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(3) + adjust
            _NEW_DATA_["wlm3_offset"] = newOffset
            _PERSISTENT_["wlm3_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(3,float(newOffset))
        except:
            pass

###############
# Apply instrument calibration 
###############
        
C2H2 = (_INSTR_["c2h2_conc_slope"],_INSTR_["c2h2_conc_intercept"])
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])

try:
    if _DATA_["SpectrumID"] == 201:
        c2h2_conc = applyLinear(_DATA_["c2h2_conc_precal"],C2H2)
        _NEW_DATA_["c2h2_conc"] = c2h2_conc
        #try:
        #    h2o_precorr = applyLinear(_OLD_DATA_["h2o_conc_precal"][-1].value,H2O)
        #    co2_conc_dry = co2_conc/(1.0+h2o_precorr*(_INSTR_["co2_watercorrection_linear"]+h2o_precorr*_INSTR_["co2_watercorrection_quadratic"]))
        #    _NEW_DATA_["co2_conc_dry"] = co2_conc_dry
        #except:
        #    _NEW_DATA_["co2_conc_dry"] = 0.0
    else:
        _NEW_DATA_["c2h2_conc"] = _OLD_DATA_["c2h2_conc"][-1].value
except:
    #_NEW_DATA_["co2_conc_dry"] = 0.0
    _NEW_DATA_["c2h2_conc"] = 0.0
    
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
    h2o_conc = applyLinear(_DATA_["h2o_conc_precal"],H2O)
    _NEW_DATA_["h2o_conc"] = h2o_conc
    #try:
    #    h2o_precorr = applyLinear(_OLD_DATA_["h2o_conc_precal"][-1].value,H2O)
    #    ch4_conc_dry = ch4_conc/(1.0+h2o_precorr*(_INSTR_["ch4_watercorrection_linear"]+h2o_precorr*_INSTR_["ch4_watercorrection_quadratic"]))
    #    _NEW_DATA_["ch4_conc_dry"] = ch4_conc_dry
    #except:
    #    _NEW_DATA_["ch4_conc_dry"] = 0.0
except:
    _NEW_DATA_["h2o_conc"] = 0.0
    #_NEW_DATA_["ch4_conc_dry"] = 0.0
    
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
                    if interpData[i]:
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
    _REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]
