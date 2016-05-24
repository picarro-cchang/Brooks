/*
 * Copyright 2012 Picarro Inc.
 *
 * Common definitions for the CM-CRDS platform.
 */

#ifndef __CM_CRDS_H__
#define __CM_CRDS_H__

#include <stdint.h>


#define TEMP_SENSE_BUFFER_VOL 3

#define HEATER1_PWM_BUFFER_VOL 11
#define HEATER2_PWM_BUFFER_VOL 10


#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

    void cmCrdsSetup(void);
    float cmCrdsGetBufferVolumeTempC(void);
    void cmCrdsSetBufferVolumePWM(uint8_t pwm);

    int cmCrdsDebugGetADCTemp(void);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* __CM_CRDS_H__ */
