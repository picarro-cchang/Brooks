/*
 * FILE:
 *   ds1631.c
 *
 * DESCRIPTION:
 *   Routines to communicate with DS1631 temperature sensor
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   6-May-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include <std.h>
#include <tsk.h>
#include "dspAutogen.h"
#include "i2c_dsp.h"
#include "ds1631.h"

static unsigned int ds1631_rdBytes(I2C_device *i2c,Uint8 command,int n)
/* Read up to 4 bytes in high-endian order in response to command,
    returning an unsigned */
{
    Uint8 reply[4];
    unsigned int i, result=0;
    if (n>0 && n<=4)
    {
        I2C_write_bytes(hI2C[i2c->chain],i2c->addr,&command,1);
        I2C_read_bytes(hI2C[i2c->chain],i2c->addr,reply,n);
        for (i=0; i<n; i++) result = (result << 8) | (unsigned int)reply[i];
    }
    return result;
}

static void ds1631_wrBytes(I2C_device *i2c,Uint8 bytes[],int n)
{
    I2C_write_bytes(hI2C[i2c->chain],i2c->addr,bytes,n);
    I2C_sendStop(hI2C[i2c->chain]);
}

static void ds1631_wrByte(I2C_device *i2c,Uint8 byte)
{
    Uint8 bytes[1];
    bytes[0] = byte;
    ds1631_wrBytes(i2c,bytes,1);
}

void ds1631_reset(I2C_device *i2c)
{
    ds1631_wrByte(i2c,0x54);
    // The reset command is NACKed
    I2C_FSETSH(hI2C[i2c->chain],I2CSTR,NACK,CLR);
}

void ds1631_startConvert(I2C_device *i2c)
{
    ds1631_wrByte(i2c,0x51);
}

void ds1631_writeConfig(I2C_device *i2c,unsigned int w)
{
    Uint8 bytes[2];
    bytes[0] = 0xAC;
    bytes[1] = (Uint8)(w&0xFF);
    ds1631_wrBytes(i2c,bytes,2);
}

unsigned int ds1631_readConfig(I2C_device *i2c)
{
    return ds1631_rdBytes(i2c,0xAC,1);
}

unsigned int ds1631_readTemperature(I2C_device *i2c)
{
    return ds1631_rdBytes(i2c,0xAA,2);
}

float ds1631_readTemperatureAsFloat(I2C_device *i2c)
{
    unsigned int temp = ds1631_readTemperature(i2c);
    if (temp < 0x8000) return (float)temp/256.0;
    else return ((float)temp/256.0) - 256.0;
}

void ds1631_init(I2C_device *i2c)
/* Initialize the DS1631 sensor by resetting it, and setting
    up continuous measurements with 12 bit resolution */
{
    int loop;
    ds1631_reset(i2c);
    for (loop=0;loop<2000;loop++);
    ds1631_writeConfig(i2c,0x8c);
    for (loop=0;loop<2000;loop++);
    ds1631_startConvert(i2c);
}
