/*
 * FILE:
 *   action_handler.c
 *
 * DESCRIPTION:
 *   Routines to perform DSP actions. Actions are operations that
 *    can be placed on the runqueue and which can be accessed
 *    directly from Python.

 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   4-Apr-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include <std.h>
#include <stdio.h>
#include <string.h>
#include <csl.h>
#include <csl_cache.h>
#include <csl_timer.h>

#include "dspAutogen.h"
#include "dspMainCfg.h"
#include "interface.h"
#include "misc.h"
#include "pid.h"
#include "registers.h"
#include "scheduler.h"
#include "scopeHandler.h"
#include "sentryHandler.h"
#include "spectrumCntrl.h"
#include "tempCntrl.h"
#include "laserCurrentCntrl.h"
#include "fanCntrl.h"
#include "heaterCntrl.h"
#include "tunerCntrl.h"
#include "valveCntrl.h"
#include "peakDetectCntrl.h"
#include "i2c_dsp.h"
#include "ds1631.h"
#include "ltc2451.h"
#include "ltc2499.h"
#include "fpga.h"
#include "i2cEeprom.h"
#include "rddCntrl.h"
#include "adxl345.h"
#include "sgdbrCurrentSource.h"
#include "soa_cntrl.h"

static char message[120];

#define READ_REG(regNum, result)                 \
    {                                            \
        DataType d;                              \
        int status = readRegister((regNum), &d); \
        if (STATUS_OK != status)                 \
            return status;                       \
        switch (getRegisterType(regNum))         \
        {                                        \
        case float_type:                         \
            (result) = d.asFloat;                \
            break;                               \
        case uint_type:                          \
            (result) = d.asUint;                 \
            break;                               \
        case int_type:                           \
            (result) = d.asInt;                  \
            break;                               \
        }                                        \
    }

#define WRITE_REG(regNum, result)            \
    {                                        \
        DataType d;                          \
        int status;                          \
        switch (getRegisterType(regNum))     \
        {                                    \
        case float_type:                     \
            d.asFloat = (result);            \
            break;                           \
        case uint_type:                      \
            d.asUint = (result);             \
            break;                           \
        case int_type:                       \
            d.asInt = (result);              \
            break;                           \
        }                                    \
        status = writeRegister((regNum), d); \
        if (STATUS_OK != status)             \
            return status;                   \
    }

int writeBlock(unsigned int numInt, void *params, void *env)
// Writes a block to the communication area. The number of integers written is numInt-1, since params[0] is the start index
// The indices lie in various "areas", defined by the OFFSET
{
    unsigned int offset = *(unsigned int *)params;
    unsigned int *data = ((unsigned int *)params) + 1;
    // printf("WriteBlock: numInt = %d, offset = %d\n", numInt, offset);

    numInt -= 1;
    if (offset + numInt > SHAREDMEM_SIZE)
        return ERROR_OUTSIDE_SHAREDMEM;
    else
        memcpy((void *)(SHAREDMEM_BASE + 4 * offset), data, 4 * numInt);
#if EXT_MEM
    CACHE_wbL2((void *)(SHAREDMEM_BASE + 4 * offset), 4 * numInt, CACHE_WAIT);
#endif
    return STATUS_OK;
}

int initRunqueue(unsigned int numInt, void *params, void *env)
// Load up the scheduler runqueue based on the operation groups defined.
//  Required parameter is the number of groups.
{
    unsigned int *paramsAsInt = (unsigned int *)params;
    unsigned int i, nGroups;
    long long now;
    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    get_timestamp(&now);
    nGroups = paramsAsInt[0];
    for (i = 0; i < nGroups; i++)
    {
        unsigned int period_ms = 100 * get_group_period(i);
        long long next_time = ((now + period_ms) / period_ms) * period_ms;
        insert_into_runqueue(i, next_time);
    }
    return STATUS_OK;
}

int testScheduler(unsigned int numInt, void *params, void *env)
// This action simply sends back its parameters via message_puts in order to help
//  test the operation of the scheduler.
{
    unsigned int i;
    unsigned int *paramsAsInt = (unsigned int *)params;
    strcpy(message, "testScheduler");
    for (i = 0; i < numInt; i++)
    {
        sprintf(message + strlen(message), " %d", paramsAsInt[i]);
    }
    message_puts(LOG_LEVEL_STANDARD, message);
    return STATUS_OK;
}

int streamRegisterAsFloat(unsigned int numInt, void *params, void *env)
// This action streams the value of a register. The first parameter
//  is the stream number and the second is the register number. Note
//  that the type of data on the stream is the same as the type of the
//  register
{
    unsigned int *paramsAsInt = (unsigned int *)params;
    unsigned int streamNum;
    float value;
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    streamNum = paramsAsInt[0];
    READ_REG(paramsAsInt[1], value);
    sensor_put_from(streamNum, value);
    return STATUS_OK;
}

int streamFpgaRegisterAsFloat(unsigned int numInt, void *params, void *env)
// This action streams the value of an FPGA register. The first parameter
//  is the stream number, the second is the location in the FPGA map
//  and the third is the register number
{
    unsigned int *paramsAsInt = (unsigned int *)params;
    unsigned int fpgaBase, regNum, streamNum;
    float value;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    streamNum = paramsAsInt[0];
    fpgaBase = paramsAsInt[1];
    regNum = paramsAsInt[2];
    value = readFPGA(fpgaBase + regNum);
    sensor_put_from(streamNum, value);
    return STATUS_OK;
}

int setTimestamp(unsigned int numInt, void *params, void *env)
// Writes a 64 bit timestamp to the instrument. params[0] is the
//  least significant 32 bits and params[1] is the most significant
//  32 bits of the host timestamp.
{
    unsigned int *paramsAsInt = (unsigned int *)params;
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    timestamp = paramsAsInt[0] + (((long long)paramsAsInt[1]) << 32);
    return STATUS_OK;
}

int nudgeTimestamp(unsigned int numInt, void *params, void *env)
// Uses 64 bit host timestamp to adjust the instrument timestamp.
// i.e., the timestamps are compared and if they differ by more
//  than NUDGE_LIMIT ms, the analyzer timestamp is changed
//  by speeding up or slowing down the clock by 1 part in 64. If the
//  difference lies within NUDGE_WINDOW ms, reset the timer divisor to
//  normal value. Otherwise, the analyzer timestamp is moved towards the
//  host timestamp by changing the division ratio of the DSP PRD timer to
//  speed up or slow down the clock by approximately 1 part in 2**11.

// params[0] is the least significant 32 bits and params[1] is
//  the most significant 32 bits of the host timestamp.
{
    unsigned int *paramsAsInt = (unsigned int *)params;
    unsigned int target_divisor;
    long long hostTimestamp = paramsAsInt[0] + (((long long)paramsAsInt[1]) << 32);
    long long delta = timestamp - hostTimestamp;

    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    if (delta & 0x80000000)
    { // timestamp < hostTimestamp, may need to speed up DSP clock
        delta = (~delta) + 1;
        if (delta > NUDGE_LIMIT)
            target_divisor = DSP_TIMER_DIVISOR - (DSP_TIMER_DIVISOR >> 6);
        else if (delta < NUDGE_WINDOW)
            target_divisor = DSP_TIMER_DIVISOR;
        else
            target_divisor = DSP_TIMER_DIVISOR - (DSP_TIMER_DIVISOR >> 11);
    }
    else
    { // timestamp > hostTimestamp, may need to slow down DSP clock
        if (delta > NUDGE_LIMIT)
            target_divisor = DSP_TIMER_DIVISOR + (DSP_TIMER_DIVISOR >> 6);
        else if (delta < NUDGE_WINDOW)
            target_divisor = DSP_TIMER_DIVISOR;
        else
            target_divisor = DSP_TIMER_DIVISOR + (DSP_TIMER_DIVISOR >> 11);
    }
    if (TIMER_getPeriod(hTimer0) != target_divisor)
    {
        TIMER_pause(hTimer0);
        TIMER_setPeriod(hTimer0, target_divisor);
        // Be careful that we do not move period past the current count
        if (TIMER_getCount(hTimer0) >= target_divisor)
            TIMER_setCount(hTimer0, target_divisor - 1);
        TIMER_resume(hTimer0);
    }
    return STATUS_OK;
}

int r_getTimestamp(unsigned int numInt, void *params, void *env)
// Read the 64 bit timestamp into two registers, the LS 32 bits into
//  the first and the MS 32 bits into the second
{
    unsigned int *reg = (unsigned int *)params;
    long long ts = timestamp;
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    WRITE_REG(reg[0], (uint32)(ts & 0xFFFFFFFF));
    WRITE_REG(reg[1], (uint32)(ts >> 32));
    return STATUS_OK;
}

int r_wbCache(unsigned int numInt, void *params, void *env)
/* Write back cache for a region of memory
   Input:
        addr(int):      address to region
        length(int):    length of region in bytes
*/
{
    unsigned int *reg = (unsigned int *)params;
    CACHE_wbL2((void *)reg[0], reg[1], CACHE_WAIT);
    return STATUS_OK;
}

