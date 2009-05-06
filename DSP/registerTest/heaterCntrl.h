/*
 * FILE:
 *   heaterCntrl.h
 *
 * DESCRIPTION:
 *   Heater controller routines
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   27-Apr-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef _HEATER_CNTRL_H_
#define _HEATER_CNTRL_H_

typedef struct HEATER_CNTRL {
    // References to registers
    unsigned int *state_;
    float *gain_;
    float *quantize_;
    float *uBiasSlope_;
    float *uBiasOffset_;
    float *minMark_;
    float *maxMark_;
    float *manualMark_;
    float *mark_;
    float *cavitySetpoint_;
    float *cavityTec_;
} HeaterCntrl;

int heaterCntrlInit(void);
int heaterCntrlStep(void);

#endif /* _HEATER_CNTRL_H_ */
