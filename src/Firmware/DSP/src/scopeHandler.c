/*
 * FILE:
 *   scopeHandler.c
 *
 * DESCRIPTION:
 *   Task which controls access to the ringdown buffers when the analyzer
 *  is in oscilloscope mode
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   16-Feb-2011  sze  Initial version.
 *
 *  Copyright (c) 2011 Picarro, Inc. All rights reserved
 */
#include <std.h>
#include <lck.h>
#include <sem.h>

#include "interface.h"
#include "dspAutogen.h"
#include "dspData.h"
#include "dspMaincfg.h"
#include "fpga.h"
#include "rdHandlers.h"
#include "registers.h"
#include "scopeHandler.h"
#include "spectrumCntrl.h"
#include <math.h>

int fillScopeTrace = 1;

void getScopeTrace()
{
    LCK_pend(&LCK_scopeBuffer,SYS_FOREVER);
    fillScopeTrace = 0;
    LCK_post(&LCK_scopeBuffer);
}

void releaseScopeTrace()
{
    LCK_pend(&LCK_scopeBuffer,SYS_FOREVER);
    fillScopeTrace = 1;
    LCK_post(&LCK_scopeBuffer);
}

// This is the task function associated with TSK_scopeHandler
void scopeHandler(void)
{
   int i, bufferNum;
   
   while (1) {
        SEM_pend(&SEM_wfmAvailable,SYS_FOREVER);
        if (!get_queue(&rdBufferQueue,&bufferNum)) {
            message_puts(LOG_LEVEL_STANDARD,"rdBuffer queue empty in scopeHandler");
        }
        LCK_pend(&LCK_scopeBuffer,SYS_FOREVER);
        if (bufferNum != MISSING_RINGDOWN) {
            RingdownBufferType *ringdownBuffer;
            // Copy trace to memory
            ringdownBuffer = &ringdownBuffers[bufferNum];
            if (fillScopeTrace) {
                for (i=0;i<4096;i++) oscilloscopeTrace->data[i] = ringdownBuffer->ringdownWaveform[i] & 0xFFFF;
            }
            // Relinquish the buffer
            if (bufferNum == 0)
                SEM_postBinary(&SEM_rdBuffer0Available);
            else if (bufferNum == 1)
                SEM_postBinary(&SEM_rdBuffer1Available);
        }
        LCK_post(&LCK_scopeBuffer);
    }
}
