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
#include "dspData.h"
#include "fpga.h"

#include <math.h>
#include <stdio.h>
#include "fastrts67x.h"

#ifdef TESTING
	#include "testHarness.h"
#else
	#include "registerTestcfg.h"
#endif

SpectCntrlParams spectCntrlParams;

#define state              (*(s->state_))
#define mode               (*(s->mode_))
#define active             (*(s->active_))
#define next               (*(s->next_))
#define iter               (*(s->iter_))
#define row                (*(s->row_))
#define dwell              (*(s->dwell_))

int spectCntrlInit(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
    s->state_ = (SPECT_CNTRL_StateType *)registerAddr(SPECT_CNTRL_STATE_REGISTER); 
    s->mode_  = (unsigned int *)registerAddr(SPECT_CNTRL_MODE_REGISTER); 
    s->active_= (unsigned int *)registerAddr(SPECT_CNTRL_ACTIVE_SCHEME_REGISTER); 
    s->next_  = (unsigned int *)registerAddr(SPECT_CNTRL_NEXT_SCHEME_REGISTER);
    s->iter_  = (unsigned int *)registerAddr(SPECT_CNTRL_SCHEME_ITER_REGISTER);
    s->row_   = (unsigned int *)registerAddr(SPECT_CNTRL_SCHEME_ROW_REGISTER); 
    s->dwell_ = (unsigned int *)registerAddr(SPECT_CNTRL_DWELL_COUNT_REGISTER);
	s->laserTemp_[0] = (float *)registerAddr(LASER1_TEMPERATURE_REGISTER);
	s->laserTemp_[1] = (float *)registerAddr(LASER2_TEMPERATURE_REGISTER);
	s->laserTemp_[2] = (float *)registerAddr(LASER3_TEMPERATURE_REGISTER);
	s->laserTemp_[3] = (float *)registerAddr(LASER4_TEMPERATURE_REGISTER);
    s->coarseLaserCurrent_[0] = (float *)registerAddr(LASER1_MANUAL_COARSE_CURRENT_REGISTER);
    s->coarseLaserCurrent_[1] = (float *)registerAddr(LASER2_MANUAL_COARSE_CURRENT_REGISTER);
    s->coarseLaserCurrent_[2] = (float *)registerAddr(LASER3_MANUAL_COARSE_CURRENT_REGISTER);
    s->coarseLaserCurrent_[3] = (float *)registerAddr(LASER4_MANUAL_COARSE_CURRENT_REGISTER);
	s->etalonTemperature_ = (float *)registerAddr(ETALON_TEMPERATURE_REGISTER);
	s->cavityPressure_ = (float *)registerAddr(CAVITY_PRESSURE_REGISTER);
	s->ambientPressure_ = (float *)registerAddr(AMBIENT_PRESSURE_REGISTER);
	s->defaultThreshold_ = (unsigned int *)registerAddr(SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER);
	return STATUS_OK;
}

int spectCntrlStep(void)
// This is called every 100ms from the scheduler thread to start spectrum acquisition
{
    SpectCntrlParams *s=&spectCntrlParams;
	static SPECT_CNTRL_StateType prevState = SPECT_CNTRL_IdleState;
	SPECT_CNTRL_StateType stateAtStart;
	
	stateAtStart = state;	
	if (SPECT_CNTRL_StartingState == state) {
		setAutoInject();
		state = SPECT_CNTRL_RunningState;
		if (SPECT_CNTRL_SchemeSingleMode == mode || 
			SPECT_CNTRL_SchemeMultipleMode == mode || 
			SPECT_CNTRL_SchemeSequenceMode == mode) {
			iter = 0;
			row = 0;
			dwell = 0;
		}	
	}
	else if (SPECT_CNTRL_RunningState == state) {
		if (SPECT_CNTRL_StartingState == prevState || 
			SPECT_CNTRL_PausedState   == prevState) {
				// Enable laser shutdown 
				// TODO: Handle SOA shutdown
				changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W, 1);
				changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W, 1);
				
				SEM_pendBinary(&SEM_startRdCycle,100);	// Eat up anything pending				
				SEM_postBinary(&SEM_startRdCycle);
		}
	}
	prevState = stateAtStart;
	
	return STATUS_OK;
}

#define PI 3.141592654
void spectCntrl(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	
    int bank, status;
	float theta, dtheta;
	theta = 0.0;	
	dtheta = 0.001;
	
    while (1) {
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
				message_puts("Waiting for bank to become available");
            }
			else {
				message_puts("Ringdown manager busy");
			}
            // Wait around for another ms and recheck
            SEM_pendBinary(&SEM_waitForRdMan,SYS_FOREVER);
        }
        // We shall load the parameters of the ringdown here...
		if (SPECT_CNTRL_ContinuousMode == mode) {
		}
		else {
			advanceDwellCounter();	
		}

		setupRingdown();
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

