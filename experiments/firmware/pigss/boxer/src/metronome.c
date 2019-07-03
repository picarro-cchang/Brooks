
#include <stdio.h>

// Device-specific port and peripheral definitions.  Also provides
// special bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Library functions and macros for AVR interrupts
#include <avr/interrupt.h>

// Macros and functions for saving and reading data out of flash.
#include <avr/pgmspace.h>

// Functions for using the logger
#include "logger.h"

// Provides commands for handling SPI chip selects
#include "cs.h"

// Provides commands for writing to SPI
#include "spi.h"

// Functions for maintaining a simple schedule
#include "OS.h"

#include "ltc2601.h"

// Functions for working with the BarGraph click board
#include "bargraph.h"

// Functions for working with channels
#include "channel.h"

// Functions for working with the TCA9539 I2C GPIO expander
#include "tca9539.h"

#include "metronome.h"

void metronome_init() {
  logger_msg_p("metronome",log_level_INFO,PSTR("Initializing metronome"));

  // The metronome will use timer1 -- a 16-bit synchronous timer
  //
  // Configure the clock source for timer1 to be the system clock
  // prescaled by 256.  This will cause timer overflows in...
  //
  // 1/(16e6) * 2**16 * 256 = 1.0486
  //
  // ...seconds.  Each timer increment will take 16us.
  TCCR1B |= _BV(CS12);

  // Calculate the compare match value needed to get the metronome
  // period.
  float timer_tick_s = (1.0/F_CPU) * 256;
  uint16_t compare_val = (uint16_t)( METRONOME_PERIOD_MS / (1000 * timer_tick_s) );

  // Timer1 has output compare regesters A, B, and C.  I'll use C for
  // the metronome, since the metronome will always reset the counter.
  // I'll assume the A and B compare values are below C.
  OCR1C = compare_val;

  // Enable compare C match interrupts
  TIMSK1 |= _BV(OCIE1C);
  return;
}

uint32_t pressure_reading  = 0;

void test_task() {
  logger_msg_p("metronome",log_level_DEBUG,PSTR("Test task"));
}


// The metronome interrupt -- interrupt for timer 1 compare match C
ISR(TIMER1_COMPC_vect) {
  // logger_msg_p("metronome", log_level_INFO, PSTR("Tick"));

  // Reset the counter
  TCNT1 = 0;
  OS_TaskTimer();
  return;
}
