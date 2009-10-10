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

#include "dspAutogen.h"
#include "interface.h"
#include "misc.h"
#include "pid.h"
#include "registers.h"
#include "scheduler.h"
#include "sentryHandler.h"
#include "spectrumCntrl.h"
#include "tempCntrl.h"
#include "laserCurrentCntrl.h"
#include "heaterCntrl.h"
#include "tunerCntrl.h"
#include "valveCntrl.h"
#include "i2c_dsp.h"
#include "ds1631.h"
#include "ltc2451.h"
#include "ltc2499.h"
#include "fpga.h"

char message[120];

#define READ_REG(regNum,result) { \
	DataType d; \
    int status = readRegister((regNum),&d);\
    if (STATUS_OK != status) return status; \
    switch (getRegisterType(regNum)) { \
        case float_type: \
            (result) = d.asFloat; \
            break; \
        case uint_type: \
            (result) = d.asUint; \
            break; \
        case int_type: \
            (result) = d.asInt; \
            break; \
    } \
}

#define WRITE_REG(regNum,result) { \
	DataType d; \
	int status; \
    switch (getRegisterType(regNum)) { \
		case float_type: \
			d.asFloat = (result); \
			break; \
		case uint_type: \
			d.asUint = (result); \
			break; \
		case int_type: \
			d.asInt = (result); \
			break; \
	} \
    status = writeRegister((regNum),d); \
    if (STATUS_OK != status) return status; \
}

int writeBlock(unsigned int numInt,void *params,void *env)
// Writes a block to the communication area. The number of integers written is numInt-1, since params[0] is the start index
// The indices lie in various "areas", defined by the OFFSET
{
    unsigned int offset = *(unsigned int*)params;
    unsigned int *data = ((unsigned int*)params) + 1;
    // printf("WriteBlock: numInt = %d, offset = %d\n", numInt, offset);

    numInt -= 1;
    if (offset+numInt > SHAREDMEM_SIZE) return ERROR_OUTSIDE_SHAREDMEM;
    else memcpy((void*)(SHAREDMEM_BASE+4*offset),data,4*numInt);
#if EXT_MEM
    CACHE_wbL2((void *)(SHAREDMEM_BASE+4*offset),4*numInt, CACHE_WAIT);
#endif
    return STATUS_OK;
}

int initRunqueue(unsigned int numInt,void *params,void *env)
// Load up the scheduler runqueue based on the operation groups defined.
//  Required parameter is the number of groups.
{
    unsigned int *paramsAsInt = (unsigned int *) params;
    unsigned int i, nGroups;
    long long now;
    if (1 != numInt) return ERROR_BAD_NUM_PARAMS;
    get_timestamp(&now);
    nGroups = paramsAsInt[0];
    for (i=0;i<nGroups;i++)
    {
        int period = get_group_period(i);
        long long next_time = ((now + period)/period )*period;
        insert_into_runqueue(i,next_time);
    }
    return STATUS_OK;
}

int testScheduler(unsigned int numInt,void *params,void *env)
// This action simply sends back its parameters via message_puts in order to help
//  test the operation of the scheduler.
{
    unsigned int i;
    unsigned int *paramsAsInt = (unsigned int *) params;
    strcpy(message,"testScheduler");
    for (i=0;i<numInt;i++)
    {
        sprintf(message+strlen(message)," %d",paramsAsInt[i]);
    }
    message_puts(message);
    return STATUS_OK;
}

int streamRegisterAsFloat(unsigned int numInt,void *params,void *env)
// This action streams the value of a register. The first parameter
//  is the stream number and the second is the register number. Note
//  that the type of data on the stream is the same as the type of the
//  register
{
    unsigned int *paramsAsInt = (unsigned int *) params;
    unsigned int streamNum;
    float value;
    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;
    streamNum = paramsAsInt[0];
    READ_REG(paramsAsInt[1],value);
    sensor_put_from(streamNum,value);
    return STATUS_OK;
}

int streamFpgaRegisterAsFloat(unsigned int numInt,void *params,void *env)
// This action streams the value of an FPGA register. The first parameter
//  is the stream number, the second is the location in the FPGA map
//  and the third is the register number
{
    unsigned int *paramsAsInt = (unsigned int *) params;
    unsigned int fpgaBase, regNum, streamNum;
    float value;
    if (3 != numInt) return ERROR_BAD_NUM_PARAMS;
    streamNum = paramsAsInt[0];
    fpgaBase = paramsAsInt[1];
    regNum = paramsAsInt[2];
    value = readFPGA(fpgaBase + regNum);
    sensor_put_from(streamNum,value);
    return STATUS_OK;
}

