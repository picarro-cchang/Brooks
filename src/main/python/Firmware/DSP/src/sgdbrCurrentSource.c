/*
 * FILE:
 *   sgdbrCurrentSource.c
 *
 * DESCRIPTION:
 *   Routines for handling SGDBR laser current source
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   6-Feb-2018  sze  Initial version.
 *   27-Oct-2022 sze  Four laser version.
 *
 *  Copyright (c) 2018 Picarro, Inc. All rights reserved
 */
#include "interface.h"
#include "dspData.h"
#include "fpga.h"
#include "registers.h"
#include "sgdbrCurrentSource.h"
#include <math.h>
#include <stdio.h>
#include <assert.h>
#include <csl.h>
#include <csl_cache.h>
#include <csl_irq.h>
#define US_DELAY 20

#define HTONL(n)                                                                                                       \
    (((((unsigned long)(n)&0xFF)) << 24) | ((((unsigned long)(n)&0xFF00)) << 8) |                                      \
     ((((unsigned long)(n)&0xFF0000)) >> 8) | ((((unsigned long)(n)&0xFF000000)) >> 24))

// Structures for controlling SGDBR current sources
SgdbrCntrl sgdbrACntrl, sgdbrBCntrl, sgdbrCCntrl, sgdbrDCntrl;
SgdbrCntrl *sgdbrCntrl[4] = {&sgdbrACntrl, &sgdbrBCntrl, &sgdbrCCntrl, &sgdbrDCntrl};
SgdbrCntrl *sA = NULL, *sB = NULL, *sC = NULL, *sD = NULL;

static char last_auto_sgdbr = ' ';

#define state (*(s->state_))
#define front_mirror (*(s->front_mirror_))
#define back_mirror (*(s->back_mirror_))
#define gain (*(s->gain_))
#define soa (*(s->soa_))
#define coarse_phase (*(s->coarse_phase_))
#define fine_phase (*(s->fine_phase_))
#define chirp (*(s->chirp_))
#define spare (*(s->spare_))
#define rd_config (*(s->rd_config_))
#define front_step (*(s->front_step_))
#define back_step (*(s->back_step_))
#define phase_step (*(s->phase_step_))
#define soa_step (*(s->soa_step_))
#define semi_period (*(s->semi_period_))
#define pulse_temp_ptp (*(s->pulse_temp_ptp_))

#define laserTemp (*(s->laser_temp_))
#define laserTempSetpoint (*(s->laser_temp_setpoint_))
#define laserTempWindow (*(s->laser_temp_window_))

static inline int _get_extinguish_deselected()
{
    return 0 != (readFPGA(FPGA_INJECT + INJECT_CONTROL2) & (1 << INJECT_CONTROL2_EXTINGUISH_DESELECTED_B));
}

static inline char _get_selected_sgdbr_laser()
{
    int sel = (readFPGA(FPGA_INJECT + INJECT_CONTROL) >> INJECT_CONTROL_LASER_SELECT_B) & 3;
    switch (sel)
    {
    case 0:
        return 'A';
    case 1:
        return 'C';
    case 2:
        return 'B';
    case 3:
        return 'D';
    }
	message_puts(LOG_LEVEL_CRITICAL, "Invalid SGDBR laser index in _get_selected_sgdbr_laser.");
	return 'X';
}

static inline void _wait_done(SgdbrCntrl *s)
{
    while (0 == (readFPGA(s->fpga_csr) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)))
        ;
}

