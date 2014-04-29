##  This version of the data analyze script implements bookending as it is currently (13 July 2010) done on the G1000
##  13 Aug 2010:  changed from exponential average to box average when reporting delta_30s, delta_2min, and delta_5min
##                because exponential average overweights first data point after the looong water scan.
##                fixed bug in bookending that allowed bookending across a water scan.
##  23 Aug 2010:  changed data reporting to use the new, water-corrected concentration results returned by the V1.57 fitter
##                currently not using the methane correction to Peak88 because of water-methane interference
##                also changed some naming conventions based on Ed's email of 22 Aug
##  24 Aug 2010:  Added virtual laser 3 for H2O
##  25 Aug 2010:  Added reporting of bookended "instrument ratio"

from math import exp
from numpy import mean
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

# Static variables used for wlm offsets, bookending and averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm3_offset"] = 0.0
    _PERSISTENT_["buffer30"]  = []
    _PERSISTENT_["buffer120"] = []
    _PERSISTENT_["buffer300"] = []
    _PERSISTENT_["ratio30"]  = []
    _PERSISTENT_["ratio120"] = []
    _PERSISTENT_["ratio300"] = []
    _PERSISTENT_["init"] = False


REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [105, 109]

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


try:
    if _OLD_DATA_["species"][-1].value == 106 and _OLD_DATA_["species"][-2].value == 105 and _OLD_DATA_["species"][-3].value == 106:
        # 13 July 2010 species pattern: ...109 105 106 105 106 105 106 105 106 105 106 109 105 106 105 ...
        # this code implements bookending on the C-12 "book" which must not extend across a water scan     
        temp = protDivide((_OLD_DATA_["peak88_baseave_noch4"][-1].value + _OLD_DATA_["peak88_baseave_noch4"][-3].value)/2,
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
    temp = applyLinear(_DATA_["h2o_actual"],H2O)
    _NEW_DATA_["H2O"] = temp
except:
    pass
    
if _DATA_["species"] in TARGET_SPECIES:
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
            
    elif _DATA_["species"] == 109: # Update the offset for virtual laser 3
        try:
            h2o_adjust = _DATA_["adjust_91"]
            h2o_adjust = min(max_adjust_H2O,max(-max_adjust_H2O,h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(3) + h2o_adjust
            _NEW_DATA_["wlm3_offset"] = newOffset0
            _PERSISTENT_["wlm3_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
            # pass### "New H2O (virtual laser 3) offset: %.5f" % newOffset0 
        except:
            pass
            # pass### "No new H2O (virtual laser 3) offset"
            
if _DATA_["species"] in TARGET_SPECIES:
    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
    _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    _REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]

