// The TCA9539 16-bit I2C I/O expander from Texas Instruments

#ifndef TCA9539_H
#define TCA9539_H

// I2C address.
#define TCA9539_I2C_ADDRESS 0x77

// Set initial values
int8_t tca9539_init(uint8_t slave_address);

// All registers are 1 byte wide
//
// |----------------------------+--------------------+-----------------------|
// | Command (register address) | Register           | Notes                 |
// |----------------------------+--------------------+-----------------------|
// |                       0x00 | Input port 0       | Read this register    |
// |                       0x01 | Input port 1       | Read this register    |
// |                       0x02 | Output port 0      | Read/write            |
// |                       0x03 | Output port        | Read/write            |
// |                       0x04 | Polarity inversion |                       |
// |                       0x05 | Polarity inversion |                       |
// |                       0x06 | Configure port 0   | 1 = input, 0 = output |
// |                       0x07 | Configure port 1   | 1 = input, 0 = output |
// |----------------------------+--------------------+-----------------------|
int8_t tca9539_write(uint8_t slave_address, uint8_t register_address, uint8_t data);

// Reading from a register will return 1 byte
uint8_t tca9539_read(uint8_t slave_address, uint8_t register_address);

#endif