int r_wbInvCache(unsigned int numInt, void *params, void *env)
/* Write back and invalidate cache for a region of memory
   Input:
        addr(int):      address to region
        length(int):    length of region in bytes
*/
{
    unsigned int *reg = (unsigned int *)params;
    CACHE_wbInvL2((void *)reg[0], reg[1], CACHE_WAIT);
    return STATUS_OK;
}

int r_update_from_simulators(unsigned int numInt, void *params, void *env)
{
    return STATUS_OK;
}

int r_step_simulators(unsigned int numInt, void *params, void *env)
{
    return STATUS_OK;
}

int r_resistanceToTemperature(unsigned int numInt, void *params, void *env)
{
    float resistance, constA, constB, constC, result;
    int status;

    unsigned int *reg = (unsigned int *)params;
    if (5 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], resistance);
    READ_REG(reg[1], constA);
    READ_REG(reg[2], constB);
    READ_REG(reg[3], constC);
    status = resistanceToTemperature(resistance, constA, constB, constC, &result);
    WRITE_REG(reg[4], result);
    return status;
}

int r_tempCntrlSetCommand(unsigned int numInt, void *params, void *env)
{
    return STATUS_OK;
}

int r_applyPidStep(unsigned int numInt, void *params, void *env)
{
    return STATUS_OK;
}

int r_tempCntrlLaser1Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser1Init();
}

int r_tempCntrlLaser1Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser1Step();
    return status;
}

int r_tempCntrlLaser2Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser2Init();
}

int r_tempCntrlLaser2Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser2Step();
    return status;
}

int r_tempCntrlLaser3Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser3Init();
}

int r_tempCntrlLaser3Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser3Step();
    return status;
}

int r_tempCntrlLaser4Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser4Init();
}

int r_tempCntrlLaser4Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser4Step();
    return status;
}

int r_floatRegisterToFpga(unsigned int numInt, void *params, void *env)
/* Copy contents of a floating point register to an FPGA register,
    treating value as an unsigned int. The FPGA register is the sum
    of two arguments so that we can pass a block base and an offset within
    the block. */
{
    float value;
    unsigned int *reg = (unsigned int *)params;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], value);
    writeFPGA(reg[1] + reg[2], (unsigned int)value);
    return STATUS_OK;
}

int r_fpgaToFloatRegister(unsigned int numInt, void *params, void *env)
/* Copy contents of an FPGA register to a floating point register,
    treating value as an unsigned short. The FPGA register is the sum
    of two arguments so that we can pass a block base and an offset within
    the block. */
{
    float value;
    unsigned int *reg = (unsigned int *)params;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    value = readFPGA(reg[0] + reg[1]);
    WRITE_REG(reg[2], value);
    return STATUS_OK;
}

int r_intToFpga(unsigned int numInt, void *params, void *env)
/* Copy integer (passed as first parameter) to the specified FPGA register.
    The FPGA register is the sum of two arguments so that we can pass a
    block base and an offset within the block. */
{
    unsigned int *reg = (unsigned int *)params;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    writeFPGA(reg[1] + reg[2], reg[0]);
    return STATUS_OK;
}

