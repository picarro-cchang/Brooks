/*
 * FILE:
 *   spectrumCntrl.h
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
#ifndef _SPECT_CNTRL_H_
#define _SPECT_CNTRL_H_

typedef struct SPECT_CNTRL_PARAMS
{
    // References to registers
    SPECT_CNTRL_StateType *state_;    // Controller state
    unsigned int *mode_;     // Controller mode
    unsigned int *active_;   // Active scheme index
    unsigned int *next_;     // Next scheme index
    unsigned int *iter_;     // Scheme iteration
    unsigned int *row_;      // Scheme row
    unsigned int *dwell_;    // Dwell counter
    float *laserTemp_[4];    // Laser temperature registers
    float *coarseLaserCurrent_[4];    // Coarse laser current registers
	float *etalonTemperature_; // Etalon temperature
	float *cavityPressure_;    // Cavity pressure
	float *ambientPressure_;   // Ambient pressure
	unsigned int *defaultThreshold_;  // Default ringdown threshold
    // Local variables for controller
	unsigned int schemeCounter_; // Increments at last ringdown of a scheme
} SpectCntrlParams;

int  spectCntrlInit(void);
void spectCntrl(void);
int  spectCntrlStep(void);
void setAutoInject(void);
void setupRingdown(void);
void validateSchemePosition(void);
void advanceDwellCounter(void);
void advanceSchemeRow(void);
void advanceSchemeIteration(void);
void advanceScheme(void);

#endif /* _SPECT_CNTRL_H_ */
