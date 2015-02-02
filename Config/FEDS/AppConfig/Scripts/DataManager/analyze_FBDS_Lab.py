#  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
#  2011 0323 - removed wlm3 feedback for SID 109 (old water at 6250) and used VL3 for the
#              high precision CH4 measurement, SID 25.  Now wlm4 is used exclusively for the 
#              low precision CH4 measurement, SID 29, which is also used for iCO2 correction.
#  2011 0727 - modified isotopic methane analysis to use new schemes that report the entire spectrum in one piece

import os  # new ChemDetect
import sys
import inspect
from math import exp
from numpy import mean, isfinite
from Host.Common.EventManagerProxy import Log, LogExc
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
from Host.Common.timestamp import getTimestamp
here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)
from Chemdetect.instructionprocess import InstructionProcess # new ChemDetect
from Host.Common.CustomConfigObj import CustomConfigObj # new ChemDetect
import traceback

# Static variables used for wlm offsets, bookending and averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm3_offset"] = 0.0
    _PERSISTENT_["wlm4_offset"] = 0.0
    _PERSISTENT_["wlm5_offset"] = 0.0
    _PERSISTENT_["wlm6_offset"] = 0.0
    _PERSISTENT_["wlm7_offset"] = 0.0
    _PERSISTENT_["wlm8_offset"] = 0.0
    _PERSISTENT_["buffer30_iCH4"]  = []
    _PERSISTENT_["buffer120_iCH4"] = []
    _PERSISTENT_["buffer300_iCH4"] = []
    _PERSISTENT_["buffer30_iCH4_high_conc"] = []
    _PERSISTENT_["buffer120_iCH4_high_conc"] = []
    _PERSISTENT_["buffer300_iCH4_high_conc"] = []
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
    _PERSISTENT_["state"] = "high_conc"
    _PERSISTENT_["last_delta_time"] = 0
    _PERSISTENT_["delta_high_conc_iCH4"] = 0
    _PERSISTENT_["delta_high_conc_iCH4_30s"] = 0
    _PERSISTENT_["delta_high_conc_iCH4_2min"] = 0
    _PERSISTENT_["delta_high_conc_iCH4_5min"] = 0
    _PERSISTENT_["delta_interval"] = 0
    _PERSISTENT_["Delta_iCH4_Raw"] = 0.0
    
    # For ChemDetect
    _PERSISTENT_["chemdetect_inst"] = InstructionProcess()
    configFile = os.path.join(here,"..\..\..\InstrConfig\Calibration\InstrCal\ChemDetect\ChemDetect.ini")
    configPath = os.path.split(configFile)[0]
    
    config = CustomConfigObj(configFile) 
    ChemDetect_FileName = config.get("Main", "ChemDetect_FileName") # Get the ChemDetect excel file name from the ini file
    print "ChemDetect_FileName = ", ChemDetect_FileName
    _PERSISTENT_["chemdetect_inst"].load_set_from_csv(os.path.join(configPath,ChemDetect_FileName))
                                                       # need to replace with self.instruction_path
    _PERSISTENT_["ChemDetect_previous"] = 0.0

    script = "adjustTempOffset.py"
    scriptRelPath = os.path.join(here, '..', '..', '..', 'CommonConfig',
                                 'Scripts', 'DataManager', script)
    cp = file(os.path.join(here, scriptRelPath), "rU")
    codeAsString = cp.read() + "\n"
    cp.close()
    _PERSISTENT_["adjustOffsetScript"] = compile(codeAsString, script, 'exec')

# Cannot execute this here or end up with extra rows of zeroes at instrument startup.
# Execute it when data is actually copied to the report dict.
#exec _PERSISTENT_["adjustOffsetScript"] in globals()

try:
    if _DATA_LOGGER_:
        try:
            _DATA_LOGGER_.DATALOGGER_stopLogRpc("DataLog_Sensor_Minimal")
        except Exception, err:
            print "_DATA_LOGGER_ Error: %r" % err
except:
    pass
        
REPORT_UPPER_LIMIT = 20000.0
REPORT_LOWER_LIMIT = -20000.0

TARGET_SPECIES = [11, 25, 105, 106, 150, 153]

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

# Handle options from command line
optDict = eval("dict(%s)" % _OPTIONS_)
conc = optDict.get("conc", "high").lower()
print "conc = " + conc
    
