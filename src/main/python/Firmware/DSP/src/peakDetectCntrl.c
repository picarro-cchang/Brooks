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
 *  PEAK_DETECT_CNTRL_TriggeredState: triggerDelay samples have arrived since peak was found. During this time
 *   we can either have the reverse flow through the analyzer to replay the pulse, or we can shut off the valves
 *   to allow the baseline to be measured. After triggeredDuration samples, either return to the idleState or enter
 *   the transitioningState (if the transitioningDuration is nonzero)
 *  PEAK_DETECT_CNTRL_TransitioningState: After triggeredDuration samples, enter this state . In this state,
 *   the flow is reestablished, and the processed loss is monitored once the transitioningHoldoff has elapsed.
 *   Once the processed loss starts falling, transition to the HoldingState. If no maximum in the processed loss
 *   is found within transitioningDuration, return to the idle state.
 *  PEAK_DETECT_CNTRL_HoldingState: Shut off the valves to trap the sample for holdingDuration, so that the
 *   concentrations can be measured. After this time, return to the idle state.
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
 * The minimum between peakIndex and the current sample is compared against background + fallingThreshold: Condition 2
 *   is true it is below the threshold.
 * The falling threshold is the larger of lowerThreshold2 and thresholdFactor * (peak value - background)
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
 * After triggeredDuration samples in the Triggered state, the controller returns to the Idle state, or enters the
 *  Transitioning state.
 *
 * While in the Transitioning state, transitioningHoldoff samples are allowed to elapse, before the processed loss
 *  is monitored. If the loss falls while it exceeds background+minLossForHolding and the value of the holdingDuration
 *  is nonzero, the system transitions to the Holding state.
 *
 * It remains in this state for up to the contents of the holdingDuration register, and then returns to the
 *  idle state.
 *
 * In each state, there is an associated valveMask. This is a sixteen bit integer, the top eight bits
 *  indicate which valves can be affected and the bottom eight bits indicate the value to which the 
 *  affected valves are to be set
 * Since there are only six solenoid valves, the high order 2 bits of the valve mask and value are used 
 *  for another purpose if these (flow mask) bits are 00, the flow rate is not changed. If they are 01,
 *  the proportional valve controller is instructed to save the values of the inlet and outlet valves and the
 *  controller state, and then to close both valves. If they are 10, the proportional valve controller restores
 *  a previously saved state, and  if the bits are 11, the corresponding value bits select which of four
 *  flow rate setpoints the flow controller is placed in when that state is entered.

 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   11-Nov-2011  sze  Initial version.
 *   27-Jul-2012  sze  Introduced cancelling state and ability to examine remaining time in triggered state
 *   13-Mar-2013  sze  Added flow control setpoint adjustment
 *   10-Feb-2016  sze  Added Transitioning and Holding states for ethane to methane ratio measurement
 *   12-Apr-2016  sze  Introduced fallingThreshold and minLossForHolding to scale the thresholds for entering the
 *                      triggered state and for entering the holdingState by the peak amplitude.
 *  Copyright (c) 2011 Picarro, Inc. All rights reserved
 */
#include "interface.h"
#include "registers.h"
#include "peakDetectCntrl.h"
#include "dspAutogen.h"
 
#include <math.h>
#include <stdio.h>

