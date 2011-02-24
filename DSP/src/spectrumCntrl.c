/*
 * FILE:
 *   spectrumCntrl.c
 *
 * DESCRIPTION:
 *   Spectrum controller routines
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   4-Aug-2009  sze  Initial version.
 *  12-Oct-2009  sze  Modified behavior of increment bit in subSchemeId so that it increments count after last ringdown of a scheme row
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include "interface.h"
#include "registers.h"
#include "spectrumCntrl.h"
#include "tunerCntrl.h"
#include "dspAutogen.h"
#include "dspData.h"
#include "fpga.h"

#include <math.h>
#include <stdio.h>
#include "fastrts67x.h"

#ifdef TESTING
#include "testHarness.h"
#else
#include "dspMaincfg.h"
#endif

RingdownParamsType nextRdParams;
SpectCntrlParams spectCntrlParams;

int spectCntrlInit(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
    s->state_ = (SPECT_CNTRL_StateType *)registerAddr(SPECT_CNTRL_STATE_REGISTER);
    s->mode_  = (unsigned int *)registerAddr(SPECT_CNTRL_MODE_REGISTER);
    s->active_= (unsigned int *)registerAddr(SPECT_CNTRL_ACTIVE_SCHEME_REGISTER);
    s->next_  = (unsigned int *)registerAddr(SPECT_CNTRL_NEXT_SCHEME_REGISTER);
    s->iter_  = (unsigned int *)registerAddr(SPECT_CNTRL_SCHEME_ITER_REGISTER);
    s->row_   = (unsigned int *)registerAddr(SPECT_CNTRL_SCHEME_ROW_REGISTER);
    s->dwell_ = (unsigned int *)registerAddr(SPECT_CNTRL_DWELL_COUNT_REGISTER);
    s->laserTemp_[0] = (float *)registerAddr(LASER1_TEMPERATURE_REGISTER);
    s->laserTemp_[1] = (float *)registerAddr(LASER2_TEMPERATURE_REGISTER);
    s->laserTemp_[2] = (float *)registerAddr(LASER3_TEMPERATURE_REGISTER);
    s->laserTemp_[3] = (float *)registerAddr(LASER4_TEMPERATURE_REGISTER);
    s->coarseLaserCurrent_[0] = (float *)registerAddr(LASER1_MANUAL_COARSE_CURRENT_REGISTER);
    s->coarseLaserCurrent_[1] = (float *)registerAddr(LASER2_MANUAL_COARSE_CURRENT_REGISTER);
    s->coarseLaserCurrent_[2] = (float *)registerAddr(LASER3_MANUAL_COARSE_CURRENT_REGISTER);
    s->coarseLaserCurrent_[3] = (float *)registerAddr(LASER4_MANUAL_COARSE_CURRENT_REGISTER);
    s->laserTempUserSetpoint_[0] = (float *)registerAddr(LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    s->laserTempUserSetpoint_[1] = (float *)registerAddr(LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    s->laserTempUserSetpoint_[2] = (float *)registerAddr(LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    s->laserTempUserSetpoint_[3] = (float *)registerAddr(LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER);
    s->laserTempSetpoint_[0] = (float *)registerAddr(LASER1_TEMP_CNTRL_SETPOINT_REGISTER);
    s->laserTempSetpoint_[1] = (float *)registerAddr(LASER2_TEMP_CNTRL_SETPOINT_REGISTER);
    s->laserTempSetpoint_[2] = (float *)registerAddr(LASER3_TEMP_CNTRL_SETPOINT_REGISTER);
    s->laserTempSetpoint_[3] = (float *)registerAddr(LASER4_TEMP_CNTRL_SETPOINT_REGISTER);
    s->pztIncrPerFsr_ = (float *)registerAddr(PZT_INCR_PER_CAVITY_FSR);
    s->pztOffsetUpdateFactor_ = (float *)registerAddr(PZT_OFFSET_UPDATE_FACTOR);
    s->pztOffsetByVirtualLaser_[0] = (float *)registerAddr(PZT_OFFSET_VIRTUAL_LASER1);
    s->pztOffsetByVirtualLaser_[1] = (float *)registerAddr(PZT_OFFSET_VIRTUAL_LASER2);
    s->pztOffsetByVirtualLaser_[2] = (float *)registerAddr(PZT_OFFSET_VIRTUAL_LASER3);
    s->pztOffsetByVirtualLaser_[3] = (float *)registerAddr(PZT_OFFSET_VIRTUAL_LASER4);
    s->pztOffsetByVirtualLaser_[4] = (float *)registerAddr(PZT_OFFSET_VIRTUAL_LASER5);
    s->pztOffsetByVirtualLaser_[5] = (float *)registerAddr(PZT_OFFSET_VIRTUAL_LASER6);
    s->pztOffsetByVirtualLaser_[6] = (float *)registerAddr(PZT_OFFSET_VIRTUAL_LASER7);
    s->pztOffsetByVirtualLaser_[7] = (float *)registerAddr(PZT_OFFSET_VIRTUAL_LASER8);
    s->schemeOffsetByVirtualLaser_[0] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER1);
    s->schemeOffsetByVirtualLaser_[1] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER2);
    s->schemeOffsetByVirtualLaser_[2] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER3);
    s->schemeOffsetByVirtualLaser_[3] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER4);
    s->schemeOffsetByVirtualLaser_[4] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER5);
    s->schemeOffsetByVirtualLaser_[5] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER6);
    s->schemeOffsetByVirtualLaser_[6] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER7);
    s->schemeOffsetByVirtualLaser_[7] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER8);
    s->etalonTemperature_ = (float *)registerAddr(ETALON_TEMPERATURE_REGISTER);
    s->cavityPressure_ = (float *)registerAddr(CAVITY_PRESSURE_REGISTER);
    s->ambientPressure_ = (float *)registerAddr(AMBIENT_PRESSURE_REGISTER);
    s->defaultThreshold_ = (unsigned int *)registerAddr(SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER);
    s->virtLaser_ = (VIRTUAL_LASER_Type *)registerAddr(VIRTUAL_LASER_REGISTER);
    s->dasStatus_ = (unsigned int *)registerAddr(DAS_STATUS_REGISTER);
    s->schemeCounter_ =  0;
    s->incrFlag_ = 0;
    s->incrCounter_ = 0;
    s->incrCounterNext_ = 1;
    s->useMemo_ = 0;
    switchToRampMode();
    return STATUS_OK;
}

int spectCntrlStep(void)
// This is called every 100ms from the scheduler thread to start spectrum acquisition
{
    SpectCntrlParams *s=&spectCntrlParams;
    static SPECT_CNTRL_StateType prevState = SPECT_CNTRL_IdleState;
    SPECT_CNTRL_StateType stateAtStart;

    stateAtStart = *(s->state_);
    if (SPECT_CNTRL_StartingState == *(s->state_))
    {
        s->useMemo_ = 0;
        s->incrCounterNext_ = s->incrCounter_ + 1;
        s->schemeCounter_++;
        setAutomaticLaserTemperatureControl();
        setAutomaticLaserCurrentControl();
        *(s->state_) = SPECT_CNTRL_RunningState;
        if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_) ||
                SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) ||
                SPECT_CNTRL_SchemeSequenceMode == *(s->mode_))
        {
            // Enable frequency locking for schemes
            changeBitsFPGA(FPGA_RDMAN+RDMAN_OPTIONS, RDMAN_OPTIONS_LOCK_ENABLE_B, RDMAN_OPTIONS_LOCK_ENABLE_W, 1);
            *(s->iter_) = 0;
            *(s->row_) = 0;
            *(s->dwell_) = 0;
            // If we start in sequence mode, automatically start at the beginning
            if (SPECT_CNTRL_SchemeSequenceMode == *(s->mode_))
            {
                schemeSequence->currentIndex =  0;
                *(s->active_) = schemeSequence->schemeIndices[schemeSequence->currentIndex];
            }
            // Starting acquisition always goes to the scheme specified by "next"
            else *(s->active_) = *(s->next_);
        }
    }
    else if (SPECT_CNTRL_StartManualState == *(s->state_))
    {
        s->useMemo_ = 0;
        s->incrCounterNext_ = s->incrCounter_ + 1;
        s->schemeCounter_++;
        *(s->mode_) = SPECT_CNTRL_ContinuousManualTempMode;
        setAutomaticLaserCurrentControl(); // To allow ringdowns
        *(s->state_) = SPECT_CNTRL_RunningState;
    }
    else if (SPECT_CNTRL_RunningState == *(s->state_))
    {
        if (SPECT_CNTRL_StartingState == prevState ||
                SPECT_CNTRL_StartManualState == prevState ||
                SPECT_CNTRL_PausedState   == prevState)
        {
            switchToRampMode();
            // Enable laser shutdown
            // TODO: Handle SOA shutdown
            changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W, 1);
            changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W, 1);

            SEM_pendBinary(&SEM_startRdCycle,100);	// Eat up anything pending
            SEM_postBinary(&SEM_startRdCycle);
        }
    }
    else if (SPECT_CNTRL_IdleState == *(s->state_))
    {
        if (SPECT_CNTRL_IdleState != prevState)
        {
            switchToRampMode();
            setManualControl();
        }
        s->useMemo_ = 0;
    }
    else switchToRampMode();

    prevState = stateAtStart;

    return STATUS_OK;
}

#define PI 3.141592654
void spectCntrl(void)
{
    int bank, status, nloops;
    int *counter = (int*)(REG_BASE+4*RD_INITIATED_COUNT_REGISTER);

    nloops = 0;
    while (1)
    {
        SEM_pendBinary(&SEM_startRdCycle,SYS_FOREVER);
        (*counter)++;
        
        // The next while loop periodically checks to see if we are allowed
        //  to start the ringdown
        while (1)
        {
            status = readFPGA(FPGA_RDMAN+RDMAN_STATUS);
            // Can start a new ringdown if the manager is not busy and if the
            //  bank for acquisition is not in use
            if ( !(status & 1<<RDMAN_STATUS_BUSY_B) )
            {
                bank = (status & 1<<RDMAN_STATUS_BANK_B) >> RDMAN_STATUS_BANK_B;
                if (0 == bank)
                {
                    if ( !(status & 1<<RDMAN_STATUS_BANK0_IN_USE_B) ) break;
                }
                else   // 1 == bank
                {
                    if ( !(status & 1<<RDMAN_STATUS_BANK1_IN_USE_B) ) break;
                }
                if (nloops == 0) message_puts(LOG_LEVEL_INFO,"Waiting for bank to become available");
            }
            else
            {
                if (nloops == 0) message_puts(LOG_LEVEL_STANDARD,"Ringdown manager busy");
            }
            // Wait around for another ms and recheck. Reset manager if busy for more
            //  than 50ms.
            nloops++;
            SEM_pendBinary(&SEM_waitForRdMan,SYS_FOREVER);
            if (nloops > 50) {
                changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_RESET_RDMAN_B,
                               RDMAN_CONTROL_RESET_RDMAN_W,1);
                SEM_pendBinary(&SEM_waitForRdMan,SYS_FOREVER);
                message_puts(LOG_LEVEL_STANDARD,"Resetting ringdown manager");
                nloops = 0;
                break;
            }
        }
        setupNextRdParams();
        // Then initiate the ringdown...
        changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_START_RD_B,
                       RDMAN_CONTROL_START_RD_W,1);
    }
}

static int activeMemo = -1, rowMemo = -1;
void setupLaserTemperatureAndPztOffset(int useMemo)
{
    SpectCntrlParams *s=&spectCntrlParams;
    unsigned int aLaserNum, vLaserNum;
    volatile SchemeTableType *schemeTable = &schemeTables[*(s->active_)];
    volatile VirtualLaserParamsType *vLaserParams;
    int pztOffset;
    float laserTemp;
    
    if (SPECT_CNTRL_ContinuousMode == *(s->mode_))
    {
        vLaserParams = &virtualLaserParams[*(s->virtLaser_)];
        // In continuous mode, we use the parameter values currently in the registers
        vLaserNum = 1 + (unsigned int)*(s->virtLaser_);
        aLaserNum = 1 + (vLaserParams->actualLaser & 0x3);
        // *(s->laserTempSetpoint_[aLaserNum - 1]) = *(s->laserTempUserSetpoint_[aLaserNum - 1]);
        pztOffset = *(s->pztOffsetByVirtualLaser_[vLaserNum - 1]);
        writeFPGA(FPGA_TWGEN+TWGEN_PZT_OFFSET,pztOffset % 65536);
    }
    else if (SPECT_CNTRL_ContinuousManualTempMode == *(s->mode_))
    {   // With manual temperature control, there are no virtual lasers and the PZT offset is zero
        writeFPGA(FPGA_TWGEN+TWGEN_PZT_OFFSET,0);    
    }
    else {    
        if (useMemo && *(s->active_) == activeMemo && *(s->row_) == rowMemo) return;
        *(s->virtLaser_) = (VIRTUAL_LASER_Type) schemeTable->rows[*(s->row_)].virtualLaser;
        vLaserNum = 1 + (unsigned int)*(s->virtLaser_);
        vLaserParams = &virtualLaserParams[vLaserNum-1];
        laserTemp = 0.001 * schemeTable->rows[*(s->row_)].laserTemp; // Scheme temperatures are in milli-degrees C
        aLaserNum = 1 + (vLaserParams->actualLaser & 0x3);
        if (laserTemp != 0.0)
        {
            *(s->laserTempSetpoint_[aLaserNum - 1]) = laserTemp + *(s->schemeOffsetByVirtualLaser_[vLaserNum - 1]);
        }
    
        // The PZT offset for this row is the sum of the PZT offset for the virtual laser from the appropriate
        //  register and any setpoint in the scheme file. Note that all PZT values are interpreted modulo 65536
    
        pztOffset = *(s->pztOffsetByVirtualLaser_[vLaserNum - 1]) + schemeTable->rows[*(s->row_)].pztSetpoint;
        writeFPGA(FPGA_TWGEN+TWGEN_PZT_OFFSET,pztOffset % 65536);
    
        activeMemo = *(s->active_);
        rowMemo = *(s->row_);
    }
}

void setupNextRdParams(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
    RingdownParamsType *r=&nextRdParams;

    unsigned int laserNum, laserTempAsInt;
    volatile SchemeTableType *schemeTable;
    volatile VirtualLaserParamsType *vLaserParams;
    float setpoint, dp, theta, ratio1Multiplier, ratio2Multiplier;

    s->incrCounter_ = s->incrCounterNext_;
    if (SPECT_CNTRL_ContinuousMode == *(s->mode_))
    {
        // In continuous mode, we run with the parameter values currently in the registers
        vLaserParams = &virtualLaserParams[*(s->virtLaser_)];
        laserNum = vLaserParams->actualLaser & 0x3;
        r->injectionSettings = (*(s->virtLaser_) << 2) | laserNum;
        r->laserTemperature = *(s->laserTemp_[laserNum]);
        r->coarseLaserCurrent = *(s->coarseLaserCurrent_[laserNum]);
        r->etalonTemperature = *(s->etalonTemperature_);
        r->cavityPressure = *(s->cavityPressure_);
        r->ambientPressure = *(s->ambientPressure_);
        r->schemeTableAndRow = 0;
        r->countAndSubschemeId = (s->incrCounter_ << 16);
        r->ringdownThreshold = *(s->defaultThreshold_);
        r->status = 0;
        laserTempAsInt = 1000.0*r->laserTemperature;
        // Set up the FPGA registers for this ringdown
        changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W, laserNum);
        writeFPGA(FPGA_RDMAN+RDMAN_THRESHOLD,r->ringdownThreshold);
    }
    else if (SPECT_CNTRL_ContinuousManualTempMode == *(s->mode_))
    {
        // In this mode there are no virtual lasers. Get actual laser number from FPGA
        laserNum = readBitsFPGA(FPGA_INJECT+INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W);
        r->injectionSettings = laserNum;
        r->laserTemperature = *(s->laserTemp_[laserNum]);
        r->coarseLaserCurrent = *(s->coarseLaserCurrent_[laserNum]);
        r->etalonTemperature = *(s->etalonTemperature_);
        r->cavityPressure = *(s->cavityPressure_);
        r->ambientPressure = *(s->ambientPressure_);
        r->schemeTableAndRow = 0;
        r->countAndSubschemeId = (s->incrCounter_ << 16);
        r->ringdownThreshold = *(s->defaultThreshold_);
        r->status = 0;
        laserTempAsInt = 1000.0*r->laserTemperature;
        // Set up the FPGA registers for this ringdown
        writeFPGA(FPGA_RDMAN+RDMAN_THRESHOLD,r->ringdownThreshold);
    }
    else    // We are running a scheme
    {
        do {
            // This loop is here so that a dwell count of zero can be used to set up the
            //  laser temperature without triggering a ringdown
            setupLaserTemperatureAndPztOffset(s->useMemo_);
            s->useMemo_ = 1;
            schemeTable = &schemeTables[*(s->active_)];
            if (schemeTable->rows[*(s->row_)].dwellCount > 0) break;
            s->incrFlag_ = schemeTable->rows[*(s->row_)].subschemeId & SUBSCHEME_ID_IncrMask;
            advanceSchemeRow();
            s->incrCounter_ = s->incrCounterNext_;
        }
        while (1);
        // while (*(s->row_) != 0);
        schemeTable = &schemeTables[*(s->active_)];
        *(s->virtLaser_) = (VIRTUAL_LASER_Type) schemeTable->rows[*(s->row_)].virtualLaser;
        vLaserParams = &virtualLaserParams[*(s->virtLaser_)];
        setpoint = schemeTable->rows[*(s->row_)].setpoint;
        laserNum = vLaserParams->actualLaser & 0x3;
        r->injectionSettings = (*(s->virtLaser_) << 2) | laserNum;
        r->laserTemperature = *(s->laserTemp_[laserNum]);
        r->coarseLaserCurrent = *(s->coarseLaserCurrent_[laserNum]);
        r->etalonTemperature = *(s->etalonTemperature_);
        r->cavityPressure = *(s->cavityPressure_);
        r->ambientPressure = *(s->ambientPressure_);
        r->schemeTableAndRow = (*(s->active_) << 16) | (*(s->row_) & 0xFFFF);

        //laserTempAsInt = schemeTable->rows[*(s->row_)].laserTemp;
        laserTempAsInt = 1000.0*r->laserTemperature;

        // If SUBSCHEME_ID_IncrMask is set, this means that we should increment
        //  s->incrCounter_ the next time that we advance to the next scheme row
        s->incrFlag_ = schemeTable->rows[*(s->row_)].subschemeId & SUBSCHEME_ID_IncrMask;
        r->countAndSubschemeId = (s->incrCounter_ << 16) | (schemeTable->rows[*(s->row_)].subschemeId & 0xFFFF);
        r->ringdownThreshold   = schemeTable->rows[*(s->row_)].threshold;
        if (r->ringdownThreshold == 0) r->ringdownThreshold = *(s->defaultThreshold_);
        r->status = (s->schemeCounter_ & RINGDOWN_STATUS_SequenceMask);
        if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_) ||
                SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) ||
                SPECT_CNTRL_SchemeSequenceMode == *(s->mode_)) r->status |= RINGDOWN_STATUS_SchemeActiveMask;
        // Determine if we are on the last ringdown of the scheme and set status bits appropriately
        if (*(s->iter_) >= schemeTables[*(s->active_)].numRepeats-1 &&
                *(s->row_)  >= schemeTables[*(s->active_)].numRows-1 &&
                *(s->dwell_) >= schemeTables[*(s->active_)].rows[*(s->row_)].dwellCount-1)
        {
            // We need to decide if acquisition is continuing or not. Acquisition stops if the scheme is run in Single mode, or
            //  if we are running a non-looping sequence and have reached the last scheme in the sequence
            if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_) ||
                    (SPECT_CNTRL_SchemeSequenceMode == *(s->mode_)
                     && schemeSequence->currentIndex == schemeSequence->numberOfIndices-1
                     && !schemeSequence->loopFlag)) r->status |= RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask;
            else if (SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) ||
                     SPECT_CNTRL_SchemeSequenceMode == *(s->mode_)) r->status |= RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask;
        }

        // Correct the setpoint angle using the etalon temperature and ambient pressure
        dp = r->ambientPressure - vLaserParams->calPressure;
        theta = setpoint - vLaserParams->tempSensitivity*(r->etalonTemperature-vLaserParams->calTemp) -
                (vLaserParams->pressureC0 + dp*(vLaserParams->pressureC1 + dp*(vLaserParams->pressureC2 + dp*vLaserParams->pressureC3)));

        // Compute the ratio multipliers corresponding to this setpoint
        ratio1Multiplier = ((-sinsp(theta + vLaserParams->phase))/(vLaserParams->ratio1Scale * cossp(vLaserParams->phase)));
        ratio2Multiplier = ((cossp(theta))/(vLaserParams->ratio2Scale * cossp(vLaserParams->phase)));

        // Set up the FPGA registers for this ringdown
        changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W, laserNum);

        writeFPGA(FPGA_LASERLOCKER+LASERLOCKER_RATIO1_MULTIPLIER, (int)(ratio1Multiplier*32767.0));
        writeFPGA(FPGA_LASERLOCKER+LASERLOCKER_RATIO2_MULTIPLIER, (int)(ratio2Multiplier*32767.0));

        writeFPGA(FPGA_LASERLOCKER+LASERLOCKER_RATIO1_CENTER, (int)(vLaserParams->ratio1Center*32768.0));
        writeFPGA(FPGA_LASERLOCKER+LASERLOCKER_RATIO2_CENTER, (int)(vLaserParams->ratio2Center*32768.0));

        writeFPGA(FPGA_RDMAN+RDMAN_THRESHOLD,r->ringdownThreshold);
        // Also write the laser temperature to the wavelength monitor simulator, solely to allow
        //  the simulator to calculate an angle that depends on laser temperature as well as current
        writeFPGA(FPGA_WLMSIM+WLMSIM_LASER_TEMP,laserTempAsInt);

    }
    writeFPGA(FPGA_RDMAN+RDMAN_PARAM0,*(uint32*)&r->injectionSettings);
    writeFPGA(FPGA_RDMAN+RDMAN_PARAM1,*(uint32*)&r->laserTemperature);
    writeFPGA(FPGA_RDMAN+RDMAN_PARAM2,*(uint32*)&r->coarseLaserCurrent);
    writeFPGA(FPGA_RDMAN+RDMAN_PARAM3,*(uint32*)&r->etalonTemperature);
    writeFPGA(FPGA_RDMAN+RDMAN_PARAM4,*(uint32*)&r->cavityPressure);
    writeFPGA(FPGA_RDMAN+RDMAN_PARAM5,*(uint32*)&r->ambientPressure);
    writeFPGA(FPGA_RDMAN+RDMAN_PARAM6,*(uint32*)&r->schemeTableAndRow);
    writeFPGA(FPGA_RDMAN+RDMAN_PARAM7,*(uint32*)&r->countAndSubschemeId);
    writeFPGA(FPGA_RDMAN+RDMAN_PARAM8,*(uint32*)&r->ringdownThreshold);
    writeFPGA(FPGA_RDMAN+RDMAN_PARAM9,*(uint32*)&r->status);
}

void modifyParamsOnTimeout(unsigned int schemeCount)
// If a ringdown timeout occurs, i.e., if there is no ringdown within the allotted interval, we
//  proceed to the next scheme row, short-circuiting the dwell count requested. An entry is
//  placed on the ringdown buffer queue with a special status when this occurs. It may be necessary
//  to modify the bits which indicate if we are at the end of a scheme as a result of this
//  short-circuiting.
{
    SpectCntrlParams *s=&spectCntrlParams;
    RingdownParamsType *r=&nextRdParams;
    r->status |= RINGDOWN_STATUS_RingdownTimeout;
    if (s->schemeCounter_ != schemeCount)
    {
        // We have advanced to another scheme, so set the end-of-scheme status bits appropriately
        r->status &= ~(RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask | RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask);
        // We need to decide if acquisition is continuing or not. Acquisition stops if the scheme is run in Single mode, or
        //  if we are running a non-looping sequence and have reached the last scheme in the sequence
        if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_) ||
                (SPECT_CNTRL_SchemeSequenceMode == *(s->mode_)
                 && schemeSequence->currentIndex == schemeSequence->numberOfIndices-1
                 && !schemeSequence->loopFlag)) r->status |= RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask;
        else if (SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) ||
                 SPECT_CNTRL_SchemeSequenceMode == *(s->mode_)) r->status |= RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask;
    }
}

unsigned int getSpectCntrlSchemeCount(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
    return s->schemeCounter_;
}

void setAutomaticLaserTemperatureControl(void)
{
    DataType data;
    
    data.asInt = TEMP_CNTRL_AutomaticState;
    writeRegister(LASER1_TEMP_CNTRL_STATE_REGISTER,data);
    writeRegister(LASER2_TEMP_CNTRL_STATE_REGISTER,data);
    writeRegister(LASER3_TEMP_CNTRL_STATE_REGISTER,data);
    writeRegister(LASER4_TEMP_CNTRL_STATE_REGISTER,data);
}

void setAutomaticLaserCurrentControl(void)
// Set optical injection, laser current and laser temperature controllers to automatic mode. This should be called by the
//  scheduler thread in response to a request to start a scheme, otherwise a race condition could occur
//  leading to the wrong value for INJECT_CONTROL_MODE.
{
    DataType data;

    data.asInt = LASER_CURRENT_CNTRL_AutomaticState;
    writeRegister(LASER1_CURRENT_CNTRL_STATE_REGISTER,data);
    writeRegister(LASER2_CURRENT_CNTRL_STATE_REGISTER,data);
    writeRegister(LASER3_CURRENT_CNTRL_STATE_REGISTER,data);
    writeRegister(LASER4_CURRENT_CNTRL_STATE_REGISTER,data);


    // Setting the FPGA optical injection block to automatic mode has to be done independently
    //  of setting the individual current controllers. Care is needed since the current controllers
    //  periodically write to the INJECT_CONTROL register.

    changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL,INJECT_CONTROL_MODE_B,INJECT_CONTROL_MODE_W,1);
}

void setManualControl(void)
// Set optical injection and laser current controllers to manual mode.
{
    DataType data;

    // The FPGA optical injection block is placed in manual mode
    // when any laser current controller is in the manual state
    
    data.asInt = LASER_CURRENT_CNTRL_ManualState;
    writeRegister(LASER1_CURRENT_CNTRL_STATE_REGISTER,data);
    writeRegister(LASER2_CURRENT_CNTRL_STATE_REGISTER,data);
    writeRegister(LASER3_CURRENT_CNTRL_STATE_REGISTER,data);
    writeRegister(LASER4_CURRENT_CNTRL_STATE_REGISTER,data);
}

void validateSchemePosition(void)
// Ensure that the dwell count, scheme row and scheme iteration values are valid and reset
//  them to zero if not
{
    SpectCntrlParams *s=&spectCntrlParams;
    if (*(s->active_) >= NUM_SCHEME_TABLES)
    {
        message_puts(LOG_LEVEL_STANDARD,"Active scheme index is out of range, resetting to zero");
        *(s->active_) = 0;
    }
    if (*(s->iter_) >= schemeTables[*(s->active_)].numRepeats)
    {
        message_puts(LOG_LEVEL_STANDARD,"Scheme iteration is out of range, resetting to zero");
        *(s->iter_) = 0;
    }
    if (*(s->row_) >= schemeTables[*(s->active_)].numRows)
    {
        message_puts(LOG_LEVEL_STANDARD,"Scheme row is out of range, resetting to zero");
        *(s->row_) = 0;
    }
    if (*(s->dwell_) >= schemeTables[*(s->active_)].rows[*(s->row_)].dwellCount)
    {
        message_puts(LOG_LEVEL_STANDARD,"Dwell count is out of range, resetting to zero");
        *(s->dwell_) = 0;
    }
}

void advanceDwellCounter(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
    *(s->dwell_) = *(s->dwell_) + 1;
    if (*(s->dwell_) >= schemeTables[*(s->active_)].rows[*(s->row_)].dwellCount)
    {
        advanceSchemeRow();
    }
}

void advanceSchemeRow(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
    *(s->row_) = *(s->row_) + 1;
    if (s->incrFlag_)
    {
        s->incrCounterNext_ = s->incrCounter_ + 1;
        s->incrFlag_ = 0;
    }
    if (*(s->row_) >= schemeTables[*(s->active_)].numRows)
    {
        advanceSchemeIteration();
    }
    else
    {
        *(s->dwell_) = 0;
    }
}

void advanceSchemeIteration(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
    *(s->iter_) = *(s->iter_) + 1;
    if (*(s->iter_) >= schemeTables[*(s->active_)].numRepeats)
    {
        advanceScheme();
    }
    else
    {
        *(s->row_) = 0;
        *(s->dwell_) = 0;
    }
}

void advanceScheme(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
    s->schemeCounter_++;
    s->incrCounterNext_ = s->incrCounter_ + 1;
    if (SPECT_CNTRL_SchemeSequenceMode == *(s->mode_))
    {
        schemeSequence->currentIndex += 1;
        if (schemeSequence->currentIndex >= schemeSequence->numberOfIndices)
        {
            if (schemeSequence->loopFlag) schemeSequence->currentIndex = 0;
            else *(s->state_) = SPECT_CNTRL_IdleState;
        }
        *(s->active_) = schemeSequence->schemeIndices[schemeSequence->currentIndex];
    }
    else *(s->active_) = *(s->next_);
    *(s->iter_) = 0;
    *(s->row_) = 0;
    *(s->dwell_) = 0;
    if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_))
        *(s->state_) = SPECT_CNTRL_IdleState;
}

int activeLaserTempLocked(void)
// This determines if the laser temperature control loop for the currently selected laser
//  in the scheme is locked
{
    SpectCntrlParams *s=&spectCntrlParams;
    unsigned int dasStatus = *(s->dasStatus_);
    unsigned int aLaserNum = 1+readBitsFPGA(FPGA_INJECT+INJECT_CONTROL,INJECT_CONTROL_LASER_SELECT_B,INJECT_CONTROL_LASER_SELECT_W);

    switch (aLaserNum) {
        case 1:
            return 0 != (dasStatus & (1<<DAS_STATUS_Laser1TempCntrlLockedBit));
        case 2:
            return 0 != (dasStatus & (1<<DAS_STATUS_Laser2TempCntrlLockedBit));
        case 3:
            return 0 != (dasStatus & (1<<DAS_STATUS_Laser3TempCntrlLockedBit));
        case 4:
            return 0 != (dasStatus & (1<<DAS_STATUS_Laser4TempCntrlLockedBit));
    }
    return 0;
}

void spectCntrlError(void)
// This is called to place the spectrum controller subsystem in a sane state
//  in response to an error or abort condition
{
    SpectCntrlParams *s=&spectCntrlParams;

    *(s->state_) = SPECT_CNTRL_ErrorState;
    // Eat up posted semaphores
    SEM_pend(&SEM_rdFitting,0);
    SEM_pend(&SEM_rdDataMoving,0);
    SEM_pendBinary(&SEM_startRdCycle,0);

    // Reset the RDMAN block, clear bank in use bits, acknowledge all interrupts
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_RESET_RDMAN_B,
                   RDMAN_CONTROL_RESET_RDMAN_W,1);
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_BANK0_CLEAR_B,
                   RDMAN_CONTROL_BANK0_CLEAR_W,1);
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_BANK1_CLEAR_B,
                   RDMAN_CONTROL_BANK1_CLEAR_W,1);
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_RD_IRQ_ACK_B,
                   RDMAN_CONTROL_RD_IRQ_ACK_W,1);
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_ACQ_DONE_ACK_B,
                   RDMAN_CONTROL_ACQ_DONE_ACK_W,1);

    // Indicate both ringdown buffers are available
    SEM_postBinary(&SEM_rdBuffer0Available);
    SEM_postBinary(&SEM_rdBuffer1Available);
    switchToRampMode();
    message_puts(LOG_LEVEL_CRITICAL,"Spectrum controller enters error state.");
}

void update_wlmsim_laser_temp(void)
// This is called periodically by the scheduler to update the laser temperature register of the WLM simulator
//  with the temperature of the selected laser. This should only be done if the spectrum controller is not
//  in the starting or running states.
{
    SpectCntrlParams *s=&spectCntrlParams;
    if (*(s->state_) != SPECT_CNTRL_StartingState && *(s->state_) != SPECT_CNTRL_RunningState)
    {
        unsigned int laserNum = readBitsFPGA(FPGA_INJECT+INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W);
        unsigned int laserTempAsInt = *(s->laserTemp_[laserNum]) * 1000;
        writeFPGA(FPGA_WLMSIM+WLMSIM_LASER_TEMP,laserTempAsInt);
    }
}