static void _sgdbrProgramFpga(SgdbrCntrl *s)
/* Transfer the data in the latticeFpgaPrograms region to the SPI port */
{
    int i, loops;
    unsigned int gie;
    gie = IRQ_globalDisable();

    writeFPGA(s->fpga_csr, (1 << SGDBRCURRENTSOURCE_CSR_CPHA_B) | (1 << SGDBRCURRENTSOURCE_CSR_CPOL_B));
    for (loops = 0; loops < 1000 * US_DELAY; loops++)
        ;
    // Assert chip select
    writeFPGA(s->fpga_csr, (1 << SGDBRCURRENTSOURCE_CSR_CPHA_B) | (1 << SGDBRCURRENTSOURCE_CSR_CPOL_B) |
                               (1 << SGDBRCURRENTSOURCE_CSR_SELECT_B));
    for (loops = 0; loops < 50 * US_DELAY; loops++)
        ;
    // Assert reset
    writeFPGA(s->fpga_csr, (1 << SGDBRCURRENTSOURCE_CSR_CPHA_B) | (1 << SGDBRCURRENTSOURCE_CSR_CPOL_B) |
                               (1 << SGDBRCURRENTSOURCE_CSR_SELECT_B) | (1 << SGDBRCURRENTSOURCE_CSR_RESET_B));
    for (loops = 0; loops < 400 * US_DELAY; loops++)
        ;
    // Deassert reset
    writeFPGA(s->fpga_csr, (1 << SGDBRCURRENTSOURCE_CSR_CPHA_B) | (1 << SGDBRCURRENTSOURCE_CSR_CPOL_B) |
                               (1 << SGDBRCURRENTSOURCE_CSR_SELECT_B));
    for (loops = 0; loops < 3000 * US_DELAY; loops++)
        ;

    // Deassert chip select and force it to remain deselected
    writeFPGA(s->fpga_csr, (1 << SGDBRCURRENTSOURCE_CSR_CPHA_B) | (1 << SGDBRCURRENTSOURCE_CSR_CPOL_B) |
                               (1 << SGDBRCURRENTSOURCE_CSR_DESELECT_B));
    for (loops = 0; loops < 50 * US_DELAY; loops++)
        ;

    // Send binary image
    for (i = 0; i < latticeFpgaPrograms->num_words; i++)
    {
        writeFPGA(s->fpga_mosi_data, HTONL(latticeFpgaPrograms->data[i]));
        _wait_done(s);
    }

    // Deassert forced chip deselect
    writeFPGA(s->fpga_csr, (1 << SGDBRCURRENTSOURCE_CSR_CPHA_B) | (1 << SGDBRCURRENTSOURCE_CSR_CPOL_B));

    // Write a word out to indicate end
    writeFPGA(s->fpga_mosi_data, HTONL(0xF1D0DEAD));

    IRQ_globalRestore(gie);
}

