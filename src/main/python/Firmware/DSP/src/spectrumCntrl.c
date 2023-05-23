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
#include "scopeHandler.h"
#include "spectrumCntrl.h"
#include "tunerCntrl.h"
#include "dspAutogen.h"
#include "dspData.h"
#include "fpga.h"
#include "rdHandlers.h"
#include "sgdbrCurrentSource.h"

#include <math.h>
#include <stdio.h>
#include "fastrts67x.h"

#ifdef TESTING
#include "testHarness.h"
#else
#include "dspMaincfg.h"
#endif

#define min(x, y) ((x) < (y) ? (x) : (y))

RingdownParamsType nextRdParams;
SpectCntrlParams spectCntrlParams;

// The pztOffsets array which is used to set the position of the PZT during ringowns is kept separate from
//  the values in the registers s->pztOffsetByVirtualLaser so that we can keep the PZT position fixed during
//  the execution of a scheme for those applications (typically using laser current tuning) which rely on
//  precisely spaced cavity modes over a scheme. For such applications, the pztOffsets are updated from the
//  register values at the start of each scheme (in advanceScheme) so that offset changes made the registers do
//  not take effect until the next scheme starts.
static float pztOffsets[NUM_VIRTUAL_LASERS];
// The pztLctOffset is used to provide an update for the PZT position on a fast (per-ringdown) timescale in
//  laser current tuning mode for applications where gas composition and pressure changes affect the refractive
//  index. The frequency separation between the cavity modes can no longer be relied upon to be preciesly equal.
float pztLctOffset;

