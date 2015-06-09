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

#include <std.h>
#include <csl.h>
#include <csl_cache.h>
#include <csl_hpi.h>
#include <csl_i2c.h>
#include <csl_irq.h>
#include <log.h>
#include <prd.h>
#include <sem.h>
#include "dspMaincfg.h"

#define EXT_MEM 0

#include <stdio.h>
#include "crc.h"
#include "dspAutogen.h"
#include "dspData.h"
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
static int ringdown_pointer = 0;
TIMER_Handle hTimer0;

void init_comms()
{
    DataType d;
    hTimer0 = TIMER_open(TIMER_DEV0, 0);

    memset(messages,0,4*MESSAGE_REGION_SIZE);
    message_pointer = 0;
    memset(sensorEntries,0,4*SENSOR_REGION_SIZE);
    sensor_pointer = 0;
    // Initialize the COMM_STATUS register
    commStatSeqNum = 0;
    d.asUint = ((commStatSeqNum<<COMM_STATUS_SequenceNumberShift)&
                COMM_STATUS_SequenceNumberMask)|COMM_STATUS_CompleteMask;
    writeRegister(COMM_STATUS_REGISTER,d);
    memset((void *)ringdownEntries,0,sizeof(RingdownEntryType)*NUM_RINGDOWN_ENTRIES);
    CACHE_wbL2((void *)(ringdownEntries), sizeof(RingdownEntryType)*NUM_RINGDOWN_ENTRIES, CACHE_WAIT);
}

void message_puts(unsigned int level,char *message)
{
    long long ts;
    Message *m = messages + message_pointer;
    if (level > LOG_LEVEL_CRITICAL) level = LOG_LEVEL_CRITICAL;
    get_timestamp(&ts);
    m->timestamp = 0LL;
    m->message[0] = '0' + level;
    m->message[1] = ':';
    strncpy(m->message + 2,message,120);
    m->timestamp = ts;
    message_pointer++;
    if (message_pointer>=NUM_MESSAGES) message_pointer = 0;
}

void sensor_put_from(unsigned int streamNum, float value)
{
    long long ts;
    SensorEntryType *s = sensorEntries + sensor_pointer;
    get_timestamp(&ts);
    s->streamNum = streamNum;
    s->value = value;
    s->timestamp = ts;
    sensor_pointer++;
    if (sensor_pointer>=NUM_SENSOR_ENTRIES) sensor_pointer = 0;
}

volatile RingdownEntryType *get_ringdown_entry_addr()
/* Get address of next available ringdown entry which is to be
    filled with data */
{
    return ringdownEntries + ringdown_pointer;
}

void ringdown_put()
/* Timestamp the filled ringdown entry and make it available for
    download by the host. Note that we were careful to initialize
    the circular buffer with zeros, so that the timestamp for the
    next available (as yet uncollected) entry is either zero or
    less than the current entry. It is also necessary to flush the
    L2 cache back to external memory after each write.
*/
{
    long long ts;
    volatile RingdownEntryType *r = ringdownEntries + ringdown_pointer;
    CACHE_wbL2((void *)r, 64, CACHE_WAIT);
    get_timestamp(&ts);
    r->timestamp = ts;
    CACHE_wbL2((void *)r, 64, CACHE_WAIT);
    ringdown_pointer++;
    if (ringdown_pointer>=NUM_RINGDOWN_ENTRIES) ringdown_pointer = 0;
}

// DSP writes to a register and writes back the cache, to ensure that the data can subsequently be read
//  by the host
int writeRegister(unsigned int regNum,DataType data)
{
    if (regNum >= REG_REGION_SIZE) return ERROR_UNKNOWN_REGISTER;
    else *(int*)(registerAddr(regNum)) = data.asInt;
#if EXT_MEM
    CACHE_wbL2((void *)(registerAddr(regNum)), 4, CACHE_WAIT);
#endif
    return STATUS_OK;
}