static int _sgdbrCntrlStep(SgdbrCntrl *s)
{
    static int peak_loc = 0;
    unsigned int gie;
    int front_mirror_set, back_mirror_set, gain_set, soa_set;
    int coarse_phase_set, fine_phase_set, chirp_set, spare_set;
    int rd_config_set;

    gie = IRQ_globalDisable();
    s->temp_history[2] = s->temp_history[1];
    s->temp_history[1] = s->temp_history[0];
    s->temp_history[0] = laserTemp;

    if ((s->temp_history[1] <= s->temp_history[0]) && (s->temp_history[1] <= s->temp_history[2]))
    {
        s->temp_valley = s->temp_history[1];
        pulse_temp_ptp = (int)(1000 * (s->temp_peak - s->temp_valley)) + 0.001 * peak_loc;
    }

    if ((s->temp_history[1] >= s->temp_history[0]) && (s->temp_history[1] >= s->temp_history[2]))
    {
        s->temp_peak = s->temp_history[1];
        peak_loc = s->pulse_gen_counter;
        // Record the peak to peak amplitude and where in the cycle the peak occured
        pulse_temp_ptp = (int)(1000 * (s->temp_peak - s->temp_valley)) + 0.001 * peak_loc;
    }

    switch (state)
    {
    case SGDBR_CNTRL_DisabledState:
        s->pulse_gen_counter = 0;
        changeInMaskFPGA(s->fpga_csr, 1 << SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B, 0);
        front_mirror_set = 0;
        back_mirror_set = 0;
        gain_set = 0;
        soa_set = 0;
        coarse_phase_set = 0;
        fine_phase_set = 0;
        chirp_set = 0;
        spare_set = 0;
        rd_config_set = 0;
        break;
    case SGDBR_CNTRL_PulseGenState:
        changeInMaskFPGA(s->fpga_csr, 1 << SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B, 0);
        if (s->pulse_gen_counter >= 2 * semi_period)
        {
            s->pulse_gen_counter = 0;
            sensor_put_from(s->stream_pulse_temp_ptp, pulse_temp_ptp);
        }
        else if (s->pulse_gen_counter == semi_period)
        {
            sensor_put_from(s->stream_pulse_temp_ptp, pulse_temp_ptp);
        }
        s->pulse_gen_counter++;
        if (s->pulse_gen_counter <= semi_period)
        {
            front_mirror_set = front_mirror + front_step;
            back_mirror_set = back_mirror + back_step;
            gain_set = gain;
            soa_set = soa + soa_step;
            coarse_phase_set = coarse_phase + phase_step;
            fine_phase_set = fine_phase;
            chirp_set = chirp;
            spare_set = spare;
            rd_config_set = rd_config;
            break;
        }
        goto update_registers;
    case SGDBR_CNTRL_ManualState:
        s->pulse_gen_counter = 0;
        changeInMaskFPGA(s->fpga_csr, 1 << SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B, 0);
        goto update_registers;
    case SGDBR_CNTRL_AutomaticState:
        s->pulse_gen_counter = 0;
        changeInMaskFPGA(s->fpga_csr, 1 << SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B,
                         1 << SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B);
    update_registers:
        front_mirror_set = front_mirror;
        back_mirror_set = back_mirror;
        gain_set = gain;
        soa_set = soa;
        coarse_phase_set = coarse_phase;
        fine_phase_set = fine_phase;
        chirp_set = chirp;
        spare_set = spare;
        rd_config_set = rd_config;
        break;
    }
    // Set everything to zero if laser temperature is outside range (+/- 3 degrees) of setpoint
    if (!((laserTempSetpoint - laserTemp) <= laserTempWindow && (laserTempSetpoint - laserTemp) >= -laserTempWindow))
    {
        front_mirror_set = 0;
        back_mirror_set = 0;
        gain_set = 0;
        soa_set = 0;
        coarse_phase_set = 0;
        fine_phase_set = 0;
        chirp_set = 0;
        spare_set = 0;
        rd_config_set = 0;
    }
    // Set the currents
    if ((state != SGDBR_CNTRL_AutomaticState) || (front_mirror_set != s->front_mirror_old))
    {
        writeFPGA(s->fpga_mosi_data, SGDBR_FRONT_MIRROR_DAC | (0xFFFF & (int)front_mirror_set));
        _wait_done(s);
        s->front_mirror_old = front_mirror_set;
    }
    if ((state != SGDBR_CNTRL_AutomaticState) || (back_mirror_set != s->back_mirror_old))
    {
        writeFPGA(s->fpga_mosi_data, SGDBR_BACK_MIRROR_DAC | (0xFFFF & (int)back_mirror_set));
        _wait_done(s);
        s->back_mirror_old = back_mirror_set;
    }

    if ((state != SGDBR_CNTRL_AutomaticState) || (coarse_phase_set != s->coarse_phase_old))
    {
        writeFPGA(s->fpga_mosi_data, SGDBR_COARSE_PHASE_DAC | (0xFFFF & (int)coarse_phase_set));
        _wait_done(s);
        s->coarse_phase_old = coarse_phase_set;
    }
    if ((state != SGDBR_CNTRL_AutomaticState) || (fine_phase_set != s->fine_phase_old))
    {
        writeFPGA(s->fpga_mosi_data, SGDBR_FINE_PHASE_DAC | (0xFFFF & (int)fine_phase_set));
        _wait_done(s);
        s->fine_phase_old = fine_phase_set;
    }
    if ((state != SGDBR_CNTRL_AutomaticState) || (chirp_set != s->chirp_old))
    {
        writeFPGA(s->fpga_mosi_data, SGDBR_CHIRP_DAC | (0xFFFF & (int)chirp_set));
        _wait_done(s);
        s->chirp_old = chirp_set;
    }
    if ((state != SGDBR_CNTRL_AutomaticState) || (spare_set != s->spare_old))
    {
        writeFPGA(s->fpga_mosi_data, SGDBR_SPARE_DAC | (0xFFFF & (int)spare_set));
        _wait_done(s);
        s->spare_old = spare_set;
    }
    if ((state != SGDBR_CNTRL_AutomaticState) || (rd_config_set != s->rd_config_old))
    {
        writeFPGA(s->fpga_mosi_data, SGDBR_RD_CONFIG | (0xFFFF & rd_config_set));
        _wait_done(s);
        s->rd_config_old = rd_config_set;
    }
    // In order to support multiple lasers with combiners, we need to be able to support extinguishing
    //  deselected lasers. This involves turning off the gain and soa currents when in the Manual or Disabled
    //  control state and this is not the selected laser. In automatic mode, the current setting
    //  will be dealt with in spectrumCntrl.
    if (state != SGDBR_CNTRL_AutomaticState)
    {
        if (_get_extinguish_deselected() && s->name != _get_selected_sgdbr_laser())
        {
            gain_set = 0;
            soa_set = 0;
        }
        if (gain_set != s->gain_old)
        {
            writeFPGA(s->fpga_mosi_data, SGDBR_GAIN_DAC | (0xFFFF & (int)gain_set));
            _wait_done(s);
            s->gain_old = gain_set;
        }
        if (soa_set != s->soa_old)
        {
            writeFPGA(s->fpga_mosi_data, SGDBR_SOA_DAC | (0xFFFF & (int)soa_set));
            _wait_done(s);
            s->soa_old = soa_set;
        }
        last_auto_sgdbr = ' ';
    }
    else
    {
        s->gain_old = -1;
        s->soa_old = -1;
    }

    IRQ_globalRestore(gie);
    return STATUS_OK;
}

