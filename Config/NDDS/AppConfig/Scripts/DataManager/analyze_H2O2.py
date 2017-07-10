#  Analysis script for NBDS hydrogen peroxide analyzer
#  16 Jul 2012:  use ammonia (AEDS) analysis script as starting point
#  23 May 2013:  add report delay on startup
#  16 Mar 2017: Added back in Laser Aging (EW)

import os
import sys
import inspect
from math import exp
from numpy import mean
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
# Need to find path to the translation table
here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)
from translate import newname

# Static variables used for wlm offsets, bookending and averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["buffer30"]  = []
    _PERSISTENT_["buffer120"] = []
    _PERSISTENT_["buffer300"] = []
    _PERSISTENT_["buffer30_CH4"]  = []
    _PERSISTENT_["buffer120_CH4"] = []
    _PERSISTENT_["buffer300_CH4"] = []
    _PERSISTENT_["ignore_count"] = 5
    _PERSISTENT_["init"] = False

    script = "adjustTempOffset.py"
    scriptRelPath = os.path.join(here, '..', '..', '..', 'CommonConfig',
                                 'Scripts', 'DataManager', script)
    cp = file(os.path.join(here, scriptRelPath), "rU")
    codeAsString = cp.read() + "\n"
    cp.close()
    _PERSISTENT_["adjustOffsetScript"] = compile(codeAsString, script, 'exec')
REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [65,66]

def clipReportData(value):
    if value > REPORT_UPPER_LIMIT:
        return REPORT_UPPER_LIMIT
    elif  value < REPORT_LOWER_LIMIT:
        return REPORT_LOWER_LIMIT
    else:
        return value

def applyLinear(value,xform):
    return xform[0]*value + xform[1]

def apply2Linear(value,xform1,xform2):
    return applyLinear(applyLinear(value,xform1),xform2)

def protDivide(num,den):
    if den != 0:
        return num/den
    return 0

def expAverage(xavg,x,dt,tau):
    if xavg is None:
        xavg = x
    else:
        xavg = (1.0-exp(-dt/tau))*x + exp(-dt/tau)*xavg
    return xavg

def boxAverage(buffer,x,t,tau):
    buffer.append((x,t))
    while t-buffer[0][1] > tau:
        buffer.pop(0)
    return mean([d for (d,t) in buffer])

# Define linear transformtions for post-processing
H2O2_CONC = (_INSTR_["concentration_h2o2_slope"],_INSTR_["concentration_h2o2_intercept"])
H2O_CONC = (_INSTR_["concentration_h2o_slope"],_INSTR_["concentration_h2o_intercept"])
CH4_CONC = (_INSTR_["concentration_ch4_slope"],_INSTR_["concentration_ch4_intercept"])

if _DATA_["species"] == 65:
    try:
        _NEW_DATA_["H2O"] = _OLD_DATA_["H2O"][-1].value
    except:
        pass

    try:
        temp = applyLinear(_DATA_["h2o2_ppbv"],H2O2_CONC)
        _NEW_DATA_["H2O2"] = temp
        now = _OLD_DATA_["H2O2"][-1].time
        _NEW_DATA_["H2O2_30s"] = boxAverage(_PERSISTENT_["buffer30"],temp,now,30)
        _NEW_DATA_["H2O2_2min"] = boxAverage(_PERSISTENT_["buffer120"],temp,now,120)
        _NEW_DATA_["H2O2_5min"] = boxAverage(_PERSISTENT_["buffer300"],temp,now,300)

        _NEW_DATA_["CH4"] = _OLD_DATA_["CH4"][-1].value
        _NEW_DATA_["CH4_30s"] = _OLD_DATA_["CH4_30s"][-1].value
        _NEW_DATA_["CH4_2min"] = _OLD_DATA_["CH4_2min"][-1].value
        _NEW_DATA_["CH4_5min"] = _OLD_DATA_["CH4_5min"][-1].value        
        
    except:
        _NEW_DATA_["H2O2"] = 0.0
        _NEW_DATA_["H2O2_30s"] = 0.0
        _NEW_DATA_["H2O2_2min"] = 0.0
        _NEW_DATA_["H2O2_5min"] = 0.0

        _NEW_DATA_["CH4"] = 0.0
        _NEW_DATA_["CH4_30s"] = 0.0
        _NEW_DATA_["CH4_2min"] = 0.0
        _NEW_DATA_["CH4_5min"] = 0.0

if _DATA_["species"] == 66:
    try:    
        temp = applyLinear(_DATA_["ch4_ppmv"],CH4_CONC)
        _NEW_DATA_["CH4"] = temp
        now = _OLD_DATA_["CH4"][-1].time
        _NEW_DATA_["CH4_30s"] = boxAverage(_PERSISTENT_["buffer30_CH4"],temp,now,30)
        _NEW_DATA_["CH4_2min"] = boxAverage(_PERSISTENT_["buffer120_CH4"],temp,now,120)
        _NEW_DATA_["CH4_5min"] = boxAverage(_PERSISTENT_["buffer300_CH4"],temp,now,300)    
    
        _NEW_DATA_["H2O2"] = _OLD_DATA_["H2O2"][-1].value
        _NEW_DATA_["H2O2_30s"] = _OLD_DATA_["H2O2_30s"][-1].value
        _NEW_DATA_["H2O2_2min"] = _OLD_DATA_["H2O2_2min"][-1].value
        _NEW_DATA_["H2O2_5min"] = _OLD_DATA_["H2O2_5min"][-1].value
        

    except:
        _NEW_DATA_["H2O2"] = 0.0
        _NEW_DATA_["H2O2_30s"] = 0.0
        _NEW_DATA_["H2O2_2min"] = 0.0
        _NEW_DATA_["H2O2_5min"] = 0.0

        _NEW_DATA_["CH4"] = 0.0
        _NEW_DATA_["CH4_30s"] = 0.0
        _NEW_DATA_["CH4_2min"] = 0.0
        _NEW_DATA_["CH4_5min"] = 0.0
    try:
        temp = applyLinear(_DATA_["h2o_conc"],H2O_CONC)
        _NEW_DATA_["H2O"] = temp
    except:
        pass

    if _PERSISTENT_["ignore_count"] > 0:
        _PERSISTENT_["ignore_count"] = _PERSISTENT_["ignore_count"] - 1
exec _PERSISTENT_["adjustOffsetScript"] in globals()

max_adjust = 5.0e-5
gain = 0.2

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
    if _DATA_["species"] == 66: # Update the offset for virtual laser 1
        try:
            wlm_adjust = _DATA_["h2o2_adjust"]
            wlm_adjust = min(max_adjust,max(-max_adjust,gain*wlm_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + wlm_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            # print "New H2O2 (virtual laser 1) offset: %.5f" % newOffset0
        except:
            pass
            # print "No new H2O2 (virtual laser 1) offset"

if _PERSISTENT_["ignore_count"] == 0:
    if _DATA_["species"] in TARGET_SPECIES:
        _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]

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
