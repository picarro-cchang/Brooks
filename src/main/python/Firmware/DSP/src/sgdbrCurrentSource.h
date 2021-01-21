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
 *
 *  Copyright (c) 2018 Picarro, Inc. All rights reserved
 */
#ifndef _SGDBR_CURRENT_SOURCE_H_
#define _SGDBR_CURRENT_SOURCE_H_

typedef struct SGDBR_CNTRL
{
    char name;                   // 'A' or 'B' depending on laser
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
    float *laser_temp_;          // Laser temperature
    float *laser_temp_setpoint_; // Laser temperature setpoint

    float front_mirror_old; // Old front mirror current setting
    float back_mirror_old;  // Old back mirror current setting
    float gain_old;         // Old gain current setting
    float soa_old;          // Old SOA current setting
    float coarse_phase_old; // Old coarse phase current setting
    float fine_phase_old;   // Old fine phase current setting
    float chirp_old;        // Old chirp current setting
    float spare_old;        // Old spare DAC setting
    int rd_config_old;      // Old rd_config setting

    // FPGA register indices
    unsigned int fpga_csr;
    unsigned int fpga_sck_divisor;
    unsigned int fpga_num_of_clock_pulses;
    unsigned int fpga_mosi_data;
    unsigned int fpga_miso_data;
} SgdbrCntrl;

int sgdbrACntrlInit(void);
int sgdbrBCntrlInit(void);
int sgdbrACntrlStep(void);
int sgdbrBCntrlStep(void);
void sgdbrAProgramFpga(void);
void sgdbrBProgramFpga(void);
double sgdbrAReadThermistorAdc(void);
double sgdbrBReadThermistorAdc(void);
void setup_all_gain_and_soa_currents(void);

#endif /* _SGDBR_CURRENT_SOURCE_H_ */
