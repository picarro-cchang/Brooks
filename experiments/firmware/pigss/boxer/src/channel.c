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

// Provides strcmp()
#include <string.h>

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

// Provides definitions for working with the Whitfield PCB
#include "whitfield.h"

#include "spi.h"

// Provides functions for handling system states
#include "system.h"

// Provides definitions and functions for working with the front panel
#include "aloha.h"

// Provides commands for working with bypass DACs
#include "pressure.h"

// Provides commands for working with the TCA954xA I2C multiplexers
#include "tca954xa.h"



#include "channel.h"

// Initialize the channel array
channel_t channel_array[] = {
			     {1,      // Channel number
			      false,  // Channel enabled for sampling
			      3},     // Position in the hardware byte
			     {2,
			      false,
			     2},
			     {3,
			      false,
			     0},
			     {4,
			      false,
			     1},
			     {5,
			      false,
			     7},
			     {6,
			      false,
			     6},
			     {7,
			      false,
			     4},
			     {8,
			      false,
			     5},
			      // End of array indicator.  Must be last
			     {0,false,0}
			     };

// Define a pointer to the channel configuration
channel_config_t channel_config;
channel_config_t *channel_config_ptr = &channel_config;

void channel_init() {
  // Disable all channels
  channel_set(0);
}

int8_t channel_set( uint8_t setting ) {
  uint8_t channel_array_index = 0;
  while ((channel_array[channel_array_index].number) != 0) {
    if ((1 << channel_array_index) & setting) {
      // Turn this channel on
      channel_array[channel_array_index].enabled = true;
    } else {
      channel_array[channel_array_index].enabled = false;
    }
    channel_array_index++;
  }
  channel_update();
  return 0;
}

