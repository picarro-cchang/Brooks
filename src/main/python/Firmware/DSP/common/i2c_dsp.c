/*
 * FILE:
 *   i2c_dsp.c
 *
 * DESCRIPTION:
 *   Routines to communicate with I2C on the DSP
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
// #include <stdio.h>
#include <sem.h>
#include <tsk.h>
#include "interface.h"
#include "i2c_dsp.h"
#include "registers.h"
#include "dspAutogen.h"
#include "ltc2451.h"
#include "ltc2485.h"
#include "adxl345.h"
#include "pca8574.h"

#define I2C_MAXLOOPS (300)

#define IDEF static inline

I2C_Handle hI2C[2] = {0, 0};
// static char msg[120];
/*
I2C_devAddr logic_eeprom_I2C = {&hI2C0,0x55};
I2C_devAddr wlm_eeprom_I2C = {&hI2C1,0x50};
I2C_devAddr laser_thermistor_I2C = {&hI2C0,0x26};
I2C_devAddr laser_current_I2C = {&hI2C0,0x14};
I2C_devAddr laser_eeprom_I2C = {&hI2C0,0x50};
I2C_devAddr etalon_thermistor_I2C = {&hI2C1,0x27};
I2C_devAddr warm_box_heatsink_thermistor_I2C = {&hI2C1,0x26};
I2C_devAddr warm_box_thermistor_I2C = {&hI2C1,0x15};
I2C_devAddr hot_box_heatsink_thermistor_I2C = {&hI2C0,0x27};
I2C_devAddr cavity_thermistor_I2C = {&hI2C0,0x26};
I2C_devAddr cavity_pressure_I2C = {&hI2C0,0x24};
I2C_devAddr ambient_pressure_I2C = {&hI2C0,0x17};
I2C_devAddr das_temp_sensor_I2C = {&hI2C0,0x4E};
I2C_devAddr valve_pump_tec_I2C_old = {&hI2C1,0x20};
I2C_devAddr valve_pump_tec_I2C_new = {&hI2C1,0x70};
I2C_devAddr laser_tec_current_monitor_I2C = {&hI2C1,0x14};
*/

/*----------------------------------------------------------------------------*/
int I2C0MuxChan = 0;
int I2C1MuxChan = 0;
/*----------------------------------------------------------------------------*/
// Returns 1 if NACK is received, 0 if ACK is received
IDEF Uint32 I2C_nack(I2C_Handle hI2c)
{
    return I2C_FGETH(hI2c, I2CSTR, NACK);
}
/*----------------------------------------------------------------------------*/
// Returns 1 if I2C module registers are ready to be accessed
IDEF Uint32 I2C_ardy(I2C_Handle hI2c)
{
    return I2C_FGETH(hI2c, I2CSTR, ARDY);
}
/*----------------------------------------------------------------------------*/
// Returns 1 if I2C transmit register is empty
IDEF Uint32 I2C_xsmt(I2C_Handle hI2c)
{
    return I2C_FGETH(hI2c, I2CSTR, XSMT);
}
/*----------------------------------------------------------------------------*/
int initializeI2C(I2C_Handle hI2c)
// Initialize I2C port, return I2C_BUSY if I2C bus does not become free
// SYSCLK2 is set to 50/(3+1)*9 = 112.5MHz and the I2C prescaler is set to 0xE=14
//  so the I2C prescaled module clock is 112.5/14 = 8.0357MHz. The
//  high and low durations of SCLK are 1/(ICCH+5) and 1/(ICCL+5) times the prescaled
//  module clock period.
//  With ICCH = 1, this gives a high period of 0.75us and
//  With ICCL = 8, this gives a low period of  1.62us

