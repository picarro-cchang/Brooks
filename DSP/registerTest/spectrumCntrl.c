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
#include "tunerCntrl.h"
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

RingdownParamsType nextRdParams;
SpectCntrlParams spectCntrlParams;

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
    s->laserTempSetpoint_[0] = (float *)registerAddr(LASER1_TEMP_CNTRL_SETPOINT_REGISTER);
    s->laserTempSetpoint_[1] = (float *)registerAddr(LASER2_TEMP_CNTRL_SETPOINT_REGISTER);
    s->laserTempSetpoint_[2] = (float *)registerAddr(LASER3_TEMP_CNTRL_SETPOINT_REGISTER);
    s->laserTempSetpoint_[3] = (float *)registerAddr(LASER4_TEMP_CNTRL_SETPOINT_REGISTER);
	s->etalonTemperature_ = (float *)registerAddr(ETALON_TEMPERATURE_REGISTER);
	s->cavityPressure_ = (float *)registerAddr(CAVITY_PRESSURE_REGISTER);
	s->ambientPressure_ = (float *)registerAddr(AMBIENT_PRESSURE_REGISTER);
	s->defaultThreshold_ = (unsigned int *)registerAddr(SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER);
	s->virtLaser_ = (VIRTUAL_LASER_Type *)registerAddr(VIRTUAL_LASER_REGISTER);
	s->schemeCounter_ =  0;
	switchToRampMode();
	return STATUS_OK;
}

int spectCntrlStep(void)
// This is called every 100ms from the scheduler thread to start spectrum acquisition
{
    SpectCntrlParams *s=&spectCntrlParams;
	static SPECT_CNTRL_StateType prevState = SPECT_CNTRL_IdleState;
	SPECT_CNTRL_StateType stateAtStart;
	
	stateAtStart = *(s->state_);	
	if (SPECT_CNTRL_StartingState == *(s->state_)) {
		setAutomaticControl();
		*(s->state_) = SPECT_CNTRL_RunningState;
		if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_) || 
			SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) || 
			SPECT_CNTRL_SchemeSequenceMode == *(s->mode_)) {
			// Enable frequency locking for schemes
			changeBitsFPGA(FPGA_RDMAN+RDMAN_OPTIONS, RDMAN_OPTIONS_LOCK_ENABLE_B, RDMAN_OPTIONS_LOCK_ENABLE_W, 1);
			*(s->iter_) = 0;
			*(s->row_) = 0;
			*(s->dwell_) = 0;
		}	
	}
	else if (SPECT_CNTRL_RunningState == *(s->state_)) {
		if (SPECT_CNTRL_StartingState == prevState || 
			SPECT_CNTRL_PausedState   == prevState) {
				switchToRampMode();
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
		setupNextRdParams();
		/*
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
		*/	
        // Then initiate the ringdown...
        changeBitsFPGA(FPGA_RDMAN+RDMAN_CONTROL,RDMAN_CONTROL_START_RD_B,
                       RDMAN_CONTROL_START_RD_W,1);
    }
}

void setupLaserTemperature(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	unsigned int laserNum;
	volatile SchemeTableType *schemeTable = &schemeTables[*(s->active_)];
	volatile VirtualLaserParamsType *vLaserParams;
	float laserTemp;
	
	*(s->virtLaser_) = (VIRTUAL_LASER_Type) schemeTable->rows[*(s->row_)].laserUsed;
	vLaserParams = &virtualLaserParams[*(s->virtLaser_)];
	laserTemp = 0.001 * schemeTable->rows[*(s->row_)].laserTemp; // Scheme temperatures are in milli-degrees C
	laserNum = vLaserParams->actualLaser & 0x3;

	if (laserTemp != 0.0) {
		*(s->laserTempSetpoint_[laserNum]) = laserTemp;
	}
}

