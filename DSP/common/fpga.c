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
    *(unsigned int*)(FPGA_REG_BASE+4*regNum) = value;
    CACHE_wbL2((void *)(FPGA_REG_BASE+4*regNum), 4, CACHE_WAIT);
}

unsigned int readFPGA(unsigned int regNum)
{
    return 0xFFFF & (*(unsigned int*)(FPGA_REG_BASE+4*regNum));
}

void changeBitsFPGA(unsigned int regNum, unsigned int lsb,
                    unsigned int width, unsigned int value)
/* Change the values of the bits between lsb and lsb+width-1
    to the specified value */
{
    unsigned int current = *(unsigned int*)(FPGA_REG_BASE+4*regNum);
    unsigned int mask = ((1<<width)-1) << lsb;
    current = (current & ~mask) | ((value << lsb) & mask);
    *(unsigned int*)(FPGA_REG_BASE+4*regNum) = current;
    CACHE_wbL2((void *)(FPGA_REG_BASE+4*regNum), 4, CACHE_WAIT);
}

void changeInMaskFPGA(unsigned int regNum, unsigned int mask,
                      unsigned int value)
/* Change the values of the bits which have a "1" in the mask
    to the corresponding bits in value */
{
    unsigned int current = *(unsigned int*)(FPGA_REG_BASE+4*regNum);
    current = (current & ~mask) | (value & mask);
    *(unsigned int*)(FPGA_REG_BASE+4*regNum) = current;
    CACHE_wbL2((void *)(FPGA_REG_BASE+4*regNum), 4, CACHE_WAIT);
}

unsigned int readBitsFPGA(unsigned int regNum, unsigned int lsb,
                          unsigned int width)
/* Read the values of the bits between lsb and lsb+width-1 */
{
    unsigned int current = *(unsigned int*)(FPGA_REG_BASE+4*regNum);
    unsigned int mask = ((1<<width)-1) << lsb;
    return (current & mask) >> lsb;
}

void *rdDataAddr(int bank)
/* Get DSP pointer to ringdown data area */
{
    return (void *)(RDMEM_ADDRESS + 4*(bank ? 0x4000:0x0000));
}

void *rdMetaAddr(int bank)
/* Get DSP pointer to ringdown metadata area */
{
    return (void *)(RDMEM_ADDRESS + 4*(bank ? 0x5000:0x1000));
}

void *rdDataAndMetaAddr(int bank)
/* Get DSP pointer to area with both data and metadata as LSW and MSW of 32-bit ints*/
{
    return (void *)(RDMEM_ADDRESS + 4*(bank ? 0x6000:0x2000));
}

void *rdParamAddr(int bank)
/* Get DSP pointer to ringdown parameter area */
{
    return (void *)(RDMEM_ADDRESS + 4*(bank ? 0x7000:0x3000));
}

#endif