#define state                (*(p->state_))
#define valveState           (*(p->valve_state_))
#define processedLoss        (*(p->processedLoss_))
#define backgroundSamples    (*(p->backgroundSamples_))
#define background           (*(p->background_))
#define upperThreshold       (*(p->upperThreshold_))
#define lowerThreshold1      (*(p->lowerThreshold1_))
#define lowerThreshold2      (*(p->lowerThreshold2_))
#define thresholdFactor      (*(p->thresholdFactor_))
#define postPeakSamples      (*(p->postPeakSamples_))
#define activeSize           (*(p->activeSize_))
#define triggerCondition     (*(p->triggerCondition_))
#define triggerDelay         (*(p->triggerDelay_))
#define triggeredDuration    (*(p->triggeredDuration_))
#define transitioningDuration (*(p->transitioningDuration_))
#define transitioningHoldoff  (*(p->transitioningHoldoff_))
#define holdingDuration      (*(p->holdingDuration_))
#define holdingMaxLoss       (*(p->holdingMaxLoss_))
#define cancellingDelay      (*(p->cancellingDelay_))
#define primingDuration      (*(p->primingDuration_))
#define purgingDuration      (*(p->purgingDuration_))
#define samplesLeft          (*(p->samplesLeft_))
#define idleValveMaskAndValue           (*(p->idleValveMaskAndValue_))
#define armedValveMaskAndValue          (*(p->armedValveMaskAndValue_))
#define triggerPendingValveMaskAndValue (*(p->triggerPendingValveMaskAndValue_))
#define triggeredValveMaskAndValue      (*(p->triggeredValveMaskAndValue_))
#define transitioningValveMaskAndValue      (*(p->transitioningValveMaskAndValue_))
#define holdingValveMaskAndValue        (*(p->holdingValveMaskAndValue_))
#define inactiveValveMaskAndValue       (*(p->inactiveValveMaskAndValue_))
#define cancellingValveMaskAndValue     (*(p->cancellingValveMaskAndValue_))
#define primingValveMaskAndValue        (*(p->primingValveMaskAndValue_))
#define purgingValveMaskAndValue        (*(p->purgingValveMaskAndValue_))
#define injectionPendingValveMaskAndValue   (*(p->injectionPendingValveMaskAndValue_))
#define flow0Setpoint                   (*(p->flow0Setpoint_))
#define flow1Setpoint                   (*(p->flow1Setpoint_))
#define flow2Setpoint                   (*(p->flow2Setpoint_))
#define flow3Setpoint                   (*(p->flow3Setpoint_))
#define flowCntrlSetpoint               (*(p->flowCntrlSetpoint_))
#define solenoidValves      (*(p->solenoidValves_))

PeakDetectCntrl peakDetectCntrl;

