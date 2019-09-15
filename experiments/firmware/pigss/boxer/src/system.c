// Miscellaneous system functions

// ----------------------- Include files ------------------------------
#include <stdio.h>
#include <string.h>

// Contains macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>

// Watchdog timer
#include <avr/wdt.h>

// Bit manipulation for AVR
#include "avr035.h"

#include "usart.h"

// Sets up logging
#include "logger.h"

// Provides commands for working with the eeprom
#include "eeprom.h"

// Provides commands for handling SPI chip selects
#include "cs.h"

// Provides commands for writing to SPI
#include "spi.h"

// Provides definitions and functions for using the Topaz manifold boards
#include "topaz.h"

// Provides channel_set() for turning channels on and off
#include "channel.h"

// Provides definitions and functions for working with Vernon
#include "vernon.h"

// Provides definitions and functions for working with the Aloha front panel
#include "aloha.h"

#include "system.h"

// ----------------------- Globals ------------------------------------

// idnstr format: Organization, model, serial, version
const char idnstr[] PROGMEM = "Picarro,Boxer,SN%u,%s";

/* System status structure

   Keeps track of miscellaneous system status:
   -- Serial number
*/
system_state_t system_state;
system_state_t *system_state_ptr = &system_state;

// ----------------------- Functions ----------------------------------

void system_init( void ) {
  uint16_t sernum = 0;
  eeprom_load_sernum(system_state_ptr);
  eeprom_load_slotid(system_state_ptr);

  // The system status structure needs to know about what's connected.
  // We can only talk to Topaz boards if they have a serial number, so
  // try to get that.
  sernum = topaz_get_serial_number('a');
  logger_msg_p("system",log_level_INFO,PSTR("Topaz A serial number is %i"),
	       sernum);

  sernum = topaz_get_serial_number('b');
  logger_msg_p("system",log_level_INFO,PSTR("Topaz B serial number is %i"),
	       sernum);

  // Get the serial number for Vernon
  sernum = vernon_get_serial_number();
  logger_msg_p("system",log_level_INFO,PSTR("Vernon serial number is %i"),
	       sernum);

  // Make PF7 an input to detect nRTS
  DDRF &= ~( _BV(DDF7) );

  // Set the OK status on the front panel
  uint32_t led_value = system_state_get_fp_led_value();
  aloha_write( (uint32_t) 1<<STATUS_GREEN | led_value);

  // Check for USB connection.  We only have to do this at startup,
  // since the system always goes through a reset when a USB channel is opened
  led_value = system_state_get_fp_led_value();
  if ( system_usb_is_connected() ) {
    aloha_write( (uint32_t) 1<<COM_GREEN | led_value);
  } else {
    aloha_write( (uint32_t) 1<<COM_RED | led_value);
  }
}

void cmd_idn_q( command_arg_t *command_arg_ptr ) {
  usart_printf_p(USART_CHANNEL_COMMAND, idnstr, system_state_ptr -> sernum,REVCODE);
  usart_printf(USART_CHANNEL_COMMAND, LINE_TERMINATION_CHARACTERS);
}

system_state_value_t set_system_state(system_state_value_t requested_state) {
  // For now, just set the state to the requested value
  system_state_ptr -> state_enum = requested_state;
  return(system_state_ptr -> state_enum);
}

system_state_value_t get_system_state( void ) {
  // Return the current system state
  return(system_state_ptr -> state_enum);
}

int8_t system_enter_standby(void) {
  int8_t retval = 0;
  switch( system_state.state_enum ) {
  case system_state_INIT:
    // Transition from INIT to STANDBY
    //
    // All channels --> OFF
    channel_set(0);
    // Clean solenoid --> OFF
    vernon_set_clean_solenoid(0);
    logger_msg_p("system",log_level_INFO,PSTR("State change INIT to STANDBY"));
    set_system_state(system_state_STANDBY);

    break;
  case system_state_STANDBY:
    // We're already in standby, but disabling all channels resets the
    // proportional valves.
    channel_set(0);
    break;
  case system_state_CONTROL:
    // Transition from CONTROL to STANDBY
    //
    // All channels --> OFF
    channel_set(0);
    // Clean solenoid --> OFF
    vernon_set_clean_solenoid(0);
    logger_msg_p("system",log_level_INFO,PSTR("State change CONTROL to STANDBY"));
    set_system_state(system_state_STANDBY);
    break;
  case system_state_CLEAN:
    // Transition from CLEAN to STANDBY
    //
    // All channels --> OFF
    channel_set(0);
    // Clean solenoid --> OFF
    vernon_set_clean_solenoid(0);
    // Blue LEDs --> OFF
    aloha_clear_clean_leds();
    logger_msg_p("system",log_level_INFO,PSTR("State change CLEAN to STANDBY"));
    set_system_state(system_state_STANDBY);
    break;    
  default:
    logger_msg_p("system", log_level_ERROR,
		 PSTR("Enter standby from bad system state %d"),
		 system_state_ptr -> state_enum);
    retval += -1;
    break;
  }
  return retval;
}

