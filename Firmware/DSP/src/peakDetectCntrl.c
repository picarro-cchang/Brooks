/*
 * FILE:
 *   peakDetectCntrl.c
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
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   11-Nov-2011  sze  Initial version.
 *   27-Jul-2012  sze  Introduced cancelling state and ability to examine remaining time in triggered state
 *
 *  Copyright (c) 2011 Picarro, Inc. All rights reserved
 */
#include "interface.h"
#include "registers.h"
#include "peakDetectCntrl.h"
#include "dspAutogen.h"
 
#include <math.h>
#include <stdio.h>

#define state               (*(p->state_))
#define processedLoss       (*(p->processedLoss_))
#define backgroundSamples   (*(p->backgroundSamples_))
#define background          (*(p->background_))
#define upperThreshold      (*(p->upperThreshold_))
#define lowerThreshold1     (*(p->lowerThreshold1_))
#define lowerThreshold2     (*(p->lowerThreshold2_))
#define postPeakSamples     (*(p->postPeakSamples_))
#define activeSize          (*(p->activeSize_))
#define triggerCondition    (*(p->triggerCondition_))
#define triggerDelay        (*(p->triggerDelay_))
#define resetDelay          (*(p->resetDelay_))
#define cancellingDelay     (*(p->cancellingDelay_))
#define triggeredSamplesLeft (*(p->triggeredSamplesLeft_))
#define idleValveMaskAndValue           (*(p->idleValveMaskAndValue_))
#define armedValveMaskAndValue          (*(p->armedValveMaskAndValue_))
#define triggerPendingValveMaskAndValue (*(p->triggerPendingValveMaskAndValue_))
#define triggeredValveMaskAndValue      (*(p->triggeredValveMaskAndValue_))
#define inactiveValveMaskAndValue       (*(p->inactiveValveMaskAndValue_))
#define cancellingValveMaskAndValue     (*(p->cancellingValveMaskAndValue_))
#define solenoidValves      (*(p->solenoidValves_))

PeakDetectCntrl peakDetectCntrl;

int peakDetectCntrlInit(unsigned int processedLossRegisterIndex)
{
    int i;
    PeakDetectCntrl *p = &peakDetectCntrl;
    
    p->state_ = (PEAK_DETECT_CNTRL_StateType *)registerAddr(PEAK_DETECT_CNTRL_STATE_REGISTER);
    p->processedLoss_ = (float *)registerAddr(processedLossRegisterIndex);
    p->backgroundSamples_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_BACKGROUND_SAMPLES_REGISTER);
    p->background_ = (float *)registerAddr(PEAK_DETECT_CNTRL_BACKGROUND_REGISTER);
    p->upperThreshold_ = (float *)registerAddr(PEAK_DETECT_CNTRL_UPPER_THRESHOLD_REGISTER);
    p->lowerThreshold1_ = (float *)registerAddr(PEAK_DETECT_CNTRL_LOWER_THRESHOLD_1_REGISTER);
    p->lowerThreshold2_ = (float *)registerAddr(PEAK_DETECT_CNTRL_LOWER_THRESHOLD_2_REGISTER);
    p->postPeakSamples_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_POST_PEAK_SAMPLES_REGISTER);
    p->activeSize_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_ACTIVE_SIZE_REGISTER);
    p->triggerCondition_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRIGGER_CONDITION_REGISTER);
    p->triggerDelay_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRIGGER_DELAY_REGISTER);
    p->resetDelay_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_RESET_DELAY_REGISTER);
    p->cancellingDelay_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_CANCELLING_SAMPLES_REGISTER);
    p->triggeredSamplesLeft_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_REMAINING_TRIGGERED_SAMPLES_REGISTER);
    p->idleValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_IDLE_VALVE_MASK_AND_VALUE_REGISTER);
    p->armedValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_ARMED_VALVE_MASK_AND_VALUE_REGISTER);
    p->triggerPendingValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRIGGER_PENDING_VALVE_MASK_AND_VALUE_REGISTER);
    p->triggeredValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRIGGERED_VALVE_MASK_AND_VALUE_REGISTER);
    p->inactiveValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_INACTIVE_VALVE_MASK_AND_VALUE_REGISTER);
    p->cancellingValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_CANCELLING_VALVE_MASK_AND_VALUE_REGISTER);
    p->solenoidValves_ = (unsigned int *)registerAddr(VALVE_CNTRL_SOLENOID_VALVES_REGISTER);
    p->cancellingWait = 0;
    p->historyTail = 0;
    p->activeLength = 0;
    p->triggerWait = 0;
    p->lastState = state = PEAK_DETECT_CNTRL_IdleState;
    for (i=0; i<PEAK_DETECT_MAX_HISTORY_LENGTH; i++) p->historyBuffer[i] = 0.0;
    return STATUS_OK;
}

static unsigned int modifyValves(unsigned int current, unsigned int maskAndValue)
// Apply the maskAndValue to the current setting of a set of valves and return the
//  new setting
{
    unsigned int mask  = (maskAndValue >> 8) & 0xFF;
    unsigned int value = maskAndValue & 0xFF;
    return (current & ~mask) | value;
}