int spectCntrlInit(void)
{
    SpectCntrlParams *s = &spectCntrlParams;
    s->state_ = (SPECT_CNTRL_StateType *)registerAddr(SPECT_CNTRL_STATE_REGISTER);
    s->mode_ = (unsigned int *)registerAddr(SPECT_CNTRL_MODE_REGISTER);
    s->active_ = (unsigned int *)registerAddr(SPECT_CNTRL_ACTIVE_SCHEME_REGISTER);
    s->next_ = (unsigned int *)registerAddr(SPECT_CNTRL_NEXT_SCHEME_REGISTER);
    s->iter_ = (unsigned int *)registerAddr(SPECT_CNTRL_SCHEME_ITER_REGISTER);
    s->row_ = (unsigned int *)registerAddr(SPECT_CNTRL_SCHEME_ROW_REGISTER);
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
    s->pztUpdateMode_ = (unsigned int *)registerAddr(PZT_UPDATE_MODE_REGISTER);
    s->schemeOffsetByVirtualLaser_[0] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER1);
    s->schemeOffsetByVirtualLaser_[1] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER2);
    s->schemeOffsetByVirtualLaser_[2] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER3);
    s->schemeOffsetByVirtualLaser_[3] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER4);
    s->schemeOffsetByVirtualLaser_[4] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER5);
    s->schemeOffsetByVirtualLaser_[5] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER6);
    s->schemeOffsetByVirtualLaser_[6] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER7);
    s->schemeOffsetByVirtualLaser_[7] = (float *)registerAddr(SCHEME_OFFSET_VIRTUAL_LASER8);
    s->frontMirrorDac_[0] = (float *)registerAddr(SGDBR_A_CNTRL_FRONT_MIRROR_REGISTER);
    s->frontMirrorDac_[1] = (float *)registerAddr(SGDBR_B_CNTRL_FRONT_MIRROR_REGISTER);
    s->frontMirrorDac_[2] = (float *)registerAddr(SGDBR_C_CNTRL_FRONT_MIRROR_REGISTER);
    s->frontMirrorDac_[3] = (float *)registerAddr(SGDBR_D_CNTRL_FRONT_MIRROR_REGISTER);
    s->backMirrorDac_[0] = (float *)registerAddr(SGDBR_A_CNTRL_BACK_MIRROR_REGISTER);
    s->backMirrorDac_[1] = (float *)registerAddr(SGDBR_B_CNTRL_BACK_MIRROR_REGISTER);
    s->backMirrorDac_[2] = (float *)registerAddr(SGDBR_C_CNTRL_BACK_MIRROR_REGISTER);
    s->backMirrorDac_[3] = (float *)registerAddr(SGDBR_D_CNTRL_BACK_MIRROR_REGISTER);
    s->gainDac_[0] = (float *)registerAddr(SGDBR_A_CNTRL_GAIN_REGISTER);
    s->gainDac_[1] = (float *)registerAddr(SGDBR_B_CNTRL_GAIN_REGISTER);
    s->gainDac_[2] = (float *)registerAddr(SGDBR_C_CNTRL_GAIN_REGISTER);
    s->gainDac_[3] = (float *)registerAddr(SGDBR_D_CNTRL_GAIN_REGISTER);
    s->soaSetting_[0] = (float *)registerAddr(SGDBR_A_CNTRL_SOA_REGISTER);
    s->soaSetting_[1] = (float *)registerAddr(SGDBR_B_CNTRL_SOA_REGISTER);
    s->soaSetting_[2] = (float *)registerAddr(SGDBR_C_CNTRL_SOA_REGISTER);
    s->soaSetting_[3] = (float *)registerAddr(SGDBR_D_CNTRL_SOA_REGISTER);
    s->soaDac[0] = 0.0;
    s->soaDac[1] = 0.0;
    s->soaDac[2] = 0.0;
    s->soaDac[3] = 0.0;
    s->coarsePhaseDac_[0] = (float *)registerAddr(SGDBR_A_CNTRL_COARSE_PHASE_REGISTER);
    s->coarsePhaseDac_[1] = (float *)registerAddr(SGDBR_B_CNTRL_COARSE_PHASE_REGISTER);
    s->coarsePhaseDac_[2] = (float *)registerAddr(SGDBR_C_CNTRL_COARSE_PHASE_REGISTER);
    s->coarsePhaseDac_[3] = (float *)registerAddr(SGDBR_D_CNTRL_COARSE_PHASE_REGISTER);
    s->finePhaseDac_[0] = (float *)registerAddr(SGDBR_A_CNTRL_FINE_PHASE_REGISTER);
    s->finePhaseDac_[1] = (float *)registerAddr(SGDBR_B_CNTRL_FINE_PHASE_REGISTER);
    s->finePhaseDac_[2] = (float *)registerAddr(SGDBR_C_CNTRL_FINE_PHASE_REGISTER);
    s->finePhaseDac_[3] = (float *)registerAddr(SGDBR_D_CNTRL_FINE_PHASE_REGISTER);
    s->front_to_soa_coeff_[0] = (float *)registerAddr(SGDBR_A_CNTRL_FRONT_TO_SOA_COEFF_REGISTER);
    s->front_to_soa_coeff_[1] = (float *)registerAddr(SGDBR_B_CNTRL_FRONT_TO_SOA_COEFF_REGISTER);
    s->front_to_soa_coeff_[2] = (float *)registerAddr(SGDBR_C_CNTRL_FRONT_TO_SOA_COEFF_REGISTER);
    s->front_to_soa_coeff_[3] = (float *)registerAddr(SGDBR_D_CNTRL_FRONT_TO_SOA_COEFF_REGISTER);
    s->back_to_soa_coeff_[0] = (float *)registerAddr(SGDBR_A_CNTRL_BACK_TO_SOA_COEFF_REGISTER);
    s->back_to_soa_coeff_[1] = (float *)registerAddr(SGDBR_B_CNTRL_BACK_TO_SOA_COEFF_REGISTER);
    s->back_to_soa_coeff_[2] = (float *)registerAddr(SGDBR_C_CNTRL_BACK_TO_SOA_COEFF_REGISTER);
    s->back_to_soa_coeff_[3] = (float *)registerAddr(SGDBR_D_CNTRL_BACK_TO_SOA_COEFF_REGISTER);
    s->phase_to_soa_coeff_[0] = (float *)registerAddr(SGDBR_A_CNTRL_PHASE_TO_SOA_COEFF_REGISTER);
    s->phase_to_soa_coeff_[1] = (float *)registerAddr(SGDBR_B_CNTRL_PHASE_TO_SOA_COEFF_REGISTER);
    s->phase_to_soa_coeff_[2] = (float *)registerAddr(SGDBR_C_CNTRL_PHASE_TO_SOA_COEFF_REGISTER);
    s->phase_to_soa_coeff_[3] = (float *)registerAddr(SGDBR_D_CNTRL_PHASE_TO_SOA_COEFF_REGISTER);
    s->dead_zone_[0] = (float *)registerAddr(SGDBR_A_CNTRL_MIRROR_DEAD_ZONE_REGISTER);
    s->dead_zone_[1] = (float *)registerAddr(SGDBR_B_CNTRL_MIRROR_DEAD_ZONE_REGISTER);
    s->dead_zone_[2] = (float *)registerAddr(SGDBR_C_CNTRL_MIRROR_DEAD_ZONE_REGISTER);
    s->dead_zone_[3] = (float *)registerAddr(SGDBR_D_CNTRL_MIRROR_DEAD_ZONE_REGISTER);
    s->minimum_soa_[0] = (float *)registerAddr(SGDBR_A_CNTRL_MINIMUM_SOA_REGISTER);
    s->minimum_soa_[1] = (float *)registerAddr(SGDBR_B_CNTRL_MINIMUM_SOA_REGISTER);
    s->minimum_soa_[2] = (float *)registerAddr(SGDBR_C_CNTRL_MINIMUM_SOA_REGISTER);
    s->minimum_soa_[3] = (float *)registerAddr(SGDBR_D_CNTRL_MINIMUM_SOA_REGISTER);

    s->sgdbr_csr_[0] = FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_CSR;
    s->sgdbr_csr_[1] = FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_CSR;
    s->sgdbr_csr_[2] = FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_CSR;
    s->sgdbr_csr_[3] = FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_CSR;
    s->sgdbr_mosi_data_[0] = FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_MOSI_DATA;
    s->sgdbr_mosi_data_[1] = FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_MOSI_DATA;
    s->sgdbr_mosi_data_[2] = FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_MOSI_DATA;
    s->sgdbr_mosi_data_[3] = FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_MOSI_DATA;
    s->sgdbr_miso_data_[0] = FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_MISO_DATA;
    s->sgdbr_miso_data_[1] = FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_MISO_DATA;
    s->sgdbr_miso_data_[2] = FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_MISO_DATA;
    s->sgdbr_miso_data_[3] = FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_MISO_DATA;
    s->schemeThresholdFactorByVirtualLaser_[0] = (float *)registerAddr(THRESHOLD_FACTOR_VIRTUAL_LASER1);
    s->schemeThresholdFactorByVirtualLaser_[1] = (float *)registerAddr(THRESHOLD_FACTOR_VIRTUAL_LASER2);
    s->schemeThresholdFactorByVirtualLaser_[2] = (float *)registerAddr(THRESHOLD_FACTOR_VIRTUAL_LASER3);
    s->schemeThresholdFactorByVirtualLaser_[3] = (float *)registerAddr(THRESHOLD_FACTOR_VIRTUAL_LASER4);
    s->schemeThresholdFactorByVirtualLaser_[4] = (float *)registerAddr(THRESHOLD_FACTOR_VIRTUAL_LASER5);
    s->schemeThresholdFactorByVirtualLaser_[5] = (float *)registerAddr(THRESHOLD_FACTOR_VIRTUAL_LASER6);
    s->schemeThresholdFactorByVirtualLaser_[6] = (float *)registerAddr(THRESHOLD_FACTOR_VIRTUAL_LASER7);
    s->schemeThresholdFactorByVirtualLaser_[7] = (float *)registerAddr(THRESHOLD_FACTOR_VIRTUAL_LASER8);
    s->schemeThresholdBase_ = (unsigned int *)registerAddr(SCHEME_THRESHOLD_BASE);
    s->etalonTemperature_ = (float *)registerAddr(ETALON_TEMPERATURE_REGISTER);
    s->cavityPressure_ = (float *)registerAddr(CAVITY_PRESSURE_REGISTER);
    s->ambientPressure_ = (float *)registerAddr(AMBIENT_PRESSURE_REGISTER);
    s->defaultThreshold_ = (unsigned int *)registerAddr(SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER);
    s->analyzerTuningMode_ = (unsigned int *)registerAddr(ANALYZER_TUNING_MODE_REGISTER);
    s->virtLaser_ = (VIRTUAL_LASER_Type *)registerAddr(VIRTUAL_LASER_REGISTER);
    s->dasStatus_ = (unsigned int *)registerAddr(DAS_STATUS_REGISTER);
    s->schemeCounter_ = 0;
    s->incrFlag_ = 0;
    s->incrCounter_ = 0;
    s->incrCounterNext_ = 1;
    s->useMemo_ = 0;
    s->modeIndex_ = 0;
    s->wlm_angle_modulus_ = (float *)registerAddr(PZT_CNTRL_WLM_ANGLE_MODULUS);
    s->ref_update_time_constant_ = (float *)registerAddr(PZT_CNTRL_UPDATE_TIME_CONSTANT);
    s->pzt_update_scale_factor_ = (float *)registerAddr(PZT_CNTRL_SCALE_FACTOR);
    s->pzt_update_clamp_ = (float *)registerAddr(PZT_CNTRL_UPDATE_CLAMP);
    s->pzt_cntrl_state_ = (unsigned int *)registerAddr(PZT_CNTRL_STATE_REGISTER);
    s->pzt_cntrl_shift_ = (float *)registerAddr(PZT_CNTRL_SHIFT);
    s->pzt_cntrl_flattening_factor_ = (float *)registerAddr(PZT_CNTRL_FLATTENING_FACTOR);
    s->pzt_cntrl_reference_centering_factor_ = (float *)registerAddr(PZT_CNTRL_REFERENCE_CENTERING_FACTOR);
    pztLctOffset = 0.0;
    switchToRampMode();
    return STATUS_OK;
}