# Define linear transformtions for post-processing
DELTA_iCH4 = (_INSTR_["iCH4_concentration_iso_slope"],_INSTR_["iCH4_concentration_iso_intercept"])
RATIO_iCH4 = (_INSTR_["iCH4_concentration_r_slope"],_INSTR_["iCH4_concentration_r_intercept"])
C12_iCH4 = (_INSTR_["iCH4_concentration_c12_gal_slope"],_INSTR_["iCH4_concentration_c12_gal_intercept"])
C13_iCH4 = (_INSTR_["iCH4_concentration_c13_gal_slope"],_INSTR_["iCH4_concentration_c13_gal_intercept"])
C12_CH4_CFADS = (_INSTR_["CH4_CFADS_concentration_c12_gal_slope"],_INSTR_["CH4_CFADS_concentration_c12_gal_intercept"])
H2O = (_INSTR_["concentration_h2o_gal_slope"],_INSTR_["concentration_h2o_gal_intercept"])
CO2 = (_INSTR_["concentration_co2_gal_slope"],_INSTR_["concentration_co2_gal_intercept"])
DELTA_iCO2 = (_INSTR_["iCO2_concentration_iso_slope"],_INSTR_["iCO2_concentration_iso_intercept"])
RATIO_iCO2 = (_INSTR_["iCO2_concentration_r_slope"],_INSTR_["iCO2_concentration_r_intercept"])
C12_iCO2 = (_INSTR_["iCO2_concentration_c12_gal_slope"],_INSTR_["iCO2_concentration_c12_gal_intercept"])
C13_iCO2 = (_INSTR_["iCO2_concentration_c13_gal_slope"],_INSTR_["iCO2_concentration_c13_gal_intercept"])
DELTA_HIGH_CONC_iCH4 = (_INSTR_["iCH4_high_concentration_iso_slope"],_INSTR_["iCH4_high_concentration_iso_intercept"])
CH4_HIGH_THRESHOLD = _INSTR_["ch4_high_threshold"]
CH4_LOW_THRESHOLD = _INSTR_["ch4_low_threshold"]

P5_off_low_conc = _INSTR_["Peak5_offset_low_conc"]
P5_quad_low_conc = _INSTR_["Peak5_quad_low_conc"]
P5_A1_low_conc = _INSTR_["Peak5_CO2_lin_low_conc"]
P5_H1_low_conc = _INSTR_["Peak5_water_lin_low_conc"]
P5_H1M1_low_conc = _INSTR_["Peak5_water_bilin_low_conc"]

try:
    NUM_BLOCKING_DATA = _INSTR_["num_blocking_data"]
except:
    NUM_BLOCKING_DATA = 20

#iCH4   
#print  _OLD_DATA_["species"][-1].value, _OLD_DATA_["species"][-2].value, _OLD_DATA_["species"][-3].value


_12_ch4_raw = 0.0

# Uses high concentration methane    
try:
    _12_ch4_raw = _DATA_["12CH4_raw"]
    temp = applyLinear(_12_ch4_raw,C12_iCH4)  
    _NEW_DATA_["12CH4_high_range"] = temp
    _NEW_DATA_["HR_12CH4"] = temp
    if _PERSISTENT_["state"] == "high_conc": _DATA_["CH4"] = temp
except:
    pass
    
try:
    temp = applyLinear(_DATA_["13CH4_raw"],C13_iCH4)  # Uses high concentration methane
    _NEW_DATA_["13CH4"] = temp
except:
    pass

# Get the current sequence from the spectrum collector as the definitive evidence of the current mode
#  It is important not to trust _SPEC_COLL_.setSequence works, as there could have been an exception
try:
    seq = _SPEC_COLL_.getSequence()
    if seq == "FBDS_InLab_mode_LOW_CH4":
        _PERSISTENT_["state"] = "low_conc"
    elif seq == "FBDS_InLab_mode":
        _PERSISTENT_["state"] = "high_conc"
except:
    pass

if conc == "low":
    if _PERSISTENT_["state"] == "high_conc":
        try:
            _SPEC_COLL_.setSequence("FBDS_InLab_mode_LOW_CH4")
            # _DRIVER_.setMultipleNoRepeatScan()
        except: # For Virtual analyzer
            pass
