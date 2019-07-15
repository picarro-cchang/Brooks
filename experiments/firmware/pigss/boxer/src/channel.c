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

#include "topaz.h"


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
			      false},
			      // End of array indicator.  Must be last
			      {0,false}
			     };

// Define a pointer to the channel configuration
channel_config_t channel_config;
channel_config_t *channel_config_ptr = &channel_config;


void channel_init() {
  uint8_t channel_array_index = 0;
  // Disable all channels
  while ((channel_array[channel_array_index].number) != 0) {
    channel_array[channel_array_index].enabled = false;
    channel_array_index++;
  }
  // Update the hardware and display
  channel_update();
}

int8_t channel_update() {
  uint8_t retval = 0;
  uint8_t gpio_byte = 0;
  uint8_t channel_array_index = 0;
  while ((channel_array[channel_array_index].number) != 0) {
    if (channel_array[channel_array_index].enabled == true) {
      gpio_byte |= _BV(channel_array_index);      
    }
    channel_array_index++;
  }
  // Handle Topaz A hardware
  if (topaz_is_connected('a')) {
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS, TCA9539_OUTPUT_PORT_0_REG, gpio_byte);
    retval = channel_display();
    return 0;
  } else {
    logger_msg_p("topaz", log_level_ERROR, PSTR("Topaz %c is not connected"),
		 'a');
    return -1;
  }
}

uint8_t channel_display() {
  uint16_t bargraph_word = 0;
  uint8_t channel_array_index = 0;
  while ((channel_array[channel_array_index].number) != 0) {
    if (channel_array[channel_array_index].enabled == true) {
      bargraph_word |= _BV(channel_array_index);
    }
    channel_array_index++;
  }
  bargraph_write( &cs_manifold_b_sr, bargraph_word );
  return 0;
}

void cmd_chanena( command_arg_t *command_arg_ptr ) {
  // Channel to enable
  uint16_t channel = command_arg_ptr -> uint16_arg;
  uint8_t channel_index = channel - 1;  
  uint8_t channel_settings = channel_config_ptr -> enable;
  if (channel == 0 || channel > 8 ) {
    // Argument is out of range
    command_nack();
    return;
  }
  // Enable the channel
  channel_array[channel_index].enabled = true;
  channel_update();

  // Acknowledge the successful commmand
  command_ack();
  return;
}

void cmd_chanena_q( command_arg_t *command_arg_ptr ) {
  // Channel to query
  uint16_t channel = command_arg_ptr -> uint16_arg;
  uint8_t channel_index = channel - 1;  
  if (channel == 0 || channel > 8 ) {
    // Argument is out of range
    command_nack();
    return;
  }
  if (channel_array[channel_index].enabled) {
    usart_printf(USART_CHANNEL_COMMAND, "1%s", LINE_TERMINATION_CHARACTERS);
  } else {
    usart_printf(USART_CHANNEL_COMMAND, "0%s", LINE_TERMINATION_CHARACTERS);
  }
  return;
}

void cmd_chanoff( command_arg_t *command_arg_ptr ) {
  // Channel to turn off
  uint16_t channel = command_arg_ptr -> uint16_arg;
  uint8_t channel_index = channel - 1;
  if (channel == 0 || channel > 8 ) {
    // Argument is out of range
    command_nack();
    return;
  }
  // Disable the channel
  channel_array[channel_index].enabled = false;
  channel_update();
  
  // Acknowledge the successful commmand
  command_ack();
  return;
}

void cmd_chanset( command_arg_t *command_arg_ptr ) {
  // Word with lower byte containing channel settings
  uint16_t channel_settings = command_arg_ptr -> uint16_arg;
  if (channel_settings > 255) {
    // Argument is out of range
    command_nack();
    return;
  }
  uint8_t channel_array_index = 0;
  while ((channel_array[channel_array_index].number) != 0) {
    if ((1 << channel_array_index) & channel_settings) {
      // Turn this channel on
      channel_array[channel_array_index].enabled = true;
    } else {
      channel_array[channel_array_index].enabled = false;
    }
    channel_array_index++;
  }
  channel_update();
  // Acknowledge the successful command
  command_ack();
  return;
}

void cmd_chanset_q( command_arg_t *command_arg_ptr ) {
  uint8_t channel_settings = 0;
  uint8_t channel_array_index = 0;
  while ((channel_array[channel_array_index].number) != 0) {
    if (channel_array[channel_array_index].enabled == true) {
      channel_settings += 1 << channel_array_index;      
    }
    channel_array_index++;
  }
  usart_printf(USART_CHANNEL_COMMAND,"%d%s",
	       channel_settings, LINE_TERMINATION_CHARACTERS);
  return;
}
