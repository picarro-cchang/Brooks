// Module for handling chip-select lines

#include <stdio.h>

// Device-specific port and peripheral definitions.  Also provides
// special bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Library functions and macros for AVR interrupts
#include <avr/interrupt.h>

// Macros and functions for saving and reading data out of flash.
#include <avr/pgmspace.h>

// Convenience functions for busy-wait loops
#include <util/delay.h>

// Functions for using the logger
#include "logger.h"

#include "cs.h"

void cs_init() {
  // Initialize all cs lines

  //**************** Shift register for manifold A *****************//

  // Make PB0 an output initialized high
  PORTB |= _BV(PORTB0);
  DDRB |= _BV(DDB0);

  //**************** Shift register for manifold B *****************//

  // Make PL3 an output initialized high
  PORTL |= _BV(PORTL3);
  DDRL |= _BV(DDL3);
  return;
}


void cs_manifold_a_sr(uint8_t state) {
  // Set the state of the CS line for the shift register on manifold A
  //
  // Arguments:
  //   state -- 1 for CS high, 0 for CS low
  if ( state ) {
    // Set cs high
    PORTB |= _BV(PORTB0);
    loop_until_bit_is_set(PORTB, PORTB0);
  } else {
    // Set cs low
    PORTB &= ~(_BV(PORTB0));
    loop_until_bit_is_clear(PORTB, PORTB0);
  }
  return;
}


void cs_manifold_b_sr(uint8_t state) {
  // Set the state of the CS line for the shift register on manifold B
  //
  // Arguments:
  //   state -- 1 for CS high, 0 for CS low
  if ( state ) {
    // Set cs high
    PORTL |= _BV(PORTL3);
    loop_until_bit_is_set(PORTL, PORTL3);
  } else {
    // Set cs low
    PORTL &= ~(_BV(PORTL3));
    loop_until_bit_is_clear(PORTL, PORTL3);
  }
  return;
}

// cs_manifold_a_dac_1
// cs_manifold_a_dac_2
// ...
// cs_manifold_a_dac_4

// cs_manifold_a_pmi_1
// cs_manifold_a_pmi_2
// ...
// cs_manifold_a_pmi_4

// cs_manifold_a_pmx