void setup_all_gain_and_soa_currents(void)
// This is called by spectrumCntrl.c to set up the gain and SOA currents for all SGDBR
//  lasers when the system is in automatic mode.
{
    int laserIndex, selIndex;
    char names[4] = {'A', 'B', 'C', 'D'};
    SgdbrCntrl *availSgdbrCntrl[4];
    SgdbrCntrl *selected, *deselected;
    char sel = _get_selected_sgdbr_laser();
	availSgdbrCntrl[0] = sA;
	availSgdbrCntrl[1] = sB;
	availSgdbrCntrl[2] = sC;
	availSgdbrCntrl[3] = sD;
    if ((sel != last_auto_sgdbr) && _get_extinguish_deselected())
    {
        // Find the selected laser
        for (selIndex=0; selIndex<4; selIndex++) {
            if (sel == names[selIndex]) {
                // Turn off gain and SOA currents for all deselected lasers
                for (laserIndex=0; laserIndex<4; laserIndex++) {
                    if (laserIndex == selIndex) continue;
                    if ((deselected = availSgdbrCntrl[laserIndex]) != NULL) {
                        writeFPGA(deselected->fpga_mosi_data, SGDBR_GAIN_DAC | 0);
                        _wait_done(deselected);
                        writeFPGA(deselected->fpga_mosi_data, SGDBR_SOA_DAC | 0);
                        _wait_done(deselected);
                    }
                }
                // Finally turn on gain and SOA currents for the selected laser
                if ((selected = availSgdbrCntrl[selIndex]) != NULL) {
                    writeFPGA(selected->fpga_mosi_data, SGDBR_GAIN_DAC | (int)*(selected->gain_));
                    _wait_done(selected);
                    writeFPGA(selected->fpga_mosi_data, SGDBR_SOA_DAC | (int)*(selected->soa_));
                    _wait_done(selected);
                }
                last_auto_sgdbr = names[selIndex];
                break;
            }
        }
    }
}

static double _sgdbrReadThermistorAdc(SgdbrCntrl *s)
{
    int complete, flags, result;
    writeFPGA(s->fpga_mosi_data, SGDBR_ADC_CONFIG);
    _wait_done(s);
    result = readFPGA_long(s->fpga_miso_data);
    complete = (result & 0x04000000) == 0;
    if (complete)
    {
        flags = (result >> 23) & 0x3;
        result = (result & 0x1FFFFFF) << 1;
        if (flags == 0)
            result = -0x1000000;
        else if (flags == 3)
            result = 0xFFFFFF;
        else
        {
            if (result >= 0x1000000)
                result = result - 0x2000000;
        }
        return result / 33554432.0;
    }
    else
        return -9999.0; // Indicates conversion incomplete
}

