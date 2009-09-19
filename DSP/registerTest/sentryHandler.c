/*
 * FILE:
 *   sentryHandler.c
 *
 * DESCRIPTION:
 *   Routines to manage sentries and place the instrument in a safe state under
 *    various error conditions. This is a high priority task executed periodically
 *    under the control of a semaphore posted by a PRD.
 * 
 *   We detect problems with the scheduler thread being unable to run as well as
 *    sentry breaches. Since the scheduler thread is responsible for updating the
 *    sensor values, its failure to run correctly is more serious than a sentry
 *    being breached.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   25-Aug-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include <stdio.h>
#include <std.h>
#include <sem.h>
#include <prd.h>

#include "fpga.h"
#include "registers.h"
#include "registerTestcfg.h"
#include "sentryHandler.h"
#include "interface.h"
#include "valveCntrl.h"

typedef struct {
    unsigned int bitMask;
    float *value;
    float *minSentry;
    float *maxSentry;
} sentryCheckType;

static sentryCheckType sentryChecks[32];
static unsigned int *maxTripped;
static unsigned int *minTripped;
static unsigned int numSentries = 0;
unsigned int schedulerAlive = 0;
static unsigned int secSinceStartup = 0;

void initSentryChecks(void)
{
    unsigned int i = 0, j;
    maxTripped = (unsigned int *)registerAddr(SENTRY_UPPER_LIMIT_TRIPPED_REGISTER);
    minTripped = (unsigned int *)registerAddr(SENTRY_LOWER_LIMIT_TRIPPED_REGISTER);
    
    numSentries = 0;
    sentryChecks[i].bitMask   = SENTRY_Laser1TemperatureMask;
    sentryChecks[i].value     = (float *)registerAddr(LASER1_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER1_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER1_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_Laser2TemperatureMask;
    sentryChecks[i].value     = (float *)registerAddr(LASER2_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER2_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER2_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_Laser3TemperatureMask;
    sentryChecks[i].value     = (float *)registerAddr(LASER3_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER3_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER3_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_Laser4TemperatureMask;
    sentryChecks[i].value     = (float *)registerAddr(LASER4_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER4_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER4_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_EtalonTemperatureMask;
    sentryChecks[i].value     = (float *)registerAddr(ETALON_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_ETALON_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_ETALON_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_WarmBoxTemperatureMask;
    sentryChecks[i].value     = (float *)registerAddr(WARM_BOX_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_WarmBoxHeatsinkTemperatureMask;
    sentryChecks[i].value     = (float *)registerAddr(WARM_BOX_HEATSINK_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_CavityTemperatureMask;
    sentryChecks[i].value     = (float *)registerAddr(CAVITY_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_HotBoxHeatsinkTemperatureMask;
    sentryChecks[i].value     = (float *)registerAddr(HOT_BOX_HEATSINK_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_DasTemperatureMask;
    sentryChecks[i].value     = (float *)registerAddr(DAS_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_DAS_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_DAS_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_Laser1CurrentMask;
    sentryChecks[i].value     = (float *)registerAddr(LASER1_CURRENT_MONITOR_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER1_CURRENT_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER1_CURRENT_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_Laser2CurrentMask;
    sentryChecks[i].value     = (float *)registerAddr(LASER2_CURRENT_MONITOR_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER2_CURRENT_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER2_CURRENT_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_Laser3CurrentMask;
    sentryChecks[i].value     = (float *)registerAddr(LASER3_CURRENT_MONITOR_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER3_CURRENT_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER3_CURRENT_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_Laser4CurrentMask;
    sentryChecks[i].value     = (float *)registerAddr(LASER4_CURRENT_MONITOR_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER4_CURRENT_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER4_CURRENT_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_CavityPressureMask;
    sentryChecks[i].value     = (float *)registerAddr(CAVITY_PRESSURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_CAVITY_PRESSURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_CAVITY_PRESSURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = SENTRY_AmbientPressureMask;
    sentryChecks[i].value     = (float *)registerAddr(AMBIENT_PRESSURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_AMBIENT_PRESSURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_AMBIENT_PRESSURE_MAX_REGISTER);
    i++;
    //  Initialize all values to mid-range so that the sentries do not trip if sensors are absent 
    for (j=0; j<i; j++) {
        *(sentryChecks[j].value) = 0.5 * (*(sentryChecks[j].minSentry) + *(sentryChecks[j].maxSentry));
    }
    *maxTripped = 0;
    *minTripped = 0;
    numSentries = i;
}

void safeMode(void)
// Place instrument in safe mode with scheduler running but laser, TEC and heater currents shut off
//  and all valves closed
{
    // Disable the spectrum controller
    *(SPECT_CNTRL_StateType *)registerAddr(SPECT_CNTRL_STATE_REGISTER) = SPECT_CNTRL_IdleState;
    
    // Disable all laser current drivers
    *(LASER_CURRENT_CNTRL_StateType *)registerAddr(LASER1_CURRENT_CNTRL_STATE_REGISTER) = LASER_CURRENT_CNTRL_DisabledState;
    *(LASER_CURRENT_CNTRL_StateType *)registerAddr(LASER2_CURRENT_CNTRL_STATE_REGISTER) = LASER_CURRENT_CNTRL_DisabledState;
    *(LASER_CURRENT_CNTRL_StateType *)registerAddr(LASER3_CURRENT_CNTRL_STATE_REGISTER) = LASER_CURRENT_CNTRL_DisabledState;
    *(LASER_CURRENT_CNTRL_StateType *)registerAddr(LASER4_CURRENT_CNTRL_STATE_REGISTER) = LASER_CURRENT_CNTRL_DisabledState;

    // Disable all temperature controllers
    *(TEMP_CNTRL_StateType *)registerAddr(LASER1_TEMP_CNTRL_STATE_REGISTER) = TEMP_CNTRL_DisabledState;
    *(TEMP_CNTRL_StateType *)registerAddr(LASER2_TEMP_CNTRL_STATE_REGISTER) = TEMP_CNTRL_DisabledState;
    *(TEMP_CNTRL_StateType *)registerAddr(LASER3_TEMP_CNTRL_STATE_REGISTER) = TEMP_CNTRL_DisabledState;
    *(TEMP_CNTRL_StateType *)registerAddr(LASER4_TEMP_CNTRL_STATE_REGISTER) = TEMP_CNTRL_DisabledState;
    
    // Turn off laser currents in FPGA
    writeFPGA(FPGA_INJECT + INJECT_CONTROL, 0);
    // Turn off laser TEC PWM in FPGA
    writeFPGA(FPGA_PWM_LASER1 + PWM_CS, 0);
    writeFPGA(FPGA_PWM_LASER2 + PWM_CS, 0);
    writeFPGA(FPGA_PWM_LASER3 + PWM_CS, 0);
    writeFPGA(FPGA_PWM_LASER4 + PWM_CS, 0);
    // TO DO: Disable warm box, hot box and heater controllers
    // TO DO: Close all valves

    write_valve_pump_tec(0);
}

// Task function for sentry handler
void sentryHandler(void)
{
    int i;
    while (1)
    {
        SEM_pend(&SEM_sentryHandler,SYS_FOREVER);
        secSinceStartup++;
        if (secSinceStartup >= 10) {
            if (schedulerAlive < 4) {   // Should be 5, since heartbeat occurs every 200ms
                message_puts("Scheduler is not running. Placing instrument in safe mode.");
                safeMode();
            }
            else {
                if (numSentries > 0) {
                    for (i=0; i<numSentries; i++) {
                        if (*(sentryChecks[i].value) > *(sentryChecks[i].maxSentry)) {
                            *maxTripped |= sentryChecks[i].bitMask;
                        }
                        if (*(sentryChecks[i].value) < *(sentryChecks[i].minSentry)) {
                            *minTripped |= sentryChecks[i].bitMask;
                        }
                    }
                    if (*maxTripped != 0 || *minTripped != 0) {
                        message_puts("One or more sentries have been tripped. Placing instrument in safe mode.");
                        safeMode();
                    }
                }
            }
        }
        schedulerAlive = 0;
    }
}

