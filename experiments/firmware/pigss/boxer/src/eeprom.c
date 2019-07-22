
// EEPROM module
// 
// The ATmega2560 contains 4K bytes of data EEPROM memory.  It is
// organized as a separate data space in which single bytes can be
// read and written.


// ----------------------- Include files ------------------------------
#include <stdio.h>

/* avr/io.h
   
   Device-specific port definitions.  Also provides special
   bit-manipulations functions like bit_is_clear and
   loop_until_bit_is_set.
*/
#include <avr/io.h>

/* logger.h

   Provides logger_msg and logger_msg_p for log messages tagged with a
   system and severity.
*/
#include "logger.h"

/* pgmspace.h
   
   Provides macros and functions for saving and reading data out of
   flash.
*/
#include <avr/pgmspace.h>

/* avr/interrupt.h

   Provides sei() and cli() for enabling and disabling all interrupts.
 */
#include <avr/interrupt.h>

// Provide definition of system_state_t
#include "system.h"

#include "eeprom.h"

// ----------------------- Functions ----------------------------------

/* eeprom_write_char( address, data )

   Writes an 8-bit data value to an eeprom address.

   Returns: none
*/
void eeprom_write_char( uint16_t address, uint8_t data ) {
  /* Disable all interrupts by clearing the global interrupt mask.
     Writing to the eeprom takes a long time (few ms).
   */
  cli();
  // Wait for all writes to finish.  If the EEPE (eeprom write enable)
  // bit in the EECR (EEPROM control register) is set, data is being
  // written.
  loop_until_bit_is_clear(EECR, EEPE);
  /* EEAR is the eeprom address register.  Even though there's 9 bits
     of address space, you can just write to the EEAR location. 
  */
  EEAR = address;
  EEDR = data;
  // The EEMPE (eeprom master write enable bit) must be set before the
  // eeprom-writing strobe EEPE can be set.  Furthermore, EEMPE will
  // be cleared automatically in 4 cycles, so you can't just set it in
  // an init function.
  EECR |= _BV(EEMPE);
  EECR |= _BV(EEPE); // Write the data
  sei(); // Turn interrupts back on 
  logger_msg_p("eeprom",log_level_INFO,
	       PSTR("Wrote %i to address %i"),data,address);
}

/* eeprom_read_char( address )

   Reads an eeprom address.

   Returns: 8-bit unsigned integer
*/
uint8_t eeprom_read_char( uint16_t address ) {
  cli(); // Disable all interrupts
  // Wait for all writes to finish.  If the EEPE (eeprom write enable)
  // bit in the EECR register is set, data is being written.
  loop_until_bit_is_clear(EECR, EEPE);
  /* EEAR is the eeprom address register.  Even though there's 9 bits
     of address space, you can just write to the EEAR location. 
  */
  EEAR = address;
  /* Start eeprom read by writing EERE */
  EECR |= _BV(EERE);
  /* Return data from data register */
  sei(); // Turn interrupts back on
  logger_msg_p("eeprom",log_level_INFO,
	       PSTR("Read %i from address %i"),EEDR,address);
  return EEDR;
}

void eeprom_save_sernum( uint16_t sernum ) {
  logger_msg_p( "eeprom", log_level_DEBUG,
		PSTR("Writing serial number %u"),sernum);
  uint8_t lowbyte = (uint8_t)(sernum & 0xff);
  uint8_t highbyte = (uint8_t)( (sernum & 0xff00) >> 8);
  eeprom_write_char(SERNUM_ADDR,lowbyte);
  eeprom_write_char(SERNUM_ADDR + 1, highbyte);
}

void eeprom_load_sernum( system_state_t *system_state_ptr ) {
  uint8_t lowbyte = eeprom_read_char(SERNUM_ADDR);
  uint8_t highbyte = eeprom_read_char(SERNUM_ADDR + 1);
  system_state_ptr -> sernum = (uint16_t)( (highbyte << 8) + lowbyte );
  logger_msg_p( "eeprom", log_level_DEBUG,
		PSTR("Loading serial number %u"),
		system_state_ptr -> sernum);
}

void cmd_write_sernum( command_arg_t *command_arg_ptr ) {
  uint16_t sernum = (command_arg_ptr -> uint16_arg);
  eeprom_save_sernum(sernum);
  system_init();
  // Acknowledge the successful command
  command_ack();
}

void eeprom_save_slotid( uint8_t slotid ) {
  logger_msg_p( "eeprom", log_level_DEBUG,
		PSTR("Writing slot ID %u"),slotid);
  eeprom_write_char(SLOTID_ADDR,slotid);
}

void eeprom_load_slotid( system_state_t *system_state_ptr ) {
  uint8_t slotid = eeprom_read_char(SLOTID_ADDR);
  system_state_ptr -> slotid = slotid;
  logger_msg_p( "eeprom", log_level_DEBUG,
		PSTR("Loading slot ID %u"),
		system_state_ptr -> slotid);
}

void cmd_write_slotid( command_arg_t *command_arg_ptr ) {
  uint8_t slotid = (uint8_t)(command_arg_ptr -> uint16_arg);
  eeprom_save_slotid(slotid);
  system_init();
  // Acknowledge the successful command
  command_ack();
}






