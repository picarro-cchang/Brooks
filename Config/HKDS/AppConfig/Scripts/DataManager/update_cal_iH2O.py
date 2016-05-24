from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

max_adjust = 2.0e-4

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
    try:
        h2o_adjust = _OLD_DATA_["h2o_adjust"][-1].value/5.0
        h2o_adjust = min(max_adjust,max(-max_adjust,h2o_adjust))
        newOffset0 = _FREQ_CONV_.getWlmOffset(1) + h2o_adjust
        _NEW_DATA_["wlm1_offset"] = newOffset0
        _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
        # print "new H2O offset: %.5f" % newOffset0 
    except:
        # print "No H2O offset update"
        pass
            
