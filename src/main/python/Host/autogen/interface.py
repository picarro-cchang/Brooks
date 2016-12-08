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
#  Copyright (c) 2008-2016 Picarro, Inc. All rights reserved
#

from ctypes import c_ubyte, c_byte, c_uint, c_int, c_ushort, c_short
from ctypes import c_longlong, c_float, c_double, Structure, Union, sizeof

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
ERROR_TIMEOUT = -17
error_messages.append("Operation timed out")

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
    ("lockerError",c_int)
    ]

class RingdownMetadataDoubleType(Structure):
    _fields_ = [
    ("ratio1",c_double),
    ("ratio2",c_double),
    ("pztValue",c_double),
    ("lockerOffset",c_double),
    ("fineLaserCurrent",c_double),
    ("lockerError",c_double)
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
    ("addressAtRingdown",c_uint),
    ("extLaserLevelCounter",c_uint),
    ("extLaserSequenceId",c_uint)
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
    ("laserUsed",c_ushort),
    ("ringdownThreshold",c_ushort),
    ("subschemeId",c_ushort),
    ("schemeVersionAndTable",c_ushort),
    ("schemeRow",c_ushort),
    ("ratio1",c_ushort),
    ("ratio2",c_ushort),
    ("fineLaserCurrent",c_ushort),
    ("coarseLaserCurrent",c_ushort),
    ("fitAmplitude",c_ushort),
    ("fitBackground",c_ushort),
    ("fitRmsResidual",c_ushort),
    ("laserTemperature",c_float),
    ("etalonTemperature",c_float),
    ("cavityPressure",c_float)
    ]

class ProcessedRingdownEntryType(Structure):
    _fields_ = [
    ("timestamp",c_longlong),
    ("wlmAngle",c_float),
    ("waveNumber",c_double),
    ("waveNumberSetpoint",c_double),
    ("uncorrectedAbsorbance",c_float),
    ("correctedAbsorbance",c_float),
    ("status",c_ushort),
    ("count",c_ushort),
    ("tunerValue",c_ushort),
    ("pztValue",c_ushort),
    ("laserUsed",c_ushort),
    ("ringdownThreshold",c_ushort),
    ("subschemeId",c_ushort),
    ("schemeVersionAndTable",c_ushort),
    ("schemeRow",c_ushort),
    ("ratio1",c_ushort),
    ("ratio2",c_ushort),
    ("fineLaserCurrent",c_ushort),
    ("coarseLaserCurrent",c_ushort),
    ("fitAmplitude",c_ushort),
    ("fitBackground",c_ushort),
    ("fitRmsResidual",c_ushort),
    ("laserTemperature",c_float),
    ("etalonTemperature",c_float),
    ("cavityPressure",c_float),
    ("extra1",c_uint),
    ("extra2",c_uint),
    ("extra3",c_uint),
    ("extra4",c_uint)
    ]

class SensorEntryType(Structure):
    _fields_ = [
    ("timestamp",c_longlong),
    ("streamNum",c_uint),
    ("value",c_float)
    ]

class OscilloscopeTraceType(Structure):
    _fields_ = [
    ("data",c_ushort*4096)
    ]

class ValveSequenceEntryType(Structure):
    _fields_ = [
    ("maskAndValue",c_ushort),
    ("dwell",c_ushort)
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
    ("offset",c_float),
    ("num",c_float*9),
    ("den",c_float*9),
    ("state",c_float*8)
    ]

class InterpolatorEnvType(Structure):
    _fields_ = [
    ("target",c_float),
    ("current",c_float),
    ("steps",c_uint)
    ]

class Byte4EnvType(Structure):
    _fields_ = [
    ("buffer",c_uint*1)
    ]

class Byte16EnvType(Structure):
    _fields_ = [
    ("buffer",c_uint*4)
    ]

class Byte64EnvType(Structure):
    _fields_ = [
    ("buffer",c_uint*16)
    ]

class SchemeRowType(Structure):
    _fields_ = [
    ("setpoint",c_float),
    ("dwellCount",c_ushort),
    ("subschemeId",c_ushort),
    ("virtualLaser",c_ushort),
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
    ("pressureC3",c_float)
    ]

class WLMCalRowType(Structure):
    _fields_ = [
    ("waveNumberAsUint",c_uint),
    ("ratio1",c_float),
    ("ratio2",c_float)
    ]

class WLMHeaderType(Structure):
    _fields_ = [
    ("identifier",c_ubyte*32),
    ("etalon_temperature",c_float),
    ("etalon1_offset",c_float),
    ("reference1_offset",c_float),
    ("etalon2_offset",c_float),
    ("reference2_offset",c_float),
    ("padding",c_ubyte*12)
    ]

class WLMCalibrationType(Structure):
    _fields_ = [
    ("header",WLMHeaderType),
    ("wlmCalRows",WLMCalRowType*336)
    ]

# Constant definitions
# Scheduler period (ms)
SCHEDULER_PERIOD = 100
# Maximum number of lasers
MAX_LASERS = 4
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
# Offset for oscilloscope trace in DSP shared memory
OSCILLOSCOPE_TRACE_OFFSET = (RINGDOWN_BUFFER_OFFSET+NUM_RINGDOWN_BUFFERS*RINGDOWN_BUFFER_SIZE)
# Size of an oscilloscope trace in 32 bit ints
OSCILLOSCOPE_TRACE_SIZE = (sizeof(OscilloscopeTraceType)/4)
# Number of oscilloscope traces in 32 bit ints
NUM_OSCILLOSCOPE_TRACES = 1
# Offset for valve sequence area in DSP shared memory
VALVE_SEQUENCE_OFFSET = 0x7800
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
# Number of bits in FPGA EMIF address
EMIF_ADDR_WIDTH = 20
# Number of bits in EMIF data
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
# FPGA register base address
FPGA_REG_BASE_ADDRESS = (RDMEM_ADDRESS + (1 << (EMIF_ADDR_WIDTH+1)))
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
# Bad I2C read value
I2C_READ_ERROR = 0x80000000
# Time error (ms) beyond which fast correction takes place
NUDGE_LIMIT = 5000
# Do not adjust if timestamps agree within this window (ms)
NUDGE_WINDOW = 20
# Base address of DSP timer 0 registers
DSP_TIMER0_BASE = 0x01940000
# Divisor to get 1ms for a 225MHz DSP clock
DSP_TIMER_DIVISOR = 56250
# Maximum number of fitter processes
MAX_FITTERS = 8
# Maximum number of samples in peak detection history buffer
PEAK_DETECT_MAX_HISTORY_LENGTH = 1024
# Laser current generator accumulator width
LASER_CURRENT_GEN_ACC_WIDTH = 24
# Size of EEPROM blocks. Objects saved in EEPROM use integer number of blocks
EEPROM_BLOCK_SIZE = 128

# Enumerated definitions for RegTypes
RegTypes = c_uint
float_type = 0 # 
uint_type = 1 # 
int_type = 2 # 

# Dictionary for enumerated constants in RegTypes
RegTypesDict = {}
RegTypesDict[0] = 'float_type' # 
RegTypesDict[1] = 'uint_type' # 
RegTypesDict[2] = 'int_type' # 

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
STREAM_Ratio1 = 14 # 
STREAM_Ratio2 = 15 # 
STREAM_Laser1Current = 16 # 
STREAM_Laser2Current = 17 # 
STREAM_Laser3Current = 18 # 
STREAM_Laser4Current = 19 # 
STREAM_CavityPressure = 20 # 
STREAM_AmbientPressure = 21 # 
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
STREAM_MPVPosition = 32 # 
STREAM_FanState = 33 # 
STREAM_ProcessedLoss1 = 34 # 
STREAM_ProcessedLoss2 = 35 # 
STREAM_ProcessedLoss3 = 36 # 
STREAM_ProcessedLoss4 = 37 # 
STREAM_Flow1 = 38 # 
STREAM_Battery_Voltage = 39 # 
STREAM_Battery_Current = 40 # 
STREAM_Battery_Charge = 41 # 
STREAM_Battery_Temperature = 42 # 
STREAM_AccelX = 43 # 
STREAM_AccelY = 44 # 
STREAM_AccelZ = 45 # 
STREAM_CavityTemp1 = 46 # 
STREAM_CavityTemp2 = 47 # 
STREAM_CavityTemp3 = 48 # 
STREAM_CavityTemp4 = 49 # 

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
STREAM_MemberTypeDict[14] = 'STREAM_Ratio1' # 
STREAM_MemberTypeDict[15] = 'STREAM_Ratio2' # 
STREAM_MemberTypeDict[16] = 'STREAM_Laser1Current' # 
STREAM_MemberTypeDict[17] = 'STREAM_Laser2Current' # 
STREAM_MemberTypeDict[18] = 'STREAM_Laser3Current' # 
STREAM_MemberTypeDict[19] = 'STREAM_Laser4Current' # 
STREAM_MemberTypeDict[20] = 'STREAM_CavityPressure' # 
STREAM_MemberTypeDict[21] = 'STREAM_AmbientPressure' # 
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
STREAM_MemberTypeDict[32] = 'STREAM_MPVPosition' # 
STREAM_MemberTypeDict[33] = 'STREAM_FanState' # 
STREAM_MemberTypeDict[34] = 'STREAM_ProcessedLoss1' # 
STREAM_MemberTypeDict[35] = 'STREAM_ProcessedLoss2' # 
STREAM_MemberTypeDict[36] = 'STREAM_ProcessedLoss3' # 
STREAM_MemberTypeDict[37] = 'STREAM_ProcessedLoss4' # 
STREAM_MemberTypeDict[38] = 'STREAM_Flow1' # 
STREAM_MemberTypeDict[39] = 'STREAM_Battery_Voltage' # 
STREAM_MemberTypeDict[40] = 'STREAM_Battery_Current' # 
STREAM_MemberTypeDict[41] = 'STREAM_Battery_Charge' # 
STREAM_MemberTypeDict[42] = 'STREAM_Battery_Temperature' # 
STREAM_MemberTypeDict[43] = 'STREAM_AccelX' # 
STREAM_MemberTypeDict[44] = 'STREAM_AccelY' # 
STREAM_MemberTypeDict[45] = 'STREAM_AccelZ' # 
STREAM_MemberTypeDict[46] = 'STREAM_CavityTemp1' # 
STREAM_MemberTypeDict[47] = 'STREAM_CavityTemp2' # 
STREAM_MemberTypeDict[48] = 'STREAM_CavityTemp3' # 
STREAM_MemberTypeDict[49] = 'STREAM_CavityTemp4' # 

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

# Enumerated definitions for FAN_CNTRL_StateType
FAN_CNTRL_StateType = c_uint
FAN_CNTRL_OffState = 0 # Fans off
FAN_CNTRL_OnState = 1 # Fans on

# Dictionary for enumerated constants in FAN_CNTRL_StateType
FAN_CNTRL_StateTypeDict = {}
FAN_CNTRL_StateTypeDict[0] = 'FAN_CNTRL_OffState' # Fans off
FAN_CNTRL_StateTypeDict[1] = 'FAN_CNTRL_OnState' # Fans on

# Enumerated definitions for SPECT_CNTRL_StateType
SPECT_CNTRL_StateType = c_uint
SPECT_CNTRL_IdleState = 0 # Not acquiring
SPECT_CNTRL_StartingState = 1 # Start acquisition
SPECT_CNTRL_StartManualState = 2 # Start acquisition with manual temperature control
SPECT_CNTRL_RunningState = 3 # Acquisition in progress
SPECT_CNTRL_PausedState = 4 # Acquisition paused
SPECT_CNTRL_ErrorState = 5 # Error state
SPECT_CNTRL_DiagnosticState = 6 # Diagnostic state

# Dictionary for enumerated constants in SPECT_CNTRL_StateType
SPECT_CNTRL_StateTypeDict = {}
SPECT_CNTRL_StateTypeDict[0] = 'SPECT_CNTRL_IdleState' # Not acquiring
SPECT_CNTRL_StateTypeDict[1] = 'SPECT_CNTRL_StartingState' # Start acquisition
SPECT_CNTRL_StateTypeDict[2] = 'SPECT_CNTRL_StartManualState' # Start acquisition with manual temperature control
SPECT_CNTRL_StateTypeDict[3] = 'SPECT_CNTRL_RunningState' # Acquisition in progress
SPECT_CNTRL_StateTypeDict[4] = 'SPECT_CNTRL_PausedState' # Acquisition paused
SPECT_CNTRL_StateTypeDict[5] = 'SPECT_CNTRL_ErrorState' # Error state
SPECT_CNTRL_StateTypeDict[6] = 'SPECT_CNTRL_DiagnosticState' # Diagnostic state

# Enumerated definitions for SPECT_CNTRL_ModeType
SPECT_CNTRL_ModeType = c_uint
SPECT_CNTRL_SchemeSingleMode = 0 # Perform single scheme
SPECT_CNTRL_SchemeMultipleMode = 1 # Perform multiple schemes
SPECT_CNTRL_SchemeMultipleNoRepeatMode = 2 # Multiple schemes no repeats
SPECT_CNTRL_ContinuousMode = 3 # Continuous acquisition
SPECT_CNTRL_ContinuousManualTempMode = 4 # Continuous acquisition with manual temperature control

# Dictionary for enumerated constants in SPECT_CNTRL_ModeType
SPECT_CNTRL_ModeTypeDict = {}
SPECT_CNTRL_ModeTypeDict[0] = 'SPECT_CNTRL_SchemeSingleMode' # Perform single scheme
SPECT_CNTRL_ModeTypeDict[1] = 'SPECT_CNTRL_SchemeMultipleMode' # Perform multiple schemes
SPECT_CNTRL_ModeTypeDict[2] = 'SPECT_CNTRL_SchemeMultipleNoRepeatMode' # Multiple schemes no repeats
SPECT_CNTRL_ModeTypeDict[3] = 'SPECT_CNTRL_ContinuousMode' # Continuous acquisition
SPECT_CNTRL_ModeTypeDict[4] = 'SPECT_CNTRL_ContinuousManualTempMode' # Continuous acquisition with manual temperature control

# Enumerated definitions for TUNER_ModeType
TUNER_ModeType = c_uint
TUNER_RampMode = 0 # Ramp mode
TUNER_DitherMode = 1 # Dither mode

# Dictionary for enumerated constants in TUNER_ModeType
TUNER_ModeTypeDict = {}
TUNER_ModeTypeDict[0] = 'TUNER_RampMode' # Ramp mode
TUNER_ModeTypeDict[1] = 'TUNER_DitherMode' # Dither mode

# Enumerated definitions for TUNER_DITHER_MEDIAN_CountType
TUNER_DITHER_MEDIAN_CountType = c_uint
TUNER_DITHER_MEDIAN_1 = 1 # 1
TUNER_DITHER_MEDIAN_3 = 3 # 3
TUNER_DITHER_MEDIAN_5 = 5 # 5
TUNER_DITHER_MEDIAN_7 = 7 # 7
TUNER_DITHER_MEDIAN_9 = 9 # 9

# Dictionary for enumerated constants in TUNER_DITHER_MEDIAN_CountType
TUNER_DITHER_MEDIAN_CountTypeDict = {}
TUNER_DITHER_MEDIAN_CountTypeDict[1] = 'TUNER_DITHER_MEDIAN_1' # 1
TUNER_DITHER_MEDIAN_CountTypeDict[3] = 'TUNER_DITHER_MEDIAN_3' # 3
TUNER_DITHER_MEDIAN_CountTypeDict[5] = 'TUNER_DITHER_MEDIAN_5' # 5
TUNER_DITHER_MEDIAN_CountTypeDict[7] = 'TUNER_DITHER_MEDIAN_7' # 7
TUNER_DITHER_MEDIAN_CountTypeDict[9] = 'TUNER_DITHER_MEDIAN_9' # 9

# Enumerated definitions for VALVE_CNTRL_StateType
VALVE_CNTRL_StateType = c_uint
VALVE_CNTRL_DisabledState = 0 # Disabled
VALVE_CNTRL_OutletControlState = 1 # Outlet control
VALVE_CNTRL_InletControlState = 2 # Inlet control
VALVE_CNTRL_ManualControlState = 3 # Manual control
VALVE_CNTRL_SaveAndCloseValvesState = 4 # Save valve settings and close valves
VALVE_CNTRL_RestoreValvesState = 5 # Restore valve settings and saved state
VALVE_CNTRL_OutletOnlyControlState = 6 # Outlet only (no inlet valve) control, normal operation
VALVE_CNTRL_OutletOnlyRecoveryState = 7 # Outlet only (no inlet valve) control, pump disconnected

# Dictionary for enumerated constants in VALVE_CNTRL_StateType
VALVE_CNTRL_StateTypeDict = {}
VALVE_CNTRL_StateTypeDict[0] = 'VALVE_CNTRL_DisabledState' # Disabled
VALVE_CNTRL_StateTypeDict[1] = 'VALVE_CNTRL_OutletControlState' # Outlet control
VALVE_CNTRL_StateTypeDict[2] = 'VALVE_CNTRL_InletControlState' # Inlet control
VALVE_CNTRL_StateTypeDict[3] = 'VALVE_CNTRL_ManualControlState' # Manual control
VALVE_CNTRL_StateTypeDict[4] = 'VALVE_CNTRL_SaveAndCloseValvesState' # Save valve settings and close valves
VALVE_CNTRL_StateTypeDict[5] = 'VALVE_CNTRL_RestoreValvesState' # Restore valve settings and saved state
VALVE_CNTRL_StateTypeDict[6] = 'VALVE_CNTRL_OutletOnlyControlState' # Outlet only (no inlet valve) control, normal operation
VALVE_CNTRL_StateTypeDict[7] = 'VALVE_CNTRL_OutletOnlyRecoveryState' # Outlet only (no inlet valve) control, pump disconnected

# Enumerated definitions for FLOW_CNTRL_StateType
FLOW_CNTRL_StateType = c_uint
FLOW_CNTRL_DisabledState = 0 # Disabled
FLOW_CNTRL_EnabledState = 1 # Enabled

# Dictionary for enumerated constants in FLOW_CNTRL_StateType
FLOW_CNTRL_StateTypeDict = {}
FLOW_CNTRL_StateTypeDict[0] = 'FLOW_CNTRL_DisabledState' # Disabled
FLOW_CNTRL_StateTypeDict[1] = 'FLOW_CNTRL_EnabledState' # Enabled

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

# Enumerated definitions for PEAK_DETECT_CNTRL_StateType
PEAK_DETECT_CNTRL_StateType = c_uint
PEAK_DETECT_CNTRL_IdleState = 0 # Idle
PEAK_DETECT_CNTRL_ArmedState = 1 # Armed
PEAK_DETECT_CNTRL_TriggerPendingState = 2 # Trigger Pending
PEAK_DETECT_CNTRL_TriggeredState = 3 # Triggered
PEAK_DETECT_CNTRL_InactiveState = 4 # Inactive
PEAK_DETECT_CNTRL_CancellingState = 5 # Cancelling
PEAK_DETECT_CNTRL_PrimingState = 6 # Priming
PEAK_DETECT_CNTRL_PurgingState = 7 # Purging
PEAK_DETECT_CNTRL_InjectionPendingState = 8 # Injection Pending
PEAK_DETECT_CNTRL_TransitioningState = 9 # Transitioning
PEAK_DETECT_CNTRL_HoldingState = 10 # Holding

# Dictionary for enumerated constants in PEAK_DETECT_CNTRL_StateType
PEAK_DETECT_CNTRL_StateTypeDict = {}
PEAK_DETECT_CNTRL_StateTypeDict[0] = 'PEAK_DETECT_CNTRL_IdleState' # Idle
PEAK_DETECT_CNTRL_StateTypeDict[1] = 'PEAK_DETECT_CNTRL_ArmedState' # Armed
PEAK_DETECT_CNTRL_StateTypeDict[2] = 'PEAK_DETECT_CNTRL_TriggerPendingState' # Trigger Pending
PEAK_DETECT_CNTRL_StateTypeDict[3] = 'PEAK_DETECT_CNTRL_TriggeredState' # Triggered
PEAK_DETECT_CNTRL_StateTypeDict[4] = 'PEAK_DETECT_CNTRL_InactiveState' # Inactive
PEAK_DETECT_CNTRL_StateTypeDict[5] = 'PEAK_DETECT_CNTRL_CancellingState' # Cancelling
PEAK_DETECT_CNTRL_StateTypeDict[6] = 'PEAK_DETECT_CNTRL_PrimingState' # Priming
PEAK_DETECT_CNTRL_StateTypeDict[7] = 'PEAK_DETECT_CNTRL_PurgingState' # Purging
PEAK_DETECT_CNTRL_StateTypeDict[8] = 'PEAK_DETECT_CNTRL_InjectionPendingState' # Injection Pending
PEAK_DETECT_CNTRL_StateTypeDict[9] = 'PEAK_DETECT_CNTRL_TransitioningState' # Transitioning
PEAK_DETECT_CNTRL_StateTypeDict[10] = 'PEAK_DETECT_CNTRL_HoldingState' # Holding

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

# Enumerated definitions for ACTUAL_LASER_Type
ACTUAL_LASER_Type = c_uint
ACTUAL_LASER_1 = 0 # Actual laser 1
ACTUAL_LASER_2 = 1 # Actual laser 2
ACTUAL_LASER_3 = 2 # Actual laser 3
ACTUAL_LASER_4 = 3 # Actual laser 4

# Dictionary for enumerated constants in ACTUAL_LASER_Type
ACTUAL_LASER_TypeDict = {}
ACTUAL_LASER_TypeDict[0] = 'ACTUAL_LASER_1' # Actual laser 1
ACTUAL_LASER_TypeDict[1] = 'ACTUAL_LASER_2' # Actual laser 2
ACTUAL_LASER_TypeDict[2] = 'ACTUAL_LASER_3' # Actual laser 3
ACTUAL_LASER_TypeDict[3] = 'ACTUAL_LASER_4' # Actual laser 4

# Enumerated definitions for DAS_STATUS_BitType
DAS_STATUS_BitType = c_uint
DAS_STATUS_Laser1TempCntrlLockedBit = 0 # Laser 1 Temperature Locked
DAS_STATUS_Laser1TempCntrlActiveBit = 1 # Laser 1 Temperature Controller On
DAS_STATUS_Laser2TempCntrlLockedBit = 2 # Laser 2 Temperature Locked
DAS_STATUS_Laser2TempCntrlActiveBit = 3 # Laser 2 Temperature Controller On
DAS_STATUS_Laser3TempCntrlLockedBit = 4 # Laser 3 Temperature Locked
DAS_STATUS_Laser3TempCntrlActiveBit = 5 # Laser 3 Temperature Controller On
DAS_STATUS_Laser4TempCntrlLockedBit = 6 # Laser 4 Temperature Locked
DAS_STATUS_Laser4TempCntrlActiveBit = 7 # Laser 4 Temperature Controller On
DAS_STATUS_WarmBoxTempCntrlLockedBit = 8 # Warm Box Temperature Locked
DAS_STATUS_WarmBoxTempCntrlActiveBit = 9 # Warm Box Temperature Controller On
DAS_STATUS_CavityTempCntrlLockedBit = 10 # Cavity Temperature Locked
DAS_STATUS_CavityTempCntrlActiveBit = 11 # Cavity Temperature Controller On
DAS_STATUS_HeaterTempCntrlLockedBit = 12 # Heater Control Locked
DAS_STATUS_HeaterTempCntrlActiveBit = 13 # Heater Controller On

# Dictionary for enumerated constants in DAS_STATUS_BitType
DAS_STATUS_BitTypeDict = {}
DAS_STATUS_BitTypeDict[0] = 'DAS_STATUS_Laser1TempCntrlLockedBit' # Laser 1 Temperature Locked
DAS_STATUS_BitTypeDict[1] = 'DAS_STATUS_Laser1TempCntrlActiveBit' # Laser 1 Temperature Controller On
DAS_STATUS_BitTypeDict[2] = 'DAS_STATUS_Laser2TempCntrlLockedBit' # Laser 2 Temperature Locked
DAS_STATUS_BitTypeDict[3] = 'DAS_STATUS_Laser2TempCntrlActiveBit' # Laser 2 Temperature Controller On
DAS_STATUS_BitTypeDict[4] = 'DAS_STATUS_Laser3TempCntrlLockedBit' # Laser 3 Temperature Locked
DAS_STATUS_BitTypeDict[5] = 'DAS_STATUS_Laser3TempCntrlActiveBit' # Laser 3 Temperature Controller On
DAS_STATUS_BitTypeDict[6] = 'DAS_STATUS_Laser4TempCntrlLockedBit' # Laser 4 Temperature Locked
DAS_STATUS_BitTypeDict[7] = 'DAS_STATUS_Laser4TempCntrlActiveBit' # Laser 4 Temperature Controller On
DAS_STATUS_BitTypeDict[8] = 'DAS_STATUS_WarmBoxTempCntrlLockedBit' # Warm Box Temperature Locked
DAS_STATUS_BitTypeDict[9] = 'DAS_STATUS_WarmBoxTempCntrlActiveBit' # Warm Box Temperature Controller On
DAS_STATUS_BitTypeDict[10] = 'DAS_STATUS_CavityTempCntrlLockedBit' # Cavity Temperature Locked
DAS_STATUS_BitTypeDict[11] = 'DAS_STATUS_CavityTempCntrlActiveBit' # Cavity Temperature Controller On
DAS_STATUS_BitTypeDict[12] = 'DAS_STATUS_HeaterTempCntrlLockedBit' # Heater Control Locked
DAS_STATUS_BitTypeDict[13] = 'DAS_STATUS_HeaterTempCntrlActiveBit' # Heater Controller On

# Enumerated definitions for TEC_CNTRL_Type
TEC_CNTRL_Type = c_uint
TEC_CNTRL_Disabled = 0 # Disabled
TEC_CNTRL_Enabled = 1 # Enabled

# Dictionary for enumerated constants in TEC_CNTRL_Type
TEC_CNTRL_TypeDict = {}
TEC_CNTRL_TypeDict[0] = 'TEC_CNTRL_Disabled' # Disabled
TEC_CNTRL_TypeDict[1] = 'TEC_CNTRL_Enabled' # Enabled

# Enumerated definitions for OVERLOAD_BitType
OVERLOAD_BitType = c_uint
OVERLOAD_WarmBoxTecBit = 0 # Warm box TEC overload
OVERLOAD_HotBoxTecBit = 1 # Hot box TEC overload

# Dictionary for enumerated constants in OVERLOAD_BitType
OVERLOAD_BitTypeDict = {}
OVERLOAD_BitTypeDict[0] = 'OVERLOAD_WarmBoxTecBit' # Warm box TEC overload
OVERLOAD_BitTypeDict[1] = 'OVERLOAD_HotBoxTecBit' # Hot box TEC overload

# Enumerated definitions for ANALYZER_TUNING_ModeType
ANALYZER_TUNING_ModeType = c_uint
ANALYZER_TUNING_CavityLengthTuningMode = 0 # Cavity Length Tuning
ANALYZER_TUNING_LaserCurrentTuningMode = 1 # Laser Current Tuning
ANALYZER_TUNING_FsrHoppingTuningMode = 2 # Fsr Hopping Tuning

# Dictionary for enumerated constants in ANALYZER_TUNING_ModeType
ANALYZER_TUNING_ModeTypeDict = {}
ANALYZER_TUNING_ModeTypeDict[0] = 'ANALYZER_TUNING_CavityLengthTuningMode' # Cavity Length Tuning
ANALYZER_TUNING_ModeTypeDict[1] = 'ANALYZER_TUNING_LaserCurrentTuningMode' # Laser Current Tuning
ANALYZER_TUNING_ModeTypeDict[2] = 'ANALYZER_TUNING_FsrHoppingTuningMode' # Fsr Hopping Tuning

# Enumerated definitions for SENTRY_BitType
SENTRY_BitType = c_uint
SENTRY_Laser1TemperatureBit = 0 # Laser 1 Temperature
SENTRY_Laser2TemperatureBit = 1 # Laser 2 Temperature
SENTRY_Laser3TemperatureBit = 2 # Laser 3 Temperature
SENTRY_Laser4TemperatureBit = 3 # Laser 4 Temperature
SENTRY_EtalonTemperatureBit = 4 # Etalon Temperature
SENTRY_WarmBoxTemperatureBit = 5 # Warm Box Temperature
SENTRY_WarmBoxHeatsinkTemperatureBit = 6 # Warm Box Heatsink Temperature
SENTRY_CavityTemperatureBit = 7 # Cavity Temperature
SENTRY_HotBoxHeatsinkTemperatureBit = 8 # Hot Box Heatsink Temperature
SENTRY_DasTemperatureBit = 9 # DAS (ambient) Temperature
SENTRY_Laser1CurrentBit = 10 # Laser 1 Current
SENTRY_Laser2CurrentBit = 11 # Laser 2 Current
SENTRY_Laser3CurrentBit = 12 # Laser 3 Current
SENTRY_Laser4CurrentBit = 13 # Laser 4 Current
SENTRY_CavityPressureBit = 14 # Cavity Pressure
SENTRY_AmbientPressureBit = 15 # Ambient Pressure

# Dictionary for enumerated constants in SENTRY_BitType
SENTRY_BitTypeDict = {}
SENTRY_BitTypeDict[0] = 'SENTRY_Laser1TemperatureBit' # Laser 1 Temperature
SENTRY_BitTypeDict[1] = 'SENTRY_Laser2TemperatureBit' # Laser 2 Temperature
SENTRY_BitTypeDict[2] = 'SENTRY_Laser3TemperatureBit' # Laser 3 Temperature
SENTRY_BitTypeDict[3] = 'SENTRY_Laser4TemperatureBit' # Laser 4 Temperature
SENTRY_BitTypeDict[4] = 'SENTRY_EtalonTemperatureBit' # Etalon Temperature
SENTRY_BitTypeDict[5] = 'SENTRY_WarmBoxTemperatureBit' # Warm Box Temperature
SENTRY_BitTypeDict[6] = 'SENTRY_WarmBoxHeatsinkTemperatureBit' # Warm Box Heatsink Temperature
SENTRY_BitTypeDict[7] = 'SENTRY_CavityTemperatureBit' # Cavity Temperature
SENTRY_BitTypeDict[8] = 'SENTRY_HotBoxHeatsinkTemperatureBit' # Hot Box Heatsink Temperature
SENTRY_BitTypeDict[9] = 'SENTRY_DasTemperatureBit' # DAS (ambient) Temperature
SENTRY_BitTypeDict[10] = 'SENTRY_Laser1CurrentBit' # Laser 1 Current
SENTRY_BitTypeDict[11] = 'SENTRY_Laser2CurrentBit' # Laser 2 Current
SENTRY_BitTypeDict[12] = 'SENTRY_Laser3CurrentBit' # Laser 3 Current
SENTRY_BitTypeDict[13] = 'SENTRY_Laser4CurrentBit' # Laser 4 Current
SENTRY_BitTypeDict[14] = 'SENTRY_CavityPressureBit' # Cavity Pressure
SENTRY_BitTypeDict[15] = 'SENTRY_AmbientPressureBit' # Ambient Pressure

# Enumerated definitions for HARDWARE_PRESENT_BitType
HARDWARE_PRESENT_BitType = c_uint
HARDWARE_PRESENT_Laser1Bit = 0 # Laser 1
HARDWARE_PRESENT_Laser2Bit = 1 # Laser 2
HARDWARE_PRESENT_Laser3Bit = 2 # Laser 3
HARDWARE_PRESENT_Laser4Bit = 3 # Laser 4
HARDWARE_PRESENT_SoaBit = 4 # SOA
HARDWARE_PRESENT_PowerBoardBit = 5 # Power Board
HARDWARE_PRESENT_WarmBoxBit = 6 # Warm Box
HARDWARE_PRESENT_HotBoxBit = 7 # Hot Box
HARDWARE_PRESENT_DasTempMonitorBit = 8 # Das Temp Monitor
HARDWARE_PRESENT_AnalogInterface = 9 # Analog Interface
HARDWARE_PRESENT_FiberAmplifierBit = 10 # Fiber Amplifier
HARDWARE_PRESENT_FanCntrlDisabledBit = 11 # Fan Control Disabled
HARDWARE_PRESENT_FlowSensorBit = 12 # Flow Sensor
HARDWARE_PRESENT_RddVarGainBit = 13 # Variable gain ringdown detector
HARDWARE_PRESENT_AccelerometerBit = 14 # Accelerometer

