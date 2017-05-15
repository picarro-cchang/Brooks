#  Analysis script for HCl analyzer started by Hoffnagle 24 Jul 2015
#  2015 0814:  modified to use stronger water line for wlm offset adjust

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


# REPORT_UPPER_LIMIT = 5000.0
# REPORT_LOWER_LIMIT = -5000.0

# TARGET_SPECIES = [60, 61]

# def clipReportData(value):
    # if value > REPORT_UPPER_LIMIT:
        # return REPORT_UPPER_LIMIT
    # elif  value < REPORT_LOWER_LIMIT:
        # return REPORT_LOWER_LIMIT
    # else:
        # return value
        
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
HCl_CONC = (_INSTR_["concentration_hcl_slope"],_INSTR_["concentration_hcl_intercept"])
H2O_CONC = (_INSTR_["concentration_h2o_slope"],_INSTR_["concentration_h2o_intercept"])
CH4_CONC = (_INSTR_["concentration_ch4_slope"],_INSTR_["concentration_ch4_intercept"])

    
try:   
    temp = applyLinear(_DATA_["hcl_conc"],HCl_CONC)
    _NEW_DATA_["HCl"] = temp
    now = _OLD_DATA_["HCl"][-2].time
    _NEW_DATA_["HCl_30sec"] = boxAverage(_PERSISTENT_["buffer30"],temp,now,30)
    _NEW_DATA_["HCl_2min"] = boxAverage(_PERSISTENT_["buffer120"],temp,now,120)
    _NEW_DATA_["HCl_5min"] = boxAverage(_PERSISTENT_["buffer300"],temp,now,300)
except Exception, e:
    print "Exception: %s, %r" % (e,e)
    pass
    
try:   
    _NEW_DATA_["H2O"] = applyLinear(_DATA_["h2o_conc_raw"],H2O_CONC)
except Exception, e:
    print "Exception: %s, %r" % (e,e)
    pass   

try:
    _NEW_DATA_["CH4"] = applyLinear(_DATA_["ch4_conc_raw"],CH4_CONC)
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
 
    
max_adjust = 5.0e-5
hcl_gain = 0.1

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
    if _DATA_["species"] == 63: # Update the offset for virtual laser 1
        try:
            hcl_adjust = _DATA_["hcl_adjust"]*hcl_gain
            hcl__adjust = min(max_adjust,max(-max_adjust,hcl_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + hcl_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            # print "New HCl (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            # print "No new HCl (virtual laser 1) offset"
            

_REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]