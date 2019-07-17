// Pressure control module

#ifndef PRESSURE_H
#define PRESSURE_H

#include <stdbool.h>

#define PRESSURE_DAC_REFERENCE_VOLTS 3.0

// Set the voltage output from one of the pressure-control DACs
//
// Arguments:
//   channel -- 1-8
//   voltage -- floating-point voltage
int8_t pressure_dac_set(uint8_t channel, float voltage);


#endif
