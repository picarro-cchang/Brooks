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
from ctypes import c_longlong, c_float, Structure, Union, sizeof

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
ERROR_RD_BAD_RINGDOWN = -15
error_messages.append("Bad ringdown")
ERROR_RD_INSUFFICIENT_DATA = -16
error_messages.append("Insufficient data for ringdown calculation")

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
    ("warmBoxTemp",c_uint),
    ("hotBoxTecHeatsinkTemp",c_uint),
    ("warmBoxTecHeatsinkTemp",c_uint),
    ("laser1Temp",c_uint),
    ("laser2Temp",c_uint),
    ("laserCurrent",c_uint),
    ("cavityPressure",c_uint),
    ("inletPressure",c_uint),
    ("outletPressure",c_uint),
    ("customDataArray",c_ushort*16)
    ]

class RingdownMetadataType(Structure):
    _fields_ = [
    ("ratio1",c_uint),
    ("ratio2",c_uint),
    ("pztValue",c_uint),
    ("lockerOffset",c_uint),
    ("fineLaserCurrent",c_uint),
    ("lockerError",c_uint)
    ]

class RingdownParamsType(Structure):
    _fields_ = [
    ("injectionSettings",c_uint),
    ("laserTemperature",c_float),
    ("coarseLaserCurrent",c_uint),
    ("etalonTemperature",c_float),
    ("cavityPressure",c_float),
    ("ambientPressure",c_float),
    ("schemeTableAndRow",c_uint),
    ("countAndSubschemeId",c_uint),
    ("ringdownThreshold",c_uint),
    ("status",c_uint),
    ("tunerAtRingdown",c_uint),
    ("addressAtRingdown",c_uint)
    ]

class RingdownBufferType(Structure):
    _fields_ = [
    ("ringdownWaveform",c_uint*4096),
    ("parameters",RingdownParamsType)
    ]

class RingdownEntryType(Structure):
    _fields_ = [
    ("timestamp",c_longlong),
    ("wlmAngle",c_float),
    ("uncorrectedAbsorbance",c_float),
    ("correctedAbsorbance",c_float),
    ("status",c_ushort),
    ("count",c_ushort),
    ("tunerValue",c_ushort),
    ("pztValue",c_ushort),
    ("lockerOffset",c_ushort),
    ("laserUsed",c_ushort),
    ("ringdownThreshold",c_ushort),
    ("subschemeId",c_ushort),
    ("schemeTable",c_ushort),
    ("schemeRow",c_ushort),
    ("ratio1",c_ushort),
    ("ratio2",c_ushort),
    ("fineLaserCurrent",c_ushort),
    ("coarseLaserCurrent",c_ushort),
    ("laserTemperature",c_float),
    ("etalonTemperature",c_float),
    ("cavityPressure",c_ushort),
    ("ambientPressure",c_ushort),
    ("lockerError",c_ushort),
    ("padToCacheLine",c_ushort*1)
    ]

class SensorEntryType(Structure):
    _fields_ = [
    ("timestamp",c_longlong),
    ("streamNum",c_uint),
    ("value",DataType)
    ]

