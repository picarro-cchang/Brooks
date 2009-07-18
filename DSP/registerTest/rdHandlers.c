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

#include "interface.h"
#include "rdFitting.h"
#include "registers.h"
#include "fpga.h"


void ringdownInterrupt(unsigned int funcArg, unsigned int eventId)
{
    // Responds to the EXT4 interrupt, indicating that a ringdown
    //  (or a timeout) has occured
    unsigned int gie;
    int *counter = (int*)(REG_BASE+4*RD_IRQ_COUNT_REGISTER);

    gie = IRQ_globalDisable();
    (*counter)++;

    // Acknowledge the interrupt
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_RD_IRQ_ACK_B,
                   RDMAN_CONTROL_RD_IRQ_ACK_W,1);
    // Clear interrupt source
    IRQ_clear(IRQ_EVT_EXTINT4);
    // Restore interrupts
    IRQ_globalRestore(gie);
}

void acqDoneInterrupt(unsigned int funcArg, unsigned int eventId)
{
    // Responds to the EXT5 interrupt, indicating that ringdown
    //  acquisition is complete
    unsigned int gie;
    int *counter = (int*)(REG_BASE+4*ACQ_DONE_COUNT_REGISTER);
    int bank;
    volatile int *buffer;
    volatile int *meta;
    volatile int *param;
    float uncorrectedLoss, correctedLoss;
    DataType data;
    volatile RingdownEntryType *ringdownEntry;

    gie = IRQ_globalDisable();
    (*counter)++;

    // Acknowledge the interrupt
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_ACQ_DONE_ACK_B,
                   RDMAN_CONTROL_ACQ_DONE_ACK_W,1);
    // Clear interrupt source
    IRQ_clear(IRQ_EVT_EXTINT5);
    // Do fitting
    bank = readBitsFPGA(FPGA_RDMAN+RDMAN_STATUS, RDMAN_STATUS_BANK_B,
                        RDMAN_STATUS_BANK_W);
    buffer = rdDataAddr(!bank);
    rdFittingProcessRingdown(buffer,&uncorrectedLoss,&correctedLoss,0);
    data.asFloat = uncorrectedLoss;
    writeRegister(RD_LATEST_LOSS_REGISTER,data);
    meta = rdMetaAddr(!bank);
    param = rdParamAddr(!bank);
    
    // Process metadata and params, and write results to ringdown queue
    ringdownEntry = get_ringdown_entry_addr();
    ringdownEntry->uncorrectedAbsorbance = uncorrectedLoss;
    ringdownEntry->correctedAbsorbance = correctedLoss;
    ringdownEntry->pztValue = param[PARAM_TUNER_AT_RINGDOWN_INDEX];
    ringdown_put();
    
    // Indicate bank is no longer in use
    if (bank) changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_BANK0_CLEAR_B,
                                 RDMAN_CONTROL_BANK0_CLEAR_B,1);
    else changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_BANK1_CLEAR_B,
                            RDMAN_CONTROL_BANK1_CLEAR_B,1);

    // Restore interrupts
    IRQ_globalRestore(gie);
}
    float uncorrectedAbsorbance;
    float correctedAbsorbance;
    uint16 status;
    uint16 pztValue;
