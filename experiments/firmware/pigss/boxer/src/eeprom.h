
#ifndef EEPROM_H
#define EEPROM_H

// Provides definition of system_state_t
#include "functions.h"

// Define the offset for general system variables. The eeprom has 512
// total locations.  I'll allocate addresses 0-99 for general system
// storage.

// The serial number is two bytes wide -- occupying addresses 0 and 1.
// The next open address is 2.
#define SERNUM_ADDR 0

// Write an 8-bit value to an eeprom address
void eeprom_write_char( uint16_t address, uint8_t data );

// Return an 8-bit unsigned integer from an eeprom address
uint8_t eeprom_read_char( uint16_t address );

// Write the serial number
void eeprom_save_sernum( uint16_t );

// Load the serial number into the system state structure
void eeprom_load_sernum( system_state_t *system_state_ptr );

// Remote command to set the instrument's serial number
void cmd_write_sernum( command_arg_t *command_arg_ptr );



#endif // End the include guard
