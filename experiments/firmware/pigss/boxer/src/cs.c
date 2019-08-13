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

// Functions for working with SPI bus
#include "spi.h"

#include "cs.h"

void cs_init() {
  // Initialize all cs lines

  //*************************** Topaz A ****************************//

  // Make PB0 an output initialized high for Topaz A shift register
  PORTB |= _BV(PORTB0);
  DDRB |= _BV(DDB0);

  // Make PE3 an output initialized low for Topaz A output enable
  PORTE &= ~(_BV(PORTE3));
  DDRE |= _BV(PORTE3);

  // Make PF0 an output initialized high for Topaz A multiplexed CS
  PORTF |= _BV(PORTF0);
  DDRF |= _BV(DDF0);

  //*************************** Topaz B ****************************//

  // Make PL3 an output initialized high for Topaz B shift register
  PORTL |= _BV(PORTL3);
  DDRL |= _BV(DDL3);

  // Make PE4 an output initialized low for Topaz B output enable
  PORTE &= ~(_BV(PORTE4));
  DDRE |= _BV(PORTE4);

  // Make PF1 an output initialized high for Topaz B multiplexed CS
  PORTF |= _BV(PORTF1);
  DDRF |= _BV(DDF1);

  return;
}

int8_t cs_manifold_a_sr(uint8_t state) {
  if ( state ) {
    // Set cs high
    PORTB |= _BV(PORTB0);
    loop_until_bit_is_set(PORTB, PORTB0);
  } else {
    // Set cs low
    PORTB &= ~(_BV(PORTB0));
    loop_until_bit_is_clear(PORTB, PORTB0);
  }
  // There aren't a lot of ways for this to fail.
  return 0;
}

int8_t cs_manifold_b_sr(uint8_t state) {
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
  // There aren't a lot of ways for this to fail.
  return 0;
}

void cs_topaz_a_target(uint8_t state) {
  if ( state ) {
    // Set cs high
    PORTF |= _BV(PORTF0);
    loop_until_bit_is_set(PORTF, PORTF0);
  } else {
    // Set cs low
    PORTF &= ~(_BV(PORTF0));
    loop_until_bit_is_clear(PORTF, PORTF0);
  }
  return;
}

void cs_topaz_b_target(uint8_t state) {
  if ( state ) {
    // Set cs high
    PORTF |= _BV(PORTF1);
    loop_until_bit_is_set(PORTF, PORTF1);
  } else {
    // Set cs low
    PORTF &= ~(_BV(PORTF1));
    loop_until_bit_is_clear(PORTF, PORTF1);
  }
  return;
}

//******************** Proportional valve DACs *********************//

void cs_ch1_dac_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  spi_write(0);
  cs_manifold_a_sr(1);
}

void cs_ch2_dac_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  spi_write(2);
  cs_manifold_a_sr(1);
}

void cs_ch3_dac_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  spi_write(4);
  cs_manifold_a_sr(1);
}

void cs_ch4_dac_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  spi_write(6);
  cs_manifold_a_sr(1);
}

//************************ Pressure sensors ************************//

void cs_ch1_mpr_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  spi_write(1);
  cs_manifold_a_sr(1);
}

void cs_ch2_mpr_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  spi_write(3);
  cs_manifold_a_sr(1);
}

void cs_ch3_mpr_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  spi_write(5);
  cs_manifold_a_sr(1);
}

void cs_ch4_mpr_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  spi_write(7);
  cs_manifold_a_sr(1);
}

void cs_outlet_a_mpr_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  spi_write(8);
  cs_manifold_a_sr(1);
}

void cs_outlet_b_mpr_mux(void) {
  // Set the mux address
  cs_manifold_b_sr(0);
  spi_write(8);
  cs_manifold_b_sr(1);
}

