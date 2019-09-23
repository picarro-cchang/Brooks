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

// Convenience macros for setting and clearing bits
#include "avr035.h"

// Functions for using the logger
#include "logger.h"

// Functions for working with SPI bus
#include "spi.h"

#include "cs.h"

void cs_init() {
  // Initialize all cs lines

  //*************************** Topaz A ****************************//

  // Make PB0 an output initialized high for Topaz A shift register CS
  SETBIT(PORTB,PORTB0);
  SETBIT(DDRB,DDB0);

  // Make PE3 an output initialized high for Topaz A shift register
  // output enable
  SETBIT(PORTE,PORTE3);
  SETBIT(DDRE,DDE3);

  // Write a safe value to the shift register
  cs_manifold_a_sr(0);
  spi_write(0xff);
  cs_manifold_a_sr(1);

  // Make PF0 an output initialized high for Topaz A multiplexed CS
  SETBIT(PORTF,PORTF0);
  SETBIT(DDRF,DDF0);

  // Enable the Topaz A shift register
  manifold_a_sr_noe(0);

  //*************************** Topaz B ****************************//

  // Make PL3 an output initialized high for Topaz B shift register CS
  SETBIT(PORTL,PORTL3);
  SETBIT(DDRL,DDL3);

  // Make PE4 an output initialized high for Topaz B shift register
  // output enable
  SETBIT(PORTE,PORTE4);
  SETBIT(DDRE,DDE4);

  // Write a safe value to the shift register
  cs_manifold_b_sr(0);
  spi_write(0xff);
  cs_manifold_b_sr(1);

  // Make PF1 an output initialized high for Topaz B multiplexed CS
  SETBIT(PORTF,PORTF1);
  SETBIT(DDRF,DDF1);

  // Enable the Topaz B shift register
  manifold_b_sr_noe(0);

  return;
}

int8_t manifold_a_sr_noe(uint8_t state) {
  if ( state ) {
    // Set nOE high to disable shift register
    SETBIT(PORTE,PORTE3);
    loop_until_bit_is_set(PORTE, PORTE3);
  } else {
    // Set nOE low to enable shift register
    CLEARBIT(PORTE,PORTE3);
    loop_until_bit_is_clear(PORTE, PORTE3);
  }
  return 0;
}

int8_t manifold_b_sr_noe(uint8_t state) {
  if ( state ) {
    // Set nOE high to disable shift register
    SETBIT(PORTE,PORTE4);
    loop_until_bit_is_set(PORTE, PORTE4);
  } else {
    // Set nOE low to enable shift register
    CLEARBIT(PORTE,PORTE4);
    loop_until_bit_is_clear(PORTE, PORTE4);
  }
  return 0;
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

// We can set both muxes at the same time, since that only uses one
// SPI write.  The correct device will still be identified by the A or
// B target CS line.

void cs_nw_dac_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  cs_manifold_b_sr(0);
  spi_write(0);
  cs_manifold_a_sr(1);
  cs_manifold_b_sr(1);
}

void cs_sw_dac_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  cs_manifold_b_sr(0);
  spi_write(2);
  cs_manifold_a_sr(1);
  cs_manifold_b_sr(1);
}

void cs_se_dac_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  cs_manifold_b_sr(0);
  spi_write(4);
  cs_manifold_a_sr(1);
  cs_manifold_b_sr(1);
}

void cs_ne_dac_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  cs_manifold_b_sr(0);
  spi_write(6);
  cs_manifold_a_sr(1);
  cs_manifold_b_sr(1);
}

//************************ Pressure sensors ************************//

void cs_nw_mpr_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  cs_manifold_b_sr(0);
  spi_write(1);
  cs_manifold_a_sr(1);
  cs_manifold_b_sr(1);
}

void cs_sw_mpr_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  cs_manifold_b_sr(0);
  spi_write(3);
  cs_manifold_a_sr(1);
  cs_manifold_b_sr(1);
}

void cs_se_mpr_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  cs_manifold_b_sr(0);
  spi_write(5);
  cs_manifold_a_sr(1);
  cs_manifold_b_sr(1);
}

void cs_ne_mpr_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  cs_manifold_b_sr(0);
  spi_write(7);
  cs_manifold_a_sr(1);
  cs_manifold_b_sr(1);
}

void cs_outlet_mpr_mux(void) {
  // Set the mux address
  cs_manifold_a_sr(0);
  cs_manifold_b_sr(0);
  spi_write(8);
  cs_manifold_a_sr(1);
  cs_manifold_b_sr(1);
}