elif conc == "auto":
    if _12_ch4_raw > 0.05:
        if _12_ch4_raw > CH4_HIGH_THRESHOLD:
            if _PERSISTENT_["state"] == "low_conc":
                # Switch to high concentration schemes
                print "Switching to HIGH_CONC mode"
                try:                
                    _SPEC_COLL_.setSequence("FBDS_InLab_mode")
                    # _DRIVER_.setMultipleNoRepeatScan()
                    print "No exception when switching to HIGH_CONC mode"
                except: # For Virtual analyzer
                    print "Exception when switching to HIGH_CONC mode"
        elif _12_ch4_raw < CH4_LOW_THRESHOLD:
            if _PERSISTENT_["state"] == "high_conc":
                # Switch to low  concentration schemes
                print "Switching to LOW_CONC mode"
                try:                
                    _SPEC_COLL_.setSequence("FBDS_InLab_mode_LOW_CH4")
                    # _DRIVER_.setMultipleNoRepeatScan()
                except: # For Virtual analyzer
                    pass
            
# Calculate delta without CFADS laser
try:
    if _DATA_["species"] == 150: 
        temp = protDivide(_DATA_["peak5_spec"],_DATA_["peak0_spec"])
        delta_high_conc_iCH4 = applyLinear(temp,DELTA_HIGH_CONC_iCH4)
        now = _OLD_DATA_["peak5_spec"][-1].time
        # calculate delta time interval
        if _PERSISTENT_["last_delta_time"] != 0:
            delta_interval = now - _PERSISTENT_["last_delta_time"]
        else:
            delta_interval = 0
        _PERSISTENT_["last_delta_time"] = now
        _PERSISTENT_["delta_high_conc_iCH4"] = delta_high_conc_iCH4
        _PERSISTENT_["delta_high_conc_iCH4_30s"] = boxAverage(_PERSISTENT_["buffer30_iCH4_high_conc"],delta_high_conc_iCH4,now,30)
        _PERSISTENT_["delta_high_conc_iCH4_2min"] = boxAverage(_PERSISTENT_["buffer120_iCH4_high_conc"],delta_high_conc_iCH4,now,120)
        _PERSISTENT_["delta_high_conc_iCH4_5min"] = boxAverage(_PERSISTENT_["buffer300_iCH4_high_conc"],delta_high_conc_iCH4,now,300)
        _PERSISTENT_["delta_interval"] = delta_interval
        # end of calculate delta time interval    
        if _PERSISTENT_["num_delta_iCH4_values"] <= NUM_BLOCKING_DATA:
            _PERSISTENT_["num_delta_iCH4_values"] += 1
        elif not _PERSISTENT_["plot_iCH4"]:
            _PERSISTENT_["plot_iCH4"] = True
except Exception,e:
    print "Error %s (%r)" % (e,e)
    
_NEW_DATA_["HR_Delta_iCH4_Raw"] = _PERSISTENT_["delta_high_conc_iCH4"]
_NEW_DATA_["HR_Delta_iCH4_30s"] = _PERSISTENT_["delta_high_conc_iCH4_30s"]
_NEW_DATA_["HR_Delta_iCH4_2min"] = _PERSISTENT_["delta_high_conc_iCH4_2min"]
_NEW_DATA_["HR_Delta_iCH4_5min"] = _PERSISTENT_["delta_high_conc_iCH4_5min"]
_NEW_DATA_["delta_interval"] = _PERSISTENT_["delta_interval"]