static void resetSpectCntrl(void)
{
    // Eat up posted semaphores
    SEM_pend(&SEM_rdFitting, 0);
    SEM_pend(&SEM_rdDataMoving, 0);
    SEM_pendBinary(&SEM_startRdCycle, 0);

    // Reset the RDMAN block, clear bank in use bits, acknowledge all interrupts
    changeBitsFPGA(FPGA_RDMAN + RDMAN_CONTROL, RDMAN_CONTROL_RESET_RDMAN_B,
                   RDMAN_CONTROL_RESET_RDMAN_W, 1);
    changeBitsFPGA(FPGA_RDMAN + RDMAN_CONTROL, RDMAN_CONTROL_BANK0_CLEAR_B,
                   RDMAN_CONTROL_BANK0_CLEAR_W, 1);
    changeBitsFPGA(FPGA_RDMAN + RDMAN_CONTROL, RDMAN_CONTROL_BANK1_CLEAR_B,
                   RDMAN_CONTROL_BANK1_CLEAR_W, 1);
    changeBitsFPGA(FPGA_RDMAN + RDMAN_CONTROL, RDMAN_CONTROL_RD_IRQ_ACK_B,
                   RDMAN_CONTROL_RD_IRQ_ACK_W, 1);
    changeBitsFPGA(FPGA_RDMAN + RDMAN_CONTROL, RDMAN_CONTROL_ACQ_DONE_ACK_B,
                   RDMAN_CONTROL_ACQ_DONE_ACK_W, 1);
    // Indicate both ringdown buffers are available
    SEM_postBinary(&SEM_rdBuffer0Available);
    SEM_postBinary(&SEM_rdBuffer1Available);
    switchToRampMode();
}

int spectCntrlStep(void)
// This is called every 100ms from the scheduler thread to start spectrum acquisition
{
    int i;
    SpectCntrlParams *s = &spectCntrlParams;
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
            SPECT_CNTRL_SchemeMultipleNoRepeatMode == *(s->mode_))
        {
            // For schemes, enable frequency locking only if we are not doing Fsr Hopping
            if (*(s->analyzerTuningMode_) == ANALYZER_TUNING_FsrHoppingTuningMode)
            {
                changeBitsFPGA(FPGA_RDMAN + RDMAN_OPTIONS, RDMAN_OPTIONS_LOCK_ENABLE_B, RDMAN_OPTIONS_LOCK_ENABLE_W, 0);
            }
            else
            {
                changeBitsFPGA(FPGA_RDMAN + RDMAN_OPTIONS, RDMAN_OPTIONS_LOCK_ENABLE_B, RDMAN_OPTIONS_LOCK_ENABLE_W, 1);
            }
            *(s->iter_) = 0;
            *(s->row_) = 0;
            *(s->dwell_) = 0;
            // Starting acquisition always goes to the scheme specified by "next"
            *(s->active_) = *(s->next_);
            for (i = 0; i < NUM_VIRTUAL_LASERS; i++)
                pztOffsets[i] = *(s->pztOffsetByVirtualLaser_[i]);
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
            SPECT_CNTRL_PausedState == prevState)
        {
            switchToRampMode();
            // Enable laser shutdown
            // TODO: Handle SOA shutdown
            changeBitsFPGA(FPGA_INJECT + INJECT_CONTROL, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W, 1);
            changeBitsFPGA(FPGA_INJECT + INJECT_CONTROL, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W, 1);

            SEM_pendBinary(&SEM_startRdCycle, 100); // Eat up anything pending
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
    else if (SPECT_CNTRL_DiagnosticState == *(s->state_))
    {
        switchToRampMode();
        setAutomaticLaserCurrentControl();
    }
    else
        switchToRampMode();

    prevState = stateAtStart;

    return STATUS_OK;
}

#define PI 3.141592654
void spectCntrl(void)
{
    int bank, status, nloops;
    int *counter = (int *)(REG_BASE + 4 * RD_INITIATED_COUNT_REGISTER);

    while (1)
    {
        SEM_pendBinary(&SEM_startRdCycle, SYS_FOREVER);
        nloops = 0;
        (*counter)++;

        // The next while loop periodically checks to see if we are allowed
        //  to start the ringdown
        while (1)
        {
            status = readFPGA(FPGA_RDMAN + RDMAN_STATUS);
            // Can start a new ringdown if the manager is not busy and if the
            //  bank for acquisition is not in use
            if (!(status & 1 << RDMAN_STATUS_BUSY_B))
            {
                bank = (status & 1 << RDMAN_STATUS_BANK_B) >> RDMAN_STATUS_BANK_B;
                if (0 == bank)
                {
                    if (!(status & 1 << RDMAN_STATUS_BANK0_IN_USE_B))
                        break;
                }
                else // 1 == bank
                {
                    if (!(status & 1 << RDMAN_STATUS_BANK1_IN_USE_B))
                        break;
                }
            }
            // Wait around for another ms and recheck. Reset manager if busy for more
            //  than 5s.
            nloops++;
            SEM_pendBinary(&SEM_waitForRdMan, SYS_FOREVER);
            if (nloops > 5000)
            {
                changeBitsFPGA(FPGA_RDMAN + RDMAN_CONTROL, RDMAN_CONTROL_BANK0_CLEAR_B,
                               RDMAN_CONTROL_BANK0_CLEAR_W, 1);
                changeBitsFPGA(FPGA_RDMAN + RDMAN_CONTROL, RDMAN_CONTROL_BANK1_CLEAR_B,
                               RDMAN_CONTROL_BANK1_CLEAR_W, 1);
                changeBitsFPGA(FPGA_RDMAN + RDMAN_CONTROL, RDMAN_CONTROL_RESET_RDMAN_B,
                               RDMAN_CONTROL_RESET_RDMAN_W, 1);
                SEM_pendBinary(&SEM_waitForRdMan, SYS_FOREVER);
                message_puts(LOG_LEVEL_INFO, "Resetting ringdown manager");
                nloops = 0;
                break;
            }
        }
        setupNextRdParams();
        // Then initiate the ringdown...
        changeBitsFPGA(FPGA_RDMAN + RDMAN_CONTROL, RDMAN_CONTROL_START_RD_B,
                       RDMAN_CONTROL_START_RD_W, 1);
    }
}