class ValveSequenceEntryType(Structure):
    _fields_ = [
    ("maskAndValue",c_ushort),
    ("dwell",c_ushort)
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

class SchemeRowType(Structure):
    _fields_ = [
    ("setpoint",c_float),
    ("dwellCount",c_ushort),
    ("subschemeId",c_ushort),
    ("laserUsed",c_ushort),
    ("threshold",c_ushort),
    ("pztSetpoint",c_ushort),
    ("laserTemp",c_ushort)
    ]

class SchemeTableHeaderType(Structure):
    _fields_ = [
    ("numRepeats",c_uint),
    ("numRows",c_uint)
    ]

class SchemeTableType(Structure):
    _fields_ = [
    ("numRepeats",c_uint),
    ("numRows",c_uint),
    ("rows",SchemeRowType*8192)
    ]

class SchemeSequenceType(Structure):
    _fields_ = [
    ("numberOfIndices",c_ushort),
    ("currentIndex",c_ushort),
    ("restartFlag",c_ushort),
    ("loopFlag",c_ushort),
    ("schemeIndices",c_ushort*16)
    ]

class VirtualLaserParamsType(Structure):
    _fields_ = [
    ("actualLaser",c_uint),
    ("tempSensitivity",c_float),
    ("ratio1Center",c_float),
    ("ratio2Center",c_float),
    ("ratio1Scale",c_float),
    ("ratio2Scale",c_float),
    ("phase",c_float),
    ("calTemp",c_float),
    ("calPressure",c_float),
    ("pressureC0",c_float),
    ("pressureC1",c_float),
    ("pressureC2",c_float),
    ("pressureC3",c_float),
    ("angleCenter",c_float),
    ("angleScale",c_float),
    ("angleToTempC0",c_float),
    ("angleToTempC1",c_float),
    ("angleToTempC2",c_float),
    ("angleToTempC3",c_float),
    ("tempCenter",c_float),
    ("tempScale",c_float),
    ("tempToAngleC0",c_float),
    ("tempToAngleC1",c_float),
    ("tempToAngleC2",c_float),
    ("tempToAngleC3",c_float)
    ]

# Constant definitions
# Number of points in controller waveforms
CONTROLLER_WAVEFORM_POINTS = 1000
# Number of points for waveforms on controller rindown pane
CONTROLLER_RINGDOWN_POINTS = 10000
# Number of points for Allan statistics plots in controller
CONTROLLER_STATS_POINTS = 32
# Base address for DSP data memory
DSP_DATA_ADDRESS = 0x80800000
# Offset for ringdown results in DSP data memory
RDRESULTS_OFFSET = 0x0
# Number of ringdown entries
NUM_RINGDOWN_ENTRIES = 2048
# Size of a ringdown entry in 32 bit ints
RINGDOWN_ENTRY_SIZE = (sizeof(RingdownEntryType)/4)
# Offset for scheme table in DSP shared memory
SCHEME_OFFSET = (RDRESULTS_OFFSET+NUM_RINGDOWN_ENTRIES*RINGDOWN_ENTRY_SIZE)
# Number of scheme tables
NUM_SCHEME_TABLES = 16
# Maximum rows in a scheme table
NUM_SCHEME_ROWS = 8192
# Size of a scheme row in 32 bit ints
SCHEME_ROW_SIZE = (sizeof(SchemeRowType)/4)
# Size of a scheme table in 32 bit ints
SCHEME_TABLE_SIZE = (sizeof(SchemeTableType)/4)
# Offset for virtual laser parameters in DSP shared memory
VIRTUAL_LASER_PARAMS_OFFSET = (SCHEME_OFFSET+NUM_SCHEME_TABLES*SCHEME_TABLE_SIZE)
# Maximum number of virtual lasers
NUM_VIRTUAL_LASERS = 8
# Size of a virtual laser parameter table in 32 bit ints
VIRTUAL_LASER_PARAMS_SIZE = (sizeof(VirtualLaserParamsType)/4)
# Base address for DSP shared memory
SHAREDMEM_ADDRESS = 0x10000
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
# Offset for ringdown buffer area in DSP shared memory
RINGDOWN_BUFFER_OFFSET = 0x4000
# Number of ringdown buffer areas in DSP shared memory
NUM_RINGDOWN_BUFFERS = 2
# Code to indicate that we abandoned this scheme row due to a timeout
MISSING_RINGDOWN = NUM_RINGDOWN_BUFFERS
# Size of a ringdown buffer area in 32 bit ints
RINGDOWN_BUFFER_SIZE = (sizeof(RingdownBufferType)/4)
# Offset for scheme sequence area in DSP shared memory
SCHEME_SEQUENCE_OFFSET = 0x7800
# Size of scheme sequence in 32 bit ints
SCHEME_SEQUENCE_SIZE = (sizeof(SchemeSequenceType)/4)
# Offset for valve sequence area in DSP shared memory
VALVE_SEQUENCE_OFFSET = (SCHEME_SEQUENCE_OFFSET+SCHEME_SEQUENCE_SIZE)
# Number of valve sequence entries
NUM_VALVE_SEQUENCE_ENTRIES = 256
# Size of a valve sequence in 32 bit ints
VALVE_SEQUENCE_ENTRY_SIZE = (sizeof(ValveSequenceEntryType)/4)
# Offset following used of shared memory
NEXT_AVAILABLE_OFFSET = (VALVE_SEQUENCE_OFFSET+NUM_VALVE_SEQUENCE_ENTRIES*VALVE_SEQUENCE_ENTRY_SIZE)
# Size (in 32-bit ints) of DSP shared memory
SHAREDMEM_SIZE = 0x8000
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
HOST_REGION_SIZE = (RINGDOWN_BUFFER_OFFSET - HOST_OFFSET)
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
RDMEM_PARAM_WIDTH = 32
# Number of address bits reserved for a ringdown region in each bank
RDMEM_RESERVED_BANK_ADDR_WIDTH = 12
# Number of address bits for one bank of data
DATA_BANK_ADDR_WIDTH = 12
# Number of address bits for one bank of metadata
META_BANK_ADDR_WIDTH = 12
# Number of address bits for one bank of parameters
PARAM_BANK_ADDR_WIDTH = 6
# Tuner value at ringdown index in parameter array
PARAM_TUNER_AT_RINGDOWN_INDEX = 10
# Metadata address at ringdown index in parameter array
PARAM_META_ADDR_AT_RINGDOWN_INDEX = 11
# Number of in-range samples to acquire lock
TEMP_CNTRL_LOCK_COUNT = 5
# Number of out-of-range samples to lose lock
TEMP_CNTRL_UNLOCK_COUNT = 5
# Code to confirm FPGA is programmed
FPGA_MAGIC_CODE = 0xC0DE0001
# Extra bits in accumulator for ringdown simulator
RDSIM_EXTRA = 4
# Number of bits for wavelength monitor ADCs
WLM_ADC_WIDTH = 16

# Enumerated definitions for STREAM_MemberType
STREAM_MemberType = c_uint
STREAM_Laser1Temp = 0 # 
STREAM_Laser2Temp = 1 # 
STREAM_Laser3Temp = 2 # 
STREAM_Laser4Temp = 3 # 
STREAM_EtalonTemp = 4 # 
STREAM_WarmBoxTemp = 5 # 
STREAM_WarmBoxHeatsinkTemp = 6 # 
STREAM_CavityTemp = 7 # 
STREAM_HotBoxHeatsinkTemp = 8 # 
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
STREAM_WarmBoxTec = 26 # 
STREAM_HotBoxTec = 27 # 
STREAM_HotBoxHeater = 28 # 
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
STREAM_MemberTypeDict[5] = 'STREAM_WarmBoxTemp' # 
STREAM_MemberTypeDict[6] = 'STREAM_WarmBoxHeatsinkTemp' # 
STREAM_MemberTypeDict[7] = 'STREAM_CavityTemp' # 
STREAM_MemberTypeDict[8] = 'STREAM_HotBoxHeatsinkTemp' # 
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
STREAM_MemberTypeDict[26] = 'STREAM_WarmBoxTec' # 
STREAM_MemberTypeDict[27] = 'STREAM_HotBoxTec' # 
STREAM_MemberTypeDict[28] = 'STREAM_HotBoxHeater' # 
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
TEMP_CNTRL_AutomaticState = 6 # Automatic Control

# Dictionary for enumerated constants in TEMP_CNTRL_StateType
TEMP_CNTRL_StateTypeDict = {}
TEMP_CNTRL_StateTypeDict[0] = 'TEMP_CNTRL_DisabledState' # Controller Disabled
TEMP_CNTRL_StateTypeDict[1] = 'TEMP_CNTRL_EnabledState' # Controller Enabled
TEMP_CNTRL_StateTypeDict[2] = 'TEMP_CNTRL_SuspendedState' # Controller Suspended
TEMP_CNTRL_StateTypeDict[3] = 'TEMP_CNTRL_SweepingState' # Continuous Sweeping
TEMP_CNTRL_StateTypeDict[4] = 'TEMP_CNTRL_SendPrbsState' # Sending PRBS
TEMP_CNTRL_StateTypeDict[5] = 'TEMP_CNTRL_ManualState' # Manual Control
TEMP_CNTRL_StateTypeDict[6] = 'TEMP_CNTRL_AutomaticState' # Automatic Control

# Enumerated definitions for LASER_CURRENT_CNTRL_StateType
LASER_CURRENT_CNTRL_StateType = c_uint
LASER_CURRENT_CNTRL_DisabledState = 0 # Controller Disabled
LASER_CURRENT_CNTRL_AutomaticState = 1 # Automatic Control
LASER_CURRENT_CNTRL_SweepingState = 2 # Continuous Sweeping
LASER_CURRENT_CNTRL_ManualState = 3 # Manual Control

# Dictionary for enumerated constants in LASER_CURRENT_CNTRL_StateType
LASER_CURRENT_CNTRL_StateTypeDict = {}
LASER_CURRENT_CNTRL_StateTypeDict[0] = 'LASER_CURRENT_CNTRL_DisabledState' # Controller Disabled
LASER_CURRENT_CNTRL_StateTypeDict[1] = 'LASER_CURRENT_CNTRL_AutomaticState' # Automatic Control
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

# Enumerated definitions for SPECT_CNTRL_StateType
SPECT_CNTRL_StateType = c_uint
SPECT_CNTRL_IdleState = 0 # Not acquiring
SPECT_CNTRL_StartingState = 1 # Start acquisition
SPECT_CNTRL_RunningState = 2 # Acquisition in progress
SPECT_CNTRL_PausedState = 3 # Acquisition paused
SPECT_CNTRL_ErrorState = 4 # Error state

# Dictionary for enumerated constants in SPECT_CNTRL_StateType
SPECT_CNTRL_StateTypeDict = {}
SPECT_CNTRL_StateTypeDict[0] = 'SPECT_CNTRL_IdleState' # Not acquiring
SPECT_CNTRL_StateTypeDict[1] = 'SPECT_CNTRL_StartingState' # Start acquisition
SPECT_CNTRL_StateTypeDict[2] = 'SPECT_CNTRL_RunningState' # Acquisition in progress
SPECT_CNTRL_StateTypeDict[3] = 'SPECT_CNTRL_PausedState' # Acquisition paused
SPECT_CNTRL_StateTypeDict[4] = 'SPECT_CNTRL_ErrorState' # Error state

# Enumerated definitions for SPECT_CNTRL_ModeType
SPECT_CNTRL_ModeType = c_uint
SPECT_CNTRL_SchemeSingleMode = 0 # Perform single scheme
SPECT_CNTRL_SchemeMultipleMode = 1 # Perform multiple schemes
SPECT_CNTRL_SchemeSequenceMode = 2 # Perform scheme sequence
SPECT_CNTRL_ContinuousMode = 3 # Continuous acquisition

# Dictionary for enumerated constants in SPECT_CNTRL_ModeType
SPECT_CNTRL_ModeTypeDict = {}
SPECT_CNTRL_ModeTypeDict[0] = 'SPECT_CNTRL_SchemeSingleMode' # Perform single scheme
SPECT_CNTRL_ModeTypeDict[1] = 'SPECT_CNTRL_SchemeMultipleMode' # Perform multiple schemes
SPECT_CNTRL_ModeTypeDict[2] = 'SPECT_CNTRL_SchemeSequenceMode' # Perform scheme sequence
SPECT_CNTRL_ModeTypeDict[3] = 'SPECT_CNTRL_ContinuousMode' # Continuous acquisition

# Enumerated definitions for TUNER_ModeType
TUNER_ModeType = c_uint
TUNER_RampMode = 0 # Ramp mode
TUNER_DitherMode = 1 # Dither mode

# Dictionary for enumerated constants in TUNER_ModeType
TUNER_ModeTypeDict = {}
TUNER_ModeTypeDict[0] = 'TUNER_RampMode' # Ramp mode
TUNER_ModeTypeDict[1] = 'TUNER_DitherMode' # Dither mode

# Enumerated definitions for VALVE_CNTRL_StateType
VALVE_CNTRL_StateType = c_uint
VALVE_CNTRL_DisabledState = 0 # Disabled
VALVE_CNTRL_OutletControlState = 1 # Outlet control
VALVE_CNTRL_InletControlState = 2 # Inlet control
VALVE_CNTRL_ManualControlState = 3 # Manual control

# Dictionary for enumerated constants in VALVE_CNTRL_StateType
VALVE_CNTRL_StateTypeDict = {}
VALVE_CNTRL_StateTypeDict[0] = 'VALVE_CNTRL_DisabledState' # Disabled
VALVE_CNTRL_StateTypeDict[1] = 'VALVE_CNTRL_OutletControlState' # Outlet control
VALVE_CNTRL_StateTypeDict[2] = 'VALVE_CNTRL_InletControlState' # Inlet control
VALVE_CNTRL_StateTypeDict[3] = 'VALVE_CNTRL_ManualControlState' # Manual control

# Enumerated definitions for VALVE_CNTRL_THRESHOLD_StateType
VALVE_CNTRL_THRESHOLD_StateType = c_uint
VALVE_CNTRL_THRESHOLD_DisabledState = 0 # Disabled
VALVE_CNTRL_THRESHOLD_ArmedState = 1 # Armed
VALVE_CNTRL_THRESHOLD_TriggeredState = 2 # Triggered

# Dictionary for enumerated constants in VALVE_CNTRL_THRESHOLD_StateType
VALVE_CNTRL_THRESHOLD_StateTypeDict = {}
VALVE_CNTRL_THRESHOLD_StateTypeDict[0] = 'VALVE_CNTRL_THRESHOLD_DisabledState' # Disabled
VALVE_CNTRL_THRESHOLD_StateTypeDict[1] = 'VALVE_CNTRL_THRESHOLD_ArmedState' # Armed
VALVE_CNTRL_THRESHOLD_StateTypeDict[2] = 'VALVE_CNTRL_THRESHOLD_TriggeredState' # Triggered

# Enumerated definitions for VIRTUAL_LASER_Type
VIRTUAL_LASER_Type = c_uint
VIRTUAL_LASER_1 = 0 # Virtual laser 1
VIRTUAL_LASER_2 = 1 # Virtual laser 2
VIRTUAL_LASER_3 = 2 # Virtual laser 3
VIRTUAL_LASER_4 = 3 # Virtual laser 4
VIRTUAL_LASER_5 = 4 # Virtual laser 5
VIRTUAL_LASER_6 = 5 # Virtual laser 6
VIRTUAL_LASER_7 = 6 # Virtual laser 7
VIRTUAL_LASER_8 = 7 # Virtual laser 8

# Dictionary for enumerated constants in VIRTUAL_LASER_Type
VIRTUAL_LASER_TypeDict = {}
VIRTUAL_LASER_TypeDict[0] = 'VIRTUAL_LASER_1' # Virtual laser 1
VIRTUAL_LASER_TypeDict[1] = 'VIRTUAL_LASER_2' # Virtual laser 2
VIRTUAL_LASER_TypeDict[2] = 'VIRTUAL_LASER_3' # Virtual laser 3
VIRTUAL_LASER_TypeDict[3] = 'VIRTUAL_LASER_4' # Virtual laser 4
VIRTUAL_LASER_TypeDict[4] = 'VIRTUAL_LASER_5' # Virtual laser 5
VIRTUAL_LASER_TypeDict[5] = 'VIRTUAL_LASER_6' # Virtual laser 6
VIRTUAL_LASER_TypeDict[6] = 'VIRTUAL_LASER_7' # Virtual laser 7
VIRTUAL_LASER_TypeDict[7] = 'VIRTUAL_LASER_8' # Virtual laser 8

# Definitions for COMM_STATUS_BITMASK
COMM_STATUS_CompleteMask = 0x1
COMM_STATUS_BadCrcMask = 0x2
COMM_STATUS_BadSequenceNumberMask = 0x4
COMM_STATUS_BadArgumentsMask = 0x8
COMM_STATUS_SequenceNumberMask = 0xFF000000
COMM_STATUS_ReturnValueMask = 0x00FFFF00
COMM_STATUS_SequenceNumberShift = 24
COMM_STATUS_ReturnValueShift = 8

# Definitions for RINGDOWN_STATUS_BITMASK
RINGDOWN_STATUS_SequenceMask = 0x0F
RINGDOWN_STATUS_SchemeActiveMask = 0x10
RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask = 0x20
RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask = 0x40
RINGDOWN_STATUS_RingdownTimeout = 0x80

# Definitions for SUBSCHEME_ID_BITMASK
SUBSCHEME_ID_IncrMask = 0x8000

# Definitions for SENTRY_BITMASK
SENTRY_Laser1TemperatureMask = 0x0001
SENTRY_Laser2TemperatureMask = 0x0002
SENTRY_Laser3TemperatureMask = 0x0004
SENTRY_Laser4TemperatureMask = 0x0008
SENTRY_EtalonTemperatureMask = 0x0010
SENTRY_WarmBoxTemperatureMask = 0x0020
SENTRY_WarmBoxHeatsinkTemperatureMask = 0x0040
SENTRY_CavityTemperatureMask = 0x0080
SENTRY_HotBoxHeatsinkTemperatureMask = 0x0100
SENTRY_DasTemperatureMask = 0x0200
SENTRY_Laser1CurrentMask = 0x0400
SENTRY_Laser2CurrentMask = 0x0800
SENTRY_Laser3CurrentMask = 0x1000
SENTRY_Laser4CurrentMask = 0x2000
SENTRY_CavityPressureMask = 0x4000
SENTRY_AmbientPressureMask = 0x8000

# Register definitions
INTERFACE_NUMBER_OF_REGISTERS = 356

NOOP_REGISTER = 0
VERIFY_INIT_REGISTER = 1
COMM_STATUS_REGISTER = 2
TIMESTAMP_LSB_REGISTER = 3
TIMESTAMP_MSB_REGISTER = 4
SCHEDULER_CONTROL_REGISTER = 5
RD_IRQ_COUNT_REGISTER = 6
ACQ_DONE_COUNT_REGISTER = 7
DAS_TEMPERATURE_REGISTER = 8
LASER_TEC_MONITOR_TEMPERATURE_REGISTER = 9
CONVERSION_LASER1_THERM_CONSTA_REGISTER = 10
CONVERSION_LASER1_THERM_CONSTB_REGISTER = 11
CONVERSION_LASER1_THERM_CONSTC_REGISTER = 12
CONVERSION_LASER1_CURRENT_SLOPE_REGISTER = 13
CONVERSION_LASER1_CURRENT_OFFSET_REGISTER = 14
LASER1_RESISTANCE_REGISTER = 15
LASER1_TEMPERATURE_REGISTER = 16
LASER1_THERMISTOR_ADC_REGISTER = 17
LASER1_TEC_REGISTER = 18
LASER1_MANUAL_TEC_REGISTER = 19
LASER1_TEMP_CNTRL_STATE_REGISTER = 20
LASER1_TEMP_CNTRL_LOCK_STATUS_REGISTER = 21
LASER1_TEMP_CNTRL_SETPOINT_REGISTER = 22
LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER = 23
LASER1_TEMP_CNTRL_TOLERANCE_REGISTER = 24
LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER = 25
LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER = 26
LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER = 27
LASER1_TEMP_CNTRL_H_REGISTER = 28
LASER1_TEMP_CNTRL_K_REGISTER = 29
LASER1_TEMP_CNTRL_TI_REGISTER = 30
LASER1_TEMP_CNTRL_TD_REGISTER = 31
LASER1_TEMP_CNTRL_B_REGISTER = 32
LASER1_TEMP_CNTRL_C_REGISTER = 33
LASER1_TEMP_CNTRL_N_REGISTER = 34
LASER1_TEMP_CNTRL_S_REGISTER = 35
LASER1_TEMP_CNTRL_FFWD_REGISTER = 36
LASER1_TEMP_CNTRL_AMIN_REGISTER = 37
LASER1_TEMP_CNTRL_AMAX_REGISTER = 38
LASER1_TEMP_CNTRL_IMAX_REGISTER = 39
LASER1_TEC_PRBS_GENPOLY_REGISTER = 40
LASER1_TEC_PRBS_AMPLITUDE_REGISTER = 41
LASER1_TEC_PRBS_MEAN_REGISTER = 42
LASER1_TEC_MONITOR_REGISTER = 43
LASER1_CURRENT_CNTRL_STATE_REGISTER = 44
LASER1_MANUAL_COARSE_CURRENT_REGISTER = 45
LASER1_MANUAL_FINE_CURRENT_REGISTER = 46
LASER1_CURRENT_SWEEP_MIN_REGISTER = 47
LASER1_CURRENT_SWEEP_MAX_REGISTER = 48
LASER1_CURRENT_SWEEP_INCR_REGISTER = 49
LASER1_CURRENT_MONITOR_REGISTER = 50
CONVERSION_LASER2_THERM_CONSTA_REGISTER = 51
CONVERSION_LASER2_THERM_CONSTB_REGISTER = 52
CONVERSION_LASER2_THERM_CONSTC_REGISTER = 53
CONVERSION_LASER2_CURRENT_SLOPE_REGISTER = 54
CONVERSION_LASER2_CURRENT_OFFSET_REGISTER = 55
LASER2_RESISTANCE_REGISTER = 56
LASER2_TEMPERATURE_REGISTER = 57
LASER2_THERMISTOR_ADC_REGISTER = 58
LASER2_TEC_REGISTER = 59
LASER2_MANUAL_TEC_REGISTER = 60
LASER2_TEMP_CNTRL_STATE_REGISTER = 61
LASER2_TEMP_CNTRL_LOCK_STATUS_REGISTER = 62
LASER2_TEMP_CNTRL_SETPOINT_REGISTER = 63
LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER = 64
LASER2_TEMP_CNTRL_TOLERANCE_REGISTER = 65
LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER = 66
LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER = 67
LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER = 68
LASER2_TEMP_CNTRL_H_REGISTER = 69
LASER2_TEMP_CNTRL_K_REGISTER = 70
LASER2_TEMP_CNTRL_TI_REGISTER = 71
LASER2_TEMP_CNTRL_TD_REGISTER = 72
LASER2_TEMP_CNTRL_B_REGISTER = 73
LASER2_TEMP_CNTRL_C_REGISTER = 74
LASER2_TEMP_CNTRL_N_REGISTER = 75
LASER2_TEMP_CNTRL_S_REGISTER = 76
LASER2_TEMP_CNTRL_FFWD_REGISTER = 77
LASER2_TEMP_CNTRL_AMIN_REGISTER = 78
LASER2_TEMP_CNTRL_AMAX_REGISTER = 79
LASER2_TEMP_CNTRL_IMAX_REGISTER = 80
LASER2_TEC_PRBS_GENPOLY_REGISTER = 81
LASER2_TEC_PRBS_AMPLITUDE_REGISTER = 82
LASER2_TEC_PRBS_MEAN_REGISTER = 83
LASER2_TEC_MONITOR_REGISTER = 84
LASER2_CURRENT_CNTRL_STATE_REGISTER = 85
LASER2_MANUAL_COARSE_CURRENT_REGISTER = 86
LASER2_MANUAL_FINE_CURRENT_REGISTER = 87
LASER2_CURRENT_SWEEP_MIN_REGISTER = 88
LASER2_CURRENT_SWEEP_MAX_REGISTER = 89
LASER2_CURRENT_SWEEP_INCR_REGISTER = 90
LASER2_CURRENT_MONITOR_REGISTER = 91
CONVERSION_LASER3_THERM_CONSTA_REGISTER = 92
CONVERSION_LASER3_THERM_CONSTB_REGISTER = 93
CONVERSION_LASER3_THERM_CONSTC_REGISTER = 94
CONVERSION_LASER3_CURRENT_SLOPE_REGISTER = 95
CONVERSION_LASER3_CURRENT_OFFSET_REGISTER = 96
LASER3_RESISTANCE_REGISTER = 97
LASER3_TEMPERATURE_REGISTER = 98
LASER3_THERMISTOR_ADC_REGISTER = 99
LASER3_TEC_REGISTER = 100
LASER3_MANUAL_TEC_REGISTER = 101
LASER3_TEMP_CNTRL_STATE_REGISTER = 102
LASER3_TEMP_CNTRL_LOCK_STATUS_REGISTER = 103
LASER3_TEMP_CNTRL_SETPOINT_REGISTER = 104
LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER = 105
LASER3_TEMP_CNTRL_TOLERANCE_REGISTER = 106
LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER = 107
LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER = 108
LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER = 109
LASER3_TEMP_CNTRL_H_REGISTER = 110
LASER3_TEMP_CNTRL_K_REGISTER = 111
LASER3_TEMP_CNTRL_TI_REGISTER = 112
LASER3_TEMP_CNTRL_TD_REGISTER = 113
LASER3_TEMP_CNTRL_B_REGISTER = 114
LASER3_TEMP_CNTRL_C_REGISTER = 115
LASER3_TEMP_CNTRL_N_REGISTER = 116
LASER3_TEMP_CNTRL_S_REGISTER = 117
LASER3_TEMP_CNTRL_FFWD_REGISTER = 118
LASER3_TEMP_CNTRL_AMIN_REGISTER = 119
LASER3_TEMP_CNTRL_AMAX_REGISTER = 120
LASER3_TEMP_CNTRL_IMAX_REGISTER = 121
LASER3_TEC_PRBS_GENPOLY_REGISTER = 122
LASER3_TEC_PRBS_AMPLITUDE_REGISTER = 123
LASER3_TEC_PRBS_MEAN_REGISTER = 124
LASER3_TEC_MONITOR_REGISTER = 125
LASER3_CURRENT_CNTRL_STATE_REGISTER = 126
LASER3_MANUAL_COARSE_CURRENT_REGISTER = 127
LASER3_MANUAL_FINE_CURRENT_REGISTER = 128
LASER3_CURRENT_SWEEP_MIN_REGISTER = 129
LASER3_CURRENT_SWEEP_MAX_REGISTER = 130
LASER3_CURRENT_SWEEP_INCR_REGISTER = 131
LASER3_CURRENT_MONITOR_REGISTER = 132
CONVERSION_LASER4_THERM_CONSTA_REGISTER = 133
CONVERSION_LASER4_THERM_CONSTB_REGISTER = 134
CONVERSION_LASER4_THERM_CONSTC_REGISTER = 135
CONVERSION_LASER4_CURRENT_SLOPE_REGISTER = 136
CONVERSION_LASER4_CURRENT_OFFSET_REGISTER = 137
LASER4_RESISTANCE_REGISTER = 138
LASER4_TEMPERATURE_REGISTER = 139
LASER4_THERMISTOR_ADC_REGISTER = 140
LASER4_TEC_REGISTER = 141
LASER4_MANUAL_TEC_REGISTER = 142
LASER4_TEMP_CNTRL_STATE_REGISTER = 143
LASER4_TEMP_CNTRL_LOCK_STATUS_REGISTER = 144
LASER4_TEMP_CNTRL_SETPOINT_REGISTER = 145
LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER = 146
LASER4_TEMP_CNTRL_TOLERANCE_REGISTER = 147
LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER = 148
LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER = 149
LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER = 150
LASER4_TEMP_CNTRL_H_REGISTER = 151
LASER4_TEMP_CNTRL_K_REGISTER = 152
LASER4_TEMP_CNTRL_TI_REGISTER = 153
LASER4_TEMP_CNTRL_TD_REGISTER = 154
LASER4_TEMP_CNTRL_B_REGISTER = 155
LASER4_TEMP_CNTRL_C_REGISTER = 156
LASER4_TEMP_CNTRL_N_REGISTER = 157
LASER4_TEMP_CNTRL_S_REGISTER = 158
LASER4_TEMP_CNTRL_FFWD_REGISTER = 159
LASER4_TEMP_CNTRL_AMIN_REGISTER = 160
LASER4_TEMP_CNTRL_AMAX_REGISTER = 161
LASER4_TEMP_CNTRL_IMAX_REGISTER = 162
LASER4_TEC_PRBS_GENPOLY_REGISTER = 163
LASER4_TEC_PRBS_AMPLITUDE_REGISTER = 164
LASER4_TEC_PRBS_MEAN_REGISTER = 165
LASER4_TEC_MONITOR_REGISTER = 166
LASER4_CURRENT_CNTRL_STATE_REGISTER = 167
LASER4_MANUAL_COARSE_CURRENT_REGISTER = 168
LASER4_MANUAL_FINE_CURRENT_REGISTER = 169
LASER4_CURRENT_SWEEP_MIN_REGISTER = 170
LASER4_CURRENT_SWEEP_MAX_REGISTER = 171
LASER4_CURRENT_SWEEP_INCR_REGISTER = 172
LASER4_CURRENT_MONITOR_REGISTER = 173
CONVERSION_ETALON_THERM_CONSTA_REGISTER = 174
CONVERSION_ETALON_THERM_CONSTB_REGISTER = 175
CONVERSION_ETALON_THERM_CONSTC_REGISTER = 176
ETALON_RESISTANCE_REGISTER = 177
ETALON_TEMPERATURE_REGISTER = 178
ETALON_THERMISTOR_ADC_REGISTER = 179
CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER = 180
CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER = 181
CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER = 182
WARM_BOX_RESISTANCE_REGISTER = 183
WARM_BOX_TEMPERATURE_REGISTER = 184
WARM_BOX_THERMISTOR_ADC_REGISTER = 185
WARM_BOX_TEC_REGISTER = 186
WARM_BOX_MANUAL_TEC_REGISTER = 187
WARM_BOX_TEMP_CNTRL_STATE_REGISTER = 188
WARM_BOX_TEMP_CNTRL_LOCK_STATUS_REGISTER = 189
WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER = 190
WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER = 191
WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER = 192
WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER = 193
WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER = 194
WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER = 195
WARM_BOX_TEMP_CNTRL_H_REGISTER = 196
WARM_BOX_TEMP_CNTRL_K_REGISTER = 197
WARM_BOX_TEMP_CNTRL_TI_REGISTER = 198
WARM_BOX_TEMP_CNTRL_TD_REGISTER = 199
WARM_BOX_TEMP_CNTRL_B_REGISTER = 200
WARM_BOX_TEMP_CNTRL_C_REGISTER = 201
WARM_BOX_TEMP_CNTRL_N_REGISTER = 202
WARM_BOX_TEMP_CNTRL_S_REGISTER = 203
WARM_BOX_TEMP_CNTRL_FFWD_REGISTER = 204
WARM_BOX_TEMP_CNTRL_AMIN_REGISTER = 205
WARM_BOX_TEMP_CNTRL_AMAX_REGISTER = 206
WARM_BOX_TEMP_CNTRL_IMAX_REGISTER = 207
WARM_BOX_TEC_PRBS_GENPOLY_REGISTER = 208
WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER = 209
WARM_BOX_TEC_PRBS_MEAN_REGISTER = 210
WARM_BOX_MAX_HEATSINK_TEMP_REGISTER = 211
CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER = 212
CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER = 213
CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER = 214
WARM_BOX_HEATSINK_RESISTANCE_REGISTER = 215
WARM_BOX_HEATSINK_TEMPERATURE_REGISTER = 216
WARM_BOX_HEATSINK_THERMISTOR_ADC_REGISTER = 217
CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER = 218
CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER = 219
CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER = 220
HOT_BOX_HEATSINK_RESISTANCE_REGISTER = 221
HOT_BOX_HEATSINK_TEMPERATURE_REGISTER = 222
HOT_BOX_HEATSINK_ADC_REGISTER = 223
CONVERSION_CAVITY_THERM_CONSTA_REGISTER = 224
CONVERSION_CAVITY_THERM_CONSTB_REGISTER = 225
CONVERSION_CAVITY_THERM_CONSTC_REGISTER = 226
CAVITY_RESISTANCE_REGISTER = 227
CAVITY_TEMPERATURE_REGISTER = 228
CAVITY_THERMISTOR_ADC_REGISTER = 229
CAVITY_TEC_REGISTER = 230
CAVITY_MANUAL_TEC_REGISTER = 231
CAVITY_TEMP_CNTRL_STATE_REGISTER = 232
CAVITY_TEMP_CNTRL_LOCK_STATUS_REGISTER = 233
CAVITY_TEMP_CNTRL_SETPOINT_REGISTER = 234
CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER = 235
CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER = 236
CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER = 237
CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER = 238
CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER = 239
CAVITY_TEMP_CNTRL_H_REGISTER = 240
CAVITY_TEMP_CNTRL_K_REGISTER = 241
CAVITY_TEMP_CNTRL_TI_REGISTER = 242
CAVITY_TEMP_CNTRL_TD_REGISTER = 243
CAVITY_TEMP_CNTRL_B_REGISTER = 244
CAVITY_TEMP_CNTRL_C_REGISTER = 245
CAVITY_TEMP_CNTRL_N_REGISTER = 246
CAVITY_TEMP_CNTRL_S_REGISTER = 247
CAVITY_TEMP_CNTRL_FFWD_REGISTER = 248
CAVITY_TEMP_CNTRL_AMIN_REGISTER = 249
CAVITY_TEMP_CNTRL_AMAX_REGISTER = 250
CAVITY_TEMP_CNTRL_IMAX_REGISTER = 251
CAVITY_TEC_PRBS_GENPOLY_REGISTER = 252
CAVITY_TEC_PRBS_AMPLITUDE_REGISTER = 253
CAVITY_TEC_PRBS_MEAN_REGISTER = 254
CAVITY_MAX_HEATSINK_TEMP_REGISTER = 255
HEATER_CNTRL_STATE_REGISTER = 256
HEATER_CNTRL_GAIN_REGISTER = 257
HEATER_CNTRL_QUANTIZE_REGISTER = 258
HEATER_CNTRL_UBIAS_SLOPE_REGISTER = 259
HEATER_CNTRL_UBIAS_OFFSET_REGISTER = 260
HEATER_CNTRL_MARK_MIN_REGISTER = 261
HEATER_CNTRL_MARK_MAX_REGISTER = 262
HEATER_CNTRL_MANUAL_MARK_REGISTER = 263
HEATER_CNTRL_MARK_REGISTER = 264
CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER = 265
CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER = 266
CAVITY_PRESSURE_REGISTER = 267
CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER = 268
CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER = 269
AMBIENT_PRESSURE_REGISTER = 270
TUNER_SWEEP_RAMP_HIGH_REGISTER = 271
TUNER_SWEEP_RAMP_LOW_REGISTER = 272
TUNER_WINDOW_RAMP_HIGH_REGISTER = 273
TUNER_WINDOW_RAMP_LOW_REGISTER = 274
TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER = 275
TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER = 276
TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER = 277
TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER = 278
RDFITTER_MINLOSS_REGISTER = 279
RDFITTER_MAXLOSS_REGISTER = 280
RDFITTER_LATEST_LOSS_REGISTER = 281
RDFITTER_IMPROVEMENT_STEPS_REGISTER = 282
RDFITTER_START_SAMPLE_REGISTER = 283
RDFITTER_FRACTIONAL_THRESHOLD_REGISTER = 284
RDFITTER_ABSOLUTE_THRESHOLD_REGISTER = 285
RDFITTER_NUMBER_OF_POINTS_REGISTER = 286
RDFITTER_MAX_E_FOLDINGS_REGISTER = 287
SPECT_CNTRL_STATE_REGISTER = 288
SPECT_CNTRL_MODE_REGISTER = 289
SPECT_CNTRL_ACTIVE_SCHEME_REGISTER = 290
SPECT_CNTRL_NEXT_SCHEME_REGISTER = 291
SPECT_CNTRL_SCHEME_ITER_REGISTER = 292
SPECT_CNTRL_SCHEME_ROW_REGISTER = 293
SPECT_CNTRL_DWELL_COUNT_REGISTER = 294
SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER = 295
SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER = 296
SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER = 297
VIRTUAL_LASER_REGISTER = 298
VALVE_CNTRL_STATE_REGISTER = 299
VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER = 300
VALVE_CNTRL_INLET_VALVE_REGISTER = 301
VALVE_CNTRL_OUTLET_VALVE_REGISTER = 302
VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER = 303
VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER = 304
VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER = 305
VALVE_CNTRL_INLET_VALVE_MIN_REGISTER = 306
VALVE_CNTRL_INLET_VALVE_MAX_REGISTER = 307
VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER = 308
VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER = 309
VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER = 310
VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER = 311
VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER = 312
VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER = 313
VALVE_CNTRL_THRESHOLD_STATE_REGISTER = 314
VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER = 315
VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER = 316
VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER = 317
VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER = 318
VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER = 319
VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER = 320
VALVE_CNTRL_SEQUENCE_STEP_REGISTER = 321
SENTRY_UPPER_LIMIT_TRIPPED_REGISTER = 322
SENTRY_LOWER_LIMIT_TRIPPED_REGISTER = 323
SENTRY_LASER1_TEMPERATURE_MIN_REGISTER = 324
SENTRY_LASER1_TEMPERATURE_MAX_REGISTER = 325
SENTRY_LASER2_TEMPERATURE_MIN_REGISTER = 326
SENTRY_LASER2_TEMPERATURE_MAX_REGISTER = 327
SENTRY_LASER3_TEMPERATURE_MIN_REGISTER = 328
SENTRY_LASER3_TEMPERATURE_MAX_REGISTER = 329
SENTRY_LASER4_TEMPERATURE_MIN_REGISTER = 330
SENTRY_LASER4_TEMPERATURE_MAX_REGISTER = 331
SENTRY_ETALON_TEMPERATURE_MIN_REGISTER = 332
SENTRY_ETALON_TEMPERATURE_MAX_REGISTER = 333
SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER = 334
SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER = 335
SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER = 336
SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER = 337
SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER = 338
SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER = 339
SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER = 340
SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER = 341
SENTRY_DAS_TEMPERATURE_MIN_REGISTER = 342
SENTRY_DAS_TEMPERATURE_MAX_REGISTER = 343
SENTRY_LASER1_CURRENT_MIN_REGISTER = 344
SENTRY_LASER1_CURRENT_MAX_REGISTER = 345
SENTRY_LASER2_CURRENT_MIN_REGISTER = 346
SENTRY_LASER2_CURRENT_MAX_REGISTER = 347
SENTRY_LASER3_CURRENT_MIN_REGISTER = 348
SENTRY_LASER3_CURRENT_MAX_REGISTER = 349
SENTRY_LASER4_CURRENT_MIN_REGISTER = 350
SENTRY_LASER4_CURRENT_MAX_REGISTER = 351
SENTRY_CAVITY_PRESSURE_MIN_REGISTER = 352
SENTRY_CAVITY_PRESSURE_MAX_REGISTER = 353
SENTRY_AMBIENT_PRESSURE_MIN_REGISTER = 354
SENTRY_AMBIENT_PRESSURE_MAX_REGISTER = 355

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
registerInfo.append(RegInfo("SCHEDULER_CONTROL_REGISTER",c_uint,0,1.0,"rw"))
registerByName["RD_IRQ_COUNT_REGISTER"] = RD_IRQ_COUNT_REGISTER
registerInfo.append(RegInfo("RD_IRQ_COUNT_REGISTER",c_uint,0,1.0,"r"))
registerByName["ACQ_DONE_COUNT_REGISTER"] = ACQ_DONE_COUNT_REGISTER
registerInfo.append(RegInfo("ACQ_DONE_COUNT_REGISTER",c_uint,0,1.0,"r"))
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
registerByName["CONVERSION_LASER1_CURRENT_SLOPE_REGISTER"] = CONVERSION_LASER1_CURRENT_SLOPE_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER1_CURRENT_SLOPE_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER1_CURRENT_OFFSET_REGISTER"] = CONVERSION_LASER1_CURRENT_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER1_CURRENT_OFFSET_REGISTER",c_float,1,1.0,"rw"))
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
registerByName["CONVERSION_LASER2_CURRENT_SLOPE_REGISTER"] = CONVERSION_LASER2_CURRENT_SLOPE_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER2_CURRENT_SLOPE_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER2_CURRENT_OFFSET_REGISTER"] = CONVERSION_LASER2_CURRENT_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER2_CURRENT_OFFSET_REGISTER",c_float,1,1.0,"rw"))
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
registerByName["LASER2_CURRENT_CNTRL_STATE_REGISTER"] = LASER2_CURRENT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER2_CURRENT_CNTRL_STATE_REGISTER",LASER_CURRENT_CNTRL_StateType,0,1.0,"rw"))
registerByName["LASER2_MANUAL_COARSE_CURRENT_REGISTER"] = LASER2_MANUAL_COARSE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER2_MANUAL_COARSE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_MANUAL_FINE_CURRENT_REGISTER"] = LASER2_MANUAL_FINE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER2_MANUAL_FINE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_CURRENT_SWEEP_MIN_REGISTER"] = LASER2_CURRENT_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER2_CURRENT_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_CURRENT_SWEEP_MAX_REGISTER"] = LASER2_CURRENT_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER2_CURRENT_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_CURRENT_SWEEP_INCR_REGISTER"] = LASER2_CURRENT_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER2_CURRENT_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER2_CURRENT_MONITOR_REGISTER"] = LASER2_CURRENT_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER2_CURRENT_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerByName["CONVERSION_LASER3_THERM_CONSTA_REGISTER"] = CONVERSION_LASER3_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER3_THERM_CONSTB_REGISTER"] = CONVERSION_LASER3_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER3_THERM_CONSTC_REGISTER"] = CONVERSION_LASER3_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER3_CURRENT_SLOPE_REGISTER"] = CONVERSION_LASER3_CURRENT_SLOPE_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_CURRENT_SLOPE_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER3_CURRENT_OFFSET_REGISTER"] = CONVERSION_LASER3_CURRENT_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_CURRENT_OFFSET_REGISTER",c_float,1,1.0,"rw"))
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
registerByName["LASER3_CURRENT_CNTRL_STATE_REGISTER"] = LASER3_CURRENT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER3_CURRENT_CNTRL_STATE_REGISTER",LASER_CURRENT_CNTRL_StateType,0,1.0,"rw"))
registerByName["LASER3_MANUAL_COARSE_CURRENT_REGISTER"] = LASER3_MANUAL_COARSE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER3_MANUAL_COARSE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_MANUAL_FINE_CURRENT_REGISTER"] = LASER3_MANUAL_FINE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER3_MANUAL_FINE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_CURRENT_SWEEP_MIN_REGISTER"] = LASER3_CURRENT_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER3_CURRENT_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_CURRENT_SWEEP_MAX_REGISTER"] = LASER3_CURRENT_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER3_CURRENT_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_CURRENT_SWEEP_INCR_REGISTER"] = LASER3_CURRENT_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER3_CURRENT_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER3_CURRENT_MONITOR_REGISTER"] = LASER3_CURRENT_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER3_CURRENT_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerByName["CONVERSION_LASER4_THERM_CONSTA_REGISTER"] = CONVERSION_LASER4_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER4_THERM_CONSTB_REGISTER"] = CONVERSION_LASER4_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER4_THERM_CONSTC_REGISTER"] = CONVERSION_LASER4_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER4_CURRENT_SLOPE_REGISTER"] = CONVERSION_LASER4_CURRENT_SLOPE_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_CURRENT_SLOPE_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_LASER4_CURRENT_OFFSET_REGISTER"] = CONVERSION_LASER4_CURRENT_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_CURRENT_OFFSET_REGISTER",c_float,1,1.0,"rw"))
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
registerByName["LASER4_CURRENT_CNTRL_STATE_REGISTER"] = LASER4_CURRENT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER4_CURRENT_CNTRL_STATE_REGISTER",LASER_CURRENT_CNTRL_StateType,0,1.0,"rw"))
registerByName["LASER4_MANUAL_COARSE_CURRENT_REGISTER"] = LASER4_MANUAL_COARSE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER4_MANUAL_COARSE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_MANUAL_FINE_CURRENT_REGISTER"] = LASER4_MANUAL_FINE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER4_MANUAL_FINE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_CURRENT_SWEEP_MIN_REGISTER"] = LASER4_CURRENT_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER4_CURRENT_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_CURRENT_SWEEP_MAX_REGISTER"] = LASER4_CURRENT_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER4_CURRENT_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_CURRENT_SWEEP_INCR_REGISTER"] = LASER4_CURRENT_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER4_CURRENT_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerByName["LASER4_CURRENT_MONITOR_REGISTER"] = LASER4_CURRENT_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER4_CURRENT_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerByName["CONVERSION_ETALON_THERM_CONSTA_REGISTER"] = CONVERSION_ETALON_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_ETALON_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_ETALON_THERM_CONSTB_REGISTER"] = CONVERSION_ETALON_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_ETALON_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_ETALON_THERM_CONSTC_REGISTER"] = CONVERSION_ETALON_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_ETALON_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["ETALON_RESISTANCE_REGISTER"] = ETALON_RESISTANCE_REGISTER
registerInfo.append(RegInfo("ETALON_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["ETALON_TEMPERATURE_REGISTER"] = ETALON_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("ETALON_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["ETALON_THERMISTOR_ADC_REGISTER"] = ETALON_THERMISTOR_ADC_REGISTER
registerInfo.append(RegInfo("ETALON_THERMISTOR_ADC_REGISTER",c_uint,0,1.0,"r"))
registerByName["CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER"] = CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER"] = CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER"] = CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_RESISTANCE_REGISTER"] = WARM_BOX_RESISTANCE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["WARM_BOX_TEMPERATURE_REGISTER"] = WARM_BOX_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["WARM_BOX_THERMISTOR_ADC_REGISTER"] = WARM_BOX_THERMISTOR_ADC_REGISTER
registerInfo.append(RegInfo("WARM_BOX_THERMISTOR_ADC_REGISTER",c_uint,0,1.0,"r"))
registerByName["WARM_BOX_TEC_REGISTER"] = WARM_BOX_TEC_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEC_REGISTER",c_float,0,1.0,"r"))
registerByName["WARM_BOX_MANUAL_TEC_REGISTER"] = WARM_BOX_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("WARM_BOX_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_STATE_REGISTER"] = WARM_BOX_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_LOCK_STATUS_REGISTER"] = WARM_BOX_TEMP_CNTRL_LOCK_STATUS_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_LOCK_STATUS_REGISTER",c_uint,0,1.0,"r"))
registerByName["WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER"] = WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"r"))
registerByName["WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER"] = WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_H_REGISTER"] = WARM_BOX_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_K_REGISTER"] = WARM_BOX_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_TI_REGISTER"] = WARM_BOX_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_TD_REGISTER"] = WARM_BOX_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_B_REGISTER"] = WARM_BOX_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_C_REGISTER"] = WARM_BOX_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_N_REGISTER"] = WARM_BOX_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_S_REGISTER"] = WARM_BOX_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_FFWD_REGISTER"] = WARM_BOX_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_AMIN_REGISTER"] = WARM_BOX_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_AMAX_REGISTER"] = WARM_BOX_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEMP_CNTRL_IMAX_REGISTER"] = WARM_BOX_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEC_PRBS_GENPOLY_REGISTER"] = WARM_BOX_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerByName["WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER"] = WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_TEC_PRBS_MEAN_REGISTER"] = WARM_BOX_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_MAX_HEATSINK_TEMP_REGISTER"] = WARM_BOX_MAX_HEATSINK_TEMP_REGISTER
registerInfo.append(RegInfo("WARM_BOX_MAX_HEATSINK_TEMP_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER"] = CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER"] = CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER"] = CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerByName["WARM_BOX_HEATSINK_RESISTANCE_REGISTER"] = WARM_BOX_HEATSINK_RESISTANCE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_HEATSINK_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["WARM_BOX_HEATSINK_TEMPERATURE_REGISTER"] = WARM_BOX_HEATSINK_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_HEATSINK_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["WARM_BOX_HEATSINK_THERMISTOR_ADC_REGISTER"] = WARM_BOX_HEATSINK_THERMISTOR_ADC_REGISTER
registerInfo.append(RegInfo("WARM_BOX_HEATSINK_THERMISTOR_ADC_REGISTER",c_uint,0,1.0,"r"))
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
registerByName["CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER"] = CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER"] = CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerByName["CAVITY_PRESSURE_REGISTER"] = CAVITY_PRESSURE_REGISTER
registerInfo.append(RegInfo("CAVITY_PRESSURE_REGISTER",c_float,0,1.0,"r"))
registerByName["CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER"] = CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER
registerInfo.append(RegInfo("CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER",c_float,1,1.0,"rw"))
registerByName["CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER"] = CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerByName["AMBIENT_PRESSURE_REGISTER"] = AMBIENT_PRESSURE_REGISTER
registerInfo.append(RegInfo("AMBIENT_PRESSURE_REGISTER",c_float,0,1.0,"r"))
registerByName["TUNER_SWEEP_RAMP_HIGH_REGISTER"] = TUNER_SWEEP_RAMP_HIGH_REGISTER
registerInfo.append(RegInfo("TUNER_SWEEP_RAMP_HIGH_REGISTER",c_float,1,1.0,"rw"))
registerByName["TUNER_SWEEP_RAMP_LOW_REGISTER"] = TUNER_SWEEP_RAMP_LOW_REGISTER
registerInfo.append(RegInfo("TUNER_SWEEP_RAMP_LOW_REGISTER",c_float,1,1.0,"rw"))
registerByName["TUNER_WINDOW_RAMP_HIGH_REGISTER"] = TUNER_WINDOW_RAMP_HIGH_REGISTER
registerInfo.append(RegInfo("TUNER_WINDOW_RAMP_HIGH_REGISTER",c_float,1,1.0,"rw"))
registerByName["TUNER_WINDOW_RAMP_LOW_REGISTER"] = TUNER_WINDOW_RAMP_LOW_REGISTER
registerInfo.append(RegInfo("TUNER_WINDOW_RAMP_LOW_REGISTER",c_float,1,1.0,"rw"))
registerByName["TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER"] = TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER
registerInfo.append(RegInfo("TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerByName["TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER"] = TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER
registerInfo.append(RegInfo("TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerByName["TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER"] = TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER
registerInfo.append(RegInfo("TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerByName["TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER"] = TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER
registerInfo.append(RegInfo("TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerByName["RDFITTER_MINLOSS_REGISTER"] = RDFITTER_MINLOSS_REGISTER
registerInfo.append(RegInfo("RDFITTER_MINLOSS_REGISTER",c_float,1,1.0,"rw"))
registerByName["RDFITTER_MAXLOSS_REGISTER"] = RDFITTER_MAXLOSS_REGISTER
registerInfo.append(RegInfo("RDFITTER_MAXLOSS_REGISTER",c_float,1,1.0,"rw"))
registerByName["RDFITTER_LATEST_LOSS_REGISTER"] = RDFITTER_LATEST_LOSS_REGISTER
registerInfo.append(RegInfo("RDFITTER_LATEST_LOSS_REGISTER",c_float,0,1.0,"r"))
registerByName["RDFITTER_IMPROVEMENT_STEPS_REGISTER"] = RDFITTER_IMPROVEMENT_STEPS_REGISTER
registerInfo.append(RegInfo("RDFITTER_IMPROVEMENT_STEPS_REGISTER",c_uint,1,1.0,"rw"))
registerByName["RDFITTER_START_SAMPLE_REGISTER"] = RDFITTER_START_SAMPLE_REGISTER
registerInfo.append(RegInfo("RDFITTER_START_SAMPLE_REGISTER",c_uint,1,1.0,"rw"))
registerByName["RDFITTER_FRACTIONAL_THRESHOLD_REGISTER"] = RDFITTER_FRACTIONAL_THRESHOLD_REGISTER
registerInfo.append(RegInfo("RDFITTER_FRACTIONAL_THRESHOLD_REGISTER",c_float,1,1.0,"rw"))
registerByName["RDFITTER_ABSOLUTE_THRESHOLD_REGISTER"] = RDFITTER_ABSOLUTE_THRESHOLD_REGISTER
registerInfo.append(RegInfo("RDFITTER_ABSOLUTE_THRESHOLD_REGISTER",c_float,1,1.0,"rw"))
registerByName["RDFITTER_NUMBER_OF_POINTS_REGISTER"] = RDFITTER_NUMBER_OF_POINTS_REGISTER
registerInfo.append(RegInfo("RDFITTER_NUMBER_OF_POINTS_REGISTER",c_uint,1,1.0,"rw"))
registerByName["RDFITTER_MAX_E_FOLDINGS_REGISTER"] = RDFITTER_MAX_E_FOLDINGS_REGISTER
registerInfo.append(RegInfo("RDFITTER_MAX_E_FOLDINGS_REGISTER",c_float,1,1.0,"rw"))
registerByName["SPECT_CNTRL_STATE_REGISTER"] = SPECT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_StateType,0,1.0,"rw"))
registerByName["SPECT_CNTRL_MODE_REGISTER"] = SPECT_CNTRL_MODE_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_MODE_REGISTER",SPECT_CNTRL_ModeType,1,1.0,"rw"))
registerByName["SPECT_CNTRL_ACTIVE_SCHEME_REGISTER"] = SPECT_CNTRL_ACTIVE_SCHEME_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_ACTIVE_SCHEME_REGISTER",c_uint,0,1.0,"rw"))
registerByName["SPECT_CNTRL_NEXT_SCHEME_REGISTER"] = SPECT_CNTRL_NEXT_SCHEME_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_NEXT_SCHEME_REGISTER",c_uint,0,1.0,"rw"))
registerByName["SPECT_CNTRL_SCHEME_ITER_REGISTER"] = SPECT_CNTRL_SCHEME_ITER_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_SCHEME_ITER_REGISTER",c_uint,0,1.0,"r"))
registerByName["SPECT_CNTRL_SCHEME_ROW_REGISTER"] = SPECT_CNTRL_SCHEME_ROW_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_SCHEME_ROW_REGISTER",c_uint,0,1.0,"r"))
registerByName["SPECT_CNTRL_DWELL_COUNT_REGISTER"] = SPECT_CNTRL_DWELL_COUNT_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_DWELL_COUNT_REGISTER",c_uint,0,1.0,"r"))
registerByName["SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER"] = SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER",c_uint,1,1.0,"rw"))
registerByName["SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER"] = SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER",c_uint,1,1.0,"rw"))
registerByName["SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER"] = SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER",c_uint,1,1.0,"rw"))
registerByName["VIRTUAL_LASER_REGISTER"] = VIRTUAL_LASER_REGISTER
registerInfo.append(RegInfo("VIRTUAL_LASER_REGISTER",VIRTUAL_LASER_Type,0,1.0,"rw"))
registerByName["VALVE_CNTRL_STATE_REGISTER"] = VALVE_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_STATE_REGISTER",VALVE_CNTRL_StateType,0,1.0,"rw"))
registerByName["VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER"] = VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_INLET_VALVE_REGISTER"] = VALVE_CNTRL_INLET_VALVE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_REGISTER",c_float,0,1.0,"rw"))
registerByName["VALVE_CNTRL_OUTLET_VALVE_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_REGISTER",c_float,0,1.0,"rw"))
registerByName["VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER"] = VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER"] = VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER"] = VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_INLET_VALVE_MIN_REGISTER"] = VALVE_CNTRL_INLET_VALVE_MIN_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_INLET_VALVE_MAX_REGISTER"] = VALVE_CNTRL_INLET_VALVE_MAX_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER"] = VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_THRESHOLD_STATE_REGISTER"] = VALVE_CNTRL_THRESHOLD_STATE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_THRESHOLD_STATE_REGISTER",VALVE_CNTRL_THRESHOLD_StateType,0,1.0,"rw"))
registerByName["VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER"] = VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER"] = VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER"] = VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER"] = VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER",c_float,1,1.0,"rw"))
registerByName["VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER"] = VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER",c_uint,1,1.0,"rw"))
registerByName["VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER"] = VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER",c_uint,1,1.0,"rw"))
registerByName["VALVE_CNTRL_SEQUENCE_STEP_REGISTER"] = VALVE_CNTRL_SEQUENCE_STEP_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_SEQUENCE_STEP_REGISTER",c_int,0,1.0,"rw"))
registerByName["SENTRY_UPPER_LIMIT_TRIPPED_REGISTER"] = SENTRY_UPPER_LIMIT_TRIPPED_REGISTER
registerInfo.append(RegInfo("SENTRY_UPPER_LIMIT_TRIPPED_REGISTER",c_uint,0,1.0,"r"))
registerByName["SENTRY_LOWER_LIMIT_TRIPPED_REGISTER"] = SENTRY_LOWER_LIMIT_TRIPPED_REGISTER
registerInfo.append(RegInfo("SENTRY_LOWER_LIMIT_TRIPPED_REGISTER",c_uint,0,1.0,"r"))
registerByName["SENTRY_LASER1_TEMPERATURE_MIN_REGISTER"] = SENTRY_LASER1_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER1_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER1_TEMPERATURE_MAX_REGISTER"] = SENTRY_LASER1_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER1_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER2_TEMPERATURE_MIN_REGISTER"] = SENTRY_LASER2_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER2_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER2_TEMPERATURE_MAX_REGISTER"] = SENTRY_LASER2_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER2_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER3_TEMPERATURE_MIN_REGISTER"] = SENTRY_LASER3_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER3_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER3_TEMPERATURE_MAX_REGISTER"] = SENTRY_LASER3_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER3_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER4_TEMPERATURE_MIN_REGISTER"] = SENTRY_LASER4_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER4_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER4_TEMPERATURE_MAX_REGISTER"] = SENTRY_LASER4_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER4_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_ETALON_TEMPERATURE_MIN_REGISTER"] = SENTRY_ETALON_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_ETALON_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_ETALON_TEMPERATURE_MAX_REGISTER"] = SENTRY_ETALON_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_ETALON_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER"] = SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER"] = SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER"] = SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER"] = SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER"] = SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER"] = SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER"] = SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER"] = SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_DAS_TEMPERATURE_MIN_REGISTER"] = SENTRY_DAS_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_DAS_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_DAS_TEMPERATURE_MAX_REGISTER"] = SENTRY_DAS_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_DAS_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER1_CURRENT_MIN_REGISTER"] = SENTRY_LASER1_CURRENT_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER1_CURRENT_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER1_CURRENT_MAX_REGISTER"] = SENTRY_LASER1_CURRENT_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER1_CURRENT_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER2_CURRENT_MIN_REGISTER"] = SENTRY_LASER2_CURRENT_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER2_CURRENT_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER2_CURRENT_MAX_REGISTER"] = SENTRY_LASER2_CURRENT_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER2_CURRENT_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER3_CURRENT_MIN_REGISTER"] = SENTRY_LASER3_CURRENT_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER3_CURRENT_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER3_CURRENT_MAX_REGISTER"] = SENTRY_LASER3_CURRENT_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER3_CURRENT_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER4_CURRENT_MIN_REGISTER"] = SENTRY_LASER4_CURRENT_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER4_CURRENT_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_LASER4_CURRENT_MAX_REGISTER"] = SENTRY_LASER4_CURRENT_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER4_CURRENT_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_CAVITY_PRESSURE_MIN_REGISTER"] = SENTRY_CAVITY_PRESSURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_CAVITY_PRESSURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_CAVITY_PRESSURE_MAX_REGISTER"] = SENTRY_CAVITY_PRESSURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_CAVITY_PRESSURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_AMBIENT_PRESSURE_MIN_REGISTER"] = SENTRY_AMBIENT_PRESSURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_AMBIENT_PRESSURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerByName["SENTRY_AMBIENT_PRESSURE_MAX_REGISTER"] = SENTRY_AMBIENT_PRESSURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_AMBIENT_PRESSURE_MAX_REGISTER",c_float,1,1.0,"rw"))

