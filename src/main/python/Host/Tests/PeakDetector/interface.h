/*
 * FILE:
 *   interface.h
 *
 * DESCRIPTION:
 *   Automatically generated interface H file for Picarro gas analyzer. 
 *    DO NOT EDIT.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */
#ifndef _INTERFACE_H
#define _INTERFACE_H

typedef unsigned int uint32;
typedef int int32;
typedef unsigned short uint16;
typedef short int16;
typedef unsigned char uint8;
typedef char int8;

#ifndef FALSE
    #define FALSE (0)
#endif
#ifndef TRUE
    #define TRUE  (1)
#endif

/* Interface Version */
#define interface_version (1)

#define STATUS_OK (0)

/* Constant definitions */
// Maximum number of samples in peak detection history buffer
#define PEAK_DETECT_MAX_HISTORY_LENGTH (1024)

typedef enum {
    VALVE_CNTRL_DisabledState = 0, // Disabled
    VALVE_CNTRL_OutletControlState = 1, // Outlet control
    VALVE_CNTRL_InletControlState = 2, // Inlet control
    VALVE_CNTRL_ManualControlState = 3 // Manual control
} VALVE_CNTRL_StateType;

typedef enum {
    FLOW_CNTRL_DisabledState = 0, // Disabled
    FLOW_CNTRL_EnabledState = 1 // Enabled
} FLOW_CNTRL_StateType;

typedef enum {
    VALVE_CNTRL_THRESHOLD_DisabledState = 0, // Disabled
    VALVE_CNTRL_THRESHOLD_ArmedState = 1, // Armed
    VALVE_CNTRL_THRESHOLD_TriggeredState = 2 // Triggered
} VALVE_CNTRL_THRESHOLD_StateType;

typedef enum {
    PEAK_DETECT_CNTRL_IdleState = 0, // Idle
    PEAK_DETECT_CNTRL_ArmedState = 1, // Armed
    PEAK_DETECT_CNTRL_TriggerPendingState = 2, // Trigger Pending
    PEAK_DETECT_CNTRL_TriggeredState = 3, // Triggered
    PEAK_DETECT_CNTRL_InactiveState = 4, // Inactive
    PEAK_DETECT_CNTRL_CancellingState = 5, // Cancelling
    PEAK_DETECT_CNTRL_PrimingState = 6, // Priming
    PEAK_DETECT_CNTRL_PurgingState = 7, // Purging
    PEAK_DETECT_CNTRL_InjectionPendingState = 8 // Injection Pending
} PEAK_DETECT_CNTRL_StateType;

#endif
