#  Analysis script for MADS HF analyzer started by Hoffnagle
#  2016 0629:  merged with AEDS script to create AMADS
#  2016 0711:  variant for LCT operation
#  2016 0901:  added filter for pressure lock to prevent spikes from perturbing PZT
#  2016 1110:  adapted to "surrogate" measurement of N2O in air to validate proper operation

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
sigma = 0.10

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["pzt1_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER1")
    _PERSISTENT_["pzt2_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER2")
    _PERSISTENT_["bufferO230"]  = []
    _PERSISTENT_["bufferN2O30"]  = []
    _PERSISTENT_["ignore_count"] = 5
    _PERSISTENT_["init"] = False

# REPORT_UPPER_LIMIT = 5000.0
# REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [5, 61]

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

# Define linear transformations for post-processing
O2_CONC = (_INSTR_["concentration_o2_slope"],_INSTR_["concentration_o2_intercept"])
NH3_CONC = (_INSTR_["concentration_nh3_slope"],_INSTR_["concentration_nh3_intercept"])
N2O_CONC = (_INSTR_["concentration_n2o_slope"],_INSTR_["concentration_n2o_intercept"])
H2O_CONC = (_INSTR_["concentration_h2o_slope"],_INSTR_["concentration_h2o_intercept"])

try:
    temp = applyLinear(_DATA_["n2o_conc"],N2O_CONC)
    _NEW_DATA_["N2O"] = temp
    now = _OLD_DATA_["N2O"][-2].time
    _NEW_DATA_["N2O_30s"] = boxAverage(_PERSISTENT_["bufferN2O30"],temp,now,30)
except:
    pass

try:
    _NEW_DATA_["H2O"] = _DATA_["h2o_conc_61"]
    temp = applyLinear(_DATA_["o2_conc"],O2_CONC)
    _NEW_DATA_["O2"] = temp
    now = _OLD_DATA_["O2"][-2].time
    _NEW_DATA_["O2_30s"] = boxAverage(_PERSISTENT_["bufferO230"],temp,now,30)
except:
    pass
 
max_adjust = 5.0e-5
PZTgain = 0.05

# Check instrument status and do not do any updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if abs(_DATA_["CavityPressure"]-140.0) > 0.1:
    good = False
if not good:
    print "Updating WLM offset not done because of bad instrument status"
else:
    FSR = _DATA_["pzt_per_fsr"]
    if _DATA_["species"] == 5: # Update the offset for virtual laser 2
        try:
            nh3_adjust = _DATA_["cm_adjust"]
            nh3_adjust = min(max_adjust,max(-max_adjust,nh3_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(2) + nh3_adjust
            _PERSISTENT_["wlm2_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
            # print "New NH3 (virtual laser 2) offset: %.5f" % newOffset0
        except:
            pass
            # print "No new NH3 (virtual laser 2) offset"
            
#  PZT voltage control goes here.  For the time being I am not locking the pzt offsets
            
        try:
            adjust = _DATA_["pzt2_adjust"]*PZTgain
            newPZToffset = _PERSISTENT_["pzt2_offset"] + adjust
            _PERSISTENT_["pzt2_offset"] = newPZToffset
        except:
            pass
        if _PERSISTENT_["pzt2_offset"] < 32768 - 1.2*FSR:
            _PERSISTENT_["pzt2_offset"] += FSR
        if _PERSISTENT_["pzt2_offset"] > 32768 + 1.2*FSR:
            _PERSISTENT_["pzt2_offset"] -= FSR                    
        _NEW_DATA_["pzt2_offset"] = _PERSISTENT_["pzt2_offset"]
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER2",_PERSISTENT_["pzt2_offset"])

    if _DATA_["species"] == 61: # Update the offset for virtual laser 1
        try:
            o2_adjust = _DATA_["adjust_81"]
            o2_adjust = min(max_adjust,max(-max_adjust,o2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + o2_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            # print "New O2 (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            # print "No new O2 (virtual laser 1) offset"
            
#  PZT voltage control goes here.  For the time being I am not locking the pzt offsets
            
        try:
            adjust = _DATA_["pzt1_adjust"]*PZTgain
            newPZToffset = _PERSISTENT_["pzt1_offset"] + adjust
            _PERSISTENT_["pzt1_offset"] = newPZToffset
        except:
            pass
        if _PERSISTENT_["pzt1_offset"] < 32768 - 1.2*FSR:
            _PERSISTENT_["pzt1_offset"] += FSR
        if _PERSISTENT_["pzt1_offset"] > 32768 + 1.2*FSR:
            _PERSISTENT_["pzt1_offset"] -= FSR                    
        _NEW_DATA_["pzt1_offset"] = _PERSISTENT_["pzt1_offset"]
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1",_PERSISTENT_["pzt1_offset"])
            
if _PERSISTENT_["ignore_count"] > 0:
    _PERSISTENT_["ignore_count"] = _PERSISTENT_["ignore_count"] - 1
else:
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

        _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
        _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
        _REPORT_["pzt1_offset"] = _PERSISTENT_["pzt1_offset"]
        _REPORT_["pzt2_offset"] = _PERSISTENT_["pzt2_offset"]