# Calculate delta with CFADS laser
try:
    #if _OLD_DATA_["species"][-1].value == 150 and _OLD_DATA_["species"][-2].value == 25 and _OLD_DATA_["species"][-3].value == 150:
    if _DATA_["species"]  == 150:
        #print "species", _OLD_DATA_["species"][-1].value
        #print "ch4_splinemax", _OLD_DATA_["ch4_splinemax"][-2].value
        #peak30_spec_ave = (_OLD_DATA_["peak30_spec"][-1].value + _OLD_DATA_["peak30_spec"][-3].value)/2
        #peakheight_5_ave = (_OLD_DATA_["peakheight_5"][-1].value + _OLD_DATA_["peakheight_5"][-3].value)/2
        #peak5_spec_low_conc = peakheight_5_ave + P5_off_low_conc + P5_quad_low_conc*(_OLD_DATA_["ch4_splinemax"][-2].value)*(_OLD_DATA_["ch4_splinemax"][-2].value)
        #peak5_spec_low_conc += P5_A1_low_conc*_OLD_DATA_["peak24_spec"][-4].value + P5_H1_low_conc*peak30_spec_ave + P5_H1M1_low_conc*peak30_spec_ave*peakheight_5_ave
        peak5_spec_low_conc = _DATA_["peakheight_5"] + P5_off_low_conc + P5_quad_low_conc*(_DATA_["ch4_splinemax"])*(_DATA_["ch4_splinemax"])
        peak5_spec_low_conc += P5_A1_low_conc*_DATA_["peak24_spec"] + P5_H1_low_conc*_DATA_["peak30_spec"]+ P5_H1M1_low_conc*_DATA_["peak30_spec"]*_DATA_["peakheight_5"]
        temp = protDivide(peak5_spec_low_conc, _DATA_["ch4_splinemax"])        
        delta_iCH4 = applyLinear(temp,DELTA_iCH4)
        #print "delta_iCH4", delta_iCH4
        _NEW_DATA_["HP_Delta_iCH4_Raw"] = delta_iCH4
        now = _OLD_DATA_["peak5_spec"][-1].time
        _NEW_DATA_["HP_Delta_iCH4_30s"] = boxAverage(_PERSISTENT_["buffer30_iCH4"],delta_iCH4,now,30)
        _NEW_DATA_["HP_Delta_iCH4_2min"] = boxAverage(_PERSISTENT_["buffer120_iCH4"],delta_iCH4,now,120)
        _NEW_DATA_["HP_Delta_iCH4_5min"] = boxAverage(_PERSISTENT_["buffer300_iCH4"],delta_iCH4,now,300)
        ratio_iCH4 = applyLinear(temp,RATIO_iCH4)
        _NEW_DATA_["Ratio_Raw_iCH4"] = ratio_iCH4
        _NEW_DATA_["Ratio_30s_iCH4"] = boxAverage(_PERSISTENT_["ratio30_iCH4"],ratio_iCH4,now,30)
        _NEW_DATA_["Ratio_2min_iCH4"] = boxAverage(_PERSISTENT_["ratio120_iCH4"],ratio_iCH4,now,120)
        _NEW_DATA_["Ratio_5min_iCH4"] = boxAverage(_PERSISTENT_["ratio300_iCH4"],ratio_iCH4,now,300)
    else:
        _NEW_DATA_["HP_Delta_iCH4_Raw"] = _OLD_DATA_["HP_Delta_iCH4_Raw"][-1].value
        _NEW_DATA_["HP_Delta_iCH4_30s"] = _OLD_DATA_["HP_Delta_iCH4_30s"][-1].value
        _NEW_DATA_["HP_Delta_iCH4_2min"] = _OLD_DATA_["HP_Delta_iCH4_2min"][-1].value
        _NEW_DATA_["HP_Delta_iCH4_5min"] = _OLD_DATA_["HP_Delta_iCH4_5min"][-1].value
        _NEW_DATA_["Ratio_Raw_iCH4"] = _OLD_DATA_["Ratio_Raw_iCH4"][-1].value
        _NEW_DATA_["Ratio_30s_iCH4"] = _OLD_DATA_["Ratio_30s_iCH4"][-1].value
        _NEW_DATA_["Ratio_2min_iCH4"] = _OLD_DATA_["Ratio_2min_iCH4"][-1].value
        _NEW_DATA_["Ratio_5min_iCH4"] = _OLD_DATA_["Ratio_5min_iCH4"][-1].value
except Exception,e:
    print "Error %s (%r)" % (e,e) #For VA: Errors happened are "deque index out of range" (due to IF line) (probably because there are no '-3' and '-2'
                                  #at the beginning of data) and "KeyError('Delta_Raw_iCH4',)" due to Delta_Raw_iCH4 line at the beginning of ELSE section

# new data culumn that cosolidate the low and high conc delta values
try:
    if _PERSISTENT_["state"] == "low_conc":
        _PERSISTENT_["Delta_iCH4_Raw"] = _NEW_DATA_["HP_Delta_iCH4_Raw"]
    elif _PERSISTENT_["state"] == "high_conc":
        _PERSISTENT_["Delta_iCH4_Raw"] = _NEW_DATA_["HR_Delta_iCH4_Raw"]
except:
    pass

_NEW_DATA_["Delta_iCH4_Raw"] = _PERSISTENT_["Delta_iCH4_Raw"]
    
