/*
 * FILE:
 *   pca8574.h
 *
 * DESCRIPTION:
 *   Routines to communicate with PC8574 I2C to parallel port
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   18-Sep-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _PCA8574_H_
#define  _PCA8574_H_

unsigned char pca8574_rdByte();
void pca8574_wrByte(unsigned char byte);
#endif
