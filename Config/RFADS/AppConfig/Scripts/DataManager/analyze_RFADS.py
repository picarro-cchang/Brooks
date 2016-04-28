#  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
# 20150701  Added ethane scan, and analysis at WLM, from analyze_expt.py  (proj 26)
# 20160208  Added peak detector state to the report. Commented out isotopic methane section          
# 20160210  Cleaned script to only report ethane and methane for surveyor and Peripherals

import os
import sys
import inspect
import traceback
import collections

from math import exp

import numpy
from numpy import mean, isfinite, isnan

from Host import PeriphIntrf

from Host.Common.EventManagerProxy import Log, LogExc
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
from Host.Common.timestamp import getTimestamp
from Host.Common.CustomConfigObj import CustomConfigObj

here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path:
    sys.path.append(here)

# From fitterThread.py -- should be integrated into DM to use the "flat" .ini structure of FitterConfig.ini
def evalLeaves(d):
    for k in d:
        if isinstance(d[k],dict):
            evalLeaves(d[k])
        else:
            try:
                d[k] = eval(d[k])
            except:
                pass
    return d
    
if _PERSISTENT_["init"]:
    _PERSISTENT_["turnOffHeater"] = True

    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm7_offset"] = 0.0
    _PERSISTENT_["wlm8_offset"] = 0.0
    _PERSISTENT_["buffer30"]  = []
    _PERSISTENT_["buffer120"] = []
    _PERSISTENT_["buffer300"] = []
    _PERSISTENT_["init"] = False
    _PERSISTENT_["num_values"] = 0    
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

    fitterConfigFile = os.path.join(here,'..','..','..','InstrConfig','Calibration','InstrCal','FitterConfig.ini')
    fitterConfig = evalLeaves(CustomConfigObj(fitterConfigFile, list_values=False).copy())
    _PERSISTENT_['baselineCavityLoss'] = fitterConfig['CFADS_Baseline_level']
    _PERSISTENT_['C2H6_nominal_sdev'] = _INSTR_["C2H6_nominal_sdev"]

try:
    if _DATA_LOGGER_ and _DATA_LOGGER_.DATALOGGER_logEnabledRpc('DataLog_Sensor_Minimal'):
        try:
            _DATA_LOGGER_.DATALOGGER_stopLogRpc("DataLog_Sensor_Minimal")
        except Exception, err:
            pass###print "_DATA_LOGGER_ Error: %r" % err
except:
    pass

TARGET_SPECIES = [170]

def clipReportData(value):
    if value > REPORT_UPPER_LIMIT:
        return REPORT_UPPER_LIMIT
    elif  value < REPORT_LOWER_LIMIT:
        return REPORT_LOWER_LIMIT
    else:
        return value

def applyLinear(value,xform):
    return xform[0]*value + xform[1]

def protDivide(num,den):
    if den != 0:
        return num/den
    return 0

def boxAverage(buffer,x,t,tau):
    buffer.append((x,t))
    while t-buffer[0][1] > tau:
        buffer.pop(0)
    return mean([d for (d,t) in buffer])

# Handle options from command line
optDict = eval("dict(%s)" % _OPTIONS_)
conc = optDict.get("conc", "high").lower()

# Define linear transformtions for post-processing
C12_CH4_CFADS = (_INSTR_["CH4_CFADS_concentration_c12_gal_slope"],_INSTR_["CH4_CFADS_concentration_c12_gal_intercept"])
C2H6 = (_INSTR_["C2H6_concentration_slope"],_INSTR_["C2H6_concentration_intercept"])

Warmbox_setpoint = _DRIVER_.rdDasReg('WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER')

try:
    NUM_BLOCKING_DATA = _INSTR_["num_blocking_data"]
except:
    NUM_BLOCKING_DATA = 20

# new RADS ethane section
try:
    ch4 = applyLinear(_DATA_["ch4_conc_ppmv_final"],C12_CH4_CFADS)
    c2h6 = applyLinear(_DATA_["c2h6_conc_corrected"],C2H6)
    ratio = protDivide(c2h6,ch4)
    _NEW_DATA_["CH4"] = ch4
    _NEW_DATA_["C2H6"] = c2h6
    _NEW_DATA_["C2H4_PF"] = _DATA_["PF_c2h4_conc"]
    _NEW_DATA_["C2H6_PF"] = _DATA_["PF_c2h6_conc"]
    _NEW_DATA_["C2C1Ratio"] = ratio
    _NEW_DATA_["H2O"] = 0.0001*_DATA_["h2o_conc"]
    now = _OLD_DATA_["C2C1Ratio"][-1].time
    _NEW_DATA_["Ratio_30s"] = boxAverage(_PERSISTENT_["buffer30"],ratio,now,30)
    _NEW_DATA_["Ratio_2min"] = boxAverage(_PERSISTENT_["buffer120"],ratio,now,120)
    _NEW_DATA_["Ratio_5min"] = boxAverage(_PERSISTENT_["buffer300"],ratio,now,300)
    if _PERSISTENT_["num_values"] <= NUM_BLOCKING_DATA:
        _PERSISTENT_["num_values"] += 1
    elif not _PERSISTENT_["plot"]:
        _PERSISTENT_["plot"] = True
except:
    pass

    
try:
    _DATA_["CH4up"] = _DATA_["12CH4_up"]
    _DATA_["CH4down"] = _DATA_["12CH4_down"]
    _DATA_["CH4dt"] = _DATA_["C12H4_time_separation"]
except:
    pass

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
    # Turn off heater on first good data
    if _PERSISTENT_["turnOffHeater"]:
        Log("Heater turned off")
        _DRIVER_.wrDasReg("HEATER_TEMP_CNTRL_STATE_REGISTER","HEATER_CNTRL_DisabledState")
        _PERSISTENT_["turnOffHeater"] = False

    elif (_DATA_["species"] == 170): # Update the offset for virtual laser 2
        try:
            adjust = _DATA_["c2h6_adjust"]
            adjust = min(max_adjust,max(-max_adjust,adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(2) + adjust
            _NEW_DATA_["wlm2_offset"] = newOffset0
            _PERSISTENT_["wlm2_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
        except:
            pass
        
        try:
            ch4_high_adjust = _DATA_["ch4_adjust"]
            ch4_high_adjust = min(max_adjust,max(-max_adjust,damp*ch4_high_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(8) + ch4_high_adjust
            _NEW_DATA_["wlm8_offset"] = newOffset0
            _PERSISTENT_["wlm8_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(8,float(newOffset0))
        except:
            pass

if _DATA_["species"] in TARGET_SPECIES:
    _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    _REPORT_["wlm8_offset"] = _PERSISTENT_["wlm8_offset"]
        
    exec _PERSISTENT_["adjustOffsetScript"] in globals()
    
    for k in _DATA_.keys():
        _REPORT_[k] = _DATA_[k]

    for k in _NEW_DATA_.keys():
        if k.startswith("Delta"):
            _REPORT_[k] = clipReportData(_NEW_DATA_[k])
        else:
            _REPORT_[k] = _NEW_DATA_[k]
    _REPORT_["peak_detector_state"] = _DRIVER_.rdDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER")
    _REPORT_['C2H6_nominal_sdev'] = _PERSISTENT_['C2H6_nominal_sdev']
#=================================================================================
