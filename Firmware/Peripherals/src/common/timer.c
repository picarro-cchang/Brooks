/*
 * Copyright 2012 Picarro Inc.
 */

#include <avr/interrupt.h>

#include "timer.h"


/** The Arduino takes over Timer0 for its own purposes, namely for
 * providing Fast PWM outputs and the delays() and millis() series of
 * functions.
 *
 * Calling this routine gives Timer0 back to your code (at the expense
 * of losing the ability to do PWM with its pins and calling the
 * aforementioned routines).
 */
void timerClobber0(void)
{
    cli();
    TIMSK0 = 0;
    TCCR0A = 0;
    TCCR0B = 0;
    TCNT0 = 0;
    OCR0A = 0;
    OCR0B = 0;
    sei();
}