static int activeMemo = -1, rowMemo = -1;

static inline void sgdbr_wait_done(SpectCntrlParams *s, int sgdbrIndex)
{
    while (0 == (readFPGA(s->sgdbr_csr_[sgdbrIndex]) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)))
        ;
}

static inline int sgdbr_find_index(int aLaserNum)
{
    // Return index 0 for SGDBR_A, 1 for SGDBR_B, 2 for SGDBR_C and 3 for SGDBR_D, given
    //  the actual laser number (1-4)
    switch (aLaserNum)
    {
    case 1:
        return 0;
    case 2:
        return 2;
    case 3:
        return 1;
    default:
        return 3;
    }
}

void setupLaserTemperatureAndPztOffset(int useMemo)
{
    SpectCntrlParams *s = &spectCntrlParams;
    unsigned int aLaserNum, vLaserNum;
    volatile SchemeTableType *schemeTable = &schemeTables[*(s->active_)];
    volatile VirtualLaserParamsType *vLaserParams;
    int pztOffset, extSoaNumber;
    float soa_offset, extSoaCurrent;
    float laserTemp;
    int extSoaCurrentRegs[4] = {SOA1_CURRENT_SETPOINT_REGISTER, SOA2_CURRENT_SETPOINT_REGISTER, SOA3_CURRENT_SETPOINT_REGISTER, SOA4_CURRENT_SETPOINT_REGISTER};

    if (SPECT_CNTRL_ContinuousMode == *(s->mode_))
    {
        vLaserParams = &virtualLaserParams[*(s->virtLaser_)];
        // In continuous mode, we use the parameter values currently in the registers
        vLaserNum = 1 + (unsigned int)*(s->virtLaser_);
        aLaserNum = 1 + (vLaserParams->actualLaser & 0x3);
        //
        extSoaNumber = vLaserParams->extSoaNumber;
        extSoaCurrent = vLaserParams->extSoaCurrent;
        // Set the SOA current  
        *(float *)registerAddr(extSoaCurrentRegs[extSoaNumber - 1]) = extSoaCurrent;

        // *(s->laserTempSetpoint_[aLaserNum - 1]) = *(s->laserTempUserSetpoint_[aLaserNum - 1]);
        // In continuous mode update the pztOffsets from the DSP registers immediately
        pztOffsets[vLaserNum - 1] = *(s->pztOffsetByVirtualLaser_[vLaserNum - 1]);
        pztOffset = pztOffsets[vLaserNum - 1]; // *(s->pztOffsetByVirtualLaser_[vLaserNum - 1]);
        if (*(s->pztUpdateMode_) == PZT_UPDATE_UseVLOffset_Mode)
        {
            writeFPGA(FPGA_TWGEN + TWGEN_PZT_OFFSET, pztOffset % 65536);
        }
    }
    else if (SPECT_CNTRL_ContinuousManualTempMode == *(s->mode_))
    { // With manual temperature control, do not adjust the PZT
        vLaserParams = &virtualLaserParams[*(s->virtLaser_)];
        //
        extSoaNumber = vLaserParams->extSoaNumber;
        extSoaCurrent = vLaserParams->extSoaCurrent;
        // Set the SOA current  
        *(float *)registerAddr(extSoaCurrentRegs[extSoaNumber - 1]) = extSoaCurrent;
    }
    else
    { // We are running a scheme
        volatile SchemeRowType *schemeRowPtr;
        // Do not use cached information if the pzt control is enabled
        if (*(s->pzt_cntrl_state_) == PZT_CNTRL_DisabledState && useMemo && *(s->active_) == activeMemo && *(s->row_) == rowMemo)
            return;
        *(s->virtLaser_) = (VIRTUAL_LASER_Type)schemeTable->rows[*(s->row_)].virtualLaser;
        vLaserNum = 1 + (unsigned int)*(s->virtLaser_);
        vLaserParams = &virtualLaserParams[vLaserNum - 1];
        //
        extSoaNumber = vLaserParams->extSoaNumber;
        extSoaCurrent = vLaserParams->extSoaCurrent;
        // Set the SOA current  
        *(float *)registerAddr(extSoaCurrentRegs[extSoaNumber - 1]) = extSoaCurrent;

        // The PZT offset for this row is the sum of the PZT offset for the virtual laser from the appropriate
        //  register and any setpoint in the scheme file. Note that all PZT values are interpreted modulo 65536
        if (*(s->analyzerTuningMode_) == ANALYZER_TUNING_CavityLengthTuningMode || *(s->pzt_cntrl_state_) == PZT_CNTRL_EnabledState)
        {
            // In cavity length tunining mode, or if the PZT controller is enabled, update the PZT offset directly from the 
            //  pztOffsetByVirtualLaser_ register
            pztOffsets[vLaserNum - 1] = *(s->pztOffsetByVirtualLaser_[vLaserNum - 1]);
        }
        // In other modes, the pztOffset is only updated when we go from one scheme to the next since this is done
        //  in advanceScheme()
        pztOffset = pztOffsets[vLaserNum - 1] + schemeTable->rows[*(s->row_)].pztSetpoint;

        // In Laser current tuning mode, we apply an additional pztLctOffset which is updated on a per ringdown
        //  basis to compensate for pressure and composition changes
        if (*(s->analyzerTuningMode_) == ANALYZER_TUNING_LaserCurrentTuningMode && *(s->pzt_cntrl_state_) == PZT_CNTRL_EnabledState)
            {
                pztOffset = pztLctOffset;
                // Now check if the pztOffset lies outside the permitted range of 8192 to 57344. If so, we move the pztOffsetByVirtualLaser
                //  by +/- *(s->pztIncrPerFsr_) to recenter the position
                if (pztOffset >= 57344) {
                    pztOffset -= *(s->pztIncrPerFsr_);
                }
                else if (pztOffset < 8192) {
                    pztOffset += *(s->pztIncrPerFsr_);
                }
                pztLctOffset = pztOffset;
            }
        if (*(s->pztUpdateMode_) == PZT_UPDATE_UseVLOffset_Mode)
        {
            writeFPGA(FPGA_TWGEN + TWGEN_PZT_OFFSET, pztOffset % 65536);
        }

        laserTemp = 0.001 * schemeTable->rows[*(s->row_)].laserTemp; // Scheme temperatures are in milli-degrees C
        aLaserNum = 1 + (vLaserParams->actualLaser & 0x3);
        if (laserTemp != 0.0)
        {
            *(s->laserTempSetpoint_[aLaserNum - 1]) = laserTemp + *(s->schemeOffsetByVirtualLaser_[vLaserNum - 1]);
        }

        // If the laserType is one (for the SGDBR laser) we need to update the front and back mirror and the coarse
        //  phase DAC. We need to modify the DSP registers as well as write to the FPGA block.
        schemeRowPtr = &(schemeTable->rows[*(s->row_)]);
        if (vLaserParams->laserType == 1)
        {
            int sgdbrIndex;
            sgdbrIndex = sgdbr_find_index(aLaserNum);
            *(s->frontMirrorDac_[sgdbrIndex]) = schemeRowPtr->frontMirrorDac;
            *(s->backMirrorDac_[sgdbrIndex]) = schemeRowPtr->backMirrorDac;
            *(s->coarsePhaseDac_[sgdbrIndex]) = schemeRowPtr->coarsePhaseDac;
            sgdbr_wait_done(s, sgdbrIndex);
            writeFPGA(s->sgdbr_mosi_data_[sgdbrIndex], SGDBR_FRONT_MIRROR_DAC | schemeRowPtr->frontMirrorDac);
            sgdbr_wait_done(s, sgdbrIndex);
            writeFPGA(s->sgdbr_mosi_data_[sgdbrIndex], SGDBR_BACK_MIRROR_DAC | schemeRowPtr->backMirrorDac);
            sgdbr_wait_done(s, sgdbrIndex);
            writeFPGA(s->sgdbr_mosi_data_[sgdbrIndex], SGDBR_COARSE_PHASE_DAC | schemeRowPtr->coarsePhaseDac);
            sgdbr_wait_done(s, sgdbrIndex);
            setup_all_gain_and_soa_currents();
            // Calculate the SOA current offset and update the SOA current
            soa_offset = 0;
            if (schemeRowPtr->frontMirrorDac > *(s->dead_zone_[sgdbrIndex]))
            {
                soa_offset += *(s->front_to_soa_coeff_[sgdbrIndex]) * (schemeRowPtr->frontMirrorDac - *(s->dead_zone_[sgdbrIndex]));
            }
            if (schemeRowPtr->backMirrorDac > *(s->dead_zone_[sgdbrIndex]))
            {
                soa_offset += *(s->back_to_soa_coeff_[sgdbrIndex]) * (schemeRowPtr->backMirrorDac - *(s->dead_zone_[sgdbrIndex]));
            }
            soa_offset += *(s->phase_to_soa_coeff_[sgdbrIndex]) * (schemeRowPtr->coarsePhaseDac);
            s->soaDac[sgdbrIndex] = *(s->soaSetting_[sgdbrIndex]) + soa_offset;
            if (s->soaDac[sgdbrIndex] < *(s->minimum_soa_[sgdbrIndex]))
                s->soaDac[sgdbrIndex] = *(s->minimum_soa_[sgdbrIndex]);
            writeFPGA(s->sgdbr_mosi_data_[sgdbrIndex], SGDBR_SOA_DAC | s->soaDac[sgdbrIndex]);
            sgdbr_wait_done(s, sgdbrIndex);
        }

        activeMemo = *(s->active_);
        rowMemo = *(s->row_);
    }
}

