#  Data analysis script for merged C13/C12 and D/H.  Based on CBDS analysis but with major changes to merge with new isotopic water

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
    _PERSISTENT_["cbuffer30"]  = []
    _PERSISTENT_["cbuffer120"] = []
    _PERSISTENT_["cbuffer300"] = []
    _PERSISTENT_["hbuffer30"]  = []
    _PERSISTENT_["hbuffer120"] = []
    _PERSISTENT_["hbuffer300"] = []
    _PERSISTENT_["init"] = False
    _PERSISTENT_["last_delta_time"] = 0
    _PERSISTENT_["delta_interval"] = 0


REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [160,164]

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
DELTA_C = (_INSTR_["c_concentration_iso_slope"],_INSTR_["c_concentration_iso_intercept"])
DELTA_H = (_INSTR_["h_concentration_iso_slope"],_INSTR_["h_concentration_iso_intercept"])
C12 = (_INSTR_["concentration_c12_gal_slope"],_INSTR_["concentration_c12_gal_intercept"])
C13 = (_INSTR_["concentration_c13_gal_slope"],_INSTR_["concentration_c13_gal_intercept"])
H2O = (_INSTR_["concentration_h2o_gal_slope"],_INSTR_["concentration_h2o_gal_intercept"])

try:
    if _DATA_["species"] == 164:
        temp = protDivide(_DATA_["peak24_spec"],_DATA_["peak20_spec"])
        delta_c = applyLinear(temp,DELTA_C)
        _NEW_DATA_["DeltaC13_Raw"] = delta_c
        now = _OLD_DATA_["peak20_spec"][-2].time
        _NEW_DATA_["DeltaC13_30s"] = boxAverage(_PERSISTENT_["cbuffer30"],delta_c,now,30)
        _NEW_DATA_["DeltaC13_2min"] = boxAverage(_PERSISTENT_["cbuffer120"],delta_c,now,120)
        _NEW_DATA_["DeltaC13_5min"] = boxAverage(_PERSISTENT_["cbuffer300"],delta_c,now,300)

        # calculate delta time interval
        now = _OLD_DATA_["peak20_spec"][-1].time
        if _PERSISTENT_["last_delta_time"] != 0:
            delta_interval = now - _PERSISTENT_["last_delta_time"]
        else:
            delta_interval = 0
        _PERSISTENT_["last_delta_time"] = now
        _PERSISTENT_["delta_interval"] = delta_interval
        # end of calculate delta time interval

    else:
        try:
            _NEW_DATA_["DeltaC13_Raw"] = _OLD_DATA_["DeltaC13_Raw"][-1].value
            _NEW_DATA_["DeltaC13_30s"] = _OLD_DATA_["DeltaC13_30s"][-1].value
            _NEW_DATA_["DeltaC13_2min"] = _OLD_DATA_["DeltaC13_2min"][-1].value
            _NEW_DATA_["DeltaC13_5min"] = _OLD_DATA_["DeltaC13_5min"][-1].value
        except:
            _NEW_DATA_["DeltaC13_Raw"] = 0.0
            _NEW_DATA_["DeltaC13_30s"] = 0.0
            _NEW_DATA_["DeltaC13_2min"] = 0.0
            _NEW_DATA_["DeltaC13_5min"] = 0.0
except:
    pass

_NEW_DATA_["delta_interval"] = _PERSISTENT_["delta_interval"]

try:
    if _DATA_["species"] == 160:
        temp = protDivide(_DATA_["peak13_spec"],_DATA_["peak12_spec"])
        delta_h = applyLinear(temp,DELTA_H)
        _NEW_DATA_["DeltaD_Raw"] = delta_h
        now = _OLD_DATA_["peak13_spec"][-1].time
        _NEW_DATA_["DeltaD_30s"] = boxAverage(_PERSISTENT_["hbuffer30"],delta_h,now,30)
        _NEW_DATA_["DeltaD_2min"] = boxAverage(_PERSISTENT_["hbuffer120"],delta_h,now,120)
        _NEW_DATA_["DeltaD_5min"] = boxAverage(_PERSISTENT_["hbuffer300"],delta_h,now,300)
    else:
        try:
            _NEW_DATA_["DeltaD_Raw"] = _OLD_DATA_["DeltaD_Raw"][-1].value
            _NEW_DATA_["DeltaD_30s"] = _OLD_DATA_["DeltaD_30s"][-1].value
            _NEW_DATA_["DeltaD_2min"] = _OLD_DATA_["DeltaD_2min"][-1].value
            _NEW_DATA_["DeltaD_5min"] = _OLD_DATA_["DeltaD_5min"][-1].value
        except:
            _NEW_DATA_["DeltaD_Raw"] = 0.0
            _NEW_DATA_["DeltaD_30s"] = 0.0
            _NEW_DATA_["DeltaD_2min"] = 0.0
            _NEW_DATA_["DeltaD_5min"] = 0.0

except:
    pass

try:
    temp = applyLinear(_DATA_["CO2_626_ppm"],C12)
    _NEW_DATA_["12CO2"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["CO2_636_ppm"],C13)
    _NEW_DATA_["13CO2"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["H2O_ppm"],H2O)
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
    print "Updating WLM offset not done because of bad instrument status"
else:
    if _DATA_["species"] == 164: # Update the offset for virtual lasers 1 and 2
        try:
            co2_adjust = _DATA_["adjust_20"]
            co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + co2_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            # print "New C12 (virtual laser 1) offset: %.5f" % newOffset0
        except:
            pass
            # print "No new C12 (virtual laser 1) offset"

        try:
            co2_adjust = _DATA_["adjust_24"]
            co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(2) + co2_adjust
            _NEW_DATA_["wlm2_offset"] = newOffset0
            _PERSISTENT_["wlm2_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
            # print "New C13 (virtual laser 2) offset: %.5f" % newOffset0
        except:
            pass
            # print "No new C13 (virtual laser 2) offset"

    elif _DATA_["species"] == 160: # Update the offsets for virtual lasers 4 and 5
        try:
            h2o_adjust = _DATA_["adjust_12"]
            h2o_adjust = min(max_adjust,max(-max_adjust,h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(4) + h2o_adjust
            _NEW_DATA_["wlm4_offset"] = newOffset0
            _PERSISTENT_["wlm4_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(4,float(newOffset0))
            # print "New H2O (virtual laser 4) offset: %.5f" % newOffset0
        except:
            pass
            # print "No new H2O (virtual laser 4) offset"
        try:
            hdo_adjust = _DATA_["adjust_13"]
            hdo_adjust = min(max_adjust,max(-max_adjust,hdo_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(5) + hdo_adjust
            _NEW_DATA_["wlm5_offset"] = newOffset0
            _PERSISTENT_["wlm5_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(5,float(newOffset0))
            # print "New HDO (virtual laser 5) offset: %.5f" % newOffset0
        except:
            pass
            # print "No new HDO (virtual laser 5) offset"

if _DATA_["species"] in TARGET_SPECIES:
    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
    _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    _REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]
    _REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
    _REPORT_["wlm5_offset"] = _PERSISTENT_["wlm5_offset"]

