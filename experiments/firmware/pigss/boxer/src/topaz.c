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

// 32K x 8 I2C FRAM module
#include "mb85rc256v.h"

# include "topaz.h"

int8_t topaz_a_connect(void) {
  // Configure I2C mux on Topaz.  Channel 1 is the only active channel.
  int8_t retval = tca9548a_write(TOPAZ_I2C_MUX_ADDRESS, 1);
  if (retval != 0) {
    // We were unable to connect
    return -1;
  }
  return 0;
}

int8_t topaz_set_serial_number(char board, uint16_t serial_number) {
  uint8_t i2c_address;

  union {
    uint8_t b[2];
    uint16_t w;
  } sernum_union;
  sernum_union.w = serial_number;
  
  if (board == 'a') {
    // Configure system board I2C mux or I2C address here
    i2c_address = TOPAZ_I2C_MUX_ADDRESS;
  } else {
    i2c_address = TOPAZ_I2C_MUX_ADDRESS;
  }

  // Configure I2C mux on Topaz.  The only active mux position is 1.
  tca9548a_write(i2c_address,1);
 

  uint16_t register_address;
  for (int8_t bytenum = 1; bytenum >= 0; bytenum--) {
    // MSB is byte 1
    register_address = TOPAZ_SERNUM_ADDR + bytenum;
    mb85rc256v_write(TOPAZ_I2C_NVM_ADDRESS,
		     register_address,
		     sernum_union.b[bytenum]);    
  }
  return 0;
}

uint16_t topaz_get_serial_number(char board) {
  uint8_t i2c_address;

  union {
    uint8_t b[2];
    uint16_t w;
  } sernum_union;
  
  if (board == 'a') {
    // Configure system board I2C mux or I2C address here
    i2c_address = TOPAZ_I2C_MUX_ADDRESS;
  } else {
    i2c_address = TOPAZ_I2C_MUX_ADDRESS;
  }

  // Configure I2C mux on Topaz.  The only active mux position is 1.
  tca9548a_write(i2c_address,1);
  
  uint16_t register_address;
  for (int8_t bytenum = 1; bytenum >= 0; bytenum--) {
    // MSB is byte 1
    register_address = TOPAZ_SERNUM_ADDR + bytenum;
    sernum_union.b[bytenum] = mb85rc256v_read(TOPAZ_I2C_NVM_ADDRESS,
					      register_address);    
  }
  return sernum_union.w;
}

void cmd_topaz_a_set_serial_number( command_arg_t *command_arg_ptr ) {
  uint16_t sernum = (command_arg_ptr -> uint16_arg);
  topaz_set_serial_number('a', sernum);
  
  // Acknowledge the successful command
  command_ack();
}

void cmd_topaz_a_get_serial_number( command_arg_t *command_arg_ptr ) {
  uint16_t sernum;
  sernum = topaz_get_serial_number('a');
  usart_printf(USART_CHANNEL_COMMAND, "%u%s",
	       sernum,
	       LINE_TERMINATION_CHARACTERS );
}

void cmd_topaz_b_set_serial_number( command_arg_t *command_arg_ptr ) {
  uint16_t sernum = (command_arg_ptr -> uint16_arg);
  topaz_set_serial_number('b', sernum);
  
  // Acknowledge the successful command
  command_ack();
}

void cmd_topaz_b_get_serial_number( command_arg_t *command_arg_ptr ) {
  uint16_t sernum;
  sernum = topaz_get_serial_number('b');
  usart_printf(USART_CHANNEL_COMMAND, "%u%s",
	       sernum,
	       LINE_TERMINATION_CHARACTERS );
}
