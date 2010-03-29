/*
 * FILE:
 *   i2c_dsp.h
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
#include <sem.h>
#include <tsk.h>
#include "interface.h"
#include "i2c_dsp.h"
#include "registers.h"
#include "dspAutogen.h"

#define I2C_MAXLOOPS (300)

#define IDEF  static inline

I2C_Handle hI2C[2] = {0, 0};

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
    return I2C_FGETH(hI2c,I2CSTR,NACK);
}
/*----------------------------------------------------------------------------*/
// Returns 1 if I2C module registers are ready to be accessed
IDEF Uint32 I2C_ardy(I2C_Handle hI2c)
{
    return I2C_FGETH(hI2c,I2CSTR,ARDY);
}
/*----------------------------------------------------------------------------*/
// Returns 1 if I2C transmit register is empty
IDEF Uint32 I2C_xsmt(I2C_Handle hI2c)
{
    return I2C_FGETH(hI2c,I2CSTR,XSMT);
}
/*----------------------------------------------------------------------------*/
int initializeI2C(I2C_Handle hI2c)
// Initialize I2C port, return I2C_BUSY if I2C bus does not become free
{
    int loops = 0;
    Uint32 i2coar = I2C_I2COAR_A_OF(0x10);  // Own address
    Uint32 i2cimr = 0x0;    // Interrupt enable mask
    Uint32 i2cclkl = I2C_I2CCLKL_ICCL_OF(0x8);  // I2C Clock divider (low)
    Uint32 i2cclkh = I2C_I2CCLKH_ICCH_OF(0x1); // I2C Clock divider (high)
    Uint32 i2ccnt  = I2C_I2CCNT_ICDC_OF(3); // Transfer 3 words
    Uint32 i2csar  = I2C_I2CSAR_A_OF(0x10); // Slave address
    Uint32 i2cmdr  = I2C_I2CMDR_RMK(\
                                    I2C_I2CMDR_NACKMOD_ACK,\
                                    I2C_I2CMDR_FREE_BSTOP,\
                                    I2C_I2CMDR_STT_NONE,\
                                    I2C_I2CMDR_STP_NONE,\
                                    I2C_I2CMDR_MST_MASTER,\
                                    I2C_I2CMDR_TRX_XMT,\
                                    I2C_I2CMDR_XA_7BIT,\
                                    I2C_I2CMDR_RM_REPEAD,\
                                    I2C_I2CMDR_DLB_NONE,\
                                    I2C_I2CMDR_IRS_NRST,\
                                    I2C_I2CMDR_STB_NONE,\
                                    I2C_I2CMDR_FDF_NONE,\
                                    I2C_I2CMDR_BC_BIT8FDF);
    Uint32 i2cpsc  = I2C_I2CPSC_IPSC_OF(0xE); // Prescaler
    // Wait for bus to be not busy
    while (I2C_bb(hI2c))
    {
        loops++;
        if (loops >= I2C_MAXLOOPS) return I2C_BUSY;
        // TSK_sleep(1);
    };

    I2C_configArgs(hI2c,i2coar,i2cimr,i2cclkl,i2cclkh,i2ccnt,i2csar,i2cmdr,i2cpsc);
    return 0;
}
/*----------------------------------------------------------------------------*/
int getI2CMode(I2C_Handle hI2c)
{
    return I2C_RGETH(hI2c,I2CMDR);
}
/*----------------------------------------------------------------------------*/
int getI2CStatus(I2C_Handle hI2c)
{
    return I2C_RGETH(hI2c,I2CSTR);
}
/*----------------------------------------------------------------------------*/
int I2C_write_bytes(I2C_Handle hI2c,int i2caddr,Uint8 *buffer,int nbytes)
// Send contents of buffer to the device associated with I2C_Handle
// Returns 0 on success. I2C_NACK on NACK error, I2C_NXRDY on I2C_xrdy timeout
//  I2C_NARDY on register access timeout, I2C_BUSY on bus busy timeout
{
    int i;
    int loops = 0;
    i = 0;
    I2C_outOfReset(hI2c);
    // Set up the slave address of the I2C
    I2C_RSETH(hI2c,I2CSAR,i2caddr);
    // Set up as master transmitter, and send start bit
    I2C_FSETSH(hI2c,I2CMDR,MST,MASTER);
    I2C_FSETSH(hI2c,I2CMDR,TRX,XMT);
    I2C_FSETSH(hI2c,I2CMDR,STT,START);
    while (0 == I2C_nack(hI2c))
    {
        if (0 == I2C_xrdy(hI2c))
        {
            loops++;
            if (loops >= I2C_MAXLOOPS)
            {
                I2C_FSETSH(hI2c,I2CSTR,ICXRDY,CLR);
                /*sprintf(msg,"XRDY timeout in I2C_write_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                        hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                message_puts(msg);*/
                message_puts("XRDY timeout in I2C_write_bytes");
                return I2C_NXRDY;
            }
            //TSK_sleep(1);
            continue;
        }
        if (i>=nbytes)
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
                    I2C_FSETSH(hI2c,I2CSTR,ARDY,CLR);
                    /*sprintf(msg,"ARDY timeout in I2C_write_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                                hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                    message_puts(msg);*/
                    message_puts("ARDY timeout in I2C_write_bytes");
                    return I2C_NARDY;
                }
                //TSK_sleep(1);
            }
            return 0;
        }
        // LOG_printf(&trace,"WriteByte: 0x%x",data[i]);
        I2C_writeByte(hI2c,buffer[i++]);
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
    I2C_FSETSH(hI2c,I2CSTR,BB,CLR);
    I2C_FSETSH(hI2c,I2CSTR,NACK,CLR);
    I2C_FSETSH(hI2c,I2CSTR,ICXRDY,CLR);
    /*sprintf(msg,"NACK in I2C_write_bytes, I2CAddr=%x",i2caddr);
    message_puts(msg);*/
    message_puts("NACK in I2C_write_bytes");
    return I2C_NACK;
}
/*----------------------------------------------------------------------------*/
int I2C_write_bytes_nostart(I2C_Handle hI2c,Uint8 *buffer,int nbytes)
// Continue a write without sending the start byte and the I2C slave address.
//  This is primarily used in conjunction with EEPROM writing code
{
    int i;
    int loops = 0;
    i = 0;
    while (0 == I2C_nack(hI2c))
    {
        if (0 == I2C_xrdy(hI2c))
        {
            loops++;
            if (loops >= I2C_MAXLOOPS)
            {
                I2C_FSETSH(hI2c,I2CSTR,ICXRDY,CLR);
                /*sprintf(msg,"XRDY timeout in I2C_write_bytes_nostart, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d",
                        hI2c,I2C0MuxChan,I2C1MuxChan);
                message_puts(msg);*/
                message_puts("XRDY timeout in I2C_write_bytes_nostart");
                return I2C_NXRDY;
            }
            //TSK_sleep(1);
            continue;
        }
        if (i>=nbytes)
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
                    I2C_FSETSH(hI2c,I2CSTR,ARDY,CLR);
                    /*sprintf(msg,"ARDY timeout in I2C_write_bytes_nostart, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d",
                            hI2c,I2C0MuxChan,I2C1MuxChan);
                    message_puts(msg);*/
                    message_puts("ARDY timeout in I2C_write_bytes_nostart");
                    return I2C_NARDY;
                }
                //TSK_sleep(1);
            }
            return 0;
        }
        // LOG_printf(&trace,"WriteByte: 0x%x",data[i]);
        I2C_writeByte(hI2c,buffer[i++]);
        loops = 0;
    }
    I2C_sendStop(hI2c);
    I2C_FSETSH(hI2c,I2CSTR,BB,CLR);
    I2C_FSETSH(hI2c,I2CSTR,NACK,CLR);
    I2C_FSETSH(hI2c,I2CSTR,ICXRDY,CLR);
    /*sprintf(msg,"NACK timeout in I2C_write_bytes_nostart, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d",
            hI2c,I2C0MuxChan,I2C1MuxChan);
    message_puts(msg);*/
    message_puts("NACK timeout in I2C_write_bytes_nostart");
    return I2C_NACK;
}
/*----------------------------------------------------------------------------*/
int I2C_read_bytes(I2C_Handle hI2c,int i2caddr,Uint8 *buffer,int nbytes)
// Read nbytes at the device associated with I2C_Handle
// Send ACK after each read except for the last
// Returns 0 on success. I2C_NACK on NACK error, I2C_NRRDY on I2C_rrdy timeout
//  and I2C_NARDY on register access timeout
{
    int i;
    int loops;
    I2C_outOfReset(hI2c);
    i = 0;
    I2C_FSETSH(hI2c,I2CSTR,ICRRDY,CLR);
    // Set up the slave address of the I2C
    I2C_RSETH(hI2c,I2CSAR,i2caddr);
    // Set up as master receiver, and send start bit
    I2C_FSETSH(hI2c,I2CMDR,MST,MASTER);
    I2C_FSETSH(hI2c,I2CMDR,TRX,RCV);
    I2C_FSETSH(hI2c,I2CMDR,STT,START);
    //I2C_start(hI2c);
    while (0 == I2C_nack(hI2c))
    {
        while (i<nbytes-1)
        {
            loops = 0;
            while (0 == I2C_rrdy(hI2c))
            {
                loops++;
                if (loops >= 50*I2C_MAXLOOPS)
                {
                    // Go through here on timeout
                    /*sprintf(msg,"RRDY (n-1) timeout in I2C_read_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                            hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                    message_puts(msg);*/
                    message_puts("RRDY (n-1) timeout in I2C_read_bytes");
                    I2C_FSETSH(hI2c,I2CSTR,ICRRDY,CLR);
                    return I2C_NRRDY;
                }
                //TSK_sleep(1);
            }
            buffer[i++] = I2C_readByte(hI2c);
        }
        while (0 == I2C_ardy(hI2c))
        {
            loops++;
            if (loops >= I2C_MAXLOOPS)
            {
                /* sprintf(msg,"ARDY timeout in I2C_read_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                        hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                message_puts(msg); */
                message_puts("ARDY timeout in I2C_read_bytes");
                I2C_FSETSH(hI2c,I2CSTR,ARDY,CLR);
                return I2C_NARDY;
            }
        }
        I2C_sendStop(hI2c);
        buffer[i++] = I2C_readByte(hI2c);
        loops = 0;
        while (0 == I2C_rrdy(hI2c))
        {
            loops++;
            if (loops >= 50*I2C_MAXLOOPS)
            {
                /*sprintf(msg,"RRDY (1) timeout in I2C_read_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                        hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                message_puts(msg);*/
                message_puts("RRDY (1) timeout in I2C_read_bytes");
                I2C_FSETSH(hI2c,I2CSTR,ICRRDY,CLR);
                return I2C_NRRDY;
            }
            //TSK_sleep(1);
        }
        I2C_readByte(hI2c);
        loops = 0;
        while (I2C_bb(hI2c))
        {
            loops++;
            if (loops >= I2C_MAXLOOPS)
            {
                /*sprintf(msg,"BB timeout in I2C_read_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
                        hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
                message_puts(msg);*/
                message_puts("BB timeout in I2C_read_bytes");
                I2C_FSETSH(hI2c,I2CSTR,BB,CLR);
                return I2C_BUSY;
            }
            //TSK_sleep(1);
        }
        return 0;
    }
    I2C_FSETSH(hI2c,I2CSTR,BB,CLR);
    I2C_FSETSH(hI2c,I2CSTR,NACK,CLR);
    I2C_FSETSH(hI2c,I2CSTR,ICRRDY,CLR);
    /*sprintf(msg,"NACK in I2C_read_bytes, hI2c=%d, I2C0MuxChan=%d, I2C1MuxChan=%d, I2CAddr=%x",
            hI2c,I2C0MuxChan,I2C1MuxChan,i2caddr);
    message_puts(msg);*/
    message_puts("NACK in I2C_read_bytes");
    return I2C_NACK;
}

