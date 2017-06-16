#  This version of the data analysis script uses bookending to try to improve water correction when water concentration
#  is rapidly changing.  Also reports the average of the two CO2 measurements within one scheme, spectrum IDs 10 and 12.
#  This should reduce noise on the CO2 measurement and also align the average measurment time with that of CH4.
#  Sequence of measurements is ... CO2 CH4 CO2 H2O ... with corresponding spectrum IDs ... 10 25 12 11 ...
#  Note indices of _OLD_DATA_ in the water correction calculation
#  2017 0316:  Changed H2S reporting to come from "f_h2s_peak_ppbv" instead of "f_h2s_ppbv_baseave" to improve transient response (jah)
#  2017 0322:  Removed "bookending" which makes no sense in a one-species analyzer (jah)
#  2017 0419:  Added correction for water cross-talk to H2S from Chris Rella's report

import inspect
import os
import sys
import time
from numpy import mean, sqrt
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
# Need to find path to the translation table
here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)
from translate import newname
from DynamicNoiseFilter import variableExpAverage, negative_number_filter

AVE_TIME_SEC = 300

def applyLinear(value,xform):
    return xform[0]*value + xform[1]

def boxAverage(buffer,x,t,tau):
    buffer.append((x,t))
    while t-buffer[0][1] > tau:
        buffer.pop(0)
    return mean([d for (d,t) in buffer])

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm4_offset"] = 0.0
    _PERSISTENT_["buffer30"]  = []
    _PERSISTENT_["buffer120"] = []
    _PERSISTENT_["buffer300"] = []
    _PERSISTENT_["ignore_count"] = 7
    _PERSISTENT_["bufferExpAvg_H2S"] = []
    _PERSISTENT_["bufferZZ_H2S"] = []
    _PERSISTENT_["previousNoise_H2S"]=0.0
    _PERSISTENT_["previousS_H2S"]=0.0
    _PERSISTENT_["tau_H2S"]=0.0
    _PERSISTENT_["H2S_filter"]=0.0
    _PERSISTENT_["Pressure_Save"]=140.0
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
    if _DATA_["species"] == 1: # Update the offset for virtual laser 1
        try:
            adjust = _DATA_["h2s_adjust"]
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

H2S = (_INSTR_["h2s_conc_slope"],_INSTR_["h2s_conc_intercept"])
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])

try:
    if _DATA_["SpectrumID"] == 125:
        h2s_raw = applyLinear(_DATA_["f_h2s_peak_ppbv"],H2S)
        h2s_conc = h2s_raw + _INSTR_["h2s_watercorrection_BDlinear"]*_DATA_["h2o_from_h2s"] + _INSTR_["h2s_watercorrection_BDbilinear"]*_DATA_["h2o_from_h2s"]*(_DATA_["y_eff"]-1.0) +  _INSTR_["h2s_watercorrection_BDquadratic"]*_DATA_["h2o_from_h2s"]*_DATA_["h2o_from_h2s"]
        _NEW_DATA_["H2S_raw"] = h2s_raw
        _NEW_DATA_["H2S_conc"] = h2s_conc
        now = _OLD_DATA_["H2S_raw"][-2].time
        _NEW_DATA_["H2S_30s"] = boxAverage(_PERSISTENT_["buffer30"],h2s_conc,now,30)
        _NEW_DATA_["H2S_2min"] = boxAverage(_PERSISTENT_["buffer120"],h2s_conc,now,120)
        _NEW_DATA_["H2S_5min"] = boxAverage(_PERSISTENT_["buffer300"],h2s_conc,now,300)
        if(abs(_DATA_["CavityPressure"]-_PERSISTENT_["Pressure_Save"]) < 2.0):
            _PERSISTENT_["H2S_filter"] = h2s_conc 
            _PERSISTENT_["previousS_H2S"],_PERSISTENT_["previousNoise_H2S"],_PERSISTENT_["tau_H2S"] = variableExpAverage(_PERSISTENT_["bufferZZ_H2S"],_PERSISTENT_["bufferExpAvg_H2S"],h2s_conc,now,1100,3,_PERSISTENT_["previousS_H2S"],_PERSISTENT_["previousNoise_H2S"])
        _PERSISTENT_["Pressure_Save"] = _DATA_["CavityPressure"]
        #print _PERSISTENT_["previousS_H2S"],_PERSISTENT_["previousNoise_H2S"],_PERSISTENT_["tau_H2S"]
        _NEW_DATA_["H2S_sigma"]=_PERSISTENT_["previousNoise_H2S"]*1.5*sqrt(2)
        _NEW_DATA_["H2S_ExpAvg"]=_PERSISTENT_["previousS_H2S"]
        _NEW_DATA_["H2S_tau"]=_PERSISTENT_["tau_H2S"]
        _NEW_DATA_["H2S_P_filter"] = _PERSISTENT_["H2S_filter"]
        _NEW_DATA_["H2Sraw-H2Sexpavg"] = _NEW_DATA_["H2S_P_filter"] - _NEW_DATA_["H2S_ExpAvg"]
        _NEW_DATA_["H2S_ExpAvg_NZ"] = negative_number_filter("H2S",_NEW_DATA_["H2S_ExpAvg"])
        _NEW_DATA_["H2S"] =_NEW_DATA_["H2S_ExpAvg_NZ"] 
    else:
        _NEW_DATA_["H2S_raw"] = _OLD_DATA_["H2S_raw"][-1].value
        _NEW_DATA_["H2S_conc"] = _OLD_DATA_["H2S_conc"][-1].value
        _NEW_DATA_["H2S_30s"] = _OLD_DATA_["H2S_30s"][-1].value
        _NEW_DATA_["H2S_2min"] = _OLD_DATA_["H2S_2min"][-1].value
        _NEW_DATA_["H2S_5min"] = _OLD_DATA_["H2S_5min"][-1].value
        #_NEW_DATA_["H2S_sigma"] = _OLD_DATA_["H2S_sigma"][-1].value
		