# FPGA block definitions

# Block KERNEL Kernel
KERNEL_MAGIC_CODE = 0 # Code indicating FPGA is programmed
KERNEL_FPGA_RESET = 1 # Used to reset Cypress FX2
KERNEL_FPGA_RESET_RESET_B = 0 # Reset Cypress FX2 and FPGA bit position
KERNEL_FPGA_RESET_RESET_W = 1 # Reset Cypress FX2 and FPGA bit width

KERNEL_DIAG_1 = 2 # DSP accessible register for diagnostics
KERNEL_INTRONIX_CLKSEL = 3 # 
KERNEL_INTRONIX_CLKSEL_DIVISOR_B = 0 # Intronix sampling rate bit position
KERNEL_INTRONIX_CLKSEL_DIVISOR_W = 5 # Intronix sampling rate bit width

KERNEL_INTRONIX_1 = 4 # 
KERNEL_INTRONIX_1_CHANNEL_B = 0 # Intronix display 1 channel bit position
KERNEL_INTRONIX_1_CHANNEL_W = 8 # Intronix display 1 channel bit width

KERNEL_INTRONIX_2 = 5 # 
KERNEL_INTRONIX_2_CHANNEL_B = 0 # Intronix display 2 channel bit position
KERNEL_INTRONIX_2_CHANNEL_W = 8 # Intronix display 2 channel bit width

