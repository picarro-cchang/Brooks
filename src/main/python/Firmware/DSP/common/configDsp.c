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
#include <csl_gpio.h>
#include <csl_hpi.h>
#include <tsk.h>
#include "configDsp.h"


GPIO_Handle hGpio;

// GPIO assignment
// GPIO_PIN0 : disabled, used as host data line HD4
// GPIO_PIN1 : disabled, used as HPI interrupt line HINTz
// GPIO_PIN2 : disabled, used as CLKOUT2
// GPIO_PIN3 : disabled, used as host data line HD7
// GPIO_PIN4 : enabled as input, interrupt at ringdown
// GPIO_PIN5 : enabled as input, interrupt when ringdown data available
// GPIO_PIN6 : enabled as input
// GPIO_PIN7 : enabled as input
// GPIO_PIN8 : disabled, used as host data line HD8
// GPIO_PIN9 : disabled, used as host data line HD9
// GPIO_PIN10: disabled, used as host data line HD10
// GPIO_PIN11: disabled, used as host data line HD11
// GPIO_PIN12: disabled, used as host data line HD12
// GPIO_PIN13: disabled, used as host data line HD13
// GPIO_PIN14: disabled, used as host data line HD14
// GPIO_PIN15: disabled, used as host data line HD15

void GPIO_init()
{
    // Reset GPIO to default. Pass through.
    hGpio = GPIO_open(GPIO_DEV0, GPIO_OPEN_RESET);

    // Set Pin Direction
    GPIO_pinDirection(hGpio,GPIO_PIN4,GPIO_INPUT);
    GPIO_pinDirection(hGpio,GPIO_PIN5,GPIO_INPUT);
    GPIO_pinDirection(hGpio,GPIO_PIN6,GPIO_INPUT);
    GPIO_pinDirection(hGpio,GPIO_PIN7,GPIO_INPUT);

    GPIO_intPolarity( hGpio, GPIO_GPINT4, GPIO_RISING);
    GPIO_intPolarity( hGpio, GPIO_GPINT5, GPIO_RISING);
    GPIO_intPolarity( hGpio, GPIO_GPINT6, GPIO_RISING);
    GPIO_intPolarity( hGpio, GPIO_GPINT7, GPIO_RISING);

    GPIO_pinEnable( hGpio, GPIO_PIN4 | GPIO_PIN5 | GPIO_PIN6 | GPIO_PIN7 );
}

void configDsp()
{
    unsigned int gie;
    gie = IRQ_globalDisable();
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
    GPIO_init();
    IRQ_resetAll();
    IRQ_globalRestore(gie);
}

// Reset strategy
// Cypress PE4 = 1 resets FPGA
// Cypress PA7 = 1 resets DSP
// FPGA cyp_reset = 1 resets Cypress by removing power
