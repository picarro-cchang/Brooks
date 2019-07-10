// The MB85RC256V 32K x 8 FRAM IC with I2C interface

#ifndef MB85RC256V_H
#define MB85RC256V_H

// Write to a memory location.
//
// Arguments:
//   slave_address -- The I2C address
//   register_address -- The internal register address
//   data -- Data to store
//
// Addresses 0x0000 to 0x7fff are available
//
// Example:
//   mb85rc256v_write(0x50, 0x00, 0xbe);
//   ...writes 0xbe to register address 0 of I2C slave 0x50
int8_t mb85rc256v_write(uint8_t slave_address, uint16_t register_address, uint8_t data);

// Return a byte from a memory location
//
// Arguments:
//   slave_address -- The I2C address
//   register_address -- The internal register address
//
// Example:
//   uint8_t retval = mb85rc256v_read(0x50, 0x00);
//   ...reads register address 0 of I2C slave 0x50
uint8_t mb85rc256v_read(uint8_t slave_address, uint16_t register_address);

#endif
