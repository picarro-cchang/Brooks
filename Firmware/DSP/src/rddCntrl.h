/*
 * FILE:
 *   rddCntrl.h
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
 *
 *  Copyright (c) 2012 Picarro, Inc. All rights reserved
 */
#ifndef _RDD_CNTRL_H_
#define _RDD_CNTRL_H_

typedef struct RDD_CNTRL
{
    // References to registers
    unsigned int *rddBalance_;
    unsigned int *rddGain_;
    unsigned int currentBalance;
    unsigned int currentGain;
    int pendingCommand;
} RddCntrl;

int rddCntrlInit(void);
int rddCntrlStep(void);
int rddCntrlDoCommand(int command);

#endif /* _RDD_CNTRL_H_ */
