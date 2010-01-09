/*
 * FILE:
 *   interface.h
 *
 * DESCRIPTION:
 *   Automatically generated interface H file for Picarro gas analyzer. 
 *    DO NOT EDIT.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */
#ifndef _INTERFACE_H
#define _INTERFACE_H

typedef unsigned int uint32;
typedef int int32;
typedef unsigned short uint16;
typedef short int16;
typedef unsigned char uint8;
typedef char int8;
typedef int bool;

#ifndef FALSE
    #define FALSE (0)
#endif
#ifndef TRUE
    #define TRUE  (1)
#endif



/* Interface Version */
#define interface_version (1)

#define STATUS_OK (0)
#define ERROR_UNAVAILABLE (-1)
#define ERROR_CRC_BAD (-2)
#define ERROR_DSP_UNEXPECTED_SEQUENCE_NUMBER (-3)
#define ERROR_HOST_UNEXPECTED_SEQUENCE_NUMBER (-4)
#define ERROR_BAD_COMMAND (-5)
#define ERROR_BAD_NUM_PARAMS (-6)
#define ERROR_OUTSIDE_SHAREDMEM (-7)
#define ERROR_UNKNOWN_REGISTER (-8)
#define ERROR_NOT_READABLE (-9)
#define ERROR_NOT_WRITABLE (-10)
#define ERROR_READ_FAILED (-11)
#define ERROR_WRITE_FAILED (-12)
#define ERROR_BAD_FILTER_COEFF (-13)
#define ERROR_BAD_VALUE (-14)
#define ERROR_RD_BAD_RINGDOWN (-15)
#define ERROR_RD_INSUFFICIENT_DATA (-16)

typedef union {
    float asFloat;
    uint32 asUint;
    int32 asInt;
} DataType;

typedef struct {
    uint32 time;
    uint32 cause;
    uint32 etalonPd1Current;
    uint32 refPd1Current;
    uint32 etalonPd2Current;
    uint32 refPd2Current;
    uint32 etalonTemp;
    uint32 cavityTemp;
    uint32 warmBoxTemp;
    uint32 hotBoxTecHeatsinkTemp;
    uint32 warmBoxTecHeatsinkTemp;
    uint32 laser1Temp;
    uint32 laser2Temp;
    uint32 laserCurrent;
    uint32 cavityPressure;
    uint32 inletPressure;
    uint32 outletPressure;
    uint16 customDataArray[16];
} DIAG_EventLogStruct;

typedef struct {
    uint32 ratio1;
    uint32 ratio2;
    uint32 pztValue;
    uint32 lockerOffset;
    uint32 fineLaserCurrent;
    int32 lockerError;
} RingdownMetadataType;

typedef struct {
    double ratio1;
    double ratio2;
    double pztValue;
    double lockerOffset;
    double fineLaserCurrent;
    double lockerError;
} RingdownMetadataDoubleType;

typedef struct {
    uint32 injectionSettings;
    float laserTemperature;
    uint32 coarseLaserCurrent;
    float etalonTemperature;
    float cavityPressure;
    float ambientPressure;
    uint32 schemeTableAndRow;
    uint32 countAndSubschemeId;
    uint32 ringdownThreshold;
    uint32 status;
    uint32 tunerAtRingdown;
    uint32 addressAtRingdown;
} RingdownParamsType;

typedef struct {
    uint32 ringdownWaveform[4096];
    RingdownParamsType parameters;
} RingdownBufferType;

typedef struct {
    long long timestamp;
    float wlmAngle;
    float uncorrectedAbsorbance;
    float correctedAbsorbance;
    uint16 status;
    uint16 count;
    uint16 tunerValue;
    uint16 pztValue;
    uint16 lockerOffset;
    uint16 laserUsed;
    uint16 ringdownThreshold;
    uint16 subschemeId;
    uint16 schemeTable;
    uint16 schemeRow;
    uint16 ratio1;
    uint16 ratio2;
    uint16 fineLaserCurrent;
    uint16 coarseLaserCurrent;
    float laserTemperature;
    float etalonTemperature;
    uint16 cavityPressure;
    uint16 ambientPressure;
    int16 lockerError;
    uint16 padToCacheLine;
} RingdownEntryType;

typedef struct {
    long long timestamp;
    double waveNumber;
    double waveNumberSetpoint;
    float uncorrectedAbsorbance;
    float correctedAbsorbance;
    uint16 status;
    uint16 count;
    uint16 tunerValue;
    uint16 pztValue;
    uint16 lockerOffset;
    uint16 laserUsed;
    uint16 ringdownThreshold;
    uint16 subschemeId;
    uint16 schemeTable;
    uint16 schemeRow;
    uint16 ratio1;
    uint16 ratio2;
    uint16 fineLaserCurrent;
    uint16 coarseLaserCurrent;
    float laserTemperature;
    float etalonTemperature;
    uint16 cavityPressure;
    uint16 ambientPressure;
    int16 lockerError;
    uint16 padToCacheLine;
} ProcessedRingdownEntryType;

typedef struct {
    long long timestamp;
    uint32 streamNum;
    float value;
} SensorEntryType;

typedef struct {
    uint16 maskAndValue;
    uint16 dwell;
} ValveSequenceEntryType;

typedef struct {
    int32 swpDir;
    int32 lockCount;
    int32 unlockCount;
    int32 firstIteration;
    float a;
    float u;
    float perr;
    float derr1;
    float derr2;
    float Dincr;
} PidControllerEnvType;

typedef struct {
    int32 var1;
    int32 var2;
} CheckEnvType;

typedef struct {
    uint32 counter;
} PulseGenEnvType;

typedef struct {
    float offset;
    float num[9];
    float den[9];
    float state[8];
} FilterEnvType;

typedef struct {
    float setpoint;
    uint16 dwellCount;
    uint16 subschemeId;
    uint16 virtualLaser;
    uint16 threshold;
    uint16 pztSetpoint;
    uint16 laserTemp;
} SchemeRowType;

typedef struct {
    uint32 numRepeats;
    uint32 numRows;
} SchemeTableHeaderType;

typedef struct {
    uint32 numRepeats;
    uint32 numRows;
    SchemeRowType rows[8192];
} SchemeTableType;

typedef struct {
    uint16 numberOfIndices;
    uint16 currentIndex;
    uint16 restartFlag;
    uint16 loopFlag;
    uint16 schemeIndices[16];
} SchemeSequenceType;

typedef struct {
    uint32 actualLaser;
    float tempSensitivity;
    float ratio1Center;
    float ratio2Center;
    float ratio1Scale;
    float ratio2Scale;
    float phase;
    float calTemp;
    float calPressure;
    float pressureC0;
    float pressureC1;
    float pressureC2;
    float pressureC3;
} VirtualLaserParamsType;