static int _sgdbrACntrlInit(void)
{
    SgdbrCntrl *s = &sgdbrACntrl;
    s->name = 'A';
    s->state_ = (unsigned int *)registerAddr(SGDBR_A_CNTRL_STATE_REGISTER);
    s->front_mirror_ = (float *)registerAddr(SGDBR_A_CNTRL_FRONT_MIRROR_REGISTER);
    s->back_mirror_ = (float *)registerAddr(SGDBR_A_CNTRL_BACK_MIRROR_REGISTER);
    s->gain_ = (float *)registerAddr(SGDBR_A_CNTRL_GAIN_REGISTER);
    s->soa_ = (float *)registerAddr(SGDBR_A_CNTRL_SOA_REGISTER);
    s->coarse_phase_ = (float *)registerAddr(SGDBR_A_CNTRL_COARSE_PHASE_REGISTER);
    s->fine_phase_ = (float *)registerAddr(SGDBR_A_CNTRL_FINE_PHASE_REGISTER);
    s->chirp_ = (float *)registerAddr(SGDBR_A_CNTRL_CHIRP_REGISTER);
    s->spare_ = (float *)registerAddr(SGDBR_A_CNTRL_SPARE_DAC_REGISTER);
    s->rd_config_ = (int *)registerAddr(SGDBR_A_CNTRL_RD_CONFIG_REGISTER);
    s->front_step_ = (float *)registerAddr(SGDBR_A_CNTRL_PULSE_FRONT_STEP_REGISTER);
    s->back_step_ = (float *)registerAddr(SGDBR_A_CNTRL_PULSE_BACK_STEP_REGISTER);
    s->phase_step_ = (float *)registerAddr(SGDBR_A_CNTRL_PULSE_PHASE_STEP_REGISTER);
    s->soa_step_ = (float *)registerAddr(SGDBR_A_CNTRL_PULSE_SOA_STEP_REGISTER);
    s->semi_period_ = (unsigned int *)registerAddr(SGDBR_A_CNTRL_PULSE_SEMI_PERIOD_REGISTER);
    s->laser_temp_ = (float *)registerAddr(LASER1_TEMPERATURE_REGISTER);
    s->laser_temp_setpoint_ = (float *)registerAddr(LASER1_TEMP_CNTRL_SETPOINT_REGISTER);
    s->laser_temp_window_ = (float *)registerAddr(TEMPERATURE_WINDOW_FOR_LASER_SHUTDOWN_REGISTER);
    s->pulse_temp_amplitude_ = (float *)registerAddr(SGDBR_A_CNTRL_PULSE_TEMP_AMPLITUDE_REGISTER);
    s->pulse_temp_ptp_ = (float *)registerAddr(SGDBR_A_CNTRL_PULSE_TEMP_PEAK_TO_PEAK_REGISTER);

    s->stream_pulse_temp_ptp = STREAM_SgdbrAPulseTempPtp;

    s->fpga_csr = FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_CSR;
    s->fpga_mosi_data = FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_MOSI_DATA;
    s->fpga_miso_data = FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_MISO_DATA;

    s->pulse_gen_counter = 0;
    s->temp_history[0] = s->temp_history[1] = s->temp_history[2] = s->temp_peak = s->temp_valley = laserTemp;
    s->front_mirror_old = -1;
    s->back_mirror_old = -1;
    s->gain_old = -1;
    s->soa_old = -1;
    s->coarse_phase_old = -1;
    s->fine_phase_old = -1;
    s->chirp_old = -1;
    s->spare_old = -1;
    s->rd_config_old = -1;

    sA = s;
    return 0;
}

