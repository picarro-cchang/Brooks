#  Data analysis script for the experimental instrument operating at 7193 wavenumbers
#  2011 0920 - adapted from CFF analysis script

from math import exp
from numpy import mean
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

# Static variables used for wlm offsets, bookending and averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm5_offset"] = 0.0
    _PERSISTENT_["average30"]  = []
    _PERSISTENT_["average120"] = []
    _PERSISTENT_["average300"] = []
    _PERSISTENT_["init"] = False
    _PERSISTENT_["plot"] = False

REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [2, 3, 4, 45, 47]

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
# CO2 = (_INSTR_["co2_slope"],_INSTR_["co2_intercept"])
# N2O = (_INSTR_["n2o_slope"],_INSTR_["n2o_intercept"])

try:
    NUM_BLOCKING_DATA = _INSTR_["num_blocking_data"]
except:
    NUM_BLOCKING_DATA = 3

if _DATA_["species"] in TARGET_SPECIES:
    try:
        n2o = _DATA_["n2o_conc"]
        now = _OLD_DATA_["peak_1a"][-1].time
        _NEW_DATA_["N2O_raw"] = n2o
        _NEW_DATA_["CO2"] = _DATA_["co2_conc"]
        _NEW_DATA_["NH3"] = _DATA_["nh3_conc_ave"]
        _NEW_DATA_["H2O"] = _DATA_["h2o_conc"]
        _NEW_DATA_["N2O_30s"] = boxAverage(_PERSISTENT_["average30"],n2o,now,30)
        _NEW_DATA_["N2O_2min"] = boxAverage(_PERSISTENT_["average120"],n2o,now,120)
        _NEW_DATA_["N2O_5min"] = boxAverage(_PERSISTENT_["average300"],n2o,now,300)
    except:
        pass
            
    for k in _DATA_.keys():
        _REPORT_[k] = _DATA_[k]
    
    for k in _NEW_DATA_.keys():
        if k.startswith("Delta"):
            _REPORT_[k] = clipReportData(_NEW_DATA_[k])
        else:    
            _REPORT_[k] = _NEW_DATA_[k]
        
max_adjust = 1.0e-4

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
    if _DATA_["species"] == 13: # Update the offset for virtual laser 1
        try:
            n2o_adjust = _DATA_["adjust_n2o"]
            n2o_adjust = min(max_adjust,max(-max_adjust,n2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + n2o_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            #print "New N2O (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            #print "No new N2O (virtual laser 1) offset"
    if _DATA_["species"] in [2,3]: # Update the offset for virtual laser 5
        try:
            h2o_adjust = _DATA_["h2o_adjust"]
            h2o_adjust = min(max_adjust,max(-max_adjust,h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(5) + h2o_adjust
            _PERSISTENT_["wlm5_offset"] = newOffset0
            _NEW_DATA_["wlm5_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(5,float(newOffset0))
            #print "New H2O (virtual laser 5) offset: %.5f" % newOffset5 
        except:
            pass
            #print "No new H2O (virtual laser 5) offset"
           
if _DATA_["species"] in TARGET_SPECIES:
    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
    _REPORT_["wlm5_offset"] = _PERSISTENT_["wlm5_offset"]