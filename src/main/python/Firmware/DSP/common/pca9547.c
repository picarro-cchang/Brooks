/*
 * FILE:
 *   pca9547.c
 *
 * DESCRIPTION:
 *   Routines to communicate with PC9547 I2C mux
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
#include "pca9547.h"

unsigned int mux1_rdChan()
/* Read channel from I2C multiplexer 1 */
{
    I2C_device *d = &i2c_devices[CHAIN0_MUX];
    Uint8 reply[1];
    I2C_read_bytes(hI2C[d->chain],d->addr,reply,1);
    return reply[0];
}

unsigned int mux2_rdChan()
/* Read channel from I2C multiplexer 2 */
{
    I2C_device *d = &i2c_devices[CHAIN1_MUX];
    Uint8 reply[1];
    I2C_read_bytes(hI2C[d->chain],d->addr,reply,1);
    return reply[0];
}

void mux1_wrChan(unsigned int uchan)
/* Write channel to I2C multiplexer 1 */
{
    I2C_device *d = &i2c_devices[CHAIN0_MUX];
    Uint8 chan[1];
    chan[0] = 0x8 + uchan;
    I2C_write_bytes(hI2C[d->chain],d->addr,chan,1);
    I2C_sendStop(hI2C[d->chain]);
}

void mux2_wrChan(unsigned int uchan)
/* Write channel to I2C multiplexer 2 */
{
    I2C_device *d = &i2c_devices[CHAIN1_MUX];
    Uint8 chan[1];
    chan[0] = 0x8 + uchan;
    I2C_write_bytes(hI2C[d->chain],d->addr,chan,1);
    I2C_sendStop(hI2C[d->chain]);
}
