#include <stdio.h>

// Provides integer max value definitions
#include <stdint.h>

// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Library functions and macros for AVR interrupts
#include <avr/interrupt.h>

// Convenience functions for busy-wait loops
#include <util/delay.h>

// Provides macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>

// Provides logger_msg and logger_msg_p for log messages tagged with a
// system and severity.
#include "logger.h"

// Provide cs functions
#include "cs.h"

// Provides command_ack and command_nack
#include "command.h"

// Provides functions for working with the UART
#include "usart.h"

#include "topaz.h"


#include "spi.h"

#include "bargraph.h"

// Provides functions for working with Honeywell MPR pressure sensors
#include "mpr.h"

#include "pressure.h"

int8_t pressure_dac_set(uint8_t channel, uint16_t counts) {
  switch(channel) {
  case 1 :
    cs_ch1_dac_mux();
    ltc2601_write( &cs_topaz_a_target, 0x3, counts);
    break;
  case 2 :
    cs_ch2_dac_mux();
    ltc2601_write( &cs_topaz_a_target, 0x3, counts);
    break;
  case 3 :
    cs_ch3_dac_mux();
    ltc2601_write( &cs_topaz_a_target, 0x3, counts);
    break;
  case 4 :
    cs_ch4_dac_mux();
    ltc2601_write( &cs_topaz_a_target, 0x3, counts);
    break;  
  }
  
  return 0;
}

int8_t pressure_mpr_inlet_trigger(uint8_t channel) {
  switch(channel) {
  case 1 :
    cs_ch1_mpr_mux();
    mpr_trigger( &cs_topaz_a_target );
    break;
  case 2 :
    cs_ch2_mpr_mux();
    mpr_trigger( &cs_topaz_a_target );
    break;
  case 3 :
    cs_ch3_mpr_mux();
    mpr_trigger( &cs_topaz_a_target );
    break;
  case 4 :
    cs_ch4_mpr_mux();
    mpr_trigger( &cs_topaz_a_target );
    break; 
  }
  return 0;
}

int8_t pressure_mpr_outlet_trigger(char board) {
  switch(board) {
  case 'a' :
    cs_outlet_a_mpr_mux();
    mpr_trigger( &cs_topaz_a_target );
    break;
  case 'b' :
    cs_outlet_b_mpr_mux();
    mpr_trigger( &cs_topaz_b_target );
    break;
  }
  return 0;
}

int8_t pressure_mpr_inlet_read(uint8_t channel, uint32_t *data_ptr) {
  switch(channel) {
  case 1 :
    cs_ch1_mpr_mux();
    mpr_read( &cs_topaz_a_target, data_ptr);
    break;
  case 2 :
    cs_ch2_mpr_mux();
    mpr_read( &cs_topaz_a_target, data_ptr);
    break;
  case 3 :
    cs_ch3_mpr_mux();
    mpr_read( &cs_topaz_a_target, data_ptr);
    break;
  case 4 :
    cs_ch4_mpr_mux();
    mpr_read( &cs_topaz_a_target, data_ptr);
    break;
  }
  return 0;
}

int8_t pressure_mpr_outlet_read(char board, uint32_t *data_ptr) {
  switch(board) {
  case 'a' :
    cs_outlet_a_mpr_mux();
    mpr_read( &cs_topaz_a_target, data_ptr);
    break;
  case 'b' :
    cs_outlet_b_mpr_mux();
    mpr_read( &cs_topaz_b_target, data_ptr);
    break;
  }
  return 0;
}
