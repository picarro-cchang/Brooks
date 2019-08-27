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

#include "vernon.h"

int8_t vernon_init(void) {
  int8_t retval = 0;

  // Make PD5 an output initialized high for Vernon I2C power control
  PORTD |= _BV(PORTD5);
  DDRD |= _BV(DDB5);

  return 0;
}

int8_t vernon_connect(void) {
  int8_t retval = 0;
  if (strcmp( PCB, "whitfield" ) == 0) {
    // We're using the Whitfield board.  This has a TCA9544A I2C mux
    // in front of the Vernon connector.

    // Vernon is on channel 2 (SD2 / SC2)
    retval = tca9548a_write(WHITFIELD_I2C_MUX_ADDRESS, 6);
    if (retval != 0) {
      logger_msg_p("vernon", log_level_ERROR, PSTR("Whitfield I2C switch problem"));
    } else {
      logger_msg_p("vernon", log_level_DEBUG, PSTR("Whitfield I2C switch to channel 2"));
    }
  }

  // Configure I2C mux on Vernon.  Channel 0 is the only active channel.


  retval = tca9548a_write(VERNON_I2C_MUX_ADDRESS, 1);



  if (retval != 0) {
    // We were unable to connect
    return -1;
  }
  return retval;
}

uint16_t vernon_get_serial_number(void) {
  int8_t retval = 0;


  // Try to connect to the Vernon board
  retval = vernon_connect();

  if (retval != 0) {
    // There was a problem connecting.  Let the system know that
    // there's no Topaz board connected.
    system_state_set_vernon_sernum(0);
    logger_msg_p("topaz", log_level_ERROR, PSTR("Vernon is not connected"));
    return 0;
  }

  // We were able to connect just fine. 

  system_state_set_vernon_sernum(1);
  logger_msg_p("vernon", log_level_INFO, PSTR("Connected to Vernon"));
  return 1;
}
