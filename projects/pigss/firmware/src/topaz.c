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

// Provides strcmp()
#include <string.h>

// Convenience functions for busy-wait loops
#include <util/delay.h>

// Functions for working with UART interfaces.
// Definition of LINE_TERMINATION_CHARACTERS
#include "usart.h"

// Functions for maintaining a simple schedule
#include "OS.h"

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

// Provides functions for working with the pressure sensors
#include "pressure.h"

// Provides functions and definitions for working with Whitfield boards
#include "whitfield.h"

#include "topaz.h"

int8_t topaz_init(void) {
  int8_t retval = 0;
  // Handle Topaz A
  if (topaz_is_connected('a')) {
    if (strcmp( PCB, "whitfield") == 0) {
      // We're using the Whitfield board.  This has a TCA9544A I2C mux
      // in front of the Topaz connectors.

      // Topaz A is on channel 0 (SD0 / SC0)
      retval += whitfield_set_i2c_mux(0);
    }
    // Make P00, P01, P02, P03 GPIO outputs (clear bit positions) for
    // valve control.
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
		  TCA9539_PORT_0_CONFIG_COMMAND,
		  ~(_BV(TOPAZ_SOLENOID_1_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_2_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_3_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_4_SHIFT)) );
    tca9539_write(0x74,0x06,0);
    // Initialize the outputs to zero
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
		  TCA9539_OUTPUT_PORT_0_REG,
		  ~(_BV(TOPAZ_SOLENOID_1_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_2_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_3_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_4_SHIFT)) );
    // Make P17 an output for the reset line
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
		  TCA9539_PORT_1_CONFIG_COMMAND,
		  (uint8_t) ~(_BV(TOPAZ_CLR_SHIFT)) );
    // Initialize the reset line high
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
    		  TCA9539_OUTPUT_PORT_1_REG,
    		  _BV(TOPAZ_CLR_SHIFT) );
    topaz_reset('a');
  } else {
    logger_msg_p("topaz", log_level_ERROR, PSTR("Topaz %c is not connected"),
		 'a');
    retval += -1;
  }
  // Handle Topaz B
  if (topaz_is_connected('b')) {
    if (strcmp( PCB, "whitfield") == 0) {
      // We're using the Whitfield board.  This has a TCA9544A I2C mux
      // in front of the Topaz connectors.

      // Topaz B is on channel 1 (SD1 / SC1)
      retval += whitfield_set_i2c_mux(1);
    }
    // Make P00, P01, P02, P03 GPIO outputs (clear bit positions) for
    // valve control.
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
		  TCA9539_PORT_0_CONFIG_COMMAND,
		  ~(_BV(TOPAZ_SOLENOID_1_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_2_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_3_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_4_SHIFT)) );
    tca9539_write(0x74,0x06,0);
    // Initialize the outputs to zero
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
		  TCA9539_OUTPUT_PORT_0_REG,
		  ~(_BV(TOPAZ_SOLENOID_1_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_2_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_3_SHIFT)) &
		  ~(_BV(TOPAZ_SOLENOID_4_SHIFT)) );
    // Make P17 an output for the reset line
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
		  TCA9539_PORT_1_CONFIG_COMMAND,
		  (uint8_t) ~(_BV(TOPAZ_CLR_SHIFT)) );
    // Initialize the reset line high
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
    		  TCA9539_OUTPUT_PORT_1_REG,
    		  _BV(TOPAZ_CLR_SHIFT) );
    topaz_reset('b');
  } else {
    logger_msg_p("topaz", log_level_ERROR, PSTR("Topaz %c is not connected"),
		 'B');
    retval += -1;
  }
  return retval;
}

int8_t topaz_connect(char board) {
  int8_t retval = 0;
  if (strcmp( PCB, "whitfield" ) == 0) {
    // We're using the Whitfield board.  This has a TCA9544A I2C mux
    // in front of the Topaz connectors.
    switch(board) {
    case 'a':
      // Topaz A is on channel 0 (SD0 / SC0)
      retval += whitfield_set_i2c_mux(0);
      break;
    case 'b':
      // Topaz B is on channel 1 (SD1 / SC1)
      retval += whitfield_set_i2c_mux(1);
      break;
    default:
      return -1;
    }
  }

  // Configure I2C mux on Topaz.  Channel 1 is the only active channel.
  retval = tca9548a_write(TOPAZ_I2C_MUX_ADDRESS, 1);
  if (retval != 0) {
    // We were unable to connect
    return -1;
  }
  return retval;
}

