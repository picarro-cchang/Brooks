/*
 * FILE:
 *   misc.h
 *
 * DESCRIPTION:
 *   Miscellaneous routines to perform actions for software testing
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   12-Apr-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef _MISC_H_
#define _MISC_H_

#include "interface.h"
int pulseGenerator(unsigned int lowDuration,unsigned int highDuration,
                   float *result,PulseGenEnvType *env);
int filter(float x, float *y,FilterEnvType *env);

#endif /* _MISC_H_ */
