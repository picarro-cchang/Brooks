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
#include <math.h>
#include <stdio.h>

    VALVE_CNTRL_StateType *state_;      // Valve controller state
    float *setpoint_;                   // Cavity pressure setpoint
    float *inlet_;                      // Inlet valve value
    float *outlet_;                     // Outlet valve value
    float *dpdtMax_;                    // Maximum rate of change of pressure
    float *inletGain1_;                 // Gain 1 for inlet valve
    float *inletGain2_;                 // Gain 2 for inlet valve
    float *inletMin_;                   // Minimum for inlet valve
    float *inletMax_;                   // Maximum for inlet valve
    float *inletMaxChange_;             // Maximum change for inlet valve
    float *outletGain1_;                // Gain 1 for outlet valve
    float *outletGain2_;                // Gain 2 for outlet valve
    float *outletMin_;                  // Minimum for outlet valve
    float *outletMax_;                  // Maximum for outlet valve
    float *outletMaxChange_;            // Maximum change for outlet valve

    VALVE_CNTRL_THRESHOLD_StateType *threshState;   // Threshold state
    float *lossThreshold_;              // Loss threshold for triggering
    float *rateThreshold_;              // Rate threshold for triggering
    float *inletTriggeredValue_;        // Value for inlet valve when triggered
    float *outletTriggeredValue_;       // Value for outlet valve when triggered
    unsigned int *solenoidMask_;        // Mask to apply to solenoid valves when triggered
    unsigned int *solenoidState_;       // Solenoid valve states when triggered
    int *sequenceStep_;                 // Sequence step


#define state           (*(v->state_))
#define setpoint        (*(v->setpoint_))
#define inlet           (*(v->inlet_))
#define outlet          (*(v->outlet_))
#define dpdtMax         (*(v->dpdtMax_))
#define inletGain1      (*(v->inletGain1_))
#define inletGain2      (*(v->inletGain2_))
#define inletMin        (*(v->inletMin_))
#define inletMax        (*(v->inletMax_))
#define inletMaxChange  (*(v->inletMaxChange_))
#define outletGain1     (*(v->outletGain1_))
#define outletGain2     (*(v->outletGain2_))
#define outletMin       (*(v->outletMin_))
#define outletMax       (*(v->outetMax_))
#define outletMaxChange (*(v->outletMaxChange_))
#define threshState     (*(v->threshState_))
#define lossThreshold   (*(v->lossThreshold_))
#define rateThreshold   (*(v->rateThreshold_))
#define inletTriggeredValue     (*(v->inletTriggeredValue_))
#define outletTriggeredValue    (*(v->outletTriggeredValue_))
#define solenoidMask    (*(v->solenoidMask_))
#define solenoidState   (*(v->solenoidState_))
#define sequenceStep    (*(v->sequenceStep_))

ValveCntrl valveCntrl;

int valveCntrlStep()
{
    ValveCntrl *v = &valveCntrl;
    char msg[120];
    // Step the valve controller

    if (sequenceStep >= 0) { // Valve sequencing is enabled
        if (sequenceStep < NUM_VALVE_SEQUENCE_ENTRIES) {
            unsigned short maskAndValue = valveSequence[sequenceStep].maskAndValue;
            unsigned short dwell = valveSequence[sequenceStep].dwell;
            // Zero maskAndValue means that we should stay at the present step      
            if (maskAndValue != 0) {
                unsigned int value = maskAndValue & 0xFF;
                maskAndValue >>= 8;
                if (v->dwellCount == 0) {     // Update the solenoid valves
                    // TO DO: Read current valve settings from FPGA, apply mask and value        
                    sprintf(msg,"Valve mask: %2x, value: %2x",maskAndValue,value);
                    message_puts(msg);
                }
                if (v->dwellCount >= dwell) { // Move to the next step in the sequence
                    sequenceStep += 1;
                    v->dwellCount = 0;
                }
                else v->dwellCount++;
            }
        }
        else sequenceStep = -1;
    }
    return STATUS_OK;   
}

int valveCntrlInit(void)
{
    ValveCntrl *v = &valveCntrl;

    v->state_               = (VALVE_CNTRL_StateType *)registerAddr(VALVE_CNTRL_STATE_REGISTER);
    v->setpoint_            = (float*)registerAddr(VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER);
    v->inlet_               = (float*)registerAddr(VALVE_CNTRL_INLET_VALVE_REGISTER);
    v->outlet_              = (float*)registerAddr(VALVE_CNTRL_OUTLET_VALVE_REGISTER);
    v->dpdtMax_             = (float*)registerAddr(VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER);
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
    v->threshState_         = (VALVE_CNTRL_THRESHOLD_StateType *)registerAddr(VALVE_CNTRL_THRESHOLD_STATE_REGISTER);
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
    sequenceStep = -1;
    v->deltaT = 0.2;
    v->lastLoss = 0;
    v->dwellCount = 0;
    return STATUS_OK;
}
