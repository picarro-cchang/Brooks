#include <stdio.h>

// Provides integer max value definitions
#include <stdint.h>

// Provides strcmp
#include <string.h>

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

// Provides enumerated system states and system state structure accessors
#include "system.h"

#include "topaz.h"

#include "spi.h"

// Provides ltc2601_write() for proportional DACs
#include "ltc2601.h"

#include "bargraph.h"

// Provides functions for working with Honeywell MPR pressure sensors
#include "mpr.h"

// Provides exponential moving average
#include "math.h"

#include "pressure.h"

pressure_state_t pressure_state = { .ema_alpha = 65535 };

//*************** Uncalibrated (counts) data storage ***************//

// Last smoothed pressure value for all inlets (uncalibrated)
uint32_t pressure_inlet_old_counts[8] =
  {0ul,0ul,0ul,0ul,0ul,0ul,0ul,0ul};

// Last smoothed pressure value for all outlets (uncalibrated)
uint32_t pressure_outlet_old_counts[2] = {0ul,0ul};

// New smoothed pressure values for all inlets (uncalibrated)
uint32_t pressure_inlet_new_counts[8] =
  {0ul,0ul,0ul,0ul,0ul,0ul,0ul,0ul};

// New smoothed pressure value for all outlets (uncalibrated)
uint32_t pressure_outlet_new_counts[2] = {0ul,0ul};

//*************** Calibrated (Pascals) data storage ****************//

// Last smoothed pressure value for all inlets (uncalibrated)
uint32_t pressure_inlet_old_pascals[8] =
  {0ul,0ul,0ul,0ul,0ul,0ul,0ul,0ul};

// Last smoothed pressure value for all outlets (uncalibrated)
uint32_t pressure_outlet_old_pascals[2] = {0ul,0ul};

// New smoothed pressure values for all inlets (uncalibrated)
uint32_t pressure_inlet_new_pascals[8] =
  {0ul,0ul,0ul,0ul,0ul,0ul,0ul,0ul};

// New smoothed pressure value for all outlets (uncalibrated)
uint32_t pressure_outlet_new_pascals[2] = {0ul,0ul};

//******************* Propotional valve settings *******************//

// Each DAC will have an entry in this array.  Channel 1 will be the
// first entry.
uint16_t pressure_dac_counts[8] =
  {0ul,0ul,0ul,0ul,0ul,0ul,0ul,0ul};


int8_t pressure_init(void) {
  int8_t retval = 0;

  uint16_t pressure_read_period_ms = 0;
  uint16_t mpr_read_delay_ms = 0;

  if (strcmp( LOG_LEVEL, "debug" ) == 0) {
    // We're debugging.  Slow the reads way down.
    pressure_read_period_ms = 1000;
    mpr_read_delay_ms = 500;
  } else if (strcmp( LOG_LEVEL, "info" ) == 0) {
    // We're debugging.  Slow the reads way down.
    pressure_read_period_ms = 2000;
    mpr_read_delay_ms = 1000;
  } else if (strcmp( LOG_LEVEL, "error" ) == 0) {
    // This could be a release.  The minimum read delay is 5ms.
    pressure_read_period_ms = 25;
    mpr_read_delay_ms = 6;
  }

  // OS_TaskCreate(function pointer, interval (ms), READY, BLOCKED or SUSPENDED)
  //
  // READY tasks will execute ASAP and then switch to BLOCKED
  // BLOCKED tasks will wait for their interval to expire and then become READY
  // SUSPENDED tasks will never execute

  // Task -- Trigger all the pressure sensors.  This task will
  // schedule the read, which will then cancel itself.  The next
  // trigger will schedule it again.
  if (strcmp( PRESSURE_READS_ENABLED, "true" ) == 0) {
    // Pressure reads are enabled
    OS_TaskCreate(&pressure_mpr_trigger_task, pressure_read_period_ms, BLOCKED);    
  }

  // Task -- Read all the pressure sensors
  OS_TaskCreate(&pressure_mpr_read_task, mpr_read_delay_ms, SUSPENDED);

  // Find the MPR trigger task number
  int8_t state_number = OS_get_task_number(&pressure_mpr_trigger_task);
  if (state_number >= 0) {
    pressure_state.pressure_trigger_task_number = (uint8_t) state_number;
    logger_msg_p("pressure", log_level_DEBUG, PSTR("Pressure trigger task id is %i"),
	       pressure_state.pressure_trigger_task_number);
  } else {
    logger_msg_p("pressure", log_level_ERROR, PSTR("Pressure trigger task id not found"));
    retval += -1;
  }

  // Find the MPR read task number
  state_number = OS_get_task_number(&pressure_mpr_read_task);
  if (state_number >= 0) {
    pressure_state.pressure_read_task_number = (uint8_t) state_number;
    logger_msg_p("pressure", log_level_DEBUG, PSTR("Pressure read task id is %i"),
	       pressure_state.pressure_read_task_number);
  } else {
    logger_msg_p("pressure", log_level_ERROR, PSTR("Pressure read task id not found"));
    retval += -1;
  }

  // Initialize exponential moving average value
  pressure_state.ema_alpha = 65535;
  
  return retval;
}