/* Constant definitions */
// Maximum number of lasers
#define MAX_LASERS (4)
// Number of points in controller waveforms
#define CONTROLLER_WAVEFORM_POINTS (1000)
// Number of points for waveforms on controller rindown pane
#define CONTROLLER_RINGDOWN_POINTS (10000)
// Number of points for Allan statistics plots in controller
#define CONTROLLER_STATS_POINTS (32)
// Base address for DSP data memory
#define DSP_DATA_ADDRESS (0x80800000)
// Offset for ringdown results in DSP data memory
#define RDRESULTS_OFFSET (0x0)
// Number of ringdown entries
#define NUM_RINGDOWN_ENTRIES (2048)
// Size of a ringdown entry in 32 bit ints
#define RINGDOWN_ENTRY_SIZE ((sizeof(RingdownEntryType)/4))
// Offset for scheme table in DSP shared memory
#define SCHEME_OFFSET ((RDRESULTS_OFFSET+NUM_RINGDOWN_ENTRIES*RINGDOWN_ENTRY_SIZE))
// Number of scheme tables
#define NUM_SCHEME_TABLES (16)
// Maximum rows in a scheme table
#define NUM_SCHEME_ROWS (8192)
// Size of a scheme row in 32 bit ints
#define SCHEME_ROW_SIZE ((sizeof(SchemeRowType)/4))
// Size of a scheme table in 32 bit ints
#define SCHEME_TABLE_SIZE ((sizeof(SchemeTableType)/4))
// Offset for virtual laser parameters in DSP shared memory
#define VIRTUAL_LASER_PARAMS_OFFSET ((SCHEME_OFFSET+NUM_SCHEME_TABLES*SCHEME_TABLE_SIZE))
// Maximum number of virtual lasers
#define NUM_VIRTUAL_LASERS (8)
// Size of a virtual laser parameter table in 32 bit ints
#define VIRTUAL_LASER_PARAMS_SIZE ((sizeof(VirtualLaserParamsType)/4))
// Base address for DSP shared memory
#define SHAREDMEM_ADDRESS (0x10000)
// Base address for ringdown memory
#define RDMEM_ADDRESS (0xA0000000)
// Offset for software registers in DSP shared memory
#define REG_OFFSET (0x0)
// Offset for sensor stream area in DSP shared memory
#define SENSOR_OFFSET (0x1B00)
// Offset for message area in DSP shared memory
#define MESSAGE_OFFSET (0x2B00)
// Offset for group table in DSP shared memory
#define GROUP_OFFSET (0x2F00)
// Offset for operation table in DSP shared memory
#define OPERATION_OFFSET (0x2F20)
// Offset for operand table in DSP shared memory
#define OPERAND_OFFSET (0x3300)
// Offset for environment table in DSP shared memory
#define ENVIRONMENT_OFFSET (0x3700)
// Offset for host area in DSP shared memory
#define HOST_OFFSET (0x3F00)
// Offset for ringdown buffer area in DSP shared memory
#define RINGDOWN_BUFFER_OFFSET (0x4000)
// Number of ringdown buffer areas in DSP shared memory
#define NUM_RINGDOWN_BUFFERS (2)
// Code to indicate that we abandoned this scheme row due to a timeout
#define MISSING_RINGDOWN (NUM_RINGDOWN_BUFFERS)
// Size of a ringdown buffer area in 32 bit ints
#define RINGDOWN_BUFFER_SIZE ((sizeof(RingdownBufferType)/4))
// Offset for scheme sequence area in DSP shared memory
#define SCHEME_SEQUENCE_OFFSET (0x7800)
// Size of scheme sequence in 32 bit ints
#define SCHEME_SEQUENCE_SIZE ((sizeof(SchemeSequenceType)/4))
// Offset for valve sequence area in DSP shared memory
#define VALVE_SEQUENCE_OFFSET ((SCHEME_SEQUENCE_OFFSET+SCHEME_SEQUENCE_SIZE))
// Number of valve sequence entries
#define NUM_VALVE_SEQUENCE_ENTRIES (256)
// Size of a valve sequence in 32 bit ints
#define VALVE_SEQUENCE_ENTRY_SIZE ((sizeof(ValveSequenceEntryType)/4))
// Offset following used of shared memory
#define NEXT_AVAILABLE_OFFSET ((VALVE_SEQUENCE_OFFSET+NUM_VALVE_SEQUENCE_ENTRIES*VALVE_SEQUENCE_ENTRY_SIZE))
// Size (in 32-bit ints) of DSP shared memory
#define SHAREDMEM_SIZE (0x8000)
// Number of software registers
#define REG_REGION_SIZE ((SENSOR_OFFSET - REG_OFFSET))
// Number of 32-bit ints in sensor area
#define SENSOR_REGION_SIZE ((MESSAGE_OFFSET - SENSOR_OFFSET))
// Number of sensor steam entries in sensor area
#define NUM_SENSOR_ENTRIES (SENSOR_REGION_SIZE>>2)
// Number of 32-bit ints in message area
#define MESSAGE_REGION_SIZE ((GROUP_OFFSET - MESSAGE_OFFSET))
// Number of messages in message area
#define NUM_MESSAGES (MESSAGE_REGION_SIZE>>5)
// Number of 32-bit ints in group table
#define GROUP_TABLE_SIZE ((OPERATION_OFFSET - GROUP_OFFSET))
// Number of 32-bit ints in operation table
#define OPERATION_TABLE_SIZE ((OPERAND_OFFSET - OPERATION_OFFSET))
// Number of operations in operation table
#define NUM_OPERATIONS (OPERATION_TABLE_SIZE>>1)
// Number of 32-bit ints in operand table
#define OPERAND_TABLE_SIZE ((ENVIRONMENT_OFFSET - OPERAND_OFFSET))
// Number of 32-bit ints in environment table
#define ENVIRONMENT_TABLE_SIZE ((HOST_OFFSET - ENVIRONMENT_OFFSET))
// Number of 32-bit ints in host area
#define HOST_REGION_SIZE ((RINGDOWN_BUFFER_OFFSET - HOST_OFFSET))
// Number of bits in FPGA EMIF address
#define EMIF_ADDR_WIDTH (20)
// Number of bits in EMIF data
#define EMIF_DATA_WIDTH (32)
// Number of bits in an FPGA register
#define FPGA_REG_WIDTH (16)
// Mask to access ringdown memory
#define FPGA_RDMEM_MASK (0)
// Mask to access FPGA registers
#define FPGA_REG_MASK (1)
// Number of bits in ringdown data
#define RDMEM_DATA_WIDTH (18)
// Number of bits in ringdown metadata
#define RDMEM_META_WIDTH (16)
// Number of bits in ringdown parameters
#define RDMEM_PARAM_WIDTH (32)
// Number of address bits reserved for a ringdown region in each bank
#define RDMEM_RESERVED_BANK_ADDR_WIDTH (12)
// Number of address bits for one bank of data
#define DATA_BANK_ADDR_WIDTH (12)
// Number of address bits for one bank of metadata
#define META_BANK_ADDR_WIDTH (12)
// Number of address bits for one bank of parameters
#define PARAM_BANK_ADDR_WIDTH (6)
// Tuner value at ringdown index in parameter array
#define PARAM_TUNER_AT_RINGDOWN_INDEX (10)
// Metadata address at ringdown index in parameter array
#define PARAM_META_ADDR_AT_RINGDOWN_INDEX (11)
// FPGA register base address
#define FPGA_REG_BASE_ADDRESS ((RDMEM_ADDRESS + (1 << (EMIF_ADDR_WIDTH+1))))
// Number of in-range samples to acquire lock
#define TEMP_CNTRL_LOCK_COUNT (5)
// Number of out-of-range samples to lose lock
#define TEMP_CNTRL_UNLOCK_COUNT (5)
// Code to confirm FPGA is programmed
#define FPGA_MAGIC_CODE (0xC0DE0001)
// Extra bits in accumulator for ringdown simulator
#define RDSIM_EXTRA (4)
// Number of bits for wavelength monitor ADCs
#define WLM_ADC_WIDTH (16)

typedef enum {
    float_type = 0, // 
    uint_type = 1, // 
    int_type = 2 // 
} RegTypes;

typedef enum {
    STREAM_Laser1Temp = 0, // 
    STREAM_Laser2Temp = 1, // 
    STREAM_Laser3Temp = 2, // 
    STREAM_Laser4Temp = 3, // 
    STREAM_EtalonTemp = 4, // 
    STREAM_WarmBoxTemp = 5, // 
    STREAM_WarmBoxHeatsinkTemp = 6, // 
    STREAM_CavityTemp = 7, // 
    STREAM_HotBoxHeatsinkTemp = 8, // 
    STREAM_DasTemp = 9, // 
    STREAM_Etalon1 = 10, // 
    STREAM_Reference1 = 11, // 
    STREAM_Etalon2 = 12, // 
    STREAM_Reference2 = 13, // 
    STREAM_Ratio1 = 14, // 
    STREAM_Ratio2 = 15, // 
    STREAM_Laser1Current = 16, // 
    STREAM_Laser2Current = 17, // 
    STREAM_Laser3Current = 18, // 
    STREAM_Laser4Current = 19, // 
    STREAM_CavityPressure = 20, // 
    STREAM_AmbientPressure = 21, // 
    STREAM_Laser1Tec = 22, // 
    STREAM_Laser2Tec = 23, // 
    STREAM_Laser3Tec = 24, // 
    STREAM_Laser4Tec = 25, // 
    STREAM_WarmBoxTec = 26, // 
    STREAM_HotBoxTec = 27, // 
    STREAM_HotBoxHeater = 28, // 
    STREAM_InletValve = 29, // 
    STREAM_OutletValve = 30, // 
    STREAM_ValveMask = 31 // 
} STREAM_MemberType;

typedef enum {
    TEMP_CNTRL_DisabledState = 0, // Controller Disabled
    TEMP_CNTRL_EnabledState = 1, // Controller Enabled
    TEMP_CNTRL_SuspendedState = 2, // Controller Suspended
    TEMP_CNTRL_SweepingState = 3, // Continuous Sweeping
    TEMP_CNTRL_SendPrbsState = 4, // Sending PRBS
    TEMP_CNTRL_ManualState = 5, // Manual Control
    TEMP_CNTRL_AutomaticState = 6 // Automatic Control
} TEMP_CNTRL_StateType;

typedef enum {
    LASER_CURRENT_CNTRL_DisabledState = 0, // Controller Disabled
    LASER_CURRENT_CNTRL_AutomaticState = 1, // Automatic Control
    LASER_CURRENT_CNTRL_SweepingState = 2, // Continuous Sweeping
    LASER_CURRENT_CNTRL_ManualState = 3 // Manual Control
} LASER_CURRENT_CNTRL_StateType;

typedef enum {
    HEATER_CNTRL_DisabledState = 0, // Controller Disabled
    HEATER_CNTRL_EnabledState = 1, // Controller Enabled
    HEATER_CNTRL_ManualState = 2 // Manual Control
} HEATER_CNTRL_StateType;

typedef enum {
    SPECT_CNTRL_IdleState = 0, // Not acquiring
    SPECT_CNTRL_StartingState = 1, // Start acquisition
    SPECT_CNTRL_RunningState = 2, // Acquisition in progress
    SPECT_CNTRL_PausedState = 3, // Acquisition paused
    SPECT_CNTRL_ErrorState = 4 // Error state
} SPECT_CNTRL_StateType;

typedef enum {
    SPECT_CNTRL_SchemeSingleMode = 0, // Perform single scheme
    SPECT_CNTRL_SchemeMultipleMode = 1, // Perform multiple schemes
    SPECT_CNTRL_SchemeSequenceMode = 2, // Perform scheme sequence
    SPECT_CNTRL_ContinuousMode = 3 // Continuous acquisition
} SPECT_CNTRL_ModeType;

typedef enum {
    TUNER_RampMode = 0, // Ramp mode
    TUNER_DitherMode = 1 // Dither mode
} TUNER_ModeType;

typedef enum {
    TUNER_DITHER_MEDIAN_1 = 1, // 1
    TUNER_DITHER_MEDIAN_3 = 3, // 3
    TUNER_DITHER_MEDIAN_5 = 5, // 5
    TUNER_DITHER_MEDIAN_7 = 7, // 7
    TUNER_DITHER_MEDIAN_9 = 9 // 9
} TUNER_DITHER_MEDIAN_CountType;

typedef enum {
    VALVE_CNTRL_DisabledState = 0, // Disabled
    VALVE_CNTRL_OutletControlState = 1, // Outlet control
    VALVE_CNTRL_InletControlState = 2, // Inlet control
    VALVE_CNTRL_ManualControlState = 3 // Manual control
} VALVE_CNTRL_StateType;

typedef enum {
    VALVE_CNTRL_THRESHOLD_DisabledState = 0, // Disabled
    VALVE_CNTRL_THRESHOLD_ArmedState = 1, // Armed
    VALVE_CNTRL_THRESHOLD_TriggeredState = 2 // Triggered
} VALVE_CNTRL_THRESHOLD_StateType;

typedef enum {
    VIRTUAL_LASER_1 = 0, // Virtual laser 1
    VIRTUAL_LASER_2 = 1, // Virtual laser 2
    VIRTUAL_LASER_3 = 2, // Virtual laser 3
    VIRTUAL_LASER_4 = 3, // Virtual laser 4
    VIRTUAL_LASER_5 = 4, // Virtual laser 5
    VIRTUAL_LASER_6 = 5, // Virtual laser 6
    VIRTUAL_LASER_7 = 6, // Virtual laser 7
    VIRTUAL_LASER_8 = 7 // Virtual laser 8
} VIRTUAL_LASER_Type;

