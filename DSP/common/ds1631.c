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
#include "i2c_dsp.h"
#include "ds1631.h"

static unsigned int ds1631_rdBytes(Uint8 command,int n)
/* Read up to 4 bytes in high-endian order in response to command,
    returning an unsigned */
{
    Uint8 reply[4];
    unsigned int i, result=0;
    if (n>0 && n<=4)
    {
        I2C_write_bytes(hI2C0,0x4E,&command,1);
        I2C_read_bytes(hI2C0,0x4E,reply,n);
        for (i=0; i<n; i++) result = (result << 8) | (unsigned int)reply[i];
    }
    return result;
}

static void ds1631_wrBytes(Uint8 bytes[],int n)
{
    I2C_write_bytes(hI2C0,0x4E,bytes,n);
    I2C_sendStop(hI2C0);
}

static void ds1631_wrByte(Uint8 byte)
{
    Uint8 bytes[1];
    bytes[0] = byte;
    ds1631_wrBytes(bytes,1);
}

void ds1631_reset()
{
    ds1631_wrByte(0x54);
	// The reset command is NACKed
    I2C_FSETSH(hI2C0,I2CSTR,NACK,CLR);
}

void ds1631_startConvert()
{
    ds1631_wrByte(0x51);
}

void ds1631_writeConfig(unsigned int w)
{
    Uint8 bytes[2];
    bytes[0] = 0xAC;
    bytes[1] = (Uint8)(w&0xFF);
    ds1631_wrBytes(bytes,2);
}

unsigned int ds1631_readConfig()
{
    return ds1631_rdBytes(0xAC,1);
}

unsigned int ds1631_readTemperature()
{
    return ds1631_rdBytes(0xAA,2);
}

float ds1631_readTemperatureAsFloat()
{
    unsigned int temp = ds1631_readTemperature();
    if (temp < 0x8000) return (float)temp/256.0;
    else return ((float)temp/256.0) - 256.0;
}

void ds1631_init()
/* Initialize the DS1631 sensor by resetting it, and setting
    up continuous measurements with 12 bit resolution */
{
    int loop;
    ds1631_reset();
	for (loop=0;loop<2000;loop++);
    ds1631_writeConfig(0x8c);
	for (loop=0;loop<2000;loop++);
    ds1631_startConvert();
}