// DSP writes back a block of registers to the cache, so that the data can subsequently be read
//  by the host
int writebackRegisters(unsigned int regNums[],unsigned int n)
{
    int status = STATUS_OK;
#if EXT_MEM
    int i;
    for (i=0; i<n; i++)
    {
        if (regNums[i] >= REG_REGION_SIZE) status = ERROR_UNKNOWN_REGISTER;
        else CACHE_wbL2((void *)(registerAddr(regNums[i])), 4, CACHE_WAIT);
    }
#endif
    return status;
}

RegTypes getRegisterType(unsigned int regNum)
{
    return regTypes[regNum];
}

int readRegister(unsigned int regNum, DataType *data)
{
    if (regNum >= REG_REGION_SIZE) return ERROR_UNKNOWN_REGISTER;
    else data->asInt = *(int*)(registerAddr(regNum));
    return STATUS_OK;
}

void *registerAddr(unsigned int regNum)
/* Returns pointer to the specified register index for direct read-access by DSP.
   Pointer should be non-null, and cast to the appropriate type as required */
{
    if (regNum >= REG_REGION_SIZE) return 0;
    return (void*)(REG_BASE+4*regNum);
}

unsigned int getDasStatusBit(unsigned int bitNum)
/* Gets a single bit in the DAS_STATUS_REGISTER  */
{
    unsigned int dasStatus = *(unsigned int*)(registerAddr(DAS_STATUS_REGISTER));
    unsigned int mask = 1<<bitNum;
    return (0 != (dasStatus&mask));
}

void setDasStatusBit(unsigned int bitNum)
/* Sets a single bit in the DAS_STATUS_REGISTER  */
{
    unsigned int *dasStatus = (unsigned int*)(registerAddr(DAS_STATUS_REGISTER));
    unsigned int mask = 1<<bitNum;
    (*dasStatus) = (*dasStatus) | mask;
}

void resetDasStatusBit(unsigned int bitNum)
/* Resets a single bit in the DAS_STATUS_REGISTER  */
{
    unsigned int *dasStatus = (unsigned int*)(registerAddr(DAS_STATUS_REGISTER));
    unsigned int mask = 1<<bitNum;
    (*dasStatus) = (*dasStatus) & (~mask);
}

/* The following variables are set in the hwiHpiInterrupt and used in the backend process
    which actually performs the action */

static unsigned int command, envAddr, numInt; 
static HostWriteArea *host;

void hwiHpiInterrupt(unsigned int funcArg, unsigned int eventId)
{
    // Responds to the DSPINT interrupt, which is a signal that the host wants
    //  the DSP to process a command in the message area starting at HOST_BASE
    DataType d;
    unsigned int gie, seqNum,  crc;

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

    else {
        if (seqNum != commStatSeqNum)
        {
            char msg[32];
            sprintf(msg,"Unexpected DSP sequence number 0x%x 0x%x",seqNum,commStatSeqNum);
            message_puts(msg);
        }
        // TODO: Check for valid arguments before writing the "in-progress" code
        // Indicate that the command is in-progress by setting the sequence number field, but keeping
        //  the Complete status reset
        d.asUint = ((commStatSeqNum<<COMM_STATUS_SequenceNumberShift)&COMM_STATUS_SequenceNumberMask);
        writeRegister(COMM_STATUS_REGISTER,d);
        SEM_post(&SEM_hpiIntBackend);
    }
    // Clear interrupt source
    HPI_setDspint(1);
    IRQ_clear(IRQ_EVT_DSPINT);
    // Restore interrupts
    IRQ_globalRestore(gie);
}

void backend(void)
/* Perform the host-initiated command in the scheduler thread, so that no races can occur with 
    scheduled actions */
{
    DataType d;
    int retVal;
    // Perform the command, using the autogenerated dispatch table to select the correct action
    retVal = doAction(command,numInt,(void*)(host->data+2),(void*)&env_table[envAddr]);
    // Indicate that the process is complete, and place return value into COMM_STATUS_REGISTER.
    d.asUint = ((commStatSeqNum<<COMM_STATUS_SequenceNumberShift)&COMM_STATUS_SequenceNumberMask)|
               ((retVal<<COMM_STATUS_ReturnValueShift)&COMM_STATUS_ReturnValueMask)|
               (COMM_STATUS_CompleteMask);
    writeRegister(COMM_STATUS_REGISTER,d);
}
