/*
 * FILE:
 *   misc.c
 *
 * DESCRIPTION:
 *   Miscellaneous routines to perform actions for software testing
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   12-Apr-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include "misc.h"
#include "dspAutogen.h"
#include <math.h>

int pulseGenerator(unsigned int lowDuration,unsigned int highDuration,
                   float *result,PulseGenEnvType *env)
// Generate a pulse
{
    unsigned int period = lowDuration + highDuration;
    unsigned int rem = env->counter % period;
    *result = (rem < lowDuration) ? 0.0 : 1.0;
    env->counter++;
    return STATUS_OK;
}

#define MAX_ORDER (8)
int filter(float x, float *y,FilterEnvType *env)
// Apply a linear filter to x to give y. Coefficients and state are
//   stored in env
{
    int i;
    float div = env->den[0];
    if (div == 0.0) {
        *y = 0.0;
        return ERROR_BAD_FILTER_COEFF;
    }
    *y = env->state[0] + (env->num[0]/div)*x;
    for (i=0;i<MAX_ORDER-1;i++) {
        env->state[i] = env->state[i+1] + (env->num[i+1]*x - env->den[i+1]*(*y))/div;
    }
    env->state[MAX_ORDER-1] = (env->num[MAX_ORDER]*x - env->den[MAX_ORDER]*(*y))/div;
    return STATUS_OK;
}
