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
#include "dspAutogen.h"
#include "i2c_dsp.h"
#include "ltc2451.h"
#include "fpga.h"
#include <math.h>

#define min(x,y) ((x)<(y) ? (x):(y))
#define state             (*(c->state_))
#define manualCoarse      (*(c->manual_coarse_))
#define manualFine        (*(c->manual_fine_))
#define coarse            (c->coarse)
#define swpMin            (*(c->swpMin_))
#define swpMax            (*(c->swpMax_))
#define swpInc            (*(c->swpInc_))
#define swpDir            (c->swpDir)
#define extraCoarseScale  (*(c->extra_coarse_scale_))
#define extraFineScale    (*(c->extra_fine_scale_))
#define extraOffset       (*(c->extra_offset_))
#define laserTemp         (*(c->laser_temp_))
#define laserTempSetpoint (*(c->laser_temp_setpoint_))
#define laserTempWindow   (*(c->laser_temp_window_))

int laserCurrentCntrlStep(LaserCurrentCntrl *c)
/*
 * When the controller is in the Disabled state, the current regulator of
 *  the laser is disabled, and the shorting switch is turned on
 *
 * When the controller is in the Automatic state, the current regulator of
 *  the laser is enabled, but the shorting switch is turned off. This does
 *  NOT place the FPGA INJECT block in the automatic state, since this is
 *  done only when ringdowns are to be collected, and at that time, another
 *  process puts ALL the laser current controllers in the automatic
 *  state and then switches the FPGA INJECT block to the automatic state
 *
 * When ANY controller is in the Manual state, the FPGA INJECT block is
 *  placed in the manual state. The current regulator of the laser is
 *  enabled and the shorting switch is turned off
 *
 * When ANY controller is in the Sweeping state,  the FPGA INJECT block is
 *  placed in the manual state. The current regulator of the laser is
 *  enabled and the shorting switch is turned off. The laser current
 *  of the selected laser is swept between the chosen limits
 */
{
    float fine;
    // Step the laser current controller
    unsigned int current_enable_mask = 1<<(INJECT_CONTROL_LASER_CURRENT_ENABLE_B+(c->laserNum-1));
    unsigned int laser_enable_mask = 1<<(INJECT_CONTROL_MANUAL_LASER_ENABLE_B+(c->laserNum-1));
    unsigned int automatic_mask = 1<<INJECT_CONTROL_MODE_B;

    switch (state)
    {
    case LASER_CURRENT_CNTRL_DisabledState:
        coarse = 0;
        fine = 0;
        changeInMaskFPGA(c->fpga_control,
                         current_enable_mask | laser_enable_mask,
                         0);
        break;
    case LASER_CURRENT_CNTRL_AutomaticState:
        coarse = manualCoarse;
        fine = 32768.0;
        changeInMaskFPGA(c->fpga_control,
                         current_enable_mask | laser_enable_mask,
                         current_enable_mask);
        break;
    case LASER_CURRENT_CNTRL_ManualState:
        coarse = manualCoarse;
        fine = manualFine;
        changeInMaskFPGA(c->fpga_control,
                         current_enable_mask | laser_enable_mask | automatic_mask,
                         current_enable_mask | laser_enable_mask );
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
        fine = manualFine;
        changeInMaskFPGA(c->fpga_control,
                         current_enable_mask | laser_enable_mask | automatic_mask,
                         current_enable_mask | laser_enable_mask );
        break;
    }
    // Only allow laser current once laser temperature is in range of setpoint
    if ((laserTempSetpoint - laserTemp) <= laserTempWindow && (laserTempSetpoint - laserTemp) >= -laserTempWindow) {
        writeFPGA(c->fpga_coarse, (unsigned short)coarse);
        writeFPGA(c->fpga_fine, (unsigned short)fine);
    }
    else {
        writeFPGA(c->fpga_coarse, 0);
        writeFPGA(c->fpga_fine, 0);        
    }

    writeFPGA(c->fpga_extra_coarse_scale, (unsigned short)min(65535.0, 32768.0*extraCoarseScale));
    writeFPGA(c->fpga_extra_fine_scale, (unsigned short)min(65535.0, 65536.0*extraFineScale));
    writeFPGA(c->fpga_extra_offset, (short)extraOffset);
    
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
#undef extraCoarseScale
#undef extraFineScale
#undef extraOffset

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
    c->extra_coarse_scale_ =  (float *)registerAddr(LASER1_EXTRA_COARSE_SCALE_REGISTER);
    c->extra_fine_scale_ =  (float *)registerAddr(LASER1_EXTRA_FINE_SCALE_REGISTER);
    c->extra_offset_ =  (int *)registerAddr(LASER1_EXTRA_OFFSET_REGISTER);
    c->laser_temp_window_ = (float *)registerAddr(TEMPERATURE_WINDOW_FOR_LASER_SHUTDOWN_REGISTER);
    c->coarse = 0.0;
    c->swpDir    = 1;
    *(c->state_)  = LASER_CURRENT_CNTRL_DisabledState;
    c->fpga_coarse = FPGA_INJECT + INJECT_LASER1_COARSE_CURRENT;
    c->fpga_fine   = FPGA_INJECT + INJECT_LASER1_FINE_CURRENT;
    c->fpga_control = FPGA_INJECT + INJECT_CONTROL;
    c->fpga_extra_coarse_scale = FPGA_INJECT + INJECT_LASER1_EXTRA_COARSE_SCALE;
    c->fpga_extra_fine_scale = FPGA_INJECT + INJECT_LASER1_EXTRA_FINE_SCALE;
    c->fpga_extra_offset = FPGA_INJECT + INJECT_LASER1_EXTRA_OFFSET;
    c->laserNum = 1;
    c->laser_temp_ = (float *)registerAddr(LASER1_TEMPERATURE_REGISTER);
    c->laser_temp_setpoint_ = (float *)registerAddr(LASER1_TEMP_CNTRL_SETPOINT_REGISTER);
    return STATUS_OK;
}