int r_currentCntrlLaser1Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return currentCntrlLaser1Init();
}

int r_currentCntrlLaser1Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = currentCntrlLaser1Step();
    return status;
}

int r_currentCntrlLaser2Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return currentCntrlLaser2Init();
}

int r_currentCntrlLaser2Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = currentCntrlLaser2Step();
    return status;
}

int r_currentCntrlLaser3Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return currentCntrlLaser3Init();
}

int r_currentCntrlLaser3Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = currentCntrlLaser3Step();
    return status;
}

int r_currentCntrlLaser4Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return currentCntrlLaser4Init();
}

int r_currentCntrlLaser4Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = currentCntrlLaser4Step();
    return status;
}

int r_tempCntrlWarmBoxInit(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlWarmBoxInit();
}

int r_tempCntrlWarmBoxStep(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlWarmBoxStep();
    return status;
}

int r_tempCntrlCavityInit(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlCavityInit();
}

int r_tempCntrlCavityStep(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlCavityStep();
    return status;
}

int r_heaterCntrlInit(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    //return heaterCntrlInit();
    return tempCntrlHeaterInit();
}

int r_heaterCntrlStep(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    //    status = heaterCntrlStep();
    status = tempCntrlHeaterStep();
    return status;
}

int r_tunerCntrlInit(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tunerCntrlInit();
}

int r_tunerCntrlStep(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tunerCntrlStep();
    return status;
}

int r_spectCntrlInit(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return spectCntrlInit();
}

int r_spectCntrlStep(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = spectCntrlStep();
    return status;
}

int r_valveCntrlInit(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return valveCntrlInit();
}

int r_valveCntrlStep(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = valveCntrlStep();
    return status;
}

int r_envChecker(unsigned int numInt, void *params, void *env)
// This action tests the use of the environment pointer
{
    CheckEnvType *myEnv = (CheckEnvType *)env;
    sprintf(message, "envChecker: %5d %5d", myEnv->var1, myEnv->var2);
    myEnv->var1 += 1;
    myEnv->var2 += 2;
    message_puts(LOG_LEVEL_STANDARD, message);
    return STATUS_OK;
}

int r_pulseGenerator(unsigned int numInt, void *params, void *env)
/*
    Pulse generator:
    Inputs:
        Register (int):   Duration of low level
        Register (int):   Duration of high level
    Output:
        Register (float): Generator output
    Environment:
        PulseGenEnvType
    Comments:
        The output levels are 0.0 and 1.0
*/
{
    unsigned int lowDuration, highDuration;
    int status;
    float result;
    unsigned int *reg = (unsigned int *)params;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], lowDuration);
    READ_REG(reg[1], highDuration);
    status = pulseGenerator(lowDuration, highDuration, &result,
                            (PulseGenEnvType *)env);
    WRITE_REG(reg[2], result);
    return status;
}

int r_filter(unsigned int numInt, void *params, void *env)
/*
    Discrete time filter:
    Input:
        Register (float):   Input sequence
    Output:
        Register (float):   Output sequence
    Environment:
        FilterEnvType
    Comments:
        The filter coefficients and state are in FilterEnvType
*/
{
    float x, y;
    int status;

    unsigned int *reg = (unsigned int *)params;
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], x);
    status = filter(x, &y, (FilterEnvType *)env);
    WRITE_REG(reg[1], y);
    return status;
}

int r_ds1631_readTemp(unsigned int numInt, void *params, void *env)
/* Read DS1631 temprature */
{
    unsigned int *reg = (unsigned int *)params;
    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    WRITE_REG(reg[0], ds1631_readTemperatureAsFloat(&i2c_devices[DAS_TEMP_SENSOR]));
    return STATUS_OK;
}

int r_read_thermistor_resistance_sgdbr(unsigned int numInt, void *params, void *env)
/*
    Reads thermistor resistance on the SGDBR current source board

    Output:
        Register (float): Register to contain result
    Input:
        Register (float): Register containing series resistance
*/
{
    unsigned int *reg = (unsigned int *)params;
    float Vfrac = 0.0, Rseries;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
	Vfrac = sgdbrReadThermistorAdc(reg[0]);
    READ_REG(reg[2], Rseries);
    if (Vfrac < 0.0 || Vfrac > 1.0)
        return ERROR_BAD_VALUE;
    WRITE_REG(reg[1], (Rseries * Vfrac) / (1.0 - Vfrac));
    return STATUS_OK;
}

int r_sgdbr_cntrl_init(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
	return sgdbrCntrlInit(reg[0]);
}

int r_sgdbr_cntrl_step(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
	return sgdbrCntrlStep(reg[0]);
}

int r_read_thermistor_resistance(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    float result;
    float Vfrac, Rseries;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[2], Rseries);
    result = ltc2485_read(reg[0]);
    Vfrac = result / 33554432.0;
    if (Vfrac <= 0.0 || Vfrac >= 1.0)
        return ERROR_BAD_VALUE;
    WRITE_REG(reg[1], (Rseries * Vfrac) / (1.0 - Vfrac));
    return STATUS_OK;
}

int r_read_thermistor_resistance_16bit(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    float result;
    float Vfrac, Rseries;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[2], Rseries);
    result = ltc2451_read(reg[0]);
    Vfrac = (result - 32768.0) / 32768.0;
    if (Vfrac <= 0.0 || Vfrac >= 1.0)
        return ERROR_BAD_VALUE;
    WRITE_REG(reg[1], (Rseries * Vfrac) / (1.0 - Vfrac));
    return STATUS_OK;
}

int r_read_pressure_adc(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    unsigned int result;
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    result = ltc2485_read(reg[0]);
    if (result != I2C_READ_ERROR)
        WRITE_REG(reg[1], result);
    return STATUS_OK;
}

int r_read_laser_current(unsigned int numInt, void *params, void *env)
/*
    Reads laser current monitor of specified laser. If an I2C error
    occurs the register is not updated.

    Input:
        laserNum (int)  :  Laser number to read (1-origin)
        Register (float): Register containing conversion slope
        Register (float): Register containing conversion offset
    Output:
        Register (float):  Register to receive current reading
*/
{
    unsigned int *reg = (unsigned int *)params;
    float slope, offset, result;
    int adc_value;
    if (4 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[1], slope);
    READ_REG(reg[2], offset);
    adc_value = read_laser_current_adc(reg[0]);
    if (adc_value != I2C_READ_ERROR)
    { /* Filter out I2C errors */
        result = adc_value * slope + offset;
        WRITE_REG(reg[3], result);
    }
    return STATUS_OK;
}

