/*
 * Copyright 2012 Picarro Inc.
 */

#include <Arduino.h>

#include <stdint.h>

#include <avr/interrupt.h>

#include "pid.h"
#include "timer.h"
#include "cm_crds.h"


volatile uint8_t READ_AND_UPDATE_BUFFER_VOL = 0;
volatile uint8_t TIMER0_COUNTER = 0;
/* Timer0 is an 8-bit timer and even when it is fully prescaled, it
 * can only manage (1 / 16e6 * 1024 * 255) ~ 16.32 ms. We want to do a
 * sensor poll approx. every 500 ms, so we need to signal to the main
 * loop every 31 timer interrupts.
 */
volatile uint8_t READ_AND_UPDATE_COUNT = 31;

uint16_t PRBS_GEN = 0x0481;
uint16_t PRBS_REG = 0x0001;



struct pidState pidBufferHeater;


ISR(TIMER0_COMPA_vect)
{
    TIMER0_COUNTER++;

    if (TIMER0_COUNTER == READ_AND_UPDATE_COUNT) {
	TIMER0_COUNTER = 0;
	READ_AND_UPDATE_BUFFER_VOL = 1;
    }
}


void setup(void)
{
    Serial.begin(9600);

    timerClobber0();

    cli();
    TCCR0A = _BV(WGM01);
    TCCR0B = _BV(CS02) | _BV(CS00);
    OCR0A = 255;
    TIMSK0 = _BV(OCIE0A);
    TCNT0 = 0;
    sei();

    cmCrdsSetup();
    cmCrdsSetBufferVolumePWM(128);
}


void loop(void)
{
    if (READ_AND_UPDATE_BUFFER_VOL) {
	float tempC;

	READ_AND_UPDATE_BUFFER_VOL = 0;

	tempC = cmCrdsGetBufferVolumeTempC();
	Serial.print("Buffer volume temperature: ");
	Serial.print(tempC);
	Serial.println(" C");

	if (READ_AND_UPDATE_BUFFER_VOL == 1) {
	    // We are unable to keep up with our desired update speed.
	    Serial.println("READ_AND_UPDATE_BUFFER_VOL laggging.");
	}
    }
}
