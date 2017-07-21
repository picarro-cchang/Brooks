#  Analysis script for AEDS Ammonia analyzer started by Hoffnagle 2010-12-15
#  2014 0731:  Added correction for direct and indirect water interference, dry-mole-fraction
#              Added nonlinear calculation of h2o_actual based on cross-calibration with CFADS
#  2015 0611:  Changed reporting so that "NH3" now means dry mole fraction, not raw value.

import os
import sys
import inspect
from math import exp
from numpy import mean, sqrt
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

# Need to find path to the translation table
here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)
from translate import newname
from DynamicNoiseFilter import variableExpAverage, negative_number_filter

# Static variables used for wlm offsets, bookending and averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["buffer30"]  = []
    _PERSISTENT_["buffer120"] = []
    _PERSISTENT_["buffer300"] = []
    _PERSISTENT_["ignore_count"] = 5

    _PERSISTENT_["bufferExpAvg_NH3"] = []
    _PERSISTENT_["bufferZZ_NH3"] = []
    _PERSISTENT_["previousNoise_NH3"]=0.0
    _PERSISTENT_["previousS_NH3"]=0.0
    _PERSISTENT_["tau_NH3"]=0.0
    _PERSISTENT_["NH3_filter"]=0.0
    _PERSISTENT_["Pressure_Save"]=140.0
    _PERSISTENT_["init"] = False


REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [2, 4]

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
NH3_CONC = (_INSTR_["concentration_nh3_slope"],_INSTR_["concentration_nh3_intercept"])
CO2_CONC = (_INSTR_["concentration_co2_slope"],_INSTR_["concentration_co2_intercept"])
H2O_CONC = (_INSTR_["concentration_h2o_slope"],_INSTR_["concentration_h2o_intercept"])

# Import water selfbroadening, cross-talk and cross-broadening parameters
Hlin = _INSTR_["water_linear"]
Hquad = _INSTR_["water_quadratic"]
H1 = _INSTR_["water_crosstalk_linear"]
A1H1 = _INSTR_["water_crossbroadening_linear"]
A1H2 = _INSTR_["water_crossbroadening_quadratic"]

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if abs(_DATA_["CavityPressure"]-140.0) > 0.1:
    good = False

if _DATA_["species"] == 4:
    try:
        _NEW_DATA_["CO2"] = _OLD_DATA_["CO2"][-1].value
        _NEW_DATA_["H2O"] = _OLD_DATA_["H2O"][-1].value
    except:
        pass

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
        _NEW_DATA_["NH3_raw"] = dry
        #print "NH3_raw=", _NEW_DATA_["NH3_raw"]

        if((_DATA_["species"]==4) and (abs(_DATA_["CavityPressure"]-_PERSISTENT_["Pressure_Save"]) < 2.0)):
            _PERSISTENT_["NH3_filter"] = dry 
            _PERSISTENT_["previousS_NH3"],_PERSISTENT_["previousNoise_NH3"],_PERSISTENT_["tau_NH3"] = variableExpAverage(_PERSISTENT_["bufferZZ_NH3"],_PERSISTENT_["bufferExpAvg_NH3"],dry,now,1100,1,_PERSISTENT_["previousS_NH3"],_PERSISTENT_["previousNoise_NH3"])
        _PERSISTENT_["Pressure_Save"]=_DATA_["CavityPressure"]
        _NEW_DATA_["NH3_sigma"]=_PERSISTENT_["previousNoise_NH3"]*1.5*sqrt(2)
        _NEW_DATA_["NH3_ExpAvg"]=_PERSISTENT_["previousS_NH3"]
        _NEW_DATA_["NH3_tau"]=_PERSISTENT_["tau_NH3"]
        _NEW_DATA_["NH3_filter"] = _PERSISTENT_["NH3_filter"]
        _NEW_DATA_["NH3raw-NH3expavg"] = _NEW_DATA_["NH3_filter"] - _NEW_DATA_["NH3_ExpAvg"]
        _NEW_DATA_["NH3_ExpAvg_NZ"] = negative_number_filter("NH3",_NEW_DATA_["NH3_ExpAvg"])
        _NEW_DATA_["NH3"]=_NEW_DATA_["NH3_ExpAvg_NZ"]
        #print "NH3=", _NEW_DATA_["NH3"]
        _NEW_DATA_["NH3_30s"] = boxAverage(_PERSISTENT_["buffer30"],dry,now,30)
        _NEW_DATA_["NH3_2min"] = boxAverage(_PERSISTENT_["buffer120"],dry,now,120)
        _NEW_DATA_["NH3_5min"] = boxAverage(_PERSISTENT_["buffer300"],dry,now,300)
        
    except:
        pass

if _DATA_["species"] == 2:
    try:
        h2o_actual = Hlin*_DATA_["peak15"] + Hquad*_DATA_["peak15"]**2
        temp = applyLinear(h2o_actual,H2O_CONC)
        _NEW_DATA_["H2O"] = temp
    except:
        pass

    try:
        _NEW_DATA_["NH3_uncorrected"] = _OLD_DATA_["NH3_uncorrected"][-1].value
        _NEW_DATA_["NH3_broadeningCorrected"] = _OLD_DATA_["NH3_broadeningCorrected"][-1].value
        _NEW_DATA_["NH3_dry"] = _OLD_DATA_["NH3_dry"][-1].value
        _NEW_DATA_["NH3_raw"] = _OLD_DATA_["NH3_Raw"][-1].value
        _NEW_DATA_["NH3_30s"] = _OLD_DATA_["NH3_30s"][-1].value
        _NEW_DATA_["NH3_2min"] = _OLD_DATA_["NH3_2min"][-1].value
        _NEW_DATA_["NH3_5min"] = _OLD_DATA_["NH3_5min"][-1].value
        
        _NEW_DATA_["NH3_sigma"]=_PERSISTENT_["previousNoise_NH3"]*1.5*sqrt(2)
        _NEW_DATA_["NH3_ExpAvg"]=_PERSISTENT_["previousS_NH3"]
        _NEW_DATA_["NH3_tau"]=_PERSISTENT_["tau_NH3"]
        _NEW_DATA_["NH3_filter"] = _PERSISTENT_["NH3_filter"]
        _NEW_DATA_["NH3raw-NH3expavg"] = _NEW_DATA_["NH3_filter"] - _NEW_DATA_["NH3_ExpAvg"]
        _NEW_DATA_["NH3_ExpAvg_NZ"] = negative_number_filter("NH3",_NEW_DATA_["NH3_ExpAvg"])
        _NEW_DATA_["NH3"]=_NEW_DATA_["NH3_ExpAvg_NZ"]
        #print "NH3=", _NEW_DATA_["NH3"]
    
    except:
        pass

    try:
        temp = applyLinear(_DATA_["co2_conc"],CO2_CONC)
        _NEW_DATA_["CO2"] = temp
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
    if _DATA_["species"] == 2: # Update the offset for virtual laser 1
        try:
            nh3_adjust = _DATA_["cm_adjust"]
            nh3_adjust = min(max_adjust,max(-max_adjust,nh3_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + nh3_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            # print "New NH3 (virtual laser 1) offset: %.5f" % newOffset0
        except:
            pass
            # print "No new NH3 (virtual laser 1) offset"

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
