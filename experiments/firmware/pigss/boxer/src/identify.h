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
} identify_state_t;

// Command to return the proper sample flow controller value
void cmd_mfcval_q( command_arg_t *command_arg_ptr );


//****** Set and get members of the identify state structure *******//

int8_t identify_state_set_mfc_value(float mfc_value);

float identify_state_get_mfc_value(void);

#endif // End the include guard
