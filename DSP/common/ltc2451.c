/*
 * FILE:
 *   ltc2451.c
 *
 * DESCRIPTION:
 *   Routines to communicate with LTC2451 ADC
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
#include "ltc2451.h"

unsigned int ltc2451_read(I2C_device *i2c)
/* Read 2 bytes in high-endian order returning an unsigned */
{
    Uint8 reply[2];
    unsigned int result=0;
    I2C_read_bytes(hI2C[i2c->chain],i2c->addr,reply,2);
    result = reply[0];
    result = (result << 8) | reply[1];
    return result;
}

void ltc2451_set_speed(I2C_device *i2c, int low_speed)
/* low_speed is 1 for 30Hz, 0 for 60Hz */
{
    Uint8 bytes[1];
    bytes[0] = low_speed;
    I2C_write_bytes(hI2C[i2c->chain],i2c->addr,bytes,1);
    I2C_sendStop(hI2C[i2c->chain]);
}
