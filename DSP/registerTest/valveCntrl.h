/*
    * FILE:
    *   tempCntrl.h
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
#ifndef _VALVE_CNTRL_H_
#define _VALVE_CNTRL_H_

typedef struct VALVE_CNTRL
{
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

    VALVE_CNTRL_THRESHOLD_StateType *threshState_;   // Threshold state
    float *lossThreshold_;              // Loss threshold for triggering
    float *rateThreshold_;              // Rate threshold for triggering
    float *inletTriggeredValue_;        // Value for inlet valve when triggered
    float *outletTriggeredValue_;       // Value for outlet valve when triggered
    unsigned int *solenoidMask_;        // Mask to apply to solenoid valves when triggered
    unsigned int *solenoidState_;       // Solenoid valve states when triggered
    int *sequenceStep_;                 // Sequence step
    
    float deltaT;                       // Time between runs of valve controller
    float lastLoss;                     // Previous loss
    unsigned int dwellCount;            // Count samples to time valve sequence    
} ValveCntrl;

int valveCntrlInit(void);
int valveCntrlStep(void);

#endif /* _VALVE_CNTRL_H_ */