int r_schedulerHeartbeat(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    schedulerAlive++;
    return STATUS_OK;
}

int r_sentryInit(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    initSentryChecks();
    return STATUS_OK;
}

int r_modifyValvePumpTec(unsigned int numInt, void *params, void *env)
/* Modify the valve, pump and TEC states by using the first parameter as a mask
    and the second as the index of an integer register specifying bits to set
    within the mask */
{
    unsigned int *reg = (unsigned int *)params;
    unsigned int valveValues;

    READ_REG(reg[1], valveValues);
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    modify_valve_pump_tec(reg[0], valveValues);
    return STATUS_OK;
}

int r_update_wlmsim_laser_temp(unsigned int numInt, void *params, void *env)
/* Write the temperature of the currently selected laser to the WLM simulator register */
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    update_wlmsim_laser_temp();
    return STATUS_OK;
}

int r_simulate_laser_current_reading(unsigned int numInt, void *params, void *env)
/* For the specified laser number (1-origin), place the simulated laser current reading (obtained
    by combining coarse and fine laser contributions) into the specified register.  The scaling is
    360nA/fine_current unit, and 10 fine_current units = 1 coarse_current unit. */
{
    unsigned int *reg = (unsigned int *)params;
    unsigned int dac = 0;
    float current;

    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;

    switch (reg[0])
    {
    case 1:
        dac = 10 * readFPGA(FPGA_INJECT + INJECT_LASER1_COARSE_CURRENT) + 2 * readFPGA(FPGA_INJECT + INJECT_LASER1_FINE_CURRENT);
        break;
    case 2:
        dac = 10 * readFPGA(FPGA_INJECT + INJECT_LASER2_COARSE_CURRENT) + 2 * readFPGA(FPGA_INJECT + INJECT_LASER2_FINE_CURRENT);
        break;
    case 3:
        dac = 10 * readFPGA(FPGA_INJECT + INJECT_LASER3_COARSE_CURRENT) + 2 * readFPGA(FPGA_INJECT + INJECT_LASER3_FINE_CURRENT);
        break;
    case 4:
        dac = 10 * readFPGA(FPGA_INJECT + INJECT_LASER4_COARSE_CURRENT) + 2 * readFPGA(FPGA_INJECT + INJECT_LASER4_FINE_CURRENT);
        break;
    }
    current = 0.00036 * dac;
    WRITE_REG(reg[1], current);
    return STATUS_OK;
}

int r_adc_to_pressure(unsigned int numInt, void *params, void *env)
/*
    Reads laser current monitor of specified laser
    Input:
        Register (int):  Register containing ADC value
        Register (float): Register containing conversion slope
        Register (float): Register containing conversion offset
    Output:
        Register (float):  Register to receive output pressure
*/
{
    unsigned int *reg = (unsigned int *)params;
    int adcVal;
    float slope, offset, result;
    if (4 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], adcVal);
    READ_REG(reg[1], slope);
    READ_REG(reg[2], offset);
    result = adcVal * slope + offset;
    WRITE_REG(reg[3], result);
    return STATUS_OK;
}

int r_set_inlet_valve(unsigned int numInt, void *params, void *env)
/*
    Sets up the inlet valve dynamic PWM
    Input:
        Register (float):   Register containing mean inlet valve position
        Register (float):   Register containing peak-to-peak dither
*/
{
    unsigned int *reg = (unsigned int *)params;
    float value, dither;
    float minPwm = 0.0, maxPwm = 65535.0;

    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], value);
    READ_REG(reg[1], dither);
    if (dither > 20000.0)
        dither = 20000.0;
    if (value < minPwm)
        value = minPwm;
    if (value > maxPwm)
        value = maxPwm;
    if (value - 0.5 * dither < minPwm)
        dither = 2.0 * (value - minPwm);
    if (value + 0.5 * dither > maxPwm)
        dither = 2.0 * (maxPwm - value);
    writeFPGA(FPGA_DYNAMICPWM_INLET + DYNAMICPWM_HIGH, value + 0.5 * dither);
    writeFPGA(FPGA_DYNAMICPWM_INLET + DYNAMICPWM_LOW, value - 0.5 * dither);
    return STATUS_OK;
}

int r_set_outlet_valve(unsigned int numInt, void *params, void *env)
/*
    Sets up the outlet valve dynamic PWM
    Input:
        Register (float):   Register containing mean outlet valve position
        Register (float):   Register containing peak-to-peak dither
*/
{
    unsigned int *reg = (unsigned int *)params;
    float value, dither;
    float minPwm = 0.0, maxPwm = 65535.0;

    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], value);
    READ_REG(reg[1], dither);
    if (dither > 20000.0)
        dither = 20000.0;
    if (value < minPwm)
        value = minPwm;
    if (value > maxPwm)
        value = maxPwm;
    if (value - 0.5 * dither < minPwm)
        dither = 2.0 * (value - minPwm);
    if (value + 0.5 * dither > maxPwm)
        dither = 2.0 * (maxPwm - value);
    writeFPGA(FPGA_DYNAMICPWM_OUTLET + DYNAMICPWM_HIGH, value + 0.5 * dither);
    writeFPGA(FPGA_DYNAMICPWM_OUTLET + DYNAMICPWM_LOW, value - 0.5 * dither);
    return STATUS_OK;
}

int r_interpolator_set_target(unsigned int numInt, void *params, void *env)
/* Interpolators are used to spread out an actuator change over a number of samples so as to
    reduce the effects of sudden changes. reg[0] specifies a register which contains the target
    value of the actuator, and reg[1] specifies the number of steps over which the change
    is to be spread. The interpolator state is stored in an InterpolatorEnvType object. */
{
    unsigned int *reg = (unsigned int *)params;
    InterpolatorEnvType *intenv = (InterpolatorEnvType *)env;

    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], intenv->target);
    intenv->steps = reg[1];
    return STATUS_OK;
}

