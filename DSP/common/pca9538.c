/*
 * FILE:
 *   pca9538.c
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
#include <std.h>
#include <tsk.h>
#include "i2c_dsp.h"
#include "pca9538.h"

static unsigned char pca9538_rdByte(I2C_devAddr *i2c)
{
    unsigned char reply;
    I2C_read_bytes(*(i2c->hI2C),i2c->addr,&reply,1);
    return reply;
}

static void pca9538_wrBytes(I2C_devAddr *i2c, Uint8 bytes[],int n)
{
    I2C_write_bytes(*(i2c->hI2C),i2c->addr,bytes,n);
}

void pca9538_wrConfig(I2C_devAddr *i2c, unsigned char byte)
{
    Uint8 bytes[2];
    bytes[0] = 3;
    bytes[1] = byte;
    pca9538_wrBytes(i2c,bytes,2);
    I2C_sendStop(*(i2c->hI2C));
}

void pca9538_wrPolarity(I2C_devAddr *i2c, unsigned char byte)
{
    Uint8 bytes[2];
    bytes[0] = 2;
    bytes[1] = byte;
    pca9538_wrBytes(i2c,bytes,2);
    I2C_sendStop(*(i2c->hI2C));
}

void pca9538_wrOutput(I2C_devAddr *i2c, unsigned char byte)
{
    Uint8 bytes[2];
    bytes[0] = 1;
    bytes[1] = byte;
    pca9538_wrBytes(i2c,bytes,2);
    I2C_sendStop(*(i2c->hI2C));
}

int pca9538_rdInput(I2C_devAddr *i2c)
{
    Uint8 bytes[1];
    bytes[0] = 0;
    pca9538_wrBytes(i2c,bytes,1);
    return pca9538_rdByte(i2c);
}
