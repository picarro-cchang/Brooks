// Definitions and functions for Topaz (90069) boards

#ifndef TOPAZ_H
#define TOPAZ_H

// Rev A Topaz boards ship with an I2C mux address of 0x70.  This can
// be switched to 0x71 by swapping two resistors.
#define TOPAZ_I2C_MUX_ADDRESS 0x70

// Non-volatile memory I2C address
#define TOPAZ_I2C_NVM_ADDRESS 0x50

//************************ Memory locations ************************//
// Topaz boards have a 32K x 8 non-volatile memory array.

// Serial numbers are 16 bits.  We need to specify the location of the
// lower byte.  The next open address will be this + 2
#define TOPAZ_SERNUM_ADDR 0u


// Return the serial number from a Topaz board
//
// Arguments:
//   board -- Either a or b
uint16_t topaz_get_serial_number(char board);

// Set the serial number 
int8_t topaz_set_serial_number(char board, uint16_t serial_number);

// Command to set the serial number for Topaz A
void cmd_topaz_a_set_serial_number( command_arg_t *command_arg_ptr);

// Command to get the serial number for Topaz A
void cmd_topaz_a_get_serial_number( command_arg_t *command_arg_ptr);

// Command to set the serial number for Topaz B
void cmd_topaz_b_set_serial_number( command_arg_t *command_arg_ptr);

// Command to get the serial number for Topaz B
void cmd_topaz_b_get_serial_number( command_arg_t *command_arg_ptr);

// Set the I2C mux(s) to talk to Topaz A
int8_t topaz_a_connect(void);


#endif
