/*
 * FILE:
 *   read_flow_sensor.c
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
#include "read_flow_sensor.h"

static int flow_sensor_rdBytes(I2C_device *i2c)
/* Read 2 bytes in high-endian order. Return -1 on I2C error */
{
    Uint8 reply[2];
    unsigned int i, n=2, result=0;
    if (I2C_read_bytes(hI2C[i2c->chain],i2c->addr,reply,n) != 0) return I2C_READ_ERROR;
    for (i=0; i<n; i++) result = (result << 8) | (unsigned int)reply[i];
    return result;
}

int read_flow_sensor(I2C_device *i2c)
{
    return flow_sensor_rdBytes(i2c);
}