void setupNextRdParams(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	RingdownParamsType *r=&nextRdParams;

	unsigned int laserNum;
	volatile SchemeTableType *schemeTable;
	volatile VirtualLaserParamsType *vLaserParams;
	float setpoint, dp, theta, ratio1Multiplier, ratio2Multiplier;
	
	if (SPECT_CNTRL_ContinuousMode == *(s->mode_)) { 
		// In continuous mode, we run with the parameter values currently in the registers
		vLaserParams = &virtualLaserParams[*(s->virtLaser_)];
		laserNum = vLaserParams->actualLaser & 0x3;		
		r->injectionSettings = (*(s->virtLaser_) << 2) | laserNum;
		r->laserTemperature = *(s->laserTemp_[laserNum]);
		r->coarseLaserCurrent = *(s->coarseLaserCurrent_[laserNum]);
		r->etalonTemperature = *(s->etalonTemperature_);
		r->cavityPressure = *(s->cavityPressure_);
		r->ambientPressure = *(s->ambientPressure_);
		r->schemeTableAndRow = 0;
		r->countAndSubschemeId = 0;
		r->ringdownThreshold = *(s->defaultThreshold_);
		r->status = 0;
		// Set up the FPGA registers for this ringdown
		changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL, INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W, laserNum);
		writeFPGA(FPGA_RDMAN+RDMAN_THRESHOLD,r->ringdownThreshold);
	}
	else {	// We are running a scheme		
		schemeTable = &schemeTables[*(s->active_)];
		*(s->virtLaser_) = (VIRTUAL_LASER_Type) schemeTable->rows[*(s->row_)].laserUsed;
		vLaserParams = &virtualLaserParams[*(s->virtLaser_)];
		setpoint = schemeTable->rows[*(s->row_)].setpoint;
	
		laserNum = vLaserParams->actualLaser & 0x3;		
		r->injectionSettings = (*(s->virtLaser_) << 2) | laserNum;
		r->laserTemperature = *(s->laserTemp_[laserNum]);
		r->coarseLaserCurrent = *(s->coarseLaserCurrent_[laserNum]);
		r->etalonTemperature = *(s->etalonTemperature_);
		r->cavityPressure = *(s->cavityPressure_);
		r->ambientPressure = *(s->ambientPressure_);
		r->schemeTableAndRow = (*(s->active_) << 16) | (*(s->row_) & 0xFFFF);
		
		// TODO: Handle count!		
		r->countAndSubschemeId = (schemeTable->rows[*(s->row_)].subschemeId & 0xFFFF);
		r->ringdownThreshold   = schemeTable->rows[*(s->row_)].threshold;
		if (r->ringdownThreshold == 0) r->ringdownThreshold = *(s->defaultThreshold_);
		r->status = (s->schemeCounter_ & RINGDOWN_STATUS_SchemeIncrMask);
		if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_) ||
			SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) ||
			SPECT_CNTRL_SchemeSequenceMode == *(s->mode_)) r->status |= RINGDOWN_STATUS_SchemeActiveMask;
		// Determine if we are on the last ringdown of the scheme
		if (*(s->iter_) == schemeTables[*(s->active_)].numRepeats-1 &&
			*(s->row_)  == schemeTables[*(s->active_)].numRows-1 &&
			*(s->dwell_) == schemeTables[*(s->active_)].rows[*(s->row_)].dwellCount-1) {
			if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_)) r->status |= RINGDOWN_STATUS_SchemeCompleteInSingleModeMask;
			else if (SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) ||
					 SPECT_CNTRL_SchemeSequenceMode == *(s->mode_)) r->status |= RINGDOWN_STATUS_SchemeCompleteInMultipleModeMask;
		}
			
		// Correct the setpoint angle using the etalon temperature and ambient pressure
		dp = r->ambientPressure - vLaserParams->calPressure;
		theta = setpoint - vLaserParams->tempSensitivity*(r->etalonTemperature-vLaserParams->calTemp) -
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
		
		writeFPGA(FPGA_RDMAN+RDMAN_THRESHOLD,r->ringdownThreshold);
	}
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM0,*(uint32*)&r->injectionSettings);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM1,*(uint32*)&r->laserTemperature);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM2,*(uint32*)&r->coarseLaserCurrent);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM3,*(uint32*)&r->etalonTemperature);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM4,*(uint32*)&r->cavityPressure);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM5,*(uint32*)&r->ambientPressure);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM6,*(uint32*)&r->schemeTableAndRow);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM7,*(uint32*)&r->countAndSubschemeId);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM8,*(uint32*)&r->ringdownThreshold);
	writeFPGA(FPGA_RDMAN+RDMAN_PARAM9,*(uint32*)&r->status);
}



void modifyParamsOnTimeout(unsigned int schemeCount)
// If a ringdown timeout occurs, i.e., if there is no ringdown within the allotted interval, we
//  proceed to the next scheme row, short-circuiting the dwell count requested. An entry is
//  placed on the ringdown buffer queue with a special status when this occurs. It may be necessary
//  to modify the bits which indicate if we are at the end of a scheme as a result of this 
//  short-circuiting.
{
    SpectCntrlParams *s=&spectCntrlParams;
	RingdownParamsType *r=&nextRdParams;
	r->status |= RINGDOWN_STATUS_RingdownTimeout;
	if (s->schemeCounter_ != schemeCount) {
		// We have advanced to another scheme, so set the end-of-scheme status bits appropriately
		r->status &= ~(RINGDOWN_STATUS_SchemeCompleteInSingleModeMask | RINGDOWN_STATUS_SchemeCompleteInMultipleModeMask);
		if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_)) r->status |= RINGDOWN_STATUS_SchemeCompleteInSingleModeMask;
		else if (SPECT_CNTRL_SchemeMultipleMode == *(s->mode_) ||
			     SPECT_CNTRL_SchemeSequenceMode == *(s->mode_)) r->status |= RINGDOWN_STATUS_SchemeCompleteInMultipleModeMask;
	}
}