int8_t pressure_dac_set(uint8_t channel, uint16_t counts) {
  switch(channel) {
  case 1 :
    cs_ne_dac_mux();
    ltc2601_write( &cs_topaz_a_target, 0x3, counts);
    pressure_dac_counts[0] = counts;
    break;
  case 2 :
    cs_se_dac_mux();
    ltc2601_write( &cs_topaz_a_target, 0x3, counts);
    pressure_dac_counts[1] = counts;
    break;
  case 3 :
    cs_nw_dac_mux();
    ltc2601_write( &cs_topaz_a_target, 0x3, counts);
    pressure_dac_counts[2] = counts;
    break;
  case 4 :
    cs_sw_dac_mux();
    ltc2601_write( &cs_topaz_a_target, 0x3, counts);
    pressure_dac_counts[3] = counts;
    break;
  case 5 :
    cs_ne_dac_mux();
    ltc2601_write( &cs_topaz_b_target, 0x3, counts);
    pressure_dac_counts[4] = counts;
    break;
  case 6 :
    cs_se_dac_mux();
    ltc2601_write( &cs_topaz_b_target, 0x3, counts);
    pressure_dac_counts[5] = counts;
    break;
  case 7 :
    cs_nw_dac_mux();
    ltc2601_write( &cs_topaz_b_target, 0x3, counts);
    pressure_dac_counts[6] = counts;
    break;
  case 8 :
    cs_sw_dac_mux();
    ltc2601_write( &cs_topaz_b_target, 0x3, counts);
    pressure_dac_counts[7] = counts;
    break;
  }
  return 0;
}