static int _sgdbrBCntrlInit(void)
{
    SgdbrCntrl *s = &sgdbrBCntrl;
    s->name = 'B';
    s->state_ = (unsigned int *)registerAddr(SGDBR_B_CNTRL_STATE_REGISTER);
    s->front_mirror_ = (float *)registerAddr(SGDBR_B_CNTRL_FRONT_MIRROR_REGISTER);
    s->back_mirror_ = (float *)registerAddr(SGDBR_B_CNTRL_BACK_MIRROR_REGISTER);
    s->gain_ = (float *)registerAddr(SGDBR_B_CNTRL_GAIN_REGISTER);
    s->soa_ = (float *)registerAddr(SGDBR_B_CNTRL_SOA_REGISTER);
    s->coarse_phase_ = (float *)registerAddr(SGDBR_B_CNTRL_COARSE_PHASE_REGISTER);
    s->fine_phase_ = (float *)registerAddr(SGDBR_B_CNTRL_FINE_PHASE_REGISTER);
    s->chirp_ = (float *)registerAddr(SGDBR_B_CNTRL_CHIRP_REGISTER);
    s->spare_ = (float *)registerAddr(SGDBR_B_CNTRL_SPARE_DAC_REGISTER);
    s->rd_config_ = (int *)registerAddr(SGDBR_B_CNTRL_RD_CONFIG_REGISTER);
    s->front_step_ = (float *)registerAddr(SGDBR_B_CNTRL_PULSE_FRONT_STEP_REGISTER);
    s->back_step_ = (float *)registerAddr(SGDBR_B_CNTRL_PULSE_BACK_STEP_REGISTER);
    s->phase_step_ = (float *)registerAddr(SGDBR_B_CNTRL_PULSE_PHASE_STEP_REGISTER);
    s->soa_step_ = (float *)registerAddr(SGDBR_B_CNTRL_PULSE_SOA_STEP_REGISTER);
    s->semi_period_ = (unsigned int *)registerAddr(SGDBR_B_CNTRL_PULSE_SEMI_PERIOD_REGISTER);
    s->laser_temp_ = (float *)registerAddr(LASER3_TEMPERATURE_REGISTER);
    s->laser_temp_setpoint_ = (float *)registerAddr(LASER3_TEMP_CNTRL_SETPOINT_REGISTER);
    s->laser_temp_window_ = (float *)registerAddr(TEMPERATURE_WINDOW_FOR_LASER_SHUTDOWN_REGISTER);
    s->pulse_temp_ptp_ = (float *)registerAddr(SGDBR_B_CNTRL_PULSE_TEMP_PEAK_TO_PEAK_REGISTER);

    s->stream_pulse_temp_ptp = STREAM_SgdbrBPulseTempPtp;

    s->fpga_csr = FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_CSR;
    s->fpga_mosi_data = FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_MOSI_DATA;
    s->fpga_miso_data = FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_MISO_DATA;

    s->pulse_gen_counter = 0;
    s->temp_history[0] = s->temp_history[1] = s->temp_history[2] = s->temp_peak = s->temp_valley = laserTemp;
    s->front_mirror_old = -1;
    s->back_mirror_old = -1;
    s->gain_old = -1;
    s->soa_old = -1;
    s->coarse_phase_old = -1;
    s->fine_phase_old = -1;
    s->chirp_old = -1;
    s->spare_old = -1;
    s->rd_config_old = -1;

    sB = s;
    return 0;
}

