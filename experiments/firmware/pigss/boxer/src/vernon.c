#include <stdio.h>

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

#include "vernon.h"

int8_t vernon_init(void) {
  int8_t retval = 0;

  // Make PD5 an output initialized high for Vernon I2C power control
  PORTD |= _BV(PORTD5);
  DDRD |= _BV(DDB5);
  
  return 0;
}
