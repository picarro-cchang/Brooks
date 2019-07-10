#include <stdio.h>

// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>


// Provides macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>

// Provides logger_msg and logger_msg_p for log messages tagged with a
// system and severity.
#include "logger.h"


#include "i2c.h"


void i2c_init() {
  // Set the TWI clock prescaler
  //
  // Setting the whole status register to zero sets a prescaler of 1.
  // The i2c clock frequency is given by:
  //
  // Fscl = Fosc / (16 + 2 * TWBR * prescaler)
  //
  // With Fosc = 16MHz and prescaler = 1, TWBR = 64 gives 100kHz SCL
  TWSR = 0;
  TWBR = 64;
}

