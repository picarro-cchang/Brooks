// The LTC2607 16-bit I2C dual DAC from Analog Devices / Linear
// Technology

#ifndef LTC2607_H
#define LTC2607_H

// Set initial values
int8_t ltc2607_init(uint8_t slave_address);


// |----+----+----+----+---------+---------------------------------------------|
// | C3 | C2 | C1 | C0 | command | Action                                      |
// |----+----+----+----+---------+---------------------------------------------|
// |  0 |  0 |  0 |  0 |     0x0 | Write to input register                     |
// |  0 |  0 |  0 |  1 |     0x1 | Power up and update DAC register            |
// |  0 |  0 |  1 |  1 |     0x3 | Power up, write to, and update DAC register |
// |  0 |  1 |  0 |  0 |     0x4 | Power down                                  |
// |  1 |  1 |  1 |  1 |     0xf | No operation                                |
// |----+----+----+----+---------+---------------------------------------------|
//
// |----+----+----+----+---------+----------|
// | A3 | A2 | A1 | A0 | Address | DAC      |
// |----+----+----+----+---------+----------|
// |  0 |  0 |  0 |  0 |     0x0 | DAC A    |
// |  0 |  0 |  0 |  1 |     0x1 | DAC B    |
// |  1 |  1 |  1 |  1 |     0xf | All DACs |
// |----+----+----+----+---------+----------|
//
// For example,
// ltc2607_write( 0x72, 0x3, 0x0, 0x7fff);
// ...will update DAC A of the LTC2607 at I2C address 0x72
//
int8_t ltc2607_write( uint8_t slave_address,
		      uint8_t command,
		      uint8_t address,
		      uint16_t data );

#endif
