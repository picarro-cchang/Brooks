/*
 * Copyright 2012 Picarro Inc.
 */

#include <Arduino.h>

#include "Adafruit_MAX31855.h"


Adafruit_MAX31855 TC_0(3, 4, 2);
Adafruit_MAX31855 TC_1(3, 5, 2);
Adafruit_MAX31855 TC_2(3, 6, 2);


void setup(void)
{
    Serial.begin(9600);
    delay(500);
}


void loop(void)
{
    double intT0 = TC_0.readInternal();
    double t0 = TC_0.readCelsius();
    double intT1 = TC_1.readInternal();
    double t1 = TC_1.readCelsius();
    double intT2 = TC_2.readInternal();
    double t2 = TC_2.readCelsius();

    Serial.print(intT0);
    Serial.print(",");
    if (isnan(t0)) {
	Serial.print(-1.0);
    } else {
	Serial.print(t0);
    }
    Serial.print(",");

    Serial.print(intT1);
    Serial.print(",");
    if (isnan(t1)) {
	Serial.print(-1.0);
    } else {
	Serial.print(t1);
    }
    Serial.print(",");

    Serial.print(intT2);
    Serial.print(",");
    if (isnan(t2)) {
	Serial.println(-1.0);
    } else {
	Serial.println(t2);
    }

    delay(1000);
}
