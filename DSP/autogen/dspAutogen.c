/*
 * FILE:
 *   dspAutogen.c
 *
 * DESCRIPTION:
 *   Automatically generated DSP C file for Picarro gas analyzer. DO NOT EDIT.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */

#include <stdlib.h>
#include "dspAutogen.h"
#include "interface.h"

extern int writeRegister(unsigned int regNum,DataType data);
RegTypes regTypes[406];

/* I2C devices */
I2C_device i2c_devices[33] = {
    {0, -1, 0x55},
    {0, 0, 0x26},
    {0, 0, 0x14},
    {0, 0, 0x50},
    {0, 1, 0x26},
    {0, 1, 0x14},
    {0, 1, 0x50},
    {0, 2, 0x26},
    {0, 2, 0x14},
    {0, 2, 0x50},
    {0, 3, 0x26},
    {0, 3, 0x14},
    {0, 3, 0x50},
    {1, 0, 0x27},
    {1, 0, 0x26},
    {1, 0, 0x15},
    {1, 0, 0x50},
    {0, 7, 0x27},
    {0, 7, 0x26},
    {0, 7, 0x24},
    {0, 7, 0x17},
    {0, 7, 0x14},
    {0, 7, 0x15},
    {1, 4, 0x14},
    {1, 4, 0x15},
    {1, 4, 0x24},
    {1, 4, 0x26},
    {1, 4, 0x50},
    {0, -1, 0x4e},
    {1, 4, 0x70},
    {0, 4, 0x10},
    {0, -1, 0x70},
    {1, -1, 0x71}};