void setupNextRdParams(void)
{
    SpectCntrlParams *s = &spectCntrlParams;
    RingdownParamsType *r = &nextRdParams;

    unsigned int laserNum, laserTempAsInt, lossTag;
    int sgdbrIndex;
    volatile SchemeTableType *schemeTable;
    volatile VirtualLaserParamsType *vLaserParams;
    float phi, dp, minScale, ratio1Multiplier, ratio2Multiplier, theta;

    if (*(s->pzt_cntrl_state_) == PZT_CNTRL_ResetOffsetState) {
        pztLctOffset = 0.0;
        *(s->pzt_cntrl_state_) = PZT_CNTRL_EnabledState;
    }

    s->incrCounter_ = s->incrCounterNext_;

    if (SPECT_CNTRL_ContinuousMode == *(s->mode_))
    {
        // In continuous mode, we run with the parameter values currently in the registers
        vLaserParams = &virtualLaserParams[*(s->virtLaser_)];
        laserNum = vLaserParams->actualLaser & 0x3;
        r->injectionSettings = (*(s->virtLaser_) << INJECTION_SETTINGS_virtualLaserShift) | (laserNum << INJECTION_SETTINGS_actualLaserShift);
        r->laserTemperature = *(s->laserTemp_[laserNum]);
        r->coarseLaserCurrent = *(s->coarseLaserCurrent_[laserNum]);
        r->etalonTemperature = *(s->etalonTemperature_);
        r->cavityPressure = *(s->cavityPressure_);
        r->ambientPressure = *(s->ambientPressure_);
        r->schemeTableAndRow = 0;
        r->countAndSubschemeId = (s->incrCounter_ << 16);
        r->ringdownThreshold = *(s->defaultThreshold_);
        r->status = 0;
        r->angleSetpoint = 0.0;
        laserTempAsInt = 1000.0 * r->laserTemperature;
        // Set up the FPGA registers for this ringdown
        changeBitsFPGA(FPGA_INJECT + INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W, laserNum);
        changeBitsFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_CONFIG, SGDBRMANAGER_CONFIG_SELECT_B, SGDBRMANAGER_CONFIG_SELECT_W, sgdbr_find_index(laserNum + 1));
        writeFPGA(FPGA_RDMAN + RDMAN_THRESHOLD, r->ringdownThreshold);
        s->modeIndex_ = 0;
    }
    else if (SPECT_CNTRL_ContinuousManualTempMode == *(s->mode_))
    {
        // Get actual laser number from FPGA and virtual laser number from register
        // In this way, if a virtual laser number is specified, it is used (for frequency conversion)
        //  but if not, it will still work.
        laserNum = readBitsFPGA(FPGA_INJECT + INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W);
        changeBitsFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_CONFIG, SGDBRMANAGER_CONFIG_SELECT_B, SGDBRMANAGER_CONFIG_SELECT_W, sgdbr_find_index(laserNum + 1));
        r->injectionSettings = (*(s->virtLaser_) << INJECTION_SETTINGS_virtualLaserShift) | (laserNum << INJECTION_SETTINGS_actualLaserShift);
        r->laserTemperature = *(s->laserTemp_[laserNum]);
        r->coarseLaserCurrent = *(s->coarseLaserCurrent_[laserNum]);
        r->etalonTemperature = *(s->etalonTemperature_);
        r->cavityPressure = *(s->cavityPressure_);
        r->ambientPressure = *(s->ambientPressure_);
        r->schemeTableAndRow = 0;
        r->countAndSubschemeId = 0; // (s->incrCounter_ << 16);
        r->ringdownThreshold = *(s->defaultThreshold_);
        r->status = 0;
        r->angleSetpoint = 0.0;
        laserTempAsInt = 1000.0 * r->laserTemperature;
        s->modeIndex_ = 0;
        // Set up the FPGA registers for this ringdown
        writeFPGA(FPGA_RDMAN + RDMAN_THRESHOLD, r->ringdownThreshold);
    }
    else // We are running a scheme
    {
        do
        {
            schemeTable = &schemeTables[*(s->active_)];
            *(s->virtLaser_) = (VIRTUAL_LASER_Type)schemeTable->rows[*(s->row_)].virtualLaser;
            vLaserParams = &virtualLaserParams[*(s->virtLaser_)];
            if (vLaserParams->laserType == 1)
            {
                // Deal with angle setpoint == -1.0e6 which indicates that the SGDBR laser
                // cannot tune to this frequency and we should proceed to the next scheme row
                if (schemeTable->rows[*(s->row_)].setpoint <= -1.0e6)
                {
                    s->incrFlag_ = schemeTable->rows[*(s->row_)].subschemeId & SUBSCHEME_ID_IncrMask;
                    advanceSchemeRow();
                    s->incrCounter_ = s->incrCounterNext_;
                    continue;
                }
            }
            // This loop is here so that a dwell count of zero can be used to set up the
            //  laser temperature without triggering a ringdown
            setupLaserTemperatureAndPztOffset(s->useMemo_);
            s->useMemo_ = 1;
            if (schemeTable->rows[*(s->row_)].dwellCount > 0)
                break;
            s->incrFlag_ = schemeTable->rows[*(s->row_)].subschemeId & SUBSCHEME_ID_IncrMask;
            advanceSchemeRow();
            s->incrCounter_ = s->incrCounterNext_;
        } while (1);
        // while (*(s->row_) != 0);
        s->modeIndex_ = schemeTable->rows[*(s->row_)].modeIndex;
        laserNum = vLaserParams->actualLaser & 0x3;
        // The loss tag is used to classify ringdowns for storage in the LOSS_BUFFER_n registers
        lossTag = schemeTable->rows[*(s->row_)].pztSetpoint & 0x7;
        r->injectionSettings = (lossTag << INJECTION_SETTINGS_lossTagShift) |
                               (*(s->virtLaser_) << INJECTION_SETTINGS_virtualLaserShift) |
                               (laserNum << INJECTION_SETTINGS_actualLaserShift);
        r->laserTemperature = *(s->laserTemp_[laserNum]);
        r->coarseLaserCurrent = *(s->coarseLaserCurrent_[laserNum]);
        r->etalonTemperature = *(s->etalonTemperature_);
        r->cavityPressure = *(s->cavityPressure_);
        r->ambientPressure = *(s->ambientPressure_);
        r->schemeTableAndRow = (*(s->active_) << 16) | (*(s->row_) & 0xFFFF);

        // laserTempAsInt = schemeTable->rows[*(s->row_)].laserTemp;
        laserTempAsInt = 1000.0 * r->laserTemperature;

        // If SUBSCHEME_ID_IncrMask is set, this means that we should increment
        //  s->incrCounter_ the next time that we advance to the next scheme row
        s->incrFlag_ = schemeTable->rows[*(s->row_)].subschemeId & SUBSCHEME_ID_IncrMask;
        r->countAndSubschemeId = (s->incrCounter_ << 16) | (schemeTable->rows[*(s->row_)].subschemeId & 0xFFFF);
        r->ringdownThreshold = schemeTable->rows[*(s->row_)].threshold;
        if (r->ringdownThreshold == 0)
            r->ringdownThreshold = *(s->defaultThreshold_);
        else
        {
            float base = *(s->schemeThresholdBase_);
            unsigned int vLaserNum = 1 + (unsigned int)*(s->virtLaser_);
            r->ringdownThreshold = base + (r->ringdownThreshold - base) * (*(s->schemeThresholdFactorByVirtualLaser_[vLaserNum - 1]));
        }

        r->status = (s->schemeCounter_ & RINGDOWN_STATUS_SequenceMask);
        if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_) ||
            SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) ||
            SPECT_CNTRL_SchemeMultipleNoRepeatMode == *(s->mode_))
            r->status |= RINGDOWN_STATUS_SchemeActiveMask;
        // Determine if we are on the last ringdown of the scheme and set status bits appropriately
        if ((*(s->iter_) >= schemeTables[*(s->active_)].numRepeats - 1 || SPECT_CNTRL_SchemeMultipleNoRepeatMode == *(s->mode_)) &&
            *(s->row_) >= schemeTables[*(s->active_)].numRows - 1 &&
            *(s->dwell_) >= schemeTables[*(s->active_)].rows[*(s->row_)].dwellCount - 1)
        {
            // We need to decide if acquisition is continuing or not. Acquisition stops if the scheme is run in Single mode, or
            //  if we are running a non-looping sequence and have reached the last scheme in the sequence
            if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_))
                r->status |= RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask;
            else if (SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) ||
                     SPECT_CNTRL_SchemeMultipleNoRepeatMode == *(s->mode_))
                r->status |= RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask;
        }

        if (vLaserParams->laserType == 1)
        {
            // Set up the locker multipliers on the basis of the pseudo-angle setpoint
            // Correct the setpoint angle using the etalon temperature and ambient pressure
            r->angleSetpoint = schemeTable->rows[*(s->row_)].setpoint;
            dp = r->ambientPressure - vLaserParams->calPressure;
            phi = r->angleSetpoint - vLaserParams->tempSensitivity * (r->etalonTemperature - vLaserParams->calTemp) -
                  (vLaserParams->pressureC0 + dp * (vLaserParams->pressureC1 + dp * (vLaserParams->pressureC2 + dp * vLaserParams->pressureC3)));
            ratio1Multiplier = -sinsp(phi);
            ratio2Multiplier = cossp(phi);
        }
        else
        {
            r->angleSetpoint = schemeTable->rows[*(s->row_)].setpoint;
            // Correct the setpoint angle using the etalon temperature and ambient pressure
            dp = r->ambientPressure - vLaserParams->calPressure;
            theta = r->angleSetpoint - vLaserParams->tempSensitivity * (r->etalonTemperature - vLaserParams->calTemp) -
                    (vLaserParams->pressureC0 + dp * (vLaserParams->pressureC1 + dp * (vLaserParams->pressureC2 + dp * vLaserParams->pressureC3)));

            // Compute the ratio multipliers corresponding to this setpoint. Both ratios must be no greater than one in absolute value.
            minScale = min(vLaserParams->ratio1Scale, vLaserParams->ratio2Scale);
            ratio1Multiplier = -minScale * sinsp(theta + vLaserParams->phase) / vLaserParams->ratio1Scale;
            ratio2Multiplier = minScale * cossp(theta) / vLaserParams->ratio2Scale;
        }

        // Set up the FPGA registers for this ringdown
        changeBitsFPGA(FPGA_INJECT + INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W, laserNum);
        changeBitsFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_CONFIG, SGDBRMANAGER_CONFIG_SELECT_B, SGDBRMANAGER_CONFIG_SELECT_W, sgdbr_find_index(laserNum + 1));

        writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_RATIO1_MULTIPLIER, (int)(ratio1Multiplier * 32767.0));
        writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_RATIO2_MULTIPLIER, (int)(ratio2Multiplier * 32767.0));

        writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_RATIO1_CENTER, (int)(vLaserParams->ratio1Center * 32768.0));
        writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_RATIO2_CENTER, (int)(vLaserParams->ratio2Center * 32768.0));

        writeFPGA(FPGA_RDMAN + RDMAN_THRESHOLD, r->ringdownThreshold);
        // Also write the laser temperature to the wavelength monitor simulator, solely to allow
        //  the simulator to calculate an angle that depends on laser temperature as well as current
        writeFPGA(FPGA_WLMSIM + WLMSIM_LASER_TEMP, laserTempAsInt);
    }

    sgdbrIndex = sgdbr_find_index(laserNum + 1);
    r->frontAndBackMirrorCurrentDac = ((0xFFFF & (int)(*(s->frontMirrorDac_[sgdbrIndex]))) << 16) | (0xFFFF & (int)(*(s->backMirrorDac_[sgdbrIndex])));
    r->gainAndSoaCurrentDac = ((0xFFFF & (int)(*(s->gainDac_[sgdbrIndex]))) << 16) | (0xFFFF & (int)(s->soaDac[sgdbrIndex]));
    r->coarseAndFinePhaseCurrentDac = ((0xFFFF & (int)(*(s->coarsePhaseDac_[sgdbrIndex]))) << 16) | (0xFFFF & (int)(*(s->finePhaseDac_[sgdbrIndex])));
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM0, *(uint32 *)&r->injectionSettings);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM1, *(uint32 *)&r->laserTemperature);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM2, *(uint32 *)&r->coarseLaserCurrent);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM3, *(uint32 *)&r->etalonTemperature);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM4, *(uint32 *)&r->cavityPressure);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM5, *(uint32 *)&r->ambientPressure);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM6, *(uint32 *)&r->schemeTableAndRow);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM7, *(uint32 *)&r->countAndSubschemeId);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM8, *(uint32 *)&r->ringdownThreshold);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM9, *(uint32 *)&r->status);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM10, *(uint32 *)&r->angleSetpoint);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM11, *(uint32 *)&r->frontAndBackMirrorCurrentDac);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM12, *(uint32 *)&r->gainAndSoaCurrentDac);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM13, *(uint32 *)&r->coarseAndFinePhaseCurrentDac);
    writeFPGA(FPGA_RDMAN + RDMAN_PARAM14, s->modeIndex_);
}

