#!/usr/bin/python
#
# FILE:
#   interface.py
#
# DESCRIPTION:
#   Automatically generated Python interface file for Picarro gas analyzer.
#    DO NOT EDIT.
#
# SEE ALSO:
#   Specify any related information.
#
#  Copyright (c) 2008 Picarro, Inc. All rights reserved
#

from ctypes import c_byte, c_uint, c_int, c_ushort, c_short
from ctypes import c_longlong, c_float, Structure, Union

class RegInfo(object):
    "Class to store register access information"
    def __init__(self,name,type,persistence,firstVersion,access):
        self.name = name
        self.type = type
        self.persistence = persistence
        self.firstVersion = firstVersion
        self.readable = "r" in access
        self.writable = "w" in access


# Interface Version
interface_version = 1

error_messages = []
STATUS_OK = 0
error_messages.append("Status OK")
ERROR_UNAVAILABLE = -1
error_messages.append("Data not available")
ERROR_CRC_BAD = -2
error_messages.append("CRC error in host command")
ERROR_DSP_UNEXPECTED_SEQUENCE_NUMBER = -3
error_messages.append("DSP detected host command out of sequence")
ERROR_HOST_UNEXPECTED_SEQUENCE_NUMBER = -4
error_messages.append("Host received acknowledgement out of sequence")
ERROR_BAD_COMMAND = -5
error_messages.append("Unrecognized host command")
ERROR_BAD_NUM_PARAMS = -6
error_messages.append("Incorrect number of parameters calling a DSP function")
ERROR_OUTSIDE_SHAREDMEM = -7
error_messages.append("Attempt to access outside shared memory")
ERROR_UNKNOWN_REGISTER = -8
error_messages.append("Invalid register specified")
ERROR_NOT_READABLE = -9
error_messages.append("Register is not readable")
ERROR_NOT_WRITABLE = -10
error_messages.append("Register is not writable")
ERROR_READ_FAILED = -11
error_messages.append("Register read failed")
ERROR_WRITE_FAILED = -12
error_messages.append("Register write failed")
ERROR_BAD_FILTER_COEFF = -13
error_messages.append("Invalid filter coefficients")
ERROR_BAD_VALUE = -14
error_messages.append("Invalid value")

# Constant definitions
# Number of points in controller waveforms
CONTROLLER_WAVEFORM_POINTS = 1000
# Base address for DSP shared memory
SHAREDMEM_ADDRESS = 0x20000
# Base address for ringdown memory
RDMEM_ADDRESS = 0xA0000000
# Offset for software registers in DSP shared memory
REG_OFFSET = 0x0
# Offset for sensor stream area in DSP shared memory
SENSOR_OFFSET = 0x1B00
# Offset for message area in DSP shared memory
MESSAGE_OFFSET = 0x2B00
# Offset for group table in DSP shared memory
GROUP_OFFSET = 0x2F00
# Offset for operation table in DSP shared memory
OPERATION_OFFSET = 0x2F20
# Offset for operand table in DSP shared memory
OPERAND_OFFSET = 0x3300
# Offset for environment table in DSP shared memory
ENVIRONMENT_OFFSET = 0x3700
# Offset for host area in DSP shared memory
HOST_OFFSET = 0x3F00
# Size (in 32-bit ints) of DSP shared memory
SHAREDMEM_SIZE = 0x4000
# Number of software registers
REG_REGION_SIZE = (SENSOR_OFFSET - REG_OFFSET)
# Number of 32-bit ints in sensor area
SENSOR_REGION_SIZE = (MESSAGE_OFFSET - SENSOR_OFFSET)
# Number of sensor steam entries in sensor area
NUM_SENSOR_ENTRIES = SENSOR_REGION_SIZE>>2
# Number of 32-bit ints in message area
MESSAGE_REGION_SIZE = (GROUP_OFFSET - MESSAGE_OFFSET)
# Number of messages in message area
NUM_MESSAGES = MESSAGE_REGION_SIZE>>5
# Number of 32-bit ints in group table
GROUP_TABLE_SIZE = (OPERATION_OFFSET - GROUP_OFFSET)
# Number of 32-bit ints in operation table
OPERATION_TABLE_SIZE = (OPERAND_OFFSET - OPERATION_OFFSET)
# Number of operations in operation table
NUM_OPERATIONS = OPERATION_TABLE_SIZE>>1
# Number of 32-bit ints in operand table
OPERAND_TABLE_SIZE = (ENVIRONMENT_OFFSET - OPERAND_OFFSET)
# Number of 32-bit ints in environment table
ENVIRONMENT_TABLE_SIZE = (HOST_OFFSET - ENVIRONMENT_OFFSET)
# Number of 32-bit ints in host area
HOST_REGION_SIZE = (SHAREDMEM_SIZE - HOST_OFFSET)
# Number of bits in EMIF address
EMIF_ADDR_WIDTH = 20
# Number of bits in EMIF address
EMIF_DATA_WIDTH = 32
# Number of bits in an FPGA register
FPGA_REG_WIDTH = 16
# Mask to access ringdown memory
FPGA_RDMEM_MASK = 0
# Mask to access FPGA registers
FPGA_REG_MASK = 1
# Number of bits in ringdown data
RDMEM_DATA_WIDTH = 18
# Number of bits in ringdown metadata
RDMEM_META_WIDTH = 16
# Number of bits in ringdown parameters
RDMEM_PARAM_WIDTH = 16
# Number of address bits reserved for a ringdown region in each bank
RDMEM_RESERVED_BANK_ADDR_WIDTH = 12
# Number of address bits for one bank of data
DATA_BANK_ADDR_WIDTH = 12
# Number of address bits for one bank of metadata
META_BANK_ADDR_WIDTH = 12
# Number of address bits for one bank of parameters
PARAM_BANK_ADDR_WIDTH = 6
# Number of in-range samples to acquire lock
TEMP_CNTRL_LOCK_COUNT = 5
# Number of out-of-range samples to lose lock
TEMP_CNTRL_UNLOCK_COUNT = 5
# Code to confirm FPGA is programmed
FPGA_MAGIC_CODE = 0xC0DE0001

class DataType(Union):
    _fields_ = [
    ("asFloat",c_float),
    ("asUint",c_uint),
    ("asInt",c_int)
    ]

class DIAG_EventLogStruct(Structure):
    _fields_ = [
    ("time",c_uint),
    ("cause",c_uint),
    ("etalonPd1Current",c_uint),
    ("refPd1Current",c_uint),
    ("etalonPd2Current",c_uint),
    ("refPd2Current",c_uint),
    ("etalonTemp",c_uint),
    ("cavityTemp",c_uint),
    ("warmChamberTemp",c_uint),
    ("hotChamberTecHeatsinkTemp",c_uint),
    ("warmChamberTecHeatsinkTemp",c_uint),
    ("laser1Temp",c_uint),
    ("laser2Temp",c_uint),
    ("laserCurrent",c_uint),
    ("cavityPressure",c_uint),
    ("inletPressure",c_uint),
    ("outletPressure",c_uint),
    ("customDataArray",c_ushort*16)
    ]

class RD_ResultsEntryType(Structure):
    _fields_ = [
    ("lockValue",DataType),
    ("ratio1",c_float),
    ("ratio2",c_float),
    ("correctedAbsorbance",c_float),
    ("uncorrectedAbsorbance",c_float),
    ("tunerValue",c_ushort),
    ("pztValue",c_ushort),
    ("etalonAndLaserSelectAndFitStatus",c_ushort),
    ("schemeStatusAndSchemeTableIndex",c_ushort),
    ("msTicks",c_uint),
    ("count",c_ushort),
    ("subSchemeId",c_ushort),
    ("schemeIndex",c_ushort),
    ("fineLaserCurrent",c_ushort),
    ("lockSetpoint",DataType)
    ]

class SensorEntryType(Structure):
    _fields_ = [
    ("timestamp",c_longlong),
    ("streamNum",c_uint),
    ("value",DataType)
    ]

class PidControllerEnvType(Structure):
    _fields_ = [
    ("swpDir",c_int),
    ("lockCount",c_int),
    ("unlockCount",c_int),
    ("firstIteration",c_int),
    ("a",c_float),
    ("u",c_float),
    ("perr",c_float),
    ("derr1",c_float),
    ("derr2",c_float),
    ("Dincr",c_float)
    ]

class CheckEnvType(Structure):
    _fields_ = [
    ("var1",c_int),
    ("var2",c_int)
    ]

class PulseGenEnvType(Structure):
    _fields_ = [
    ("counter",c_uint)
    ]

class FilterEnvType(Structure):
    _fields_ = [
    ("num",c_float*9),
    ("den",c_float*9),
    ("state",c_float*8)
    ]

# Enumerated definitions for STREAM_MemberType
STREAM_MemberType = c_uint
STREAM_Laser1Temp = 0 # 
STREAM_Laser2Temp = 1 # 
STREAM_Laser3Temp = 2 # 
STREAM_Laser4Temp = 3 # 
STREAM_EtalonTemp = 4 # 
STREAM_WarmChamberTemp = 5 # 
STREAM_WarmChamberTecTemp = 6 # 
STREAM_CavityTemp = 7 # 
STREAM_HotChamberTecTemp = 8 # 
STREAM_DasTemp = 9 # 
STREAM_Etalon1 = 10 # 
STREAM_Reference1 = 11 # 
STREAM_Etalon2 = 12 # 
STREAM_Reference2 = 13 # 
STREAM_Laser1Current = 14 # 
STREAM_Laser2Current = 15 # 
STREAM_Laser3Current = 16 # 
STREAM_Laser4Current = 17 # 
STREAM_CavityPressure = 18 # 
STREAM_AmbientPressure = 19 # 
STREAM_InletPressure = 20 # 
STREAM_OutletPressure = 21 # 
STREAM_Laser1Tec = 22 # 
STREAM_Laser2Tec = 23 # 
STREAM_Laser3Tec = 24 # 
STREAM_Laser4Tec = 25 # 
STREAM_WarmChamberTec = 26 # 
STREAM_HotChamberTec = 27 # 
STREAM_HotChamberHeater = 28 # 
STREAM_InletValve = 29 # 
STREAM_OutletValve = 30 # 
STREAM_ValveMask = 31 # 

