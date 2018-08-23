#!/usr/bin/python
#
# File Name: InstErrors.py
# Purpose: Provide instrument error info and recovery action.
#
# Notes:
#
# File History:
# 06-11-06 Al   Created file
# 11-12-06 Al   Added more error definitions.
# 12-12-06 Al   Added INST_ERROR_MEAS_SYS_RPC_FAILED
# 12-12-20 Al   Added Cal manager and data manager errors

from Host.Common.SharedTypes import RPC_PORT_INSTR_MANAGER, RPC_PORT_MEAS_SYSTEM, RPC_PORT_DATA_MANAGER, RPC_PORT_SAMPLE_MGR, RPC_PORT_DRIVER, RPC_PORT_CAL_MANAGER

class ErrorInfo(object):
    "Class to store error information"
    def __init__(self,errorRec,name,description,rpcPortNum):
        self.errorRec = errorRec
        self.name = name
        self.desc = description
        self.rpcPortNum = rpcPortNum

# Error recovery action types
DO_NOTHING    = 0
SHUTDOWN_INST = 1  # shutdown instrument and go into reset state
RESTART_INST  = 2  # restart instrument
RESTART_DAS   = 3  # restart DAS
RESTART_MEAS  = 4  # restart measurement
CLEAR_ERROR   = 5  # Calls appropriate application clearError RPC
SELF_DIAG     = 6  # perform self-diag

errorActionDict = {0: "DO_NOTHING",
                   1: "SHUTDOWN_INST",
                   2: "RESTART_INST",
                   3: "RESTART_DAS",
                   4: "RESTART_MEAS",
                   5: "CLEAR_ERROR",
                   6: "SELF_DIAG"
                    }
error_info = []