static int _sgdbrCCntrlInit(void)
{
    SgdbrCntrl *s = &sgdbrCCntrl;
    s->name = 'C';
    s->state_ = (unsigned int *)registerAddr(SGDBR_C_CNTRL_STATE_REGISTER);
    s->front_mirror_ = (float *)registerAddr(SGDBR_C_CNTRL_FRONT_MIRROR_REGISTER);
    s->back_mirror_ = (float *)registerAddr(SGDBR_C_CNTRL_BACK_MIRROR_REGISTER);
    s->gain_ = (float *)registerAddr(SGDBR_C_CNTRL_GAIN_REGISTER);
    s->soa_ = (float *)registerAddr(SGDBR_C_CNTRL_SOA_REGISTER);
    s->coarse_phase_ = (float *)registerAddr(SGDBR_C_CNTRL_COARSE_PHASE_REGISTER);
    s->fine_phase_ = (float *)registerAddr(SGDBR_C_CNTRL_FINE_PHASE_REGISTER);
    s->chirp_ = (float *)registerAddr(SGDBR_C_CNTRL_CHIRP_REGISTER);
    s->spare_ = (float *)registerAddr(SGDBR_C_CNTRL_SPARE_DAC_REGISTER);
    s->rd_config_ = (int *)registerAddr(SGDBR_C_CNTRL_RD_CONFIG_REGISTER);
    s->front_step_ = (float *)registerAddr(SGDBR_C_CNTRL_PULSE_FRONT_STEP_REGISTER);
    s->back_step_ = (float *)registerAddr(SGDBR_C_CNTRL_PULSE_BACK_STEP_REGISTER);
    s->phase_step_ = (float *)registerAddr(SGDBR_C_CNTRL_PULSE_PHASE_STEP_REGISTER);
    s->soa_step_ = (float *)registerAddr(SGDBR_C_CNTRL_PULSE_SOA_STEP_REGISTER);
    s->semi_period_ = (unsigned int *)registerAddr(SGDBR_C_CNTRL_PULSE_SEMI_PERIOD_REGISTER);
    s->laser_temp_ = (float *)registerAddr(LASER2_TEMPERATURE_REGISTER);
    s->laser_temp_setpoint_ = (float *)registerAddr(LASER2_TEMP_CNTRL_SETPOINT_REGISTER);
    s->laser_temp_window_ = (float *)registerAddr(TEMPERATURE_WINDOW_FOR_LASER_SHUTDOWN_REGISTER);
    s->pulse_temp_ptp_ = (float *)registerAddr(SGDBR_C_CNTRL_PULSE_TEMP_PEAK_TO_PEAK_REGISTER);

    s->stream_pulse_temp_ptp = STREAM_SgdbrCPulseTempPtp;

    s->fpga_csr = FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_CSR;
    s->fpga_mosi_data = FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_MOSI_DATA;
    s->fpga_miso_data = FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_MISO_DATA;

    s->pulse_gen_counter = 0;
    s->temp_history[0] = s->temp_history[1] = s->temp_history[2] = s->temp_peak = s->temp_valley = laserTemp;
    s->front_mirror_old = -1;
    s->back_mirror_old = -1;
    s->gain_old = -1;
    s->soa_old = -1;
    s->coarse_phase_old = -1;
    s->fine_phase_old = -1;
    s->chirp_old = -1;
    s->spare_old = -1;
    s->rd_config_old = -1;

    sC = s;
    return 0;
}

static int _sgdbrDCntrlInit(void)
{
    SgdbrCntrl *s = &sgdbrDCntrl;
    s->name = 'D';
    s->state_ = (unsigned int *)registerAddr(SGDBR_D_CNTRL_STATE_REGISTER);
    s->front_mirror_ = (float *)registerAddr(SGDBR_D_CNTRL_FRONT_MIRROR_REGISTER);
    s->back_mirror_ = (float *)registerAddr(SGDBR_D_CNTRL_BACK_MIRROR_REGISTER);
    s->gain_ = (float *)registerAddr(SGDBR_D_CNTRL_GAIN_REGISTER);
    s->soa_ = (float *)registerAddr(SGDBR_D_CNTRL_SOA_REGISTER);
    s->coarse_phase_ = (float *)registerAddr(SGDBR_D_CNTRL_COARSE_PHASE_REGISTER);
    s->fine_phase_ = (float *)registerAddr(SGDBR_D_CNTRL_FINE_PHASE_REGISTER);
    s->chirp_ = (float *)registerAddr(SGDBR_D_CNTRL_CHIRP_REGISTER);
    s->spare_ = (float *)registerAddr(SGDBR_D_CNTRL_SPARE_DAC_REGISTER);
    s->rd_config_ = (int *)registerAddr(SGDBR_D_CNTRL_RD_CONFIG_REGISTER);
    s->front_step_ = (float *)registerAddr(SGDBR_D_CNTRL_PULSE_FRONT_STEP_REGISTER);
    s->back_step_ = (float *)registerAddr(SGDBR_D_CNTRL_PULSE_BACK_STEP_REGISTER);
    s->phase_step_ = (float *)registerAddr(SGDBR_D_CNTRL_PULSE_PHASE_STEP_REGISTER);
    s->soa_step_ = (float *)registerAddr(SGDBR_D_CNTRL_PULSE_SOA_STEP_REGISTER);
    s->semi_period_ = (unsigned int *)registerAddr(SGDBR_D_CNTRL_PULSE_SEMI_PERIOD_REGISTER);
    s->laser_temp_ = (float *)registerAddr(LASER4_TEMPERATURE_REGISTER);
    s->laser_temp_setpoint_ = (float *)registerAddr(LASER4_TEMP_CNTRL_SETPOINT_REGISTER);
    s->laser_temp_window_ = (float *)registerAddr(TEMPERATURE_WINDOW_FOR_LASER_SHUTDOWN_REGISTER);
    s->pulse_temp_ptp_ = (float *)registerAddr(SGDBR_D_CNTRL_PULSE_TEMP_PEAK_TO_PEAK_REGISTER);

    s->stream_pulse_temp_ptp = STREAM_SgdbrDPulseTempPtp;

    s->fpga_csr = FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_CSR;
    s->fpga_mosi_data = FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_MOSI_DATA;
    s->fpga_miso_data = FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_MISO_DATA;

    s->pulse_gen_counter = 0;
    s->temp_history[0] = s->temp_history[1] = s->temp_history[2] = s->temp_peak = s->temp_valley = laserTemp;
    s->front_mirror_old = -1;
    s->back_mirror_old = -1;
    s->gain_old = -1;
    s->soa_old = -1;
    s->coarse_phase_old = -1;
    s->fine_phase_old = -1;
    s->chirp_old = -1;
    s->spare_old = -1;
    s->rd_config_old = -1;

    sD = s;
    return 0;
}

