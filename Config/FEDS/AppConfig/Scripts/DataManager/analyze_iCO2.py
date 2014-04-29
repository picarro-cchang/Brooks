#  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
#  2011 0323 - removed wlm3 feedback for SID 109 (old water at 6250) and used VL3 for the
#              high precision CH4 measurement, SID 25.  Now wlm4 is used exclusively for the 
#              low precision CH4 measurement, SID 29, which is also used for iCO2 correction.

from math import exp
from numpy import mean
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

# Static variables used for wlm offsets, bookending and averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm3_offset"] = 0.0
    _PERSISTENT_["wlm4_offset"] = 0.0
    _PERSISTENT_["wlm5_offset"] = 0.0
    _PERSISTENT_["buffer30"]  = []
    _PERSISTENT_["buffer120"] = []
    _PERSISTENT_["buffer300"] = []
    _PERSISTENT_["ratio30"]  = []
    _PERSISTENT_["ratio120"] = []
    _PERSISTENT_["ratio300"] = []
    _PERSISTENT_["init"] = False
    _PERSISTENT_["num_delta_values"] = 0
    _PERSISTENT_["plot"] = False

REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [11, 25, 29, 105, 109]

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
DELTA = (_INSTR_["concentration_iso_slope"],_INSTR_["concentration_iso_intercept"])
RATIO = (_INSTR_["concentration_r_slope"],_INSTR_["concentration_r_intercept"])
C12 = (_INSTR_["concentration_c12_gal_slope"],_INSTR_["concentration_c12_gal_intercept"])
C13 = (_INSTR_["concentration_c13_gal_slope"],_INSTR_["concentration_c13_gal_intercept"])
H2O = (_INSTR_["concentration_h2o_gal_slope"],_INSTR_["concentration_h2o_gal_intercept"])
CH4 = (_INSTR_["concentration_ch4_slope"],_INSTR_["concentration_ch4_intercept"])
CH4_HIGH_PRECISION = (_INSTR_["concentration_ch4_high_precision_slope"],_INSTR_["concentration_ch4_high_precision_intercept"])

try:
    NUM_BLOCKING_DATA = _INSTR_["num_blocking_data"]
except:
    NUM_BLOCKING_DATA = 3

try:
    if _OLD_DATA_["species"][-1].value == 106 and _OLD_DATA_["species"][-2].value == 105 and _OLD_DATA_["species"][-3].value == 106:
        temp = protDivide((_OLD_DATA_["peak88_baseave_spec"][-1].value + _OLD_DATA_["peak88_baseave_spec"][-3].value)/2,
                           _OLD_DATA_["peak87_baseave_spec"][-2].value)
        delta = applyLinear(temp,DELTA)
        _NEW_DATA_["Delta_Raw"] = delta
        now = _OLD_DATA_["peak87_baseave"][-2].time
        _NEW_DATA_["Delta_30s"] = boxAverage(_PERSISTENT_["buffer30"],delta,now,30)
        _NEW_DATA_["Delta_2min"] = boxAverage(_PERSISTENT_["buffer120"],delta,now,120)
        _NEW_DATA_["Delta_5min"] = boxAverage(_PERSISTENT_["buffer300"],delta,now,300)
        ratio = applyLinear(temp,RATIO)
        _NEW_DATA_["Ratio_Raw"] = ratio
        _NEW_DATA_["Ratio_30s"] = boxAverage(_PERSISTENT_["ratio30"],ratio,now,30)
        _NEW_DATA_["Ratio_2min"] = boxAverage(_PERSISTENT_["ratio120"],ratio,now,120)
        _NEW_DATA_["Ratio_5min"] = boxAverage(_PERSISTENT_["ratio300"],ratio,now,300)
        if _PERSISTENT_["num_delta_values"] <= NUM_BLOCKING_DATA:
            _PERSISTENT_["num_delta_values"] += 1
        elif not _PERSISTENT_["plot"]:
            _PERSISTENT_["plot"] = True
    else:
        _NEW_DATA_["Delta_Raw"] = _OLD_DATA_["Delta_Raw"][-1].value
        _NEW_DATA_["Delta_30s"] = _OLD_DATA_["Delta_30s"][-1].value
        _NEW_DATA_["Delta_2min"] = _OLD_DATA_["Delta_2min"][-1].value
        _NEW_DATA_["Delta_5min"] = _OLD_DATA_["Delta_5min"][-1].value
        _NEW_DATA_["Ratio_Raw"] = _OLD_DATA_["Ratio_Raw"][-1].value
        _NEW_DATA_["Ratio_30s"] = _OLD_DATA_["Ratio_30s"][-1].value
        _NEW_DATA_["Ratio_2min"] = _OLD_DATA_["Ratio_2min"][-1].value
        _NEW_DATA_["Ratio_5min"] = _OLD_DATA_["Ratio_5min"][-1].value
