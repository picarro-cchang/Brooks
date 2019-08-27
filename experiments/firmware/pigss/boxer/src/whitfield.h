// Definitions and functions for Whitfield (90071) boards

#ifndef WHITFIELD_H
#define WHITFIELD_H

// I2C mux address
#define WHITFIELD_I2C_MUX_ADDRESS 0x70

//********************** Function prototypes ***********************//

// Set the I2C multiplexer
//
// Arguments:
//   channel -- 0-3
int8_t whitfield_set_i2c_mux(uint8_t channel);


#endif
