#  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
#  2011 0323 - removed wlm3 feedback for SID 109 (old water at 6250) and used VL3 for the
#              high precision CH4 measurement, SID 25.  Now wlm4 is used exclusively for the
#              low precision CH4 measurement, SID 29, which is also used for iCO2 correction.
#  2011 0727 - modified isotopic methane analysis to use new schemes that report the entire spectrum in one piece
# 2014 0602 removed unnecessary sections left from CFI
#           added flag for isotopic capture when WB within .07 degC tolerance
#           improved reporting structure for Peripheral health monitoring

import os
import sys
import inspect
import traceback

from math import exp

from numpy import mean, isfinite, isnan

from Host.Common.EventManagerProxy import Log, LogExc
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
from Host.Common.timestamp import getTimestamp

here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path:
    sys.path.append(here)

from Chemdetect.instructionprocess import InstructionProcess # new ChemDetect
from Host.Common.CustomConfigObj import CustomConfigObj # new ChemDetect
from Host.PeriphIntrf.PeripheralStatus import PeripheralStatus

# ALARM_STATUS flags
ALARM_STATUS = 0x0000
ALARM_PZT_STD_MASK = 0x8000
ALARM_SHIFT_MASK = 0x4000
ALARM_CAVITY_PRESSURE_MASK = 0x2000
ALARM_CAVITY_TEMP_MASK = 0x1000
ALARM_WARMBOX_TEMP_MASK = 0x800
ALARM_OUTLET_VALVE_MASK = 0x400
ALARM_DELTA_INTERVAL_MASK = 0x200
ALARM_WLM_OFFSET_MASK = 0x100
ALARM_CHEMDETECT_MASK = 0x80
CHEM_DETECT = 0

# Alarm limits
PZT_STD_DEV_LIMIT = 100.0
SHIFT_ABS_LIMIT = 0.001
CAVITY_PRESSURE_LOW_LIMIT = 143.0
CAVITY_PRESSURE_HIGH_LIMIT = 152.0
CAVITY_TEMP_LOW_LIMIT = 40.0
CAVITY_TEMP_HIGH_LIMIT = 50.0
DELTA_INTERVAL_LIMIT = 5.0
OFFSET_ABS_LIMIT = 0.052

GPS_GOOD = 2.0

# System status flags
SYSTEM_STATUS = 0x00000000
SYSTEM_WIND_ANOMALY = 0x0001

# Valve masks
VALVE_MASK_ACTIVE = 0x10


if _PERSISTENT_["init"]:
    _PERSISTENT_["turnOffHeater"] = True
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
    _PERSISTENT_["last_delta_time"] = 0
    _PERSISTENT_["delta_high_conc_iCH4"] = 0
    _PERSISTENT_["delta_high_conc_iCH4_30s"] = 0
    _PERSISTENT_["delta_high_conc_iCH4_2min"] = 0
    _PERSISTENT_["delta_high_conc_iCH4_5min"] = 0
    _PERSISTENT_["delta_interval"] = 0
    _PERSISTENT_["Delta_iCH4_Raw"] = 0.0
    _PERSISTENT_["fineLaserCurrent_6_mean"] = 0
    WBisoTempLocked = False

    # For ChemDetect
    _PERSISTENT_["chemdetect_inst"] = InstructionProcess()
    configFile = os.path.join(here,"..\..\..\InstrConfig\Calibration\InstrCal\ChemDetect\ChemDetect.ini")
    configPath = os.path.split(configFile)[0]

    config = CustomConfigObj(configFile)
    # Get the ChemDetect excel file name from the ini file
    ChemDetect_FileName = config.get("Main", "ChemDetect_FileName") 
    _PERSISTENT_["chemdetect_inst"].load_set_from_csv(os.path.join(configPath,ChemDetect_FileName))
    # need to replace with self.instruction_path
    _PERSISTENT_["ChemDetect_previous"] = 0.0

    _PERSISTENT_['outletValve_min'] = _DRIVER_.rdDasReg(
        'VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER')
    _PERSISTENT_['outletValve_max'] = _DRIVER_.rdDasReg(
        'VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER')

    _PERSISTENT_['inactiveForWind'] = False

    #For Laser Aging
    script = "adjustTempOffset.py"
    scriptRelPath = os.path.join(here, '..', '..', '..', 'CommonConfig',
                                 'Scripts', 'DataManager', script)
    cp = file(os.path.join(here, scriptRelPath), "rU")
    codeAsString = cp.read() + "\n"
    cp.close()
    _PERSISTENT_["adjustOffsetScript"] = compile(codeAsString, script, 'exec')

