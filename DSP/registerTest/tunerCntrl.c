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
    writeFPGA(FPGA_TWGEN+TWGEN_SLOPE_DOWN, *(float*)registerAddr(TUNER_DOWN_SLOPE_REGISTER));
    writeFPGA(FPGA_TWGEN+TWGEN_SLOPE_UP,   *(float*)registerAddr(TUNER_UP_SLOPE_REGISTER));
    writeFPGA(FPGA_TWGEN+TWGEN_SWEEP_LOW,  *(float*)registerAddr(TUNER_SWEEP_RAMP_LOW_REGISTER));
    writeFPGA(FPGA_TWGEN+TWGEN_SWEEP_HIGH, *(float*)registerAddr(TUNER_SWEEP_RAMP_HIGH_REGISTER));
    writeFPGA(FPGA_TWGEN+TWGEN_WINDOW_LOW, *(float*)registerAddr(TUNER_WINDOW_RAMP_LOW_REGISTER));
    writeFPGA(FPGA_TWGEN+TWGEN_WINDOW_HIGH,*(float*)registerAddr(TUNER_WINDOW_RAMP_HIGH_REGISTER));
    return STATUS_OK;
}

int tunerCntrlInit(void)
{
    tunerCntrlStep();
    writeFPGA(FPGA_TWGEN+TWGEN_CS, (1<<TWGEN_CS_RUN_B)|(1<<TWGEN_CS_CONT_B));
    return STATUS_OK;
}