//  With ICCH = 35, this gives a high period of 4.97us
//  With ICCL = 35, this gives a low period of  4.97us
{
    int loops = 0;
    Uint32 i2coar = I2C_I2COAR_A_OF(0x44);     // Own address
    Uint32 i2cimr = 0x0;                       // Interrupt enable mask
    Uint32 i2cclkl = I2C_I2CCLKL_ICCL_OF(0x9); // I2C Clock divider (low)
    Uint32 i2cclkh = I2C_I2CCLKH_ICCH_OF(0x1); // I2C Clock divider (high)
    Uint32 i2ccnt = I2C_I2CCNT_ICDC_OF(3);     // Transfer 3 words
    Uint32 i2csar = I2C_I2CSAR_A_OF(0x10);     // Slave address
    Uint32 i2cmdr = I2C_I2CMDR_RMK(
        I2C_I2CMDR_NACKMOD_ACK,
        I2C_I2CMDR_FREE_BSTOP,
        I2C_I2CMDR_STT_NONE,
        I2C_I2CMDR_STP_NONE,
        I2C_I2CMDR_MST_MASTER,
        I2C_I2CMDR_TRX_XMT,
        I2C_I2CMDR_XA_7BIT,
        I2C_I2CMDR_RM_REPEAD,
        I2C_I2CMDR_DLB_NONE,
        I2C_I2CMDR_IRS_NRST,
        I2C_I2CMDR_STB_NONE,
        I2C_I2CMDR_FDF_NONE,
        I2C_I2CMDR_BC_BIT8FDF);
    Uint32 i2cpsc = I2C_I2CPSC_IPSC_OF(0xE); // Prescaler
    // Wait for bus to be not busy
    while (I2C_bb(hI2c))
    {
        loops++;
        if (loops >= I2C_MAXLOOPS)
            return I2C_BUSY;
        // TSK_sleep(1);
    };

    I2C_configArgs(hI2c, i2coar, i2cimr, i2cclkl, i2cclkh, i2ccnt, i2csar, i2cmdr, i2cpsc);
    return 0;
}
/*----------------------------------------------------------------------------*/
int getI2CMode(I2C_Handle hI2c)
{
    return I2C_RGETH(hI2c, I2CMDR);
}
/*----------------------------------------------------------------------------*/
int getI2CStatus(I2C_Handle hI2c)
{
    return I2C_RGETH(hI2c, I2CSTR);
}
/*----------------------------------------------------------------------------*/
int I2C_write_bytes(I2C_Handle hI2c, int i2caddr, Uint8 *buffer, int nbytes)
// Send contents of buffer to the device associated with I2C_Handle
// Returns 0 on success. I2C_NACK on NACK error, I2C_NXRDY on I2C_xrdy timeout
//  I2C_NARDY on register access timeout, I2C_BUSY on bus busy timeout
{
    int i, result;
    int loops = 0;
    int gie = IRQ_globalDisable();
    i = 0;

    I2C_outOfReset(hI2c);
    // Set up the slave address of the I2C
    I2C_RSETH(hI2c, I2CSAR, i2caddr);
    // Set up as master transmitter, and send start bit
    I2C_FSETSH(hI2c, I2CMDR, MST, MASTER);
    I2C_FSETSH(hI2c, I2CMDR, TRX, XMT);
    I2C_FSETSH(hI2c, I2CMDR, STT, START);
    while (0 == I2C_nack(hI2c))
    {
        if (0 == I2C_xrdy(hI2c))
        {
            loops++;
            if (loops >= I2C_MAXLOOPS)
            {
                I2C_FSETSH(hI2c, I2CSTR, ICXRDY, CLR);
                /*
                sprintf(msg,"XRDY timeout in I2C_write_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                        hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                message_puts(LOG_LEVEL_INFO,msg);
                */
                message_puts(LOG_LEVEL_INFO, "XRDY timeout in I2C_write_bytes");
                result = I2C_NXRDY;
                goto error;
            }
            // TSK_sleep(1);
            continue;
        }
        if (i >= nbytes)
        {
            // Normal return. Do NOT send stop, in case we need
            //  to follow-up with a read which has a repeat-start
            //  bit.
            loops = 0;
            while (0 == I2C_ardy(hI2c))
            {
                loops++;
                if (loops >= I2C_MAXLOOPS)
                {
                    I2C_FSETSH(hI2c, I2CSTR, ARDY, CLR);
                    /*
                    sprintf(msg,"ARDY timeout in I2C_write_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                                hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                    message_puts(LOG_LEVEL_INFO,msg);
                    */
                    message_puts(LOG_LEVEL_INFO, "ARDY timeout in I2C_write_bytes");
                    result = I2C_NARDY;
                    goto error;
                }
                // TSK_sleep(1);
            }
            result = 0;
            goto done;
        }
        // LOG_printf(&trace,"WriteByte: 0x%x",data[i]);
        I2C_writeByte(hI2c, buffer[i++]);
        loops = 0;
    }
    /* Error return if NACK received. Send stop bit to terminate
    I2C_sendStop(hI2c);
    I2C_FSETSH(hI2c,I2CSTR,NACK,CLR);
    // Clear XRDY flag in case a byte has already been placed
    //  in the I2CDXR. This byte should be discarded in case of a
    //  NACK problem.
    I2C_FSETSH(hI2c,I2CSTR,ICXRDY,CLR);
    */
    I2C_sendStop(hI2c);
    I2C_FSETSH(hI2c, I2CSTR, BB, CLR);
    I2C_FSETSH(hI2c, I2CSTR, NACK, CLR);
    I2C_FSETSH(hI2c, I2CSTR, ICXRDY, CLR);
    /* sprintf(msg,"NACK in I2C_write_bytes, I2CAddr=%x",i2caddr);
    message_puts(LOG_LEVEL_INFO,msg);
    */
    message_puts(LOG_LEVEL_INFO, "NACK in I2C_write_bytes");
    result = I2C_NACK;
    goto error;
error:
    I2C_reset(hI2c);
    IRQ_globalRestore(gie);
    dspI2CInit();
    return result;
done:
    IRQ_globalRestore(gie);
    return result;
}
/*----------------------------------------------------------------------------*/
int I2C_write_bytes_nostart(I2C_Handle hI2c, Uint8 *buffer, int nbytes)
// Continue a write without sending the start byte and the I2C slave address.
//  This is primarily used in conjunction with EEPROM writing code
{
    int i, result;
    int loops = 0;
    int gie = IRQ_globalDisable();
    i = 0;
    while (0 == I2C_nack(hI2c))
    {
        if (0 == I2C_xrdy(hI2c))
        {
            loops++;
            if (loops >= I2C_MAXLOOPS)
            {
                I2C_FSETSH(hI2c, I2CSTR, ICXRDY, CLR);
                /*
                sprintf(msg,"XRDY timeout in I2C_write_bytes_nostart, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d",
                        hI2c,I2C0MuxChan,I2C1MuxChan);
                message_puts(LOG_LEVEL_INFO,msg);
                */
                message_puts(LOG_LEVEL_INFO, "XRDY timeout in I2C_write_bytes_nostart");
                result = I2C_NXRDY;
                goto error;
            }
            // TSK_sleep(1);
            continue;
        }
        if (i >= nbytes)
        {
            // Normal return. Do NOT send stop, in case we need
            //  to follow-up with a read which has a repeat-start
            //  bit.
            loops = 0;
            while (0 == I2C_ardy(hI2c))
            {
                loops++;
                if (loops >= I2C_MAXLOOPS)
                {
                    I2C_FSETSH(hI2c, I2CSTR, ARDY, CLR);
                    /*
                    sprintf(msg,"ARDY timeout in I2C_write_bytes_nostart, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d",
                            hI2c,I2C0MuxChan,I2C1MuxChan);
                    message_puts(LOG_LEVEL_INFO,msg);
                    */
                    message_puts(LOG_LEVEL_INFO, "ARDY timeout in I2C_write_bytes_nostart");
                    result = I2C_NARDY;
                    goto error;
                }
                // TSK_sleep(1);
            }
            result = 0;
            goto done;
        }
        // LOG_printf(&trace,"WriteByte: 0x%x",data[i]);
        I2C_writeByte(hI2c, buffer[i++]);
        loops = 0;
    }
    I2C_sendStop(hI2c);
    I2C_FSETSH(hI2c, I2CSTR, BB, CLR);
    I2C_FSETSH(hI2c, I2CSTR, NACK, CLR);
    I2C_FSETSH(hI2c, I2CSTR, ICXRDY, CLR);
    /*
    sprintf(msg,"NACK timeout in I2C_write_bytes_nostart, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d",
            hI2c,I2C0MuxChan,I2C1MuxChan);
    message_puts(LOG_LEVEL_INFO,msg);
    */
    message_puts(LOG_LEVEL_INFO, "NACK timeout in I2C_write_bytes_nostart");
    result = I2C_NACK;
    goto error;
error:
    I2C_reset(hI2c);
    IRQ_globalRestore(gie);
    dspI2CInit();
    return result;
done:
    IRQ_globalRestore(gie);
    return result;
}
/*----------------------------------------------------------------------------*/
int I2C_read_bytes(I2C_Handle hI2c, int i2caddr, Uint8 *buffer, int nbytes)
// Read nbytes at the device associated with I2C_Handle
// Send ACK after each read except for the last
// Returns 0 on success. I2C_NACK on NACK error, I2C_NRRDY on I2C_rrdy timeout
//  and I2C_NARDY on register access timeout
{
    int i, result;
    int loops;
    int gie = IRQ_globalDisable();

    I2C_outOfReset(hI2c);
    i = 0;
    // Set up the slave address of the I2C
    I2C_RSETH(hI2c, I2CSAR, i2caddr);
    // Set up as master receiver, and send start bit
    I2C_FSETSH(hI2c, I2CMDR, MST, MASTER);
    I2C_FSETSH(hI2c, I2CMDR, TRX, RCV);
    I2C_FSETSH(hI2c, I2CMDR, STT, START);
    // I2C_start(hI2c);
    while (0 == I2C_nack(hI2c))
    {
        while (i < nbytes - 1)
        {
            loops = 0;
            while (0 == I2C_rrdy(hI2c))
            {
                loops++;
                if (loops >= 1000 * I2C_MAXLOOPS)
                {
                    // Go through here on timeout

                    // sprintf(msg,"RRDY (n-1) timeout in I2C_read_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                    //         hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                    // message_puts(LOG_LEVEL_INFO,msg);

                    message_puts(LOG_LEVEL_INFO, "RRDY (n-1) timeout in I2C_read_bytes");
                    I2C_FSETSH(hI2c, I2CSTR, ICRRDY, CLR);
                    result = I2C_NRRDY;
                    goto error;
                }
                if (I2C_nack(hI2c))
                {
                    result = I2C_NACK;
                    I2C_FSETSH(hI2c, I2CSTR, NACK, CLR);
                    goto error;
                }
                // TSK_sleep(1);
            }
            buffer[i++] = I2C_readByte(hI2c);
        }
        while (0 == I2C_ardy(hI2c))
        {
            loops++;
            if (loops >= I2C_MAXLOOPS)
            {
                /*
                sprintf(msg,"ARDY timeout in I2C_read_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                        hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                message_puts(LOG_LEVEL_INFO,msg);
                */
                message_puts(LOG_LEVEL_INFO, "ARDY timeout in I2C_read_bytes");
                I2C_FSETSH(hI2c, I2CSTR, ARDY, CLR);
                result = I2C_NARDY;
                goto error;
            }
        }
        I2C_sendStop(hI2c);
        buffer[i++] = I2C_readByte(hI2c);
        loops = 0;
        while (0 == I2C_rrdy(hI2c))
        {
            loops++;
            if (loops >= 1000 * I2C_MAXLOOPS)
            {
                /*
                sprintf(msg,"RRDY (1) timeout in I2C_read_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                        hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                message_puts(LOG_LEVEL_INFO,msg);
                */
                message_puts(LOG_LEVEL_INFO, "RRDY (1) timeout in I2C_read_bytes");
                I2C_FSETSH(hI2c, I2CSTR, ICRRDY, CLR);
                result = I2C_NRRDY;
                goto error;
            }
            if (I2C_nack(hI2c))
            {
                result = I2C_NACK;
                I2C_FSETSH(hI2c, I2CSTR, NACK, CLR);
                goto error;
            }
            // TSK_sleep(1);
        }
        I2C_readByte(hI2c);
        loops = 0;
        while (I2C_bb(hI2c))
        {
            loops++;
            if (loops >= I2C_MAXLOOPS)
            {
                /*
                sprintf(msg,"BB timeout in I2C_read_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                        hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                message_puts(LOG_LEVEL_INFO,msg);
                */
                message_puts(LOG_LEVEL_INFO, "BB timeout in I2C_read_bytes");
                I2C_FSETSH(hI2c, I2CSTR, BB, CLR);
                result = I2C_BUSY;
                goto error;
            }
            // TSK_sleep(1);
        }
        result = 0;
        goto done;
    }
    I2C_FSETSH(hI2c, I2CSTR, BB, CLR);
    I2C_FSETSH(hI2c, I2CSTR, NACK, CLR);
    I2C_FSETSH(hI2c, I2CSTR, ICRRDY, CLR);
    /*
    sprintf(msg,"NACK in I2C_read_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
            hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
    message_puts(LOG_LEVEL_INFO,msg);
    */
    message_puts(LOG_LEVEL_INFO, "NACK in I2C_read_bytes");
    result = I2C_NACK;
    goto error;
error:
    I2C_sendStop(hI2c);
    I2C_reset(hI2c);
    IRQ_globalRestore(gie);
    dspI2CInit();
    return result;
done:
    IRQ_globalRestore(gie);
    return result;
}

