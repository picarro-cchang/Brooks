/*
 * FILE:
 *   dspAutogen.h
 *
 * DESCRIPTION:
 *   Automatically generated DSP H file for Picarro gas analyzer. DO NOT EDIT.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 *  Copyright (c) 2008-2023 Picarro, Inc. All rights reserved
 */
#ifndef _DSP_AUTOGEN_H
#define _DSP_AUTOGEN_H

#include "interface.h"

typedef struct i2c_device{ int chain; int mux; int addr; } I2C_device;
extern I2C_device i2c_devices[57];

void initRegisters(void);
extern RegTypes regTypes[710];
int doAction(unsigned int command,unsigned int numInt,void *params,void *env);
int writeBlock(unsigned int numInt,void *params,void *env);
int setTimestamp(unsigned int numInt,void *params,void *env);
int r_getTimestamp(unsigned int numInt,void *params,void *env);
int initRunqueue(unsigned int numInt,void *params,void *env);
int testScheduler(unsigned int numInt,void *params,void *env);
int streamRegisterAsFloat(unsigned int numInt,void *params,void *env);
int streamFpgaRegisterAsFloat(unsigned int numInt,void *params,void *env);
int r_resistanceToTemperature(unsigned int numInt,void *params,void *env);
int r_tempCntrlSetCommand(unsigned int numInt,void *params,void *env);
int r_applyPidStep(unsigned int numInt,void *params,void *env);
int r_tempCntrlLaser1Init(unsigned int numInt,void *params,void *env);
int r_tempCntrlLaser1Step(unsigned int numInt,void *params,void *env);
int r_tempCntrlLaser2Init(unsigned int numInt,void *params,void *env);
int r_tempCntrlLaser2Step(unsigned int numInt,void *params,void *env);
int r_tempCntrlLaser3Init(unsigned int numInt,void *params,void *env);
int r_tempCntrlLaser3Step(unsigned int numInt,void *params,void *env);
int r_tempCntrlLaser4Init(unsigned int numInt,void *params,void *env);
int r_tempCntrlLaser4Step(unsigned int numInt,void *params,void *env);
int r_floatRegisterToFpga(unsigned int numInt,void *params,void *env);
int r_fpgaToFloatRegister(unsigned int numInt,void *params,void *env);
int r_intToFpga(unsigned int numInt,void *params,void *env);
int r_currentCntrlLaser1Init(unsigned int numInt,void *params,void *env);
int r_currentCntrlLaser1Step(unsigned int numInt,void *params,void *env);
int r_currentCntrlLaser2Init(unsigned int numInt,void *params,void *env);
int r_currentCntrlLaser2Step(unsigned int numInt,void *params,void *env);
int r_currentCntrlLaser3Init(unsigned int numInt,void *params,void *env);
int r_currentCntrlLaser3Step(unsigned int numInt,void *params,void *env);
int r_currentCntrlLaser4Init(unsigned int numInt,void *params,void *env);
int r_currentCntrlLaser4Step(unsigned int numInt,void *params,void *env);
int r_tempCntrlWarmBoxInit(unsigned int numInt,void *params,void *env);
int r_tempCntrlWarmBoxStep(unsigned int numInt,void *params,void *env);
int r_tempCntrlCavityInit(unsigned int numInt,void *params,void *env);
int r_tempCntrlCavityStep(unsigned int numInt,void *params,void *env);
int r_heaterCntrlInit(unsigned int numInt,void *params,void *env);
int r_heaterCntrlStep(unsigned int numInt,void *params,void *env);
int r_tunerCntrlInit(unsigned int numInt,void *params,void *env);
int r_tunerCntrlStep(unsigned int numInt,void *params,void *env);
int r_spectCntrlInit(unsigned int numInt,void *params,void *env);
int r_spectCntrlStep(unsigned int numInt,void *params,void *env);
int r_fanCntrlInit(unsigned int numInt,void *params,void *env);
int r_fanCntrlStep(unsigned int numInt,void *params,void *env);
int r_activateFan(unsigned int numInt,void *params,void *env);
int r_envChecker(unsigned int numInt,void *params,void *env);
int r_wbInvCache(unsigned int numInt,void *params,void *env);
int r_wbCache(unsigned int numInt,void *params,void *env);
int r_schedulerHeartbeat(unsigned int numInt,void *params,void *env);
int r_sentryInit(unsigned int numInt,void *params,void *env);
int r_valveCntrlInit(unsigned int numInt,void *params,void *env);
int r_valveCntrlStep(unsigned int numInt,void *params,void *env);
int r_peakDetectCntrlInit(unsigned int numInt,void *params,void *env);
int r_peakDetectCntrlStep(unsigned int numInt,void *params,void *env);
int r_modifyValvePumpTec(unsigned int numInt,void *params,void *env);
int r_pulseGenerator(unsigned int numInt,void *params,void *env);
int r_filter(unsigned int numInt,void *params,void *env);
int r_ds1631_readTemp(unsigned int numInt,void *params,void *env);
int r_read_thermistor_resistance(unsigned int numInt,void *params,void *env);
int r_read_laser_current(unsigned int numInt,void *params,void *env);
int r_update_wlmsim_laser_temp(unsigned int numInt,void *params,void *env);
int r_simulate_laser_current_reading(unsigned int numInt,void *params,void *env);
int r_read_pressure_adc(unsigned int numInt,void *params,void *env);
int r_adc_to_pressure(unsigned int numInt,void *params,void *env);
int r_set_inlet_valve(unsigned int numInt,void *params,void *env);
int r_set_outlet_valve(unsigned int numInt,void *params,void *env);
int r_interpolator_set_target(unsigned int numInt,void *params,void *env);
int r_interpolator_step(unsigned int numInt,void *params,void *env);
int r_eeprom_write(unsigned int numInt,void *params,void *env);
int r_eeprom_read(unsigned int numInt,void *params,void *env);
int r_eeprom_ready(unsigned int numInt,void *params,void *env);
int r_i2c_check(unsigned int numInt,void *params,void *env);
int nudgeTimestamp(unsigned int numInt,void *params,void *env);
int r_eeprom_write_low_level(unsigned int numInt,void *params,void *env);
int r_eeprom_read_low_level(unsigned int numInt,void *params,void *env);
int r_eeprom_ready_low_level(unsigned int numInt,void *params,void *env);
int r_float_arithmetic(unsigned int numInt,void *params,void *env);
int r_get_scope_trace(unsigned int numInt,void *params,void *env);
int r_release_scope_trace(unsigned int numInt,void *params,void *env);
int r_read_flow_sensor(unsigned int numInt,void *params,void *env);
int r_rdd_cntrl_init(unsigned int numInt,void *params,void *env);
int r_rdd_cntrl_step(unsigned int numInt,void *params,void *env);
int r_rdd_cntrl_do_command(unsigned int numInt,void *params,void *env);
int r_rdd2_cntrl_init(unsigned int numInt,void *params,void *env);
int r_rdd2_cntrl_step(unsigned int numInt,void *params,void *env);
int r_rdd2_cntrl_do_command(unsigned int numInt,void *params,void *env);
int r_batt_mon_write_byte(unsigned int numInt,void *params,void *env);
int r_batt_mon_read_regs(unsigned int numInt,void *params,void *env);
int r_acc_read_reg(unsigned int numInt,void *params,void *env);
int r_acc_write_reg(unsigned int numInt,void *params,void *env);
int r_acc_read_accel(unsigned int numInt,void *params,void *env);
int r_read_thermistor_resistance_16bit(unsigned int numInt,void *params,void *env);
int r_average_float_registers(unsigned int numInt,void *params,void *env);
int r_update_from_simulators(unsigned int numInt,void *params,void *env);
int r_step_simulators(unsigned int numInt,void *params,void *env);
int r_tempCntrlFilterHeaterInit(unsigned int numInt,void *params,void *env);
int r_tempCntrlFilterHeaterStep(unsigned int numInt,void *params,void *env);
int r_action_sgdbr_program_fpga(unsigned int numInt,void *params,void *env);
int r_read_thermistor_resistance_sgdbr(unsigned int numInt,void *params,void *env);
int r_sgdbr_cntrl_init(unsigned int numInt,void *params,void *env);
int r_sgdbr_cntrl_step(unsigned int numInt,void *params,void *env);
int r_sgdbr_a_set_currents(unsigned int numInt,void *params,void *env);
int r_sgdbr_b_set_currents(unsigned int numInt,void *params,void *env);
int r_sgdbr_c_set_currents(unsigned int numInt,void *params,void *env);
int r_sgdbr_d_set_currents(unsigned int numInt,void *params,void *env);
int r_soa_cntrl_soa1_init(unsigned int numInt,void *params,void *env);
int r_soa_cntrl_soa1_step(unsigned int numInt,void *params,void *env);
int r_soa_cntrl_soa2_init(unsigned int numInt,void *params,void *env);
int r_soa_cntrl_soa2_step(unsigned int numInt,void *params,void *env);
int r_soa_cntrl_soa3_init(unsigned int numInt,void *params,void *env);
int r_soa_cntrl_soa3_step(unsigned int numInt,void *params,void *env);
int r_soa_cntrl_soa4_init(unsigned int numInt,void *params,void *env);
int r_soa_cntrl_soa4_step(unsigned int numInt,void *params,void *env);
int r_read_soa_monitor(unsigned int numInt,void *params,void *env);
int r_set_soa_current(unsigned int numInt,void *params,void *env);
int r_set_soa_temperature(unsigned int numInt,void *params,void *env);
int r_set_soa_control(unsigned int numInt,void *params,void *env);
#endif
