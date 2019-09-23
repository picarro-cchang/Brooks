#ifndef SPI_H
#define SPI_H

void spi_init( void );

// Write a byte to the SPI.  Returns the byte received when the byte
// is written.
//
// SS/CS must be handled elsewhere
uint8_t spi_write( uint8_t data );

#endif
