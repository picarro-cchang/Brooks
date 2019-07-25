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

// Functions for maintaining a simple schedule
#include "OS.h"

#include "topaz.h"


#include "spi.h"

#include "bargraph.h"

// Provides functions for working with Honeywell MPR pressure sensors
#include "mpr.h"

// Provides exponential moving average
#include "math.h"

#include "pressure.h"

//*************** Uncalibrated (counts) data storage ***************//

// Last smoothed pressure value for all inlets (uncalibrated)
uint32_t pressure_channel_inlet_old_counts[8] =
  {0ul,0ul,0ul,0ul,0ul,0ul,0ul,0ul};

// Last smoothed pressure value for all outlets (uncalibrated)
uint32_t pressure_outlet_old_counts[2] = {0ul,0ul};

// New smoothed pressure values for all inlets (uncalibrated)
uint32_t pressure_channel_inlet_new_counts[8] =
  {0ul,0ul,0ul,0ul,0ul,0ul,0ul,0ul};

// New smoothed pressure value for all outlets (uncalibrated)
uint32_t pressure_outlet_new_counts[2] = {0ul,0ul}; 

//*************** Calibrated (Pascals) data storage ****************//

// Last smoothed pressure value for all inlets (uncalibrated)
uint32_t pressure_channel_inlet_old_pascals[8] =
  {0ul,0ul,0ul,0ul,0ul,0ul,0ul,0ul};

// Last smoothed pressure value for all outlets (uncalibrated)
uint32_t pressure_outlet_old_pascals[2] = {0ul,0ul};

// New smoothed pressure values for all inlets (uncalibrated)
uint32_t pressure_channel_inlet_new_pascals[8] =
  {0ul,0ul,0ul,0ul,0ul,0ul,0ul,0ul};

// New smoothed pressure value for all outlets (uncalibrated)
uint32_t pressure_outlet_new_pascals[2] = {0ul,0ul};



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

int8_t pressure_mpr_trigger_cycle( void ) {
  // Trigger all the inlet channels
  for (uint8_t channel = 1; channel < 5; channel++) {
    pressure_mpr_inlet_trigger(channel);
  }
  // Trigger the outlet channels
  pressure_mpr_outlet_trigger('a');
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

void pressure_mpr_trigger_task(void) {
  pressure_mpr_trigger_cycle();

  // Schedule the read
  OS_SetTaskState(1, BLOCKED);				   
}

void pressure_mpr_read_task(void) {
  pressure_mpr_outlet_read('a', &pressure_outlet_new_counts[0]);
  pressure_outlet_old_counts[0] = math_ema_ui32(pressure_outlet_new_counts[0],
						pressure_outlet_old_counts[0],
						PRESSURE_EMA_ALPHA);
  pressure_outlet_old_pascals[0] = pressure_convert_pascals(pressure_outlet_old_counts[0]);
  logger_msg_p("pressure", log_level_INFO,
	       PSTR("Old pressure code 0x%lx"),
	       pressure_outlet_old_counts[0]);

  // Cancel the read
  OS_SetTaskState(1, SUSPENDED);
}

void cmd_out_prs_raw_q( command_arg_t *command_arg_ptr ) {
  uint16_t board_number = (command_arg_ptr -> uint16_arg);
  switch(board_number) {
  case 1 :
    usart_printf( USART_CHANNEL_COMMAND, "%lu%s",
	       pressure_outlet_old_counts[0],
		 LINE_TERMINATION_CHARACTERS );
    break;
  default :
    // This is an out of range input
    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
  }
}

uint32_t pressure_convert_pascals( uint32_t raw ) {
  uint64_t temp = 0;
  temp = (uint64_t) (raw - MPR_NMIN) * MPR_PMAX_PASCAL;
  return (uint32_t) temp/(MPR_NMAX - MPR_NMIN);
}
