/*
 * FILE:
 *   i2cEeprom.h
 *
 * DESCRIPTION:
 *   Routines to communicate with I2C EEPROMs
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   17-Feb-2010  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _I2CEEPROM_H_
#define  _I2CEEPROM_H_

int eeprom_write(I2C_device *i2c,unsigned short address,unsigned char *buffer, int nbytes);
int eeprom_busy(I2C_device *i2c);
int eeprom_read(I2C_device *i2c,unsigned short address,unsigned char *buffer, int nbytes);

#endif