try:
    temp = applyLinear(_DATA_["h2o_conc_pct"],H2O)
    _NEW_DATA_["H2O"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["co2_conc"],CO2)
    _NEW_DATA_["CO2"] = temp
except:
    pass
    
# Uses low concentration methane (CFADS)
try:
    temp = applyLinear(_DATA_["ch4_conc_ppmv_final"],C12_CH4_CFADS)  
    _NEW_DATA_["HP_12CH4"] = temp
    if _PERSISTENT_["state"] == "low_conc": _DATA_["CH4"] = temp
except:
    pass    
   
try: # new ChemDetect section    
    if _PERSISTENT_["state"] == "low_conc":  # HP mode
      _NEW_DATA_["HP_or_HR_mode"] = 1
      Cor_HP_HCres_CO2 = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_HP_HCres_CO2']
      Cor_HP_HCbaseoffset_H2O = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_HP_HCbaseoffset_H2O']
      _NEW_DATA_["HC_res2"] = _DATA_["HC_res"] - Cor_HP_HCres_CO2 * _NEW_DATA_["CO2"] # CO2 Correction on HC_res
      _NEW_DATA_["HC_base_offset2"]= _DATA_["HC_base_offset"] - Cor_HP_HCbaseoffset_H2O * _NEW_DATA_["H2O"] # H2O Cor on HC_base_offset
      a0_HC_base_offset2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a0_HC_base_offset2_HP']
      a1_HC_base_offset2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a1_HC_base_offset2_HP']
      a0_HC_res2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a0_HC_res2_HP']
      a1_HC_res2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a1_HC_res2_HP']
#   endif -----------------------------------------------------------------------------------------

    if _PERSISTENT_["state"] == "high_conc": # HR mode
      _NEW_DATA_["HP_or_HR_mode"] = 2
      Cor_HR_HCres_CO2 = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_HR_HCres_CO2']
      Cor_HR_HCres_H2O = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_HR_HCres_H2O']
      Cor_HR_HCbaseoffset_H2O = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_HR_HCbaseoffset_H2O']
      _NEW_DATA_["HC_res2"] = _DATA_["HC_res"] - Cor_HR_HCres_CO2*_NEW_DATA_["CO2"] - Cor_HR_HCres_H2O*_NEW_DATA_["H2O"] # CO2 & H2O Cor on HC_res 
      _NEW_DATA_["HC_base_offset2"] = _DATA_["HC_base_offset"] - Cor_HR_HCbaseoffset_H2O*_NEW_DATA_["H2O"] #H2O Cor on HC_base_offset 
      a0_HC_base_offset2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a0_HC_base_offset2_HR']
      a1_HC_base_offset2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a1_HC_base_offset2_HR']
      a0_HC_res2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a0_HC_res2_HR']
      a1_HC_res2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a1_HC_res2_HR']
#   endif -----------------------------------------------------------------------------------------

    HC_base_offset2_fit = a0_HC_base_offset2 + _NEW_DATA_["12CH4_high_range"] * a1_HC_base_offset2 #fit params obtained from 3D data 2011-09-25
    _NEW_DATA_["HC_base_offset2_diff"]= _NEW_DATA_["HC_base_offset2"] - HC_base_offset2_fit
    _NEW_DATA_["HC_base_offset2_a1"] = (_NEW_DATA_["HC_base_offset2"] - a0_HC_base_offset2) / _NEW_DATA_["12CH4_high_range"]
    HC_res2_fit = a0_HC_res2 + _NEW_DATA_["12CH4_high_range"] * a1_HC_res2  #fit params obtained from 3D data on 2011-09-25
    _NEW_DATA_["HC_res2_diff"] = _NEW_DATA_["HC_res2"] - HC_res2_fit
    _NEW_DATA_["HC_res2_a1"] = (_NEW_DATA_["HC_res2"] - a0_HC_res2) / _NEW_DATA_["12CH4_high_range"]
       
    
except:
    pass
    
try:
    _DATA_["CH4up"] = _DATA_["12CH4_up"]  
    _DATA_["CH4down"] = _DATA_["12CH4_down"]  
    _DATA_["CH4dt"] = _DATA_["C12H4_time_separation"]  
except:
    pass
    