int peakDetectCntrlInit(unsigned int processedLossRegisterIndex)
{
    int i;
    PeakDetectCntrl *p = &peakDetectCntrl;
    
    p->state_ = (PEAK_DETECT_CNTRL_StateType *)registerAddr(PEAK_DETECT_CNTRL_STATE_REGISTER);
    p->valve_state_ = (VALVE_CNTRL_StateType *)registerAddr(VALVE_CNTRL_STATE_REGISTER);
    p->processedLoss_ = (float *)registerAddr(processedLossRegisterIndex);
    p->backgroundSamples_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_BACKGROUND_SAMPLES_REGISTER);
    p->background_ = (float *)registerAddr(PEAK_DETECT_CNTRL_BACKGROUND_REGISTER);
    p->upperThreshold_ = (float *)registerAddr(PEAK_DETECT_CNTRL_UPPER_THRESHOLD_REGISTER);
    p->lowerThreshold1_ = (float *)registerAddr(PEAK_DETECT_CNTRL_LOWER_THRESHOLD_1_REGISTER);
    p->lowerThreshold2_ = (float *)registerAddr(PEAK_DETECT_CNTRL_LOWER_THRESHOLD_2_REGISTER);
    p->thresholdFactor_ = (float *)registerAddr(PEAK_DETECT_CNTRL_THRESHOLD_FACTOR_REGISTER);
    p->postPeakSamples_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_POST_PEAK_SAMPLES_REGISTER);
    p->activeSize_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_ACTIVE_SIZE_REGISTER);
    p->triggerCondition_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRIGGER_CONDITION_REGISTER);
    p->triggerDelay_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRIGGER_DELAY_REGISTER);
    p->triggeredDuration_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRIGGERED_DURATION_REGISTER);
    p->transitioningDuration_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRANSITIONING_DURATION_REGISTER);
    p->transitioningHoldoff_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRANSITIONING_HOLDOFF_REGISTER);
    p->holdingDuration_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_HOLDING_DURATION_REGISTER);
    p->holdingMaxLoss_ = (float *)registerAddr(PEAK_DETECT_CNTRL_HOLDING_MAX_LOSS_REGISTER);
    p->cancellingDelay_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_CANCELLING_SAMPLES_REGISTER);
    p->primingDuration_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_PRIMING_DURATION_REGISTER);
    p->purgingDuration_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_PURGING_DURATION_REGISTER);
    p->samplesLeft_ = (int *)registerAddr(PEAK_DETECT_CNTRL_REMAINING_TRIGGERED_SAMPLES_REGISTER);
    p->idleValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_IDLE_VALVE_MASK_AND_VALUE_REGISTER);
    p->armedValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_ARMED_VALVE_MASK_AND_VALUE_REGISTER);
    p->triggerPendingValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRIGGER_PENDING_VALVE_MASK_AND_VALUE_REGISTER);
    p->triggeredValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRIGGERED_VALVE_MASK_AND_VALUE_REGISTER);
    p->transitioningValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_TRANSITIONING_VALVE_MASK_AND_VALUE_REGISTER);
    p->holdingValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_HOLDING_VALVE_MASK_AND_VALUE_REGISTER);
    p->inactiveValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_INACTIVE_VALVE_MASK_AND_VALUE_REGISTER);
    p->cancellingValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_CANCELLING_VALVE_MASK_AND_VALUE_REGISTER);
    p->primingValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_PRIMING_VALVE_MASK_AND_VALUE_REGISTER);
    p->purgingValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_PURGING_VALVE_MASK_AND_VALUE_REGISTER);
    p->injectionPendingValveMaskAndValue_ = (unsigned int *)registerAddr(PEAK_DETECT_CNTRL_INJECTION_PENDING_VALVE_MASK_AND_VALUE_REGISTER);
    p->flow0Setpoint_ = (float *)registerAddr(FLOW_0_SETPOINT_REGISTER);
    p->flow1Setpoint_ = (float *)registerAddr(FLOW_1_SETPOINT_REGISTER);
    p->flow2Setpoint_ = (float *)registerAddr(FLOW_2_SETPOINT_REGISTER);
    p->flow3Setpoint_ = (float *)registerAddr(FLOW_3_SETPOINT_REGISTER);
    p->flowCntrlSetpoint_ = (float *)registerAddr(FLOW_CNTRL_SETPOINT_REGISTER);
    p->solenoidValves_ = (unsigned int *)registerAddr(VALVE_CNTRL_SOLENOID_VALVES_REGISTER);
    p->historyTail = 0;
    p->activeLength = 0;
    p->lastState = state = PEAK_DETECT_CNTRL_IdleState;
    for (i=0; i<PEAK_DETECT_MAX_HISTORY_LENGTH; i++) p->historyBuffer[i] = 0.0;
    p->minLossForHolding = lowerThreshold2;
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

static void setFlow(unsigned int maskAndValue) {
    PeakDetectCntrl *p = &peakDetectCntrl;
    unsigned int mask  = (maskAndValue >> 14) & 0x03;
    unsigned int value = (maskAndValue >> 6) & 0x03;
    switch (mask) {
    case 1:
        valveState = VALVE_CNTRL_SaveAndCloseValvesState;
        break;
    case 2:
        if (valveState == VALVE_CNTRL_SaveAndCloseValvesState)
            valveState = VALVE_CNTRL_RestoreValvesState;
        break;
    case 3:
        if (valveState == VALVE_CNTRL_SaveAndCloseValvesState || valveState == VALVE_CNTRL_RestoreValvesState) {
            valveState = VALVE_CNTRL_DisabledState;
        }
        switch (value) {
        case 0:
            flowCntrlSetpoint = flow0Setpoint;
            break;
        case 1:
            flowCntrlSetpoint = flow1Setpoint;
            break;
        case 2:
            flowCntrlSetpoint = flow2Setpoint;
            break;
        case 3:
            flowCntrlSetpoint = flow3Setpoint;
            break;
        }
        break;
    }
}

static int checkDecreasingLoss(PeakDetectCntrl *p, unsigned int tail)
{
    int ptr = tail - 1;
    float v0, v1, v2, v3;
    if (ptr < 0) ptr += PEAK_DETECT_MAX_HISTORY_LENGTH;
    v0 = p->historyBuffer[ptr];
    ptr--;
    if (ptr < 0) ptr += PEAK_DETECT_MAX_HISTORY_LENGTH;
    v1 = p->historyBuffer[ptr];
    ptr--;
    if (ptr < 0) ptr += PEAK_DETECT_MAX_HISTORY_LENGTH;
    v2 = p->historyBuffer[ptr];
    ptr--;
    if (ptr < 0) ptr += PEAK_DETECT_MAX_HISTORY_LENGTH;
    v3 = p->historyBuffer[ptr];
    return (v0 <= v1) && (v1 <= v2) && (v2 <= v3) && (v0 < v3);
}


