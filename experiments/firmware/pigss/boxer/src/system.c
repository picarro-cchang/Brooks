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

// Provides definitions and functions for working with the channel
// identification module
#include "identify.h"

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
  case system_state_SHUTDOWN:
    // SHUTDOWN to STANDBY only happens with a reset
    logger_msg_p("system",log_level_ERROR,PSTR("Forbidden state change SHUTDOWN to STANDBY"));
    retval += -1;
    break; 
  case system_state_CONTROL:
    // Transition from CONTROL to STANDBY
    //
    // All channels --> OFF
    channel_set(0);
    // Clean solenoid --> OFF
    vernon_set_clean_solenoid(0);
    // MFC value --> 0
    identify_state_set_mfc_value(0.0);
    // Actually set the system state
    set_system_state(system_state_STANDBY);
    logger_msg_p("system",log_level_INFO,PSTR("State change CONTROL to STANDBY"));
    break;
  case system_state_CLEAN:
    // Transition from CLEAN to STANDBY
    //
    // All channels --> OFF
    channel_set(0);
    // Clean solenoid --> OFF
    vernon_set_clean_solenoid(0);
    // MFC value --> 0
    identify_state_set_mfc_value(0.0);
    // Blue LEDs --> OFF
    aloha_clear_clean_leds();
    // Actually set the system state
    set_system_state(system_state_STANDBY);
    logger_msg_p("system",log_level_INFO,PSTR("State change CLEAN to STANDBY"));
    break;
  case system_state_IDENTIFY:
    // Transition from IDENTIFY to STANDBY
    //
    // All channels --> OFF
    channel_set(0);
    // MFC value --> 0
    identify_state_set_mfc_value(0.0);
    // Actually set the system state
    set_system_state(system_state_STANDBY);
    logger_msg_p("system",log_level_INFO,PSTR("State change IDENTIFY to STANDBY"));
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
  case system_state_SHUTDOWN:
    // Transition from SHUTDOWN to CONTROL is forbidden
    logger_msg_p("system",log_level_ERROR,PSTR("Forbidden state change SHUTDOWN to CONTROL"));
    retval += -1;
    break;
  case system_state_INIT:
    // Transition from INIT to CONTROL is forbidden
    retval += -1;
    break;
  case system_state_STANDBY:
    // Transition from STANDBY to CONTROL
    // MFC value --> 40
    identify_state_set_mfc_value(40.0);
    // Actually set the system state
    set_system_state(system_state_CONTROL);
    logger_msg_p("system",log_level_INFO,PSTR("State change STANDBY to CONTROL"));    
    break;
  case system_state_CLEAN:
    // Transition from CLEAN to CONTROL
    //
    // Clean solenoid --> OFF
    vernon_set_clean_solenoid(0);
    // Turn off blue LEDs
    aloha_clear_clean_leds();
    // MFC value --> 40
    identify_state_set_mfc_value(40.0);
    // Actually set the system state
    set_system_state(system_state_CONTROL);
    logger_msg_p("system",log_level_INFO,PSTR("State change CLEAN to CONTROL"));
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
    // MFC value --> 40
    identify_state_set_mfc_value(40.0);
    // Actually set the system state
    set_system_state(system_state_CLEAN);
    logger_msg_p("system",log_level_INFO,PSTR("State change STANDBY to CLEAN"));
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
    // MFC value --> 40
    identify_state_set_mfc_value(40.0);
    // Actually set the system state
    set_system_state(system_state_CLEAN);
    logger_msg_p("system",log_level_INFO,PSTR("State change CONTROL to CLEAN"));
    break;
  case system_state_SHUTDOWN:
    // Transition from SHUTDOWN to CLEAN is not allowed
    logger_msg_p("system",log_level_ERROR,PSTR("Forbidden state change SHUTDOWN to CONTROL"));
    retval += -1;
  default:
    logger_msg_p("system", log_level_ERROR,
		 PSTR("Enter clean from bad system state %d"),
		 system_state.state_enum);
    retval += -1;
    break;
  }
  return retval; 
}

