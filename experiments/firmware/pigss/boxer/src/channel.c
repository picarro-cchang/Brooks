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


#include "spi.h"

#include "bargraph.h"

#include "channel.h"

// Define a pointer to the channel configuration
channel_config_t channel_config;
channel_config_t *channel_config_ptr = &channel_config;


void channel_init() {
  // Disable all channels
  channel_config_ptr -> enable = 0;
  channel_update;
}

uint8_t channel_write(uint8_t channel_settings) {
  uint8_t retval = 0;
  channel_config_ptr -> enable = channel_settings;
  logger_msg_p("channel", log_level_DEBUG, PSTR("Channel enable byte is %d"),
	       channel_config_ptr -> enable);
  // Write to channel hardware goes here

  retval = channel_update();
  retval = channel_display();
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

