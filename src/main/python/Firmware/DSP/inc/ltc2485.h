/*
 * FILE:
 *   ltc2485.h
 *
 * DESCRIPTION:
 *   Routines to communicate with LTC2485
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   10-Jun-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _LTC2485_H_
#define  _LTC2485_H_

void ltc2485_configure(I2C_device *i2c,int selectTemp,int rejectCode,int speed);
int ltc2485_getData(I2C_device *i2c,int *flags);
#endif
