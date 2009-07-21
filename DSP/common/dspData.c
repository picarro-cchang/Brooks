/*
 * FILE:
 *   dspData.c
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

#include "interface.h"
#include "dspData.h"

#pragma DATA_SECTION( ringdownEntries , ".dsp_data" );
volatile RingdownEntryType ringdownEntries[NUM_RINGDOWN_ENTRIES];

#pragma DATA_SECTION( ringdownWaveform , ".iram" );
int ringdownWaveform[4096];
