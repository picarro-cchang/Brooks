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
#include "i2c_dsp.h"

#define I2C_BUSY     (-1)
#define I2C_NACK     (-2)
#define I2C_NARDY    (-3)
#define I2C_NRRDY    (-4)
#define I2C_NXRDY    (-5)
#define I2C_BADPAGE  (-6)

#define I2C_MAXLOOPS (1000)

#define IDEF  static inline

I2C_Handle hI2C0, hI2C1;
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
int initializeI2C(I2C_Handle hI2c)
// Initialize I2C port, return I2C_BUSY if I2C bus does not become free
{
    int loops = 0;
    Uint32 i2coar = I2C_I2COAR_A_OF(0x10);  // Own address
    Uint32 i2cimr = 0x0;    // Interrupt enable mask
    Uint32 i2cclkl = I2C_I2CCLKL_ICCL_OF(0x8);  // I2C Clock divider (low)
    Uint32 i2cclkh = I2C_I2CCLKH_ICCH_OF(0x10); // I2C Clock divider (high)
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
    Uint32 i2cpsc  = I2C_I2CPSC_IPSC_OF(0x19); // Prescaler
    // Wait for bus to be not busy
    while (I2C_bb(hI2c))
    {
        loops++;
        if (loops >= I2C_MAXLOOPS) return I2C_BUSY;
        TSK_sleep(1);
    };

    I2C_configArgs(hI2c,i2coar,i2cimr,i2cclkl,i2cclkh,i2ccnt,i2csar,i2cmdr,i2cpsc);
    return 0;
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
            if (loops >= I2C_MAXLOOPS) return I2C_NXRDY;
            TSK_sleep(1);
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
                if (loops >= I2C_MAXLOOPS) return I2C_NARDY;
                TSK_sleep(1);
            }
            return 0;
        }
        // LOG_printf(&trace,"WriteByte: 0x%x",data[i]);
        I2C_writeByte(hI2c,buffer[i++]);
    }
    // Error return if NACK received. Send stop bit to terminate
    I2C_sendStop(hI2c);
    I2C_FSETSH(hI2c,I2CSTR,NACK,CLR);
    // Clear XRDY flag in case a byte has already been placed
    //  in the I2CDXR. This byte should be discarded in case of a
    //  NACK problem.
    I2C_FSETSH(hI2c,I2CSTR,ICXRDY,CLR);
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
    i = 0;
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
                if (loops >= I2C_MAXLOOPS) return I2C_NRRDY;
                TSK_sleep(1);
            }
            buffer[i++] = I2C_readByte(hI2c);
        }
        while (0 == I2C_ardy(hI2c));
        I2C_sendStop(hI2c);
        buffer[i++] = I2C_readByte(hI2c);
        loops = 0;
        while (0 == I2C_rrdy(hI2c))
        {
            loops++;
            if (loops >= I2C_MAXLOOPS) return I2C_NRRDY;
            TSK_sleep(1);
        }
        I2C_readByte(hI2c);
        loops = 0;
        while (I2C_bb(hI2c))
        {
            loops++;
            if (loops >= I2C_MAXLOOPS) return I2C_BUSY;
            TSK_sleep(1);
        }
        return 0;
    }
    // Error return if NACK received
    I2C_sendStop(hI2c);
    I2C_FSETSH(hI2c,I2CSTR,NACK,CLR);
    // Clear RRDY flag
    I2C_FSETSH(hI2c,I2CSTR,ICRRDY,CLR);
    return I2C_NACK;
}

/*----------------------------------------------------------------------------*/
void dspI2CInit()
{
    hI2C0 = I2C_open(I2C_PORT0,I2C_OPEN_RESET);
    initializeI2C(hI2C0);
    hI2C1 = I2C_open(I2C_PORT1,I2C_OPEN_RESET);
    initializeI2C(hI2C1);
}
/*----------------------------------------------------------------------------*/
int I2C0MuxChan = 0;
int I2C1MuxChan = 0;
/*----------------------------------------------------------------------------*/
void setI2C0Mux(int channel)
{
    Uint8 bytes[1];
    bytes[0] =  8 + (channel & 0x7);
    I2C_write_bytes(hI2C0,0x70,bytes,1);
    I2C_sendStop(hI2C0);
    I2C0MuxChan = channel;
}
/*----------------------------------------------------------------------------*/
int fetchI2C0Mux()
{
    Uint8 bytes[1];
    I2C_read_bytes(hI2C0,0x70,bytes,1);
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
    bytes[0] =  8 + (channel & 0x7);
    I2C_write_bytes(hI2C1,0x71,bytes,1);
    I2C_sendStop(hI2C1);
    I2C1MuxChan = channel;
}
/*----------------------------------------------------------------------------*/
int fetchI2C1Mux()
{
    Uint8 bytes[1];
    I2C_read_bytes(hI2C1,0x71,bytes,1);
    I2C1MuxChan = bytes[0] & 0x7;
    return I2C1MuxChan;
}
/*----------------------------------------------------------------------------*/
int getI2C1Mux()
{
  return I2C1MuxChan;
}
/*----------------------------------------------------------------------------*/
