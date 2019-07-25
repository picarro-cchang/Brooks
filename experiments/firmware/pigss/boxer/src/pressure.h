// Pressure control module

#ifndef PRESSURE_H
#define PRESSURE_H

#include <stdbool.h>

#define PRESSURE_DAC_REFERENCE_VOLTS 3.0

// Alpha value for pressure moving average
#define PRESSURE_EMA_ALPHA 65535

// Set the voltage output from one of the pressure-control DACs
//
// Arguments:
//   channel -- 1-8
//   counts -- counts sent to the DAC
int8_t pressure_dac_set(uint8_t channel, uint16_t counts);

// Trigger one of the inlet pressure sensors
int8_t pressure_mpr_inlet_trigger(uint8_t channel);

// Trigger one of the outlet pressure sensors
int8_t pressure_mpr_outlet_trigger(char board);

// Trigger all of the pressure sensors
int8_t pressure_mpr_trigger_cycle( void );

// Read one of the inlet pressure sensors
int8_t pressure_mpr_inlet_read(uint8_t channel, uint32_t *data_ptr);

// Read one of the outlet pressure sensors
int8_t pressure_mpr_outlet_read(char board, uint32_t *data_ptr);

// Task to trigger all pressure sensors and schedule the read
void pressure_mpr_trigger_task(void);

// Task to read all pressure sensors and cancel itself
void pressure_mpr_read_task(void);

// Command to return the averaged counts from outlet pressure sensors
void cmd_out_prs_raw_q( command_arg_t *command_arg_ptr );

// Command to return the averaged pressure from an outlet sensor in
// Pascals
void cmd_out_prs_pas_q( command_arg_t *command_arg_ptr );

// Return a calibrated pressure in Pascals
//
// Arguments:
//   raw -- Raw sensor counts
uint32_t pressure_convert_pascals( uint32_t raw );

#endif
