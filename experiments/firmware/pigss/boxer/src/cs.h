#ifndef CS_H
#define CS_H

void cs_init(void);

// Set the state of the CS line for Topaz A and B shift registers
//
// Arguments:
//   state -- 1 for CS high, 0 for CS low
int8_t cs_manifold_a_sr(uint8_t state);
int8_t cs_manifold_b_sr(uint8_t state);

// Set the state of the target CS line.  This CS is multiplexed to
// handle all DACs and pressure sensors.
//
// Arguments:
//   state -- 1 for CS high, 0 for CS low
void cs_topaz_a_target(uint8_t state);
void cs_topaz_b_target(uint8_t state);


//******************** Proportional valve DACs *********************//

// Each Topaz board has 4 quadrants, which ultimately get mapped to
// channels.  The north position is set by the 4-pin MTA100 connector.

// Set the cs mux position to point to the NW quadrant proportional
// valve DAC
void cs_nw_dac_mux(void);

// Set the cs mux position to point to the NW quadrant proportional
// valve DAC
void cs_sw_dac_mux(void);

// Set the cs mux position to point to the SE quadrant proportional
// valve DAC
void cs_se_dac_mux(void);

// Set the cs mux position to point to the NE quadrant proportional
// valve DAC
void cs_ne_dac_mux(void);

//************************ Pressure sensors ************************//

// Set the cs mux position to point to the channel 1 pressure sensor
void cs_ch1_mpr_mux(void);

// Set the cs mux position to point to the channel 2 pressure sensor
void cs_ch2_mpr_mux(void);

// Set the cs mux position to point to the channel 3 pressure sensor
void cs_ch3_mpr_mux(void);

// Set the cs mux position to point to the channel 4 pressure sensor
void cs_ch4_mpr_mux(void);

// Set the cs mux position to point to the Topaz A outlet
void cs_outlet_a_mpr_mux(void);

// Set the cs mux position to point to the Topaz B outlet
void cs_outlet_b_mpr_mux(void);



#endif // End the include guard