typedef enum {
    ACTUAL_LASER_1 = 0, // Actual laser 1
    ACTUAL_LASER_2 = 1, // Actual laser 2
    ACTUAL_LASER_3 = 2, // Actual laser 3
    ACTUAL_LASER_4 = 3 // Actual laser 4
} ACTUAL_LASER_Type;

typedef enum {
    DAS_STATUS_Laser1TempCntrlLockedBit = 0, // Laser 1 Temperature Locked
    DAS_STATUS_Laser1TempCntrlActiveBit = 1, // Laser 1 Temperature Controller On
    DAS_STATUS_Laser2TempCntrlLockedBit = 2, // Laser 2 Temperature Locked
    DAS_STATUS_Laser2TempCntrlActiveBit = 3, // Laser 2 Temperature Controller On
    DAS_STATUS_Laser3TempCntrlLockedBit = 4, // Laser 3 Temperature Locked
    DAS_STATUS_Laser3TempCntrlActiveBit = 5, // Laser 3 Temperature Controller On
    DAS_STATUS_Laser4TempCntrlLockedBit = 6, // Laser 4 Temperature Locked
    DAS_STATUS_Laser4TempCntrlActiveBit = 7, // Laser 4 Temperature Controller On
    DAS_STATUS_WarmBoxTempCntrlLockedBit = 8, // Warm Box Temperature Locked
    DAS_STATUS_WarmBoxTempCntrlActiveBit = 9, // Warm Box Temperature Controller On
    DAS_STATUS_CavityTempCntrlLockedBit = 10, // Cavity Temperature Locked
    DAS_STATUS_CavityTempCntrlActiveBit = 11, // Cavity Temperature Controller On
    DAS_STATUS_HeaterTempCntrlLockedBit = 12, // Heater Control Locked
    DAS_STATUS_HeaterTempCntrlActiveBit = 13 // Heater Controller On
} DAS_STATUS_BitType;

typedef enum {
    TEC_CNTRL_Disabled = 0, // Disabled
    TEC_CNTRL_Enabled = 1 // Enabled
} TEC_CNTRL_Type;

typedef enum {
    OVERLOAD_WarmBoxTecBit = 0, // Warm box TEC overload
    OVERLOAD_HotBoxTecBit = 1 // Hot box TEC overload
} OVERLOAD_BitType;

typedef enum {
    ANALYZER_TUNING_CavityLengthTuningMode = 0, // Cavity Length Tuning
    ANALYZER_TUNING_LaserCurrentTuningMode = 1 // Laser Current Tuning
} ANALYZER_TUNING_ModeType;

typedef enum {
    SENTRY_Laser1TemperatureBit = 0, // Laser 1 Temperature
    SENTRY_Laser2TemperatureBit = 1, // Laser 2 Temperature
    SENTRY_Laser3TemperatureBit = 2, // Laser 3 Temperature
    SENTRY_Laser4TemperatureBit = 3, // Laser 4 Temperature
    SENTRY_EtalonTemperatureBit = 4, // Etalon Temperature
    SENTRY_WarmBoxTemperatureBit = 5, // Warm Box Temperature
    SENTRY_WarmBoxHeatsinkTemperatureBit = 6, // Warm Box Heatsink Temperature
    SENTRY_CavityTemperatureBit = 7, // Cavity Temperature
    SENTRY_HotBoxHeatsinkTemperatureBit = 8, // Hot Box Heatsink Temperature
    SENTRY_DasTemperatureBit = 9, // DAS (ambient) Temperature
    SENTRY_Laser1CurrentBit = 10, // Laser 1 Current
    SENTRY_Laser2CurrentBit = 11, // Laser 2 Current
    SENTRY_Laser3CurrentBit = 12, // Laser 3 Current
    SENTRY_Laser4CurrentBit = 13, // Laser 4 Current
    SENTRY_CavityPressureBit = 14, // Cavity Pressure
    SENTRY_AmbientPressureBit = 15 // Ambient Pressure
} SENTRY_BitType;

typedef enum {
    HARDWARE_PRESENT_Laser1Bit = 0, // Laser 1
    HARDWARE_PRESENT_Laser2Bit = 1, // Laser 2
    HARDWARE_PRESENT_Laser3Bit = 2, // Laser 3
    HARDWARE_PRESENT_Laser4Bit = 3, // Laser 4
    HARDWARE_PRESENT_SoaBit = 4, // SOA
    HARDWARE_PRESENT_PowerBoardBit = 5, // Power Board
    HARDWARE_PRESENT_WarmBoxBit = 6, // Warm Box
    HARDWARE_PRESENT_HotBoxBit = 7, // Hot Box
    HARDWARE_PRESENT_ResettableI2CPort = 8 // Resettable I2C port
} HARDWARE_PRESENT_BitType;

/* Definitions for COMM_STATUS_BITMASK */
#define COMM_STATUS_CompleteMask (0x1)
#define COMM_STATUS_BadCrcMask (0x2)
#define COMM_STATUS_BadSequenceNumberMask (0x4)
#define COMM_STATUS_BadArgumentsMask (0x8)
#define COMM_STATUS_SequenceNumberMask (0xFF000000)
#define COMM_STATUS_ReturnValueMask (0x00FFFF00)
#define COMM_STATUS_SequenceNumberShift (24)
#define COMM_STATUS_ReturnValueShift (8)

/* Definitions for RINGDOWN_STATUS_BITMASK */
#define RINGDOWN_STATUS_SequenceMask (0x0F)
#define RINGDOWN_STATUS_SchemeActiveMask (0x10)
#define RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask (0x20)
#define RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask (0x40)
#define RINGDOWN_STATUS_RingdownTimeout (0x80)

/* Definitions for SUBSCHEME_ID_BITMASK */
#define SUBSCHEME_ID_IdMask (0x7FFF)
#define SUBSCHEME_ID_IncrMask (0x8000)
#define SUBSCHEME_ID_IgnoreMask (0x4000)
#define SUBSCHEME_ID_RecenterMask (0x2000)
#define SUBSCHEME_ID_IsCalMask (0x1000)
#define SUBSCHEME_ID_SpectrumSubsectionMask (0x0300)
#define SUBSCHEME_ID_SpectrumMask (0x00FF)

/* Register definitions */
#define INTERFACE_NUMBER_OF_REGISTERS (401)