void initRegisters() 
{
    DataType d;
    d.asUint = 0xABCD1234;
    writeRegister(NOOP_REGISTER,d);
    d.asUint = 0x19680511;
    writeRegister(VERIFY_INIT_REGISTER,d);
    d.asUint = 0;
    writeRegister(SCHEDULER_CONTROL_REGISTER,d);
    d.asUint = 0;
    writeRegister(HARDWARE_PRESENT_REGISTER,d);
    d.asUint = 0;
    writeRegister(RD_IRQ_COUNT_REGISTER,d);
    d.asUint = 0;
    writeRegister(ACQ_DONE_COUNT_REGISTER,d);
    d.asUint = 0;
    writeRegister(RD_DATA_MOVING_COUNT_REGISTER,d);
    d.asUint = 0;
    writeRegister(RD_QDMA_DONE_COUNT_REGISTER,d);
    d.asUint = 0;
    writeRegister(RD_FITTING_COUNT_REGISTER,d);
    d.asUint = 0;
    writeRegister(RD_INITIATED_COUNT_REGISTER,d);
    d.asUint = 0;
    writeRegister(DAS_STATUS_REGISTER,d);
    d.asFloat = 20.0;
    writeRegister(DAS_TEMPERATURE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(HEATER_CNTRL_SENSOR_REGISTER,d);
    d.asFloat = 0.00112789997365;
    writeRegister(CONVERSION_LASER1_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000234289997024;
    writeRegister(CONVERSION_LASER1_THERM_CONSTB_REGISTER,d);
    d.asFloat = 8.72979981636e-008;
    writeRegister(CONVERSION_LASER1_THERM_CONSTC_REGISTER,d);
    d.asFloat = 7.62939e-3;
    writeRegister(CONVERSION_LASER1_CURRENT_SLOPE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(CONVERSION_LASER1_CURRENT_OFFSET_REGISTER,d);
    d.asFloat = 30000;
    writeRegister(LASER1_THERMISTOR_SERIES_RESISTANCE_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(LASER1_TEC_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(LASER1_MANUAL_TEC_REGISTER,d);
    d.asUint = TEMP_CNTRL_DisabledState;
    writeRegister(LASER1_TEMP_CNTRL_STATE_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(LASER1_TEMP_CNTRL_SETPOINT_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER,d);
    d.asFloat = 0.1;
    writeRegister(LASER1_TEMP_CNTRL_TOLERANCE_REGISTER,d);
    d.asFloat = 30.0;
    writeRegister(LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER,d);
    d.asFloat = 20.0;
    writeRegister(LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.05;
    writeRegister(LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER,d);
    d.asFloat = 0.2;
    writeRegister(LASER1_TEMP_CNTRL_H_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER1_TEMP_CNTRL_K_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(LASER1_TEMP_CNTRL_TI_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER1_TEMP_CNTRL_TD_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(LASER1_TEMP_CNTRL_B_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(LASER1_TEMP_CNTRL_C_REGISTER,d);
    d.asFloat = 100.0;
    writeRegister(LASER1_TEMP_CNTRL_N_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(LASER1_TEMP_CNTRL_S_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER1_TEMP_CNTRL_FFWD_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(LASER1_TEMP_CNTRL_AMIN_REGISTER,d);
    d.asFloat = 55000.0;
    writeRegister(LASER1_TEMP_CNTRL_AMAX_REGISTER,d);
    d.asFloat = 10000.0;
    writeRegister(LASER1_TEMP_CNTRL_IMAX_REGISTER,d);
    d.asUint = 0x481;
    writeRegister(LASER1_TEC_PRBS_GENPOLY_REGISTER,d);
    d.asFloat = 5000.0;
    writeRegister(LASER1_TEC_PRBS_AMPLITUDE_REGISTER,d);
    d.asFloat = 40000.0;
    writeRegister(LASER1_TEC_PRBS_MEAN_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER1_TEC_MONITOR_REGISTER,d);
    d.asUint = LASER_CURRENT_CNTRL_DisabledState;
    writeRegister(LASER1_CURRENT_CNTRL_STATE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER1_MANUAL_COARSE_CURRENT_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER1_MANUAL_FINE_CURRENT_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER1_CURRENT_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER1_CURRENT_SWEEP_MAX_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER1_CURRENT_SWEEP_INCR_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER1_CURRENT_MONITOR_REGISTER,d);
    d.asFloat = 0.00112789997365;
    writeRegister(CONVERSION_LASER2_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000234289997024;
    writeRegister(CONVERSION_LASER2_THERM_CONSTB_REGISTER,d);
    d.asFloat = 8.72979981636e-008;
    writeRegister(CONVERSION_LASER2_THERM_CONSTC_REGISTER,d);
    d.asFloat = 7.62939e-3;
    writeRegister(CONVERSION_LASER2_CURRENT_SLOPE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(CONVERSION_LASER2_CURRENT_OFFSET_REGISTER,d);
    d.asFloat = 30000;
    writeRegister(LASER2_THERMISTOR_SERIES_RESISTANCE_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(LASER2_TEC_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(LASER2_MANUAL_TEC_REGISTER,d);
    d.asUint = TEMP_CNTRL_DisabledState;
    writeRegister(LASER2_TEMP_CNTRL_STATE_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(LASER2_TEMP_CNTRL_SETPOINT_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER,d);
    d.asFloat = 0.1;
    writeRegister(LASER2_TEMP_CNTRL_TOLERANCE_REGISTER,d);
    d.asFloat = 30.0;
    writeRegister(LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER,d);
    d.asFloat = 20.0;
    writeRegister(LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.05;
    writeRegister(LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER,d);
    d.asFloat = 0.2;
    writeRegister(LASER2_TEMP_CNTRL_H_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER2_TEMP_CNTRL_K_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(LASER2_TEMP_CNTRL_TI_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER2_TEMP_CNTRL_TD_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(LASER2_TEMP_CNTRL_B_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(LASER2_TEMP_CNTRL_C_REGISTER,d);
    d.asFloat = 100.0;
    writeRegister(LASER2_TEMP_CNTRL_N_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(LASER2_TEMP_CNTRL_S_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER2_TEMP_CNTRL_FFWD_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(LASER2_TEMP_CNTRL_AMIN_REGISTER,d);
    d.asFloat = 55000.0;
    writeRegister(LASER2_TEMP_CNTRL_AMAX_REGISTER,d);
    d.asFloat = 10000.0;
    writeRegister(LASER2_TEMP_CNTRL_IMAX_REGISTER,d);
    d.asUint = 0x481;
    writeRegister(LASER2_TEC_PRBS_GENPOLY_REGISTER,d);
    d.asFloat = 5000.0;
    writeRegister(LASER2_TEC_PRBS_AMPLITUDE_REGISTER,d);
    d.asFloat = 40000.0;
    writeRegister(LASER2_TEC_PRBS_MEAN_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER2_TEC_MONITOR_REGISTER,d);
    d.asUint = LASER_CURRENT_CNTRL_DisabledState;
    writeRegister(LASER2_CURRENT_CNTRL_STATE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER2_MANUAL_COARSE_CURRENT_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER2_MANUAL_FINE_CURRENT_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER2_CURRENT_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER2_CURRENT_SWEEP_MAX_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER2_CURRENT_SWEEP_INCR_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER2_CURRENT_MONITOR_REGISTER,d);
    d.asFloat = 0.00112789997365;
    writeRegister(CONVERSION_LASER3_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000234289997024;
    writeRegister(CONVERSION_LASER3_THERM_CONSTB_REGISTER,d);
    d.asFloat = 8.72979981636e-008;
    writeRegister(CONVERSION_LASER3_THERM_CONSTC_REGISTER,d);
    d.asFloat = 7.62939e-3;
    writeRegister(CONVERSION_LASER3_CURRENT_SLOPE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(CONVERSION_LASER3_CURRENT_OFFSET_REGISTER,d);
    d.asFloat = 30000;
    writeRegister(LASER3_THERMISTOR_SERIES_RESISTANCE_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(LASER3_TEC_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(LASER3_MANUAL_TEC_REGISTER,d);
    d.asUint = TEMP_CNTRL_DisabledState;
    writeRegister(LASER3_TEMP_CNTRL_STATE_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(LASER3_TEMP_CNTRL_SETPOINT_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER,d);
    d.asFloat = 0.1;
    writeRegister(LASER3_TEMP_CNTRL_TOLERANCE_REGISTER,d);
    d.asFloat = 30.0;
    writeRegister(LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER,d);
    d.asFloat = 20.0;
    writeRegister(LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.05;
    writeRegister(LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER,d);
    d.asFloat = 0.2;
    writeRegister(LASER3_TEMP_CNTRL_H_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER3_TEMP_CNTRL_K_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(LASER3_TEMP_CNTRL_TI_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER3_TEMP_CNTRL_TD_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(LASER3_TEMP_CNTRL_B_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(LASER3_TEMP_CNTRL_C_REGISTER,d);
    d.asFloat = 100.0;
    writeRegister(LASER3_TEMP_CNTRL_N_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(LASER3_TEMP_CNTRL_S_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER3_TEMP_CNTRL_FFWD_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(LASER3_TEMP_CNTRL_AMIN_REGISTER,d);
    d.asFloat = 55000.0;
    writeRegister(LASER3_TEMP_CNTRL_AMAX_REGISTER,d);
    d.asFloat = 10000.0;
    writeRegister(LASER3_TEMP_CNTRL_IMAX_REGISTER,d);
    d.asUint = 0x481;
    writeRegister(LASER3_TEC_PRBS_GENPOLY_REGISTER,d);
    d.asFloat = 5000.0;
    writeRegister(LASER3_TEC_PRBS_AMPLITUDE_REGISTER,d);
    d.asFloat = 40000.0;
    writeRegister(LASER3_TEC_PRBS_MEAN_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER3_TEC_MONITOR_REGISTER,d);
    d.asUint = LASER_CURRENT_CNTRL_DisabledState;
    writeRegister(LASER3_CURRENT_CNTRL_STATE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER3_MANUAL_COARSE_CURRENT_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER3_MANUAL_FINE_CURRENT_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER3_CURRENT_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER3_CURRENT_SWEEP_MAX_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER3_CURRENT_SWEEP_INCR_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER3_CURRENT_MONITOR_REGISTER,d);
    d.asFloat = 0.00112789997365;
    writeRegister(CONVERSION_LASER4_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000234289997024;
    writeRegister(CONVERSION_LASER4_THERM_CONSTB_REGISTER,d);
    d.asFloat = 8.72979981636e-008;
    writeRegister(CONVERSION_LASER4_THERM_CONSTC_REGISTER,d);
    d.asFloat = 7.62939e-3;
    writeRegister(CONVERSION_LASER4_CURRENT_SLOPE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(CONVERSION_LASER4_CURRENT_OFFSET_REGISTER,d);
    d.asFloat = 30000;
    writeRegister(LASER4_THERMISTOR_SERIES_RESISTANCE_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(LASER4_TEC_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(LASER4_MANUAL_TEC_REGISTER,d);
    d.asUint = TEMP_CNTRL_DisabledState;
    writeRegister(LASER4_TEMP_CNTRL_STATE_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(LASER4_TEMP_CNTRL_SETPOINT_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER,d);
    d.asFloat = 0.1;
    writeRegister(LASER4_TEMP_CNTRL_TOLERANCE_REGISTER,d);
    d.asFloat = 30.0;
    writeRegister(LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER,d);
    d.asFloat = 20.0;
    writeRegister(LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.05;
    writeRegister(LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER,d);
    d.asFloat = 0.2;
    writeRegister(LASER4_TEMP_CNTRL_H_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER4_TEMP_CNTRL_K_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(LASER4_TEMP_CNTRL_TI_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER4_TEMP_CNTRL_TD_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(LASER4_TEMP_CNTRL_B_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(LASER4_TEMP_CNTRL_C_REGISTER,d);
    d.asFloat = 100.0;
    writeRegister(LASER4_TEMP_CNTRL_N_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(LASER4_TEMP_CNTRL_S_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER4_TEMP_CNTRL_FFWD_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(LASER4_TEMP_CNTRL_AMIN_REGISTER,d);
    d.asFloat = 55000.0;
    writeRegister(LASER4_TEMP_CNTRL_AMAX_REGISTER,d);
    d.asFloat = 10000.0;
    writeRegister(LASER4_TEMP_CNTRL_IMAX_REGISTER,d);
    d.asUint = 0x481;
    writeRegister(LASER4_TEC_PRBS_GENPOLY_REGISTER,d);
    d.asFloat = 5000.0;
    writeRegister(LASER4_TEC_PRBS_AMPLITUDE_REGISTER,d);
    d.asFloat = 40000.0;
    writeRegister(LASER4_TEC_PRBS_MEAN_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER4_TEC_MONITOR_REGISTER,d);
    d.asUint = LASER_CURRENT_CNTRL_DisabledState;
    writeRegister(LASER4_CURRENT_CNTRL_STATE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER4_MANUAL_COARSE_CURRENT_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER4_MANUAL_FINE_CURRENT_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER4_CURRENT_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER4_CURRENT_SWEEP_MAX_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER4_CURRENT_SWEEP_INCR_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER4_CURRENT_MONITOR_REGISTER,d);
    d.asFloat = 0.00112789997365;
    writeRegister(CONVERSION_ETALON_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000234289997024;
    writeRegister(CONVERSION_ETALON_THERM_CONSTB_REGISTER,d);
    d.asFloat = 8.72979981636e-008;
    writeRegister(CONVERSION_ETALON_THERM_CONSTC_REGISTER,d);
    d.asFloat = 30000;
    writeRegister(ETALON_THERMISTOR_SERIES_RESISTANCE_REGISTER,d);
    d.asFloat = 0.00112789997365;
    writeRegister(CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000234289997024;
    writeRegister(CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER,d);
    d.asFloat = 8.72979981636e-008;
    writeRegister(CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER,d);
    d.asFloat = 30000;
    writeRegister(WARM_BOX_THERMISTOR_SERIES_RESISTANCE_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(WARM_BOX_TEC_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(WARM_BOX_MANUAL_TEC_REGISTER,d);
    d.asUint = TEMP_CNTRL_DisabledState;
    writeRegister(WARM_BOX_TEMP_CNTRL_STATE_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER,d);
    d.asFloat = 0.1;
    writeRegister(WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER,d);
    d.asFloat = 30.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER,d);
    d.asFloat = 20.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.05;
    writeRegister(WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER,d);
    d.asFloat = 0.2;
    writeRegister(WARM_BOX_TEMP_CNTRL_H_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_K_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_TI_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_TD_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_B_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_C_REGISTER,d);
    d.asFloat = 100.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_N_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_S_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_FFWD_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_AMIN_REGISTER,d);
    d.asFloat = 55000.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_AMAX_REGISTER,d);
    d.asFloat = 10000.0;
    writeRegister(WARM_BOX_TEMP_CNTRL_IMAX_REGISTER,d);
    d.asUint = 0x481;
    writeRegister(WARM_BOX_TEC_PRBS_GENPOLY_REGISTER,d);
    d.asFloat = 5000.0;
    writeRegister(WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER,d);
    d.asFloat = 40000.0;
    writeRegister(WARM_BOX_TEC_PRBS_MEAN_REGISTER,d);
    d.asFloat = 70.0;
    writeRegister(WARM_BOX_MAX_HEATSINK_TEMP_REGISTER,d);
    d.asFloat = 0.00112789997365;
    writeRegister(CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000234289997024;
    writeRegister(CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER,d);
    d.asFloat = 8.72979981636e-008;
    writeRegister(CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER,d);
    d.asFloat = 30000;
    writeRegister(WARM_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER,d);
    d.asFloat = 0.000847030023579;
    writeRegister(CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000205610005651;
    writeRegister(CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER,d);
    d.asFloat = 9.26699996739e-008;
    writeRegister(CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER,d);
    d.asFloat = 124000;
    writeRegister(HOT_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER,d);
    d.asFloat = 0.000847030023579;
    writeRegister(CONVERSION_CAVITY_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000205610005651;
    writeRegister(CONVERSION_CAVITY_THERM_CONSTB_REGISTER,d);
    d.asFloat = 9.26699996739e-008;
    writeRegister(CONVERSION_CAVITY_THERM_CONSTC_REGISTER,d);
    d.asFloat = 124000;
    writeRegister(CAVITY_THERMISTOR_SERIES_RESISTANCE_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(CAVITY_TEC_REGISTER,d);
    d.asFloat = 32768.0;
    writeRegister(CAVITY_MANUAL_TEC_REGISTER,d);
    d.asUint = TEMP_CNTRL_DisabledState;
    writeRegister(CAVITY_TEMP_CNTRL_STATE_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(CAVITY_TEMP_CNTRL_SETPOINT_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER,d);
    d.asFloat = 0.1;
    writeRegister(CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER,d);
    d.asFloat = 30.0;
    writeRegister(CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER,d);
    d.asFloat = 20.0;
    writeRegister(CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.05;
    writeRegister(CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(CAVITY_TEMP_CNTRL_H_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(CAVITY_TEMP_CNTRL_K_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(CAVITY_TEMP_CNTRL_TI_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(CAVITY_TEMP_CNTRL_TD_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(CAVITY_TEMP_CNTRL_B_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(CAVITY_TEMP_CNTRL_C_REGISTER,d);
    d.asFloat = 100.0;
    writeRegister(CAVITY_TEMP_CNTRL_N_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(CAVITY_TEMP_CNTRL_S_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(CAVITY_TEMP_CNTRL_FFWD_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(CAVITY_TEMP_CNTRL_AMIN_REGISTER,d);
    d.asFloat = 55000.0;
    writeRegister(CAVITY_TEMP_CNTRL_AMAX_REGISTER,d);
    d.asFloat = 10000.0;
    writeRegister(CAVITY_TEMP_CNTRL_IMAX_REGISTER,d);
    d.asUint = 0x481;
    writeRegister(CAVITY_TEC_PRBS_GENPOLY_REGISTER,d);
    d.asFloat = 5000.0;
    writeRegister(CAVITY_TEC_PRBS_AMPLITUDE_REGISTER,d);
    d.asFloat = 40000.0;
    writeRegister(CAVITY_TEC_PRBS_MEAN_REGISTER,d);
    d.asFloat = 70.0;
    writeRegister(CAVITY_MAX_HEATSINK_TEMP_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(HEATER_MARK_REGISTER,d);
    d.asFloat = 4000.0;
    writeRegister(HEATER_MANUAL_MARK_REGISTER,d);
    d.asUint = TEMP_CNTRL_DisabledState;
    writeRegister(HEATER_TEMP_CNTRL_STATE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(HEATER_TEMP_CNTRL_SETPOINT_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER,d);
    d.asFloat = 0.1;
    writeRegister(HEATER_TEMP_CNTRL_TOLERANCE_REGISTER,d);
    d.asFloat = 2.0;
    writeRegister(HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER,d);
    d.asFloat = -2.0;
    writeRegister(HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER,d);
    d.asFloat = 0.01;
    writeRegister(HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(HEATER_TEMP_CNTRL_H_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(HEATER_TEMP_CNTRL_K_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(HEATER_TEMP_CNTRL_TI_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(HEATER_TEMP_CNTRL_TD_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(HEATER_TEMP_CNTRL_B_REGISTER,d);
    d.asFloat = 1.0;
    writeRegister(HEATER_TEMP_CNTRL_C_REGISTER,d);
    d.asFloat = 100.0;
    writeRegister(HEATER_TEMP_CNTRL_N_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(HEATER_TEMP_CNTRL_S_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(HEATER_TEMP_CNTRL_AMIN_REGISTER,d);
    d.asFloat = 30000.0;
    writeRegister(HEATER_TEMP_CNTRL_AMAX_REGISTER,d);
    d.asFloat = 10000.0;
    writeRegister(HEATER_TEMP_CNTRL_IMAX_REGISTER,d);
    d.asUint = 0x481;
    writeRegister(HEATER_PRBS_GENPOLY_REGISTER,d);
    d.asFloat = 5000.0;
    writeRegister(HEATER_PRBS_AMPLITUDE_REGISTER,d);
    d.asFloat = 40000.0;
    writeRegister(HEATER_PRBS_MEAN_REGISTER,d);
    d.asFloat = 45.1;
    writeRegister(HEATER_CUTOFF_REGISTER,d);
    d.asInt = 32768;
    writeRegister(CAVITY_PRESSURE_ADC_REGISTER,d);
    d.asFloat = 1.5258789E-2;
    writeRegister(CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER,d);
    d.asInt = 32768;
    writeRegister(AMBIENT_PRESSURE_ADC_REGISTER,d);
    d.asFloat = 1.5258789E-2;
    writeRegister(CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER,d);
    d.asUint = ANALYZER_TUNING_CavityLengthTuningMode;
    writeRegister(ANALYZER_TUNING_MODE_REGISTER,d);
    d.asFloat = 50000.0;
    writeRegister(TUNER_SWEEP_RAMP_HIGH_REGISTER,d);
    d.asFloat = 10000.0;
    writeRegister(TUNER_SWEEP_RAMP_LOW_REGISTER,d);
    d.asFloat = 48000.0;
    writeRegister(TUNER_WINDOW_RAMP_HIGH_REGISTER,d);
    d.asFloat = 12000.0;
    writeRegister(TUNER_WINDOW_RAMP_LOW_REGISTER,d);
    d.asFloat = 1500.0;
    writeRegister(TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER,d);
    d.asFloat = 1500.0;
    writeRegister(TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER,d);
    d.asFloat = 1250.0;
    writeRegister(TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER,d);
    d.asFloat = 1250.0;
    writeRegister(TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER,d);
    d.asUint = 9;
    writeRegister(TUNER_DITHER_MEDIAN_COUNT_REGISTER,d);
    d.asFloat = 0.2;
    writeRegister(RDFITTER_MINLOSS_REGISTER,d);
    d.asFloat = 50.0;
    writeRegister(RDFITTER_MAXLOSS_REGISTER,d);
    d.asUint = 1;
    writeRegister(RDFITTER_IMPROVEMENT_STEPS_REGISTER,d);
    d.asUint = 10;
    writeRegister(RDFITTER_START_SAMPLE_REGISTER,d);
    d.asFloat = 0.85;
    writeRegister(RDFITTER_FRACTIONAL_THRESHOLD_REGISTER,d);
    d.asFloat = 13000;
    writeRegister(RDFITTER_ABSOLUTE_THRESHOLD_REGISTER,d);
    d.asUint = 3500;
    writeRegister(RDFITTER_NUMBER_OF_POINTS_REGISTER,d);
    d.asFloat = 8.0;
    writeRegister(RDFITTER_MAX_E_FOLDINGS_REGISTER,d);
    d.asUint = 2;
    writeRegister(RDFITTER_META_BACKOFF_REGISTER,d);
    d.asUint = 6;
    writeRegister(RDFITTER_META_SAMPLES_REGISTER,d);
    d.asUint = SPECT_CNTRL_IdleState;
    writeRegister(SPECT_CNTRL_STATE_REGISTER,d);
    d.asUint = SPECT_CNTRL_SchemeSingleMode;
    writeRegister(SPECT_CNTRL_MODE_REGISTER,d);
    d.asUint = 0;
    writeRegister(SPECT_CNTRL_ACTIVE_SCHEME_REGISTER,d);
    d.asUint = 0;
    writeRegister(SPECT_CNTRL_NEXT_SCHEME_REGISTER,d);
    d.asUint = 0;
    writeRegister(SPECT_CNTRL_SCHEME_ITER_REGISTER,d);
    d.asUint = 0;
    writeRegister(SPECT_CNTRL_SCHEME_ROW_REGISTER,d);
    d.asUint = 0;
    writeRegister(SPECT_CNTRL_DWELL_COUNT_REGISTER,d);
    d.asUint = 15000;
    writeRegister(SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER,d);
    d.asUint = 100000;
    writeRegister(SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER,d);
    d.asUint = 1000000;
    writeRegister(SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER,d);
    d.asUint = VIRTUAL_LASER_3;
    writeRegister(VIRTUAL_LASER_REGISTER,d);
    d.asFloat = 16400;
    writeRegister(PZT_INCR_PER_CAVITY_FSR,d);
    d.asFloat = 0;
    writeRegister(PZT_OFFSET_UPDATE_FACTOR,d);
    d.asFloat = 0;
    writeRegister(PZT_OFFSET_VIRTUAL_LASER1,d);
    d.asFloat = 0;
    writeRegister(PZT_OFFSET_VIRTUAL_LASER2,d);
    d.asFloat = 0;
    writeRegister(PZT_OFFSET_VIRTUAL_LASER3,d);
    d.asFloat = 0;
    writeRegister(PZT_OFFSET_VIRTUAL_LASER4,d);
    d.asFloat = 0;
    writeRegister(PZT_OFFSET_VIRTUAL_LASER5,d);
    d.asFloat = 0;
    writeRegister(PZT_OFFSET_VIRTUAL_LASER6,d);
    d.asFloat = 0;
    writeRegister(PZT_OFFSET_VIRTUAL_LASER7,d);
    d.asFloat = 0;
    writeRegister(PZT_OFFSET_VIRTUAL_LASER8,d);
    d.asFloat = 0;
    writeRegister(SCHEME_OFFSET_VIRTUAL_LASER1,d);
    d.asFloat = 0;
    writeRegister(SCHEME_OFFSET_VIRTUAL_LASER2,d);
    d.asFloat = 0;
    writeRegister(SCHEME_OFFSET_VIRTUAL_LASER3,d);
    d.asFloat = 0;
    writeRegister(SCHEME_OFFSET_VIRTUAL_LASER4,d);
    d.asFloat = 0;
    writeRegister(SCHEME_OFFSET_VIRTUAL_LASER5,d);
    d.asFloat = 0;
    writeRegister(SCHEME_OFFSET_VIRTUAL_LASER6,d);
    d.asFloat = 0;
    writeRegister(SCHEME_OFFSET_VIRTUAL_LASER7,d);
    d.asFloat = 0;
    writeRegister(SCHEME_OFFSET_VIRTUAL_LASER8,d);
    d.asUint = VALVE_CNTRL_DisabledState;
    writeRegister(VALVE_CNTRL_STATE_REGISTER,d);
    d.asFloat = 140.0;
    writeRegister(VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(VALVE_CNTRL_USER_INLET_VALVE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(VALVE_CNTRL_INLET_VALVE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(VALVE_CNTRL_OUTLET_VALVE_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER,d);
    d.asFloat = 50.0;
    writeRegister(VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER,d);
    d.asFloat = 50.0;
    writeRegister(VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER,d);
    d.asFloat = 0.5;
    writeRegister(VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER,d);
    d.asFloat = 20000.0;
    writeRegister(VALVE_CNTRL_INLET_VALVE_MIN_REGISTER,d);
    d.asFloat = 65000.0;
    writeRegister(VALVE_CNTRL_INLET_VALVE_MAX_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER,d);
    d.asFloat = 50.0;
    writeRegister(VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER,d);
    d.asFloat = 0.5;
    writeRegister(VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER,d);
    d.asFloat = 20000.0;
    writeRegister(VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER,d);
    d.asFloat = 65000.0;
    writeRegister(VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER,d);
    d.asFloat = 1000.0;
    writeRegister(VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER,d);
    d.asUint = VALVE_CNTRL_THRESHOLD_DisabledState;
    writeRegister(VALVE_CNTRL_THRESHOLD_STATE_REGISTER,d);
    d.asFloat = 2000.0;
    writeRegister(VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER,d);
    d.asFloat = 0;
    writeRegister(VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER,d);
    d.asFloat = 0;
    writeRegister(VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER,d);
    d.asFloat = 0;
    writeRegister(VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER,d);
    d.asUint = 0x3F;
    writeRegister(VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER,d);
    d.asUint = 0x0;
    writeRegister(VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER,d);
    d.asInt = -1;
    writeRegister(VALVE_CNTRL_SEQUENCE_STEP_REGISTER,d);
    d.asUint = 0x0;
    writeRegister(VALVE_CNTRL_SOLENOID_VALVES_REGISTER,d);
    d.asUint = 0x0;
    writeRegister(VALVE_CNTRL_MPV_POSITION_REGISTER,d);
    d.asUint = TEC_CNTRL_Disabled;
    writeRegister(TEC_CNTRL_REGISTER,d);
    d.asUint = 0;
    writeRegister(SENTRY_UPPER_LIMIT_TRIPPED_REGISTER,d);
    d.asUint = 0;
    writeRegister(SENTRY_LOWER_LIMIT_TRIPPED_REGISTER,d);
    d.asFloat = 3.0;
    writeRegister(SENTRY_LASER1_TEMPERATURE_MIN_REGISTER,d);
    d.asFloat = 52.0;
    writeRegister(SENTRY_LASER1_TEMPERATURE_MAX_REGISTER,d);
    d.asFloat = 3.0;
    writeRegister(SENTRY_LASER2_TEMPERATURE_MIN_REGISTER,d);
    d.asFloat = 52.0;
    writeRegister(SENTRY_LASER2_TEMPERATURE_MAX_REGISTER,d);
    d.asFloat = 3.0;
    writeRegister(SENTRY_LASER3_TEMPERATURE_MIN_REGISTER,d);
    d.asFloat = 52.0;
    writeRegister(SENTRY_LASER3_TEMPERATURE_MAX_REGISTER,d);
    d.asFloat = 3.0;
    writeRegister(SENTRY_LASER4_TEMPERATURE_MIN_REGISTER,d);
    d.asFloat = 52.0;
    writeRegister(SENTRY_LASER4_TEMPERATURE_MAX_REGISTER,d);
    d.asFloat = 3.0;
    writeRegister(SENTRY_ETALON_TEMPERATURE_MIN_REGISTER,d);
    d.asFloat = 52.0;
    writeRegister(SENTRY_ETALON_TEMPERATURE_MAX_REGISTER,d);
    d.asFloat = 3.0;
    writeRegister(SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER,d);
    d.asFloat = 52.0;
    writeRegister(SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER,d);
    d.asFloat = 3.0;
    writeRegister(SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER,d);
    d.asFloat = 80.0;
    writeRegister(SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER,d);
    d.asFloat = 3.0;
    writeRegister(SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER,d);
    d.asFloat = 85.0;
    writeRegister(SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER,d);
    d.asFloat = 3.0;
    writeRegister(SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER,d);
    d.asFloat = 95.0;
    writeRegister(SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER,d);
    d.asFloat = 5.0;
    writeRegister(SENTRY_DAS_TEMPERATURE_MIN_REGISTER,d);
    d.asFloat = 55.0;
    writeRegister(SENTRY_DAS_TEMPERATURE_MAX_REGISTER,d);
    d.asFloat = -5.0;
    writeRegister(SENTRY_LASER1_CURRENT_MIN_REGISTER,d);
    d.asFloat = 180.0;
    writeRegister(SENTRY_LASER1_CURRENT_MAX_REGISTER,d);
    d.asFloat = -5.0;
    writeRegister(SENTRY_LASER2_CURRENT_MIN_REGISTER,d);
    d.asFloat = 180.0;
    writeRegister(SENTRY_LASER2_CURRENT_MAX_REGISTER,d);
    d.asFloat = -5.0;
    writeRegister(SENTRY_LASER3_CURRENT_MIN_REGISTER,d);
    d.asFloat = 180.0;
    writeRegister(SENTRY_LASER3_CURRENT_MAX_REGISTER,d);
    d.asFloat = -5.0;
    writeRegister(SENTRY_LASER4_CURRENT_MIN_REGISTER,d);
    d.asFloat = 180.0;
    writeRegister(SENTRY_LASER4_CURRENT_MAX_REGISTER,d);
    d.asFloat = -5.0;
    writeRegister(SENTRY_CAVITY_PRESSURE_MIN_REGISTER,d);
    d.asFloat = 900.0;
    writeRegister(SENTRY_CAVITY_PRESSURE_MAX_REGISTER,d);
    d.asFloat = 200.0;
    writeRegister(SENTRY_AMBIENT_PRESSURE_MIN_REGISTER,d);
    d.asFloat = 900.0;
    writeRegister(SENTRY_AMBIENT_PRESSURE_MAX_REGISTER,d);
    d.asUint = FAN_CNTRL_OnState;
    writeRegister(FAN_CNTRL_STATE_REGISTER,d);
    d.asFloat = 25.0;
    writeRegister(FAN_CNTRL_TEMPERATURE_REGISTER,d);
    d.asInt = -300;
    writeRegister(KEEP_ALIVE_REGISTER,d);
    regTypes[NOOP_REGISTER] = uint_type;
    regTypes[VERIFY_INIT_REGISTER] = uint_type;
    regTypes[COMM_STATUS_REGISTER] = uint_type;
    regTypes[TIMESTAMP_LSB_REGISTER] = uint_type;
    regTypes[TIMESTAMP_MSB_REGISTER] = uint_type;
    regTypes[SCHEDULER_CONTROL_REGISTER] = uint_type;
    regTypes[HARDWARE_PRESENT_REGISTER] = uint_type;
    regTypes[RD_IRQ_COUNT_REGISTER] = uint_type;
    regTypes[ACQ_DONE_COUNT_REGISTER] = uint_type;
    regTypes[RD_DATA_MOVING_COUNT_REGISTER] = uint_type;
    regTypes[RD_QDMA_DONE_COUNT_REGISTER] = uint_type;
    regTypes[RD_FITTING_COUNT_REGISTER] = uint_type;
    regTypes[RD_INITIATED_COUNT_REGISTER] = uint_type;
    regTypes[DAS_STATUS_REGISTER] = uint_type;
    regTypes[DAS_TEMPERATURE_REGISTER] = float_type;
    regTypes[HEATER_CNTRL_SENSOR_REGISTER] = float_type;
    regTypes[CONVERSION_LASER1_THERM_CONSTA_REGISTER] = float_type;
    regTypes[CONVERSION_LASER1_THERM_CONSTB_REGISTER] = float_type;
    regTypes[CONVERSION_LASER1_THERM_CONSTC_REGISTER] = float_type;
    regTypes[CONVERSION_LASER1_CURRENT_SLOPE_REGISTER] = float_type;
    regTypes[CONVERSION_LASER1_CURRENT_OFFSET_REGISTER] = float_type;
    regTypes[LASER1_RESISTANCE_REGISTER] = float_type;
    regTypes[LASER1_TEMPERATURE_REGISTER] = float_type;
    regTypes[LASER1_THERMISTOR_SERIES_RESISTANCE_REGISTER] = float_type;
    regTypes[LASER1_TEC_REGISTER] = float_type;
    regTypes[LASER1_MANUAL_TEC_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[LASER1_TEMP_CNTRL_SETPOINT_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_TOLERANCE_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_H_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_K_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_TI_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_TD_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_B_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_C_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_N_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_S_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_FFWD_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_AMIN_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_AMAX_REGISTER] = float_type;
    regTypes[LASER1_TEMP_CNTRL_IMAX_REGISTER] = float_type;
    regTypes[LASER1_TEC_PRBS_GENPOLY_REGISTER] = uint_type;
    regTypes[LASER1_TEC_PRBS_AMPLITUDE_REGISTER] = float_type;
    regTypes[LASER1_TEC_PRBS_MEAN_REGISTER] = float_type;
    regTypes[LASER1_TEC_MONITOR_REGISTER] = float_type;
    regTypes[LASER1_CURRENT_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[LASER1_MANUAL_COARSE_CURRENT_REGISTER] = float_type;
    regTypes[LASER1_MANUAL_FINE_CURRENT_REGISTER] = float_type;
    regTypes[LASER1_CURRENT_SWEEP_MIN_REGISTER] = float_type;
    regTypes[LASER1_CURRENT_SWEEP_MAX_REGISTER] = float_type;
    regTypes[LASER1_CURRENT_SWEEP_INCR_REGISTER] = float_type;
    regTypes[LASER1_CURRENT_MONITOR_REGISTER] = float_type;
    regTypes[CONVERSION_LASER2_THERM_CONSTA_REGISTER] = float_type;
    regTypes[CONVERSION_LASER2_THERM_CONSTB_REGISTER] = float_type;
    regTypes[CONVERSION_LASER2_THERM_CONSTC_REGISTER] = float_type;
    regTypes[CONVERSION_LASER2_CURRENT_SLOPE_REGISTER] = float_type;
    regTypes[CONVERSION_LASER2_CURRENT_OFFSET_REGISTER] = float_type;
    regTypes[LASER2_RESISTANCE_REGISTER] = float_type;
    regTypes[LASER2_TEMPERATURE_REGISTER] = float_type;
    regTypes[LASER2_THERMISTOR_SERIES_RESISTANCE_REGISTER] = float_type;
    regTypes[LASER2_TEC_REGISTER] = float_type;
    regTypes[LASER2_MANUAL_TEC_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[LASER2_TEMP_CNTRL_SETPOINT_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_TOLERANCE_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_H_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_K_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_TI_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_TD_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_B_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_C_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_N_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_S_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_FFWD_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_AMIN_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_AMAX_REGISTER] = float_type;
    regTypes[LASER2_TEMP_CNTRL_IMAX_REGISTER] = float_type;
    regTypes[LASER2_TEC_PRBS_GENPOLY_REGISTER] = uint_type;
    regTypes[LASER2_TEC_PRBS_AMPLITUDE_REGISTER] = float_type;
    regTypes[LASER2_TEC_PRBS_MEAN_REGISTER] = float_type;
    regTypes[LASER2_TEC_MONITOR_REGISTER] = float_type;
    regTypes[LASER2_CURRENT_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[LASER2_MANUAL_COARSE_CURRENT_REGISTER] = float_type;
    regTypes[LASER2_MANUAL_FINE_CURRENT_REGISTER] = float_type;
    regTypes[LASER2_CURRENT_SWEEP_MIN_REGISTER] = float_type;
    regTypes[LASER2_CURRENT_SWEEP_MAX_REGISTER] = float_type;
    regTypes[LASER2_CURRENT_SWEEP_INCR_REGISTER] = float_type;
    regTypes[LASER2_CURRENT_MONITOR_REGISTER] = float_type;
    regTypes[CONVERSION_LASER3_THERM_CONSTA_REGISTER] = float_type;
    regTypes[CONVERSION_LASER3_THERM_CONSTB_REGISTER] = float_type;
    regTypes[CONVERSION_LASER3_THERM_CONSTC_REGISTER] = float_type;
    regTypes[CONVERSION_LASER3_CURRENT_SLOPE_REGISTER] = float_type;
    regTypes[CONVERSION_LASER3_CURRENT_OFFSET_REGISTER] = float_type;
    regTypes[LASER3_RESISTANCE_REGISTER] = float_type;
    regTypes[LASER3_TEMPERATURE_REGISTER] = float_type;
    regTypes[LASER3_THERMISTOR_SERIES_RESISTANCE_REGISTER] = float_type;
    regTypes[LASER3_TEC_REGISTER] = float_type;
    regTypes[LASER3_MANUAL_TEC_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[LASER3_TEMP_CNTRL_SETPOINT_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_TOLERANCE_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_H_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_K_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_TI_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_TD_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_B_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_C_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_N_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_S_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_FFWD_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_AMIN_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_AMAX_REGISTER] = float_type;
    regTypes[LASER3_TEMP_CNTRL_IMAX_REGISTER] = float_type;
    regTypes[LASER3_TEC_PRBS_GENPOLY_REGISTER] = uint_type;
    regTypes[LASER3_TEC_PRBS_AMPLITUDE_REGISTER] = float_type;
    regTypes[LASER3_TEC_PRBS_MEAN_REGISTER] = float_type;
    regTypes[LASER3_TEC_MONITOR_REGISTER] = float_type;
    regTypes[LASER3_CURRENT_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[LASER3_MANUAL_COARSE_CURRENT_REGISTER] = float_type;
    regTypes[LASER3_MANUAL_FINE_CURRENT_REGISTER] = float_type;
    regTypes[LASER3_CURRENT_SWEEP_MIN_REGISTER] = float_type;
    regTypes[LASER3_CURRENT_SWEEP_MAX_REGISTER] = float_type;
    regTypes[LASER3_CURRENT_SWEEP_INCR_REGISTER] = float_type;
    regTypes[LASER3_CURRENT_MONITOR_REGISTER] = float_type;
    regTypes[CONVERSION_LASER4_THERM_CONSTA_REGISTER] = float_type;
    regTypes[CONVERSION_LASER4_THERM_CONSTB_REGISTER] = float_type;
    regTypes[CONVERSION_LASER4_THERM_CONSTC_REGISTER] = float_type;
    regTypes[CONVERSION_LASER4_CURRENT_SLOPE_REGISTER] = float_type;
    regTypes[CONVERSION_LASER4_CURRENT_OFFSET_REGISTER] = float_type;
    regTypes[LASER4_RESISTANCE_REGISTER] = float_type;
    regTypes[LASER4_TEMPERATURE_REGISTER] = float_type;
    regTypes[LASER4_THERMISTOR_SERIES_RESISTANCE_REGISTER] = float_type;
    regTypes[LASER4_TEC_REGISTER] = float_type;
    regTypes[LASER4_MANUAL_TEC_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[LASER4_TEMP_CNTRL_SETPOINT_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_TOLERANCE_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_H_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_K_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_TI_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_TD_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_B_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_C_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_N_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_S_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_FFWD_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_AMIN_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_AMAX_REGISTER] = float_type;
    regTypes[LASER4_TEMP_CNTRL_IMAX_REGISTER] = float_type;
    regTypes[LASER4_TEC_PRBS_GENPOLY_REGISTER] = uint_type;
    regTypes[LASER4_TEC_PRBS_AMPLITUDE_REGISTER] = float_type;
    regTypes[LASER4_TEC_PRBS_MEAN_REGISTER] = float_type;
    regTypes[LASER4_TEC_MONITOR_REGISTER] = float_type;
    regTypes[LASER4_CURRENT_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[LASER4_MANUAL_COARSE_CURRENT_REGISTER] = float_type;
    regTypes[LASER4_MANUAL_FINE_CURRENT_REGISTER] = float_type;
    regTypes[LASER4_CURRENT_SWEEP_MIN_REGISTER] = float_type;
    regTypes[LASER4_CURRENT_SWEEP_MAX_REGISTER] = float_type;
    regTypes[LASER4_CURRENT_SWEEP_INCR_REGISTER] = float_type;
    regTypes[LASER4_CURRENT_MONITOR_REGISTER] = float_type;
    regTypes[CONVERSION_ETALON_THERM_CONSTA_REGISTER] = float_type;
    regTypes[CONVERSION_ETALON_THERM_CONSTB_REGISTER] = float_type;
    regTypes[CONVERSION_ETALON_THERM_CONSTC_REGISTER] = float_type;
    regTypes[ETALON_RESISTANCE_REGISTER] = float_type;
    regTypes[ETALON_TEMPERATURE_REGISTER] = float_type;
    regTypes[ETALON_THERMISTOR_SERIES_RESISTANCE_REGISTER] = float_type;
    regTypes[CONVERSION_WARM_BOX_THERM_CONSTA_REGISTER] = float_type;
    regTypes[CONVERSION_WARM_BOX_THERM_CONSTB_REGISTER] = float_type;
    regTypes[CONVERSION_WARM_BOX_THERM_CONSTC_REGISTER] = float_type;
    regTypes[WARM_BOX_RESISTANCE_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMPERATURE_REGISTER] = float_type;
    regTypes[WARM_BOX_THERMISTOR_SERIES_RESISTANCE_REGISTER] = float_type;
    regTypes[WARM_BOX_TEC_REGISTER] = float_type;
    regTypes[WARM_BOX_MANUAL_TEC_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_H_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_K_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_TI_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_TD_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_B_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_C_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_N_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_S_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_FFWD_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_AMIN_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_AMAX_REGISTER] = float_type;
    regTypes[WARM_BOX_TEMP_CNTRL_IMAX_REGISTER] = float_type;
    regTypes[WARM_BOX_TEC_PRBS_GENPOLY_REGISTER] = uint_type;
    regTypes[WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER] = float_type;
    regTypes[WARM_BOX_TEC_PRBS_MEAN_REGISTER] = float_type;
    regTypes[WARM_BOX_MAX_HEATSINK_TEMP_REGISTER] = float_type;
    regTypes[CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTA_REGISTER] = float_type;
    regTypes[CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTB_REGISTER] = float_type;
    regTypes[CONVERSION_WARM_BOX_HEATSINK_THERM_CONSTC_REGISTER] = float_type;
    regTypes[WARM_BOX_HEATSINK_RESISTANCE_REGISTER] = float_type;
    regTypes[WARM_BOX_HEATSINK_TEMPERATURE_REGISTER] = float_type;
    regTypes[WARM_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER] = float_type;
    regTypes[CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER] = float_type;
    regTypes[CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER] = float_type;
    regTypes[CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER] = float_type;
    regTypes[HOT_BOX_HEATSINK_RESISTANCE_REGISTER] = float_type;
    regTypes[HOT_BOX_HEATSINK_TEMPERATURE_REGISTER] = float_type;
    regTypes[HOT_BOX_HEATSINK_THERMISTOR_SERIES_RESISTANCE_REGISTER] = float_type;
    regTypes[CONVERSION_CAVITY_THERM_CONSTA_REGISTER] = float_type;
    regTypes[CONVERSION_CAVITY_THERM_CONSTB_REGISTER] = float_type;
    regTypes[CONVERSION_CAVITY_THERM_CONSTC_REGISTER] = float_type;
    regTypes[CAVITY_RESISTANCE_REGISTER] = float_type;
    regTypes[CAVITY_TEMPERATURE_REGISTER] = float_type;
    regTypes[CAVITY_THERMISTOR_SERIES_RESISTANCE_REGISTER] = float_type;
    regTypes[CAVITY_TEC_REGISTER] = float_type;
    regTypes[CAVITY_MANUAL_TEC_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[CAVITY_TEMP_CNTRL_SETPOINT_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_H_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_K_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_TI_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_TD_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_B_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_C_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_N_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_S_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_FFWD_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_AMIN_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_AMAX_REGISTER] = float_type;
    regTypes[CAVITY_TEMP_CNTRL_IMAX_REGISTER] = float_type;
    regTypes[CAVITY_TEC_PRBS_GENPOLY_REGISTER] = uint_type;
    regTypes[CAVITY_TEC_PRBS_AMPLITUDE_REGISTER] = float_type;
    regTypes[CAVITY_TEC_PRBS_MEAN_REGISTER] = float_type;
    regTypes[CAVITY_MAX_HEATSINK_TEMP_REGISTER] = float_type;
    regTypes[HEATER_MARK_REGISTER] = float_type;
    regTypes[HEATER_MANUAL_MARK_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[HEATER_TEMP_CNTRL_SETPOINT_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_TOLERANCE_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_H_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_K_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_TI_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_TD_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_B_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_C_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_N_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_S_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_AMIN_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_AMAX_REGISTER] = float_type;
    regTypes[HEATER_TEMP_CNTRL_IMAX_REGISTER] = float_type;
    regTypes[HEATER_PRBS_GENPOLY_REGISTER] = uint_type;
    regTypes[HEATER_PRBS_AMPLITUDE_REGISTER] = float_type;
    regTypes[HEATER_PRBS_MEAN_REGISTER] = float_type;
    regTypes[HEATER_CUTOFF_REGISTER] = float_type;
    regTypes[CAVITY_PRESSURE_ADC_REGISTER] = int_type;
    regTypes[CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER] = float_type;
    regTypes[CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER] = float_type;
    regTypes[CAVITY_PRESSURE_REGISTER] = float_type;
    regTypes[AMBIENT_PRESSURE_ADC_REGISTER] = int_type;
    regTypes[CONVERSION_AMBIENT_PRESSURE_SCALING_REGISTER] = float_type;
    regTypes[CONVERSION_AMBIENT_PRESSURE_OFFSET_REGISTER] = float_type;
    regTypes[AMBIENT_PRESSURE_REGISTER] = float_type;
    regTypes[ANALYZER_TUNING_MODE_REGISTER] = uint_type;
    regTypes[TUNER_SWEEP_RAMP_HIGH_REGISTER] = float_type;
    regTypes[TUNER_SWEEP_RAMP_LOW_REGISTER] = float_type;
    regTypes[TUNER_WINDOW_RAMP_HIGH_REGISTER] = float_type;
    regTypes[TUNER_WINDOW_RAMP_LOW_REGISTER] = float_type;
    regTypes[TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER] = float_type;
    regTypes[TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER] = float_type;
    regTypes[TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER] = float_type;
    regTypes[TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER] = float_type;
    regTypes[TUNER_DITHER_MEDIAN_COUNT_REGISTER] = uint_type;
    regTypes[RDFITTER_MINLOSS_REGISTER] = float_type;
    regTypes[RDFITTER_MAXLOSS_REGISTER] = float_type;
    regTypes[RDFITTER_LATEST_LOSS_REGISTER] = float_type;
    regTypes[RDFITTER_IMPROVEMENT_STEPS_REGISTER] = uint_type;
    regTypes[RDFITTER_START_SAMPLE_REGISTER] = uint_type;
    regTypes[RDFITTER_FRACTIONAL_THRESHOLD_REGISTER] = float_type;
    regTypes[RDFITTER_ABSOLUTE_THRESHOLD_REGISTER] = float_type;
    regTypes[RDFITTER_NUMBER_OF_POINTS_REGISTER] = uint_type;
    regTypes[RDFITTER_MAX_E_FOLDINGS_REGISTER] = float_type;
    regTypes[RDFITTER_META_BACKOFF_REGISTER] = uint_type;
    regTypes[RDFITTER_META_SAMPLES_REGISTER] = uint_type;
    regTypes[SPECT_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[SPECT_CNTRL_MODE_REGISTER] = uint_type;
    regTypes[SPECT_CNTRL_ACTIVE_SCHEME_REGISTER] = uint_type;
    regTypes[SPECT_CNTRL_NEXT_SCHEME_REGISTER] = uint_type;
    regTypes[SPECT_CNTRL_SCHEME_ITER_REGISTER] = uint_type;
    regTypes[SPECT_CNTRL_SCHEME_ROW_REGISTER] = uint_type;
    regTypes[SPECT_CNTRL_DWELL_COUNT_REGISTER] = uint_type;
    regTypes[SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER] = uint_type;
    regTypes[SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER] = uint_type;
    regTypes[SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER] = uint_type;
    regTypes[VIRTUAL_LASER_REGISTER] = uint_type;
    regTypes[PZT_INCR_PER_CAVITY_FSR] = float_type;
    regTypes[PZT_OFFSET_UPDATE_FACTOR] = float_type;
    regTypes[PZT_OFFSET_VIRTUAL_LASER1] = float_type;
    regTypes[PZT_OFFSET_VIRTUAL_LASER2] = float_type;
    regTypes[PZT_OFFSET_VIRTUAL_LASER3] = float_type;
    regTypes[PZT_OFFSET_VIRTUAL_LASER4] = float_type;
    regTypes[PZT_OFFSET_VIRTUAL_LASER5] = float_type;
    regTypes[PZT_OFFSET_VIRTUAL_LASER6] = float_type;
    regTypes[PZT_OFFSET_VIRTUAL_LASER7] = float_type;
    regTypes[PZT_OFFSET_VIRTUAL_LASER8] = float_type;
    regTypes[SCHEME_OFFSET_VIRTUAL_LASER1] = float_type;
    regTypes[SCHEME_OFFSET_VIRTUAL_LASER2] = float_type;
    regTypes[SCHEME_OFFSET_VIRTUAL_LASER3] = float_type;
    regTypes[SCHEME_OFFSET_VIRTUAL_LASER4] = float_type;
    regTypes[SCHEME_OFFSET_VIRTUAL_LASER5] = float_type;
    regTypes[SCHEME_OFFSET_VIRTUAL_LASER6] = float_type;
    regTypes[SCHEME_OFFSET_VIRTUAL_LASER7] = float_type;
    regTypes[SCHEME_OFFSET_VIRTUAL_LASER8] = float_type;
    regTypes[VALVE_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_USER_INLET_VALVE_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_INLET_VALVE_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_OUTLET_VALVE_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_INLET_VALVE_MIN_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_INLET_VALVE_MAX_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_THRESHOLD_STATE_REGISTER] = uint_type;
    regTypes[VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER] = float_type;
    regTypes[VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER] = uint_type;
    regTypes[VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER] = uint_type;
    regTypes[VALVE_CNTRL_SEQUENCE_STEP_REGISTER] = int_type;
    regTypes[VALVE_CNTRL_SOLENOID_VALVES_REGISTER] = uint_type;
    regTypes[VALVE_CNTRL_MPV_POSITION_REGISTER] = uint_type;
    regTypes[TEC_CNTRL_REGISTER] = uint_type;
    regTypes[SENTRY_UPPER_LIMIT_TRIPPED_REGISTER] = uint_type;
    regTypes[SENTRY_LOWER_LIMIT_TRIPPED_REGISTER] = uint_type;
    regTypes[SENTRY_LASER1_TEMPERATURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_LASER1_TEMPERATURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_LASER2_TEMPERATURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_LASER2_TEMPERATURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_LASER3_TEMPERATURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_LASER3_TEMPERATURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_LASER4_TEMPERATURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_LASER4_TEMPERATURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_ETALON_TEMPERATURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_ETALON_TEMPERATURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_DAS_TEMPERATURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_DAS_TEMPERATURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_LASER1_CURRENT_MIN_REGISTER] = float_type;
    regTypes[SENTRY_LASER1_CURRENT_MAX_REGISTER] = float_type;
    regTypes[SENTRY_LASER2_CURRENT_MIN_REGISTER] = float_type;
    regTypes[SENTRY_LASER2_CURRENT_MAX_REGISTER] = float_type;
    regTypes[SENTRY_LASER3_CURRENT_MIN_REGISTER] = float_type;
    regTypes[SENTRY_LASER3_CURRENT_MAX_REGISTER] = float_type;
    regTypes[SENTRY_LASER4_CURRENT_MIN_REGISTER] = float_type;
    regTypes[SENTRY_LASER4_CURRENT_MAX_REGISTER] = float_type;
    regTypes[SENTRY_CAVITY_PRESSURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_CAVITY_PRESSURE_MAX_REGISTER] = float_type;
    regTypes[SENTRY_AMBIENT_PRESSURE_MIN_REGISTER] = float_type;
    regTypes[SENTRY_AMBIENT_PRESSURE_MAX_REGISTER] = float_type;
    regTypes[FAN_CNTRL_STATE_REGISTER] = uint_type;
    regTypes[FAN_CNTRL_TEMPERATURE_REGISTER] = float_type;
    regTypes[KEEP_ALIVE_REGISTER] = int_type;
}

int doAction(unsigned int command,unsigned int numInt,void *params,void *env)
{
    switch (command) {
        case ACTION_WRITE_BLOCK:
            return writeBlock(numInt,params,env);
        case ACTION_SET_TIMESTAMP:
            return setTimestamp(numInt,params,env);
        case ACTION_GET_TIMESTAMP:
            return r_getTimestamp(numInt,params,env);
        case ACTION_INIT_RUNQUEUE:
            return initRunqueue(numInt,params,env);
        case ACTION_TEST_SCHEDULER:
            return testScheduler(numInt,params,env);
        case ACTION_STREAM_REGISTER_ASFLOAT:
            return streamRegisterAsFloat(numInt,params,env);
        case ACTION_STREAM_FPGA_REGISTER_ASFLOAT:
            return streamFpgaRegisterAsFloat(numInt,params,env);
        case ACTION_RESISTANCE_TO_TEMPERATURE:
            return r_resistanceToTemperature(numInt,params,env);
        case ACTION_TEMP_CNTRL_SET_COMMAND:
            return r_tempCntrlSetCommand(numInt,params,env);
        case ACTION_APPLY_PID_STEP:
            return r_applyPidStep(numInt,params,env);
        case ACTION_TEMP_CNTRL_LASER1_INIT:
            return r_tempCntrlLaser1Init(numInt,params,env);
        case ACTION_TEMP_CNTRL_LASER1_STEP:
            return r_tempCntrlLaser1Step(numInt,params,env);
        case ACTION_TEMP_CNTRL_LASER2_INIT:
            return r_tempCntrlLaser2Init(numInt,params,env);
        case ACTION_TEMP_CNTRL_LASER2_STEP:
            return r_tempCntrlLaser2Step(numInt,params,env);
        case ACTION_TEMP_CNTRL_LASER3_INIT:
            return r_tempCntrlLaser3Init(numInt,params,env);
        case ACTION_TEMP_CNTRL_LASER3_STEP:
            return r_tempCntrlLaser3Step(numInt,params,env);
        case ACTION_TEMP_CNTRL_LASER4_INIT:
            return r_tempCntrlLaser4Init(numInt,params,env);
        case ACTION_TEMP_CNTRL_LASER4_STEP:
            return r_tempCntrlLaser4Step(numInt,params,env);
        case ACTION_FLOAT_REGISTER_TO_FPGA:
            return r_floatRegisterToFpga(numInt,params,env);
        case ACTION_FPGA_TO_FLOAT_REGISTER:
            return r_fpgaToFloatRegister(numInt,params,env);
        case ACTION_INT_TO_FPGA:
            return r_intToFpga(numInt,params,env);
        case ACTION_CURRENT_CNTRL_LASER1_INIT:
            return r_currentCntrlLaser1Init(numInt,params,env);
        case ACTION_CURRENT_CNTRL_LASER1_STEP:
            return r_currentCntrlLaser1Step(numInt,params,env);
        case ACTION_CURRENT_CNTRL_LASER2_INIT:
            return r_currentCntrlLaser2Init(numInt,params,env);
        case ACTION_CURRENT_CNTRL_LASER2_STEP:
            return r_currentCntrlLaser2Step(numInt,params,env);
        case ACTION_CURRENT_CNTRL_LASER3_INIT:
            return r_currentCntrlLaser3Init(numInt,params,env);
        case ACTION_CURRENT_CNTRL_LASER3_STEP:
            return r_currentCntrlLaser3Step(numInt,params,env);
        case ACTION_CURRENT_CNTRL_LASER4_INIT:
            return r_currentCntrlLaser4Init(numInt,params,env);
        case ACTION_CURRENT_CNTRL_LASER4_STEP:
            return r_currentCntrlLaser4Step(numInt,params,env);
        case ACTION_TEMP_CNTRL_WARM_BOX_INIT:
            return r_tempCntrlWarmBoxInit(numInt,params,env);
        case ACTION_TEMP_CNTRL_WARM_BOX_STEP:
            return r_tempCntrlWarmBoxStep(numInt,params,env);
        case ACTION_TEMP_CNTRL_CAVITY_INIT:
            return r_tempCntrlCavityInit(numInt,params,env);
        case ACTION_TEMP_CNTRL_CAVITY_STEP:
            return r_tempCntrlCavityStep(numInt,params,env);
        case ACTION_HEATER_CNTRL_INIT:
            return r_heaterCntrlInit(numInt,params,env);
        case ACTION_HEATER_CNTRL_STEP:
            return r_heaterCntrlStep(numInt,params,env);
        case ACTION_TUNER_CNTRL_INIT:
            return r_tunerCntrlInit(numInt,params,env);
        case ACTION_TUNER_CNTRL_STEP:
            return r_tunerCntrlStep(numInt,params,env);
        case ACTION_SPECTRUM_CNTRL_INIT:
            return r_spectCntrlInit(numInt,params,env);
        case ACTION_SPECTRUM_CNTRL_STEP:
            return r_spectCntrlStep(numInt,params,env);
        case ACTION_FAN_CNTRL_INIT:
            return r_fanCntrlInit(numInt,params,env);
        case ACTION_FAN_CNTRL_STEP:
            return r_fanCntrlStep(numInt,params,env);
        case ACTION_ACTIVATE_FAN:
            return r_activateFan(numInt,params,env);
        case ACTION_ENV_CHECKER:
            return r_envChecker(numInt,params,env);
        case ACTION_WB_INV_CACHE:
            return r_wbInvCache(numInt,params,env);
        case ACTION_WB_CACHE:
            return r_wbCache(numInt,params,env);
        case ACTION_SCHEDULER_HEARTBEAT:
            return r_schedulerHeartbeat(numInt,params,env);
        case ACTION_SENTRY_INIT:
            return r_sentryInit(numInt,params,env);
        case ACTION_VALVE_CNTRL_INIT:
            return r_valveCntrlInit(numInt,params,env);
        case ACTION_VALVE_CNTRL_STEP:
            return r_valveCntrlStep(numInt,params,env);
        case ACTION_MODIFY_VALVE_PUMP_TEC:
            return r_modifyValvePumpTec(numInt,params,env);
        case ACTION_PULSE_GENERATOR:
            return r_pulseGenerator(numInt,params,env);
        case ACTION_FILTER:
            return r_filter(numInt,params,env);
        case ACTION_DS1631_READTEMP:
            return r_ds1631_readTemp(numInt,params,env);
        case ACTION_READ_THERMISTOR_RESISTANCE:
            return r_read_thermistor_resistance(numInt,params,env);
        case ACTION_READ_LASER_CURRENT:
            return r_read_laser_current(numInt,params,env);
        case ACTION_UPDATE_WLMSIM_LASER_TEMP:
            return r_update_wlmsim_laser_temp(numInt,params,env);
        case ACTION_SIMULATE_LASER_CURRENT_READING:
            return r_simulate_laser_current_reading(numInt,params,env);
        case ACTION_READ_PRESSURE_ADC:
            return r_read_pressure_adc(numInt,params,env);
        case ACTION_ADC_TO_PRESSURE:
            return r_adc_to_pressure(numInt,params,env);
        case ACTION_SET_INLET_VALVE:
            return r_set_inlet_valve(numInt,params,env);
        case ACTION_SET_OUTLET_VALVE:
            return r_set_outlet_valve(numInt,params,env);
        case ACTION_INTERPOLATOR_SET_TARGET:
            return r_interpolator_set_target(numInt,params,env);
        case ACTION_INTERPOLATOR_STEP:
            return r_interpolator_step(numInt,params,env);
        case ACTION_EEPROM_WRITE:
            return r_eeprom_write(numInt,params,env);
        case ACTION_EEPROM_READ:
            return r_eeprom_read(numInt,params,env);
        case ACTION_EEPROM_READY:
            return r_eeprom_ready(numInt,params,env);
        case ACTION_I2C_CHECK:
            return r_i2c_check(numInt,params,env);
        case ACTION_NUDGE_TIMESTAMP:
            return nudgeTimestamp(numInt,params,env);
        case ACTION_EEPROM_WRITE_LOW_LEVEL:
            return r_eeprom_write_low_level(numInt,params,env);
        case ACTION_EEPROM_READ_LOW_LEVEL:
            return r_eeprom_read_low_level(numInt,params,env);
        case ACTION_EEPROM_READY_LOW_LEVEL:
            return r_eeprom_ready_low_level(numInt,params,env);
        case ACTION_FLOAT_ARITHMETIC:
            return r_float_arithmetic(numInt,params,env);
        case ACTION_GET_SCOPE_TRACE:
            return r_get_scope_trace(numInt,params,env);
        case ACTION_RELEASE_SCOPE_TRACE:
            return r_release_scope_trace(numInt,params,env);
        default:
            return ERROR_BAD_COMMAND;
    }
}

