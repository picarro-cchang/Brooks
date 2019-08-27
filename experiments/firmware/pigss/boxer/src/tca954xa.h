// The TCA954xA series of I2C multiplexers from Texas Instruments

#ifndef TCA954xA_H
#define TCA954xA_H

// All parts in this series communicate the same way -- with one
// control register.  The tca9548_set_channel() function can work with
// all parts.

// It looks like TCA parts are lower-voltage versions of PCA parts.

// |----------+--------+----------+----------------------------|
// | Part     | Reset? | channels | comment                    |
// |----------+--------+----------+----------------------------|
// | TCA9543A | Yes    |        2 | 1 or both channels at once |
// | TCA9544A | No     |        4 | 1 channel at a time        |
// | TCA9548A | Yes    |        8 | 1 or more channels at once |
// |----------+--------+----------+----------------------------|


// TCA9544A channel settings
//
// |---------+--------------|
// | Channel | Control byte |
// |---------+--------------|
// |       0 |            4 |
// |       1 |            5 |
// |       2 |            6 |
// |       3 |            7 |
// |---------+--------------|

#define TCA9548A_I2C_ADDRESS 0x74

// Set initial values
int8_t tca9548a_init(uint8_t slave_address);

// There is a 1-byte control register controlling which channels are
// active.  Active channels have a 1 in their bit position.  There may
// be more than 1 active channel.

// Write to the device.  Since there's only 1 internal register,
// there's no internal register address.
int8_t tca9548a_write(uint8_t slave_address, uint8_t command_byte);

// Reading from a register will return the command byte
int16_t tca9548a_read(uint8_t slave_address);

// Set an active channel
//
// There can be more than one I2C switch, so we need to know which one
// we're talking to.  That's the slave_address.  Channel can be 0-7.
int8_t tca9548_set_channel(uint8_t slave_address, uint8_t channel);

#endif
