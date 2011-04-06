/*
 * FILE:
 *   fanCntrl.c
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
#include "interface.h"
#include "registers.h"
#include "fanCntrl.h"
#include "valveCntrl.h"
#include "dspAutogen.h"
#include <math.h>

#define tempThreshold   (*(f->tempThreshold_))
#define dasTemp         (*(f->dasTemp_))
#define fanState        (*(f->state_))

FanCntrl fanCntrl;

int fanCntrlStep(void)
{
    FanCntrl *f = &fanCntrl;
    fanState = (dasTemp > tempThreshold) ? FAN_CNTRL_OnState : FAN_CNTRL_OffState;
    return STATUS_OK;
}    

int fanCntrlInit(void)
{
    FanCntrl *f = &fanCntrl;
    f->tempThreshold_ = (float *)registerAddr(FAN_CNTRL_TEMPERATURE_REGISTER);
    f->dasTemp_ = (float *)registerAddr(DAS_TEMPERATURE_REGISTER);
    f->state_ = (unsigned int *)registerAddr(FAN_CNTRL_STATE_REGISTER);
    fanState = FAN_CNTRL_OnState;
    return STATUS_OK;
}
#undef  tempThreshold
#undef  dasTemp
#undef  fanState


void setFan(FAN_CNTRL_StateType state)
{
    if (state == FAN_CNTRL_OnState) modify_valve_pump_tec(0x40,0x40);
    else modify_valve_pump_tec(0x40,0);
}
