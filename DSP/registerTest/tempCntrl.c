/*
 * FILE:
 *   tempCntrl.c
 *
 * DESCRIPTION:
 *   Temperature controller routines
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   16-Dec-2008  sze  Initial version.
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */
#include "interface.h"
#include "registers.h"
#include "pid.h"
#include "tempCntrl.h"
#include "dspAutogen.h"
#include "i2c_dsp.h"
#include "ltc2499.h"
#include "ltc2485.h"
#include "pca9547.h"
#include <math.h>

int resistanceToTemperature(float resistance,float constA,float constB,
                            float constC,float *result)
// Convert thermistor resistance to temperature in degrees Celsius
{
    float lnResistance;
    float temp;
    if (resistance > 1.0 && resistance < 5.0e6)
    {
        lnResistance = log(resistance);
        temp = 1/(constA + (constB * lnResistance) +
                  (constC * lnResistance * lnResistance * lnResistance));
        *result = temp - 273.15;
        return STATUS_OK;
    }
    else
    {
        message_puts("Bad resistance in resistanceToTemperature");
        *result = 0.0;
        return STATUS_OK;
    }
}

/*
int tempCntrlWrite(TempCntrl *t)
{
    return STATUS_OK;
}
*/
#define state     (*(t->state_))
#define tol       (*(t->tol_))
#define locked    (*(t->locked_))
#define swpMin    (*(t->swpMin_))
#define swpMax    (*(t->swpMax_))
#define swpInc    (*(t->swpInc_))
#define extMax    (*(t->extMax_))
#define prbsAmp   (*(t->prbsAmp_))
#define prbsMean  (*(t->prbsMean_))
#define prbsGen   (*(t->prbsGen_))
#define prbsReg   (t->prbsReg)
#define temp      (*(t->temp_))
#define extTemp   (*(t->extTemp_))
#define dasTemp   (*(t->dasTemp_))
#define tec       (*(t->tec_))
#define userSetpoint    (*(t->userSetpoint_))
#define manualTec (*(t->manualTec_))
#define pidParams (&(t->pidParamsRef))
#define r         (*(pidParams->r_))
#define b         (*(pidParams->b_))
#define c         (*(pidParams->c_))
#define h         (*(pidParams->h_))
#define K         (*(pidParams->K_))
#define Ti        (*(pidParams->Ti_))
#define Td        (*(pidParams->Td_))
#define N         (*(pidParams->N_))
#define S         (*(pidParams->S_))
#define Imax      (*(pidParams->Imax_))
#define Amin      (*(pidParams->Amin_))
#define Amax      (*(pidParams->Amax_))
#define swpDir          (t->swpDir)
#define lockCount       (t->lockCount)
#define unlockCount     (t->unlockCount)
#define firstIteration  (t->firstIteration)
#define pidState        (&(t->pidState))
#define hasExt    ((0 != t->extMax_) && (0 != t->extTemp_))