int8_t topaz_reset(char board) {
  int8_t retval = 0;
  switch(board) {
  case 'a':
    if (strcmp( PCB, "whitfield") == 0) {
      // We're using the Whitfield board.  This has a TCA9544A I2C mux
      // in front of the Topaz connectors.

      // Topaz A is on channel 0 (SD0 / SC0)
      retval += whitfield_set_i2c_mux(0);
    }
    if (!topaz_is_connected('a')) {
      // No Topaz connection
      return -1;
    }
    break;
  case 'b':
    if (strcmp( PCB, "whitfield") == 0) {
      // We're using the Whitfield board.  This has a TCA9544A I2C mux
      // in front of the Topaz connectors.

      // Topaz B is on channel 1 (SD1 / SC1)
      retval += whitfield_set_i2c_mux(1);
    }
    if (!topaz_is_connected('b')) {
      // No Topaz connection
      return -1;
    }
    break;
  default:
    retval += -1;
  }
  // Stop the pressure triggers and reads
  OS_SetTaskState(pressure_state_get_trigger_task_number(), SUSPENDED);
  OS_SetTaskState(pressure_state_get_read_task_number(), SUSPENDED);
  
  // Bring the reset line low
  tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
		TCA9539_OUTPUT_PORT_1_REG,
		0);

  // Wait for MPR devices to reset.  Honeywell claims this can take 250ms
  _delay_ms(250);
  
  // Bring the reset line back up
  tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
		TCA9539_OUTPUT_PORT_1_REG,
		_BV(TOPAZ_CLR_SHIFT));

  // Wait for the power-on reset time
  _delay_ms(5);

  // Start the pressure triggers and reads again
  OS_SetTaskState(pressure_state_get_trigger_task_number(), BLOCKED);
  OS_SetTaskState(pressure_state_get_read_task_number(), BLOCKED);

  return retval;
}



int8_t topaz_set_serial_number(char board, uint16_t serial_number) {
  uint8_t i2c_address;
  int8_t retval = 0;

  union {
    uint8_t b[2];
    uint16_t w;
  } sernum_union;
  sernum_union.w = serial_number;

  // Enable I2C communication on the chosen board
  retval = topaz_connect(board);

  uint16_t register_address;
  for (int8_t bytenum = 1; bytenum >= 0; bytenum--) {
    // MSB is byte 1
    register_address = TOPAZ_SERNUM_ADDR + bytenum;
    mb85rc256v_write(TOPAZ_I2C_NVM_ADDRESS,
		     register_address,
		     sernum_union.b[bytenum]);
  }
  return retval;
}

int8_t topaz_get_temperature(char board) {
  int8_t retval = 0;

  // Enable I2C communication on the chosen board
  retval = topaz_connect(board);
  uint8_t temperature_reading = lm75a_get_temperature(TOPAZ_I2C_TSENSOR_ADDRESS);

  // The usable range of the lm75 is -55C to +125C.  I'm already
  // ignoring negative temperatures, and it's OK to cast the output as int8.
  if (retval >= 0) {
    return (int8_t) temperature_reading;
  } else {
    return retval;
  }
  
}

