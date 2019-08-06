// Channel module

#ifndef CHANNEL_H
#define CHANNEL_H

#include <stdbool.h>

// Channel data structure
typedef struct channel_struct {
  // We'll have channels with numbers 1-8
  uint8_t number;
  // Enabled channels are enabled for flowing sample gas
  bool enabled;
} channel_t;

// Channel configuration structure
typedef struct channel_config_struct {
  // Each channel has a position in the enable bitfield.  Set the bit
  // to enable the channel, and clear it to disable it.  Channels
  // start with 1 -- not 0.
  uint8_t enable;

  // The clean channel should only be open when all the sample valves
  // are disabled.
  bool clean_open;
} channel_config_t;

//********************** Function prototypes ***********************//

void channel_init(void);

// Set the channel configuration
//
// Bits that are set indicate enabled channels.  For example, 0x1 will
// enable channel 1 and disable everything else.
int8_t channel_set( uint8_t setting );

// Update the channel hardware and display
int8_t channel_update(void);

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
