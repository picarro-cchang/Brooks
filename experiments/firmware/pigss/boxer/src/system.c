// Miscellaneous system functions

// ----------------------- Include files ------------------------------
#include <stdio.h>
#include <string.h>

// Contains macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>

// Watchdog timer
#include <avr/wdt.h>

#include "usart.h"

// Sets up logging
#include "logger.h"

// Provides commands for working with the eeprom
#include "eeprom.h"

// Provides commands for handling SPI chip selects
#include "cs.h"

// Provides commands for writing to SPI
#include "spi.h"

// Provides definitions and functions for using the Topaz manifold boards
#include "topaz.h"

// Provides channel_set() for turning channels on and off
#include "channel.h"

#include "system.h"

// ----------------------- Globals ------------------------------------

// idnstr format: Organization, model, serial, version
const char idnstr[] PROGMEM = "Picarro,Boxer,SN%u,%s";

/* System status structure

   Keeps track of miscellaneous system status:
   -- Serial number
*/
system_state_t system_state;
system_state_t *system_state_ptr = &system_state;

// ----------------------- Functions ----------------------------------

void system_init( void ) {
  uint16_t sernum = 0;
  eeprom_load_sernum(system_state_ptr);
  eeprom_load_slotid(system_state_ptr);

  // The system status structure needs to know about what's connected.
  // We can only talk to Topaz boards if they have a serial number, so
  // try to get that.
  sernum = topaz_get_serial_number('a');
  logger_msg_p("system",log_level_INFO,PSTR("Topaz A serial number is %i"),
	       sernum);
}

void cmd_idn_q( command_arg_t *command_arg_ptr ) {
  usart_printf_p(USART_CHANNEL_COMMAND, idnstr, system_state_ptr -> sernum,REVCODE);
  usart_printf(USART_CHANNEL_COMMAND, LINE_TERMINATION_CHARACTERS);
}

system_state_value_t set_system_state(system_state_value_t requested_state) {
  // For now, just set the state to the requested value
  system_state_ptr -> state_enum = requested_state;
  return(system_state_ptr -> state_enum);
}

system_state_value_t get_system_state( void ) {
  // Return the current system state
  return(system_state_ptr -> state_enum);
}

int8_t system_enter_standby(void) {
  switch( system_state.state_enum ) {
  case system_state_INIT:
    // Transition from INIT to STANDBY
    //
    // All channels --> OFF
    channel_set(0);
    // Clean solenoid --> OFF
    logger_msg_p("system",log_level_INFO,PSTR("State change INIT to STANDBY"));
    set_system_state(system_state_STANDBY);

    break;
  case system_state_STANDBY:
    break;
  default:
    break;
  }
  return 0;
}

void cmd_rst( command_arg_t *command_arg_ptr ) {
  // Set watchdog to lowest interval and delay longer than that
  wdt_enable(WDTO_15MS);
  while(1);
}

void cmd_opstate_q( command_arg_t *command_arg_ptr ) {
  switch( system_state_ptr -> state_enum ) {
  case system_state_INIT:
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "init",
		 LINE_TERMINATION_CHARACTERS );
    break;
  case system_state_STANDBY:
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "standby",
		 LINE_TERMINATION_CHARACTERS );
    break;
  default:
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "none",
		 LINE_TERMINATION_CHARACTERS );
  }

}

void cmd_slotid_q( command_arg_t *command_arg_ptr ) {
  usart_printf(USART_CHANNEL_COMMAND, "%u%s",
	       system_state_ptr -> slotid,
	       LINE_TERMINATION_CHARACTERS);
}

int8_t system_state_set_topaz_sernum(char board, uint16_t sernum) {
  if (board == 'a') {
    system_state.topaz_a_sernum = sernum;
  } else {
    system_state.topaz_b_sernum = sernum;
  }
  return 0;
}

int8_t system_state_set_system_sernum(uint16_t sernum) {
  system_state.sernum = sernum;
  return 0;
}

int8_t system_state_set_system_slotid( uint8_t slotid ) {
  system_state.slotid = slotid;
  return 0;
}

uint16_t system_state_get_topaz_sernum(char board ) {
  if (board == 'a') {
    return system_state.topaz_a_sernum;
  } else {
    return system_state.topaz_b_sernum;
  }

}