#define NOOP_REGISTER (0)
#define VERIFY_INIT_REGISTER (1)
#define COMM_STATUS_REGISTER (2)
#define TIMESTAMP_LSB_REGISTER (3)
#define TIMESTAMP_MSB_REGISTER (4)
#define SCHEDULER_CONTROL_REGISTER (5)
#define HARDWARE_PRESENT_REGISTER (6)
#define RD_IRQ_COUNT_REGISTER (7)
#define ACQ_DONE_COUNT_REGISTER (8)
#define RD_DATA_MOVING_COUNT_REGISTER (9)
#define RD_QDMA_DONE_COUNT_REGISTER (10)
#define RD_FITTING_COUNT_REGISTER (11)
#define RD_INITIATED_COUNT_REGISTER (12)
#define DAS_STATUS_REGISTER (13)
#define DAS_TEMPERATURE_REGISTER (14)
#define LASER_TEC_MONITOR_TEMPERATURE_REGISTER (15)
#define CONVERSION_LASER1_THERM_CONSTA_REGISTER (16)
#define CONVERSION_LASER1_THERM_CONSTB_REGISTER (17)
#define CONVERSION_LASER1_THERM_CONSTC_REGISTER (18)
#define CONVERSION_LASER1_CURRENT_SLOPE_REGISTER (19)
#define CONVERSION_LASER1_CURRENT_OFFSET_REGISTER (20)
#define LASER1_RESISTANCE_REGISTER (21)
#define LASER1_TEMPERATURE_REGISTER (22)
#define LASER1_THERMISTOR_ADC_REGISTER (23)
#define LASER1_TEC_REGISTER (24)
#define LASER1_MANUAL_TEC_REGISTER (25)
#define LASER1_TEMP_CNTRL_STATE_REGISTER (26)
#define LASER1_TEMP_CNTRL_SETPOINT_REGISTER (27)
#define LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER (28)
#define LASER1_TEMP_CNTRL_TOLERANCE_REGISTER (29)
#define LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER (30)
#define LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER (31)
#define LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER (32)
#define LASER1_TEMP_CNTRL_H_REGISTER (33)
#define LASER1_TEMP_CNTRL_K_REGISTER (34)
#define LASER1_TEMP_CNTRL_TI_REGISTER (35)
#define LASER1_TEMP_CNTRL_TD_REGISTER (36)
#define LASER1_TEMP_CNTRL_B_REGISTER (37)
#define LASER1_TEMP_CNTRL_C_REGISTER (38)
#define LASER1_TEMP_CNTRL_N_REGISTER (39)
#define LASER1_TEMP_CNTRL_S_REGISTER (40)
#define LASER1_TEMP_CNTRL_FFWD_REGISTER (41)
#define LASER1_TEMP_CNTRL_AMIN_REGISTER (42)
#define LASER1_TEMP_CNTRL_AMAX_REGISTER (43)
#define LASER1_TEMP_CNTRL_IMAX_REGISTER (44)
#define LASER1_TEC_PRBS_GENPOLY_REGISTER (45)
#define LASER1_TEC_PRBS_AMPLITUDE_REGISTER (46)
#define LASER1_TEC_PRBS_MEAN_REGISTER (47)
#define LASER1_TEC_MONITOR_REGISTER (48)
#define LASER1_CURRENT_CNTRL_STATE_REGISTER (49)
#define LASER1_MANUAL_COARSE_CURRENT_REGISTER (50)
#define LASER1_MANUAL_FINE_CURRENT_REGISTER (51)
#define LASER1_CURRENT_SWEEP_MIN_REGISTER (52)
#define LASER1_CURRENT_SWEEP_MAX_REGISTER (53)
#define LASER1_CURRENT_SWEEP_INCR_REGISTER (54)
#define LASER1_CURRENT_MONITOR_REGISTER (55)
#define CONVERSION_LASER2_THERM_CONSTA_REGISTER (56)
#define CONVERSION_LASER2_THERM_CONSTB_REGISTER (57)
#define CONVERSION_LASER2_THERM_CONSTC_REGISTER (58)
#define CONVERSION_LASER2_CURRENT_SLOPE_REGISTER (59)
#define CONVERSION_LASER2_CURRENT_OFFSET_REGISTER (60)
#define LASER2_RESISTANCE_REGISTER (61)
#define LASER2_TEMPERATURE_REGISTER (62)
#define LASER2_THERMISTOR_ADC_REGISTER (63)
#define LASER2_TEC_REGISTER (64)
#define LASER2_MANUAL_TEC_REGISTER (65)
#define LASER2_TEMP_CNTRL_STATE_REGISTER (66)
#define LASER2_TEMP_CNTRL_SETPOINT_REGISTER (67)
#define LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER (68)
#define LASER2_TEMP_CNTRL_TOLERANCE_REGISTER (69)
#define LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER (70)
#define LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER (71)
#define LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER (72)
#define LASER2_TEMP_CNTRL_H_REGISTER (73)
#define LASER2_TEMP_CNTRL_K_REGISTER (74)
#define LASER2_TEMP_CNTRL_TI_REGISTER (75)
#define LASER2_TEMP_CNTRL_TD_REGISTER (76)
#define LASER2_TEMP_CNTRL_B_REGISTER (77)
#define LASER2_TEMP_CNTRL_C_REGISTER (78)
#define LASER2_TEMP_CNTRL_N_REGISTER (79)
#define LASER2_TEMP_CNTRL_S_REGISTER (80)
#define LASER2_TEMP_CNTRL_FFWD_REGISTER (81)
#define LASER2_TEMP_CNTRL_AMIN_REGISTER (82)
#define LASER2_TEMP_CNTRL_AMAX_REGISTER (83)
#define LASER2_TEMP_CNTRL_IMAX_REGISTER (84)
#define LASER2_TEC_PRBS_GENPOLY_REGISTER (85)
#define LASER2_TEC_PRBS_AMPLITUDE_REGISTER (86)
#define LASER2_TEC_PRBS_MEAN_REGISTER (87)
#define LASER2_TEC_MONITOR_REGISTER (88)
#define LASER2_CURRENT_CNTRL_STATE_REGISTER (89)
#define LASER2_MANUAL_COARSE_CURRENT_REGISTER (90)
#define LASER2_MANUAL_FINE_CURRENT_REGISTER (91)
#define LASER2_CURRENT_SWEEP_MIN_REGISTER (92)
#define LASER2_CURRENT_SWEEP_MAX_REGISTER (93)
#define LASER2_CURRENT_SWEEP_INCR_REGISTER (94)
#define LASER2_CURRENT_MONITOR_REGISTER (95)
#define CONVERSION_LASER3_THERM_CONSTA_REGISTER (96)
#define CONVERSION_LASER3_THERM_CONSTB_REGISTER (97)
#define CONVERSION_LASER3_THERM_CONSTC_REGISTER (98)
#define CONVERSION_LASER3_CURRENT_SLOPE_REGISTER (99)
#define CONVERSION_LASER3_CURRENT_OFFSET_REGISTER (100)
#define LASER3_RESISTANCE_REGISTER (101)
#define LASER3_TEMPERATURE_REGISTER (102)
#define LASER3_THERMISTOR_ADC_REGISTER (103)
#define LASER3_TEC_REGISTER (104)
#define LASER3_MANUAL_TEC_REGISTER (105)
#define LASER3_TEMP_CNTRL_STATE_REGISTER (106)
#define LASER3_TEMP_CNTRL_SETPOINT_REGISTER (107)
#define LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER (108)
#define LASER3_TEMP_CNTRL_TOLERANCE_REGISTER (109)
#define LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER (110)
#define LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER (111)
#define LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER (112)
#define LASER3_TEMP_CNTRL_H_REGISTER (113)
#define LASER3_TEMP_CNTRL_K_REGISTER (114)
#define LASER3_TEMP_CNTRL_TI_REGISTER (115)
#define LASER3_TEMP_CNTRL_TD_REGISTER (116)
#define LASER3_TEMP_CNTRL_B_REGISTER (117)
#define LASER3_TEMP_CNTRL_C_REGISTER (118)
#define LASER3_TEMP_CNTRL_N_REGISTER (119)
#define LASER3_TEMP_CNTRL_S_REGISTER (120)
#define LASER3_TEMP_CNTRL_FFWD_REGISTER (121)
#define LASER3_TEMP_CNTRL_AMIN_REGISTER (122)
#define LASER3_TEMP_CNTRL_AMAX_REGISTER (123)
#define LASER3_TEMP_CNTRL_IMAX_REGISTER (124)
#define LASER3_TEC_PRBS_GENPOLY_REGISTER (125)
#define LASER3_TEC_PRBS_AMPLITUDE_REGISTER (126)
#define LASER3_TEC_PRBS_MEAN_REGISTER (127)
#define LASER3_TEC_MONITOR_REGISTER (128)
#define LASER3_CURRENT_CNTRL_STATE_REGISTER (129)
#define LASER3_MANUAL_COARSE_CURRENT_REGISTER (130)
#define LASER3_MANUAL_FINE_CURRENT_REGISTER (131)
#define LASER3_CURRENT_SWEEP_MIN_REGISTER (132)
#define LASER3_CURRENT_SWEEP_MAX_REGISTER (133)
#define LASER3_CURRENT_SWEEP_INCR_REGISTER (134)
#define LASER3_CURRENT_MONITOR_REGISTER (135)
#define CONVERSION_LASER4_THERM_CONSTA_REGISTER (136)
#define CONVERSION_LASER4_THERM_CONSTB_REGISTER (137)
#define CONVERSION_LASER4_THERM_CONSTC_REGISTER (138)
#define CONVERSION_LASER4_CURRENT_SLOPE_REGISTER (139)
#define CONVERSION_LASER4_CURRENT_OFFSET_REGISTER (140)
#define LASER4_RESISTANCE_REGISTER (141)
#define LASER4_TEMPERATURE_REGISTER (142)
#define LASER4_THERMISTOR_ADC_REGISTER (143)
#define LASER4_TEC_REGISTER (144)
#define LASER4_MANUAL_TEC_REGISTER (145)
#define LASER4_TEMP_CNTRL_STATE_REGISTER (146)
#define LASER4_TEMP_CNTRL_SETPOINT_REGISTER (147)
#define LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER (148)
#define LASER4_TEMP_CNTRL_TOLERANCE_REGISTER (149)
#define LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER (150)
#define LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER (151)
#define LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER (152)
#define LASER4_TEMP_CNTRL_H_REGISTER (153)
#define LASER4_TEMP_CNTRL_K_REGISTER (154)
#define LASER4_TEMP_CNTRL_TI_REGISTER (155)
#define LASER4_TEMP_CNTRL_TD_REGISTER (156)
#define LASER4_TEMP_CNTRL_B_REGISTER (157)
#define LASER4_TEMP_CNTRL_C_REGISTER (158)
#define LASER4_TEMP_CNTRL_N_REGISTER (159)
#define LASER4_TEMP_CNTRL_S_REGISTER (160)
#define LASER4_TEMP_CNTRL_FFWD_REGISTER (161)
#define LASER4_TEMP_CNTRL_AMIN_REGISTER (162)
#define LASER4_TEMP_CNTRL_AMAX_REGISTER (163)
#define LASER4_TEMP_CNTRL_IMAX_REGISTER (164)
#define LASER4_TEC_PRBS_GENPOLY_REGISTER (165)
#define LASER4_TEC_PRBS_AMPLITUDE_REGISTER (166)
#define LASER4_TEC_PRBS_MEAN_REGISTER (167)
#define LASER4_TEC_MONITOR_REGISTER (168)
#define LASER4_CURRENT_CNTRL_STATE_REGISTER (169)
#define LASER4_MANUAL_COARSE_CURRENT_REGISTER (170)
#define LASER4_MANUAL_FINE_CURRENT_REGISTER (171)
#define LASER4_CURRENT_SWEEP_MIN_REGISTER (172)
#define LASER4_CURRENT_SWEEP_MAX_REGISTER (173)
#define LASER4_CURRENT_SWEEP_INCR_REGISTER (174)
#define LASER4_CURRENT_MONITOR_REGISTER (175)
#define CONVERSION_ETALON_THERM_CONSTA_REGISTER (176)
#define CONVERSION_ETALON_THERM_CONSTB_REGISTER (177)
#define CONVERSION_ETALON_THERM_CONSTC_REGISTER (178)
#define ETALON_RESISTANCE_REGISTER (179)
#define ETALON_TEMPERATURE_REGISTER (180)
#define ETALON_THERMISTOR_ADC_REGISTER (181)
#define CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER (182)
#define CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER (183)
#define CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER (184)
#define WARM_BOX_RESISTANCE_REGISTER (185)
#define WARM_BOX_TEMPERATURE_REGISTER (186)
#define WARM_BOX_THERMISTOR_ADC_REGISTER (187)
#define WARM_BOX_TEC_REGISTER (188)
#define WARM_BOX_MANUAL_TEC_REGISTER (189)
#define WARM_BOX_TEMP_CNTRL_STATE_REGISTER (190)
#define WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER (191)
#define WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER (192)
#define WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER (193)
#define WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER (194)
#define WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER (195)
#define WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER (196)
#define WARM_BOX_TEMP_CNTRL_H_REGISTER (197)
#define WARM_BOX_TEMP_CNTRL_K_REGISTER (198)
#define WARM_BOX_TEMP_CNTRL_TI_REGISTER (199)
#define WARM_BOX_TEMP_CNTRL_TD_REGISTER (200)
#define WARM_BOX_TEMP_CNTRL_B_REGISTER (201)
#define WARM_BOX_TEMP_CNTRL_C_REGISTER (202)
#define WARM_BOX_TEMP_CNTRL_N_REGISTER (203)
#define WARM_BOX_TEMP_CNTRL_S_REGISTER (204)
#define WARM_BOX_TEMP_CNTRL_FFWD_REGISTER (205)
#define WARM_BOX_TEMP_CNTRL_AMIN_REGISTER (206)
#define WARM_BOX_TEMP_CNTRL_AMAX_REGISTER (207)
#define WARM_BOX_TEMP_CNTRL_IMAX_REGISTER (208)
#define WARM_BOX_TEC_PRBS_GENPOLY_REGISTER (209)
#define WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER (210)
#define WARM_BOX_TEC_PRBS_MEAN_REGISTER (211)
#define WARM_BOX_MAX_HEATSINK_TEMP_REGISTER (212)
#define CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER (213)
#define CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER (214)
#define CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER (215)
#define WARM_BOX_HEATSINK_RESISTANCE_REGISTER (216)
#define WARM_BOX_HEATSINK_TEMPERATURE_REGISTER (217)
#define WARM_BOX_HEATSINK_THERMISTOR_ADC_REGISTER (218)
#define CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER (219)
#define CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER (220)
#define CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER (221)
#define HOT_BOX_HEATSINK_RESISTANCE_REGISTER (222)
#define HOT_BOX_HEATSINK_TEMPERATURE_REGISTER (223)
#define HOT_BOX_HEATSINK_ADC_REGISTER (224)
#define CONVERSION_CAVITY_THERM_CONSTA_REGISTER (225)
#define CONVERSION_CAVITY_THERM_CONSTB_REGISTER (226)
#define CONVERSION_CAVITY_THERM_CONSTC_REGISTER (227)
#define CAVITY_RESISTANCE_REGISTER (228)
#define CAVITY_TEMPERATURE_REGISTER (229)
#define CAVITY_THERMISTOR_ADC_REGISTER (230)
#define CAVITY_TEC_REGISTER (231)
#define CAVITY_MANUAL_TEC_REGISTER (232)
#define CAVITY_TEMP_CNTRL_STATE_REGISTER (233)
#define CAVITY_TEMP_CNTRL_SETPOINT_REGISTER (234)
#define CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER (235)
#define CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER (236)
#define CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER (237)
#define CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER (238)
#define CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER (239)
#define CAVITY_TEMP_CNTRL_H_REGISTER (240)
#define CAVITY_TEMP_CNTRL_K_REGISTER (241)
#define CAVITY_TEMP_CNTRL_TI_REGISTER (242)
#define CAVITY_TEMP_CNTRL_TD_REGISTER (243)
#define CAVITY_TEMP_CNTRL_B_REGISTER (244)
#define CAVITY_TEMP_CNTRL_C_REGISTER (245)
#define CAVITY_TEMP_CNTRL_N_REGISTER (246)
#define CAVITY_TEMP_CNTRL_S_REGISTER (247)
#define CAVITY_TEMP_CNTRL_FFWD_REGISTER (248)
#define CAVITY_TEMP_CNTRL_AMIN_REGISTER (249)
#define CAVITY_TEMP_CNTRL_AMAX_REGISTER (250)
#define CAVITY_TEMP_CNTRL_IMAX_REGISTER (251)
#define CAVITY_TEC_PRBS_GENPOLY_REGISTER (252)
#define CAVITY_TEC_PRBS_AMPLITUDE_REGISTER (253)
#define CAVITY_TEC_PRBS_MEAN_REGISTER (254)
#define CAVITY_MAX_HEATSINK_TEMP_REGISTER (255)
#define HEATER_MARK_REGISTER (256)
#define HEATER_MANUAL_MARK_REGISTER (257)
#define HEATER_TEMP_CNTRL_STATE_REGISTER (258)
#define HEATER_TEMP_CNTRL_SETPOINT_REGISTER (259)
#define HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER (260)
#define HEATER_TEMP_CNTRL_TOLERANCE_REGISTER (261)
#define HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER (262)
#define HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER (263)
#define HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER (264)
#define HEATER_TEMP_CNTRL_H_REGISTER (265)
#define HEATER_TEMP_CNTRL_K_REGISTER (266)
#define HEATER_TEMP_CNTRL_TI_REGISTER (267)
#define HEATER_TEMP_CNTRL_TD_REGISTER (268)
#define HEATER_TEMP_CNTRL_B_REGISTER (269)
#define HEATER_TEMP_CNTRL_C_REGISTER (270)
#define HEATER_TEMP_CNTRL_N_REGISTER (271)
#define HEATER_TEMP_CNTRL_S_REGISTER (272)
#define HEATER_TEMP_CNTRL_AMIN_REGISTER (273)
#define HEATER_TEMP_CNTRL_AMAX_REGISTER (274)
#define HEATER_TEMP_CNTRL_IMAX_REGISTER (275)
#define HEATER_PRBS_GENPOLY_REGISTER (276)
#define HEATER_PRBS_AMPLITUDE_REGISTER (277)
#define HEATER_PRBS_MEAN_REGISTER (278)
#define CAVITY_PRESSURE_ADC_REGISTER (279)
#define CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER (280)
#define CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER (281)
#define CAVITY_PRESSURE_REGISTER (282)
#define AMBIENT_PRESSURE_ADC_REGISTER (283)
#define CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER (284)
#define CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER (285)
#define AMBIENT_PRESSURE_REGISTER (286)
#define ANALYZER_TUNING_MODE_REGISTER (287)
#define TUNER_SWEEP_RAMP_HIGH_REGISTER (288)
#define TUNER_SWEEP_RAMP_LOW_REGISTER (289)
#define TUNER_WINDOW_RAMP_HIGH_REGISTER (290)
#define TUNER_WINDOW_RAMP_LOW_REGISTER (291)
#define TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER (292)
#define TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER (293)
#define TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER (294)
#define TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER (295)
#define TUNER_DITHER_MEDIAN_COUNT_REGISTER (296)
#define RDFITTER_MINLOSS_REGISTER (297)
#define RDFITTER_MAXLOSS_REGISTER (298)
#define RDFITTER_LATEST_LOSS_REGISTER (299)
#define RDFITTER_IMPROVEMENT_STEPS_REGISTER (300)
#define RDFITTER_START_SAMPLE_REGISTER (301)
#define RDFITTER_FRACTIONAL_THRESHOLD_REGISTER (302)
#define RDFITTER_ABSOLUTE_THRESHOLD_REGISTER (303)
#define RDFITTER_NUMBER_OF_POINTS_REGISTER (304)
#define RDFITTER_MAX_E_FOLDINGS_REGISTER (305)
#define RDFITTER_META_BACKOFF_REGISTER (306)
#define RDFITTER_META_SAMPLES_REGISTER (307)
#define SPECT_CNTRL_STATE_REGISTER (308)
#define SPECT_CNTRL_MODE_REGISTER (309)
#define SPECT_CNTRL_ACTIVE_SCHEME_REGISTER (310)
#define SPECT_CNTRL_NEXT_SCHEME_REGISTER (311)
#define SPECT_CNTRL_SCHEME_ITER_REGISTER (312)
#define SPECT_CNTRL_SCHEME_ROW_REGISTER (313)
#define SPECT_CNTRL_DWELL_COUNT_REGISTER (314)
#define SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER (315)
#define SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER (316)
#define SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER (317)
#define VIRTUAL_LASER_REGISTER (318)
#define PZT_INCR_PER_CAVITY_FSR (319)
#define PZT_OFFSET_UPDATE_FACTOR (320)
#define PZT_OFFSET_VIRTUAL_LASER1 (321)
#define PZT_OFFSET_VIRTUAL_LASER2 (322)
#define PZT_OFFSET_VIRTUAL_LASER3 (323)
#define PZT_OFFSET_VIRTUAL_LASER4 (324)
#define PZT_OFFSET_VIRTUAL_LASER5 (325)
#define PZT_OFFSET_VIRTUAL_LASER6 (326)
#define PZT_OFFSET_VIRTUAL_LASER7 (327)
#define PZT_OFFSET_VIRTUAL_LASER8 (328)
#define SCHEME_OFFSET_VIRTUAL_LASER1 (329)
#define SCHEME_OFFSET_VIRTUAL_LASER2 (330)
#define SCHEME_OFFSET_VIRTUAL_LASER3 (331)
#define SCHEME_OFFSET_VIRTUAL_LASER4 (332)
#define SCHEME_OFFSET_VIRTUAL_LASER5 (333)
#define SCHEME_OFFSET_VIRTUAL_LASER6 (334)
#define SCHEME_OFFSET_VIRTUAL_LASER7 (335)
#define SCHEME_OFFSET_VIRTUAL_LASER8 (336)
#define VALVE_CNTRL_STATE_REGISTER (337)
#define VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER (338)
#define VALVE_CNTRL_USER_INLET_VALVE_REGISTER (339)
#define VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER (340)
#define VALVE_CNTRL_INLET_VALVE_REGISTER (341)
#define VALVE_CNTRL_OUTLET_VALVE_REGISTER (342)
#define VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER (343)
#define VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER (344)
#define VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER (345)
#define VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER (346)
#define VALVE_CNTRL_INLET_VALVE_MIN_REGISTER (347)
#define VALVE_CNTRL_INLET_VALVE_MAX_REGISTER (348)
#define VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER (349)
#define VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER (350)
#define VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER (351)
#define VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER (352)
#define VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER (353)
#define VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER (354)
#define VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER (355)
#define VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER (356)
#define VALVE_CNTRL_THRESHOLD_STATE_REGISTER (357)
#define VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER (358)
#define VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER (359)
#define VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER (360)
#define VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER (361)
#define VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER (362)
#define VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER (363)
#define VALVE_CNTRL_SEQUENCE_STEP_REGISTER (364)
#define VALVE_CNTRL_SOLENOID_VALVES_REGISTER (365)
#define TEC_CNTRL_REGISTER (366)
#define SENTRY_UPPER_LIMIT_TRIPPED_REGISTER (367)
#define SENTRY_LOWER_LIMIT_TRIPPED_REGISTER (368)
#define SENTRY_LASER1_TEMPERATURE_MIN_REGISTER (369)
#define SENTRY_LASER1_TEMPERATURE_MAX_REGISTER (370)
#define SENTRY_LASER2_TEMPERATURE_MIN_REGISTER (371)
#define SENTRY_LASER2_TEMPERATURE_MAX_REGISTER (372)
#define SENTRY_LASER3_TEMPERATURE_MIN_REGISTER (373)
#define SENTRY_LASER3_TEMPERATURE_MAX_REGISTER (374)
#define SENTRY_LASER4_TEMPERATURE_MIN_REGISTER (375)
#define SENTRY_LASER4_TEMPERATURE_MAX_REGISTER (376)
#define SENTRY_ETALON_TEMPERATURE_MIN_REGISTER (377)
#define SENTRY_ETALON_TEMPERATURE_MAX_REGISTER (378)
#define SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER (379)
#define SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER (380)
#define SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER (381)
#define SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER (382)
#define SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER (383)
#define SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER (384)
#define SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER (385)
#define SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER (386)
#define SENTRY_DAS_TEMPERATURE_MIN_REGISTER (387)
#define SENTRY_DAS_TEMPERATURE_MAX_REGISTER (388)
#define SENTRY_LASER1_CURRENT_MIN_REGISTER (389)
#define SENTRY_LASER1_CURRENT_MAX_REGISTER (390)
#define SENTRY_LASER2_CURRENT_MIN_REGISTER (391)
#define SENTRY_LASER2_CURRENT_MAX_REGISTER (392)
#define SENTRY_LASER3_CURRENT_MIN_REGISTER (393)
#define SENTRY_LASER3_CURRENT_MAX_REGISTER (394)
#define SENTRY_LASER4_CURRENT_MIN_REGISTER (395)
#define SENTRY_LASER4_CURRENT_MAX_REGISTER (396)
#define SENTRY_CAVITY_PRESSURE_MIN_REGISTER (397)
#define SENTRY_CAVITY_PRESSURE_MAX_REGISTER (398)
#define SENTRY_AMBIENT_PRESSURE_MIN_REGISTER (399)
#define SENTRY_AMBIENT_PRESSURE_MAX_REGISTER (400)

