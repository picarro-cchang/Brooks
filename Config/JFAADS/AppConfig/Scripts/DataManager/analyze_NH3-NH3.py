#  Analysis script for AEDS Ammonia analyzer started by Hoffnagle 2010-12-15

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
    _PERSISTENT_["init"] = False


REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [2, 4]

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
NH3_CONC = (_INSTR_["concentration_nh3_slope"],_INSTR_["concentration_nh3_intercept"])
CO2_CONC = (_INSTR_["concentration_co2_slope"],_INSTR_["concentration_co2_intercept"])
H2O_CONC = (_INSTR_["concentration_h2o_slope"],_INSTR_["concentration_h2o_intercept"])

if _DATA_["species"] == 4:
    try:
        _NEW_DATA_["CO2"] = _OLD_DATA_["CO2"][-1].value
        _NEW_DATA_["H2O"] = _OLD_DATA_["H2O"][-1].value
    except:
        pass
        
    try:   
        temp = applyLinear(_DATA_["nh3_conc_ave"],NH3_CONC)
        _NEW_DATA_["NH3"] = temp
        now = _OLD_DATA_["NH3"][-2].time
        _NEW_DATA_["NH3_30s"] = boxAverage(_PERSISTENT_["buffer30"],temp,now,30)
        _NEW_DATA_["NH3_2min"] = boxAverage(_PERSISTENT_["buffer120"],temp,now,120)
        _NEW_DATA_["NH3_5min"] = boxAverage(_PERSISTENT_["buffer300"],temp,now,300)
    except:
        pass

if _DATA_["species"] == 2:
    try:
        _NEW_DATA_["NH3"] = _OLD_DATA_["NH3"][-1].value
        _NEW_DATA_["NH3_30s"] = _OLD_DATA_["NH3_30s"][-1].value
        _NEW_DATA_["NH3_2min"] = _OLD_DATA_["NH3_2min"][-1].value
        _NEW_DATA_["NH3_5min"] = _OLD_DATA_["NH3_5min"][-1].value
    except:
        pass
        
    try:
        temp = applyLinear(_DATA_["co2_conc"],CO2_CONC)
        _NEW_DATA_["CO2"] = temp
    except:
        pass
         
    try:
        temp = applyLinear(_DATA_["h2o_conc"],H2O_CONC)
        _NEW_DATA_["H2O"] = temp
    except:
        pass
    
if _DATA_["species"] in TARGET_SPECIES:
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
        
max_adjust = 5.0e-5

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
    if _DATA_["species"] == 2: # Update the offset for virtual laser 1
        try:
            nh3_adjust = _DATA_["cm_adjust"]
            nh3_adjust = min(max_adjust,max(-max_adjust,nh3_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + nh3_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            # print "New NH3 (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            # print "No new NH3 (virtual laser 1) offset"
            
if _DATA_["species"] in TARGET_SPECIES:
    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]

