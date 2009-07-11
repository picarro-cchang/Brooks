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

/* Constant definitions */
// Number of points in controller waveforms
#define CONTROLLER_WAVEFORM_POINTS (1000)
// Base address for DSP shared memory
#define SHAREDMEM_ADDRESS (0x20000)
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
// Size (in 32-bit ints) of DSP shared memory
#define SHAREDMEM_SIZE (0x4000)
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
#define HOST_REGION_SIZE ((SHAREDMEM_SIZE - HOST_OFFSET))
// Number of bits in EMIF address
#define EMIF_ADDR_WIDTH (20)
// Number of bits in EMIF address
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
#define RDMEM_PARAM_WIDTH (16)
// Number of address bits reserved for a ringdown region in each bank
#define RDMEM_RESERVED_BANK_ADDR_WIDTH (12)
// Number of address bits for one bank of data
#define DATA_BANK_ADDR_WIDTH (12)
// Number of address bits for one bank of metadata
#define META_BANK_ADDR_WIDTH (12)
// Number of address bits for one bank of parameters
#define PARAM_BANK_ADDR_WIDTH (6)
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
    uint32 warmChamberTemp;
    uint32 hotChamberTecHeatsinkTemp;
    uint32 warmChamberTecHeatsinkTemp;
    uint32 laser1Temp;
    uint32 laser2Temp;
    uint32 laserCurrent;
    uint32 cavityPressure;
    uint32 inletPressure;
    uint32 outletPressure;
    uint16 customDataArray[16];
} DIAG_EventLogStruct;

typedef struct {
    DataType lockValue;
    float ratio1;
    float ratio2;
    float correctedAbsorbance;
    float uncorrectedAbsorbance;
    uint16 tunerValue;
    uint16 pztValue;
    uint16 etalonAndLaserSelectAndFitStatus;
    uint16 schemeStatusAndSchemeTableIndex;
    uint32 msTicks;
    uint16 count;
    uint16 subSchemeId;
    uint16 schemeIndex;
    uint16 fineLaserCurrent;
    DataType lockSetpoint;
} RD_ResultsEntryType;

typedef struct {
    long long timestamp;
    uint32 streamNum;
    DataType value;
} SensorEntryType;

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
    float num[9];
    float den[9];
    float state[8];
} FilterEnvType;

typedef enum {
    STREAM_Laser1Temp = 0, // 
    STREAM_Laser2Temp = 1, // 
    STREAM_Laser3Temp = 2, // 
    STREAM_Laser4Temp = 3, // 
    STREAM_EtalonTemp = 4, // 
    STREAM_WarmChamberTemp = 5, // 
    STREAM_WarmChamberTecTemp = 6, // 
    STREAM_CavityTemp = 7, // 
    STREAM_HotChamberTecTemp = 8, // 
    STREAM_DasTemp = 9, // 
    STREAM_Etalon1 = 10, // 
    STREAM_Reference1 = 11, // 
    STREAM_Etalon2 = 12, // 
    STREAM_Reference2 = 13, // 
    STREAM_Laser1Current = 14, // 
    STREAM_Laser2Current = 15, // 
    STREAM_Laser3Current = 16, // 
    STREAM_Laser4Current = 17, // 
    STREAM_CavityPressure = 18, // 
    STREAM_AmbientPressure = 19, // 
    STREAM_InletPressure = 20, // 
    STREAM_OutletPressure = 21, // 
    STREAM_Laser1Tec = 22, // 
    STREAM_Laser2Tec = 23, // 
    STREAM_Laser3Tec = 24, // 
    STREAM_Laser4Tec = 25, // 
    STREAM_WarmChamberTec = 26, // 
    STREAM_HotChamberTec = 27, // 
    STREAM_HotChamberHeater = 28, // 
    STREAM_InletValve = 29, // 
    STREAM_OutletValve = 30, // 
    STREAM_ValveMask = 31 // 
} STREAM_MemberType;

