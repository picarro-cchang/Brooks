/*
 * FILE:
 *   tempCntrl.h
 *
 * DESCRIPTION:
 *   Temperature controller routines
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   16-Dec-2008  sze  Initial version.
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */
#ifndef _TEMP_CNTRL_H_
#define _TEMP_CNTRL_H_

typedef struct TEMP_CNTRL
{
    // References to registers
    unsigned int *state_;    // Controller state
    float *tol_;             // Lock tolerance
    unsigned int lockBit_;   // Locked bit position in DAS status
    unsigned int activeBit_; // Active bit position in DAS status
    float *swpMin_;          // Minimum sweep value
    float *swpMax_;          // Maximum sweep value
    float *swpInc_;          // Sweep increment
    float *extMax_;          // Maximum external temperature
    float *prbsAmp_;         // Pseudo-random binary sequence amplitude
    float *prbsMean_;        // Pseudo-random binary sequence mean value
    unsigned int *prbsGen_;  // Pseudo-random binary sequence generator polynomial
    float *temp_;            // Temperature
    float *extTemp_;         // External temperature, e.g., heatsink
    float *dasTemp_;         // Das temperature for feed-forward
    float *userSetpoint_;    // User-specified temperature setpoint
    float *manualTec_;       // Manual control TEC value
    float *tec_;             // TEC actuator value
    // Local variables for controller
    unsigned int prbsReg; // Pseudo-random binary sequence generator register
    int swpDir;
    int lockCount;
    int unlockCount;
    int firstIteration;
    int disabledValue;
    float lastTec;
    // PID structures
    PidState pidState;
    PidParamsRef pidParamsRef;
} TempCntrl;

int resistanceToTemperature(float resistance, float constA,
                            float constB, float constC, float *result);
int tempCntrlLaser1Init(void);
int tempCntrlLaser1Step(void);
int tempCntrlLaser2Init(void);
int tempCntrlLaser2Step(void);
int tempCntrlLaser3Init(void);
int tempCntrlLaser3Step(void);
int tempCntrlLaser4Init(void);
int tempCntrlLaser4Step(void);
int tempCntrlCavityInit(void);
int tempCntrlCavityStep(void);
int tempCntrlWarmBoxInit(void);
int tempCntrlWarmBoxStep(void);
int tempCntrlHeaterInit(void);
int tempCntrlHeaterStep(void);
int tempCntrlFilterHeaterInit(void);
int tempCntrlFilterHeaterStep(void);
int read_laser_tec_imon(int desired, int next, float *result);
int read_laser_tec_monitors(void);

#endif /* _TEMP_CNTRL_H_ */
