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
#here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
#if here not in sys.path: sys.path.append(here)
#from translate import newname

AVE_TIME_SEC = 300

def applyLinear(value,xform):
    return xform[0]*value + xform[1]

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["h2o_pzt_adjust"] = 0.0
    _PERSISTENT_["pztAdjustGuy_new"] = 0.0
    _PERSISTENT_["ignore_count"] = 0
    _PERSISTENT_["init"] = False

    #script = "adjustTempOffset.py"
    #scriptRelPath = os.path.join(here, '..', '..', '..', 'CommonConfig',
    #                             'Scripts', 'DataManager', script)
    #cp = file(os.path.join(here, scriptRelPath), "rU")
    #codeAsString = cp.read() + "\n"
    #cp.close()
    #_PERSISTENT_["adjustOffsetScript"] = compile(codeAsString, script, 'exec')

# Cannot unconditionally execute this script here else end up with
# different columns in output when SpectrumID is 10 vs. other values.
#exec _PERSISTENT_["adjustOffsetScript"] in globals()

###############
# Calibration of WLM offsets
###############

max_adjust = 1.0e-5
WLMgain = 0.3

max_pzt_adjust = 5000
PZTgain = 0.2

# Check instrument status and do not do any updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)

#print '- '*20
#print 'data manager outputs:'
#print good

if not good:
    print "Updating WLM offset not done because of bad instrument status"
else:
    if (_DATA_["goodH2O"] > 5) and False: # Update the offset for virtual laser 1 using H2O
        try:
            adjust = _DATA_["h2o_adjust"]*WLMgain
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset = _FREQ_CONV_.getWlmOffset(1) + adjust
            _PERSISTENT_["wlm1_offset"] = newOffset
            _NEW_DATA_["wlm1_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(1,float(newOffset))
        except:
            pass
    if False: #
        try:
            adjust = _DATA_["pztAdjustGuy"]*PZTgain
            adjust = min(max_pzt_adjust,max(-max_pzt_adjust,adjust))
            old_pzt_offset = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER1")
            newPZToffset = old_pzt_offset + adjust
            while newPZToffset > 45768:
                newPZToffset -= _DATA_["pzt_per_fsr"]
            while newPZToffset < 19768:
                newPZToffset += _DATA_["pzt_per_fsr"]
            _PERSISTENT_["pztAdjustGuy_new"] = newPZToffset
            _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1",newPZToffset)
            print 'Adjusting PZT --'
            print old_pzt_offset, newPZToffset
        except:
            print 'failed to move the PZT'
            pass
    
###############
# Apply instrument calibration
###############
"""
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
    # must run this script here since updating _REPORT_
    exec _PERSISTENT_["adjustOffsetScript"] in globals()

    t = time.gmtime(_MEAS_TIME_)
    t1 = float("%04d%02d%02d" % t[0:3])
    t2 = "%02d%02d%02d.%03.0f" % (t[3],t[4],t[5],1000*(_MEAS_TIME_-int(_MEAS_TIME_)),)
"""

if _PERSISTENT_["ignore_count"] > 0:
    _PERSISTENT_["ignore_count"] = _PERSISTENT_["ignore_count"] - 1
else:
    #print t2
    _REPORT_["time"] = _MEAS_TIME_
    #_REPORT_["ymd"] = t1
    #_REPORT_["hms"] = t2
    print _REPORT_['time']

    for k in _DATA_.keys():
        _REPORT_[k] = _DATA_[k]
        #print k, _DATA_[k]

    for k in _NEW_DATA_.keys():
        _REPORT_[k] = _NEW_DATA_[k]

    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
    _REPORT_["pztAdjustGuy_new"] = _PERSISTENT_["pztAdjustGuy_new"]
    #_REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    #_REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
