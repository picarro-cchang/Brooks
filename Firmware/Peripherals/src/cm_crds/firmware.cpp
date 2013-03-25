/*
 * Copyright 2012 Picarro, Inc.
 */

#include <Arduino.h>

#include <stdint.h>

#include <avr/interrupt.h>

#include "circular_buffer.h"
#include "picarro_errors.h"
#include "timer.h"
#include "cm_crds.h"


#define SERIAL_BUFFER_LEN 64

struct serialBuffer {
    struct circularBuffer hdr;
    uint8_t items[SERIAL_BUFFER_LEN];
};

volatile struct serialBuffer RX_BUFFER;


volatile uint8_t SENSOR_POLL_EVENT = 0;
volatile uint8_t TIMER0_COUNTER = 0;
/* Timer0 is an 8-bit timer and even when it is fully prescaled, it
 * can only manage (1 / 16e6 * 1024 * 255) ~ 16.32 ms. We want to do a
 * sensor poll approx. every 500 ms, so we need to signal to the main
 * loop every 31 timer interrupts.
 */
volatile uint8_t READ_AND_UPDATE_COUNT = 31;

volatile enum pError LAST_ERROR = PERROR_SUCCESS;


ISR(TIMER0_COMPA_vect)
{
    TIMER0_COUNTER++;

    if (TIMER0_COUNTER == READ_AND_UPDATE_COUNT) {
	TIMER0_COUNTER = 0;
	SENSOR_POLL_EVENT = 1;
    }
}


void SerialEvent(void)
{
    while (Serial.available() > 0 && LAST_ERROR != PERROR_SOFT_SERIAL_OVERFLOW) {
	if (CIRC_BUF_FULL(RX_BUFFER)) {
	    LAST_ERROR = PERROR_SOFT_SERIAL_OVERFLOW;
	    return;
	}

	CIRC_BUF_PUT(RX_BUFFER, Serial.read());
    }
}


void setup(void)
{
    Serial.begin(9600);

    CIRC_BUF_INIT(RX_BUFFER);
}


void loop(void)
{
    while (1) {
	/* Check error state */
	if (LAST_ERROR != PERROR_SUCCESS) {
	    Serial.print("Firmware error status = ");
	    Serial.println(LAST_ERROR);
	}

	Serial.print("RX_BUFFER full? ");
	Serial.println(CIRC_BUF_FULL(RX_BUFFER));

	/* Execute a command */

	/* Check for the next command */
    }
}