void cmd_pressure_dac_set_1( command_arg_t *command_arg_ptr ) {
  if (topaz_is_connected('a')) {
      uint16_t setting = (command_arg_ptr -> uint16_arg);
      pressure_dac_set(1, setting);
      command_ack();
      return;
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_pressure_dac_set_2( command_arg_t *command_arg_ptr ) {
  if (topaz_is_connected('a')) {
    uint16_t setting = (command_arg_ptr -> uint16_arg);
    pressure_dac_set(2, setting);
    command_ack();
    return;
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_pressure_dac_set_3( command_arg_t *command_arg_ptr ) {
  if (topaz_is_connected('a')) {
    uint16_t setting = (command_arg_ptr -> uint16_arg);
    pressure_dac_set(3, setting);
    command_ack();
    return;
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_pressure_dac_set_4( command_arg_t *command_arg_ptr ) {
  if (topaz_is_connected('a')) {
    uint16_t setting = (command_arg_ptr -> uint16_arg);
    pressure_dac_set(4, setting);
    command_ack();
    return;
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_pressure_dac_set_5( command_arg_t *command_arg_ptr ) {
  if (topaz_is_connected('b')) {
    uint16_t setting = (command_arg_ptr -> uint16_arg);
    pressure_dac_set(5, setting);
    command_ack();
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_pressure_dac_set_6( command_arg_t *command_arg_ptr ) {
  if (topaz_is_connected('b')) {
    uint16_t setting = (command_arg_ptr -> uint16_arg);
    pressure_dac_set(6, setting);
    command_ack();
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_pressure_dac_set_7( command_arg_t *command_arg_ptr ) {
  if (topaz_is_connected('b')) {
      uint16_t setting = (command_arg_ptr -> uint16_arg);
      pressure_dac_set(7, setting);
      command_ack();
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_pressure_dac_set_8( command_arg_t *command_arg_ptr ) {
  if (topaz_is_connected('b')) {
    uint16_t setting = (command_arg_ptr -> uint16_arg);
    pressure_dac_set(8, setting);
    command_ack();
  } else {
    command_nack(NACK_COMMAND_FAILED);
    return;
  }
}

void cmd_pressure_dac_query( command_arg_t *command_arg_ptr ) {
  uint16_t channel = (command_arg_ptr -> uint16_arg);
  if (channel < 1 || channel > 8) {
    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
    return;
  }
  uint8_t index = channel - 1;
  usart_printf( USART_CHANNEL_COMMAND, "%u%s",
		pressure_dac_counts[index],
		LINE_TERMINATION_CHARACTERS );
  return;
}

int8_t pressure_mpr_inlet_trigger(uint8_t channel) {
  logger_msg_p("pressure", log_level_DEBUG, PSTR("Triggering channel %u inlet"),channel);
  switch(channel) {
  case 1 :
    cs_ne_mpr_mux();
    mpr_trigger( &cs_topaz_a_target );
    break;
  case 2 :
    cs_se_mpr_mux();
    mpr_trigger( &cs_topaz_a_target );
    break;
  case 3 :
    cs_nw_mpr_mux();
    mpr_trigger( &cs_topaz_a_target );
    break;
  case 4 :
    cs_sw_mpr_mux();
    mpr_trigger( &cs_topaz_a_target );
    break;
  case 5 :
    cs_ne_mpr_mux();
    mpr_trigger( &cs_topaz_b_target );
    break;
  case 6 :
    cs_se_mpr_mux();
    mpr_trigger( &cs_topaz_b_target );
    break;
  case 7 :
    cs_nw_mpr_mux();
    mpr_trigger( &cs_topaz_b_target );
    break;
  case 8 :
    cs_sw_mpr_mux();
    mpr_trigger( &cs_topaz_b_target );
    break;
  }
  return 0;
}

int8_t pressure_mpr_outlet_trigger(char board) {
  logger_msg_p("pressure", log_level_DEBUG, PSTR("Triggering Topaz %c outlet"),board);
  switch(board) {
  case 'a' :
    cs_outlet_mpr_mux();
    mpr_trigger( &cs_topaz_a_target );
    break;
  case 'b' :
    cs_outlet_mpr_mux();
    mpr_trigger( &cs_topaz_b_target );
    break;
  }
  return 0;
}

int8_t pressure_mpr_trigger_cycle( void ) {
  uint8_t retval = 0;
  if (topaz_is_connected('a')) {
    // Trigger Topaz A inlets
    for (uint8_t channel = 1; channel <= 4; channel++) {
      retval += pressure_mpr_inlet_trigger(channel);
    }
    // Trigger Topaz A outlet
    retval += pressure_mpr_outlet_trigger('a');

    // Add a delay while we switch between boards
    _delay_us(PRESSURE_READ_KLUDGE_DELAY_US);
  } else {
    logger_msg_p("pressure", log_level_DEBUG, PSTR("Skipping unconnected Topaz %c triggers"),'a');
  }

  if (topaz_is_connected('b')) {
    // Trigger Topaz B inlets
    for (uint8_t channel = 5; channel <= 8; channel++) {
      retval += pressure_mpr_inlet_trigger(channel);
    }
    // Trigger Topaz B outlet
    retval += pressure_mpr_outlet_trigger('b');
  } else {
    logger_msg_p("pressure", log_level_DEBUG, PSTR("Skipping unconnected Topaz %c triggers"),'b');
  }

  return retval;
}

int8_t pressure_mpr_inlet_read(uint8_t channel, uint32_t *data_ptr) {
  logger_msg_p("pressure", log_level_DEBUG, PSTR("Reading channel %u inlet"),channel);
  switch(channel) {
  case 1 :
    cs_ne_mpr_mux();
    mpr_read( &cs_topaz_a_target, data_ptr);
    break;
  case 2 :
    cs_se_mpr_mux();
    mpr_read( &cs_topaz_a_target, data_ptr);
    break;
  case 3 :
    cs_nw_mpr_mux();
    mpr_read( &cs_topaz_a_target, data_ptr);
    break;
  case 4 :
    cs_sw_mpr_mux();
    mpr_read( &cs_topaz_a_target, data_ptr);
    break;
  case 5 :
    cs_ne_mpr_mux();
    mpr_read( &cs_topaz_b_target, data_ptr);
    break;
  case 6 :
    cs_se_mpr_mux();
    mpr_read( &cs_topaz_b_target, data_ptr);
    break;
  case 7 :
    cs_nw_mpr_mux();
    mpr_read( &cs_topaz_b_target, data_ptr);
    break;
  case 8 :
    cs_sw_mpr_mux();
    mpr_read( &cs_topaz_b_target, data_ptr);
    break;

  }
  return 0;
}

int8_t pressure_mpr_outlet_read(char board, uint32_t *data_ptr) {
  logger_msg_p("pressure", log_level_DEBUG, PSTR("Reading Topaz %c outlet"),board);
  switch(board) {
  case 'a' :
    cs_outlet_mpr_mux();
    mpr_read( &cs_topaz_a_target, data_ptr);
    break;
  case 'b' :
    cs_outlet_mpr_mux();
    mpr_read( &cs_topaz_b_target, data_ptr);
    break;
  }
  return 0;
}

void pressure_mpr_trigger_task(void) {
  volatile int8_t retval = 0;  
  retval += pressure_mpr_trigger_cycle();

  // Schedule the read
  OS_SetTaskState(pressure_state.pressure_read_task_number, BLOCKED);
}

void pressure_mpr_read_task(void) {
  uint8_t index = 0;

  // Cancel the read
  OS_SetTaskState(pressure_state.pressure_read_task_number, SUSPENDED);

  if (topaz_is_connected('a')) {
    // Topaz A inlets
    for (uint8_t channel = 1; channel <= 4; channel++) {
      index = channel - 1;
      pressure_mpr_inlet_read(channel, &pressure_inlet_new_counts[index]);
      pressure_inlet_old_counts[index] = math_ema_ui32(pressure_inlet_new_counts[index],
						       pressure_inlet_old_counts[index],
						       pressure_state.ema_alpha);
      pressure_inlet_old_pascals[index] =
	pressure_convert_inlet_pascals(channel, pressure_inlet_old_counts[index]);
      // This delay has to be here to avoid SPI read errors
      //_delay_us(PRESSURE_READ_KLUDGE_DELAY_US);
    }

    // Topaz A outlet
    pressure_mpr_outlet_read('a', &pressure_outlet_new_counts[0]);
    pressure_outlet_old_counts[0] = math_ema_ui32(pressure_outlet_new_counts[0],
						  pressure_outlet_old_counts[0],
						  pressure_state.ema_alpha);
    pressure_outlet_old_pascals[0] =
      pressure_convert_outlet_pascals('a', pressure_outlet_old_counts[0]);

    // Add a delay while we switch between boards
    _delay_us(PRESSURE_READ_KLUDGE_DELAY_US);
  } else {
    logger_msg_p("pressure", log_level_DEBUG, PSTR("Skipping unconnected Topaz %c reads"),'a');
  }

  if (topaz_is_connected('b')) {
    // Topaz B inlets
    for (uint8_t channel = 5; channel <= 8; channel++) {
      index = channel - 1;
      pressure_mpr_inlet_read(channel, &pressure_inlet_new_counts[index]);
      pressure_inlet_old_counts[index] = math_ema_ui32(pressure_inlet_new_counts[index],
						       pressure_inlet_old_counts[index],
						       pressure_state.ema_alpha);
      pressure_inlet_old_pascals[index] =
	pressure_convert_inlet_pascals(channel, pressure_inlet_old_counts[index]);
    }

    // Topaz B outlet
    pressure_mpr_outlet_read('b', &pressure_outlet_new_counts[1]);
    pressure_outlet_old_counts[1] = math_ema_ui32(pressure_outlet_new_counts[1],
						  pressure_outlet_old_counts[1],
						  pressure_state.ema_alpha);
    pressure_outlet_old_pascals[1] =
      pressure_convert_outlet_pascals('b', pressure_outlet_old_counts[1]);
  } else {
    logger_msg_p("pressure", log_level_DEBUG, PSTR("Skipping unconnected Topaz %c reads"),'b');
  }

}

void cmd_out_prs_raw_q( command_arg_t *command_arg_ptr ) {
  uint16_t board_number = (command_arg_ptr -> uint16_arg);
  switch(board_number) {
  case 1 :
    usart_printf( USART_CHANNEL_COMMAND, "%lu%s",
	       pressure_outlet_old_counts[0],
		 LINE_TERMINATION_CHARACTERS );
    break;
  case 2 :
    usart_printf( USART_CHANNEL_COMMAND, "%lu%s",
		  pressure_outlet_old_counts[1],
		  LINE_TERMINATION_CHARACTERS );
    break;
  default :
    // This is an out of range input
    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
  }
}

void cmd_out_prs_pas_q( command_arg_t *command_arg_ptr ) {
  uint16_t board_number = (command_arg_ptr -> uint16_arg);
  switch(board_number) {
  case 1 :
    usart_printf( USART_CHANNEL_COMMAND, "%lu%s",
		  pressure_outlet_old_pascals[0],
		  LINE_TERMINATION_CHARACTERS );
    break;
  case 2 :
    usart_printf( USART_CHANNEL_COMMAND, "%lu%s",
		  pressure_outlet_old_pascals[1],
		  LINE_TERMINATION_CHARACTERS );
    break;
  default :
    // This is an out of range input
    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
  }
}

void cmd_in_prs_raw_q( command_arg_t *command_arg_ptr ) {
  uint16_t channel = (command_arg_ptr -> uint16_arg);
  if (channel < 1 || channel > 8) {
    // Argument is out of range
    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
    return;
  }
  uint8_t index = channel - 1;
  usart_printf( USART_CHANNEL_COMMAND, "%lu%s",
		pressure_inlet_old_counts[index],
		LINE_TERMINATION_CHARACTERS );
}

void cmd_in_prs_pas_q( command_arg_t *command_arg_ptr ) {
  uint16_t channel = (command_arg_ptr -> uint16_arg);
  if (channel < 1 || channel > 8) {
    // Argument is out of range
    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
    return;
  }
  uint8_t index = channel - 1;
  usart_printf( USART_CHANNEL_COMMAND, "%lu%s",
		pressure_inlet_old_pascals[index],
		LINE_TERMINATION_CHARACTERS );
}

void cmd_pressure_set_ema_alpha( command_arg_t *command_arg_ptr ) {
  uint16_t alpha = (command_arg_ptr -> uint16_arg);
  pressure_state.ema_alpha = alpha;
  command_ack();
  return;
}

void cmd_pressure_get_ema_alpha( command_arg_t *command_arg_ptr ){
  usart_printf(USART_CHANNEL_COMMAND, "%u%s",
	       pressure_state.ema_alpha,
	       LINE_TERMINATION_CHARACTERS);
}

uint32_t pressure_convert_outlet_pascals( char board, uint32_t raw ) {
  uint32_t nmin = 0;
  uint32_t nmax = 0;
  uint32_t pmax_pascal = 0;
  switch(board) {
  case 'a' :
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  case 'b' :
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  default:
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  }
  uint64_t pascals = 0;
  pascals = (uint64_t) (raw - nmin) * pmax_pascal / (nmax - nmin);
  logger_msg_p("pressure", log_level_DEBUG,
	       PSTR("Converted pressure is %lu Pascals"),
	       pascals);
  return (uint32_t) pascals;
}

uint32_t pressure_convert_inlet_pascals( uint8_t channel, uint32_t raw ) {
  uint32_t nmin = 0;
  uint32_t nmax = 0;
  uint32_t pmax_pascal = 0;
  switch(channel) {
  case 1 :
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  case 2 :
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  case 3 :
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  case 4 :
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  case 5 :
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  case 6 :
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  case 7 :
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  case 8 :
    nmin = MPR_NMIN;
    nmax = MPR_NMAX;
    pmax_pascal = MPR_PMAX_PASCAL;
  }
  uint64_t pascals = 0;
  pascals = (uint64_t) (raw - nmin) * pmax_pascal / (nmax - nmin);
  logger_msg_p("pressure", log_level_DEBUG,
	       PSTR("Converted pressure is %lu Pascals"),
	       pascals);
  return (uint32_t) pascals;
}
