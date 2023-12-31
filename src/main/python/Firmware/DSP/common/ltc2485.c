/*
 * FILE:
 *   ltc2485.c
 *
 * DESCRIPTION:
 *   Routines to communicate with LTC2485 ADC
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   10-Jun-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include <std.h>
#include <tsk.h>
#include "dspAutogen.h"
#include "i2c_dsp.h"
#include "ltc2485.h"

static int ltc2485_rdBytes(I2C_device *i2c, int n)
/* Read up to 4 bytes in high-endian order. Return -1 on I2C error */
{
    Uint8 reply[4];
    unsigned int i, result=0;
    if (n>0 && n<=4)
    {
        if (I2C_read_bytes(hI2C[i2c->chain],i2c->addr,reply,n) != 0) return I2C_READ_ERROR;
        for (i=0; i<n; i++) result = (result << 8) | (unsigned int)reply[i];
    }
    return result;
}

static int ltc2485_wrBytes(I2C_device *i2c, Uint8 bytes[],int n)
{
    return I2C_write_bytes(hI2C[i2c->chain],i2c->addr,bytes,n);
    // Do not send stop signal, since this would start a conversion
}

void ltc2485_configure(I2C_device *i2c, int selectTemp,int rejectCode,int speed)
/*
   If selectTemp is 0, ADC measures voltage. Otherwise ADC measures temperature.
   rejectCode is 00 for 50Hz/60Hz rejection
                 01 for 50Hz rejection
                 10 for 60Hz rejection
   speed is 0 for normal speed, 1 for double speed (lower resolution) */
{
    Uint8 bytes[1];
    bytes[0] = ((selectTemp & 1)<<3)|((rejectCode & 3) << 1)|(speed & 1);
    ltc2485_wrBytes(i2c,bytes,1);
}

int ltc2485_getData(I2C_device *i2c,int *flags)
/* *flags = 0 => underflow, 3 => overflow, 1 or 2 => ok.
   Return value is signed 24 bit integer, with saturation.
   Returns I2C_READ_ERROR on an I2C problem. */
{
    int result = ltc2485_rdBytes(i2c,4);
    if (result == I2C_READ_ERROR) return result;
    *flags = (result >> 30) & 0x3;
    result = (result & 0x7FFFFFFF) >> 6;
    if (*flags == 0) return -0x1000000;
    else if (*flags == 3) return 0xFFFFFF;
    else {
        if (result < 0x1000000) return result;
        else return ((int)result) - 0x2000000;
    }
}
