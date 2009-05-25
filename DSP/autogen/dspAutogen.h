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

void initRegisters(void);
int doAction(unsigned int command,unsigned int numInt,void *params,void *env);
int writeBlock(unsigned int numInt,void *params,void *env);
int setTimestamp(unsigned int numInt,void *params,void *env);
int r_getTimestamp(unsigned int numInt,void *params,void *env);
int initRunqueue(unsigned int numInt,void *params,void *env);
int testScheduler(unsigned int numInt,void *params,void *env);
int streamRegister(unsigned int numInt,void *params,void *env);
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
int r_tempCntrlCavityInit(unsigned int numInt,void *params,void *env);
int r_tempCntrlCavityStep(unsigned int numInt,void *params,void *env);
int r_heaterCntrlInit(unsigned int numInt,void *params,void *env);
int r_heaterCntrlStep(unsigned int numInt,void *params,void *env);
int r_envChecker(unsigned int numInt,void *params,void *env);
int r_pulseGenerator(unsigned int numInt,void *params,void *env);
int r_filter(unsigned int numInt,void *params,void *env);
int r_ds1631_readTemp(unsigned int numInt,void *params,void *env);
int r_laser_tec_imon(unsigned int numInt,void *params,void *env);
int r_read_laser_tec_monitors(unsigned int numInt,void *params,void *env);
#endif
