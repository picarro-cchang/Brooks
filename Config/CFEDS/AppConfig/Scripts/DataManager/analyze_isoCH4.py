import sys
import os
if os.path.isdir("../AppConfig/Scripts/DataManager"):
    # For .exe version
    pulseAnalyzerPath = "../AppConfig/Scripts/DataManager"
elif os.path.isdir("../../AppConfig/Scripts/DataManager"):
    # For .py version
    pulseAnalyzerPath = "../../AppConfig/Scripts/DataManager"

if pulseAnalyzerPath not in sys.path: sys.path.append(pulseAnalyzerPath)
import time
from PulseAnalyzer import PulseAnalyzer
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED


if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm3_offset"] = 0.0
    _PERSISTENT_["init"] = False


REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0

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

# Define linear transformtions for post-processing
DELTA = (_INSTR_["concentration_iso_slope"],_INSTR_["concentration_iso_intercept"])
RATIO = (_INSTR_["concentration_r_slope"],_INSTR_["concentration_r_intercept"])
C12 = (_INSTR_["concentration_c12_gal_slope"],_INSTR_["concentration_c12_gal_intercept"])
C13 = (_INSTR_["concentration_c13_gal_slope"],_INSTR_["concentration_c13_gal_intercept"])
H2O = (_INSTR_["concentration_h2o_gal_slope"],_INSTR_["concentration_h2o_gal_intercept"])
CO2 = (_INSTR_["concentration_co2_gal_slope"],_INSTR_["concentration_co2_gal_intercept"])
PEAK2_INTCPT = -_INSTR_["peak2_offset"]
RECIP2 = _INSTR_["peak2_recipLin"]
RECIPSQR2 = -_INSTR_["peak2_recipQuad"]
PEAK3_OFFSET = _INSTR_["peak3_offset"]
PEAK3_QUAD = _INSTR_["peak3_quad"]
PEAK2_ZERO = (1.0,_INSTR_["peak2_offset"])
PEAK3_ZERO = (1.0,_INSTR_["peak3_offset"])

try:
    if _DATA_["species"] == 1: #CH4
        # Note: _OLD_DATA_[][-1] is the current data
        #delta = protDivide(_DATA_["peak2"], _DATA_["peak3"])
        #peak2_corr = _DATA_["peak2"]-PEAK2_INTCPT-RECIP2/_DATA_["peak3"]-RECIPSQR2/(_DATA_["peak3"]**2)
        peak3_corr = _DATA_["peak3"] + PEAK3_OFFSET + PEAK3_QUAD*_DATA_["peak2"]**2
        #delta = protDivide(peak2_corr,_DATA_["peak3"])
        delta = protDivide(_DATA_["peak2"],peak3_corr)
        _NEW_DATA_["delta"] = applyLinear(delta,DELTA)
        ratio = protDivide(_DATA_["peak2"],peak3_corr)
        temp = applyLinear(ratio,RATIO)
        _NEW_DATA_["ratio"] = temp
        temp = applyLinear(peak3_corr,C12)
        _NEW_DATA_["12ch4_conc"] = temp
        temp = applyLinear(_DATA_["peak2"],C13)
        _NEW_DATA_["13ch4_conc"] = temp
    else:
        _NEW_DATA_["delta"] = _OLD_DATA_["delta"][-1].value
        _NEW_DATA_["ratio"] = _OLD_DATA_["ratio"][-1].value
        _NEW_DATA_["12ch4_conc"] = _OLD_DATA_["12ch4_conc"][-1].value
        _NEW_DATA_["13ch4_conc"] = _OLD_DATA_["13ch4_conc"][-1].value
except:
    pass

try:
    if _DATA_["species"] == 3: #H2O
        temp = applyLinear(_DATA_["str33"],H2O)
        _NEW_DATA_["h2o_conc"] = temp
    else:
        _NEW_DATA_["h2o_conc"] = _OLD_DATA_["h2o_conc"][-1].value
except:
    pass

try:
    if _DATA_["species"] == 5: #12CO2
        temp = applyLinear(_DATA_["str_87"],CO2)
        _NEW_DATA_["co2_conc"] = temp
    else:
        _NEW_DATA_["co2_conc"] = _OLD_DATA_["co2_conc"][-1].value
except:
    pass

for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_.keys():
    if k == "delta":
        _REPORT_[k] = clipReportData(_NEW_DATA_[k])
    else:
        _REPORT_[k] = _NEW_DATA_[k]


max_adjust = 1.0e-5

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
    if _DATA_["spectrum"] == 105: # Update the offset for virtual laser 1
        try:
            co2_adjust = _DATA_["cm_adjust"]
            co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + co2_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            print "New C12 (virtual laser 1) offset: %.5f" % newOffset0
        except:
            print "No new C12 (virtual laser 1) offset"

    #elif _DATA_["spectrum"] == 109: # Update the offset for virtual laser 2
    elif _DATA_["spectrum"] == 153: # Update the offset for virtual laser 2
        try:
            h2o_adjust = _DATA_["h2o_adjust"]
            h2o_adjust = min(max_adjust,max(-max_adjust,h2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(2) + h2o_adjust
            _NEW_DATA_["wlm2_offset"] = newOffset0
            _PERSISTENT_["wlm2_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
            print "New H2O (virtual laser 2) offset: %.5f" % newOffset0
        except:
            print "No new H2O (virtual laser 2) offset"

    elif _DATA_["spectrum"] == 150: # Update the offsets for virtual laser 3
        try:
            ch4_adjust = _DATA_["ch4_adjust"]
            ch4_adjust = min(max_adjust,max(-max_adjust,ch4_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(3) + ch4_adjust
            _NEW_DATA_["wlm3_offset"] = newOffset0
            _PERSISTENT_["wlm3_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
            print "New CH4 (virtual laser 3) offset: %.5f" % newOffset0
        except:
            print "No new CH4 (virtual laser 3) offset"

try:
    _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
    _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
    _REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]
except:
    print "Cannot report all wlm_offsets"
