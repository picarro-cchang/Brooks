/*
 * FILE:
 *   rddCntrl.c
 *
 * DESCRIPTION:
 *   Ringdown detector controller
 *
 * The ringdown detector controller handles the variable gain control for the cavity output
 *  detector. There are two digital potentiometers (A0, A1) which control
 * (a) The balance between the ringdown detector (A0=0) and the backscatter detector (A0=255)
 * (b) The overall gain of the detector Gain = (R_i + R + R_f)/((1-\beta) R + R_i) where
 *    R_i, R and R_f are the input, potentiometer and feedback resistances of the second
 *    amplifier stage and \beta ranges from 0 trough 1 as A1 ranges from 0 to 255. Typical
 *    values are R_i = 80 ohms, R = 1000 ohms and R_f = 1080 ohms
 *
 * The digital potentiometer is accessed via an I2C interface which exposes two functions
 * (a) rdd_read which reads four bytes with the potentiometer settings A0 in bis 7-0
 *      and A1 in bits 23-16.
 * (b) rdd_write which writes one or two bytes. The two byte writes are used to set
 *      the potentiometer gains while the one byte writes issue a variety of commands
 *      documented in the AD5252 data sheet
 *
 * This program is run by the scheduler so that all I2C accesses take place in a single
 *  thread. It monitors the DSP registers RDD_BALANCE_REGISTER and RDD_GAIN_REGISTER
 *  and issues a write command to the I2C system if either has changed. It then reads
 *  back the potentiometer settings to verify that the writes have occured successfully.
 *  Similarly, if a command is to be sent to the digital potentiometers, this is only done
 *  during rddCntrlStep so as not to interfere with other I2C activity
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   10-Nov-2012  sze  Initial version.
 *   09-06-2019   HBC  add second detector gain and offset adjust
 *  Copyright (c) 2012 Picarro, Inc. All rights reserved
 */
#include "interface.h"
#include "i2c_dsp.h"
#include "registers.h"
#include "rddCntrl.h"
#include "dspAutogen.h"
#include <math.h>

#define rddBalance      (*(r->rddBalance_))
#define rddGain         (*(r->rddGain_))
#define rdd2Balance      (*(r->rdd2Balance_))
#define rdd2Gain         (*(r->rdd2Gain_))

RddCntrl rddCntrl;
int readBack = 1;
int read2Back = 1;

int rddCntrlStep(void)
{
    RddCntrl *r = &rddCntrl;
    if (readBack) {
        unsigned int gains = rdd_read(RDD_POTENTIOMETERS);
        rddBalance = r->currentBalance = (gains>>16) & 0xFF;
        rddGain = r->currentGain = gains & 0xFF;
        readBack = 0;
    }
    if (rddBalance != r->currentBalance) {
        rdd_write(RDD_POTENTIOMETERS,(rddBalance & 0xFF)<<8 | 1,2);
        readBack = 1;
    }
    if (rddGain != r->currentGain) {
        rdd_write(RDD_POTENTIOMETERS,((rddGain & 0xFF)<<8) | 3,2);
        readBack = 1;
    }
    if (r->pendingCommand >= 0) {
        rdd_write(RDD_POTENTIOMETERS,(r->pendingCommand & 0xFF),1);
        readBack = 1;
        r->pendingCommand = -1;
    }
    return STATUS_OK;
}

int rdd2CntrlStep(void)
{
    RddCntrl *r = &rddCntrl;
    if (read2Back) {
        unsigned int gains = rdd_read(RDD2_POTENTIOMETERS);
        rdd2Balance = r->current2Balance = (gains>>16) & 0xFF;
        rdd2Gain = r->current2Gain = gains & 0xFF;
        read2Back = 0;
    }
    if (rdd2Balance != r->current2Balance) {
        rdd_write(RDD2_POTENTIOMETERS,(rdd2Balance & 0xFF)<<8 | 1,2);
        read2Back = 1;
    }
    if (rdd2Gain != r->current2Gain) {
        rdd_write(RDD2_POTENTIOMETERS,((rdd2Gain & 0xFF)<<8) | 3,2);
        read2Back = 1;
    }
    if (r->pending2Command >= 0) {
        rdd_write(RDD2_POTENTIOMETERS,(r->pending2Command & 0xFF),1);
        read2Back = 1;
        r->pending2Command = -1;
    }
    return STATUS_OK;
}


int rddCntrlInit(void)
{
    unsigned int gains;
    RddCntrl *r = &rddCntrl;
    r->rddBalance_ = (unsigned int *)registerAddr(RDD_BALANCE_REGISTER);
    r->rddGain_ = (unsigned int *)registerAddr(RDD_GAIN_REGISTER);
    gains = rdd_read(RDD_POTENTIOMETERS);
    r->pendingCommand = -1; // No command pending
    r->currentBalance = (gains>>16) & 0xFF;
    r->currentGain = gains & 0xFF;
    return STATUS_OK;
}

int rdd2CntrlInit(void)
{
    unsigned int gains;
    RddCntrl *r = &rddCntrl;
    r->rdd2Balance_ = (unsigned int *)registerAddr(RDD2_BALANCE_REGISTER);
    r->rdd2Gain_ = (unsigned int *)registerAddr(RDD2_GAIN_REGISTER);
    gains = rdd_read(RDD2_POTENTIOMETERS);
    r->pending2Command = -1; // No command pending
    r->current2Balance = (gains>>16) & 0xFF;
    r->current2Gain = gains & 0xFF;
    return STATUS_OK;
}


int rddCntrlDoCommand(int command)
{
    RddCntrl *r = &rddCntrl;
    r->pendingCommand = command;
    return STATUS_OK;
}

int rdd2CntrlDoCommand(int command)
{
    RddCntrl *r = &rddCntrl;
    r->pending2Command = command;
    return STATUS_OK;
}

#undef  rddBalance
#undef  rddGain
#undef  rdd2Balance
#undef  rdd2Gain
