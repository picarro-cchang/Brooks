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
#include <csl_irq.h>
#include <csl_edma.h>

#include "dspData.h"
#include "fpga.h"
#include "interface.h"
#include "rdFitting.h"
#include "rdHandlers.h"
#include "registers.h"
#include "tunerCntrl.h"

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
    int i, bank;
    float uncorrectedLoss, correctedLoss;
    DataType data;
    volatile RingdownEntryType *ringdownEntry;
    RingdownMetadataType meta;
    int *metaPtr = (int*) &meta;

    unsigned int gie;
    unsigned int base;
    gie = IRQ_globalDisable();

    // Reset bit 1 of DIAG_1 after QDMA and set bit 2
    changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 1, 2, 2);

    bank = (tccNum == EDMA_CHA_TCC10) ? 0 : 1;
        
    rdFittingProcessRingdown(ringdownBuffer.ringdownWaveform,&uncorrectedLoss,&correctedLoss,0);
    data.asFloat = uncorrectedLoss;
    writeRegister(RDFITTER_LATEST_LOSS_REGISTER,data);
    // We need to find position of metadata just before ringdown. We have a modified circular
    //  buffer which wraps back to the midpoint, and the MSB indicates if this buffer has wrapped.
    base = ringdownBuffer.addressAtRingdown & ~0x7;
    if (base == 32768 + 2048) base = 4096;
    else base = base & 0xFFF;
    base = base - 8;
    // The metadata are in the MS 16 bits of the ringdown waveform
    for (i=0;i<8;i++) metaPtr[i] = ringdownBuffer.ringdownWaveform[base+i] >> 16;

    // Get metadata and params, and write results to ringdown queue    
    ringdownEntry = get_ringdown_entry_addr();
    ringdownEntry->uncorrectedAbsorbance = uncorrectedLoss;
    ringdownEntry->correctedAbsorbance = correctedLoss;
    ringdownEntry->tunerValue = ringdownBuffer.tunerAtRingdown;
    ringdownEntry->ratio1 = meta.ratio1;
    ringdownEntry->ratio2 = meta.ratio2;
    ringdownEntry->pztValue = meta.pztValue;
    ringdownEntry->lockerOffset = meta.lockerOffset;
    ringdownEntry->fineLaserCurrent = meta.fineLaserCurrent;
    ringdownEntry->lockerError = meta.lockerError;
    ringdownEntry->ringdownThreshold = ringdownBuffer.ringdownThreshold;
    ringdownEntry->subschemeId = ringdownBuffer.subschemeId;
    ringdownEntry->schemeRowAndIndex = ringdownBuffer.schemeRowAndIndex;
    ringdownEntry->coarseLaserCurrent = ringdownBuffer.coarseLaserCurrent;
    ringdownEntry->laserTemperature = ringdownBuffer.laserTemperature;
    ringdownEntry->etalonTemperature = ringdownBuffer.etalonTemperature;
    ringdownEntry->cavityPressure = ringdownBuffer.cavityPressure;
    ringdownEntry->ambientPressure = ringdownBuffer.ambientPressure;
    ringdown_put();

    // Indicate bank is no longer in use
    if (!bank) {
        // memset(rdMetaAddr(0),0,16384);
        changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_BANK0_CLEAR_B,
                                 RDMAN_CONTROL_BANK0_CLEAR_B,1);
    }
    else {
        // memset(rdMetaAddr(1),0,16384);
        changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_BANK1_CLEAR_B,
                            RDMAN_CONTROL_BANK1_CLEAR_B,1);
    }
    
    // Reset bit 2 of DIAG_1 after fitting
    changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 2, 1, 0);

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
}

void ringdownInterrupt(unsigned int funcArg, unsigned int eventId)
{
    // Responds to the EXT4 interrupt, indicating that a ringdown
    //  (or a timeout) has occured
    unsigned int gie, status;
    int allowDither, badRingdown;
    int *counter = (int*)(REG_BASE+4*RD_IRQ_COUNT_REGISTER);

    gie = IRQ_globalDisable();
    (*counter)++;
    // Set bit 0 of DIAG_1 at start of ringdownInterrupt
    changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 0, 1, 1);

    // Acknowledge the interrupt
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_RD_IRQ_ACK_B,
                   RDMAN_CONTROL_RD_IRQ_ACK_W,1);
    // Clear interrupt source
    IRQ_clear(IRQ_EVT_EXTINT4);
    // Reset bit 0 of DIAG_1 at start of ringdownInterrupt
    changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 0, 1, 0);
    
    // Check if this was a timeout or abort, which should cause a switch to ramp mode
    status = readFPGA(FPGA_RDMAN+RDMAN_STATUS);
    
    allowDither = (0 != (readFPGA(FPGA_RDMAN+RDMAN_OPTIONS) & (1<<RDMAN_OPTIONS_DITHER_ENABLE_B)));
    badRingdown = (0 != (status & (1<<RDMAN_STATUS_TIMEOUT_B | 1<<RDMAN_STATUS_ABORTED_B)));
    if (!allowDither || badRingdown) {
        switchToRampMode();    
    }
    else {
        setupDither(readFPGA(FPGA_RDMAN+RDMAN_TUNER_AT_RINGDOWN));
    }
    
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
    // Do fitting
    bank = readBitsFPGA(FPGA_RDMAN+RDMAN_STATUS, RDMAN_STATUS_BANK_B,
                        RDMAN_STATUS_BANK_W);
    // Transfer the OTHER bank via QDMA
    if (bank) {
        // Transfer bank 0
        EDMA_qdmaConfigArgs(BANK0_OPTIONS,(Uint32)rdDataAndMetaAddr(0),sizeof(RingdownBufferType)/sizeof(int),(Uint32)&ringdownBuffer,0);
    }
    else {
        // Transfer bank 1
        EDMA_qdmaConfigArgs(BANK1_OPTIONS,(Uint32)rdDataAndMetaAddr(1),sizeof(RingdownBufferType)/sizeof(int),(Uint32)&ringdownBuffer,0);
    }
    // Restore interrupts
    IRQ_globalRestore(gie);
}
