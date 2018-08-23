/*
 * FILE:
 *   adxl345.h
 *
 * DESCRIPTION:
 *   Routines to communicate with ADXL345 three axis accelerometer
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   9-Sep-2014  sze  Initial version.
 *
 *  Copyright (c) 2014 Picarro, Inc. All rights reserved
 */
#ifndef  _ADXL345_H_
#define  _ADXL345_H_

int adxl345_read_register(I2C_device *i2c, Uint8 reg, int nbytes);
int adxl345_write_register(I2C_device *i2c, Uint8 reg, unsigned int data, int nbytes);
int adxl345_read_accel(I2C_device *i2c, short int *ax, short int *ay, short int *az);

#endif
