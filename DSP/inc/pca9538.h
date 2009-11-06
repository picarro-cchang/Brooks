/*
 * FILE:
 *   pca9538.h
 *
 * DESCRIPTION:
 *   Routines to communicate with PC9538 I2C to parallel port
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   4-Nov-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _PCA9538_H_
#define  _PCA9538_H_

void pca9538_wrConfig(I2C_devAddr *i2c, unsigned char byte);
void pca9538_wrPolarity(I2C_devAddr *i2c, unsigned char byte);
void pca9538_wrOutput(I2C_devAddr *i2c, unsigned char byte);
int pca9538_rdInput(I2C_devAddr *i2c);

#endif