typedef enum {
    LOGICPORT_CLOCK_PERIOD_20ns = 0, // 20 ns
    LOGICPORT_CLOCK_PERIOD_40ns = 1, // 40 ns
    LOGICPORT_CLOCK_PERIOD_80ns = 2, // 80 ns
    LOGICPORT_CLOCK_PERIOD_160ns = 3, // 160 ns
    LOGICPORT_CLOCK_PERIOD_320ns = 4, // 320 ns
    LOGICPORT_CLOCK_PERIOD_640ns = 5, // 640 ns
    LOGICPORT_CLOCK_PERIOD_1280ns = 6, // 1.28 us
    LOGICPORT_CLOCK_PERIOD_2560ns = 7, // 2.56 us
    LOGICPORT_CLOCK_PERIOD_5120ns = 8, // 5.12 us
    LOGICPORT_CLOCK_PERIOD_10240ns = 9, // 10.24 us
    LOGICPORT_CLOCK_PERIOD_20480ns = 10, // 20.48 us
    LOGICPORT_CLOCK_PERIOD_40960ns = 11, // 40.96 us
    LOGICPORT_CLOCK_PERIOD_81920ns = 12, // 81.92 us
    LOGICPORT_CLOCK_PERIOD_163840ns = 13, // 163.8 us
    LOGICPORT_CLOCK_PERIOD_327680ns = 14, // 327.7 us
    LOGICPORT_CLOCK_PERIOD_655360ns = 15, // 655.4 us
    LOGICPORT_CLOCK_PERIOD_1310720ns = 16, // 1.311 ms
    LOGICPORT_CLOCK_PERIOD_2621440ns = 17, // 2.621 ms
    LOGICPORT_CLOCK_PERIOD_5242880ns = 18, // 5.243 ms
    LOGICPORT_CLOCK_PERIOD_10485760ns = 19, // 10.49 ms
    LOGICPORT_CLOCK_PERIOD_20971520ns = 20, // 20.97 ms
    LOGICPORT_CLOCK_PERIOD_41943040ns = 21, // 41.94 ms
    LOGICPORT_CLOCK_PERIOD_83886080ns = 22, // 83.39 ms
    LOGICPORT_CLOCK_PERIOD_167772160ns = 23, // 167.8 ms
    LOGICPORT_CLOCK_PERIOD_335544320ns = 24, // 335.5 ms
    LOGICPORT_CLOCK_PERIOD_671088640ns = 25, // 671.1 ms
    LOGICPORT_CLOCK_PERIOD_1342177280ns = 26, // 1.342 s
    LOGICPORT_CLOCK_PERIOD_2684354560ns = 27, // 2.684 s
    LOGICPORT_CLOCK_PERIOD_5368709120ns = 28 // 5.368 s
} LOGICPORT_CLOCK_PERIOD_Type;

typedef enum {
    LOGICPORT_SOURCE_RD_ADC = 0, // Ringdown ADC
    LOGICPORT_SOURCE_TUNER = 1 // Tuner Value
} LOGICPORT_SOURCE_Type;

