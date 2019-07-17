#ifndef CS_H
#define CS_H

void cs_init(void);

void cs_manifold_a_sr(uint8_t);

void cs_manifold_b_sr(uint8_t);

// Set the state of the target CS line.  This CS is multiplexed to
// handle all DACs and pressure sensors.
//
// Arguments:
//   state -- 1 for CS high, 0 for CS low
void cs_topaz_a_target(uint8_t state);

// Set the cs mux position to point to the channel 1 proportional
// valve DAC
void cs_ch1_dac_mux(void);

// Set the cs mux position to point to the channel 2 proportional
// valve DAC
void cs_ch2_dac_mux(void);

// Set the cs mux position to point to the channel 3 proportional
// valve DAC
void cs_ch3_dac_mux(void);

// Set the cs mux position to point to the channel 4 proportional
// valve DAC
void cs_ch4_dac_mux(void);

#endif // End the include guard
