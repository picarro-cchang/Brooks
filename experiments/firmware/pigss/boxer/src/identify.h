// The identify module provides structures and functions to support
// channel identification

#ifndef IDENTIFY_H
#define IDENTIFY_H

// Identify states
//
// Identify states are sub-states inside the system_state_IDENTIFY
// state.
typedef enum identify_state_enum {
				  identify_state_AMBIENT,
				  identify_state_CALCULATE
} identify_state_enum_t;

typedef struct identify_state_struct {
  identify_state_enum_t state_enum;
  float mfc_value;
  // Active channels will be set in the active channel byte
  uint8_t active_channel_byte;
  // Exit identify task number
  uint8_t exit_identify_task_number;
} identify_state_t;

// Initialize the module
int8_t identify_init(void);

// Do whatever we need to do to figure out which channels are active
int8_t identify_find_active_channels(void);

// Exit identify mode
void identify_exit_task(void);

// Command to return the proper sample flow controller value
void cmd_mfcval_q( command_arg_t *command_arg_ptr );

// Command to return the identify substate
void cmd_idstate_q( command_arg_t *command_arg_ptr );

// Command to return the active channel byte
void cmd_activech_q( command_arg_t *command_arg_ptr );

//****** Set and get members of the identify state structure *******//

int8_t identify_state_set_mfc_value(float mfc_value);

float identify_state_get_mfc_value(void);

int8_t identify_state_set_state_enum(identify_state_enum_t state);

identify_state_enum_t identify_state_get_state_enum(void);

#endif // End the include guard
