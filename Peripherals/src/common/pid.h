/*
 * Copyright 2012 Picarro Inc.
 *
 * Implementation of Sze Tan's PID control loop with actuator
 * saturation and rate limitation. This version is intended to be run
 * on ATMega AVR microcontrollers, but can likely be used elsewhere.
 */

#ifndef __PID_H__
#define __PID_H__


struct pidState {
    /* Target setpoint */
    float setPoint;
    /* Actuator output signal */
    float actuatorOut;
    /* Control output signal, before saturation effects */
    float controlOut;
    /* Previous (N -1) proportional error */
    float propErr1;
    /* Previous (N - 1) derivative error */
    float derivErr1;
    /* Previous (N - 2) derivative error */
    float derivErr2;
    /* Derivative increment */
    float derivIncr;
    /* Proportional setpoint weight */
    float b;
    /* Derivative setpoint weight */
    float c;
    /* Proportional gain */
    float propGain;
    /* Integral time */
    float timeIntegral;
    /* Derivative time */
    float timeDeriv;
    /* Derivative regularization factor */
    float regFactorDeriv;
    /* Saturation regularization factor */
    float regFactorSat;
    /* Most negative actuator increment per sample */
    float iMin;
    /* Most positive actuator increment per sample */
    float iMax;
    /* Minimum allowed actuator value */
    float aMin;
    /* Maximum allowed actuator value */
    float aMax;
};

void pidUpdateSetPoint(struct pidState *st, float setPoint);
void pidStart(struct pidState *st, float processVar, float controlVar);
void pidStep(struct pidState *st, float processVar);

#endif /* __PID_H__ */