static unsigned int processHistoryBuffer(PeakDetectCntrl *p, unsigned int tail, unsigned int length)
{
    unsigned int bitPos, cond0, cond1, cond2, cond3, i, peakPos;
    int postPeak;
    float peakValue, minValue1, minValue2;
    
    int start;
    // Find background
    start = tail - backgroundSamples;
    if (start < 0) start += PEAK_DETECT_MAX_HISTORY_LENGTH;
    
    if (backgroundSamples > 0) background = p->historyBuffer[start];
    for (i=start; i!=tail; i=(i+1)%PEAK_DETECT_MAX_HISTORY_LENGTH) {
        if (p->historyBuffer[i] <= background) background = p->historyBuffer[i];
    }
    // Now deal with samples in the active region
    start = tail - length;
    if (start < 0) start += PEAK_DETECT_MAX_HISTORY_LENGTH;
    // Find peak within active region
    peakValue = p->historyBuffer[start];
    peakPos = start;
    for (i=start; i!=tail; i=(i+1)%PEAK_DETECT_MAX_HISTORY_LENGTH) {
        if (p->historyBuffer[i] >= peakValue) {
            peakValue = p->historyBuffer[i];
            peakPos = i;
        }
    }
    cond0 = peakValue >= (background + upperThreshold);
    // Find minimum between start and peak
    minValue1 = p->historyBuffer[start];
    for (i=start; i!=peakPos; i=(i+1)%PEAK_DETECT_MAX_HISTORY_LENGTH) {
        if (p->historyBuffer[i] <= minValue1) minValue1 = p->historyBuffer[i];
    }
    cond1 = minValue1 <= (background + lowerThreshold1);
    // Find minimum between peak and tail
    minValue2 = p->historyBuffer[peakPos];
    for (i=peakPos; i!=tail; i=(i+1)%PEAK_DETECT_MAX_HISTORY_LENGTH) {
        if (p->historyBuffer[i] <= minValue2) minValue2 = p->historyBuffer[i];
    }
    cond2 = minValue2 <= (background + lowerThreshold2);
    // Find number of samples after peak
    postPeak = tail-peakPos-1;
    if (postPeak<0) postPeak += PEAK_DETECT_MAX_HISTORY_LENGTH;
    cond3 =(postPeak >= postPeakSamples);
    
    // Apply triggerCondition logical function to see if a peak has been found
    bitPos = 8*(cond3) + 4*(cond2) + 2*(cond1) + (cond0);
    return 0 != ((triggerCondition >> bitPos) & 1);
}

int peakDetectCntrlStep()
{
    PeakDetectCntrl *p = &peakDetectCntrl;
    if (activeSize > PEAK_DETECT_MAX_HISTORY_LENGTH) activeSize = PEAK_DETECT_MAX_HISTORY_LENGTH;
    
    // Save most recent processed loss to history buffer
    p->historyBuffer[p->historyTail++] = processedLoss;
    if (p->historyTail >= PEAK_DETECT_MAX_HISTORY_LENGTH) p->historyTail -= PEAK_DETECT_MAX_HISTORY_LENGTH;
    p->activeLength++;
    if (p->activeLength >= activeSize) p->activeLength = activeSize;
    
    // State machine transition code
    if (state == PEAK_DETECT_CNTRL_IdleState) {
        solenoidValves = modifyValves(solenoidValves,idleValveMaskAndValue);
    }
    else if (state == PEAK_DETECT_CNTRL_ArmedState) {
        // If we newly transition to armed state, reset effective length of active buffer
        if (p->lastState != state) p->activeLength = 1;
        solenoidValves = modifyValves(solenoidValves,armedValveMaskAndValue);
        if (processHistoryBuffer(p,p->historyTail,p->activeLength)) {
            // Peak detected! Trigger immediately or after specified delay
            if (triggerDelay == 0) {
                state = PEAK_DETECT_CNTRL_TriggeredState;
                triggeredSamplesLeft = resetDelay;
            }
            else {
                state = PEAK_DETECT_CNTRL_TriggerPendingState;
                p->triggerWait = 0;
            }
        }
    }
    else if (state == PEAK_DETECT_CNTRL_TriggerPendingState) {
        solenoidValves = modifyValves(solenoidValves,triggerPendingValveMaskAndValue);
        p->triggerWait++;
        if (p->triggerWait >= triggerDelay) {
            state = PEAK_DETECT_CNTRL_TriggeredState;
            triggeredSamplesLeft = resetDelay;
        }
    }
    else if (state == PEAK_DETECT_CNTRL_TriggeredState) {
        solenoidValves = modifyValves(solenoidValves,triggeredValveMaskAndValue);
        triggeredSamplesLeft = triggeredSamplesLeft - 1;
        if (triggeredSamplesLeft <= 0) {
            state = PEAK_DETECT_CNTRL_IdleState;
        }
    }
    else if (state == PEAK_DETECT_CNTRL_InactiveState) {
        solenoidValves = modifyValves(solenoidValves,inactiveValveMaskAndValue);
    }
    else if (state == PEAK_DETECT_CNTRL_CancellingState) {
        if (p->lastState != PEAK_DETECT_CNTRL_CancellingState) p->cancellingWait = 0;
        solenoidValves = modifyValves(solenoidValves,cancellingValveMaskAndValue);
        p->cancellingWait++;
        if (p->cancellingWait > cancellingDelay) {
            p->cancellingWait = 0;
            state = PEAK_DETECT_CNTRL_IdleState;
        }        
    }
    // Save state
    p->lastState = state;
    return STATUS_OK;
}
