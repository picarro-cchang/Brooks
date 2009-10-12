/*
 * FILE:
 *   pca8574.c
 *
 * DESCRIPTION:
 *   Routines to communicate with PC8574 I2C to parallel port
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   18-Sep-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include <std.h>
#include <tsk.h>
#include "i2c_dsp.h"
#include "pca8574.h"

unsigned char pca8574_rdByte(I2C_devAddr *i2c)
{
    unsigned char reply;
    I2C_read_bytes(*(i2c->hI2C),i2c->addr,&reply,1);
    return reply;
}

void pca8574_wrByte(I2C_devAddr *i2c,unsigned char byte)
{
    I2C_write_bytes(*(i2c->hI2C),i2c->addr,&byte,1);
    I2C_sendStop(*(i2c->hI2C));
}