int currentCntrlLaser1Step(void)
{
    return laserCurrentCntrlStep(&currentCntrlLaser1);
}

int currentCntrlLaser2Init(void)
{
    LaserCurrentCntrl *c = &currentCntrlLaser2;
    c->state_ = (unsigned int *)registerAddr(LASER2_CURRENT_CNTRL_STATE_REGISTER);
    c->manual_coarse_ = (float *)registerAddr(LASER2_MANUAL_COARSE_CURRENT_REGISTER);
    c->manual_fine_ = (float *)registerAddr(LASER2_MANUAL_FINE_CURRENT_REGISTER);
    c->swpMin_ = (float *)registerAddr(LASER2_CURRENT_SWEEP_MIN_REGISTER);
    c->swpMax_ = (float *)registerAddr(LASER2_CURRENT_SWEEP_MAX_REGISTER);
    c->swpInc_ = (float *)registerAddr(LASER2_CURRENT_SWEEP_INCR_REGISTER);
    c->extra_coarse_scale_ =  (float *)registerAddr(LASER2_EXTRA_COARSE_SCALE_REGISTER);
    c->extra_fine_scale_ =  (float *)registerAddr(LASER2_EXTRA_FINE_SCALE_REGISTER);
    c->extra_offset_ =  (int *)registerAddr(LASER2_EXTRA_OFFSET_REGISTER);
    c->laser_temp_window_ = (float *)registerAddr(TEMPERATURE_WINDOW_FOR_LASER_SHUTDOWN_REGISTER);
    c->coarse = 0.0;
    c->swpDir    = 1;
    *(c->state_)  = LASER_CURRENT_CNTRL_DisabledState;
    c->fpga_coarse = FPGA_INJECT + INJECT_LASER2_COARSE_CURRENT;
    c->fpga_fine   = FPGA_INJECT + INJECT_LASER2_FINE_CURRENT;
    c->fpga_control = FPGA_INJECT + INJECT_CONTROL;
    c->fpga_extra_coarse_scale = FPGA_INJECT + INJECT_LASER2_EXTRA_COARSE_SCALE;
    c->fpga_extra_fine_scale = FPGA_INJECT + INJECT_LASER2_EXTRA_FINE_SCALE;
    c->fpga_extra_offset = FPGA_INJECT + INJECT_LASER2_EXTRA_OFFSET;
    c->laserNum = 2;
    c->laser_temp_ = (float *)registerAddr(LASER2_TEMPERATURE_REGISTER);
    c->laser_temp_setpoint_ = (float *)registerAddr(LASER2_TEMP_CNTRL_SETPOINT_REGISTER);
    return STATUS_OK;
}

int currentCntrlLaser2Step(void)
{
    return laserCurrentCntrlStep(&currentCntrlLaser2);
}

