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

void writeFPGA(unsigned int regNum, unsigned int value);
unsigned int readFPGA(unsigned int regNum);
void changeInMaskFPGA(unsigned int regNum, unsigned int mask,
                      unsigned int value);
void changeBitsFPGA(unsigned int regNum, unsigned int lsb,
                    unsigned int width, unsigned int value);
unsigned int readBitsFPGA(unsigned int regNum, unsigned int lsb,
                  unsigned int width);

#endif /* _FPGA_H_ */
