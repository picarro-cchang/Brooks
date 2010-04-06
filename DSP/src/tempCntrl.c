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
 *    7-May-2009  sze  Added error checking in resistanceToTemperature
 *   29-May-2009  sze  Added handling of temp sensor in laser TEC current monitor
 *   13-Jun-2009  sze  Added code to read I2C laser thermistor ADCs
 *   21-Aug-2009  sze  Added TEMP_CNTRL_AutomaticState
 *   31-Aug-2009  sze  Added warm box temperature control
 *   26-Sep-2009  sze  Moved locked register to a single bit in DAS status register
 *    1-Oct-2009  sze  Added active bit in DAS status register
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
#include "valveCntrl.h"
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
#define activeBit (t->activeBit_)
#define lockBit   (t->lockBit_)
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
#define disabledValue   (t->disabledValue)
#define lastTec         (t->lastTec)
#define hasExt    ((0 != t->extMax_) && (0 != t->extTemp_))

int tempCntrlStep(TempCntrl *t)
{
    // Step the temperature controller, computing the new TEC value
    float error, tecNext;
    int inRange;

    switch (state)
    {
    case TEMP_CNTRL_DisabledState:
        resetDasStatusBit(activeBit);
        resetDasStatusBit(lockBit);
        tec = disabledValue;
        prbsReg = 0x1;
        break;
    case TEMP_CNTRL_ManualState:
        setDasStatusBit(activeBit);
        resetDasStatusBit(lockBit);
        if (manualTec > Amax) manualTec = Amax;
        if (manualTec < Amin) manualTec = Amin;
        tec = manualTec;
        prbsReg = 0x1;
        break;
    case TEMP_CNTRL_EnabledState:
        // Start or step the controller
        r = userSetpoint;
    case TEMP_CNTRL_AutomaticState:
        setDasStatusBit(activeBit);
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
        if (getDasStatusBit(lockBit))
        {
            if (!inRange) unlockCount++;
            else unlockCount = 0;
            if (unlockCount > TEMP_CNTRL_UNLOCK_COUNT) resetDasStatusBit(lockBit);
        }
        else
        {
            if (inRange) lockCount++;
            else lockCount = 0;
            if (lockCount > TEMP_CNTRL_LOCK_COUNT) setDasStatusBit(lockBit);
        }
        tec = pidState->a;
        prbsReg = 0x1;
        break;
    case TEMP_CNTRL_SweepingState:
        setDasStatusBit(activeBit);
        resetDasStatusBit(lockBit);
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
        setDasStatusBit(activeBit);
        resetDasStatusBit(lockBit);
        if (prbsReg & 0x1)
        {
            tecNext = prbsMean + prbsAmp;
            prbsReg ^= prbsGen;
        }
        else
        {
            tecNext = prbsMean - prbsAmp;
        }
        if (tecNext > Amax) tecNext = Amax;
        if (tecNext < Amin) tecNext = Amin;
        tec = tecNext;
        prbsReg >>= 1;
        break;
    }
    if (hasExt)
    {
        if (extTemp > extMax) {
            float change = disabledValue - lastTec;
            if (change > Imax) change = Imax;
            if (change < -Imax) change = -Imax;
            tec  = lastTec + change;
            pidState->a = tec;
        }  
    }
    lastTec = tec;
    return STATUS_OK;
}

#undef state
#undef disabledValue
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
#undef lockBit
#undef activeBit
#undef lockCount
#undef unlockCount
#undef firstIteration
#undef pidState
#undef lastTec

