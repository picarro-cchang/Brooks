/*
 * FILE:
 *   fpga.c
 *
 * DESCRIPTION:
 *   DSP routines for accessing FPGA registers
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   21-Apr-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include <std.h>
#include <csl.h>
#include <csl_cache.h>
#include "interface.h"
#include "fpga.h"

#define FPGA_REG_BASE (RDMEM_ADDRESS + (1<<(EMIF_ADDR_WIDTH+1)))

#ifdef SIMULATION
void writeFPGA(unsigned int regNum, unsigned int value)
{
    // printf("Writing %d to FPGA register %d\n",value,regNum);
}

unsigned int readFPGA(unsigned int regNum)
{
    return 0;
}

#else
void writeFPGA(unsigned int regNum, unsigned int value)
{
    *(int*)(FPGA_REG_BASE+4*regNum) = value;
    CACHE_wbL2((void *)(FPGA_REG_BASE+4*regNum), 4, CACHE_WAIT);
}

unsigned int readFPGA(unsigned int regNum)
{
    return 0xFFFF & (*(unsigned int*)(FPGA_REG_BASE+4*regNum));
}
#endif
