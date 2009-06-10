/*
 * FILE:
 *   registers.c
 *
 * DESCRIPTION:
 *   Routines to access software registers
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   19-Dec-2008  sze  Initial version.
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */

#ifdef SIMULATION
// Include files for simulation mode
#include "registerTestSim.h"
#include <stdio.h>
#else
#include <std.h>
#include <csl.h>
#include <csl_cache.h>
#include <csl_hpi.h>
#include <csl_i2c.h>
#include <csl_irq.h>
#include <log.h>
#include <prd.h>
#include <sem.h>
#include "registerTestcfg.h"
#endif

#define EXT_MEM 0

#include "crc.h"
#include "dspAutogen.h"
#include "scheduler.h"
#include <string.h>

static unsigned int commStatSeqNum=0;

long long timestamp = 0LL;
/* Fetch the global timestamp value */
void get_timestamp(long long *ts)
{
    *ts = timestamp;
}

Message *messages = (Message *)(MESSAGE_BASE);  // This is an array of size NUM_MESSAGES
static int message_pointer = 0;
SensorEntryType *sensorEntries = (SensorEntryType *)(SENSOR_BASE);  // This is an array of size NUM_SENSOR_ENTRIES
static int sensor_pointer = 0;

void init_comms()
{
    DataType d;
    memset(messages,0,4*MESSAGE_REGION_SIZE);
    message_pointer = 0;
    memset(sensorEntries,0,4*SENSOR_REGION_SIZE);
    sensor_pointer = 0;
    // Initialize the COMM_STATUS register
    commStatSeqNum = 0;
    d.asUint = ((commStatSeqNum<<COMM_STATUS_SequenceNumberShift)&
                COMM_STATUS_SequenceNumberMask)|COMM_STATUS_CompleteMask;
    writeRegister(COMM_STATUS_REGISTER,d);
}

void message_puts(char *message)
{
    long long ts;
    Message *m = messages + message_pointer;
    get_timestamp(&ts);
    m->timestamp = 0LL;
    strncpy(m->message,message,120);
    m->timestamp = ts;
    message_pointer++;
    if (message_pointer>=NUM_MESSAGES) message_pointer = 0;
}

void sensor_put_from(unsigned int streamNum, void *addr)
{
    long long ts;
    SensorEntryType *s = sensorEntries + sensor_pointer;
    get_timestamp(&ts);
    s->streamNum = streamNum;
    s->value.asUint = *(uint32*)addr;
    s->timestamp = ts;
    sensor_pointer++;
    if (sensor_pointer>=NUM_SENSOR_ENTRIES) sensor_pointer = 0;
}

// DSP writes to a register and writes back the cache, to ensure that the data can subsequently be read
//  by the host
int writeRegister(unsigned int regNum,DataType data)
{
    if (regNum >= REG_REGION_SIZE) return ERROR_UNKNOWN_REGISTER;
    else *(int*)(REG_BASE+4*regNum) = data.asInt;
#if EXT_MEM
    CACHE_wbL2((void *)(REG_BASE+4*regNum), 4, CACHE_WAIT);
#endif
    return STATUS_OK;
}

// DSP writes back a block of registers to the cache, so that the data can subsequently be read
//  by the host

#ifdef SIMULATION
#if EXT_MEM
#else
#pragma argsused
#endif
#endif

int writebackRegisters(unsigned int regNums[],unsigned int n)
{
    int status = STATUS_OK;
#if EXT_MEM
    int i;
    for (i=0; i<n; i++)
    {
        if (regNums[i] >= REG_REGION_SIZE) status = ERROR_UNKNOWN_REGISTER;
        else CACHE_wbL2((void *)(REG_BASE+4*regNums[i]), 4, CACHE_WAIT);
    }
#endif
    return status;
}

int readRegister(unsigned int regNum, DataType *data)
{
    if (regNum >= REG_REGION_SIZE) return ERROR_UNKNOWN_REGISTER;
    else data->asInt = *(int*)(REG_BASE+4*regNum);
    return STATUS_OK;
}

void *registerAddr(unsigned int regNum)
/* Returns pointer to the specified register index for direct read-access by DSP.
   Pointer should be non-null, and cast to the appropriate type as required */
{
    if (regNum >= REG_REGION_SIZE) return 0;
    return (void*)(REG_BASE+4*regNum);
}

