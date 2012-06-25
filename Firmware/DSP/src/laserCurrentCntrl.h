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
    // FPGA register indices
    unsigned int fpga_control;
    unsigned int fpga_coarse;
    unsigned int fpga_fine;
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
