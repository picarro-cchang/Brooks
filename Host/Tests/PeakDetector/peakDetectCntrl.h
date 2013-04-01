/*
 * FILE:
 *   peakDetectCntrl.h
 *
 * DESCRIPTION:
 *   Peak detection controller routines for determining whether an eligible peak
 * in the "processedLoss" has been found. The routine runs periodically (typically every 0.2s)
 * and maintains a history buffer containing the previous processed losses. The controller
 * can be in one of these states:
 *
 *  PEAK_DETECT_CNTRL_IdleState: Do not process contents of history buffer
 *  PEAK_DETECT_CNTRL_ArmedState: Process contents of history buffer
 *  PEAK_DETECT_CNTRL_TriggerPendingState: Peak has been found in history buffer
 *  PEAK_DETECT_CNTRL_TriggeredState: triggerDelay samples have arrived since peak was found
 *  PEAK_DETECT_CNTRL_InactiveState: Do not process contents of history buffer, used to indicate
 *   non-survey mode for methane leak detection applications
 *  PEAK_DETECT_CNTRL_CancellingState: Used to return to IdleState if triggered state is cancelled.
 *   Number of samples in this state is determined by PEAK_DETECT_CNTRL_CANCELLING_SAMPLES_REGISTER
 *  PEAK_DETECT_CNTRL_PrimingState: Used to fill the reference gas line after the valve to the tank
 *   is opened. Remains in this state for number of samples in PEAK_DETECT_CNTRL_PRIMING_DURATION_REGISTER
 *   and then proceeds to the purging state
 *  PEAK_DETECT_CNTRL_PurgingState: Used to purge the line into the analyzer before actual injection of 
 *   the reference gas. Remains in this state for number of samples in 
 *   PEAK_DETECT_CNTRL_PURGING_DURATION_REGISTER and then proceeds to the injection pending state
 *  PEAK_DETECT_CNTRL_InjectionPendingState: Signals that the analyzer is ready for injection of the 
 *   reference gas sample. The peak detector should be placed in the Armed state and the reference gas injected.
 * 
 * The minimum of the previous "backgroundSamples" points within the history buffer are used 
 *  determine the value of "background". If "backgroundSamples" is zero, the value of 
 *  "background" is not updated.
 * The most recent points in the history buffer are called the active points. The number of
 *  active points is set to zero when entering the ArmedState. As points are collected, the
 *  number of active points is incremented, but its value is capped at "activeSize"
 * When new points arrive:
 *  1) The peak value in the active region is found, its location is peakIndex
 *  2) The minimum value in the active region from the start to peakIndex is found
 *  3) The minimum value in the active region from the peakIndex to the end of the buffer 
 *      (i.e., the current sample) is found
 *
 * The peak value is compared against background + upperThreshold: Condition 0 is true if it exceeds the threshold.
 * The minimum between start and peakIndex is compared against background + lowerThreshold1: Condition 1 is true if
 *   it is below the threshold
 * The minimum between peakIndex and the current sample is compared against background + lowerThreshold2: Condition 2 
 *   is true it is below the threshold
 * The position of the peak is compared against "postPeakSamples": Condition 3 is true if there are at least this
 *  number of samples in the active region since the peak
 * 
 * The value of "triggerCondition" specifies the logical function which is to be applied to the results
 *  of the three conditions to determine whether a transition to the triggered state should occur.
 * From the conditions, the "conditionBit" = 8*(Condition 3) + 4*(Condition 2) + 2*(Condition 1) + (Condition 0) is found.
 * When triggerCondition is written out as a binary number, if the conditionBit is 1, the controller
 *  will enter the TriggerPending state
 *
 * After triggerDeleay samples in the TriggerPending state, the controller enters the Triggered state
 * After resetDelay samples in the Triggered state, the controller returns to the Idle state
 *
 * In each state, there is an associated valveMask. This is a sixteen bit integer, the top eight bits
 *  indicate which valves can be affected and the bottom eight bits indicate the value to which the 
 *  affected valves are to be set
 * Since there are only six solenoid valves, the high order 2 bits of the valve mask and value are used 
 *  for another purpose. If either of the two mask bits is one, the two value bits select which of four 
 *  flow rate setpoints the flow controller is placed in when that state is entered. If both mask bits are
 *  zero, the flow rate is not changed.
 
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   11-Nov-2011  sze  Initial version.
 *   27-Jul-2012  sze  Introduced cancelling state and ability to examine remaining time in triggered state
 *   13-Mar-2013  sze  Added flow control setpoint adjustment
 *
 *  Copyright (c) 2011 Picarro, Inc. All rights reserved
 */
#ifndef _PEAK_DETECT_CNTRL_H_
#define _PEAK_DETECT_CNTRL_H_

typedef struct PEAK_DETECT_CNTRL
{
    PEAK_DETECT_CNTRL_StateType *state_; // Valve controller state
    float *processedLoss_;              // Processed loss
    unsigned int *backgroundSamples_;   // Number of samples for background calculation
    float *background_;                 // Background value
    float *upperThreshold_;             // Upper threshold
    float *lowerThreshold1_;            // Lower threshold 1
    float *lowerThreshold2_;            // Lower threshold 2
    unsigned int *postPeakSamples_;     // Required number of points after peak
    unsigned int *activeSize_;          // Size of active region to use for peak detection
    unsigned int *triggerCondition_;    // Specifies logical function for triggering
    unsigned int *triggerDelay_;        // Number of samples to delay when trigger conditions are met
    unsigned int *resetDelay_;          // Number of samples after entering triggered state before resetting to idle state
    unsigned int *cancellingDelay_;     // Number of samples after to remain in cancelling state before resetting to idle state
    unsigned int *primingDuration_;     // Number of samples after to remain in priming state before entering purging state
    unsigned int *purgingDuration_;     // Number of samples after to remain in purging state before entering injection pending state
    unsigned int *samplesLeft_;         // Number of samples left for lengthy operations
    unsigned int *idleValveMaskAndValue_;           // Valve mask and value for idle state
    unsigned int *armedValveMaskAndValue_;          // Valve mask and value for armed state
    unsigned int *triggerPendingValveMaskAndValue_; // Valve mask and value for trigger pending state
    unsigned int *triggeredValveMaskAndValue_;      // Valve mask and value for triggered state
    unsigned int *inactiveValveMaskAndValue_;       // Valve mask and value for triggered state
    unsigned int *cancellingValveMaskAndValue_;     // Valve mask and value for cancelling state
    unsigned int *primingValveMaskAndValue_;        // Valve mask and value for priming state
    unsigned int *purgingValveMaskAndValue_;        // Valve mask and value for purging state
    unsigned int *injectionPendingValveMaskAndValue_;  // Valve mask and value for injection pending state
    unsigned int *solenoidValves_;      // Solenoid valve mask
    float *flow0Setpoint_;              // Flow setpoint in state 0
    float *flow1Setpoint_;              // Flow setpoint in state 1
    float *flow2Setpoint_;              // Flow setpoint in state 2
    float *flow3Setpoint_;              // Flow setpoint in state 3
    float *flowCntrlSetpoint_;          // Flow control setpoint register

    unsigned int historyTail;
    unsigned int activeLength;
    unsigned int triggerWait;
    PEAK_DETECT_CNTRL_StateType lastState;
    float historyBuffer[PEAK_DETECT_MAX_HISTORY_LENGTH];
} PeakDetectCntrl;

int peakDetectCntrlInit(unsigned int processedLossRegisterIndex);
int peakDetectCntrlStep(void);

#endif /* _PEAK_DETECT_CNTRL_H_ */