KERNEL_INTRONIX_3 = 6 # 
KERNEL_INTRONIX_3_CHANNEL_B = 0 # Intronix display 3 channel bit position
KERNEL_INTRONIX_3_CHANNEL_W = 8 # Intronix display 3 channel bit width


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
RDSIM_OPTIONS = 0 # Options
RDSIM_OPTIONS_INPUT_SEL_B = 0 # Source of decay and tuner center parameters bit position
RDSIM_OPTIONS_INPUT_SEL_W = 1 # Source of decay and tuner center parameters bit width

RDSIM_TUNER_CENTER = 1 # Tuner value around which cavity fills
RDSIM_TUNER_WINDOW_HALF_WIDTH = 2 # Half-width of tuner window within which cavity fills
RDSIM_FILLING_RATE = 3 # Rate of increase of accumulator value during filling
RDSIM_DECAY = 4 # Exponential decay of accumulator when not filling
RDSIM_DECAY_IN_SHIFT = 5 # Bits to  right shift decay input
RDSIM_DECAY_IN_OFFSET = 6 # 
RDSIM_ACCUMULATOR = 7 # Simulated ringdown value

# Block LASERLOCKER Laser frequency locker
LASERLOCKER_CS = 0 # Control/Status register
LASERLOCKER_CS_RUN_B = 0 # Stop/Run bit position
LASERLOCKER_CS_RUN_W = 1 # Stop/Run bit width
LASERLOCKER_CS_CONT_B = 1 # Single/Continuous bit position
LASERLOCKER_CS_CONT_W = 1 # Single/Continuous bit width
LASERLOCKER_CS_PRBS_B = 2 # Generate PRBS bit position
LASERLOCKER_CS_PRBS_W = 1 # Generate PRBS bit width
LASERLOCKER_CS_ACC_EN_B = 3 # Enable fine current acc bit position
LASERLOCKER_CS_ACC_EN_W = 1 # Enable fine current acc bit width
LASERLOCKER_CS_SAMPLE_DARK_B = 4 # Sample dark currents bit position
LASERLOCKER_CS_SAMPLE_DARK_W = 1 # Sample dark currents bit width
LASERLOCKER_CS_ADC_STROBE_B = 5 # Load WLM ADC values bit position
LASERLOCKER_CS_ADC_STROBE_W = 1 # Load WLM ADC values bit width
LASERLOCKER_CS_TUNING_OFFSET_SEL_B = 6 # Tuner offset source bit position
LASERLOCKER_CS_TUNING_OFFSET_SEL_W = 1 # Tuner offset source bit width
LASERLOCKER_CS_LASER_FREQ_OK_B = 7 # Laser frequency in window bit position
LASERLOCKER_CS_LASER_FREQ_OK_W = 1 # Laser frequency in window bit width
LASERLOCKER_CS_CURRENT_OK_B = 8 # Fine current calculation bit position
LASERLOCKER_CS_CURRENT_OK_W = 1 # Fine current calculation bit width

