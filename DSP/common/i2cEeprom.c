/*
 * FILE:
 *   i2cEeprom.c
 *
 * DESCRIPTION:
 *   Routines to communicate with I2C EEPROMs
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   17-Feb-2010  sze  Initial version.
 *
 *  Copyright (c) 2010 Picarro, Inc. All rights reserved
 */
#include <std.h>
#include <tsk.h>
#include "dspAutogen.h"
#include "fpga.h"
#include "i2c_dsp.h"
#include "i2cEeprom.h"
#include "registers.h"

static int diag_bit = 0;

int eeprom_send_address(I2C_device *i2c,unsigned short address)
{
    int loops;
    unsigned char data[2];
    data[0] = (address>>8) & 0xFF;
    data[1] = address & 0xFF;
    for (loops=0; loops<10000; loops++);
    // Toggle bit 3 of kernel diag register for debugging I2C EEPROM
    diag_bit = !diag_bit;
    changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 3, 1, diag_bit);
    return I2C_write_bytes(hI2C[i2c->chain],i2c->addr,data,2);
}

int eeprom_write(I2C_device *i2c,unsigned short address,unsigned char *buffer, int nbytes)
// Write up to 64 bytes to the EEPROM at location address. These data must all fit in a single page.
//  Call eeprom_busy to check when data have been written.
{
    unsigned short lastAddress = address+nbytes-1;
    int stat;
    
    if ((address & 0xFFC0) != (lastAddress & 0xFFC0)) {
        message_puts("Page error in eeprom_write");
        return I2C_BADPAGE;
    }
    if (0 != (stat = eeprom_send_address(i2c,address))) {
        message_puts("eeprom_send_address failed in eeprom_write");
        return stat;
    }
    // We need to write the data immediately following the address, with no I2C address info
    stat = I2C_write_bytes_nostart(hI2C[i2c->chain],buffer,nbytes);
    I2C_sendStop(hI2C[i2c->chain]);
    if (0 != stat) {
        message_puts("eeprom send data failed in eeprom_write");
        return stat;
    }
    return 0;
}

int eeprom_busy(I2C_device *i2c)
{
    unsigned char buffer[1];
    return I2C_NACK == I2C_write_bytes(hI2C[i2c->chain],i2c->addr,buffer,0);
}

int eeprom_read(I2C_device *i2c,unsigned short address,unsigned char *buffer, int nbytes)
{
    if (eeprom_busy(i2c)) {
        message_puts("Device busy in eeprom_read");
        return I2C_BUSY;
    }
    eeprom_send_address(i2c,address);
    return I2C_read_bytes(hI2C[i2c->chain],i2c->addr,buffer,nbytes);
}
