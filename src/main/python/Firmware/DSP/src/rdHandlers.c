/*
 * FILE:
 *   rdHandlers.c
 *
 * DESCRIPTION:
 *   Ringdown interrupt handlers
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   10-Jul-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */

#include <std.h>
#include <string.h>
#include <csl.h>
#include <hwi.h>
#include <csl_irq.h>
#include <csl_edma.h>
#include <sem.h>
#include "dspMaincfg.h"

#include "dspData.h"
#include "fpga.h"
#include "interface.h"
#include "rdFitting.h"
#include "rdHandlers.h"
#include "registers.h"
#include "scopeHandler.h"
#include "spectrumCntrl.h"
#include "tunerCntrl.h"

/* The following computes a median filter by brute force. It is used to make the dither waveform centering robust against
    outliers */

#define BUFFSIZE 10
#define SWAP(a,b) { int temp=(a);(a)=(b);(b)=temp; }
#define SORT(a,b) { if ((a)>(b)) SWAP((a),(b)); }

static int buffer[BUFFSIZE];  // Keeps up to 10 past samples
static int buffPointer = 0; // Location in buffer for next datum
static int pointsInBuff = 0; // Number of points currently in buffer

void reset_median(void)
{
    buffPointer = 0;
    pointsInBuff = 0;
}

void insert_point(int x)
{
    buffer[buffPointer] = x;
    buffPointer++;
    if (buffPointer >= BUFFSIZE) buffPointer = 0;
    pointsInBuff++;
    if (pointsInBuff > BUFFSIZE) pointsInBuff = BUFFSIZE;
}

int get_median(int maxPoints)
{
    static int p[9];
    int pointer = buffPointer;
    if (maxPoints > 9) maxPoints = 9;
    if (maxPoints < 1) maxPoints = 1;
    if (0 == (maxPoints & 1)) maxPoints++;
    if (pointsInBuff < 1) return 0;    
    pointer--; if (pointer<0) pointer += BUFFSIZE; p[0] = buffer[pointer];
    if (pointsInBuff < 3 || maxPoints == 1) return p[0];
    pointer--; if (pointer<0) pointer += BUFFSIZE; p[1] = buffer[pointer];
    pointer--; if (pointer<0) pointer += BUFFSIZE; p[2] = buffer[pointer];
    if (pointsInBuff < 5 || maxPoints == 3) {
        SORT(p[0],p[1]) ; SORT(p[1],p[2]) ; SORT(p[0],p[1]) ;
        return p[1];
    }
    pointer--; if (pointer<0) pointer += BUFFSIZE; p[3] = buffer[pointer];
    pointer--; if (pointer<0) pointer += BUFFSIZE; p[4] = buffer[pointer];
    if (pointsInBuff < 7 || maxPoints == 5) {
        SORT(p[0],p[1]); SORT(p[3],p[4]); SORT(p[0],p[3]);
        SORT(p[1],p[4]); SORT(p[1],p[2]); SORT(p[2],p[3]);
        SORT(p[1],p[2]); 
        return(p[2]) ;
    }
    pointer--; if (pointer<0) pointer += BUFFSIZE; p[5] = buffer[pointer];
    pointer--; if (pointer<0) pointer += BUFFSIZE; p[6] = buffer[pointer];
    if (pointsInBuff < 9 || maxPoints == 7) {
        SORT(p[0], p[5]) ; SORT(p[0], p[3]) ; SORT(p[1], p[6]) ;
        SORT(p[2], p[4]) ; SORT(p[0], p[1]) ; SORT(p[3], p[5]) ;
        SORT(p[2], p[6]) ; SORT(p[2], p[3]) ; SORT(p[3], p[6]) ;
        SORT(p[4], p[5]) ; SORT(p[1], p[4]) ; SORT(p[1], p[3]) ;
        SORT(p[3], p[4]) ; return (p[3]) ;
    }
    pointer--; if (pointer<0) pointer += BUFFSIZE; p[7] = buffer[pointer];
    pointer--; if (pointer<0) pointer += BUFFSIZE; p[8] = buffer[pointer];
    SORT(p[1], p[2]) ; SORT(p[4], p[5]) ; SORT(p[7], p[8]) ;
    SORT(p[0], p[1]) ; SORT(p[3], p[4]) ; SORT(p[6], p[7]) ;
    SORT(p[1], p[2]) ; SORT(p[4], p[5]) ; SORT(p[7], p[8]) ;
    SORT(p[0], p[3]) ; SORT(p[5], p[8]) ; SORT(p[4], p[7]) ;
    SORT(p[3], p[6]) ; SORT(p[1], p[4]) ; SORT(p[2], p[5]) ;
    SORT(p[4], p[7]) ; SORT(p[4], p[2]) ; SORT(p[6], p[4]) ;
    SORT(p[4], p[2]) ; return(p[4]) ;
}