typedef enum {
    TEMP_CNTRL_DisabledState = 0, // Controller Disabled
    TEMP_CNTRL_EnabledState = 1, // Controller Enabled
    TEMP_CNTRL_SuspendedState = 2, // Controller Suspended
    TEMP_CNTRL_SweepingState = 3, // Continuous Sweeping
    TEMP_CNTRL_SendPrbsState = 4, // Sending PRBS
    TEMP_CNTRL_ManualState = 5 // Manual Control
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

/* Definitions for COMM_STATUS_BITMASK */
#define COMM_STATUS_CompleteMask (0x1)
#define COMM_STATUS_BadCrcMask (0x2)
#define COMM_STATUS_BadSequenceNumberMask (0x4)
#define COMM_STATUS_BadArgumentsMask (0x8)
#define COMM_STATUS_SequenceNumberMask (0xFF000000)
#define COMM_STATUS_ReturnValueMask (0x00FFFF00)
#define COMM_STATUS_SequenceNumberShift (24)
#define COMM_STATUS_ReturnValueShift (8)

/* Register definitions */
#define INTERFACE_NUMBER_OF_REGISTERS (231)

#define NOOP_REGISTER (0)
#define VERIFY_INIT_REGISTER (1)
#define COMM_STATUS_REGISTER (2)
#define TIMESTAMP_LSB_REGISTER (3)
#define TIMESTAMP_MSB_REGISTER (4)
#define SCHEDULER_CONTROL_REGISTER (5)
#define LOGICPORT_CLOCK_PERIOD_REGISTER (6)
#define LOGICPORT_SOURCE_REGISTER (7)
#define RD_IRQ_COUNT_REGISTER (8)
#define ACQ_DONE_COUNT_REGISTER (9)
#define DAS_TEMPERATURE_REGISTER (10)
#define LASER_TEC_MONITOR_TEMPERATURE_REGISTER (11)
#define CONVERSION_LASER1_THERM_CONSTA_REGISTER (12)
#define CONVERSION_LASER1_THERM_CONSTB_REGISTER (13)
#define CONVERSION_LASER1_THERM_CONSTC_REGISTER (14)
#define LASER1_RESISTANCE_REGISTER (15)
#define LASER1_TEMPERATURE_REGISTER (16)
#define LASER1_THERMISTOR_ADC_REGISTER (17)
#define LASER1_TEC_REGISTER (18)
#define LASER1_MANUAL_TEC_REGISTER (19)
#define LASER1_TEMP_CNTRL_STATE_REGISTER (20)
#define LASER1_TEMP_CNTRL_LOCK_STATUS_REGISTER (21)
#define LASER1_TEMP_CNTRL_SETPOINT_REGISTER (22)
#define LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER (23)
#define LASER1_TEMP_CNTRL_TOLERANCE_REGISTER (24)
#define LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER (25)
#define LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER (26)
#define LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER (27)
#define LASER1_TEMP_CNTRL_H_REGISTER (28)
#define LASER1_TEMP_CNTRL_K_REGISTER (29)
#define LASER1_TEMP_CNTRL_TI_REGISTER (30)
#define LASER1_TEMP_CNTRL_TD_REGISTER (31)
#define LASER1_TEMP_CNTRL_B_REGISTER (32)
#define LASER1_TEMP_CNTRL_C_REGISTER (33)
#define LASER1_TEMP_CNTRL_N_REGISTER (34)
#define LASER1_TEMP_CNTRL_S_REGISTER (35)
#define LASER1_TEMP_CNTRL_FFWD_REGISTER (36)
#define LASER1_TEMP_CNTRL_AMIN_REGISTER (37)
#define LASER1_TEMP_CNTRL_AMAX_REGISTER (38)
#define LASER1_TEMP_CNTRL_IMAX_REGISTER (39)
#define LASER1_TEC_PRBS_GENPOLY_REGISTER (40)
#define LASER1_TEC_PRBS_AMPLITUDE_REGISTER (41)
#define LASER1_TEC_PRBS_MEAN_REGISTER (42)
#define LASER1_TEC_MONITOR_REGISTER (43)
#define LASER1_CURRENT_CNTRL_STATE_REGISTER (44)
#define LASER1_MANUAL_COARSE_CURRENT_REGISTER (45)
#define LASER1_MANUAL_FINE_CURRENT_REGISTER (46)
#define LASER1_CURRENT_SWEEP_MIN_REGISTER (47)
#define LASER1_CURRENT_SWEEP_MAX_REGISTER (48)
#define LASER1_CURRENT_SWEEP_INCR_REGISTER (49)
#define LASER1_CURRENT_MONITOR_REGISTER (50)
#define CONVERSION_LASER2_THERM_CONSTA_REGISTER (51)
#define CONVERSION_LASER2_THERM_CONSTB_REGISTER (52)
#define CONVERSION_LASER2_THERM_CONSTC_REGISTER (53)
#define LASER2_RESISTANCE_REGISTER (54)
#define LASER2_TEMPERATURE_REGISTER (55)
#define LASER2_THERMISTOR_ADC_REGISTER (56)
#define LASER2_TEC_REGISTER (57)
#define LASER2_MANUAL_TEC_REGISTER (58)
#define LASER2_TEMP_CNTRL_STATE_REGISTER (59)
#define LASER2_TEMP_CNTRL_LOCK_STATUS_REGISTER (60)
#define LASER2_TEMP_CNTRL_SETPOINT_REGISTER (61)
#define LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER (62)
#define LASER2_TEMP_CNTRL_TOLERANCE_REGISTER (63)
#define LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER (64)
#define LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER (65)
#define LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER (66)
#define LASER2_TEMP_CNTRL_H_REGISTER (67)
#define LASER2_TEMP_CNTRL_K_REGISTER (68)
#define LASER2_TEMP_CNTRL_TI_REGISTER (69)
#define LASER2_TEMP_CNTRL_TD_REGISTER (70)
#define LASER2_TEMP_CNTRL_B_REGISTER (71)
#define LASER2_TEMP_CNTRL_C_REGISTER (72)
#define LASER2_TEMP_CNTRL_N_REGISTER (73)
#define LASER2_TEMP_CNTRL_S_REGISTER (74)
#define LASER2_TEMP_CNTRL_FFWD_REGISTER (75)
#define LASER2_TEMP_CNTRL_AMIN_REGISTER (76)
#define LASER2_TEMP_CNTRL_AMAX_REGISTER (77)
#define LASER2_TEMP_CNTRL_IMAX_REGISTER (78)
#define LASER2_TEC_PRBS_GENPOLY_REGISTER (79)
#define LASER2_TEC_PRBS_AMPLITUDE_REGISTER (80)
#define LASER2_TEC_PRBS_MEAN_REGISTER (81)
#define LASER2_TEC_MONITOR_REGISTER (82)
#define LASER2_CURRENT_CNTRL_STATE_REGISTER (83)
#define LASER2_MANUAL_COARSE_CURRENT_REGISTER (84)
#define LASER2_MANUAL_FINE_CURRENT_REGISTER (85)
#define LASER2_CURRENT_SWEEP_MIN_REGISTER (86)
#define LASER2_CURRENT_SWEEP_MAX_REGISTER (87)
#define LASER2_CURRENT_SWEEP_INCR_REGISTER (88)
#define LASER2_CURRENT_MONITOR_REGISTER (89)
#define CONVERSION_LASER3_THERM_CONSTA_REGISTER (90)
#define CONVERSION_LASER3_THERM_CONSTB_REGISTER (91)
#define CONVERSION_LASER3_THERM_CONSTC_REGISTER (92)
#define LASER3_RESISTANCE_REGISTER (93)
#define LASER3_TEMPERATURE_REGISTER (94)
#define LASER3_THERMISTOR_ADC_REGISTER (95)
#define LASER3_TEC_REGISTER (96)
#define LASER3_MANUAL_TEC_REGISTER (97)
#define LASER3_TEMP_CNTRL_STATE_REGISTER (98)
#define LASER3_TEMP_CNTRL_LOCK_STATUS_REGISTER (99)
#define LASER3_TEMP_CNTRL_SETPOINT_REGISTER (100)
#define LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER (101)
#define LASER3_TEMP_CNTRL_TOLERANCE_REGISTER (102)
#define LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER (103)
#define LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER (104)
#define LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER (105)
#define LASER3_TEMP_CNTRL_H_REGISTER (106)
#define LASER3_TEMP_CNTRL_K_REGISTER (107)
#define LASER3_TEMP_CNTRL_TI_REGISTER (108)
#define LASER3_TEMP_CNTRL_TD_REGISTER (109)
#define LASER3_TEMP_CNTRL_B_REGISTER (110)
#define LASER3_TEMP_CNTRL_C_REGISTER (111)
#define LASER3_TEMP_CNTRL_N_REGISTER (112)
#define LASER3_TEMP_CNTRL_S_REGISTER (113)
#define LASER3_TEMP_CNTRL_FFWD_REGISTER (114)
#define LASER3_TEMP_CNTRL_AMIN_REGISTER (115)
#define LASER3_TEMP_CNTRL_AMAX_REGISTER (116)
#define LASER3_TEMP_CNTRL_IMAX_REGISTER (117)
#define LASER3_TEC_PRBS_GENPOLY_REGISTER (118)
#define LASER3_TEC_PRBS_AMPLITUDE_REGISTER (119)
#define LASER3_TEC_PRBS_MEAN_REGISTER (120)
#define LASER3_TEC_MONITOR_REGISTER (121)
#define LASER3_CURRENT_CNTRL_STATE_REGISTER (122)
#define LASER3_MANUAL_COARSE_CURRENT_REGISTER (123)
#define LASER3_MANUAL_FINE_CURRENT_REGISTER (124)
#define LASER3_CURRENT_SWEEP_MIN_REGISTER (125)
#define LASER3_CURRENT_SWEEP_MAX_REGISTER (126)
#define LASER3_CURRENT_SWEEP_INCR_REGISTER (127)
#define LASER3_CURRENT_MONITOR_REGISTER (128)
#define CONVERSION_LASER4_THERM_CONSTA_REGISTER (129)
#define CONVERSION_LASER4_THERM_CONSTB_REGISTER (130)
#define CONVERSION_LASER4_THERM_CONSTC_REGISTER (131)
#define LASER4_RESISTANCE_REGISTER (132)
#define LASER4_TEMPERATURE_REGISTER (133)
#define LASER4_THERMISTOR_ADC_REGISTER (134)
#define LASER4_TEC_REGISTER (135)
#define LASER4_MANUAL_TEC_REGISTER (136)
#define LASER4_TEMP_CNTRL_STATE_REGISTER (137)
#define LASER4_TEMP_CNTRL_LOCK_STATUS_REGISTER (138)
#define LASER4_TEMP_CNTRL_SETPOINT_REGISTER (139)
#define LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER (140)
#define LASER4_TEMP_CNTRL_TOLERANCE_REGISTER (141)
#define LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER (142)
#define LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER (143)
#define LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER (144)
#define LASER4_TEMP_CNTRL_H_REGISTER (145)
#define LASER4_TEMP_CNTRL_K_REGISTER (146)
#define LASER4_TEMP_CNTRL_TI_REGISTER (147)
#define LASER4_TEMP_CNTRL_TD_REGISTER (148)
#define LASER4_TEMP_CNTRL_B_REGISTER (149)
#define LASER4_TEMP_CNTRL_C_REGISTER (150)
#define LASER4_TEMP_CNTRL_N_REGISTER (151)
#define LASER4_TEMP_CNTRL_S_REGISTER (152)
#define LASER4_TEMP_CNTRL_FFWD_REGISTER (153)
#define LASER4_TEMP_CNTRL_AMIN_REGISTER (154)
#define LASER4_TEMP_CNTRL_AMAX_REGISTER (155)
#define LASER4_TEMP_CNTRL_IMAX_REGISTER (156)
#define LASER4_TEC_PRBS_GENPOLY_REGISTER (157)
#define LASER4_TEC_PRBS_AMPLITUDE_REGISTER (158)
#define LASER4_TEC_PRBS_MEAN_REGISTER (159)
#define LASER4_TEC_MONITOR_REGISTER (160)
#define LASER4_CURRENT_CNTRL_STATE_REGISTER (161)
#define LASER4_MANUAL_COARSE_CURRENT_REGISTER (162)
#define LASER4_MANUAL_FINE_CURRENT_REGISTER (163)
#define LASER4_CURRENT_SWEEP_MIN_REGISTER (164)
#define LASER4_CURRENT_SWEEP_MAX_REGISTER (165)
#define LASER4_CURRENT_SWEEP_INCR_REGISTER (166)
#define LASER4_CURRENT_MONITOR_REGISTER (167)
#define CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER (168)
#define CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER (169)
#define CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER (170)
#define HOT_BOX_HEATSINK_RESISTANCE_REGISTER (171)
#define HOT_BOX_HEATSINK_TEMPERATURE_REGISTER (172)
#define HOT_BOX_HEATSINK_ADC_REGISTER (173)
#define CONVERSION_CAVITY_THERM_CONSTA_REGISTER (174)
#define CONVERSION_CAVITY_THERM_CONSTB_REGISTER (175)
#define CONVERSION_CAVITY_THERM_CONSTC_REGISTER (176)
#define CAVITY_RESISTANCE_REGISTER (177)
#define CAVITY_TEMPERATURE_REGISTER (178)
#define CAVITY_THERMISTOR_ADC_REGISTER (179)
#define CAVITY_TEC_REGISTER (180)
#define CAVITY_MANUAL_TEC_REGISTER (181)
#define CAVITY_TEMP_CNTRL_STATE_REGISTER (182)
#define CAVITY_TEMP_CNTRL_LOCK_STATUS_REGISTER (183)
#define CAVITY_TEMP_CNTRL_SETPOINT_REGISTER (184)
#define CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER (185)
#define CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER (186)
#define CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER (187)
#define CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER (188)
#define CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER (189)
#define CAVITY_TEMP_CNTRL_H_REGISTER (190)
#define CAVITY_TEMP_CNTRL_K_REGISTER (191)
#define CAVITY_TEMP_CNTRL_TI_REGISTER (192)
#define CAVITY_TEMP_CNTRL_TD_REGISTER (193)
#define CAVITY_TEMP_CNTRL_B_REGISTER (194)
#define CAVITY_TEMP_CNTRL_C_REGISTER (195)
#define CAVITY_TEMP_CNTRL_N_REGISTER (196)
#define CAVITY_TEMP_CNTRL_S_REGISTER (197)
#define CAVITY_TEMP_CNTRL_FFWD_REGISTER (198)
#define CAVITY_TEMP_CNTRL_AMIN_REGISTER (199)
#define CAVITY_TEMP_CNTRL_AMAX_REGISTER (200)
#define CAVITY_TEMP_CNTRL_IMAX_REGISTER (201)
#define CAVITY_TEC_PRBS_GENPOLY_REGISTER (202)
#define CAVITY_TEC_PRBS_AMPLITUDE_REGISTER (203)
#define CAVITY_TEC_PRBS_MEAN_REGISTER (204)
#define CAVITY_MAX_HEATSINK_TEMP_REGISTER (205)
#define HEATER_CNTRL_STATE_REGISTER (206)
#define HEATER_CNTRL_GAIN_REGISTER (207)
#define HEATER_CNTRL_QUANTIZE_REGISTER (208)
#define HEATER_CNTRL_UBIAS_SLOPE_REGISTER (209)
#define HEATER_CNTRL_UBIAS_OFFSET_REGISTER (210)
#define HEATER_CNTRL_MARK_MIN_REGISTER (211)
#define HEATER_CNTRL_MARK_MAX_REGISTER (212)
#define HEATER_CNTRL_MANUAL_MARK_REGISTER (213)
#define HEATER_CNTRL_MARK_REGISTER (214)
#define TUNER_SWEEP_RAMP_HIGH_REGISTER (215)
#define TUNER_SWEEP_RAMP_LOW_REGISTER (216)
#define TUNER_WINDOW_RAMP_HIGH_REGISTER (217)
#define TUNER_WINDOW_RAMP_LOW_REGISTER (218)
#define TUNER_UP_SLOPE_REGISTER (219)
#define TUNER_DOWN_SLOPE_REGISTER (220)
#define RD_MINLOSS_REGISTER (221)
#define RD_MAXLOSS_REGISTER (222)
#define RD_LATEST_LOSS_REGISTER (223)
#define RD_IMPROVEMENT_STEPS_REGISTER (224)
#define RD_START_SAMPLE_REGISTER (225)
#define RD_FRACTIONAL_THRESHOLD_REGISTER (226)
#define RD_ABSOLUTE_THRESHOLD_REGISTER (227)
#define RD_NUMBER_OF_SAMPLES_REGISTER (228)
#define RD_NUMBER_OF_POINTS_REGISTER (229)
#define RD_MAX_E_FOLDINGS_REGISTER (230)

/* FPGA block definitions */

/* Block KERNEL Kernel */
#define KERNEL_MAGIC_CODE (0) // Code indicating FPGA is programmed
#define KERNEL_RESET (1) // Used to reset Cypress FX2
#define KERNEL_GPREG_1 (2) // General purpose register

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
#define RDSIM_TUNER_CENTER (0) // Tuner value around which cavity fills
#define RDSIM_TUNER_WINDOW_HALF_WIDTH (1) // Half-width of tuner window within which cavity fills
#define RDSIM_FILLING_RATE (2) // Rate of increase of accumulator value during filling
#define RDSIM_DECAY (3) // Exponential decay of accumulator when not filling
#define RDSIM_ACCUMULATOR (4) // Simulated ringdown value

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
#define LASERLOCKER_CS_TUNING_OFFSET_SEL_B (6) // Tuner offset from register/port bit position
#define LASERLOCKER_CS_TUNING_OFFSET_SEL_W (1) // Tuner offset from register/port bit width
#define LASERLOCKER_CS_LASER_FREQ_OK_B (7) // Laser frequency in window bit position
#define LASERLOCKER_CS_LASER_FREQ_OK_W (1) // Laser frequency in window bit width
#define LASERLOCKER_CS_CURRENT_OK_B (8) // Current calculation complete bit position
#define LASERLOCKER_CS_CURRENT_OK_W (1) // Current calculation complete bit width

#define LASERLOCKER_ETA1 (1) // Etalon 1 reading
#define LASERLOCKER_REF1 (2) // Reference 1 reading
#define LASERLOCKER_ETA2 (3) // Etalon 2 reading
#define LASERLOCKER_REF2 (4) // Reference 2 reading
#define LASERLOCKER_ETA1_DARK (5) // Etalon 1 dark reading
#define LASERLOCKER_REF1_DARK (6) // Reference 1 dark reading
#define LASERLOCKER_ETA2_DARK (7) // Etalon 2 dark reading
#define LASERLOCKER_REF2_DARK (8) // Reference 2 dark reading
#define LASERLOCKER_ETA1_OFFSET (9) // Etalon 1 offset
#define LASERLOCKER_REF1_OFFSET (10) // Reference 1 offset
#define LASERLOCKER_ETA2_OFFSET (11) // Etalon 2 offset
#define LASERLOCKER_REF2_OFFSET (12) // Reference 2 offset
#define LASERLOCKER_RATIO1 (13) // Ratio 1
#define LASERLOCKER_RATIO2 (14) // Ratio 2
#define LASERLOCKER_RATIO1_CENTER (15) // Ratio 1 ellipse center
#define LASERLOCKER_RATIO1_MULTIPLIER (16) // Ratio 1 multiplier
#define LASERLOCKER_RATIO2_CENTER (17) // Ratio 2 ellipse center
#define LASERLOCKER_RATIO2_MULTIPLIER (18) // Ratio 2 multiplier
#define LASERLOCKER_TUNING_OFFSET (19) // Error offset to shift frequency
#define LASERLOCKER_LOCK_ERROR (20) // Locker loop error
#define LASERLOCKER_WM_LOCK_WINDOW (21) // Lock window
#define LASERLOCKER_WM_INT_GAIN (22) // Locker integral gain
#define LASERLOCKER_WM_PROP_GAIN (23) // Locker proportional gain
#define LASERLOCKER_WM_DERIV_GAIN (24) // Locker derivative gain
#define LASERLOCKER_FINE_CURRENT (25) // Fine laser current
#define LASERLOCKER_CYCLE_COUNTER (26) // Cycle counter

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
#define RDMAN_CONTROL_LOCK_ENABLE_B (4) // Enable frequency locking bit position
#define RDMAN_CONTROL_LOCK_ENABLE_W (1) // Enable frequency locking bit width
#define RDMAN_CONTROL_UP_SLOPE_ENABLE_B (5) // Allow ring-down on positive tuner slope bit position
#define RDMAN_CONTROL_UP_SLOPE_ENABLE_W (1) // Allow ring-down on positive tuner slope bit width
#define RDMAN_CONTROL_DOWN_SLOPE_ENABLE_B (6) // Allow ring-down on negative tuner slope bit position
#define RDMAN_CONTROL_DOWN_SLOPE_ENABLE_W (1) // Allow ring-down on negative tuner slope bit width
#define RDMAN_CONTROL_BANK0_CLEAR_B (7) // Mark bank 0 available for write bit position
#define RDMAN_CONTROL_BANK0_CLEAR_W (1) // Mark bank 0 available for write bit width
#define RDMAN_CONTROL_BANK1_CLEAR_B (8) // Mark bank 1 available for write bit position
#define RDMAN_CONTROL_BANK1_CLEAR_W (1) // Mark bank 1 available for write bit width
#define RDMAN_CONTROL_RD_IRQ_ACK_B (9) // Acknowledge ring-down interrupt bit position
#define RDMAN_CONTROL_RD_IRQ_ACK_W (1) // Acknowledge ring-down interrupt bit width
#define RDMAN_CONTROL_ACQ_DONE_ACK_B (10) // Acknowledge data acquired interrupt bit position
#define RDMAN_CONTROL_ACQ_DONE_ACK_W (1) // Acknowledge data acquired interrupt bit width

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

#define RDMAN_PARAM0 (2) // Parameter 0 register
#define RDMAN_PARAM1 (3) // Parameter 1 register
#define RDMAN_PARAM2 (4) // Parameter 2 register
#define RDMAN_PARAM3 (5) // Parameter 3 register
#define RDMAN_PARAM4 (6) // Parameter 4 register
#define RDMAN_PARAM5 (7) // Parameter 5 register
#define RDMAN_PARAM6 (8) // Parameter 6 register
#define RDMAN_PARAM7 (9) // Parameter 7 register
#define RDMAN_DATA_ADDRCNTR (10) // Counter for ring-down data
#define RDMAN_METADATA_ADDRCNTR (11) // Counter for ring-down metadata
#define RDMAN_PARAM_ADDRCNTR (12) // Counter for parameter data
#define RDMAN_DIVISOR (13) // Ring-down data counter rate divisor
#define RDMAN_NUM_SAMP (14) // Number of samples to collect for ring-down waveform
#define RDMAN_THRESHOLD (15) // Ring-down threshold
#define RDMAN_LOCK_DURATION (16) // Duration (us) for laser frequency to be locked before ring-down is allowed
#define RDMAN_PRECONTROL_DURATION (17) // Duration (us) for laser current to be at nominal value before frequency locking is enabled
#define RDMAN_TIMEOUT_DURATION (18) // Duration (ms) within which ring-down must occur to be valid
#define RDMAN_TUNER_AT_RINGDOWN (19) // Value of tuner at ring-down
#define RDMAN_METADATA_ADDR_AT_RINGDOWN (20) // Metadata address at ring-down

/* Block TWGEN Tuner waveform generator */
#define TWGEN_ACC (0) // Accumulator
#define TWGEN_CS (1) // Control/Status Register
#define TWGEN_CS_RUN_B (0) // STOP/RUN bit position
#define TWGEN_CS_RUN_W (1) // STOP/RUN bit width
#define TWGEN_CS_CONT_B (1) // SINGLE/CONTINUOUS bit position
#define TWGEN_CS_CONT_W (1) // SINGLE/CONTINUOUS bit width
#define TWGEN_CS_RESET_B (2) // Reset generator bit position
#define TWGEN_CS_RESET_W (1) // Reset generator bit width

#define TWGEN_SLOPE_DOWN (2) // Slope in downward direction
#define TWGEN_SLOPE_UP (3) // Slope in upward direction
#define TWGEN_SWEEP_LOW (4) // Lower limit of sweep
#define TWGEN_SWEEP_HIGH (5) // Higher limit of sweep
#define TWGEN_WINDOW_LOW (6) // Lower limit of window
#define TWGEN_WINDOW_HIGH (7) // Higher limit of window

/* Block INJECT Optical injection subsystem */
#define INJECT_CONTROL (0) // Control register
#define INJECT_CONTROL_MODE_B (0) // Manual/Automatic mode bit position
#define INJECT_CONTROL_MODE_W (1) // Manual/Automatic mode bit width
#define INJECT_CONTROL_LASER_SELECT_B (1) // Laser under automatic control bit position
#define INJECT_CONTROL_LASER_SELECT_W (2) // Laser under automatic control bit width
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

/* FPGA map indices */

#define FPGA_KERNEL (0) // Kernel registers
#define FPGA_LASER1_PWM (3) // Laser 1 TEC pulse width modulator registers
#define FPGA_LASER2_PWM (5) // Laser 2 TEC pulse width modulator registers
#define FPGA_LASER3_PWM (7) // Laser 3 TEC pulse width modulator registers
#define FPGA_LASER4_PWM (9) // Laser 4 TEC pulse width modulator registers
#define FPGA_RDSIM (11) // Ringdown simulator registers
#define FPGA_LASERLOCKER (16) // Laser frequency locker registers
#define FPGA_RDMAN (43) // Ringdown manager registers
#define FPGA_TWGEN (64) // Tuner waveform generator
#define FPGA_INJECT (72) // Optical Injection Subsystem

/* Environment addresses */

#define LASER1_TEMP_CNTRL_ENV (0)
#define LASER2_TEMP_CNTRL_ENV (10)
#define CHECK_ENV (20)
#define PULSE_GEN_ENV (22)
#define FILTER_ENV (23)
#define LASER_TEMP_MODEL_ENV (49)

/* Action codes */
#define ACTION_WRITE_BLOCK (1)
#define ACTION_SET_TIMESTAMP (2)
#define ACTION_GET_TIMESTAMP (3)
#define ACTION_INIT_RUNQUEUE (4)
#define ACTION_TEST_SCHEDULER (5)
#define ACTION_STREAM_REGISTER (6)
#define ACTION_RESISTANCE_TO_TEMPERATURE (7)
#define ACTION_TEMP_CNTRL_SET_COMMAND (8)
#define ACTION_APPLY_PID_STEP (9)
#define ACTION_TEMP_CNTRL_LASER1_INIT (10)
#define ACTION_TEMP_CNTRL_LASER1_STEP (11)
#define ACTION_TEMP_CNTRL_LASER2_INIT (12)
#define ACTION_TEMP_CNTRL_LASER2_STEP (13)
#define ACTION_TEMP_CNTRL_LASER3_INIT (14)
#define ACTION_TEMP_CNTRL_LASER3_STEP (15)
#define ACTION_TEMP_CNTRL_LASER4_INIT (16)
#define ACTION_TEMP_CNTRL_LASER4_STEP (17)
#define ACTION_FLOAT_REGISTER_TO_FPGA (18)
#define ACTION_FPGA_TO_FLOAT_REGISTER (19)
#define ACTION_INT_TO_FPGA (20)
#define ACTION_CURRENT_CNTRL_LASER1_INIT (21)
#define ACTION_CURRENT_CNTRL_LASER1_STEP (22)
#define ACTION_CURRENT_CNTRL_LASER2_INIT (23)
#define ACTION_CURRENT_CNTRL_LASER2_STEP (24)
#define ACTION_CURRENT_CNTRL_LASER3_INIT (25)
#define ACTION_CURRENT_CNTRL_LASER3_STEP (26)
#define ACTION_CURRENT_CNTRL_LASER4_INIT (27)
#define ACTION_CURRENT_CNTRL_LASER4_STEP (28)
#define ACTION_TEMP_CNTRL_CAVITY_INIT (29)
#define ACTION_TEMP_CNTRL_CAVITY_STEP (30)
#define ACTION_HEATER_CNTRL_INIT (31)
#define ACTION_HEATER_CNTRL_STEP (32)
#define ACTION_TUNER_CNTRL_INIT (33)
#define ACTION_TUNER_CNTRL_STEP (34)
#define ACTION_ENV_CHECKER (35)
#define ACTION_PULSE_GENERATOR (36)
#define ACTION_FILTER (37)
#define ACTION_DS1631_READTEMP (38)
#define ACTION_LASER_TEC_IMON (39)
#define ACTION_READ_LASER_TEC_MONITORS (40)
#define ACTION_READ_LASER_THERMISTOR_RESISTANCE (41)
#define ACTION_READ_LASER_CURRENT (42)
#endif
