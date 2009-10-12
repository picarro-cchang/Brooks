/*
 * FILE:
 *   ltc2499.c
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
#include <std.h>
#include <tsk.h>
#include "i2c_dsp.h"
#include "ltc2499.h"

static unsigned int ltc2499_rdBytes(I2C_devAddr *i2c,int n)
/* Read up to 4 bytes in high-endian order returning an unsigned */
{
    Uint8 reply[4];
    unsigned int i, result=0;
    if (n>0 && n<=4)
    {
        I2C_read_bytes(*(i2c->hI2C),i2c->addr,reply,n);
        for (i=0; i<n; i++) result = (result << 8) | (unsigned int)reply[i];
    }
    return result;
}

static void ltc2499_wrBytes(I2C_devAddr *i2c,Uint8 bytes[],int n)
{
    I2C_write_bytes(*(i2c->hI2C),i2c->addr,bytes,n);
    // Do not send stop signal, since this would start a conversion
    // I2C_sendStop(hI2C1);
}

void ltc2499_configure(I2C_devAddr *i2c,int single,int channel,int selectTemp,int rejectCode,int speed)
/* single = 1 for single ended input, 0 for differential input
   For single ended input, channel specifies input channel relative to ground
   For differential input,
      channel n   (for n in 0-7) indicates CH(2n)+ relative to CH(2n+1)-
      channel 8+n (for n in 0-7) indicates CH(2n+1)+ relative to CH(2n)-
   If selectTemp is 0, ADC measures voltage. Otherwise ADC measures temperature.
   rejectCode is 00 for 50Hz/60Hz rejection
                 01 for 50Hz rejection
                 10 for 60Hz rejection
   speed is 0 for normal speed, 1 for double speed (lower resolution) */
{
    Uint8 bytes[2];
    bytes[0] = 0xA0|((single & 1)<<4)|(channel & 0xF);
    bytes[1] = 0x80|((selectTemp & 1)<<6)|((rejectCode & 3) << 4)|((speed & 1) << 3);
    ltc2499_wrBytes(i2c,bytes,2);
}

int ltc2499_getData(I2C_devAddr *i2c,int *flags)
/* *flags = 0 => underflow, 3 => overflow, 1 or 2 => ok */
{
    unsigned int result = ltc2499_rdBytes(i2c,4);
    *flags = result >> 30;
    result = (result & 0x7FFFFFFF) >> 6;
    if (result < 0x1000000) return result;
    else return ((int)result) - 0x2000000;
}