if _DATA_["species"] in TARGET_SPECIES and _PERSISTENT_["plot_iCH4"]:
    # Get peripheral data
    try:    
        if _PERIPH_INTRF_:
            try:
                interpData = _PERIPH_INTRF_( _DATA_["timestamp"], _PERIPH_INTRF_COLS_)
                for i in range(len(_PERIPH_INTRF_COLS_)):
                    if interpData[i] is not None:
                        _NEW_DATA_[_PERIPH_INTRF_COLS_[i]] = interpData[i]
            except Exception, err:
                print "%r" % err
    except:
        pass
        
    exec _PERSISTENT_["adjustOffsetScript"] in globals()
            
    #print _DATA_["species"]
    for k in _DATA_.keys():
        _REPORT_[k] = _DATA_[k]
            
    for k in _NEW_DATA_.keys():
        if k.startswith("Delta"):
            _REPORT_[k] = clipReportData(_NEW_DATA_[k])
        else:    
            _REPORT_[k] = _NEW_DATA_[k]
        
#if _DATA_["species"] in TARGET_SPECIES:
    #print _DATA_["species"]
   
max_adjust = 1.0e-5
max_adjust_H2O = 1.0e-4
max_delay = 20
damp = 0.2

# Check instrument status and do not do any updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)

nowTs = getTimestamp()
delay = nowTs-_DATA_["timestamp"]
if delay > max_delay*1000:
    Log("Large data processing latency, check excessive processor use",
        Data=dict(delay='%.1f s' % (0.001*delay,)),Level=2)
    good = False

if not good:
    print "Updating WLM offset not done because of bad instrument status"
