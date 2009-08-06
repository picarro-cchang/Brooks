/*
 * FILE:
 *   spectrumCntrl.c
 *
 * DESCRIPTION:
 *   Spectrum controller routines
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   4-Aug-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include "interface.h"
#include "registers.h"
#include "spectrumCntrl.h"
#include "dspAutogen.h"
#include "fpga.h"

#include <math.h>
#include <std.h>
#include <sem.h>
#include <prd.h>
#include "registerTestcfg.h"

SpectCntrlParams spectCntrlParams;

#define state              (*(s->state_))
#define active             (*(s->active_))
#define next               (*(s->next_))
#define iter               (*(s->iter_))
#define row                (*(s->row_))
#define dwell              (*(s->dwell_))


int spectCntrlInit(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
    s->state_ = (unsigned int *)registerAddr(SPECT_CNTRL_STATE_REGISTER); 
    s->active_= (unsigned int *)registerAddr(SPECT_CNTRL_ACTIVE_SCHEME_REGISTER); 
    s->next_  = (unsigned int *)registerAddr(SPECT_CNTRL_NEXT_SCHEME_REGISTER);
    s->iter_  = (unsigned int *)registerAddr(SPECT_CNTRL_SCHEME_ITER_REGISTER);
    s->row_   = (unsigned int *)registerAddr(SPECT_CNTRL_SCHEME_ROW_REGISTER); 
    s->dwell_ = (unsigned int *)registerAddr(SPECT_CNTRL_DWELL_COUNT_REGISTER);
    return STATUS_OK;
}

#define PI 3.141592654
void spectCntrl(void)
{
    int bank, status;
	float theta, dtheta;
	theta = 0.0;	
	dtheta = 0.001;
	
    while (1) {
/*        SEM_pendBinary(&SEM_waitForRdMan,SYS_FOREVER);
        changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_START_RD_B,
                       RDMAN_CONTROL_START_RD_W,1);
	}
}
*/
        SEM_pendBinary(&SEM_startRdCycle,SYS_FOREVER);
        // The next while loop periodically checks to see if we are allowed
        //  to start the ringdown
        while (1) {
            status = readFPGA(FPGA_RDMAN+RDMAN_STATUS);
            // Can start a new ringdown if the manager is not busy and if the
            //  bank for acquisition is not in use
            if ( !(status & 1<<RDMAN_STATUS_BUSY_B) ) {
                bank = (status & 1<<RDMAN_STATUS_BANK_B) >> RDMAN_STATUS_BANK_B;
                if (0 == bank) {
                    if ( !(status & 1<<RDMAN_STATUS_BANK0_IN_USE_B) ) break;
                }
                else { // 1 == bank
                    if ( !(status & 1<<RDMAN_STATUS_BANK1_IN_USE_B) ) break;
                }
            }
            // Wait around for another ms and recheck
			message_puts("Waiting for 1ms tick");
            SEM_pendBinary(&SEM_waitForRdMan,SYS_FOREVER);
        }
        // We shall load the parameters of the ringdown here...
		theta += dtheta;
		if (theta > PI/4.0) {
			dtheta = -fabs(dtheta);
			theta = PI/4.0;
		}
		else if (theta < -PI/4.0) {
			dtheta = fabs(dtheta);
			theta = -PI/4.0;
		}
		writeFPGA(FPGA_LASERLOCKER+LASERLOCKER_RATIO1_MULTIPLIER,(int)(32000.0*cos(theta)));
		writeFPGA(FPGA_LASERLOCKER+LASERLOCKER_RATIO2_MULTIPLIER,(int)(32000.0*sin(theta)));
			
        // Then initiate the ringdown...
        changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_START_RD_B,
                       RDMAN_CONTROL_START_RD_W,1);
    }
}
