/*
 * FILE:
 *   sgdbrCurrentSource.h
 *
 * DESCRIPTION:
 *   Routines for handling SGDBR laser current source
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   6-Feb-2018  sze  Initial version.
 *   27-Oct-2022 sze  Four laser version.
 *
 *  Copyright (c) 2018 Picarro, Inc. All rights reserved
 */
#ifndef _SGDBR_CURRENT_SOURCE_H_
#define _SGDBR_CURRENT_SOURCE_H_

typedef struct SGDBR_CNTRL
{
    char name;                   // 'A', 'B', 'C' or 'D' depending on laser
    // References to registers
    unsigned int *state_;        // Controller state
    float *front_mirror_;        // Manual front mirror current setting
    float *back_mirror_;         // Manual back mirror current setting
    float *gain_;                // Manual gain current setting
    float *soa_;                 // Manual SOA current setting
    float *coarse_phase_;        // Manual coarse phase current setting
    float *fine_phase_;          // Manual fine phase current setting
    float *chirp_;               // Manual chirp current setting
    float *spare_;               // Manual spare DAC setting
    int *rd_config_;             // Manual ring down configuration
    float *front_step_;          // Step in front mirror current for pulse generator
    float *back_step_;           // Step in back mirror current for pulse generator
    float *phase_step_;           // Step in coarse phase current for pulse generator
    float *soa_step_;             // Step in SOA current for pulse generator
    unsigned int *semi_period_;   // Semi-period for pulse generator mode
    float *laser_temp_;          // Laser temperature
    float *laser_temp_setpoint_; // Laser temperature setpoint
    float *laser_temp_window_;    // Temperature window outside of which to turn off currents
    float *pulse_temp_amplitude_; // Amplitude of temperature fluctuations due to pulse generator
    float *pulse_temp_ptp_;       // Peak-to-peak value of temperature fluctuations due to pulse generator 

    float front_mirror_old; // Old front mirror current setting
    float back_mirror_old;  // Old back mirror current setting
    float gain_old;         // Old gain current setting
    float soa_old;          // Old SOA current setting
    float coarse_phase_old; // Old coarse phase current setting
    float fine_phase_old;   // Old fine phase current setting
    float chirp_old;        // Old chirp current setting
    float spare_old;        // Old spare DAC setting
    int rd_config_old;      // Old rd_config setting
    int pulse_gen_counter;  // Counter within pulse generator period
    float temp_peak, temp_valley;  // Most recent local extrema of temperature
    float temp_history[3];   // Most recent temperature data

    // Stream indices   
    unsigned int stream_pulse_temp_ptp;

    // FPGA register indices
    unsigned int fpga_csr;
    unsigned int fpga_sck_divisor;
    unsigned int fpga_num_of_clock_pulses;
    unsigned int fpga_mosi_data;
    unsigned int fpga_miso_data;
} SgdbrCntrl;

int sgdbrCntrlInit(int laserIndex);
int sgdbrCntrlStep(int laserIndex);
void sgdbrProgramFpga(int laserIndex);
double sgdbrReadThermistorAdc(int laserIndex);
void setup_all_gain_and_soa_currents(void);

#endif /* _SGDBR_CURRENT_SOURCE_H_ */