/* Implement a queue of integers */

void init_queue(QueueInt *q,int *array,int size)
// Initialize the queue structure
{
    q->queueArray = array;
    q->head = 0;
    q->tail = 0;
    q->count = 0;
    q->size = size;
}

int put_queue(QueueInt *q,int datum)
// Place datum at tail of queue. Returns 1 on success, 0 on failure.
{
    int key=HWI_disable();
    if (q->count == q->size)
    {
        HWI_restore(key);
        return 0;
    }
    q->queueArray[q->tail++] = datum;
    if (q->tail >= q->size) q->tail -= q->size;
    q->count++;
    HWI_restore(key);
    return 1;
}

int get_queue(QueueInt *q,int *datumRef)
// Get *datumRef from head of queue. Returns 1 on success, 0 on failure.
{
    int key=HWI_disable();
    if (q->count == 0)
    {
        HWI_restore(key);
        return 0;
    }
    *datumRef = q->queueArray[q->head++];
    if (q->head >= q->size) q->head -= q->size;
    q->count--;
    HWI_restore(key);
    return 1;
}

// Queues for posting filled bank numbers from ACQ_DONE interrupts
//  and for posting ringdown buffer numbers that need fitting

QueueInt bankQueue;
QueueInt rdBufferQueue;
int bankQueueArray[4];
int rdBufferQueueArray[4];

// Initialize EDMA

#define BANK0_OPTIONS   ((EDMA_OPT_FS_YES << _EDMA_OPT_FS_SHIFT)   | (EDMA_OPT_LINK_NO << _EDMA_OPT_LINK_SHIFT) |\
                         (EDMA_CHA_TCC10 << _EDMA_OPT_TCC_SHIFT)   | (EDMA_OPT_TCINT_YES << _EDMA_OPT_TCINT_SHIFT ) |\
                         (EDMA_OPT_DUM_INC << _EDMA_OPT_DUM_SHIFT) | (EDMA_OPT_2DD_NO << _EDMA_OPT_2DD_SHIFT) |\
                         (EDMA_OPT_SUM_INC << _EDMA_OPT_SUM_SHIFT) | (EDMA_OPT_2DS_NO << _EDMA_OPT_2DS_SHIFT) |\
                         (EDMA_OPT_ESIZE_32BIT << _EDMA_OPT_ESIZE_SHIFT) | (EDMA_OPT_PRI_HIGH << _EDMA_OPT_PRI_SHIFT))

#define BANK1_OPTIONS   ((EDMA_OPT_FS_YES << _EDMA_OPT_FS_SHIFT)   | (EDMA_OPT_LINK_NO << _EDMA_OPT_LINK_SHIFT) |\
                         (EDMA_CHA_TCC11 << _EDMA_OPT_TCC_SHIFT)   | (EDMA_OPT_TCINT_YES << _EDMA_OPT_TCINT_SHIFT ) |\
                         (EDMA_OPT_DUM_INC << _EDMA_OPT_DUM_SHIFT) | (EDMA_OPT_2DD_NO << _EDMA_OPT_2DD_SHIFT) |\
                         (EDMA_OPT_SUM_INC << _EDMA_OPT_SUM_SHIFT) | (EDMA_OPT_2DS_NO << _EDMA_OPT_2DS_SHIFT) |\
                         (EDMA_OPT_ESIZE_32BIT << _EDMA_OPT_ESIZE_SHIFT) | (EDMA_OPT_PRI_HIGH << _EDMA_OPT_PRI_SHIFT))


