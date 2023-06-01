/*
 * FILE:
 *   soa_cntrl.h
 *
 * DESCRIPTION:
 *   SOA controller routines for new SOA board
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   19-Jan-2021  sze  Initial version.
 *
 *  Copyright (c) 2021 Picarro, Inc. All rights reserved
 */
#ifndef _SOA_CNTRL_H_
#define _SOA_CNTRL_H_

#include "i2c_dsp.h"

typedef struct SOA_CNTRL
{
    // References to registers
    float *current_setpoint_;   // Minimum sweep value
    float *temperature_setpoint_;   // Maximum sweep value
    float *tec_current_monitor_;   // Sweep increment
    float *tec_voltage_monitor_;   // Maximum external temperature
    float *temperature_monitor_;  // Pseudo-random binary sequence amplitude
    unsigned int *soa_enable_mask_;  // Mask to enable SOA
    //
    int soa_index;
    int prev_soa_enable_mask;
    int prev_dset;
    int prev_tset;
    int monitor_counter;
    int i2c_current_ident;
    int i2c_control_ident;
    int i2c_tec_ident;
    int i2c_monitor_ident;
    int a_or_d_loop;
} SoaCntrl;
int soa_cntrl_soa1_init(int i2c_current_ident, int i2c_control_ident, int i2c_tec_ident, int i2c_monitor_ident);
int soa_cntrl_soa1_step(void);
int soa_cntrl_soa2_init(int i2c_current_ident, int i2c_control_ident, int i2c_tec_ident, int i2c_monitor_ident);
int soa_cntrl_soa2_step(void);
int soa_cntrl_soa3_init(int i2c_current_ident, int i2c_control_ident, int i2c_tec_ident, int i2c_monitor_ident);
int soa_cntrl_soa3_step(void);
int soa_cntrl_soa4_init(int i2c_current_ident, int i2c_control_ident, int i2c_tec_ident, int i2c_monitor_ident);
int soa_cntrl_soa4_step(void);

#endif /* _SOA_CNTRL_H_ */
