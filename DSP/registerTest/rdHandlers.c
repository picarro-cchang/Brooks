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

    gie = IRQ_globalDisable();
    (*counter)++;

    // Acknowledge the interrupt
    changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_ACQ_DONE_ACK_B,
                   RDMAN_CONTROL_ACQ_DONE_ACK_W,1);
    // Clear interrupt source
    IRQ_clear(IRQ_EVT_EXTINT5);
    // Restore interrupts
    IRQ_globalRestore(gie);
}