try:
    if _DATA_LOGGER_ and _DATA_LOGGER_.DATALOGGER_logEnabledRpc('DataLog_Sensor_Minimal'):
        try:
            _DATA_LOGGER_.DATALOGGER_stopLogRpc("DataLog_Sensor_Minimal")
        except Exception, err:
            pass###print "_DATA_LOGGER_ Error: %r" % err
except:
    pass

REPORT_UPPER_LIMIT = 20000.0
REPORT_LOWER_LIMIT = -20000.0

WB_TEMP_ISO_THRESHOLD = 0.07

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

Warmbox_setpoint = _DRIVER_.rdDasReg('WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER')

try:
    NUM_BLOCKING_DATA = _INSTR_["num_blocking_data"]
except:
    NUM_BLOCKING_DATA = 20

#iCH4

_12_ch4_raw = 0.0

# Uses high concentration methane
try:
    _12_ch4_raw = _DATA_["12CH4_raw"]
    temp = applyLinear(_12_ch4_raw,C12_iCH4)
    _NEW_DATA_["12CH4_high_range"] = temp
    _NEW_DATA_["HR_12CH4"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["13CH4_raw"],C13_iCH4)  # Uses high concentration methane
    _NEW_DATA_["13CH4"] = temp
except:
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
    pass

_NEW_DATA_["HR_Delta_iCH4_Raw"] = _PERSISTENT_["delta_high_conc_iCH4"]
_NEW_DATA_["HR_Delta_iCH4_30s"] = _PERSISTENT_["delta_high_conc_iCH4_30s"]
_NEW_DATA_["HR_Delta_iCH4_2min"] = _PERSISTENT_["delta_high_conc_iCH4_2min"]
_NEW_DATA_["HR_Delta_iCH4_5min"] = _PERSISTENT_["delta_high_conc_iCH4_5min"]
_NEW_DATA_["delta_interval"] = _PERSISTENT_["delta_interval"]
_NEW_DATA_["HP_or_HR_mode"] = 1

# Calculate delta with CFADS laser
try:
    if _DATA_["species"]  == 150:
        peak5_spec_low_conc = _DATA_["peakheight_5"] + P5_off_low_conc + P5_quad_low_conc*(_DATA_["ch4_splinemax"])*(_DATA_["ch4_splinemax"])
        peak5_spec_low_conc += P5_A1_low_conc*_DATA_["peak24_spec"] + P5_H1_low_conc*_DATA_["peak30_spec"]+ P5_H1M1_low_conc*_DATA_["peak30_spec"]*_DATA_["peakheight_5"]
        temp = protDivide(peak5_spec_low_conc, _DATA_["ch4_splinemax"])
        delta_iCH4 = applyLinear(temp,DELTA_iCH4)
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

if "HP_Delta_iCH4_Raw" in _NEW_DATA_:
    _PERSISTENT_["Delta_iCH4_Raw"] = _NEW_DATA_["HP_Delta_iCH4_Raw"]

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
    _DATA_["CH4"] = temp
except:
    pass

for v in ['HC_res2_a1', 'HC_res2_diff', 'HC_res2', 'HC_base_offset2_a1', 'HC_base_offset2_diff', 'HC_base_offset2']:
    _NEW_DATA_[v] = 0 # so these always exist in slow or fast modes
    
