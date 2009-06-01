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
    TEMP_CNTRL_DisabledState = 0, // Controller Disabled
    TEMP_CNTRL_EnabledState = 1, // Controller Enabled
    TEMP_CNTRL_SuspendedState = 2, // Controller Suspended
    TEMP_CNTRL_SweepingState = 3, // Continuous Sweeping
    TEMP_CNTRL_SendPrbsState = 4, // Sending PRBS
    TEMP_CNTRL_ManualState = 5 // Manual Control
} TEMP_CNTRL_StateType;

typedef enum {
    LASER_CURRENT_CNTRL_DisabledState = 0, // Controller Disabled
    LASER_CURRENT_CNTRL_EnabledState = 1, // Controller Enabled
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
#define INTERFACE_NUMBER_OF_REGISTERS (192)

#define NOOP_REGISTER (0)
#define VERIFY_INIT_REGISTER (1)
#define COMM_STATUS_REGISTER (2)
#define TIMESTAMP_LSB_REGISTER (3)
#define TIMESTAMP_MSB_REGISTER (4)
#define SCHEDULER_CONTROL_REGISTER (5)
#define LOW_DURATION_REGISTER (6)
#define HIGH_DURATION_REGISTER (7)
#define DAS_TEMPERATURE_REGISTER (8)
#define LASER_TEC_MONITOR_TEMPERATURE_REGISTER (9)
#define CONVERSION_LASER1_THERM_CONSTA_REGISTER (10)
#define CONVERSION_LASER1_THERM_CONSTB_REGISTER (11)
#define CONVERSION_LASER1_THERM_CONSTC_REGISTER (12)
#define LASER1_RESISTANCE_REGISTER (13)
#define LASER1_TEMPERATURE_REGISTER (14)
#define LASER1_THERMISTOR_ADC_REGISTER (15)
#define LASER1_TEC_REGISTER (16)
#define LASER1_MANUAL_TEC_REGISTER (17)
#define LASER1_TEMP_CNTRL_STATE_REGISTER (18)
#define LASER1_TEMP_CNTRL_LOCK_STATUS_REGISTER (19)
#define LASER1_TEMP_CNTRL_SETPOINT_REGISTER (20)
#define LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER (21)
#define LASER1_TEMP_CNTRL_TOLERANCE_REGISTER (22)
#define LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER (23)
#define LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER (24)
#define LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER (25)
#define LASER1_TEMP_CNTRL_H_REGISTER (26)
#define LASER1_TEMP_CNTRL_K_REGISTER (27)
#define LASER1_TEMP_CNTRL_TI_REGISTER (28)
#define LASER1_TEMP_CNTRL_TD_REGISTER (29)
#define LASER1_TEMP_CNTRL_B_REGISTER (30)
#define LASER1_TEMP_CNTRL_C_REGISTER (31)
#define LASER1_TEMP_CNTRL_N_REGISTER (32)
#define LASER1_TEMP_CNTRL_S_REGISTER (33)
#define LASER1_TEMP_CNTRL_FFWD_REGISTER (34)
#define LASER1_TEMP_CNTRL_AMIN_REGISTER (35)
#define LASER1_TEMP_CNTRL_AMAX_REGISTER (36)
#define LASER1_TEMP_CNTRL_IMAX_REGISTER (37)
#define LASER1_TEC_PRBS_GENPOLY_REGISTER (38)
#define LASER1_TEC_PRBS_AMPLITUDE_REGISTER (39)
#define LASER1_TEC_PRBS_MEAN_REGISTER (40)
#define LASER1_TEC_MONITOR_REGISTER (41)
#define LASER1_CURRENT_CNTRL_STATE_REGISTER (42)
#define LASER1_MANUAL_COARSE_CURRENT_REGISTER (43)
#define LASER1_MANUAL_FINE_CURRENT_REGISTER (44)
#define LASER1_CURRENT_SWEEP_MIN_REGISTER (45)
#define LASER1_CURRENT_SWEEP_MAX_REGISTER (46)
#define LASER1_CURRENT_SWEEP_INCR_REGISTER (47)
#define LASER1_CURRENT_MONITOR_REGISTER (48)
#define CONVERSION_LASER2_THERM_CONSTA_REGISTER (49)
#define CONVERSION_LASER2_THERM_CONSTB_REGISTER (50)
#define CONVERSION_LASER2_THERM_CONSTC_REGISTER (51)
#define LASER2_RESISTANCE_REGISTER (52)
#define LASER2_TEMPERATURE_REGISTER (53)
#define LASER2_THERMISTOR_ADC_REGISTER (54)
#define LASER2_TEC_REGISTER (55)
#define LASER2_MANUAL_TEC_REGISTER (56)
#define LASER2_TEMP_CNTRL_STATE_REGISTER (57)
#define LASER2_TEMP_CNTRL_LOCK_STATUS_REGISTER (58)
#define LASER2_TEMP_CNTRL_SETPOINT_REGISTER (59)
#define LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER (60)
#define LASER2_TEMP_CNTRL_TOLERANCE_REGISTER (61)
#define LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER (62)
#define LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER (63)
#define LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER (64)
#define LASER2_TEMP_CNTRL_H_REGISTER (65)
#define LASER2_TEMP_CNTRL_K_REGISTER (66)
#define LASER2_TEMP_CNTRL_TI_REGISTER (67)
#define LASER2_TEMP_CNTRL_TD_REGISTER (68)
#define LASER2_TEMP_CNTRL_B_REGISTER (69)
#define LASER2_TEMP_CNTRL_C_REGISTER (70)
#define LASER2_TEMP_CNTRL_N_REGISTER (71)
#define LASER2_TEMP_CNTRL_S_REGISTER (72)
#define LASER2_TEMP_CNTRL_FFWD_REGISTER (73)
#define LASER2_TEMP_CNTRL_AMIN_REGISTER (74)
#define LASER2_TEMP_CNTRL_AMAX_REGISTER (75)
#define LASER2_TEMP_CNTRL_IMAX_REGISTER (76)
#define LASER2_TEC_PRBS_GENPOLY_REGISTER (77)
#define LASER2_TEC_PRBS_AMPLITUDE_REGISTER (78)
#define LASER2_TEC_PRBS_MEAN_REGISTER (79)
#define LASER2_TEC_MONITOR_REGISTER (80)
#define CONVERSION_LASER3_THERM_CONSTA_REGISTER (81)
#define CONVERSION_LASER3_THERM_CONSTB_REGISTER (82)
#define CONVERSION_LASER3_THERM_CONSTC_REGISTER (83)
#define LASER3_RESISTANCE_REGISTER (84)
#define LASER3_TEMPERATURE_REGISTER (85)
#define LASER3_THERMISTOR_ADC_REGISTER (86)
#define LASER3_TEC_REGISTER (87)
#define LASER3_MANUAL_TEC_REGISTER (88)
#define LASER3_TEMP_CNTRL_STATE_REGISTER (89)
#define LASER3_TEMP_CNTRL_LOCK_STATUS_REGISTER (90)
#define LASER3_TEMP_CNTRL_SETPOINT_REGISTER (91)
#define LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER (92)
#define LASER3_TEMP_CNTRL_TOLERANCE_REGISTER (93)
#define LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER (94)
#define LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER (95)
#define LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER (96)
#define LASER3_TEMP_CNTRL_H_REGISTER (97)
#define LASER3_TEMP_CNTRL_K_REGISTER (98)
#define LASER3_TEMP_CNTRL_TI_REGISTER (99)
#define LASER3_TEMP_CNTRL_TD_REGISTER (100)
#define LASER3_TEMP_CNTRL_B_REGISTER (101)
#define LASER3_TEMP_CNTRL_C_REGISTER (102)
#define LASER3_TEMP_CNTRL_N_REGISTER (103)
#define LASER3_TEMP_CNTRL_S_REGISTER (104)
#define LASER3_TEMP_CNTRL_FFWD_REGISTER (105)
#define LASER3_TEMP_CNTRL_AMIN_REGISTER (106)
#define LASER3_TEMP_CNTRL_AMAX_REGISTER (107)
#define LASER3_TEMP_CNTRL_IMAX_REGISTER (108)
#define LASER3_TEC_PRBS_GENPOLY_REGISTER (109)
#define LASER3_TEC_PRBS_AMPLITUDE_REGISTER (110)
#define LASER3_TEC_PRBS_MEAN_REGISTER (111)
#define LASER3_TEC_MONITOR_REGISTER (112)
#define CONVERSION_LASER4_THERM_CONSTA_REGISTER (113)
#define CONVERSION_LASER4_THERM_CONSTB_REGISTER (114)
#define CONVERSION_LASER4_THERM_CONSTC_REGISTER (115)
#define LASER4_RESISTANCE_REGISTER (116)
#define LASER4_TEMPERATURE_REGISTER (117)
#define LASER4_THERMISTOR_ADC_REGISTER (118)
#define LASER4_TEC_REGISTER (119)
#define LASER4_MANUAL_TEC_REGISTER (120)
#define LASER4_TEMP_CNTRL_STATE_REGISTER (121)
#define LASER4_TEMP_CNTRL_LOCK_STATUS_REGISTER (122)
#define LASER4_TEMP_CNTRL_SETPOINT_REGISTER (123)
#define LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER (124)
#define LASER4_TEMP_CNTRL_TOLERANCE_REGISTER (125)
#define LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER (126)
#define LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER (127)
#define LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER (128)
#define LASER4_TEMP_CNTRL_H_REGISTER (129)
#define LASER4_TEMP_CNTRL_K_REGISTER (130)
#define LASER4_TEMP_CNTRL_TI_REGISTER (131)
#define LASER4_TEMP_CNTRL_TD_REGISTER (132)
#define LASER4_TEMP_CNTRL_B_REGISTER (133)
#define LASER4_TEMP_CNTRL_C_REGISTER (134)
#define LASER4_TEMP_CNTRL_N_REGISTER (135)
#define LASER4_TEMP_CNTRL_S_REGISTER (136)
#define LASER4_TEMP_CNTRL_FFWD_REGISTER (137)
#define LASER4_TEMP_CNTRL_AMIN_REGISTER (138)
#define LASER4_TEMP_CNTRL_AMAX_REGISTER (139)
#define LASER4_TEMP_CNTRL_IMAX_REGISTER (140)
#define LASER4_TEC_PRBS_GENPOLY_REGISTER (141)
#define LASER4_TEC_PRBS_AMPLITUDE_REGISTER (142)
#define LASER4_TEC_PRBS_MEAN_REGISTER (143)
#define LASER4_TEC_MONITOR_REGISTER (144)
#define CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER (145)
#define CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER (146)
#define CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER (147)
#define HOT_BOX_HEATSINK_RESISTANCE_REGISTER (148)
#define HOT_BOX_HEATSINK_TEMPERATURE_REGISTER (149)
#define HOT_BOX_HEATSINK_ADC_REGISTER (150)
#define CONVERSION_CAVITY_THERM_CONSTA_REGISTER (151)
#define CONVERSION_CAVITY_THERM_CONSTB_REGISTER (152)
#define CONVERSION_CAVITY_THERM_CONSTC_REGISTER (153)
#define CAVITY_RESISTANCE_REGISTER (154)
#define CAVITY_TEMPERATURE_REGISTER (155)
#define CAVITY_THERMISTOR_ADC_REGISTER (156)
#define CAVITY_TEC_REGISTER (157)
#define CAVITY_MANUAL_TEC_REGISTER (158)
#define CAVITY_TEMP_CNTRL_STATE_REGISTER (159)
#define CAVITY_TEMP_CNTRL_LOCK_STATUS_REGISTER (160)
#define CAVITY_TEMP_CNTRL_SETPOINT_REGISTER (161)
#define CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER (162)
#define CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER (163)
#define CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER (164)
#define CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER (165)
#define CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER (166)
#define CAVITY_TEMP_CNTRL_H_REGISTER (167)
#define CAVITY_TEMP_CNTRL_K_REGISTER (168)
#define CAVITY_TEMP_CNTRL_TI_REGISTER (169)
#define CAVITY_TEMP_CNTRL_TD_REGISTER (170)
#define CAVITY_TEMP_CNTRL_B_REGISTER (171)
#define CAVITY_TEMP_CNTRL_C_REGISTER (172)
#define CAVITY_TEMP_CNTRL_N_REGISTER (173)
#define CAVITY_TEMP_CNTRL_S_REGISTER (174)
#define CAVITY_TEMP_CNTRL_FFWD_REGISTER (175)
#define CAVITY_TEMP_CNTRL_AMIN_REGISTER (176)
#define CAVITY_TEMP_CNTRL_AMAX_REGISTER (177)
#define CAVITY_TEMP_CNTRL_IMAX_REGISTER (178)
#define CAVITY_TEC_PRBS_GENPOLY_REGISTER (179)
#define CAVITY_TEC_PRBS_AMPLITUDE_REGISTER (180)
#define CAVITY_TEC_PRBS_MEAN_REGISTER (181)
#define CAVITY_MAX_HEATSINK_TEMP_REGISTER (182)
#define HEATER_CNTRL_STATE_REGISTER (183)
#define HEATER_CNTRL_GAIN_REGISTER (184)
#define HEATER_CNTRL_QUANTIZE_REGISTER (185)
#define HEATER_CNTRL_UBIAS_SLOPE_REGISTER (186)
#define HEATER_CNTRL_UBIAS_OFFSET_REGISTER (187)
#define HEATER_CNTRL_MARK_MIN_REGISTER (188)
#define HEATER_CNTRL_MARK_MAX_REGISTER (189)
#define HEATER_CNTRL_MANUAL_MARK_REGISTER (190)
#define HEATER_CNTRL_MARK_REGISTER (191)

/* FPGA block definitions */

/* Block KERNEL Kernel */
#define KERNEL_MAGIC_CODE (0) // Code indicating FPGA is programmed
#define KERNEL_RESET (1) // Used to reset Cypress FX2

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
#define RDSIM_CS (0) // Control/Status register
#define RDSIM_CS_RUN_B (0) // STOP/RUN bit position
#define RDSIM_CS_RUN_W (1) // STOP/RUN bit width
#define RDSIM_CS_CONT_B (1) // SINGLE/CONTINUOUS bit position
#define RDSIM_CS_CONT_W (1) // SINGLE/CONTINUOUS bit width
#define RDSIM_CS_INIT_B (2) // NORMAL/INIT bit position
#define RDSIM_CS_INIT_W (1) // NORMAL/INIT bit width
#define RDSIM_CS_ADC_CLK_B (3) // SINGLE mode ADC clock bit position
#define RDSIM_CS_ADC_CLK_W (1) // SINGLE mode ADC clock bit width

#define RDSIM_VALUE (1) // Ringdown value register
#define RDSIM_DECAY (2) // Decay rate register
#define RDSIM_AMPLITUDE (3) // Ringdown amplitude register

/* Block LASERLOCK Laser frequency locker */
#define LASERLOCK_CS (0) // Control/Status register
#define LASERLOCK_CS_RUN_B (0) // STOP/RUN bit position
#define LASERLOCK_CS_RUN_W (1) // STOP/RUN bit width
#define LASERLOCK_CS_CONT_B (1) // SINGLE/CONTINUOUS bit position
#define LASERLOCK_CS_CONT_W (1) // SINGLE/CONTINUOUS bit width
#define LASERLOCK_CS_PRBS_B (2) // Enables generation of PRBS for loop characterization bit position
#define LASERLOCK_CS_PRBS_W (1) // Enables generation of PRBS for loop characterization bit width
#define LASERLOCK_CS_ACC_EN_B (3) // Resets or enables fine current accumulator bit position
#define LASERLOCK_CS_ACC_EN_W (1) // Resets or enables fine current accumulator bit width
#define LASERLOCK_CS_SAMPLE_DARK_B (4) // Strobe high to sample dark current bit position
#define LASERLOCK_CS_SAMPLE_DARK_W (1) // Strobe high to sample dark current bit width
#define LASERLOCK_CS_ADC_STROBE_B (5) // Strobe high to start new computation cycle bit position
#define LASERLOCK_CS_ADC_STROBE_W (1) // Strobe high to start new computation cycle bit width
#define LASERLOCK_CS_TUNING_OFFSET_SEL_B (6) // 0 selects register, 1 selects input for tuning offset input bit position
#define LASERLOCK_CS_TUNING_OFFSET_SEL_W (1) // 0 selects register, 1 selects input for tuning offset input bit width
#define LASERLOCK_CS_LOCKED_B (14) // Flag indicating loop is locked bit position
#define LASERLOCK_CS_LOCKED_W (1) // Flag indicating loop is locked bit width
#define LASERLOCK_CS_DONE_B (15) // Flag indicating cycle is complete bit position
#define LASERLOCK_CS_DONE_W (1) // Flag indicating cycle is complete bit width

#define LASERLOCK_ETA1 (1) // Etalon 1 reading
#define LASERLOCK_REF1 (2) // Reference 1 reading
#define LASERLOCK_ETA2 (3) // Etalon 2 reading
#define LASERLOCK_REF2 (4) // Reference 2 reading
#define LASERLOCK_ETA1_DARK (5) // Etalon 1 dark reading (ro)
#define LASERLOCK_REF1_DARK (6) // Reference 1 dark reading (ro)
#define LASERLOCK_ETA2_DARK (7) // Etalon 2 dark reading (ro)
#define LASERLOCK_REF2_DARK (8) // Reference 2 dark reading (ro)
#define LASERLOCK_ETA1_OFFSET (9) // Etalon 1 offset to be subtracted before finding ratio
#define LASERLOCK_REF1_OFFSET (10) // Reference 1 offset to be subtracted before finding ratio
#define LASERLOCK_ETA2_OFFSET (11) // Etalon 2 offset to be subtracted before finding ratio
#define LASERLOCK_REF2_OFFSET (12) // Reference 2 offset to be subtracted before finding ratio
#define LASERLOCK_RATIO1 (13) // Ratio 1 (ro)
#define LASERLOCK_RATIO2 (14) // Ratio 2 (ro)
#define LASERLOCK_RATIO1_CENTER (15) // Center of ellipse for ratio 1
#define LASERLOCK_RATIO1_MULTIPLIER (16) // Factor for ratio 1 in error linear combination
#define LASERLOCK_RATIO2_CENTER (17) // Center of ellipse for ratio 2
#define LASERLOCK_RATIO2_MULTIPLIER (18) // Factor for ratio 2 in error linear combination
#define LASERLOCK_TUNING_OFFSET (19) // Offset to add to error to shift frequency
#define LASERLOCK_LOCK_ERROR (20) // Frequency loop lock error (ro)
#define LASERLOCK_WM_LOCK_WINDOW (21) // Defines when laser frequency is in lock
#define LASERLOCK_WM_INT_GAIN (22) // Integral gain for wavelength locking
#define LASERLOCK_WM_PROP_GAIN (23) // Proportional gain for wavelength locking
#define LASERLOCK_WM_DERIV_GAIN (24) // Derivative gain for wavelength locking
#define LASERLOCK_FINE_CURRENT (25) // Fine laser current (ro)
#define LASERLOCK_CYCLE_COUNTER (26) // Cycle counter (ro)

/* Block RDMETAMAN Ringdown metadata manager */
#define RDMETAMAN_CS (0) // Control/Status register
#define RDMETAMAN_CS_RUN_B (0) // STOP/RUN bit position
#define RDMETAMAN_CS_RUN_W (1) // STOP/RUN bit width
#define RDMETAMAN_CS_CONT_B (1) // SINGLE/CONTINUOUS bit position
#define RDMETAMAN_CS_CONT_W (1) // SINGLE/CONTINUOUS bit width
#define RDMETAMAN_CS_START_B (2) // Start address counter bit position
#define RDMETAMAN_CS_START_W (1) // Start address counter bit width
#define RDMETAMAN_CS_BANK_B (3) // Bank select bit position
#define RDMETAMAN_CS_BANK_W (1) // Bank select bit width
#define RDMETAMAN_CS_RD_B (4) // Ringdown bit position
#define RDMETAMAN_CS_RD_W (1) // Ringdown bit width
#define RDMETAMAN_CS_LASER_LOCKER_DONE_B (5) // Laser locker done (metadata strobe) bit position
#define RDMETAMAN_CS_LASER_LOCKER_DONE_W (1) // Laser locker done (metadata strobe) bit width
#define RDMETAMAN_CS_LAPPED_B (15) // Address counter wrapped bit position
#define RDMETAMAN_CS_LAPPED_W (1) // Address counter wrapped bit width

#define RDMETAMAN_METADATA_ADDRCNTR (1) // Metadata address counter
#define RDMETAMAN_PARAM_ADDRCNTR (2) // Parameter address counter
#define RDMETAMAN_TUNER (3) // Tuner value
#define RDMETAMAN_TUNER_AT_RINGDOWN (4) // Tuner value at ringdown
#define RDMETAMAN_ADDR_AT_RINGDOWN (5) // Metadata address counter value at ringdown
#define RDMETAMAN_PARAM0 (6) // Ringdown parameter 0
#define RDMETAMAN_PARAM1 (7) // Ringdown parameter 1
#define RDMETAMAN_PARAM2 (8) // Ringdown parameter 2
#define RDMETAMAN_PARAM3 (9) // Ringdown parameter 3
#define RDMETAMAN_PARAM4 (10) // Ringdown parameter 4
#define RDMETAMAN_PARAM5 (11) // Ringdown parameter 5
#define RDMETAMAN_PARAM6 (12) // Ringdown parameter 6
#define RDMETAMAN_PARAM7 (13) // Ringdown parameter 7

/* Block RDDATMAN Ringdown data manager */
#define RDDATMAN_CS (0) // Control/Status register
#define RDDATMAN_CS_RUN_B (0) // STOP/RUN bit position
#define RDDATMAN_CS_RUN_W (1) // STOP/RUN bit width
#define RDDATMAN_CS_CONT_B (1) // SINGLE/CONTINUOUS bit position
#define RDDATMAN_CS_CONT_W (1) // SINGLE/CONTINUOUS bit width
#define RDDATMAN_CS_ACK_B (2) // Acknowledge completion of acquisition bit position
#define RDDATMAN_CS_ACK_W (1) // Acknowledge completion of acquisition bit width
#define RDDATMAN_CS_BANK_B (3) // Bank select bit position
#define RDDATMAN_CS_BANK_W (1) // Bank select bit width
#define RDDATMAN_CS_GATE_B (4) // Gate to arm for ringdown acquisition bit position
#define RDDATMAN_CS_GATE_W (1) // Gate to arm for ringdown acquisition bit width
#define RDDATMAN_CS_RD_CLOCK_B (14) // Ringdown ADC clock bit position
#define RDDATMAN_CS_RD_CLOCK_W (1) // Ringdown ADC clock bit width
#define RDDATMAN_CS_ACQ_DONE_B (15) // Acquisition done bit position
#define RDDATMAN_CS_ACQ_DONE_W (1) // Acquisition done bit width

#define RDDATMAN_DATA_ADDRCNTR (1) // Address counter
#define RDDATMAN_DATA (2) // Ringdown data
#define RDDATMAN_DIVISOR (3) // Divisor for ringdown ADC clock
#define RDDATMAN_NUM_SAMP (4) // Number of samples to collect
#define RDDATMAN_THRESHOLD (5) // Ringdown threshold

/* Block RDMAN Ringdown manager */
#define RDMAN_CONTROL (0) // Control register
#define RDMAN_CONTROL_RUN_B (0) // STOP/RUN bit position
#define RDMAN_CONTROL_RUN_W (1) // STOP/RUN bit width
#define RDMAN_CONTROL_CONT_B (1) // SINGLE/CONTINUOUS bit position
#define RDMAN_CONTROL_CONT_W (1) // SINGLE/CONTINUOUS bit width
#define RDMAN_CONTROL_START_RD_B (2) // Start ringdown cycle bit position
#define RDMAN_CONTROL_START_RD_W (1) // Start ringdown cycle bit width
#define RDMAN_CONTROL_LOCK_ENABLE_B (3) // Enable laser locking bit position
#define RDMAN_CONTROL_LOCK_ENABLE_W (1) // Enable laser locking bit width
#define RDMAN_CONTROL_UP_SLOPE_ENABLE_B (4) // Enable ringdown on positive slope bit position
#define RDMAN_CONTROL_UP_SLOPE_ENABLE_W (1) // Enable ringdown on positive slope bit width
#define RDMAN_CONTROL_DOWN_SLOPE_ENABLE_B (5) // Enable ringdown on negative slope bit position
#define RDMAN_CONTROL_DOWN_SLOPE_ENABLE_W (1) // Enable ringdown on negative slope bit width
#define RDMAN_CONTROL_BANK0_CLEAR_B (6) // Reset bank 0 in use bit position
#define RDMAN_CONTROL_BANK0_CLEAR_W (1) // Reset bank 0 in use bit width
#define RDMAN_CONTROL_BANK1_CLEAR_B (7) // Reset bank 1 in use bit position
#define RDMAN_CONTROL_BANK1_CLEAR_W (1) // Reset bank 1 in use bit width
#define RDMAN_CONTROL_LASER_LOCKED_B (8) // Laser wavelength locked bit position
#define RDMAN_CONTROL_LASER_LOCKED_W (1) // Laser wavelength locked bit width
#define RDMAN_CONTROL_LASER_LOCKER_DONE_B (9) // Laser locker done (metadata strobe) bit position
#define RDMAN_CONTROL_LASER_LOCKER_DONE_W (1) // Laser locker done (metadata strobe) bit width
#define RDMAN_CONTROL_RD_IRQ_ACK_B (10) // Acknowledge ringdown irq bit position
#define RDMAN_CONTROL_RD_IRQ_ACK_W (1) // Acknowledge ringdown irq bit width
#define RDMAN_CONTROL_ACQ_DONE_ACK_B (11) // Acknowledge acquisition irq bit position
#define RDMAN_CONTROL_ACQ_DONE_ACK_W (1) // Acknowledge acquisition irq bit width

#define RDMAN_STATUS (1) // Status register
#define RDMAN_STATUS_SHUTDOWN_B (0) // Injection shutdown bit position
#define RDMAN_STATUS_SHUTDOWN_W (1) // Injection shutdown bit width
#define RDMAN_STATUS_RD_IRQ_B (1) // Ringdown interrupt bit position
#define RDMAN_STATUS_RD_IRQ_W (1) // Ringdown interrupt bit width
#define RDMAN_STATUS_ACQ_DONE_B (2) // Acquisition done interrupt bit position
#define RDMAN_STATUS_ACQ_DONE_W (1) // Acquisition done interrupt bit width
#define RDMAN_STATUS_BANK_B (3) // Bank for writes (ro) bit position
#define RDMAN_STATUS_BANK_W (1) // Bank for writes (ro) bit width
#define RDMAN_STATUS_BANK0_IN_USE_B (4) // Bank 0 in use   (ro) bit position
#define RDMAN_STATUS_BANK0_IN_USE_W (1) // Bank 0 in use   (ro) bit width
#define RDMAN_STATUS_BANK1_IN_USE_B (5) // Bank 1 in use   (ro) bit position
#define RDMAN_STATUS_BANK1_IN_USE_W (1) // Bank 1 in use   (ro) bit width
#define RDMAN_STATUS_LAPPED_B (6) // Address counter wrapped bit position
#define RDMAN_STATUS_LAPPED_W (1) // Address counter wrapped bit width
#define RDMAN_STATUS_TIMEOUT_B (7) // Ringdown timeout occured bit position
#define RDMAN_STATUS_TIMEOUT_W (1) // Ringdown timeout occured bit width

#define RDMAN_TUNER (2) // Tuner value
#define RDMAN_DATA (3) // Ringdown data
#define RDMAN_PARAM0 (4) // Ringdown parameter 0
#define RDMAN_PARAM1 (5) // Ringdown parameter 1
#define RDMAN_PARAM2 (6) // Ringdown parameter 2
#define RDMAN_PARAM3 (7) // Ringdown parameter 3
#define RDMAN_PARAM4 (8) // Ringdown parameter 4
#define RDMAN_PARAM5 (9) // Ringdown parameter 5
#define RDMAN_PARAM6 (10) // Ringdown parameter 6
#define RDMAN_PARAM7 (11) // Ringdown parameter 7
#define RDMAN_DATA_ADDRCNTR (12) // Address counter
#define RDMAN_METADATA_ADDRCNTR (13) // Metadata address counter
#define RDMAN_PARAM_ADDRCNTR (14) // Parameter address counter
#define RDMAN_DIVISOR (15) // Divisor for ringdown ADC clock
#define RDMAN_NUM_SAMP (16) // Number of samples to collect
#define RDMAN_THRESHOLD (17) // Ringdown threshold
#define RDMAN_PRECONTROL_TIME (18) // Precontrol time
#define RDMAN_RINGDOWN_TIMEOUT (19) // Ringdown timeout
#define RDMAN_TUNER_AT_RINGDOWN (20) // Tuner value at ringdown
#define RDMAN_METADATA_ADDR_AT_RINGDOWN (21) // Metadata address counter value at ringdown

/* Block LASER_CURRENT_DAC Laser current DAC */
#define LASER_CURRENT_DAC_CS (0) // Control/Status register
#define LASER_CURRENT_DAC_CS_RUN_B (0) // STOP/RUN bit position
#define LASER_CURRENT_DAC_CS_RUN_W (1) // STOP/RUN bit width
#define LASER_CURRENT_DAC_CS_CONT_B (1) // SINGLE/CONTINUOUS bit position
#define LASER_CURRENT_DAC_CS_CONT_W (1) // SINGLE/CONTINUOUS bit width

#define LASER_CURRENT_DAC_COARSE_CURRENT (1) // Coarse current DAC
#define LASER_CURRENT_DAC_FINE_CURRENT (2) // Fine current DAC

/* Block RDCOMPARE Ringdown comparator */
#define RDCOMPARE_THRESHOLD (0) // Ringdown threshold
#define RDCOMPARE_RATE_DIVISOR (1) // Ringdown address counter divisor

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
#define INJECT_CONTROL_LASER_SELECT_B (1) // Select laser bit position
#define INJECT_CONTROL_LASER_SELECT_W (2) // Select laser bit width
#define INJECT_CONTROL_LASER_CURRENT_ENABLE_B (3) // Laser current enable bit position
#define INJECT_CONTROL_LASER_CURRENT_ENABLE_W (4) // Laser current enable bit width
#define INJECT_CONTROL_MANUAL_LASER_ENABLE_B (7) // Deasserts short across laser in manual mode bit position
#define INJECT_CONTROL_MANUAL_LASER_ENABLE_W (4) // Deasserts short across laser in manual mode bit width
#define INJECT_CONTROL_MANUAL_SOA_ENABLE_B (11) // Deasserts short across SOA in manual mode bit position
#define INJECT_CONTROL_MANUAL_SOA_ENABLE_W (1) // Deasserts short across SOA in manual mode bit width
#define INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B (12) // Enables laser shutdown bit position
#define INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W (1) // Enables laser shutdown bit width
#define INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B (13) // Enables SOA shutdown bit position
#define INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W (1) // Enables SOA shutdown bit width

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
#define FPGA_LASER1_PWM (2) // Laser 1 TEC pulse width modulator registers
#define FPGA_LASER2_PWM (4) // Laser 2 TEC pulse width modulator registers
#define FPGA_LASER3_PWM (6) // Laser 3 TEC pulse width modulator registers
#define FPGA_LASER4_PWM (8) // Laser 4 TEC pulse width modulator registers
#define FPGA_RDSIM (10) // Ringdown simulator registers
#define FPGA_LASERLOCK (14) // Laser frequency locker registers
#define FPGA_RDMETAMAN (41) // Ringdown metadata manager registers
#define FPGA_RDDATMAN (55) // Ringdown data manager registers
#define FPGA_RDMAN (61) // Ringdown manager registers
#define FPGA_LASER1_CURRENT_DAC (83) // Laser1 current DAC registers
#define FPGA_LASER2_CURRENT_DAC (86) // Laser2 current DAC registers
#define FPGA_LASER3_CURRENT_DAC (89) // Laser3 current DAC registers
#define FPGA_LASER4_CURRENT_DAC (92) // Laser4 current DAC registers
#define FPGA_RDCOMPARE (95) // Ringdown comparator
#define FPGA_TWGEN (97) // Tuner waveform generator
#define FPGA_INJECT (105) // Optical Injection Subsystem

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
#define ACTION_TEMP_CNTRL_CAVITY_INIT (23)
#define ACTION_TEMP_CNTRL_CAVITY_STEP (24)
#define ACTION_HEATER_CNTRL_INIT (25)
#define ACTION_HEATER_CNTRL_STEP (26)
#define ACTION_ENV_CHECKER (27)
#define ACTION_PULSE_GENERATOR (28)
#define ACTION_FILTER (29)
#define ACTION_DS1631_READTEMP (30)
#define ACTION_LASER_TEC_IMON (31)
#define ACTION_READ_LASER_TEC_MONITORS (32)
#endif