LASERLOCKER_ETA1 = 1 # Etalon 1 reading
LASERLOCKER_REF1 = 2 # Reference 1 reading
LASERLOCKER_ETA2 = 3 # Etalon 2 reading
LASERLOCKER_REF2 = 4 # Reference 2 reading
LASERLOCKER_ETA1_DARK = 5 # Etalon 1 dark reading
LASERLOCKER_REF1_DARK = 6 # Reference 1 dark reading
LASERLOCKER_ETA2_DARK = 7 # Etalon 2 dark reading
LASERLOCKER_REF2_DARK = 8 # Reference 2 dark reading
LASERLOCKER_ETA1_OFFSET = 9 # Etalon 1 offset
LASERLOCKER_REF1_OFFSET = 10 # Reference 1 offset
LASERLOCKER_ETA2_OFFSET = 11 # Etalon 2 offset
LASERLOCKER_REF2_OFFSET = 12 # Reference 2 offset
LASERLOCKER_RATIO1 = 13 # Ratio 1
LASERLOCKER_RATIO2 = 14 # Ratio 2
LASERLOCKER_RATIO1_CENTER = 15 # Ratio 1 ellipse center
LASERLOCKER_RATIO1_MULTIPLIER = 16 # Ratio 1 multiplier
LASERLOCKER_RATIO2_CENTER = 17 # Ratio 2 ellipse center
LASERLOCKER_RATIO2_MULTIPLIER = 18 # Ratio 2 multiplier
LASERLOCKER_TUNING_OFFSET = 19 # Error offset to shift frequency
LASERLOCKER_LOCK_ERROR = 20 # Locker loop error
LASERLOCKER_WM_LOCK_WINDOW = 21 # Lock window
LASERLOCKER_WM_INT_GAIN = 22 # Locker integral gain
LASERLOCKER_WM_PROP_GAIN = 23 # Locker proportional gain
LASERLOCKER_WM_DERIV_GAIN = 24 # Locker derivative gain
LASERLOCKER_FINE_CURRENT = 25 # Fine laser current
LASERLOCKER_CYCLE_COUNTER = 26 # Cycle counter

# Block RDMAN Ringdown manager
RDMAN_CONTROL = 0 # Control register
RDMAN_CONTROL_RUN_B = 0 # Stop/Run bit position
RDMAN_CONTROL_RUN_W = 1 # Stop/Run bit width
RDMAN_CONTROL_CONT_B = 1 # Single/Continuous bit position
RDMAN_CONTROL_CONT_W = 1 # Single/Continuous bit width
RDMAN_CONTROL_START_RD_B = 2 # Start ringdown cycle bit position
RDMAN_CONTROL_START_RD_W = 1 # Start ringdown cycle bit width
RDMAN_CONTROL_ABORT_RD_B = 3 # Abort ringdown bit position
RDMAN_CONTROL_ABORT_RD_W = 1 # Abort ringdown bit width
RDMAN_CONTROL_RESET_RDMAN_B = 4 # Reset ringdown manager bit position
RDMAN_CONTROL_RESET_RDMAN_W = 1 # Reset ringdown manager bit width
RDMAN_CONTROL_BANK0_CLEAR_B = 5 # Mark bank 0 available for write bit position
RDMAN_CONTROL_BANK0_CLEAR_W = 1 # Mark bank 0 available for write bit width
RDMAN_CONTROL_BANK1_CLEAR_B = 6 # Mark bank 1 available for write bit position
RDMAN_CONTROL_BANK1_CLEAR_W = 1 # Mark bank 1 available for write bit width
RDMAN_CONTROL_RD_IRQ_ACK_B = 7 # Acknowledge ring-down interrupt bit position
RDMAN_CONTROL_RD_IRQ_ACK_W = 1 # Acknowledge ring-down interrupt bit width
RDMAN_CONTROL_ACQ_DONE_ACK_B = 8 # Acknowledge data acquired interrupt bit position
RDMAN_CONTROL_ACQ_DONE_ACK_W = 1 # Acknowledge data acquired interrupt bit width
RDMAN_CONTROL_RAMP_DITHER_B = 9 # Tuner waveform mode bit position
RDMAN_CONTROL_RAMP_DITHER_W = 1 # Tuner waveform mode bit width

RDMAN_STATUS = 1 # Status register
RDMAN_STATUS_SHUTDOWN_B = 0 # Indicates shutdown of optical injection bit position
RDMAN_STATUS_SHUTDOWN_W = 1 # Indicates shutdown of optical injection bit width
RDMAN_STATUS_RD_IRQ_B = 1 # Ring down interrupt occured bit position
RDMAN_STATUS_RD_IRQ_W = 1 # Ring down interrupt occured bit width
RDMAN_STATUS_ACQ_DONE_B = 2 # Data acquired interrupt occured bit position
RDMAN_STATUS_ACQ_DONE_W = 1 # Data acquired interrupt occured bit width
RDMAN_STATUS_BANK_B = 3 # Active bank for data acquisition bit position
RDMAN_STATUS_BANK_W = 1 # Active bank for data acquisition bit width
RDMAN_STATUS_BANK0_IN_USE_B = 4 # Bank 0 memory in use bit position
RDMAN_STATUS_BANK0_IN_USE_W = 1 # Bank 0 memory in use bit width
RDMAN_STATUS_BANK1_IN_USE_B = 5 # Bank 1 memory in use bit position
RDMAN_STATUS_BANK1_IN_USE_W = 1 # Bank 1 memory in use bit width
RDMAN_STATUS_LAPPED_B = 6 # Metadata counter lapped bit position
RDMAN_STATUS_LAPPED_W = 1 # Metadata counter lapped bit width
RDMAN_STATUS_LASER_FREQ_LOCKED_B = 7 # Laser frequency locked bit position
RDMAN_STATUS_LASER_FREQ_LOCKED_W = 1 # Laser frequency locked bit width
RDMAN_STATUS_TIMEOUT_B = 8 # Timeout without ring-down bit position
RDMAN_STATUS_TIMEOUT_W = 1 # Timeout without ring-down bit width
RDMAN_STATUS_ABORTED_B = 9 # Ring-down aborted bit position
RDMAN_STATUS_ABORTED_W = 1 # Ring-down aborted bit width
RDMAN_STATUS_BUSY_B = 10 # Ringdown Cycle State bit position
RDMAN_STATUS_BUSY_W = 1 # Ringdown Cycle State bit width

RDMAN_OPTIONS = 2 # Options register
RDMAN_OPTIONS_LOCK_ENABLE_B = 0 # Enable frequency locking bit position
RDMAN_OPTIONS_LOCK_ENABLE_W = 1 # Enable frequency locking bit width
RDMAN_OPTIONS_UP_SLOPE_ENABLE_B = 1 # Allow ring-down on positive tuner slope bit position
RDMAN_OPTIONS_UP_SLOPE_ENABLE_W = 1 # Allow ring-down on positive tuner slope bit width
RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B = 2 # Allow ring-down on negative tuner slope bit position
RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_W = 1 # Allow ring-down on negative tuner slope bit width
RDMAN_OPTIONS_DITHER_ENABLE_B = 3 # Allow transition to dither mode bit position
RDMAN_OPTIONS_DITHER_ENABLE_W = 1 # Allow transition to dither mode bit width

RDMAN_PARAM0 = 3 # Parameter 0 register
RDMAN_PARAM1 = 4 # Parameter 1 register
RDMAN_PARAM2 = 5 # Parameter 2 register
RDMAN_PARAM3 = 6 # Parameter 3 register
RDMAN_PARAM4 = 7 # Parameter 4 register
RDMAN_PARAM5 = 8 # Parameter 5 register
RDMAN_PARAM6 = 9 # Parameter 6 register
RDMAN_PARAM7 = 10 # Parameter 7 register
RDMAN_PARAM8 = 11 # Parameter 8 register
RDMAN_PARAM9 = 12 # Parameter 9 register
RDMAN_DATA_ADDRCNTR = 13 # Counter for ring-down data
RDMAN_METADATA_ADDRCNTR = 14 # Counter for ring-down metadata
RDMAN_PARAM_ADDRCNTR = 15 # Counter for parameter data
RDMAN_DIVISOR = 16 # Ring-down data counter rate divisor
RDMAN_NUM_SAMP = 17 # Number of samples to collect for ring-down waveform
RDMAN_THRESHOLD = 18 # Ring-down threshold
RDMAN_LOCK_DURATION = 19 # Duration (us) for laser frequency to be locked before ring-down is allowed
RDMAN_PRECONTROL_DURATION = 20 # Duration (us) for laser current to be at nominal value before frequency locking is enabled
RDMAN_TIMEOUT_DURATION = 21 # Duration (ms) within which ring-down must occur to be valid
RDMAN_TUNER_AT_RINGDOWN = 22 # Value of tuner at ring-down
RDMAN_METADATA_ADDR_AT_RINGDOWN = 23 # Metadata address at ring-down

