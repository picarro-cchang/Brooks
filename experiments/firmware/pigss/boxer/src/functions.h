
// The functions module provides miscellaneous structures and
// functions to support the system.

#ifndef FUN_H
#define FUN_H

/* command.h 

   Contains the definition of command_t -- the variable type containing
   the attributes of each remote command. */
#include "command.h"


// Overall system state structure
typedef struct system_status_struct {
  // System serial number
  uint16_t sernum;
  // System slot ID -- where the instrument is in the rack
  uint8_t slotid;
} system_state_t;

// Function called by the *idn? command
void cmd_idn_q( command_arg_t *command_arg_ptr );

// Function called by the slotid? command
void cmd_slotid_q( command_arg_t *command_arg_ptr );

// Initialize the system state structure.  This populates the
// structure with non-volatile values from eeprom.
void functions_init( void );

#endif // End the include guard
