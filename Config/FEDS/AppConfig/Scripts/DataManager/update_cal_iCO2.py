from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

max_adjust = 2.0e-4

# Check instrument status and do not do any updates if any parameters are unlocked

pass### "Instrument status", _INSTR_STATUS_
pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if not good:
    pass### "Updating WLM offset not done because of bad instrument status"
else:    
    try:
        co2_adjust = _OLD_DATA_["adjust_87"][-1].value/5.0
        co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
        newOffset0 = _FREQ_CONV_.getWlmOffset(1) + co2_adjust
        _NEW_DATA_["wlm1_offset"] = newOffset0
        _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
        # pass### "New C12 (virtual laser 1) offset: %.5f" % newOffset0 
    except:
        # pass### "No new C12 (virtual laser 1) offset"
        pass
    try:
        co2_adjust = _OLD_DATA_["adjust_88"][-1].value/5.0
        co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
        newOffset0 = _FREQ_CONV_.getWlmOffset(2) + co2_adjust
        _NEW_DATA_["wlm2_offset"] = newOffset0
        _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
        # pass### "New C13 (virtual laser 2) offset: %.5f" % newOffset0 
    except:
        # pass### "No new C13 (virtual laser 2) offset"
        pass
    try:
        h2o_adjust = _OLD_DATA_["adjust_91"][-1].value/5.0
        h2o_adjust = min(max_adjust,max(-max_adjust,h2o_adjust))
        newOffset0 = _FREQ_CONV_.getWlmOffset(3) + h2o_adjust
        _NEW_DATA_["wlm3_offset"] = newOffset0
        _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
        # pass### "New H2O (virtual laser 3) offset: %.5f" % newOffset0 
    except:
        # pass### "No new H2O (virtual laser 3) offset"
        pass
            
