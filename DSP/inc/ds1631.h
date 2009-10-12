/*
 * FILE:
 *   ds1631.h
 *
 * DESCRIPTION:
 *   Routines to communicate with DS1631 temperature sensor
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   6-May-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _DS1631_H_
#define  _DS1631_H_

void ds1631_reset(I2C_devAddr *i2c);
void ds1631_startConvert(I2C_devAddr *i2c);
void ds1631_writeConfig(I2C_devAddr *i2c,unsigned int w);
unsigned int ds1631_readConfig(I2C_devAddr *i2c);
unsigned int ds1631_readTemperature(I2C_devAddr *i2c);
float ds1631_readTemperatureAsFloat(I2C_devAddr *i2c);

void ds1631_init(I2C_devAddr *i2c);
#endif