#ifdef SIMULATION
#pragma argsused
#endif
void hwiHpiInterrupt(unsigned int funcArg, unsigned int eventId)
{
    // Responds to the DSPINT interrupt, which is a signal that the host wants
    //  the DSP to process a command in the message area starting at HOST_BASE
    unsigned int gie, seqNum, numInt, command, crc, envAddr;
    int retVal;
    HostWriteArea *host;
    DataType d;

    gie = IRQ_globalDisable();

    d.asUint = 0xAAAAAAAA; // Code to indicate interrupt handler was called
    writeRegister(COMM_STATUS_REGISTER,d);

    // First read the 32bits at HOST_BASE in the HostWriteArea. This contains the
    // sequence number, the number of integers in the data and the command.
    // The following 32 bits contains the environment address

    // The next instruction should just invalidate the cache, since the
    //  DSP is not supposed to write to the HostWriteArea.
#if EXT_MEM
    CACHE_wbInvL2((void *)HOST_BASE, 8, CACHE_WAIT);
#endif
    commStatSeqNum++;   // Expected sequence number
    commStatSeqNum &= 0xFF;

    host = (HostWriteArea *) HOST_BASE;
    seqNum = (host->data[0] >> 24) & 0xFF;
    numInt = (host->data[0] >> 16) & 0xFF;
    command = host->data[0] & 0xFFFF;
    envAddr = host->data[1] & 0xFFFF;
    // printf("seqNum = %d, numInt = %d, command = %d, envAddr = %d\n",
    //  seqNum, numInt, command, envAddr);

    // Next read the following numInt+1 32-bit quantities in the HostWriteArea, which
    //  should contain the data as well as a CRC32 checksum. Again we need to invalidate
    //  the cache before accessing the data.
#if EXT_MEM
    CACHE_wbInvL2((void *)(HOST_BASE+8), 4*(numInt+1), CACHE_WAIT);
#endif

    // Compute the CRC32 and compare it with that sent in data[numInt+2]
    crc = calcCrc32(0,(unsigned int *)host->data,numInt+2);
    if (crc != host->data[numInt+2])
    {
        d.asUint = ((commStatSeqNum<<COMM_STATUS_SequenceNumberShift)&COMM_STATUS_SequenceNumberMask)|
                   (COMM_STATUS_BadCrcMask)|
                   (COMM_STATUS_CompleteMask);
        // Indicate bad CRC as well as set complete flag
        writeRegister(COMM_STATUS_REGISTER,d);
    }
    // Next check the sequence number sent coincides with the expected sequence number

    else if (seqNum != commStatSeqNum)
    {
        d.asUint = ((commStatSeqNum<<COMM_STATUS_SequenceNumberShift)&COMM_STATUS_SequenceNumberMask)|
                   (COMM_STATUS_BadSequenceNumberMask)|
                   (COMM_STATUS_CompleteMask);
        // Indicate bad sequence number as well as set complete flag
        writeRegister(COMM_STATUS_REGISTER,d);
    }

    else
    {
        // TODO: Check for valid arguments before writing the "in-progress" code
        // Indicate that the command is in-progress by setting the sequence number field, but keeping
        //  the Complete status reset
        d.asUint = ((commStatSeqNum<<COMM_STATUS_SequenceNumberShift)&COMM_STATUS_SequenceNumberMask);
        writeRegister(COMM_STATUS_REGISTER,d);
        // Perform the command, using the autogenerated dispatch table to select the correct action
        retVal = doAction(command,numInt,(void*)(host->data+2),(void*)&env_table[envAddr]);
        // Indicate that the process is complete
        d.asUint = ((commStatSeqNum<<COMM_STATUS_SequenceNumberShift)&COMM_STATUS_SequenceNumberMask)|
                   ((retVal<<COMM_STATUS_ReturnValueShift)&COMM_STATUS_ReturnValueMask)|
                   (COMM_STATUS_CompleteMask);
        writeRegister(COMM_STATUS_REGISTER,d);
    }
    // Clear interrupt source
    HPI_setDspint(1);
    IRQ_clear(IRQ_EVT_DSPINT);
    // Restore interrupts
    IRQ_globalRestore(gie);
}