try: # new ChemDetect section
    Cor_HP_HCres_CO2 = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_HP_HCres_CO2']
    Cor_HP_HCbaseoffset_H2O = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_HP_HCbaseoffset_H2O']
    _NEW_DATA_["HC_res2"] = _DATA_["HC_res"] - Cor_HP_HCres_CO2 * _NEW_DATA_["CO2"] # CO2 Correction on HC_res
    _NEW_DATA_["HC_base_offset2"]= _DATA_["HC_base_offset"] - Cor_HP_HCbaseoffset_H2O * _NEW_DATA_["H2O"] # H2O Cor on HC_base_offset
    a0_HC_base_offset2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a0_HC_base_offset2_HP']
    a1_HC_base_offset2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a1_HC_base_offset2_HP']
    a0_HC_res2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a0_HC_res2_HP']
    a1_HC_res2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a1_HC_res2_HP']

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

suppressReporting = _DATA_['fast_flag'] and _DATA_['species'] != 25


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


# _REPORT_['SYSTEM_STATUS'] = 0x00000000

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

if _DATA_['WarmBoxTemp'] > Warmbox_setpoint - WB_TEMP_ISO_THRESHOLD and _DATA_['WarmBoxTemp'] < Warmbox_setpoint + WB_TEMP_ISO_THRESHOLD:
    WBisoTempLocked = True

else:
    WBisoTempLocked = False


# Pass-through status fields from the peripheral interface
passThrough = [
    PeripheralStatus.WIND_DIRECTION_NOT_AVAILABLE,
    PeripheralStatus.WIND_MESSAGE_CHECKSUM_ERROR,
    PeripheralStatus.WIND_AXIS1_FAILED,
    PeripheralStatus.WIND_AXIS2_FAILED,
    PeripheralStatus.WIND_NONVOLATILE_CHECKSUM_ERROR,
    PeripheralStatus.WIND_ROM_CHECKSUM_ERROR,
    PeripheralStatus.MALFORMED_DATA_STRING,
    PeripheralStatus.WIND_BAD_UNITS
]

if 'PERIPHERAL_STATUS' in _NEW_DATA_:
    for f in passThrough:
        SYSTEM_STATUS |= (int(_NEW_DATA_['PERIPHERAL_STATUS']) & f)

if not good:
    print "Updating WLM offset not done because of bad instrument status"