/* FPGA block definitions */

/* Block KERNEL Kernel */
#define KERNEL_MAGIC_CODE (0) // Code indicating FPGA is programmed
#define KERNEL_CONTROL (1) // Kernel control register
#define KERNEL_CONTROL_CYPRESS_RESET_B (0) // Reset Cypress FX2 and FPGA bit position
#define KERNEL_CONTROL_CYPRESS_RESET_W (1) // Reset Cypress FX2 and FPGA bit width
#define KERNEL_CONTROL_OVERLOAD_RESET_B (1) // Reset overload register bit position
#define KERNEL_CONTROL_OVERLOAD_RESET_W (1) // Reset overload register bit width
#define KERNEL_CONTROL_I2C_RESET_B (2) // Reset i2c multiplexers bit position
#define KERNEL_CONTROL_I2C_RESET_W (1) // Reset i2c multiplexers bit width

#define KERNEL_DIAG_1 (2) // DSP accessible register for diagnostics
#define KERNEL_INTRONIX_CLKSEL (3) // 
#define KERNEL_INTRONIX_CLKSEL_DIVISOR_B (0) // Intronix sampling rate bit position
#define KERNEL_INTRONIX_CLKSEL_DIVISOR_W (5) // Intronix sampling rate bit width

#define KERNEL_INTRONIX_1 (4) // 
#define KERNEL_INTRONIX_1_CHANNEL_B (0) // Intronix display 1 channel bit position
#define KERNEL_INTRONIX_1_CHANNEL_W (8) // Intronix display 1 channel bit width