# Dictionary for enumerated constants in STREAM_MemberType
STREAM_MemberTypeDict = {}
STREAM_MemberTypeDict[0] = 'STREAM_Laser1Temp' # 
STREAM_MemberTypeDict[1] = 'STREAM_Laser2Temp' # 
STREAM_MemberTypeDict[2] = 'STREAM_Laser3Temp' # 
STREAM_MemberTypeDict[3] = 'STREAM_Laser4Temp' # 
STREAM_MemberTypeDict[4] = 'STREAM_EtalonTemp' # 
STREAM_MemberTypeDict[5] = 'STREAM_WarmChamberTemp' # 
STREAM_MemberTypeDict[6] = 'STREAM_WarmChamberTecTemp' # 
STREAM_MemberTypeDict[7] = 'STREAM_CavityTemp' # 
STREAM_MemberTypeDict[8] = 'STREAM_HotChamberTecTemp' # 
STREAM_MemberTypeDict[9] = 'STREAM_DasTemp' # 
STREAM_MemberTypeDict[10] = 'STREAM_Etalon1' # 
STREAM_MemberTypeDict[11] = 'STREAM_Reference1' # 
STREAM_MemberTypeDict[12] = 'STREAM_Etalon2' # 
STREAM_MemberTypeDict[13] = 'STREAM_Reference2' # 
STREAM_MemberTypeDict[14] = 'STREAM_Laser1Current' # 
STREAM_MemberTypeDict[15] = 'STREAM_Laser2Current' # 
STREAM_MemberTypeDict[16] = 'STREAM_Laser3Current' # 
STREAM_MemberTypeDict[17] = 'STREAM_Laser4Current' # 
STREAM_MemberTypeDict[18] = 'STREAM_CavityPressure' # 
STREAM_MemberTypeDict[19] = 'STREAM_AmbientPressure' # 
STREAM_MemberTypeDict[20] = 'STREAM_InletPressure' # 
STREAM_MemberTypeDict[21] = 'STREAM_OutletPressure' # 
STREAM_MemberTypeDict[22] = 'STREAM_Laser1Tec' # 
STREAM_MemberTypeDict[23] = 'STREAM_Laser2Tec' # 
STREAM_MemberTypeDict[24] = 'STREAM_Laser3Tec' # 
STREAM_MemberTypeDict[25] = 'STREAM_Laser4Tec' # 
STREAM_MemberTypeDict[26] = 'STREAM_WarmChamberTec' # 
STREAM_MemberTypeDict[27] = 'STREAM_HotChamberTec' # 
STREAM_MemberTypeDict[28] = 'STREAM_HotChamberHeater' # 
STREAM_MemberTypeDict[29] = 'STREAM_InletValve' # 
STREAM_MemberTypeDict[30] = 'STREAM_OutletValve' # 
STREAM_MemberTypeDict[31] = 'STREAM_ValveMask' # 

# Enumerated definitions for TEMP_CNTRL_StateType
TEMP_CNTRL_StateType = c_uint
TEMP_CNTRL_DisabledState = 0 # Controller Disabled
TEMP_CNTRL_EnabledState = 1 # Controller Enabled
TEMP_CNTRL_SuspendedState = 2 # Controller Suspended
TEMP_CNTRL_SweepingState = 3 # Continuous Sweeping
TEMP_CNTRL_SendPrbsState = 4 # Sending PRBS
TEMP_CNTRL_ManualState = 5 # Manual Control

# Dictionary for enumerated constants in TEMP_CNTRL_StateType
TEMP_CNTRL_StateTypeDict = {}
TEMP_CNTRL_StateTypeDict[0] = 'TEMP_CNTRL_DisabledState' # Controller Disabled
TEMP_CNTRL_StateTypeDict[1] = 'TEMP_CNTRL_EnabledState' # Controller Enabled
TEMP_CNTRL_StateTypeDict[2] = 'TEMP_CNTRL_SuspendedState' # Controller Suspended
TEMP_CNTRL_StateTypeDict[3] = 'TEMP_CNTRL_SweepingState' # Continuous Sweeping
TEMP_CNTRL_StateTypeDict[4] = 'TEMP_CNTRL_SendPrbsState' # Sending PRBS
TEMP_CNTRL_StateTypeDict[5] = 'TEMP_CNTRL_ManualState' # Manual Control

# Enumerated definitions for LASER_CURRENT_CNTRL_StateType
LASER_CURRENT_CNTRL_StateType = c_uint
LASER_CURRENT_CNTRL_DisabledState = 0 # Controller Disabled
LASER_CURRENT_CNTRL_EnabledState = 1 # Controller Enabled
LASER_CURRENT_CNTRL_SweepingState = 2 # Continuous Sweeping
LASER_CURRENT_CNTRL_ManualState = 3 # Manual Control

# Dictionary for enumerated constants in LASER_CURRENT_CNTRL_StateType
LASER_CURRENT_CNTRL_StateTypeDict = {}
LASER_CURRENT_CNTRL_StateTypeDict[0] = 'LASER_CURRENT_CNTRL_DisabledState' # Controller Disabled
LASER_CURRENT_CNTRL_StateTypeDict[1] = 'LASER_CURRENT_CNTRL_EnabledState' # Controller Enabled
LASER_CURRENT_CNTRL_StateTypeDict[2] = 'LASER_CURRENT_CNTRL_SweepingState' # Continuous Sweeping
LASER_CURRENT_CNTRL_StateTypeDict[3] = 'LASER_CURRENT_CNTRL_ManualState' # Manual Control

# Enumerated definitions for HEATER_CNTRL_StateType
HEATER_CNTRL_StateType = c_uint
HEATER_CNTRL_DisabledState = 0 # Controller Disabled
HEATER_CNTRL_EnabledState = 1 # Controller Enabled
HEATER_CNTRL_ManualState = 2 # Manual Control

# Dictionary for enumerated constants in HEATER_CNTRL_StateType
HEATER_CNTRL_StateTypeDict = {}
HEATER_CNTRL_StateTypeDict[0] = 'HEATER_CNTRL_DisabledState' # Controller Disabled
HEATER_CNTRL_StateTypeDict[1] = 'HEATER_CNTRL_EnabledState' # Controller Enabled
HEATER_CNTRL_StateTypeDict[2] = 'HEATER_CNTRL_ManualState' # Manual Control

# Definitions for COMM_STATUS_BITMASK
COMM_STATUS_CompleteMask = 0x1
COMM_STATUS_BadCrcMask = 0x2
COMM_STATUS_BadSequenceNumberMask = 0x4
COMM_STATUS_BadArgumentsMask = 0x8
COMM_STATUS_SequenceNumberMask = 0xFF000000
COMM_STATUS_ReturnValueMask = 0x00FFFF00
COMM_STATUS_SequenceNumberShift = 24
COMM_STATUS_ReturnValueShift = 8

# Register definitions
INTERFACE_NUMBER_OF_REGISTERS = 192

