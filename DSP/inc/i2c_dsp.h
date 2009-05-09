/*
 * FILE:
 *   i2c_dsp.h
 *
 * DESCRIPTION:
 *   Routines to communicate with I2C on the DSP
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   6-May-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _I2C_DSP_H_
#define  _I2C_DSP_H_

#include <std.h>
#include <csl_i2c.h>

extern I2C_Handle hI2C0, hI2C1;
int initializeI2C(I2C_Handle hI2c);
int I2C_write_bytes(I2C_Handle hI2c,int i2caddr,Uint8 *buffer,int nbytes);
int I2C_read_bytes(I2C_Handle hI2c,int i2caddr,Uint8 *buffer,int nbytes);
void dspI2CInit();
void setI2C0Mux(int channel);
int fetchI2C0Mux();
int getI2C0Mux();
void setI2C1Mux(int channel);
int fetchI2C1Mux();
int getI2C1Mux();

#endif