void modifyParamsOnTimeout(unsigned int schemeCount)
// If a ringdown timeout occurs, i.e., if there is no ringdown within the allotted interval, we
//  proceed to the next scheme row, short-circuiting the dwell count requested. An entry is
//  placed on the ringdown buffer queue with a special status when this occurs. It may be necessary
//  to modify the bits which indicate if we are at the end of a scheme as a result of this
//  short-circuiting.
{
    SpectCntrlParams *s = &spectCntrlParams;
    RingdownParamsType *r = &nextRdParams;
    r->status |= RINGDOWN_STATUS_RingdownTimeout;
    if (s->schemeCounter_ != schemeCount)
    {
        // We have advanced to another scheme, so set the end-of-scheme status bits appropriately
        r->status &= ~(RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask | RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask);
        // We need to decide if acquisition is continuing or not. Acquisition stops if the scheme is run in Single mode, or
        //  if we are running a non-looping sequence and have reached the last scheme in the sequence
        if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_))
            r->status |= RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask;
        else if (SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) ||
                 SPECT_CNTRL_SchemeMultipleNoRepeatMode == *(s->mode_))
            r->status |= RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask;
    }
}

unsigned int getSpectCntrlSchemeCount(void)
{
    SpectCntrlParams *s = &spectCntrlParams;
    return s->schemeCounter_;
}