static int checkIncreasingLoss(PeakDetectCntrl *p, unsigned int tail)
{
    int ptr = tail - 1;
    float v0, v1, v2, v3;
    if (ptr < 0) ptr += PEAK_DETECT_MAX_HISTORY_LENGTH;
    v0 = p->historyBuffer[ptr];
    ptr--;
    if (ptr < 0) ptr += PEAK_DETECT_MAX_HISTORY_LENGTH;
    v1 = p->historyBuffer[ptr];
    ptr--;
    if (ptr < 0) ptr += PEAK_DETECT_MAX_HISTORY_LENGTH;
    v2 = p->historyBuffer[ptr];
    ptr--;
    if (ptr < 0) ptr += PEAK_DETECT_MAX_HISTORY_LENGTH;
    v3 = p->historyBuffer[ptr];
    return (v0 >= v1) && (v1 >= v2) && (v2 >= v3) && (v0 > v3);
}

static unsigned int processHistoryBuffer(PeakDetectCntrl *p, int tail, unsigned int length)
{
    unsigned int bitPos, cond0, cond1, cond2, cond3, i, peakPos;
    int postPeak;
    float peakValue, minValue1, minValue2, fallingThreshold;
    
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
    fallingThreshold = thresholdFactor * (peakValue-background);
    if (fallingThreshold < lowerThreshold2) fallingThreshold = lowerThreshold2;
    cond2 = minValue2 <= (background + fallingThreshold);
    // Find number of samples after peak
    postPeak = tail-peakPos-1;
    if (postPeak<0) postPeak += PEAK_DETECT_MAX_HISTORY_LENGTH;
    cond3 =(postPeak >= postPeakSamples);
    
    // We calculate minLossForHolding to be the maximum of fallingThreshold above the background and
    //  the loss at the time when we leave the triggered state (see below in peakDetectCntrlStep
    //  state machine)
    p->minLossForHolding = fallingThreshold + background;

    // Apply triggerCondition logical function to see if a peak has been found
    bitPos = 8*(cond3) + 4*(cond2) + 2*(cond1) + (cond0);
    return 0 != ((triggerCondition >> bitPos) & 1);
}