int8_t channel_update() {
  int8_t retval = 0;
  uint8_t channel = 0;

  // Bits in the channel_hardware_byte will be cleared if the channel is
  // enabled.
  uint8_t channel_hardware_byte = 0;

  // Keep track of how many channels have been enabled
  uint8_t enabled_channels = 0;

  // The new LED value
  uint32_t new_led_value = system_state_get_fp_led_value();

  uint8_t channel_array_index = 0;
  // Loop through the channel array to set the hardware byte for
  // active or inactive channels.  Set the bypass DACs for inactive
  // channels.
  while ((channel_array[channel_array_index].number) != 0) {
    channel = channel_array[channel_array_index].number;
    if (channel_array[channel_array_index].enabled == true) {
      // Channel is enabled for sampling
      enabled_channels += 1;
      // Set hardware byte for configuring solenoid valves.  Solenoid
      // valves are energized when a channel is disabled, so enabled
      // channel bits are cleared in the hardware byte.
      channel_hardware_byte &= ~(_BV(channel_array[channel_array_index].bitshift));

      // Configure LED values for new lit LEDs
      switch(channel) {
      case 1:
	new_led_value |= (uint32_t) 1<<CH1_GREEN;
	break;
      case 2:
	new_led_value |= (uint32_t) 1<<CH2_GREEN;
	break;
      case 3:
	new_led_value |= (uint32_t) 1<<CH3_GREEN;
	break;
      case 4:
	new_led_value |= (uint32_t) 1<<CH4_GREEN;
	break;
      case 5:
	new_led_value |= (uint32_t) 1<<CH5_GREEN;
	break;
      case 6:
	new_led_value |= (uint32_t) 1<<CH6_GREEN;
	break;
      case 7:
	new_led_value |= (uint32_t) 1<<CH7_GREEN;
	break;
      case 8:
	new_led_value |= (uint32_t) 1<<CH8_GREEN;
	break;	
      }
    } else {
      // Channel has been disabled.  Set the bypass DAC to get the
      // inactive flow level.
      retval = pressure_dac_set(channel, PRESSURE_DAC_INACTIVE_COUNTS);
      // Clear the bit in the hardware byte
      channel_hardware_byte |= _BV(channel_array[channel_array_index].bitshift);

      // Remove lit LEDs
      switch(channel) {
      case 1:
	new_led_value &=  ~( (uint32_t) 1<<CH1_GREEN);
	break;
      case 2:
      	new_led_value &= ~( (uint32_t) 1<<CH2_GREEN);
      	break;
      case 3:
      	new_led_value &= ~( (uint32_t) 1<<CH3_GREEN);
      	break;
      case 4:
      	new_led_value &= ~( (uint32_t) 1<<CH4_GREEN);
      	break;
      case 5:
      	new_led_value &= ~( (uint32_t) 1<<CH5_GREEN);
      	break;
      case 6:
      	new_led_value &= ~( (uint32_t) 1<<CH6_GREEN);
      	break;
      case 7:
      	new_led_value &= ~( (uint32_t) 1<<CH7_GREEN);
      	break;
      case 8:
      	new_led_value &= ~( (uint32_t) 1<<CH8_GREEN);
      	break;
	
      }
    }
    channel_array_index++;
  }
  if (enabled_channels > 0) {
    // If any channel is enabled, we need to be in control mode
    retval += system_enter_control();
    // Clear the blue LED bits
    new_led_value = aloha_clear_clean_led_bits(new_led_value);
  } else {
    // There are no enabled channels.  This means we're in standby.
    set_system_state(system_state_STANDBY);
  }

  // Update hardware.  Disabled channels are energized.
  uint8_t topaz_a_byte = channel_hardware_byte;
  uint8_t topaz_b_byte = channel_hardware_byte >> 4;

  // Handle Topaz A hardware
  if (topaz_is_connected('a')) {
    if (strcmp( PCB, "whitfield") == 0) {
      // We're using the Whitfield board.  This has a TCA9544A I2C mux
      // in front of the Topaz connectors.

      // Topaz A is on channel 0 (SD0 / SC0)
      retval += tca9548a_write(WHITFIELD_I2C_MUX_ADDRESS, 4);
      logger_msg_p("whitfield", log_level_DEBUG, PSTR("I2C mux to Topaz A"));
    }
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
		  TCA9539_OUTPUT_PORT_0_REG,
		  topaz_a_byte);
  } else {
    logger_msg_p("topaz", log_level_ERROR, PSTR("Topaz %c is not connected"),'a');
    retval += -1;
  }
  // Handle Topaz B hardware
  if (topaz_is_connected('b')) {
    if (strcmp( PCB, "whitfield") == 0) {
      // We're using the Whitfield board.  This has a TCA9544A I2C mux
      // in front of the Topaz connectors.

      // Topaz B is on channel 1 (SD1 / SC1)
      retval += tca9548a_write(WHITFIELD_I2C_MUX_ADDRESS, 5);
    }
    tca9539_write(TOPAZ_I2C_GPIO_ADDRESS,
		  TCA9539_OUTPUT_PORT_0_REG,
		  topaz_b_byte);

  } else {
    logger_msg_p("topaz", log_level_ERROR, PSTR("Topaz %c is not connected"),'b');
    retval += -1;
  }
  // Handle the front panel
  aloha_write(new_led_value);


  return retval;
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
  return 0;
}

void cmd_chanena( command_arg_t *command_arg_ptr ) {
  // Channel to enable
  uint16_t channel = command_arg_ptr -> uint16_arg;
  uint8_t channel_index = channel - 1;
  uint8_t channel_settings = channel_config_ptr -> enable;
  if (channel == 0 || channel > 8 ) {
    // Argument is out of range
    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
    return;
  }
  if (channel <= 4 && topaz_is_connected('a')) {
    // Enable the channel
    channel_array[channel_index].enabled = true;
    channel_update();
    command_ack();
    return;
  }
  if (channel <= 4 && !topaz_is_connected('a')) {
    // The 1-4 channel Topaz isn't connected
    logger_msg_p("topaz", log_level_ERROR, PSTR("Topaz %c is not connected"),
		 'a');
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
  if (channel <= 8 && topaz_is_connected('b')) {
    // Enable the channel
    channel_array[channel_index].enabled = true;
    channel_update();
    command_ack();
    return;
  }
  if (channel <= 8 && !topaz_is_connected('a')) {
    // The 5-8 channel Topaz isn't connected
    logger_msg_p("topaz", log_level_ERROR, PSTR("Topaz %c is not connected"),
		 'b');
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_chanena_q( command_arg_t *command_arg_ptr ) {
  // Channel to query
  uint16_t channel = command_arg_ptr -> uint16_arg;
  uint8_t channel_index = channel - 1;
  if (channel == 0 || channel > 8 ) {
    // Argument is out of range
    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
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
    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
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
    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
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
