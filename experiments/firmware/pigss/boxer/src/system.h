
// The functions module provides miscellaneous structures and
// functions to support the system.

#ifndef SYSTEM_H
#define SYSTEM_H

// Provides the definition of command_t -- the variable type
// containing the attributes of each remote command.
#include "command.h"

// System states
typedef enum system_state_enum {
				system_state_STANDBY,
				system_state_INIT,
				system_state_ID_CHANNELS,
				system_state_CONTROL
} system_state_value_t;

// Overall system state structure
typedef struct system_status_struct {
  // System serial number
  uint16_t sernum;
  // System slot ID -- where the instrument is in the rack
  uint8_t slotid;
  // System state -- one of an enumerated type
  system_state_value_t state_enum;
  // Topaz A serial number (0 if board not connected)
  uint16_t topaz_a_sernum;
  // Topaz B serial number (0 if board not connected)
  uint16_t topaz_b_sernum;
} system_state_t;

// The system state structure variable will have global scope, and
// will be defined in functions.c
extern system_state_t *system_state_ptr;

//********************** Function prototypes ***********************//

// Try to set the system state.  Return the actual system state, which
// may not be what you asked for.
system_state_value_t set_system_state(system_state_value_t requested_state);

// Function called by the *idn? command
void cmd_idn_q( command_arg_t *command_arg_ptr );

// Function called by the *rst command
void cmd_rst( command_arg_t *command_arg_ptr );

// Function called by the opstate? command
void cmd_opstate_q( command_arg_t *command_arg_ptr );

// Function called by the slotid? command
void cmd_slotid_q( command_arg_t *command_arg_ptr );

// Function called by the standby command
void cmd_standby( command_arg_t *command_arg_ptr );

// Initialize the system state structure.  This populates the
// structure with non-volatile values from eeprom.
void system_init( void );

//******* Set and get members of the system_state structure ********//

// Set the topaz a serial number in the system state structure
int8_t system_state_set_topaz_sernum(char board, uint16_t sernum);

// Set the system slotid in the system state structure
int8_t system_state_set_system_slotid(uint8_t slotid);

// Get the Topaz serial number in the system state struction
uint16_t system_state_get_topaz_sernum(char board);

// Set the system-level serial number
int8_t system_state_set_system_sernum(uint16_t sernum);

// Enter standby mode
int8_t system_enter_standby(void);

// Enter control mode
int8_t system_enter_control(void);

#endif // End the include guard