# Block TWGEN Tuner waveform generator
TWGEN_ACC = 0 # Accumulator
TWGEN_CS = 1 # Control/Status Register
TWGEN_CS_RUN_B = 0 # Stop/Run bit position
TWGEN_CS_RUN_W = 1 # Stop/Run bit width
TWGEN_CS_CONT_B = 1 # Single/Continuous bit position
TWGEN_CS_CONT_W = 1 # Single/Continuous bit width
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
INJECT_CONTROL_LASER_SELECT_B = 1 # Laser under automatic control bit position
INJECT_CONTROL_LASER_SELECT_W = 2 # Laser under automatic control bit width
INJECT_CONTROL_LASER_CURRENT_ENABLE_B = 3 # Laser current enable bit position
INJECT_CONTROL_LASER_CURRENT_ENABLE_W = 4 # Laser current enable bit width
INJECT_CONTROL_LASER1_CURRENT_ENABLE_B = 3 # Laser 1 current source bit position
INJECT_CONTROL_LASER1_CURRENT_ENABLE_W = 1 # Laser 1 current source bit width
INJECT_CONTROL_LASER2_CURRENT_ENABLE_B = 4 # Laser 2 current source bit position
INJECT_CONTROL_LASER2_CURRENT_ENABLE_W = 1 # Laser 2 current source bit width
INJECT_CONTROL_LASER3_CURRENT_ENABLE_B = 5 # Laser 3 current source bit position
INJECT_CONTROL_LASER3_CURRENT_ENABLE_W = 1 # Laser 3 current source bit width
INJECT_CONTROL_LASER4_CURRENT_ENABLE_B = 6 # Laser 4 current source bit position
INJECT_CONTROL_LASER4_CURRENT_ENABLE_W = 1 # Laser 4 current source bit width
INJECT_CONTROL_MANUAL_LASER_ENABLE_B = 7 # Deasserts short across laser in manual mode bit position
INJECT_CONTROL_MANUAL_LASER_ENABLE_W = 4 # Deasserts short across laser in manual mode bit width
INJECT_CONTROL_MANUAL_LASER1_ENABLE_B = 7 # Laser 1 current (in manual mode) bit position
INJECT_CONTROL_MANUAL_LASER1_ENABLE_W = 1 # Laser 1 current (in manual mode) bit width
INJECT_CONTROL_MANUAL_LASER2_ENABLE_B = 8 # Laser 2 current (in manual mode) bit position
INJECT_CONTROL_MANUAL_LASER2_ENABLE_W = 1 # Laser 2 current (in manual mode) bit width
INJECT_CONTROL_MANUAL_LASER3_ENABLE_B = 9 # Laser 3 current (in manual mode) bit position
INJECT_CONTROL_MANUAL_LASER3_ENABLE_W = 1 # Laser 3 current (in manual mode) bit width
INJECT_CONTROL_MANUAL_LASER4_ENABLE_B = 10 # Laser 4 current (in manual mode) bit position
INJECT_CONTROL_MANUAL_LASER4_ENABLE_W = 1 # Laser 4 current (in manual mode) bit width
INJECT_CONTROL_MANUAL_SOA_ENABLE_B = 11 # SOA current (in manual mode) bit position
INJECT_CONTROL_MANUAL_SOA_ENABLE_W = 1 # SOA current (in manual mode) bit width
INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B = 12 # Enables laser shutdown (in automatic mode) bit position
INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W = 1 # Enables laser shutdown (in automatic mode) bit width
INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B = 13 # Enables SOA shutdown (in automatic mode) bit position
INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W = 1 # Enables SOA shutdown (in automatic mode) bit width

INJECT_LASER1_COARSE_CURRENT = 1 # Sets coarse current for laser 1
INJECT_LASER2_COARSE_CURRENT = 2 # Sets coarse current for laser 2
INJECT_LASER3_COARSE_CURRENT = 3 # Sets coarse current for laser 3
INJECT_LASER4_COARSE_CURRENT = 4 # Sets coarse current for laser 4
INJECT_LASER1_FINE_CURRENT = 5 # Sets fine current for laser 1
INJECT_LASER2_FINE_CURRENT = 6 # Sets fine current for laser 2
INJECT_LASER3_FINE_CURRENT = 7 # Sets fine current for laser 3
INJECT_LASER4_FINE_CURRENT = 8 # Sets fine current for laser 4

# Block WLMSIM Wavelength monitor simulator
WLMSIM_OPTIONS = 0 # Options
WLMSIM_OPTIONS_INPUT_SEL_B = 0 # Input select bit position
WLMSIM_OPTIONS_INPUT_SEL_W = 1 # Input select bit width

WLMSIM_Z0 = 1 # Phase angle
WLMSIM_RFAC = 2 # Reflectivity factor
WLMSIM_WFAC = 3 # Width factor of simulated spectrum
WLMSIM_ETA1 = 4 # Etalon 1
WLMSIM_REF1 = 5 # Reference 1
WLMSIM_ETA2 = 6 # Etalon 2
WLMSIM_REF2 = 7 # Reference 2

# Block DYNAMICPWM Dynamic PWM for proportional valves
DYNAMICPWM_CS = 0 # Control/Status
DYNAMICPWM_CS_RUN_B = 0 # Stop/Run bit position
DYNAMICPWM_CS_RUN_W = 1 # Stop/Run bit width
DYNAMICPWM_CS_CONT_B = 1 # Single/Continuous bit position
DYNAMICPWM_CS_CONT_W = 1 # Single/Continuous bit width
DYNAMICPWM_CS_PWM_OUT_B = 2 # PWM output bit position
DYNAMICPWM_CS_PWM_OUT_W = 1 # PWM output bit width

DYNAMICPWM_DELTA = 1 # Pulse width change per update

# FPGA map indices
FPGA_KERNEL = 0 # Kernel registers
FPGA_PWM_LASER1 = 7 # Laser 1 TEC pulse width modulator registers
FPGA_PWM_LASER2 = 9 # Laser 2 TEC pulse width modulator registers
FPGA_PWM_LASER3 = 11 # Laser 3 TEC pulse width modulator registers
FPGA_PWM_LASER4 = 13 # Laser 4 TEC pulse width modulator registers
FPGA_RDSIM = 15 # Ringdown simulator registers
FPGA_LASERLOCKER = 23 # Laser frequency locker registers
FPGA_RDMAN = 50 # Ringdown manager registers
FPGA_TWGEN = 74 # Tuner waveform generator
FPGA_INJECT = 82 # Optical Injection Subsystem
FPGA_WLMSIM = 91 # WLM Simulator
FPGA_DYNAMICPWM_INLET = 99 # Inlet proportional valve dynamic PWM
FPGA_DYNAMICPWM_OUTLET = 101 # Outlet proportional valve dynamic PWM

persistent_fpga_registers = []
persistent_fpga_registers.append((u'FPGA_KERNEL', [u'KERNEL_INTRONIX_CLKSEL', u'KERNEL_INTRONIX_1', u'KERNEL_INTRONIX_2', u'KERNEL_INTRONIX_3']))
persistent_fpga_registers.append((u'FPGA_RDSIM', [u'RDSIM_OPTIONS', u'RDSIM_TUNER_CENTER', u'RDSIM_TUNER_WINDOW_HALF_WIDTH', u'RDSIM_FILLING_RATE', u'RDSIM_DECAY', u'RDSIM_DECAY_IN_SHIFT', u'RDSIM_DECAY_IN_OFFSET']))
persistent_fpga_registers.append((u'FPGA_LASERLOCKER', [u'LASERLOCKER_ETA1_OFFSET', u'LASERLOCKER_REF1_OFFSET', u'LASERLOCKER_ETA2_OFFSET', u'LASERLOCKER_REF2_OFFSET', u'LASERLOCKER_RATIO1_CENTER', u'LASERLOCKER_RATIO1_MULTIPLIER', u'LASERLOCKER_RATIO2_CENTER', u'LASERLOCKER_RATIO2_MULTIPLIER', u'LASERLOCKER_TUNING_OFFSET', u'LASERLOCKER_WM_LOCK_WINDOW', u'LASERLOCKER_WM_INT_GAIN', u'LASERLOCKER_WM_PROP_GAIN', u'LASERLOCKER_WM_DERIV_GAIN']))
persistent_fpga_registers.append((u'FPGA_RDMAN', [u'RDMAN_OPTIONS', u'RDMAN_DIVISOR', u'RDMAN_NUM_SAMP', u'RDMAN_THRESHOLD', u'RDMAN_LOCK_DURATION', u'RDMAN_PRECONTROL_DURATION', u'RDMAN_TIMEOUT_DURATION']))
persistent_fpga_registers.append((u'FPGA_TWGEN', [u'TWGEN_SLOPE_DOWN', u'TWGEN_SLOPE_UP', u'TWGEN_SWEEP_LOW', u'TWGEN_SWEEP_HIGH', u'TWGEN_WINDOW_LOW', u'TWGEN_WINDOW_HIGH']))
persistent_fpga_registers.append((u'FPGA_INJECT', [u'INJECT_CONTROL']))
persistent_fpga_registers.append((u'FPGA_WLMSIM', [u'WLMSIM_OPTIONS', u'WLMSIM_RFAC', u'WLMSIM_WFAC']))
persistent_fpga_registers.append((u'FPGA_DYNAMICPWM_INLET', [u'DYNAMICPWM_DELTA']))
persistent_fpga_registers.append((u'FPGA_DYNAMICPWM_OUTLET', [u'DYNAMICPWM_DELTA']))

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
ACTION_STREAM_FPGA_REGISTER = 7
ACTION_RESISTANCE_TO_TEMPERATURE = 8
ACTION_TEMP_CNTRL_SET_COMMAND = 9
ACTION_APPLY_PID_STEP = 10
ACTION_TEMP_CNTRL_LASER1_INIT = 11
ACTION_TEMP_CNTRL_LASER1_STEP = 12
ACTION_TEMP_CNTRL_LASER2_INIT = 13
ACTION_TEMP_CNTRL_LASER2_STEP = 14
ACTION_TEMP_CNTRL_LASER3_INIT = 15
ACTION_TEMP_CNTRL_LASER3_STEP = 16
ACTION_TEMP_CNTRL_LASER4_INIT = 17
ACTION_TEMP_CNTRL_LASER4_STEP = 18
ACTION_FLOAT_REGISTER_TO_FPGA = 19
ACTION_FPGA_TO_FLOAT_REGISTER = 20
ACTION_INT_TO_FPGA = 21
ACTION_CURRENT_CNTRL_LASER1_INIT = 22
ACTION_CURRENT_CNTRL_LASER1_STEP = 23
ACTION_CURRENT_CNTRL_LASER2_INIT = 24
ACTION_CURRENT_CNTRL_LASER2_STEP = 25
ACTION_CURRENT_CNTRL_LASER3_INIT = 26
ACTION_CURRENT_CNTRL_LASER3_STEP = 27
ACTION_CURRENT_CNTRL_LASER4_INIT = 28
ACTION_CURRENT_CNTRL_LASER4_STEP = 29
ACTION_TEMP_CNTRL_WARM_BOX_INIT = 30
ACTION_TEMP_CNTRL_WARM_BOX_STEP = 31
ACTION_TEMP_CNTRL_CAVITY_INIT = 32
ACTION_TEMP_CNTRL_CAVITY_STEP = 33
ACTION_HEATER_CNTRL_INIT = 34
ACTION_HEATER_CNTRL_STEP = 35
ACTION_TUNER_CNTRL_INIT = 36
ACTION_TUNER_CNTRL_STEP = 37
ACTION_SPECTRUM_CNTRL_INIT = 38
ACTION_SPECTRUM_CNTRL_STEP = 39
ACTION_ENV_CHECKER = 40
ACTION_WB_INV_CACHE = 41
ACTION_WB_CACHE = 42
ACTION_SCHEDULER_HEARTBEAT = 43
ACTION_SENTRY_INIT = 44
ACTION_VALVE_CNTRL_INIT = 45
ACTION_VALVE_CNTRL_STEP = 46
ACTION_PULSE_GENERATOR = 47
ACTION_FILTER = 48
ACTION_DS1631_READTEMP = 49
ACTION_LASER_TEC_IMON = 50
ACTION_READ_LASER_TEC_MONITORS = 51
ACTION_READ_LASER_THERMISTOR_RESISTANCE = 52
ACTION_READ_LASER_CURRENT = 53


# Parameter form definitions

parameter_forms = []

# Form: System Configuration Parameters

__p = []

