/*
 * FILE:
 *   dspData.h
 *
 * DESCRIPTION:
 *   Declare structures which reside in the DSP_DATA segment
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   14-Jul-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */

#ifndef  _DSPDATA_H_
#define  _DSPDATA_H_
#include "interface.h"

extern volatile RingdownEntryType ringdownEntries[];
extern int ringdownWaveform[4096];

#endif
