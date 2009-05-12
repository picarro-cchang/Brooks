/*
 * FILE:
 *   configDsp.c
 *
 * DESCRIPTION:
 *   Routines to configure DSP for operation
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   6-May-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include <std.h>
#include <csl.h>
#include <csl_i2c.h>
#include <csl_cache.h>
#include <csl_chip.h>
#include <csl_irq.h>
#include <csl_hpi.h>
#include <tsk.h>
#include "configDsp.h"

void configDsp()
{
    CSL_init();
    CACHE_reset();
    CACHE_enableCaching(CACHE_CE00);
    CACHE_setL2Mode(CACHE_64KCACHE);
    CHIP_configArgs(
       CHIP_DEVCFG_RMK(
          CHIP_DEVCFG_EKSRC_SYSCLK3,     // SYSCLK3 (90MHz) is the EMIF clock source
          CHIP_DEVCFG_TOUT1SEL_TOUT1PIN, // TOUT1SEL
          CHIP_DEVCFG_TOUT0SEL_TOUT0PIN, // TOUT0SEL
          CHIP_DEVCFG_MCBSP0DIS_1,       // MCBSP0 disabled
          CHIP_DEVCFG_MCBSP1DIS_1        // MCBSP1 disabled
    ));
}