unsigned int getSpectCntrlSchemeCount(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	return s->schemeCounter_;
}

void setAutomaticControl(void)
// Set optical injection, laser current and laser temperature controllers to automatic mode. This should be called by the
//  scheduler thread in response to a request to start a scheme, otherwise a race condition could occur
//  leading to the wrong value for INJECT_CONTROL_MODE.
{
	DataType data;

	data.asInt = LASER_CURRENT_CNTRL_AutomaticState;
	writeRegister(LASER1_CURRENT_CNTRL_STATE_REGISTER,data);
	writeRegister(LASER2_CURRENT_CNTRL_STATE_REGISTER,data);
	writeRegister(LASER3_CURRENT_CNTRL_STATE_REGISTER,data);
	writeRegister(LASER4_CURRENT_CNTRL_STATE_REGISTER,data);

	data.asInt = TEMP_CNTRL_AutomaticState;
	writeRegister(LASER1_TEMP_CNTRL_STATE_REGISTER,data);
	writeRegister(LASER2_TEMP_CNTRL_STATE_REGISTER,data);
	writeRegister(LASER3_TEMP_CNTRL_STATE_REGISTER,data);
	writeRegister(LASER4_TEMP_CNTRL_STATE_REGISTER,data);
	
	// Setting the FPGA optical injection block to automatic mode has to be done independently
	//  of setting the individual current controllers. Care is needed since the current controllers
	//  periodically write to the INJECT_CONTROL register.
	
	changeBitsFPGA(FPGA_INJECT+INJECT_CONTROL,INJECT_CONTROL_MODE_B,INJECT_CONTROL_MODE_W,1);
}

void validateSchemePosition(void)
// Ensure that the dwell count, scheme row and scheme iteration values are valid and reset 
//  them to zero if not

// TODO: Set up scheme status bits which indicate if we are at the end of a scheme

{
    SpectCntrlParams *s=&spectCntrlParams;
	if (*(s->active_) >= NUM_SCHEME_TABLES) {
		message_puts("Active scheme index is out of range, resetting to zero");
		*(s->active_) = 0;
	}
	if (*(s->iter_) >= schemeTables[*(s->active_)].numRepeats) {
		message_puts("Scheme iteration is out of range, resetting to zero");
		*(s->iter_) = 0;
	}	
	if (*(s->row_) >= schemeTables[*(s->active_)].numRows) {
		message_puts("Scheme row is out of range, resetting to zero");
		*(s->row_) = 0;
	}	
	if (*(s->dwell_) >= schemeTables[*(s->active_)].rows[*(s->row_)].dwellCount) {
		message_puts("Dwell count is out of range, resetting to zero");
		*(s->dwell_) = 0;
	}
}

void advanceDwellCounter(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	*(s->dwell_) = *(s->dwell_) + 1;
	if (*(s->dwell_) >= schemeTables[*(s->active_)].rows[*(s->row_)].dwellCount) {
		advanceSchemeRow();
	}
}

void advanceSchemeRow(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	*(s->row_) = *(s->row_) + 1;
	if (*(s->row_) >= schemeTables[*(s->active_)].numRows) {
		advanceSchemeIteration();
	}
	else {
		*(s->dwell_) = 0;
	}
}

void advanceSchemeIteration(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	*(s->iter_) = *(s->iter_) + 1;
	if (*(s->iter_) >= schemeTables[*(s->active_)].numRepeats) {
		advanceScheme();
	}
	else {
		*(s->row_) = 0;
		*(s->dwell_) = 0;
	}
}

void advanceScheme(void)
{
    SpectCntrlParams *s=&spectCntrlParams;
	s->schemeCounter_++;
	*(s->active_) = *(s->next_);
	*(s->iter_) = 0;
	*(s->row_) = 0;
	*(s->dwell_) = 0;
	if (SPECT_CNTRL_SchemeSingleMode == *(s->mode_)) 
		*(s->state_) = SPECT_CNTRL_IdleState;
}
