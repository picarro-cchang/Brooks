/*
 * FILE:
 *   tunerCntrl.h
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
#ifndef _TUNER_CNTRL_H_
#define _TUNER_CNTRL_H_

int tunerCntrlStep(void);
int tunerCntrlInit(void);

#endif /* _TUNER_CNTRL_H_ */
