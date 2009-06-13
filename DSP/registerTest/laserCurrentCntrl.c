/*
 * FILE:
 *   laserCurrentCntrl.c
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
#include "interface.h"
#include "registers.h"
#include "laserCurrentCntrl.h"
#include "i2c_dsp.h"
#include "ltc2451.h"
#include "dspAutogen.h"
#include "fpga.h"
#include <math.h>

#define state             (*(c->state_))
#define manualCoarse      (*(c->manual_coarse_))
#define manualFine        (*(c->manual_fine_))
#define swpMin            (*(c->swpMin_))
#define swpMax            (*(c->swpMax_))
#define swpInc            (*(c->swpInc_))
#define coarse            (c->coarse)
#define swpDir            (c->swpDir)

int laserCurrentCntrlStep(LaserCurrentCntrl *c)
{
    float fine;
    // Step the laser current controller
    switch (state)
    {
    case LASER_CURRENT_CNTRL_DisabledState:
        coarse = 0;
        fine = 0;
        break;
    case LASER_CURRENT_CNTRL_EnabledState:
        coarse = manualCoarse;
        fine = 32768.0;
        break;
    case LASER_CURRENT_CNTRL_ManualState:
        coarse = manualCoarse;
        fine = manualFine;
        break;
    case LASER_CURRENT_CNTRL_SweepingState:
        coarse += swpDir * swpInc;
        if (coarse >= swpMax)
        {
            coarse = swpMax;
            swpDir = -1;
        }
        else if (coarse <= swpMin)
        {
            coarse = swpMin;
            swpDir = 1;
        }
        fine = 32768.0;
        break;
    }
    writeFPGA(c->fpga_coarse,(unsigned short)coarse);
    writeFPGA(c->fpga_fine,  (unsigned short)fine);
    return STATUS_OK;
}

#undef state
#undef manualCoarse
#undef manualFine
#undef coarse
#undef swpMin
#undef swpMax
#undef swpInc
#undef swpDir

LaserCurrentCntrl currentCntrlLaser1;
LaserCurrentCntrl currentCntrlLaser2;
LaserCurrentCntrl currentCntrlLaser3;
LaserCurrentCntrl currentCntrlLaser4;

int currentCntrlLaser1Init(void)
{
    LaserCurrentCntrl *c = &currentCntrlLaser1;
    c->state_ = (unsigned int *)registerAddr(LASER1_CURRENT_CNTRL_STATE_REGISTER);
    c->manual_coarse_ = (float *)registerAddr(LASER1_MANUAL_COARSE_CURRENT_REGISTER);
    c->manual_fine_ = (float *)registerAddr(LASER1_MANUAL_FINE_CURRENT_REGISTER);
    c->swpMin_ = (float *)registerAddr(LASER1_CURRENT_SWEEP_MIN_REGISTER);
    c->swpMax_ = (float *)registerAddr(LASER1_CURRENT_SWEEP_MAX_REGISTER);
    c->swpInc_ = (float *)registerAddr(LASER1_CURRENT_SWEEP_INCR_REGISTER);
    c->coarse = 0.0;
    c->swpDir    = 1;
    *(c->state_)  = LASER_CURRENT_CNTRL_DisabledState;
    c->fpga_coarse = FPGA_INJECT + INJECT_LASER1_COARSE_CURRENT;
    c->fpga_fine   = FPGA_INJECT + INJECT_LASER1_FINE_CURRENT;
    return STATUS_OK;
}

int currentCntrlLaser1Step(void)
{
    int status = laserCurrentCntrlStep(&currentCntrlLaser1);
    *(float *)registerAddr(LASER1_CURRENT_MONITOR_REGISTER) =
        currentCntrlLaser1.coarse;
    return status;
}

int read_laser_current_adc(int laserNum)
// Read laser current ADC for specified laser. laserNum is in the range 1-4
{
    unsigned int chan[5] = {0,0,1,2,3};
    int result, loops;

    setI2C0Mux(chan[laserNum]);
    for (loops=0;loops<1000;loops++);
    result = ltc2451_read();
    return result;
}
