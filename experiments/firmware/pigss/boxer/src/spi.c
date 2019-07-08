#include <stdio.h>

// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Library functions and macros for AVR interrupts
#include <avr/interrupt.h>

// Provides macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>


// Provides logger_msg and logger_msg_p for log messages tagged with a
// system and severity.
#include "logger.h"


#include "spi.h"


void spi_init() {
  // Set MOSI, SCK, and SS to be outputs.
  DDRB |= _BV(DDB1); // SCK
  DDRB |= _BV(DDB2); // MOSI

  // Set SPI clock rate with 16MHz clock.  The clock frequency can be
  // up to 3 MHz

  // |-------+------+------+---------|
  // | SPI2X | SPR1 | SPR0 | Divider |
  // |-------+------+------+---------|
  // |     0 |    0 |    0 |       4 |
  // |     0 |    0 |    1 |      16 |
  // |     0 |    1 |    0 |      64 |
  // |     0 |    1 |    1 |     128 |
  // |-------+------+------+---------|
  
  // SPCR |= _BV(SPR0); // Set fosc / 16 = 1MHz

  // MPR sensors have a maximum SPI clock of 800kHz
  SPCR |= _BV(SPR1); // Set fosc / 64 = 250 kHz

  // The clock idles low by default (CPOL = 0)
  // The data is sampled on the clock's rising edge (CPHA = 0) by default

  // Leave the data sent MSB first

  // Set master mode
  SPCR |= _BV(MSTR);

  // Enable SPI (this must be the last step when configuring SPCR)
  SPCR |= _BV(SPE);

  // Bring SCK low, so it can idle there
  PORTB &= ~(_BV(PORTB1));

  logger_msg_p("spi", log_level_INFO, PSTR("SPI control register is 0x%x"),SPCR);
  if (bit_is_clear(SPCR, MSTR)) {
    logger_msg_p("spi", log_level_ERROR, PSTR("Failed to set master mode"));
  }
}

uint8_t spi_write( uint8_t data ) {
  // Returns the byte received when data is written to SPI
  //
  // The SS must be handled elsewhere.

  
  // Dump data into the output buffer
  SPDR = data;
  
  // Wait for the transmission complete flag to be set
  while(!(SPSR & _BV(SPIF)));
  logger_msg_p("spi", log_level_DEBUG, PSTR("Wrote 0x%x"),data);

  // Return received data
  return(SPDR);
}
