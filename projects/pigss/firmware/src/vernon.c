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

// Provides functions for working with the LM75A temperature sensor
#include "lm75a.h"

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
  if ( vernon_is_connected() ) {

    // Vernon is on channel 2 of the Whitfield I2C mux
    retval += whitfield_set_i2c_mux(2);

    
    // Make P00, P01, P02, P03, P04, P05 GPIO outputs (clear bit
    // positions) for valve control.
    tca9539_write(VERNON_I2C_GPIO_ADDRESS,
		  TCA9539_PORT_0_CONFIG_COMMAND,
		  ~(_BV(VERNON_CLEAN_SOLENOID_SHIFT)) &
		  ~(_BV(VERNON_SPARE_SOLENOID_SHIFT)) &
		  ~(_BV(VERNON_GPIO1_SHIFT)) &
		  ~(_BV(VERNON_GPIO2_SHIFT)) &
		  ~(_BV(VERNON_GPIO3_SHIFT)) &
		  ~(_BV(VERNON_GPIO4_SHIFT)) );
    // Initialize the outputs to zero
    tca9539_write(VERNON_I2C_GPIO_ADDRESS,
		  TCA9539_OUTPUT_PORT_0_REG,
		  ~(_BV(VERNON_CLEAN_SOLENOID_SHIFT)) &
		  ~(_BV(VERNON_SPARE_SOLENOID_SHIFT)) &
		  ~(_BV(VERNON_GPIO1_SHIFT)) &
		  ~(_BV(VERNON_GPIO2_SHIFT)) &
		  ~(_BV(VERNON_GPIO3_SHIFT)) &
		  ~(_BV(VERNON_GPIO4_SHIFT)) );
  } else {
    logger_msg_p("vernon", log_level_ERROR, PSTR("Vernon is not connected"));
    retval += -1;
  }

  uint8_t temp_reading = lm75a_get_temperature(VERNON_I2C_TSENSOR_ADDRESS);
  logger_msg_p("vernon", log_level_DEBUG, PSTR("Vernon temp is %i C"), temp_reading);

  return retval;
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
    logger_msg_p("vernon", log_level_ERROR, PSTR("Vernon is not connected"));
    return 0;
  }

  // We were able to connect just fine.  Vernon doesn't actually have
  // the ability to store a serial number, so we'll just assign a
  // serial number of 1 for a connected board.
  system_state_set_vernon_sernum(1);
  logger_msg_p("vernon", log_level_INFO, PSTR("Connected to Vernon"));
  return 1;
}

bool vernon_is_connected(void) {
  uint16_t sernum = system_state_get_vernon_sernum();
  if (sernum == 0) {
    return false;
  } else {
    return true;
  }
}

int8_t vernon_set_clean_solenoid(uint8_t setting) {
  int8_t retval = 0;
  if (vernon_is_connected()) {
    // Vernon is on channel 2 of the Whitfield I2C mux
    retval += whitfield_set_i2c_mux(2);

    // Get the GPIO output byte
    uint8_t gpio_output_byte = tca9539_read(VERNON_I2C_GPIO_ADDRESS,
					    TCA9539_OUTPUT_PORT_0_REG);
    uint8_t gpio_setting_byte = 0;
    switch( setting ) {
    case 0:
      gpio_setting_byte = gpio_output_byte & ~(_BV(0));
      break;
    case 1:
      gpio_setting_byte = gpio_output_byte | _BV(0);
      break;
    default:
      gpio_setting_byte = gpio_output_byte;
      break;
    }
    tca9539_write(VERNON_I2C_GPIO_ADDRESS,
		  TCA9539_OUTPUT_PORT_0_REG,
		  gpio_setting_byte);
    gpio_output_byte = tca9539_read(VERNON_I2C_GPIO_ADDRESS,
				   TCA9539_OUTPUT_PORT_0_REG);
    logger_msg_p("vernon", log_level_DEBUG, PSTR("Vernon GPIO output byte is 0x%x"),gpio_output_byte);
  } else {
    logger_msg_p("vernon", log_level_ERROR, PSTR("Vernon is not connected"));
    retval += -1;
  }
  return retval;
}

void cmd_vernon_temperature_q( command_arg_t *command_arg_ptr ) {
  uint8_t temperature_reading = lm75a_get_temperature(VERNON_I2C_TSENSOR_ADDRESS);
  usart_printf( USART_CHANNEL_COMMAND, "%i%s",
		temperature_reading,
		LINE_TERMINATION_CHARACTERS );
}
