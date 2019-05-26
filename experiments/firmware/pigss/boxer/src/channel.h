// Channel module

#ifndef CHANNEL_H
#define CHANNEL_H

// Channel configuration structure
typedef struct channel_config_struct {
  // Each channel has a position in the enable bitfield.  Set the bit
  // to enable the channel, and clear it to disable it.  Channels
  // start with 1 -- not 0.
  uint8_t enable;
} channel_config_t;

void channel_init(void);

// Set the active channelsj
//
// Arguments:
//   channel_settings -- byte with 1s in the active channel positions
uint8_t channel_write(uint8_t channel_settings);

// Update the channel hardware and display
uint8_t channel_update(void);

// Drive the active channel display hardware
uint8_t channel_display(void);

// Enable channel n
void cmd_chanena( command_arg_t *command_arg_ptr );

// Query the enable status of channel n
void cmd_chanena_q( command_arg_t *command_arg_ptr );

// Disable channel n
void cmd_chanoff( command_arg_t *command_arg_ptr );

// Set the channel enable register
void cmd_chanset( command_arg_t *command_arg_ptr );

// Query the channel enable register
void cmd_chanset_q( command_arg_t *command_arg_ptr );





#endif
