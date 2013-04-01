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
 *
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

#include "interface.h"
#include "peakDetect.h"
 
#include <math.h>
#include <stdio.h>

#define state                (p->state)
#define processedLoss        (p->processedLoss)
#define backgroundSamples    (p->backgroundSamples)
#define background           (p->background)
#define upperThreshold       (p->upperThreshold)
#define lowerThreshold1      (p->lowerThreshold1)
#define lowerThreshold2      (p->lowerThreshold2)
#define postPeakSamples      (p->postPeakSamples)
#define activeSize           (p->activeSize)
#define triggerCondition     (p->triggerCondition)
#define triggerDelay         (p->triggerDelay)
#define resetDelay           (p->resetDelay)
#define cancellingDelay      (p->cancellingDelay)
#define primingDuration      (p->primingDuration)
#define purgingDuration      (p->purgingDuration)
#define samplesLeft          (p->samplesLeft)
#define idleValveMaskAndValue           (p->idleValveMaskAndValue)
#define armedValveMaskAndValue          (p->armedValveMaskAndValue)
#define triggerPendingValveMaskAndValue (p->triggerPendingValveMaskAndValue)
#define triggeredValveMaskAndValue      (p->triggeredValveMaskAndValue)
#define inactiveValveMaskAndValue       (p->inactiveValveMaskAndValue)
#define cancellingValveMaskAndValue     (p->cancellingValveMaskAndValue)
#define primingValveMaskAndValue        (p->primingValveMaskAndValue)
#define purgingValveMaskAndValue        (p->purgingValveMaskAndValue)
#define injectionPendingValveMaskAndValue   (p->injectionPendingValveMaskAndValue)
#define flow0Setpoint                   (p->flow0Setpoint)
#define flow1Setpoint                   (p->flow1Setpoint)
#define flow2Setpoint                   (p->flow2Setpoint)
#define flow3Setpoint                   (p->flow3Setpoint)
#define flowCntrlSetpoint               (p->flowCntrlSetpoint)
#define solenoidValves                  (p->solenoidValves)

PeakDetectCntrl peakDetectCntrl;

int peakDetectCntrlInit()
{
    int i;
    PeakDetectCntrl *p = &peakDetectCntrl;
    
    state = PEAK_DETECT_CNTRL_IdleState;
    processedLoss = 500;
    backgroundSamples = 200;
    background = 1.0;
    upperThreshold = 0.3;
    lowerThreshold1 = 0.15;
    lowerThreshold2 = 0.15;
    postPeakSamples = 100;
    activeSize = 300;
    triggerCondition = 0xA800;
    triggerDelay = 0;
    resetDelay = 2700;
    cancellingDelay = 25;
    primingDuration = 100;
    purgingDuration = 100;
    samplesLeft = 0;
    idleValveMaskAndValue = 0x0000;
    armedValveMaskAndValue = 0x1300;
    triggerPendingValveMaskAndValue = 0x1300;
    triggeredValveMaskAndValue = 0x1303;
    inactiveValveMaskAndValue = 0x1310;
    cancellingValveMaskAndValue = 0x1310;
    primingValveMaskAndValue = 0x1F14;
    purgingValveMaskAndValue = 0x1F10;
    injectionPendingValveMaskAndValue = 0x1310; 
    flow0Setpoint = 400;
    flow1Setpoint = 400;
    flow2Setpoint = 400;
    flow3Setpoint = 400;
    flowCntrlSetpoint = 100;
    solenoidValves = 0;
    p->historyTail = 0;
    p->activeLength = 0;
    p->triggerWait = 0;
    p->lastState = state = PEAK_DETECT_CNTRL_IdleState;
    for (i=0; i<PEAK_DETECT_MAX_HISTORY_LENGTH; i++) p->historyBuffer[i] = 0.0;
    return STATUS_OK;
}

unsigned int modifyValves(unsigned int current, unsigned int maskAndValue)
// Apply the maskAndValue to the current setting of a set of valves and return the
//  new setting
{
    unsigned int mask  = (maskAndValue >> 8) & 0xFF;
    unsigned int value = maskAndValue & 0xFF;
    return (current & ~mask) | value;
}

void setFlow(unsigned int maskAndValue) {
    PeakDetectCntrl *p = &peakDetectCntrl;
    unsigned int mask  = (maskAndValue >> 14) & 0x03;
    unsigned int value = (maskAndValue >> 6) & 0x03;
    if (mask) {
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
    }
}

unsigned int processHistoryBuffer(PeakDetectCntrl *p, unsigned int tail, unsigned int length)
{
    unsigned bitPos, i, peakPos;
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
    p->cond0 = peakValue >= (background + upperThreshold);
    // Find minimum between start and peak
    minValue1 = p->historyBuffer[start];
    for (i=start; i!=peakPos; i=(i+1)%PEAK_DETECT_MAX_HISTORY_LENGTH) {
        if (p->historyBuffer[i] <= minValue1) minValue1 = p->historyBuffer[i];
    }
    p->cond1 = minValue1 <= (background + lowerThreshold1);
    // Find minimum between peak and tail
    minValue2 = p->historyBuffer[peakPos];
    for (i=peakPos; i!=tail; i=(i+1)%PEAK_DETECT_MAX_HISTORY_LENGTH) {
        if (p->historyBuffer[i] <= minValue2) minValue2 = p->historyBuffer[i];
    }
    p->cond2 = minValue2 <= (background + lowerThreshold2);
    // Find number of samples after peak
    postPeak = tail-peakPos-1;
    if (postPeak<0) postPeak += PEAK_DETECT_MAX_HISTORY_LENGTH;
    p->cond3 =(postPeak >= postPeakSamples);
    
    // Apply triggerCondition logical function to see if a peak has been found
    bitPos = 8*(p->cond3) + 4*(p->cond2) + 2*(p->cond1) + (p->cond0);
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
                samplesLeft = resetDelay;
            }
            else {
                nextState = PEAK_DETECT_CNTRL_TriggerPendingState;
                p->triggerWait = 0;
            }
        }
    }
    else if (state == PEAK_DETECT_CNTRL_TriggerPendingState) {
        setFlow(triggerPendingValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,triggerPendingValveMaskAndValue&0x3F3F);
        p->triggerWait++;
        if (p->triggerWait >= triggerDelay) {
            nextState = PEAK_DETECT_CNTRL_TriggeredState;
            samplesLeft = resetDelay;
        }
    }
    else if (state == PEAK_DETECT_CNTRL_TriggeredState) {
        setFlow(triggeredValveMaskAndValue&0xC0C0);
        solenoidValves = modifyValves(solenoidValves,triggeredValveMaskAndValue&0x3F3F);
        samplesLeft = samplesLeft - 1;
        if (samplesLeft <= 0) {
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
