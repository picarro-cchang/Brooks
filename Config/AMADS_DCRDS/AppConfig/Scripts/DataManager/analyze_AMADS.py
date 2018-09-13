#  Analysis script for MADS HF analyzer started by Hoffnagle
#  2016 0629:  merged with AEDS script to create AMADS

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
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["bufferHF30"]  = []
    _PERSISTENT_["bufferHF120"] = []
    _PERSISTENT_["bufferHF300"] = []
    _PERSISTENT_["bufferNH330"]  = []
    _PERSISTENT_["bufferNH3120"] = []
    _PERSISTENT_["bufferNH3300"] = []
    _PERSISTENT_["ignore_count"] = 5
    _PERSISTENT_["init"] = False

    script = "adjustTempOffset.py"
    scriptRelPath = os.path.join(here, '..', '..', '..', 'CommonConfig',
                                 'Scripts', 'DataManager', script)
    cp = file(os.path.join(here, scriptRelPath), "rU")
    codeAsString = cp.read() + "\n"
    cp.close()
    _PERSISTENT_["adjustOffsetScript"] = compile(codeAsString, script, 'exec')

exec _PERSISTENT_["adjustOffsetScript"] in globals()

# REPORT_UPPER_LIMIT = 5000.0
# REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [2, 4, 60, 61]

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

# Define linear transformations for post-processing
HF_CONC = (_INSTR_["concentration_hf_slope"],_INSTR_["concentration_hf_intercept"])
H2O_CONC_60 = (_INSTR_["concentration_h2o_60_slope"],_INSTR_["concentration_h2o_60_intercept"])
O2_CONC = (_INSTR_["concentration_o2_slope"],_INSTR_["concentration_o2_intercept"])
NH3_CONC = (_INSTR_["concentration_nh3_slope"],_INSTR_["concentration_nh3_intercept"])
CO2_CONC = (_INSTR_["concentration_co2_slope"],_INSTR_["concentration_co2_intercept"])
H2O_CONC = (_INSTR_["concentration_h2o_slope"],_INSTR_["concentration_h2o_intercept"])

# Import water selfbroadening, cross-talk and cross-broadening parameters
Hlin = _INSTR_["water_linear"]
Hquad = _INSTR_["water_quadratic"]
H1 = _INSTR_["water_crosstalk_linear"]
A1H1 = _INSTR_["water_crossbroadening_linear"]
A1H2 = _INSTR_["water_crossbroadening_quadratic"]

try:
    temp = applyLinear(_DATA_["nh3_conc_ave"],NH3_CONC)
    _NEW_DATA_["NH3_uncorrected"] = temp
    now = _OLD_DATA_["NH3_uncorrected"][-2].time
    h2o_actual = Hlin*_DATA_["peak15"] + Hquad*_DATA_["peak15"]**2
    str15 = 1.1794*_DATA_["peak15"] + 0.001042*_DATA_["peak15"]**2
    corrected = (temp + H1*_DATA_["peak15"])/(1.0 + A1H1*str15 + A1H2*str15**2)
    dry = corrected/(1.0-0.01*h2o_actual)
    _NEW_DATA_["NH3_broadeningCorrected"] = corrected
    _NEW_DATA_["NH3_dry"] = dry
    _NEW_DATA_["NH3"] = dry
    _NEW_DATA_["NH3_30s"] = boxAverage(_PERSISTENT_["bufferNH330"],dry,now,30)
    _NEW_DATA_["NH3_2min"] = boxAverage(_PERSISTENT_["bufferNH3120"],dry,now,120)
    _NEW_DATA_["NH3_5min"] = boxAverage(_PERSISTENT_["bufferNH3300"],dry,now,300)
except:
    pass

try:
    h2o_actual = Hlin*_DATA_["peak15"] + Hquad*_DATA_["peak15"]**2
    temp = applyLinear(h2o_actual,H2O_CONC)
    _NEW_DATA_["H2O"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["co2_conc"],CO2_CONC)
    _NEW_DATA_["CO2"] = temp
except:
    pass

try:   
    temp = applyLinear(_DATA_["hf_ppbv_ave"],HF_CONC)
    _NEW_DATA_["HF"] = temp
    now = _OLD_DATA_["HF"][-2].time
    _NEW_DATA_["HF_30sec"] = boxAverage(_PERSISTENT_["bufferHF30"],temp,now,30)
    _NEW_DATA_["HF_2min"] = boxAverage(_PERSISTENT_["bufferHF120"],temp,now,120)
    _NEW_DATA_["HF_5min"] = boxAverage(_PERSISTENT_["bufferHF300"],temp,now,300)
except Exception, e:
    print "Exception: %s, %r" % (e,e)
    pass

try:
    _NEW_DATA_["O2"] = applyLinear(_DATA_["o2_conc"],O2_CONC)
except:
    pass
 
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
    if _DATA_["species"] == 2: # Update the offset for virtual laser 2
        try:
            nh3_adjust = _DATA_["cm_adjust"]
            nh3_adjust = min(max_adjust,max(-max_adjust,nh3_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(2) + nh3_adjust
            _PERSISTENT_["wlm2_offset"] = newOffset0
            _NEW_DATA_["wlm2_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
            # print "New NH3 (virtual laser 2) offset: %.5f" % newOffset0
        except:
            pass
            # print "No new NH3 (virtual laser 2) offset"

    if _DATA_["species"] == 61: # Update the offset for virtual laser 1
        try:
            o2_adjust = _DATA_["adjust_81"]
            o2_adjust = min(max_adjust,max(-max_adjust,o2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + o2_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            # print "New O2 (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            # print "No new O2 (virtual laser 1) offset"
            
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
