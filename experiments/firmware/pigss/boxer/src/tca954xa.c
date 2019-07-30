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

#include "tca954xa.h"

int8_t tca9548a_init(uint8_t slave_address) {
  // De-select all i2c channels
  tca9548a_write(slave_address, 0);


  // Read the value in the control register
  uint8_t retval = tca9548a_read(TCA9548A_I2C_ADDRESS);
  logger_msg_p("tca954xa", log_level_DEBUG, PSTR("Control register contains 0x%x"),
	       retval);
  return 0;
}

int8_t tca9548a_set_channel(uint8_t slave_address, uint8_t channel) {
  int8_t retval = 0;
  uint8_t control_byte = 1 << channel;
  retval = tca9548a_write(slave_address, control_byte);
  return retval;
}

// Saved TWI status register, for error messages only.  We need to
// save it in a variable, since the datasheet only guarantees the TWSR
// register to have valid contents while the TWINT bit in TWCR is set.
uint8_t twst;

int16_t tca9548a_read(uint8_t slave_address) {
  
  // Keep track of the number of times we've tried to read
  uint8_t tries = 0;
  // Slave address + read bit
  uint8_t sla = slave_address << 1;

  union {
    uint8_t b[1];
    uint16_t w;
  } data_union;

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
    logger_msg_p("tca954xa",log_level_DEBUG,PSTR("Set start condition"));
    break;
  case TW_MT_ARB_LOST:
    logger_msg_p("tca954xa",log_level_DEBUG,PSTR("Arbitration lost"));
    goto begin;

  default:
    logger_msg_p("tca954xa",log_level_ERROR,PSTR("Could not set start condition"));
    return -1;
  }

  // Send control byte with bit set for reading
  TWDR = sla | TW_READ;
  // Clear interrupt to start transmission
  TWCR = _BV(TWINT) | _BV(TWEN);
  // Wait for transmission to finish
  while ((TWCR & _BV(TWINT)) == 0);
  twst = TW_STATUS;
  logger_msg_p("tca954xa", log_level_DEBUG, PSTR("TWI status is 0x%x"),twst);
  switch (twst) {
  case TW_MR_SLA_ACK:
    logger_msg_p("tca954xa", log_level_DEBUG, PSTR("SLA+R transmitted, ACK received"));
    break;

  case TW_MR_SLA_NACK:
    logger_msg_p("tca954xa", log_level_DEBUG,
		 PSTR("SLA+R transmitted, NACK received after %u tries"), tries);
    goto restart;

  case TW_MR_ARB_LOST:
    logger_msg_p("tca954xa",log_level_DEBUG,PSTR("Arbitration lost"));
    goto begin;

  default:
    logger_msg_p("tca954xa",log_level_ERROR,PSTR("Could not select device"));
    goto error;
  }

  // Read the return

  for (int8_t bytenum = 0; bytenum >= 0; bytenum--) {
    // Clear interrupt to start transmission
    if (bytenum == 0) {
      // This is the last byte -- send NACK instead
      TWCR = _BV(TWINT) | _BV(TWEN);
    } else {
      // Send ACK from master after byte received
      TWCR = _BV(TWINT) | _BV(TWEN) | _BV(TWEA);
    }
    // Wait for transmission to finish
    while ((TWCR & _BV(TWINT)) == 0);
    twst = TW_STATUS;
    logger_msg_p("tca954xa", log_level_DEBUG, PSTR("TWI status is 0x%x"),twst);
    switch (twst) {
    case TW_MR_DATA_NACK:
      logger_msg_p("tca954xa", log_level_DEBUG, PSTR("NACK received after data request"));
      // No data or end of data -- fall through

    case TW_MR_DATA_ACK:
      data_union.b[bytenum] = TWDR;
      logger_msg_p("tca954xa", log_level_DEBUG, PSTR("Read %u from control register"),
       		   data_union.b[bytenum]);
      break;

    default:
      goto error;
    }
  }

 quit:
  // Send stop condition
  TWCR = _BV(TWINT) | _BV(TWSTO) | _BV(TWEN);

  
  return data_union.w;

 error:
  data_union.w = -1;
  goto quit;
}

int8_t tca9548a_write(uint8_t slave_address, uint8_t command_byte) {
  int16_t retval = 0;
  // Keep track of the number of times we've tried to write
  uint8_t tries = 0;
  // Slave address + R/W bit
  uint8_t sla = slave_address << 1;

  union {
    uint8_t b[1];
    uint8_t w;
  } data_union;
  data_union.w = command_byte;

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
    logger_msg_p("tca954xa",log_level_DEBUG,PSTR("Start condition set"));
    break;
  case TW_MT_ARB_LOST:
    logger_msg_p("tca954xa",log_level_DEBUG,PSTR("Arbitration lost"));
    goto begin;

  default:
    logger_msg_p("tca954xa",log_level_ERROR,PSTR("Could not set start condition"));
    return -1;
  }

  //********************** Send control byte ***********************//
  TWDR = sla | TW_WRITE;
  // Clear interrupt to start transmission
  TWCR = _BV(TWINT) | _BV(TWEN);
  // Wait for start condition to finish
  while ((TWCR & _BV(TWINT)) == 0);
  twst = TW_STATUS;
  logger_msg_p("tca954xa", log_level_DEBUG, PSTR("TWI status is 0x%x"),twst);
  switch (twst) {
  case TW_MT_SLA_ACK:
    logger_msg_p("tca954xa", log_level_DEBUG, PSTR("SLA+W transmitted, ACK received"));
    break;

  case TW_MT_SLA_NACK:
    logger_msg_p("tca954xa", log_level_DEBUG,
		 PSTR("SLA+W sent, got NACK from address 0x%x after %u tries"),
		 slave_address, tries);
    goto restart;

  case TW_MT_ARB_LOST:	/* re-arbitrate */
    logger_msg_p("tca954xa",log_level_DEBUG,PSTR("Arbitration lost"));
    goto begin;

  default:
    logger_msg_p("tca954xa",log_level_ERROR,PSTR("Could not select device"));
    goto error;		/* must send stop condition */
  }

  //*********************** Write data bytes ***********************//

  for (int8_t bytenum = 0; bytenum >= 0; bytenum--) {
    TWDR = data_union.b[bytenum];
    // Clear interrupt to start transmission
    TWCR = _BV(TWINT) | _BV(TWEN);
    // Wait for transmission to finish
    while ((TWCR & _BV(TWINT)) == 0);

    twst = TW_STATUS;
    logger_msg_p("tca954xa", log_level_DEBUG, PSTR("TWI status is 0x%x"),twst);
    switch (twst) {
    case TW_MT_DATA_ACK:
      logger_msg_p("tca954xa", log_level_DEBUG, PSTR("Slave ACKed data byte %u."),
		   bytenum);
      logger_msg_p("tca954xa", log_level_DEBUG, PSTR("Wrote 0x%x to control register"),
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

