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
#include <csl.h>
#include <csl_irq.h>
#include <csl_edma.h>

#include "dspData.h"
#include "fpga.h"
#include "interface.h"
#include "rdFitting.h"
#include "rdHandlers.h"
#include "registers.h"

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
    volatile int *meta;
    volatile int *param;
    float uncorrectedLoss, correctedLoss;
    DataType data;
    volatile RingdownEntryType *ringdownEntry;
    unsigned int gie;
    gie = IRQ_globalDisable();

    // Reset bit 9 of GPREG_1 after QDMA and set bit 10
    changeBitsFPGA(FPGA_KERNEL+KERNEL_GPREG_1, 9, 2, 2);

    bank = (tccNum == EDMA_CHA_TCC10) ? 0 : 1;
    
    rdFittingProcessRingdown(ringdownWaveform,&uncorrectedLoss,&correctedLoss,0);
    data.asFloat = uncorrectedLoss;
    writeRegister(RD_LATEST_LOSS_REGISTER,data);

    meta = rdMetaAddr(bank);
    param = rdParamAddr(bank);
    
    // Process metadata and params, and write results to ringdown queue
    ringdownEntry = get_ringdown_entry_addr();
    ringdownEntry->uncorrectedAbsorbance = uncorrectedLoss;
    ringdownEntry->correctedAbsorbance = correctedLoss;
    ringdownEntry->pztValue = param[PARAM_TUNER_AT_RINGDOWN_INDEX];
    ringdown_put();
    
    // Indicate bank is no longer in use
    if (!bank) changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_BANK0_CLEAR_B,
                                 RDMAN_CONTROL_BANK0_CLEAR_B,1);
    else changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_BANK1_CLEAR_B,
                            RDMAN_CONTROL_BANK1_CLEAR_B,1);
                            
    // Reset bit 10 of GPREG_1 after fitting
    changeBitsFPGA(FPGA_KERNEL+KERNEL_GPREG_1, 10, 1, 0);

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
    unsigned int gie;
    int *counter = (int*)(REG_BASE+4*RD_IRQ_COUNT_REGISTER);

    gie = IRQ_globalDisable();
    (*counter)++;
    // Set bit 8 of GPREG_1 at start of ringdownInterrupt
    changeBitsFPGA(FPGA_KERNEL+KERNEL_GPREG_1, 8, 1, 1);

    // Acknowledge the interrupt
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_RD_IRQ_ACK_B,
                   RDMAN_CONTROL_RD_IRQ_ACK_W,1);
    // Clear interrupt source
    IRQ_clear(IRQ_EVT_EXTINT4);
    // Reset bit 8 of GPREG_1 at start of ringdownInterrupt
    changeBitsFPGA(FPGA_KERNEL+KERNEL_GPREG_1, 8, 1, 0);
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

    // Set bit 9 of GPREG_1 at start of acqDoneInterrupt
    changeBitsFPGA(FPGA_KERNEL+KERNEL_GPREG_1, 9, 1, 1);

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
        EDMA_qdmaConfigArgs(BANK0_OPTIONS,(Uint32)rdDataAddr(0),4096,(Uint32)ringdownWaveform,0);
    }
    else {
        // Transfer bank 1
        EDMA_qdmaConfigArgs(BANK1_OPTIONS,(Uint32)rdDataAddr(0),4096,(Uint32)ringdownWaveform,0);
    }
    // Restore interrupts
    IRQ_globalRestore(gie);
}
