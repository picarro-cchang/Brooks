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

extern volatile RingdownEntryType        *ringdownEntries;
extern volatile SchemeTableType          *schemeTables;
extern volatile VirtualLaserParamsType   *virtualLaserParams;
extern volatile OscilloscopeTraceType    *oscilloscopeTrace;
extern volatile SchemeSequenceType       *schemeSequence;
extern RingdownBufferType                *ringdownBuffers;
extern ValveSequenceEntryType            *valveSequence;

void dspDataInit(void);
#endif
