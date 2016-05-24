/*
 * FILE:
 *   heaterCntrl.c
 *
 * DESCRIPTION:
 *   Heater controller routines
 *
 * Heater control is based on the idea that there is a "target value" for
 *  the cavity TEC drive, and that the heater is adjusted so as to make
 *  the cavity TEC drive close to this value.
 * The target value for the cavity TEC is placed in the variable "uBias".
 *  The value of uBias is calculated as a linear function of the cavity
 *  setpoint temperature, with a slope and offset specified by
 *  HEATER_CNTRL_UBIAS_SLOPE_REGISTER and HEATER_CNTRL_UBIAS_OFFSET_REGISTER.
 * The difference between the actual cavity TEC and the target value
 *  drives the adjustment of the heater current as follows:
 * The difference is quantized to a multiple of the contents of
 *  HEATER_CNTRL_QUANTIZE_REGISTER. Thus if the absolute value of the
 *  difference is is less than half of the quantization, the heater
 *  power is unchanged.
 * The heater power setting (the square of the mark) is incremented by
 *  the product of the HEATER_CNTRL_GAIN_REGISTER and the quantized
 *  difference between the cavity TEC value and the target value.
 *  The mark is updated, and limited to the range specified by
 *  HEATER_CNTRL_MARK_MIN_REGISTER and HEATER_CNTRL_MARK_MAX_REGISTER.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   27-Apr-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include "interface.h"
#include "registers.h"
#include "heaterCntrl.h"
#include "dspAutogen.h"
#include <math.h>

#define state           (*(h->state_))
#define gain            (*(h->gain_))
#define quantize        (*(h->quantize_))
#define uBiasSlope      (*(h->uBiasSlope_))
#define uBiasOffset     (*(h->uBiasOffset_))
#define minMark         (*(h->minMark_))
#define maxMark         (*(h->maxMark_))
#define manualMark      (*(h->manualMark_))
#define mark            (*(h->mark_))
#define cavitySetpoint  (*(h->cavitySetpoint_))
#define cavityTec       (*(h->cavityTec_))

HeaterCntrl heaterCntrl;

int heaterCntrlStep(void)
{
    HeaterCntrl *h = &heaterCntrl;
    float uBias, tecDiff, quantizedDiff, power;

    switch (state)
    {
    case HEATER_CNTRL_DisabledState:
        mark = 0;
        break;
    case HEATER_CNTRL_ManualState:
        mark = manualMark;
        break;
    case HEATER_CNTRL_EnabledState:
        uBias = uBiasSlope * cavitySetpoint + uBiasOffset;
        tecDiff = cavityTec - uBias;
        quantizedDiff = quantize * floor(tecDiff/quantize + 0.5);
        power = mark * mark + gain * quantizedDiff;
        mark = sqrt(power);
        if (mark < minMark) mark = minMark;
        if (mark > maxMark) mark = maxMark;
        break;
    }
    return STATUS_OK;
}

#undef state
#undef gain
#undef quantize
#undef uBiasSlope
#undef uBiasOffset
#undef minMark
#undef maxMark
#undef manualMark
#undef mark
#undef cavitySetpoint
#undef cavityTec

int heaterCntrlInit(void)
{
    HeaterCntrl *h = &heaterCntrl;
    h->state_ = (unsigned int *)registerAddr(HEATER_CNTRL_STATE_REGISTER);
    h->gain_ = (float *)registerAddr(HEATER_CNTRL_GAIN_REGISTER);
    h->quantize_ = (float *)registerAddr(HEATER_CNTRL_QUANTIZE_REGISTER);
    h->uBiasSlope_ = (float *)registerAddr(HEATER_CNTRL_UBIAS_SLOPE_REGISTER);
    h->uBiasOffset_ = (float *)registerAddr(HEATER_CNTRL_UBIAS_OFFSET_REGISTER);
    h->minMark_ = (float *)registerAddr(HEATER_CNTRL_MARK_MIN_REGISTER);
    h->maxMark_ = (float *)registerAddr(HEATER_CNTRL_MARK_MAX_REGISTER);
    h->manualMark_ = (float *)registerAddr(HEATER_CNTRL_MANUAL_MARK_REGISTER);
    h->mark_ = (float *)registerAddr(HEATER_CNTRL_MARK_REGISTER);
    h->cavitySetpoint_ = (float *)registerAddr(CAVITY_TEMP_CNTRL_SETPOINT_REGISTER);
    h->cavityTec_ = (float *)registerAddr(CAVITY_TEC_REGISTER);
    return STATUS_OK;
}
