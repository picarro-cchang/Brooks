#  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
#  2011 0323 - removed wlm3 feedback for SID 109 (old water at 6250) and used VL3 for the
#              high precision CH4 measurement, SID 25.  Now wlm4 is used exclusively for the 
#              low precision CH4 measurement, SID 29, which is also used for iCO2 correction.
#  2011 0727 - modified isotopic methane analysis to use new schemes that report the entire spectrum in one piece

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
    _PERSISTENT_["wlm7_offset"] = 0.0
    _PERSISTENT_["wlm8_offset"] = 0.0
    _PERSISTENT_["buffer30_iCH4"]  = []
    _PERSISTENT_["buffer120_iCH4"] = []
    _PERSISTENT_["buffer300_iCH4"] = []
    _PERSISTENT_["ratio30_iCH4"]  = []
    _PERSISTENT_["ratio120_iCH4"] = []
    _PERSISTENT_["ratio300_iCH4"] = []
    _PERSISTENT_["buffer30_iCO2"]  = []
    _PERSISTENT_["buffer120_iCO2"] = []
    _PERSISTENT_["buffer300_iCO2"] = []
    _PERSISTENT_["ratio30_iCO2"]  = []
    _PERSISTENT_["ratio120_iCO2"] = []
    _PERSISTENT_["ratio300_iCO2"] = []
    _PERSISTENT_["init"] = False
    _PERSISTENT_["num_delta_iCH4_values"] = 0
    _PERSISTENT_["num_delta_iCO2_values"] = 0
    _PERSISTENT_["plot_iCH4"] = False
    _PERSISTENT_["plot_iCO2"] = False
    _PERSISTENT_["state"] = "low_conc"
    
REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [11, 25, 105, 106, 160]

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
DELTA_iCH4 = (_INSTR_["iCH4_concentration_iso_slope"],_INSTR_["iCH4_concentration_iso_intercept"])
RATIO_iCH4 = (_INSTR_["iCH4_concentration_r_slope"],_INSTR_["iCH4_concentration_r_intercept"])
C12_iCH4 = (_INSTR_["iCH4_concentration_c12_gal_slope"],_INSTR_["iCH4_concentration_c12_gal_intercept"])
C13_iCH4 = (_INSTR_["iCH4_concentration_c13_gal_slope"],_INSTR_["iCH4_concentration_c13_gal_intercept"])
H2O = (_INSTR_["concentration_h2o_gal_slope"],_INSTR_["concentration_h2o_gal_intercept"])
DELTA_iCO2 = (_INSTR_["iCO2_concentration_iso_slope"],_INSTR_["iCO2_concentration_iso_intercept"])
RATIO_iCO2 = (_INSTR_["iCO2_concentration_r_slope"],_INSTR_["iCO2_concentration_r_intercept"])
C12_iCO2 = (_INSTR_["iCO2_concentration_c12_gal_slope"],_INSTR_["iCO2_concentration_c12_gal_intercept"])
C13_iCO2 = (_INSTR_["iCO2_concentration_c13_gal_slope"],_INSTR_["iCO2_concentration_c13_gal_intercept"])
DELTA_HIGH_CONC_iCH4 = (_INSTR_["iCH4_high_concentration_iso_slope"],_INSTR_["iCH4_high_concentration_iso_intercept"])
PEAK0_HIGH_THRESHOLD = _INSTR_["peak0_high_threshold"]
PEAK0_LOW_THRESHOLD = _INSTR_["peak0_low_threshold"]

try:
    NUM_BLOCKING_DATA = _INSTR_["num_blocking_data"]
except:
    NUM_BLOCKING_DATA = 3

#iCH4   
#pass###  _OLD_DATA_["species"][-1].value, _OLD_DATA_["species"][-2].value, _OLD_DATA_["species"][-3].value

if _DATA_["peak0_spec"] > PEAK0_HIGH_THRESHOLD:
    if _PERSISTENT_["state"] == "low_conc":
        # Switch to high concentration schemes
        _MEAS_SYSTEM_.Mode_Set("FBDS_high_CH4_conc_mode")
    _PERSISTENT_["state"] = "high_conc"
elif _DATA_["peak0_spec"] < PEAK0_LOW_THRESHOLD:
    if _PERSISTENT_["state"] == "high_conc":
        # Switch to low  concentration schemes
        _MEAS_SYSTEM_.Mode_Set("FBDS_mode")
    _PERSISTENT_["state"] = "low_conc"

