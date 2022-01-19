/*
 * FILE:
 *   laserCurrentCntrl.h
 *
 * DESCRIPTION:
 *   Laser current controller routines
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   21-Apr-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef _LASER_CURRENT_CNTRL_H_
#define _LASER_CURRENT_CNTRL_H_

typedef struct LASER_CURRENT_CNTRL
{
    // References to registers
    unsigned int *state_;    // Controller state
    float *manual_coarse_;   // Manual control of coarse current DAC
    float *manual_fine_;     // Manual control of fine current DAC
    float *swpMin_;   // Minimum sweep value
    float *swpMax_;   // Maximum sweep value
    float *swpInc_;   // Sweep increment
    float *extra_coarse_scale_; // Scale factor for coarse current when applying extra current
    float *extra_fine_scale_; // Scale factor for fine current when applying extra current
    int *extra_offset_; // Offset when applying extra current
    float *laser_temp_; // Temperature of laser
    float *laser_temp_setpoint_; // Temperature setpoint of laser
    float *laser_temp_window_; // Temperature window outside of which to turn off currents
    // FPGA register indices
    unsigned int fpga_control;
    unsigned int fpga_coarse;
    unsigned int fpga_fine;
    unsigned int fpga_extra_coarse_scale;
    unsigned int fpga_extra_fine_scale;
    unsigned int fpga_extra_offset;
    // Local variables for controller
    unsigned int laserNum; // Laser number (1-origin)
    float coarse;
    int swpDir;
} LaserCurrentCntrl;

int laserCurrentCntrlStep(LaserCurrentCntrl *c);

int currentCntrlLaser1Init(void);
int currentCntrlLaser1Step(void);
int currentCntrlLaser2Init(void);
int currentCntrlLaser2Step(void);
int currentCntrlLaser3Init(void);
int currentCntrlLaser3Step(void);
int currentCntrlLaser4Init(void);
int currentCntrlLaser4Step(void);

int read_laser_current_adc(int laserNum);

#endif /* _LASER_CURRENT_CNTRL_H_ */
