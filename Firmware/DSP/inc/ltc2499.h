/*
 * FILE:
 *   ltc2499.h
 *
 * DESCRIPTION:
 *   Routines to communicate with LTC2499 16 channel ADC
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   8-May-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _LTC2499_H_
#define  _LTC2499_H_

void ltc2499_configure(I2C_device *i2c,int single,int channel,int selectTemp,int rejectCode,int speed);
int ltc2499_getData(I2C_device *i2c,int *flags);
#endif
