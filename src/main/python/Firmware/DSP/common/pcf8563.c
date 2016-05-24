/*
 * FILE:
 *   pcf8563.c
 *
 * DESCRIPTION:
 *   Routines to communicate with PCF8563 real-time clock
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   7-May-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include <std.h>
#include <tsk.h>
#include "i2c_dsp.h"
#include "pcf8563.h"

static void pcf8563_rdBytes(Uint8 command,Uint8 bytes[],int n)
/* Read n bytes in response to command */
{
    I2C_write_bytes(hI2C1,0x51,&command,1);
    I2C_read_bytes(hI2C1,0x51,bytes,n);
}

static void pcf8563_wrBytes(Uint8 bytes[],int n)
{
    I2C_write_bytes(hI2C1,0x51,bytes,n);
    I2C_sendStop(hI2C1);
}

static void pcf8563_write(int regNum,int value)
{
    Uint8 bytes[2];
    bytes[0] = regNum;
    bytes[1] = value & 0xFF;
    pcf8563_wrBytes(bytes,2);
}

static unsigned int bin2bcd(unsigned int x)
{
    unsigned int val, y = 0;
    for (val=1; x>0; x=x/10,val<<=4)
        y += (x % 10) * val;
    return y;
}

static unsigned int bcd2bin(unsigned int x)
{
    unsigned int val, y = 0;
    for (val=1; x>0; x>>=4,val*=10)
        y += (x % 16) * val;
    return y;
}

void pcf8563_set_time(unsigned int year,unsigned int month,
                      unsigned int day, unsigned int hours,
                      unsigned int minutes,unsigned int seconds,
                      unsigned int weekday)
/* Set the clock. Note Sunday = 0 .. Saturday = 6,
    January = 1 .. December = 12 */
{
    Uint8 bytes[8];
    bytes[0] = 2;
    bytes[1] = bin2bcd(seconds);
    bytes[2] = bin2bcd(minutes);
    bytes[3] = bin2bcd(hours);
    bytes[4] = bin2bcd(day);
    bytes[5] = weekday;
    bytes[6] = (((year/100) & 1)<<7) | bin2bcd(month);
    bytes[7] = bin2bcd(year % 100);
    pcf8563_wrBytes(bytes,8);
}

void pcf8563_get_time(unsigned int *year,unsigned int *month,
                      unsigned int *day,unsigned int *hours,
                      unsigned int *minutes,unsigned int *seconds,
                      unsigned int *weekday)
{
    Uint8 bytes[7];
    pcf8563_rdBytes(0x2,bytes,7);
    *year = bcd2bin(bytes[6]) + ((bytes[5] & 0x80) ? 1900 : 2000);
    *month = bcd2bin(bytes[5] & 0x1F);
    *day = bcd2bin(bytes[3] & 0x3F);
    *hours = bcd2bin(bytes[2] & 0x3F);
    *minutes = bcd2bin(bytes[1] & 0x7F);
    *seconds = bcd2bin(bytes[0] & 0x7F);
    *weekday = bytes[4] & 0x7;
}

void pcf8563_init()
/* Initialize the PCF8563 */
{
    int loop;
    pcf8563_write(0,0);
    for (loop=0;loop<2000;loop++);
    pcf8563_write(1,0);
    for (loop=0;loop<2000;loop++);
    // Set CLKOUT freq to 1Hz
    pcf8563_write(0xD,0x3);
    for (loop=0;loop<2000;loop++);
    // Set timer source clock frequency to 1/60 Hz
    pcf8563_write(0xE,0x3);
}