#define KERNEL_INTRONIX_2 (5) // 
#define KERNEL_INTRONIX_2_CHANNEL_B (0) // Intronix display 2 channel bit position
#define KERNEL_INTRONIX_2_CHANNEL_W (8) // Intronix display 2 channel bit width

#define KERNEL_INTRONIX_3 (6) // 
#define KERNEL_INTRONIX_3_CHANNEL_B (0) // Intronix display 3 channel bit position
#define KERNEL_INTRONIX_3_CHANNEL_W (8) // Intronix display 3 channel bit width

#define KERNEL_OVERLOAD (7) // Overload register

/* Block PWM Pulse width modulator */
#define PWM_CS (0) // Control/Status register
#define PWM_CS_RUN_B (0) // STOP/RUN bit position
#define PWM_CS_RUN_W (1) // STOP/RUN bit width
#define PWM_CS_CONT_B (1) // SINGLE/CONTINUOUS bit position
#define PWM_CS_CONT_W (1) // SINGLE/CONTINUOUS bit width
#define PWM_CS_PWM_OUT_B (2) // PWM_OUT bit position
#define PWM_CS_PWM_OUT_W (1) // PWM_OUT bit width

#define PWM_PULSE_WIDTH (1) // Pulse width register

/* Block RDSIM Ringdown simulator */
#define RDSIM_OPTIONS (0) // Options
#define RDSIM_OPTIONS_INPUT_SEL_B (0) // Source of decay and tuner center parameters bit position
#define RDSIM_OPTIONS_INPUT_SEL_W (1) // Source of decay and tuner center parameters bit width

#define RDSIM_PZT_CENTER (1) // PZT value (mod 16384) around which cavity fills
#define RDSIM_PZT_WINDOW_HALF_WIDTH (2) // Half-width of PZT window within which cavity fills
#define RDSIM_FILLING_RATE (3) // Rate of increase of accumulator value during filling
#define RDSIM_DECAY (4) // Exponential decay of accumulator when not filling
#define RDSIM_DECAY_IN_SHIFT (5) // Bits to  right shift decay input
#define RDSIM_DECAY_IN_OFFSET (6) // 
#define RDSIM_ACCUMULATOR (7) // Simulated ringdown value

/* Block LASERLOCKER Laser frequency locker */
#define LASERLOCKER_CS (0) // Control/Status register
#define LASERLOCKER_CS_RUN_B (0) // Stop/Run bit position
#define LASERLOCKER_CS_RUN_W (1) // Stop/Run bit width
#define LASERLOCKER_CS_CONT_B (1) // Single/Continuous bit position
#define LASERLOCKER_CS_CONT_W (1) // Single/Continuous bit width
#define LASERLOCKER_CS_PRBS_B (2) // Generate PRBS bit position
#define LASERLOCKER_CS_PRBS_W (1) // Generate PRBS bit width
#define LASERLOCKER_CS_ACC_EN_B (3) // Enable fine current acc bit position
#define LASERLOCKER_CS_ACC_EN_W (1) // Enable fine current acc bit width
#define LASERLOCKER_CS_SAMPLE_DARK_B (4) // Sample dark currents bit position
#define LASERLOCKER_CS_SAMPLE_DARK_W (1) // Sample dark currents bit width
#define LASERLOCKER_CS_ADC_STROBE_B (5) // Load WLM ADC values bit position
#define LASERLOCKER_CS_ADC_STROBE_W (1) // Load WLM ADC values bit width
#define LASERLOCKER_CS_TUNING_OFFSET_SEL_B (6) // Tuner offset source bit position
#define LASERLOCKER_CS_TUNING_OFFSET_SEL_W (1) // Tuner offset source bit width
#define LASERLOCKER_CS_LASER_FREQ_OK_B (7) // Laser frequency in window bit position
#define LASERLOCKER_CS_LASER_FREQ_OK_W (1) // Laser frequency in window bit width
#define LASERLOCKER_CS_CURRENT_OK_B (8) // Fine current calculation bit position
#define LASERLOCKER_CS_CURRENT_OK_W (1) // Fine current calculation bit width

#define LASERLOCKER_OPTIONS (1) // Options register
#define LASERLOCKER_OPTIONS_SIM_ACTUAL_B (0) // Wavelength Monitor Data Source bit position
#define LASERLOCKER_OPTIONS_SIM_ACTUAL_W (1) // Wavelength Monitor Data Source bit width

#define LASERLOCKER_ETA1 (2) // Etalon 1 reading
#define LASERLOCKER_REF1 (3) // Reference 1 reading
#define LASERLOCKER_ETA2 (4) // Etalon 2 reading
#define LASERLOCKER_REF2 (5) // Reference 2 reading
#define LASERLOCKER_ETA1_DARK (6) // Etalon 1 dark reading
#define LASERLOCKER_REF1_DARK (7) // Reference 1 dark reading
#define LASERLOCKER_ETA2_DARK (8) // Etalon 2 dark reading
#define LASERLOCKER_REF2_DARK (9) // Reference 2 dark reading
#define LASERLOCKER_ETA1_OFFSET (10) // Etalon 1 offset
#define LASERLOCKER_REF1_OFFSET (11) // Reference 1 offset
#define LASERLOCKER_ETA2_OFFSET (12) // Etalon 2 offset
#define LASERLOCKER_REF2_OFFSET (13) // Reference 2 offset
#define LASERLOCKER_RATIO1 (14) // Ratio 1
#define LASERLOCKER_RATIO2 (15) // Ratio 2
#define LASERLOCKER_RATIO1_CENTER (16) // Ratio 1 ellipse center
#define LASERLOCKER_RATIO1_MULTIPLIER (17) // Ratio 1 multiplier
#define LASERLOCKER_RATIO2_CENTER (18) // Ratio 2 ellipse center
#define LASERLOCKER_RATIO2_MULTIPLIER (19) // Ratio 2 multiplier
#define LASERLOCKER_TUNING_OFFSET (20) // Error offset to shift frequency
#define LASERLOCKER_LOCK_ERROR (21) // Locker loop error
#define LASERLOCKER_WM_LOCK_WINDOW (22) // Lock window
#define LASERLOCKER_WM_INT_GAIN (23) // Locker integral gain
#define LASERLOCKER_WM_PROP_GAIN (24) // Locker proportional gain
#define LASERLOCKER_WM_DERIV_GAIN (25) // Locker derivative gain
#define LASERLOCKER_FINE_CURRENT (26) // Fine laser current
#define LASERLOCKER_CYCLE_COUNTER (27) // Cycle counter