int8_t system_enter_identify(void) {
  int8_t retval = 0;
  switch( system_state.state_enum ) {
  case system_state_IDENTIFY:
    // Nothing to do here
    break;
  case system_state_CLEAN:
    // Transition from CLEAN to IDENTIFY is forbidden
    retval += -1;
    break;
  case system_state_INIT:
    // Transition from INIT to IDENTIFY is forbidden
    retval += -1;
    break;
  case system_state_STANDBY:
    // Transition from STANDBY to IDENTIFY.AMBIENT
    //
    // In this interim release, we'll just kick off a delay

    // Set the overall system state
    set_system_state(system_state_IDENTIFY);
    // Set the identify substate
    identify_state_set_state_enum(identify_state_AMBIENT);
    // Kick off the channel identification procedure
    identify_find_active_channels();
    logger_msg_p("system",log_level_INFO,PSTR("State change STANDBY to IDENTIFY.AMBIENT"));
    break;
  case system_state_CONTROL:
    // Transition from CONTROL to IDENTIFY is forbidden
    retval += -1;
    break;
  case system_state_SHUTDOWN:
    // Transition from SHUTDOWN to IDENTIFY is forbidden
    retval += -1;
    break;
  default:
    logger_msg_p("system", log_level_ERROR,
		 PSTR("Enter IDENTIFY from bad system state %d"),
		 system_state.state_enum);
    retval += -1;
    break;
  }
  return retval; 
}

int8_t system_enter_shutdown(void) {
  int8_t retval = 0;
  switch( system_state.state_enum ) {
  case system_state_SHUTDOWN:
    // Nothing to do here
    break;
  case system_state_INIT:
    // Transition from INIT to SHUTDOWN is forbidden
    retval += -1;
    break;
  case system_state_STANDBY:
    // Transition from STANDBY to SHUTDOWN
    //
    // All channels --> ON (relaxes solenoids).  This will actually
    // set the system state to CONTROL, but
    // channel_set(0xff);
    channel_set_solenoids(0);
    // Clean solenoid --> OFF
    vernon_set_clean_solenoid(0);
    // All LEDs --> OFF
    aloha_write((uint32_t) 0);
    logger_msg_p("system",log_level_INFO,PSTR("State change STANDBY to SHUTDOWN"));
    set_system_state(system_state_SHUTDOWN);
    break;
  case system_state_CONTROL:
    // Transition from CONTROL to SHUTDOWN
    //
    // All channels --> ON (relaxes solenoids)
    channel_set(0xff);
    // Clean solenoid --> OFF
    vernon_set_clean_solenoid(0);
    logger_msg_p("system",log_level_INFO,PSTR("State change CONTROL to SHUTDOWN"));
    set_system_state(system_state_SHUTDOWN);
    break;
  case system_state_CLEAN:
    // Transition from CLEAN to SHUTDOWN
    //
    // All channels --> ON (relaxes solenoids)
    channel_set(0xff);
    // Clean solenoid --> OFF
    vernon_set_clean_solenoid(0);
    logger_msg_p("system",log_level_INFO,PSTR("State change CLEAN to SHUTDOWN"));
    set_system_state(system_state_SHUTDOWN);
    break; 
    
  default:
    logger_msg_p("system", log_level_ERROR,
		 PSTR("Enter shutdown from bad system state %d"),
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
  case system_state_SHUTDOWN:
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "shutdown",
		 LINE_TERMINATION_CHARACTERS );
    break;
  case system_state_IDENTIFY:
    usart_printf(USART_CHANNEL_COMMAND, "%s%s",
		 "identify",
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

void cmd_identify( command_arg_t *command_arg_ptr ) {
  int8_t retval = 0;
  retval = system_enter_identify();
  if (retval == 0) {
    command_ack();
    return;
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_shutdown( command_arg_t *command_arg_ptr ) {
  int8_t retval = 0;
  retval = system_enter_shutdown();
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
  if ( CHECKBIT(PINF,PINF7) ) {
    // nRTS is high, so USB is not connected
    return false;
  } else {
    return true;
  }
}

void system_comcheck_task( void ) {
  if ( system_usb_is_connected() ) {
    // Everything is OK
    return;
  } else {
    logger_msg_p("system",log_level_DEBUG,PSTR("No connection"));
    system_enter_shutdown();
    return;
  }
}