int r_interpolator_step(unsigned int numInt, void *params, void *env)
/* Performs a single step of the interpolator indicated by *env, and writes the result to the
    FPGA register whose block index and register index are passed as params[0] and params[1].
    This should be run after the interpolator_set_target action by placing it in a lower
    priority group. */
{
    unsigned int *reg = (unsigned int *)params;
    InterpolatorEnvType *intenv = (InterpolatorEnvType *)env;

    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    if (intenv->steps >= 1)
    {
        float alpha = 1.0 / (intenv->steps);
        intenv->current = (1 - alpha) * (intenv->current) + alpha * (intenv->target);
        (intenv->steps)--;
    }
    else
        intenv->current = (intenv->target);
    writeFPGA(reg[0] + reg[1], (unsigned int)(intenv->current));
    return STATUS_OK;
}

static int _eeprom_read(I2C_device *dev, unsigned int addr, unsigned int nbytes, void *env)
/* Reads from an EEPROM. */
{
    unsigned int chain, loops;
    Byte64EnvType *byte64Env = (Byte64EnvType *)env;

    chain = dev->chain;
    // Switch the I2C multiplexer if necessary
    switch (chain)
    {
    case 0:
        if (dev->mux >= 0)
            setI2C0Mux(dev->mux);
        break;
    case 1:
        if (dev->mux >= 0)
            setI2C1Mux(dev->mux);
        break;
    }
    for (loops = 0; loops < 1000; loops++)
        ;
    eeprom_read(dev, addr, (unsigned char *)(byte64Env->buffer), nbytes);
    return STATUS_OK;
}

int r_eeprom_read_low_level(unsigned int numInt, void *params, void *env)
/* Reads from an EEPROM. Arguments are the I2C chain, the multiplexer channel,
    the I2C address, the address in the EEPROM and the number of bytes to read. The result is
    placed within the environment. */
{
    unsigned int *reg = (unsigned int *)params;
    I2C_device device;

    if (5 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    device.chain = reg[0];
    device.mux = reg[1];
    device.addr = reg[2];
    return _eeprom_read(&device, reg[3], reg[4], env);
}

int r_eeprom_read(unsigned int numInt, void *params, void *env)
/* Reads from an EEPROM in the analyzer. Arguments are the EEPROM ID, the address in the EEPROM
    and the number of bytes to read. The result is placed within the environment. */
{
    unsigned int id, *reg = (unsigned int *)params;

    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    id = reg[0];
    return _eeprom_read(&i2c_devices[id], reg[1], reg[2], env);
}

static int _eeprom_write(I2C_device *dev, unsigned int addr, unsigned int nbytes, void *env)
/* Writes to an EEPROM */
{
    unsigned int chain, loops;
    Byte64EnvType *byte64Env = (Byte64EnvType *)env;

    chain = dev->chain;
    // Switch the I2C multiplexer if necessary
    switch (chain)
    {
    case 0:
        if (dev->mux >= 0)
            setI2C0Mux(dev->mux);
        break;
    case 1:
        if (dev->mux >= 0)
            setI2C1Mux(dev->mux);
        break;
    }
    for (loops = 0; loops < 1000; loops++)
        ;
    eeprom_write(dev, addr, (unsigned char *)(byte64Env->buffer), nbytes);
    return STATUS_OK;
}

int r_eeprom_write_low_level(unsigned int numInt, void *params, void *env)
/* Writes to an EEPROM. Arguments are the I2C chain, the multiplexer channel,
    the I2C address, the address in the EEPROM and the number of bytes to write.
    The result is obtained from the environment. */
{
    unsigned int *reg = (unsigned int *)params;
    I2C_device device;

    if (5 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    device.chain = reg[0];
    device.mux = reg[1];
    device.addr = reg[2];
    return _eeprom_write(&device, reg[3], reg[4], env);
}

int r_eeprom_write(unsigned int numInt, void *params, void *env)
/* Writes to an EEPROM in the analyzer. Arguments are the EEPROM ID, the address in the EEPROM
    and the number of bytes to write. The data is obtained from the environment. */
{
    unsigned int id, *reg = (unsigned int *)params;

    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    id = reg[0];
    return _eeprom_write(&i2c_devices[id], reg[1], reg[2], env);
}

static int _eeprom_ready(I2C_device *dev)
/* Check that the EEPROM in the analyzer is ready for read/write. */
{
    unsigned int chain, loops;

    chain = dev->chain;
    // Switch the I2C multiplexer if necessary
    switch (chain)
    {
    case 0:
        if (dev->mux >= 0)
            setI2C0Mux(dev->mux);
        break;
    case 1:
        if (dev->mux >= 0)
            setI2C1Mux(dev->mux);
        break;
    }
    for (loops = 0; loops < 1000; loops++)
        ;
    return !eeprom_busy(dev);
}

int r_eeprom_ready_low_level(unsigned int numInt, void *params, void *env)
/* Check that the EEPROM in the analyzer is ready for read/write. Arguments are the I2C chain, the
    multiplexer channel and the I2C address. The result is placed in the COMM_STATUS_REGISTER. */
{
    unsigned int *reg = (unsigned int *)params;
    I2C_device device;

    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    device.chain = reg[0];
    device.mux = reg[1];
    device.addr = reg[2];
    return _eeprom_ready(&device);
}

int r_eeprom_ready(unsigned int numInt, void *params, void *env)
/* Check that the EEPROM in the analyzer is ready for read/write. Argument is the EEPROM ID.
    The result is placed in the COMM_STATUS_REGISTER. */
{
    unsigned int id, *reg = (unsigned int *)params;

    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    id = reg[0];
    return _eeprom_ready(&i2c_devices[id]);
}

int r_i2c_check(unsigned int numInt, void *params, void *env)
/* Check the I2C device specified by checking if it will acknowlege a read request (for 0 bytes).
    The arguments are the I2C chain index (0 or 1), the multiplexer setting (0 through 7, or -1 if don't care)
    and the I2C address. Returned value is the status of the read request.
 */
{
    int *reg = (int *)params, loops;
    int chain, addr;

    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    chain = reg[0];
    switch (chain)
    {
    case 0:
        if (reg[1] >= 0)
            setI2C0Mux(reg[1]);
        break;
    case 1:
        if (reg[1] >= 0)
            setI2C1Mux(reg[1]);
        break;
    }
    for (loops = 0; loops < 1000; loops++)
        ;
    addr = reg[2];
    return I2C_check_ack(hI2C[chain], addr);
}

int r_float_arithmetic(unsigned int numInt, void *params, void *env)
{
    unsigned int op;
    float x, y, result;

    unsigned int *reg = (unsigned int *)params;
    if (4 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], x);
    READ_REG(reg[1], y);
    op = reg[3];
    switch (op)
    {
    case FLOAT_ARITHMETIC_Addition:
        result = x + y;
        break;
    case FLOAT_ARITHMETIC_Subtraction:
        result = x - y;
        break;
    case FLOAT_ARITHMETIC_Multiplication:
        result = x * y;
        break;
    case FLOAT_ARITHMETIC_Division:
        result = (y != 0.0) ? (x / y) : 0.0;
        break;
    case FLOAT_ARITHMETIC_Average:
        result = 0.5 * (x + y);
        break;
    }
    WRITE_REG(reg[2], result);
    return STATUS_OK;
}

int r_get_scope_trace(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    getScopeTrace();
    return STATUS_OK;
}

int r_release_scope_trace(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    releaseScopeTrace();
    return STATUS_OK;
}

int r_fanCntrlInit(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return fanCntrlInit();
}

int r_fanCntrlStep(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return fanCntrlStep();
}

int r_activateFan(unsigned int numInt, void *params, void *env)
{
    unsigned int state;
    unsigned int *reg = (unsigned int *)params;
    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], state);
    setFan((FAN_CNTRL_StateType)state);
    return STATUS_OK;
}

