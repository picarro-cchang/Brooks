/*
 * Copyright 2012 Picarro Inc.
 *
 * Implementation of Sze Tan's PID control loop with actuator
 * saturation and rate limitation. This version is intended to be run
 * on ATMega AVR microcontrollers, but can likely be used elsewhere.
 */

#include "pid.h"


void pidStep(struct pidState *st, float processVar)
{
    float integralErr;
    float propErr;
    float derivErr;
    float propIncr;
    float integralIncr;
    float derivIncr;
    float change;


    integralErr = st->setPoint - processVar;
    propErr = (st->b * st->setPoint) - processVar;
    derivErr = (st->c * st->setPoint) - processVar;

    /* Incrememts for the P, I and D terms. */
    propIncr = st->propGain * (propErr - st->propErr1);
    integralIncr = ((st->propGain / st->timeIntegral) * integralErr) +
        ((st->actuatorOut - st->controlOut) / st->regFactorSat);
    derivIncr = (st->timeDeriv / (st->timeDeriv + st->regFactorDeriv)) *
        (st->derivIncr + (st->propGain * st->regFactorDeriv *
                          (derivErr - (2.0 * st->derivErr1) + st->derivErr2)));
    st->controlOut += (propIncr + integralIncr + derivIncr);

    /* Update the actuator value based on rate and value limits. */
    change = st->controlOut - st->actuatorOut;

    if (change > st->iMax) {
        change = st->iMax;
    } else if (change < st->iMin) {
        change = st->iMin;
    }

    st->actuatorOut += change;

    if (st->actuatorOut > st->aMax) {
        st->actuatorOut = st->aMax;
    } else if (st->actuatorOut < st->aMin) {
        st->actuatorOut = st->aMin;
    }

    /* For next time. */
    st->derivIncr = derivIncr;
    st->derivErr2 = st->derivErr1;
    st->derivErr1 = derivErr;
    st->propErr1 = propErr;
}


void pidUpdateSetPoint(struct pidState *st, float setPoint)
{
    st->setPoint = setPoint;
}


/** The ordinary step command requires that some of the previous
 * values are stashed from the previous time through the loop. At t=0,
 * this is obviously not possible, so we provide a command for the
 * first step.
 */
void pidStart(struct pidState *st, float processVar, float controlVar)
{
    float propErr;
    float derivErr;


    propErr = (st->b * st->setPoint) - processVar;
    derivErr = (st->c * st->setPoint) - processVar;

    st->propErr1 = propErr;
    st->derivErr2 = derivErr;
    st->derivErr1 = derivErr;
    st->derivIncr = 0.0;
    st->controlOut = controlVar;
    st->actuatorOut = controlVar;
}