else:
    # Turn off heater on first good data
    if _PERSISTENT_["turnOffHeater"]:
        Log("Heater turned off")
        _DRIVER_.wrDasReg("HEATER_TEMP_CNTRL_STATE_REGISTER","HEATER_CNTRL_DisabledState")
        _PERSISTENT_["turnOffHeater"] = False

    # Wind anomaly handling
    validWindCheck = True
    windFields = ['PERIPHERAL_STATUS', 'CAR_SPEED', 'GPS_FIT']
    
    for f in windFields:
        validWindCheck &= (f in _NEW_DATA_)

    if validWindCheck:
        if (int(_NEW_DATA_['PERIPHERAL_STATUS']) & PeripheralStatus.WIND_ANOMALY) > 0:
            if not isnan(_NEW_DATA_['CAR_SPEED']) and _NEW_DATA_['GPS_FIT'] == GPS_GOOD:
                print "Wind NaN due to anomaly"
                _PERSISTENT_['inactiveForWind'] = True
            else:
                print "Wind NaN due to GPS"
        else:
            if _PERSISTENT_['inactiveForWind']:
                print "Survey status back to active after wind anomaly"
                _PERSISTENT_['inactiveForWind'] = False

    if _PERSISTENT_['inactiveForWind']:
        SYSTEM_STATUS |= PeripheralStatus.WIND_ANOMALY
        _NEW_DATA_['ValveMask'] = int(_DATA_['ValveMask']) | VALVE_MASK_ACTIVE


    if _DATA_["species"] == 150: # Update the offset for virtual laser 3,4,5
        try:
            ch4_adjust = _DATA_["adjust_5"]
            ch4_adjust = min(max_adjust,max(-max_adjust,damp*ch4_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(3) + ch4_adjust
            _NEW_DATA_["wlm3_offset"] = newOffset0
            _PERSISTENT_["wlm3_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
        except:
            pass

        try:
            ch4_adjust = _DATA_["adjust_0"]
            ch4_adjust = min(max_adjust,max(-max_adjust,damp*ch4_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(4) + ch4_adjust
            _NEW_DATA_["wlm4_offset"] = newOffset0
            _PERSISTENT_["wlm4_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(4,float(newOffset0))
        except:
            pass

        try:
            h2o_adjust = _DATA_["adjust_30"]
            h2o_adjust = min(max_adjust,max(-max_adjust,damp*h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(5) + h2o_adjust
            _NEW_DATA_["wlm5_offset"] = newOffset0
            _PERSISTENT_["wlm5_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(5,float(newOffset0))
        except:
            pass

        try:
            ch4_high_adjust = _DATA_["ch4_high_adjust"]
            ch4_high_adjust = min(max_adjust,max(-max_adjust,damp*ch4_high_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(8) + ch4_high_adjust
            _NEW_DATA_["wlm8_offset"] = newOffset0
            _PERSISTENT_["wlm8_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(8,float(newOffset0))
        except:
            pass

    elif _DATA_["species"] == 11: # Update the offset for virtual laser 7
        try:
            h2o_adjust = _DATA_["adjust_75"]
            h2o_adjust = min(max_adjust,max(-max_adjust,damp*h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(7) + h2o_adjust
            _NEW_DATA_["wlm7_offset"] = newOffset0
            _PERSISTENT_["wlm7_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(7,float(newOffset0))
        except:
            pass

    elif _DATA_["species"] == 153: # Update the offset for virtual laser 6
        try:
            co2_adjust = _DATA_["adjust_24"]
            co2_adjust = min(max_adjust,max(-max_adjust,damp*co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(6) + co2_adjust
            _NEW_DATA_["wlm6_offset"] = newOffset0
            _PERSISTENT_["wlm6_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(6,float(newOffset0))
        except:
            pass

# Save all the variables defined in the _OLD_DATA_  and  _NEW_DATA_ arrays in the
# _PERSISTENT_ arrays so that they can be used in the ChemDetect spreadsheet.
for colname in _OLD_DATA_:    #  new ChemDetect section
    _PERSISTENT_["chemdetect_inst"].current_var_values[colname] = _OLD_DATA_[colname][-1].value

for colname in _NEW_DATA_:
    _PERSISTENT_["chemdetect_inst"].current_var_values[colname] = _NEW_DATA_[colname]

if _OLD_DATA_["species"][-1].value == 150 and not _DATA_['fast_flag']:
    _PERSISTENT_["chemdetect_inst"].process_set()

    if _PERSISTENT_["chemdetect_inst"].current_var_values['RED'] == True:
        pass
        #print "WARNING: ChemDetect Status is RED"

if _DATA_["species"] in TARGET_SPECIES and _PERSISTENT_["plot_iCH4"] and not suppressReporting:
    if _OLD_DATA_["species"][-1].value == 150:
        if _PERSISTENT_["chemdetect_inst"].current_var_values['RED'] == True:
            CHEM_DETECT = 1.0  # BAD data
        else:
            CHEM_DETECT = 0.0  # Good data
    else:
        CHEM_DETECT = _PERSISTENT_["ChemDetect_previous"]

    _PERSISTENT_["ChemDetect_previous"] = CHEM_DETECT

    # Update the upper alarm status bits with some additional instrument status
    # flags.

    if CHEM_DETECT == 1.0:
        ALARM_STATUS |= ALARM_CHEMDETECT_MASK

    pztNames = ['13CH4', '12CH4', 'H2O']
    for name in pztNames:
        try:
            if _DATA_["pzt_%s_stdev" % name] > PZT_STD_DEV_LIMIT:
                ALARM_STATUS |= ALARM_PZT_STD_MASK
                break
        except KeyError:
            pass

    shifts = ['shift_0', 'shift_5', 'shift_24', 'shift_30', 'ch4_high_shift']
    for s in shifts:
        if abs(_DATA_[s]) > SHIFT_ABS_LIMIT:
            ALARM_STATUS |= ALARM_SHIFT_MASK
            break

    # Maybe use unlocked flag instead?
    cavityPressure = _DATA_['cavity_pressure']
    if cavityPressure > CAVITY_PRESSURE_HIGH_LIMIT or \
        cavityPressure < CAVITY_PRESSURE_LOW_LIMIT:
        ALARM_STATUS |= ALARM_CAVITY_PRESSURE_MASK

    cavityTemp = _DATA_['cavity_temperature']
    if cavityTemp > 50.0 or cavityTemp < 40.0:
        ALARM_STATUS |= ALARM_CAVITY_TEMP_MASK

    warmBoxTemp = _DATA_['WarmBoxTemp']
    if warmBoxTemp > CAVITY_TEMP_HIGH_LIMIT or \
        warmBoxTemp < CAVITY_TEMP_LOW_LIMIT:
        ALARM_STATUS |= ALARM_WARMBOX_TEMP_MASK

    outletValve = _DATA_['OutletValve']
    if outletValve > _PERSISTENT_['outletValve_max'] or \
        outletValve < _PERSISTENT_['outletValve_min']:
        ALARM_STATUS |= ALARM_OUTLET_VALVE_MASK

    if _PERSISTENT_['delta_interval'] > DELTA_INTERVAL_LIMIT:
        ALARM_STATUS |= ALARM_DELTA_INTERVAL_MASK

    wlmOffsets = ['wlm3_offset', 'wlm4_offset', 'wlm5_offset']
    for offset in wlmOffsets:
        # Each FSR is ~0.026 in offset.
        if abs(_PERSISTENT_[offset]) > OFFSET_ABS_LIMIT:
            ALARM_STATUS |= ALARM_WLM_OFFSET_MASK
            break

if _DATA_["species"] in TARGET_SPECIES and _PERSISTENT_["plot_iCH4"] and not suppressReporting:

    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
    _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    _REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]
    _REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
    _REPORT_["wlm5_offset"] = _PERSISTENT_["wlm5_offset"]
    _REPORT_["wlm6_offset"] = _PERSISTENT_["wlm6_offset"]
    _REPORT_["wlm7_offset"] = _PERSISTENT_["wlm7_offset"]
    _REPORT_["wlm8_offset"] = _PERSISTENT_["wlm8_offset"]
    _REPORT_["SYSTEM_STATUS"] = SYSTEM_STATUS
    _REPORT_["ALARM_STATUS"] = ALARM_STATUS
    _REPORT_["CHEM_DETECT"] = CHEM_DETECT
    _REPORT_["WBisoTempLocked"] = WBisoTempLocked
    _REPORT_["fineLaserCurrent_6_mean"] = _PERSISTENT_["fineLaserCurrent_6_mean"]  #report 0 for VL6 made to prevent new Column upon mode switch when WL is on to track CO2
    
    exec _PERSISTENT_["adjustOffsetScript"] in globals()
    
    for k in _DATA_.keys():
        _REPORT_[k] = _DATA_[k]

    for k in _NEW_DATA_.keys():
        if k.startswith("Delta"):
            _REPORT_[k] = clipReportData(_NEW_DATA_[k])
        else:
            _REPORT_[k] = _NEW_DATA_[k]

#=================================================================================
