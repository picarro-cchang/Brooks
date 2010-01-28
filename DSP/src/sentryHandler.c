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
#include <string.h>
#include <sem.h>
#include <prd.h>

#include "fpga.h"
#include "registers.h"
#include "dspMaincfg.h"
#include "sentryHandler.h"
#include "interface.h"
#include "valveCntrl.h"

typedef struct
{
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
static unsigned int ticksPerSecond = 20;
static unsigned int ticksSinceStartup = 0;
static char sentry_msg[32][40];
static char msg[120];

void initSentryChecks(void)
{
    unsigned int i = 0, j;
    maxTripped = (unsigned int *)registerAddr(SENTRY_UPPER_LIMIT_TRIPPED_REGISTER);
    minTripped = (unsigned int *)registerAddr(SENTRY_LOWER_LIMIT_TRIPPED_REGISTER);

    numSentries = 0;
    sentryChecks[i].bitMask   = 1 << SENTRY_Laser1TemperatureBit;
    sentryChecks[i].value     = (float *)registerAddr(LASER1_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER1_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER1_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_Laser2TemperatureBit;
    sentryChecks[i].value     = (float *)registerAddr(LASER2_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER2_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER2_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_Laser3TemperatureBit;
    sentryChecks[i].value     = (float *)registerAddr(LASER3_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER3_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER3_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_Laser4TemperatureBit;
    sentryChecks[i].value     = (float *)registerAddr(LASER4_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER4_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER4_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_EtalonTemperatureBit;
    sentryChecks[i].value     = (float *)registerAddr(ETALON_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_ETALON_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_ETALON_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_WarmBoxTemperatureBit;
    sentryChecks[i].value     = (float *)registerAddr(WARM_BOX_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_WarmBoxHeatsinkTemperatureBit;
    sentryChecks[i].value     = (float *)registerAddr(WARM_BOX_HEATSINK_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_CavityTemperatureBit;
    sentryChecks[i].value     = (float *)registerAddr(CAVITY_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_HotBoxHeatsinkTemperatureBit;
    sentryChecks[i].value     = (float *)registerAddr(HOT_BOX_HEATSINK_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_DasTemperatureBit;
    sentryChecks[i].value     = (float *)registerAddr(DAS_TEMPERATURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_DAS_TEMPERATURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_DAS_TEMPERATURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_Laser1CurrentBit;
    sentryChecks[i].value     = (float *)registerAddr(LASER1_CURRENT_MONITOR_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER1_CURRENT_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER1_CURRENT_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_Laser2CurrentBit;
    sentryChecks[i].value     = (float *)registerAddr(LASER2_CURRENT_MONITOR_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER2_CURRENT_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER2_CURRENT_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_Laser3CurrentBit;
    sentryChecks[i].value     = (float *)registerAddr(LASER3_CURRENT_MONITOR_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER3_CURRENT_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER3_CURRENT_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_Laser4CurrentBit;
    sentryChecks[i].value     = (float *)registerAddr(LASER4_CURRENT_MONITOR_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_LASER4_CURRENT_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_LASER4_CURRENT_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_CavityPressureBit;
    sentryChecks[i].value     = (float *)registerAddr(CAVITY_PRESSURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_CAVITY_PRESSURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_CAVITY_PRESSURE_MAX_REGISTER);
    i++;
    sentryChecks[i].bitMask   = 1 << SENTRY_AmbientPressureBit;
    sentryChecks[i].value     = (float *)registerAddr(AMBIENT_PRESSURE_REGISTER);
    sentryChecks[i].minSentry = (float *)registerAddr(SENTRY_AMBIENT_PRESSURE_MIN_REGISTER);
    sentryChecks[i].maxSentry = (float *)registerAddr(SENTRY_AMBIENT_PRESSURE_MAX_REGISTER);
    i++;
    
    strcpy(sentry_msg[SENTRY_Laser1TemperatureBit],"Laser 1 Temperature");
    strcpy(sentry_msg[SENTRY_Laser2TemperatureBit],"Laser 2 Temperature");
    strcpy(sentry_msg[SENTRY_Laser3TemperatureBit],"Laser 3 Temperature");
    strcpy(sentry_msg[SENTRY_Laser4TemperatureBit],"Laser 4 Temperature");
    strcpy(sentry_msg[SENTRY_EtalonTemperatureBit],"Etalon Temperature");
    strcpy(sentry_msg[SENTRY_WarmBoxTemperatureBit],"Warm Box Temperature");
    strcpy(sentry_msg[SENTRY_WarmBoxHeatsinkTemperatureBit],"Warm Box Heatsink Temperature");
    strcpy(sentry_msg[SENTRY_CavityTemperatureBit],"Cavity Temperature");
    strcpy(sentry_msg[SENTRY_HotBoxHeatsinkTemperatureBit],"Hot Box Heatsink Temperature");
    strcpy(sentry_msg[SENTRY_DasTemperatureBit],"DAS (ambient) Temperature");
    strcpy(sentry_msg[SENTRY_Laser1CurrentBit],"Laser 1 Current");
    strcpy(sentry_msg[SENTRY_Laser2CurrentBit],"Laser 2 Current");
    strcpy(sentry_msg[SENTRY_Laser3CurrentBit],"Laser 3 Current");
    strcpy(sentry_msg[SENTRY_Laser4CurrentBit],"Laser 4 Current");
    strcpy(sentry_msg[SENTRY_CavityPressureBit],"Cavity Pressure");
    strcpy(sentry_msg[SENTRY_AmbientPressureBit],"Ambient Pressure");
    
    //  Initialize all values to mid-range so that the sentries do not trip if sensors are absent
    for (j=0; j<i; j++)
    {
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
    *(TEMP_CNTRL_StateType *)registerAddr(WARM_BOX_TEMP_CNTRL_STATE_REGISTER) = TEMP_CNTRL_DisabledState;
    *(TEMP_CNTRL_StateType *)registerAddr(CAVITY_TEMP_CNTRL_STATE_REGISTER)   = TEMP_CNTRL_DisabledState;
    //*(HEATER_CNTRL_StateType *)registerAddr(HEATER_CNTRL_STATE_REGISTER)   = HEATER_CNTRL_DisabledState;
    *(TEMP_CNTRL_StateType *)registerAddr(HEATER_TEMP_CNTRL_STATE_REGISTER)  = TEMP_CNTRL_DisabledState;

    // Turn off laser currents in FPGA
    writeFPGA(FPGA_INJECT + INJECT_CONTROL, 0);
    // Turn off laser TEC PWM in FPGA
    writeFPGA(FPGA_PWM_LASER1 + PWM_CS, 0);
    writeFPGA(FPGA_PWM_LASER2 + PWM_CS, 0);
    writeFPGA(FPGA_PWM_LASER3 + PWM_CS, 0);
    writeFPGA(FPGA_PWM_LASER4 + PWM_CS, 0);

    *(TEC_CNTRL_Type*)registerAddr(TEC_CNTRL_REGISTER) = TEC_CNTRL_Disabled;
    write_valve_pump_tec(0);
}

// Task function for sentry handler
void sentryHandler(void)
{
    int overloaded = 0, schedulerFailed = 0;
    int prevOverload = 0, inSafeMode = 0;
    int i;
    
    while (1)
    {
        int overload;
        int hardwarePresent = *(int *)registerAddr(HARDWARE_PRESENT_REGISTER);
        int installedMask = 0;
		int powerBoardPresent = 0 != (hardwarePresent & (1<<HARDWARE_PRESENT_PowerBoardBit));
            
        if (hardwarePresent & (1<<HARDWARE_PRESENT_WarmBoxBit)) installedMask |= 1<<OVERLOAD_WarmBoxTecBit;
        if (hardwarePresent & (1<<HARDWARE_PRESENT_HotBoxBit))  installedMask |= 1<<OVERLOAD_HotBoxTecBit;
            
        SEM_pend(&SEM_sentryHandler,SYS_FOREVER);
        ticksSinceStartup++;
        if (inSafeMode) safeMode(); // Force system into safe mode once tripped
            
        // Handle overload conditions by seeing if any overload bits persist for more than 50ms
        
        if (powerBoardPresent && !inSafeMode) {       
            overload = readFPGA(FPGA_KERNEL + KERNEL_OVERLOAD);
            if (overload) {
                // Reset latched bits in the kernel overload register
                changeBitsFPGA(FPGA_KERNEL + KERNEL_CONTROL, KERNEL_CONTROL_OVERLOAD_RESET_B, KERNEL_CONTROL_OVERLOAD_RESET_W, 1);
            }
            overloaded = (overload & prevOverload) & installedMask;
            if (0 != overloaded) {
                safeMode();
                inSafeMode = 1;
            }
            prevOverload = overload;
        }
        
        if (ticksSinceStartup > 10*ticksPerSecond) {
            if (0 == (ticksSinceStartup % ticksPerSecond)) {    // Things to check once every second
                if (schedulerFailed || schedulerAlive < 4) {    // Should be 5, since heartbeat occurs every 200ms
                    schedulerFailed = 1;
                    safeMode();
                    inSafeMode = 1;
                }
                schedulerAlive = 0;
                
                for (i=0; i<numSentries; i++)
                {
                    if (*(sentryChecks[i].value) > *(sentryChecks[i].maxSentry))
                    {
                        *maxTripped |= sentryChecks[i].bitMask;
                    }
                    if (*(sentryChecks[i].value) < *(sentryChecks[i].minSentry))
                    {
                        *minTripped |= sentryChecks[i].bitMask;
                    }
                }
                if (*maxTripped != 0 || *minTripped != 0)
                {
                    safeMode();
                    inSafeMode = 1;
                }
            }            
        }
    
        // Send messages every 5s once in safe mode
        
        if (0 == (ticksSinceStartup % (5*ticksPerSecond))) {
            if (inSafeMode) {
                unsigned int max = *maxTripped, min = *minTripped;
                for (i=0; i<numSentries; i++) {
                    if ((max & 1) && (min & 1)) sprintf(msg,"%s minimum and maximum sentries exceeded.",sentry_msg[i]);
                    else if (max & 1) sprintf(msg,"%s maximum sentry exceeded.",sentry_msg[i]);
                    else if (min & 1) sprintf(msg,"%s minimum sentry exceeded.",sentry_msg[i]);
                    if ((max & 1) || (min & 1)) message_puts(msg);
                    max >>= 1; min >>= 1;
                }
                if (schedulerFailed) message_puts("Scheduler failure.");
                if (overloaded) {
                    sprintf(msg,"Overload condition detected: 0x%x",overloaded);
                    message_puts(msg);
                }
                message_puts("Instrument placed in safe mode.");
            }    
        }
    }
}
