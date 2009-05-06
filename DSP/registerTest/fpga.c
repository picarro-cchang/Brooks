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
#include <stdio.h>
#include "interface.h"
#include "fpga.h"

#ifdef SIMULATION
void writeFPGA(unsigned int regNum, unsigned short value)
{
    // printf("Writing %d to FPGA register %d\n",value,regNum);
}

#else
void writeFPGA(unsigned int regNum, unsigned short value)
{
}
#endif
