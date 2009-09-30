#include <stdio.h>
#include "interface.h"
#include "registerTest.h"
#include "registerTestSim.h"
#include "registers.h"

unsigned char  SHAREDMEM_BASE[4*SHAREDMEM_SIZE];
unsigned char  USER_REG[4];

#pragma argsused
void IRQ_resetAll(void)
{
}

#pragma argsused
void IRQ_enable(unsigned int eventId)
{
}

#pragma argsused
unsigned int IRQ_globalDisable(void)
{
    return 0;
}

#pragma argsused
void IRQ_clear(unsigned int eventId)
{
}

#pragma argsused
void IRQ_globalRestore(unsigned int eventId)
{
}

#pragma argsused
void CSL_init(void)
{
}

#pragma argsused
void CACHE_reset(void)
{
}

#pragma argsused
void CACHE_enableCaching(unsigned int block)
{
}

#pragma argsused
void CACHE_setL2Mode(unsigned int mode)
{
}

#pragma argsused
void HPI_setDspint(unsigned int value)
{
}

void simReadRegMem(unsigned int regNum, unsigned int numInt, unsigned int *data)
{
    // if (regNum >= MESSAGE_OFFSET && regNum < GROUP_OFFSET) printf("Accessing register %x\n",regNum);
    memcpy(data,registerAddr(regNum),4*numInt);
}

void simWriteHostMem(unsigned int regNum, unsigned int numInt, unsigned int *data)
{
    memcpy(HOST_BASE+4*regNum,data,4*numInt);
}

int simReadUser(void)
// Allow the simulator to have read access to the user LEDs
{
    int data;
    memcpy(&data,USER_REG,4);
    return data;
}
