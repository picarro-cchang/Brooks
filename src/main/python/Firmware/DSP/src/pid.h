/*
 * FILE:
 *   pid.h
 *
 * DESCRIPTION:
 *   Header file for PID temperature controller
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   16-Dec-2008  sze  Initial version.
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */
#ifndef  _PID_H_
#define  _PID_H_

typedef struct PID_STATE
{
    float a;      // Actuator output signal
    float u;      // Control signal, before saturation effects
    float perr;   // Saved proportional error
    float derr1;  // Saved derivative error on last sample
    float derr2;  // Saved derivative error two samples ago
    float Dincr;  // Variable for calculating derivative increment
} PidState;

typedef struct PID_PARAMS_BY_REF
{
    float *r_;    // Setpoint
    float *b_;    // Proportional setpoint weight
    float *c_;    // Derivative setpoint weight
    float *h_;    // Sample interval
    float *K_;    // Proportional gain
    float *Ti_;   // Integral time
    float *Td_;   // Derivative time
    float *N_;    // Derivative regularization factor
    float *S_;    // Saturation regularization factor
    float *Imax_; // Largest actuator increment/decrement per sample
    float *Amin_; // Minimum allowed actuator value
    float *Amax_; // Maximum allowed actuator value
    float *ffwd_; // Feed-forward factor based on external temperature
} PidParamsRef;

void pid_step(float processVar,float extVar,PidState *state,
              PidParamsRef *params);
void pid_bumpless_restart(float processVar,float controlVar,
                          PidState *state,PidParamsRef *params);

#endif