int currentCntrlLaser3Init(void)
{
    LaserCurrentCntrl *c = &currentCntrlLaser3;
    c->state_ = (unsigned int *)registerAddr(LASER3_CURRENT_CNTRL_STATE_REGISTER);
    c->manual_coarse_ = (float *)registerAddr(LASER3_MANUAL_COARSE_CURRENT_REGISTER);
    c->manual_fine_ = (float *)registerAddr(LASER3_MANUAL_FINE_CURRENT_REGISTER);
    c->swpMin_ = (float *)registerAddr(LASER3_CURRENT_SWEEP_MIN_REGISTER);
    c->swpMax_ = (float *)registerAddr(LASER3_CURRENT_SWEEP_MAX_REGISTER);
    c->swpInc_ = (float *)registerAddr(LASER3_CURRENT_SWEEP_INCR_REGISTER);
    c->extra_coarse_scale_ =  (float *)registerAddr(LASER3_EXTRA_COARSE_SCALE_REGISTER);
    c->extra_fine_scale_ =  (float *)registerAddr(LASER3_EXTRA_FINE_SCALE_REGISTER);
    c->extra_offset_ =  (int *)registerAddr(LASER3_EXTRA_OFFSET_REGISTER);
    c->laser_temp_window_ = (float *)registerAddr(TEMPERATURE_WINDOW_FOR_LASER_SHUTDOWN_REGISTER);
    c->coarse = 0.0;
    c->swpDir    = 1;
    *(c->state_)  = LASER_CURRENT_CNTRL_DisabledState;
    c->fpga_coarse = FPGA_INJECT + INJECT_LASER3_COARSE_CURRENT;
    c->fpga_fine   = FPGA_INJECT + INJECT_LASER3_FINE_CURRENT;
    c->fpga_control = FPGA_INJECT + INJECT_CONTROL;
    c->fpga_extra_coarse_scale = FPGA_INJECT + INJECT_LASER3_EXTRA_COARSE_SCALE;
    c->fpga_extra_fine_scale = FPGA_INJECT + INJECT_LASER3_EXTRA_FINE_SCALE;
    c->fpga_extra_offset = FPGA_INJECT + INJECT_LASER3_EXTRA_OFFSET;
    c->laserNum = 3;
    c->laser_temp_ = (float *)registerAddr(LASER3_TEMPERATURE_REGISTER);
    c->laser_temp_setpoint_ = (float *)registerAddr(LASER3_TEMP_CNTRL_SETPOINT_REGISTER);
    return STATUS_OK;
}

int currentCntrlLaser3Step(void)
{
    return laserCurrentCntrlStep(&currentCntrlLaser3);
}

int currentCntrlLaser4Init(void)
{
    LaserCurrentCntrl *c = &currentCntrlLaser4;
    c->state_ = (unsigned int *)registerAddr(LASER4_CURRENT_CNTRL_STATE_REGISTER);
    c->manual_coarse_ = (float *)registerAddr(LASER4_MANUAL_COARSE_CURRENT_REGISTER);
    c->manual_fine_ = (float *)registerAddr(LASER4_MANUAL_FINE_CURRENT_REGISTER);
    c->swpMin_ = (float *)registerAddr(LASER4_CURRENT_SWEEP_MIN_REGISTER);
    c->swpMax_ = (float *)registerAddr(LASER4_CURRENT_SWEEP_MAX_REGISTER);
    c->swpInc_ = (float *)registerAddr(LASER4_CURRENT_SWEEP_INCR_REGISTER);
    c->extra_coarse_scale_ =  (float *)registerAddr(LASER4_EXTRA_COARSE_SCALE_REGISTER);
    c->extra_fine_scale_ =  (float *)registerAddr(LASER4_EXTRA_FINE_SCALE_REGISTER);
    c->extra_offset_ =  (int *)registerAddr(LASER4_EXTRA_OFFSET_REGISTER);
    c->laser_temp_window_ = (float *)registerAddr(TEMPERATURE_WINDOW_FOR_LASER_SHUTDOWN_REGISTER);
    c->coarse = 0.0;
    c->swpDir    = 1;
    *(c->state_)  = LASER_CURRENT_CNTRL_DisabledState;
    c->fpga_coarse = FPGA_INJECT + INJECT_LASER4_COARSE_CURRENT;
    c->fpga_fine   = FPGA_INJECT + INJECT_LASER4_FINE_CURRENT;
    c->fpga_control = FPGA_INJECT + INJECT_CONTROL;
    c->fpga_extra_coarse_scale = FPGA_INJECT + INJECT_LASER4_EXTRA_COARSE_SCALE;
    c->fpga_extra_fine_scale = FPGA_INJECT + INJECT_LASER4_EXTRA_FINE_SCALE;
    c->fpga_extra_offset = FPGA_INJECT + INJECT_LASER4_EXTRA_OFFSET;
    c->laserNum = 4;
    c->laser_temp_ = (float *)registerAddr(LASER4_TEMPERATURE_REGISTER);
    c->laser_temp_setpoint_ = (float *)registerAddr(LASER4_TEMP_CNTRL_SETPOINT_REGISTER);
    return STATUS_OK;
}

int currentCntrlLaser4Step(void)
{
    return laserCurrentCntrlStep(&currentCntrlLaser4);
}

int read_laser_current_adc(int laserNum)
// Read laser current ADC for specified laser. laserNum is in the range 1-4.
//  Returns I2C_READ_ERROR if an I2C error occured.
{
    I2C_device *devices[4] =  {&i2c_devices[LASER1_CURRENT_ADC],
                               &i2c_devices[LASER2_CURRENT_ADC],
                               &i2c_devices[LASER3_CURRENT_ADC],
                               &i2c_devices[LASER4_CURRENT_ADC]};
    int result, loops;

    setI2C0Mux(devices[laserNum-1]->mux);
    for (loops=0;loops<1000;loops++);
    result = ltc2451_getData(devices[laserNum-1]);
    return result;
}
