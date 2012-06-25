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
    VIRTUAL_LASER_Type *virtLaser_;   // Virtual laser register
    unsigned int *dasStatus_; // Das status register
    float *laserTemp_[4];     // Laser temperature registers
    float *laserTempSetpoint_[4];     // Laser temperature setpoint registers
    float *laserTempUserSetpoint_[4]; // Laser temperature user setpoint registers
    float *coarseLaserCurrent_[4];    // Coarse laser current registers
    float *etalonTemperature_; // Etalon temperature
    float *cavityPressure_;    // Cavity pressure
    float *ambientPressure_;   // Ambient pressure
    float *pztIncrPerFsr_;     // PZT increment per cavity FSR
    float *pztOffsetUpdateFactor_;      // PZT offset update factor
    float *pztOffsetByVirtualLaser_[8]; // PZT offsets for each virtual laser
    float *schemeOffsetByVirtualLaser_[8]; // Scheme temperature offsets for each virtual laser
    unsigned int *defaultThreshold_;  // Default ringdown threshol
    unsigned int *analyzerTuningMode_;  // Analyzer tuning mode
    // Local variables for controller
    unsigned int schemeCounter_;   // Increments after last ringdown of a scheme
    int incrFlag_;                 // Flag indicating MSB of scheme ID is set
    unsigned int incrCounter_;     // Increments after last ringdown of a scheme row with MSB of subscheme ID set
    unsigned int incrCounterNext_; // Records schemeCounter_ on last increment of incrCounter_
    int useMemo_;
} SpectCntrlParams;

extern RingdownParamsType nextRdParams;
extern SpectCntrlParams spectCntrlParams;

int  spectCntrlInit(void);
void spectCntrl(void);
int  spectCntrlStep(void);
void setAutomaticLaserCurrentControl(void);
void setAutomaticLaserTemperatureControl(void);
void setManualControl(void);
void setupNextRdParams(void);
void setupLaserTemperatureAndPztOffset(int useMemo);
int activeLaserTempLocked(void);
void validateSchemePosition(void);
void advanceDwellCounter(void);
void advanceSchemeRow(void);
void advanceSchemeIteration(void);
void advanceScheme(void);
void modifyParamsOnTimeout(unsigned int scheme);
unsigned int getSpectCntrlSchemeCount(void);
void spectCntrlError(void);
void update_wlmsim_laser_temp(void);

#endif /* _SPECT_CNTRL_H_ */