void edmaDoneInterrupt(int tccNum)
{
    int bank;
    unsigned int gie;
    int *counter = (int*)(REG_BASE+4*RD_QDMA_DONE_COUNT_REGISTER);
    
    gie = IRQ_globalDisable();
    (*counter)++;

    // Reset bit 1 of DIAG_1 after QDMA and set bit 2
    changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 1, 2, 2);

    bank = (tccNum == EDMA_CHA_TCC10) ? 0 : 1;

    // Inform the ringdown fitter that a particular ringdown buffer (tied to the FPGA bank)
    //  has data for fitting by putting the buffer number on the rdBufferQueue

    if (!put_queue(&rdBufferQueue,bank))
    {
        message_puts(LOG_LEVEL_STANDARD,"rdBuffer queue full in edmaDoneInterrupt");
        spectCntrlError();
    }
    else   // put succeeded, post the good news to SEM_rdFitting or SEM_wfmAvailable depending on
           // whether we are in scope mode
    {
        if (readFPGA(FPGA_RDMAN + RDMAN_OPTIONS) & (1<<RDMAN_OPTIONS_SCOPE_MODE_B)) SEM_post(&SEM_wfmAvailable);
        else SEM_post(&SEM_rdFitting);
    }

    // Indicate bank in FPGA is no longer in use
    if (!bank)
    {
        changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_BANK0_CLEAR_B,
                       RDMAN_CONTROL_BANK0_CLEAR_W,1);
    }
    else
    {
        changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_BANK1_CLEAR_B,
                       RDMAN_CONTROL_BANK1_CLEAR_W,1);
    }

    EDMA_intClear(tccNum);
    // Restore interrupts
    IRQ_globalRestore(gie);
}

void edmaInit(void)
{
    EDMA_resetAll();
    EDMA_intHook(EDMA_CHA_TCC10, edmaDoneInterrupt);
    EDMA_intHook(EDMA_CHA_TCC11, edmaDoneInterrupt);
    EDMA_intClear(EDMA_CHA_TCC10);
    EDMA_intClear(EDMA_CHA_TCC11);
    EDMA_intEnable(EDMA_CHA_TCC10);
    EDMA_intEnable(EDMA_CHA_TCC11);

    init_queue(&bankQueue,bankQueueArray,4);
    init_queue(&rdBufferQueue,rdBufferQueueArray,4);
}

void ringdownInterrupt(unsigned int funcArg, unsigned int eventId)
{
    // Responds to the EXT4 interrupt, indicating that a ringdown
    //  (or a timeout) has occured
    unsigned int gie, status;
    int allowDither, abortedRingdown, timedOut;
    int *counter = (int*)(REG_BASE+4*RD_IRQ_COUNT_REGISTER);
    TUNER_ModeType mode;

    gie = IRQ_globalDisable();
    (*counter)++;
    // Set bit 0 of DIAG_1 at start of ringdownInterrupt
    changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 0, 1, 1);

	do {
	    // Acknowledge the interrupt
    	changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_RD_IRQ_ACK_B,
        	           RDMAN_CONTROL_RD_IRQ_ACK_W,1);
	    // Clear interrupt source
    	IRQ_clear(IRQ_EVT_EXTINT4);
	} while (readFPGA(FPGA_RDMAN+RDMAN_STATUS) & (1<<RDMAN_STATUS_RD_IRQ_B));
    // Reset bit 0 of DIAG_1 at start of ringdownInterrupt
    changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 0, 1, 0);

    // Check if this was a timeout or abort, which should cause a switch to ramp mode
    status = readFPGA(FPGA_RDMAN+RDMAN_STATUS);

    allowDither = (0 != (readFPGA(FPGA_RDMAN+RDMAN_OPTIONS) & (1<<RDMAN_OPTIONS_DITHER_ENABLE_B)));
    timedOut = (0 != (status & (1<<RDMAN_STATUS_TIMEOUT_B)));
    abortedRingdown = (0 != (status & (1<<RDMAN_STATUS_ABORTED_B)));
    if (abortedRingdown)
    {
        message_puts(LOG_LEVEL_STANDARD,"Ringdown aborted");
        spectCntrlError();
        IRQ_globalRestore(gie);
        return;
    }

    mode = (TUNER_ModeType)readBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL, RDMAN_CONTROL_RAMP_DITHER_B, RDMAN_CONTROL_RAMP_DITHER_W);
    if (!timedOut && allowDither) {
        insert_point(readFPGA(FPGA_RDMAN+RDMAN_TUNER_AT_RINGDOWN));
        setupDither(get_median(*(unsigned int*)registerAddr(TUNER_DITHER_MEDIAN_COUNT_REGISTER)));
    }
    else {
        reset_median();
        switchToRampMode();
    }
    if (!timedOut) advanceDwellCounter();
    else
    {
        if (mode == TUNER_RampMode)
        {
            unsigned int schemeCount = getSpectCntrlSchemeCount();
            if (activeLaserTempLocked()) {
                advanceSchemeRow();
                // Enqueue a special code on the ringdown buffer queue to indicate that we have
                //  advanced to the next scheme row
                modifyParamsOnTimeout(schemeCount);
            }
            if (!put_queue(&rdBufferQueue,MISSING_RINGDOWN))
            {
                message_puts(LOG_LEVEL_STANDARD,"rdBuffer queue full in ringdownInterrupt");
                spectCntrlError();
                IRQ_globalRestore(gie);
                return;
            }
            else   // post the bad news to SEM_rdFitting.
            {
                // The rdFitting task will initiate the next ringdown after noting the timeout.
                SEM_post(&SEM_rdFitting);
            }
        }
        else   // We have a timeout in dither mode. Do not advance scheme row but allow next ringdown to happen
        {
            if (SPECT_CNTRL_RunningState == *(int*)registerAddr(SPECT_CNTRL_STATE_REGISTER)) SEM_postBinary(&SEM_startRdCycle);
        }
    }

    // Change the temperature and apply PZT offset for the selected laser
    setupLaserTemperatureAndPztOffset(1);

    // Restore interrupts
    IRQ_globalRestore(gie);
}