INST_ERROR_OKAY = 0
error_info.append(ErrorInfo(DO_NOTHING,"INST_ERROR_OKAY","No Error",RPC_PORT_INSTR_MANAGER))
INST_ERROR_INVALID_SAMPLE_MGR_MODE = -1
error_info.append(ErrorInfo(SHUTDOWN_INST, "INST_ERROR_INVALID_SAMPLE_MGR_MODE", "Invalid Sample Manager mode",RPC_PORT_INSTR_MANAGER))
INST_ERROR_INVALID_MEAS_SYS_MODE   = -2
error_info.append(ErrorInfo(SHUTDOWN_INST, "INST_ERROR_INVALID_MEAS_SYS_MODE","Invalid Measurement System mode",RPC_PORT_INSTR_MANAGER))
INST_ERROR_DAS_ERROR_OCCURRED      = -3
error_info.append(ErrorInfo(RESTART_DAS, "INST_ERROR_DAS_ERROR_OCCURRED","DAS error cccurred",RPC_PORT_INSTR_MANAGER))
INST_ERROR_DAS_RESET_OCCURRED      = -4
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_DAS_RESET_OCCURRED","DAS reset occurred",RPC_PORT_INSTR_MANAGER))
INST_ERROR_BAD_CALIBRATION_FILE    = -5
error_info.append(ErrorInfo(SHUTDOWN_INST, "INST_ERROR_BAD_CALIBRATION_FILE","Calibration file is invalid",RPC_PORT_INSTR_MANAGER))
INST_ERROR_CAVITY_TEMP_CONTROL_ENABLE_FAILED = -6
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_CAVITY_TEMP_CONTROL_ENABLE_FAILED","Cavity Temperature Control Enable failed",RPC_PORT_INSTR_MANAGER))
INST_ERROR_WARM_CHAMBER_TEMP_CONTROL_ENABLE_FAILED = -7
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_WARM_CHAMBER_TEMP_CONTROL_ENABLE_FAILED","Warm Chamber Temperature Control Enable failed",RPC_PORT_INSTR_MANAGER))
INST_ERROR_LASER_TEMP_CONTROL_ENABLE_FAILED = -8
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_LASER_TEMP_CONTROL_ENABLE_FAILED","Laser Temperature Control Enable failed",RPC_PORT_INSTR_MANAGER))
INST_ERROR_HEATER_CONTROL_ENABLE_FAILED = -9
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_HEATER_CONTROL_ENABLE_FAILED","Heater Control Enable failed",RPC_PORT_INSTR_MANAGER))
INST_ERROR_LASER_I_CONTROL_ENABLE_FAILED = -10
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_LASER_I_CONTROL_ENABLE_FAILED","Laser Current Control Enable failed",RPC_PORT_INSTR_MANAGER))
INST_ERROR_INVALID_STATE = -11
error_info.append(ErrorInfo(DO_NOTHING, "INST_ERROR_INVALID_STATE","Invalid INSTMGR state",RPC_PORT_INSTR_MANAGER))
INST_ERROR_INVALID_EVENT = -12
error_info.append(ErrorInfo(DO_NOTHING, "INST_ERROR_INVALID_EVENT","Invalid INSTMGR event",RPC_PORT_INSTR_MANAGER))
INST_ERROR_TEMP_LOCK_TIMEOUT = -13
error_info.append(ErrorInfo(SHUTDOWN_INST, "INST_ERROR_TEMP_LOCK_TIMEOUT","Temperature Lock Timeout occurred",RPC_PORT_INSTR_MANAGER))
INST_ERROR_PRESSURE_LOCK_TIMEOUT = -14
error_info.append(ErrorInfo(SHUTDOWN_INST, "INST_ERROR_PRESSURE_LOCK_TIMEOUT","Pressure Lock Timeout occurred",RPC_PORT_INSTR_MANAGER))
INST_ERROR_DAS_CAL_WRITE_FAILED = -15
error_info.append(ErrorInfo(SHUTDOWN_INST, "INST_ERROR_DAS_CAL_WRITE_FAILED","DAS Cal Write Failed",RPC_PORT_INSTR_MANAGER))
INST_ERROR_SAMPLE_MGR_RPC_FAILED = -16
error_info.append(ErrorInfo(SHUTDOWN_INST, "INST_ERROR_SAMPLE_MGR_FAILED","Sample Manager RPC Failed",RPC_PORT_INSTR_MANAGER))
INST_ERROR_MEAS_SYS = -17
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_MEAS_SYS","Meas System entered Error State",RPC_PORT_MEAS_SYSTEM))
INST_ERROR_DATA_MANAGER = -18
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_DATA_MANAGER","Data Manager entered Error State",RPC_PORT_DATA_MANAGER))
INST_ERROR_MEAS_SYS_RESTART = -19
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_MEAS_SYS_RESTART","Meas Sys Restarted",RPC_PORT_MEAS_SYSTEM))
INST_ERROR_DATA_MANAGER_RESTART = -20
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_DATA_MANAGER_RESTART","Data Manager Restarted",RPC_PORT_DATA_MANAGER))
INST_ERROR_SAMPLE_MANAGER_RESTART = -21
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_SAMPLE_MANAGER_RESTART","Sample Manager Restarted",RPC_PORT_SAMPLE_MGR))
INST_ERROR_DRIVER_RESTART = -22
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_DRIVER_RESTART","Driver Restarted",RPC_PORT_DRIVER))
INST_ERROR_MULTI_APP_RESTART = -23
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_MULTI_APP_RESTART","Multiple Apps Restarted",RPC_PORT_INSTR_MANAGER))
INST_ERROR_MEAS_SYS_RPC_FAILED = -24
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_MEAS_SYS_RPC_FAILED","Meas System Rpc Failed",RPC_PORT_INSTR_MANAGER))
INST_ERROR_CAL_MANAGER_RESTART = -25
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_CAL_MANAGER_RESTART","Cal Manager Restarted",RPC_PORT_CAL_MANAGER))
INST_ERROR_CAL_MANAGER = -26
error_info.append(ErrorInfo(RESTART_INST, "INST_ERROR_CAL_MANAGER","Cal Manager entered Error State",RPC_PORT_CAL_MANAGER))
INST_ERROR_DATA_MANAGER_RPC_FAILED = -27
error_info.append(ErrorInfo(RESTART_INST, "ERROR_DATA_MANAGER_RPC_FAILED","DataMgr RPC Failed",RPC_PORT_INSTR_MANAGER))
INST_ERROR_MAX                     = -27