except:
    pass

try:
    temp = applyLinear(_DATA_["12CO2_ppm_wet"],C12)
    _NEW_DATA_["12CO2"] = temp
except:
    pass
    
try:
    temp = applyLinear(_DATA_["12CO2_ppm_dry"],C12)
    _NEW_DATA_["12CO2_dry"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["13CO2_ppm_wet"],C13)
    _NEW_DATA_["13CO2"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["13CO2_ppm_dry"],C13)
    _NEW_DATA_["13CO2_dry"] = temp
except:
    pass
    
try:
    temp = applyLinear(_DATA_["h2o_conc"],H2O)  # Uses 6057.8 water peak
    _NEW_DATA_["H2O"] = temp
except:
    pass
    
try:
    temp = applyLinear(_DATA_["ch4_conc_ppmv_final"],CH4_HIGH_PRECISION)  # Uses high precision methane
    _NEW_DATA_["CH4_High_Precision"] = temp
except:
    pass
    
try:
    temp = applyLinear(_DATA_["ch4_conc_for_correction"],CH4)  # Uses high concentration methane
    _NEW_DATA_["CH4"] = temp
except:
    pass
            
if _DATA_["species"] in TARGET_SPECIES and _PERSISTENT_["plot"]:
    for k in _DATA_.keys():
        _REPORT_[k] = _DATA_[k]
    
    for k in _NEW_DATA_.keys():
        if k.startswith("Delta"):
            _REPORT_[k] = clipReportData(_NEW_DATA_[k])
        else:    
            _REPORT_[k] = _NEW_DATA_[k]
        
max_adjust = 1.0e-5
max_adjust_H2O = 1.0e-4

# Check instrument status and do not do any updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if not good:
    pass### "Updating WLM offset not done because of bad instrument status"
else:
    if _DATA_["species"] == 105: # Update the offset for virtual laser 1
        try:
            co2_adjust = _DATA_["adjust_87"]
            co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + co2_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            # pass### "New C12 (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            # pass### "No new C12 (virtual laser 1) offset"
    elif _DATA_["species"] == 106: # Update the offset for virtual laser 2
        try:
            co2_adjust = _DATA_["adjust_88"]
            co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(2) + co2_adjust
            _NEW_DATA_["wlm2_offset"] = newOffset0
            _PERSISTENT_["wlm2_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
            # pass### "New C13 (virtual laser 2) offset: %.5f" % newOffset0 
        except:
            pass
            # pass### "No new C13 (virtual laser 2) offset"

    elif _DATA_["species"] == 25: # Update the offset for virtual laser 3
        try:
            ch4_high_adjust = _DATA_["ch4_high_adjust"]
            ch4_high_adjust = min(max_adjust,max(-max_adjust,ch4_high_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(3) + ch4_high_adjust
            _NEW_DATA_["wlm3_offset"] = newOffset0
            _PERSISTENT_["wlm3_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
            # pass### "New CH4 high precision(virtual laser 3) offset: %.5f" % newOffset0 
        except:
            pass
            # pass### "No new CH4 high precision(virtual laser 3) offset"            
                      
    elif _DATA_["species"] == 29: # Update the offset for virtual laser 4
        try:
            ch4_low_adjust = _DATA_["ch4_low_adjust"]
            ch4_low_adjust = min(max_adjust,max(-max_adjust,ch4_low_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(4) + ch4_low_adjust
            _NEW_DATA_["wlm4_offset"] = newOffset0
            _PERSISTENT_["wlm4_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(4,float(newOffset0))
            # pass### "New CH4 low precision(virtual laser 4) offset: %.5f" % newOffset0 
        except:
            pass
            # pass### "No new CH4 low precision(virtual laser 4) offset"
            
    elif _DATA_["species"] == 11: # Update the offset for virtual laser 5
        try:
            h2o_adjust = _DATA_["adjust_75"]
            h2o_adjust = min(max_adjust,max(-max_adjust,h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(5) + h2o_adjust
            _NEW_DATA_["wlm5_offset"] = newOffset0
            _PERSISTENT_["wlm5_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(5,float(newOffset0))
            # pass### "New H2O (virtual laser 5) offset: %.5f" % newOffset0 
        except:
            pass
            # pass### "No new H2O (virtual laser 5) offset"
            
if _DATA_["species"] in TARGET_SPECIES and _PERSISTENT_["plot"]:
    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
    _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    _REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]
    _REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
    _REPORT_["wlm5_offset"] = _PERSISTENT_["wlm5_offset"]