/* Block RDMAN Ringdown manager */
#define RDMAN_CONTROL (0) // Control register
#define RDMAN_CONTROL_RUN_B (0) // Stop/Run bit position
#define RDMAN_CONTROL_RUN_W (1) // Stop/Run bit width
#define RDMAN_CONTROL_CONT_B (1) // Single/Continuous bit position
#define RDMAN_CONTROL_CONT_W (1) // Single/Continuous bit width
#define RDMAN_CONTROL_START_RD_B (2) // Start ringdown cycle bit position
#define RDMAN_CONTROL_START_RD_W (1) // Start ringdown cycle bit width
#define RDMAN_CONTROL_ABORT_RD_B (3) // Abort ringdown bit position
#define RDMAN_CONTROL_ABORT_RD_W (1) // Abort ringdown bit width
#define RDMAN_CONTROL_RESET_RDMAN_B (4) // Reset ringdown manager bit position
#define RDMAN_CONTROL_RESET_RDMAN_W (1) // Reset ringdown manager bit width
#define RDMAN_CONTROL_BANK0_CLEAR_B (5) // Mark bank 0 available for write bit position
#define RDMAN_CONTROL_BANK0_CLEAR_W (1) // Mark bank 0 available for write bit width
#define RDMAN_CONTROL_BANK1_CLEAR_B (6) // Mark bank 1 available for write bit position
#define RDMAN_CONTROL_BANK1_CLEAR_W (1) // Mark bank 1 available for write bit width
#define RDMAN_CONTROL_RD_IRQ_ACK_B (7) // Acknowledge ring-down interrupt bit position
#define RDMAN_CONTROL_RD_IRQ_ACK_W (1) // Acknowledge ring-down interrupt bit width
#define RDMAN_CONTROL_ACQ_DONE_ACK_B (8) // Acknowledge data acquired interrupt bit position
#define RDMAN_CONTROL_ACQ_DONE_ACK_W (1) // Acknowledge data acquired interrupt bit width
#define RDMAN_CONTROL_RAMP_DITHER_B (9) // Tuner waveform mode bit position
#define RDMAN_CONTROL_RAMP_DITHER_W (1) // Tuner waveform mode bit width

#define RDMAN_STATUS (1) // Status register
#define RDMAN_STATUS_SHUTDOWN_B (0) // Indicates shutdown of optical injection bit position
#define RDMAN_STATUS_SHUTDOWN_W (1) // Indicates shutdown of optical injection bit width
#define RDMAN_STATUS_RD_IRQ_B (1) // Ring down interrupt occured bit position
#define RDMAN_STATUS_RD_IRQ_W (1) // Ring down interrupt occured bit width
#define RDMAN_STATUS_ACQ_DONE_B (2) // Data acquired interrupt occured bit position
#define RDMAN_STATUS_ACQ_DONE_W (1) // Data acquired interrupt occured bit width
#define RDMAN_STATUS_BANK_B (3) // Active bank for data acquisition bit position
#define RDMAN_STATUS_BANK_W (1) // Active bank for data acquisition bit width
#define RDMAN_STATUS_BANK0_IN_USE_B (4) // Bank 0 memory in use bit position
#define RDMAN_STATUS_BANK0_IN_USE_W (1) // Bank 0 memory in use bit width
#define RDMAN_STATUS_BANK1_IN_USE_B (5) // Bank 1 memory in use bit position
#define RDMAN_STATUS_BANK1_IN_USE_W (1) // Bank 1 memory in use bit width
#define RDMAN_STATUS_LAPPED_B (6) // Metadata counter lapped bit position
#define RDMAN_STATUS_LAPPED_W (1) // Metadata counter lapped bit width
#define RDMAN_STATUS_LASER_FREQ_LOCKED_B (7) // Laser frequency locked bit position
#define RDMAN_STATUS_LASER_FREQ_LOCKED_W (1) // Laser frequency locked bit width
#define RDMAN_STATUS_TIMEOUT_B (8) // Timeout without ring-down bit position
#define RDMAN_STATUS_TIMEOUT_W (1) // Timeout without ring-down bit width
#define RDMAN_STATUS_ABORTED_B (9) // Ring-down aborted bit position
#define RDMAN_STATUS_ABORTED_W (1) // Ring-down aborted bit width
#define RDMAN_STATUS_BUSY_B (10) // Ringdown Cycle State bit position
#define RDMAN_STATUS_BUSY_W (1) // Ringdown Cycle State bit width

#define RDMAN_OPTIONS (2) // Options register
#define RDMAN_OPTIONS_LOCK_ENABLE_B (0) // Enable frequency locking bit position
#define RDMAN_OPTIONS_LOCK_ENABLE_W (1) // Enable frequency locking bit width
#define RDMAN_OPTIONS_UP_SLOPE_ENABLE_B (1) // Allow ring-down on positive tuner slope bit position
#define RDMAN_OPTIONS_UP_SLOPE_ENABLE_W (1) // Allow ring-down on positive tuner slope bit width
#define RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B (2) // Allow ring-down on negative tuner slope bit position
#define RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_W (1) // Allow ring-down on negative tuner slope bit width
#define RDMAN_OPTIONS_DITHER_ENABLE_B (3) // Allow transition to dither mode bit position
#define RDMAN_OPTIONS_DITHER_ENABLE_W (1) // Allow transition to dither mode bit width
#define RDMAN_OPTIONS_SIM_ACTUAL_B (4) // Ringdown data source bit position
#define RDMAN_OPTIONS_SIM_ACTUAL_W (1) // Ringdown data source bit width

#define RDMAN_PARAM0 (3) // Parameter 0 register
#define RDMAN_PARAM1 (4) // Parameter 1 register
#define RDMAN_PARAM2 (5) // Parameter 2 register
#define RDMAN_PARAM3 (6) // Parameter 3 register
#define RDMAN_PARAM4 (7) // Parameter 4 register
#define RDMAN_PARAM5 (8) // Parameter 5 register
#define RDMAN_PARAM6 (9) // Parameter 6 register
#define RDMAN_PARAM7 (10) // Parameter 7 register
#define RDMAN_PARAM8 (11) // Parameter 8 register
#define RDMAN_PARAM9 (12) // Parameter 9 register
#define RDMAN_DATA_ADDRCNTR (13) // Counter for ring-down data
#define RDMAN_METADATA_ADDRCNTR (14) // Counter for ring-down metadata
#define RDMAN_PARAM_ADDRCNTR (15) // Counter for parameter data
#define RDMAN_DIVISOR (16) // Ring-down data counter rate divisor
#define RDMAN_NUM_SAMP (17) // Number of samples to collect for ring-down waveform
#define RDMAN_THRESHOLD (18) // Ring-down threshold
#define RDMAN_LOCK_DURATION (19) // Duration (us) for laser frequency to be locked before ring-down is allowed
#define RDMAN_PRECONTROL_DURATION (20) // Duration (us) for laser current to be at nominal value before frequency locking is enabled
#define RDMAN_TIMEOUT_DURATION (21) // Duration (ms) within which ring-down must occur to be valid
#define RDMAN_TUNER_AT_RINGDOWN (22) // Value of tuner at ring-down
#define RDMAN_METADATA_ADDR_AT_RINGDOWN (23) // Metadata address at ring-down

/* Block TWGEN Tuner waveform generator */
#define TWGEN_ACC (0) // Accumulator
#define TWGEN_CS (1) // Control/Status Register
#define TWGEN_CS_RUN_B (0) // Stop/Run bit position
#define TWGEN_CS_RUN_W (1) // Stop/Run bit width
#define TWGEN_CS_CONT_B (1) // Single/Continuous bit position
#define TWGEN_CS_CONT_W (1) // Single/Continuous bit width
#define TWGEN_CS_RESET_B (2) // Reset generator bit position
#define TWGEN_CS_RESET_W (1) // Reset generator bit width
#define TWGEN_CS_TUNE_PZT_B (3) // Tune PZT bit position
#define TWGEN_CS_TUNE_PZT_W (1) // Tune PZT bit width

#define TWGEN_SLOPE_DOWN (2) // Slope in downward direction
#define TWGEN_SLOPE_UP (3) // Slope in upward direction
#define TWGEN_SWEEP_LOW (4) // Lower limit of sweep
#define TWGEN_SWEEP_HIGH (5) // Higher limit of sweep
#define TWGEN_WINDOW_LOW (6) // Lower limit of window
#define TWGEN_WINDOW_HIGH (7) // Higher limit of window
#define TWGEN_PZT_OFFSET (8) // PZT offset

/* Block INJECT Optical injection subsystem */
#define INJECT_CONTROL (0) // Control register
#define INJECT_CONTROL_MODE_B (0) // Manual/Automatic mode bit position
#define INJECT_CONTROL_MODE_W (1) // Manual/Automatic mode bit width
#define INJECT_CONTROL_LASER_SELECT_B (1) // Laser selected bit position
#define INJECT_CONTROL_LASER_SELECT_W (2) // Laser selected bit width
#define INJECT_CONTROL_LASER_CURRENT_ENABLE_B (3) // Laser current enable bit position
#define INJECT_CONTROL_LASER_CURRENT_ENABLE_W (4) // Laser current enable bit width
#define INJECT_CONTROL_LASER1_CURRENT_ENABLE_B (3) // Laser 1 current source bit position
#define INJECT_CONTROL_LASER1_CURRENT_ENABLE_W (1) // Laser 1 current source bit width
#define INJECT_CONTROL_LASER2_CURRENT_ENABLE_B (4) // Laser 2 current source bit position
#define INJECT_CONTROL_LASER2_CURRENT_ENABLE_W (1) // Laser 2 current source bit width
#define INJECT_CONTROL_LASER3_CURRENT_ENABLE_B (5) // Laser 3 current source bit position
#define INJECT_CONTROL_LASER3_CURRENT_ENABLE_W (1) // Laser 3 current source bit width
#define INJECT_CONTROL_LASER4_CURRENT_ENABLE_B (6) // Laser 4 current source bit position
#define INJECT_CONTROL_LASER4_CURRENT_ENABLE_W (1) // Laser 4 current source bit width
#define INJECT_CONTROL_MANUAL_LASER_ENABLE_B (7) // Deasserts short across laser in manual mode bit position
#define INJECT_CONTROL_MANUAL_LASER_ENABLE_W (4) // Deasserts short across laser in manual mode bit width
#define INJECT_CONTROL_MANUAL_LASER1_ENABLE_B (7) // Laser 1 current (in manual mode) bit position
#define INJECT_CONTROL_MANUAL_LASER1_ENABLE_W (1) // Laser 1 current (in manual mode) bit width
#define INJECT_CONTROL_MANUAL_LASER2_ENABLE_B (8) // Laser 2 current (in manual mode) bit position
#define INJECT_CONTROL_MANUAL_LASER2_ENABLE_W (1) // Laser 2 current (in manual mode) bit width
#define INJECT_CONTROL_MANUAL_LASER3_ENABLE_B (9) // Laser 3 current (in manual mode) bit position
#define INJECT_CONTROL_MANUAL_LASER3_ENABLE_W (1) // Laser 3 current (in manual mode) bit width
#define INJECT_CONTROL_MANUAL_LASER4_ENABLE_B (10) // Laser 4 current (in manual mode) bit position
#define INJECT_CONTROL_MANUAL_LASER4_ENABLE_W (1) // Laser 4 current (in manual mode) bit width
#define INJECT_CONTROL_MANUAL_SOA_ENABLE_B (11) // SOA current (in manual mode) bit position
#define INJECT_CONTROL_MANUAL_SOA_ENABLE_W (1) // SOA current (in manual mode) bit width
#define INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B (12) // Enables laser shutdown (in automatic mode) bit position
#define INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W (1) // Enables laser shutdown (in automatic mode) bit width
#define INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B (13) // Enables SOA shutdown (in automatic mode) bit position
#define INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W (1) // Enables SOA shutdown (in automatic mode) bit width