void setAutomaticLaserTemperatureControl(void)
{
    DataType data;

    data.asInt = TEMP_CNTRL_AutomaticState;
    writeRegister(LASER1_TEMP_CNTRL_STATE_REGISTER, data);
    writeRegister(LASER2_TEMP_CNTRL_STATE_REGISTER, data);
    writeRegister(LASER3_TEMP_CNTRL_STATE_REGISTER, data);
    writeRegister(LASER4_TEMP_CNTRL_STATE_REGISTER, data);
}

void setAutomaticLaserCurrentControl(void)
// Set optical injection, laser current and laser temperature controllers to automatic mode. This should be called by the
//  scheduler thread in response to a request to start a scheme, otherwise a race condition could occur
//  leading to the wrong value for INJECT_CONTROL_MODE.
{
    DataType data;

    data.asInt = LASER_CURRENT_CNTRL_AutomaticState;
    writeRegister(LASER1_CURRENT_CNTRL_STATE_REGISTER, data);
    writeRegister(LASER2_CURRENT_CNTRL_STATE_REGISTER, data);
    writeRegister(LASER3_CURRENT_CNTRL_STATE_REGISTER, data);
    writeRegister(LASER4_CURRENT_CNTRL_STATE_REGISTER, data);
    data.asInt = SGDBR_CNTRL_AutomaticState;
    writeRegister(SGDBR_A_CNTRL_STATE_REGISTER, data);
    writeRegister(SGDBR_B_CNTRL_STATE_REGISTER, data);
    writeRegister(SGDBR_C_CNTRL_STATE_REGISTER, data);
    writeRegister(SGDBR_D_CNTRL_STATE_REGISTER, data);

    // Setting the FPGA optical injection block to automatic mode has to be done independently
    //  of setting the individual current controllers. Care is needed since the current controllers
    //  periodically write to the INJECT_CONTROL register.

    changeBitsFPGA(FPGA_INJECT + INJECT_CONTROL, INJECT_CONTROL_MODE_B, INJECT_CONTROL_MODE_W, 1);
}

