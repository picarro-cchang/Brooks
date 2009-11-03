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
    float *cavityPressure_;             // Cavity pressure
    float *setpoint_;                   // Cavity pressure setpoint
    float *userInlet_;                  // User-entered inlet valve value
    float *userOutlet_;                 // User-entered outlet valve value
    float *inlet_;                      // Inlet valve value
    float *outlet_;                     // Outlet valve value
    float *dpdtMax_;                    // Maximum rate of change of pressure
    float *dpdtAbort_;                  // Maximum rate of change of pressure above which valves are closed
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

    unsigned int *solenoidValves_;      // States of solenoid valves

    VALVE_CNTRL_THRESHOLD_StateType *threshState_;   // Threshold state
    float *latestLoss_;                  // Latest loss (ppm/cm)
    float *lossThreshold_;              // Loss threshold for triggering
    float *rateThreshold_;              // Rate threshold for triggering
    float *inletTriggeredValue_;        // Value for inlet valve when triggered
    float *outletTriggeredValue_;       // Value for outlet valve when triggered
    unsigned int *solenoidMask_;        // Mask to apply to solenoid valves when triggered
    unsigned int *solenoidState_;       // Solenoid valve states when triggered
    int *sequenceStep_;                 // Sequence step

    float deltaT;                       // Time between runs of valve controller
    float lastPressure;                 // Last cavity pressure
    float lastLossPpb;                  // Previous loss
    unsigned int dwellCount;            // Count samples to time valve sequence
    int nonDecreasingCount;             // Counts samples during which pressure is nondecreasing
} ValveCntrl;

int valveCntrlInit(void);
int valveCntrlStep(void);
void valveSequencerStep(void);
void proportionalValveStep(void);
void thresholdTriggerStep(void);
int modify_valve_pump_tec(unsigned int mask, unsigned int code);
int write_valve_pump_tec(unsigned int code);
int read_cavity_pressure_adc(void);
int read_ambient_pressure_adc(void);

#endif /* _VALVE_CNTRL_H_ */
