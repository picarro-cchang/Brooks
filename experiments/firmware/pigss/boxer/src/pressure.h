// Pressure control module

#ifndef PRESSURE_H
#define PRESSURE_H

#include <stdbool.h>

#define PRESSURE_DAC_REFERENCE_VOLTS 3.0

// Alpha value for pressure moving average
#define PRESSURE_EMA_ALPHA 65535

// Setpoint for bypass DACs when channels are disabled
#define PRESSURE_DAC_INACTIVE_COUNTS 17134

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

// Command to return the averaged counts from inlet pressure sensors
void cmd_in_prs_raw_q( command_arg_t *command_arg_ptr );

// Command to return the averaged pressure from an outlet sensor in
// Pascals
void cmd_out_prs_pas_q( command_arg_t *command_arg_ptr );

// Command to return the averaged pressure from an inlet sensor in
// Pascals
void cmd_in_prs_pas_q( command_arg_t *command_arg_ptr );

// Return a calibrated pressure in Pascals for outlet sensors.
//
// This can't be an all-sensor function, since calibration constants
// are unique to each sensor.  And outlet sensors are called A and B,
// where inlet sensors are 1-8.
//
// Arguments:
//   board -- Board A or B
//   raw -- Raw sensor counts
uint32_t pressure_convert_outlet_pascals( char board, uint32_t raw );

// Return a calibrated pressure in Pascals for inlet sensors.
//
// This can't be an all-sensor function, since calibration constants
// are unique to each sensor.  And outlet sensors are called A and B,
// where inlet sensors are 1-8.
//
// Arguments:
//   channel -- 1-8
//   raw -- Raw sensor counts
uint32_t pressure_convert_inlet_pascals( uint8_t channel, uint32_t raw );

// Set the bypass proportional valve DAC for channel 1
void cmd_pressure_dac_set_1( command_arg_t *command_arg_ptr );

// Set the bypass proportional valve DAC for channel 2
void cmd_pressure_dac_set_2( command_arg_t *command_arg_ptr );

// Set the bypass proportional valve DAC for channel 3
void cmd_pressure_dac_set_3( command_arg_t *command_arg_ptr );

// Set the bypass proportional valve DAC for channel 4
void cmd_pressure_dac_set_4( command_arg_t *command_arg_ptr );

// Set the bypass proportional valve DAC for channel 5
void cmd_pressure_dac_set_5( command_arg_t *command_arg_ptr );

// Set the bypass proportional valve DAC for channel 6
void cmd_pressure_dac_set_6( command_arg_t *command_arg_ptr );

// Set the bypass proportional valve DAC for channel 7
void cmd_pressure_dac_set_7( command_arg_t *command_arg_ptr );

// Set the bypass proportional valve DAC for channel 8
void cmd_pressure_dac_set_8( command_arg_t *command_arg_ptr );

// Query one of the proportional valve DAC values
void cmd_pressure_dac_query( command_arg_t *command_arg_ptr );

#endif
