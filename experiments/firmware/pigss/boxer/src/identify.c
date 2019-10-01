#include <stdio.h>

// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Provides macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>

// Convenience functions for busy-wait loops
#include <util/delay.h>

// Functions for working with UART interfaces.
// Definition of LINE_TERMINATION_CHARACTERS
#include "usart.h"

// Provides logger_msg and logger_msg_p for log messages tagged with a
// system and severity.
#include "logger.h"

// Provides setter and getter functions for the system state structure
#include "system.h"

#include "identify.h"

identify_state_t identify_state = { .mfc_value = 0.0 };

int8_t identify_state_set_mfc_value(float mfc_value) {
  identify_state.mfc_value = mfc_value;
  return 0;
}

float identify_state_get_mfc_value(void) {
  return identify_state.mfc_value;
}

void cmd_mfcval_q( command_arg_t *command_arg_ptr ) {
  usart_printf( USART_CHANNEL_COMMAND, "%0.1f%s", (float) identify_state.mfc_value,
		LINE_TERMINATION_CHARACTERS );
}