int setTimestamp(unsigned int numInt,void *params,void *env)
// Writes a 64 bit timestamp to the instrument. params[0] is the
//  least significant 32 bits and params[1]
{
    unsigned int *paramsAsInt = (unsigned int *) params;
    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;
    timestamp = paramsAsInt[0] + (((long long)paramsAsInt[1])<<32);
    return STATUS_OK;
}

int r_getTimestamp(unsigned int numInt,void *params,void *env)
// Read the 64 bit timestamp into two registers, the LS 32 bits into
//  the first and the MS 32 bits into the second
{
    unsigned int *reg = (unsigned int *) params;
    long long ts = timestamp;
    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;
    WRITE_REG(reg[0],(uint32)(ts & 0xFFFFFFFF));
    WRITE_REG(reg[1],(uint32)(ts >> 32));
    return STATUS_OK;
}

int r_wbCache(unsigned int numInt,void *params,void *env)
/* Write back cache for a region of memory
   Input:
        addr(int):      address to region
        length(int):    length of region in bytes
*/
{
    unsigned int *reg = (unsigned int *) params;
    CACHE_wbL2((void *)reg[0], reg[1], CACHE_WAIT);
    return STATUS_OK;
}

int r_wbInvCache(unsigned int numInt,void *params,void *env)
/* Write back and invalidate cache fors a region of memory
   Input:
        addr(int):      address to region
        length(int):    length of region in bytes
*/
{
    unsigned int *reg = (unsigned int *) params;
    CACHE_wbInvL2((void *)reg[0], reg[1], CACHE_WAIT);
    return STATUS_OK;
}

int r_resistanceToTemperature(unsigned int numInt,void *params,void *env)
{
    float resistance, constA, constB, constC, result;
    int status;

    unsigned int *reg = (unsigned int *) params;
    if (5 != numInt) return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0],resistance);
    READ_REG(reg[1],constA);
    READ_REG(reg[2],constB);
    READ_REG(reg[3],constC);
    status = resistanceToTemperature(resistance,constA,constB,constC,&result);
    WRITE_REG(reg[4],result);
    return status;
}

int r_tempCntrlSetCommand(unsigned int numInt,void *params,void *env)
{
    return STATUS_OK;
}

int r_applyPidStep(unsigned int numInt,void *params,void *env)
{
    return STATUS_OK;
}

int r_tempCntrlLaser1Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser1Init();
}

int r_tempCntrlLaser1Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser1Step();
    return status;
}

int r_tempCntrlLaser2Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser2Init();
}

int r_tempCntrlLaser2Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser2Step();
    return status;
}

int r_tempCntrlLaser3Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser3Init();
}

int r_tempCntrlLaser3Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser3Step();
    return status;
}

int r_tempCntrlLaser4Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser4Init();
}

int r_tempCntrlLaser4Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser4Step();
    return status;
}

int r_floatRegisterToFpga(unsigned int numInt,void *params,void *env)
/* Copy contents of a floating point register to an FPGA register,
    treating value as an unsigned int. The FPGA register is the sum
    of two arguments so that we can pass a block base and an offset within
    the block. */
{
    float value;
    unsigned int *reg = (unsigned int *) params;
    if (3 != numInt) return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0],value);
    writeFPGA(reg[1]+reg[2],(unsigned int)value);
    return STATUS_OK;
}

int r_fpgaToFloatRegister(unsigned int numInt,void *params,void *env)
/* Copy contents of an FPGA register to a floating point register,
    treating value as an unsigned short. The FPGA register is the sum
    of two arguments so that we can pass a block base and an offset within
    the block. */
{
    float value;
    unsigned int *reg = (unsigned int *) params;
    if (3 != numInt) return ERROR_BAD_NUM_PARAMS;
    value = readFPGA(reg[0]+reg[1]);
    WRITE_REG(reg[2],value);
    return STATUS_OK;
}

int r_intToFpga(unsigned int numInt,void *params,void *env)
/* Copy integer (passed as first parameter) to the specified FPGA register.
    The FPGA register is the sum of two arguments so that we can pass a
    block base and an offset within the block. */
{
    unsigned int *reg = (unsigned int *) params;
    if (3 != numInt) return ERROR_BAD_NUM_PARAMS;
    writeFPGA(reg[1]+reg[2],reg[0]);
    return STATUS_OK;
}

int r_currentCntrlLaser1Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return currentCntrlLaser1Init();
}