NOOP_REGISTER = 0
VERIFY_INIT_REGISTER = 1
COMM_STATUS_REGISTER = 2
TIMESTAMP_LSB_REGISTER = 3
TIMESTAMP_MSB_REGISTER = 4
SCHEDULER_CONTROL_REGISTER = 5
LOW_DURATION_REGISTER = 6
HIGH_DURATION_REGISTER = 7
DAS_TEMPERATURE_REGISTER = 8
LASER_TEC_MONITOR_TEMPERATURE_REGISTER = 9
CONVERSION_LASER1_THERM_CONSTA_REGISTER = 10
CONVERSION_LASER1_THERM_CONSTB_REGISTER = 11
CONVERSION_LASER1_THERM_CONSTC_REGISTER = 12
LASER1_RESISTANCE_REGISTER = 13
LASER1_TEMPERATURE_REGISTER = 14
LASER1_THERMISTOR_ADC_REGISTER = 15
LASER1_TEC_REGISTER = 16
LASER1_MANUAL_TEC_REGISTER = 17
LASER1_TEMP_CNTRL_STATE_REGISTER = 18
LASER1_TEMP_CNTRL_LOCK_STATUS_REGISTER = 19
LASER1_TEMP_CNTRL_SETPOINT_REGISTER = 20
LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER = 21
LASER1_TEMP_CNTRL_TOLERANCE_REGISTER = 22
LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER = 23
LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER = 24
LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER = 25
LASER1_TEMP_CNTRL_H_REGISTER = 26
LASER1_TEMP_CNTRL_K_REGISTER = 27
LASER1_TEMP_CNTRL_TI_REGISTER = 28
LASER1_TEMP_CNTRL_TD_REGISTER = 29
LASER1_TEMP_CNTRL_B_REGISTER = 30
LASER1_TEMP_CNTRL_C_REGISTER = 31
LASER1_TEMP_CNTRL_N_REGISTER = 32
LASER1_TEMP_CNTRL_S_REGISTER = 33
LASER1_TEMP_CNTRL_FFWD_REGISTER = 34
LASER1_TEMP_CNTRL_AMIN_REGISTER = 35
LASER1_TEMP_CNTRL_AMAX_REGISTER = 36
LASER1_TEMP_CNTRL_IMAX_REGISTER = 37
LASER1_TEC_PRBS_GENPOLY_REGISTER = 38
LASER1_TEC_PRBS_AMPLITUDE_REGISTER = 39
LASER1_TEC_PRBS_MEAN_REGISTER = 40
LASER1_TEC_MONITOR_REGISTER = 41
LASER1_CURRENT_CNTRL_STATE_REGISTER = 42
LASER1_MANUAL_COARSE_CURRENT_REGISTER = 43
LASER1_MANUAL_FINE_CURRENT_REGISTER = 44
LASER1_CURRENT_SWEEP_MIN_REGISTER = 45
LASER1_CURRENT_SWEEP_MAX_REGISTER = 46
LASER1_CURRENT_SWEEP_INCR_REGISTER = 47
LASER1_CURRENT_MONITOR_REGISTER = 48
CONVERSION_LASER2_THERM_CONSTA_REGISTER = 49
CONVERSION_LASER2_THERM_CONSTB_REGISTER = 50
CONVERSION_LASER2_THERM_CONSTC_REGISTER = 51
LASER2_RESISTANCE_REGISTER = 52
LASER2_TEMPERATURE_REGISTER = 53
LASER2_THERMISTOR_ADC_REGISTER = 54
LASER2_TEC_REGISTER = 55
LASER2_MANUAL_TEC_REGISTER = 56
LASER2_TEMP_CNTRL_STATE_REGISTER = 57
LASER2_TEMP_CNTRL_LOCK_STATUS_REGISTER = 58
LASER2_TEMP_CNTRL_SETPOINT_REGISTER = 59
LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER = 60
LASER2_TEMP_CNTRL_TOLERANCE_REGISTER = 61
LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER = 62
LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER = 63
LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER = 64
LASER2_TEMP_CNTRL_H_REGISTER = 65
LASER2_TEMP_CNTRL_K_REGISTER = 66
LASER2_TEMP_CNTRL_TI_REGISTER = 67
LASER2_TEMP_CNTRL_TD_REGISTER = 68
LASER2_TEMP_CNTRL_B_REGISTER = 69
LASER2_TEMP_CNTRL_C_REGISTER = 70
LASER2_TEMP_CNTRL_N_REGISTER = 71
LASER2_TEMP_CNTRL_S_REGISTER = 72
LASER2_TEMP_CNTRL_FFWD_REGISTER = 73
LASER2_TEMP_CNTRL_AMIN_REGISTER = 74
LASER2_TEMP_CNTRL_AMAX_REGISTER = 75
LASER2_TEMP_CNTRL_IMAX_REGISTER = 76
LASER2_TEC_PRBS_GENPOLY_REGISTER = 77
LASER2_TEC_PRBS_AMPLITUDE_REGISTER = 78
LASER2_TEC_PRBS_MEAN_REGISTER = 79
LASER2_TEC_MONITOR_REGISTER = 80
CONVERSION_LASER3_THERM_CONSTA_REGISTER = 81
CONVERSION_LASER3_THERM_CONSTB_REGISTER = 82
CONVERSION_LASER3_THERM_CONSTC_REGISTER = 83
LASER3_RESISTANCE_REGISTER = 84
LASER3_TEMPERATURE_REGISTER = 85
LASER3_THERMISTOR_ADC_REGISTER = 86
LASER3_TEC_REGISTER = 87
LASER3_MANUAL_TEC_REGISTER = 88
LASER3_TEMP_CNTRL_STATE_REGISTER = 89
LASER3_TEMP_CNTRL_LOCK_STATUS_REGISTER = 90
LASER3_TEMP_CNTRL_SETPOINT_REGISTER = 91
LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER = 92
LASER3_TEMP_CNTRL_TOLERANCE_REGISTER = 93
LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER = 94
LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER = 95
LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER = 96
LASER3_TEMP_CNTRL_H_REGISTER = 97
LASER3_TEMP_CNTRL_K_REGISTER = 98
LASER3_TEMP_CNTRL_TI_REGISTER = 99
LASER3_TEMP_CNTRL_TD_REGISTER = 100
LASER3_TEMP_CNTRL_B_REGISTER = 101
LASER3_TEMP_CNTRL_C_REGISTER = 102
LASER3_TEMP_CNTRL_N_REGISTER = 103
LASER3_TEMP_CNTRL_S_REGISTER = 104
LASER3_TEMP_CNTRL_FFWD_REGISTER = 105
LASER3_TEMP_CNTRL_AMIN_REGISTER = 106
LASER3_TEMP_CNTRL_AMAX_REGISTER = 107
LASER3_TEMP_CNTRL_IMAX_REGISTER = 108
LASER3_TEC_PRBS_GENPOLY_REGISTER = 109
LASER3_TEC_PRBS_AMPLITUDE_REGISTER = 110
LASER3_TEC_PRBS_MEAN_REGISTER = 111
LASER3_TEC_MONITOR_REGISTER = 112
CONVERSION_LASER4_THERM_CONSTA_REGISTER = 113
CONVERSION_LASER4_THERM_CONSTB_REGISTER = 114
CONVERSION_LASER4_THERM_CONSTC_REGISTER = 115
LASER4_RESISTANCE_REGISTER = 116
LASER4_TEMPERATURE_REGISTER = 117
LASER4_THERMISTOR_ADC_REGISTER = 118
LASER4_TEC_REGISTER = 119
LASER4_MANUAL_TEC_REGISTER = 120
LASER4_TEMP_CNTRL_STATE_REGISTER = 121
LASER4_TEMP_CNTRL_LOCK_STATUS_REGISTER = 122
LASER4_TEMP_CNTRL_SETPOINT_REGISTER = 123
LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER = 124
LASER4_TEMP_CNTRL_TOLERANCE_REGISTER = 125
LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER = 126
LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER = 127
LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER = 128
LASER4_TEMP_CNTRL_H_REGISTER = 129
LASER4_TEMP_CNTRL_K_REGISTER = 130
LASER4_TEMP_CNTRL_TI_REGISTER = 131
LASER4_TEMP_CNTRL_TD_REGISTER = 132
LASER4_TEMP_CNTRL_B_REGISTER = 133
LASER4_TEMP_CNTRL_C_REGISTER = 134
LASER4_TEMP_CNTRL_N_REGISTER = 135
LASER4_TEMP_CNTRL_S_REGISTER = 136
LASER4_TEMP_CNTRL_FFWD_REGISTER = 137
LASER4_TEMP_CNTRL_AMIN_REGISTER = 138
LASER4_TEMP_CNTRL_AMAX_REGISTER = 139
LASER4_TEMP_CNTRL_IMAX_REGISTER = 140
LASER4_TEC_PRBS_GENPOLY_REGISTER = 141
LASER4_TEC_PRBS_AMPLITUDE_REGISTER = 142
LASER4_TEC_PRBS_MEAN_REGISTER = 143
LASER4_TEC_MONITOR_REGISTER = 144
CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER = 145
CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER = 146
CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER = 147
HOT_BOX_HEATSINK_RESISTANCE_REGISTER = 148
HOT_BOX_HEATSINK_TEMPERATURE_REGISTER = 149
HOT_BOX_HEATSINK_ADC_REGISTER = 150
CONVERSION_CAVITY_THERM_CONSTA_REGISTER = 151
CONVERSION_CAVITY_THERM_CONSTB_REGISTER = 152
CONVERSION_CAVITY_THERM_CONSTC_REGISTER = 153
CAVITY_RESISTANCE_REGISTER = 154
CAVITY_TEMPERATURE_REGISTER = 155
CAVITY_THERMISTOR_ADC_REGISTER = 156
CAVITY_TEC_REGISTER = 157
CAVITY_MANUAL_TEC_REGISTER = 158
CAVITY_TEMP_CNTRL_STATE_REGISTER = 159
CAVITY_TEMP_CNTRL_LOCK_STATUS_REGISTER = 160
CAVITY_TEMP_CNTRL_SETPOINT_REGISTER = 161
CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER = 162
CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER = 163
CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER = 164
CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER = 165
CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER = 166
CAVITY_TEMP_CNTRL_H_REGISTER = 167
CAVITY_TEMP_CNTRL_K_REGISTER = 168
CAVITY_TEMP_CNTRL_TI_REGISTER = 169
CAVITY_TEMP_CNTRL_TD_REGISTER = 170
CAVITY_TEMP_CNTRL_B_REGISTER = 171
CAVITY_TEMP_CNTRL_C_REGISTER = 172
CAVITY_TEMP_CNTRL_N_REGISTER = 173
CAVITY_TEMP_CNTRL_S_REGISTER = 174
CAVITY_TEMP_CNTRL_FFWD_REGISTER = 175
CAVITY_TEMP_CNTRL_AMIN_REGISTER = 176
CAVITY_TEMP_CNTRL_AMAX_REGISTER = 177
CAVITY_TEMP_CNTRL_IMAX_REGISTER = 178
CAVITY_TEC_PRBS_GENPOLY_REGISTER = 179
CAVITY_TEC_PRBS_AMPLITUDE_REGISTER = 180
CAVITY_TEC_PRBS_MEAN_REGISTER = 181
CAVITY_MAX_HEATSINK_TEMP_REGISTER = 182
HEATER_CNTRL_STATE_REGISTER = 183
HEATER_CNTRL_GAIN_REGISTER = 184
HEATER_CNTRL_QUANTIZE_REGISTER = 185
HEATER_CNTRL_UBIAS_SLOPE_REGISTER = 186
HEATER_CNTRL_UBIAS_OFFSET_REGISTER = 187
HEATER_CNTRL_MARK_MIN_REGISTER = 188
HEATER_CNTRL_MARK_MAX_REGISTER = 189
HEATER_CNTRL_MANUAL_MARK_REGISTER = 190
HEATER_CNTRL_MARK_REGISTER = 191