else:
    if _DATA_["species"] == 105: # Update the offset for virtual laser 1
        try:
            co2_adjust = _DATA_["adjust_87"]
            #print 'co2_adjust', co2_adjust
            co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + co2_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            #print "New C12 (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            #print "No new C12 (virtual laser 1) offset"
    elif _DATA_["species"] == 106: # Update the offset for virtual laser 2
        try:
            co2_adjust = _DATA_["adjust_88"]
            co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(2) + co2_adjust
            _NEW_DATA_["wlm2_offset"] = newOffset0
            _PERSISTENT_["wlm2_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
            #print "New C13 (virtual laser 2) offset: %.5f" % newOffset0 
        except:
            pass
            #print "No new C13 (virtual laser 2) offset"

    elif _DATA_["species"] == 150: # Update the offset for virtual laser 3,4,5
        try:
            ch4_adjust = _DATA_["adjust_5"]
            ch4_adjust = min(max_adjust,max(-max_adjust,damp*ch4_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(3) + ch4_adjust
            _NEW_DATA_["wlm3_offset"] = newOffset0
            _PERSISTENT_["wlm3_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
            #print "New (13)CH4(virtual laser 3) offset: %.5f" % newOffset0 
        except:
            pass
            #print "No new (13)CH4 (virtual laser 3) offset"            
                      
        try:
            ch4_adjust = _DATA_["adjust_0"]
            ch4_adjust = min(max_adjust,max(-max_adjust,damp*ch4_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(4) + ch4_adjust
            _NEW_DATA_["wlm4_offset"] = newOffset0
            _PERSISTENT_["wlm4_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(4,float(newOffset0))
            #print "New (12)CH4(virtual laser 4) offset: %.5f" % newOffset0 
        except:
            pass
            #print "No new (12)CH4 (virtual laser 4) offset"
            
        try:
            h2o_adjust = _DATA_["adjust_30"]
            h2o_adjust = min(max_adjust,max(-max_adjust,damp*h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(5) + h2o_adjust
            _NEW_DATA_["wlm5_offset"] = newOffset0
            _PERSISTENT_["wlm5_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(5,float(newOffset0))
            #print "New H2O (virtual laser 5) offset: %.5f" % newOffset0 
        except:
            pass
            #print "No new H2O (virtual laser 5) offset"
  
    #print _PERSISTENT_["plot_iCH4"]
    #elif _DATA_["species"] == 25: # Update the offset for virtual laser 8
        #print "species", _DATA_["species"]
        #print "ch4_high_adjust", _DATA_["ch4_high_adjust"]
        try:
            #print "species", "species", _DATA_["species"]
            ch4_high_adjust = _DATA_["ch4_high_adjust"]
            ch4_high_adjust = min(max_adjust,max(-max_adjust,damp*ch4_high_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(8) + ch4_high_adjust
            _NEW_DATA_["wlm8_offset"] = newOffset0
            _PERSISTENT_["wlm8_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(8,float(newOffset0))
            #print "New CH4 high precision(virtual laser 8) offset: %.5f" % newOffset0 
        except:
            pass
            print "No new CH4 high precision(virtual laser 8) offset"            
                      
          
    elif _DATA_["species"] == 11: # Update the offset for virtual laser 7
        try:
            h2o_adjust = _DATA_["adjust_75"]
            h2o_adjust = min(max_adjust,max(-max_adjust,damp*h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(7) + h2o_adjust
            _NEW_DATA_["wlm7_offset"] = newOffset0
            _PERSISTENT_["wlm7_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(7,float(newOffset0))
            #print "New H2O (virtual laser 7) offset: %.5f" % newOffset0 
        except:
            pass
            print "No new H2O (virtual laser 7) offset"
            
    elif _DATA_["species"] == 153: # Update the offset for virtual laser 6
        try:
            co2_adjust = _DATA_["adjust_24"]
            co2_adjust = min(max_adjust,max(-max_adjust,damp*co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(6) + co2_adjust
            _NEW_DATA_["wlm6_offset"] = newOffset0
            _PERSISTENT_["wlm6_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(6,float(newOffset0))
            #print "New CO2 (virtual laser 6) offset: %.5f" % newOffset0 
        except:
            pass
            print "No new CO2 (virtual laser 6) offset"

  
if _DATA_["species"] in TARGET_SPECIES and (_PERSISTENT_["plot_iCH4"] or _PERSISTENT_["plot_iCO2"]):
    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
    #print 'wlm1_offset', wlm1_offset
    _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    _REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]
    _REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
    _REPORT_["wlm5_offset"] = _PERSISTENT_["wlm5_offset"]
    _REPORT_["wlm6_offset"] = _PERSISTENT_["wlm6_offset"]
    _REPORT_["wlm7_offset"] = _PERSISTENT_["wlm7_offset"]
    _REPORT_["wlm8_offset"] = _PERSISTENT_["wlm8_offset"]

# Save all the variables defined in the _OLD_DATA_  and  _NEW_DATA_ arrays in the
# _PERSISTENT_ arrays so that they can be used in the ChemDetect spreadsheet.
for colname in _OLD_DATA_:    #  new ChemDetect section
     _PERSISTENT_["chemdetect_inst"].current_var_values[colname] = _OLD_DATA_[colname][-1].value
     
for colname in _NEW_DATA_:    
     _PERSISTENT_["chemdetect_inst"].current_var_values[colname] = _NEW_DATA_[colname]
     
if _OLD_DATA_["species"][-1].value == 150:
  _PERSISTENT_["chemdetect_inst"].process_set()
  
  if _PERSISTENT_["chemdetect_inst"].current_var_values['RED'] == True:
     print "WARNING: ChemDetect Status is RED"

if _DATA_["species"] in TARGET_SPECIES and (_PERSISTENT_["plot_iCH4"] or _PERSISTENT_["plot_iCO2"]):
  if _OLD_DATA_["species"][-1].value == 150:
    print ' '
    print '12CH4_high_range = ', _NEW_DATA_["12CH4_high_range"]
    print 'ChemDetect: NOTOK_HC_res2         = ', _PERSISTENT_["chemdetect_inst"].current_var_values['NOTOK_HC_res2']
#   print 'ChemDetect: NOTOK_HC_base_offset2 = ', _PERSISTENT_["chemdetect_inst"].current_var_values['NOTOK_HC_base_offset2']
#   print 'ChemDetect: NOTOK_HC_slope_offset= ', _PERSISTENT_["chemdetect_inst"].current_var_values['NOTOK_HC_slope_offset']
    
    if _PERSISTENT_["chemdetect_inst"].current_var_values['RED'] == True:
       _REPORT_["ChemDetect"] = 1.0  # BAD data
    else:
       _REPORT_["ChemDetect"] = 0.0  # Good data 
  else:
    #_REPORT_["ChemDetect"] = -1.0  ## N/A due to non-ch4 data
    _REPORT_["ChemDetect"] = _PERSISTENT_["ChemDetect_previous"]

  print "_REPORT_[ChemDetect] = ", _REPORT_["ChemDetect"]    
  _PERSISTENT_["ChemDetect_previous"] = _REPORT_["ChemDetect"]

#=================================================================================