TempCntrl tempCntrlLaser1;
TempCntrl tempCntrlLaser2;
TempCntrl tempCntrlLaser3;
TempCntrl tempCntrlLaser4;
TempCntrl tempCntrlWarmBox;
TempCntrl tempCntrlCavity;
TempCntrl tempCntrlHeater;

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
    t->disabledValue = 0x8000;
    t->userSetpoint_ = (float *)registerAddr(LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(LASER1_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(LASER1_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->activeBit_  = DAS_STATUS_Laser1TempCntrlActiveBit;
    t->lockBit_    = DAS_STATUS_Laser1TempCntrlLockedBit;
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
    resetDasStatusBit(t->lockBit_);
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = t->lastTec = s->a = s->u = t->disabledValue;
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
    t->disabledValue = 0x8000;
    t->userSetpoint_ = (float *)registerAddr(LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(LASER2_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(LASER2_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->activeBit_  = DAS_STATUS_Laser2TempCntrlActiveBit;
    t->lockBit_    = DAS_STATUS_Laser2TempCntrlLockedBit;
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
    resetDasStatusBit(t->lockBit_);
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = t->lastTec = s->a = s->u = t->disabledValue;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    return STATUS_OK;
}
int tempCntrlLaser2Step(void)
{
    unsigned int regList[] = {LASER2_TEMP_CNTRL_SETPOINT_REGISTER,
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
    t->disabledValue = 0x8000;
    t->userSetpoint_ = (float *)registerAddr(LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(LASER3_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(LASER3_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->activeBit_  = DAS_STATUS_Laser3TempCntrlActiveBit;
    t->lockBit_    = DAS_STATUS_Laser3TempCntrlLockedBit;
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
    resetDasStatusBit(t->lockBit_);
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = t->lastTec = s->a = s->u = t->disabledValue;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    return STATUS_OK;
}
int tempCntrlLaser3Step(void)
{
    unsigned int regList[] = {LASER3_TEMP_CNTRL_SETPOINT_REGISTER,
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
    t->disabledValue = 0x8000;
    t->userSetpoint_ = (float *)registerAddr(LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(LASER4_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(LASER4_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->activeBit_  = DAS_STATUS_Laser4TempCntrlActiveBit;
    t->lockBit_    = DAS_STATUS_Laser4TempCntrlLockedBit;
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
    resetDasStatusBit(t->lockBit_);
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = t->lastTec = s->a = s->u = t->disabledValue;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    return STATUS_OK;
}
int tempCntrlLaser4Step(void)
{
    unsigned int regList[] = {LASER4_TEMP_CNTRL_SETPOINT_REGISTER,

    LASER4_TEMP_CNTRL_STATE_REGISTER,
                              LASER4_TEC_REGISTER
                             };
    int status;
    status = tempCntrlStep(&tempCntrlLaser4);
    writebackRegisters(regList,sizeof(regList)/sizeof(unsigned int));
    return status;
}

int read_etalon_thermistor_adc()
// Read etalon thermistor ADC. Returns I2C_READ_ERROR on an I2C error 
{
    int flags, result, loops;
    I2C_device *d = &i2c_devices[ETALON_THERMISTOR_ADC];
    
    setI2C1Mux(d->mux);  // I2C bus 8
    for (loops=0;loops<1000;loops++);
    result = ltc2485_getData(d, &flags);
    if (result == I2C_READ_ERROR) return result;
    if (flags == 0) result = -16777216;
    else if (flags == 3) result = 16777215;
    return result;
}

int read_warm_box_thermistor_adc()
// Read warm box thermistor ADC
{
    int flags, result, loops;
    I2C_device *d = &i2c_devices[WARM_BOX_THERMISTOR_ADC];

    setI2C1Mux(d->mux);  // I2C bus 8
    for (loops=0;loops<1000;loops++);
    result = ltc2485_getData(d, &flags);
    if (result == I2C_READ_ERROR) return result;
    if (flags == 0) result = -16777216;
    else if (flags == 3) result = 16777215;
    return result;
}

int read_warm_box_heatsink_thermistor_adc()
// Read warm box heatsink thermistor ADC
{
    int flags, result, loops;
    I2C_device *d = &i2c_devices[WARM_BOX_HEATSINK_THERMISTOR_ADC];

    setI2C1Mux(d->mux);  // I2C bus 8
    for (loops=0;loops<1000;loops++);
    result = ltc2485_getData(d, &flags);
    if (result == I2C_READ_ERROR) return result;
    if (flags == 0) result = -16777216;
    else if (flags == 3) result = 16777215;
    return result;
}

int read_cavity_thermistor_adc()
// Read cavity thermistor ADC
{
    int flags, result, loops;
    I2C_device *d = &i2c_devices[CAVITY_THERMISTOR_ADC];

    setI2C0Mux(d->mux);  // I2C bus 7
    for (loops=0;loops<1000;loops++);
    result = ltc2485_getData(d, &flags);
    if (result == I2C_READ_ERROR) return result;
    if (flags == 0) result = -16777216;
    else if (flags == 3) result = 16777215;
    return result;
}

int read_hot_box_heatsink_thermistor_adc()
// Read hot box heatsink thermistor ADC
{
    int flags, result, loops;
    I2C_device *d = &i2c_devices[HOT_BOX_HEATSINK_THERMISTOR_ADC];

    setI2C0Mux(d->mux);  // I2C bus 7
    for (loops=0;loops<1000;loops++);
    result = ltc2485_getData(d, &flags);
    if (result == I2C_READ_ERROR) return result;
    if (flags == 0) result = -16777216;
    else if (flags == 3) result = 16777215;
    return result;
}

int read_laser_thermistor_adc(int laserNum)
// Read thermistor ADC for specified laser. laserNum is in the range 1-4
{
    I2C_device *devices[4] =  {&i2c_devices[LASER1_THERMISTOR_ADC],
                               &i2c_devices[LASER2_THERMISTOR_ADC],
                               &i2c_devices[LASER3_THERMISTOR_ADC],
                               &i2c_devices[LASER4_THERMISTOR_ADC]};

    int flags, result, loops;

    setI2C0Mux(devices[laserNum-1]->mux);
    for (loops=0;loops<1000;loops++);
    result = ltc2485_getData(devices[laserNum-1], &flags);
    if (result == I2C_READ_ERROR) return result;
    if (flags == 0) result = -16777216;
    else if (flags == 3) result = 16777215;
    return result;
}

int tempCntrlWarmBoxInit(void)
{
    TempCntrl *t = &tempCntrlWarmBox;
    PidParamsRef *p = &(t->pidParamsRef);
    PidState *s  = &(t->pidState);
    p->r_        = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER);
    p->b_        = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_B_REGISTER);
    p->c_        = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_C_REGISTER);
    p->h_        = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_H_REGISTER);
    p->K_        = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_K_REGISTER);
    p->Ti_       = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_TI_REGISTER);
    p->Td_       = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_TD_REGISTER);
    p->N_        = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_N_REGISTER);
    p->S_        = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_S_REGISTER);
    p->Imax_     = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_IMAX_REGISTER);
    p->Amin_     = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_AMIN_REGISTER);
    p->Amax_     = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_AMAX_REGISTER);
    p->ffwd_     = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_FFWD_REGISTER);
    t->disabledValue = 0x8000;
    t->userSetpoint_ = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(WARM_BOX_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->activeBit_  = DAS_STATUS_WarmBoxTempCntrlActiveBit;
    t->lockBit_    = DAS_STATUS_WarmBoxTempCntrlLockedBit;
    t->swpMin_   = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER);
    t->swpMax_   = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER);
    t->swpInc_   = (float *)registerAddr(WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER);
    t->extMax_   = (float *)registerAddr(WARM_BOX_MAX_HEATSINK_TEMP_REGISTER);
    t->prbsAmp_  = (float *)registerAddr(WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER);
    t->prbsMean_ = (float *)registerAddr(WARM_BOX_TEC_PRBS_MEAN_REGISTER);
    t->prbsGen_  = (unsigned int *)registerAddr(WARM_BOX_TEC_PRBS_GENPOLY_REGISTER);
    t->temp_     = (float *)registerAddr(WARM_BOX_TEMPERATURE_REGISTER);
    t->extTemp_  = (float *)registerAddr(WARM_BOX_HEATSINK_TEMPERATURE_REGISTER);
    t->dasTemp_  = (float *)registerAddr(DAS_TEMPERATURE_REGISTER);
    t->tec_      = (float *)registerAddr(WARM_BOX_TEC_REGISTER);
    t->manualTec_ = (float *)registerAddr(WARM_BOX_MANUAL_TEC_REGISTER);
    t->swpDir    = 1;
    *(t->state_)  = TEMP_CNTRL_DisabledState;
    resetDasStatusBit(t->lockBit_);
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = t->lastTec = s->a = s->u = t->disabledValue;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    return STATUS_OK;
}