void setManualControl(void)
// Set optical injection and laser current controllers to manual mode.
{
    DataType data;

    // The FPGA optical injection block is placed in manual mode
    // when any laser current controller is in the manual state

    data.asInt = LASER_CURRENT_CNTRL_ManualState;
    writeRegister(LASER1_CURRENT_CNTRL_STATE_REGISTER, data);
    writeRegister(LASER2_CURRENT_CNTRL_STATE_REGISTER, data);
    writeRegister(LASER3_CURRENT_CNTRL_STATE_REGISTER, data);
    writeRegister(LASER4_CURRENT_CNTRL_STATE_REGISTER, data);
    data.asInt = SGDBR_CNTRL_ManualState;
    writeRegister(SGDBR_A_CNTRL_STATE_REGISTER, data);
    writeRegister(SGDBR_B_CNTRL_STATE_REGISTER, data);
    writeRegister(SGDBR_C_CNTRL_STATE_REGISTER, data);
    writeRegister(SGDBR_D_CNTRL_STATE_REGISTER, data);
}

void validateSchemePosition(void)
// Ensure that the dwell count, scheme row and scheme iteration values are valid and reset
//  them to zero if not
{
    SpectCntrlParams *s = &spectCntrlParams;
    if (*(s->active_) >= NUM_SCHEME_TABLES)
    {
        message_puts(LOG_LEVEL_STANDARD, "Active scheme index is out of range, resetting to zero");
        *(s->active_) = 0;
    }
    if (*(s->iter_) >= schemeTables[*(s->active_)].numRepeats)
    {
        message_puts(LOG_LEVEL_STANDARD, "Scheme iteration is out of range, resetting to zero");
        *(s->iter_) = 0;
    }
    if (*(s->row_) >= schemeTables[*(s->active_)].numRows)
    {
        message_puts(LOG_LEVEL_STANDARD, "Scheme row is out of range, resetting to zero");
        *(s->row_) = 0;
    }
    if (*(s->dwell_) >= schemeTables[*(s->active_)].rows[*(s->row_)].dwellCount)
    {
        message_puts(LOG_LEVEL_STANDARD, "Dwell count is out of range, resetting to zero");
        *(s->dwell_) = 0;
    }
}

void advanceDwellCounter(void)
{
    SpectCntrlParams *s = &spectCntrlParams;
    *(s->dwell_) = *(s->dwell_) + 1;
    if (*(s->dwell_) >= schemeTables[*(s->active_)].rows[*(s->row_)].dwellCount)
    {
        advanceSchemeRow();
    }
}

void advanceSchemeRow(void)
{
    SpectCntrlParams *s = &spectCntrlParams;
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
    SpectCntrlParams *s = &spectCntrlParams;
    *(s->iter_) = *(s->iter_) + 1;
    if (*(s->iter_) >= schemeTables[*(s->active_)].numRepeats ||
        SPECT_CNTRL_SchemeMultipleNoRepeatMode == *(s->mode_))
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
    int i;
    SpectCntrlParams *s = &spectCntrlParams;
    s->schemeCounter_++;
    s->incrCounterNext_ = s->incrCounter_ + 1;
    *(s->active_) = *(s->next_);
    for (i = 0; i < NUM_VIRTUAL_LASERS; i++)
        pztOffsets[i] = *(s->pztOffsetByVirtualLaser_[i]);
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
    SpectCntrlParams *s = &spectCntrlParams;
    unsigned int dasStatus = *(s->dasStatus_);
    unsigned int aLaserNum = 1 + readBitsFPGA(FPGA_INJECT + INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W);

    switch (aLaserNum)
    {
    case 1:
        return 0 != (dasStatus & (1 << DAS_STATUS_Laser1TempCntrlLockedBit));
    case 2:
        return 0 != (dasStatus & (1 << DAS_STATUS_Laser2TempCntrlLockedBit));
    case 3:
        return 0 != (dasStatus & (1 << DAS_STATUS_Laser3TempCntrlLockedBit));
    case 4:
        return 0 != (dasStatus & (1 << DAS_STATUS_Laser4TempCntrlLockedBit));
    }
    return 0;
}

void spectCntrlError(void)
// This is called to place the spectrum controller subsystem in a sane state
//  in response to an error or abort condition
{
    SpectCntrlParams *s = &spectCntrlParams;
    *(s->state_) = SPECT_CNTRL_ErrorState;
    resetSpectCntrl();
    message_puts(LOG_LEVEL_CRITICAL, "Spectrum controller enters error state.");
}

void update_wlmsim_laser_temp(void)
// This is called periodically by the scheduler to update the laser temperature register of the WLM simulator
//  with the temperature of the selected laser. This should only be done if the spectrum controller is not
//  in the starting or running states.
{
    SpectCntrlParams *s = &spectCntrlParams;
    if (*(s->state_) != SPECT_CNTRL_StartingState && *(s->state_) != SPECT_CNTRL_RunningState)
    {
        unsigned int laserNum = readBitsFPGA(FPGA_INJECT + INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W);
        unsigned int laserTempAsInt = *(s->laserTemp_[laserNum]) * 1000;
        writeFPGA(FPGA_WLMSIM + WLMSIM_LASER_TEMP, laserTempAsInt);
    }
}