void setupRingdown(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	RingdownParamsType rdParams;
	unsigned int virtLaserNum, laserNum;
	volatile SchemeTableType *schemeTable = &schemeTables[active];
	volatile VirtualLaserParamsType *vLaserParams;
	float setpoint, dp, theta, ratio1Multiplier, ratio2Multiplier;
	
	virtLaserNum = schemeTable->rows[row].laserUsed;
	vLaserParams = &virtualLaserParams[virtLaserNum];
	setpoint = schemeTable->rows[row].setpoint;

	laserNum = vLaserParams->actualLaser & 0x3;		
	rdParams.injectionSettings = (virtLaserNum << 2) | laserNum;
	rdParams.laserTemperature = *(s->laserTemp_[laserNum]);
	rdParams.coarseLaserCurrent = *(s->coarseLaserCurrent_[laserNum]);
	rdParams.etalonTemperature = *(s->etalonTemperature_);
	rdParams.cavityPressure = *(s->cavityPressure_);
	rdParams.ambientPressure = *(s->ambientPressure_);
	rdParams.schemeTableAndRow = (active << 16) | (row & 0xFFFF);
	
	// TODO: Handle count!		
	rdParams.countAndSubschemeId = (schemeTable->rows[row].subschemeId & 0xFFFF);
	rdParams.ringdownThreshold   = schemeTable->rows[row].threshold;
	if (rdParams.ringdownThreshold == 0) rdParams.ringdownThreshold = *(s->defaultThreshold_);
	// TODO: Compute rdParams.status
	rdParams.status = 0;
	
	// Correct the setpoint angle using the etalon temperature and ambient pressure
	dp = rdParams.ambientPressure - vLaserParams->calPressure;
	theta = setpoint - vLaserParams->tempSensitivity*(rdParams.etalonTemperature-vLaserParams->calTemp) -
			(vLaserParams->pressureC0 + dp*(vLaserParams->pressureC1 + dp*(vLaserParams->pressureC2 + dp*vLaserParams->pressureC3)));
	
	// Compute the ratio multipliers corresponding to this setpoint
	ratio1Multiplier = ((-sinsp(theta + vLaserParams->phase))/(vLaserParams->ratio1Scale * cossp(vLaserParams->phase)));
	ratio2Multiplier = ((cossp(theta))/(vLaserParams->ratio2Scale * cossp(vLaserParams->phase)));

	// Set up the FPGA registers for this ringdown
	changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W, laserNum);

	writeFPGA(FPGA_LASERLOCKER+LASERLOCKER_RATIO1_MULTIPLIER, (int)(ratio1Multiplier*32767.0));
	writeFPGA(FPGA_LASERLOCKER+LASERLOCKER_RATIO2_MULTIPLIER, (int)(ratio2Multiplier*32767.0));

	writeFPGA(FPGA_LASERLOCKER+LASERLOCKER_RATIO1_CENTER, (int)(vLaserParams->ratio1Center*32768.0));
	writeFPGA(FPGA_LASERLOCKER+LASERLOCKER_RATIO2_CENTER, (int)(vLaserParams->ratio2Center*32768.0));
	
	writeFPGA(FPGA_RDMAN+RDMAN_THRESHOLD,rdParams.ringdownThreshold);

	writeFPGA(FPGA_RDMAN+RDMAN_PARAM0,*(uint32*)&rdParams.injectionSettings);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM1,*(uint32*)&rdParams.laserTemperature);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM2,*(uint32*)&rdParams.coarseLaserCurrent);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM3,*(uint32*)&rdParams.etalonTemperature);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM4,*(uint32*)&rdParams.cavityPressure);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM5,*(uint32*)&rdParams.ambientPressure);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM6,*(uint32*)&rdParams.schemeTableAndRow);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM7,*(uint32*)&rdParams.countAndSubschemeId);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM8,*(uint32*)&rdParams.ringdownThreshold);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM9,*(uint32*)&rdParams.status);
	
	// TODO: Change the temperature of the selected laser
}

void setAutoInject(void)
// Set optical injection and laser current controllers to automatic mode. This should be called by the
//  scheduler thread in response to a request to start a scheme, otherwise a race condition could occur
//  leading to the wrong value for INJECT_CONTROL_MODE.
{
	DataType data;

	data.asInt = LASER_CURRENT_CNTRL_AutomaticState;
	writeRegister(LASER1_CURRENT_CNTRL_STATE_REGISTER,data);
	writeRegister(LASER2_CURRENT_CNTRL_STATE_REGISTER,data);
	writeRegister(LASER3_CURRENT_CNTRL_STATE_REGISTER,data);
	writeRegister(LASER4_CURRENT_CNTRL_STATE_REGISTER,data);

	// Setting the FPGA optical injection block to automatic mode has to be done independently
	//  of setting the individual current controllers. Care is needed since the current controllers
	//  periodically write to the INJECT_CONTROL register.
	
	changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL,INJECT_CONTROL_MODE_B,INJECT_CONTROL_MODE_W,1);
}

void validateSchemePosition(void)
// Ensure that the dwell count, scheme row and scheme iteration values are valid and reset 
//  them to zero if not

// TODO: Set up scheme status bits which indicate if we are at the end of scheme iteration or of a scheme

{
    SpectCntrlParams *s=&spectCntrlParams;
	if (active >= NUM_SCHEME_TABLES) {
		message_puts("Active scheme index is out of range, resetting to zero");
		active = 0;
	}
	if (iter >= schemeTables[active].numRepeats) {
		message_puts("Scheme iteration is out of range, resetting to zero");
		iter = 0;
	}	
	if (row >= schemeTables[active].numRows) {
		message_puts("Scheme row is out of range, resetting to zero");
		row = 0;
	}	
	if (dwell >= schemeTables[active].rows[row].dwellCount) {
		message_puts("Dwell count is out of range, resetting to zero");
		dwell = 0;
	}
}

void advanceDwellCounter(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	dwell = dwell + 1;
	if (dwell >= schemeTables[active].rows[row].dwellCount) {
		advanceSchemeRow();
	}
}

void advanceSchemeRow(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	row = row + 1;
	if (row >= schemeTables[active].numRows) {
		advanceSchemeIteration();
	}
	else {
		dwell = 0;
	}
}

void advanceSchemeIteration(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	iter = iter + 1;
	if (iter >= schemeTables[active].numRepeats) {
		advanceScheme();
	}
	else {
		row = 0;
		dwell = 0;
	}
}

void advanceScheme(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	active = next;
	iter = 0;
	row = 0;
	dwell = 0;
}