__p.append(('dsp','uint32',SCHEDULER_CONTROL_REGISTER,'Scheduler enable','','%d',1,1))
__p.append(('dsp','uint32',RD_IRQ_COUNT_REGISTER,'Ringdown interrupt count','','%d',1,0))
__p.append(('dsp','uint32',ACQ_DONE_COUNT_REGISTER,'Acquisition done interrupt count','','%d',1,0))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_FPGA_RESET,[(1, u'Reset Cypress FX2 and FPGA', [(0, u'Idle'), (1, u'Reset')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_INTRONIX_CLKSEL,[(31, u'Intronix sampling rate', [(0, u'20 ns'), (1, u'40 ns'), (2, u'80 ns'), (3, u'160 ns'), (4, u'320 ns'), (5, u'640 ns'), (6, u'1.28 us'), (7, u'2.56 us'), (8, u'5.12 us'), (9, u'10.24 us'), (10, u'20.48 us'), (11, u'40.96 us'), (12, u'81.92 us'), (13, u'163.8 us'), (14, u'327.7 us'), (15, u'655.4 us'), (16, u'1.311 ms'), (17, u'2.621 ms'), (18, u'5.243 ms'), (19, u'10.49 ms'), (20, u'20.97 ms'), (21, u'41.94 ms'), (22, u'83.39 ms'), (23, u'167.8 ms'), (24, u'335.5 ms'), (25, u'671.1 ms'), (26, u'1.342 s'), (27, u'2.684 s'), (28, u'5.368 s')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_INTRONIX_1,[(255, u'Intronix display 1 channel', [(0, u'Tuner waveform (LS)'), (1, u'Tuner waveform (MS)'), (2, u'Ringdown ADC waveform (LS)'), (3, u'Ringdown ADC waveform (MS)'), (4, u'Ringdown simulator waveform (LS)'), (5, u'Ringdown simulator waveform (MS)'), (6, u'Laser fine current (LS)'), (7, u'Laser fine current (MS)'), (8, u'Locker error (LS)'), (9, u'Locker error (MS)'), (10, u'Ratio 1 (LS)'), (11, u'Ratio 1 (MS)'), (12, u'Ratio 2 (LS)'), (13, u'Ratio 2 (MS)')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_INTRONIX_2,[(255, u'Intronix display 2 channel', [(0, u'Tuner waveform (LS)'), (1, u'Tuner waveform (MS)'), (2, u'Ringdown ADC waveform (LS)'), (3, u'Ringdown ADC waveform (MS)'), (4, u'Ringdown simulator waveform (LS)'), (5, u'Ringdown simulator waveform (MS)'), (6, u'Laser fine current (LS)'), (7, u'Laser fine current (MS)'), (8, u'Locker error (LS)'), (9, u'Locker error (MS)'), (10, u'Ratio 1 (LS)'), (11, u'Ratio 1 (MS)'), (12, u'Ratio 2 (LS)'), (13, u'Ratio 2 (MS)')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_INTRONIX_3,[(255, u'Intronix display 3 channel', [(0, u'Tuner waveform (LS)'), (1, u'Tuner waveform (MS)'), (2, u'Ringdown ADC waveform (LS)'), (3, u'Ringdown ADC waveform (MS)'), (4, u'Ringdown simulator waveform (LS)'), (5, u'Ringdown simulator waveform (MS)'), (6, u'Laser fine current (LS)'), (7, u'Laser fine current (MS)'), (8, u'Locker error (LS)'), (9, u'Locker error (MS)'), (10, u'Ratio 1 (LS)'), (11, u'Ratio 1 (MS)'), (12, u'Ratio 2 (LS)'), (13, u'Ratio 2 (MS)')])],None,None,1,1))
parameter_forms.append(('System Configuration Parameters',__p))

# Form: Laser 1 Parameters

__p = []

__p.append(('dsp','choices',LASER1_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),(TEMP_CNTRL_AutomaticState,"Automatic Control"),],1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('dsp','float',LASER1_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('dsp','uint32',LASER1_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('dsp','float',LASER1_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('dsp','float',LASER1_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('dsp','float',LASER1_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
__p.append(('dsp','choices',LASER1_CURRENT_CNTRL_STATE_REGISTER,'Current Controller Mode','',[(LASER_CURRENT_CNTRL_DisabledState,"Controller Disabled"),(LASER_CURRENT_CNTRL_AutomaticState,"Automatic Control"),(LASER_CURRENT_CNTRL_SweepingState,"Continuous Sweeping"),(LASER_CURRENT_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('dsp','float',LASER1_MANUAL_COARSE_CURRENT_REGISTER,'Manual Coarse Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER1_MANUAL_FINE_CURRENT_REGISTER,'Manual Fine Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER1_CURRENT_SWEEP_MIN_REGISTER,'Current Sweep Minimum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER1_CURRENT_SWEEP_MAX_REGISTER,'Current Sweep Maximum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER1_CURRENT_SWEEP_INCR_REGISTER,'Current Sweep Increment','digU/sample','%.1f',1,1))
parameter_forms.append(('Laser 1 Parameters',__p))

# Form: Laser 2 Parameters

__p = []

__p.append(('dsp','choices',LASER2_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),(TEMP_CNTRL_AutomaticState,"Automatic Control"),],1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('dsp','float',LASER2_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('dsp','uint32',LASER2_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('dsp','float',LASER2_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('dsp','float',LASER2_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('dsp','float',LASER2_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
__p.append(('dsp','choices',LASER2_CURRENT_CNTRL_STATE_REGISTER,'Current Controller Mode','',[(LASER_CURRENT_CNTRL_DisabledState,"Controller Disabled"),(LASER_CURRENT_CNTRL_AutomaticState,"Automatic Control"),(LASER_CURRENT_CNTRL_SweepingState,"Continuous Sweeping"),(LASER_CURRENT_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('dsp','float',LASER2_MANUAL_COARSE_CURRENT_REGISTER,'Manual Coarse Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER2_MANUAL_FINE_CURRENT_REGISTER,'Manual Fine Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER2_CURRENT_SWEEP_MIN_REGISTER,'Current Sweep Minimum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER2_CURRENT_SWEEP_MAX_REGISTER,'Current Sweep Maximum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER2_CURRENT_SWEEP_INCR_REGISTER,'Current Sweep Increment','digU/sample','%.1f',1,1))
parameter_forms.append(('Laser 2 Parameters',__p))

# Form: Laser 3 Parameters

__p = []

__p.append(('dsp','choices',LASER3_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),(TEMP_CNTRL_AutomaticState,"Automatic Control"),],1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('dsp','float',LASER3_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('dsp','uint32',LASER3_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('dsp','float',LASER3_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('dsp','float',LASER3_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('dsp','float',LASER3_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
__p.append(('dsp','choices',LASER3_CURRENT_CNTRL_STATE_REGISTER,'Current Controller Mode','',[(LASER_CURRENT_CNTRL_DisabledState,"Controller Disabled"),(LASER_CURRENT_CNTRL_AutomaticState,"Automatic Control"),(LASER_CURRENT_CNTRL_SweepingState,"Continuous Sweeping"),(LASER_CURRENT_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('dsp','float',LASER3_MANUAL_COARSE_CURRENT_REGISTER,'Manual Coarse Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER3_MANUAL_FINE_CURRENT_REGISTER,'Manual Fine Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER3_CURRENT_SWEEP_MIN_REGISTER,'Current Sweep Minimum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER3_CURRENT_SWEEP_MAX_REGISTER,'Current Sweep Maximum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER3_CURRENT_SWEEP_INCR_REGISTER,'Current Sweep Increment','digU/sample','%.1f',1,1))
parameter_forms.append(('Laser 3 Parameters',__p))

# Form: Laser 4 Parameters

__p = []

__p.append(('dsp','choices',LASER4_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),(TEMP_CNTRL_AutomaticState,"Automatic Control"),],1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('dsp','float',LASER4_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('dsp','uint32',LASER4_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('dsp','float',LASER4_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('dsp','float',LASER4_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('dsp','float',LASER4_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
__p.append(('dsp','choices',LASER4_CURRENT_CNTRL_STATE_REGISTER,'Current Controller Mode','',[(LASER_CURRENT_CNTRL_DisabledState,"Controller Disabled"),(LASER_CURRENT_CNTRL_AutomaticState,"Automatic Control"),(LASER_CURRENT_CNTRL_SweepingState,"Continuous Sweeping"),(LASER_CURRENT_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('dsp','float',LASER4_MANUAL_COARSE_CURRENT_REGISTER,'Manual Coarse Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER4_MANUAL_FINE_CURRENT_REGISTER,'Manual Fine Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER4_CURRENT_SWEEP_MIN_REGISTER,'Current Sweep Minimum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER4_CURRENT_SWEEP_MAX_REGISTER,'Current Sweep Maximum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER4_CURRENT_SWEEP_INCR_REGISTER,'Current Sweep Increment','digU/sample','%.1f',1,1))
parameter_forms.append(('Laser 4 Parameters',__p))

# Form: Warm Box Temperature Parameters

__p = []

__p.append(('dsp','choices',WARM_BOX_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),(TEMP_CNTRL_AutomaticState,"Automatic Control"),],1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('dsp','float',WARM_BOX_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('dsp','uint32',WARM_BOX_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('dsp','float',WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('dsp','float',WARM_BOX_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('dsp','float',WARM_BOX_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
__p.append(('dsp','float',WARM_BOX_MAX_HEATSINK_TEMP_REGISTER,'Warm Box heatsink maximum temperature','degC','%.3f',1,1))
parameter_forms.append(('Warm Box Temperature Parameters',__p))

# Form: Cavity Temperature Parameters

__p = []

__p.append(('dsp','choices',CAVITY_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),(TEMP_CNTRL_AutomaticState,"Automatic Control"),],1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Setpoint','degC','%.3f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.4f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_AMIN_REGISTER,'Minimum TEC value (Amin)','','%.0f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_AMAX_REGISTER,'Maximum TEC value (Amax)','','%.0f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('dsp','float',CAVITY_TEMP_CNTRL_FFWD_REGISTER,'DAS temperature feed forward coefficient','','%.3f',1,1))
__p.append(('dsp','uint32',CAVITY_TEC_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('dsp','float',CAVITY_TEC_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('dsp','float',CAVITY_TEC_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('dsp','float',CAVITY_MANUAL_TEC_REGISTER,'Manual TEC Value','digU','%.0f',1,1))
__p.append(('dsp','float',CAVITY_MAX_HEATSINK_TEMP_REGISTER,'Hot Box heatsink maximum temperature','degC','%.3f',1,1))
__p.append(('dsp','choices',HEATER_CNTRL_STATE_REGISTER,'Heater Controller Mode','',[(HEATER_CNTRL_DisabledState,"Controller Disabled"),(HEATER_CNTRL_EnabledState,"Controller Enabled"),(HEATER_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('dsp','float',HEATER_CNTRL_GAIN_REGISTER,'Heater control gain','','%.0f',1,1))
__p.append(('dsp','float',HEATER_CNTRL_QUANTIZE_REGISTER,'Heater control quantization','','%.0f',1,1))
__p.append(('dsp','float',HEATER_CNTRL_UBIAS_SLOPE_REGISTER,'Heater control UBias slope','','%.0f',1,1))
__p.append(('dsp','float',HEATER_CNTRL_UBIAS_OFFSET_REGISTER,'Heater control UBias offset','','%.0f',1,1))
__p.append(('dsp','float',HEATER_CNTRL_MARK_MIN_REGISTER,'Heater minimum mark','','%.0f',1,1))
__p.append(('dsp','float',HEATER_CNTRL_MARK_MAX_REGISTER,'Heater maximum mark','','%.0f',1,1))
__p.append(('dsp','float',HEATER_CNTRL_MANUAL_MARK_REGISTER,'Heater manual mode mark','','%.0f',1,1))
parameter_forms.append(('Cavity Temperature Parameters',__p))

# Form: Sample Handling Parameters

__p = []

__p.append(('dsp','choices',VALVE_CNTRL_STATE_REGISTER,'Valve Controller Mode','',[(VALVE_CNTRL_DisabledState,"Disabled"),(VALVE_CNTRL_OutletControlState,"Outlet control"),(VALVE_CNTRL_InletControlState,"Inlet control"),(VALVE_CNTRL_ManualControlState,"Manual control"),],1,1))
__p.append(('dsp','float',VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER,'Cavity pressure setpoint','torr','%.2f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_REGISTER,'Inlet valve value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_REGISTER,'Outlet valve value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER,'Cavity pressure maximum rate of change','torr/s','%.3f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER,'Inlet valve gain 1','','%.2f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER,'Inlet valve gain 2','','%.2f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_MIN_REGISTER,'Inlet valve minimum value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_MAX_REGISTER,'Inlet valve maximum value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER,'Inlet valve maximum change between samples','digU','%.1f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER,'Outlet valve gain 1','','%.2f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER,'Outlet valve gain 2','','%.2f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER,'Inlet valve minimum value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER,'Outlet valve maximum value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER,'Outlet valve maximum change between samples','digU','%.1f',1,1))
__p.append(('dsp','choices',VALVE_CNTRL_THRESHOLD_STATE_REGISTER,'Loss-based Triggering','',[(VALVE_CNTRL_THRESHOLD_DisabledState,"Disabled"),(VALVE_CNTRL_THRESHOLD_ArmedState,"Armed"),(VALVE_CNTRL_THRESHOLD_TriggeredState,"Triggered"),],1,1))
__p.append(('dsp','float',VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER,'Loss threshold for trigger','ppb/cm','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER,'Rate of change of loss for trigger','ppb/cm/sample','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER,'Inlet valve when triggered','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER,'Outlet valve when triggered','digU','%.0f',1,1))
__p.append(('dsp','uint32',VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER,'Bit mask to select solenoid valves affected by trigger','','$%X',1,1))
__p.append(('dsp','uint32',VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER,'Solenoid valve states when triggered','','$%X',1,1))
__p.append(('dsp','int32',VALVE_CNTRL_SEQUENCE_STEP_REGISTER,'Valve sequence step (-1 to disable)','','%d',1,1))
parameter_forms.append(('Sample Handling Parameters',__p))

# Form: Tuner Waveform Parameters

__p = []

__p.append(('fpga','mask',FPGA_TWGEN+TWGEN_CS,[(1, u'Stop/Run', [(0, u'Stop'), (1, u'Run')]), (2, u'Single/Continuous', [(0, u'Single'), (2, u'Continuous')]), (4, u'Reset generator', [(0, u'Idle'), (4, u'Reset')])],None,None,1,1))
__p.append(('fpga','uint16',FPGA_TWGEN+TWGEN_SWEEP_HIGH,'Tuner sweep higher limit','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_TWGEN+TWGEN_SWEEP_LOW,'Tuner sweep lower limit','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_TWGEN+TWGEN_WINDOW_HIGH,'Tuner window higher limit','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_TWGEN+TWGEN_WINDOW_LOW,'Tuner window lower limit','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_TWGEN+TWGEN_SLOPE_UP,'Tuner up slope','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_TWGEN+TWGEN_SLOPE_DOWN,'Tuner down slope','digU','%d',1,1))
__p.append(('dsp','float',TUNER_SWEEP_RAMP_HIGH_REGISTER,'Ramp mode upper sweep limit','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_SWEEP_RAMP_LOW_REGISTER,'Ramp mode lower sweep limit','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_WINDOW_RAMP_HIGH_REGISTER,'Ramp mode upper window limit','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_WINDOW_RAMP_LOW_REGISTER,'Ramp mode lower window limit','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER,'Dither mode upper sweep offset','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER,'Dither mode lower sweep offset','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER,'Dither mode upper window offset','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER,'Dither mode lower window offset','digU','%.0f',1,1))
parameter_forms.append(('Tuner Waveform Parameters',__p))

# Form: Optical Injection Parameters

__p = []

__p.append(('dsp','choices',VIRTUAL_LASER_REGISTER,'Virtual laser','',[(VIRTUAL_LASER_1,"Virtual laser 1"),(VIRTUAL_LASER_2,"Virtual laser 2"),(VIRTUAL_LASER_3,"Virtual laser 3"),(VIRTUAL_LASER_4,"Virtual laser 4"),(VIRTUAL_LASER_5,"Virtual laser 5"),(VIRTUAL_LASER_6,"Virtual laser 6"),(VIRTUAL_LASER_7,"Virtual laser 7"),(VIRTUAL_LASER_8,"Virtual laser 8"),],1,1))
__p.append(('fpga','mask',FPGA_INJECT+INJECT_CONTROL,[(1, u'Manual/Automatic mode', [(0, u'Manual'), (1, u'Automatic')]), (6, u'Laser under automatic control', [(0, u'Laser 1'), (2, u'Laser 2'), (4, u'Laser 3'), (6, u'Laser 4')]), (120, u'Laser current enable', []), (8, u'Laser 1 current source', [(0, u'Disabled'), (8, u'Enabled')]), (16, u'Laser 2 current source', [(0, u'Disabled'), (16, u'Enabled')]), (32, u'Laser 3 current source', [(0, u'Disabled'), (32, u'Enabled')]), (64, u'Laser 4 current source', [(0, u'Disabled'), (64, u'Enabled')]), (1920, u'Deasserts short across laser in manual mode', []), (128, u'Laser 1 current (in manual mode)', [(0, u'Off'), (128, u'On')]), (256, u'Laser 2 current (in manual mode)', [(0, u'Off'), (256, u'On')]), (512, u'Laser 3 current (in manual mode)', [(0, u'Off'), (512, u'On')]), (1024, u'Laser 4 current (in manual mode)', [(0, u'Off'), (1024, u'On')]), (2048, u'SOA current (in manual mode)', [(0, u'Off'), (2048, u'On')]), (4096, u'Enables laser shutdown (in automatic mode)', [(0, u'Disabled'), (4096, u'Enabled')]), (8192, u'Enables SOA shutdown (in automatic mode)', [(0, u'Disabled'), (8192, u'Enabled')])],None,None,1,1))
parameter_forms.append(('Optical Injection Parameters',__p))

# Form: Spectrum Controller Parameters

__p = []

__p.append(('dsp','choices',SPECT_CNTRL_STATE_REGISTER,'Spectrum Controller State','',[(SPECT_CNTRL_IdleState,"Not acquiring"),(SPECT_CNTRL_StartingState,"Start acquisition"),(SPECT_CNTRL_RunningState,"Acquisition in progress"),(SPECT_CNTRL_PausedState,"Acquisition paused"),(SPECT_CNTRL_ErrorState,"Error state"),],1,1))
__p.append(('dsp','choices',SPECT_CNTRL_MODE_REGISTER,'Spectrum Controller Mode','',[(SPECT_CNTRL_SchemeSingleMode,"Perform single scheme"),(SPECT_CNTRL_SchemeMultipleMode,"Perform multiple schemes"),(SPECT_CNTRL_SchemeSequenceMode,"Perform scheme sequence"),(SPECT_CNTRL_ContinuousMode,"Continuous acquisition"),],1,1))
__p.append(('dsp','uint32',SPECT_CNTRL_ACTIVE_SCHEME_REGISTER,'Active scheme table index','','%d',1,1))
__p.append(('dsp','uint32',SPECT_CNTRL_NEXT_SCHEME_REGISTER,'Next scheme table index','','%d',1,1))
__p.append(('dsp','uint32',SPECT_CNTRL_SCHEME_ITER_REGISTER,'Iteration counter for current scheme','','%d',1,0))
__p.append(('dsp','uint32',SPECT_CNTRL_SCHEME_ROW_REGISTER,'Row number within active scheme','','%d',1,0))
__p.append(('dsp','uint32',SPECT_CNTRL_DWELL_COUNT_REGISTER,'Dwell counter for current scheme row','','%d',1,0))
__p.append(('dsp','uint32',SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER,'Default ringdown threshold','','%d',1,1))
__p.append(('dsp','uint32',SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER,'Dither mode ringdown timeout','us','%d',1,1))
__p.append(('dsp','uint32',SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER,'Ramp mode ringdown timeout','us','%d',1,1))
parameter_forms.append(('Spectrum Controller Parameters',__p))

# Form: Ringdown Simulator Parameters

__p = []

__p.append(('fpga','mask',FPGA_RDSIM+RDSIM_OPTIONS,[(1, u'Source of decay and tuner center parameters', [(0, u'Registers'), (1, u'Input ports')])],None,None,1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_TUNER_CENTER,'Tuner value around which cavity fills','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_TUNER_WINDOW_HALF_WIDTH,'Half-width of tuner window within which cavity fills','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_FILLING_RATE,'Rate of increase of accumulator value during filling','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_DECAY,'Exponential decay of accumulator when not filling','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_DECAY_IN_SHIFT,'Bits to  right shift decay input','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_DECAY_IN_OFFSET,'Offset to add to shifted decay input','','%d',1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_WFAC,'Width factor of simulated spectrum','','%d',1,1))
parameter_forms.append(('Ringdown Simulator Parameters',__p))

# Form: Ringdown Manager Parameters

__p = []

__p.append(('fpga','mask',FPGA_RDMAN+RDMAN_CONTROL,[(1, u'Stop/Run', [(0, u'Stop'), (1, u'Run')]), (2, u'Single/Continuous', [(0, u'Single'), (2, u'Continuous')]), (4, u'Start ringdown cycle', [(0, u'Idle'), (4, u'Start')]), (8, u'Abort ringdown', [(0, u'Idle'), (8, u'Abort')]), (16, u'Reset ringdown manager', [(0, u'Idle'), (16, u'Reset')]), (32, u'Mark bank 0 available for write', [(0, u'Idle'), (32, u'Mark available')]), (64, u'Mark bank 1 available for write', [(0, u'Idle'), (64, u'Mark available')]), (128, u'Acknowledge ring-down interrupt', [(0, u'Idle'), (128, u'Acknowledge')]), (256, u'Acknowledge data acquired interrupt', [(0, u'Idle'), (256, u'Acknowledge')]), (512, u'Tuner waveform mode', [(0, u'Ramp'), (512, u'Dither')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_RDMAN+RDMAN_STATUS,[(1, u'Indicates shutdown of optical injection', [(0, u'Injecting'), (1, u'Shut down')]), (2, u'Ring down interrupt occured', [(0, u'Idle'), (2, u'Interrupt Active')]), (4, u'Data acquired interrupt occured', [(0, u'Idle'), (4, u'Interrupt Active')]), (8, u'Active bank for data acquisition', [(0, u'Bank 0'), (8, u'Bank 1')]), (16, u'Bank 0 memory in use', [(0, u'Available'), (16, u'In Use')]), (32, u'Bank 1 memory in use', [(0, u'Available'), (32, u'In Use')]), (64, u'Metadata counter lapped', [(0, u'Not lapped'), (64, u'Lapped')]), (128, u'Laser frequency locked', [(0, u'Unlocked'), (128, u'Locked')]), (256, u'Timeout without ring-down', [(0, u'Idle'), (256, u'Timed Out')]), (512, u'Ring-down aborted', [(0, u'Idle'), (512, u'Aborted')]), (1024, u'Ringdown Cycle State', [(0, u'Idle'), (1024, u'Busy')])],None,None,1,0))
__p.append(('fpga','mask',FPGA_RDMAN+RDMAN_OPTIONS,[(1, u'Enable frequency locking', [(0, u'Disable'), (1, u'Enable')]), (2, u'Allow ring-down on positive tuner slope', [(0, u'No'), (2, u'Yes')]), (4, u'Allow ring-down on negative tuner slope', [(0, u'No'), (4, u'Yes')]), (8, u'Allow transition to dither mode', [(0, u'Disallow'), (8, u'Allow')])],None,None,1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_DATA_ADDRCNTR,'Ringdown data address','','%d',1,0))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_METADATA_ADDRCNTR,'Ringdown metadata address','','%d',1,0))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_PARAM_ADDRCNTR,'Ringdown parameter address','','%d',1,0))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_DIVISOR,'Ringdown ADC divisor','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_NUM_SAMP,'Ringdown samples to collect','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_THRESHOLD,'Ringdown threshold','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_LOCK_DURATION,'Laser lock duration (us)','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_PRECONTROL_DURATION,'Precontrol duration (us)','','%d',1,1))
__p.append(('fpga','uint32',FPGA_RDMAN+RDMAN_TIMEOUT_DURATION,'Ringdown timeout duration (us)','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_TUNER_AT_RINGDOWN,'Tuner value at ringdown','','%d',1,0))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_METADATA_ADDR_AT_RINGDOWN,'Metadata address at ringdown','','%d',1,0))
parameter_forms.append(('Ringdown Manager Parameters',__p))

# Form: Ringdown Data Fitting Parameters

__p = []

__p.append(('dsp','float',RDFITTER_MINLOSS_REGISTER,'Minimum loss','ppm/cm','%.4f',1,1))
__p.append(('dsp','float',RDFITTER_MAXLOSS_REGISTER,'Minimum loss','ppm/cm','%.4f',1,1))
__p.append(('dsp','float',RDFITTER_LATEST_LOSS_REGISTER,'Most recent loss','ppm/cm','%.3f',1,0))
__p.append(('dsp','uint32',RDFITTER_IMPROVEMENT_STEPS_REGISTER,'Number of iterations of ringdown fit improvement','','%d',1,1))
__p.append(('dsp','uint32',RDFITTER_START_SAMPLE_REGISTER,'Initial ringdown samples to ignore','','%d',1,1))
__p.append(('dsp','float',RDFITTER_FRACTIONAL_THRESHOLD_REGISTER,'Fractional threshold for fit window determination','','%.2f',1,1))
__p.append(('dsp','float',RDFITTER_ABSOLUTE_THRESHOLD_REGISTER,'Absolute threshold for fit window determination','','%.0f',1,1))
__p.append(('dsp','uint32',RDFITTER_NUMBER_OF_POINTS_REGISTER,'Maximum number of points in fit window','','%d',1,1))
__p.append(('dsp','float',RDFITTER_MAX_E_FOLDINGS_REGISTER,'Maximum number of time constants in fit window','','%.1f',1,1))
parameter_forms.append(('Ringdown Data Fitting Parameters',__p))

# Form: Wavelength Monitor Simulator Parameters

__p = []

__p.append(('fpga','mask',FPGA_WLMSIM+WLMSIM_OPTIONS,[(1, u'Input select', [(0, u'Register'), (1, u'Input port')])],None,None,1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_RFAC,'Reflectivity factor','','%d',1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_Z0,'Phase angle','','%d',1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_ETA1,'Etalon 1 photocurrent','digU','%d',1,0))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_REF1,'Reference 1 photocurrent','digU','%d',1,0))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_ETA2,'Etalon 2 photocurrent','digU','%d',1,0))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_REF2,'Reference 2 photocurrent','digU','%d',1,0))
parameter_forms.append(('Wavelength Monitor Simulator Parameters',__p))

# Form: Laser Locker Parameters

__p = []

__p.append(('fpga','mask',FPGA_LASERLOCKER+LASERLOCKER_CS,[(1, u'Stop/Run', [(0, u'Stop'), (1, u'Run')]), (2, u'Single/Continuous', [(0, u'Single'), (2, u'Continuous')]), (4, u'Generate PRBS', [(0, u'Idle'), (4, u'Send PRBS')]), (8, u'Enable fine current acc', [(0, u'Reset'), (8, u'Accumulate')]), (16, u'Sample dark currents', [(0, u'Idle'), (16, u'Sample')]), (32, u'Load WLM ADC values', [(0, u'Idle'), (32, u'Load')]), (64, u'Tuner offset source', [(0, u'Register'), (64, u'Input port')]), (128, u'Laser frequency in window', [(0, u'Out of range'), (128, u'In Window')]), (256, u'Fine current calculation', [(0, u'In progress'), (256, u'Complete')])],None,None,1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_ETA1,'Etalon 1 reading','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_REF1,'Reference 1 reading','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_ETA2,'Etalon 2 reading','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_REF2,'Reference 2 reading','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_ETA1_OFFSET,'Etalon 1 offset','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_REF1_OFFSET,'Reference 1 offset','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_ETA2_OFFSET,'Etalon 2 offset','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_REF2_OFFSET,'Reference 2 offset','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_RATIO1_CENTER,'Ratio 1 ellipse center','digU','%d',1,1))
__p.append(('fpga','int16',FPGA_LASERLOCKER+LASERLOCKER_RATIO1_MULTIPLIER,'Ratio 1 multiplier','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_RATIO2_CENTER,'Ratio 2 ellipse center','digU','%d',1,1))
__p.append(('fpga','int16',FPGA_LASERLOCKER+LASERLOCKER_RATIO2_MULTIPLIER,'Ratio 2 multiplier','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_TUNING_OFFSET,'Tuning offset for frequency shift','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_WM_LOCK_WINDOW,'Lock window','digU','%d',1,1))
__p.append(('fpga','int16',FPGA_LASERLOCKER+LASERLOCKER_WM_INT_GAIN,'Locker integral gain','digU','%d',1,1))
__p.append(('fpga','int16',FPGA_LASERLOCKER+LASERLOCKER_WM_PROP_GAIN,'Locker proportional gain','digU','%d',1,1))
__p.append(('fpga','int16',FPGA_LASERLOCKER+LASERLOCKER_WM_DERIV_GAIN,'Locker derivative gain','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_RATIO1,'Wavelength monitor ratio 1','digU','%d',1,0))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_RATIO2,'Wavelength monitor ratio 2','digU','%d',1,0))
__p.append(('fpga','int16',FPGA_LASERLOCKER+LASERLOCKER_LOCK_ERROR,'Locker loop error','digU','%d',1,0))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_FINE_CURRENT,'Fine laser current','digU','%d',1,0))
__p.append(('fpga','uint16',FPGA_LASERLOCKER+LASERLOCKER_CYCLE_COUNTER,'Cycle count','','%d',1,0))
parameter_forms.append(('Laser Locker Parameters',__p))

# Form: Sentry Parameters

__p = []

__p.append(('dsp','uint32',SENTRY_LOWER_LIMIT_TRIPPED_REGISTER,'Lower limit sentries tripped','','$%X',1,0))
__p.append(('dsp','uint32',SENTRY_UPPER_LIMIT_TRIPPED_REGISTER,'Upper limit sentries tripped','','$%X',1,0))
__p.append(('dsp','float',SENTRY_LASER1_TEMPERATURE_MIN_REGISTER,'Laser 1 minimum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER1_TEMPERATURE_MAX_REGISTER,'Laser 1 maximum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER2_TEMPERATURE_MIN_REGISTER,'Laser 2 minimum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER2_TEMPERATURE_MAX_REGISTER,'Laser 2 maximum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER3_TEMPERATURE_MIN_REGISTER,'Laser 3 minimum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER3_TEMPERATURE_MAX_REGISTER,'Laser 3 maximum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER4_TEMPERATURE_MIN_REGISTER,'Laser 4 minimum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER4_TEMPERATURE_MAX_REGISTER,'Laser 4 maximum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_ETALON_TEMPERATURE_MIN_REGISTER,'Etalon minimum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_ETALON_TEMPERATURE_MAX_REGISTER,'Etalon maximum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER,'Warm box minimum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER,'Warm box maximum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER,'Warm box heatsink minimum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER,'Warm box heatsink maximum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER,'Cavity minimum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER,'Cavity maximum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER,'Hot box heatsink minimum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER,'Hot box heatsink maximum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_DAS_TEMPERATURE_MIN_REGISTER,'DAS minimum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_DAS_TEMPERATURE_MAX_REGISTER,'DAS maximum temperature','degC','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER1_CURRENT_MIN_REGISTER,'Laser 1 minimum current','mA','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER1_CURRENT_MAX_REGISTER,'Laser 1 maximum current','mA','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER2_CURRENT_MIN_REGISTER,'Laser 2 minimum current','mA','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER2_CURRENT_MAX_REGISTER,'Laser 2 maximum current','mA','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER3_CURRENT_MIN_REGISTER,'Laser 3 minimum current','mA','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER3_CURRENT_MAX_REGISTER,'Laser 3 maximum current','mA','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER4_CURRENT_MIN_REGISTER,'Laser 4 minimum current','mA','%.1f',1,1))
__p.append(('dsp','float',SENTRY_LASER4_CURRENT_MAX_REGISTER,'Laser 4 maximum current','mA','%.1f',1,1))
__p.append(('dsp','float',SENTRY_CAVITY_PRESSURE_MIN_REGISTER,'Cavity minimum pressure','torr','%.1f',1,1))
__p.append(('dsp','float',SENTRY_CAVITY_PRESSURE_MAX_REGISTER,'Cavity maximum pressure','torr','%.1f',1,1))
__p.append(('dsp','float',SENTRY_AMBIENT_PRESSURE_MIN_REGISTER,'Ambient minimum pressure','torr','%.1f',1,1))
__p.append(('dsp','float',SENTRY_AMBIENT_PRESSURE_MAX_REGISTER,'Ambient maximum pressure','torr','%.1f',1,1))
parameter_forms.append(('Sentry Parameters',__p))
