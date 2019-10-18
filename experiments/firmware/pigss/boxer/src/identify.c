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

// Functions for simple scheduling
#include "OS.h"

// Functions for working with UART interfaces.
// Definition of LINE_TERMINATION_CHARACTERS
#include "usart.h"

// Provides logger_msg and logger_msg_p for log messages tagged with a
// system and severity.
#include "logger.h"

// Provides setter and getter functions for the system state structure
#include "system.h"

// Functions for working with channel solenoids
#include "channel.h"

#include "identify.h"

identify_state_t identify_state;

int8_t identify_init(void) {
  int8_t retval = 0;
  identify_state.mfc_value = 0.0;
  identify_state.active_channel_byte = 0;

  // Exit identify state task
  OS_TaskCreate(&identify_exit_task, 5000, SUSPENDED);
  
  int8_t state_number = OS_get_task_number(&identify_exit_task);
  if (state_number >= 0) {
    identify_state.exit_identify_task_number = (uint8_t) state_number;
    logger_msg_p("identify", log_level_DEBUG, PSTR("Exit task id is %i"),
	       identify_state.exit_identify_task_number);
  } else {
    logger_msg_p("identify", log_level_ERROR, PSTR("Exit task id not found"));
    retval += -1;
  }
  return retval;
}

int8_t identify_find_active_channels(void) {
  // Enable all channels while we figure things out
  channel_set(255);

  // For now, we'll just say all channels are active
  identify_state.active_channel_byte = 255;

  // Schedule the transition back to standby
  OS_SetTaskState(identify_state.exit_identify_task_number, BLOCKED);
}

void identify_exit_task(void) {
  // Cancel the exit task
  OS_SetTaskState(identify_state.exit_identify_task_number, SUSPENDED);
  // Simply go back to standby
  system_enter_standby();
}

int8_t identify_state_set_mfc_value(float mfc_value) {
  identify_state.mfc_value = mfc_value;
  return 0;
}

float identify_state_get_mfc_value(void) {
  return identify_state.mfc_value;
}

int8_t identify_state_set_state_enum(identify_state_enum_t state) {
  identify_state.state_enum = state;
  return 0;
}

identify_state_enum_t identify_state_get_state_enum(void) {
  return identify_state.state_enum;
}

void cmd_mfcval_q( command_arg_t *command_arg_ptr ) {
  usart_printf( USART_CHANNEL_COMMAND, "%0.1f%s", (float) identify_state.mfc_value,
		LINE_TERMINATION_CHARACTERS );
}

void cmd_activech_q( command_arg_t *command_arg_ptr ) {
  usart_printf( USART_CHANNEL_COMMAND, "%i%s",
		identify_state.active_channel_byte,
		LINE_TERMINATION_CHARACTERS );
}

void cmd_idstate_q( command_arg_t *command_arg_ptr ) {
  switch( system_state_get_system_state() ) {
  case system_state_IDENTIFY:
    switch( identify_state.state_enum ) {
    case identify_state_AMBIENT:
      usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		   "ambient",
		   LINE_TERMINATION_CHARACTERS );
      break;
    case identify_state_CALCULATE:
      usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		   "calculate",
		   LINE_TERMINATION_CHARACTERS );
      break;
    default:
      break;
    }
    break;

  default:
    // If we aren't in identify, we can't be in an identify state.  We
    // should return "none."
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "none",
		 LINE_TERMINATION_CHARACTERS );
  }
}