int tempCntrlStep(TempCntrl *t)
{
    // Step the temperature controller, computing the new TEC value
    float error;
    int inRange;

    switch (state)
    {
    case TEMP_CNTRL_DisabledState:
        tec = 0x8000;
        prbsReg = 0x1;
        break;
    case TEMP_CNTRL_ManualState:
        tec = manualTec;
        prbsReg = 0x1;
        break;
    case TEMP_CNTRL_EnabledState:
        // Start or step the controller
        r = userSetpoint;
    case TEMP_CNTRL_AutomaticState:
        error = r - temp;
        inRange = (error>=-tol && error<=tol);
        if (firstIteration)
        {
            firstIteration = FALSE;
            pid_bumpless_restart(temp,pidState->a,pidState,pidParams);
        }
        else
        {
            pid_step(temp,dasTemp,pidState,pidParams);
        }
        // Update locked state
        if (locked)
        {
            if (!inRange) unlockCount++;
            else unlockCount = 0;
            if (unlockCount > TEMP_CNTRL_UNLOCK_COUNT) locked = FALSE;
        }
        else
        {
            if (inRange) lockCount++;
            else lockCount = FALSE;
            if (lockCount > TEMP_CNTRL_LOCK_COUNT) locked = TRUE;
        }
        tec = pidState->a;
        prbsReg = 0x1;
        break;
    case TEMP_CNTRL_SweepingState:
        r += swpDir * swpInc;
        if (r >= swpMax)
        {
            r = swpMax;
            swpDir = -1;
        }
        else if (r <= swpMin)
        {
            r = swpMin;
            swpDir = 1;
        }
        pid_step(temp,dasTemp,pidState,pidParams);
        tec = pidState->a;
        prbsReg = 0x1;
        break;
    case TEMP_CNTRL_SendPrbsState:
        if (prbsReg & 0x1)
        {
            tec = prbsMean + prbsAmp;
            prbsReg ^= prbsGen;
        }
        else
        {
            tec = prbsMean - prbsAmp;
        }
        prbsReg >>= 1;
        break;
    }
    if (hasExt)
    {
        if (extTemp > extMax) tec = 0x8000;
    }
    return STATUS_OK;
}

#undef state
#undef tol
#undef swpMin
#undef swpMax
#undef swpInc
#undef hasExtMax
#undef extMax
#undef prbsAmp
#undef prbsMean
#undef prbsGen
#undef prbsReg
#undef temp
#undef extTemp
#undef dasTemp
#undef tec
#undef manualTec
#undef pidParams
#undef r
#undef b
#undef c
#undef h
#undef K
#undef Ti
#undef Td
#undef N
#undef S
#undef Imax
#undef Amin
#undef Amax
#undef userSetpoint
#undef swpDir
#undef locked
#undef lockCount
#undef unlockCount
#undef firstIteration
#undef pidState

TempCntrl tempCntrlLaser1;
TempCntrl tempCntrlLaser2;
TempCntrl tempCntrlLaser3;
TempCntrl tempCntrlLaser4;
TempCntrl tempCntrlCavity;

