/*
 * FILE:
 *   adxl345.c
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
#include <std.h>
#include <tsk.h>
#include "dspAutogen.h"
#include "i2c_dsp.h"
#include "adxl345.h"

int adxl345_read_register(I2C_device *i2c, Uint8 reg, int nbytes)
/* Read up to 4 bytes in little-endian order from register reg */
{
    Uint8 reply[4];
    int status;
    unsigned int i, result=0;
    if (nbytes>0 && nbytes<=4)
    {
        if ((status=I2C_write_bytes(hI2C[i2c->chain], i2c->addr, &reg, 1))<0) return status;
        if ((status=I2C_read_bytes(hI2C[i2c->chain], i2c->addr, reply, nbytes))<0) return status;
        for (i=0; i<nbytes; i++) result |= ((unsigned int)reply[i]) << (8*i);

    }
    return result;    
}

int adxl345_write_register(I2C_device *i2c, Uint8 reg, unsigned int data, int nbytes)
/* Write up to 3 bytes in little-endian order to register reg */
{
    int i, status;
    Uint8 buffer[4];
    if (nbytes>0 && nbytes<=3)
    {
	    buffer[0] = reg;
	    for (i=0; i<nbytes; i++) {
		    buffer[i+1] = *(((Uint8 *)(&data)) + i);
		}
	    if ((status=I2C_write_bytes(hI2C[i2c->chain], i2c->addr, buffer, nbytes+1))<0) return status;
	    I2C_sendStop(hI2C[i2c->chain]);
	}
    return 0;
}

int adxl345_read_accel(I2C_device *i2c, short int *ax, short int *ay, short int *az)
{
    int status;
    if ((status=adxl345_read_register(i2c, 0x32, 2))<0) return status;
    else *(unsigned short int *)ax = (status & 0xFFFF);
    if ((status=adxl345_read_register(i2c, 0x34, 2))<0) return status;
    else *(unsigned short int *)ay = (status & 0xFFFF);
    if ((status=adxl345_read_register(i2c, 0x36, 2))<0) return status;
    else *(unsigned short int *)az = (status & 0xFFFF);
    return 0;
}
