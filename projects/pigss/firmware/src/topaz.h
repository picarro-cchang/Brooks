// Definitions and functions for Topaz (90069) boards

#ifndef TOPAZ_H
#define TOPAZ_H

// Definitions and functions needed for TCA9539 I2C GPIO module
#include "tca9539.h"

// 32K x 8 I2C FRAM module
#include "mb85rc256v.h"

// Rev A Topaz boards ship with an I2C mux address of 0x70.  This can
// be switched to 0x71 by swapping two resistors.
#define TOPAZ_I2C_MUX_ADDRESS 0x71

// Non-volatile memory I2C address
#define TOPAZ_I2C_NVM_ADDRESS 0x50

// GPIO expander I2C address
#define TOPAZ_I2C_GPIO_ADDRESS 0x74

// Temperature sensor I2C address
#define TOPAZ_I2C_TSENSOR_ADDRESS 0x48

// Valve bitshifts in the GPIO register
#define TOPAZ_SOLENOID_1_SHIFT 0
#define TOPAZ_SOLENOID_2_SHIFT 1
#define TOPAZ_SOLENOID_3_SHIFT 2
#define TOPAZ_SOLENOID_4_SHIFT 3

// CLR (reset) line bitshift.  This is in the second output port.
#define TOPAZ_CLR_SHIFT 7

//************************ Memory locations ************************//
// Topaz boards have a 32K x 8 non-volatile memory array.

// Serial numbers are 16 bits.  We need to specify the location of the
// lower byte.  The next open address will be this + 2
#define TOPAZ_SERNUM_ADDR 0u

//******************* Proportional valve scaling *******************//

// Scaling for proportional valve drive (counts / mA)
#define TOPAZ_COUNTS_PER_MA 290u

//********************** Function prototypes ***********************//

// Connect to the Topaz board.  This will return -1 if the connection
// fails.
int8_t topaz_connect(char board);

// Set up GPIO on the Topaz boards
int8_t topaz_init(void);

// Toggle the reset line on the Topaz board
int8_t topaz_reset(char board);

// Return the serial number from a Topaz board
//
// Arguments:
//   board -- Either a or b
//
// This is the only way to change the connected state of Topaz boards.
uint16_t topaz_get_serial_number(char board);

// Set the serial number 
int8_t topaz_set_serial_number(char board, uint16_t serial_number);

// Get the temperature
//
// Arguments:
//   board -- Either a or b
//
// The LM75B on the Topaz board will output -55C to +125C with 1C
// resolution.  We'll simply use the range 0 to 125.
int8_t topaz_get_temperature(char board);

// Command to set the serial number for Topaz A
void cmd_topaz_a_set_serial_number( command_arg_t *command_arg_ptr);

// Command to get the serial number for Topaz A
void cmd_topaz_a_get_serial_number( command_arg_t *command_arg_ptr);

// Command to set the serial number for Topaz B
void cmd_topaz_b_set_serial_number( command_arg_t *command_arg_ptr);

// Command to get the serial number for Topaz B
void cmd_topaz_b_get_serial_number( command_arg_t *command_arg_ptr);

// Command to get the temperature on Topaz A
//
// Temperature will be a positive integer indicating temperature in C
void cmd_topaz_a_temperature_q( command_arg_t *command_arg_ptr );

// Command to get the temperature on Topaz B
//
// Temperature will be a positive integer indicating temperature in C
void cmd_topaz_b_temperature_q( command_arg_t *command_arg_ptr );

// Command to reset Topaz A
void cmd_topaz_a_reset( command_arg_t *command_arg_ptr );

// Command to reset Topaz B
void cmd_topaz_b_reset( command_arg_t *command_arg_ptr );

// Set the I2C mux(s) to talk to Topaz A
int8_t topaz_a_connect(void);

// Check for Topaz connection without the i2c timeout penalty
bool topaz_is_connected(char board);


#endif