void acqDoneInterrupt(unsigned int funcArg, unsigned int eventId)
{
    // Responds to the EXT5 interrupt, indicating that ringdown
    //  acquisition is complete
    unsigned int gie;
    int bank;
    int *counter = (int*)(REG_BASE+4*ACQ_DONE_COUNT_REGISTER);

    gie = IRQ_globalDisable();
    (*counter)++;

    // Set bit 1 of DIAG_1 at start of acqDoneInterrupt
    changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 1, 1, 1);

    // Acknowledge the interrupt
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_ACQ_DONE_ACK_B,
                   RDMAN_CONTROL_ACQ_DONE_ACK_W,1);
    // Clear interrupt source
    IRQ_clear(IRQ_EVT_EXTINT5);

    bank = readBitsFPGA(FPGA_RDMAN+RDMAN_STATUS, RDMAN_STATUS_BANK_B,
                        RDMAN_STATUS_BANK_W);

    // The OTHER bank is the one which has just been filled. Place it on
    //  the bankQueue so that it can be transferred by QDMA

    if (!put_queue(&bankQueue,!bank))
    {
        message_puts(LOG_LEVEL_STANDARD,"bankQueue is full in acqDoneInterrupt.");
        spectCntrlError();
        IRQ_globalRestore(gie);
        return;
    }
    else   // Inform TSK_rdDataMoving that there are data to be moved
    {
        SEM_post(&SEM_rdDataMoving);
    }
    // Restore interrupts
    IRQ_globalRestore(gie);

    // Indicate next ringdown can start
    if (SPECT_CNTRL_RunningState == *(int*)registerAddr(SPECT_CNTRL_STATE_REGISTER)) SEM_postBinary(&SEM_startRdCycle);
    changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 1, 1, 0);
}

void rdDataMoving(void)
{
    int bank;
    int *counter = (int*)(REG_BASE+4*RD_DATA_MOVING_COUNT_REGISTER);
    while (1)
    {
        // Use SEM_rdDataMoving to indicate when FPGA data are available
        SEM_pend(&SEM_rdDataMoving,SYS_FOREVER);
        (*counter)++;
        if (!get_queue(&bankQueue,&bank))
        {
            message_puts(LOG_LEVEL_STANDARD,"bankQueue empty in rdDataMoving");
            spectCntrlError();
            continue;
        }
        if (bank == 0)
        {
            // Transfer bank 0
            SEM_pendBinary(&SEM_rdBuffer0Available,SYS_FOREVER);
            EDMA_qdmaConfigArgs(BANK0_OPTIONS,(Uint32)rdDataAndMetaAddr(0),sizeof(RingdownBufferType)/sizeof(int),(Uint32)&ringdownBuffers[0],0);
        }
        else if (bank == 1)
        {
            // Transfer bank 1
            SEM_pendBinary(&SEM_rdBuffer1Available,SYS_FOREVER);
            EDMA_qdmaConfigArgs(BANK1_OPTIONS,(Uint32)rdDataAndMetaAddr(1),sizeof(RingdownBufferType)/sizeof(int),(Uint32)&ringdownBuffers[1],0);
        }
    }
}