int r_peakDetectCntrlInit(unsigned int numInt, void *params, void *env)
/* Initialize the peak detection controller, passing it the index of a
   processed loss register which is to be used to trigger the peak detection */
{
    unsigned int *reg = (unsigned int *)params;
    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return peakDetectCntrlInit(reg[0]);
}

int r_peakDetectCntrlStep(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return peakDetectCntrlStep();
}

int r_read_flow_sensor(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    float slope, offset, result;
    if (4 != numInt)
        return ERROR_BAD_NUM_PARAMS;

    result = read_flow_sensor(reg[0]);
    READ_REG(reg[1], slope);
    READ_REG(reg[2], offset);
    WRITE_REG(reg[3], slope * result + offset);

    return STATUS_OK;
}

// The following actions are for interacting with the variable gain ring down detector

int r_rdd_cntrl_init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return rddCntrlInit();
}

int r_rdd_cntrl_step(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return rddCntrlStep();
}

int r_rdd_cntrl_do_command(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return rddCntrlDoCommand(reg[0]);
}

// The following actions are for interacting with the variable gain ring down detector 2

int r_rdd2_cntrl_init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return rdd2CntrlInit();
}

int r_rdd2_cntrl_step(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return rdd2CntrlStep();
}

int r_rdd2_cntrl_do_command(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return rdd2CntrlDoCommand(reg[0]);
}

