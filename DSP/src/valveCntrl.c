/*
 * FILE:
 *   valveCntrl.c
 *
 * DESCRIPTION:
 *   Valve control routines. The valve controller consists of three subparts:
 *    a) Inlet or outlet proportional valve control to set cavity pressure to a desired
 *        setpoint.
 *    b) Trapping a gas sample on the basis of the optical absorption measured at a single
 *        frequency.
 *    c) Sequencing the solenoid valves according to a preloaded table.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   31-Aug-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include "interface.h"
#include "registers.h"
#include "valveCntrl.h"
#include "dspAutogen.h"
#include "dspData.h"
#include "fpga.h"
#include "i2c_dsp.h"
#include "ltc2485.h"
#include "pca8574.h"
#include "pca9538.h"
#include <math.h>
#include <stdio.h>
#define INVALID_PRESSURE_VALUE (-100.0)

#define state           (*(v->state_))
#define cavityPressure  (*(v->cavityPressure_))
#define setpoint        (*(v->setpoint_))
#define userInlet       (*(v->userInlet_))
#define userOutlet      (*(v->userOutlet_))
#define inlet           (*(v->inlet_))
#define outlet          (*(v->outlet_))
#define dpdtMax         (*(v->dpdtMax_))
#define dpdtAbort       (*(v->dpdtAbort_))
#define inletGain1      (*(v->inletGain1_))
#define inletGain2      (*(v->inletGain2_))
#define inletMin        (*(v->inletMin_))
#define inletMax        (*(v->inletMax_))
#define inletMaxChange  (*(v->inletMaxChange_))
#define outletGain1     (*(v->outletGain1_))
#define outletGain2     (*(v->outletGain2_))
#define outletMin       (*(v->outletMin_))
#define outletMax       (*(v->outletMax_))
#define outletMaxChange (*(v->outletMaxChange_))
#define solenoidValves  (*(v->solenoidValves_))
#define threshState     (*(v->threshState_))
#define latestLoss      (*(v->latestLoss_))
#define lossThreshold   (*(v->lossThreshold_))
#define rateThreshold   (*(v->rateThreshold_))
#define inletTriggeredValue     (*(v->inletTriggeredValue_))
#define outletTriggeredValue    (*(v->outletTriggeredValue_))
#define solenoidMask    (*(v->solenoidMask_))
#define solenoidState   (*(v->solenoidState_))
#define sequenceStep    (*(v->sequenceStep_))

ValveCntrl valveCntrl;

void proportionalValveStep()
{
    ValveCntrl *v = &valveCntrl;
    float delta, dError, dpdt, dpdtSet, error, valveValue;

    if (v->lastPressure > INVALID_PRESSURE_VALUE) {
        dpdt = (cavityPressure-v->lastPressure)/v->deltaT;
        if (cavityPressure-v->lastPressure >= -0.2) v->nonDecreasingCount++;
        else v->nonDecreasingCount = 0;
    }
    else
        dpdt = 0;
    error = setpoint - cavityPressure;
    v->lastPressure = cavityPressure;
    
    if (dpdt >= dpdtAbort || dpdt <= -dpdtAbort) {
        message_puts("Maximum pressure change exceeded. Valves closed to protect cavity.");
        state = VALVE_CNTRL_DisabledState;
    }
    
    switch (state)
    {
    case VALVE_CNTRL_DisabledState:
        inlet = 0;
        outlet = 0;
        v->nonDecreasingCount = 0;
        break;
    case VALVE_CNTRL_ManualControlState:
        inlet = userInlet;
        outlet = userOutlet;
        break;
    case VALVE_CNTRL_OutletControlState:
        inlet = userInlet;
        // Gain2 sets how the pressure rate setpoint depends on the pressure error
        dpdtSet = outletGain2 * error;
        // Limit rate setpoint to maximum allowed rate of change
        if (dpdtSet < -dpdtMax) dpdtSet = -dpdtMax;
        else if (dpdtSet > dpdtMax) dpdtSet = dpdtMax;
        // Following implements an integral controller for the rate of change of pressure
        // Gain1 sets the integral gain
        dError = dpdtSet - dpdt;
        delta = -outletGain1 * dError;  // -ve because opening outlet decreases pressure
        // Limit change of valve value
        if (delta < -outletMaxChange) delta = -outletMaxChange;
        else if (delta > outletMaxChange) delta = outletMaxChange;
        valveValue = outlet + delta;
        // Limit absolute valve value
        if (valveValue < outletMin) valveValue = outletMin;
        else if (valveValue > outletMax) valveValue = outletMax;
        outlet = valveValue;
        break;
    case VALVE_CNTRL_InletControlState:
        outlet = userOutlet;
        // Gain2 sets how the pressure rate setpoint depends on the pressure error
        dpdtSet = inletGain2 * error;
        // Limit rate setpoint to maximum allowed rate of change
        if (dpdtSet < -dpdtMax) dpdtSet = -dpdtMax;
        else if (dpdtSet > dpdtMax) dpdtSet = dpdtMax;
        // Following implements an integral controller for the rate of change of pressure
        // Gain1 sets the integral gain
        dError = dpdtSet - dpdt;
        delta = inletGain1 * dError;   // +ve because opening inlet increases pressure
        // Limit change of valve value
        if (delta < -inletMaxChange) delta = -inletMaxChange;
        if (delta > inletMaxChange) delta = inletMaxChange;
        valveValue = inlet + delta;
        // Limit absolute valve value
        if (valveValue < inletMin) valveValue = inletMin;
        if (valveValue > inletMax) valveValue = inletMax;
        inlet = valveValue;
        if (inlet <= inletMin && v->nonDecreasingCount>10) {
            message_puts("Check vacuum pump connection, valves closed to protect cavity.");
            state = VALVE_CNTRL_DisabledState;
        }        
        break;
    }
    userInlet = inlet;
    userOutlet = outlet;
    if (outlet >= outletMax && v->nonDecreasingCount>10) {
        message_puts("Check vacuum pump connection, valves closed to protect cavity.");
        state = VALVE_CNTRL_DisabledState;
    }
}

#define SWAP(a,b) { float temp=(a); (a)=(b); (b)=temp; }
#define SORT(a,b) { if ((a)>(b)) SWAP((a),(b)); }

void thresholdTriggerStep()
{
    ValveCntrl *v = &valveCntrl;
    // Variables for median filter of last five losses
    static float last5[5] = {0.0, 0.0, 0.0, 0.0, 0.0};
    float t0, t1, t2, t3, t4, lossPpb, lossRate;

    lossPpb = 1000.0*latestLoss;
    // Calculate rolling median of last five loss points
    t0 = last5[0];
    t1 = last5[1];
    t2 = last5[2];
    t3 = last5[3];
    t4 = last5[4];
    SORT(t0,t1);
    SORT(t3,t4);
    SORT(t0,t3);
    SORT(t1,t4);
    SORT(t1,t2);
    SORT(t2,t3);
    SORT(t1,t2);
    lossPpb = t2;

    // Calculate rate of change of loss
    lossRate = (lossPpb - v->lastLossPpb)/v->deltaT;
    v->lastLossPpb = lossPpb;

    if (threshState == VALVE_CNTRL_THRESHOLD_ArmedState)
    {
        // When armed, check if loss is above rising loss threshold and if
        //  rate is below rising loss rate threshold. If both hold, the system
        //  enters the triggered state.
        if (lossPpb >= lossThreshold && lossRate <= rateThreshold)
        {
            state = VALVE_CNTRL_ManualControlState;
            if (outletTriggeredValue >= 0) outlet = outletTriggeredValue;
            if (inletTriggeredValue >= 0)  inlet = inletTriggeredValue;
            // Set up the solenoid valve state based on solenoidMask
            //  and solenoidState
            solenoidValves = (solenoidValves & ~solenoidMask) | (solenoidState & solenoidMask);
            threshState = VALVE_CNTRL_THRESHOLD_TriggeredState;
        }
    }
}

void valveSequencerStep()
{
    ValveCntrl *v = &valveCntrl;
    if (sequenceStep >= 0)   // Valve sequencing is enabled
    {
        if (sequenceStep < NUM_VALVE_SEQUENCE_ENTRIES)
        {
            unsigned short maskAndValue = valveSequence[sequenceStep].maskAndValue;
            unsigned short dwell = valveSequence[sequenceStep].dwell;
            // Zero maskAndValue means that we should stay at the present step
            if (maskAndValue != 0)
            {
                unsigned int value = maskAndValue & 0xFF;
                maskAndValue >>= 8;
                if (v->dwellCount == 0)       // Update the solenoid valves
                {
                    solenoidValves = (solenoidValves & ~maskAndValue) | value;
                }
                if (v->dwellCount >= dwell)   // Move to the next step in the sequence
                {
                    sequenceStep += 1;
                    v->dwellCount = 0;
                }
                else v->dwellCount++;
            }
        }
        else sequenceStep = -1;
    }
}

static int valveCntrlDelay = 10;

int valveCntrlStep()
{
    ValveCntrl *v = &valveCntrl;
    // Step the valve controller
    if (valveCntrlDelay == 0) {
        proportionalValveStep();
        thresholdTriggerStep();
        valveSequencerStep();
        modify_valve_pump_tec(0x3F,solenoidValves);
    } 
    else valveCntrlDelay--;
    return STATUS_OK;
}

int valveCntrlInit(void)
{
    ValveCntrl *v = &valveCntrl;
    
    valveCntrlDelay = 20;
    v->state_               = (VALVE_CNTRL_StateType *)registerAddr(VALVE_CNTRL_STATE_REGISTER);
    v->cavityPressure_      = (float*)registerAddr(CAVITY_PRESSURE_REGISTER);
    v->setpoint_            = (float*)registerAddr(VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER);
    v->userInlet_           = (float*)registerAddr(VALVE_CNTRL_USER_INLET_VALVE_REGISTER);
    v->userOutlet_          = (float*)registerAddr(VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER);
    v->inlet_               = (float*)registerAddr(VALVE_CNTRL_INLET_VALVE_REGISTER);
    v->outlet_              = (float*)registerAddr(VALVE_CNTRL_OUTLET_VALVE_REGISTER);
    v->dpdtMax_             = (float*)registerAddr(VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER);
    v->dpdtAbort_           = (float*)registerAddr(VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER);
    v->inletGain1_          = (float*)registerAddr(VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER);
    v->inletGain2_          = (float*)registerAddr(VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER);
    v->inletMin_            = (float*)registerAddr(VALVE_CNTRL_INLET_VALVE_MIN_REGISTER);
    v->inletMax_            = (float*)registerAddr(VALVE_CNTRL_INLET_VALVE_MAX_REGISTER);
    v->inletMaxChange_      = (float*)registerAddr(VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER);
    v->outletGain1_         = (float*)registerAddr(VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER);
    v->outletGain2_         = (float*)registerAddr(VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER);
    v->outletMin_           = (float*)registerAddr(VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER);
    v->outletMax_           = (float*)registerAddr(VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER);
    v->outletMaxChange_     = (float*)registerAddr(VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER);
    v->solenoidValves_      = (unsigned int*)registerAddr(VALVE_CNTRL_SOLENOID_VALVES_REGISTER);
    v->threshState_         = (VALVE_CNTRL_THRESHOLD_StateType *)registerAddr(VALVE_CNTRL_THRESHOLD_STATE_REGISTER);
    v->latestLoss_          = (float*)registerAddr(RDFITTER_LATEST_LOSS_REGISTER);
    v->lossThreshold_       = (float*)registerAddr(VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER);
    v->rateThreshold_       = (float*)registerAddr(VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER);
    v->inletTriggeredValue_ = (float*)registerAddr(VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER);
    v->outletTriggeredValue_= (float*)registerAddr(VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER);
    v->solenoidMask_        = (unsigned int*)registerAddr(VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER);
    v->solenoidState_       = (unsigned int*)registerAddr(VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER);
    v->sequenceStep_        = (int*)registerAddr(VALVE_CNTRL_SEQUENCE_STEP_REGISTER);

    state = VALVE_CNTRL_DisabledState;
    threshState = VALVE_CNTRL_THRESHOLD_DisabledState;
    inlet = 0;
    outlet = 0;
    solenoidValves = 0;
    sequenceStep = -1;
    v->deltaT = 0.2;
    v->lastLossPpb = 0;
    v->lastPressure = INVALID_PRESSURE_VALUE;
    v->dwellCount = 0;
    v->nonDecreasingCount = 0;

    // modify_valve_pump_tec(0x7F,0);    // Close all valves, turn off pump
    return STATUS_OK;
}

int modify_valve_pump_tec(unsigned int mask, unsigned int code)
// Writes to PCA9538 I2C to parallel port which controls states of solenoid valves, pump and TEC PWM.
//  Note the inversion, which is needed since the I2C port starts up with its outputs high.
{
    I2C_device *d = &i2c_devices[VALVE_PUMP_TEC_PORT];
    static unsigned int shadow = 0;
    unsigned int loops, newValue;
    int powerBoardPresent = *(int *)registerAddr(HARDWARE_PRESENT_REGISTER) & (1<<HARDWARE_PRESENT_PowerBoardBit);
    int activeMask = (1<<PWM_CS_RUN_B)|(1<<PWM_CS_CONT_B);
    int warmBoxPwmActive = (readFPGA(FPGA_PWM_WARMBOX+PWM_CS) & activeMask) == activeMask;
    int hotBoxPwmActive = (readFPGA(FPGA_PWM_HOTBOX+PWM_CS) & activeMask) == activeMask;

    newValue = (shadow & (~mask)) | (code & mask);
    if (powerBoardPresent) {    
        setI2C1Mux(d->mux);  // Select SC15 and SD15
        for (loops=0;loops<1000;loops++);
        if (warmBoxPwmActive && hotBoxPwmActive) {
            pca9538_wrConfig(d,0);
            for (loops=0;loops<1000;loops++);
            pca9538_wrOutput(d,~newValue);
        }
    }
    shadow = newValue;
    return STATUS_OK;
}

int write_valve_pump_tec(unsigned int code)
// Writes to I2C to parallel port which controls states of solenoid valves, pump and TEC PWM.
//  Note the inversion, which is needed since the I2C port starts up with its outputs high.
{
    return modify_valve_pump_tec(0xFF,code);
}

int read_cavity_pressure_adc()
// Read cavity pressure ADC. Returns I2C_READ_ERROR on I2C error.
{
    int flags, result, loops;
    I2C_device *d = &i2c_devices[CAVITY_PRESSURE_ADC];

    setI2C0Mux(d->mux);  // I2C bus 7
    for (loops=0;loops<1000;loops++);
    result = ltc2485_getData(d, &flags);
    if (result==I2C_READ_ERROR) return result;
    if (flags == 0) result = -16777216;
    else if (flags == 3) result = 16777215;
    return result;
}

int read_ambient_pressure_adc()
// Read ambient pressure ADC. Returns I2C_READ_ERROR on I2C error.
{
    int flags, result, loops;
    I2C_device *d = &i2c_devices[AMBIENT_PRESSURE_ADC];

    setI2C0Mux(d->mux);  // I2C bus 7
    for (loops=0;loops<1000;loops++);
    result = ltc2485_getData(d, &flags);
    if (result==I2C_READ_ERROR) return result;
    if (flags == 0) result = -16777216;
    else if (flags == 3) result = 16777215;
    return result;
}
