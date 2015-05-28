#  Analysis script for isotopic water at 7200 wavenumbers.
#  2011 0804:  Added time averages to experimental analysis script and changed names to conform better to HBDS style
#  2011 0819:  Added methane reporting with averaging and changed reporting of concentrations to be more self-consistent
#  2012 0215:  Reduced max shift from 1e-4 to 1e-5 to prevent "mouse bites"
#  2012 0216:  Changed reported deltas to include methane cross-talk correction for air carrier ONLY (logbook III.66)
#  2012 0328:  Tweaked methane cross-talk coefficients based on more careful CH4/water step test
#  2012 0822:  Added conditions for stable operation and correct pressure to WLM update
#  2014 0319:  Changed methane correction coefficients to compensate for changed water calibration (jah)
#              Changed total water reporting to include delta17=0.528*delta18 and doubly rare isotopologues (jah)
#  2014 0613:  Changed WLM adjust/offset reporting to work correctly when pressure is unlocked

import inspect
import sys
import os
from numpy import mean
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)

if os.path.isdir("../AppConfig/Scripts/DataManager"):
    # For .exe version
    pulseAnalyzerPath = "../AppConfig/Scripts/DataManager"
elif os.path.isdir("../../AppConfig/Scripts/DataManager"):
    # For .py version
    pulseAnalyzerPath = "../../AppConfig/Scripts/DataManager"

if pulseAnalyzerPath not in sys.path: sys.path.append(pulseAnalyzerPath)
import time
from PulseAnalyzer import PulseAnalyzer
REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0
max_shift = 1.0e-5
H16OH_cm_adjust_gain = 0.2
H18OH_cm_adjust_gain = 0.2
H16OD_cm_adjust_gain = 0.2
R17_VSMOW = 0.0003799
R18_VSMOW = 0.0020052
RD_VSMOW = 0.00031153
Rest_VSMOW = 6.432e-7

# Static variables for averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["Dbuffer30"]  = []
    _PERSISTENT_["Dbuffer120"] = []
    _PERSISTENT_["Dbuffer300"] = []
    _PERSISTENT_["O18buffer30"]  = []
    _PERSISTENT_["O18buffer120"] = []
    _PERSISTENT_["O18buffer300"] = []
    _PERSISTENT_["CH4buffer30"]  = []
    _PERSISTENT_["CH4buffer120"] = []
    _PERSISTENT_["CH4buffer300"] = []
    _PERSISTENT_["init"] = False

    script = "adjustTempOffset.py"
    scriptRelPath = os.path.join(here, '..', '..', '..', 'CommonConfig',
                                 'Scripts', 'DataManager', script)
    cp = file(os.path.join(here, scriptRelPath), "rU")
    codeAsString = cp.read() + "\n"
    cp.close()
    _PERSISTENT_["adjustOffsetScript"] = compile(codeAsString, script, 'exec')

exec _PERSISTENT_["adjustOffsetScript"] in globals()

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

def boxAverage(buffer,x,t,tau):
    buffer.append((x,t))
    while t-buffer[0][1] > tau:
        buffer.pop(0)
    return mean([d for (d,t) in buffer])

laserMap = [3,4,5,-1,-1] #physical laser number as function of species (index); -1 => not valid
adjustMap = ["h16oh","h18oh","h16od","",""]

def adjustWLM(species,max_adj,gain):
    laser = laserMap[int(species)]
    adjust = adjustMap[int(species)]
    if laser == -1:
        print "No offset update"
        return None, None
    else:
        try:
            cm_adjust = _DATA_[adjust+"_adjust"]*gain
            cm_adjust = min(max_adj,max(-max_adj,cm_adjust))
            #_NEW_DATA_[adjust+"_WLMadjust"] = cm_adjust
            newOffset = _FREQ_CONV_.getWlmOffset(laser) + cm_adjust
            #_NEW_DATA_["wlm"+adjust+"_offset"] = newOffset
            _FREQ_CONV_.setWlmOffset(laser,float(newOffset))
            return cm_adjust, newOffset
            # print "new offset %d: %.5f" % laser % newOffset
        except:
            return None, None
            #print "No offset %d update" % laser

