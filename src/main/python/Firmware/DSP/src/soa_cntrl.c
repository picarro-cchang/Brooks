/*
 * FILE:
 *   soa_cntrl.c
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
#include "registers.h"
#include "interface.h"
#include "soa_cntrl.h"
#include "i2c_dsp.h"
#include <math.h>

int soa_cntrl_step(SoaCntrl *s)
{
    float Vref, Vcom; // LTC2493 ADC reference and common voltages
    float Rwiper, Rpot, Rsense, Iref;  // Current source parameters
    float mon_adc, Iset, temp_set;
    int status, bitmask, enable, Dset, Tset;

    Vref = 2.5;
    Vcom = 1.25;
    Rwiper = 160.0;  // Digital potentiometer wiper resistance
    Rpot = 100000.0; // Digital potentiometer value
    Rsense = 1.3;    // Sense resistor for current source
    Iref = 10.0e-6;  // Reference current for regulator

    // Check if we need to change the state of the IO line which disables 
    //  SOA current source in the control register
    if (*(s->soa_enable_mask_) != (s->prev_soa_enable_mask))
    {
        bitmask = 1 << (s->soa_index - 1);
        enable = *(s->soa_enable_mask_) & bitmask;
        if (enable != (s->prev_soa_enable_mask & bitmask))
        {
            if (enable)
                pca8574_write(s->i2c_control_ident, 0);
            else
                pca8574_write(s->i2c_control_ident, 1);
        }
        s->prev_soa_enable_mask = *(s->soa_enable_mask_);
    }

    // Set up the digital potentiometer for the specfied current setpoint
    // SOA Current in mA where D is the digital pot setting is
    //  1000.0 * (2*Rwiper + Rpot * (D/256.0)) * Iref / Rsense
    // Inverse relation is
    //  D = 256*((Iset*Rsense)/(1000.0*Iref) - 2*Rwiper)/Rpot
    Iset = *(s->current_setpoint_);  // Setpoint in mA
    Dset = (int)(256.0 * ((Iset * Rsense) / (1000.0 * Iref) - 2 * Rwiper)/Rpot + 0.5);
    if (Dset > 255) Dset = 255;
    if (Dset < 0) Dset = 0;
    // Update setpoint to available value
    *(s->current_setpoint_) = 1000.0 * (2*Rwiper + Rpot * (Dset/256.0)) * Iref / Rsense;
    if (Dset != s->prev_dset) {
        ad5248_write(s->i2c_current_ident, 0, Dset);
        s->prev_dset = Dset;
    }

    // Set up the DAC for the specified TEC temperature setpoint
    //  Temperature setpoint to voltage:
    //  V = (T+25.0)/40.0 where T is in Celsius
    // Vref for DAC is 2.5V

    temp_set = *(s->temperature_setpoint_);
    Tset = (int)((65536.0 / Vref) * (temp_set + 25.0)/40.0 + 0.5);
    if (Tset > 65535) Tset = 65535;
    if (Tset < 0) Tset = 0;
    // Update setpoint to available value
    *(s->temperature_setpoint_) = 40.0*Vref*Tset/65536.0 - 25.0;
    if (Tset != s->prev_tset) {
        ltc2606_write(s->i2c_tec_ident, Tset);
        s->prev_tset = Tset;
    }

    // Set up the ADC monitor reading
    mon_adc = ltc2493se_read(s->i2c_monitor_ident, s->monitor_counter, &status) / 33554432.0;
    if (status != 0)
        return status;
    if (mon_adc < 0.0 || mon_adc > 1.0)
        return ERROR_BAD_VALUE;
    mon_adc = Vcom + Vref * (mon_adc - 0.5); // Convert to voltage
    switch (s->monitor_counter)
    {
    case 0:
        // ADC readback is from channel 2
        *(s->temperature_monitor_) = 40.0 * mon_adc - 25.0;
        s->monitor_counter = 1;
        break;
    case 1:
        // ADC readback is from channel 0
        *(s->tec_voltage_monitor_) = (mon_adc - 1.25)/0.25;
        s->monitor_counter = 2;
        break;
    case 2:
        // ADC readback is from channel 1
        *(s->tec_current_monitor_) = (mon_adc - 1.25)/0.525;
        s->monitor_counter = 0;
        break;
    default:
        // Should not get here
        s->monitor_counter = 0;
        break;
    }

    return STATUS_OK;
}

SoaCntrl soa_cntrl_soa1;
SoaCntrl soa_cntrl_soa2;
SoaCntrl soa_cntrl_soa3;
SoaCntrl soa_cntrl_soa4;

int soa_cntrl_soa1_init(int i2c_current_ident, int i2c_control_ident, int i2c_tec_ident, int i2c_monitor_ident)
{
    SoaCntrl *s = &soa_cntrl_soa1;
    s->soa_index = 1;
    s->monitor_counter = 0;
    s->prev_soa_enable_mask = 0;
    s->prev_dset = 0;
    s->prev_tset = 0;
    s->i2c_current_ident = i2c_current_ident;
    s->i2c_control_ident = i2c_control_ident;
    s->i2c_tec_ident = i2c_tec_ident;
    s->i2c_monitor_ident = i2c_monitor_ident;

    s->current_setpoint_ = (float *)registerAddr(SOA1_CURRENT_SETPOINT_REGISTER);
    s->temperature_setpoint_ = (float *)registerAddr(SOA1_TEMPERATURE_SETPOINT_REGISTER);
    s->tec_current_monitor_ = (float *)registerAddr(SOA1_TEC_CURRENT_MONITOR_REGISTER);
    s->tec_voltage_monitor_ = (float *)registerAddr(SOA1_TEC_VOLTAGE_MONITOR_REGISTER);
    s->temperature_monitor_ = (float *)registerAddr(SOA1_TEMPERATURE_MONITOR_REGISTER);
    s->soa_enable_mask_ = (unsigned int *)registerAddr(SOA_ENABLE_MASK_REGISTER);
    return STATUS_OK;
}

int soa_cntrl_soa1_step(void)
{
    int status;
    status = soa_cntrl_step(&soa_cntrl_soa1);
    return status;
}

int soa_cntrl_soa2_init(int i2c_current_ident, int i2c_control_ident, int i2c_tec_ident, int i2c_monitor_ident)
{
    SoaCntrl *s = &soa_cntrl_soa2;
    s->soa_index = 2;
    s->monitor_counter = 0;
    s->prev_soa_enable_mask = 0;
    s->prev_dset = 0;
    s->prev_tset = 0;
    s->i2c_current_ident = i2c_current_ident;
    s->i2c_control_ident = i2c_control_ident;
    s->i2c_tec_ident = i2c_tec_ident;
    s->i2c_monitor_ident = i2c_monitor_ident;

    s->current_setpoint_ = (float *)registerAddr(SOA2_CURRENT_SETPOINT_REGISTER);
    s->temperature_setpoint_ = (float *)registerAddr(SOA2_TEMPERATURE_SETPOINT_REGISTER);
    s->tec_current_monitor_ = (float *)registerAddr(SOA2_TEC_CURRENT_MONITOR_REGISTER);
    s->tec_voltage_monitor_ = (float *)registerAddr(SOA2_TEC_VOLTAGE_MONITOR_REGISTER);
    s->temperature_monitor_ = (float *)registerAddr(SOA2_TEMPERATURE_MONITOR_REGISTER);
    s->soa_enable_mask_ = (unsigned int *)registerAddr(SOA_ENABLE_MASK_REGISTER);
    return STATUS_OK;
}

int soa_cntrl_soa2_step(void)
{
    int status;
    status = soa_cntrl_step(&soa_cntrl_soa2);
    return status;
}

int soa_cntrl_soa3_init(int i2c_current_ident, int i2c_control_ident, int i2c_tec_ident, int i2c_monitor_ident)
{
    SoaCntrl *s = &soa_cntrl_soa3;
    s->soa_index = 3;
    s->monitor_counter = 0;
    s->prev_soa_enable_mask = 0;
    s->prev_dset = 0;
    s->prev_tset = 0;
    s->i2c_current_ident = i2c_current_ident;
    s->i2c_control_ident = i2c_control_ident;
    s->i2c_tec_ident = i2c_tec_ident;
    s->i2c_monitor_ident = i2c_monitor_ident;

    s->current_setpoint_ = (float *)registerAddr(SOA3_CURRENT_SETPOINT_REGISTER);
    s->temperature_setpoint_ = (float *)registerAddr(SOA3_TEMPERATURE_SETPOINT_REGISTER);
    s->tec_current_monitor_ = (float *)registerAddr(SOA3_TEC_CURRENT_MONITOR_REGISTER);
    s->tec_voltage_monitor_ = (float *)registerAddr(SOA3_TEC_VOLTAGE_MONITOR_REGISTER);
    s->temperature_monitor_ = (float *)registerAddr(SOA3_TEMPERATURE_MONITOR_REGISTER);
    s->soa_enable_mask_ = (unsigned int *)registerAddr(SOA_ENABLE_MASK_REGISTER);
    return STATUS_OK;
}

int soa_cntrl_soa3_step(void)
{
    int status;
    status = soa_cntrl_step(&soa_cntrl_soa3);
    return status;
}

int soa_cntrl_soa4_init(int i2c_current_ident, int i2c_control_ident, int i2c_tec_ident, int i2c_monitor_ident)
{
    SoaCntrl *s = &soa_cntrl_soa4;
    s->soa_index = 4;
    s->monitor_counter = 0;
    s->prev_soa_enable_mask = 0;
    s->prev_dset = 0;
    s->prev_tset = 0;
    s->i2c_current_ident = i2c_current_ident;
    s->i2c_control_ident = i2c_control_ident;
    s->i2c_tec_ident = i2c_tec_ident;
    s->i2c_monitor_ident = i2c_monitor_ident;

    s->current_setpoint_ = (float *)registerAddr(SOA4_CURRENT_SETPOINT_REGISTER);
    s->temperature_setpoint_ = (float *)registerAddr(SOA4_TEMPERATURE_SETPOINT_REGISTER);
    s->tec_current_monitor_ = (float *)registerAddr(SOA4_TEC_CURRENT_MONITOR_REGISTER);
    s->tec_voltage_monitor_ = (float *)registerAddr(SOA4_TEC_VOLTAGE_MONITOR_REGISTER);
    s->temperature_monitor_ = (float *)registerAddr(SOA4_TEMPERATURE_MONITOR_REGISTER);
    s->soa_enable_mask_ = (unsigned int *)registerAddr(SOA_ENABLE_MASK_REGISTER);
    return STATUS_OK;
}

int soa_cntrl_soa4_step(void)
{
    int status;
    status = soa_cntrl_step(&soa_cntrl_soa4);
    return status;
}