# Dictionary for enumerated constants in HARDWARE_PRESENT_BitType
HARDWARE_PRESENT_BitTypeDict = {}
HARDWARE_PRESENT_BitTypeDict[0] = 'HARDWARE_PRESENT_Laser1Bit' # Laser 1
HARDWARE_PRESENT_BitTypeDict[1] = 'HARDWARE_PRESENT_Laser2Bit' # Laser 2
HARDWARE_PRESENT_BitTypeDict[2] = 'HARDWARE_PRESENT_Laser3Bit' # Laser 3
HARDWARE_PRESENT_BitTypeDict[3] = 'HARDWARE_PRESENT_Laser4Bit' # Laser 4
HARDWARE_PRESENT_BitTypeDict[4] = 'HARDWARE_PRESENT_SoaBit' # SOA
HARDWARE_PRESENT_BitTypeDict[5] = 'HARDWARE_PRESENT_PowerBoardBit' # Power Board
HARDWARE_PRESENT_BitTypeDict[6] = 'HARDWARE_PRESENT_WarmBoxBit' # Warm Box
HARDWARE_PRESENT_BitTypeDict[7] = 'HARDWARE_PRESENT_HotBoxBit' # Hot Box
HARDWARE_PRESENT_BitTypeDict[8] = 'HARDWARE_PRESENT_DasTempMonitorBit' # Das Temp Monitor
HARDWARE_PRESENT_BitTypeDict[9] = 'HARDWARE_PRESENT_AnalogInterface' # Analog Interface
HARDWARE_PRESENT_BitTypeDict[10] = 'HARDWARE_PRESENT_FiberAmplifierBit' # Fiber Amplifier
HARDWARE_PRESENT_BitTypeDict[11] = 'HARDWARE_PRESENT_FanCntrlDisabledBit' # Fan Control Disabled
HARDWARE_PRESENT_BitTypeDict[12] = 'HARDWARE_PRESENT_FlowSensorBit' # Flow Sensor
HARDWARE_PRESENT_BitTypeDict[13] = 'HARDWARE_PRESENT_RddVarGainBit' # Variable gain ringdown detector
HARDWARE_PRESENT_BitTypeDict[14] = 'HARDWARE_PRESENT_AccelerometerBit' # Accelerometer

# Enumerated definitions for FLOAT_ARITHMETIC_OperatorType
FLOAT_ARITHMETIC_OperatorType = c_uint
FLOAT_ARITHMETIC_Addition = 1 # 
FLOAT_ARITHMETIC_Subtraction = 2 # 
FLOAT_ARITHMETIC_Multiplication = 3 # 
FLOAT_ARITHMETIC_Division = 4 # 
FLOAT_ARITHMETIC_Average = 5 # 

# Dictionary for enumerated constants in FLOAT_ARITHMETIC_OperatorType
FLOAT_ARITHMETIC_OperatorTypeDict = {}
FLOAT_ARITHMETIC_OperatorTypeDict[1] = 'FLOAT_ARITHMETIC_Addition' # 
FLOAT_ARITHMETIC_OperatorTypeDict[2] = 'FLOAT_ARITHMETIC_Subtraction' # 
FLOAT_ARITHMETIC_OperatorTypeDict[3] = 'FLOAT_ARITHMETIC_Multiplication' # 
FLOAT_ARITHMETIC_OperatorTypeDict[4] = 'FLOAT_ARITHMETIC_Division' # 
FLOAT_ARITHMETIC_OperatorTypeDict[5] = 'FLOAT_ARITHMETIC_Average' # 

# Enumerated definitions for HEATER_CNTRL_ModeType
HEATER_CNTRL_ModeType = c_uint
HEATER_CNTRL_MODE_DELTA_TEMP = 0 # 
HEATER_CNTRL_MODE_TEC_TARGET = 1 # 
HEATER_CNTRL_MODE_HEATER_FIXED = 2 # 

# Dictionary for enumerated constants in HEATER_CNTRL_ModeType
HEATER_CNTRL_ModeTypeDict = {}
HEATER_CNTRL_ModeTypeDict[0] = 'HEATER_CNTRL_MODE_DELTA_TEMP' # 
HEATER_CNTRL_ModeTypeDict[1] = 'HEATER_CNTRL_MODE_TEC_TARGET' # 
HEATER_CNTRL_ModeTypeDict[2] = 'HEATER_CNTRL_MODE_HEATER_FIXED' # 

# Enumerated definitions for LOG_LEVEL_Type
LOG_LEVEL_Type = c_uint
LOG_LEVEL_DEBUG = 0 # 
LOG_LEVEL_INFO = 1 # 
LOG_LEVEL_STANDARD = 2 # 
LOG_LEVEL_CRITICAL = 3 # 

# Dictionary for enumerated constants in LOG_LEVEL_Type
LOG_LEVEL_TypeDict = {}
LOG_LEVEL_TypeDict[0] = 'LOG_LEVEL_DEBUG' # 
LOG_LEVEL_TypeDict[1] = 'LOG_LEVEL_INFO' # 
LOG_LEVEL_TypeDict[2] = 'LOG_LEVEL_STANDARD' # 
LOG_LEVEL_TypeDict[3] = 'LOG_LEVEL_CRITICAL' # 

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
SUBSCHEME_ID_IdMask = 0x7FFF
SUBSCHEME_ID_IncrMask = 0x8000
SUBSCHEME_ID_IgnoreMask = 0x4000
SUBSCHEME_ID_RecenterMask = 0x2000
SUBSCHEME_ID_IsCalMask = 0x1000
SUBSCHEME_ID_SpectrumSubsectionMask = 0x0300
SUBSCHEME_ID_SpectrumMask = 0x00FF

# Definitions for SCHEME_VERSION_AND_TABLE_BITMASK
SCHEME_VersionMask = 0xFFF0
SCHEME_TableMask = 0xF
SCHEME_VersionShift = 4
SCHEME_TableShift = 0

# Definitions for INJECTION_SETTINGS_BITMASK
INJECTION_SETTINGS_actualLaserMask = 0x3
INJECTION_SETTINGS_virtualLaserMask = 0x1C
INJECTION_SETTINGS_lossTagMask = 0xE0
INJECTION_SETTINGS_actualLaserShift = 0
INJECTION_SETTINGS_virtualLaserShift = 2
INJECTION_SETTINGS_lossTagShift = 5

# Register definitions
INTERFACE_NUMBER_OF_REGISTERS = 505

NOOP_REGISTER = 0
VERIFY_INIT_REGISTER = 1
COMM_STATUS_REGISTER = 2
TIMESTAMP_LSB_REGISTER = 3
TIMESTAMP_MSB_REGISTER = 4
SCHEDULER_CONTROL_REGISTER = 5
HARDWARE_PRESENT_REGISTER = 6
RD_IRQ_COUNT_REGISTER = 7
ACQ_DONE_COUNT_REGISTER = 8
RD_DATA_MOVING_COUNT_REGISTER = 9
RD_QDMA_DONE_COUNT_REGISTER = 10
RD_FITTING_COUNT_REGISTER = 11
RD_INITIATED_COUNT_REGISTER = 12
DAS_STATUS_REGISTER = 13
DAS_TEMPERATURE_REGISTER = 14
HEATER_CNTRL_SENSOR_REGISTER = 15
CONVERSION_LASER1_THERM_CONSTA_REGISTER = 16
CONVERSION_LASER1_THERM_CONSTB_REGISTER = 17
CONVERSION_LASER1_THERM_CONSTC_REGISTER = 18
CONVERSION_LASER1_CURRENT_SLOPE_REGISTER = 19
CONVERSION_LASER1_CURRENT_OFFSET_REGISTER = 20
LASER1_RESISTANCE_REGISTER = 21
LASER1_TEMPERATURE_REGISTER = 22
LASER1_THERMISTOR_SERIES_RESISTANCE_REGISTER = 23
LASER1_TEC_REGISTER = 24
LASER1_MANUAL_TEC_REGISTER = 25
LASER1_TEMP_CNTRL_STATE_REGISTER = 26
LASER1_TEMP_CNTRL_SETPOINT_REGISTER = 27
LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER = 28
LASER1_TEMP_CNTRL_TOLERANCE_REGISTER = 29
LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER = 30
LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER = 31
LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER = 32
LASER1_TEMP_CNTRL_H_REGISTER = 33
LASER1_TEMP_CNTRL_K_REGISTER = 34
LASER1_TEMP_CNTRL_TI_REGISTER = 35
LASER1_TEMP_CNTRL_TD_REGISTER = 36
LASER1_TEMP_CNTRL_B_REGISTER = 37
LASER1_TEMP_CNTRL_C_REGISTER = 38
LASER1_TEMP_CNTRL_N_REGISTER = 39
LASER1_TEMP_CNTRL_S_REGISTER = 40
LASER1_TEMP_CNTRL_FFWD_REGISTER = 41
LASER1_TEMP_CNTRL_AMIN_REGISTER = 42
LASER1_TEMP_CNTRL_AMAX_REGISTER = 43
LASER1_TEMP_CNTRL_IMAX_REGISTER = 44
LASER1_TEC_PRBS_GENPOLY_REGISTER = 45
LASER1_TEC_PRBS_AMPLITUDE_REGISTER = 46
LASER1_TEC_PRBS_MEAN_REGISTER = 47
LASER1_TEC_MONITOR_REGISTER = 48
LASER1_CURRENT_CNTRL_STATE_REGISTER = 49
LASER1_MANUAL_COARSE_CURRENT_REGISTER = 50
LASER1_MANUAL_FINE_CURRENT_REGISTER = 51
LASER1_CURRENT_SWEEP_MIN_REGISTER = 52
LASER1_CURRENT_SWEEP_MAX_REGISTER = 53
LASER1_CURRENT_SWEEP_INCR_REGISTER = 54
LASER1_CURRENT_MONITOR_REGISTER = 55
LASER1_EXTRA_COARSE_SCALE_REGISTER = 56
LASER1_EXTRA_FINE_SCALE_REGISTER = 57
LASER1_EXTRA_OFFSET_REGISTER = 58
CONVERSION_LASER2_THERM_CONSTA_REGISTER = 59
CONVERSION_LASER2_THERM_CONSTB_REGISTER = 60
CONVERSION_LASER2_THERM_CONSTC_REGISTER = 61
CONVERSION_LASER2_CURRENT_SLOPE_REGISTER = 62
CONVERSION_LASER2_CURRENT_OFFSET_REGISTER = 63
LASER2_RESISTANCE_REGISTER = 64
LASER2_TEMPERATURE_REGISTER = 65
LASER2_THERMISTOR_SERIES_RESISTANCE_REGISTER = 66
LASER2_TEC_REGISTER = 67
LASER2_MANUAL_TEC_REGISTER = 68
LASER2_TEMP_CNTRL_STATE_REGISTER = 69
LASER2_TEMP_CNTRL_SETPOINT_REGISTER = 70
LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER = 71
LASER2_TEMP_CNTRL_TOLERANCE_REGISTER = 72
LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER = 73
LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER = 74
LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER = 75
LASER2_TEMP_CNTRL_H_REGISTER = 76
LASER2_TEMP_CNTRL_K_REGISTER = 77
LASER2_TEMP_CNTRL_TI_REGISTER = 78
LASER2_TEMP_CNTRL_TD_REGISTER = 79
LASER2_TEMP_CNTRL_B_REGISTER = 80
LASER2_TEMP_CNTRL_C_REGISTER = 81
LASER2_TEMP_CNTRL_N_REGISTER = 82
LASER2_TEMP_CNTRL_S_REGISTER = 83
LASER2_TEMP_CNTRL_FFWD_REGISTER = 84
LASER2_TEMP_CNTRL_AMIN_REGISTER = 85
LASER2_TEMP_CNTRL_AMAX_REGISTER = 86
LASER2_TEMP_CNTRL_IMAX_REGISTER = 87
LASER2_TEC_PRBS_GENPOLY_REGISTER = 88
LASER2_TEC_PRBS_AMPLITUDE_REGISTER = 89
LASER2_TEC_PRBS_MEAN_REGISTER = 90
LASER2_TEC_MONITOR_REGISTER = 91
LASER2_CURRENT_CNTRL_STATE_REGISTER = 92
LASER2_MANUAL_COARSE_CURRENT_REGISTER = 93
LASER2_MANUAL_FINE_CURRENT_REGISTER = 94
LASER2_CURRENT_SWEEP_MIN_REGISTER = 95
LASER2_CURRENT_SWEEP_MAX_REGISTER = 96
LASER2_CURRENT_SWEEP_INCR_REGISTER = 97
LASER2_CURRENT_MONITOR_REGISTER = 98
LASER2_EXTRA_COARSE_SCALE_REGISTER = 99
LASER2_EXTRA_FINE_SCALE_REGISTER = 100
LASER2_EXTRA_OFFSET_REGISTER = 101
CONVERSION_LASER3_THERM_CONSTA_REGISTER = 102
CONVERSION_LASER3_THERM_CONSTB_REGISTER = 103
CONVERSION_LASER3_THERM_CONSTC_REGISTER = 104
CONVERSION_LASER3_CURRENT_SLOPE_REGISTER = 105
CONVERSION_LASER3_CURRENT_OFFSET_REGISTER = 106
LASER3_RESISTANCE_REGISTER = 107
LASER3_TEMPERATURE_REGISTER = 108
LASER3_THERMISTOR_SERIES_RESISTANCE_REGISTER = 109
LASER3_TEC_REGISTER = 110
LASER3_MANUAL_TEC_REGISTER = 111
LASER3_TEMP_CNTRL_STATE_REGISTER = 112
LASER3_TEMP_CNTRL_SETPOINT_REGISTER = 113
LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER = 114
LASER3_TEMP_CNTRL_TOLERANCE_REGISTER = 115
LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER = 116
LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER = 117
LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER = 118
LASER3_TEMP_CNTRL_H_REGISTER = 119
LASER3_TEMP_CNTRL_K_REGISTER = 120
LASER3_TEMP_CNTRL_TI_REGISTER = 121
LASER3_TEMP_CNTRL_TD_REGISTER = 122
LASER3_TEMP_CNTRL_B_REGISTER = 123
LASER3_TEMP_CNTRL_C_REGISTER = 124
LASER3_TEMP_CNTRL_N_REGISTER = 125
LASER3_TEMP_CNTRL_S_REGISTER = 126
LASER3_TEMP_CNTRL_FFWD_REGISTER = 127
LASER3_TEMP_CNTRL_AMIN_REGISTER = 128
LASER3_TEMP_CNTRL_AMAX_REGISTER = 129
LASER3_TEMP_CNTRL_IMAX_REGISTER = 130
LASER3_TEC_PRBS_GENPOLY_REGISTER = 131
LASER3_TEC_PRBS_AMPLITUDE_REGISTER = 132
LASER3_TEC_PRBS_MEAN_REGISTER = 133
LASER3_TEC_MONITOR_REGISTER = 134
LASER3_CURRENT_CNTRL_STATE_REGISTER = 135
LASER3_MANUAL_COARSE_CURRENT_REGISTER = 136
LASER3_MANUAL_FINE_CURRENT_REGISTER = 137
LASER3_CURRENT_SWEEP_MIN_REGISTER = 138
LASER3_CURRENT_SWEEP_MAX_REGISTER = 139
LASER3_CURRENT_SWEEP_INCR_REGISTER = 140
LASER3_CURRENT_MONITOR_REGISTER = 141
LASER3_EXTRA_COARSE_SCALE_REGISTER = 142
LASER3_EXTRA_FINE_SCALE_REGISTER = 143
LASER3_EXTRA_OFFSET_REGISTER = 144
CONVERSION_LASER4_THERM_CONSTA_REGISTER = 145
CONVERSION_LASER4_THERM_CONSTB_REGISTER = 146
CONVERSION_LASER4_THERM_CONSTC_REGISTER = 147
CONVERSION_LASER4_CURRENT_SLOPE_REGISTER = 148
CONVERSION_LASER4_CURRENT_OFFSET_REGISTER = 149
LASER4_RESISTANCE_REGISTER = 150
LASER4_TEMPERATURE_REGISTER = 151
LASER4_THERMISTOR_SERIES_RESISTANCE_REGISTER = 152
LASER4_TEC_REGISTER = 153
LASER4_MANUAL_TEC_REGISTER = 154
LASER4_TEMP_CNTRL_STATE_REGISTER = 155
LASER4_TEMP_CNTRL_SETPOINT_REGISTER = 156
LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER = 157
LASER4_TEMP_CNTRL_TOLERANCE_REGISTER = 158
LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER = 159
LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER = 160
LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER = 161
LASER4_TEMP_CNTRL_H_REGISTER = 162
LASER4_TEMP_CNTRL_K_REGISTER = 163
LASER4_TEMP_CNTRL_TI_REGISTER = 164
LASER4_TEMP_CNTRL_TD_REGISTER = 165
LASER4_TEMP_CNTRL_B_REGISTER = 166
LASER4_TEMP_CNTRL_C_REGISTER = 167
LASER4_TEMP_CNTRL_N_REGISTER = 168
LASER4_TEMP_CNTRL_S_REGISTER = 169
LASER4_TEMP_CNTRL_FFWD_REGISTER = 170
LASER4_TEMP_CNTRL_AMIN_REGISTER = 171
LASER4_TEMP_CNTRL_AMAX_REGISTER = 172
LASER4_TEMP_CNTRL_IMAX_REGISTER = 173
LASER4_TEC_PRBS_GENPOLY_REGISTER = 174
LASER4_TEC_PRBS_AMPLITUDE_REGISTER = 175
LASER4_TEC_PRBS_MEAN_REGISTER = 176
LASER4_TEC_MONITOR_REGISTER = 177
LASER4_CURRENT_CNTRL_STATE_REGISTER = 178
LASER4_MANUAL_COARSE_CURRENT_REGISTER = 179
LASER4_MANUAL_FINE_CURRENT_REGISTER = 180
LASER4_CURRENT_SWEEP_MIN_REGISTER = 181
LASER4_CURRENT_SWEEP_MAX_REGISTER = 182
LASER4_CURRENT_SWEEP_INCR_REGISTER = 183
LASER4_CURRENT_MONITOR_REGISTER = 184
LASER4_EXTRA_COARSE_SCALE_REGISTER = 185
LASER4_EXTRA_FINE_SCALE_REGISTER = 186
LASER4_EXTRA_OFFSET_REGISTER = 187
CONVERSION_ETALON_THERM_CONSTA_REGISTER = 188
CONVERSION_ETALON_THERM_CONSTB_REGISTER = 189
CONVERSION_ETALON_THERM_CONSTC_REGISTER = 190
ETALON_RESISTANCE_REGISTER = 191
ETALON_TEMPERATURE_REGISTER = 192
ETALON_THERMISTOR_SERIES_RESISTANCE_REGISTER = 193
CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER = 194
CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER = 195
CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER = 196
WARM_BOX_RESISTANCE_REGISTER = 197
WARM_BOX_TEMPERATURE_REGISTER = 198
WARM_BOX_THERMISTOR_SERIES_RESISTANCE_REGISTER = 199
WARM_BOX_TEC_REGISTER = 200
WARM_BOX_MANUAL_TEC_REGISTER = 201
WARM_BOX_TEMP_CNTRL_STATE_REGISTER = 202
WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER = 203
WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER = 204
WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER = 205
WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER = 206
WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER = 207
WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER = 208
WARM_BOX_TEMP_CNTRL_H_REGISTER = 209
WARM_BOX_TEMP_CNTRL_K_REGISTER = 210
WARM_BOX_TEMP_CNTRL_TI_REGISTER = 211
WARM_BOX_TEMP_CNTRL_TD_REGISTER = 212
WARM_BOX_TEMP_CNTRL_B_REGISTER = 213
WARM_BOX_TEMP_CNTRL_C_REGISTER = 214
WARM_BOX_TEMP_CNTRL_N_REGISTER = 215
WARM_BOX_TEMP_CNTRL_S_REGISTER = 216
WARM_BOX_TEMP_CNTRL_FFWD_REGISTER = 217
WARM_BOX_TEMP_CNTRL_AMIN_REGISTER = 218
WARM_BOX_TEMP_CNTRL_AMAX_REGISTER = 219
WARM_BOX_TEMP_CNTRL_IMAX_REGISTER = 220
WARM_BOX_TEC_PRBS_GENPOLY_REGISTER = 221
WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER = 222
WARM_BOX_TEC_PRBS_MEAN_REGISTER = 223
WARM_BOX_MAX_HEATSINK_TEMP_REGISTER = 224
CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER = 225
CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER = 226
CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER = 227
WARM_BOX_HEATSINK_RESISTANCE_REGISTER = 228
WARM_BOX_HEATSINK_TEMPERATURE_REGISTER = 229
WARM_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER = 230
CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER = 231
CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER = 232
CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER = 233
HOT_BOX_HEATSINK_RESISTANCE_REGISTER = 234
HOT_BOX_HEATSINK_TEMPERATURE_REGISTER = 235
HOT_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER = 236
CONVERSION_CAVITY_THERM_CONSTA_REGISTER = 237
CONVERSION_CAVITY_THERM_CONSTB_REGISTER = 238
CONVERSION_CAVITY_THERM_CONSTC_REGISTER = 239
CAVITY_RESISTANCE_REGISTER = 240
CAVITY_TEMPERATURE_REGISTER = 241
CAVITY_THERMISTOR_SERIES_RESISTANCE_REGISTER = 242
CONVERSION_CAVITY_THERM1_CONSTA_REGISTER = 243
CONVERSION_CAVITY_THERM1_CONSTB_REGISTER = 244
CONVERSION_CAVITY_THERM1_CONSTC_REGISTER = 245
CAVITY_RESISTANCE1_REGISTER = 246
CAVITY_TEMPERATURE1_REGISTER = 247
CAVITY_THERMISTOR1_SERIES_RESISTANCE_REGISTER = 248
CONVERSION_CAVITY_THERM2_CONSTA_REGISTER = 249
CONVERSION_CAVITY_THERM2_CONSTB_REGISTER = 250
CONVERSION_CAVITY_THERM2_CONSTC_REGISTER = 251
CAVITY_RESISTANCE2_REGISTER = 252
CAVITY_TEMPERATURE2_REGISTER = 253
CAVITY_THERMISTOR2_SERIES_RESISTANCE_REGISTER = 254
CONVERSION_CAVITY_THERM3_CONSTA_REGISTER = 255
CONVERSION_CAVITY_THERM3_CONSTB_REGISTER = 256
CONVERSION_CAVITY_THERM3_CONSTC_REGISTER = 257
CAVITY_RESISTANCE3_REGISTER = 258
CAVITY_TEMPERATURE3_REGISTER = 259
CAVITY_THERMISTOR3_SERIES_RESISTANCE_REGISTER = 260
CONVERSION_CAVITY_THERM4_CONSTA_REGISTER = 261
CONVERSION_CAVITY_THERM4_CONSTB_REGISTER = 262
CONVERSION_CAVITY_THERM4_CONSTC_REGISTER = 263
CAVITY_RESISTANCE4_REGISTER = 264
CAVITY_TEMPERATURE4_REGISTER = 265
CAVITY_THERMISTOR4_SERIES_RESISTANCE_REGISTER = 266
CAVITY_TEC_REGISTER = 267
CAVITY_MANUAL_TEC_REGISTER = 268
CAVITY_TEMP_CNTRL_STATE_REGISTER = 269
CAVITY_TEMP_CNTRL_SETPOINT_REGISTER = 270
CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER = 271
CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER = 272
CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER = 273
CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER = 274
CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER = 275
CAVITY_TEMP_CNTRL_H_REGISTER = 276
CAVITY_TEMP_CNTRL_K_REGISTER = 277
CAVITY_TEMP_CNTRL_TI_REGISTER = 278
CAVITY_TEMP_CNTRL_TD_REGISTER = 279
CAVITY_TEMP_CNTRL_B_REGISTER = 280
CAVITY_TEMP_CNTRL_C_REGISTER = 281
CAVITY_TEMP_CNTRL_N_REGISTER = 282
CAVITY_TEMP_CNTRL_S_REGISTER = 283
CAVITY_TEMP_CNTRL_FFWD_REGISTER = 284
CAVITY_TEMP_CNTRL_AMIN_REGISTER = 285
CAVITY_TEMP_CNTRL_AMAX_REGISTER = 286
CAVITY_TEMP_CNTRL_IMAX_REGISTER = 287
CAVITY_TEC_PRBS_GENPOLY_REGISTER = 288
CAVITY_TEC_PRBS_AMPLITUDE_REGISTER = 289
CAVITY_TEC_PRBS_MEAN_REGISTER = 290
CAVITY_MAX_HEATSINK_TEMP_REGISTER = 291
HEATER_MARK_REGISTER = 292
HEATER_MANUAL_MARK_REGISTER = 293
HEATER_TEMP_CNTRL_STATE_REGISTER = 294
HEATER_TEMP_CNTRL_SETPOINT_REGISTER = 295
HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER = 296
HEATER_TEMP_CNTRL_TOLERANCE_REGISTER = 297
HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER = 298
HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER = 299
HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER = 300
HEATER_TEMP_CNTRL_H_REGISTER = 301
HEATER_TEMP_CNTRL_K_REGISTER = 302
HEATER_TEMP_CNTRL_TI_REGISTER = 303
HEATER_TEMP_CNTRL_TD_REGISTER = 304
HEATER_TEMP_CNTRL_B_REGISTER = 305
HEATER_TEMP_CNTRL_C_REGISTER = 306
HEATER_TEMP_CNTRL_N_REGISTER = 307
HEATER_TEMP_CNTRL_S_REGISTER = 308
HEATER_TEMP_CNTRL_AMIN_REGISTER = 309
HEATER_TEMP_CNTRL_AMAX_REGISTER = 310
HEATER_TEMP_CNTRL_IMAX_REGISTER = 311
HEATER_PRBS_GENPOLY_REGISTER = 312
HEATER_PRBS_AMPLITUDE_REGISTER = 313
HEATER_PRBS_MEAN_REGISTER = 314
HEATER_CUTOFF_REGISTER = 315
CAVITY_PRESSURE_ADC_REGISTER = 316
CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER = 317
CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER = 318
CAVITY_PRESSURE_REGISTER = 319
AMBIENT_PRESSURE_ADC_REGISTER = 320
CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER = 321
CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER = 322
AMBIENT_PRESSURE_REGISTER = 323
ANALYZER_TUNING_MODE_REGISTER = 324
TUNER_SWEEP_RAMP_HIGH_REGISTER = 325
TUNER_SWEEP_RAMP_LOW_REGISTER = 326
TUNER_WINDOW_RAMP_HIGH_REGISTER = 327
TUNER_WINDOW_RAMP_LOW_REGISTER = 328
TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER = 329
TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER = 330
TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER = 331
TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER = 332
TUNER_DITHER_MEDIAN_COUNT_REGISTER = 333
RDFITTER_MINLOSS_REGISTER = 334
RDFITTER_MAXLOSS_REGISTER = 335
RDFITTER_LATEST_LOSS_REGISTER = 336
RDFITTER_IMPROVEMENT_STEPS_REGISTER = 337
RDFITTER_START_SAMPLE_REGISTER = 338
RDFITTER_FRACTIONAL_THRESHOLD_REGISTER = 339
RDFITTER_ABSOLUTE_THRESHOLD_REGISTER = 340
RDFITTER_NUMBER_OF_POINTS_REGISTER = 341
RDFITTER_MAX_E_FOLDINGS_REGISTER = 342
RDFITTER_META_BACKOFF_REGISTER = 343
RDFITTER_META_SAMPLES_REGISTER = 344
SPECT_CNTRL_STATE_REGISTER = 345
SPECT_CNTRL_MODE_REGISTER = 346
SPECT_CNTRL_ACTIVE_SCHEME_REGISTER = 347
SPECT_CNTRL_NEXT_SCHEME_REGISTER = 348
SPECT_CNTRL_SCHEME_ITER_REGISTER = 349
SPECT_CNTRL_SCHEME_ROW_REGISTER = 350
SPECT_CNTRL_DWELL_COUNT_REGISTER = 351
SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER = 352
SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER = 353
SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER = 354
VIRTUAL_LASER_REGISTER = 355
PZT_INCR_PER_CAVITY_FSR = 356
PZT_OFFSET_UPDATE_FACTOR = 357
PZT_OFFSET_VIRTUAL_LASER1 = 358
PZT_OFFSET_VIRTUAL_LASER2 = 359
PZT_OFFSET_VIRTUAL_LASER3 = 360
PZT_OFFSET_VIRTUAL_LASER4 = 361
PZT_OFFSET_VIRTUAL_LASER5 = 362
PZT_OFFSET_VIRTUAL_LASER6 = 363
PZT_OFFSET_VIRTUAL_LASER7 = 364
PZT_OFFSET_VIRTUAL_LASER8 = 365
SCHEME_OFFSET_VIRTUAL_LASER1 = 366
SCHEME_OFFSET_VIRTUAL_LASER2 = 367
SCHEME_OFFSET_VIRTUAL_LASER3 = 368
SCHEME_OFFSET_VIRTUAL_LASER4 = 369
SCHEME_OFFSET_VIRTUAL_LASER5 = 370
SCHEME_OFFSET_VIRTUAL_LASER6 = 371
SCHEME_OFFSET_VIRTUAL_LASER7 = 372
SCHEME_OFFSET_VIRTUAL_LASER8 = 373
VALVE_CNTRL_STATE_REGISTER = 374
VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER = 375
VALVE_CNTRL_USER_INLET_VALVE_REGISTER = 376
VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER = 377
VALVE_CNTRL_INLET_VALVE_REGISTER = 378
VALVE_CNTRL_OUTLET_VALVE_REGISTER = 379
VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER = 380
VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER = 381
VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER = 382
VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER = 383
VALVE_CNTRL_INLET_VALVE_MIN_REGISTER = 384
VALVE_CNTRL_INLET_VALVE_MAX_REGISTER = 385
VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER = 386
VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER = 387
VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER = 388
VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER = 389
VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER = 390
VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER = 391
VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER = 392
VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER = 393
VALVE_CNTRL_THRESHOLD_STATE_REGISTER = 394
VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER = 395
VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER = 396
VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER = 397
VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER = 398
VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER = 399
VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER = 400
VALVE_CNTRL_SEQUENCE_STEP_REGISTER = 401
VALVE_CNTRL_SOLENOID_VALVES_REGISTER = 402
VALVE_CNTRL_MPV_POSITION_REGISTER = 403
TEC_CNTRL_REGISTER = 404
SENTRY_UPPER_LIMIT_TRIPPED_REGISTER = 405
SENTRY_LOWER_LIMIT_TRIPPED_REGISTER = 406
SENTRY_LASER1_TEMPERATURE_MIN_REGISTER = 407
SENTRY_LASER1_TEMPERATURE_MAX_REGISTER = 408
SENTRY_LASER2_TEMPERATURE_MIN_REGISTER = 409
SENTRY_LASER2_TEMPERATURE_MAX_REGISTER = 410
SENTRY_LASER3_TEMPERATURE_MIN_REGISTER = 411
SENTRY_LASER3_TEMPERATURE_MAX_REGISTER = 412
SENTRY_LASER4_TEMPERATURE_MIN_REGISTER = 413
SENTRY_LASER4_TEMPERATURE_MAX_REGISTER = 414
SENTRY_ETALON_TEMPERATURE_MIN_REGISTER = 415
SENTRY_ETALON_TEMPERATURE_MAX_REGISTER = 416
SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER = 417
SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER = 418
SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER = 419
SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER = 420
SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER = 421
SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER = 422
SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER = 423
SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER = 424
SENTRY_DAS_TEMPERATURE_MIN_REGISTER = 425
SENTRY_DAS_TEMPERATURE_MAX_REGISTER = 426
SENTRY_LASER1_CURRENT_MIN_REGISTER = 427
SENTRY_LASER1_CURRENT_MAX_REGISTER = 428
SENTRY_LASER2_CURRENT_MIN_REGISTER = 429
SENTRY_LASER2_CURRENT_MAX_REGISTER = 430
SENTRY_LASER3_CURRENT_MIN_REGISTER = 431
SENTRY_LASER3_CURRENT_MAX_REGISTER = 432
SENTRY_LASER4_CURRENT_MIN_REGISTER = 433
SENTRY_LASER4_CURRENT_MAX_REGISTER = 434
SENTRY_CAVITY_PRESSURE_MIN_REGISTER = 435
SENTRY_CAVITY_PRESSURE_MAX_REGISTER = 436
SENTRY_AMBIENT_PRESSURE_MIN_REGISTER = 437
SENTRY_AMBIENT_PRESSURE_MAX_REGISTER = 438
FAN_CNTRL_STATE_REGISTER = 439
FAN_CNTRL_TEMPERATURE_REGISTER = 440
KEEP_ALIVE_REGISTER = 441
LOSS_BUFFER_0_REGISTER = 442
LOSS_BUFFER_1_REGISTER = 443
LOSS_BUFFER_2_REGISTER = 444
LOSS_BUFFER_3_REGISTER = 445
LOSS_BUFFER_4_REGISTER = 446
LOSS_BUFFER_5_REGISTER = 447
LOSS_BUFFER_6_REGISTER = 448
LOSS_BUFFER_7_REGISTER = 449
PROCESSED_LOSS_1_REGISTER = 450
PROCESSED_LOSS_2_REGISTER = 451
PROCESSED_LOSS_3_REGISTER = 452
PROCESSED_LOSS_4_REGISTER = 453
PEAK_DETECT_CNTRL_STATE_REGISTER = 454
PEAK_DETECT_CNTRL_BACKGROUND_SAMPLES_REGISTER = 455
PEAK_DETECT_CNTRL_BACKGROUND_REGISTER = 456
PEAK_DETECT_CNTRL_UPPER_THRESHOLD_REGISTER = 457
PEAK_DETECT_CNTRL_LOWER_THRESHOLD_1_REGISTER = 458
PEAK_DETECT_CNTRL_LOWER_THRESHOLD_2_REGISTER = 459
PEAK_DETECT_CNTRL_THRESHOLD_FACTOR_REGISTER = 460
PEAK_DETECT_CNTRL_ACTIVE_SIZE_REGISTER = 461
PEAK_DETECT_CNTRL_POST_PEAK_SAMPLES_REGISTER = 462
PEAK_DETECT_CNTRL_CANCELLING_SAMPLES_REGISTER = 463
PEAK_DETECT_CNTRL_TRIGGER_CONDITION_REGISTER = 464
PEAK_DETECT_CNTRL_TRIGGER_DELAY_REGISTER = 465
PEAK_DETECT_CNTRL_TRIGGERED_DURATION_REGISTER = 466
PEAK_DETECT_CNTRL_TRANSITIONING_DURATION_REGISTER = 467
PEAK_DETECT_CNTRL_TRANSITIONING_HOLDOFF_REGISTER = 468
PEAK_DETECT_CNTRL_HOLDING_MAX_LOSS_REGISTER = 469
PEAK_DETECT_CNTRL_HOLDING_DURATION_REGISTER = 470
PEAK_DETECT_CNTRL_PRIMING_DURATION_REGISTER = 471
PEAK_DETECT_CNTRL_PURGING_DURATION_REGISTER = 472
PEAK_DETECT_CNTRL_REMAINING_SAMPLES_REGISTER = 473
PEAK_DETECT_CNTRL_IDLE_VALVE_MASK_AND_VALUE_REGISTER = 474
PEAK_DETECT_CNTRL_ARMED_VALVE_MASK_AND_VALUE_REGISTER = 475
PEAK_DETECT_CNTRL_TRIGGER_PENDING_VALVE_MASK_AND_VALUE_REGISTER = 476
PEAK_DETECT_CNTRL_TRIGGERED_VALVE_MASK_AND_VALUE_REGISTER = 477
PEAK_DETECT_CNTRL_TRANSITIONING_VALVE_MASK_AND_VALUE_REGISTER = 478
PEAK_DETECT_CNTRL_HOLDING_VALVE_MASK_AND_VALUE_REGISTER = 479
PEAK_DETECT_CNTRL_INACTIVE_VALVE_MASK_AND_VALUE_REGISTER = 480
PEAK_DETECT_CNTRL_CANCELLING_VALVE_MASK_AND_VALUE_REGISTER = 481
PEAK_DETECT_CNTRL_PRIMING_VALVE_MASK_AND_VALUE_REGISTER = 482
PEAK_DETECT_CNTRL_PURGING_VALVE_MASK_AND_VALUE_REGISTER = 483
PEAK_DETECT_CNTRL_INJECTION_PENDING_VALVE_MASK_AND_VALUE_REGISTER = 484
FLOW1_REGISTER = 485
CONVERSION_FLOW1_SCALE_REGISTER = 486
CONVERSION_FLOW1_OFFSET_REGISTER = 487
RDD_BALANCE_REGISTER = 488
RDD_GAIN_REGISTER = 489
FLOW_CNTRL_STATE_REGISTER = 490
FLOW_CNTRL_SETPOINT_REGISTER = 491
FLOW_CNTRL_GAIN_REGISTER = 492
FLOW_0_SETPOINT_REGISTER = 493
FLOW_1_SETPOINT_REGISTER = 494
FLOW_2_SETPOINT_REGISTER = 495
FLOW_3_SETPOINT_REGISTER = 496
BATTERY_MONITOR_STATUS_REGISTER = 497
BATTERY_MONITOR_CHARGE_REGISTER = 498
BATTERY_MONITOR_VOLTAGE_REGISTER = 499
BATTERY_MONITOR_CURRENT_REGISTER = 500
BATTERY_MONITOR_TEMPERATURE_REGISTER = 501
ACCELEROMETER_X_REGISTER = 502
ACCELEROMETER_Y_REGISTER = 503
ACCELEROMETER_Z_REGISTER = 504