# Calculate delta without CFADS laser
try:
    temp = protDivide(_DATA_["peak5_spec"],_DATA_["peak0_spec"])
    delta_high_conc_iCH4 = applyLinear(temp,DELTA_HIGH_CONC_iCH4)
    _NEW_DATA_["delta_High_Conc_Raw_iCH4"] = delta_high_conc_iCH4
except Exception,e:
    pass### "Error %s (%r)" % (e,e)
    
try:
    if _OLD_DATA_["species"][-1].value == 160 and _OLD_DATA_["species"][-2].value == 25 and _OLD_DATA_["species"][-3].value == 160:
        pass### "species", _OLD_DATA_["species"][-1].value
        pass### "ch4_splinemax", _OLD_DATA_["ch4_splinemax"][-2].value
        temp = protDivide((_OLD_DATA_["peak5_spec"][-1].value + _OLD_DATA_["peak5_spec"][-3].value)/2,
                           _OLD_DATA_["ch4_splinemax"][-2].value)        
        delta_iCH4 = applyLinear(temp,DELTA_iCH4)
        pass### "delta_iCH4", delta_iCH4
        _NEW_DATA_["Delta_Raw_iCH4"] = delta_iCH4
        now = _OLD_DATA_["peak5_spec"][-1].time
        _NEW_DATA_["Delta_30s_iCH4"] = boxAverage(_PERSISTENT_["buffer30_iCH4"],delta_iCH4,now,30)
        _NEW_DATA_["Delta_2min_iCH4"] = boxAverage(_PERSISTENT_["buffer120_iCH4"],delta_iCH4,now,120)
        _NEW_DATA_["Delta_5min_iCH4"] = boxAverage(_PERSISTENT_["buffer300_iCH4"],delta_iCH4,now,300)
        ratio_iCH4 = applyLinear(temp,RATIO_iCH4)
        _NEW_DATA_["Ratio_Raw_iCH4"] = ratio_iCH4
        _NEW_DATA_["Ratio_30s_iCH4"] = boxAverage(_PERSISTENT_["ratio30_iCH4"],ratio_iCH4,now,30)
        _NEW_DATA_["Ratio_2min_iCH4"] = boxAverage(_PERSISTENT_["ratio120_iCH4"],ratio_iCH4,now,120)
        _NEW_DATA_["Ratio_5min_iCH4"] = boxAverage(_PERSISTENT_["ratio300_iCH4"],ratio_iCH4,now,300)
        if _PERSISTENT_["num_delta_iCH4_values"] <= NUM_BLOCKING_DATA:
            _PERSISTENT_["num_delta_iCH4_values"] += 1
        elif not _PERSISTENT_["plot_iCH4"]:
            _PERSISTENT_["plot_iCH4"] = True
    else:
        _NEW_DATA_["Delta_Raw_iCH4"] = _OLD_DATA_["Delta_Raw_iCH4"][-1].value
        _NEW_DATA_["Delta_30s_iCH4"] = _OLD_DATA_["Delta_30s_iCH4"][-1].value
        _NEW_DATA_["Delta_2min_iCH4"] = _OLD_DATA_["Delta_2min_iCH4"][-1].value
        _NEW_DATA_["Delta_5min_iCH4"] = _OLD_DATA_["Delta_5min_iCH4"][-1].value
        _NEW_DATA_["Ratio_Raw_iCH4"] = _OLD_DATA_["Ratio_Raw_iCH4"][-1].value
        _NEW_DATA_["Ratio_30s_iCH4"] = _OLD_DATA_["Ratio_30s_iCH4"][-1].value
        _NEW_DATA_["Ratio_2min_iCH4"] = _OLD_DATA_["Ratio_2min_iCH4"][-1].value
        _NEW_DATA_["Ratio_5min_iCH4"] = _OLD_DATA_["Ratio_5min_iCH4"][-1].value
except Exception,e:
    pass### "Error %s (%r)" % (e,e)

