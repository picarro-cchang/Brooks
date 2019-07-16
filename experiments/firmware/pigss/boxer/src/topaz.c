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

#include "topaz.h"

int8_t topaz_init(char board) {
  int8_t retval = 0;
  // Handle Topaz A
  if (topaz_is_connected('a')) {
    // Make P00, P01, P02, P03 GPIO outputs (clear bit positions)
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
  } else {
    logger_msg_p("topaz", log_level_ERROR, PSTR("Topaz %c is not connected"),
		 'a');
    return -1;
  }
  return 0;
}

int8_t topaz_connect(char board) {
  // Configure I2C mux on Topaz.  Channel 1 is the only active channel.
  int8_t retval = 0;
  if (board == 'a') {
    retval = tca9548a_write(TOPAZ_I2C_MUX_ADDRESS, 1);    
  } else {
    retval = tca9548a_write(TOPAZ_I2C_MUX_ADDRESS, 1);
  }
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
  int8_t retval = 0;

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

bool topaz_is_connected(char board) {
  uint16_t sernum = system_state_get_topaz_sernum(board);
  if (sernum == 0) {
    return false;
  } else {
    return true;
  }
}
