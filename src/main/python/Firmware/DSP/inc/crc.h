/*
 * FILE:
 *   crc.h
 *
 * DESCRIPTION:
 *   Computes CRC using 32-bit and 16-bit codes
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   14-Sep-2008  sze  Initial version.
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */
#ifndef _CRC_H_
#define _CRC_H_

unsigned int calcCrc32 ( unsigned int crc, unsigned int *buffer, unsigned int length32 );
unsigned int calcCrc16 ( unsigned int crc, unsigned short *buffer, unsigned int length16 );

#endif
