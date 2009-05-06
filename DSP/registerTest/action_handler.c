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

#include <stdio.h>
#include <string.h>

#include "dspAutogen.h"
#include "interface.h"
#include "misc.h"
#include "pid.h"
#include "registers.h"
#include "scheduler.h"
#include "tempCntrl.h"
#include "laserCurrentCntrl.h"
#include "heaterCntrl.h"

#define READ_REG(regNum,type,result) { \
    DataType d; \
    int status = readRegister(regNum,&d);\
    if (STATUS_OK != status) return status; \
    result = d.type; \
    }

#define WRITE_REG(regNum,type,result) { \
    DataType d; \
    int status; \
    d.type = result; \
    status = writeRegister(regNum,d);\
    if (STATUS_OK != status) return status; \
    }

#ifdef SIMULATION
    #pragma argsused
#endif
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
#ifdef SIMULATION
    #pragma argsused
#endif
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
    for (i=0;i<nGroups;i++) {
        int period = get_group_period(i);
        long long next_time = ((now + period)/period )*period;
        insert_into_runqueue(i,next_time);
    }
    return STATUS_OK;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int testScheduler(unsigned int numInt,void *params,void *env)
// This action simply sends back its parameters via message_puts in order to help
//  test the operation of the scheduler.
{
    unsigned int i;
    char message[120];
    unsigned int *paramsAsInt = (unsigned int *) params;
    strcpy(message,"testScheduler");
    for (i=0;i<numInt;i++) {
        sprintf(message+strlen(message)," %d",paramsAsInt[i]);
    }
    message_puts(message);
    return STATUS_OK;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int streamRegister(unsigned int numInt,void *params,void *env)
// This action streams the value of a register. The first parameter
//  is the stream number and the second is the register number.
{
    unsigned int *paramsAsInt = (unsigned int *) params;
    unsigned int streamNum, value;
    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;
    streamNum = paramsAsInt[0];
    READ_REG(paramsAsInt[1],asUint,value);
    sensor_put_from(streamNum,&value);
    return STATUS_OK;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int setTimestamp(unsigned int numInt,void *params,void *env)
// Writes a 64 bit timestamp to the instrument. params[0] is the
//  least significant 32 bits and params[1]
{
	  unsigned int *paramsAsInt = (unsigned int *) params;
    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;
    timestamp = paramsAsInt[0] + (((long long)paramsAsInt[1])<<32);
    return STATUS_OK;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_getTimestamp(unsigned int numInt,void *params,void *env)
// Read the 64 bit timestamp into two registers, the LS 32 bits into
//  the first and the MS 32 bits into the second
{
    unsigned int *reg = (unsigned int *) params;
    long long ts = timestamp;
    if (2 != numInt) return ERROR_BAD_NUM_PARAMS;
    WRITE_REG(reg[0],asUint,(uint32)(ts & 0xFFFFFFFF));
    WRITE_REG(reg[1],asUint,(uint32)(ts >> 32));
    return STATUS_OK;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_resistanceToTemperature(unsigned int numInt,void *params,void *env)
{
    float resistance, constA, constB, constC, result;
    int status;

    unsigned int *reg = (unsigned int *) params;
    if (5 != numInt) return ERROR_BAD_NUM_PARAMS;
    READ_REG(reg[0],asFloat,resistance);
    READ_REG(reg[1],asFloat,constA);
    READ_REG(reg[2],asFloat,constB);
    READ_REG(reg[3],asFloat,constC);
    status = resistanceToTemperature(resistance,constA,constB,constC,&result);
    WRITE_REG(reg[4],asFloat,result);
    return status;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlSetCommand(unsigned int numInt,void *params,void *env)
{
    return STATUS_OK;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_applyPidStep(unsigned int numInt,void *params,void *env)
{
    return STATUS_OK;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlLaser1Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser1Init();
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlLaser1Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser1Step();
    return status;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlLaser2Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser2Init();
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlLaser2Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser2Step();
    return status;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlLaser3Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser3Init();
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlLaser3Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser3Step();
    return status;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlLaser4Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlLaser4Init();
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlLaser4Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlLaser4Step();
    return status;
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_currentCntrlLaser1Init(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return currentCntrlLaser1Init();
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_currentCntrlLaser1Step(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = currentCntrlLaser1Step();
    return status;
}

#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlCavityInit(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return tempCntrlCavityInit();
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_tempCntrlCavityStep(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = tempCntrlCavityStep();
    return status;
}

#ifdef SIMULATION
    #pragma argsused
#endif
int r_heaterCntrlInit(unsigned int numInt,void *params,void *env)
{
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    return heaterCntrlInit();
}
#ifdef SIMULATION
    #pragma argsused
#endif
int r_heaterCntrlStep(unsigned int numInt,void *params,void *env)
{
    int status;
    if (0 != numInt) return ERROR_BAD_NUM_PARAMS;
    status = heaterCntrlStep();
    return status;
}

#ifdef SIMULATION
    #pragma argsused
#endif
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
#ifdef SIMULATION
    #pragma argsused
#endif
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
    READ_REG(reg[0],asUint,lowDuration);
    READ_REG(reg[1],asUint,highDuration);
    status = pulseGenerator(lowDuration,highDuration,&result,
                            (PulseGenEnvType *)env);
    WRITE_REG(reg[2],asFloat,result);
    return status;
}
#ifdef SIMULATION
    #pragma argsused
#endif
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
    READ_REG(reg[0],asFloat,x);
    status = filter(x,&y,(FilterEnvType *)env);
    WRITE_REG(reg[1],asFloat,y);
    return status;
}
