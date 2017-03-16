#
# File Name: InstMgrInc.py
#
# File History:
# 06-12-18 al    Initial creation
# 06-12-18 ytsai Change status to be the same as LV.

# status register bit definitions
INSTMGR_STATUS_READY                    = 0x0001
INSTMGR_STATUS_MEAS_ACTIVE              = 0x0002
INSTMGR_STATUS_ERROR_IN_BUFFER          = 0x0004
INSTMGR_STATUS_GAS_FLOWING              = 0x0040
INSTMGR_STATUS_PRESSURE_LOCKED          = 0x0080
INSTMGR_STATUS_CAVITY_TEMP_LOCKED       = 0x0100
INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED = 0x0200
INSTMGR_STATUS_WARMING_UP               = 0x2000
INSTMGR_STATUS_SYSTEM_ERROR             = 0x4000
INSTMGR_STATUS_CLEAR_MASK               = 0xFFFF

def binaryToDictionary(binVar):
    """
    Take the compact INST_STATUS (that is pervasive in the Host code) and convert it
    to a True/False dict with the mask names as the keys.
    """
    outputDict = {}
    outputDict["INSTMGR_STATUS_READY"] = bool(binVar & INSTMGR_STATUS_READY)
    outputDict["INSTMGR_STATUS_MEAS_ACTIVE"] = bool(binVar & INSTMGR_STATUS_MEAS_ACTIVE)
    outputDict["INSTMGR_STATUS_ERROR_IN_BUFFER"] = bool(binVar & INSTMGR_STATUS_ERROR_IN_BUFFER)
    outputDict["INSTMGR_STATUS_GAS_FLOWING"] = bool(binVar & INSTMGR_STATUS_GAS_FLOWING)
    outputDict["INSTMGR_STATUS_PRESSURE_LOCKED"] = bool(binVar & INSTMGR_STATUS_PRESSURE_LOCKED)
    outputDict["INSTMGR_STATUS_CAVITY_TEMP_LOCKED"] = bool(binVar & INSTMGR_STATUS_CAVITY_TEMP_LOCKED)
    outputDict["INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED"] = bool(binVar & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED)
    outputDict["INSTMGR_STATUS_WARMING_UP"] = bool(binVar & INSTMGR_STATUS_WARMING_UP)
    outputDict["INSTMGR_STATUS_SYSTEM_ERROR"] = bool(binVar & INSTMGR_STATUS_SYSTEM_ERROR)
    return outputDict

def overallStatus(binVar):
    """
    Return true if system is warmed up and the temperature and pressure PIDs have reached equilibrium.
    """
    statusOK = False
    d = binaryToDictionary(binVar)

    if d["INSTMGR_STATUS_PRESSURE_LOCKED"] and \
            d["INSTMGR_STATUS_CAVITY_TEMP_LOCKED"] and \
            d["INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED"] and \
            not d["INSTMGR_STATUS_WARMING_UP"] and \
            not d["INSTRMGR_STATUS_SYSTEM_ERROR"]:
                statusOK = True
    return statusOK

