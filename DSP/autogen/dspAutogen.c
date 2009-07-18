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
void initRegisters() 
{
    DataType d;
    d.asUint = 0xABCD1234;
    writeRegister(NOOP_REGISTER,d);
    d.asUint = 0x19680511;
    writeRegister(VERIFY_INIT_REGISTER,d);
    d.asUint = 0;
    writeRegister(SCHEDULER_CONTROL_REGISTER,d);
    d.asUint = LOGICPORT_CLOCK_PERIOD_20ns;
    writeRegister(LOGICPORT_CLOCK_PERIOD_REGISTER,d);
    d.asUint = LOGICPORT_SOURCE_RD_ADC;
    writeRegister(LOGICPORT_SOURCE_REGISTER,d);
    d.asUint = 0;
    writeRegister(RD_IRQ_COUNT_REGISTER,d);
    d.asUint = 0;
    writeRegister(ACQ_DONE_COUNT_REGISTER,d);
    d.asFloat = 20.0;
    writeRegister(DAS_TEMPERATURE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(LASER_TEC_MONITOR_TEMPERATURE_REGISTER,d);
    d.asFloat = 0.00112789997365;
    writeRegister(CONVERSION_LASER1_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000234289997024;
    writeRegister(CONVERSION_LASER1_THERM_CONSTB_REGISTER,d);
    d.asFloat = 8.72979981636e-008;
    writeRegister(CONVERSION_LASER1_THERM_CONSTC_REGISTER,d);
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
    d.asFloat = 0.000847030023579;
    writeRegister(CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000205610005651;
    writeRegister(CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTB_REGISTER,d);
    d.asFloat = 9.26699996739e-008;
    writeRegister(CONVERSION_HOT_BOX_HEATSINK_THERM_CONSTC_REGISTER,d);
    d.asFloat = 0.000847030023579;
    writeRegister(CONVERSION_CAVITY_THERM_CONSTA_REGISTER,d);
    d.asFloat = 0.000205610005651;
    writeRegister(CONVERSION_CAVITY_THERM_CONSTB_REGISTER,d);
    d.asFloat = 9.26699996739e-008;
    writeRegister(CONVERSION_CAVITY_THERM_CONSTC_REGISTER,d);
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
    d.asUint = HEATER_CNTRL_DisabledState;
    writeRegister(HEATER_CNTRL_STATE_REGISTER,d);
    d.asFloat = 50.0;
    writeRegister(HEATER_CNTRL_GAIN_REGISTER,d);
    d.asFloat = 20000.0;
    writeRegister(HEATER_CNTRL_QUANTIZE_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(HEATER_CNTRL_UBIAS_SLOPE_REGISTER,d);
    d.asFloat = 40000.0;
    writeRegister(HEATER_CNTRL_UBIAS_OFFSET_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(HEATER_CNTRL_MARK_MIN_REGISTER,d);
    d.asFloat = 8000.0;
    writeRegister(HEATER_CNTRL_MARK_MAX_REGISTER,d);
    d.asFloat = 4000.0;
    writeRegister(HEATER_CNTRL_MANUAL_MARK_REGISTER,d);
    d.asFloat = 0.0;
    writeRegister(HEATER_CNTRL_MARK_REGISTER,d);
    d.asFloat = 50000.0;
    writeRegister(TUNER_SWEEP_RAMP_HIGH_REGISTER,d);
    d.asFloat = 10000.0;
    writeRegister(TUNER_SWEEP_RAMP_LOW_REGISTER,d);
    d.asFloat = 48000.0;
    writeRegister(TUNER_WINDOW_RAMP_HIGH_REGISTER,d);
    d.asFloat = 12000.0;
    writeRegister(TUNER_WINDOW_RAMP_LOW_REGISTER,d);
    d.asFloat = 40000.0;
    writeRegister(TUNER_UP_SLOPE_REGISTER,d);
    d.asFloat = 40000.0;
    writeRegister(TUNER_DOWN_SLOPE_REGISTER,d);
    d.asFloat = 0.2;
    writeRegister(RD_MINLOSS_REGISTER,d);
    d.asFloat = 50.0;
    writeRegister(RD_MAXLOSS_REGISTER,d);
    d.asUint = 1;
    writeRegister(RD_IMPROVEMENT_STEPS_REGISTER,d);
    d.asUint = 10;
    writeRegister(RD_START_SAMPLE_REGISTER,d);
    d.asFloat = 0.85;
    writeRegister(RD_FRACTIONAL_THRESHOLD_REGISTER,d);
    d.asFloat = 13000;
    writeRegister(RD_ABSOLUTE_THRESHOLD_REGISTER,d);
    d.asUint = 3500;
    writeRegister(RD_NUMBER_OF_POINTS_REGISTER,d);
    d.asFloat = 8.0;
    writeRegister(RD_MAX_E_FOLDINGS_REGISTER,d);
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
        case ACTION_STREAM_REGISTER:
            return streamRegister(numInt,params,env);
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
        case ACTION_ENV_CHECKER:
            return r_envChecker(numInt,params,env);
        case ACTION_PULSE_GENERATOR:
            return r_pulseGenerator(numInt,params,env);
        case ACTION_FILTER:
            return r_filter(numInt,params,env);
        case ACTION_DS1631_READTEMP:
            return r_ds1631_readTemp(numInt,params,env);
        case ACTION_LASER_TEC_IMON:
            return r_laser_tec_imon(numInt,params,env);
        case ACTION_READ_LASER_TEC_MONITORS:
            return r_read_laser_tec_monitors(numInt,params,env);
        case ACTION_READ_LASER_THERMISTOR_RESISTANCE:
            return r_read_laser_thermistor_resistance(numInt,params,env);
        case ACTION_READ_LASER_CURRENT:
            return r_read_laser_current(numInt,params,env);
        default:
            return ERROR_BAD_COMMAND;
    }
}