int r_currentCntrlLaser1Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = currentCntrlLaser1Step();
    return status;
}

int r_currentCntrlLaser2Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return currentCntrlLaser2Init();
}

int r_currentCntrlLaser2Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = currentCntrlLaser2Step();
    return status;
}

int r_currentCntrlLaser3Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return currentCntrlLaser3Init();
}

int r_currentCntrlLaser3Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = currentCntrlLaser3Step();
    return status;
}

int r_currentCntrlLaser4Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return currentCntrlLaser4Init();
}

int r_currentCntrlLaser4Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = currentCntrlLaser4Step();
    return status;
}

int r_tempCntrlWarmBoxInit(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlWarmBoxInit();
}

int r_tempCntrlWarmBoxStep(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlWarmBoxStep();
    return status;
}

int r_tempCntrlCavityInit(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlCavityInit();
}

int r_tempCntrlCavityStep(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlCavityStep();
    return status;
}

int r_heaterCntrlInit(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return heaterCntrlInit();
}

int r_heaterCntrlStep(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = heaterCntrlStep();
    return status;
}

int r_tunerCntrlInit(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tunerCntrlInit();
}

int r_tunerCntrlStep(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tunerCntrlStep();
    return status;
}

int r_spectCntrlInit(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return spectCntrlInit();
}

int r_spectCntrlStep(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = spectCntrlStep();
    return status;
}

int r_valveCntrlInit(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return valveCntrlInit();
}

int r_valveCntrlStep(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = valveCntrlStep();
    return status;
}


int r_envChecker(unsigned int numInt,void *params,void *env)
// This action tests the use of the environment pointer
{
    static char message[120];
    CheckEnvType *myEnv = (CheckEnvType *) env;
    sprintf(message,"envChecker: %5d %5d",myEnv->var1,myEnv->var2);
    myEnv->var1 += 1;
    myEnv->var2 += 2;
    message_puts(message);
    return STATUS_OK;
}

int r_pulseGenerator(unsigned int numInt,void *params,void *env)
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
    unsigned int *reg = (unsigned int *) params;
    if (3 != numInt) return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0],lowDuration);
    READ_REG(reg[1],highDuration);
    status = pulseGenerator(lowDuration,highDuration,&result,
                            (PulseGenEnvType *)env);
    WRITE_REG(reg[2],result);
    return status;
}

int r_filter(unsigned int numInt,void *params,void *env)
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

    unsigned int *reg = (unsigned int *) params;
    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0],x);
    status = filter(x,&y,(FilterEnvType *)env);
    WRITE_REG(reg[1],y);
    return status;
}

int r_ds1631_readTemp(unsigned int numInt,void *params,void *env)
/* Read DS1631 temprature */
{
    unsigned int *reg = (unsigned int *) params;
    if (1 != numInt) return ERROR_BAD_NUM_PARAMS;
    WRITE_REG(reg[0],ds1631_readTemperatureAsFloat());
    return STATUS_OK;
}

int r_laser_tec_imon(unsigned int numInt,void *params,void *env)
/*
    Reads and sets up next read of the laser TEC current monitor
    Input:
        Code (int):  256*next channel + desired channel
    Output:
        Register (float):  Register to receive value. Unchanged
         if the desired channel is unavailable
*/
{
    unsigned int *reg = (unsigned int *) params;
    int desired, next, status;
    float result;

    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;
    desired = reg[0] & 0xFF;
    next = (reg[0]>>8) & 0xFF;
    status = read_laser_tec_imon(desired,next,&result);
    if (STATUS_OK == status) WRITE_REG(reg[1],result);
    return status;
}

int r_read_laser_tec_monitors(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    read_laser_tec_monitors();
    return STATUS_OK;
}

int r_read_laser_thermistor_resistance(unsigned int numInt,void *params,void *env)
{
    unsigned int *reg = (unsigned int *) params;
    float result;
    float Vfrac, Rseries = 30000.0;
    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;
    result = read_laser_thermistor_adc(reg[0]);
    Vfrac = result/33554432.0;
    if (Vfrac<=0.0 || Vfrac>=1.0) return ERROR_BAD_VALUE;
    WRITE_REG(reg[1],(Rseries*Vfrac)/(1.0-Vfrac));
    return STATUS_OK;
}