/*----------------------------------------------------------------------------*/
void dspI2CInit()
{
    int loops;
    I2C_resetAll();
    for (loops = 0; loops < 2000; loops++)
        ;
    if (hI2C[0] != 0)
        I2C_close(hI2C[0]);
    hI2C[0] = I2C_open(I2C_PORT0, I2C_OPEN_RESET);
    initializeI2C(hI2C[0]);
    if (hI2C[1] != 0)
        I2C_close(hI2C[1]);
    hI2C[1] = I2C_open(I2C_PORT1, I2C_OPEN_RESET);
    initializeI2C(hI2C[1]);
    for (loops = 0; loops < 2000; loops++)
        ;
}
/*----------------------------------------------------------------------------*/
void setI2C0Mux(int channel)
{
    Uint8 bytes[1];
    int loops;
    I2C_device *d = &i2c_devices[CHAIN0_MUX];

    if (I2C0MuxChan == channel)
        return;
    bytes[0] = 8 + (channel & 0x7);
    for (loops = 0; loops < 1000; loops++)
        ;
    if (I2C_write_bytes(hI2C[d->chain], d->addr, bytes, 1) == 0)
        I2C0MuxChan = channel;
    I2C_sendStop(hI2C[d->chain]);
}
/*----------------------------------------------------------------------------*/
int fetchI2C0Mux()
{
    Uint8 bytes[1];
    I2C_device *d = &i2c_devices[CHAIN0_MUX];

    I2C_read_bytes(hI2C[d->chain], d->addr, bytes, 1);
    I2C0MuxChan = bytes[0] & 0x7;
    return I2C0MuxChan;
}
/*----------------------------------------------------------------------------*/
int getI2C0Mux()
{
    return I2C0MuxChan;
}
/*----------------------------------------------------------------------------*/
void setI2C1Mux(int channel)
{
    Uint8 bytes[1];
    I2C_device *d = &i2c_devices[CHAIN1_MUX];
    int loops;
    if (I2C1MuxChan == channel)
        return;
    bytes[0] = 8 + (channel & 0x7);
    for (loops = 0; loops < 1000; loops++)
        ;
    if (I2C_write_bytes(hI2C[d->chain], d->addr, bytes, 1) == 0)
        I2C1MuxChan = channel;
    I2C_sendStop(hI2C[d->chain]);
}
/*----------------------------------------------------------------------------*/
int fetchI2C1Mux()
{
    Uint8 bytes[1];
    I2C_device *d = &i2c_devices[CHAIN1_MUX];
    I2C_read_bytes(hI2C[d->chain], d->addr, bytes, 1);
    I2C1MuxChan = bytes[0] & 0x7;
    return I2C1MuxChan;
}
/*----------------------------------------------------------------------------*/
int getI2C1Mux()
{
    return I2C1MuxChan;
}
/*----------------------------------------------------------------------------*/
int I2C_check_ack(I2C_Handle hI2c, int i2caddr)
// Writes device address to I2C bus and returns whether something has acknowleged
{
    int result, loops = 0;
    int gie = IRQ_globalDisable();

    I2C_outOfReset(hI2c);
    // Set up the slave address of the I2C
    I2C_RSETH(hI2c, I2CSAR, i2caddr);
    // Set up as master transmitter, and send start bit
    I2C_FSETSH(hI2c, I2CMDR, MST, MASTER);
    I2C_FSETSH(hI2c, I2CMDR, TRX, XMT);
    I2C_FSETSH(hI2c, I2CMDR, STT, START);

    for (loops = 0; loops < 200; loops++)
        if (!I2C_xsmt(hI2c))
            break;

    // Check for NACK
    if (I2C_nack(hI2c))
    {
        I2C_sendStop(hI2c);
        I2C_FSETSH(hI2c, I2CSTR, BB, CLR);
        I2C_FSETSH(hI2c, I2CSTR, NACK, CLR);
        I2C_FSETSH(hI2c, I2CSTR, ICXRDY, CLR);
        result = I2C_NACK;
        goto done;
    }
    else
    {
        I2C_sendStop(hI2c);
        result = 0;
        goto done;
    }
done:
    IRQ_globalRestore(gie);
    return result;
}
/*----------------------------------------------------------------------------*/
int ltc2451_read(int ident)
// Read 16-bit ADC associated with "ident". Returns I2C_READ_ERROR on an I2C error.
{
    int result, loops;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    result = ltc2451_getData(d);
    if (result == I2C_READ_ERROR)
        return result;
    return result;
}
/*----------------------------------------------------------------------------*/
int ltc2485_read(int ident)
// Read 24-bit ADC associated with "ident". Returns I2C_READ_ERROR on an I2C error.
{
    int flags, result, loops;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    result = ltc2485_getData(d, &flags);
    if (result == I2C_READ_ERROR)
        return result;
    if (flags == 0)
        result = -16777216;
    else if (flags == 3)
        result = 16777215;
    return result;
}
/*----------------------------------------------------------------------------*/
static int ltc24xx_rdBytes(I2C_device *i2c, Uint8 command, int n, int *status)
/* Send a command, read up to 4 bytes in high-endian order. Return -1 on I2C error */
{
    Uint8 reply[4];
    int i, result = 0;
    *status = 0;
    if (n > 0 && n <= 4)
    {
        I2C_write_bytes(hI2C[i2c->chain], i2c->addr, &command, 1);
        if (I2C_read_bytes(hI2C[i2c->chain], i2c->addr, reply, n) != 0)
        {
            *status = I2C_READ_ERROR;
            return I2C_READ_ERROR;
        }
        for (i = 0; i < n; i++)
            result = (result << 8) | (unsigned int)reply[i];
    }
    return result;
}
/*----------------------------------------------------------------------------*/
int ltc24xxse_read(I2C_device *i2c, Uint8 command, int *status)
/* Read the 24-bit data from LTC24xx as a single-ended voltage,
    taking care of sauration */
{
    int result = ltc24xx_rdBytes(i2c, command, 4, status);
    int sat;
    if (*status < 0)
    {
        return *status;
    }
    sat = (result >> 30) & 3;
    result = (result & 0x7FFFFFFF) >> 6;
    if (sat == 0)
    { // Underflow
        return 0x0;
    }
    else if (sat == 3)
    { // Overflow
        return 0x2000000;
    }
    else
    { // Convert to unsigned
        result = result ^ 0x1000000;
        return ((int)result);
    }
}
/*----------------------------------------------------------------------------*/
int ltc2493se_read(int ident, int channel, int *status)
/* Read the 24-bit data from LTC2493 as a single-ended voltage, taking care of sauration
    The "channel" (0-3) indicates which channel is to be read:
     0xB0 for channel 0
     0xB8 for channel 1
     0xB1 for channel 2
     0xB9 for channel 3
   status is 0 on successful read and I2C_READ_ERROR on error.
*/
{
    Uint8 codes[4] = {0xB0, 0xB8, 0xB1, 0xB9};
    Uint8 command;
    I2C_device *d = &i2c_devices[ident];
    int loops;
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    command = codes[channel & 0x3];
    for (loops = 0; loops < 1000; loops++)
        ;
    return ltc24xxse_read(d, command, status);
}
/*----------------------------------------------------------------------------*/
int read_flow_sensor(int ident)
// Reads a Honeywell I2C flow sensor associated with "ident". Returns I2C_READ_ERROR on an I2C error.
{
    int result, loops;
    unsigned int i, n = 2;
    Uint8 reply[4] = {0, 0, 0, 0};
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    result = 0;
    for (loops = 0; loops < 1000; loops++)
        ;
    if (I2C_read_bytes(hI2C[d->chain], d->addr, reply, n) != 0)
        return I2C_READ_ERROR;
    for (i = 0; i < n; i++)
        result = (result << 8) | (unsigned int)reply[i];
    return result;
}
/*----------------------------------------------------------------------------*/
int rdd_read(int ident)
// Write a zero then read four bytes from the variable-gain ring-down detector
{
    int result, loops;
    unsigned int i, n = 4;
    Uint8 command = 0;
    Uint8 reply[4] = {0, 0, 0, 0};
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    I2C_write_bytes(hI2C[d->chain], d->addr, &command, 1);
    result = 0;
    if (I2C_read_bytes(hI2C[d->chain], d->addr, reply, n) != 0)
        return I2C_READ_ERROR;
    for (i = 0; i < n; i++)
        result = (result << 8) | (unsigned int)reply[i];
    return result;
}
/*----------------------------------------------------------------------------*/
void rdd_write(int ident, int data, int nbytes)
// Write one or two bytes to the variable-gain ring-down detector, followed by an I2C stop
// The bytes are read out of data in little-endian order
{
    int loops;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    I2C_write_bytes(hI2C[d->chain], d->addr, (Uint8 *)&data, nbytes);
    I2C_sendStop(hI2C[d->chain]);
}
/*----------------------------------------------------------------------------*/
void ltc2606_write(int ident, int value)
// Send the 16 LSB of value to the LTC2606 digital to analog converter and power up the output
{
    int loops;
    Uint8 data[3];
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    data[0] = 0x30; // Write to DAC and power up output
    data[1] = (value & 0xFF00) >> 8;
    data[2] = value & 0xFF;
    for (loops = 0; loops < 1000; loops++)
        ;
    I2C_write_bytes(hI2C[d->chain], d->addr, data, 3);
    I2C_sendStop(hI2C[d->chain]);
}
/*----------------------------------------------------------------------------*/
void ad5248_write(int ident, int channel, int position)
// Write the specified slider position (between 0 and 255) to the selected digital potentiometer
//  (channel=0 or 1) in the AD5248
{
    int loops;
    Uint8 data[2];
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    data[0] = channel ? 64 : 0;
    data[1] = position & 0xFF;
    for (loops = 0; loops < 1000; loops++)
        ;
    I2C_write_bytes(hI2C[d->chain], d->addr, data, 2);
    I2C_sendStop(hI2C[d->chain]);
}
/*----------------------------------------------------------------------------*/
int ad5248_read(int ident, int channel)
// Read the slider position (between 0 and 255) of the selected digital potentiometer
//  (channel=0 or 1) in the AD5248
{
    int loops;
    Uint8 data;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    data = channel ? 64 : 0;
    for (loops = 0; loops < 1000; loops++)
        ;
    I2C_write_bytes(hI2C[d->chain], d->addr, &data, 1);
    I2C_sendStop(hI2C[d->chain]);
    for (loops = 0; loops < 1000; loops++)
        ;
    if (I2C_read_bytes(hI2C[d->chain], d->addr, &data, 1) != 0)
        return I2C_READ_ERROR;
    return (int)data;
}
/*----------------------------------------------------------------------------*/
int pca8574_write(int ident, int value)
{
    int loops;
    unsigned char data;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    data = value & 0xFF;
    pca8574_wrByte(d, data);
    return 0;
}
/*----------------------------------------------------------------------------*/
int pca8574_read(int ident)
{
    int loops;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    return pca8574_rdByte(d);
}
/*----------------------------------------------------------------------------*/
int i2c_register_read(int ident, int reg, Uint8 *buffer, int nbytes)
/* Read nbytes bytes into buffer starting from I2C register reg. This first
   writes reg to the I2C and then performs nbytes I2C reads */
{
    int loops;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    if (I2C_write_bytes(hI2C[d->chain], d->addr, (Uint8 *)&reg, 1) != 0)
        return I2C_READ_ERROR;
    if (I2C_read_bytes(hI2C[d->chain], d->addr, buffer, nbytes) != 0)
        return I2C_READ_ERROR;
    return 0;
}
/*----------------------------------------------------------------------------*/
int i2c_register_write(int ident, int reg, Uint8 *buffer, int nbytes)
/* Writes nbytes bytes into buffer starting from I2C register reg. This first
   writes reg to the I2C and then performs nbytes I2C writes */
{
    int i, loops;
    Uint8 temp_buff[9];
    I2C_device *d = &i2c_devices[ident];

    if (nbytes <= 8)
    {
        temp_buff[0] = reg;
        for (i = 0; i < nbytes; i++)
            temp_buff[i + 1] = buffer[i];
        if (d->chain)
            setI2C1Mux(d->mux);
        else
            setI2C0Mux(d->mux);
        for (loops = 0; loops < 1000; loops++)
            ;
        if (I2C_write_bytes(hI2C[d->chain], d->addr, temp_buff, nbytes + 1) != 0)
            return I2C_READ_ERROR;
        I2C_sendStop(hI2C[d->chain]);
        return 0;
    }
    else
        return -1;
}
/*----------------------------------------------------------------------------*/
int accel_getDeviceId(int ident)
// Get the accelerometer identification code
{
    int loops;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    return adxl345_read_register(d, 0x0, 1);
}
/*----------------------------------------------------------------------------*/
int accel_read_reg(int ident, int reg)
// Get a byte from the accelerometer register "reg"
{
    int loops;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    return adxl345_read_register(d, reg, 1);
}
/*----------------------------------------------------------------------------*/
int accel_write_reg(int ident, int reg, int value)
// Write a byte to the accelerometer register "reg"
{
    int loops;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    return adxl345_write_register(d, reg, value, 1);
}
/*----------------------------------------------------------------------------*/
int accel_read_accel(int ident, short int *ax, short int *ay, short int *az)
// Read accelerations along three axes as short ints
{
    int loops;
    I2C_device *d = &i2c_devices[ident];
    if (d->chain)
        setI2C1Mux(d->mux);
    else
        setI2C0Mux(d->mux);
    for (loops = 0; loops < 1000; loops++)
        ;
    return adxl345_read_accel(d, ax, ay, az);
}