int peakDetectCntrlStep()
{
    PeakDetectCntrl *p = &peakDetectCntrl;
    PEAK_DETECT_CNTRL_StateType nextState = state;
    if (activeSize > PEAK_DETECT_MAX_HISTORY_LENGTH) activeSize = PEAK_DETECT_MAX_HISTORY_LENGTH;
    
    // Save most recent processed loss to history buffer
    p->historyBuffer[p->historyTail++] = processedLoss;
    if (p->historyTail >= PEAK_DETECT_MAX_HISTORY_LENGTH) p->historyTail -= PEAK_DETECT_MAX_HISTORY_LENGTH;
    p->activeLength++;
    if (p->activeLength >= activeSize) p->activeLength = activeSize;
    
    // State machine transition code
    if (state == PEAK_DETECT_CNTRL_IdleState) {
        setFlow(idleValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,idleValveMaskAndValue&0x3F3F);
    }
    else if (state == PEAK_DETECT_CNTRL_ArmedState) {
        // If we newly transition to armed state, reset effective length of active buffer
        if (p->lastState != state) p->activeLength = 1;
        setFlow(armedValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,armedValveMaskAndValue&0x3F3F);
        if (processHistoryBuffer(p,p->historyTail,p->activeLength)) {
            // Peak detected! Trigger immediately or after specified delay
            if (triggerDelay == 0) {
                nextState = PEAK_DETECT_CNTRL_TriggeredState;
            }
            else {
                nextState = PEAK_DETECT_CNTRL_TriggerPendingState;
            }
        p->stateCounter = 0;
        }
    }
    else if (state == PEAK_DETECT_CNTRL_TriggerPendingState) {
        setFlow(triggerPendingValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,triggerPendingValveMaskAndValue&0x3F3F);
        p->stateCounter++;
        if (p->stateCounter >= triggerDelay) {
            nextState = PEAK_DETECT_CNTRL_TriggeredState;
            p->stateCounter = 0;
        samplesLeft = triggeredDuration + transitioningDuration + holdingDuration;
        }
    }
    else if (state == PEAK_DETECT_CNTRL_TriggeredState) {
        setFlow(triggeredValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,triggeredValveMaskAndValue&0x3F3F);
        p->stateCounter++;
        samplesLeft--;
        if (p->stateCounter >= triggeredDuration) {
            // We calculate minLossForHolding to be the maximum of fallingThreshold above the background
            //  (set up in processHistoryBuffer) and the loss at the time when we leave the triggered state
            if (p->minLossForHolding < processedLoss) p->minLossForHolding = processedLoss;
            if (transitioningDuration > 0) {
                samplesLeft = transitioningDuration + holdingDuration;
                nextState = PEAK_DETECT_CNTRL_TransitioningState;
            }
            else {
                samplesLeft = 0;
                nextState = PEAK_DETECT_CNTRL_IdleState;
            }
            p->stateCounter = 0;
        }
    }
    else if (state == PEAK_DETECT_CNTRL_TransitioningState) {
        setFlow(transitioningValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,transitioningValveMaskAndValue&0x3F3F);
        p->stateCounter++;
        samplesLeft--;
        if (p->stateCounter >= transitioningDuration) {
            samplesLeft = 0;
            nextState = PEAK_DETECT_CNTRL_IdleState;
        }
        else if (p->stateCounter >= transitioningHoldoff) {
            if (holdingDuration > 0 &&
                ((processedLoss >= holdingMaxLoss) ||
                 (checkDecreasingLoss(p,p->historyTail) && (processedLoss > p->minLossForHolding)))
               ) {
                samplesLeft = holdingDuration;
                nextState = PEAK_DETECT_CNTRL_HoldingState;
                p->stateCounter = 0;
            }
        }

    }
    else if (state == PEAK_DETECT_CNTRL_HoldingState) {
        setFlow(holdingValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,holdingValveMaskAndValue&0x3F3F);
        p->stateCounter++;
        samplesLeft--;
    if (p->stateCounter >= holdingDuration) {
        samplesLeft = 0;
            nextState = PEAK_DETECT_CNTRL_IdleState;
        }
    }
    else if (state == PEAK_DETECT_CNTRL_InactiveState) {
        setFlow(inactiveValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,inactiveValveMaskAndValue&0x3F3F);
    }
    else if (state == PEAK_DETECT_CNTRL_CancellingState) {
        if (p->lastState != PEAK_DETECT_CNTRL_CancellingState) samplesLeft = cancellingDelay;
        setFlow(cancellingValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,cancellingValveMaskAndValue&0x3F3F);
        samplesLeft = samplesLeft - 1;
        if (samplesLeft <= 0) {
            nextState = PEAK_DETECT_CNTRL_IdleState;
        }        
    }
    else if (state == PEAK_DETECT_CNTRL_PrimingState) {
        if (p->lastState != PEAK_DETECT_CNTRL_PrimingState) samplesLeft = primingDuration;
        setFlow(primingValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,primingValveMaskAndValue&0x3F3F);
        samplesLeft = samplesLeft - 1;
        if (samplesLeft <= 0) {
            nextState = PEAK_DETECT_CNTRL_PurgingState;
        }        
    }
    else if (state == PEAK_DETECT_CNTRL_PurgingState) {
        if (p->lastState != PEAK_DETECT_CNTRL_PurgingState) samplesLeft = purgingDuration;
        setFlow(purgingValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,purgingValveMaskAndValue&0x3F3F);
        samplesLeft = samplesLeft - 1;
        if (samplesLeft <= 0) {
            nextState = PEAK_DETECT_CNTRL_InjectionPendingState;
        }        
    }
    else if (state == PEAK_DETECT_CNTRL_InjectionPendingState) {
        setFlow(injectionPendingValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,injectionPendingValveMaskAndValue&0x3F3F);
    }

    // Save state
    p->lastState = state;
    state = nextState;
    return STATUS_OK;
}