int tempCntrlWarmBoxStep(void)
{
    unsigned int regList[] = {WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER,
                              WARM_BOX_TEMP_CNTRL_STATE_REGISTER,
                              WARM_BOX_TEC_REGISTER
                             };
    int status;
    if (*(TEC_CNTRL_Type *)registerAddr(TEC_CNTRL_REGISTER) == TEC_CNTRL_Disabled) modify_valve_pump_tec(0x80,0x0);
    else modify_valve_pump_tec(0x80,0x80);
    status = tempCntrlStep(&tempCntrlWarmBox);
    writebackRegisters(regList,sizeof(regList)/sizeof(unsigned int));
    return status;
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
    t->disabledValue = 0x8000;
    t->userSetpoint_ = (float *)registerAddr(CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(CAVITY_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->activeBit_  = DAS_STATUS_CavityTempCntrlActiveBit;
    t->lockBit_    = DAS_STATUS_CavityTempCntrlLockedBit;
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
    resetDasStatusBit(t->lockBit_);
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = t->lastTec = s->a = s->u = t->disabledValue;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    return STATUS_OK;
}

int tempCntrlCavityStep(void)
{
    unsigned int regList[] = {CAVITY_TEMP_CNTRL_SETPOINT_REGISTER,
                              CAVITY_TEMP_CNTRL_STATE_REGISTER,
                              CAVITY_TEC_REGISTER
                             };
    int status;
    if (*(TEC_CNTRL_Type *)registerAddr(TEC_CNTRL_REGISTER) == TEC_CNTRL_Disabled) modify_valve_pump_tec(0x80,0x0);
    else modify_valve_pump_tec(0x80,0x80);
    status = tempCntrlStep(&tempCntrlCavity);
    writebackRegisters(regList,sizeof(regList)/sizeof(unsigned int));
    return status;
}

int tempCntrlHeaterInit(void)
{
    static float zero = 0.0;
    TempCntrl *t = &tempCntrlHeater;
    PidParamsRef *p = &(t->pidParamsRef);
    PidState *s  = &(t->pidState);
    p->r_        = (float *)registerAddr(HEATER_TEMP_CNTRL_SETPOINT_REGISTER);
    p->b_        = (float *)registerAddr(HEATER_TEMP_CNTRL_B_REGISTER);
    p->c_        = (float *)registerAddr(HEATER_TEMP_CNTRL_C_REGISTER);
    p->h_        = (float *)registerAddr(HEATER_TEMP_CNTRL_H_REGISTER);
    p->K_        = (float *)registerAddr(HEATER_TEMP_CNTRL_K_REGISTER);
    p->Ti_       = (float *)registerAddr(HEATER_TEMP_CNTRL_TI_REGISTER);
    p->Td_       = (float *)registerAddr(HEATER_TEMP_CNTRL_TD_REGISTER);
    p->N_        = (float *)registerAddr(HEATER_TEMP_CNTRL_N_REGISTER);
    p->S_        = (float *)registerAddr(HEATER_TEMP_CNTRL_S_REGISTER);
    p->Imax_     = (float *)registerAddr(HEATER_TEMP_CNTRL_IMAX_REGISTER);
    p->Amin_     = (float *)registerAddr(HEATER_TEMP_CNTRL_AMIN_REGISTER);
    p->Amax_     = (float *)registerAddr(HEATER_TEMP_CNTRL_AMAX_REGISTER);
    p->ffwd_     = (float *)(&zero);
    t->disabledValue = 0x0;
    t->userSetpoint_ = (float *)registerAddr(HEATER_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    t->state_    = (unsigned int *)registerAddr(HEATER_TEMP_CNTRL_STATE_REGISTER);
    t->tol_      = (float *)registerAddr(HEATER_TEMP_CNTRL_TOLERANCE_REGISTER);
    t->activeBit_  = DAS_STATUS_HeaterTempCntrlActiveBit;
    t->lockBit_    = DAS_STATUS_HeaterTempCntrlLockedBit;
    t->swpMin_   = (float *)registerAddr(HEATER_TEMP_CNTRL_SWEEP_MIN_REGISTER);
    t->swpMax_   = (float *)registerAddr(HEATER_TEMP_CNTRL_SWEEP_MAX_REGISTER);
    t->swpInc_   = (float *)registerAddr(HEATER_TEMP_CNTRL_SWEEP_INCR_REGISTER);
    t->extMax_   = 0;
    t->prbsAmp_  = (float *)registerAddr(HEATER_PRBS_AMPLITUDE_REGISTER);
    t->prbsMean_ = (float *)registerAddr(HEATER_PRBS_MEAN_REGISTER);
    t->prbsGen_  = (unsigned int *)registerAddr(HEATER_PRBS_GENPOLY_REGISTER);
    t->temp_     = (float *)registerAddr(CAVITY_TEC_REGISTER);
    t->extTemp_  = 0;
    t->dasTemp_  = (float *)registerAddr(DAS_TEMPERATURE_REGISTER);
    t->tec_      = (float *)registerAddr(HEATER_MARK_REGISTER);
    t->manualTec_ = (float *)registerAddr(HEATER_MANUAL_MARK_REGISTER);
    t->swpDir    = 1;
    *(t->state_)  = TEMP_CNTRL_DisabledState;
    resetDasStatusBit(t->lockBit_);
    t->lockCount = 0;
    t->unlockCount = 0;
    t->firstIteration = TRUE;
    *(t->tec_) = t->lastTec = s->a = s->u = t->disabledValue;
    s->perr = 0.0;
    s->derr1 = 0.0;
    s->derr2 = 0.0;
    s->Dincr = 0.0;
    return STATUS_OK;
}

int tempCntrlHeaterStep(void)
{
    unsigned int regList[] = {HEATER_TEMP_CNTRL_SETPOINT_REGISTER,
                              HEATER_TEMP_CNTRL_STATE_REGISTER,
                              HEATER_MARK_REGISTER
                             };
    int status;
    status = tempCntrlStep(&tempCntrlHeater);
    writebackRegisters(regList,sizeof(regList)/sizeof(unsigned int));
    return status;
}
