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

#include <string.h>
#include "interface.h"
#include "dspData.h"

#define RDRESULTS_BASE            (DSP_DATA_ADDRESS+4*RDRESULTS_OFFSET)
#define SCHEME_BASE               (DSP_DATA_ADDRESS+4*SCHEME_OFFSET)
#define VIRTUAL_LASER_PARAMS_BASE (DSP_DATA_ADDRESS+4*VIRTUAL_LASER_PARAMS_OFFSET)

#define OSCILLOSCOPE_TRACE_BASE   (SHAREDMEM_ADDRESS+4*OSCILLOSCOPE_TRACE_OFFSET)
#define RINGDOWN_BUFFER_BASE      (SHAREDMEM_ADDRESS+4*RINGDOWN_BUFFER_OFFSET)
#define VALVE_SEQUENCE_BASE       (SHAREDMEM_ADDRESS+4*VALVE_SEQUENCE_OFFSET)

volatile RingdownEntryType      *ringdownEntries = (volatile RingdownEntryType *) RDRESULTS_BASE;
volatile SchemeTableType        *schemeTables    = (volatile SchemeTableType *) SCHEME_BASE;
volatile VirtualLaserParamsType *virtualLaserParams = (volatile VirtualLaserParamsType *) VIRTUAL_LASER_PARAMS_BASE;
volatile OscilloscopeTraceType  *oscilloscopeTrace = (volatile OscilloscopeTraceType *) OSCILLOSCOPE_TRACE_BASE;
RingdownBufferType              *ringdownBuffers = (RingdownBufferType *) RINGDOWN_BUFFER_BASE;
ValveSequenceEntryType          *valveSequence = (ValveSequenceEntryType *) VALVE_SEQUENCE_BASE;

void dspDataInit(void)
{
    memset((void *)schemeTables,0,4*NUM_SCHEME_TABLES*SCHEME_TABLE_SIZE);
    memset((void *)virtualLaserParams,0,4*NUM_VIRTUAL_LASERS*VIRTUAL_LASER_PARAMS_SIZE);
    memset((void *)oscilloscopeTrace,0,4*OSCILLOSCOPE_TRACE_SIZE);
    memset((void *)ringdownBuffers,0,4*NUM_RINGDOWN_BUFFERS*RINGDOWN_BUFFER_SIZE);
    memset((void *)valveSequence,0,4*NUM_VALVE_SEQUENCE_ENTRIES*VALVE_SEQUENCE_ENTRY_SIZE);
}
