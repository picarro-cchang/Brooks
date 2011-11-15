/*
 * FILE:
 *   peakDetectCntrl.h
 *
 * DESCRIPTION:
 *   Peak detection controller routines for determining whether an eligible peak
 * in the "processedLoss" has been found. The routine runs periodically (typically every 0.2s)
 * and maintains a history buffer containing the previous processed losses. The controller
 * can be in one of three states:
 *
 *  PEAK_DETECT_CNTRL_IdleState: Do not process contents of history buffer
 *  PEAK_DETECT_CNTRL_ArmedState: Process contents of history buffer
 *  PEAK_DETECT_CNTRL_TriggerPendingState: Peak has been found in history buffer
 *  PEAK_DETECT_CNTRL_TriggeredState: triggerDelay samples have arrived since peak was found
 *
 * Conceptually, the history buffer is cleared when entering the ArmedState. Up to "historySize"
 *  points are kept in the buffer, and on the introduction of each new processedLoss
 *  1) The peak value in the history buffer is found, its location is peakIndex
 *  2) The minimum value in the buffer from the start to peakIndex is found
 *  3) The minimum value in the buffer from the peakIndex to the end of the buffer 
 *      (i.e., the current sample) is found
 *
 * The peak value is compared against upperThreshold: Condition 0 is true if it exceeds the threshold.
 * The minimum between start and peakIndex is compared against lowerThreshold1: Condition 1 is true if
 *   it is below the threshold
 * The minimum between peakIndex and the current sample is compared against lowerThreshold2: Condition 2 
 *   is true it is below the threshold
 * 
 * The value of "triggerCondition" specifies the logical function which is to be applied to the results
 *  of the three conditions to determine whether a transition to the triggered state should occur.
 * From the conditions, the "conditionBit" = 4*(Condition 2) + 2*(Condition 1) + (Condition 0) is found.
 * When triggerCondition is written out as a binary number, if the conditionBit is 1, the controller
 *  will enter the TriggerPending state
 *
 * After triggerDeleay samples in the TriggerPending state, the controller enters the Triggered state
 * After resetDelay samples in the Triggered state, the controller returns to the Idle state
 *
 * In each state, there is an associated valveMask. This is a sixteen bit integer, the top eight bits
 *  indicate which valves can be affected and the bottom eight bits indicate the value to which the 
 *  affected valves are to be set
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   11-Nov-2011  sze  Initial version.
 *
 *  Copyright (c) 2011 Picarro, Inc. All rights reserved
 */
#ifndef _PEAK_DETECT_CNTRL_H_
#define _PEAK_DETECT_CNTRL_H_

typedef struct PEAK_DETECT_CNTRL
{
    PEAK_DETECT_CNTRL_StateType *state_; // Valve controller state
    float *processedLoss_;              // Processed loss
    float *upperThreshold_;             // Upper threshold
    float *lowerThreshold1_;            // Lower threshold 1
    float *lowerThreshold2_;            // Lower threshold 2
    unsigned int *historySize_;         // Size of history to use for peak detection
    unsigned int *triggerCondition_;    // Specifies logical function for triggering
    unsigned int *triggerDelay_;        // Number of samples to delay when trigger conditions are met
    unsigned int *resetDelay_;          // Number of samples after entering triggered state before resetting to idle state
    unsigned int *idleValveMaskAndValue_;           // Valve mask and value for idle state
    unsigned int *armedValveMaskAndValue_;          // Valve mask and value for armed state
    unsigned int *triggerPendingValveMaskAndValue_; // Valve mask and value for trigger pending state
    unsigned int *triggeredValveMaskAndValue_;      // Valve mask and value for triggered state
    unsigned int *solenoidValves_;      // Solenoid valve mask
    unsigned int historyTail;
    unsigned int historyLength;
    unsigned int triggerWait;
    unsigned int resetWait;
    PEAK_DETECT_CNTRL_StateType lastState;
    float historyBuffer[PEAK_DETECT_MAX_HISTORY_LENGTH];
} PeakDetectCntrl;

int peakDetectCntrlInit(unsigned int processedLossRegisterIndex);
int peakDetectCntrlStep(void);

#endif /* _PEAK_DETECT_CNTRL_H_ */
