#include <std.h>
#include <csl.h>
#include <csl_i2c.h>
#include <csl_cache.h>
#include <csl_irq.h>
#include <csl_hpi.h>
#include <log.h>
#include <sem.h>
#include <prd.h>
#include "checkDspcfg.h"
#include "configDsp.h"

#include "dspAutogen.h"
#include "interface.h"

#define SHAREDMEM_BASE    (SHAREDMEM_ADDRESS)
#define REG_BASE          (SHAREDMEM_BASE+4*REG_OFFSET)
#define SENSOR_BASE       (SHAREDMEM_BASE+4*SENSOR_OFFSET)
#define MESSAGE_BASE      (SHAREDMEM_BASE+4*MESSAGE_OFFSET)
#define GROUP_BASE        (SHAREDMEM_BASE+4*GROUP_OFFSET)
#define OPERATION_BASE    (SHAREDMEM_BASE+4*OPERATION_OFFSET)
#define OPERAND_BASE      (SHAREDMEM_BASE+4*OPERAND_OFFSET)
#define ENVIRONMENT_BASE  (SHAREDMEM_BASE+4*ENVIRONMENT_OFFSET)
#define HOST_BASE         (SHAREDMEM_BASE+4*HOST_OFFSET)

extern far LOG_Obj trace;
static int prd_count = 0;
static int hpi_count = 0;

// DSP writes to a register

int writeRegister(unsigned int regNum,int data)
{
    if (regNum >= REG_REGION_SIZE) return ERROR_UNKNOWN_REGISTER;
    else *(int*)(REG_BASE+4*regNum) = data;
    return STATUS_OK;
}

void schedulerPrdFunc(void)
{
    SEM_post(&SEM_scheduler);
}

void scheduler(void)
{
		while (1) {
        writeRegister(11,prd_count);
        prd_count++;
		    SEM_pend(&SEM_scheduler,SYS_FOREVER);
    }
}

void hwiHpiInterrupt(unsigned int funcArg, unsigned int eventId)
{
    // Responds to the DSPINT interrupt
    unsigned int gie;
    gie = IRQ_globalDisable();
    writeRegister(12,hpi_count);
    hpi_count += 1;
    // Clear interrupt source
    HPI_setDspint(1);
    IRQ_clear(IRQ_EVT_DSPINT);
    // Restore interrupts
    IRQ_globalRestore(gie);
}

main(int argc, char *argv[])
{
    // Set up DSP configuration
    configDsp();
    // Clear DSPINT bit in HPIC
    HPI_setDspint(1);
    IRQ_resetAll();
    // Enable the interrupt
    IRQ_enable(IRQ_EVT_DSPINT);
    return 0;
}
