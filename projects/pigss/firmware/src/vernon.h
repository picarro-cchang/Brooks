// Definitions and functions for Vernon (90072) boards

#ifndef VERNON_H
#define VERNON_H

// Definitions and functions needed for TCA9539 I2C GPIO module
#include "tca9539.h"

#define VERNON_I2C_MUX_ADDRESS 0x73

#define VERNON_I2C_GPIO_ADDRESS 0x74

#define VERNON_I2C_TSENSOR_ADDRESS 0x48

// Valve bitshifts in the GPIO register
#define VERNON_CLEAN_SOLENOID_SHIFT 0
#define VERNON_SPARE_SOLENOID_SHIFT 1
#define VERNON_GPIO1_SHIFT 2
#define VERNON_GPIO2_SHIFT 3
#define VERNON_GPIO3_SHIFT 4
#define VERNON_GPIO4_SHIFT 5

//********************** Function prototypes ***********************//

// Set up Vernon
int8_t vernon_init(void);

// Connect to the Vernon board.  This will return -1 if the connection
// fails.
int8_t vernon_connect(void);

// Return the serial number for a Vernon board
//
// Rev A Vernon boards can't store a serial number, so this will just
// return 1 for a successful connection.  This is for consistency with
// Topaz boards.
uint16_t vernon_get_serial_number(void);

// Check for Vernon connection without the i2c timeout penalty
bool vernon_is_connected(void);

// Open or close the clean solenoid
//
// 1 energizes (opens) the clean solenoid
// 0 de-energizes (closes) the clean solenoid
int8_t vernon_set_clean_solenoid(uint8_t setting);

// Command to get the temperature on Vernon
//
// This will return a positive temperature in C with 1C resolution.
void cmd_vernon_temperature_q( command_arg_t *command_arg_ptr );


#endif
