/*
 * FILE:
 *   ltc2451.h
 *
 * DESCRIPTION:
 *   Routines to communicate with LTC2451
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   12-Jun-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _LTC2451_H_
#define  _LTC2451_H_

int  ltc2451_getData(I2C_device *i2c);
void ltc2451_set_speed(I2C_device *i2c, int low_speed);

#endif
