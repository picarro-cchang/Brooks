// Miscellaneous system functions

// ----------------------- Include files ------------------------------
#include <stdio.h>
#include <string.h>

/* pgmspace.h
 * Contains macros and functions for saving and reading data out of
 * flash.
 */
#include <avr/pgmspace.h>

// Watchdog timer
#include <avr/wdt.h>

#include "usart.h"


/* logger.h 

   Sets up logging 
*/
#include "logger.h"

// Provides commands for working with the eeprom
#include "eeprom.h"

// Provides commands for handling SPI chip selects
#include "cs.h"

// Provides commands for writing to SPI
#include "spi.h"

// Provides definitions and functions for using the Topaz manifold boards
#include "topaz.h"

#include "functions.h"


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


void functions_init( void ) {
  uint16_t sernum;
  eeprom_load_sernum(system_state_ptr);
  eeprom_load_slotid(system_state_ptr);
  sernum = topaz_get_serial_number('a');
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

uint16_t system_state_get_topaz_sernum(char board ) {
  if (board == 'a') {
    return system_state.topaz_a_sernum;    
  } else {
    return system_state.topaz_b_sernum;    
  }

}