int sgdbrCntrlInit(int laserIndex)
// Initialize the control structure for SGDBR laser specified by laserIndex (0=A, 1=B, 2=C, 3=D)
{
    switch (laserIndex)
    {
    case 0:
        return _sgdbrACntrlInit();
    case 1:
        return _sgdbrBCntrlInit();
    case 2:
        return _sgdbrCCntrlInit();
    case 3:
        return _sgdbrDCntrlInit();
    default:
        message_puts(LOG_LEVEL_CRITICAL, "Invalid laser index in sgdbrCntrlInit");
        return ERROR_BAD_VALUE;
    }
}

int sgdbrCntrlStep(int laserIndex)
// Perform single step of the SGDBR laser controller for SGDBR laser specified by laserIndex (0=A, 1=B, 2=C, 3=D)
{
    if (laserIndex < 0 || laserIndex >= 4)
    {
        message_puts(LOG_LEVEL_CRITICAL, "Invalid laser index in sgdbrCntrlStep");
        return ERROR_BAD_VALUE;
    }
    else
    {
        return _sgdbrCntrlStep(sgdbrCntrl[laserIndex]);
    }
}

void sgdbrProgramFpga(int laserIndex)
// Program FPGA for SGDBR laser specified by laserIndex (0=A, 1=B, 2=C, 3=D)
{
    if (laserIndex < 0 || laserIndex >= 4)
    {
        message_puts(LOG_LEVEL_CRITICAL, "Invalid laser index in sgdbrProgramFpga");
    }
    else
    {
        _sgdbrProgramFpga(sgdbrCntrl[laserIndex]);
    }
}

double sgdbrReadThermistorAdc(int laserIndex)
// Return thermistor ADC value for SGDBR laser specified by laserIndex (0=A, 1=B, 2=C, 3=D)
{
    static double last_valid[] = {0.0, 0.0, 0.0, 0.0};
    double result;
    if (laserIndex < 0 || laserIndex >= 4)
    {
        message_puts(LOG_LEVEL_CRITICAL, "Invalid laser index in sgdbrReadThermistorAdc");
        return -9999.0;
    }
    else
    {
        result = _sgdbrReadThermistorAdc(sgdbrCntrl[laserIndex]);
        if (result >= -1.0)
        {
            last_valid[laserIndex] = result;
        }
        else
        { // Incomplete conversion, return last valid
            result = last_valid[laserIndex];
        }
        return result;
    }
}
