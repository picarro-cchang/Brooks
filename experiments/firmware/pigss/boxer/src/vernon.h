// Definitions and functions for Vernon (90072) boards

#ifndef VERNON_H
#define VERNON_H

#define VERNON_I2C_MUX_ADDRESS 0x73

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


#endif
