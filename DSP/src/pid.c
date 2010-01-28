/*
 * FILE:
 *   pid.c
 *
 * DESCRIPTION:
 *   PID controller routines
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   16-Dec-2008  sze  Initial version.
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */
#include "pid.h"

// Single step of a PID controller

#define r (*(params->r_))
#define y processVar
#define x extVar
#define b (*(params->b_))
#define c (*(params->c_))
#define h (*(params->h_))
#define K (*(params->K_))
#define Ti (*(params->Ti_))
#define Td (*(params->Td_))
#define N (*(params->N_))
#define S (*(params->S_))
#define Imax (*(params->Imax_))
#define Amin (*(params->Amin_))
#define Amax (*(params->Amax_))
#define ffwd (*(params->ffwd_))

void pid_step(float processVar, float extVar, PidState *state,
              PidParamsRef *params)
{
    float err, perr, derr, Pincr, Iincr, Dincr, change;
    err = r-y;
    perr = b*r-y;
    derr = c*r-y;
    change = ffwd*(y-x);
    Pincr = K*(perr - state->perr);
    Iincr = K*h/Ti * err + (state->a-state->u-change)/S;
    Dincr = Td/(Td+N*h)*(state->Dincr +
                         K*N*(derr-2*state->derr1+state->derr2));
    state->u = state->u + Pincr + Iincr + Dincr;
    change += state->u - state->a;
    if (change > Imax) change = Imax;
    if (change < -Imax) change = -Imax;
    state->a = state->a + change;
    if (state->a > Amax) state->a = Amax;
    if (state->a < Amin) state->a = Amin;
    state->Dincr = Dincr;
    state->derr2 = state->derr1;
    state->derr1 = derr;
    state->perr = perr;
}

#undef r
#undef y
#undef x
#undef b
#undef c
#undef h
#undef K
#undef Ti
#undef Td
#undef N
#undef S
#undef Imax
#undef Amin
#undef Amax
#undef ffwd

// Bumpless start for a PID controller

#define r (*(params->r_))
#define y processVar
#define b (*(params->b_))
#define c (*(params->c_))
#define h (*(params->h_))
#define K (*(params->K_))
#define Ti (*(params->Ti_))
#define Td (*(params->Td_))
#define N (*(params->N_))
#define S (*(params->S_))
#define Imax (*(params->Imax_))
#define Amin (*(params->Amin_))
#define Amax (*(params->Amax_))

void pid_bumpless_restart(float processVar,float controlVar,
                          PidState *state,PidParamsRef *params)
{
    float perr, derr;
    perr = b*r-y;
    derr = c*r-y;
    state->perr = perr;
    state->derr1 = state->derr2 = derr;
    state->Dincr = 0.0;
    state->u = state->a = controlVar;
}

#undef r
#undef y
#undef b
#undef c
#undef h
#undef K
#undef Ti
#undef Td
#undef N
#undef S
#undef Imax
#undef Amin
#undef Amax
