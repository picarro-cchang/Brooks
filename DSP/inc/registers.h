/*
 * FILE:
 *   registers.h
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
#ifndef _REGISTERS_H_
#define _REGISTERS_H_

#include "interface.h"
#include <csl_timer.h>

/* The shared memory region is divided into the following (by integer address):

0x0000 - 0x2BFF: Software registers
0x2C00 - 0x33FF: Sensor stream area
0x3400 - 0x37FF: Message area
0x3800 - 0x381F: Group table
0x3820 - 0x3AFF: Operation table
0x3B00 - 0x3EFF: Operand table

Offsets and lengths are in 4-byte integers. Offsets are defined in interface.h
 via the XML file. */

#define SHAREDMEM_BASE (SHAREDMEM_ADDRESS)
#define USER_REG 0x90080000

#define REG_BASE          (SHAREDMEM_BASE+4*REG_OFFSET)
#define SENSOR_BASE       (SHAREDMEM_BASE+4*SENSOR_OFFSET)
#define MESSAGE_BASE      (SHAREDMEM_BASE+4*MESSAGE_OFFSET)
#define GROUP_BASE        (SHAREDMEM_BASE+4*GROUP_OFFSET)
#define OPERATION_BASE    (SHAREDMEM_BASE+4*OPERATION_OFFSET)
#define OPERAND_BASE      (SHAREDMEM_BASE+4*OPERAND_OFFSET)
#define ENVIRONMENT_BASE  (SHAREDMEM_BASE+4*ENVIRONMENT_OFFSET)
#define HOST_BASE         (SHAREDMEM_BASE+4*HOST_OFFSET)

extern long long timestamp; // Global timestamp for analyzer
extern TIMER_Handle hTimer0; // Handle for DSP TIMER0

typedef struct
{
    unsigned int data[256];
} HostWriteArea;

/* Each message occupies 128 bytes, and consists of a 64 bit timestamp followed by 120
 characters of text.  */
typedef struct
{
    long long timestamp;
    char message[120];
} Message;

void get_timestamp(long long *ts);
void init_comms(void);
void message_puts(char *message);
void sensor_put_from(unsigned int streamNum, float value);
volatile RingdownEntryType *get_ringdown_entry_addr();
void ringdown_put();
unsigned int getDasStatusBit(unsigned int bitNum);
void setDasStatusBit(unsigned int bitNum);
void resetDasStatusBit(unsigned int bitNum);

/* These are from the point of view of the DSP */
int  writeRegister(unsigned int regNum,DataType data);
int  writebackRegisters(unsigned int regNums[],unsigned int n);
int  readRegister(unsigned int regNum, DataType *data);
void *registerAddr(unsigned int regNum);
RegTypes getRegisterType(unsigned int regNum);

void hwiHpiInterrupt(unsigned int funcArg, unsigned int eventId);
void backend(void);

#endif /* _REGISTERS_H_ */
