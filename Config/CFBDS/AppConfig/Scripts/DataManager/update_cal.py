from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

scanningMode = _ARGS_[0]
max_shift = 2.0e-4

# Check instrument status and do not do any updates if any parameters are unlocked

print "Instrument status", _INSTR_STATUS_
pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if not good:
    print "Updating WLM offset not done because of bad instrument status"
else:
    if "CO2" in scanningMode:
        try:
            co2_shift = _OLD_DATA_["avg_co2_shift"][-1].value/5.0
            co2_shift = min(max_shift,max(-max_shift,co2_shift))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + co2_shift
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            # print "new CO2 offset: %.5f" % newOffset0
        except:
            # print "No CO2 offset update"
            pass

    if "CH4" in scanningMode:
        try:
            ch4_shift = _OLD_DATA_["avg_ch4_shift"][-1].value/5.0
            ch4_shift = min(max_shift,max(-max_shift,ch4_shift))
            newOffset1 = _FREQ_CONV_.getWlmOffset(2) + ch4_shift
            _NEW_DATA_["wlm2_offset"] = newOffset1
            _FREQ_CONV_.setWlmOffset(2,float(newOffset1))
            # print "new CH4 offset: %.5f" % newOffset1
        except:
            # print "No CH4 offset update"
            pass

    # H2O can be on either 1st or 2nd actual laser (virtual laser 3 & 4)
    if scanningMode.find("H2O") == 0:
        try:
            h2o_shift = _OLD_DATA_["avg_h2o_shift"][-1].value/5.0
            h2o_shift = min(max_shift,max(-max_shift,h2o_shift))
            newOffset0 = _FREQ_CONV_.getWlmOffset(3) + h2o_shift
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
            # print "new H2O offset: %.5f" % newOffset0
        except:
            # print "No H2O offset update"
            pass
    if scanningMode.find("H2O") == 4:
        try:
            h2o_shift = _OLD_DATA_["avg_h2o_shift"][-1].value/5.0
            h2o_shift = min(max_shift,max(-max_shift,h2o_shift))
            newOffset1 = _FREQ_CONV_.getWlmOffset(4) + h2o_shift
            _NEW_DATA_["wlm2_offset"] = newOffset1
            _FREQ_CONV_.setWlmOffset(4,float(newOffset1))
            # print "new H2O offset: %.5f" % newOffset1
        except:
            # print "No H2O offset update"
            pass
