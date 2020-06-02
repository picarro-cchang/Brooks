/*
 * FILE:
 *   midIrDetectorCntrl.h
 *
 * DESCRIPTION:
 *   Mid IR Ringdown detector controller
 *
 * The ringdown detector controller handles the variable gain control and offset for the cavity
 *  output detector. There are three digital potentiometers organized in two I2C devices which
 *  control
 * (a) The overall gain of the detector Gain = (R_i + R + R_f)/((1-\beta) R + R_i) where
 *    R_i, R and R_f are the input, potentiometer and feedback resistances of the second
 *    amplifier stage and \beta ranges from 0 trough 1 as A1 ranges from 0 to 255. Typical
 *    values are R_i = 80 ohms, R = 1000 ohms and R_f = 1080 ohms
 * (b) The balance between the backscatter detector (A0=0) and the ringdown detector (A0=255)
 * (c) The voltage used to offset the output of the amplifier
 *
 * The potentiometers for (a) and (b) are A0 (RDAC1) and A1 (RDAC3) in the I2C device
 *  MIDIR_DETECTOR_GAIN_AND_BALANCE while the potentiometer for (c) is A1 (RDAC3)
 *  in the device MIDIR_DETECTOR_OFFSET
 *
 * The digital potentiometers are accessed via an I2C interface which exposes
 *  two functions
 * (a) rdd_read which reads four bytes with the potentiometer settings A0 (RDAC1) in bis 7-0
 *      and A1 (RDAC3) in bits 23-16.
 * (b) rdd_write which writes one or two bytes. The two byte writes are used to set
 *      the potentiometer gains while the one byte writes issue a variety of commands
 *      documented in the AD5252 data sheet
 *
 * This program is run by the scheduler so that all I2C accesses take place in a single
 *  thread. It monitors the DSP registers RDD_BALANCE_REGISTER, RDD_GAIN_REGISTER
 *  and RDD_OFFSET_REGISTER and issues a write command to the I2C system if any
 *  have changed. It then reads back the potentiometer settings to verify that the
 *  writes have occured successfully. Note that it takes a few milliseconds to perform
 *  the write into non-volatile memory, so these cannot be performed immediately after
 *  each other
 *
 *  Similarly, if a command is to be sent to the digital potentiometers, this is only done
 *  during rddCntrlStep so as not to interfere with other I2C activity
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   8-Dec-2017  sze  Initial version.
 *
 *  Copyright (c) 2017 Picarro, Inc. All rights reserved
 */
#ifndef _MIDIR_DETECTOR_CNTRL_H_
#define _MIDIR_DETECTOR_CNTRL_H_

typedef struct MIDIR_DETECTOR_CNTRL
{
    int i2cIdentGainAndBalance;
    int i2cIdentOffset;
    int readback;
    // References to registers
    unsigned int *rddBalance_;
    unsigned int *rddGain_;
    unsigned int *rddOffset_;
    unsigned int currentBalance;
    unsigned int currentGain;
    unsigned int currentOffset;
} MidIrDetectorCntrl;

int midIrDetectorCntrlInit(void);
int midIrDetectorCntrlStep(void);

#endif /* _MIDIR_DETECTOR_CNTRL_H_ */