# Dictionary for accessing registers by name, list of register information and dictionary of register initial values
registerByName = {}
registerInfo = []
registerInitialValue={}

# Dictionaries for accessing I2C devices
i2cByIndex = {}
i2cByIndex[0] = 'LOGIC_EEPROM'
i2cByIndex[1] = 'LASER1_THERMISTOR_ADC'
i2cByIndex[2] = 'LASER1_CURRENT_ADC'
i2cByIndex[3] = 'LASER1_EEPROM'
i2cByIndex[4] = 'LASER2_THERMISTOR_ADC'
i2cByIndex[5] = 'LASER2_CURRENT_ADC'
i2cByIndex[6] = 'LASER2_EEPROM'
i2cByIndex[7] = 'LASER3_THERMISTOR_ADC'
i2cByIndex[8] = 'LASER3_CURRENT_ADC'
i2cByIndex[9] = 'LASER3_EEPROM'
i2cByIndex[10] = 'LASER4_THERMISTOR_ADC'
i2cByIndex[11] = 'LASER4_CURRENT_ADC'
i2cByIndex[12] = 'LASER4_EEPROM'
i2cByIndex[13] = 'ETALON_THERMISTOR_ADC'
i2cByIndex[14] = 'WARM_BOX_HEATSINK_THERMISTOR_ADC'
i2cByIndex[15] = 'WARM_BOX_THERMISTOR_ADC'
i2cByIndex[16] = 'WLM_EEPROM'
i2cByIndex[17] = 'ACCELEROMETER'
i2cByIndex[18] = 'CAVITY_THERMISTOR_1_ADC'
i2cByIndex[19] = 'CAVITY_THERMISTOR_2_ADC'
i2cByIndex[20] = 'CAVITY_PRESSURE_ADC'
i2cByIndex[21] = 'AMBIENT_PRESSURE_ADC'
i2cByIndex[22] = 'CAVITY_THERMISTOR_3_ADC'
i2cByIndex[23] = 'CAVITY_THERMISTOR_4_ADC'
i2cByIndex[24] = 'HOT_BOX_HEATSINK_THERMISTOR_ADC'
i2cByIndex[25] = 'RDD_POTENTIOMETERS'
i2cByIndex[26] = 'FLOW1_SENSOR'
i2cByIndex[27] = 'DAS_TEMP_SENSOR'
i2cByIndex[28] = 'VALVE_PUMP_TEC_PORT'
i2cByIndex[29] = 'ANALOG_INTERFACE'
i2cByIndex[30] = 'BATTERY_MONITOR'
i2cByIndex[31] = 'CHAIN0_MUX'
i2cByIndex[32] = 'CHAIN1_MUX'

#i2cByIdent tuple is (index,chain,mux,address)
i2cByIdent = {}
i2cByIdent['LOGIC_EEPROM'] = (0, 0, -1, 0x55)
i2cByIdent['LASER1_THERMISTOR_ADC'] = (1, 0, 0, 0x26)
i2cByIdent['LASER1_CURRENT_ADC'] = (2, 0, 0, 0x14)
i2cByIdent['LASER1_EEPROM'] = (3, 0, 0, 0x50)
i2cByIdent['LASER2_THERMISTOR_ADC'] = (4, 0, 1, 0x26)
i2cByIdent['LASER2_CURRENT_ADC'] = (5, 0, 1, 0x14)
i2cByIdent['LASER2_EEPROM'] = (6, 0, 1, 0x50)
i2cByIdent['LASER3_THERMISTOR_ADC'] = (7, 0, 2, 0x26)
i2cByIdent['LASER3_CURRENT_ADC'] = (8, 0, 2, 0x14)
i2cByIdent['LASER3_EEPROM'] = (9, 0, 2, 0x50)
i2cByIdent['LASER4_THERMISTOR_ADC'] = (10, 0, 3, 0x26)
i2cByIdent['LASER4_CURRENT_ADC'] = (11, 0, 3, 0x14)
i2cByIdent['LASER4_EEPROM'] = (12, 0, 3, 0x50)
i2cByIdent['ETALON_THERMISTOR_ADC'] = (13, 1, 0, 0x27)
i2cByIdent['WARM_BOX_HEATSINK_THERMISTOR_ADC'] = (14, 1, 0, 0x26)
i2cByIdent['WARM_BOX_THERMISTOR_ADC'] = (15, 1, 0, 0x15)
i2cByIdent['WLM_EEPROM'] = (16, 1, 0, 0x50)
i2cByIdent['ACCELEROMETER'] = (17, 0, 7, 0x53)
i2cByIdent['CAVITY_THERMISTOR_1_ADC'] = (18, 0, 7, 0x27)
i2cByIdent['CAVITY_THERMISTOR_2_ADC'] = (19, 0, 7, 0x26)
i2cByIdent['CAVITY_PRESSURE_ADC'] = (20, 0, 7, 0x24)
i2cByIdent['AMBIENT_PRESSURE_ADC'] = (21, 0, 7, 0x17)
i2cByIdent['CAVITY_THERMISTOR_3_ADC'] = (22, 0, 7, 0x14)
i2cByIdent['CAVITY_THERMISTOR_4_ADC'] = (23, 0, 7, 0x15)
i2cByIdent['HOT_BOX_HEATSINK_THERMISTOR_ADC'] = (24, 0, 7, 0x54)
i2cByIdent['RDD_POTENTIOMETERS'] = (25, 0, 7, 0x2c)
i2cByIdent['FLOW1_SENSOR'] = (26, 0, 7, 0x49)
i2cByIdent['DAS_TEMP_SENSOR'] = (27, 0, -1, 0x4e)
i2cByIdent['VALVE_PUMP_TEC_PORT'] = (28, 1, 4, 0x70)
i2cByIdent['ANALOG_INTERFACE'] = (29, 0, 4, 0x10)
i2cByIdent['BATTERY_MONITOR'] = (30, 0, 5, 0x64)
i2cByIdent['CHAIN0_MUX'] = (31, 0, -1, 0x70)
i2cByIdent['CHAIN1_MUX'] = (32, 1, -1, 0x71)

#I2C channel definitions
I2C_LOGIC_EEPROM = 0
I2C_LASER1_THERMISTOR_ADC = 1
I2C_LASER1_CURRENT_ADC = 2
I2C_LASER1_EEPROM = 3
I2C_LASER2_THERMISTOR_ADC = 4
I2C_LASER2_CURRENT_ADC = 5
I2C_LASER2_EEPROM = 6
I2C_LASER3_THERMISTOR_ADC = 7
I2C_LASER3_CURRENT_ADC = 8
I2C_LASER3_EEPROM = 9
I2C_LASER4_THERMISTOR_ADC = 10
I2C_LASER4_CURRENT_ADC = 11
I2C_LASER4_EEPROM = 12
I2C_ETALON_THERMISTOR_ADC = 13
I2C_WARM_BOX_HEATSINK_THERMISTOR_ADC = 14
I2C_WARM_BOX_THERMISTOR_ADC = 15
I2C_WLM_EEPROM = 16
I2C_ACCELEROMETER = 17
I2C_CAVITY_THERMISTOR_1_ADC = 18
I2C_CAVITY_THERMISTOR_2_ADC = 19
I2C_CAVITY_PRESSURE_ADC = 20
I2C_AMBIENT_PRESSURE_ADC = 21
I2C_CAVITY_THERMISTOR_3_ADC = 22
I2C_CAVITY_THERMISTOR_4_ADC = 23
I2C_HOT_BOX_HEATSINK_THERMISTOR_ADC = 24
I2C_RDD_POTENTIOMETERS = 25
I2C_FLOW1_SENSOR = 26
I2C_DAS_TEMP_SENSOR = 27
I2C_VALVE_PUMP_TEC_PORT = 28
I2C_ANALOG_INTERFACE = 29
I2C_BATTERY_MONITOR = 30
I2C_CHAIN0_MUX = 31
I2C_CHAIN1_MUX = 32


