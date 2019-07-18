// Driver for the BarGraph click from MikroElektronika
//
// SKU: MIKROE-1423

#ifndef BARGRAPH_H
#define BARGRAPH_H

void bargraph_init(void);

// Write data to the bargraph
//
// The bargraph has 10 LEDs so, anything above 10 bits will be
// truncated.
//
// Arguments:
//   cs_ptr -- Pointer to the function that sets or clears the cs line
//   data -- 16-bit value to write
//
uint8_t bargraph_write( void (*cs_ptr)(uint8_t), uint16_t data );

#endif
