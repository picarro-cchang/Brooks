#ifndef LTC2601_H
#define LTC2601_H

void ltc2601_init(void);

// Write data to the DAC
//
// Arguments:
//   cs_ptr -- Pointer to the function that sets or clears the cs line
//   command -- DAC command (see table below)
//   data -- 16-bit value to write
//
// |----+----+----+----+---------+---------------------------------------------|
// | C3 | C2 | C1 | C0 | command | Action                                      |
// |----+----+----+----+---------+---------------------------------------------|
// |  0 |  0 |  0 |  0 |     0x0 | Write to input register                     |
// |  0 |  0 |  0 |  1 |     0x1 | Power up and update DAC register            |
// |  0 |  0 |  1 |  1 |     0x3 | Power up, write to, and update DAC register |
// |  0 |  1 |  0 |  0 |     0x4 | Power down                                  |
// |  1 |  1 |  1 |  1 |     0xf | No operation                                |
// |----+----+----+----+---------+---------------------------------------------|
uint8_t ltc2601_write( void (*cs_ptr)(uint8_t), uint8_t command, uint16_t data );

// Calling this function over and over again will produce a voltage ramp
uint8_t ltc2601_ramp_test(void);

#endif