#iCO2    
try:
    if _OLD_DATA_["species"][-1].value == 106 and _OLD_DATA_["species"][-2].value == 105 and _OLD_DATA_["species"][-3].value == 106:
        temp = protDivide((_OLD_DATA_["peak88_baseave_spec"][-1].value + _OLD_DATA_["peak88_baseave_spec"][-3].value)/2,
                           _OLD_DATA_["peak87_baseave_spec"][-2].value)
        delta_iCO2 = applyLinear(temp,DELTA_iCO2)
        _NEW_DATA_["Delta_Raw_iCO2"] = delta_iCO2
        now = _OLD_DATA_["peak87_baseave"][-2].time
        _NEW_DATA_["Delta_30s_iCO2"] = boxAverage(_PERSISTENT_["buffer30_iCO2"],delta_iCO2,now,30)
        _NEW_DATA_["Delta_2min_iCO2"] = boxAverage(_PERSISTENT_["buffer120_iCO2"],delta_iCO2,now,120)
        _NEW_DATA_["Delta_5min_iCO2"] = boxAverage(_PERSISTENT_["buffer300_iCO2"],delta_iCO2,now,300)
        ratio_iCO2 = applyLinear(temp,RATIO_iCO2)
        _NEW_DATA_["Ratio_Raw_iCO2"] = ratio_iCO2
        _NEW_DATA_["Ratio_30s_iCO2"] = boxAverage(_PERSISTENT_["ratio30_iCO2"],ratio_iCO2,now,30)
        _NEW_DATA_["Ratio_2min_iCO2"] = boxAverage(_PERSISTENT_["ratio120_iCO2"],ratio_iCO2,now,120)
        _NEW_DATA_["Ratio_5min_iCO2"] = boxAverage(_PERSISTENT_["ratio300_iCO2"],ratio_iCO2,now,300)
        if _PERSISTENT_["num_delta_iCO2_values"] <= NUM_BLOCKING_DATA:
            _PERSISTENT_["num_delta_iCO2_values"] += 1
        elif not _PERSISTENT_["plot_iCO2"]:
            _PERSISTENT_["plot_iCO2"] = True
    else:
        _NEW_DATA_["Delta_Raw_iCO2"] = _OLD_DATA_["Delta_Raw_iCO2"][-1].value
        _NEW_DATA_["Delta_30s_iCO2"] = _OLD_DATA_["Delta_30s_iCO2"][-1].value
        _NEW_DATA_["Delta_2min_iCO2"] = _OLD_DATA_["Delta_2min_iCO2"][-1].value
        _NEW_DATA_["Delta_5min_iCO2"] = _OLD_DATA_["Delta_5min_iCO2"][-1].value
        _NEW_DATA_["Ratio_Raw_iCO2"] = _OLD_DATA_["Ratio_Raw_iCO2"][-1].value
        _NEW_DATA_["Ratio_30s_iCO2"] = _OLD_DATA_["Ratio_30s_iCO2"][-1].value
        _NEW_DATA_["Ratio_2min_iCO2"] = _OLD_DATA_["Ratio_2min_iCO2"][-1].value
        _NEW_DATA_["Ratio_5min_iCO2"] = _OLD_DATA_["Ratio_5min_iCO2"][-1].value
except:
    pass    
    
try:
    temp = applyLinear(_DATA_["12CO2_ppm_wet"],C12_iCO2)
    _NEW_DATA_["12CO2"] = temp
except Exception,e:
    pass### "Error %s (%r)" % (e,e)
    
try:
    temp = applyLinear(_DATA_["12CO2_ppm_dry"],C12_iCO2)
    _NEW_DATA_["12CO2_dry"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["13CO2_ppm_wet"],C13_iCO2)
    _NEW_DATA_["13CO2"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["13CO2_ppm_dry"],C13_iCO2)
    _NEW_DATA_["13CO2_dry"] = temp
except:
    pass
    
try:
    temp = applyLinear(_DATA_["h2o_conc_pct"],H2O)
    _NEW_DATA_["H2O"] = temp
except:
    pass
    
try:
    temp = applyLinear(_DATA_["12CH4_raw"],C12_iCH4)  # Uses high concentration methane
    _NEW_DATA_["12CH4"] = temp
except:
    pass
           
try:
    temp = applyLinear(_DATA_["13CH4_raw"],C13_iCH4)  # Uses high concentration methane
    _NEW_DATA_["13CH4"] = temp
except:
    pass
           
if _DATA_["species"] in TARGET_SPECIES and (_PERSISTENT_["plot_iCH4"] or _PERSISTENT_["plot_iCO2"]):
    pass### _DATA_["species"]
    for k in _DATA_.keys():
        _REPORT_[k] = _DATA_[k]
            
    for k in _NEW_DATA_.keys():
        if k.startswith("Delta"):
            _REPORT_[k] = clipReportData(_NEW_DATA_[k])
        else:    
            _REPORT_[k] = _NEW_DATA_[k]
        
