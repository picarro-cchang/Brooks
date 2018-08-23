/*
 * FILE:
 *   fanCntrl.h
 *
 * DESCRIPTION:
 *   Fan controller routines
 *
 * Fan control operates by comparing the DAS temperature against the value in 
 *  FAN_CNTRL_TEMPERATURE_REGISTER and turning on the fan whenever the temperature
 *  exceeds the value specified
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   17-Feb-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef _FAN_CNTRL_H_
#define _FAN_CNTRL_H_

typedef struct FAN_CNTRL
{
    // References to registers
    unsigned int *state_;
    float *tempThreshold_;
    float *dasTemp_;
} FanCntrl;

int fanCntrlInit(void);
int fanCntrlStep(void);
void setFan(FAN_CNTRL_StateType state);

#endif /* _FAN_CNTRL_H_ */