/*----------------------------------------------------------------------------*/
void dspI2CInit()
{
    I2C_resetAll();
    if (hI2C[0] != 0) I2C_close(hI2C[0]);
    hI2C[0] = I2C_open(I2C_PORT0,I2C_OPEN_RESET);
    initializeI2C(hI2C[0]);
    if (hI2C[1] != 0) I2C_close(hI2C[1]);
    hI2C[1] = I2C_open(I2C_PORT1,I2C_OPEN_RESET);
    initializeI2C(hI2C[1]);
}
/*----------------------------------------------------------------------------*/
void setI2C0Mux(int channel)
{
    Uint8 bytes[1];
    int loops;
    I2C_device *d = &i2c_devices[CHAIN0_MUX];

    if (I2C0MuxChan == channel) return;
    bytes[0] =  8 + (channel & 0x7);
    while (1) {
        for (loops = 0; loops < 1000; loops++);
        if (I2C_write_bytes(hI2C[d->chain],d->addr,bytes,1) == 0) break;
        message_puts("Retrying setI2C0Mux");
    }
    I2C_sendStop(hI2C[d->chain]);
    I2C0MuxChan = channel;
}
/*----------------------------------------------------------------------------*/
int fetchI2C0Mux()
{
    Uint8 bytes[1];
    I2C_device *d = &i2c_devices[CHAIN0_MUX];

    I2C_read_bytes(hI2C[d->chain],d->addr,bytes,1);
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
    if (I2C1MuxChan == channel) return;
    bytes[0] =  8 + (channel & 0x7);
    while (1) {
        for (loops = 0; loops < 1000; loops++);
        if (I2C_write_bytes(hI2C[d->chain],d->addr,bytes,1) == 0) break;
        message_puts("Retrying setI2C1Mux");
    }
    I2C_sendStop(hI2C[d->chain]);
    I2C1MuxChan = channel;
}
/*----------------------------------------------------------------------------*/
int fetchI2C1Mux()
{
    Uint8 bytes[1];
    I2C_device *d = &i2c_devices[CHAIN1_MUX];
    I2C_read_bytes(hI2C[d->chain],d->addr,bytes,1);
    I2C1MuxChan = bytes[0] & 0x7;
    return I2C1MuxChan;
}
/*----------------------------------------------------------------------------*/
int getI2C1Mux()
{
    return I2C1MuxChan;
}
/*----------------------------------------------------------------------------*/
int I2C_check_ack(I2C_Handle hI2c,int i2caddr)
// Writes device address to I2C bus and returns whether something has acknowleged
{
    int loops = 0;
    I2C_outOfReset(hI2c);
    // Set up the slave address of the I2C
    I2C_RSETH(hI2c,I2CSAR,i2caddr);
    // Set up as master transmitter, and send start bit
    I2C_FSETSH(hI2c,I2CMDR,MST,MASTER);
    I2C_FSETSH(hI2c,I2CMDR,TRX,XMT);
    I2C_FSETSH(hI2c,I2CMDR,STT,START);
    
    for (loops=0; loops<200; loops++)
        if (!I2C_xsmt(hI2c)) break;
    
    // Check for NACK 
    if (I2C_nack(hI2c)) {
        I2C_sendStop(hI2c);
        I2C_FSETSH(hI2c,I2CSTR,BB,CLR);
        I2C_FSETSH(hI2c,I2CSTR,NACK,CLR);
        I2C_FSETSH(hI2c,I2CSTR,ICXRDY,CLR);
        return I2C_NACK;
    }
    else {
        I2C_sendStop(hI2c);
        return 0;
    }
}
