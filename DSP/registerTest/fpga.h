/*
 * FILE:
 *   fpga.h
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
#ifndef _FPGA_H_
#define _FPGA_H_

void writeFPGA(unsigned int regNum, unsigned short value);

#endif /* _FPGA_H_ */