registerByName["NOOP_REGISTER"] = NOOP_REGISTER
registerInfo.append(RegInfo("NOOP_REGISTER",c_uint,0,1.0,"rw"))
registerInitialValue["NOOP_REGISTER"] = 0xABCD1234
registerByName["VERIFY_INIT_REGISTER"] = VERIFY_INIT_REGISTER
registerInfo.append(RegInfo("VERIFY_INIT_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["VERIFY_INIT_REGISTER"] = 0x19680511
registerByName["COMM_STATUS_REGISTER"] = COMM_STATUS_REGISTER
registerInfo.append(RegInfo("COMM_STATUS_REGISTER",c_uint,0,1.0,"r"))
registerByName["TIMESTAMP_LSB_REGISTER"] = TIMESTAMP_LSB_REGISTER
registerInfo.append(RegInfo("TIMESTAMP_LSB_REGISTER",c_uint,0,1.0,"r"))
registerByName["TIMESTAMP_MSB_REGISTER"] = TIMESTAMP_MSB_REGISTER
registerInfo.append(RegInfo("TIMESTAMP_MSB_REGISTER",c_uint,0,1.0,"r"))
registerByName["SCHEDULER_CONTROL_REGISTER"] = SCHEDULER_CONTROL_REGISTER
registerInfo.append(RegInfo("SCHEDULER_CONTROL_REGISTER",c_uint,0,1.0,"rw"))
registerInitialValue["SCHEDULER_CONTROL_REGISTER"] = 0
registerByName["HARDWARE_PRESENT_REGISTER"] = HARDWARE_PRESENT_REGISTER
registerInfo.append(RegInfo("HARDWARE_PRESENT_REGISTER",c_uint,0,1.0,"rw"))
registerInitialValue["HARDWARE_PRESENT_REGISTER"] = 0
registerByName["RD_IRQ_COUNT_REGISTER"] = RD_IRQ_COUNT_REGISTER
registerInfo.append(RegInfo("RD_IRQ_COUNT_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["RD_IRQ_COUNT_REGISTER"] = 0
registerByName["ACQ_DONE_COUNT_REGISTER"] = ACQ_DONE_COUNT_REGISTER
registerInfo.append(RegInfo("ACQ_DONE_COUNT_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["ACQ_DONE_COUNT_REGISTER"] = 0
registerByName["RD_DATA_MOVING_COUNT_REGISTER"] = RD_DATA_MOVING_COUNT_REGISTER
registerInfo.append(RegInfo("RD_DATA_MOVING_COUNT_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["RD_DATA_MOVING_COUNT_REGISTER"] = 0
registerByName["RD_QDMA_DONE_COUNT_REGISTER"] = RD_QDMA_DONE_COUNT_REGISTER
registerInfo.append(RegInfo("RD_QDMA_DONE_COUNT_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["RD_QDMA_DONE_COUNT_REGISTER"] = 0
registerByName["RD_FITTING_COUNT_REGISTER"] = RD_FITTING_COUNT_REGISTER
registerInfo.append(RegInfo("RD_FITTING_COUNT_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["RD_FITTING_COUNT_REGISTER"] = 0
registerByName["RD_INITIATED_COUNT_REGISTER"] = RD_INITIATED_COUNT_REGISTER
registerInfo.append(RegInfo("RD_INITIATED_COUNT_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["RD_INITIATED_COUNT_REGISTER"] = 0
registerByName["DAS_STATUS_REGISTER"] = DAS_STATUS_REGISTER
registerInfo.append(RegInfo("DAS_STATUS_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["DAS_STATUS_REGISTER"] = 0
registerByName["DAS_TEMPERATURE_REGISTER"] = DAS_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("DAS_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["DAS_TEMPERATURE_REGISTER"] = 20.0
registerByName["HEATER_CNTRL_SENSOR_REGISTER"] = HEATER_CNTRL_SENSOR_REGISTER
registerInfo.append(RegInfo("HEATER_CNTRL_SENSOR_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["HEATER_CNTRL_SENSOR_REGISTER"] = 0.0
registerByName["CONVERSION_LASER1_THERM_CONSTA_REGISTER"] = CONVERSION_LASER1_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER1_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER1_THERM_CONSTA_REGISTER"] = 0.00112789997365
registerByName["CONVERSION_LASER1_THERM_CONSTB_REGISTER"] = CONVERSION_LASER1_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER1_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER1_THERM_CONSTB_REGISTER"] = 0.000234289997024
registerByName["CONVERSION_LASER1_THERM_CONSTC_REGISTER"] = CONVERSION_LASER1_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER1_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER1_THERM_CONSTC_REGISTER"] = 8.72979981636e-008
registerByName["CONVERSION_LASER1_CURRENT_SLOPE_REGISTER"] = CONVERSION_LASER1_CURRENT_SLOPE_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER1_CURRENT_SLOPE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER1_CURRENT_SLOPE_REGISTER"] = 7.62939e-3
registerByName["CONVERSION_LASER1_CURRENT_OFFSET_REGISTER"] = CONVERSION_LASER1_CURRENT_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER1_CURRENT_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER1_CURRENT_OFFSET_REGISTER"] = 0.0
registerByName["LASER1_RESISTANCE_REGISTER"] = LASER1_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER1_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER1_TEMPERATURE_REGISTER"] = LASER1_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("LASER1_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER1_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = LASER1_THERMISTOR_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER1_THERMISTOR_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = 30000
registerByName["LASER1_TEC_REGISTER"] = LASER1_TEC_REGISTER
registerInfo.append(RegInfo("LASER1_TEC_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LASER1_TEC_REGISTER"] = 32768.0
registerByName["LASER1_MANUAL_TEC_REGISTER"] = LASER1_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("LASER1_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_MANUAL_TEC_REGISTER"] = 32768.0
registerByName["LASER1_TEMP_CNTRL_STATE_REGISTER"] = LASER1_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_STATE_REGISTER"] = TEMP_CNTRL_DisabledState
registerByName["LASER1_TEMP_CNTRL_SETPOINT_REGISTER"] = LASER1_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_SETPOINT_REGISTER"] = 25.0
registerByName["LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = 25.0
registerByName["LASER1_TEMP_CNTRL_TOLERANCE_REGISTER"] = LASER1_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_TOLERANCE_REGISTER"] = 0.1
registerByName["LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = 30.0
registerByName["LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = 20.0
registerByName["LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = 0.05
registerByName["LASER1_TEMP_CNTRL_H_REGISTER"] = LASER1_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_H_REGISTER"] = 0.2
registerByName["LASER1_TEMP_CNTRL_K_REGISTER"] = LASER1_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_K_REGISTER"] = 0.0
registerByName["LASER1_TEMP_CNTRL_TI_REGISTER"] = LASER1_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_TI_REGISTER"] = 1000.0
registerByName["LASER1_TEMP_CNTRL_TD_REGISTER"] = LASER1_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_TD_REGISTER"] = 0.0
registerByName["LASER1_TEMP_CNTRL_B_REGISTER"] = LASER1_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_B_REGISTER"] = 1.0
registerByName["LASER1_TEMP_CNTRL_C_REGISTER"] = LASER1_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_C_REGISTER"] = 1.0
registerByName["LASER1_TEMP_CNTRL_N_REGISTER"] = LASER1_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_N_REGISTER"] = 100.0
registerByName["LASER1_TEMP_CNTRL_S_REGISTER"] = LASER1_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_S_REGISTER"] = 5.0
registerByName["LASER1_TEMP_CNTRL_FFWD_REGISTER"] = LASER1_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_FFWD_REGISTER"] = 0.0
registerByName["LASER1_TEMP_CNTRL_AMIN_REGISTER"] = LASER1_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_AMIN_REGISTER"] = 5.0
registerByName["LASER1_TEMP_CNTRL_AMAX_REGISTER"] = LASER1_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_AMAX_REGISTER"] = 55000.0
registerByName["LASER1_TEMP_CNTRL_IMAX_REGISTER"] = LASER1_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("LASER1_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEMP_CNTRL_IMAX_REGISTER"] = 10000.0
registerByName["LASER1_TEC_PRBS_GENPOLY_REGISTER"] = LASER1_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("LASER1_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["LASER1_TEC_PRBS_GENPOLY_REGISTER"] = 0x481
registerByName["LASER1_TEC_PRBS_AMPLITUDE_REGISTER"] = LASER1_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("LASER1_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEC_PRBS_AMPLITUDE_REGISTER"] = 5000.0
registerByName["LASER1_TEC_PRBS_MEAN_REGISTER"] = LASER1_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("LASER1_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_TEC_PRBS_MEAN_REGISTER"] = 40000.0
registerByName["LASER1_TEC_MONITOR_REGISTER"] = LASER1_TEC_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER1_TEC_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER1_TEC_MONITOR_REGISTER"] = 0.0
registerByName["LASER1_CURRENT_CNTRL_STATE_REGISTER"] = LASER1_CURRENT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER1_CURRENT_CNTRL_STATE_REGISTER",LASER_CURRENT_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["LASER1_CURRENT_CNTRL_STATE_REGISTER"] = LASER_CURRENT_CNTRL_DisabledState
registerByName["LASER1_MANUAL_COARSE_CURRENT_REGISTER"] = LASER1_MANUAL_COARSE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER1_MANUAL_COARSE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_MANUAL_COARSE_CURRENT_REGISTER"] = 0.0
registerByName["LASER1_MANUAL_FINE_CURRENT_REGISTER"] = LASER1_MANUAL_FINE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER1_MANUAL_FINE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_MANUAL_FINE_CURRENT_REGISTER"] = 0.0
registerByName["LASER1_CURRENT_SWEEP_MIN_REGISTER"] = LASER1_CURRENT_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER1_CURRENT_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_CURRENT_SWEEP_MIN_REGISTER"] = 0.0
registerByName["LASER1_CURRENT_SWEEP_MAX_REGISTER"] = LASER1_CURRENT_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER1_CURRENT_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_CURRENT_SWEEP_MAX_REGISTER"] = 0.0
registerByName["LASER1_CURRENT_SWEEP_INCR_REGISTER"] = LASER1_CURRENT_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER1_CURRENT_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_CURRENT_SWEEP_INCR_REGISTER"] = 0.0
registerByName["LASER1_CURRENT_MONITOR_REGISTER"] = LASER1_CURRENT_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER1_CURRENT_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER1_CURRENT_MONITOR_REGISTER"] = 0.0
registerByName["LASER1_EXTRA_COARSE_SCALE_REGISTER"] = LASER1_EXTRA_COARSE_SCALE_REGISTER
registerInfo.append(RegInfo("LASER1_EXTRA_COARSE_SCALE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_EXTRA_COARSE_SCALE_REGISTER"] = 1.0
registerByName["LASER1_EXTRA_FINE_SCALE_REGISTER"] = LASER1_EXTRA_FINE_SCALE_REGISTER
registerInfo.append(RegInfo("LASER1_EXTRA_FINE_SCALE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER1_EXTRA_FINE_SCALE_REGISTER"] = 0.0
registerByName["LASER1_EXTRA_OFFSET_REGISTER"] = LASER1_EXTRA_OFFSET_REGISTER
registerInfo.append(RegInfo("LASER1_EXTRA_OFFSET_REGISTER",c_int,1,1.0,"rw"))
registerInitialValue["LASER1_EXTRA_OFFSET_REGISTER"] = 0
registerByName["CONVERSION_LASER2_THERM_CONSTA_REGISTER"] = CONVERSION_LASER2_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER2_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER2_THERM_CONSTA_REGISTER"] = 0.00112789997365
registerByName["CONVERSION_LASER2_THERM_CONSTB_REGISTER"] = CONVERSION_LASER2_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER2_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER2_THERM_CONSTB_REGISTER"] = 0.000234289997024
registerByName["CONVERSION_LASER2_THERM_CONSTC_REGISTER"] = CONVERSION_LASER2_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER2_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER2_THERM_CONSTC_REGISTER"] = 8.72979981636e-008
registerByName["CONVERSION_LASER2_CURRENT_SLOPE_REGISTER"] = CONVERSION_LASER2_CURRENT_SLOPE_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER2_CURRENT_SLOPE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER2_CURRENT_SLOPE_REGISTER"] = 7.62939e-3
registerByName["CONVERSION_LASER2_CURRENT_OFFSET_REGISTER"] = CONVERSION_LASER2_CURRENT_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER2_CURRENT_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER2_CURRENT_OFFSET_REGISTER"] = 0.0
registerByName["LASER2_RESISTANCE_REGISTER"] = LASER2_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER2_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER2_TEMPERATURE_REGISTER"] = LASER2_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("LASER2_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER2_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = LASER2_THERMISTOR_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER2_THERMISTOR_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = 30000
registerByName["LASER2_TEC_REGISTER"] = LASER2_TEC_REGISTER
registerInfo.append(RegInfo("LASER2_TEC_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LASER2_TEC_REGISTER"] = 32768.0
registerByName["LASER2_MANUAL_TEC_REGISTER"] = LASER2_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("LASER2_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_MANUAL_TEC_REGISTER"] = 32768.0
registerByName["LASER2_TEMP_CNTRL_STATE_REGISTER"] = LASER2_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_STATE_REGISTER"] = TEMP_CNTRL_DisabledState
registerByName["LASER2_TEMP_CNTRL_SETPOINT_REGISTER"] = LASER2_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_SETPOINT_REGISTER"] = 25.0
registerByName["LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = 25.0
registerByName["LASER2_TEMP_CNTRL_TOLERANCE_REGISTER"] = LASER2_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_TOLERANCE_REGISTER"] = 0.1
registerByName["LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = 30.0
registerByName["LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = 20.0
registerByName["LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = 0.05
registerByName["LASER2_TEMP_CNTRL_H_REGISTER"] = LASER2_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_H_REGISTER"] = 0.2
registerByName["LASER2_TEMP_CNTRL_K_REGISTER"] = LASER2_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_K_REGISTER"] = 0.0
registerByName["LASER2_TEMP_CNTRL_TI_REGISTER"] = LASER2_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_TI_REGISTER"] = 1000.0
registerByName["LASER2_TEMP_CNTRL_TD_REGISTER"] = LASER2_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_TD_REGISTER"] = 0.0
registerByName["LASER2_TEMP_CNTRL_B_REGISTER"] = LASER2_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_B_REGISTER"] = 1.0
registerByName["LASER2_TEMP_CNTRL_C_REGISTER"] = LASER2_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_C_REGISTER"] = 1.0
registerByName["LASER2_TEMP_CNTRL_N_REGISTER"] = LASER2_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_N_REGISTER"] = 100.0
registerByName["LASER2_TEMP_CNTRL_S_REGISTER"] = LASER2_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_S_REGISTER"] = 5.0
registerByName["LASER2_TEMP_CNTRL_FFWD_REGISTER"] = LASER2_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_FFWD_REGISTER"] = 0.0
registerByName["LASER2_TEMP_CNTRL_AMIN_REGISTER"] = LASER2_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_AMIN_REGISTER"] = 5.0
registerByName["LASER2_TEMP_CNTRL_AMAX_REGISTER"] = LASER2_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_AMAX_REGISTER"] = 55000.0
registerByName["LASER2_TEMP_CNTRL_IMAX_REGISTER"] = LASER2_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("LASER2_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEMP_CNTRL_IMAX_REGISTER"] = 10000.0
registerByName["LASER2_TEC_PRBS_GENPOLY_REGISTER"] = LASER2_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("LASER2_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["LASER2_TEC_PRBS_GENPOLY_REGISTER"] = 0x481
registerByName["LASER2_TEC_PRBS_AMPLITUDE_REGISTER"] = LASER2_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("LASER2_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEC_PRBS_AMPLITUDE_REGISTER"] = 5000.0
registerByName["LASER2_TEC_PRBS_MEAN_REGISTER"] = LASER2_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("LASER2_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_TEC_PRBS_MEAN_REGISTER"] = 40000.0
registerByName["LASER2_TEC_MONITOR_REGISTER"] = LASER2_TEC_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER2_TEC_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER2_TEC_MONITOR_REGISTER"] = 0.0
registerByName["LASER2_CURRENT_CNTRL_STATE_REGISTER"] = LASER2_CURRENT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER2_CURRENT_CNTRL_STATE_REGISTER",LASER_CURRENT_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["LASER2_CURRENT_CNTRL_STATE_REGISTER"] = LASER_CURRENT_CNTRL_DisabledState
registerByName["LASER2_MANUAL_COARSE_CURRENT_REGISTER"] = LASER2_MANUAL_COARSE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER2_MANUAL_COARSE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_MANUAL_COARSE_CURRENT_REGISTER"] = 0.0
registerByName["LASER2_MANUAL_FINE_CURRENT_REGISTER"] = LASER2_MANUAL_FINE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER2_MANUAL_FINE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_MANUAL_FINE_CURRENT_REGISTER"] = 0.0
registerByName["LASER2_CURRENT_SWEEP_MIN_REGISTER"] = LASER2_CURRENT_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER2_CURRENT_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_CURRENT_SWEEP_MIN_REGISTER"] = 0.0
registerByName["LASER2_CURRENT_SWEEP_MAX_REGISTER"] = LASER2_CURRENT_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER2_CURRENT_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_CURRENT_SWEEP_MAX_REGISTER"] = 0.0
registerByName["LASER2_CURRENT_SWEEP_INCR_REGISTER"] = LASER2_CURRENT_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER2_CURRENT_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_CURRENT_SWEEP_INCR_REGISTER"] = 0.0
registerByName["LASER2_CURRENT_MONITOR_REGISTER"] = LASER2_CURRENT_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER2_CURRENT_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER2_CURRENT_MONITOR_REGISTER"] = 0.0
registerByName["LASER2_EXTRA_COARSE_SCALE_REGISTER"] = LASER2_EXTRA_COARSE_SCALE_REGISTER
registerInfo.append(RegInfo("LASER2_EXTRA_COARSE_SCALE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_EXTRA_COARSE_SCALE_REGISTER"] = 1.0
registerByName["LASER2_EXTRA_FINE_SCALE_REGISTER"] = LASER2_EXTRA_FINE_SCALE_REGISTER
registerInfo.append(RegInfo("LASER2_EXTRA_FINE_SCALE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER2_EXTRA_FINE_SCALE_REGISTER"] = 0.0
registerByName["LASER2_EXTRA_OFFSET_REGISTER"] = LASER2_EXTRA_OFFSET_REGISTER
registerInfo.append(RegInfo("LASER2_EXTRA_OFFSET_REGISTER",c_int,1,1.0,"rw"))
registerInitialValue["LASER2_EXTRA_OFFSET_REGISTER"] = 0
registerByName["CONVERSION_LASER3_THERM_CONSTA_REGISTER"] = CONVERSION_LASER3_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER3_THERM_CONSTA_REGISTER"] = 0.00112789997365
registerByName["CONVERSION_LASER3_THERM_CONSTB_REGISTER"] = CONVERSION_LASER3_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER3_THERM_CONSTB_REGISTER"] = 0.000234289997024
registerByName["CONVERSION_LASER3_THERM_CONSTC_REGISTER"] = CONVERSION_LASER3_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER3_THERM_CONSTC_REGISTER"] = 8.72979981636e-008
registerByName["CONVERSION_LASER3_CURRENT_SLOPE_REGISTER"] = CONVERSION_LASER3_CURRENT_SLOPE_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_CURRENT_SLOPE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER3_CURRENT_SLOPE_REGISTER"] = 7.62939e-3
registerByName["CONVERSION_LASER3_CURRENT_OFFSET_REGISTER"] = CONVERSION_LASER3_CURRENT_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER3_CURRENT_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER3_CURRENT_OFFSET_REGISTER"] = 0.0
registerByName["LASER3_RESISTANCE_REGISTER"] = LASER3_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER3_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER3_TEMPERATURE_REGISTER"] = LASER3_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("LASER3_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER3_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = LASER3_THERMISTOR_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER3_THERMISTOR_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = 30000
registerByName["LASER3_TEC_REGISTER"] = LASER3_TEC_REGISTER
registerInfo.append(RegInfo("LASER3_TEC_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LASER3_TEC_REGISTER"] = 32768.0
registerByName["LASER3_MANUAL_TEC_REGISTER"] = LASER3_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("LASER3_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_MANUAL_TEC_REGISTER"] = 32768.0
registerByName["LASER3_TEMP_CNTRL_STATE_REGISTER"] = LASER3_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_STATE_REGISTER"] = TEMP_CNTRL_DisabledState
registerByName["LASER3_TEMP_CNTRL_SETPOINT_REGISTER"] = LASER3_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_SETPOINT_REGISTER"] = 25.0
registerByName["LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = 25.0
registerByName["LASER3_TEMP_CNTRL_TOLERANCE_REGISTER"] = LASER3_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_TOLERANCE_REGISTER"] = 0.1
registerByName["LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = 30.0
registerByName["LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = 20.0
registerByName["LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = 0.05
registerByName["LASER3_TEMP_CNTRL_H_REGISTER"] = LASER3_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_H_REGISTER"] = 0.2
registerByName["LASER3_TEMP_CNTRL_K_REGISTER"] = LASER3_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_K_REGISTER"] = 0.0
registerByName["LASER3_TEMP_CNTRL_TI_REGISTER"] = LASER3_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_TI_REGISTER"] = 1000.0
registerByName["LASER3_TEMP_CNTRL_TD_REGISTER"] = LASER3_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_TD_REGISTER"] = 0.0
registerByName["LASER3_TEMP_CNTRL_B_REGISTER"] = LASER3_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_B_REGISTER"] = 1.0
registerByName["LASER3_TEMP_CNTRL_C_REGISTER"] = LASER3_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_C_REGISTER"] = 1.0
registerByName["LASER3_TEMP_CNTRL_N_REGISTER"] = LASER3_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_N_REGISTER"] = 100.0
registerByName["LASER3_TEMP_CNTRL_S_REGISTER"] = LASER3_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_S_REGISTER"] = 5.0
registerByName["LASER3_TEMP_CNTRL_FFWD_REGISTER"] = LASER3_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_FFWD_REGISTER"] = 0.0
registerByName["LASER3_TEMP_CNTRL_AMIN_REGISTER"] = LASER3_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_AMIN_REGISTER"] = 5.0
registerByName["LASER3_TEMP_CNTRL_AMAX_REGISTER"] = LASER3_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_AMAX_REGISTER"] = 55000.0
registerByName["LASER3_TEMP_CNTRL_IMAX_REGISTER"] = LASER3_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("LASER3_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEMP_CNTRL_IMAX_REGISTER"] = 10000.0
registerByName["LASER3_TEC_PRBS_GENPOLY_REGISTER"] = LASER3_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("LASER3_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["LASER3_TEC_PRBS_GENPOLY_REGISTER"] = 0x481
registerByName["LASER3_TEC_PRBS_AMPLITUDE_REGISTER"] = LASER3_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("LASER3_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEC_PRBS_AMPLITUDE_REGISTER"] = 5000.0
registerByName["LASER3_TEC_PRBS_MEAN_REGISTER"] = LASER3_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("LASER3_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_TEC_PRBS_MEAN_REGISTER"] = 40000.0
registerByName["LASER3_TEC_MONITOR_REGISTER"] = LASER3_TEC_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER3_TEC_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER3_TEC_MONITOR_REGISTER"] = 0.0
registerByName["LASER3_CURRENT_CNTRL_STATE_REGISTER"] = LASER3_CURRENT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER3_CURRENT_CNTRL_STATE_REGISTER",LASER_CURRENT_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["LASER3_CURRENT_CNTRL_STATE_REGISTER"] = LASER_CURRENT_CNTRL_DisabledState
registerByName["LASER3_MANUAL_COARSE_CURRENT_REGISTER"] = LASER3_MANUAL_COARSE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER3_MANUAL_COARSE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_MANUAL_COARSE_CURRENT_REGISTER"] = 0.0
registerByName["LASER3_MANUAL_FINE_CURRENT_REGISTER"] = LASER3_MANUAL_FINE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER3_MANUAL_FINE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_MANUAL_FINE_CURRENT_REGISTER"] = 0.0
registerByName["LASER3_CURRENT_SWEEP_MIN_REGISTER"] = LASER3_CURRENT_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER3_CURRENT_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_CURRENT_SWEEP_MIN_REGISTER"] = 0.0
registerByName["LASER3_CURRENT_SWEEP_MAX_REGISTER"] = LASER3_CURRENT_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER3_CURRENT_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_CURRENT_SWEEP_MAX_REGISTER"] = 0.0
registerByName["LASER3_CURRENT_SWEEP_INCR_REGISTER"] = LASER3_CURRENT_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER3_CURRENT_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_CURRENT_SWEEP_INCR_REGISTER"] = 0.0
registerByName["LASER3_CURRENT_MONITOR_REGISTER"] = LASER3_CURRENT_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER3_CURRENT_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER3_CURRENT_MONITOR_REGISTER"] = 0.0
registerByName["LASER3_EXTRA_COARSE_SCALE_REGISTER"] = LASER3_EXTRA_COARSE_SCALE_REGISTER
registerInfo.append(RegInfo("LASER3_EXTRA_COARSE_SCALE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_EXTRA_COARSE_SCALE_REGISTER"] = 1.0
registerByName["LASER3_EXTRA_FINE_SCALE_REGISTER"] = LASER3_EXTRA_FINE_SCALE_REGISTER
registerInfo.append(RegInfo("LASER3_EXTRA_FINE_SCALE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER3_EXTRA_FINE_SCALE_REGISTER"] = 0.0
registerByName["LASER3_EXTRA_OFFSET_REGISTER"] = LASER3_EXTRA_OFFSET_REGISTER
registerInfo.append(RegInfo("LASER3_EXTRA_OFFSET_REGISTER",c_int,1,1.0,"rw"))
registerInitialValue["LASER3_EXTRA_OFFSET_REGISTER"] = 0
registerByName["CONVERSION_LASER4_THERM_CONSTA_REGISTER"] = CONVERSION_LASER4_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER4_THERM_CONSTA_REGISTER"] = 0.00112789997365
registerByName["CONVERSION_LASER4_THERM_CONSTB_REGISTER"] = CONVERSION_LASER4_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER4_THERM_CONSTB_REGISTER"] = 0.000234289997024
registerByName["CONVERSION_LASER4_THERM_CONSTC_REGISTER"] = CONVERSION_LASER4_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER4_THERM_CONSTC_REGISTER"] = 8.72979981636e-008
registerByName["CONVERSION_LASER4_CURRENT_SLOPE_REGISTER"] = CONVERSION_LASER4_CURRENT_SLOPE_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_CURRENT_SLOPE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER4_CURRENT_SLOPE_REGISTER"] = 7.62939e-3
registerByName["CONVERSION_LASER4_CURRENT_OFFSET_REGISTER"] = CONVERSION_LASER4_CURRENT_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_LASER4_CURRENT_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_LASER4_CURRENT_OFFSET_REGISTER"] = 0.0
registerByName["LASER4_RESISTANCE_REGISTER"] = LASER4_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER4_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER4_TEMPERATURE_REGISTER"] = LASER4_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("LASER4_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["LASER4_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = LASER4_THERMISTOR_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("LASER4_THERMISTOR_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = 30000
registerByName["LASER4_TEC_REGISTER"] = LASER4_TEC_REGISTER
registerInfo.append(RegInfo("LASER4_TEC_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LASER4_TEC_REGISTER"] = 32768.0
registerByName["LASER4_MANUAL_TEC_REGISTER"] = LASER4_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("LASER4_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_MANUAL_TEC_REGISTER"] = 32768.0
registerByName["LASER4_TEMP_CNTRL_STATE_REGISTER"] = LASER4_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_STATE_REGISTER"] = TEMP_CNTRL_DisabledState
registerByName["LASER4_TEMP_CNTRL_SETPOINT_REGISTER"] = LASER4_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_SETPOINT_REGISTER"] = 25.0
registerByName["LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = 25.0
registerByName["LASER4_TEMP_CNTRL_TOLERANCE_REGISTER"] = LASER4_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_TOLERANCE_REGISTER"] = 0.1
registerByName["LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = 30.0
registerByName["LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = 20.0
registerByName["LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = 0.05
registerByName["LASER4_TEMP_CNTRL_H_REGISTER"] = LASER4_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_H_REGISTER"] = 0.2
registerByName["LASER4_TEMP_CNTRL_K_REGISTER"] = LASER4_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_K_REGISTER"] = 0.0
registerByName["LASER4_TEMP_CNTRL_TI_REGISTER"] = LASER4_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_TI_REGISTER"] = 1000.0
registerByName["LASER4_TEMP_CNTRL_TD_REGISTER"] = LASER4_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_TD_REGISTER"] = 0.0
registerByName["LASER4_TEMP_CNTRL_B_REGISTER"] = LASER4_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_B_REGISTER"] = 1.0
registerByName["LASER4_TEMP_CNTRL_C_REGISTER"] = LASER4_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_C_REGISTER"] = 1.0
registerByName["LASER4_TEMP_CNTRL_N_REGISTER"] = LASER4_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_N_REGISTER"] = 100.0
registerByName["LASER4_TEMP_CNTRL_S_REGISTER"] = LASER4_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_S_REGISTER"] = 5.0
registerByName["LASER4_TEMP_CNTRL_FFWD_REGISTER"] = LASER4_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_FFWD_REGISTER"] = 0.0
registerByName["LASER4_TEMP_CNTRL_AMIN_REGISTER"] = LASER4_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_AMIN_REGISTER"] = 5.0
registerByName["LASER4_TEMP_CNTRL_AMAX_REGISTER"] = LASER4_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_AMAX_REGISTER"] = 55000.0
registerByName["LASER4_TEMP_CNTRL_IMAX_REGISTER"] = LASER4_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("LASER4_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEMP_CNTRL_IMAX_REGISTER"] = 10000.0
registerByName["LASER4_TEC_PRBS_GENPOLY_REGISTER"] = LASER4_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("LASER4_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["LASER4_TEC_PRBS_GENPOLY_REGISTER"] = 0x481
registerByName["LASER4_TEC_PRBS_AMPLITUDE_REGISTER"] = LASER4_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("LASER4_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEC_PRBS_AMPLITUDE_REGISTER"] = 5000.0
registerByName["LASER4_TEC_PRBS_MEAN_REGISTER"] = LASER4_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("LASER4_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_TEC_PRBS_MEAN_REGISTER"] = 40000.0
registerByName["LASER4_TEC_MONITOR_REGISTER"] = LASER4_TEC_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER4_TEC_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER4_TEC_MONITOR_REGISTER"] = 0.0
registerByName["LASER4_CURRENT_CNTRL_STATE_REGISTER"] = LASER4_CURRENT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("LASER4_CURRENT_CNTRL_STATE_REGISTER",LASER_CURRENT_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["LASER4_CURRENT_CNTRL_STATE_REGISTER"] = LASER_CURRENT_CNTRL_DisabledState
registerByName["LASER4_MANUAL_COARSE_CURRENT_REGISTER"] = LASER4_MANUAL_COARSE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER4_MANUAL_COARSE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_MANUAL_COARSE_CURRENT_REGISTER"] = 0.0
registerByName["LASER4_MANUAL_FINE_CURRENT_REGISTER"] = LASER4_MANUAL_FINE_CURRENT_REGISTER
registerInfo.append(RegInfo("LASER4_MANUAL_FINE_CURRENT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_MANUAL_FINE_CURRENT_REGISTER"] = 0.0
registerByName["LASER4_CURRENT_SWEEP_MIN_REGISTER"] = LASER4_CURRENT_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("LASER4_CURRENT_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_CURRENT_SWEEP_MIN_REGISTER"] = 0.0
registerByName["LASER4_CURRENT_SWEEP_MAX_REGISTER"] = LASER4_CURRENT_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("LASER4_CURRENT_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_CURRENT_SWEEP_MAX_REGISTER"] = 0.0
registerByName["LASER4_CURRENT_SWEEP_INCR_REGISTER"] = LASER4_CURRENT_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("LASER4_CURRENT_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_CURRENT_SWEEP_INCR_REGISTER"] = 0.0
registerByName["LASER4_CURRENT_MONITOR_REGISTER"] = LASER4_CURRENT_MONITOR_REGISTER
registerInfo.append(RegInfo("LASER4_CURRENT_MONITOR_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["LASER4_CURRENT_MONITOR_REGISTER"] = 0.0
registerByName["LASER4_EXTRA_COARSE_SCALE_REGISTER"] = LASER4_EXTRA_COARSE_SCALE_REGISTER
registerInfo.append(RegInfo("LASER4_EXTRA_COARSE_SCALE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_EXTRA_COARSE_SCALE_REGISTER"] = 1.0
registerByName["LASER4_EXTRA_FINE_SCALE_REGISTER"] = LASER4_EXTRA_FINE_SCALE_REGISTER
registerInfo.append(RegInfo("LASER4_EXTRA_FINE_SCALE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["LASER4_EXTRA_FINE_SCALE_REGISTER"] = 0.0
registerByName["LASER4_EXTRA_OFFSET_REGISTER"] = LASER4_EXTRA_OFFSET_REGISTER
registerInfo.append(RegInfo("LASER4_EXTRA_OFFSET_REGISTER",c_int,1,1.0,"rw"))
registerInitialValue["LASER4_EXTRA_OFFSET_REGISTER"] = 0
registerByName["CONVERSION_ETALON_THERM_CONSTA_REGISTER"] = CONVERSION_ETALON_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_ETALON_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_ETALON_THERM_CONSTA_REGISTER"] = 0.00112789997365
registerByName["CONVERSION_ETALON_THERM_CONSTB_REGISTER"] = CONVERSION_ETALON_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_ETALON_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_ETALON_THERM_CONSTB_REGISTER"] = 0.000234289997024
registerByName["CONVERSION_ETALON_THERM_CONSTC_REGISTER"] = CONVERSION_ETALON_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_ETALON_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_ETALON_THERM_CONSTC_REGISTER"] = 8.72979981636e-008
registerByName["ETALON_RESISTANCE_REGISTER"] = ETALON_RESISTANCE_REGISTER
registerInfo.append(RegInfo("ETALON_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["ETALON_TEMPERATURE_REGISTER"] = ETALON_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("ETALON_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["ETALON_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = ETALON_THERMISTOR_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("ETALON_THERMISTOR_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["ETALON_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = 30000
registerByName["CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER"] = CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER"] = 0.00112789997365
registerByName["CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER"] = CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER"] = 0.000234289997024
registerByName["CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER"] = CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER"] = 8.72979981636e-008
registerByName["WARM_BOX_RESISTANCE_REGISTER"] = WARM_BOX_RESISTANCE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["WARM_BOX_TEMPERATURE_REGISTER"] = WARM_BOX_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["WARM_BOX_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = WARM_BOX_THERMISTOR_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_THERMISTOR_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = 30000
registerByName["WARM_BOX_TEC_REGISTER"] = WARM_BOX_TEC_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEC_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["WARM_BOX_TEC_REGISTER"] = 32768.0
registerByName["WARM_BOX_MANUAL_TEC_REGISTER"] = WARM_BOX_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("WARM_BOX_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_MANUAL_TEC_REGISTER"] = 32768.0
registerByName["WARM_BOX_TEMP_CNTRL_STATE_REGISTER"] = WARM_BOX_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_STATE_REGISTER"] = TEMP_CNTRL_DisabledState
registerByName["WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER"] = WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER"] = 25.0
registerByName["WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = 25.0
registerByName["WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER"] = WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER"] = 0.1
registerByName["WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = 30.0
registerByName["WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = 20.0
registerByName["WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = 0.05
registerByName["WARM_BOX_TEMP_CNTRL_H_REGISTER"] = WARM_BOX_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_H_REGISTER"] = 0.2
registerByName["WARM_BOX_TEMP_CNTRL_K_REGISTER"] = WARM_BOX_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_K_REGISTER"] = 0.0
registerByName["WARM_BOX_TEMP_CNTRL_TI_REGISTER"] = WARM_BOX_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_TI_REGISTER"] = 1000.0
registerByName["WARM_BOX_TEMP_CNTRL_TD_REGISTER"] = WARM_BOX_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_TD_REGISTER"] = 0.0
registerByName["WARM_BOX_TEMP_CNTRL_B_REGISTER"] = WARM_BOX_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_B_REGISTER"] = 1.0
registerByName["WARM_BOX_TEMP_CNTRL_C_REGISTER"] = WARM_BOX_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_C_REGISTER"] = 1.0
registerByName["WARM_BOX_TEMP_CNTRL_N_REGISTER"] = WARM_BOX_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_N_REGISTER"] = 100.0
registerByName["WARM_BOX_TEMP_CNTRL_S_REGISTER"] = WARM_BOX_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_S_REGISTER"] = 5.0
registerByName["WARM_BOX_TEMP_CNTRL_FFWD_REGISTER"] = WARM_BOX_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_FFWD_REGISTER"] = 0.0
registerByName["WARM_BOX_TEMP_CNTRL_AMIN_REGISTER"] = WARM_BOX_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_AMIN_REGISTER"] = 5.0
registerByName["WARM_BOX_TEMP_CNTRL_AMAX_REGISTER"] = WARM_BOX_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_AMAX_REGISTER"] = 55000.0
registerByName["WARM_BOX_TEMP_CNTRL_IMAX_REGISTER"] = WARM_BOX_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEMP_CNTRL_IMAX_REGISTER"] = 10000.0
registerByName["WARM_BOX_TEC_PRBS_GENPOLY_REGISTER"] = WARM_BOX_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEC_PRBS_GENPOLY_REGISTER"] = 0x481
registerByName["WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER"] = WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER"] = 5000.0
registerByName["WARM_BOX_TEC_PRBS_MEAN_REGISTER"] = WARM_BOX_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("WARM_BOX_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_TEC_PRBS_MEAN_REGISTER"] = 40000.0
registerByName["WARM_BOX_MAX_HEATSINK_TEMP_REGISTER"] = WARM_BOX_MAX_HEATSINK_TEMP_REGISTER
registerInfo.append(RegInfo("WARM_BOX_MAX_HEATSINK_TEMP_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_MAX_HEATSINK_TEMP_REGISTER"] = 70.0
registerByName["CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER"] = CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER"] = 0.00112789997365
registerByName["CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER"] = CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER"] = 0.000234289997024
registerByName["CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER"] = CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER"] = 8.72979981636e-008
registerByName["WARM_BOX_HEATSINK_RESISTANCE_REGISTER"] = WARM_BOX_HEATSINK_RESISTANCE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_HEATSINK_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["WARM_BOX_HEATSINK_TEMPERATURE_REGISTER"] = WARM_BOX_HEATSINK_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_HEATSINK_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["WARM_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = WARM_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("WARM_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["WARM_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = 30000
registerByName["CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER"] = CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER"] = 0.000847030023579
registerByName["CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER"] = CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER"] = 0.000205610005651
registerByName["CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER"] = CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER"] = 9.26699996739e-008
registerByName["HOT_BOX_HEATSINK_RESISTANCE_REGISTER"] = HOT_BOX_HEATSINK_RESISTANCE_REGISTER
registerInfo.append(RegInfo("HOT_BOX_HEATSINK_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["HOT_BOX_HEATSINK_TEMPERATURE_REGISTER"] = HOT_BOX_HEATSINK_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("HOT_BOX_HEATSINK_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["HOT_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = HOT_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("HOT_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HOT_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = 124000
registerByName["CONVERSION_CAVITY_THERM_CONSTA_REGISTER"] = CONVERSION_CAVITY_THERM_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM_CONSTA_REGISTER"] = 0.000847030023579
registerByName["CONVERSION_CAVITY_THERM_CONSTB_REGISTER"] = CONVERSION_CAVITY_THERM_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM_CONSTB_REGISTER"] = 0.000205610005651
registerByName["CONVERSION_CAVITY_THERM_CONSTC_REGISTER"] = CONVERSION_CAVITY_THERM_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM_CONSTC_REGISTER"] = 9.26699996739e-008
registerByName["CAVITY_RESISTANCE_REGISTER"] = CAVITY_RESISTANCE_REGISTER
registerInfo.append(RegInfo("CAVITY_RESISTANCE_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_TEMPERATURE_REGISTER"] = CAVITY_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMPERATURE_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = CAVITY_THERMISTOR_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("CAVITY_THERMISTOR_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_THERMISTOR_SERIES_RESISTANCE_REGISTER"] = 124000
registerByName["CONVERSION_CAVITY_THERM1_CONSTA_REGISTER"] = CONVERSION_CAVITY_THERM1_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM1_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM1_CONSTA_REGISTER"] = 0.000847030023579
registerByName["CONVERSION_CAVITY_THERM1_CONSTB_REGISTER"] = CONVERSION_CAVITY_THERM1_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM1_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM1_CONSTB_REGISTER"] = 0.000205610005651
registerByName["CONVERSION_CAVITY_THERM1_CONSTC_REGISTER"] = CONVERSION_CAVITY_THERM1_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM1_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM1_CONSTC_REGISTER"] = 9.26699996739e-008
registerByName["CAVITY_RESISTANCE1_REGISTER"] = CAVITY_RESISTANCE1_REGISTER
registerInfo.append(RegInfo("CAVITY_RESISTANCE1_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_TEMPERATURE1_REGISTER"] = CAVITY_TEMPERATURE1_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMPERATURE1_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_THERMISTOR1_SERIES_RESISTANCE_REGISTER"] = CAVITY_THERMISTOR1_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("CAVITY_THERMISTOR1_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_THERMISTOR1_SERIES_RESISTANCE_REGISTER"] = 124000
registerByName["CONVERSION_CAVITY_THERM2_CONSTA_REGISTER"] = CONVERSION_CAVITY_THERM2_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM2_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM2_CONSTA_REGISTER"] = 0.000847030023579
registerByName["CONVERSION_CAVITY_THERM2_CONSTB_REGISTER"] = CONVERSION_CAVITY_THERM2_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM2_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM2_CONSTB_REGISTER"] = 0.000205610005651
registerByName["CONVERSION_CAVITY_THERM2_CONSTC_REGISTER"] = CONVERSION_CAVITY_THERM2_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM2_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM2_CONSTC_REGISTER"] = 9.26699996739e-008
registerByName["CAVITY_RESISTANCE2_REGISTER"] = CAVITY_RESISTANCE2_REGISTER
registerInfo.append(RegInfo("CAVITY_RESISTANCE2_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_TEMPERATURE2_REGISTER"] = CAVITY_TEMPERATURE2_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMPERATURE2_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_THERMISTOR2_SERIES_RESISTANCE_REGISTER"] = CAVITY_THERMISTOR2_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("CAVITY_THERMISTOR2_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_THERMISTOR2_SERIES_RESISTANCE_REGISTER"] = 124000
registerByName["CONVERSION_CAVITY_THERM3_CONSTA_REGISTER"] = CONVERSION_CAVITY_THERM3_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM3_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM3_CONSTA_REGISTER"] = 0.000847030023579
registerByName["CONVERSION_CAVITY_THERM3_CONSTB_REGISTER"] = CONVERSION_CAVITY_THERM3_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM3_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM3_CONSTB_REGISTER"] = 0.000205610005651
registerByName["CONVERSION_CAVITY_THERM3_CONSTC_REGISTER"] = CONVERSION_CAVITY_THERM3_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM3_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM3_CONSTC_REGISTER"] = 9.26699996739e-008
registerByName["CAVITY_RESISTANCE3_REGISTER"] = CAVITY_RESISTANCE3_REGISTER
registerInfo.append(RegInfo("CAVITY_RESISTANCE3_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_TEMPERATURE3_REGISTER"] = CAVITY_TEMPERATURE3_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMPERATURE3_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_THERMISTOR3_SERIES_RESISTANCE_REGISTER"] = CAVITY_THERMISTOR3_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("CAVITY_THERMISTOR3_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_THERMISTOR3_SERIES_RESISTANCE_REGISTER"] = 124000
registerByName["CONVERSION_CAVITY_THERM4_CONSTA_REGISTER"] = CONVERSION_CAVITY_THERM4_CONSTA_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM4_CONSTA_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM4_CONSTA_REGISTER"] = 0.000847030023579
registerByName["CONVERSION_CAVITY_THERM4_CONSTB_REGISTER"] = CONVERSION_CAVITY_THERM4_CONSTB_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM4_CONSTB_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM4_CONSTB_REGISTER"] = 0.000205610005651
registerByName["CONVERSION_CAVITY_THERM4_CONSTC_REGISTER"] = CONVERSION_CAVITY_THERM4_CONSTC_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_THERM4_CONSTC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_THERM4_CONSTC_REGISTER"] = 9.26699996739e-008
registerByName["CAVITY_RESISTANCE4_REGISTER"] = CAVITY_RESISTANCE4_REGISTER
registerInfo.append(RegInfo("CAVITY_RESISTANCE4_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_TEMPERATURE4_REGISTER"] = CAVITY_TEMPERATURE4_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMPERATURE4_REGISTER",c_float,0,1.0,"r"))
registerByName["CAVITY_THERMISTOR4_SERIES_RESISTANCE_REGISTER"] = CAVITY_THERMISTOR4_SERIES_RESISTANCE_REGISTER
registerInfo.append(RegInfo("CAVITY_THERMISTOR4_SERIES_RESISTANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_THERMISTOR4_SERIES_RESISTANCE_REGISTER"] = 124000
registerByName["CAVITY_TEC_REGISTER"] = CAVITY_TEC_REGISTER
registerInfo.append(RegInfo("CAVITY_TEC_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["CAVITY_TEC_REGISTER"] = 32768.0
registerByName["CAVITY_MANUAL_TEC_REGISTER"] = CAVITY_MANUAL_TEC_REGISTER
registerInfo.append(RegInfo("CAVITY_MANUAL_TEC_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_MANUAL_TEC_REGISTER"] = 32768.0
registerByName["CAVITY_TEMP_CNTRL_STATE_REGISTER"] = CAVITY_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_STATE_REGISTER"] = TEMP_CNTRL_DisabledState
registerByName["CAVITY_TEMP_CNTRL_SETPOINT_REGISTER"] = CAVITY_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_SETPOINT_REGISTER"] = 25.0
registerByName["CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = 25.0
registerByName["CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER"] = CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER"] = 0.1
registerByName["CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = 30.0
registerByName["CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = 20.0
registerByName["CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = 0.05
registerByName["CAVITY_TEMP_CNTRL_H_REGISTER"] = CAVITY_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_H_REGISTER"] = 5.0
registerByName["CAVITY_TEMP_CNTRL_K_REGISTER"] = CAVITY_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_K_REGISTER"] = 0.0
registerByName["CAVITY_TEMP_CNTRL_TI_REGISTER"] = CAVITY_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_TI_REGISTER"] = 1000.0
registerByName["CAVITY_TEMP_CNTRL_TD_REGISTER"] = CAVITY_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_TD_REGISTER"] = 0.0
registerByName["CAVITY_TEMP_CNTRL_B_REGISTER"] = CAVITY_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_B_REGISTER"] = 1.0
registerByName["CAVITY_TEMP_CNTRL_C_REGISTER"] = CAVITY_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_C_REGISTER"] = 1.0
registerByName["CAVITY_TEMP_CNTRL_N_REGISTER"] = CAVITY_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_N_REGISTER"] = 100.0
registerByName["CAVITY_TEMP_CNTRL_S_REGISTER"] = CAVITY_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_S_REGISTER"] = 5.0
registerByName["CAVITY_TEMP_CNTRL_FFWD_REGISTER"] = CAVITY_TEMP_CNTRL_FFWD_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_FFWD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_FFWD_REGISTER"] = 0.0
registerByName["CAVITY_TEMP_CNTRL_AMIN_REGISTER"] = CAVITY_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_AMIN_REGISTER"] = 5.0
registerByName["CAVITY_TEMP_CNTRL_AMAX_REGISTER"] = CAVITY_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_AMAX_REGISTER"] = 55000.0
registerByName["CAVITY_TEMP_CNTRL_IMAX_REGISTER"] = CAVITY_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("CAVITY_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEMP_CNTRL_IMAX_REGISTER"] = 10000.0
registerByName["CAVITY_TEC_PRBS_GENPOLY_REGISTER"] = CAVITY_TEC_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("CAVITY_TEC_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["CAVITY_TEC_PRBS_GENPOLY_REGISTER"] = 0x481
registerByName["CAVITY_TEC_PRBS_AMPLITUDE_REGISTER"] = CAVITY_TEC_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("CAVITY_TEC_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEC_PRBS_AMPLITUDE_REGISTER"] = 5000.0
registerByName["CAVITY_TEC_PRBS_MEAN_REGISTER"] = CAVITY_TEC_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("CAVITY_TEC_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_TEC_PRBS_MEAN_REGISTER"] = 40000.0
registerByName["CAVITY_MAX_HEATSINK_TEMP_REGISTER"] = CAVITY_MAX_HEATSINK_TEMP_REGISTER
registerInfo.append(RegInfo("CAVITY_MAX_HEATSINK_TEMP_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CAVITY_MAX_HEATSINK_TEMP_REGISTER"] = 70.0
registerByName["HEATER_MARK_REGISTER"] = HEATER_MARK_REGISTER
registerInfo.append(RegInfo("HEATER_MARK_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["HEATER_MARK_REGISTER"] = 0.0
registerByName["HEATER_MANUAL_MARK_REGISTER"] = HEATER_MANUAL_MARK_REGISTER
registerInfo.append(RegInfo("HEATER_MANUAL_MARK_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_MANUAL_MARK_REGISTER"] = 4000.0
registerByName["HEATER_TEMP_CNTRL_STATE_REGISTER"] = HEATER_TEMP_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_STATE_REGISTER",TEMP_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_STATE_REGISTER"] = TEMP_CNTRL_DisabledState
registerByName["HEATER_TEMP_CNTRL_SETPOINT_REGISTER"] = HEATER_TEMP_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_SETPOINT_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_SETPOINT_REGISTER"] = 0.0
registerByName["HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER"] = 0.0
registerByName["HEATER_TEMP_CNTRL_TOLERANCE_REGISTER"] = HEATER_TEMP_CNTRL_TOLERANCE_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_TOLERANCE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_TOLERANCE_REGISTER"] = 0.1
registerByName["HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER"] = 2.0
registerByName["HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER"] = -2.0
registerByName["HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER"] = 0.01
registerByName["HEATER_TEMP_CNTRL_H_REGISTER"] = HEATER_TEMP_CNTRL_H_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_H_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_H_REGISTER"] = 5.0
registerByName["HEATER_TEMP_CNTRL_K_REGISTER"] = HEATER_TEMP_CNTRL_K_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_K_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_K_REGISTER"] = 0.0
registerByName["HEATER_TEMP_CNTRL_TI_REGISTER"] = HEATER_TEMP_CNTRL_TI_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_TI_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_TI_REGISTER"] = 1000.0
registerByName["HEATER_TEMP_CNTRL_TD_REGISTER"] = HEATER_TEMP_CNTRL_TD_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_TD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_TD_REGISTER"] = 0.0
registerByName["HEATER_TEMP_CNTRL_B_REGISTER"] = HEATER_TEMP_CNTRL_B_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_B_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_B_REGISTER"] = 1.0
registerByName["HEATER_TEMP_CNTRL_C_REGISTER"] = HEATER_TEMP_CNTRL_C_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_C_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_C_REGISTER"] = 1.0
registerByName["HEATER_TEMP_CNTRL_N_REGISTER"] = HEATER_TEMP_CNTRL_N_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_N_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_N_REGISTER"] = 100.0
registerByName["HEATER_TEMP_CNTRL_S_REGISTER"] = HEATER_TEMP_CNTRL_S_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_S_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_S_REGISTER"] = 5.0
registerByName["HEATER_TEMP_CNTRL_AMIN_REGISTER"] = HEATER_TEMP_CNTRL_AMIN_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_AMIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_AMIN_REGISTER"] = 0.0
registerByName["HEATER_TEMP_CNTRL_AMAX_REGISTER"] = HEATER_TEMP_CNTRL_AMAX_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_AMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_AMAX_REGISTER"] = 30000.0
registerByName["HEATER_TEMP_CNTRL_IMAX_REGISTER"] = HEATER_TEMP_CNTRL_IMAX_REGISTER
registerInfo.append(RegInfo("HEATER_TEMP_CNTRL_IMAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_TEMP_CNTRL_IMAX_REGISTER"] = 10000.0
registerByName["HEATER_PRBS_GENPOLY_REGISTER"] = HEATER_PRBS_GENPOLY_REGISTER
registerInfo.append(RegInfo("HEATER_PRBS_GENPOLY_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["HEATER_PRBS_GENPOLY_REGISTER"] = 0x481
registerByName["HEATER_PRBS_AMPLITUDE_REGISTER"] = HEATER_PRBS_AMPLITUDE_REGISTER
registerInfo.append(RegInfo("HEATER_PRBS_AMPLITUDE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_PRBS_AMPLITUDE_REGISTER"] = 5000.0
registerByName["HEATER_PRBS_MEAN_REGISTER"] = HEATER_PRBS_MEAN_REGISTER
registerInfo.append(RegInfo("HEATER_PRBS_MEAN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_PRBS_MEAN_REGISTER"] = 40000.0
registerByName["HEATER_CUTOFF_REGISTER"] = HEATER_CUTOFF_REGISTER
registerInfo.append(RegInfo("HEATER_CUTOFF_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["HEATER_CUTOFF_REGISTER"] = 45.1
registerByName["CAVITY_PRESSURE_ADC_REGISTER"] = CAVITY_PRESSURE_ADC_REGISTER
registerInfo.append(RegInfo("CAVITY_PRESSURE_ADC_REGISTER",c_int,0,1.0,"r"))
registerInitialValue["CAVITY_PRESSURE_ADC_REGISTER"] = 32768
registerByName["CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER"] = CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER"] = 1.5258789E-2
registerByName["CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER"] = CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER"] = 0.0
registerByName["CAVITY_PRESSURE_REGISTER"] = CAVITY_PRESSURE_REGISTER
registerInfo.append(RegInfo("CAVITY_PRESSURE_REGISTER",c_float,0,1.0,"r"))
registerByName["AMBIENT_PRESSURE_ADC_REGISTER"] = AMBIENT_PRESSURE_ADC_REGISTER
registerInfo.append(RegInfo("AMBIENT_PRESSURE_ADC_REGISTER",c_int,0,1.0,"r"))
registerInitialValue["AMBIENT_PRESSURE_ADC_REGISTER"] = 32768
registerByName["CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER"] = CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER
registerInfo.append(RegInfo("CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER"] = 1.5258789E-2
registerByName["CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER"] = CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER"] = 0.0
registerByName["AMBIENT_PRESSURE_REGISTER"] = AMBIENT_PRESSURE_REGISTER
registerInfo.append(RegInfo("AMBIENT_PRESSURE_REGISTER",c_float,0,1.0,"r"))
registerByName["ANALYZER_TUNING_MODE_REGISTER"] = ANALYZER_TUNING_MODE_REGISTER
registerInfo.append(RegInfo("ANALYZER_TUNING_MODE_REGISTER",ANALYZER_TUNING_ModeType,1,1.0,"rw"))
registerInitialValue["ANALYZER_TUNING_MODE_REGISTER"] = ANALYZER_TUNING_CavityLengthTuningMode
registerByName["TUNER_SWEEP_RAMP_HIGH_REGISTER"] = TUNER_SWEEP_RAMP_HIGH_REGISTER
registerInfo.append(RegInfo("TUNER_SWEEP_RAMP_HIGH_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["TUNER_SWEEP_RAMP_HIGH_REGISTER"] = 50000.0
registerByName["TUNER_SWEEP_RAMP_LOW_REGISTER"] = TUNER_SWEEP_RAMP_LOW_REGISTER
registerInfo.append(RegInfo("TUNER_SWEEP_RAMP_LOW_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["TUNER_SWEEP_RAMP_LOW_REGISTER"] = 10000.0
registerByName["TUNER_WINDOW_RAMP_HIGH_REGISTER"] = TUNER_WINDOW_RAMP_HIGH_REGISTER
registerInfo.append(RegInfo("TUNER_WINDOW_RAMP_HIGH_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["TUNER_WINDOW_RAMP_HIGH_REGISTER"] = 48000.0
registerByName["TUNER_WINDOW_RAMP_LOW_REGISTER"] = TUNER_WINDOW_RAMP_LOW_REGISTER
registerInfo.append(RegInfo("TUNER_WINDOW_RAMP_LOW_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["TUNER_WINDOW_RAMP_LOW_REGISTER"] = 12000.0
registerByName["TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER"] = TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER
registerInfo.append(RegInfo("TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER"] = 1500.0
registerByName["TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER"] = TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER
registerInfo.append(RegInfo("TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER"] = 1500.0
registerByName["TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER"] = TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER
registerInfo.append(RegInfo("TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER"] = 1250.0
registerByName["TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER"] = TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER
registerInfo.append(RegInfo("TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER"] = 1250.0
registerByName["TUNER_DITHER_MEDIAN_COUNT_REGISTER"] = TUNER_DITHER_MEDIAN_COUNT_REGISTER
registerInfo.append(RegInfo("TUNER_DITHER_MEDIAN_COUNT_REGISTER",TUNER_DITHER_MEDIAN_CountType,1,1.0,"rw"))
registerInitialValue["TUNER_DITHER_MEDIAN_COUNT_REGISTER"] = 9
registerByName["RDFITTER_MINLOSS_REGISTER"] = RDFITTER_MINLOSS_REGISTER
registerInfo.append(RegInfo("RDFITTER_MINLOSS_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["RDFITTER_MINLOSS_REGISTER"] = 0.2
registerByName["RDFITTER_MAXLOSS_REGISTER"] = RDFITTER_MAXLOSS_REGISTER
registerInfo.append(RegInfo("RDFITTER_MAXLOSS_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["RDFITTER_MAXLOSS_REGISTER"] = 50.0
registerByName["RDFITTER_LATEST_LOSS_REGISTER"] = RDFITTER_LATEST_LOSS_REGISTER
registerInfo.append(RegInfo("RDFITTER_LATEST_LOSS_REGISTER",c_float,0,1.0,"r"))
registerByName["RDFITTER_IMPROVEMENT_STEPS_REGISTER"] = RDFITTER_IMPROVEMENT_STEPS_REGISTER
registerInfo.append(RegInfo("RDFITTER_IMPROVEMENT_STEPS_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["RDFITTER_IMPROVEMENT_STEPS_REGISTER"] = 1
registerByName["RDFITTER_START_SAMPLE_REGISTER"] = RDFITTER_START_SAMPLE_REGISTER
registerInfo.append(RegInfo("RDFITTER_START_SAMPLE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["RDFITTER_START_SAMPLE_REGISTER"] = 10
registerByName["RDFITTER_FRACTIONAL_THRESHOLD_REGISTER"] = RDFITTER_FRACTIONAL_THRESHOLD_REGISTER
registerInfo.append(RegInfo("RDFITTER_FRACTIONAL_THRESHOLD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["RDFITTER_FRACTIONAL_THRESHOLD_REGISTER"] = 0.85
registerByName["RDFITTER_ABSOLUTE_THRESHOLD_REGISTER"] = RDFITTER_ABSOLUTE_THRESHOLD_REGISTER
registerInfo.append(RegInfo("RDFITTER_ABSOLUTE_THRESHOLD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["RDFITTER_ABSOLUTE_THRESHOLD_REGISTER"] = 13000
registerByName["RDFITTER_NUMBER_OF_POINTS_REGISTER"] = RDFITTER_NUMBER_OF_POINTS_REGISTER
registerInfo.append(RegInfo("RDFITTER_NUMBER_OF_POINTS_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["RDFITTER_NUMBER_OF_POINTS_REGISTER"] = 3500
registerByName["RDFITTER_MAX_E_FOLDINGS_REGISTER"] = RDFITTER_MAX_E_FOLDINGS_REGISTER
registerInfo.append(RegInfo("RDFITTER_MAX_E_FOLDINGS_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["RDFITTER_MAX_E_FOLDINGS_REGISTER"] = 8.0
registerByName["RDFITTER_META_BACKOFF_REGISTER"] = RDFITTER_META_BACKOFF_REGISTER
registerInfo.append(RegInfo("RDFITTER_META_BACKOFF_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["RDFITTER_META_BACKOFF_REGISTER"] = 2
registerByName["RDFITTER_META_SAMPLES_REGISTER"] = RDFITTER_META_SAMPLES_REGISTER
registerInfo.append(RegInfo("RDFITTER_META_SAMPLES_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["RDFITTER_META_SAMPLES_REGISTER"] = 6
registerByName["SPECT_CNTRL_STATE_REGISTER"] = SPECT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["SPECT_CNTRL_STATE_REGISTER"] = SPECT_CNTRL_IdleState
registerByName["SPECT_CNTRL_MODE_REGISTER"] = SPECT_CNTRL_MODE_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_MODE_REGISTER",SPECT_CNTRL_ModeType,1,1.0,"rw"))
registerInitialValue["SPECT_CNTRL_MODE_REGISTER"] = SPECT_CNTRL_SchemeSingleMode
registerByName["SPECT_CNTRL_ACTIVE_SCHEME_REGISTER"] = SPECT_CNTRL_ACTIVE_SCHEME_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_ACTIVE_SCHEME_REGISTER",c_uint,0,1.0,"rw"))
registerInitialValue["SPECT_CNTRL_ACTIVE_SCHEME_REGISTER"] = 0
registerByName["SPECT_CNTRL_NEXT_SCHEME_REGISTER"] = SPECT_CNTRL_NEXT_SCHEME_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_NEXT_SCHEME_REGISTER",c_uint,0,1.0,"rw"))
registerInitialValue["SPECT_CNTRL_NEXT_SCHEME_REGISTER"] = 0
registerByName["SPECT_CNTRL_SCHEME_ITER_REGISTER"] = SPECT_CNTRL_SCHEME_ITER_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_SCHEME_ITER_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["SPECT_CNTRL_SCHEME_ITER_REGISTER"] = 0
registerByName["SPECT_CNTRL_SCHEME_ROW_REGISTER"] = SPECT_CNTRL_SCHEME_ROW_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_SCHEME_ROW_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["SPECT_CNTRL_SCHEME_ROW_REGISTER"] = 0
registerByName["SPECT_CNTRL_DWELL_COUNT_REGISTER"] = SPECT_CNTRL_DWELL_COUNT_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_DWELL_COUNT_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["SPECT_CNTRL_DWELL_COUNT_REGISTER"] = 0
registerByName["SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER"] = SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER"] = 15000
registerByName["SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER"] = SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER"] = 100000
registerByName["SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER"] = SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER
registerInfo.append(RegInfo("SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER"] = 1000000
registerByName["VIRTUAL_LASER_REGISTER"] = VIRTUAL_LASER_REGISTER
registerInfo.append(RegInfo("VIRTUAL_LASER_REGISTER",VIRTUAL_LASER_Type,0,1.0,"rw"))
registerInitialValue["VIRTUAL_LASER_REGISTER"] = VIRTUAL_LASER_3
registerByName["PZT_INCR_PER_CAVITY_FSR"] = PZT_INCR_PER_CAVITY_FSR
registerInfo.append(RegInfo("PZT_INCR_PER_CAVITY_FSR",c_float,1,1.0,"rw"))
registerInitialValue["PZT_INCR_PER_CAVITY_FSR"] = 16400
registerByName["PZT_OFFSET_UPDATE_FACTOR"] = PZT_OFFSET_UPDATE_FACTOR
registerInfo.append(RegInfo("PZT_OFFSET_UPDATE_FACTOR",c_float,1,1.0,"rw"))
registerInitialValue["PZT_OFFSET_UPDATE_FACTOR"] = 0
registerByName["PZT_OFFSET_VIRTUAL_LASER1"] = PZT_OFFSET_VIRTUAL_LASER1
registerInfo.append(RegInfo("PZT_OFFSET_VIRTUAL_LASER1",c_float,1,1.0,"rw"))
registerInitialValue["PZT_OFFSET_VIRTUAL_LASER1"] = 0
registerByName["PZT_OFFSET_VIRTUAL_LASER2"] = PZT_OFFSET_VIRTUAL_LASER2
registerInfo.append(RegInfo("PZT_OFFSET_VIRTUAL_LASER2",c_float,1,1.0,"rw"))
registerInitialValue["PZT_OFFSET_VIRTUAL_LASER2"] = 0
registerByName["PZT_OFFSET_VIRTUAL_LASER3"] = PZT_OFFSET_VIRTUAL_LASER3
registerInfo.append(RegInfo("PZT_OFFSET_VIRTUAL_LASER3",c_float,1,1.0,"rw"))
registerInitialValue["PZT_OFFSET_VIRTUAL_LASER3"] = 0
registerByName["PZT_OFFSET_VIRTUAL_LASER4"] = PZT_OFFSET_VIRTUAL_LASER4
registerInfo.append(RegInfo("PZT_OFFSET_VIRTUAL_LASER4",c_float,1,1.0,"rw"))
registerInitialValue["PZT_OFFSET_VIRTUAL_LASER4"] = 0
registerByName["PZT_OFFSET_VIRTUAL_LASER5"] = PZT_OFFSET_VIRTUAL_LASER5
registerInfo.append(RegInfo("PZT_OFFSET_VIRTUAL_LASER5",c_float,1,1.0,"rw"))
registerInitialValue["PZT_OFFSET_VIRTUAL_LASER5"] = 0
registerByName["PZT_OFFSET_VIRTUAL_LASER6"] = PZT_OFFSET_VIRTUAL_LASER6
registerInfo.append(RegInfo("PZT_OFFSET_VIRTUAL_LASER6",c_float,1,1.0,"rw"))
registerInitialValue["PZT_OFFSET_VIRTUAL_LASER6"] = 0
registerByName["PZT_OFFSET_VIRTUAL_LASER7"] = PZT_OFFSET_VIRTUAL_LASER7
registerInfo.append(RegInfo("PZT_OFFSET_VIRTUAL_LASER7",c_float,1,1.0,"rw"))
registerInitialValue["PZT_OFFSET_VIRTUAL_LASER7"] = 0
registerByName["PZT_OFFSET_VIRTUAL_LASER8"] = PZT_OFFSET_VIRTUAL_LASER8
registerInfo.append(RegInfo("PZT_OFFSET_VIRTUAL_LASER8",c_float,1,1.0,"rw"))
registerInitialValue["PZT_OFFSET_VIRTUAL_LASER8"] = 0
registerByName["SCHEME_OFFSET_VIRTUAL_LASER1"] = SCHEME_OFFSET_VIRTUAL_LASER1
registerInfo.append(RegInfo("SCHEME_OFFSET_VIRTUAL_LASER1",c_float,1,1.0,"rw"))
registerInitialValue["SCHEME_OFFSET_VIRTUAL_LASER1"] = 0
registerByName["SCHEME_OFFSET_VIRTUAL_LASER2"] = SCHEME_OFFSET_VIRTUAL_LASER2
registerInfo.append(RegInfo("SCHEME_OFFSET_VIRTUAL_LASER2",c_float,1,1.0,"rw"))
registerInitialValue["SCHEME_OFFSET_VIRTUAL_LASER2"] = 0
registerByName["SCHEME_OFFSET_VIRTUAL_LASER3"] = SCHEME_OFFSET_VIRTUAL_LASER3
registerInfo.append(RegInfo("SCHEME_OFFSET_VIRTUAL_LASER3",c_float,1,1.0,"rw"))
registerInitialValue["SCHEME_OFFSET_VIRTUAL_LASER3"] = 0
registerByName["SCHEME_OFFSET_VIRTUAL_LASER4"] = SCHEME_OFFSET_VIRTUAL_LASER4
registerInfo.append(RegInfo("SCHEME_OFFSET_VIRTUAL_LASER4",c_float,1,1.0,"rw"))
registerInitialValue["SCHEME_OFFSET_VIRTUAL_LASER4"] = 0
registerByName["SCHEME_OFFSET_VIRTUAL_LASER5"] = SCHEME_OFFSET_VIRTUAL_LASER5
registerInfo.append(RegInfo("SCHEME_OFFSET_VIRTUAL_LASER5",c_float,1,1.0,"rw"))
registerInitialValue["SCHEME_OFFSET_VIRTUAL_LASER5"] = 0
registerByName["SCHEME_OFFSET_VIRTUAL_LASER6"] = SCHEME_OFFSET_VIRTUAL_LASER6
registerInfo.append(RegInfo("SCHEME_OFFSET_VIRTUAL_LASER6",c_float,1,1.0,"rw"))
registerInitialValue["SCHEME_OFFSET_VIRTUAL_LASER6"] = 0
registerByName["SCHEME_OFFSET_VIRTUAL_LASER7"] = SCHEME_OFFSET_VIRTUAL_LASER7
registerInfo.append(RegInfo("SCHEME_OFFSET_VIRTUAL_LASER7",c_float,1,1.0,"rw"))
registerInitialValue["SCHEME_OFFSET_VIRTUAL_LASER7"] = 0
registerByName["SCHEME_OFFSET_VIRTUAL_LASER8"] = SCHEME_OFFSET_VIRTUAL_LASER8
registerInfo.append(RegInfo("SCHEME_OFFSET_VIRTUAL_LASER8",c_float,1,1.0,"rw"))
registerInitialValue["SCHEME_OFFSET_VIRTUAL_LASER8"] = 0
registerByName["VALVE_CNTRL_STATE_REGISTER"] = VALVE_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_STATE_REGISTER",VALVE_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_STATE_REGISTER"] = VALVE_CNTRL_DisabledState
registerByName["VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER"] = VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER"] = 140.0
registerByName["VALVE_CNTRL_USER_INLET_VALVE_REGISTER"] = VALVE_CNTRL_USER_INLET_VALVE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_USER_INLET_VALVE_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_USER_INLET_VALVE_REGISTER"] = 0.0
registerByName["VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER"] = VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER"] = 0.0
registerByName["VALVE_CNTRL_INLET_VALVE_REGISTER"] = VALVE_CNTRL_INLET_VALVE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_INLET_VALVE_REGISTER"] = 0.0
registerByName["VALVE_CNTRL_OUTLET_VALVE_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_OUTLET_VALVE_REGISTER"] = 0.0
registerByName["VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER"] = VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER"] = 5.0
registerByName["VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER"] = VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER"] = 50.0
registerByName["VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER"] = VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER"] = 50.0
registerByName["VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER"] = VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER"] = 0.5
registerByName["VALVE_CNTRL_INLET_VALVE_MIN_REGISTER"] = VALVE_CNTRL_INLET_VALVE_MIN_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_INLET_VALVE_MIN_REGISTER"] = 20000.0
registerByName["VALVE_CNTRL_INLET_VALVE_MAX_REGISTER"] = VALVE_CNTRL_INLET_VALVE_MAX_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_INLET_VALVE_MAX_REGISTER"] = 65000.0
registerByName["VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER"] = VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER"] = 1000.0
registerByName["VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER"] = VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER"] = 1000.0
registerByName["VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER"] = 50.0
registerByName["VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER"] = 0.5
registerByName["VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER"] = 20000.0
registerByName["VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER"] = 65000.0
registerByName["VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER"] = 1000.0
registerByName["VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER"] = VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER"] = 1000.0
registerByName["VALVE_CNTRL_THRESHOLD_STATE_REGISTER"] = VALVE_CNTRL_THRESHOLD_STATE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_THRESHOLD_STATE_REGISTER",VALVE_CNTRL_THRESHOLD_StateType,0,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_THRESHOLD_STATE_REGISTER"] = VALVE_CNTRL_THRESHOLD_DisabledState
registerByName["VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER"] = VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER"] = 2000.0
registerByName["VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER"] = VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER"] = 0
registerByName["VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER"] = VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER"] = 0
registerByName["VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER"] = VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER"] = 0
registerByName["VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER"] = VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER"] = 0x3F
registerByName["VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER"] = VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER"] = 0x0
registerByName["VALVE_CNTRL_SEQUENCE_STEP_REGISTER"] = VALVE_CNTRL_SEQUENCE_STEP_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_SEQUENCE_STEP_REGISTER",c_int,0,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_SEQUENCE_STEP_REGISTER"] = -1
registerByName["VALVE_CNTRL_SOLENOID_VALVES_REGISTER"] = VALVE_CNTRL_SOLENOID_VALVES_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_SOLENOID_VALVES_REGISTER",c_uint,0,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_SOLENOID_VALVES_REGISTER"] = 0x0
registerByName["VALVE_CNTRL_MPV_POSITION_REGISTER"] = VALVE_CNTRL_MPV_POSITION_REGISTER
registerInfo.append(RegInfo("VALVE_CNTRL_MPV_POSITION_REGISTER",c_uint,0,1.0,"rw"))
registerInitialValue["VALVE_CNTRL_MPV_POSITION_REGISTER"] = 0x0
registerByName["TEC_CNTRL_REGISTER"] = TEC_CNTRL_REGISTER
registerInfo.append(RegInfo("TEC_CNTRL_REGISTER",TEC_CNTRL_Type,0,1.0,"rw"))
registerInitialValue["TEC_CNTRL_REGISTER"] = TEC_CNTRL_Disabled
registerByName["SENTRY_UPPER_LIMIT_TRIPPED_REGISTER"] = SENTRY_UPPER_LIMIT_TRIPPED_REGISTER
registerInfo.append(RegInfo("SENTRY_UPPER_LIMIT_TRIPPED_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["SENTRY_UPPER_LIMIT_TRIPPED_REGISTER"] = 0
registerByName["SENTRY_LOWER_LIMIT_TRIPPED_REGISTER"] = SENTRY_LOWER_LIMIT_TRIPPED_REGISTER
registerInfo.append(RegInfo("SENTRY_LOWER_LIMIT_TRIPPED_REGISTER",c_uint,0,1.0,"r"))
registerInitialValue["SENTRY_LOWER_LIMIT_TRIPPED_REGISTER"] = 0
registerByName["SENTRY_LASER1_TEMPERATURE_MIN_REGISTER"] = SENTRY_LASER1_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER1_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER1_TEMPERATURE_MIN_REGISTER"] = 3.0
registerByName["SENTRY_LASER1_TEMPERATURE_MAX_REGISTER"] = SENTRY_LASER1_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER1_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER1_TEMPERATURE_MAX_REGISTER"] = 52.0
registerByName["SENTRY_LASER2_TEMPERATURE_MIN_REGISTER"] = SENTRY_LASER2_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER2_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER2_TEMPERATURE_MIN_REGISTER"] = 3.0
registerByName["SENTRY_LASER2_TEMPERATURE_MAX_REGISTER"] = SENTRY_LASER2_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER2_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER2_TEMPERATURE_MAX_REGISTER"] = 52.0
registerByName["SENTRY_LASER3_TEMPERATURE_MIN_REGISTER"] = SENTRY_LASER3_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER3_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER3_TEMPERATURE_MIN_REGISTER"] = 3.0
registerByName["SENTRY_LASER3_TEMPERATURE_MAX_REGISTER"] = SENTRY_LASER3_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER3_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER3_TEMPERATURE_MAX_REGISTER"] = 52.0
registerByName["SENTRY_LASER4_TEMPERATURE_MIN_REGISTER"] = SENTRY_LASER4_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER4_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER4_TEMPERATURE_MIN_REGISTER"] = 3.0
registerByName["SENTRY_LASER4_TEMPERATURE_MAX_REGISTER"] = SENTRY_LASER4_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER4_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER4_TEMPERATURE_MAX_REGISTER"] = 52.0
registerByName["SENTRY_ETALON_TEMPERATURE_MIN_REGISTER"] = SENTRY_ETALON_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_ETALON_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_ETALON_TEMPERATURE_MIN_REGISTER"] = 3.0
registerByName["SENTRY_ETALON_TEMPERATURE_MAX_REGISTER"] = SENTRY_ETALON_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_ETALON_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_ETALON_TEMPERATURE_MAX_REGISTER"] = 52.0
registerByName["SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER"] = SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER"] = 3.0
registerByName["SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER"] = SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER"] = 52.0
registerByName["SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER"] = SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER"] = 3.0
registerByName["SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER"] = SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER"] = 80.0
registerByName["SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER"] = SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER"] = 3.0
registerByName["SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER"] = SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER"] = 85.0
registerByName["SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER"] = SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER"] = 3.0
registerByName["SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER"] = SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER"] = 95.0
registerByName["SENTRY_DAS_TEMPERATURE_MIN_REGISTER"] = SENTRY_DAS_TEMPERATURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_DAS_TEMPERATURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_DAS_TEMPERATURE_MIN_REGISTER"] = 5.0
registerByName["SENTRY_DAS_TEMPERATURE_MAX_REGISTER"] = SENTRY_DAS_TEMPERATURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_DAS_TEMPERATURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_DAS_TEMPERATURE_MAX_REGISTER"] = 55.0
registerByName["SENTRY_LASER1_CURRENT_MIN_REGISTER"] = SENTRY_LASER1_CURRENT_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER1_CURRENT_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER1_CURRENT_MIN_REGISTER"] = -5.0
registerByName["SENTRY_LASER1_CURRENT_MAX_REGISTER"] = SENTRY_LASER1_CURRENT_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER1_CURRENT_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER1_CURRENT_MAX_REGISTER"] = 180.0
registerByName["SENTRY_LASER2_CURRENT_MIN_REGISTER"] = SENTRY_LASER2_CURRENT_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER2_CURRENT_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER2_CURRENT_MIN_REGISTER"] = -5.0
registerByName["SENTRY_LASER2_CURRENT_MAX_REGISTER"] = SENTRY_LASER2_CURRENT_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER2_CURRENT_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER2_CURRENT_MAX_REGISTER"] = 180.0
registerByName["SENTRY_LASER3_CURRENT_MIN_REGISTER"] = SENTRY_LASER3_CURRENT_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER3_CURRENT_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER3_CURRENT_MIN_REGISTER"] = -5.0
registerByName["SENTRY_LASER3_CURRENT_MAX_REGISTER"] = SENTRY_LASER3_CURRENT_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER3_CURRENT_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER3_CURRENT_MAX_REGISTER"] = 180.0
registerByName["SENTRY_LASER4_CURRENT_MIN_REGISTER"] = SENTRY_LASER4_CURRENT_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER4_CURRENT_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER4_CURRENT_MIN_REGISTER"] = -5.0
registerByName["SENTRY_LASER4_CURRENT_MAX_REGISTER"] = SENTRY_LASER4_CURRENT_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_LASER4_CURRENT_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_LASER4_CURRENT_MAX_REGISTER"] = 180.0
registerByName["SENTRY_CAVITY_PRESSURE_MIN_REGISTER"] = SENTRY_CAVITY_PRESSURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_CAVITY_PRESSURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_CAVITY_PRESSURE_MIN_REGISTER"] = -5.0
registerByName["SENTRY_CAVITY_PRESSURE_MAX_REGISTER"] = SENTRY_CAVITY_PRESSURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_CAVITY_PRESSURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_CAVITY_PRESSURE_MAX_REGISTER"] = 900.0
registerByName["SENTRY_AMBIENT_PRESSURE_MIN_REGISTER"] = SENTRY_AMBIENT_PRESSURE_MIN_REGISTER
registerInfo.append(RegInfo("SENTRY_AMBIENT_PRESSURE_MIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_AMBIENT_PRESSURE_MIN_REGISTER"] = 200.0
registerByName["SENTRY_AMBIENT_PRESSURE_MAX_REGISTER"] = SENTRY_AMBIENT_PRESSURE_MAX_REGISTER
registerInfo.append(RegInfo("SENTRY_AMBIENT_PRESSURE_MAX_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["SENTRY_AMBIENT_PRESSURE_MAX_REGISTER"] = 900.0
registerByName["FAN_CNTRL_STATE_REGISTER"] = FAN_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("FAN_CNTRL_STATE_REGISTER",FAN_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["FAN_CNTRL_STATE_REGISTER"] = FAN_CNTRL_OnState
registerByName["FAN_CNTRL_TEMPERATURE_REGISTER"] = FAN_CNTRL_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("FAN_CNTRL_TEMPERATURE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["FAN_CNTRL_TEMPERATURE_REGISTER"] = 25.0
registerByName["KEEP_ALIVE_REGISTER"] = KEEP_ALIVE_REGISTER
registerInfo.append(RegInfo("KEEP_ALIVE_REGISTER",c_int,0,1.0,"rw"))
registerInitialValue["KEEP_ALIVE_REGISTER"] = -300
registerByName["LOSS_BUFFER_0_REGISTER"] = LOSS_BUFFER_0_REGISTER
registerInfo.append(RegInfo("LOSS_BUFFER_0_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LOSS_BUFFER_0_REGISTER"] = 0
registerByName["LOSS_BUFFER_1_REGISTER"] = LOSS_BUFFER_1_REGISTER
registerInfo.append(RegInfo("LOSS_BUFFER_1_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LOSS_BUFFER_1_REGISTER"] = 0
registerByName["LOSS_BUFFER_2_REGISTER"] = LOSS_BUFFER_2_REGISTER
registerInfo.append(RegInfo("LOSS_BUFFER_2_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LOSS_BUFFER_2_REGISTER"] = 0
registerByName["LOSS_BUFFER_3_REGISTER"] = LOSS_BUFFER_3_REGISTER
registerInfo.append(RegInfo("LOSS_BUFFER_3_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LOSS_BUFFER_3_REGISTER"] = 0
registerByName["LOSS_BUFFER_4_REGISTER"] = LOSS_BUFFER_4_REGISTER
registerInfo.append(RegInfo("LOSS_BUFFER_4_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LOSS_BUFFER_4_REGISTER"] = 0
registerByName["LOSS_BUFFER_5_REGISTER"] = LOSS_BUFFER_5_REGISTER
registerInfo.append(RegInfo("LOSS_BUFFER_5_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LOSS_BUFFER_5_REGISTER"] = 0
registerByName["LOSS_BUFFER_6_REGISTER"] = LOSS_BUFFER_6_REGISTER
registerInfo.append(RegInfo("LOSS_BUFFER_6_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LOSS_BUFFER_6_REGISTER"] = 0
registerByName["LOSS_BUFFER_7_REGISTER"] = LOSS_BUFFER_7_REGISTER
registerInfo.append(RegInfo("LOSS_BUFFER_7_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["LOSS_BUFFER_7_REGISTER"] = 0
registerByName["PROCESSED_LOSS_1_REGISTER"] = PROCESSED_LOSS_1_REGISTER
registerInfo.append(RegInfo("PROCESSED_LOSS_1_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["PROCESSED_LOSS_1_REGISTER"] = 0
registerByName["PROCESSED_LOSS_2_REGISTER"] = PROCESSED_LOSS_2_REGISTER
registerInfo.append(RegInfo("PROCESSED_LOSS_2_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["PROCESSED_LOSS_2_REGISTER"] = 0
registerByName["PROCESSED_LOSS_3_REGISTER"] = PROCESSED_LOSS_3_REGISTER
registerInfo.append(RegInfo("PROCESSED_LOSS_3_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["PROCESSED_LOSS_3_REGISTER"] = 0
registerByName["PROCESSED_LOSS_4_REGISTER"] = PROCESSED_LOSS_4_REGISTER
registerInfo.append(RegInfo("PROCESSED_LOSS_4_REGISTER",c_float,0,1.0,"r"))
registerInitialValue["PROCESSED_LOSS_4_REGISTER"] = 0
registerByName["PEAK_DETECT_CNTRL_STATE_REGISTER"] = PEAK_DETECT_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_STATE_REGISTER",PEAK_DETECT_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_STATE_REGISTER"] = PEAK_DETECT_CNTRL_InactiveState
registerByName["PEAK_DETECT_CNTRL_BACKGROUND_SAMPLES_REGISTER"] = PEAK_DETECT_CNTRL_BACKGROUND_SAMPLES_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_BACKGROUND_SAMPLES_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_BACKGROUND_SAMPLES_REGISTER"] = 200
registerByName["PEAK_DETECT_CNTRL_BACKGROUND_REGISTER"] = PEAK_DETECT_CNTRL_BACKGROUND_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_BACKGROUND_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_BACKGROUND_REGISTER"] = 1.0
registerByName["PEAK_DETECT_CNTRL_UPPER_THRESHOLD_REGISTER"] = PEAK_DETECT_CNTRL_UPPER_THRESHOLD_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_UPPER_THRESHOLD_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_UPPER_THRESHOLD_REGISTER"] = 0.3
registerByName["PEAK_DETECT_CNTRL_LOWER_THRESHOLD_1_REGISTER"] = PEAK_DETECT_CNTRL_LOWER_THRESHOLD_1_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_LOWER_THRESHOLD_1_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_LOWER_THRESHOLD_1_REGISTER"] = 0.15
registerByName["PEAK_DETECT_CNTRL_LOWER_THRESHOLD_2_REGISTER"] = PEAK_DETECT_CNTRL_LOWER_THRESHOLD_2_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_LOWER_THRESHOLD_2_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_LOWER_THRESHOLD_2_REGISTER"] = 0.15
registerByName["PEAK_DETECT_CNTRL_THRESHOLD_FACTOR_REGISTER"] = PEAK_DETECT_CNTRL_THRESHOLD_FACTOR_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_THRESHOLD_FACTOR_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_THRESHOLD_FACTOR_REGISTER"] = 0.0
registerByName["PEAK_DETECT_CNTRL_ACTIVE_SIZE_REGISTER"] = PEAK_DETECT_CNTRL_ACTIVE_SIZE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_ACTIVE_SIZE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_ACTIVE_SIZE_REGISTER"] = 300
registerByName["PEAK_DETECT_CNTRL_POST_PEAK_SAMPLES_REGISTER"] = PEAK_DETECT_CNTRL_POST_PEAK_SAMPLES_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_POST_PEAK_SAMPLES_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_POST_PEAK_SAMPLES_REGISTER"] = 100
registerByName["PEAK_DETECT_CNTRL_CANCELLING_SAMPLES_REGISTER"] = PEAK_DETECT_CNTRL_CANCELLING_SAMPLES_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_CANCELLING_SAMPLES_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_CANCELLING_SAMPLES_REGISTER"] = 25
registerByName["PEAK_DETECT_CNTRL_TRIGGER_CONDITION_REGISTER"] = PEAK_DETECT_CNTRL_TRIGGER_CONDITION_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_TRIGGER_CONDITION_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_TRIGGER_CONDITION_REGISTER"] = 0xA800
registerByName["PEAK_DETECT_CNTRL_TRIGGER_DELAY_REGISTER"] = PEAK_DETECT_CNTRL_TRIGGER_DELAY_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_TRIGGER_DELAY_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_TRIGGER_DELAY_REGISTER"] = 0
registerByName["PEAK_DETECT_CNTRL_TRIGGERED_DURATION_REGISTER"] = PEAK_DETECT_CNTRL_TRIGGERED_DURATION_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_TRIGGERED_DURATION_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_TRIGGERED_DURATION_REGISTER"] = 2700
registerByName["PEAK_DETECT_CNTRL_TRANSITIONING_DURATION_REGISTER"] = PEAK_DETECT_CNTRL_TRANSITIONING_DURATION_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_TRANSITIONING_DURATION_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_TRANSITIONING_DURATION_REGISTER"] = 0
registerByName["PEAK_DETECT_CNTRL_TRANSITIONING_HOLDOFF_REGISTER"] = PEAK_DETECT_CNTRL_TRANSITIONING_HOLDOFF_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_TRANSITIONING_HOLDOFF_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_TRANSITIONING_HOLDOFF_REGISTER"] = 0
registerByName["PEAK_DETECT_CNTRL_HOLDING_MAX_LOSS_REGISTER"] = PEAK_DETECT_CNTRL_HOLDING_MAX_LOSS_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_HOLDING_MAX_LOSS_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_HOLDING_MAX_LOSS_REGISTER"] = 4.0
registerByName["PEAK_DETECT_CNTRL_HOLDING_DURATION_REGISTER"] = PEAK_DETECT_CNTRL_HOLDING_DURATION_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_HOLDING_DURATION_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_HOLDING_DURATION_REGISTER"] = 0
registerByName["PEAK_DETECT_CNTRL_PRIMING_DURATION_REGISTER"] = PEAK_DETECT_CNTRL_PRIMING_DURATION_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_PRIMING_DURATION_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_PRIMING_DURATION_REGISTER"] = 100
registerByName["PEAK_DETECT_CNTRL_PURGING_DURATION_REGISTER"] = PEAK_DETECT_CNTRL_PURGING_DURATION_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_PURGING_DURATION_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_PURGING_DURATION_REGISTER"] = 100
registerByName["PEAK_DETECT_CNTRL_REMAINING_SAMPLES_REGISTER"] = PEAK_DETECT_CNTRL_REMAINING_SAMPLES_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_REMAINING_SAMPLES_REGISTER",c_int,0,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_REMAINING_SAMPLES_REGISTER"] = 0
registerByName["PEAK_DETECT_CNTRL_IDLE_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_IDLE_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_IDLE_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_IDLE_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["PEAK_DETECT_CNTRL_ARMED_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_ARMED_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_ARMED_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_ARMED_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["PEAK_DETECT_CNTRL_TRIGGER_PENDING_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_TRIGGER_PENDING_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_TRIGGER_PENDING_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_TRIGGER_PENDING_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["PEAK_DETECT_CNTRL_TRIGGERED_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_TRIGGERED_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_TRIGGERED_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_TRIGGERED_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["PEAK_DETECT_CNTRL_TRANSITIONING_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_TRANSITIONING_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_TRANSITIONING_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_TRANSITIONING_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["PEAK_DETECT_CNTRL_HOLDING_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_HOLDING_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_HOLDING_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_HOLDING_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["PEAK_DETECT_CNTRL_INACTIVE_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_INACTIVE_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_INACTIVE_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_INACTIVE_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["PEAK_DETECT_CNTRL_CANCELLING_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_CANCELLING_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_CANCELLING_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_CANCELLING_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["PEAK_DETECT_CNTRL_PRIMING_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_PRIMING_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_PRIMING_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_PRIMING_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["PEAK_DETECT_CNTRL_PURGING_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_PURGING_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_PURGING_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_PURGING_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["PEAK_DETECT_CNTRL_INJECTION_PENDING_VALVE_MASK_AND_VALUE_REGISTER"] = PEAK_DETECT_CNTRL_INJECTION_PENDING_VALVE_MASK_AND_VALUE_REGISTER
registerInfo.append(RegInfo("PEAK_DETECT_CNTRL_INJECTION_PENDING_VALVE_MASK_AND_VALUE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["PEAK_DETECT_CNTRL_INJECTION_PENDING_VALVE_MASK_AND_VALUE_REGISTER"] = 0x0000
registerByName["FLOW1_REGISTER"] = FLOW1_REGISTER
registerInfo.append(RegInfo("FLOW1_REGISTER",c_float,0,1.0,"r"))
registerByName["CONVERSION_FLOW1_SCALE_REGISTER"] = CONVERSION_FLOW1_SCALE_REGISTER
registerInfo.append(RegInfo("CONVERSION_FLOW1_SCALE_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_FLOW1_SCALE_REGISTER"] = 1.0
registerByName["CONVERSION_FLOW1_OFFSET_REGISTER"] = CONVERSION_FLOW1_OFFSET_REGISTER
registerInfo.append(RegInfo("CONVERSION_FLOW1_OFFSET_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["CONVERSION_FLOW1_OFFSET_REGISTER"] = 0.0
registerByName["RDD_BALANCE_REGISTER"] = RDD_BALANCE_REGISTER
registerInfo.append(RegInfo("RDD_BALANCE_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["RDD_BALANCE_REGISTER"] = 0
registerByName["RDD_GAIN_REGISTER"] = RDD_GAIN_REGISTER
registerInfo.append(RegInfo("RDD_GAIN_REGISTER",c_uint,1,1.0,"rw"))
registerInitialValue["RDD_GAIN_REGISTER"] = 128
registerByName["FLOW_CNTRL_STATE_REGISTER"] = FLOW_CNTRL_STATE_REGISTER
registerInfo.append(RegInfo("FLOW_CNTRL_STATE_REGISTER",FLOW_CNTRL_StateType,0,1.0,"rw"))
registerInitialValue["FLOW_CNTRL_STATE_REGISTER"] = FLOW_CNTRL_DisabledState
registerByName["FLOW_CNTRL_SETPOINT_REGISTER"] = FLOW_CNTRL_SETPOINT_REGISTER
registerInfo.append(RegInfo("FLOW_CNTRL_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["FLOW_CNTRL_SETPOINT_REGISTER"] = 100
registerByName["FLOW_CNTRL_GAIN_REGISTER"] = FLOW_CNTRL_GAIN_REGISTER
registerInfo.append(RegInfo("FLOW_CNTRL_GAIN_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["FLOW_CNTRL_GAIN_REGISTER"] = 20
registerByName["FLOW_0_SETPOINT_REGISTER"] = FLOW_0_SETPOINT_REGISTER
registerInfo.append(RegInfo("FLOW_0_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["FLOW_0_SETPOINT_REGISTER"] = 400
registerByName["FLOW_1_SETPOINT_REGISTER"] = FLOW_1_SETPOINT_REGISTER
registerInfo.append(RegInfo("FLOW_1_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["FLOW_1_SETPOINT_REGISTER"] = 400
registerByName["FLOW_2_SETPOINT_REGISTER"] = FLOW_2_SETPOINT_REGISTER
registerInfo.append(RegInfo("FLOW_2_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["FLOW_2_SETPOINT_REGISTER"] = 400
registerByName["FLOW_3_SETPOINT_REGISTER"] = FLOW_3_SETPOINT_REGISTER
registerInfo.append(RegInfo("FLOW_3_SETPOINT_REGISTER",c_float,1,1.0,"rw"))
registerInitialValue["FLOW_3_SETPOINT_REGISTER"] = 400
registerByName["BATTERY_MONITOR_STATUS_REGISTER"] = BATTERY_MONITOR_STATUS_REGISTER
registerInfo.append(RegInfo("BATTERY_MONITOR_STATUS_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["BATTERY_MONITOR_STATUS_REGISTER"] = 0
registerByName["BATTERY_MONITOR_CHARGE_REGISTER"] = BATTERY_MONITOR_CHARGE_REGISTER
registerInfo.append(RegInfo("BATTERY_MONITOR_CHARGE_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["BATTERY_MONITOR_CHARGE_REGISTER"] = 0
registerByName["BATTERY_MONITOR_VOLTAGE_REGISTER"] = BATTERY_MONITOR_VOLTAGE_REGISTER
registerInfo.append(RegInfo("BATTERY_MONITOR_VOLTAGE_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["BATTERY_MONITOR_VOLTAGE_REGISTER"] = 0
registerByName["BATTERY_MONITOR_CURRENT_REGISTER"] = BATTERY_MONITOR_CURRENT_REGISTER
registerInfo.append(RegInfo("BATTERY_MONITOR_CURRENT_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["BATTERY_MONITOR_CURRENT_REGISTER"] = 0
registerByName["BATTERY_MONITOR_TEMPERATURE_REGISTER"] = BATTERY_MONITOR_TEMPERATURE_REGISTER
registerInfo.append(RegInfo("BATTERY_MONITOR_TEMPERATURE_REGISTER",c_float,0,1.0,"rw"))
registerInitialValue["BATTERY_MONITOR_TEMPERATURE_REGISTER"] = 0
registerByName["ACCELEROMETER_X_REGISTER"] = ACCELEROMETER_X_REGISTER
registerInfo.append(RegInfo("ACCELEROMETER_X_REGISTER",c_float,0,1.0,"rw"))
registerByName["ACCELEROMETER_Y_REGISTER"] = ACCELEROMETER_Y_REGISTER
registerInfo.append(RegInfo("ACCELEROMETER_Y_REGISTER",c_float,0,1.0,"rw"))
registerByName["ACCELEROMETER_Z_REGISTER"] = ACCELEROMETER_Z_REGISTER
registerInfo.append(RegInfo("ACCELEROMETER_Z_REGISTER",c_float,0,1.0,"rw"))

# FPGA block definitions

# Block KERNEL Kernel
KERNEL_MAGIC_CODE = 0 # Code indicating FPGA is programmed
KERNEL_CONTROL = 1 # Kernel control register
KERNEL_CONTROL_CYPRESS_RESET_B = 0 # Reset Cypress FX2 and FPGA bit position
KERNEL_CONTROL_CYPRESS_RESET_W = 1 # Reset Cypress FX2 and FPGA bit width
KERNEL_CONTROL_OVERLOAD_RESET_B = 1 # Reset overload register bit position
KERNEL_CONTROL_OVERLOAD_RESET_W = 1 # Reset overload register bit width
KERNEL_CONTROL_I2C_RESET_B = 2 # Reset i2c multiplexers bit position
KERNEL_CONTROL_I2C_RESET_W = 1 # Reset i2c multiplexers bit width
KERNEL_CONTROL_DOUT_MAN_B = 3 # Manually set FPGA digital outputs bit position
KERNEL_CONTROL_DOUT_MAN_W = 1 # Manually set FPGA digital outputs bit width

KERNEL_DIAG_1 = 2 # DSP accessible register for diagnostics
KERNEL_CONFIG = 3 # Configuration register
KERNEL_CONFIG_AUX_PZT_B = 0 # Auxiliary PZT Enable bit position
KERNEL_CONFIG_AUX_PZT_W = 1 # Auxiliary PZT Enable bit width
KERNEL_CONFIG_ENGINE1_TEC_B = 1 # Engine 1 TEC Enable bit position
KERNEL_CONFIG_ENGINE1_TEC_W = 1 # Engine 1 TEC Enable bit width
KERNEL_CONFIG_ENGINE2_TEC_B = 2 # Engine 2 TEC Enable bit position
KERNEL_CONFIG_ENGINE2_TEC_W = 1 # Engine 2 TEC Enable bit width

KERNEL_INTRONIX_CLKSEL = 4 # 
KERNEL_INTRONIX_CLKSEL_DIVISOR_B = 0 # Intronix sampling rate bit position
KERNEL_INTRONIX_CLKSEL_DIVISOR_W = 5 # Intronix sampling rate bit width

KERNEL_INTRONIX_1 = 5 # Channel for Logicport bits 7-0
KERNEL_INTRONIX_1_CHANNEL_B = 0 # Intronix display 1 channel bit position
KERNEL_INTRONIX_1_CHANNEL_W = 8 # Intronix display 1 channel bit width

KERNEL_INTRONIX_2 = 6 # Channel for Logicport bits 15-8
KERNEL_INTRONIX_2_CHANNEL_B = 0 # Intronix display 2 channel bit position
KERNEL_INTRONIX_2_CHANNEL_W = 8 # Intronix display 2 channel bit width

KERNEL_INTRONIX_3 = 7 # Channel for Logicport bits 23-16
KERNEL_INTRONIX_3_CHANNEL_B = 0 # Intronix display 3 channel bit position
KERNEL_INTRONIX_3_CHANNEL_W = 8 # Intronix display 3 channel bit width

KERNEL_OVERLOAD = 8 # Overload register
KERNEL_DOUT_HI = 9 # Manual control of FPGA DOUT 39-32
KERNEL_DOUT_LO = 10 # Manual control of FPGA DOUT 31-0
KERNEL_DIN = 11 # FPGA DIN 63-40

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

RDSIM_PZT_CENTER = 1 # PZT value (mod 16384) around which cavity fills
RDSIM_PZT_WINDOW_HALF_WIDTH = 2 # Half-width of PZT window within which cavity fills
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

LASERLOCKER_OPTIONS = 1 # Options register
LASERLOCKER_OPTIONS_SIM_ACTUAL_B = 0 # Wavelength Monitor Data Source bit position
LASERLOCKER_OPTIONS_SIM_ACTUAL_W = 1 # Wavelength Monitor Data Source bit width
LASERLOCKER_OPTIONS_DIRECT_TUNE_B = 1 # Route tuner input to fine current output bit position
LASERLOCKER_OPTIONS_DIRECT_TUNE_W = 1 # Route tuner input to fine current output bit width

LASERLOCKER_ETA1 = 2 # Etalon 1 reading
LASERLOCKER_REF1 = 3 # Reference 1 reading
LASERLOCKER_ETA2 = 4 # Etalon 2 reading
LASERLOCKER_REF2 = 5 # Reference 2 reading
LASERLOCKER_ETA1_DARK = 6 # Etalon 1 dark reading
LASERLOCKER_REF1_DARK = 7 # Reference 1 dark reading
LASERLOCKER_ETA2_DARK = 8 # Etalon 2 dark reading
LASERLOCKER_REF2_DARK = 9 # Reference 2 dark reading
LASERLOCKER_ETA1_OFFSET = 10 # Etalon 1 offset
LASERLOCKER_REF1_OFFSET = 11 # Reference 1 offset
LASERLOCKER_ETA2_OFFSET = 12 # Etalon 2 offset
LASERLOCKER_REF2_OFFSET = 13 # Reference 2 offset
LASERLOCKER_RATIO1 = 14 # Ratio 1
LASERLOCKER_RATIO2 = 15 # Ratio 2
LASERLOCKER_RATIO1_CENTER = 16 # Ratio 1 ellipse center
LASERLOCKER_RATIO1_MULTIPLIER = 17 # Ratio 1 multiplier
LASERLOCKER_RATIO2_CENTER = 18 # Ratio 2 ellipse center
LASERLOCKER_RATIO2_MULTIPLIER = 19 # Ratio 2 multiplier
LASERLOCKER_TUNING_OFFSET = 20 # Error offset to shift frequency
LASERLOCKER_LOCK_ERROR = 21 # Locker loop error
LASERLOCKER_WM_LOCK_WINDOW = 22 # Lock window
LASERLOCKER_WM_INT_GAIN = 23 # Locker integral gain
LASERLOCKER_WM_PROP_GAIN = 24 # Locker proportional gain
LASERLOCKER_WM_DERIV_GAIN = 25 # Locker derivative gain
LASERLOCKER_FINE_CURRENT = 26 # Fine laser current
LASERLOCKER_CYCLE_COUNTER = 27 # Cycle counter

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
RDMAN_OPTIONS_SIM_ACTUAL_B = 4 # Ringdown data source bit position
RDMAN_OPTIONS_SIM_ACTUAL_W = 1 # Ringdown data source bit width
RDMAN_OPTIONS_SCOPE_MODE_B = 5 # Oscilloscope mode bit position
RDMAN_OPTIONS_SCOPE_MODE_W = 1 # Oscilloscope mode bit width
RDMAN_OPTIONS_SCOPE_SLOPE_B = 6 # Tuner slope to trigger scope bit position
RDMAN_OPTIONS_SCOPE_SLOPE_W = 1 # Tuner slope to trigger scope bit width

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
RDMAN_OFF_DURATION = 21 # Duration (us) for ringdown (no injection)
RDMAN_EXTRA_DURATION = 22 # Duration (us) of extra laser current after ringdown
RDMAN_TIMEOUT_DURATION = 23 # Duration (us) within which ring-down must occur to be valid
RDMAN_TUNER_AT_RINGDOWN = 24 # Value of tuner at ring-down
RDMAN_METADATA_ADDR_AT_RINGDOWN = 25 # Metadata address at ring-down
RDMAN_RINGDOWN_DATA = 26 # Ringdown data

# Block TWGEN Tuner waveform generator
TWGEN_ACC = 0 # Accumulator
TWGEN_CS = 1 # Control/Status Register
TWGEN_CS_RUN_B = 0 # Stop/Run bit position
TWGEN_CS_RUN_W = 1 # Stop/Run bit width
TWGEN_CS_CONT_B = 1 # Single/Continuous bit position
TWGEN_CS_CONT_W = 1 # Single/Continuous bit width
TWGEN_CS_RESET_B = 2 # Reset generator bit position
TWGEN_CS_RESET_W = 1 # Reset generator bit width
TWGEN_CS_TUNE_PZT_B = 3 # Tune PZT bit position
TWGEN_CS_TUNE_PZT_W = 1 # Tune PZT bit width

TWGEN_SLOPE_DOWN = 2 # Slope in downward direction
TWGEN_SLOPE_UP = 3 # Slope in upward direction
TWGEN_SWEEP_LOW = 4 # Lower limit of sweep
TWGEN_SWEEP_HIGH = 5 # Higher limit of sweep
TWGEN_WINDOW_LOW = 6 # Lower limit of window
TWGEN_WINDOW_HIGH = 7 # Higher limit of window
TWGEN_PZT_OFFSET = 8 # PZT offset

# Block INJECT Optical injection subsystem
INJECT_CONTROL = 0 # Control register
INJECT_CONTROL_MODE_B = 0 # Manual/Automatic mode bit position
INJECT_CONTROL_MODE_W = 1 # Manual/Automatic mode bit width
INJECT_CONTROL_LASER_SELECT_B = 1 # Laser selected bit position
INJECT_CONTROL_LASER_SELECT_W = 2 # Laser selected bit width
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
INJECT_CONTROL_MANUAL_SOA_ENABLE_B = 11 # Enable SOA current (in manual mode) bit position
INJECT_CONTROL_MANUAL_SOA_ENABLE_W = 1 # Enable SOA current (in manual mode) bit width
INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B = 12 # Enables laser shutdown (in automatic mode) bit position
INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W = 1 # Enables laser shutdown (in automatic mode) bit width
INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B = 13 # Enables SOA shutdown (in automatic mode) bit position
INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W = 1 # Enables SOA shutdown (in automatic mode) bit width
INJECT_CONTROL_OPTICAL_SWITCH_SELECT_B = 14 # Select optical switch type bit position
INJECT_CONTROL_OPTICAL_SWITCH_SELECT_W = 1 # Select optical switch type bit width
INJECT_CONTROL_SOA_PRESENT_B = 15 # SOA or fiber amplifier present bit position
INJECT_CONTROL_SOA_PRESENT_W = 1 # SOA or fiber amplifier present bit width

INJECT_CONTROL2 = 1 # Control register 2
INJECT_CONTROL2_FIBER_AMP_PRESENT_B = 0 # Fiber amplifier present bit position
INJECT_CONTROL2_FIBER_AMP_PRESENT_W = 1 # Fiber amplifier present bit width
INJECT_CONTROL2_EXTINGUISH_DESELECTED_B = 1 # Turn off deselected lasers bit position
INJECT_CONTROL2_EXTINGUISH_DESELECTED_W = 1 # Turn off deselected lasers bit width
INJECT_CONTROL2_EXTRA_MODE_B = 2 # How is extra laser current controlled? bit position
INJECT_CONTROL2_EXTRA_MODE_W = 1 # How is extra laser current controlled? bit width
INJECT_CONTROL2_EXTRA_ENABLE_B = 3 # Bit for controlling extra laser current bit position
INJECT_CONTROL2_EXTRA_ENABLE_W = 1 # Bit for controlling extra laser current bit width
INJECT_CONTROL2_EXTENDED_CURRENT_MODE_B = 4 # Use extended laser current control bit position
INJECT_CONTROL2_EXTENDED_CURRENT_MODE_W = 1 # Use extended laser current control bit width
INJECT_CONTROL2_DISABLE_SOA_WITH_LASER_B = 5 # Disable SOA for some lasers bit position
INJECT_CONTROL2_DISABLE_SOA_WITH_LASER_W = 4 # Disable SOA for some lasers bit width
INJECT_CONTROL2_DISABLE_SOA_WITH_LASER1_B = 5 # Disable SOA for laser 1 bit position
INJECT_CONTROL2_DISABLE_SOA_WITH_LASER1_W = 1 # Disable SOA for laser 1 bit width
INJECT_CONTROL2_DISABLE_SOA_WITH_LASER2_B = 6 # Disable SOA for laser 2 bit position
INJECT_CONTROL2_DISABLE_SOA_WITH_LASER2_W = 1 # Disable SOA for laser 2 bit width
INJECT_CONTROL2_DISABLE_SOA_WITH_LASER3_B = 7 # Disable SOA for laser 3 bit position
INJECT_CONTROL2_DISABLE_SOA_WITH_LASER3_W = 1 # Disable SOA for laser 3 bit width
INJECT_CONTROL2_DISABLE_SOA_WITH_LASER4_B = 8 # Disable SOA for laser 4 bit position
INJECT_CONTROL2_DISABLE_SOA_WITH_LASER4_W = 1 # Disable SOA for laser 4 bit width

INJECT_LASER1_COARSE_CURRENT = 2 # Sets coarse current for laser 1
INJECT_LASER2_COARSE_CURRENT = 3 # Sets coarse current for laser 2
INJECT_LASER3_COARSE_CURRENT = 4 # Sets coarse current for laser 3
INJECT_LASER4_COARSE_CURRENT = 5 # Sets coarse current for laser 4
INJECT_LASER1_FINE_CURRENT = 6 # Sets fine current for laser 1
INJECT_LASER2_FINE_CURRENT = 7 # Sets fine current for laser 2
INJECT_LASER3_FINE_CURRENT = 8 # Sets fine current for laser 3
INJECT_LASER4_FINE_CURRENT = 9 # Sets fine current for laser 4
INJECT_LASER1_FINE_CURRENT_RANGE = 10 # Sets range for laser 1 fine current in automatic mode
INJECT_LASER2_FINE_CURRENT_RANGE = 11 # Sets range for laser 2 fine current in automatic mode
INJECT_LASER3_FINE_CURRENT_RANGE = 12 # Sets range for laser 3 fine current in automatic mode
INJECT_LASER4_FINE_CURRENT_RANGE = 13 # Sets range for laser 4 fine current in automatic mode
INJECT_LASER1_EXTRA_COARSE_SCALE = 14 # Scale factor for laser 1 coarse current when in extra current mode
INJECT_LASER2_EXTRA_COARSE_SCALE = 15 # Scale factor for laser 2 coarse current when in extra current mode
INJECT_LASER3_EXTRA_COARSE_SCALE = 16 # Scale factor for laser 3 coarse current when in extra current mode
INJECT_LASER4_EXTRA_COARSE_SCALE = 17 # Scale factor for laser 4 coarse current when in extra current mode
INJECT_LASER1_EXTRA_FINE_SCALE = 18 # Scale factor for laser 1 fine current when in extra current mode
INJECT_LASER2_EXTRA_FINE_SCALE = 19 # Scale factor for laser 2 fine current when in extra current mode
INJECT_LASER3_EXTRA_FINE_SCALE = 20 # Scale factor for laser 3 fine current when in extra current mode
INJECT_LASER4_EXTRA_FINE_SCALE = 21 # Scale factor for laser 4 fine current when in extra current mode
INJECT_LASER1_EXTRA_OFFSET = 22 # Offset for laser 1 current when in extra current mode
INJECT_LASER2_EXTRA_OFFSET = 23 # Offset for laser 2 current when in extra current mode
INJECT_LASER3_EXTRA_OFFSET = 24 # Offset for laser 3 current when in extra current mode
INJECT_LASER4_EXTRA_OFFSET = 25 # Offset for laser 4 current when in extra current mode

# Block WLMSIM Wavelength monitor simulator
WLMSIM_OPTIONS = 0 # Options
WLMSIM_OPTIONS_INPUT_SEL_B = 0 # Input select bit position
WLMSIM_OPTIONS_INPUT_SEL_W = 1 # Input select bit width

WLMSIM_Z0 = 1 # Phase angle
WLMSIM_RFAC = 2 # Reflectivity factor
WLMSIM_WFAC = 3 # Width factor of simulated spectrum
WLMSIM_LASER_TEMP = 4 # 
WLMSIM_ETA1_OFFSET = 5 # Etalon 1 offset
WLMSIM_REF1_OFFSET = 6 # Reference 1 offset
WLMSIM_ETA2_OFFSET = 7 # Etalon 2 offset
WLMSIM_REF2_OFFSET = 8 # Reference 2 offset

# Block DYNAMICPWM Dynamic PWM for proportional valves
DYNAMICPWM_CS = 0 # Control/Status
DYNAMICPWM_CS_RUN_B = 0 # Stop/Run bit position
DYNAMICPWM_CS_RUN_W = 1 # Stop/Run bit width
DYNAMICPWM_CS_CONT_B = 1 # Single/Continuous bit position
DYNAMICPWM_CS_CONT_W = 1 # Single/Continuous bit width
DYNAMICPWM_CS_PWM_ENABLE_B = 2 # PWM enable bit position
DYNAMICPWM_CS_PWM_ENABLE_W = 1 # PWM enable bit width
DYNAMICPWM_CS_USE_COMPARATOR_B = 3 # Use comparator bit position
DYNAMICPWM_CS_USE_COMPARATOR_W = 1 # Use comparator bit width
DYNAMICPWM_CS_PWM_OUT_B = 4 # PWM output bit position
DYNAMICPWM_CS_PWM_OUT_W = 1 # PWM output bit width
DYNAMICPWM_CS_PWM_INVERT_B = 5 # Invert polarity of PWM signal bit position
DYNAMICPWM_CS_PWM_INVERT_W = 1 # Invert polarity of PWM signal bit width

DYNAMICPWM_DELTA = 1 # Pulse width change per update
DYNAMICPWM_HIGH = 2 # Upper limit of dither waveform
DYNAMICPWM_LOW = 3 # Lower limit of dither waveform
DYNAMICPWM_SLOPE = 4 # Slope of dither waveform

# Block SCALER PZT voltage scaler
SCALER_SCALE1 = 0 # Scale factor for PZT waveform

# Block LASERCURRENTGENERATOR Laser current waveform generator
LASERCURRENTGENERATOR_CONTROL_STATUS = 0 # Control status register
LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B = 0 # Register capture mode bit position
LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_W = 1 # Register capture mode bit width
LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_B = 1 # Select actual laser index bit position
LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_W = 2 # Select actual laser index bit width
LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_B = 3 # Select memory bank to use bit position
LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_W = 1 # Select memory bank to use bit width

LASERCURRENTGENERATOR_SLOW_SLOPE = 1 # 
LASERCURRENTGENERATOR_FAST_SLOPE = 2 # 
LASERCURRENTGENERATOR_FIRST_OFFSET = 3 # 
LASERCURRENTGENERATOR_SECOND_OFFSET = 4 # 
LASERCURRENTGENERATOR_FIRST_BREAKPOINT = 5 # 
LASERCURRENTGENERATOR_SECOND_BREAKPOINT = 6 # 
LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT = 7 # 
LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT = 8 # 
LASERCURRENTGENERATOR_LOWER_WINDOW = 9 # 
LASERCURRENTGENERATOR_UPPER_WINDOW = 10 # 
LASERCURRENTGENERATOR_SEQUENCE_ID = 11 # 

# FPGA registers by name
fpgaRegByName = {}
fpgaRegByName["KERNEL_MAGIC_CODE"] = KERNEL_MAGIC_CODE
fpgaRegByName["KERNEL_CONTROL"] = KERNEL_CONTROL
fpgaRegByName["KERNEL_DIAG_1"] = KERNEL_DIAG_1
fpgaRegByName["KERNEL_CONFIG"] = KERNEL_CONFIG
fpgaRegByName["KERNEL_INTRONIX_CLKSEL"] = KERNEL_INTRONIX_CLKSEL
fpgaRegByName["KERNEL_INTRONIX_1"] = KERNEL_INTRONIX_1
fpgaRegByName["KERNEL_INTRONIX_2"] = KERNEL_INTRONIX_2
fpgaRegByName["KERNEL_INTRONIX_3"] = KERNEL_INTRONIX_3
fpgaRegByName["KERNEL_OVERLOAD"] = KERNEL_OVERLOAD
fpgaRegByName["KERNEL_DOUT_HI"] = KERNEL_DOUT_HI
fpgaRegByName["KERNEL_DOUT_LO"] = KERNEL_DOUT_LO
fpgaRegByName["KERNEL_DIN"] = KERNEL_DIN
fpgaRegByName["PWM_CS"] = PWM_CS
fpgaRegByName["PWM_PULSE_WIDTH"] = PWM_PULSE_WIDTH
fpgaRegByName["RDSIM_OPTIONS"] = RDSIM_OPTIONS
fpgaRegByName["RDSIM_PZT_CENTER"] = RDSIM_PZT_CENTER
fpgaRegByName["RDSIM_PZT_WINDOW_HALF_WIDTH"] = RDSIM_PZT_WINDOW_HALF_WIDTH
fpgaRegByName["RDSIM_FILLING_RATE"] = RDSIM_FILLING_RATE
fpgaRegByName["RDSIM_DECAY"] = RDSIM_DECAY
fpgaRegByName["RDSIM_DECAY_IN_SHIFT"] = RDSIM_DECAY_IN_SHIFT
fpgaRegByName["RDSIM_DECAY_IN_OFFSET"] = RDSIM_DECAY_IN_OFFSET
fpgaRegByName["RDSIM_ACCUMULATOR"] = RDSIM_ACCUMULATOR
fpgaRegByName["LASERLOCKER_CS"] = LASERLOCKER_CS
fpgaRegByName["LASERLOCKER_OPTIONS"] = LASERLOCKER_OPTIONS
fpgaRegByName["LASERLOCKER_ETA1"] = LASERLOCKER_ETA1
fpgaRegByName["LASERLOCKER_REF1"] = LASERLOCKER_REF1
fpgaRegByName["LASERLOCKER_ETA2"] = LASERLOCKER_ETA2
fpgaRegByName["LASERLOCKER_REF2"] = LASERLOCKER_REF2
fpgaRegByName["LASERLOCKER_ETA1_DARK"] = LASERLOCKER_ETA1_DARK
fpgaRegByName["LASERLOCKER_REF1_DARK"] = LASERLOCKER_REF1_DARK
fpgaRegByName["LASERLOCKER_ETA2_DARK"] = LASERLOCKER_ETA2_DARK
fpgaRegByName["LASERLOCKER_REF2_DARK"] = LASERLOCKER_REF2_DARK
fpgaRegByName["LASERLOCKER_ETA1_OFFSET"] = LASERLOCKER_ETA1_OFFSET
fpgaRegByName["LASERLOCKER_REF1_OFFSET"] = LASERLOCKER_REF1_OFFSET
fpgaRegByName["LASERLOCKER_ETA2_OFFSET"] = LASERLOCKER_ETA2_OFFSET
fpgaRegByName["LASERLOCKER_REF2_OFFSET"] = LASERLOCKER_REF2_OFFSET
fpgaRegByName["LASERLOCKER_RATIO1"] = LASERLOCKER_RATIO1
fpgaRegByName["LASERLOCKER_RATIO2"] = LASERLOCKER_RATIO2
fpgaRegByName["LASERLOCKER_RATIO1_CENTER"] = LASERLOCKER_RATIO1_CENTER
fpgaRegByName["LASERLOCKER_RATIO1_MULTIPLIER"] = LASERLOCKER_RATIO1_MULTIPLIER
fpgaRegByName["LASERLOCKER_RATIO2_CENTER"] = LASERLOCKER_RATIO2_CENTER
fpgaRegByName["LASERLOCKER_RATIO2_MULTIPLIER"] = LASERLOCKER_RATIO2_MULTIPLIER
fpgaRegByName["LASERLOCKER_TUNING_OFFSET"] = LASERLOCKER_TUNING_OFFSET
fpgaRegByName["LASERLOCKER_LOCK_ERROR"] = LASERLOCKER_LOCK_ERROR
fpgaRegByName["LASERLOCKER_WM_LOCK_WINDOW"] = LASERLOCKER_WM_LOCK_WINDOW
fpgaRegByName["LASERLOCKER_WM_INT_GAIN"] = LASERLOCKER_WM_INT_GAIN
fpgaRegByName["LASERLOCKER_WM_PROP_GAIN"] = LASERLOCKER_WM_PROP_GAIN
fpgaRegByName["LASERLOCKER_WM_DERIV_GAIN"] = LASERLOCKER_WM_DERIV_GAIN
fpgaRegByName["LASERLOCKER_FINE_CURRENT"] = LASERLOCKER_FINE_CURRENT
fpgaRegByName["LASERLOCKER_CYCLE_COUNTER"] = LASERLOCKER_CYCLE_COUNTER
fpgaRegByName["RDMAN_CONTROL"] = RDMAN_CONTROL
fpgaRegByName["RDMAN_STATUS"] = RDMAN_STATUS
fpgaRegByName["RDMAN_OPTIONS"] = RDMAN_OPTIONS
fpgaRegByName["RDMAN_PARAM0"] = RDMAN_PARAM0
fpgaRegByName["RDMAN_PARAM1"] = RDMAN_PARAM1
fpgaRegByName["RDMAN_PARAM2"] = RDMAN_PARAM2
fpgaRegByName["RDMAN_PARAM3"] = RDMAN_PARAM3
fpgaRegByName["RDMAN_PARAM4"] = RDMAN_PARAM4
fpgaRegByName["RDMAN_PARAM5"] = RDMAN_PARAM5
fpgaRegByName["RDMAN_PARAM6"] = RDMAN_PARAM6
fpgaRegByName["RDMAN_PARAM7"] = RDMAN_PARAM7
fpgaRegByName["RDMAN_PARAM8"] = RDMAN_PARAM8
fpgaRegByName["RDMAN_PARAM9"] = RDMAN_PARAM9
fpgaRegByName["RDMAN_DATA_ADDRCNTR"] = RDMAN_DATA_ADDRCNTR
fpgaRegByName["RDMAN_METADATA_ADDRCNTR"] = RDMAN_METADATA_ADDRCNTR
fpgaRegByName["RDMAN_PARAM_ADDRCNTR"] = RDMAN_PARAM_ADDRCNTR
fpgaRegByName["RDMAN_DIVISOR"] = RDMAN_DIVISOR
fpgaRegByName["RDMAN_NUM_SAMP"] = RDMAN_NUM_SAMP
fpgaRegByName["RDMAN_THRESHOLD"] = RDMAN_THRESHOLD
fpgaRegByName["RDMAN_LOCK_DURATION"] = RDMAN_LOCK_DURATION
fpgaRegByName["RDMAN_PRECONTROL_DURATION"] = RDMAN_PRECONTROL_DURATION
fpgaRegByName["RDMAN_OFF_DURATION"] = RDMAN_OFF_DURATION
fpgaRegByName["RDMAN_EXTRA_DURATION"] = RDMAN_EXTRA_DURATION
fpgaRegByName["RDMAN_TIMEOUT_DURATION"] = RDMAN_TIMEOUT_DURATION
fpgaRegByName["RDMAN_TUNER_AT_RINGDOWN"] = RDMAN_TUNER_AT_RINGDOWN
fpgaRegByName["RDMAN_METADATA_ADDR_AT_RINGDOWN"] = RDMAN_METADATA_ADDR_AT_RINGDOWN
fpgaRegByName["RDMAN_RINGDOWN_DATA"] = RDMAN_RINGDOWN_DATA
fpgaRegByName["TWGEN_ACC"] = TWGEN_ACC
fpgaRegByName["TWGEN_CS"] = TWGEN_CS
fpgaRegByName["TWGEN_SLOPE_DOWN"] = TWGEN_SLOPE_DOWN
fpgaRegByName["TWGEN_SLOPE_UP"] = TWGEN_SLOPE_UP
fpgaRegByName["TWGEN_SWEEP_LOW"] = TWGEN_SWEEP_LOW
fpgaRegByName["TWGEN_SWEEP_HIGH"] = TWGEN_SWEEP_HIGH
fpgaRegByName["TWGEN_WINDOW_LOW"] = TWGEN_WINDOW_LOW
fpgaRegByName["TWGEN_WINDOW_HIGH"] = TWGEN_WINDOW_HIGH
fpgaRegByName["TWGEN_PZT_OFFSET"] = TWGEN_PZT_OFFSET
fpgaRegByName["INJECT_CONTROL"] = INJECT_CONTROL
fpgaRegByName["INJECT_CONTROL2"] = INJECT_CONTROL2
fpgaRegByName["INJECT_LASER1_COARSE_CURRENT"] = INJECT_LASER1_COARSE_CURRENT
fpgaRegByName["INJECT_LASER2_COARSE_CURRENT"] = INJECT_LASER2_COARSE_CURRENT
fpgaRegByName["INJECT_LASER3_COARSE_CURRENT"] = INJECT_LASER3_COARSE_CURRENT
fpgaRegByName["INJECT_LASER4_COARSE_CURRENT"] = INJECT_LASER4_COARSE_CURRENT
fpgaRegByName["INJECT_LASER1_FINE_CURRENT"] = INJECT_LASER1_FINE_CURRENT
fpgaRegByName["INJECT_LASER2_FINE_CURRENT"] = INJECT_LASER2_FINE_CURRENT
fpgaRegByName["INJECT_LASER3_FINE_CURRENT"] = INJECT_LASER3_FINE_CURRENT
fpgaRegByName["INJECT_LASER4_FINE_CURRENT"] = INJECT_LASER4_FINE_CURRENT
fpgaRegByName["INJECT_LASER1_FINE_CURRENT_RANGE"] = INJECT_LASER1_FINE_CURRENT_RANGE
fpgaRegByName["INJECT_LASER2_FINE_CURRENT_RANGE"] = INJECT_LASER2_FINE_CURRENT_RANGE
fpgaRegByName["INJECT_LASER3_FINE_CURRENT_RANGE"] = INJECT_LASER3_FINE_CURRENT_RANGE
fpgaRegByName["INJECT_LASER4_FINE_CURRENT_RANGE"] = INJECT_LASER4_FINE_CURRENT_RANGE
fpgaRegByName["INJECT_LASER1_EXTRA_COARSE_SCALE"] = INJECT_LASER1_EXTRA_COARSE_SCALE
fpgaRegByName["INJECT_LASER2_EXTRA_COARSE_SCALE"] = INJECT_LASER2_EXTRA_COARSE_SCALE
fpgaRegByName["INJECT_LASER3_EXTRA_COARSE_SCALE"] = INJECT_LASER3_EXTRA_COARSE_SCALE
fpgaRegByName["INJECT_LASER4_EXTRA_COARSE_SCALE"] = INJECT_LASER4_EXTRA_COARSE_SCALE
fpgaRegByName["INJECT_LASER1_EXTRA_FINE_SCALE"] = INJECT_LASER1_EXTRA_FINE_SCALE
fpgaRegByName["INJECT_LASER2_EXTRA_FINE_SCALE"] = INJECT_LASER2_EXTRA_FINE_SCALE
fpgaRegByName["INJECT_LASER3_EXTRA_FINE_SCALE"] = INJECT_LASER3_EXTRA_FINE_SCALE
fpgaRegByName["INJECT_LASER4_EXTRA_FINE_SCALE"] = INJECT_LASER4_EXTRA_FINE_SCALE
fpgaRegByName["INJECT_LASER1_EXTRA_OFFSET"] = INJECT_LASER1_EXTRA_OFFSET
fpgaRegByName["INJECT_LASER2_EXTRA_OFFSET"] = INJECT_LASER2_EXTRA_OFFSET
fpgaRegByName["INJECT_LASER3_EXTRA_OFFSET"] = INJECT_LASER3_EXTRA_OFFSET
fpgaRegByName["INJECT_LASER4_EXTRA_OFFSET"] = INJECT_LASER4_EXTRA_OFFSET
fpgaRegByName["WLMSIM_OPTIONS"] = WLMSIM_OPTIONS
fpgaRegByName["WLMSIM_Z0"] = WLMSIM_Z0
fpgaRegByName["WLMSIM_RFAC"] = WLMSIM_RFAC
fpgaRegByName["WLMSIM_WFAC"] = WLMSIM_WFAC
fpgaRegByName["WLMSIM_LASER_TEMP"] = WLMSIM_LASER_TEMP
fpgaRegByName["WLMSIM_ETA1_OFFSET"] = WLMSIM_ETA1_OFFSET
fpgaRegByName["WLMSIM_REF1_OFFSET"] = WLMSIM_REF1_OFFSET
fpgaRegByName["WLMSIM_ETA2_OFFSET"] = WLMSIM_ETA2_OFFSET
fpgaRegByName["WLMSIM_REF2_OFFSET"] = WLMSIM_REF2_OFFSET
fpgaRegByName["DYNAMICPWM_CS"] = DYNAMICPWM_CS
fpgaRegByName["DYNAMICPWM_DELTA"] = DYNAMICPWM_DELTA
fpgaRegByName["DYNAMICPWM_HIGH"] = DYNAMICPWM_HIGH
fpgaRegByName["DYNAMICPWM_LOW"] = DYNAMICPWM_LOW
fpgaRegByName["DYNAMICPWM_SLOPE"] = DYNAMICPWM_SLOPE
fpgaRegByName["SCALER_SCALE1"] = SCALER_SCALE1
fpgaRegByName["LASERCURRENTGENERATOR_CONTROL_STATUS"] = LASERCURRENTGENERATOR_CONTROL_STATUS
fpgaRegByName["LASERCURRENTGENERATOR_SLOW_SLOPE"] = LASERCURRENTGENERATOR_SLOW_SLOPE
fpgaRegByName["LASERCURRENTGENERATOR_FAST_SLOPE"] = LASERCURRENTGENERATOR_FAST_SLOPE
fpgaRegByName["LASERCURRENTGENERATOR_FIRST_OFFSET"] = LASERCURRENTGENERATOR_FIRST_OFFSET
fpgaRegByName["LASERCURRENTGENERATOR_SECOND_OFFSET"] = LASERCURRENTGENERATOR_SECOND_OFFSET
fpgaRegByName["LASERCURRENTGENERATOR_FIRST_BREAKPOINT"] = LASERCURRENTGENERATOR_FIRST_BREAKPOINT
fpgaRegByName["LASERCURRENTGENERATOR_SECOND_BREAKPOINT"] = LASERCURRENTGENERATOR_SECOND_BREAKPOINT
fpgaRegByName["LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT"] = LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT
fpgaRegByName["LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT"] = LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT
fpgaRegByName["LASERCURRENTGENERATOR_LOWER_WINDOW"] = LASERCURRENTGENERATOR_LOWER_WINDOW
fpgaRegByName["LASERCURRENTGENERATOR_UPPER_WINDOW"] = LASERCURRENTGENERATOR_UPPER_WINDOW
fpgaRegByName["LASERCURRENTGENERATOR_SEQUENCE_ID"] = LASERCURRENTGENERATOR_SEQUENCE_ID

# FPGA map indices
FPGA_KERNEL = 0 # Kernel registers
FPGA_PWM_LASER1 = 12 # Laser 1 TEC pulse width modulator registers
FPGA_PWM_LASER2 = 14 # Laser 2 TEC pulse width modulator registers
FPGA_PWM_LASER3 = 16 # Laser 3 TEC pulse width modulator registers
FPGA_PWM_LASER4 = 18 # Laser 4 TEC pulse width modulator registers
FPGA_PWM_WARMBOX = 20 # Warm box TEC pulse width modulator registers
FPGA_PWM_HOTBOX = 22 # Hot box TEC pulse width modulator registers
FPGA_PWM_ENGINE1 = 24 # Engine 1 TEC pulse width modulator registers
FPGA_PWM_ENGINE2 = 26 # Engine 2 TEC pulse width modulator registers
FPGA_PWM_HEATER = 28 # Heater pulse width modulator registers
FPGA_RDSIM = 30 # Ringdown simulator registers
FPGA_LASERLOCKER = 38 # Laser frequency locker registers
FPGA_RDMAN = 66 # Ringdown manager registers
FPGA_TWGEN = 93 # Tuner waveform generator
FPGA_INJECT = 102 # Optical Injection Subsystem
FPGA_WLMSIM = 128 # WLM Simulator
FPGA_DYNAMICPWM_INLET = 137 # Inlet proportional valve dynamic PWM
FPGA_DYNAMICPWM_OUTLET = 142 # Outlet proportional valve dynamic PWM
FPGA_SCALER = 147 # Scaler for PZT waveform
FPGA_LASERCURRENTGENERATOR = 148 # Laser current generator

# FPGA map dictionary
fpgaMapByName = {}
fpgaMapByName["FPGA_KERNEL"] = FPGA_KERNEL
fpgaMapByName["FPGA_PWM_LASER1"] = FPGA_PWM_LASER1
fpgaMapByName["FPGA_PWM_LASER2"] = FPGA_PWM_LASER2
fpgaMapByName["FPGA_PWM_LASER3"] = FPGA_PWM_LASER3
fpgaMapByName["FPGA_PWM_LASER4"] = FPGA_PWM_LASER4
fpgaMapByName["FPGA_PWM_WARMBOX"] = FPGA_PWM_WARMBOX
fpgaMapByName["FPGA_PWM_HOTBOX"] = FPGA_PWM_HOTBOX
fpgaMapByName["FPGA_PWM_ENGINE1"] = FPGA_PWM_ENGINE1
fpgaMapByName["FPGA_PWM_ENGINE2"] = FPGA_PWM_ENGINE2
fpgaMapByName["FPGA_PWM_HEATER"] = FPGA_PWM_HEATER
fpgaMapByName["FPGA_RDSIM"] = FPGA_RDSIM
fpgaMapByName["FPGA_LASERLOCKER"] = FPGA_LASERLOCKER
fpgaMapByName["FPGA_RDMAN"] = FPGA_RDMAN
fpgaMapByName["FPGA_TWGEN"] = FPGA_TWGEN
fpgaMapByName["FPGA_INJECT"] = FPGA_INJECT
fpgaMapByName["FPGA_WLMSIM"] = FPGA_WLMSIM
fpgaMapByName["FPGA_DYNAMICPWM_INLET"] = FPGA_DYNAMICPWM_INLET
fpgaMapByName["FPGA_DYNAMICPWM_OUTLET"] = FPGA_DYNAMICPWM_OUTLET
fpgaMapByName["FPGA_SCALER"] = FPGA_SCALER
fpgaMapByName["FPGA_LASERCURRENTGENERATOR"] = FPGA_LASERCURRENTGENERATOR

persistent_fpga_registers = []
persistent_fpga_registers.append((u'FPGA_KERNEL', [u'KERNEL_CONFIG', u'KERNEL_INTRONIX_CLKSEL', u'KERNEL_INTRONIX_1', u'KERNEL_INTRONIX_2', u'KERNEL_INTRONIX_3']))
persistent_fpga_registers.append((u'FPGA_RDSIM', [u'RDSIM_OPTIONS', u'RDSIM_PZT_WINDOW_HALF_WIDTH', u'RDSIM_FILLING_RATE', u'RDSIM_DECAY_IN_SHIFT', u'RDSIM_DECAY_IN_OFFSET']))
persistent_fpga_registers.append((u'FPGA_LASERLOCKER', [u'LASERLOCKER_OPTIONS', u'LASERLOCKER_ETA1_OFFSET', u'LASERLOCKER_REF1_OFFSET', u'LASERLOCKER_ETA2_OFFSET', u'LASERLOCKER_REF2_OFFSET', u'LASERLOCKER_TUNING_OFFSET', u'LASERLOCKER_WM_LOCK_WINDOW', u'LASERLOCKER_WM_INT_GAIN', u'LASERLOCKER_WM_PROP_GAIN', u'LASERLOCKER_WM_DERIV_GAIN']))
persistent_fpga_registers.append((u'FPGA_RDMAN', [u'RDMAN_OPTIONS', u'RDMAN_DIVISOR', u'RDMAN_NUM_SAMP', u'RDMAN_THRESHOLD', u'RDMAN_LOCK_DURATION', u'RDMAN_PRECONTROL_DURATION', u'RDMAN_OFF_DURATION', u'RDMAN_EXTRA_DURATION']))
persistent_fpga_registers.append((u'FPGA_TWGEN', [u'TWGEN_SLOPE_DOWN', u'TWGEN_SLOPE_UP']))
persistent_fpga_registers.append((u'FPGA_INJECT', [u'INJECT_CONTROL', u'INJECT_CONTROL2', u'INJECT_LASER1_FINE_CURRENT_RANGE', u'INJECT_LASER2_FINE_CURRENT_RANGE', u'INJECT_LASER3_FINE_CURRENT_RANGE', u'INJECT_LASER4_FINE_CURRENT_RANGE']))
persistent_fpga_registers.append((u'FPGA_WLMSIM', [u'WLMSIM_OPTIONS', u'WLMSIM_RFAC', u'WLMSIM_WFAC', u'WLMSIM_ETA1_OFFSET', u'WLMSIM_REF1_OFFSET', u'WLMSIM_ETA2_OFFSET', u'WLMSIM_REF2_OFFSET']))
persistent_fpga_registers.append((u'FPGA_DYNAMICPWM_INLET', [u'DYNAMICPWM_DELTA', u'DYNAMICPWM_SLOPE']))
persistent_fpga_registers.append((u'FPGA_DYNAMICPWM_OUTLET', [u'DYNAMICPWM_DELTA', u'DYNAMICPWM_SLOPE']))
persistent_fpga_registers.append((u'FPGA_SCALER', [u'SCALER_SCALE1']))
persistent_fpga_registers.append((u'FPGA_LASERCURRENTGENERATOR', [u'LASERCURRENTGENERATOR_CONTROL_STATUS', u'LASERCURRENTGENERATOR_SLOW_SLOPE', u'LASERCURRENTGENERATOR_FAST_SLOPE', u'LASERCURRENTGENERATOR_FIRST_OFFSET', u'LASERCURRENTGENERATOR_SECOND_OFFSET', u'LASERCURRENTGENERATOR_FIRST_BREAKPOINT', u'LASERCURRENTGENERATOR_SECOND_BREAKPOINT', u'LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT', u'LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT', u'LASERCURRENTGENERATOR_LOWER_WINDOW', u'LASERCURRENTGENERATOR_UPPER_WINDOW']))

# Environment addresses
BYTE4_ENV = 0
BYTE16_ENV = 1
BYTE64_ENV = 5
WARM_BOX_TEC_INTERPOLATOR_ENV = 21
CAVITY_TEC_INTERPOLATOR_ENV = 24
HEATER_INTERPOLATOR_ENV = 27
LASER1_TEMP_MODEL_ENV = 30
LASER2_TEMP_MODEL_ENV = 57
LASER3_TEMP_MODEL_ENV = 84
LASER4_TEMP_MODEL_ENV = 111

# Dictionary for accessing environments by name
envByName = {}
envByName['BYTE4_ENV'] = (BYTE4_ENV,Byte4EnvType)
envByName['BYTE16_ENV'] = (BYTE16_ENV,Byte16EnvType)
envByName['BYTE64_ENV'] = (BYTE64_ENV,Byte64EnvType)
envByName['WARM_BOX_TEC_INTERPOLATOR_ENV'] = (WARM_BOX_TEC_INTERPOLATOR_ENV,InterpolatorEnvType)
envByName['CAVITY_TEC_INTERPOLATOR_ENV'] = (CAVITY_TEC_INTERPOLATOR_ENV,InterpolatorEnvType)
envByName['HEATER_INTERPOLATOR_ENV'] = (HEATER_INTERPOLATOR_ENV,InterpolatorEnvType)
envByName['LASER1_TEMP_MODEL_ENV'] = (LASER1_TEMP_MODEL_ENV,FilterEnvType)
envByName['LASER2_TEMP_MODEL_ENV'] = (LASER2_TEMP_MODEL_ENV,FilterEnvType)
envByName['LASER3_TEMP_MODEL_ENV'] = (LASER3_TEMP_MODEL_ENV,FilterEnvType)
envByName['LASER4_TEMP_MODEL_ENV'] = (LASER4_TEMP_MODEL_ENV,FilterEnvType)

# Action codes
ACTION_WRITE_BLOCK = 1
ACTION_SET_TIMESTAMP = 2
ACTION_GET_TIMESTAMP = 3
ACTION_INIT_RUNQUEUE = 4
ACTION_TEST_SCHEDULER = 5
ACTION_STREAM_REGISTER_ASFLOAT = 6
ACTION_STREAM_FPGA_REGISTER_ASFLOAT = 7
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
ACTION_FAN_CNTRL_INIT = 40
ACTION_FAN_CNTRL_STEP = 41
ACTION_ACTIVATE_FAN = 42
ACTION_ENV_CHECKER = 43
ACTION_WB_INV_CACHE = 44
ACTION_WB_CACHE = 45
ACTION_SCHEDULER_HEARTBEAT = 46
ACTION_SENTRY_INIT = 47
ACTION_VALVE_CNTRL_INIT = 48
ACTION_VALVE_CNTRL_STEP = 49
ACTION_PEAK_DETECT_CNTRL_INIT = 50
ACTION_PEAK_DETECT_CNTRL_STEP = 51
ACTION_MODIFY_VALVE_PUMP_TEC_FROM_REGISTER = 52
ACTION_PULSE_GENERATOR = 53
ACTION_FILTER = 54
ACTION_DS1631_READTEMP = 55
ACTION_READ_THERMISTOR_RESISTANCE = 56
ACTION_READ_LASER_CURRENT = 57
ACTION_UPDATE_WLMSIM_LASER_TEMP = 58
ACTION_SIMULATE_LASER_CURRENT_READING = 59
ACTION_READ_PRESSURE_ADC = 60
ACTION_ADC_TO_PRESSURE = 61
ACTION_SET_INLET_VALVE = 62
ACTION_SET_OUTLET_VALVE = 63
ACTION_INTERPOLATOR_SET_TARGET = 64
ACTION_INTERPOLATOR_STEP = 65
ACTION_EEPROM_WRITE = 66
ACTION_EEPROM_READ = 67
ACTION_EEPROM_READY = 68
ACTION_I2C_CHECK = 69
ACTION_NUDGE_TIMESTAMP = 70
ACTION_EEPROM_WRITE_LOW_LEVEL = 71
ACTION_EEPROM_READ_LOW_LEVEL = 72
ACTION_EEPROM_READY_LOW_LEVEL = 73
ACTION_FLOAT_ARITHMETIC = 74
ACTION_GET_SCOPE_TRACE = 75
ACTION_RELEASE_SCOPE_TRACE = 76
ACTION_READ_FLOW_SENSOR = 77
ACTION_RDD_CNTRL_INIT = 78
ACTION_RDD_CNTRL_STEP = 79
ACTION_RDD_CNTRL_DO_COMMAND = 80
ACTION_BATTERY_MONITOR_WRITE_BYTE = 81
ACTION_BATTERY_MONITOR_READ_REGS = 82
ACTION_ACC_READ_REG = 83
ACTION_ACC_WRITE_REG = 84
ACTION_ACC_READ_ACCEL = 85
ACTION_READ_THERMISTOR_RESISTANCE_16BIT = 86
ACTION_AVERAGE_FLOAT_REGISTERS = 87

# Aliases
PEAK_DETECT_CNTRL_RESET_DELAY_REGISTER = PEAK_DETECT_CNTRL_TRIGGERED_DURATION_REGISTER # Old name for number of samples spent in triggered state
registerByName["PEAK_DETECT_CNTRL_RESET_DELAY_REGISTER"] = PEAK_DETECT_CNTRL_TRIGGERED_DURATION_REGISTER
PEAK_DETECT_CNTRL_REMAINING_TRIGGERED_SAMPLES_REGISTER = PEAK_DETECT_CNTRL_REMAINING_SAMPLES_REGISTER # Old name for register tracking number of samples left in capture mode
registerByName["PEAK_DETECT_CNTRL_REMAINING_TRIGGERED_SAMPLES_REGISTER"] = PEAK_DETECT_CNTRL_REMAINING_SAMPLES_REGISTER


# Parameter form definitions

parameter_forms = []

# Form: System Parameters

__p = []

__p.append(('dsp','uint32',DAS_STATUS_REGISTER,'DAS Status','','$%X',1,0))
__p.append(('dsp','uint32',SCHEDULER_CONTROL_REGISTER,'Scheduler enable','','%d',1,1))
__p.append(('dsp','uint32',RD_INITIATED_COUNT_REGISTER,'RD initiated count','','%d',1,0))
__p.append(('dsp','uint32',RD_IRQ_COUNT_REGISTER,'Ringdown interrupt count','','%d',1,0))
__p.append(('dsp','uint32',ACQ_DONE_COUNT_REGISTER,'Acquisition done interrupt count','','%d',1,0))
__p.append(('dsp','uint32',RD_DATA_MOVING_COUNT_REGISTER,'QDMA start count','','%d',1,0))
__p.append(('dsp','uint32',RD_QDMA_DONE_COUNT_REGISTER,'QDMA done interrupt count','','%d',1,0))
__p.append(('dsp','uint32',RD_FITTING_COUNT_REGISTER,'RD fitting count','','%d',1,0))
__p.append(('dsp','int32',KEEP_ALIVE_REGISTER,'Keep alive register','','%d',1,1))
__p.append(('fpga','uint16',FPGA_KERNEL+KERNEL_OVERLOAD,'Overload status','','$%X',1,0))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_CONTROL,[(1, u'Reset Cypress FX2 and FPGA', [(0, u'Idle'), (1, u'Reset')]), (2, u'Reset overload register', [(0, u'Idle'), (2, u'Reset')]), (4, u'Reset i2c multiplexers', [(0, u'Idle'), (4, u'Reset')]), (8, u'Manually set FPGA digital outputs', [(0, u'Automatic control'), (8, u'Manual control')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_CONFIG,[(1, u'Auxiliary PZT Enable', [(0, u'Disable'), (1, u'Enable')]), (2, u'Engine 1 TEC Enable', [(0, u'Disable'), (2, u'Enable')]), (4, u'Engine 2 TEC Enable', [(0, u'Disable'), (4, u'Enable')])],None,None,1,1))
__p.append(('fpga','uint32',FPGA_KERNEL+KERNEL_DOUT_HI,'Manual FPGA digital outputs (bits 39-32)','','$%X',1,1))
__p.append(('fpga','uint32',FPGA_KERNEL+KERNEL_DOUT_LO,'Manual FPGA digital outputs (bits 31-0)','','$%X',1,1))
__p.append(('fpga','uint32',FPGA_KERNEL+KERNEL_DIN,'FPGA digital inputs (bits 63-40)','','$%X',1,0))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_INTRONIX_CLKSEL,[(31, u'Intronix sampling rate', [(0, u'20 ns'), (1, u'40 ns'), (2, u'80 ns'), (3, u'160 ns'), (4, u'320 ns'), (5, u'640 ns'), (6, u'1.28 us'), (7, u'2.56 us'), (8, u'5.12 us'), (9, u'10.24 us'), (10, u'20.48 us'), (11, u'40.96 us'), (12, u'81.92 us'), (13, u'163.8 us'), (14, u'327.7 us'), (15, u'655.4 us'), (16, u'1.311 ms'), (17, u'2.621 ms'), (18, u'5.243 ms'), (19, u'10.49 ms'), (20, u'20.97 ms'), (21, u'41.94 ms'), (22, u'83.39 ms'), (23, u'167.8 ms'), (24, u'335.5 ms'), (25, u'671.1 ms'), (26, u'1.342 s'), (27, u'2.684 s'), (28, u'5.368 s')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_INTRONIX_1,[(255, u'Intronix display 1 channel', [(0, u'Tuner waveform (LS)'), (1, u'Tuner waveform (MS)'), (2, u'Ringdown ADC waveform (LS)'), (3, u'Ringdown ADC waveform (MS)'), (4, u'Ringdown simulator waveform (LS)'), (5, u'Ringdown simulator waveform (MS)'), (6, u'Laser fine current (LS)'), (7, u'Laser fine current (MS)'), (8, u'Locker error (LS)'), (9, u'Locker error (MS)'), (10, u'Ratio 1 (LS)'), (11, u'Ratio 1 (MS)'), (12, u'Ratio 2 (LS)'), (13, u'Ratio 2 (MS)'), (14, u'PZT (LS)'), (15, u'PZT (MS)'), (16, u'Etalon 1 ADC (LS)'), (17, u'Etalon 1 ADC (MS)'), (18, u'Reference 1 ADC (LS)'), (19, u'Reference 1 ADC (MS)'), (20, u'Etalon 2 ADC (LS)'), (21, u'Etalon 2 ADC (MS)'), (22, u'Reference 2 ADC (LS)'), (23, u'Reference 2 ADC (MS)'), (24, u'WLM ADC signals'), (25, u'System clocks'), (26, u'PWM signals'), (27, u'I2C signals')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_INTRONIX_2,[(255, u'Intronix display 2 channel', [(0, u'Tuner waveform (LS)'), (1, u'Tuner waveform (MS)'), (2, u'Ringdown ADC waveform (LS)'), (3, u'Ringdown ADC waveform (MS)'), (4, u'Ringdown simulator waveform (LS)'), (5, u'Ringdown simulator waveform (MS)'), (6, u'Laser fine current (LS)'), (7, u'Laser fine current (MS)'), (8, u'Locker error (LS)'), (9, u'Locker error (MS)'), (10, u'Ratio 1 (LS)'), (11, u'Ratio 1 (MS)'), (12, u'Ratio 2 (LS)'), (13, u'Ratio 2 (MS)'), (14, u'PZT (LS)'), (15, u'PZT (MS)'), (16, u'Etalon 1 ADC (LS)'), (17, u'Etalon 1 ADC (MS)'), (18, u'Reference 1 ADC (LS)'), (19, u'Reference 1 ADC (MS)'), (20, u'Etalon 2 ADC (LS)'), (21, u'Etalon 2 ADC (MS)'), (22, u'Reference 2 ADC (LS)'), (23, u'Reference 2 ADC (MS)'), (24, u'WLM ADC signals'), (25, u'System clocks'), (26, u'PWM signals'), (27, u'I2C signals')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_KERNEL+KERNEL_INTRONIX_3,[(255, u'Intronix display 3 channel', [(0, u'Tuner waveform (LS)'), (1, u'Tuner waveform (MS)'), (2, u'Ringdown ADC waveform (LS)'), (3, u'Ringdown ADC waveform (MS)'), (4, u'Ringdown simulator waveform (LS)'), (5, u'Ringdown simulator waveform (MS)'), (6, u'Laser fine current (LS)'), (7, u'Laser fine current (MS)'), (8, u'Locker error (LS)'), (9, u'Locker error (MS)'), (10, u'Ratio 1 (LS)'), (11, u'Ratio 1 (MS)'), (12, u'Ratio 2 (LS)'), (13, u'Ratio 2 (MS)'), (14, u'PZT (LS)'), (15, u'PZT (MS)'), (16, u'Etalon 1 ADC (LS)'), (17, u'Etalon 1 ADC (MS)'), (18, u'Reference 1 ADC (LS)'), (19, u'Reference 1 ADC (MS)'), (20, u'Etalon 2 ADC (LS)'), (21, u'Etalon 2 ADC (MS)'), (22, u'Reference 2 ADC (LS)'), (23, u'Reference 2 ADC (MS)'), (24, u'WLM ADC signals'), (25, u'System clocks'), (26, u'PWM signals'), (27, u'I2C signals')])],None,None,1,1))
parameter_forms.append(('System Parameters',__p))

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
__p.append(('fpga','uint16',FPGA_INJECT+INJECT_LASER1_FINE_CURRENT_RANGE,'Laser 1 fine current range (auto mode)','digU','%d',1,1))
__p.append(('dsp','float',LASER1_CURRENT_SWEEP_MIN_REGISTER,'Current Sweep Minimum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER1_CURRENT_SWEEP_MAX_REGISTER,'Current Sweep Maximum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER1_CURRENT_SWEEP_INCR_REGISTER,'Current Sweep Increment','digU/sample','%.1f',1,1))
__p.append(('dsp','float',LASER1_EXTRA_COARSE_SCALE_REGISTER,'Extra Current Mode Coarse Scale Factor (0 to 2)','','%.5f',1,1))
__p.append(('dsp','float',LASER1_EXTRA_FINE_SCALE_REGISTER,'Extra Current Mode Fine Scale Factor (0 to 1)','','%.5f',1,1))
__p.append(('dsp','int32',LASER1_EXTRA_OFFSET_REGISTER,'Extra Current Mode Offset','digU','%d',1,1))
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
__p.append(('fpga','uint16',FPGA_INJECT+INJECT_LASER2_FINE_CURRENT_RANGE,'Laser 2 fine current range (auto mode)','digU','%d',1,1))
__p.append(('dsp','float',LASER2_CURRENT_SWEEP_MIN_REGISTER,'Current Sweep Minimum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER2_CURRENT_SWEEP_MAX_REGISTER,'Current Sweep Maximum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER2_CURRENT_SWEEP_INCR_REGISTER,'Current Sweep Increment','digU/sample','%.1f',1,1))
__p.append(('dsp','float',LASER2_EXTRA_COARSE_SCALE_REGISTER,'Extra Current Mode Coarse Scale Factor (0 to 2)','','%.5f',1,1))
__p.append(('dsp','float',LASER2_EXTRA_FINE_SCALE_REGISTER,'Extra Current Mode Fine Scale Factor (0 to 1)','','%.5f',1,1))
__p.append(('dsp','int32',LASER2_EXTRA_OFFSET_REGISTER,'Extra Current Mode Offset','digU','%d',1,1))
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
__p.append(('fpga','uint16',FPGA_INJECT+INJECT_LASER3_FINE_CURRENT_RANGE,'Laser 3 fine current range (auto mode)','digU','%d',1,1))
__p.append(('dsp','choices',LASER3_CURRENT_CNTRL_STATE_REGISTER,'Current Controller Mode','',[(LASER_CURRENT_CNTRL_DisabledState,"Controller Disabled"),(LASER_CURRENT_CNTRL_AutomaticState,"Automatic Control"),(LASER_CURRENT_CNTRL_SweepingState,"Continuous Sweeping"),(LASER_CURRENT_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('dsp','float',LASER3_MANUAL_COARSE_CURRENT_REGISTER,'Manual Coarse Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER3_MANUAL_FINE_CURRENT_REGISTER,'Manual Fine Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER3_CURRENT_SWEEP_MIN_REGISTER,'Current Sweep Minimum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER3_CURRENT_SWEEP_MAX_REGISTER,'Current Sweep Maximum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER3_CURRENT_SWEEP_INCR_REGISTER,'Current Sweep Increment','digU/sample','%.1f',1,1))
__p.append(('dsp','float',LASER3_EXTRA_COARSE_SCALE_REGISTER,'Extra Current Mode Coarse Scale Factor (0 to 2)','','%.5f',1,1))
__p.append(('dsp','float',LASER3_EXTRA_FINE_SCALE_REGISTER,'Extra Current Mode Fine Scale Factor (0 to 1)','','%.5f',1,1))
__p.append(('dsp','int32',LASER3_EXTRA_OFFSET_REGISTER,'Extra Current Mode Offset','digU','%d',1,1))
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
__p.append(('fpga','uint16',FPGA_INJECT+INJECT_LASER4_FINE_CURRENT_RANGE,'Laser 4 fine current range (auto mode)','digU','%d',1,1))
__p.append(('dsp','choices',LASER4_CURRENT_CNTRL_STATE_REGISTER,'Current Controller Mode','',[(LASER_CURRENT_CNTRL_DisabledState,"Controller Disabled"),(LASER_CURRENT_CNTRL_AutomaticState,"Automatic Control"),(LASER_CURRENT_CNTRL_SweepingState,"Continuous Sweeping"),(LASER_CURRENT_CNTRL_ManualState,"Manual Control"),],1,1))
__p.append(('dsp','float',LASER4_MANUAL_COARSE_CURRENT_REGISTER,'Manual Coarse Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER4_MANUAL_FINE_CURRENT_REGISTER,'Manual Fine Current Setpoint','digU','%.0f',1,1))
__p.append(('dsp','float',LASER4_CURRENT_SWEEP_MIN_REGISTER,'Current Sweep Minimum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER4_CURRENT_SWEEP_MAX_REGISTER,'Current Sweep Maximum','digU','%.0f',1,1))
__p.append(('dsp','float',LASER4_CURRENT_SWEEP_INCR_REGISTER,'Current Sweep Increment','digU/sample','%.1f',1,1))
__p.append(('dsp','float',LASER4_EXTRA_COARSE_SCALE_REGISTER,'Extra Current Mode Coarse Scale Factor (0 to 2)','','%.5f',1,1))
__p.append(('dsp','float',LASER4_EXTRA_FINE_SCALE_REGISTER,'Extra Current Mode Fine Scale Factor (0 to 1)','','%.5f',1,1))
__p.append(('dsp','int32',LASER4_EXTRA_OFFSET_REGISTER,'Extra Current Mode Offset','digU','%d',1,1))
parameter_forms.append(('Laser 4 Parameters',__p))

# Form: Warm Box Temperature Parameters

__p = []

__p.append(('dsp','choices',WARM_BOX_TEMP_CNTRL_STATE_REGISTER,'Temperature Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),(TEMP_CNTRL_AutomaticState,"Automatic Control"),],1,1))
__p.append(('dsp','choices',TEC_CNTRL_REGISTER,'Warm and hot box TEC','',[(TEC_CNTRL_Disabled,"Disabled"),(TEC_CNTRL_Enabled,"Enabled"),],1,1))
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
__p.append(('dsp','choices',TEC_CNTRL_REGISTER,'Warm and hot box TEC','',[(TEC_CNTRL_Disabled,"Disabled"),(TEC_CNTRL_Enabled,"Enabled"),],1,1))
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
parameter_forms.append(('Cavity Temperature Parameters',__p))

# Form: Heater Controller Parameters

__p = []

__p.append(('dsp','choices',HEATER_TEMP_CNTRL_STATE_REGISTER,'Heater Controller Mode','',[(TEMP_CNTRL_DisabledState,"Controller Disabled"),(TEMP_CNTRL_EnabledState,"Controller Enabled"),(TEMP_CNTRL_SuspendedState,"Controller Suspended"),(TEMP_CNTRL_SweepingState,"Continuous Sweeping"),(TEMP_CNTRL_SendPrbsState,"Sending PRBS"),(TEMP_CNTRL_ManualState,"Manual Control"),(TEMP_CNTRL_AutomaticState,"Automatic Control"),],1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER,'Target temperature difference between heatsink and cavity','degC','%.3f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_TOLERANCE_REGISTER,'Lock tolerance','degC','%.3f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER,'Max sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER,'Min sweep value','degC','%.3f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER,'Sweep increment','degC/sample','%.3f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_H_REGISTER,'Sample interval','s','%.3f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_K_REGISTER,'Loop proportional gain (K)','','%.2f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_TI_REGISTER,'Integration time (Ti)','s','%.2f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_TD_REGISTER,'Derivative time (Td)','s','%.2f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_B_REGISTER,'Proportional setpoint gain (b)','','%.3f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_C_REGISTER,'Derivative setpoint gain (c)','','%.3f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_N_REGISTER,'Derivative regularization (N)','','%.2f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_S_REGISTER,'Saturation regularization (S)','','%.2f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_AMIN_REGISTER,'Minimum mark value (Amin)','','%.0f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_AMAX_REGISTER,'Maximum mark value (Amax)','','%.0f',1,1))
__p.append(('dsp','float',HEATER_TEMP_CNTRL_IMAX_REGISTER,'Maximum actuator increment (Imax)','','%.1f',1,1))
__p.append(('dsp','uint32',HEATER_PRBS_GENPOLY_REGISTER,'PRBS generator','','$%X',1,1))
__p.append(('dsp','float',HEATER_PRBS_AMPLITUDE_REGISTER,'PRBS amplitude','','%.1f',1,1))
__p.append(('dsp','float',HEATER_PRBS_MEAN_REGISTER,'PRBS mean','','%.1f',1,1))
__p.append(('dsp','float',HEATER_MANUAL_MARK_REGISTER,'Heater manual mode mark','','%.0f',1,1))
__p.append(('dsp','float',HEATER_CUTOFF_REGISTER,'Cavity temperature above which to turn off heater','degC','%.3f',1,1))
parameter_forms.append(('Heater Controller Parameters',__p))

# Form: Fan Controller Parameters

__p = []

__p.append(('dsp','float',FAN_CNTRL_TEMPERATURE_REGISTER,'Temperature above which fans operate','degC','%.1f',1,1))
__p.append(('dsp','choices',FAN_CNTRL_STATE_REGISTER,'Fan State','',[(FAN_CNTRL_OffState,"Fans off"),(FAN_CNTRL_OnState,"Fans on"),],1,1))
parameter_forms.append(('Fan Controller Parameters',__p))

# Form: Sample Handling Parameters

__p = []

__p.append(('dsp','choices',VALVE_CNTRL_STATE_REGISTER,'Valve Controller Mode','',[(VALVE_CNTRL_DisabledState,"Disabled"),(VALVE_CNTRL_OutletControlState,"Outlet control"),(VALVE_CNTRL_InletControlState,"Inlet control"),(VALVE_CNTRL_ManualControlState,"Manual control"),(VALVE_CNTRL_SaveAndCloseValvesState,"Save valve settings and close valves"),(VALVE_CNTRL_RestoreValvesState,"Restore valve settings and saved state"),(VALVE_CNTRL_OutletOnlyControlState,"Outlet only (no inlet valve) control, normal operation"),(VALVE_CNTRL_OutletOnlyRecoveryState,"Outlet only (no inlet valve) control, pump disconnected"),],1,1))
__p.append(('dsp','uint32',VALVE_CNTRL_SOLENOID_VALVES_REGISTER,'Solenoid valve states','','$%X',1,1))
__p.append(('dsp','float',VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER,'Cavity pressure setpoint','torr','%.2f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_USER_INLET_VALVE_REGISTER,'Inlet valve value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER,'Outlet valve value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER,'Rate of cavity pressure change to disable controller','torr/s','%.3f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER,'Cavity pressure maximum rate of change','torr/s','%.3f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER,'Inlet valve gain 1','','%.2f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER,'Inlet valve gain 2','','%.2f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_MIN_REGISTER,'Inlet valve minimum value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_MAX_REGISTER,'Inlet valve maximum value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER,'Inlet valve maximum change between samples','digU','%.1f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER,'Inlet valve dither (p-p)','digU','%.1f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER,'Outlet valve gain 1','','%.2f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER,'Outlet valve gain 2','','%.2f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER,'Outlet valve minimum value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER,'Outlet valve maximum value','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER,'Outlet valve maximum change between samples','digU','%.1f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER,'Outlet valve dither (p-p)','digU','%.1f',1,1))
__p.append(('dsp','choices',VALVE_CNTRL_THRESHOLD_STATE_REGISTER,'Loss-based Triggering','',[(VALVE_CNTRL_THRESHOLD_DisabledState,"Disabled"),(VALVE_CNTRL_THRESHOLD_ArmedState,"Armed"),(VALVE_CNTRL_THRESHOLD_TriggeredState,"Triggered"),],1,1))
__p.append(('dsp','float',VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER,'Loss threshold for trigger','ppb/cm','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER,'Rate of change of loss for trigger','ppb/cm/s','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER,'Inlet valve when triggered','digU','%.0f',1,1))
__p.append(('dsp','float',VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER,'Outlet valve when triggered','digU','%.0f',1,1))
__p.append(('dsp','uint32',VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER,'Bit mask to select solenoid valves affected by trigger','','$%X',1,1))
__p.append(('dsp','uint32',VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER,'Solenoid valve states when triggered','','$%X',1,1))
__p.append(('dsp','int32',VALVE_CNTRL_SEQUENCE_STEP_REGISTER,'Valve sequence step (-1 to disable)','','%d',1,1))
__p.append(('dsp','choices',FLOW_CNTRL_STATE_REGISTER,'Flow Controller Mode','',[(FLOW_CNTRL_DisabledState,"Disabled"),(FLOW_CNTRL_EnabledState,"Enabled"),],1,1))
__p.append(('dsp','float',FLOW_CNTRL_SETPOINT_REGISTER,'Flow setpoint','sccm','%.1f',1,1))
__p.append(('dsp','float',FLOW_CNTRL_GAIN_REGISTER,'Flow control gain','','%.1f',1,1))
parameter_forms.append(('Sample Handling Parameters',__p))

# Form: Virtual Laser Parameters

__p = []

__p.append(('dsp','float',PZT_INCR_PER_CAVITY_FSR,'PZT increment per cavity FSR','','%.0f',1,1))
__p.append(('dsp','float',PZT_OFFSET_UPDATE_FACTOR,'PZT offset update factor','','%.3f',1,1))
__p.append(('dsp','float',PZT_OFFSET_VIRTUAL_LASER1,'Virtual laser 1 PZT offset','','%.0f',1,1))
__p.append(('dsp','float',PZT_OFFSET_VIRTUAL_LASER2,'Virtual laser 2 PZT offset','','%.0f',1,1))
__p.append(('dsp','float',PZT_OFFSET_VIRTUAL_LASER3,'Virtual laser 3 PZT offset','','%.0f',1,1))
__p.append(('dsp','float',PZT_OFFSET_VIRTUAL_LASER4,'Virtual laser 4 PZT offset','','%.0f',1,1))
__p.append(('dsp','float',PZT_OFFSET_VIRTUAL_LASER5,'Virtual laser 5 PZT offset','','%.0f',1,1))
__p.append(('dsp','float',PZT_OFFSET_VIRTUAL_LASER6,'Virtual laser 6 PZT offset','','%.0f',1,1))
__p.append(('dsp','float',PZT_OFFSET_VIRTUAL_LASER7,'Virtual laser 7 PZT offset','','%.0f',1,1))
__p.append(('dsp','float',PZT_OFFSET_VIRTUAL_LASER8,'Virtual laser 8 PZT offset','','%.0f',1,1))
__p.append(('dsp','float',SCHEME_OFFSET_VIRTUAL_LASER1,'Virtual laser 1 scheme temperature offset','','%.3f',1,1))
__p.append(('dsp','float',SCHEME_OFFSET_VIRTUAL_LASER2,'Virtual laser 2 scheme temperature offset','','%.3f',1,1))
__p.append(('dsp','float',SCHEME_OFFSET_VIRTUAL_LASER3,'Virtual laser 3 scheme temperature offset','','%.3f',1,1))
__p.append(('dsp','float',SCHEME_OFFSET_VIRTUAL_LASER4,'Virtual laser 4 scheme temperature offset','','%.3f',1,1))
__p.append(('dsp','float',SCHEME_OFFSET_VIRTUAL_LASER5,'Virtual laser 5 scheme temperature offset','','%.3f',1,1))
__p.append(('dsp','float',SCHEME_OFFSET_VIRTUAL_LASER6,'Virtual laser 6 scheme temperature offset','','%.3f',1,1))
__p.append(('dsp','float',SCHEME_OFFSET_VIRTUAL_LASER7,'Virtual laser 7 scheme temperature offset','','%.3f',1,1))
__p.append(('dsp','float',SCHEME_OFFSET_VIRTUAL_LASER8,'Virtual laser 8 scheme temperature offset','','%.3f',1,1))
parameter_forms.append(('Virtual Laser Parameters',__p))

# Form: Loss Buffer Parameters

__p = []

__p.append(('dsp','float',LOSS_BUFFER_0_REGISTER,'Loss Buffer 0','','%.4f',1,0))
__p.append(('dsp','float',LOSS_BUFFER_1_REGISTER,'Loss Buffer 1','','%.4f',1,0))
__p.append(('dsp','float',LOSS_BUFFER_2_REGISTER,'Loss Buffer 2','','%.4f',1,0))
__p.append(('dsp','float',LOSS_BUFFER_3_REGISTER,'Loss Buffer 3','','%.4f',1,0))
__p.append(('dsp','float',LOSS_BUFFER_4_REGISTER,'Loss Buffer 4','','%.4f',1,0))
__p.append(('dsp','float',LOSS_BUFFER_5_REGISTER,'Loss Buffer 5','','%.4f',1,0))
__p.append(('dsp','float',LOSS_BUFFER_6_REGISTER,'Loss Buffer 6','','%.4f',1,0))
__p.append(('dsp','float',LOSS_BUFFER_7_REGISTER,'Loss Buffer 7','','%.4f',1,0))
__p.append(('dsp','float',PROCESSED_LOSS_1_REGISTER,'Processed loss 1','','%.4f',1,0))
__p.append(('dsp','float',PROCESSED_LOSS_2_REGISTER,'Processed loss 2','','%.4f',1,0))
__p.append(('dsp','float',PROCESSED_LOSS_3_REGISTER,'Processed loss 3','','%.4f',1,0))
__p.append(('dsp','float',PROCESSED_LOSS_4_REGISTER,'Processed loss 4','','%.4f',1,0))
parameter_forms.append(('Loss Buffer Parameters',__p))

# Form: Peak Detector Parameters

__p = []

__p.append(('dsp','choices',PEAK_DETECT_CNTRL_STATE_REGISTER,'Peak Detection Controller Mode','',[(PEAK_DETECT_CNTRL_IdleState,"Idle"),(PEAK_DETECT_CNTRL_ArmedState,"Armed"),(PEAK_DETECT_CNTRL_TriggerPendingState,"Trigger Pending"),(PEAK_DETECT_CNTRL_TriggeredState,"Triggered"),(PEAK_DETECT_CNTRL_InactiveState,"Inactive"),(PEAK_DETECT_CNTRL_CancellingState,"Cancelling"),(PEAK_DETECT_CNTRL_PrimingState,"Priming"),(PEAK_DETECT_CNTRL_PurgingState,"Purging"),(PEAK_DETECT_CNTRL_InjectionPendingState,"Injection Pending"),(PEAK_DETECT_CNTRL_TransitioningState,"Transitioning"),(PEAK_DETECT_CNTRL_HoldingState,"Holding"),],1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_BACKGROUND_SAMPLES_REGISTER,'Number of samples for calculating background','samples','%d',1,1))
__p.append(('dsp','float',PEAK_DETECT_CNTRL_BACKGROUND_REGISTER,'Background loss','ppm/cm','%.3f',1,1))
__p.append(('dsp','float',PEAK_DETECT_CNTRL_UPPER_THRESHOLD_REGISTER,'Upper threshold (relative to background)','ppm/cm','%.3f',1,1))
__p.append(('dsp','float',PEAK_DETECT_CNTRL_LOWER_THRESHOLD_1_REGISTER,'Lower Threshold 1 (relative to background)','ppm/cm','%.3f',1,1))
__p.append(('dsp','float',PEAK_DETECT_CNTRL_LOWER_THRESHOLD_2_REGISTER,'Lower Threshold 2 (relative to background)','ppm/cm','%.3f',1,1))
__p.append(('dsp','float',PEAK_DETECT_CNTRL_THRESHOLD_FACTOR_REGISTER,'Threshold factor to apply to peak','','%.3f',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_ACTIVE_SIZE_REGISTER,'Active buffer length','samples','%d',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_POST_PEAK_SAMPLES_REGISTER,'Samples after peak','samples','%d',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_TRIGGER_CONDITION_REGISTER,'Condition for triggering','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_TRIGGER_DELAY_REGISTER,'Trigger delay (after trigger condition met)','samples','%d',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_TRIGGERED_DURATION_REGISTER,'Triggered duration (in samples)','samples','%d',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_TRANSITIONING_DURATION_REGISTER,'Transitioning duration (in samples)','samples','%d',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_TRANSITIONING_HOLDOFF_REGISTER,'Transitioning holdoff duration (in samples)','samples','%d',1,1))
__p.append(('dsp','float',PEAK_DETECT_CNTRL_HOLDING_MAX_LOSS_REGISTER,'Maximum loss during holding state','ppm/cm','%.3f',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_HOLDING_DURATION_REGISTER,'Holding duration (in samples)','samples','%d',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_CANCELLING_SAMPLES_REGISTER,'Samples in cancelling state','samples','%d',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_PRIMING_DURATION_REGISTER,'Priming duration','samples','%d',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_PURGING_DURATION_REGISTER,'Purging duration','samples','%d',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_IDLE_VALVE_MASK_AND_VALUE_REGISTER,'Idle state valve mask and values','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_ARMED_VALVE_MASK_AND_VALUE_REGISTER,'Armed state valve mask and values','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_TRIGGER_PENDING_VALVE_MASK_AND_VALUE_REGISTER,'Trigger pending state valve mask and values','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_TRIGGERED_VALVE_MASK_AND_VALUE_REGISTER,'Triggered state valve mask and values','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_TRANSITIONING_VALVE_MASK_AND_VALUE_REGISTER,'Transitioning state valve mask and values','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_HOLDING_VALVE_MASK_AND_VALUE_REGISTER,'Holding state valve mask and values','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_INACTIVE_VALVE_MASK_AND_VALUE_REGISTER,'Inactive state valve mask and values','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_CANCELLING_VALVE_MASK_AND_VALUE_REGISTER,'Cancelling state valve mask and values','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_PRIMING_VALVE_MASK_AND_VALUE_REGISTER,'Priming state valve mask and values','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_PURGING_VALVE_MASK_AND_VALUE_REGISTER,'Purging state valve mask and values','','$%04X',1,1))
__p.append(('dsp','uint32',PEAK_DETECT_CNTRL_INJECTION_PENDING_VALVE_MASK_AND_VALUE_REGISTER,'Injection pending state valve mask and values','','$%04X',1,1))
__p.append(('dsp','float',FLOW_0_SETPOINT_REGISTER,'Flow setpoint in state 0','sccm','%.1f',1,1))
__p.append(('dsp','float',FLOW_1_SETPOINT_REGISTER,'Flow setpoint in state 1','sccm','%.1f',1,1))
__p.append(('dsp','float',FLOW_2_SETPOINT_REGISTER,'Flow setpoint in state 2','sccm','%.1f',1,1))
__p.append(('dsp','float',FLOW_3_SETPOINT_REGISTER,'Flow setpoint in state 3','sccm','%.1f',1,1))
parameter_forms.append(('Peak Detector Parameters',__p))

# Form: Tuner Parameters

__p = []

__p.append(('dsp','choices',ANALYZER_TUNING_MODE_REGISTER,'Analyzer tuning mode','',[(ANALYZER_TUNING_CavityLengthTuningMode,"Cavity Length Tuning"),(ANALYZER_TUNING_LaserCurrentTuningMode,"Laser Current Tuning"),(ANALYZER_TUNING_FsrHoppingTuningMode,"Fsr Hopping Tuning"),],1,1))
__p.append(('fpga','mask',FPGA_TWGEN+TWGEN_CS,[(1, u'Stop/Run', [(0, u'Stop'), (1, u'Run')]), (2, u'Single/Continuous', [(0, u'Single'), (2, u'Continuous')]), (4, u'Reset generator', [(0, u'Idle'), (4, u'Reset')]), (8, u'Tune PZT', [(0, u'No'), (8, u'Yes')])],None,None,1,1))
__p.append(('fpga','uint16',FPGA_TWGEN+TWGEN_SLOPE_UP,'Tuner up slope','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_TWGEN+TWGEN_SLOPE_DOWN,'Tuner down slope','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_TWGEN+TWGEN_PZT_OFFSET,'Offset to add to PZT output','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_SCALER+SCALER_SCALE1,'Scale factor for PZT waveform','digU','%d',1,1))
__p.append(('dsp','float',TUNER_SWEEP_RAMP_HIGH_REGISTER,'Ramp mode upper sweep limit','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_SWEEP_RAMP_LOW_REGISTER,'Ramp mode lower sweep limit','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_WINDOW_RAMP_HIGH_REGISTER,'Ramp mode upper window limit','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_WINDOW_RAMP_LOW_REGISTER,'Ramp mode lower window limit','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER,'Dither mode upper sweep offset','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER,'Dither mode lower sweep offset','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER,'Dither mode upper window offset','digU','%.0f',1,1))
__p.append(('dsp','float',TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER,'Dither mode lower window offset','digU','%.0f',1,1))
__p.append(('dsp','choices',TUNER_DITHER_MEDIAN_COUNT_REGISTER,'Number of ringdowns to use for centering dither','',[(TUNER_DITHER_MEDIAN_1,"1"),(TUNER_DITHER_MEDIAN_3,"3"),(TUNER_DITHER_MEDIAN_5,"5"),(TUNER_DITHER_MEDIAN_7,"7"),(TUNER_DITHER_MEDIAN_9,"9"),],1,1))
parameter_forms.append(('Tuner Parameters',__p))

# Form: Optical Injection Parameters

__p = []

__p.append(('dsp','choices',VIRTUAL_LASER_REGISTER,'Virtual laser','',[(VIRTUAL_LASER_1,"Virtual laser 1"),(VIRTUAL_LASER_2,"Virtual laser 2"),(VIRTUAL_LASER_3,"Virtual laser 3"),(VIRTUAL_LASER_4,"Virtual laser 4"),(VIRTUAL_LASER_5,"Virtual laser 5"),(VIRTUAL_LASER_6,"Virtual laser 6"),(VIRTUAL_LASER_7,"Virtual laser 7"),(VIRTUAL_LASER_8,"Virtual laser 8"),],1,1))
__p.append(('fpga','mask',FPGA_INJECT+INJECT_CONTROL,[(1, u'Manual/Automatic mode', [(0, u'Manual'), (1, u'Automatic')]), (6, u'Laser selected', [(0, u'Laser 1'), (2, u'Laser 2'), (4, u'Laser 3'), (6, u'Laser 4')]), (120, u'Laser current enable', []), (8, u'Laser 1 current source', []), (16, u'Laser 2 current source', []), (32, u'Laser 3 current source', []), (64, u'Laser 4 current source', []), (1920, u'Deasserts short across laser in manual mode', []), (128, u'Laser 1 current (in manual mode)', []), (256, u'Laser 2 current (in manual mode)', []), (512, u'Laser 3 current (in manual mode)', []), (1024, u'Laser 4 current (in manual mode)', []), (2048, u'Enable SOA current (in manual mode)', [(0, u'Off'), (2048, u'On')]), (4096, u'Enables laser shutdown (in automatic mode)', [(0, u'Disabled'), (4096, u'Enabled')]), (8192, u'Enables SOA shutdown (in automatic mode)', [(0, u'Disabled'), (8192, u'Enabled')]), (16384, u'Select optical switch type', [(0, u'2-way'), (16384, u'4-way')]), (32768, u'SOA or fiber amplifier present', [(0, u'No'), (32768, u'Yes')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_INJECT+INJECT_CONTROL2,[(1, u'Fiber amplifier present', [(0, u'No'), (1, u'Yes')]), (2, u'Turn off deselected lasers', [(0, u'No'), (2, u'Yes')]), (4, u'How is extra laser current controlled?', [(0, u'Input port'), (4, u'Bit in register')]), (8, u'Bit for controlling extra laser current', [(0, u'Normal current'), (8, u'Extra current')]), (16, u'Use extended laser current control', [(0, u'Disable'), (16, u'Enable')]), (480, u'Disable SOA for some lasers', []), (32, u'Disable SOA for laser 1', [(0, u'No'), (32, u'Yes')]), (64, u'Disable SOA for laser 2', [(0, u'No'), (64, u'Yes')]), (128, u'Disable SOA for laser 3', [(0, u'No'), (128, u'Yes')]), (256, u'Disable SOA for laser 4', [(0, u'No'), (256, u'Yes')])],None,None,1,1))
parameter_forms.append(('Optical Injection Parameters',__p))

# Form: Spectrum Controller Parameters

__p = []

__p.append(('dsp','choices',SPECT_CNTRL_STATE_REGISTER,'Spectrum Controller State','',[(SPECT_CNTRL_IdleState,"Not acquiring"),(SPECT_CNTRL_StartingState,"Start acquisition"),(SPECT_CNTRL_StartManualState,"Start acquisition with manual temperature control"),(SPECT_CNTRL_RunningState,"Acquisition in progress"),(SPECT_CNTRL_PausedState,"Acquisition paused"),(SPECT_CNTRL_ErrorState,"Error state"),(SPECT_CNTRL_DiagnosticState,"Diagnostic state"),],1,1))
__p.append(('dsp','choices',SPECT_CNTRL_MODE_REGISTER,'Spectrum Controller Mode','',[(SPECT_CNTRL_SchemeSingleMode,"Perform single scheme"),(SPECT_CNTRL_SchemeMultipleMode,"Perform multiple schemes"),(SPECT_CNTRL_SchemeMultipleNoRepeatMode,"Multiple schemes no repeats"),(SPECT_CNTRL_ContinuousMode,"Continuous acquisition"),(SPECT_CNTRL_ContinuousManualTempMode,"Continuous acquisition with manual temperature control"),],1,1))
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
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_PZT_CENTER,'PZT value (mod 16384) around which cavity fills','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_PZT_WINDOW_HALF_WIDTH,'Half-width of PZT window within which cavity fills','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_FILLING_RATE,'Rate of increase of accumulator value during filling','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_DECAY,'Exponential decay of accumulator when not filling','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_DECAY_IN_SHIFT,'Bits to  right shift decay input','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDSIM+RDSIM_DECAY_IN_OFFSET,'Offset to add to shifted decay input','','%d',1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_WFAC,'Width factor of simulated spectrum','','%d',1,1))
parameter_forms.append(('Ringdown Simulator Parameters',__p))

# Form: Ringdown Manager Parameters

__p = []

__p.append(('dsp','uint32',RDD_BALANCE_REGISTER,'Ringdown detector balance','','%d',1,1))
__p.append(('dsp','uint32',RDD_GAIN_REGISTER,'Ringdown detector gain','','%d',1,1))
__p.append(('fpga','mask',FPGA_RDMAN+RDMAN_CONTROL,[(1, u'Stop/Run', [(0, u'Stop'), (1, u'Run')]), (2, u'Single/Continuous', [(0, u'Single'), (2, u'Continuous')]), (4, u'Start ringdown cycle', [(0, u'Idle'), (4, u'Start')]), (8, u'Abort ringdown', [(0, u'Idle'), (8, u'Abort')]), (16, u'Reset ringdown manager', [(0, u'Idle'), (16, u'Reset')]), (32, u'Mark bank 0 available for write', [(0, u'Idle'), (32, u'Mark available')]), (64, u'Mark bank 1 available for write', [(0, u'Idle'), (64, u'Mark available')]), (128, u'Acknowledge ring-down interrupt', [(0, u'Idle'), (128, u'Acknowledge')]), (256, u'Acknowledge data acquired interrupt', [(0, u'Idle'), (256, u'Acknowledge')]), (512, u'Tuner waveform mode', [(0, u'Ramp'), (512, u'Dither')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_RDMAN+RDMAN_OPTIONS,[(1, u'Enable frequency locking', [(0, u'Disable'), (1, u'Enable')]), (2, u'Allow ring-down on positive tuner slope', [(0, u'No'), (2, u'Yes')]), (4, u'Allow ring-down on negative tuner slope', [(0, u'No'), (4, u'Yes')]), (8, u'Allow transition to dither mode', [(0, u'Disallow'), (8, u'Allow')]), (16, u'Ringdown data source', [(0, u'Simulator'), (16, u'Actual ADC')]), (32, u'Oscilloscope mode', [(0, u'Disabled'), (32, u'Enabled')]), (64, u'Tuner slope to trigger scope', [(0, u'Falling'), (64, u'Rising')])],None,None,1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_DIVISOR,'Ringdown ADC divisor, Sample freq = 25MHz/(divisor+1)','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_NUM_SAMP,'Ringdown samples to collect','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_THRESHOLD,'Ringdown threshold','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_LOCK_DURATION,'Laser lock duration (us)','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_PRECONTROL_DURATION,'Precontrol duration (us)','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_OFF_DURATION,'Ringdown duration (us)','','%d',1,1))
__p.append(('fpga','uint16',FPGA_RDMAN+RDMAN_EXTRA_DURATION,'Extra laser current duration (us)','','%d',1,1))
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
__p.append(('dsp','uint32',RDFITTER_META_BACKOFF_REGISTER,'Last sample backoff for metadata calculation','','%d',1,1))
__p.append(('dsp','uint32',RDFITTER_META_SAMPLES_REGISTER,'Samples to use for metadata calculation','','%d',1,1))
parameter_forms.append(('Ringdown Data Fitting Parameters',__p))

# Form: Wavelength Monitor Simulator Parameters

__p = []

__p.append(('fpga','mask',FPGA_WLMSIM+WLMSIM_OPTIONS,[(1, u'Input select', [(0, u'Register'), (1, u'Input port')])],None,None,1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_RFAC,'Reflectivity factor','','%d',1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_Z0,'Phase angle','','%d',1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_ETA1_OFFSET,'Etalon 1 offset','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_REF1_OFFSET,'Reference 1 offset','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_ETA2_OFFSET,'Etalon 2 offset','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_WLMSIM+WLMSIM_REF2_OFFSET,'Reference 2 offset','digU','%d',1,1))
parameter_forms.append(('Wavelength Monitor Simulator Parameters',__p))

# Form: Laser Locker Parameters

__p = []

__p.append(('fpga','mask',FPGA_LASERLOCKER+LASERLOCKER_CS,[(1, u'Stop/Run', [(0, u'Stop'), (1, u'Run')]), (2, u'Single/Continuous', [(0, u'Single'), (2, u'Continuous')]), (4, u'Generate PRBS', [(0, u'Idle'), (4, u'Send PRBS')]), (8, u'Enable fine current acc', [(0, u'Reset'), (8, u'Accumulate')]), (16, u'Sample dark currents', [(0, u'Idle'), (16, u'Sample')]), (32, u'Load WLM ADC values', [(0, u'Idle'), (32, u'Load')]), (64, u'Tuner offset source', [(0, u'Register'), (64, u'Input port')]), (128, u'Laser frequency in window', [(0, u'Out of range'), (128, u'In Window')]), (256, u'Fine current calculation', [(0, u'In progress'), (256, u'Complete')])],None,None,1,1))
__p.append(('fpga','mask',FPGA_LASERLOCKER+LASERLOCKER_OPTIONS,[(1, u'Wavelength Monitor Data Source', [(0, u'Simulator'), (1, u'Actual WLM')]), (2, u'Route tuner input to fine current output', [(0, u'No'), (2, u'Yes')])],None,None,1,1))
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

# Form: Inlet Dynamic Pwm Parameters

__p = []

__p.append(('fpga','mask',FPGA_DYNAMICPWM_INLET+DYNAMICPWM_CS,[(1, u'Stop/Run', [(0, u'Stop'), (1, u'Run')]), (2, u'Single/Continuous', [(0, u'Single'), (2, u'Continuous')]), (4, u'PWM enable', [(0, u'Disable'), (4, u'Enable')]), (8, u'Use comparator', [(0, u'No'), (8, u'Yes')]), (16, u'PWM output', [(0, u'Low'), (16, u'High')]), (32, u'Invert polarity of PWM signal', [(0, u'Normal'), (32, u'Inverted')])],None,None,1,1))
__p.append(('fpga','int16',FPGA_DYNAMICPWM_INLET+DYNAMICPWM_DELTA,'Pulse width change per update','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_DYNAMICPWM_INLET+DYNAMICPWM_HIGH,'Upper limit of dither waveform','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_DYNAMICPWM_INLET+DYNAMICPWM_LOW,'Lower limit of dither waveform','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_DYNAMICPWM_INLET+DYNAMICPWM_SLOPE,'Slope of dither waveform','','%d',1,1))
parameter_forms.append(('Inlet Dynamic Pwm Parameters',__p))

# Form: Outlet Dynamic Pwm Parameters

__p = []

__p.append(('fpga','mask',FPGA_DYNAMICPWM_OUTLET+DYNAMICPWM_CS,[(1, u'Stop/Run', [(0, u'Stop'), (1, u'Run')]), (2, u'Single/Continuous', [(0, u'Single'), (2, u'Continuous')]), (4, u'PWM enable', [(0, u'Disable'), (4, u'Enable')]), (8, u'Use comparator', [(0, u'No'), (8, u'Yes')]), (16, u'PWM output', [(0, u'Low'), (16, u'High')]), (32, u'Invert polarity of PWM signal', [(0, u'Normal'), (32, u'Inverted')])],None,None,1,1))
__p.append(('fpga','int16',FPGA_DYNAMICPWM_OUTLET+DYNAMICPWM_DELTA,'Pulse width change per update','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_DYNAMICPWM_OUTLET+DYNAMICPWM_HIGH,'Upper limit of dither waveform','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_DYNAMICPWM_OUTLET+DYNAMICPWM_LOW,'Lower limit of dither waveform','digU','%d',1,1))
__p.append(('fpga','uint16',FPGA_DYNAMICPWM_OUTLET+DYNAMICPWM_SLOPE,'Slope of dither waveform','','%d',1,1))
parameter_forms.append(('Outlet Dynamic Pwm Parameters',__p))

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
