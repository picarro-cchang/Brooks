// Miscellaneous system functions




// ----------------------- Include files ------------------------------
#include <stdio.h>
#include <string.h>

/* pgmspace.h
 * Contains macros and functions for saving and reading data out of
 * flash.
 */
#include <avr/pgmspace.h>
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


/* functions_init()

   Calls cal_load_sernum(pointer to system status structure) to fill
   in the serial number.
*/
void functions_init(void) {
  eeprom_load_sernum(system_state_ptr);
}

// The function called by the "*IDN?" query
void cmd_idn_q( command_arg_t *command_arg_ptr ) {
  usart_printf_p(USART_CHANNEL_COMMAND, idnstr, system_state_ptr -> sernum,REVCODE);
  usart_printf(USART_CHANNEL_COMMAND, LINE_TERMINATION_CHARACTERS);
}



