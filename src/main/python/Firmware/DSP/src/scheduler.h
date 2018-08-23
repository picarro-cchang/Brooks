/*
 * FILE:
 *   scheduler.h
 *
 * DESCRIPTION:
 *   Header file for scheduler routines
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   09-Mar-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _SCHEDULER_H_
#define  _SCHEDULER_H_

#include "registers.h"

#define NO_MORE (0xFFFF)
#define MAX_GROUPS (GROUP_TABLE_SIZE)
#define MAX_OPERATIONS (OPERATION_TABLE_SIZE)
#define MAX_OPERANDS (OPERAND_TABLE_SIZE)

/* priority (0-15) and period (0-4095) are encoded as (priority<<12) + period */
typedef struct groupSched
{
    unsigned short priority_and_period;
    unsigned short operation_address;
} GroupSched;

typedef struct runqueue
{
    long long when;
    unsigned short next_group;
} RunQueue;

typedef struct operation
{
    unsigned short opcode;
    unsigned short num_operands;
    unsigned short operand_address;
    unsigned short env_address;
} Operation;

/* A group is a collection of operations that has to be executed on a schedule. For each group, there is a priority which
    decides which of several groups that are scheduled for execution at the same time actually runs first. Numerically smaller
    priority values have precedence. Each group is scheduled to be run when the current value of the clock is divisible by
    the period. In the GroupSched structure, the priority and period are encoded as (priority<<12) | period */

extern GroupSched *group_table;

/* The run_table is a linearly linked list of groups, sorted in order of next evaluation */
extern RunQueue run_table[MAX_GROUPS];

/* The operation table consists of a collection of opcode, operand_address pairs. The operations for a group are stored in
    consecutive locations, terminated by an entry with an opcode of zero. The operand_address is a reference into the
    operand_table. Each opcode is associated with a specific number of operands, so as many of these are fetched as
    required. */
extern Operation  *operation_table;
/* Operands are typically indices of software registers containing the quantities which the operation requires. */
extern unsigned int *operand_table;

extern unsigned int *env_table;

extern unsigned short runqueue_head;

// Insert the operation group "group_num" into the runqueue, scheduling it at the time "when".
void insert_into_runqueue(unsigned short group_num, long long when);

//  Print out what is in the runqueue for debugging.
void dump_runqueue(void);

int get_group_period(unsigned int group);
int get_group_priority(unsigned int group);

// Perform group operations at the head of the run queue for the specified time, in the correct priority order.
//  After completion, the groups are rescheduled at the correct times depending on the period.
void do_groups(long long now);

// Dispatch sequence of operations, starting at the specified address until an operation with a zero opcode is encountered.
void dispatch_group(unsigned short operation_address);

// Clear all scheduler tables
void clear_scheduler_tables(void);

// Scheduler task
void scheduler(void);

#endif
