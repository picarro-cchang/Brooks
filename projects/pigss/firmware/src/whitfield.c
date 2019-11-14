#include <stdio.h>

// Provides strcmp()
#include <string.h>

// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Provides macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>

// Definitions of Two Wire Interface statuses
#include <util/twi.h>

// Functions for working with UART interfaces.
// Definition of LINE_TERMINATION_CHARACTERS
#include "usart.h"

// Definitions common to i2c devices
#include "i2c.h"

// Provides logger_msg and logger_msg_p for log messages tagged with a
// system and severity.
#include "logger.h"

// Provides functions for working with the TCA9548 I2C switch
#include "tca954xa.h"

// Provides setter and getter functions for the system state structure
#include "system.h"

// Provides i2c addresses on Whitfield
#include "whitfield.h"

int8_t whitfield_set_i2c_mux(uint8_t channel) {
  int8_t retval = 0;
  switch(channel) {
  case 0:
    // This is the Topaz A channel
    retval = tca9548a_write(WHITFIELD_I2C_MUX_ADDRESS, 4);
    logger_msg_p("whitfield", log_level_DEBUG, PSTR("I2C mux to Topaz A"));
    break;
  case 1:
    // This is the Topaz B channel
    retval = tca9548a_write(WHITFIELD_I2C_MUX_ADDRESS, 5);
    logger_msg_p("whitfield", log_level_DEBUG, PSTR("I2C mux to Topaz B"));
    break;
  case 2:
    // This is the Vernon channel
    retval = tca9548a_write(WHITFIELD_I2C_MUX_ADDRESS, 6);
    logger_msg_p("whitfield", log_level_DEBUG, PSTR("I2C mux to Vernon"));
    break;
  default:
    break;
  }
  if (retval != 0) {
    logger_msg_p("whitfield", log_level_ERROR, PSTR("Failed to set I2C mux"));
  }
  return retval;
  
}