if _DATA_["species"] in TARGET_SPECIES:
    pass### _DATA_["species"]
   
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
            #pass### 'co2_adjust', co2_adjust
            co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + co2_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            #pass### "New C12 (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            #pass### "No new C12 (virtual laser 1) offset"
    elif _DATA_["species"] == 106: # Update the offset for virtual laser 2
        try:
            co2_adjust = _DATA_["adjust_88"]
            co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(2) + co2_adjust
            _NEW_DATA_["wlm2_offset"] = newOffset0
            _PERSISTENT_["wlm2_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
            #pass### "New C13 (virtual laser 2) offset: %.5f" % newOffset0 
        except:
            pass
            #pass### "No new C13 (virtual laser 2) offset"

    elif _DATA_["species"] == 160: # Update the offset for virtual laser 3,4,5
        try:
            ch4_adjust = _DATA_["adjust_5"]
            ch4_adjust = min(max_adjust,max(-max_adjust,ch4_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(3) + ch4_adjust
            _NEW_DATA_["wlm3_offset"] = newOffset0
            _PERSISTENT_["wlm3_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
            #pass### "New (13)CH4(virtual laser 3) offset: %.5f" % newOffset0 
        except:
            pass
            #pass### "No new (13)CH4 (virtual laser 3) offset"            
                      
        try:
            ch4_adjust = _DATA_["adjust_0"]
            ch4_adjust = min(max_adjust,max(-max_adjust,ch4_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(4) + ch4_adjust
            _NEW_DATA_["wlm4_offset"] = newOffset0
            _PERSISTENT_["wlm4_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(4,float(newOffset0))
            #pass### "New (12)CH4(virtual laser 4) offset: %.5f" % newOffset0 
        except:
            pass
            #pass### "No new (12)CH4 (virtual laser 4) offset"
            
        try:
            h2o_adjust = _DATA_["adjust_30"]
            h2o_adjust = min(max_adjust,max(-max_adjust,h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(5) + h2o_adjust
            _NEW_DATA_["wlm5_offset"] = newOffset0
            _PERSISTENT_["wlm5_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(5,float(newOffset0))
            #pass### "New H2O (virtual laser 5) offset: %.5f" % newOffset0 
        except:
            pass
            #pass### "No new H2O (virtual laser 5) offset"
  
    #pass### _PERSISTENT_["plot_iCH4"]
    elif _DATA_["species"] == 25: # Update the offset for virtual laser 8
        pass### "species", _DATA_["species"]
        pass### "ch4_high_adjust", _DATA_["ch4_high_adjust"]
        try:
            pass### "species", "species", _DATA_["species"]
            ch4_high_adjust = _DATA_["ch4_high_adjust"]
            ch4_high_adjust = min(max_adjust,max(-max_adjust,ch4_high_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(8) + ch4_high_adjust
            _NEW_DATA_["wlm8_offset"] = newOffset0
            _PERSISTENT_["wlm8_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(8,float(newOffset0))
            pass### "New CH4 high precision(virtual laser 8) offset: %.5f" % newOffset0 
        except:
            pass
            pass### "No new CH4 high precision(virtual laser 8) offset"            
                      
          
    elif _DATA_["species"] == 11: # Update the offset for virtual laser 7
        try:
            h2o_adjust = _DATA_["adjust_75"]
            h2o_adjust = min(max_adjust,max(-max_adjust,h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(7) + h2o_adjust
            _NEW_DATA_["wlm7_offset"] = newOffset0
            _PERSISTENT_["wlm7_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(7,float(newOffset0))
            pass### "New H2O (virtual laser 7) offset: %.5f" % newOffset0 
        except:
            pass
            pass### "No new H2O (virtual laser 7) offset"

  
if _DATA_["species"] in TARGET_SPECIES and (_PERSISTENT_["plot_iCH4"] or _PERSISTENT_["plot_iCO2"]):
    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
    #pass### 'wlm1_offset', wlm1_offset
    _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    _REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]
    _REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
    _REPORT_["wlm5_offset"] = _PERSISTENT_["wlm5_offset"]
    #_REPORT_["wlm6_offset"] = _PERSISTENT_["wlm6_offset"]
    _REPORT_["wlm7_offset"] = _PERSISTENT_["wlm7_offset"]
    _REPORT_["wlm8_offset"] = _PERSISTENT_["wlm8_offset"]

