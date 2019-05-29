
// The functions module provides miscellaneous structures and
// functions to support the system.

#ifndef FUN_H
#define FUN_H

// Provides the definition of command_t -- the variable type
// containing the attributes of each remote command.
#include "command.h"

// System states
typedef enum system_state_enum {
				system_state_INIT,
				system_state_ID_CHANNELS,
				system_state_CONTROLLING
} system_state_value_t;

// Overall system state structure
typedef struct system_status_struct {
  // System serial number
  uint16_t sernum;
  // System slot ID -- where the instrument is in the rack
  uint8_t slotid;
  // System state -- one of an enumerated type
  system_state_value_t state_enum;
} system_state_t;

// The system state structure variable will have global scope, and
// will be defined in functions.c
extern system_state_t *system_state_ptr;

// Function called by the *idn? command
void cmd_idn_q( command_arg_t *command_arg_ptr );

// Function called by the slotid? command
void cmd_slotid_q( command_arg_t *command_arg_ptr );

// Initialize the system state structure.  This populates the
// structure with non-volatile values from eeprom.
void functions_init( void );

#endif // End the include guard