int8_t system_enter_control(void) {
  int8_t retval = 0;
  switch( system_state.state_enum ) {
  case system_state_CONTROL:
    // Nothing to do here
    break;
  case system_state_INIT:
    // Transition from INIT to CONTROL is forbidden
    break;
  case system_state_STANDBY:
    // Transition from STANDBY to CONTROL
    logger_msg_p("system",log_level_INFO,PSTR("State change STANDBY to CONTROL"));
    set_system_state(system_state_CONTROL);
    break;
  case system_state_CLEAN:
    // Transition from CLEAN to CONTROL
    //
    // Clean solenoid --> OFF
    vernon_set_clean_solenoid(0);
    // Turn off blue LEDs
    aloha_clear_clean_leds();
    logger_msg_p("system",log_level_INFO,PSTR("State change CLEAN to CONTROL"));
    set_system_state(system_state_CONTROL);
    break; 
  
    
  default:
    logger_msg_p("system", log_level_ERROR,
		 PSTR("Enter control from bad system state %d"),
		 system_state.state_enum);
    retval += -1;
    break;
  }
  return retval;
}

int8_t system_enter_clean(void) {
  int8_t retval = 0;
  switch( system_state.state_enum ) {
  case system_state_CLEAN:
    // Nothing to do here
    break;
  case system_state_INIT:
    // Transition from INIT to CLEAN is forbidden
    break;
  case system_state_STANDBY:
    // Transition from STANDBY to CLEAN
    //
    // All channels --> OFF
    channel_set(0);
    // Clean solenoid --> ON
    vernon_set_clean_solenoid(1);
    // Turn blue LEDs on
    aloha_show_clean_leds();
    logger_msg_p("system",log_level_INFO,PSTR("State change STANDBY to CLEAN"));
    set_system_state(system_state_CLEAN);
    break;
  case system_state_CONTROL:
    // Transition from CONTROL to CLEAN
    //
    // All channels --> OFF
    channel_set(0);
    // Clean solenoid --> ON
    vernon_set_clean_solenoid(1);
    // Turn blue LEDs on
    aloha_show_clean_leds();
    logger_msg_p("system",log_level_INFO,PSTR("State change CONTROL to CLEAN"));
    set_system_state(system_state_CLEAN);
    break;
    
  default:
    logger_msg_p("system", log_level_ERROR,
		 PSTR("Enter clean from bad system state %d"),
		 system_state.state_enum);
    retval += -1;
    break;
  }
  return retval; 
}

void cmd_rst( command_arg_t *command_arg_ptr ) {
  // Set watchdog to lowest interval and delay longer than that
  wdt_enable(WDTO_15MS);
  while(1);
}

void cmd_opstate_q( command_arg_t *command_arg_ptr ) {
  switch( system_state_ptr -> state_enum ) {
  case system_state_INIT:
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "init",
		 LINE_TERMINATION_CHARACTERS );
    break;
  case system_state_STANDBY:
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "standby",
		 LINE_TERMINATION_CHARACTERS );
    break;
  case system_state_CONTROL:
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "control",
		 LINE_TERMINATION_CHARACTERS );
    break;
  case system_state_CLEAN:
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "clean",
		 LINE_TERMINATION_CHARACTERS );
    break;  
  default:
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "none",
		 LINE_TERMINATION_CHARACTERS );
  }
}

void cmd_slotid_q( command_arg_t *command_arg_ptr ) {
  usart_printf(USART_CHANNEL_COMMAND, "%u%s",
	       system_state_ptr -> slotid,
	       LINE_TERMINATION_CHARACTERS);
}

void cmd_standby( command_arg_t *command_arg_ptr ) {
  int8_t retval = 0;
  retval = system_enter_standby();
  if (retval == 0) {
    command_ack();
    return;
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_clean( command_arg_t *command_arg_ptr ) {
  int8_t retval = 0;
  retval = system_enter_clean();
  if (retval == 0) {
    command_ack();
    return;
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  } 
}

int8_t system_state_set_topaz_sernum(char board, uint16_t sernum) {
  if (board == 'a') {
    system_state.topaz_a_sernum = sernum;
  } else {
    system_state.topaz_b_sernum = sernum;
  }
  return 0;
}

int8_t system_state_set_vernon_sernum(uint16_t sernum) {
  system_state.vernon_sernum = sernum;
  return 0;
}

int8_t system_state_set_system_sernum(uint16_t sernum) {
  system_state.sernum = sernum;
  return 0;
}

int8_t system_state_set_system_slotid( uint8_t slotid ) {
  system_state.slotid = slotid;
  return 0;
}

uint16_t system_state_get_topaz_sernum(char board ) {
  if (board == 'a') {
    return system_state.topaz_a_sernum;
  } else {
    return system_state.topaz_b_sernum;
  }
}

system_state_value_t system_state_get_system_state(void) {
  return system_state.state_enum;
}

uint16_t system_state_get_vernon_sernum(void) {
  return system_state.vernon_sernum;
}

int8_t system_state_set_fp_led_value(uint32_t value) {
  system_state.fp_led_value = value;
  return 0;
}

uint32_t system_state_get_fp_led_value(void) {
  return system_state.fp_led_value;
}

bool system_usb_is_connected( void ) {
  logger_msg_p("system",log_level_DEBUG,PSTR("PINF value is 0x%x"),PINF);
  if ( CHECKBIT(PINF,PINF7) ) {
    // nRTS is high, so USB is not connected
    return false;
  } else {
    return true;
  }
}
