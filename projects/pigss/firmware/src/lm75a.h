// The LM75A is a standard temperature sensor
//
// As far as I can tell, this can also be used for LM75B and LM75C

#ifndef LM75A_H
#define LM75A_H

#define LM75A_TEMPERATURE_REG 0x00
#define LM75A_CONFIG_REG 0x01
#define LM75A_THYST_REG 0x02
#define LM75A_TOS_REG 0x03

int8_t lm75a_write(uint8_t slave_address, uint8_t register_address, uint8_t data);

// Reading from a register will return 2 bytes
uint16_t lm75a_read(uint8_t slave_address, uint8_t register_address);

// Stripped-down temperature measurement -- 1C resolution and only
// positive.  Returns unsigned integer temperature in C.
uint8_t lm75a_get_temperature(uint8_t slave_address);

#endif