int r_batt_mon_read_regs(unsigned int numInt, void *params, void *env)
/* Read the following from the battery monitor:
    Status: into DSP register reg[0]
    Accumulated charge: into DSP register reg[1]
    Voltage: into DSP register reg[2]
    Current: into DSP register reg[3]
    Temperature: into DSP register reg[4] */
{
    int status;
    Uint8 reply[2] = {0, 0};
    unsigned int *reg = (unsigned int *)params;
    double r_sense = 0.018; // Sense resistor value
    if (5 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    if (0 > (status = i2c_register_read(BATTERY_MONITOR, 0x0, reply, 1)))
        return status;
    WRITE_REG(reg[0], reply[0]);
    if (0 > (status = i2c_register_read(BATTERY_MONITOR, 0x2, reply, 2)))
        return status;
    WRITE_REG(reg[1], (0.340 * 3.6 * 0.05 / r_sense) * (256 * reply[0] + reply[1])); // in Coulombs
    if (0 > (status = i2c_register_read(BATTERY_MONITOR, 0x8, reply, 2)))
        return status;
    WRITE_REG(reg[2], (23.6 / 65535.0) * (256 * reply[0] + reply[1])); // in Volts
    if (0 > (status = i2c_register_read(BATTERY_MONITOR, 0xE, reply, 2)))
        return status;
    WRITE_REG(reg[3], (0.06 / (32767.0 * r_sense)) * (256 * reply[0] + reply[1] - 32767));
    if (0 > (status = i2c_register_read(BATTERY_MONITOR, 0x14, reply, 2)))
        return status;
    WRITE_REG(reg[4], (510.0 / 65535.0) * (256 * reply[0] + reply[1]) - 273.15);
    return 0;
}

int r_batt_mon_write_byte(unsigned int numInt, void *params, void *env)
/* Write a byte (params[1]) into the specified (params[0]) battery monitor register */
{
    unsigned int *reg = (unsigned int *)params;
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return i2c_register_write(BATTERY_MONITOR, reg[0], (Uint8 *)(&reg[1]), 1);
}
int r_acc_read_reg(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return accel_read_reg(ACCELEROMETER, reg[0]);
}

int r_acc_write_reg(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return accel_write_reg(ACCELEROMETER, reg[0], reg[1]);
}

int r_acc_read_accel(unsigned int numInt, void *params, void *env)
{
    float ax, ay, az;
    float acc_sensitivity = 0.03831; // m/s^2 per digitizer unit
    short int ax_raw, ay_raw, az_raw;
    unsigned int *reg = (unsigned int *)params;
    int status;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = accel_read_accel(ACCELEROMETER, &ax_raw, &ay_raw, &az_raw);
    ax = ax_raw * acc_sensitivity;
    ay = ay_raw * acc_sensitivity;
    az = az_raw * acc_sensitivity;
    WRITE_REG(reg[0], ax);
    WRITE_REG(reg[1], ay);
    WRITE_REG(reg[2], az);
    return status;
}

int r_average_float_registers(unsigned int numInt, void *params, void *env)
{
    int i;
    unsigned int *reg = (unsigned int *)params;
    float x, sum = 0.0;
    // numInt is the number of registers to average + 1, since the destination
    // register is specified last
    if (2 > numInt)
        return ERROR_BAD_NUM_PARAMS;
    for (i = 0; i < numInt - 1; i++)
    {
        READ_REG(reg[i], x);
        sum += x;
    }
    WRITE_REG(reg[numInt - 1], sum / (numInt - 1));
    return STATUS_OK;
}

int r_action_sgdbr_program_fpga(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    if (1 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    sgdbrProgramFpga(reg[0]);
    return STATUS_OK;
}

int r_sgdbr_a_set_currents(unsigned int numInt, void *params, void *env)
{
    // Use the values passed in to set the front mirror, back mirror, coarse phase and fine phase
    //  currents (in digitizer units) of the SGDBR_A laser. We set values in both the DAS register 
    //  and the FPGA registers.
    unsigned int *reg = (unsigned int *)params;
    if (4 != numInt) return ERROR_BAD_NUM_PARAMS;
    WRITE_REG(SGDBR_A_CNTRL_FRONT_MIRROR_REGISTER, (reg[0] & 0xFFFF));
    WRITE_REG(SGDBR_A_CNTRL_BACK_MIRROR_REGISTER, (reg[1] & 0xFFFF));
    WRITE_REG(SGDBR_A_CNTRL_COARSE_PHASE_REGISTER, (reg[2] & 0xFFFF));
    WRITE_REG(SGDBR_A_CNTRL_FINE_PHASE_REGISTER, (reg[3] & 0xFFFF));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_FRONT_MIRROR_DAC | (reg[0] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_BACK_MIRROR_DAC | (reg[1] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_COARSE_PHASE_DAC | (reg[2] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_FINE_PHASE_DAC | (reg[3] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_A + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    return STATUS_OK;
}

int r_sgdbr_b_set_currents(unsigned int numInt, void *params, void *env)
{
    // Use the values passed in to set the front mirror, back mirror, coarse phase and fine phase
    //  currents (in digitizer units) of the SGDBR_B laser. We set values in both the DAS register 
    //  and the FPGA registers.
    unsigned int *reg = (unsigned int *)params;
    if (4 != numInt) return ERROR_BAD_NUM_PARAMS;
    WRITE_REG(SGDBR_B_CNTRL_FRONT_MIRROR_REGISTER, (reg[0] & 0xFFFF));
    WRITE_REG(SGDBR_B_CNTRL_BACK_MIRROR_REGISTER, (reg[1] & 0xFFFF));
    WRITE_REG(SGDBR_B_CNTRL_COARSE_PHASE_REGISTER, (reg[2] & 0xFFFF));
    WRITE_REG(SGDBR_B_CNTRL_FINE_PHASE_REGISTER, (reg[3] & 0xFFFF));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_FRONT_MIRROR_DAC | (reg[0] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_BACK_MIRROR_DAC | (reg[1] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_COARSE_PHASE_DAC | (reg[2] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_FINE_PHASE_DAC | (reg[3] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_B + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    return STATUS_OK;
}

int r_sgdbr_c_set_currents(unsigned int numInt, void *params, void *env)
{
    // Use the values passed in to set the front mirror, back mirror, coarse phase and fine phase
    //  currents (in digitizer units) of the SGDBR_C laser. We set values in both the DAS register 
    //  and the FPGA registers.
    unsigned int *reg = (unsigned int *)params;
    if (4 != numInt) return ERROR_BAD_NUM_PARAMS;
    WRITE_REG(SGDBR_C_CNTRL_FRONT_MIRROR_REGISTER, (reg[0] & 0xFFFF));
    WRITE_REG(SGDBR_C_CNTRL_BACK_MIRROR_REGISTER, (reg[1] & 0xFFFF));
    WRITE_REG(SGDBR_C_CNTRL_COARSE_PHASE_REGISTER, (reg[2] & 0xFFFF));
    WRITE_REG(SGDBR_C_CNTRL_FINE_PHASE_REGISTER, (reg[3] & 0xFFFF));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_FRONT_MIRROR_DAC | (reg[0] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_BACK_MIRROR_DAC | (reg[1] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_COARSE_PHASE_DAC | (reg[2] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_FINE_PHASE_DAC | (reg[3] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_C + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    return STATUS_OK;
}

int r_sgdbr_d_set_currents(unsigned int numInt, void *params, void *env)
{
    // Use the values passed in to set the front mirror, back mirror, coarse phase and fine phase
    //  currents (in digitizer units) of the SGDBR_C laser. We set values in both the DAS register 
    //  and the FPGA registers.
    unsigned int *reg = (unsigned int *)params;
    if (4 != numInt) return ERROR_BAD_NUM_PARAMS;
    WRITE_REG(SGDBR_D_CNTRL_FRONT_MIRROR_REGISTER, (reg[0] & 0xFFFF));
    WRITE_REG(SGDBR_D_CNTRL_BACK_MIRROR_REGISTER, (reg[1] & 0xFFFF));
    WRITE_REG(SGDBR_D_CNTRL_COARSE_PHASE_REGISTER, (reg[2] & 0xFFFF));
    WRITE_REG(SGDBR_D_CNTRL_FINE_PHASE_REGISTER, (reg[3] & 0xFFFF));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_FRONT_MIRROR_DAC | (reg[0] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_BACK_MIRROR_DAC | (reg[1] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_COARSE_PHASE_DAC | (reg[2] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    writeFPGA(FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_MOSI_DATA, SGDBR_FINE_PHASE_DAC | (reg[3] & 0xFFFF));
    while (0 == (readFPGA(FPGA_SGDBRCURRENTSOURCE_D + SGDBRCURRENTSOURCE_CSR) & (1 << SGDBRCURRENTSOURCE_CSR_DONE_B)));
    return STATUS_OK;
}

int r_tempCntrlFilterHeaterInit(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlFilterHeaterInit();
}

int r_tempCntrlFilterHeaterStep(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlFilterHeaterStep();
}

int r_soa_cntrl_soa1_init(unsigned int numInt, void *params, void *env)
/* Initialize SOA controller for SOA Board 1 (A1:A0 = 00)
    Input:
        i2c_current_ident (int):  Index of I2C device for digital potentiometer which sets SOA current
        i2c_control_ident (int):  Index of I2C device for parallel port which disables SOA current source
        i2c_tec_ident (int):  Index of I2C device for DAC which sets TEC controller temperature setpoint for SOA 
        i2c_monitor_ident (int):  Index of I2C device for ADC which monitors TEC voltage, current and SOA temperature 
*/
{
    unsigned int *reg = (unsigned int *)params;
    if (5 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return soa_cntrl_soa1_init(reg[0], reg[1], reg[2], reg[3], reg[4]);
}

int r_soa_cntrl_soa1_step(unsigned int numInt, void *params, void *env)
{
    return soa_cntrl_soa1_step();
}

int r_soa_cntrl_soa2_init(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    if (5 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return soa_cntrl_soa2_init(reg[0], reg[1], reg[2], reg[3], reg[4]);
}

int r_soa_cntrl_soa2_step(unsigned int numInt, void *params, void *env)
{
    return soa_cntrl_soa2_step();
}

int r_soa_cntrl_soa3_init(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    if (5 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return soa_cntrl_soa3_init(reg[0], reg[1], reg[2], reg[3], reg[4]);
}

int r_soa_cntrl_soa3_step(unsigned int numInt, void *params, void *env)
{
    return soa_cntrl_soa3_step();
}

int r_soa_cntrl_soa4_init(unsigned int numInt, void *params, void *env)
{
    unsigned int *reg = (unsigned int *)params;
    if (5 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return soa_cntrl_soa4_init(reg[0], reg[1], reg[2], reg[3], reg[4]);
}

int r_soa_cntrl_soa4_step(unsigned int numInt, void *params, void *env)
{
    return soa_cntrl_soa4_step();
}

int r_read_soa_monitor(unsigned int numInt, void *params, void *env)
/*
    Reads SOA monitor ADC of specified SOA
    Input:
        i2c_index (int):  Index of I2C device for LTC2493 quad ADC
        adc_index (int):  ADC channel to read (0 = voltage, 1 = current, 2 = temperature)
    Output:
        Register (float): Register to receive result
*/
{
    unsigned int *reg = (unsigned int *)params;
    int status;
    float result;
    float Vref, Vcom;
	Vref = 2.5;
	Vcom = 1.25;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    result = ltc2493se_read(reg[0], reg[1], &status) / 33554432.0;
    if (status != 0) return status;
    if (result < 0.0 || result > 1.0)
        return ERROR_BAD_VALUE;    
    WRITE_REG(reg[2], Vcom + Vref*(result - 0.5));
    return STATUS_OK;
}

int r_set_soa_current(unsigned int numInt, void *params, void *env)
/*
    Set digital potentiometer for SOA current
    Input:
        i2c_index (int):  Index of I2C device for AD5248 digital potentiomenter
        channel (int):  Which digital potentiomater to set (0-1)
        value (int):  Value to set on digital potentiomater (0-255)
*/
{
    unsigned int *reg = (unsigned int *)params;
    if (3 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    ad5248_write(reg[0], reg[1], reg[2]);
    return STATUS_OK;
}

int r_set_soa_temperature(unsigned int numInt, void *params, void *env)
/*
    Set DAC controlling SOA temperature
    Input:
        i2c_index (int):  Index of I2C device for LTC2606 DAC
        value (int): Value to write to control register
*/
{
    unsigned int *reg = (unsigned int *)params;
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;

    ltc2606_write(reg[0], reg[1]);
    return STATUS_OK;
}

int r_set_soa_control(unsigned int numInt, void *params, void *env)
/*
    Set parallel port for controlling SOA
    Input:
        i2c_index (int):  Index of I2C device for PCF8574 I/O expander
        value (int): Value to write to control register
*/
{
    unsigned int *reg = (unsigned int *)params;
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;

    pca8574_write(reg[0], reg[1]);
    return STATUS_OK;
}

int r_set_soa_tec(unsigned int numInt, void *params, void *env)
/*
    Set SOA TEC value from a floating point DAS register by converting it to an integer between 0-65535
    and writing it to the I2C based DAC (LTC2606).

    Inputs:
        i2c_index (int): Index of I2C device for LTC2606 DAC
        Register(float): Index of DAS register containing value to send
         
*/
{
    float value;
    unsigned int *reg = (unsigned int *)params;
    if (2 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[1], value);
    ltc2606_write(reg[0], (int) value);
    return STATUS_OK;
}

int r_tempCntrlSoa1Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlSoa1Init();
}

int r_tempCntrlSoa1Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlSoa1Step();
    return status;
}

int r_tempCntrlSoa2Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlSoa2Init();
}

int r_tempCntrlSoa2Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlSoa2Step();
    return status;
}

int r_tempCntrlSoa3Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlSoa3Init();
}

int r_tempCntrlSoa3Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlSoa3Step();
    return status;
}

int r_tempCntrlSoa4Init(unsigned int numInt, void *params, void *env)
{
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    return tempCntrlSoa4Init();
}

int r_tempCntrlSoa4Step(unsigned int numInt, void *params, void *env)
{
    int status;
    if (0 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlSoa4Step();
    return status;
}

int r_convertSoaTecCurrent(unsigned int numInt, void *params, void *env)
/*
    Inputs:
        Register (float): Index of DAS register with digU->current conversion slope
        Register (float): Index of DAS register with digU->current conversion offset
        Register (float): Index of DAS register with TEC digitizer units
    Output:
        Register (float): Index of DAS register with TEC current
  ls       
*/
{
    float slope, offset, digU, current;
    unsigned int *reg = (unsigned int *)params;
    if (4 != numInt)
        return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0], slope);
    READ_REG(reg[1], offset);
    READ_REG(reg[2], digU);
    current = slope * digU + offset;
    WRITE_REG(reg[3], current);
    return STATUS_OK;
}
