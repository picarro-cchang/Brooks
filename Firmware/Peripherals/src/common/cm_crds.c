/*
 * Copyright 2012 Picarro Inc.
 */

#include <Arduino.h>

#include <stdint.h>

#include "lm35.h"
#include "cm_crds.h"


void cmCrdsSetup(void)
{
    analogReference(EXTERNAL);

    pinMode(HEATER2_PWM_BUFFER_VOL, OUTPUT);
    pinMode(HEATER1_PWM_BUFFER_VOL, OUTPUT);

    analogWrite(HEATER2_PWM_BUFFER_VOL, 0);
    analogWrite(HEATER1_PWM_BUFFER_VOL, 0);
}


float cmCrdsGetBufferVolumeTempC(void)
{
    int adcTemp;


    adcTemp = analogRead(TEMP_SENSE_BUFFER_VOL);
    return lm35VoltToCentigrade(((float)adcTemp / 1024.0) * 2.5);
}


int cmCrdsDebugGetADCTemp(void)
{
    return analogRead(TEMP_SENSE_BUFFER_VOL);
}

void cmCrdsSetBufferVolumePWM(uint8_t pwm)
{
    analogWrite(HEATER1_PWM_BUFFER_VOL, pwm);
    analogWrite(HEATER2_PWM_BUFFER_VOL, pwm);
}