except:
        _NEW_DATA_["H2S_raw"] = 0.0
        _NEW_DATA_["H2S_conc"] = 0.0
        _NEW_DATA_["H2S_30s"] = 0.0
        _NEW_DATA_["H2S_2min"] = 0.0
        _NEW_DATA_["H2S_5min"] = 0.0
        #_NEW_DATA_["H2S_sigma"] = 0.0

try:
    #ch4_conc = applyLinear(_DATA_["ch4_conc_ppmv_final"],CH4)
    _NEW_DATA_["HDO_ref"] = _DATA_["h2o_from_h2s"] #applyLinear(_DATA_["h2o_from_h2s"],H2O)
    #print _DATA_["h2o_from_h2s"]
    _NEW_DATA_["CO2"] = _DATA_["co2_ppmv"]


except:
    _NEW_DATA_["HDO_ref"]=0.0
    _NEW_DATA_["CO2"] = 0.0

#try:
#    h2o_reported = applyLinear(_DATA_["h2o_conc_precal"],H2O)
 #   h2o_precorr = 0.5*(h2o_reported+_OLD_DATA_["h2o_reported"][-4].value)  # average of current and last uncorrected h2o measurements

 #   try:
 #       ch4_conc_dry = _OLD_DATA_["ch4_conc"][-2].value/(1.0+h2o_precorr*(_INSTR_["ch4_watercorrection_linear"]+h2o_precorr*_INSTR_["ch4_watercorrection_quadratic"]))
 #       _NEW_DATA_["ch4_conc_dry"] = ch4_conc_dry

 #   except:
 #       _NEW_DATA_["ch4_conc_dry"] = 0.0


#    try:
#        h2o_actual = _INSTR_["h2o_selfbroadening_linear"]*(h2o_reported+_INSTR_["h2o_selfbroadening_quadratic"]*h2o_reported**2)
#        _NEW_DATA_["h2o_reported"] = h2o_reported
#        _NEW_DATA_["h2o_conc"] = h2o_actual
#    except:
#        _NEW_DATA_["h2o_reported"] = h2o_reported
#        _NEW_DATA_["h2o_conc"] = h2o_reported
#except:
#    _NEW_DATA_["h2o_conc"] = 0.0
#    _NEW_DATA_["h2o_reported"] = 0.0

if _DATA_["SpectrumID"] == 125:
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

        _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
        _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
        _REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
