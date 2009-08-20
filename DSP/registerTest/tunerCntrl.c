/*
 * FILE:
 *   tunerCntrl.c
 *
 * DESCRIPTION:
 *   Tuner waveform generator controller routines
 *
 * This preliminary version just transfers DSP register parameters
 *  to the corresponding FPGA registers
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   3-Jun-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include "interface.h"
#include "dspAutogen.h"
#include "fpga.h"
#include "registers.h"
#include <math.h>

int tunerCntrlStep(void)
{
    return STATUS_OK;
}

void switchToRampMode(void)
{
    writeFPGA(FPGA_TWGEN+TWGEN_SWEEP_LOW,(unsigned int)*(float*)registerAddr(TUNER_SWEEP_RAMP_LOW_REGISTER));
    writeFPGA(FPGA_TWGEN+TWGEN_SWEEP_HIGH,(unsigned int)*(float*)registerAddr(TUNER_SWEEP_RAMP_HIGH_REGISTER));
    writeFPGA(FPGA_TWGEN+TWGEN_WINDOW_LOW,(unsigned int)*(float*)registerAddr(TUNER_WINDOW_RAMP_LOW_REGISTER));
    writeFPGA(FPGA_TWGEN+TWGEN_WINDOW_HIGH,(unsigned int)*(float*)registerAddr(TUNER_WINDOW_RAMP_HIGH_REGISTER));
    writeFPGA(FPGA_RDMAN+RDMAN_TIMEOUT_DURATION,(unsigned int)*(unsigned int*)registerAddr(SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER));
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL, RDMAN_CONTROL_RAMP_DITHER_B, RDMAN_CONTROL_RAMP_DITHER_W, 0);
}

void setupDither(unsigned int center)
{
    // Switch to dither mode centered about the given value, if this is possible. Otherwise
    //  go to ramp mode in the hope that a ringdown will then occur.
    unsigned int sweepLow  = center - (unsigned int)*(float*)registerAddr(TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER);
    unsigned int sweepHigh = center + (unsigned int)*(float*)registerAddr(TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER);
    unsigned int windowLow  = center - (unsigned int)*(float*)registerAddr(TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER);
    unsigned int windowHigh = center + (unsigned int)*(float*)registerAddr(TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER);
    writeFPGA(FPGA_RDMAN+RDMAN_TIMEOUT_DURATION,(unsigned int)*(unsigned int*)registerAddr(SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER));    
    if (windowHigh > sweepHigh) windowHigh = sweepHigh;
    if (windowLow  < sweepLow)  windowLow  = sweepLow;
    if (sweepHigh > *(float*)registerAddr(TUNER_SWEEP_RAMP_HIGH_REGISTER) ||
        sweepLow  < *(float*)registerAddr(TUNER_SWEEP_RAMP_LOW_REGISTER)) {
        switchToRampMode();
    }
    else {
        writeFPGA(FPGA_TWGEN+TWGEN_SWEEP_LOW,sweepLow);
        writeFPGA(FPGA_TWGEN+TWGEN_SWEEP_HIGH,sweepHigh);
        writeFPGA(FPGA_TWGEN+TWGEN_WINDOW_LOW,windowLow);
        writeFPGA(FPGA_TWGEN+TWGEN_WINDOW_HIGH,windowHigh);
        changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL, RDMAN_CONTROL_RAMP_DITHER_B, RDMAN_CONTROL_RAMP_DITHER_W, 1);        
    }
}

int tunerCntrlInit(void)
{
    writeFPGA(FPGA_TWGEN+TWGEN_CS, (1<<TWGEN_CS_RUN_B)|(1<<TWGEN_CS_CONT_B));
    // Start up in ramp mode
    switchToRampMode();
    return STATUS_OK;
}
