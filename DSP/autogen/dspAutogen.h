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
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */
#ifndef _DSP_AUTOGEN_H
#define _DSP_AUTOGEN_H

#include "interface.h"

void initRegisters(void);
extern RegTypes regTypes[398];
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
int r_envChecker(unsigned int numInt,void *params,void *env);
int r_wbInvCache(unsigned int numInt,void *params,void *env);
int r_wbCache(unsigned int numInt,void *params,void *env);
int r_schedulerHeartbeat(unsigned int numInt,void *params,void *env);
int r_sentryInit(unsigned int numInt,void *params,void *env);
int r_valveCntrlInit(unsigned int numInt,void *params,void *env);
int r_valveCntrlStep(unsigned int numInt,void *params,void *env);
int r_modifyValvePumpTec(unsigned int numInt,void *params,void *env);
int r_pulseGenerator(unsigned int numInt,void *params,void *env);
int r_filter(unsigned int numInt,void *params,void *env);
int r_ds1631_readTemp(unsigned int numInt,void *params,void *env);
int r_laser_tec_imon(unsigned int numInt,void *params,void *env);
int r_read_laser_tec_monitors(unsigned int numInt,void *params,void *env);
int r_read_laser_thermistor_resistance(unsigned int numInt,void *params,void *env);
int r_read_etalon_thermistor_resistance(unsigned int numInt,void *params,void *env);
int r_read_warm_box_thermistor_resistance(unsigned int numInt,void *params,void *env);
int r_read_warm_box_heatsink_thermistor_resistance(unsigned int numInt,void *params,void *env);
int r_read_cavity_thermistor_resistance(unsigned int numInt,void *params,void *env);
int r_read_hot_box_heatsink_thermistor_resistance(unsigned int numInt,void *params,void *env);
int r_read_laser_current(unsigned int numInt,void *params,void *env);
int r_update_wlmsim_laser_temp(unsigned int numInt,void *params,void *env);
int r_simulate_laser_current_reading(unsigned int numInt,void *params,void *env);
int r_read_cavity_pressure_adc(unsigned int numInt,void *params,void *env);
int r_read_ambient_pressure_adc(unsigned int numInt,void *params,void *env);
int r_adc_to_pressure(unsigned int numInt,void *params,void *env);
int r_set_inlet_valve(unsigned int numInt,void *params,void *env);
int r_set_outlet_valve(unsigned int numInt,void *params,void *env);
#endif
