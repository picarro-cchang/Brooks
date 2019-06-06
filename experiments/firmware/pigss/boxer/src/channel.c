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

// Provides command_ack and command_nack
#include "command.h"

// Provides functions for working with the UART
#include "usart.h"


#include "spi.h"

#include "bargraph.h"

#include "channel.h"

// Initialize the channel array
channel_t channel_array[] = {
			     {1,      // Channel number
			      false}, // Channel enabled for sampling
			     {2,
			      false},
			     {3,
			      false},
			     {4,
			      false},
			     {5,
			      false},
			     {6,
			      false},
			     {7,
			      false},
			     {8,
			      {false},
			      // End of array indicator.  Must be last
			      {0,false}
}

// Define a pointer to the channel configuration
channel_config_t channel_config;
channel_config_t *channel_config_ptr = &channel_config;


void channel_init() {
  // Disable all channels
  channel_write(0);
}

uint8_t channel_write(uint8_t channel_settings) {
  uint8_t retval = 0;
  channel_config_ptr -> enable = channel_settings;
  logger_msg_p("channel", log_level_DEBUG, PSTR("Channel enable byte is %d"),
	       channel_config_ptr -> enable);
  // Write to channel hardware goes here

  retval = channel_update();
  retval = channel_display();
  return 0;
}

uint8_t channel_update() {
  uint8_t retval = 0;
  retval = channel_display();
  return 0;
}

uint8_t channel_display() {
  bargraph_write( &cs_manifold_b_sr, (uint16_t) channel_config_ptr -> enable );
  return 0;
}

void cmd_chanena( command_arg_t *command_arg_ptr ) {
  uint16_t channel = command_arg_ptr -> uint16_arg;
  uint8_t bitshift = channel - 1;  
  uint8_t channel_settings = channel_config_ptr -> enable;
  uint8_t retval = 0;
  if (channel == 0 || channel > 8 ) {
    // Argument is out of range
    command_nack();
    return;
  }
  // Enable the channel
  channel_settings |= (1 << bitshift);
  retval = channel_write(channel_settings);

  // Acknowledge the successful commmand
  command_ack();
  return;
}

void cmd_chanena_q( command_arg_t *command_arg_ptr ) {
  uint16_t channel = command_arg_ptr -> uint16_arg;
  uint8_t bitshift = channel - 1;  
  uint8_t channel_settings = channel_config_ptr -> enable;
  uint8_t retval = 0;
  if (channel == 0 || channel > 8 ) {
    // Argument is out of range
    command_nack();
    return;
  }
  if (channel_settings & (1 << bitshift)) {
    usart_printf(USART_CHANNEL_COMMAND, "1%s", LINE_TERMINATION_CHARACTERS);
  } else {
    usart_printf(USART_CHANNEL_COMMAND, "0%s", LINE_TERMINATION_CHARACTERS);
  }
}

void cmd_chanoff( command_arg_t *command_arg_ptr ) {
  uint16_t channel = command_arg_ptr -> uint16_arg;
  uint8_t channel_settings = channel_config_ptr -> enable;
  uint8_t retval = 0;
  if (channel == 0 || channel > 8 ) {
    // Argument is out of range
    command_nack();
    return;
  }
  uint8_t bitshift = channel - 1;

  // Disable the channel
  channel_settings &= ~(1 << bitshift);

  retval = channel_write(channel_settings);
  // Acknowledge the successful commmand
  command_ack();
  return;
}

void cmd_chanset( command_arg_t *command_arg_ptr ) {
  uint16_t channel_settings = command_arg_ptr -> uint16_arg;
  uint8_t retval = 0;
  if (channel_settings > 255) {
    // Argument is out of range
    command_nack();
    return;
  }
  retval = channel_write(channel_settings);
  // Acknowledge the successful command
  command_ack();
  return;
}

void cmd_chanset_q( command_arg_t *command_arg_ptr ) {
  uint8_t channel_settings = channel_config_ptr -> enable;
  uint8_t retval = 0;
  usart_printf(USART_CHANNEL_COMMAND,"%d%s",
	       channel_settings, LINE_TERMINATION_CHARACTERS);
  return;
}