int tempCntrlLaser1Init(void)
{
    TempCntrl *t = &tempCntrlLaser1;
    PidParamsRef *p = &(t->pidParamsRef);
    PidState *s  = &(t->pidState);
    p->r_        = (float *)registerAddr(LASER1_TEMP_CNTRL_SETPOINT_REGISTER);
    p->b_        = (float *)registerAddr(LASER1_TEMP_CNTRL_B_REGISTER);
    p->c_        = (float *)registerAddr(LASER1_TEMP_CNTRL_C_REGISTER);
    p->h_        = (float *)registerAddr(LASER1_TEMP_CNTRL_H_REGISTER);
    p->K_        = (float *)registerAddr(LASER1_TEMP_CNTRL_K_REGISTER);
    p->Ti_       = (float *)registerAddr(LASER1_TEMP_CNTRL_TI_REGISTER);
    p->Td_       = (float *)registerAddr(LASER1_TEMP_CNTRL_TD_REGISTER);
    p->N_        = (float *)registerAddr(LASER1_TEMP_CNTRL_N_REGISTER);
    p->S_        = (float *)registerAddr(LASER1_TEMP_CNTRL_S_REGISTER);
    p->Imax_     = (float *)registerAddr(LASER1_TEMP_CNTRL_IMAX_REGISTER);
    p->Amin_     = (float *)registerAddr(LASER1_TEMP_CNTRL_AMIN_REGISTER);
    p->Amax_     = (float *)registerAddr(LASER1_TEMP_CNTRL_AMAX_REGISTER);
    p->ffwd_     = (float *)registerAddr(LASER1_TEMP_CNTRL_FFWD_REGISTER);
    t->userSetpoint_ = (float *)registerAddr(LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(LASER1_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(LASER1_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->locked_   = (unsigned int *)registerAddr(LASER1_TEMP_CNTRL_LOCK_STATUS_REGISTER);
    t->swpMin_   = (float *)registerAddr(LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER);
    t->swpMax_   = (float *)registerAddr(LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER);
    t->swpInc_   = (float *)registerAddr(LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER);
    t->extMax_   = 0;
    t->prbsAmp_  = (float *)registerAddr(LASER1_TEC_PRBS_AMPLITUDE_REGISTER);
    t->prbsMean_ = (float *)registerAddr(LASER1_TEC_PRBS_MEAN_REGISTER);
    t->prbsGen_  = (unsigned int *)registerAddr(LASER1_TEC_PRBS_GENPOLY_REGISTER);
    t->temp_     = (float *)registerAddr(LASER1_TEMPERATURE_REGISTER);
    t->extTemp_  = 0;
    t->dasTemp_  = (float *)registerAddr(DAS_TEMPERATURE_REGISTER);
    t->tec_      = (float *)registerAddr(LASER1_TEC_REGISTER);
    t->manualTec_ = (float *)registerAddr(LASER1_MANUAL_TEC_REGISTER);
    t->swpDir    = 1;
    *(t->state_)  = TEMP_CNTRL_DisabledState;
    *(t->locked_) = FALSE;
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = s->a = s->u = 0x8000;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    *(p->r_) = *(t->userSetpoint_);
    return STATUS_OK;
}
int tempCntrlLaser1Step(void)
{
    unsigned int regList[] = {LASER1_TEMP_CNTRL_SETPOINT_REGISTER,
                              LASER1_TEMP_CNTRL_LOCK_STATUS_REGISTER,
                              LASER1_TEMP_CNTRL_STATE_REGISTER,
                              LASER1_TEC_REGISTER
                             };
    int status;
    status = tempCntrlStep(&tempCntrlLaser1);
    writebackRegisters(regList,sizeof(regList)/sizeof(unsigned int));
    return status;
}

int tempCntrlLaser2Init(void)
{
    TempCntrl *t = &tempCntrlLaser2;
    PidParamsRef *p = &(t->pidParamsRef);
    PidState *s  = &(t->pidState);
    p->r_        = (float *)registerAddr(LASER2_TEMP_CNTRL_SETPOINT_REGISTER);
    p->b_        = (float *)registerAddr(LASER2_TEMP_CNTRL_B_REGISTER);
    p->c_        = (float *)registerAddr(LASER2_TEMP_CNTRL_C_REGISTER);
    p->h_        = (float *)registerAddr(LASER2_TEMP_CNTRL_H_REGISTER);
    p->K_        = (float *)registerAddr(LASER2_TEMP_CNTRL_K_REGISTER);
    p->Ti_       = (float *)registerAddr(LASER2_TEMP_CNTRL_TI_REGISTER);
    p->Td_       = (float *)registerAddr(LASER2_TEMP_CNTRL_TD_REGISTER);
    p->N_        = (float *)registerAddr(LASER2_TEMP_CNTRL_N_REGISTER);
    p->S_        = (float *)registerAddr(LASER2_TEMP_CNTRL_S_REGISTER);
    p->Imax_     = (float *)registerAddr(LASER2_TEMP_CNTRL_IMAX_REGISTER);
    p->Amin_     = (float *)registerAddr(LASER2_TEMP_CNTRL_AMIN_REGISTER);
    p->Amax_     = (float *)registerAddr(LASER2_TEMP_CNTRL_AMAX_REGISTER);
    p->ffwd_     = (float *)registerAddr(LASER2_TEMP_CNTRL_FFWD_REGISTER);
    t->userSetpoint_ = (float *)registerAddr(LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(LASER2_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(LASER2_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->locked_   = (unsigned int *)registerAddr(LASER2_TEMP_CNTRL_LOCK_STATUS_REGISTER);
    t->swpMin_   = (float *)registerAddr(LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER);
    t->swpMax_   = (float *)registerAddr(LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER);
    t->swpInc_   = (float *)registerAddr(LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER);
    t->extMax_   = 0;
    t->prbsAmp_  = (float *)registerAddr(LASER2_TEC_PRBS_AMPLITUDE_REGISTER);
    t->prbsMean_ = (float *)registerAddr(LASER2_TEC_PRBS_MEAN_REGISTER);
    t->prbsGen_  = (unsigned int *)registerAddr(LASER2_TEC_PRBS_GENPOLY_REGISTER);
    t->temp_     = (float *)registerAddr(LASER2_TEMPERATURE_REGISTER);
    t->extTemp_  = 0;
    t->dasTemp_  = (float *)registerAddr(DAS_TEMPERATURE_REGISTER);
    t->tec_      = (float *)registerAddr(LASER2_TEC_REGISTER);
    t->manualTec_ = (float *)registerAddr(LASER2_MANUAL_TEC_REGISTER);
    t->swpDir    = 1;
    *(t->state_)  = TEMP_CNTRL_DisabledState;
    *(t->locked_) = FALSE;
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = s->a = s->u = 0x8000;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    return STATUS_OK;
}
int tempCntrlLaser2Step(void)
{
    unsigned int regList[] = {LASER2_TEMP_CNTRL_SETPOINT_REGISTER,
                              LASER2_TEMP_CNTRL_LOCK_STATUS_REGISTER,
                              LASER2_TEMP_CNTRL_STATE_REGISTER,
                              LASER2_TEC_REGISTER
                             };
    int status;
    status = tempCntrlStep(&tempCntrlLaser2);
    writebackRegisters(regList,sizeof(regList)/sizeof(unsigned int));
    return status;
}

int tempCntrlLaser3Init(void)
{
    TempCntrl *t = &tempCntrlLaser3;
    PidParamsRef *p = &(t->pidParamsRef);
    PidState *s  = &(t->pidState);
    p->r_        = (float *)registerAddr(LASER3_TEMP_CNTRL_SETPOINT_REGISTER);
    p->b_        = (float *)registerAddr(LASER3_TEMP_CNTRL_B_REGISTER);
    p->c_        = (float *)registerAddr(LASER3_TEMP_CNTRL_C_REGISTER);
    p->h_        = (float *)registerAddr(LASER3_TEMP_CNTRL_H_REGISTER);
    p->K_        = (float *)registerAddr(LASER3_TEMP_CNTRL_K_REGISTER);
    p->Ti_       = (float *)registerAddr(LASER3_TEMP_CNTRL_TI_REGISTER);
    p->Td_       = (float *)registerAddr(LASER3_TEMP_CNTRL_TD_REGISTER);
    p->N_        = (float *)registerAddr(LASER3_TEMP_CNTRL_N_REGISTER);
    p->S_        = (float *)registerAddr(LASER3_TEMP_CNTRL_S_REGISTER);
    p->Imax_     = (float *)registerAddr(LASER3_TEMP_CNTRL_IMAX_REGISTER);
    p->Amin_     = (float *)registerAddr(LASER3_TEMP_CNTRL_AMIN_REGISTER);
    p->Amax_     = (float *)registerAddr(LASER3_TEMP_CNTRL_AMAX_REGISTER);
    p->ffwd_     = (float *)registerAddr(LASER3_TEMP_CNTRL_FFWD_REGISTER);
    t->userSetpoint_ = (float *)registerAddr(LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(LASER3_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(LASER3_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->locked_   = (unsigned int *)registerAddr(LASER3_TEMP_CNTRL_LOCK_STATUS_REGISTER);
    t->swpMin_   = (float *)registerAddr(LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER);
    t->swpMax_   = (float *)registerAddr(LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER);
    t->swpInc_   = (float *)registerAddr(LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER);
    t->extMax_   = 0;
    t->prbsAmp_  = (float *)registerAddr(LASER3_TEC_PRBS_AMPLITUDE_REGISTER);
    t->prbsMean_ = (float *)registerAddr(LASER3_TEC_PRBS_MEAN_REGISTER);
    t->prbsGen_  = (unsigned int *)registerAddr(LASER3_TEC_PRBS_GENPOLY_REGISTER);
    t->temp_     = (float *)registerAddr(LASER3_TEMPERATURE_REGISTER);
    t->extTemp_  = 0;
    t->dasTemp_  = (float *)registerAddr(DAS_TEMPERATURE_REGISTER);
    t->tec_      = (float *)registerAddr(LASER3_TEC_REGISTER);
    t->manualTec_ = (float *)registerAddr(LASER3_MANUAL_TEC_REGISTER);
    t->swpDir    = 1;
    *(t->state_)  = TEMP_CNTRL_DisabledState;
    *(t->locked_) = FALSE;
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = s->a = s->u = 0x8000;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    return STATUS_OK;
}
int tempCntrlLaser3Step(void)
{
    unsigned int regList[] = {LASER3_TEMP_CNTRL_SETPOINT_REGISTER,
                              LASER3_TEMP_CNTRL_LOCK_STATUS_REGISTER,
                              LASER3_TEMP_CNTRL_STATE_REGISTER,
                              LASER3_TEC_REGISTER
                             };
    int status;
    status = tempCntrlStep(&tempCntrlLaser3);
    writebackRegisters(regList,sizeof(regList)/sizeof(unsigned int));
    return status;
}

int tempCntrlLaser4Init(void)
{
    TempCntrl *t = &tempCntrlLaser4;
    PidParamsRef *p = &(t->pidParamsRef);
    PidState *s  = &(t->pidState);
    p->r_        = (float *)registerAddr(LASER4_TEMP_CNTRL_SETPOINT_REGISTER);
    p->b_        = (float *)registerAddr(LASER4_TEMP_CNTRL_B_REGISTER);
    p->c_        = (float *)registerAddr(LASER4_TEMP_CNTRL_C_REGISTER);
    p->h_        = (float *)registerAddr(LASER4_TEMP_CNTRL_H_REGISTER);
    p->K_        = (float *)registerAddr(LASER4_TEMP_CNTRL_K_REGISTER);
    p->Ti_       = (float *)registerAddr(LASER4_TEMP_CNTRL_TI_REGISTER);
    p->Td_       = (float *)registerAddr(LASER4_TEMP_CNTRL_TD_REGISTER);
    p->N_        = (float *)registerAddr(LASER4_TEMP_CNTRL_N_REGISTER);
    p->S_        = (float *)registerAddr(LASER4_TEMP_CNTRL_S_REGISTER);
    p->Imax_     = (float *)registerAddr(LASER4_TEMP_CNTRL_IMAX_REGISTER);
    p->Amin_     = (float *)registerAddr(LASER4_TEMP_CNTRL_AMIN_REGISTER);
    p->Amax_     = (float *)registerAddr(LASER4_TEMP_CNTRL_AMAX_REGISTER);
    p->ffwd_     = (float *)registerAddr(LASER4_TEMP_CNTRL_FFWD_REGISTER);
    t->userSetpoint_ = (float *)registerAddr(LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(LASER4_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(LASER4_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->locked_   = (unsigned int *)registerAddr(LASER4_TEMP_CNTRL_LOCK_STATUS_REGISTER);
    t->swpMin_   = (float *)registerAddr(LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER);
    t->swpMax_   = (float *)registerAddr(LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER);
    t->swpInc_   = (float *)registerAddr(LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER);
    t->extMax_   = 0;
    t->prbsAmp_  = (float *)registerAddr(LASER4_TEC_PRBS_AMPLITUDE_REGISTER);
    t->prbsMean_ = (float *)registerAddr(LASER4_TEC_PRBS_MEAN_REGISTER);
    t->prbsGen_  = (unsigned int *)registerAddr(LASER4_TEC_PRBS_GENPOLY_REGISTER);
    t->temp_     = (float *)registerAddr(LASER4_TEMPERATURE_REGISTER);
    t->extTemp_  = 0;
    t->dasTemp_  = (float *)registerAddr(DAS_TEMPERATURE_REGISTER);
    t->tec_      = (float *)registerAddr(LASER4_TEC_REGISTER);
    t->manualTec_ = (float *)registerAddr(LASER4_MANUAL_TEC_REGISTER);
    t->swpDir    = 1;
    *(t->state_)  = TEMP_CNTRL_DisabledState;
    *(t->locked_) = FALSE;
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = s->a = s->u = 0x8000;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    return STATUS_OK;
}
int tempCntrlLaser4Step(void)
{
    unsigned int regList[] = {LASER4_TEMP_CNTRL_SETPOINT_REGISTER,
                              LASER4_TEMP_CNTRL_LOCK_STATUS_REGISTER,
                              LASER4_TEMP_CNTRL_STATE_REGISTER,
                              LASER4_TEC_REGISTER
                             };
    int status;
    status = tempCntrlStep(&tempCntrlLaser4);
    writebackRegisters(regList,sizeof(regList)/sizeof(unsigned int));
    return status;
}

int read_laser_tec_imon(int desired, int next, float *result)
/*
    Read laser TEC current monitor
    Inputs:
      Codes for desired monitor channel and for next monitor channel.
        0 => temperature
        1 => laser 1
        2 => laser 2
        3 => laser 3
        4 => laser 4
    Output:
      *result is value of desired channel read from ADC. It is changed
        only if the desired channel was the one specified as "next" on
        the previous call to this function
    Return:
      STATUS_OK if desired channel is returned
      ERROR_UNAVAILABLE if channel data is not available since
       a different "next channel" was set up previously
*/
{
    int code[5] = {-1, 0, 1, 2, 3};
    static int prevChan = -1;
    int flags;

    if (next < 0 || next > 4) return ERROR_BAD_VALUE;
    //  Set up for next conversion
    if (next == 0) ltc2499_configure(0,0,1,0,0);
    else ltc2499_configure(0,code[next],0,0,0);
    if (prevChan == desired)
    {
        *result = (float) ltc2499_getData(&flags);
        if (flags == 0) *result = -16777216.0;
        else if (flags == 3) *result = 16777215.0;
        prevChan = next;
        return STATUS_OK;
    }
    else
    {
        ltc2499_getData(&flags);
        prevChan = next;
        return ERROR_UNAVAILABLE;
    }
}

int read_laser_tec_monitors()
// Cycle around the laser TEC current monitors placing results into registers
{
    unsigned int regList[] =
    {
        LASER_TEC_MONITOR_TEMPERATURE_REGISTER,
        LASER1_TEC_MONITOR_REGISTER,
        LASER2_TEC_MONITOR_REGISTER,
        LASER3_TEC_MONITOR_REGISTER,
        LASER4_TEC_MONITOR_REGISTER,
    };
    static int chan = 0;
    switch (chan)
    {
    case 0:
        read_laser_tec_imon(0,1,(float *)registerAddr(LASER_TEC_MONITOR_TEMPERATURE_REGISTER));
        chan = 1;
        break;
    case 1:
        read_laser_tec_imon(1,2,(float *)registerAddr(LASER3_TEC_MONITOR_REGISTER));
        chan = 2;
        break;
    case 2:
        read_laser_tec_imon(2,3,(float *)registerAddr(LASER1_TEC_MONITOR_REGISTER));
        chan = 3;
        break;
    case 3:
        read_laser_tec_imon(3,4,(float *)registerAddr(LASER2_TEC_MONITOR_REGISTER));
        chan = 4;
        break;
    case 4:
        read_laser_tec_imon(4,0,(float *)registerAddr(LASER4_TEC_MONITOR_REGISTER));
        chan = 0;
        break;
    default:
        break;
    }
    writebackRegisters(regList,sizeof(regList)/sizeof(unsigned int));
    return STATUS_OK;
}

int read_laser_thermistor_adc(int laserNum)
// Read thermistor ADC for specified laser. laserNum is in the range 1-4
{
    unsigned int chan[5] = {0,0,1,2,3};
    int flags, result, loops;

    setI2C0Mux(chan[laserNum]);
    for (loops=0;loops<1000;loops++);
    result = ltc2485_getData(&flags);
    if (flags == 0) result = -16777216;
    else if (flags == 3) result = 16777215;
    return result;
}

int tempCntrlCavityInit(void)
{
    TempCntrl *t = &tempCntrlCavity;
    PidParamsRef *p = &(t->pidParamsRef);
    PidState *s  = &(t->pidState);
    p->r_        = (float *)registerAddr(CAVITY_TEMP_CNTRL_SETPOINT_REGISTER);
    p->b_        = (float *)registerAddr(CAVITY_TEMP_CNTRL_B_REGISTER);
    p->c_        = (float *)registerAddr(CAVITY_TEMP_CNTRL_C_REGISTER);
    p->h_        = (float *)registerAddr(CAVITY_TEMP_CNTRL_H_REGISTER);
    p->K_        = (float *)registerAddr(CAVITY_TEMP_CNTRL_K_REGISTER);
    p->Ti_       = (float *)registerAddr(CAVITY_TEMP_CNTRL_TI_REGISTER);
    p->Td_       = (float *)registerAddr(CAVITY_TEMP_CNTRL_TD_REGISTER);
    p->N_        = (float *)registerAddr(CAVITY_TEMP_CNTRL_N_REGISTER);
    p->S_        = (float *)registerAddr(CAVITY_TEMP_CNTRL_S_REGISTER);
    p->Imax_     = (float *)registerAddr(CAVITY_TEMP_CNTRL_IMAX_REGISTER);
    p->Amin_     = (float *)registerAddr(CAVITY_TEMP_CNTRL_AMIN_REGISTER);
    p->Amax_     = (float *)registerAddr(CAVITY_TEMP_CNTRL_AMAX_REGISTER);
    p->ffwd_     = (float *)registerAddr(CAVITY_TEMP_CNTRL_FFWD_REGISTER);
    t->userSetpoint_ = (float *)registerAddr(CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(CAVITY_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->locked_   = (unsigned int *)registerAddr(CAVITY_TEMP_CNTRL_LOCK_STATUS_REGISTER);
    t->swpMin_   = (float *)registerAddr(CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER);
    t->swpMax_   = (float *)registerAddr(CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER);
    t->swpInc_   = (float *)registerAddr(CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER);
    t->extMax_   = (float *)registerAddr(CAVITY_MAX_HEATSINK_TEMP_REGISTER);
    t->prbsAmp_  = (float *)registerAddr(CAVITY_TEC_PRBS_AMPLITUDE_REGISTER);
    t->prbsMean_ = (float *)registerAddr(CAVITY_TEC_PRBS_MEAN_REGISTER);
    t->prbsGen_  = (unsigned int *)registerAddr(CAVITY_TEC_PRBS_GENPOLY_REGISTER);
    t->temp_     = (float *)registerAddr(CAVITY_TEMPERATURE_REGISTER);
    t->extTemp_  = (float *)registerAddr(HOT_BOX_HEATSINK_TEMPERATURE_REGISTER);
    t->dasTemp_  = (float *)registerAddr(DAS_TEMPERATURE_REGISTER);
    t->tec_      = (float *)registerAddr(CAVITY_TEC_REGISTER);
    t->manualTec_ = (float *)registerAddr(CAVITY_MANUAL_TEC_REGISTER);
    t->swpDir    = 1;
    *(t->state_)  = TEMP_CNTRL_DisabledState;
    *(t->locked_) = FALSE;
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = s->a = s->u = 0x8000;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    return STATUS_OK;
}

int tempCntrlCavityStep(void)
{
    unsigned int regList[] = {CAVITY_TEMP_CNTRL_SETPOINT_REGISTER,
                              CAVITY_TEMP_CNTRL_LOCK_STATUS_REGISTER,
                              CAVITY_TEMP_CNTRL_STATE_REGISTER,
                              CAVITY_TEC_REGISTER
                             };
    int status;
    status = tempCntrlStep(&tempCntrlCavity);
    writebackRegisters(regList,sizeof(regList)/sizeof(unsigned int));
    return status;
}
