// Pressure control module

#ifndef PRESSURE_H
#define PRESSURE_H

#include <stdbool.h>

#define PRESSURE_DAC_REFERENCE_VOLTS 3.0

// Set the voltage output from one of the pressure-control DACs
//
// Arguments:
//   channel -- 1-8
//   counts -- counts sent to the DAC
int8_t pressure_dac_set(uint8_t channel, uint16_t counts);

// Trigger one of the pressure sensors
int8_t pressure_mpr_trigger(uint8_t channel);

// Read one of the pressure sensors
int8_t pressure_mpr_read(uint8_t channel, uint32_t *data_ptr);


#endif