uint16_t topaz_get_serial_number(char board) {
  uint8_t i2c_address;
  int8_t retval = 0;

  union {
    uint8_t b[2];
    uint16_t w;
  } sernum_union;


  // Try to connect to the Topaz board
  retval = topaz_connect(board);

  if (retval != 0) {
    // There was a problem connecting.  Let the system know that
    // there's no Topaz board connected.
    system_state_set_topaz_sernum(board, 0);
    logger_msg_p("topaz", log_level_ERROR, PSTR("Topaz %c is not connected"),
	       board);
    return 0;
  }

  // We were able to connect just fine.  Get the serial number and set
  // it in the system state structure.
  uint16_t register_address;
  for (int8_t bytenum = 1; bytenum >= 0; bytenum--) {
    // MSB is byte 1
    register_address = TOPAZ_SERNUM_ADDR + bytenum;
    sernum_union.b[bytenum] = mb85rc256v_read(TOPAZ_I2C_NVM_ADDRESS,
					      register_address);
  }
  system_state_set_topaz_sernum(board, sernum_union.w);
  logger_msg_p("topaz", log_level_INFO, PSTR("Found serial %u for board %c"),
	       sernum_union.w, board);
  return sernum_union.w;
}

void cmd_topaz_a_set_serial_number( command_arg_t *command_arg_ptr ) {
  int8_t retval = 0;
  uint16_t sernum = (command_arg_ptr -> uint16_arg);
  retval += topaz_set_serial_number('a', sernum);
  if (retval < 0) {
    command_nack(NACK_COMMAND_FAILED);
  } else {
    // Acknowledge the successful command
    command_ack();
  }
}

void cmd_topaz_b_set_serial_number( command_arg_t *command_arg_ptr ) {
  int8_t retval = 0;
  uint16_t sernum = (command_arg_ptr -> uint16_arg);
  retval += topaz_set_serial_number('b', sernum);
  if (retval < 0) {
    command_nack(NACK_COMMAND_FAILED);
  } else {
    // Acknowledge the successful command
    command_ack();
  }
}

void cmd_topaz_a_get_serial_number( command_arg_t *command_arg_ptr ) {
  if (!topaz_is_connected('a')) {
    // There's no Topaz A
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
  uint16_t sernum;
  sernum = topaz_get_serial_number('a');
  usart_printf(USART_CHANNEL_COMMAND, "%u%s",
	       sernum,
	       LINE_TERMINATION_CHARACTERS );
}

void cmd_topaz_b_get_serial_number( command_arg_t *command_arg_ptr ) {
  if (!topaz_is_connected('b')) {
    // There's no Topaz B
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
  uint16_t sernum;
  sernum = topaz_get_serial_number('b');
  usart_printf(USART_CHANNEL_COMMAND, "%u%s",
	       sernum,
	       LINE_TERMINATION_CHARACTERS );
}

void cmd_topaz_a_reset( command_arg_t *command_arg_ptr ) {
  if (!topaz_is_connected('a')) {
      // There's no Topaz A
      command_nack(NACK_COMMAND_FAILED);
    return;
  }
  int8_t retval = 0;
  retval += topaz_reset('a');
  if (retval == 0) {
    command_ack();
  } else {
    command_nack(NACK_COMMAND_FAILED);
  }
}

void cmd_topaz_b_reset( command_arg_t *command_arg_ptr ) {
  if (!topaz_is_connected('b')) {
      // There's no Topaz B
      command_nack(NACK_COMMAND_FAILED);
    return;
  }
  int8_t retval = 0;
  retval += topaz_reset('b');
  if (retval == 0) {
    command_ack();
  } else {
    command_nack(NACK_COMMAND_FAILED);
  }
}

void cmd_topaz_a_temperature_q( command_arg_t *command_arg_ptr ) {
  if (!topaz_is_connected('a')) {
    // There's no Topaz A
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
  uint8_t temperature_reading = topaz_get_temperature('a');
  usart_printf( USART_CHANNEL_COMMAND, "%i%s",
		temperature_reading,
		LINE_TERMINATION_CHARACTERS );
  
}

void cmd_topaz_b_temperature_q( command_arg_t *command_arg_ptr ) {
  if (!topaz_is_connected('b')) {
    // There's no Topaz B
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
  uint8_t temperature_reading = topaz_get_temperature('b');
  usart_printf( USART_CHANNEL_COMMAND, "%i%s",
		temperature_reading,
		LINE_TERMINATION_CHARACTERS );
  
}

bool topaz_is_connected(char board) {
  uint16_t sernum = system_state_get_topaz_sernum(board);
  if (sernum == 0) {
    return false;
  } else {
    return true;
  }
}
