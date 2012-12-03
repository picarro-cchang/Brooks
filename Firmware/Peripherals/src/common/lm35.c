/*
 * Copyright 2012 Picarro Inc.
 *
 * Implementation of LM35 temperature sensor support code.
 */

#include "lm35.h"


float lm35VoltToCentigrade(float v)
{
    return v / 0.010;
}