#define INJECT_LASER1_COARSE_CURRENT (1) // Sets coarse current for laser 1
#define INJECT_LASER2_COARSE_CURRENT (2) // Sets coarse current for laser 2
#define INJECT_LASER3_COARSE_CURRENT (3) // Sets coarse current for laser 3
#define INJECT_LASER4_COARSE_CURRENT (4) // Sets coarse current for laser 4
#define INJECT_LASER1_FINE_CURRENT (5) // Sets fine current for laser 1
#define INJECT_LASER2_FINE_CURRENT (6) // Sets fine current for laser 2
#define INJECT_LASER3_FINE_CURRENT (7) // Sets fine current for laser 3
#define INJECT_LASER4_FINE_CURRENT (8) // Sets fine current for laser 4

/* Block WLMSIM Wavelength monitor simulator */
#define WLMSIM_OPTIONS (0) // Options
#define WLMSIM_OPTIONS_INPUT_SEL_B (0) // Input select bit position
#define WLMSIM_OPTIONS_INPUT_SEL_W (1) // Input select bit width

#define WLMSIM_Z0 (1) // Phase angle
#define WLMSIM_RFAC (2) // Reflectivity factor
#define WLMSIM_WFAC (3) // Width factor of simulated spectrum
#define WLMSIM_LASER_TEMP (4) // 
#define WLMSIM_ETA1_OFFSET (5) // Etalon 1 offset
#define WLMSIM_REF1_OFFSET (6) // Reference 1 offset
#define WLMSIM_ETA2_OFFSET (7) // Etalon 2 offset
#define WLMSIM_REF2_OFFSET (8) // Reference 2 offset

/* Block DYNAMICPWM Dynamic PWM for proportional valves */
#define DYNAMICPWM_CS (0) // Control/Status
#define DYNAMICPWM_CS_RUN_B (0) // Stop/Run bit position
#define DYNAMICPWM_CS_RUN_W (1) // Stop/Run bit width
#define DYNAMICPWM_CS_CONT_B (1) // Single/Continuous bit position
#define DYNAMICPWM_CS_CONT_W (1) // Single/Continuous bit width
#define DYNAMICPWM_CS_PWM_ENABLE_B (2) // PWM enable bit position
#define DYNAMICPWM_CS_PWM_ENABLE_W (1) // PWM enable bit width
#define DYNAMICPWM_CS_PWM_OUT_B (3) // PWM output bit position
#define DYNAMICPWM_CS_PWM_OUT_W (1) // PWM output bit width

#define DYNAMICPWM_DELTA (1) // Pulse width change per update
#define DYNAMICPWM_HIGH (2) // Upper limit of dither waveform
#define DYNAMICPWM_LOW (3) // Lower limit of dither waveform
#define DYNAMICPWM_SLOPE (4) // Slope of dither waveform

/* FPGA map indices */

#define FPGA_KERNEL (0) // Kernel registers
#define FPGA_PWM_LASER1 (8) // Laser 1 TEC pulse width modulator registers
#define FPGA_PWM_LASER2 (10) // Laser 2 TEC pulse width modulator registers
#define FPGA_PWM_LASER3 (12) // Laser 3 TEC pulse width modulator registers
#define FPGA_PWM_LASER4 (14) // Laser 4 TEC pulse width modulator registers
#define FPGA_PWM_WARMBOX (16) // Warm box TEC pulse width modulator registers
#define FPGA_PWM_HOTBOX (18) // Hot box TEC pulse width modulator registers
#define FPGA_PWM_HEATER (20) // Heater pulse width modulator registers
#define FPGA_RDSIM (22) // Ringdown simulator registers
#define FPGA_LASERLOCKER (30) // Laser frequency locker registers
#define FPGA_RDMAN (58) // Ringdown manager registers
#define FPGA_TWGEN (82) // Tuner waveform generator
#define FPGA_INJECT (91) // Optical Injection Subsystem
#define FPGA_WLMSIM (100) // WLM Simulator
#define FPGA_DYNAMICPWM_INLET (109) // Inlet proportional valve dynamic PWM
#define FPGA_DYNAMICPWM_OUTLET (114) // Outlet proportional valve dynamic PWM

/* Environment addresses */

#define LASER1_TEMP_MODEL_ENV (0)
#define LASER2_TEMP_MODEL_ENV (27)
#define LASER3_TEMP_MODEL_ENV (54)
#define LASER4_TEMP_MODEL_ENV (81)

/* Action codes */
#define ACTION_WRITE_BLOCK (1)
#define ACTION_SET_TIMESTAMP (2)
#define ACTION_GET_TIMESTAMP (3)
#define ACTION_INIT_RUNQUEUE (4)
#define ACTION_TEST_SCHEDULER (5)
#define ACTION_STREAM_REGISTER_ASFLOAT (6)
#define ACTION_STREAM_FPGA_REGISTER_ASFLOAT (7)
#define ACTION_RESISTANCE_TO_TEMPERATURE (8)
#define ACTION_TEMP_CNTRL_SET_COMMAND (9)
#define ACTION_APPLY_PID_STEP (10)
#define ACTION_TEMP_CNTRL_LASER1_INIT (11)
#define ACTION_TEMP_CNTRL_LASER1_STEP (12)
#define ACTION_TEMP_CNTRL_LASER2_INIT (13)
#define ACTION_TEMP_CNTRL_LASER2_STEP (14)
#define ACTION_TEMP_CNTRL_LASER3_INIT (15)
#define ACTION_TEMP_CNTRL_LASER3_STEP (16)
#define ACTION_TEMP_CNTRL_LASER4_INIT (17)
#define ACTION_TEMP_CNTRL_LASER4_STEP (18)
#define ACTION_FLOAT_REGISTER_TO_FPGA (19)
#define ACTION_FPGA_TO_FLOAT_REGISTER (20)
#define ACTION_INT_TO_FPGA (21)
#define ACTION_CURRENT_CNTRL_LASER1_INIT (22)
#define ACTION_CURRENT_CNTRL_LASER1_STEP (23)
#define ACTION_CURRENT_CNTRL_LASER2_INIT (24)
#define ACTION_CURRENT_CNTRL_LASER2_STEP (25)
#define ACTION_CURRENT_CNTRL_LASER3_INIT (26)
#define ACTION_CURRENT_CNTRL_LASER3_STEP (27)
#define ACTION_CURRENT_CNTRL_LASER4_INIT (28)
#define ACTION_CURRENT_CNTRL_LASER4_STEP (29)
#define ACTION_TEMP_CNTRL_WARM_BOX_INIT (30)
#define ACTION_TEMP_CNTRL_WARM_BOX_STEP (31)
#define ACTION_TEMP_CNTRL_CAVITY_INIT (32)
#define ACTION_TEMP_CNTRL_CAVITY_STEP (33)
#define ACTION_HEATER_CNTRL_INIT (34)
#define ACTION_HEATER_CNTRL_STEP (35)
#define ACTION_TUNER_CNTRL_INIT (36)
#define ACTION_TUNER_CNTRL_STEP (37)
#define ACTION_SPECTRUM_CNTRL_INIT (38)
#define ACTION_SPECTRUM_CNTRL_STEP (39)
#define ACTION_ENV_CHECKER (40)
#define ACTION_WB_INV_CACHE (41)
#define ACTION_WB_CACHE (42)
#define ACTION_SCHEDULER_HEARTBEAT (43)
#define ACTION_SENTRY_INIT (44)
#define ACTION_VALVE_CNTRL_INIT (45)
#define ACTION_VALVE_CNTRL_STEP (46)
#define ACTION_MODIFY_VALVE_PUMP_TEC (47)
#define ACTION_PULSE_GENERATOR (48)
#define ACTION_FILTER (49)
#define ACTION_DS1631_READTEMP (50)
#define ACTION_LASER_TEC_IMON (51)
#define ACTION_READ_LASER_TEC_MONITORS (52)
#define ACTION_READ_LASER_THERMISTOR_RESISTANCE (53)
#define ACTION_READ_ETALON_THERMISTOR_RESISTANCE (54)
#define ACTION_READ_WARM_BOX_THERMISTOR_RESISTANCE (55)
#define ACTION_READ_WARM_BOX_HEATSINK_THERMISTOR_RESISTANCE (56)
#define ACTION_READ_CAVITY_THERMISTOR_RESISTANCE (57)
#define ACTION_READ_HOT_BOX_HEATSINK_THERMISTOR_RESISTANCE (58)
#define ACTION_READ_LASER_CURRENT (59)
#define ACTION_UPDATE_WLMSIM_LASER_TEMP (60)
#define ACTION_SIMULATE_LASER_CURRENT_READING (61)
#define ACTION_READ_CAVITY_PRESSURE_ADC (62)
#define ACTION_READ_AMBIENT_PRESSURE_ADC (63)
#define ACTION_ADC_TO_PRESSURE (64)
#define ACTION_SET_INLET_VALVE (65)
#define ACTION_SET_OUTLET_VALVE (66)
#endif