int r_read_etalon_thermistor_resistance(unsigned int numInt,void *params,void *env)
{
    unsigned int *reg = (unsigned int *) params;
    float result;
    float Vfrac, Rseries = 30000.0;
    if (1 != numInt) return ERROR_BAD_NUM_PARAMS;
    result = read_etalon_thermistor_adc();
    Vfrac = result/33554432.0;
    if (Vfrac<=0.0 || Vfrac>=1.0) return ERROR_BAD_VALUE;
    WRITE_REG(reg[0],(Rseries*Vfrac)/(1.0-Vfrac));
    return STATUS_OK;
}

int r_read_warm_box_thermistor_resistance(unsigned int numInt,void *params,void *env)
{
    unsigned int *reg = (unsigned int *) params;
    float result;
    float Vfrac, Rseries = 30000.0;
    if (1 != numInt) return ERROR_BAD_NUM_PARAMS;
    result = read_warm_box_thermistor_adc();
    Vfrac = result/33554432.0;
    if (Vfrac<=0.0 || Vfrac>=1.0) return ERROR_BAD_VALUE;
    WRITE_REG(reg[0],(Rseries*Vfrac)/(1.0-Vfrac));
    return STATUS_OK;
}

int r_read_warm_box_heatsink_thermistor_resistance(unsigned int numInt,void *params,void *env)
{
    unsigned int *reg = (unsigned int *) params;
    float result;
    float Vfrac, Rseries = 30000.0;
    if (1 != numInt) return ERROR_BAD_NUM_PARAMS;
    result = read_warm_box_heatsink_thermistor_adc();
    Vfrac = result/33554432.0;
    if (Vfrac<=0.0 || Vfrac>=1.0) return ERROR_BAD_VALUE;
    WRITE_REG(reg[0],(Rseries*Vfrac)/(1.0-Vfrac));
    return STATUS_OK;
}

int r_read_laser_current(unsigned int numInt,void *params,void *env)
/*
    Reads laser current monitor of specified laser
    Input:
        laserNum (int)  :  Laser number to read (1-origin)
        Register (float): Register containing conversion slope
        Register (float): Register containing conversion offset
    Output:
        Register (float):  Register to receive current reading
*/
{
    unsigned int *reg = (unsigned int *) params;
    float slope, offset, result;
    if (4 != numInt) return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[1],slope);
    READ_REG(reg[2],offset);
    result = read_laser_current_adc(reg[0])*slope + offset;
    WRITE_REG(reg[3],result);
    return STATUS_OK;
}

int r_schedulerHeartbeat(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    schedulerAlive++;
    return STATUS_OK;
}

int r_sentryInit(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    initSentryChecks();
    return STATUS_OK;
}

int r_modifyValvePumpTec(unsigned int numInt,void *params,void *env)
/* Modify the valve, pump and TEC states by using the first parameter as a mask
    and the second value as the bits to set within the mask */
{
    unsigned int *reg = (unsigned int *) params;

    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;
    modify_valve_pump_tec(reg[0],reg[1]);
    return STATUS_OK;
}

int r_update_wlmsim_laser_temp(unsigned int numInt,void *params,void *env)
/* Write the temperature of the currently selected laser to the WLM simulator register */
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    update_wlmsim_laser_temp();
    return STATUS_OK;
}

int r_simulate_laser_current_reading(unsigned int numInt,void *params,void *env)
/* For the specified laser number (1-origin), place the simulated laser current reading (obtained
    by combining coarse and fine laser contributions) into the specified register.  The scaling is
    360nA/fine_current unit, and 10 fine_current units = 1 coarse_current unit. */
{
    unsigned int *reg = (unsigned int *) params;
    unsigned int dac = 0;
    float current;

    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;

    switch (reg[0])
    {
    case 1:
        dac = 10*readFPGA(FPGA_INJECT+INJECT_LASER1_COARSE_CURRENT) + readFPGA(FPGA_INJECT+INJECT_LASER1_FINE_CURRENT);
        break;
    case 2:
        dac = 10*readFPGA(FPGA_INJECT+INJECT_LASER2_COARSE_CURRENT) + readFPGA(FPGA_INJECT+INJECT_LASER2_FINE_CURRENT);
        break;
    case 3:
        dac = 10*readFPGA(FPGA_INJECT+INJECT_LASER3_COARSE_CURRENT) + readFPGA(FPGA_INJECT+INJECT_LASER3_FINE_CURRENT);
        break;
    case 4:
        dac = 10*readFPGA(FPGA_INJECT+INJECT_LASER4_COARSE_CURRENT) + readFPGA(FPGA_INJECT+INJECT_LASER4_FINE_CURRENT);
        break;
    }
    current = 0.00036*dac;
    WRITE_REG(reg[1],current);
    return STATUS_OK;
}
