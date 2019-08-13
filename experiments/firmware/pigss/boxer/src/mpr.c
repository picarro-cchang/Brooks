#include <stdio.h>

// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Provides macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>

// Definitions of Two Wire Interface statuses
#include <util/twi.h>

// Definitions common to i2c devices
#include "i2c.h"

// Provides logger_msg and logger_msg_p for log messages tagged with a
// system and severity.
#include "logger.h"

// Provides spi_write()
#include "spi.h"

// Provices cs functions
#include "cs.h"

// Functions for maintaining a simple schedule
#include "OS.h"

#include "mpr.h"

int8_t mpr_init( void (*cs_ptr)(uint8_t) ) {
  // Assume spi has already been initialized
  logger_msg_p("mpr", log_level_DEBUG, PSTR("Initializing sensor"));
  return 0;
}

int8_t mpr_trigger( void (*cs_ptr)(uint8_t) ) {
  int8_t retval = 0;
  // Write 0xaa, followed by 0x0 and 0x0 to trigger the measurement
  uint8_t bytes[3] = {0xaa, 0x00, 0x00};
  uint8_t status_byte = 0;

  // Pull cs low
  (*cs_ptr)(0);

  // Write the data starting with bytes[0] (0xaa)
  for (int8_t bytenum = 0; bytenum <= 2; bytenum++) {
    if (bytenum == 0) {
      // The first 0xaa write will return the status byte
      status_byte = spi_write(bytes[bytenum]);
    } else {
      spi_write(bytes[bytenum]);
    }
  }
  if (status_byte != 0x40) {
    // The correct status byte is 0x40
    // logger_msg_p("mpr", log_level_ERROR, PSTR("MPR status is %i"),
    // 		 status_byte);
    retval += -1;
  }
  // Return cs high
  (*cs_ptr)(1);

  return retval;
}

int8_t mpr_read( void (*cs_ptr)(uint8_t), uint32_t *data_ptr ) {
  // Make a union to read data bytes one at a time
  union {
    uint8_t bytes[4];
    uint32_t word;
  } data_union;

  uint8_t status = 0;
  data_union.word = 0;

  // Pull cs low
  (*cs_ptr)(0);

  // Read the data MSB first.  The first byte returned will be status
  for (int8_t bytenum = 3; bytenum >= 0; bytenum--) {
    if (bytenum == 3) {
      // Write the NOP command first and read sensor status
      status = spi_write(0xf0);
      data_union.bytes[bytenum] = 0;
    } else {
      // The lower 3 bytes will be sensor data
      data_union.bytes[bytenum] = spi_write(0);
    }
  }
  logger_msg_p("mpr", log_level_DEBUG, PSTR("Pressure code 0x%lx"),data_union.word);
  *data_ptr = data_union.word;

  // Return cs high
  (*cs_ptr)(1);

  return 0;
}
