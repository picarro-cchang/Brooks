// The MPR series of piezoresistive pressure sensors from Honeywell
//
// This driver uses the SPI interface

#ifndef MPR_H
#define MPR_H

// Calibration values for MPR sensors
#define MPR_NMIN 0x19999aul
#define MPR_NMAX 0xe66666ul
#define MPR_PMAX_PASCAL 103421

// Set initial values
//
// Chip-select functions take a 1 or a 0 argument to set the
// chip-select line high or low.
int8_t mpr_init( void (*cs_ptr)(uint8_t) );

// Trigger the pressure reading
//
// We need to wait 5ms after the trigger to read the result.
int8_t mpr_trigger( void (*cs_ptr)(uint8_t) );

// Read the 24-bit pressure output
int8_t mpr_read( void (*cs_ptr)(uint8_t), uint32_t *data );

#endif
