#include <stdio.h>

// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Library functions and macros for AVR interrupts
#include <avr/interrupt.h>

// Convenience functions for busy-wait loops
#include <util/delay.h>

// Provides macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>

// Provides logger_msg and logger_msg_p for log messages tagged with a
// system and severity.
#include "logger.h"

// Provide cs functions
#include "cs.h"


#include "spi.h"


void ltc2601_init() {
  // Assume spi has already been initialized
}

uint8_t ltc2601_write( uint16_t (*cs_ptr)(uint8_t), uint8_t command, uint16_t value ) {
  // Make a union to write bytes of value one at a time
  union {
    uint8_t bytes[2];
    uint16_t word;
  } data;
  data.word = value;

  // Align command bits
  uint8_t command_byte = (uint8_t)(command << 4);

  // Pull cs low
  (*cs_ptr)(0);
  
  // Write the command
  spi_write(command_byte);

  // Write the data
  for (int8_t bytenum = 1; bytenum >= 0; bytenum--) {
    spi_write(data.bytes[bytenum]);
    logger_msg_p("ltc2601", log_level_DEBUG, PSTR("Wrote 0x%x"),data.bytes[bytenum]);
  }

  // Return cs high
  (*cs_ptr)(1);
  return 0;
}
