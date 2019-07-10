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

#include "ltc2607.h"

int8_t ltc2607_init(uint8_t slave_address) {
  return 0;
}

// Saved TWI status register, for error messages only.  We need to
// save it in a variable, since the datasheet only guarantees the TWSR
// register to have valid contents while the TWINT bit in TWCR is set.
uint8_t twst;

int8_t ltc2607_write( uint8_t slave_address,
		      uint8_t command,
		      uint8_t address,
		      uint16_t data ) {
  int16_t retval = 0;
  // Keep track of the number of times we've tried to write
  uint8_t tries = 0;
  // Slave address + R/W bit
  uint8_t sla = slave_address << 1;

  union {
    uint8_t b[2];
    uint16_t w;
  } data_union;
  data_union.w = data;

  // Configure instruction byte
  uint8_t instruction = (uint8_t)((command << 4) + address);

  restart:
  if (tries++ >= MAX_I2C_TRIES)
    return -1;
 begin:
  // Send start condition
  TWCR = _BV(TWINT) | _BV(TWSTA) | _BV(TWEN);
  // Wait for start condition to finish
  while ((TWCR & _BV(TWINT)) == 0) ;

  switch ((twst = TW_STATUS)) {
  case TW_REP_START:
  case TW_START:
    // Start condition transmitted
    logger_msg_p("ltc2607",log_level_DEBUG,PSTR("Start condition set"));
    break;
  case TW_MT_ARB_LOST:
    logger_msg_p("ltc2607",log_level_DEBUG,PSTR("Arbitration lost"));
    goto begin;

  default:
    logger_msg_p("ltc2607",log_level_ERROR,PSTR("Could not set start condition"));
    return -1;
  }

  //********************** Send control byte ***********************//
  TWDR = sla | TW_WRITE;
  // Clear interrupt to start transmission
  TWCR = _BV(TWINT) | _BV(TWEN);
  // Wait for start condition to finish
  while ((TWCR & _BV(TWINT)) == 0);
  twst = TW_STATUS;
  logger_msg_p("ltc2607", log_level_DEBUG, PSTR("TWI status is 0x%x"),twst);
  switch (twst) {
  case TW_MT_SLA_ACK:
    logger_msg_p("ltc2607", log_level_DEBUG, PSTR("SLA+W transmitted, ACK received"));
    break;

  case TW_MT_SLA_NACK:
    logger_msg_p("ltc2607", log_level_DEBUG,
		 PSTR("SLA+W transmitted, NACK received after %u tries"), tries);
    goto restart;

  case TW_MT_ARB_LOST:	/* re-arbitrate */
    logger_msg_p("ltc2607",log_level_DEBUG,PSTR("Arbitration lost"));
    goto begin;

  default:
    logger_msg_p("ltc2607",log_level_ERROR,PSTR("Could not select device"));
    goto error;		/* must send stop condition */
  }

  //************ Send slave internal address (command) *************//
  TWDR = instruction;
  // Clear interrupt to start transmission
  TWCR = _BV(TWINT) | _BV(TWEN);
  // Wait for transmission to finish
  while ((TWCR & _BV(TWINT)) == 0);

  twst = TW_STATUS;
  logger_msg_p("ltc2607", log_level_DEBUG, PSTR("TWI status is 0x%x"),twst);
  switch (twst) {
    case TW_MT_DATA_ACK:
      logger_msg_p("ltc2607", log_level_DEBUG, PSTR("Slave ACKed instruction 0x%x"),
		   instruction);
      // Data transmitted, ACK received
      break;

    case TW_MT_DATA_NACK:
      // Data transmitted, NACK received
      goto quit;

    case TW_MT_ARB_LOST:
      goto begin;

    default:
      goto error;		/* must send stop condition */
  }

  //*********************** Write data bytes ***********************//

  for (int8_t bytenum = 1; bytenum >= 0; bytenum--) {
    TWDR = data_union.b[bytenum];
    // Clear interrupt to start transmission
    TWCR = _BV(TWINT) | _BV(TWEN);
    // Wait for transmission to finish
    while ((TWCR & _BV(TWINT)) == 0);

    twst = TW_STATUS;
    logger_msg_p("ltc2607", log_level_DEBUG, PSTR("TWI status is 0x%x"),twst);
    switch (twst) {
    case TW_MT_DATA_ACK:
      logger_msg_p("ltc2607", log_level_DEBUG, PSTR("Slave ACKed data byte %u."),
		   bytenum);
      logger_msg_p("ltc2607", log_level_DEBUG, PSTR("Wrote 0x%x"),
		   data_union.b[bytenum]);
      // Data transmitted, ACK received
      break;

    case TW_MT_DATA_NACK:
      // Data transmitted, NACK received
      goto quit;

    case TW_MT_ARB_LOST:
      goto begin;

    default:
      goto error;		/* must send stop condition */
    }
  }

   quit:
  // Send stop condition
  TWCR = _BV(TWINT) | _BV(TWSTO) | _BV(TWEN);
  return retval;

 error:
  retval = -1;
  goto quit;

}