# Define linear transformtions for post-processing
DELTA_18O = (_INSTR_["delta_18o_slope"],_INSTR_["delta_18o_intercept"])
DELTA_D = (_INSTR_["delta_d_slope"],_INSTR_["delta_d_intercept"])
H16OH = (_INSTR_["concentration_h16oh_gal_slope"],_INSTR_["concentration_h16oh_gal_intercept"])
H18OH = (_INSTR_["concentration_h18oh_gal_slope"],_INSTR_["concentration_h18oh_gal_intercept"])
H16OD = (_INSTR_["concentration_h16od_gal_slope"],_INSTR_["concentration_h16od_gal_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])

if _DATA_["spectrum"] in [123,124]:
    try:
        # Note: _OLD_DATA_[][-1] is the current data
        now = _OLD_DATA_["peak2_offset"][-1].time
        h2o_conc = applyLinear(_DATA_["h2o_ppm"],H2O)
        ch4_conc = applyLinear(_DATA_["ch4_ppm"],CH4)
        _NEW_DATA_["CH4"] = ch4_conc
        _NEW_DATA_["CH4_30s"] = boxAverage(_PERSISTENT_["CH4buffer30"],ch4_conc,now,30)
        _NEW_DATA_["CH4_2min"] = boxAverage(_PERSISTENT_["CH4buffer120"],ch4_conc,now,120)
        _NEW_DATA_["CH4_5min"] = boxAverage(_PERSISTENT_["CH4buffer300"],ch4_conc,now,300)
        h16oh_conc = applyLinear(_DATA_["peak2_offset"],H16OH)
        h18oh_conc = applyLinear(_DATA_["peak1_offset"],H18OH)
        h16od_conc = applyLinear(_DATA_["peak3_offset"],H16OD)
        ratioO = protDivide(h18oh_conc,h16oh_conc)
        Delta_18_16 = applyLinear(ratioO,DELTA_18O)
        if _DATA_["n2_flag"] == 0:
            Delta_18_16 -= 898.8*ch4_conc/h2o_conc
        _NEW_DATA_["Delta_18_16"] = Delta_18_16
        _NEW_DATA_["Delta_18_16_30s"] = boxAverage(_PERSISTENT_["O18buffer30"],Delta_18_16,now,30)
        _NEW_DATA_["Delta_18_16_2min"] = boxAverage(_PERSISTENT_["O18buffer120"],Delta_18_16,now,120)
        _NEW_DATA_["Delta_18_16_5min"] = boxAverage(_PERSISTENT_["O18buffer300"],Delta_18_16,now,300)
        ratioD = protDivide(h16od_conc,h16oh_conc)
        Delta_D_H = applyLinear(ratioD,DELTA_D)
        if _DATA_["n2_flag"] == 0:
            Delta_D_H += 2090*ch4_conc/h2o_conc
        _NEW_DATA_["Delta_D_H"] = Delta_D_H
        _NEW_DATA_["Delta_D_H_30s"] = boxAverage(_PERSISTENT_["Dbuffer30"],Delta_D_H,now,30)
        _NEW_DATA_["Delta_D_H_2min"] = boxAverage(_PERSISTENT_["Dbuffer120"],Delta_D_H,now,120)
        _NEW_DATA_["Delta_D_H_5min"] = boxAverage(_PERSISTENT_["Dbuffer300"],Delta_D_H,now,300)
        Delta_17_16 = 0.528*Delta_18_16
        h2o_conc *= (1.0 + (1.0+0.001*Delta_17_16)*R17_VSMOW + (1.0+0.001*Delta_18_16)*R18_VSMOW + (1.0+0.001*Delta_D_H)*RD_VSMOW + Rest_VSMOW)
        _NEW_DATA_["H2O"] = h2o_conc

    except:
        pass

# Check instrument status and do not do any WLM updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if abs(_DATA_["CavityPressure"]-50.0) > 10:
    good = False

if not good:
    #print "Updating WLM offset not done because of bad instrument status"
    _NEW_DATA_["h16oh_WLMadjust"] = _OLD_DATA_["h16oh_WLMadjust"][-1].value
    _NEW_DATA_["h18oh_WLMadjust"] = _OLD_DATA_["h18oh_WLMadjust"][-1].value
    _NEW_DATA_["h16od_WLMadjust"] = _OLD_DATA_["h16od_WLMadjust"][-1].value
    _NEW_DATA_["WLMh16oh_offset"] = _OLD_DATA_["WLMh16oh_offset"][-1].value
    _NEW_DATA_["WLMh18oh_offset"] = _OLD_DATA_["WLMh18oh_offset"][-1].value
    _NEW_DATA_["WLMh16od_offset"] = _OLD_DATA_["WLMh16od_offset"][-1].value

else:
    if _DATA_["spectrum"] in [123,124]:
        try:
            _NEW_DATA_["h16oh_WLMadjust"], _NEW_DATA_["WLMh16oh_offset"] = adjustWLM(0,max_shift,H16OH_cm_adjust_gain)
            _NEW_DATA_["h18oh_WLMadjust"], _NEW_DATA_["WLMh18oh_offset"] = adjustWLM(1,max_shift,H18OH_cm_adjust_gain)
            _NEW_DATA_["h16od_WLMadjust"], _NEW_DATA_["WLMh16od_offset"] = adjustWLM(2,max_shift,H16OD_cm_adjust_gain)
            #print "Updated WLM offsets for virtual lasers 1--3"
        except:
            pass

for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_.keys():
    if k == "delta":
        _REPORT_[k] = clipReportData(_NEW_DATA_[k])
    else:
        _REPORT_[k] = _NEW_DATA_[k]
