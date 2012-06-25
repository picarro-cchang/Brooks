/*
 * FILE:
 *   pca9547.h
 *
 * DESCRIPTION:
 *   Routines to communicate with PC9547 I2C mux
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   10-Jun-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _PCA9547_H_
#define  _PCA9547_H_

unsigned int mux1_rdChan();
unsigned int mux2_rdChan();
void mux1_wrChan(unsigned int chan);
void mux1_wrChan(unsigned int chan);
#endif
