/*
 * FILE:
 *   analogInterface.c
 *
 * DESCRIPTION:
 *   USB FX2 firmware to support analog interface.
 *
 *   There are eight output DAC channels whose data are taken from queues.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   09-Apr-2010  sze  Initial version. 
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */

#include "fx2.h"
#include "fx2regs.h"
#include "fx2sdly.h"
#include "intrins.h"
#include "../autogen/usbdefs.h"

#define QSIZE   (32)
#define NCHANNELS (8)

struct DataQueue {
    unsigned char head;
    unsigned char tail;
    unsigned char count;
    unsigned short int qdata[QSIZE];
} dataQueues[NCHANNELS];

unsigned short int samplePeriods[NCHANNELS];
unsigned short int nextSample[NCHANNELS];
unsigned short int ticks;
unsigned char underflowFlags = 0, overflowFlags = 0, serveDacs = 0;

void waitUntilEndpointEmpty()
{
}

void disableTickIrq()
{
}

void enableTickIrq()
{
}

void writeDac(unsigned char chan, unsigned short int value)
{
}

unsigned char getUnderflowStatus()
{
    return underflowFlags;
}

unsigned char getOverflowStatus()
{
    return overflowFlags;
}

void qinit(int qNum)
{
    struct DataQueue *q = &dataQueues[qNum];
    q->head = q->tail = q->count = 0;
}

unsigned char qput(unsigned char qNum,unsigned short int d)
// Places data d onto the queue, returns 1 on success, 0 if queue is full 
{
    struct DataQueue *q = &dataQueues[qNum];
    if (q->count == QSIZE) {
        overflowFlags |= (1<<qNum);
        return 0;
    }
    q->qdata[q->tail++] = d;
    if (q->tail == QSIZE) q->tail = 0;
    q->count++;
    return 1;
}

unsigned char qget(unsigned char qNum,unsigned short int *d)
// Get data *d from the queue, returns 1 on success, 0 if queue is empty 
{
    struct DataQueue *q = &dataQueues[qNum];
    if (q->count == 0) {
        underflowFlags |= (1<<qNum);
        return 0;
    }
    return 0;
    *d = q->qdata[q->head++];
    if (q->head == QSIZE) q->head = 0;
    q->count--;
    return 1;
}

void reset()
// Stop serving, empty all queues, reset underflow and overflow flags
{
    unsigned char i;
    serveDacs = 0;
    underflowFlags = 0;
    overflowFlags  = 0;
    for (i=0; i<NCHANNELS; i++) qinit(i);
}

void init()
{
    unsigned char i;
    serveDacs = 0;
    for (i=0; i<NCHANNELS; i++) {
        samplePeriods[i] = 0;
        nextSample[i] = 0;
    }
    reset();
}

void startServer()
// Start serving queues at the next tick
{
    unsigned char i;
    unsigned short int when;
    if (serveDacs) return;
    disableTickIrq();
    when = ticks + 1;
    for (i=0; i<NCHANNELS; i++) nextSample[i] = when;
    serveDacs = 1;
    enableTickIrq();
}

void setPeriod(unsigned char qNum, unsigned short int d)
{
    samplePeriods[qNum] = d;
}

void serve(unsigned short int now)
// Serve queues with non-zero periods
{
    unsigned char i;
    unsigned short int d;
    for (i=0; i<NCHANNELS; i++) {
        if (samplePeriods[i] != 0 && nextSample[i] == now) {
            if (qget(i,&d)) writeDac(i,d);
            nextSample[i] += samplePeriods[i];
        }
    }
}

void update(unsigned char channelMask, unsigned short int *cdata, unsigned short int nData)
{
    unsigned char channels[NCHANNELS];
    unsigned char j, bitsSet = 0;
    unsigned short int i;
    if (channelMask) {
        // Determine which channel queues are to be replenished
        for (j=0; j<NCHANNELS; j++) {
            if (channelMask & 1) {
                channels[bitsSet++] = j;
            }
            channelMask >>= 1;
        }
        // Deal the available data among the channels
        j = 0;
        for (i=0; i<nData; i++) {
            unsigned char chan = channels[j];
            // For zero period
            if (samplePeriods[chan]) qput(chan,*(cdata++));
            else writeDac(chan,*(cdata++));
            j++;
            if (j == bitsSet) j=0;
        }
    }
}

void getFreeSlots(unsigned char freeSlots[NCHANNELS])
// Get the number of free slots for each of the channel queues
{
    unsigned char i;
    waitUntilEndpointEmpty();
    for (i=0; i<NCHANNELS; i++) {
        freeSlots[i] = QSIZE - dataQueues[i].count;
    }
}