# Dictionary for accessing registers by name and list of register information
registerByName = {}
registerInfo = []
registerByName["NOOP_REGISTER"] = NOOP_REGISTER
registerInfo.append(RegInfo("NOOP_REGISTER",c_uint,0,1.0,"rw"))
registerByName["VERIFY_INIT_REGISTER"] = VERIFY_INIT_REGISTER
registerInfo.append(RegInfo("VERIFY_INIT_REGISTER",c_uint,0,1.0,"r"))
registerByName["COMM_STATUS_REGISTER"] = COMM_STATUS_REGISTER
registerInfo.append(RegInfo("COMM_STATUS_REGISTER",c_uint,0,1.0,"r"))
registerByName["TIMESTAMP_LSB_REGISTER"] = TIMESTAMP_LSB_REGISTER
registerInfo.append(RegInfo("TIMESTAMP_LSB_REGISTER",c_uint,0,1.0,"r"))
registerByName["TIMESTAMP_MSB_REGISTER"] = TIMESTAMP_MSB_REGISTER
registerInfo.append(RegInfo("TIMESTAMP_MSB_REGISTER",c_uint,0,1.0,"r"))
registerByName["SCHEDULER_CONTROL_REGISTER"] = SCHEDULER_CONTROL_REGISTER
registerInfo.append(RegInfo("SCHEDULER_CONTROL_REGISTER",c_uint,0,1.0,"r"))
registerByName["LOW_DURATION_REGISTER"] = LOW_DURATION_REGISTER
registerInfo.append(RegInfo("LOW_DURATION_REGISTER",c_uint,0,1.0,"rw"))
registerByName["HIGH_DURATION_REGISTER"] = HIGH_DURATION_REGISTER
registerInfo.append(RegInfo("HIGH_DURATION_REGISTER",c_uint,0,1.0,"rw"))
registerByName["DAS_TEMPERATURE_REGISTER"] = DAS_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("DAS_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER_TEC_MONITOR_TEMPERATURE_REGISTER"] = LASER_TEC_MONITOR_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("LASER_TEC_MONITOR_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["CONVERSION_LASER1_THERM_CONSTA_REGISTER"] = CONVERSION_LASER1_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER1_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER1_THERM_CONSTB_REGISTER"] = CONVERSION_LASER1_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER1_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER1_THERM_CONSTC_REGISTER"] = CONVERSION_LASER1_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER1_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_RESISTANCE_REGISTER"] = LASER1_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER1_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER1_TEMPERATURE_REGISTER"] = LASER1_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("LASER1_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER1_THERMISTOR_ADC_REGISTER"] = LASER1_THERMISTOR_ADC_REGISTER
registerInfo.append(RegInfo("LASER1_THERMISTOR_ADC_REGISTER",c_uint,0,1.0,"r"))
registerByName["LASER1_TEC_REGISTER"] = LASER1_TEC_REGISTER
registerInfo.append(RegInfo("LASER1_TEC_REGISTER",c_float,0,1.0,"rw"))
registerByName["LASER1_MANUAL_TEC_REGISTER"] = LASER1_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("LASER1_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_STATE_REGISTER"] = LASER1_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_LOCK_STATUS_REGISTER"] = LASER1_TEMP_CNTRL_LOCK_STATUS_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_LOCK_STATUS_REGISTER",c_uint,0,1.0,"r"))
registerByName["LASER1_TEMP_CNTRL_SETPOINT_REGISTER"] = LASER1_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_TOLERANCE_REGISTER"] = LASER1_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_H_REGISTER"] = LASER1_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_K_REGISTER"] = LASER1_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_TI_REGISTER"] = LASER1_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_TD_REGISTER"] = LASER1_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_B_REGISTER"] = LASER1_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_C_REGISTER"] = LASER1_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_N_REGISTER"] = LASER1_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_S_REGISTER"] = LASER1_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_FFWD_REGISTER"] = LASER1_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_AMIN_REGISTER"] = LASER1_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_AMAX_REGISTER"] = LASER1_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEMP_CNTRL_IMAX_REGISTER"] = LASER1_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEC_PRBS_GENPOLY_REGISTER"] = LASER1_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("LASER1_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerByName["LASER1_TEC_PRBS_AMPLITUDE_REGISTER"] = LASER1_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("LASER1_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEC_PRBS_MEAN_REGISTER"] = LASER1_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("LASER1_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_TEC_MONITOR_REGISTER"] = LASER1_TEC_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER1_TEC_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerByName["LASER1_CURRENT_CNTRL_STATE_REGISTER"] = LASER1_CURRENT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER1_CURRENT_CNTRL_STATE_REGISTER",LASER_CURRENT_CNTRL_StateType,0,1.0,"rw"))
registerByName["LASER1_MANUAL_COARSE_CURRENT_REGISTER"] = LASER1_MANUAL_COARSE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER1_MANUAL_COARSE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_MANUAL_FINE_CURRENT_REGISTER"] = LASER1_MANUAL_FINE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER1_MANUAL_FINE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_CURRENT_SWEEP_MIN_REGISTER"] = LASER1_CURRENT_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER1_CURRENT_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_CURRENT_SWEEP_MAX_REGISTER"] = LASER1_CURRENT_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER1_CURRENT_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_CURRENT_SWEEP_INCR_REGISTER"] = LASER1_CURRENT_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER1_CURRENT_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER1_CURRENT_MONITOR_REGISTER"] = LASER1_CURRENT_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER1_CURRENT_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerByName["CONVERSION_LASER2_THERM_CONSTA_REGISTER"] = CONVERSION_LASER2_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER2_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER2_THERM_CONSTB_REGISTER"] = CONVERSION_LASER2_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER2_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER2_THERM_CONSTC_REGISTER"] = CONVERSION_LASER2_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER2_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_RESISTANCE_REGISTER"] = LASER2_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER2_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER2_TEMPERATURE_REGISTER"] = LASER2_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("LASER2_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER2_THERMISTOR_ADC_REGISTER"] = LASER2_THERMISTOR_ADC_REGISTER
registerInfo.append(RegInfo("LASER2_THERMISTOR_ADC_REGISTER",c_uint,0,1.0,"r"))
registerByName["LASER2_TEC_REGISTER"] = LASER2_TEC_REGISTER
registerInfo.append(RegInfo("LASER2_TEC_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER2_MANUAL_TEC_REGISTER"] = LASER2_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("LASER2_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_STATE_REGISTER"] = LASER2_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_LOCK_STATUS_REGISTER"] = LASER2_TEMP_CNTRL_LOCK_STATUS_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_LOCK_STATUS_REGISTER",c_uint,0,1.0,"r"))
registerByName["LASER2_TEMP_CNTRL_SETPOINT_REGISTER"] = LASER2_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_TOLERANCE_REGISTER"] = LASER2_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_H_REGISTER"] = LASER2_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_K_REGISTER"] = LASER2_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_TI_REGISTER"] = LASER2_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_TD_REGISTER"] = LASER2_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_B_REGISTER"] = LASER2_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_C_REGISTER"] = LASER2_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_N_REGISTER"] = LASER2_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_S_REGISTER"] = LASER2_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_FFWD_REGISTER"] = LASER2_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_AMIN_REGISTER"] = LASER2_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_AMAX_REGISTER"] = LASER2_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEMP_CNTRL_IMAX_REGISTER"] = LASER2_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEC_PRBS_GENPOLY_REGISTER"] = LASER2_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("LASER2_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerByName["LASER2_TEC_PRBS_AMPLITUDE_REGISTER"] = LASER2_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("LASER2_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEC_PRBS_MEAN_REGISTER"] = LASER2_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("LASER2_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_TEC_MONITOR_REGISTER"] = LASER2_TEC_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER2_TEC_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerByName["CONVERSION_LASER3_THERM_CONSTA_REGISTER"] = CONVERSION_LASER3_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER3_THERM_CONSTB_REGISTER"] = CONVERSION_LASER3_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER3_THERM_CONSTC_REGISTER"] = CONVERSION_LASER3_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_RESISTANCE_REGISTER"] = LASER3_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER3_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER3_TEMPERATURE_REGISTER"] = LASER3_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("LASER3_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER3_THERMISTOR_ADC_REGISTER"] = LASER3_THERMISTOR_ADC_REGISTER
registerInfo.append(RegInfo("LASER3_THERMISTOR_ADC_REGISTER",c_uint,0,1.0,"r"))
registerByName["LASER3_TEC_REGISTER"] = LASER3_TEC_REGISTER
registerInfo.append(RegInfo("LASER3_TEC_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER3_MANUAL_TEC_REGISTER"] = LASER3_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("LASER3_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_STATE_REGISTER"] = LASER3_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_LOCK_STATUS_REGISTER"] = LASER3_TEMP_CNTRL_LOCK_STATUS_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_LOCK_STATUS_REGISTER",c_uint,0,1.0,"r"))
registerByName["LASER3_TEMP_CNTRL_SETPOINT_REGISTER"] = LASER3_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_TOLERANCE_REGISTER"] = LASER3_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_H_REGISTER"] = LASER3_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_K_REGISTER"] = LASER3_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_TI_REGISTER"] = LASER3_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_TD_REGISTER"] = LASER3_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_B_REGISTER"] = LASER3_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_C_REGISTER"] = LASER3_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_N_REGISTER"] = LASER3_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_S_REGISTER"] = LASER3_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_FFWD_REGISTER"] = LASER3_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_AMIN_REGISTER"] = LASER3_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_AMAX_REGISTER"] = LASER3_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEMP_CNTRL_IMAX_REGISTER"] = LASER3_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEC_PRBS_GENPOLY_REGISTER"] = LASER3_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("LASER3_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerByName["LASER3_TEC_PRBS_AMPLITUDE_REGISTER"] = LASER3_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("LASER3_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEC_PRBS_MEAN_REGISTER"] = LASER3_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("LASER3_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_TEC_MONITOR_REGISTER"] = LASER3_TEC_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER3_TEC_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerByName["CONVERSION_LASER4_THERM_CONSTA_REGISTER"] = CONVERSION_LASER4_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER4_THERM_CONSTB_REGISTER"] = CONVERSION_LASER4_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER4_THERM_CONSTC_REGISTER"] = CONVERSION_LASER4_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_RESISTANCE_REGISTER"] = LASER4_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER4_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER4_TEMPERATURE_REGISTER"] = LASER4_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("LASER4_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER4_THERMISTOR_ADC_REGISTER"] = LASER4_THERMISTOR_ADC_REGISTER
registerInfo.append(RegInfo("LASER4_THERMISTOR_ADC_REGISTER",c_uint,0,1.0,"r"))
registerByName["LASER4_TEC_REGISTER"] = LASER4_TEC_REGISTER
registerInfo.append(RegInfo("LASER4_TEC_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER4_MANUAL_TEC_REGISTER"] = LASER4_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("LASER4_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_STATE_REGISTER"] = LASER4_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_LOCK_STATUS_REGISTER"] = LASER4_TEMP_CNTRL_LOCK_STATUS_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_LOCK_STATUS_REGISTER",c_uint,0,1.0,"r"))
registerByName["LASER4_TEMP_CNTRL_SETPOINT_REGISTER"] = LASER4_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_TOLERANCE_REGISTER"] = LASER4_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_H_REGISTER"] = LASER4_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_K_REGISTER"] = LASER4_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_TI_REGISTER"] = LASER4_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_TD_REGISTER"] = LASER4_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_B_REGISTER"] = LASER4_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_C_REGISTER"] = LASER4_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_N_REGISTER"] = LASER4_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_S_REGISTER"] = LASER4_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_FFWD_REGISTER"] = LASER4_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_AMIN_REGISTER"] = LASER4_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_AMAX_REGISTER"] = LASER4_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEMP_CNTRL_IMAX_REGISTER"] = LASER4_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEC_PRBS_GENPOLY_REGISTER"] = LASER4_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("LASER4_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerByName["LASER4_TEC_PRBS_AMPLITUDE_REGISTER"] = LASER4_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("LASER4_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEC_PRBS_MEAN_REGISTER"] = LASER4_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("LASER4_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_TEC_MONITOR_REGISTER"] = LASER4_TEC_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER4_TEC_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerByName["CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER"] = CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER"] = CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER"] = CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["HOT_BOX_HEATSINK_RESISTANCE_REGISTER"] = HOT_BOX_HEATSINK_RESISTANCE_REGISTER
registerInfo.append(RegInfo("HOT_BOX_HEATSINK_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["HOT_BOX_HEATSINK_TEMPERATURE_REGISTER"] = HOT_BOX_HEATSINK_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("HOT_BOX_HEATSINK_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["HOT_BOX_HEATSINK_ADC_REGISTER"] = HOT_BOX_HEATSINK_ADC_REGISTER
registerInfo.append(RegInfo("HOT_BOX_HEATSINK_ADC_REGISTER",c_uint,0,1.0,"r"))
registerByName["CONVERSION_CAVITY_THERM_CONSTA_REGISTER"] = CONVERSION_CAVITY_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_CAVITY_THERM_CONSTB_REGISTER"] = CONVERSION_CAVITY_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_CAVITY_THERM_CONSTC_REGISTER"] = CONVERSION_CAVITY_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_RESISTANCE_REGISTER"] = CAVITY_RESISTANCE_REGISTER
registerInfo.append(RegInfo("CAVITY_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_TEMPERATURE_REGISTER"] = CAVITY_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_THERMISTOR_ADC_REGISTER"] = CAVITY_THERMISTOR_ADC_REGISTER
registerInfo.append(RegInfo("CAVITY_THERMISTOR_ADC_REGISTER",c_uint,0,1.0,"r"))
registerByName["CAVITY_TEC_REGISTER"] = CAVITY_TEC_REGISTER
registerInfo.append(RegInfo("CAVITY_TEC_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_MANUAL_TEC_REGISTER"] = CAVITY_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("CAVITY_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_STATE_REGISTER"] = CAVITY_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_LOCK_STATUS_REGISTER"] = CAVITY_TEMP_CNTRL_LOCK_STATUS_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_LOCK_STATUS_REGISTER",c_uint,0,1.0,"r"))
registerByName["CAVITY_TEMP_CNTRL_SETPOINT_REGISTER"] = CAVITY_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER"] = CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_H_REGISTER"] = CAVITY_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_K_REGISTER"] = CAVITY_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_TI_REGISTER"] = CAVITY_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_TD_REGISTER"] = CAVITY_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_B_REGISTER"] = CAVITY_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_C_REGISTER"] = CAVITY_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_N_REGISTER"] = CAVITY_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_S_REGISTER"] = CAVITY_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_FFWD_REGISTER"] = CAVITY_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_AMIN_REGISTER"] = CAVITY_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_AMAX_REGISTER"] = CAVITY_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEMP_CNTRL_IMAX_REGISTER"] = CAVITY_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEC_PRBS_GENPOLY_REGISTER"] = CAVITY_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("CAVITY_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerByName["CAVITY_TEC_PRBS_AMPLITUDE_REGISTER"] = CAVITY_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("CAVITY_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_TEC_PRBS_MEAN_REGISTER"] = CAVITY_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("CAVITY_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_MAX_HEATSINK_TEMP_REGISTER"] = CAVITY_MAX_HEATSINK_TEMP_REGISTER
registerInfo.append(RegInfo("CAVITY_MAX_HEATSINK_TEMP_REGISTER",c_float,1,1.0,"rw"))
registerByName["HEATER_CNTRL_STATE_REGISTER"] = HEATER_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("HEATER_CNTRL_STATE_REGISTER",HEATER_CNTRL_StateType,0,1.0,"rw"))
registerByName["HEATER_CNTRL_GAIN_REGISTER"] = HEATER_CNTRL_GAIN_REGISTER
registerInfo.append(RegInfo("HEATER_CNTRL_GAIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["HEATER_CNTRL_QUANTIZE_REGISTER"] = HEATER_CNTRL_QUANTIZE_REGISTER
registerInfo.append(RegInfo("HEATER_CNTRL_QUANTIZE_REGISTER",c_float,1,1.0,"rw"))
registerByName["HEATER_CNTRL_UBIAS_SLOPE_REGISTER"] = HEATER_CNTRL_UBIAS_SLOPE_REGISTER
registerInfo.append(RegInfo("HEATER_CNTRL_UBIAS_SLOPE_REGISTER",c_float,1,1.0,"rw"))
registerByName["HEATER_CNTRL_UBIAS_OFFSET_REGISTER"] = HEATER_CNTRL_UBIAS_OFFSET_REGISTER
registerInfo.append(RegInfo("HEATER_CNTRL_UBIAS_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerByName["HEATER_CNTRL_MARK_MIN_REGISTER"] = HEATER_CNTRL_MARK_MIN_REGISTER
registerInfo.append(RegInfo("HEATER_CNTRL_MARK_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["HEATER_CNTRL_MARK_MAX_REGISTER"] = HEATER_CNTRL_MARK_MAX_REGISTER
registerInfo.append(RegInfo("HEATER_CNTRL_MARK_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["HEATER_CNTRL_MANUAL_MARK_REGISTER"] = HEATER_CNTRL_MANUAL_MARK_REGISTER
registerInfo.append(RegInfo("HEATER_CNTRL_MANUAL_MARK_REGISTER",c_float,1,1.0,"rw"))
registerByName["HEATER_CNTRL_MARK_REGISTER"] = HEATER_CNTRL_MARK_REGISTER
registerInfo.append(RegInfo("HEATER_CNTRL_MARK_REGISTER",c_float,0,1.0,"rw"))

# FPGA block definitions

# Block KERNEL Kernel
KERNEL_MAGIC_CODE = 0 # Code indicating FPGA is programmed
KERNEL_RESET = 1 # Used to reset Cypress FX2

# Block PWM Pulse width modulator
PWM_CS = 0 # Control/Status register
PWM_CS_RUN_B = 0 # STOP/RUN bit position
PWM_CS_RUN_W = 1 # STOP/RUN bit width
PWM_CS_CONT_B = 1 # SINGLE/CONTINUOUS bit position
PWM_CS_CONT_W = 1 # SINGLE/CONTINUOUS bit width
PWM_CS_PWM_OUT_B = 2 # PWM_OUT bit position
PWM_CS_PWM_OUT_W = 1 # PWM_OUT bit width

PWM_PULSE_WIDTH = 1 # Pulse width register

# Block RDSIM Ringdown simulator
RDSIM_CS = 0 # Control/Status register
RDSIM_CS_RUN_B = 0 # STOP/RUN bit position
RDSIM_CS_RUN_W = 1 # STOP/RUN bit width
RDSIM_CS_CONT_B = 1 # SINGLE/CONTINUOUS bit position
RDSIM_CS_CONT_W = 1 # SINGLE/CONTINUOUS bit width
RDSIM_CS_INIT_B = 2 # NORMAL/INIT bit position
RDSIM_CS_INIT_W = 1 # NORMAL/INIT bit width
RDSIM_CS_ADC_CLK_B = 3 # SINGLE mode ADC clock bit position
RDSIM_CS_ADC_CLK_W = 1 # SINGLE mode ADC clock bit width

RDSIM_VALUE = 1 # Ringdown value register
RDSIM_DECAY = 2 # Decay rate register
RDSIM_AMPLITUDE = 3 # Ringdown amplitude register

# Block LASERLOCK Laser frequency locker
LASERLOCK_CS = 0 # Control/Status register
LASERLOCK_CS_RUN_B = 0 # STOP/RUN bit position
LASERLOCK_CS_RUN_W = 1 # STOP/RUN bit width
LASERLOCK_CS_CONT_B = 1 # SINGLE/CONTINUOUS bit position
LASERLOCK_CS_CONT_W = 1 # SINGLE/CONTINUOUS bit width
LASERLOCK_CS_PRBS_B = 2 # Enables generation of PRBS for loop characterization bit position
LASERLOCK_CS_PRBS_W = 1 # Enables generation of PRBS for loop characterization bit width
LASERLOCK_CS_ACC_EN_B = 3 # Resets or enables fine current accumulator bit position
LASERLOCK_CS_ACC_EN_W = 1 # Resets or enables fine current accumulator bit width
LASERLOCK_CS_SAMPLE_DARK_B = 4 # Strobe high to sample dark current bit position
LASERLOCK_CS_SAMPLE_DARK_W = 1 # Strobe high to sample dark current bit width
LASERLOCK_CS_ADC_STROBE_B = 5 # Strobe high to start new computation cycle bit position
LASERLOCK_CS_ADC_STROBE_W = 1 # Strobe high to start new computation cycle bit width
LASERLOCK_CS_TUNING_OFFSET_SEL_B = 6 # 0 selects register, 1 selects input for tuning offset input bit position
LASERLOCK_CS_TUNING_OFFSET_SEL_W = 1 # 0 selects register, 1 selects input for tuning offset input bit width
LASERLOCK_CS_LOCKED_B = 14 # Flag indicating loop is locked bit position
LASERLOCK_CS_LOCKED_W = 1 # Flag indicating loop is locked bit width
LASERLOCK_CS_DONE_B = 15 # Flag indicating cycle is complete bit position
LASERLOCK_CS_DONE_W = 1 # Flag indicating cycle is complete bit width

LASERLOCK_ETA1 = 1 # Etalon 1 reading
LASERLOCK_REF1 = 2 # Reference 1 reading
LASERLOCK_ETA2 = 3 # Etalon 2 reading
LASERLOCK_REF2 = 4 # Reference 2 reading
LASERLOCK_ETA1_DARK = 5 # Etalon 1 dark reading (ro)
LASERLOCK_REF1_DARK = 6 # Reference 1 dark reading (ro)
LASERLOCK_ETA2_DARK = 7 # Etalon 2 dark reading (ro)
LASERLOCK_REF2_DARK = 8 # Reference 2 dark reading (ro)
LASERLOCK_ETA1_OFFSET = 9 # Etalon 1 offset to be subtracted before finding ratio
LASERLOCK_REF1_OFFSET = 10 # Reference 1 offset to be subtracted before finding ratio
LASERLOCK_ETA2_OFFSET = 11 # Etalon 2 offset to be subtracted before finding ratio
LASERLOCK_REF2_OFFSET = 12 # Reference 2 offset to be subtracted before finding ratio
LASERLOCK_RATIO1 = 13 # Ratio 1 (ro)
LASERLOCK_RATIO2 = 14 # Ratio 2 (ro)
LASERLOCK_RATIO1_CENTER = 15 # Center of ellipse for ratio 1
LASERLOCK_RATIO1_MULTIPLIER = 16 # Factor for ratio 1 in error linear combination
LASERLOCK_RATIO2_CENTER = 17 # Center of ellipse for ratio 2
LASERLOCK_RATIO2_MULTIPLIER = 18 # Factor for ratio 2 in error linear combination
LASERLOCK_TUNING_OFFSET = 19 # Offset to add to error to shift frequency
LASERLOCK_LOCK_ERROR = 20 # Frequency loop lock error (ro)
LASERLOCK_WM_LOCK_WINDOW = 21 # Defines when laser frequency is in lock
LASERLOCK_WM_INT_GAIN = 22 # Integral gain for wavelength locking
LASERLOCK_WM_PROP_GAIN = 23 # Proportional gain for wavelength locking
LASERLOCK_WM_DERIV_GAIN = 24 # Derivative gain for wavelength locking
LASERLOCK_FINE_CURRENT = 25 # Fine laser current (ro)
LASERLOCK_CYCLE_COUNTER = 26 # Cycle counter (ro)

# Block RDMETAMAN Ringdown metadata manager
RDMETAMAN_CS = 0 # Control/Status register
RDMETAMAN_CS_RUN_B = 0 # STOP/RUN bit position
RDMETAMAN_CS_RUN_W = 1 # STOP/RUN bit width
RDMETAMAN_CS_CONT_B = 1 # SINGLE/CONTINUOUS bit position
RDMETAMAN_CS_CONT_W = 1 # SINGLE/CONTINUOUS bit width
RDMETAMAN_CS_START_B = 2 # Start address counter bit position
RDMETAMAN_CS_START_W = 1 # Start address counter bit width
RDMETAMAN_CS_BANK_B = 3 # Bank select bit position
RDMETAMAN_CS_BANK_W = 1 # Bank select bit width
RDMETAMAN_CS_RD_B = 4 # Ringdown bit position
RDMETAMAN_CS_RD_W = 1 # Ringdown bit width
RDMETAMAN_CS_LASER_LOCKER_DONE_B = 5 # Laser locker done (metadata strobe) bit position
RDMETAMAN_CS_LASER_LOCKER_DONE_W = 1 # Laser locker done (metadata strobe) bit width
RDMETAMAN_CS_LAPPED_B = 15 # Address counter wrapped bit position
RDMETAMAN_CS_LAPPED_W = 1 # Address counter wrapped bit width

RDMETAMAN_METADATA_ADDRCNTR = 1 # Metadata address counter
RDMETAMAN_PARAM_ADDRCNTR = 2 # Parameter address counter
RDMETAMAN_TUNER = 3 # Tuner value
RDMETAMAN_TUNER_AT_RINGDOWN = 4 # Tuner value at ringdown
RDMETAMAN_ADDR_AT_RINGDOWN = 5 # Metadata address counter value at ringdown
RDMETAMAN_PARAM0 = 6 # Ringdown parameter 0
RDMETAMAN_PARAM1 = 7 # Ringdown parameter 1
RDMETAMAN_PARAM2 = 8 # Ringdown parameter 2
RDMETAMAN_PARAM3 = 9 # Ringdown parameter 3
RDMETAMAN_PARAM4 = 10 # Ringdown parameter 4
RDMETAMAN_PARAM5 = 11 # Ringdown parameter 5
RDMETAMAN_PARAM6 = 12 # Ringdown parameter 6
RDMETAMAN_PARAM7 = 13 # Ringdown parameter 7

# Block RDDATMAN Ringdown data manager
RDDATMAN_CS = 0 # Control/Status register
RDDATMAN_CS_RUN_B = 0 # STOP/RUN bit position
RDDATMAN_CS_RUN_W = 1 # STOP/RUN bit width
RDDATMAN_CS_CONT_B = 1 # SINGLE/CONTINUOUS bit position
RDDATMAN_CS_CONT_W = 1 # SINGLE/CONTINUOUS bit width
RDDATMAN_CS_ACK_B = 2 # Acknowledge completion of acquisition bit position
RDDATMAN_CS_ACK_W = 1 # Acknowledge completion of acquisition bit width
RDDATMAN_CS_BANK_B = 3 # Bank select bit position
RDDATMAN_CS_BANK_W = 1 # Bank select bit width
RDDATMAN_CS_GATE_B = 4 # Gate to arm for ringdown acquisition bit position
RDDATMAN_CS_GATE_W = 1 # Gate to arm for ringdown acquisition bit width
RDDATMAN_CS_RD_CLOCK_B = 14 # Ringdown ADC clock bit position
RDDATMAN_CS_RD_CLOCK_W = 1 # Ringdown ADC clock bit width
RDDATMAN_CS_ACQ_DONE_B = 15 # Acquisition done bit position
RDDATMAN_CS_ACQ_DONE_W = 1 # Acquisition done bit width

RDDATMAN_DATA_ADDRCNTR = 1 # Address counter
RDDATMAN_DATA = 2 # Ringdown data
RDDATMAN_DIVISOR = 3 # Divisor for ringdown ADC clock
RDDATMAN_NUM_SAMP = 4 # Number of samples to collect
RDDATMAN_THRESHOLD = 5 # Ringdown threshold

# Block RDMAN Ringdown manager
RDMAN_CONTROL = 0 # Control register
RDMAN_CONTROL_RUN_B = 0 # STOP/RUN bit position
RDMAN_CONTROL_RUN_W = 1 # STOP/RUN bit width
RDMAN_CONTROL_CONT_B = 1 # SINGLE/CONTINUOUS bit position
RDMAN_CONTROL_CONT_W = 1 # SINGLE/CONTINUOUS bit width
RDMAN_CONTROL_START_RD_B = 2 # Start ringdown cycle bit position
RDMAN_CONTROL_START_RD_W = 1 # Start ringdown cycle bit width
RDMAN_CONTROL_LOCK_ENABLE_B = 3 # Enable laser locking bit position
RDMAN_CONTROL_LOCK_ENABLE_W = 1 # Enable laser locking bit width
RDMAN_CONTROL_UP_SLOPE_ENABLE_B = 4 # Enable ringdown on positive slope bit position
RDMAN_CONTROL_UP_SLOPE_ENABLE_W = 1 # Enable ringdown on positive slope bit width
RDMAN_CONTROL_DOWN_SLOPE_ENABLE_B = 5 # Enable ringdown on negative slope bit position
RDMAN_CONTROL_DOWN_SLOPE_ENABLE_W = 1 # Enable ringdown on negative slope bit width
RDMAN_CONTROL_BANK0_CLEAR_B = 6 # Reset bank 0 in use bit position
RDMAN_CONTROL_BANK0_CLEAR_W = 1 # Reset bank 0 in use bit width
RDMAN_CONTROL_BANK1_CLEAR_B = 7 # Reset bank 1 in use bit position
RDMAN_CONTROL_BANK1_CLEAR_W = 1 # Reset bank 1 in use bit width
RDMAN_CONTROL_LASER_LOCKED_B = 8 # Laser wavelength locked bit position
RDMAN_CONTROL_LASER_LOCKED_W = 1 # Laser wavelength locked bit width
RDMAN_CONTROL_LASER_LOCKER_DONE_B = 9 # Laser locker done (metadata strobe) bit position
RDMAN_CONTROL_LASER_LOCKER_DONE_W = 1 # Laser locker done (metadata strobe) bit width
RDMAN_CONTROL_RD_IRQ_ACK_B = 10 # Acknowledge ringdown irq bit position
RDMAN_CONTROL_RD_IRQ_ACK_W = 1 # Acknowledge ringdown irq bit width
RDMAN_CONTROL_ACQ_DONE_ACK_B = 11 # Acknowledge acquisition irq bit position
RDMAN_CONTROL_ACQ_DONE_ACK_W = 1 # Acknowledge acquisition irq bit width

RDMAN_STATUS = 1 # Status register
RDMAN_STATUS_SHUTDOWN_B = 0 # Injection shutdown bit position
RDMAN_STATUS_SHUTDOWN_W = 1 # Injection shutdown bit width
RDMAN_STATUS_RD_IRQ_B = 1 # Ringdown interrupt bit position
RDMAN_STATUS_RD_IRQ_W = 1 # Ringdown interrupt bit width
RDMAN_STATUS_ACQ_DONE_B = 2 # Acquisition done interrupt bit position
RDMAN_STATUS_ACQ_DONE_W = 1 # Acquisition done interrupt bit width
RDMAN_STATUS_BANK_B = 3 # Bank for writes (ro) bit position
RDMAN_STATUS_BANK_W = 1 # Bank for writes (ro) bit width
RDMAN_STATUS_BANK0_IN_USE_B = 4 # Bank 0 in use   (ro) bit position
RDMAN_STATUS_BANK0_IN_USE_W = 1 # Bank 0 in use   (ro) bit width
RDMAN_STATUS_BANK1_IN_USE_B = 5 # Bank 1 in use   (ro) bit position
RDMAN_STATUS_BANK1_IN_USE_W = 1 # Bank 1 in use   (ro) bit width
RDMAN_STATUS_LAPPED_B = 6 # Address counter wrapped bit position
RDMAN_STATUS_LAPPED_W = 1 # Address counter wrapped bit width
RDMAN_STATUS_TIMEOUT_B = 7 # Ringdown timeout occured bit position
RDMAN_STATUS_TIMEOUT_W = 1 # Ringdown timeout occured bit width

RDMAN_TUNER = 2 # Tuner value
RDMAN_DATA = 3 # Ringdown data
RDMAN_PARAM0 = 4 # Ringdown parameter 0
RDMAN_PARAM1 = 5 # Ringdown parameter 1
RDMAN_PARAM2 = 6 # Ringdown parameter 2
RDMAN_PARAM3 = 7 # Ringdown parameter 3
RDMAN_PARAM4 = 8 # Ringdown parameter 4
RDMAN_PARAM5 = 9 # Ringdown parameter 5
RDMAN_PARAM6 = 10 # Ringdown parameter 6
RDMAN_PARAM7 = 11 # Ringdown parameter 7
RDMAN_DATA_ADDRCNTR = 12 # Address counter
RDMAN_METADATA_ADDRCNTR = 13 # Metadata address counter
RDMAN_PARAM_ADDRCNTR = 14 # Parameter address counter
RDMAN_DIVISOR = 15 # Divisor for ringdown ADC clock
RDMAN_NUM_SAMP = 16 # Number of samples to collect
RDMAN_THRESHOLD = 17 # Ringdown threshold
RDMAN_PRECONTROL_TIME = 18 # Precontrol time
RDMAN_RINGDOWN_TIMEOUT = 19 # Ringdown timeout
RDMAN_TUNER_AT_RINGDOWN = 20 # Tuner value at ringdown
RDMAN_METADATA_ADDR_AT_RINGDOWN = 21 # Metadata address counter value at ringdown

# Block LASER_CURRENT_DAC Laser current DAC
LASER_CURRENT_DAC_CS = 0 # Control/Status register
LASER_CURRENT_DAC_CS_RUN_B = 0 # STOP/RUN bit position
LASER_CURRENT_DAC_CS_RUN_W = 1 # STOP/RUN bit width
LASER_CURRENT_DAC_CS_CONT_B = 1 # SINGLE/CONTINUOUS bit position
LASER_CURRENT_DAC_CS_CONT_W = 1 # SINGLE/CONTINUOUS bit width

LASER_CURRENT_DAC_COARSE_CURRENT = 1 # Coarse current DAC
LASER_CURRENT_DAC_FINE_CURRENT = 2 # Fine current DAC

# Block RDCOMPARE Ringdown comparator
RDCOMPARE_THRESHOLD = 0 # Ringdown threshold
RDCOMPARE_RATE_DIVISOR = 1 # Ringdown address counter divisor

# Block TWGEN Tuner waveform generator
TWGEN_ACC = 0 # Accumulator
TWGEN_CS = 1 # Control/Status Register
TWGEN_CS_RUN_B = 0 # STOP/RUN bit position
TWGEN_CS_RUN_W = 1 # STOP/RUN bit width
TWGEN_CS_CONT_B = 1 # SINGLE/CONTINUOUS bit position
TWGEN_CS_CONT_W = 1 # SINGLE/CONTINUOUS bit width
TWGEN_CS_RESET_B = 2 # Reset generator bit position
TWGEN_CS_RESET_W = 1 # Reset generator bit width

TWGEN_SLOPE_DOWN = 2 # Slope in downward direction
TWGEN_SLOPE_UP = 3 # Slope in upward direction
TWGEN_SWEEP_LOW = 4 # Lower limit of sweep
TWGEN_SWEEP_HIGH = 5 # Higher limit of sweep
TWGEN_WINDOW_LOW = 6 # Lower limit of window
TWGEN_WINDOW_HIGH = 7 # Higher limit of window

# Block INJECT Optical injection subsystem
INJECT_CONTROL = 0 # Control register
INJECT_CONTROL_MODE_B = 0 # Manual/Automatic mode bit position
INJECT_CONTROL_MODE_W = 1 # Manual/Automatic mode bit width
INJECT_CONTROL_LASER_SELECT_B = 1 # Select laser bit position
INJECT_CONTROL_LASER_SELECT_W = 2 # Select laser bit width
INJECT_CONTROL_LASER_CURRENT_ENABLE_B = 3 # Laser current enable bit position
INJECT_CONTROL_LASER_CURRENT_ENABLE_W = 4 # Laser current enable bit width
INJECT_CONTROL_MANUAL_LASER_ENABLE_B = 7 # Deasserts short across laser in manual mode bit position
INJECT_CONTROL_MANUAL_LASER_ENABLE_W = 4 # Deasserts short across laser in manual mode bit width
INJECT_CONTROL_MANUAL_SOA_ENABLE_B = 11 # Deasserts short across SOA in manual mode bit position
INJECT_CONTROL_MANUAL_SOA_ENABLE_W = 1 # Deasserts short across SOA in manual mode bit width
INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B = 12 # Enables laser shutdown bit position
INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W = 1 # Enables laser shutdown bit width
INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B = 13 # Enables SOA shutdown bit position
INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W = 1 # Enables SOA shutdown bit width

INJECT_LASER1_COARSE_CURRENT = 1 # Sets coarse current for laser 1
INJECT_LASER2_COARSE_CURRENT = 2 # Sets coarse current for laser 2
INJECT_LASER3_COARSE_CURRENT = 3 # Sets coarse current for laser 3
INJECT_LASER4_COARSE_CURRENT = 4 # Sets coarse current for laser 4
INJECT_LASER1_FINE_CURRENT = 5 # Sets fine current for laser 1
INJECT_LASER2_FINE_CURRENT = 6 # Sets fine current for laser 2
INJECT_LASER3_FINE_CURRENT = 7 # Sets fine current for laser 3
INJECT_LASER4_FINE_CURRENT = 8 # Sets fine current for laser 4

# FPGA map indices
FPGA_KERNEL = 0 # Kernel registers
FPGA_LASER1_PWM = 2 # Laser 1 TEC pulse width modulator registers
FPGA_LASER2_PWM = 4 # Laser 2 TEC pulse width modulator registers
FPGA_LASER3_PWM = 6 # Laser 3 TEC pulse width modulator registers
FPGA_LASER4_PWM = 8 # Laser 4 TEC pulse width modulator registers
FPGA_RDSIM = 10 # Ringdown simulator registers
FPGA_LASERLOCK = 14 # Laser frequency locker registers
FPGA_RDMETAMAN = 41 # Ringdown metadata manager registers
FPGA_RDDATMAN = 55 # Ringdown data manager registers
FPGA_RDMAN = 61 # Ringdown manager registers
FPGA_LASER1_CURRENT_DAC = 83 # Laser1 current DAC registers
FPGA_LASER2_CURRENT_DAC = 86 # Laser2 current DAC registers
FPGA_LASER3_CURRENT_DAC = 89 # Laser3 current DAC registers
FPGA_LASER4_CURRENT_DAC = 92 # Laser4 current DAC registers
FPGA_RDCOMPARE = 95 # Ringdown comparator
FPGA_TWGEN = 97 # Tuner waveform generator
FPGA_INJECT = 105 # Optical Injection Subsystem

# Environment addresses
LASER1_TEMP_CNTRL_ENV = 0
LASER2_TEMP_CNTRL_ENV = 10
CHECK_ENV = 20
PULSE_GEN_ENV = 22
FILTER_ENV = 23
LASER_TEMP_MODEL_ENV = 49

# Dictionary for accessing environments by name
envByName = {}
envByName['LASER1_TEMP_CNTRL_ENV'] = (LASER1_TEMP_CNTRL_ENV,PidControllerEnvType)
envByName['LASER2_TEMP_CNTRL_ENV'] = (LASER2_TEMP_CNTRL_ENV,PidControllerEnvType)
envByName['CHECK_ENV'] = (CHECK_ENV,CheckEnvType)
envByName['PULSE_GEN_ENV'] = (PULSE_GEN_ENV,PulseGenEnvType)
envByName['FILTER_ENV'] = (FILTER_ENV,FilterEnvType)
envByName['LASER_TEMP_MODEL_ENV'] = (LASER_TEMP_MODEL_ENV,FilterEnvType)

# Action codes
ACTION_WRITE_BLOCK = 1
ACTION_SET_TIMESTAMP = 2
ACTION_GET_TIMESTAMP = 3
ACTION_INIT_RUNQUEUE = 4
ACTION_TEST_SCHEDULER = 5
ACTION_STREAM_REGISTER = 6
ACTION_RESISTANCE_TO_TEMPERATURE = 7
ACTION_TEMP_CNTRL_SET_COMMAND = 8
ACTION_APPLY_PID_STEP = 9
ACTION_TEMP_CNTRL_LASER1_INIT = 10
ACTION_TEMP_CNTRL_LASER1_STEP = 11
ACTION_TEMP_CNTRL_LASER2_INIT = 12
ACTION_TEMP_CNTRL_LASER2_STEP = 13
ACTION_TEMP_CNTRL_LASER3_INIT = 14
ACTION_TEMP_CNTRL_LASER3_STEP = 15
ACTION_TEMP_CNTRL_LASER4_INIT = 16
ACTION_TEMP_CNTRL_LASER4_STEP = 17
ACTION_FLOAT_REGISTER_TO_FPGA = 18
ACTION_FPGA_TO_FLOAT_REGISTER = 19
ACTION_INT_TO_FPGA = 20
ACTION_CURRENT_CNTRL_LASER1_INIT = 21
ACTION_CURRENT_CNTRL_LASER1_STEP = 22
ACTION_TEMP_CNTRL_CAVITY_INIT = 23
ACTION_TEMP_CNTRL_CAVITY_STEP = 24
ACTION_HEATER_CNTRL_INIT = 25
ACTION_HEATER_CNTRL_STEP = 26
ACTION_ENV_CHECKER = 27
ACTION_PULSE_GENERATOR = 28
ACTION_FILTER = 29
ACTION_DS1631_READTEMP = 30
ACTION_LASER_TEC_IMON = 31
ACTION_READ_LASER_TEC_MONITORS = 32


# Parameter form definitions

parameter_forms = []

# Form: System Configuration Parameters

__p = []

__p.append(('int',SCHEDULER_CONTROL_REGISTER,'Scheduler enable','','%d',1,0))
parameter_forms.append(('System Configuration Parameters',__p))

# Form: Laser 1 Parameters

__p = []

__p.append(('choices',LASER1_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('float',LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('float',LASER1_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('int',LASER1_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('float',LASER1_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('float',LASER1_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('float',LASER1_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
__p.append(('choices',LASER1_CURRENT_CNTRL_STATE_REGISTER,'Current Controller Mode','',[(LASER_CURRENT_CNTRL_DisabledState,"Controller Disabled"),(LASER_CURRENT_CNTRL_EnabledState,"Controller Enabled"),(LASER_CURRENT_CNTRL_SweepingState,"Continuous Sweeping"),(LASER_CURRENT_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('float',LASER1_MANUAL_COARSE_CURRENT_REGISTER,'Manual Coarse Current Setpoint','digU','%.0f',1,1))
__p.append(('float',LASER1_MANUAL_FINE_CURRENT_REGISTER,'Manual Fine Current Setpoint','digU','%.0f',1,1))
__p.append(('float',LASER1_CURRENT_SWEEP_MIN_REGISTER,'Current Sweep Minimum','digU','%.0f',1,1))
__p.append(('float',LASER1_CURRENT_SWEEP_MAX_REGISTER,'Current Sweep Maximum','digU','%.0f',1,1))
__p.append(('float',LASER1_CURRENT_SWEEP_INCR_REGISTER,'Current Sweep Increment','digU/sample','%.1f',1,1))
parameter_forms.append(('Laser 1 Parameters',__p))

# Form: Laser 2 Parameters

__p = []

__p.append(('choices',LASER2_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('float',LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('float',LASER2_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('int',LASER2_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('float',LASER2_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('float',LASER2_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('float',LASER2_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
parameter_forms.append(('Laser 2 Parameters',__p))

# Form: Laser 3 Parameters

__p = []

__p.append(('choices',LASER3_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('float',LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('float',LASER3_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('int',LASER3_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('float',LASER3_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('float',LASER3_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('float',LASER3_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
parameter_forms.append(('Laser 3 Parameters',__p))

# Form: Laser 4 Parameters

__p = []

__p.append(('choices',LASER4_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('float',LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('float',LASER4_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('int',LASER4_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('float',LASER4_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('float',LASER4_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('float',LASER4_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
parameter_forms.append(('Laser 4 Parameters',__p))

# Form: Cavity Temperature Parameters

__p = []

__p.append(('choices',CAVITY_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('float',CAVITY_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('int',CAVITY_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('float',CAVITY_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('float',CAVITY_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('float',CAVITY_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
__p.append(('float',CAVITY_MAX_HEATSINK_TEMP_REGISTER,'Hot Box heatsink maximum temperature','degC','%.3f',1,1))
__p.append(('choices',HEATER_CNTRL_STATE_REGISTER,'Heater Controller Mode','',[(HEATER_CNTRL_DisabledState,"Controller Disabled"),(HEATER_CNTRL_EnabledState,"Controller Enabled"),(HEATER_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('float',HEATER_CNTRL_GAIN_REGISTER,'Heater control gain','','%.0f',1,1))
__p.append(('float',HEATER_CNTRL_QUANTIZE_REGISTER,'Heater control quantization','','%.0f',1,1))
__p.append(('float',HEATER_CNTRL_UBIAS_SLOPE_REGISTER,'Heater control UBias slope','','%.0f',1,1))
__p.append(('float',HEATER_CNTRL_UBIAS_OFFSET_REGISTER,'Heater control UBias offset','','%.0f',1,1))
__p.append(('float',HEATER_CNTRL_MARK_MIN_REGISTER,'Heater minimum mark','','%.0f',1,1))
__p.append(('float',HEATER_CNTRL_MARK_MAX_REGISTER,'Heater maximum mark','','%.0f',1,1))
__p.append(('float',HEATER_CNTRL_MANUAL_MARK_REGISTER,'Heater manual mode mark','','%.0f',1,1))
parameter_forms.append(('Cavity Temperature Parameters',__p))

# Form: Pulse Generator Parameters

__p = []

__p.append(('int',LOW_DURATION_REGISTER,'Pulse low duration','samples','%d',1,1))
__p.append(('int',HIGH_DURATION_REGISTER,'Pulse high duration','samples','%d',1,1))
parameter_forms.append(('Pulse Generator Parameters',__p))
