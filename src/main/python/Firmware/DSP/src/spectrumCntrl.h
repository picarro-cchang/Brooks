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
    float *schemeThresholdFactorByVirtualLaser_[8]; // Scheme temperature offsets for each virtual laser
    unsigned int *schemeThresholdBase_;  // scheme ringdown threshold base
    unsigned int *defaultThreshold_;  // Default ringdown threshol
    unsigned int *analyzerTuningMode_;  // Analyzer tuning mode
    float *frontMirrorDac_[4];  // SGDBR laser front mirror current DAC
    float *backMirrorDac_[4];   // SGDBR laser back mirror current DAC
    float *gainDac_[4];         // SGDBR laser gain current DAC
    float *soaSetting_[4];      // SGDBR laser SOA nominal setting 
    unsigned int soaDac[4];     // SGDBR laser SOA current DAC value during ringdown
    float *coarsePhaseDac_[4];  // SGDBR coarse phase current DAC
    float *finePhaseDac_[4];    // SGDBR fine phase current DAC
    float *front_to_soa_coeff_[4]; // Coefficient for modifying SOA current based on front mirror current
    float *back_to_soa_coeff_[4];  // Coefficient for modifying SOA current based on back mirror current
    float *phase_to_soa_coeff_[4];  // Coefficient for modifying SOA current based on coarse phase current
    float *dead_zone_[4];   // When mirror currents are less than this value, do not apply correction to SOA
    float *minimum_soa_[4]; // Minimum SOA value allowed during scans
    unsigned int *pzt_cntrl_state_;  // State of PZT controller
    float *wlm_angle_modulus_; // Change in WLM angle corresponding to one cavity FSR
    float *ref_update_time_constant_; // Update time constant for reference arrays
    float *pzt_update_scale_factor_; // Scale factor to convert to PZT update (in units of cavity FSR)
    float *pzt_update_clamp_;   // Maximum change in PZT position between ringdowns (in units of cavity FSR)
    float *pzt_cntrl_flattening_factor_;   // Feedback factor for flattening PZT motion
    float *pzt_cntrl_averaging_samples_;   // Number of samples to average over to determine PZT reference
    float *pzt_cntrl_shift_;   // Shift of PZT in units of cavity FSR per virtual laser

    // SGDBR current source register indices
    unsigned int sgdbr_csr_[4];    // SGDBR current source CSR
    unsigned int sgdbr_mosi_data_[4];    // SGDBR current source MOSI data
    unsigned int sgdbr_miso_data_[4];    // SGDBR current source MISO data

    // Local variables for controller
    unsigned int schemeCounter_;   // Increments after last ringdown of a scheme
    int incrFlag_;                 // Flag indicating MSB of scheme ID is set
    unsigned int incrCounter_;     // Increments after last ringdown of a scheme row with MSB of subscheme ID set
    unsigned int incrCounterNext_; // Records schemeCounter_ on last increment of incrCounter_
    int useMemo_;
    unsigned int *pztUpdateMode_; // PZT update mode
    unsigned short modeIndex_;     // Mode index sent by scheme
} SpectCntrlParams;

extern RingdownParamsType nextRdParams;
extern SpectCntrlParams spectCntrlParams;
extern float pztLctOffset;

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
