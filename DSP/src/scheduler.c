/*
 * FILE:
 *   scheduler.c
 *
 * DESCRIPTION:
 *   Scheduler routines
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   09-Mar-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#include <stdio.h>
#include <std.h>
#include <string.h>
#include <sem.h>
#include <prd.h>
#include "dspMaincfg.h"

#include "registers.h"
#include "scheduler.h"
// The following contains the prototype of the dispatcher for actions
#include "dspAutogen.h"

GroupSched *group_table = (GroupSched *) GROUP_BASE;
Operation *operation_table = (Operation *) OPERATION_BASE;
unsigned int *operand_table = (unsigned int *) OPERAND_BASE;
unsigned int *env_table = (unsigned int *) ENVIRONMENT_BASE;
unsigned short runqueue_head = NO_MORE;
RunQueue run_table[MAX_GROUPS];

void insert_into_runqueue(unsigned short group_num, long long when)
{
    if (group_num >= MAX_GROUPS) return;
    if (NO_MORE == runqueue_head)
    {
        runqueue_head = group_num;
        run_table[group_num].when = when;
        run_table[group_num].next_group = NO_MORE;
    }
    else
    {
        unsigned short *g = &runqueue_head;
        long long w;
        // Note smaller values of the priority correspond to HIGHER priorities. The priority is in the top four bits of the short
        unsigned short p, priority = (0xF000 & group_table[group_num].priority_and_period) >> 12;
        while (1)
        {
            // Check if group_num to insert needs to be inserted ahead of group *g
            w = run_table[*g].when;
            p = (0xF000 & group_table[*g].priority_and_period) >> 12;
            if ((when < w) || ((when == w) && (priority<p)))
            {
                run_table[group_num].when = when;
                run_table[group_num].next_group = *g;
                *g = group_num;
                break;
            }
            else   // group_num is to be executed after *g, so thread down the queue
            {
                unsigned short next = run_table[*g].next_group;
                if (NO_MORE != next) g = &run_table[*g].next_group;
                else
                {
                    run_table[*g].next_group = group_num;
                    run_table[group_num].when = when;
                    run_table[group_num].next_group = NO_MORE;
                    break;
                }
            }
        }
    }
}

void dump_runqueue(void)
{
    if (NO_MORE == runqueue_head) printf("Runqueue is empty\n");
    else
    {
        unsigned short i = 0;
        unsigned short g = runqueue_head;
        printf("Runqueue:\n");
        while (1)
        {
            long long when = run_table[g].when;
            unsigned short priority = (0xF000 & group_table[g].priority_and_period) >> 12;
            unsigned short period = 0xFFF & group_table[g].priority_and_period;
            unsigned short next = run_table[g].next_group;
            unsigned short addr = group_table[g].operation_address;
            printf("Entry %3d: Address %6d, Priority %2d, Period %6d, When %d\n",++i,addr,priority,period,when);
            if (NO_MORE == next) break;
            g = next;
        }
        printf("End of runqueue\n");
    }
}

int get_group_period(unsigned int group)
{
    return 0xFFF & group_table[group].priority_and_period;
}

int get_group_priority(unsigned int group)
{
    return (0xF000 & group_table[group].priority_and_period) >> 12;
}

void do_groups(long long now)
{
    unsigned short to_do = runqueue_head;
    unsigned short period;
    unsigned int period_ms;
    long long next_time;

    if (NO_MORE == runqueue_head) return;
    while (1)
    {
        if (NO_MORE == to_do)
        {
            // Should never happen
            message_puts("Nothing left to do\n");
            break;
        }
        if (run_table[to_do].when > now) break;
        period = 0xFFF & group_table[to_do].priority_and_period;
        period_ms = 100 * period;
        next_time = ((now + period_ms)/period_ms )*period_ms;
        dispatch_group(group_table[to_do].operation_address);
        runqueue_head = run_table[to_do].next_group;
        insert_into_runqueue(to_do, next_time);
        to_do = runqueue_head;
    }
    return;
}

void dispatch_group(unsigned short operation_address)
{
    Operation *op;
    unsigned int *operands;
    unsigned int *env;
    // sprintf(debug_msg,"Performing group at address %d\n",operation_address);
    // message_puts(debug_msg);
    while (1)
    {
        op = &operation_table[operation_address];
        if (op->opcode == 0) break;
        // sprintf(debug_msg,"Dispatching opcode %d with %d operands\n",
        //  op->opcode,op->num_operands);
        // message_puts(debug_msg);
        operands = &operand_table[op->operand_address];
        env = &env_table[op->env_address];
        doAction((unsigned int)(op->opcode),
                 (unsigned int)(op->num_operands),
                 operands, env);
        operation_address++;
    }
}

void clear_scheduler_tables()
{
    memset(group_table,0,4*GROUP_TABLE_SIZE);
    memset(operation_table,0,4*OPERATION_TABLE_SIZE);
    memset(operand_table,0,4*OPERAND_TABLE_SIZE);
    memset(env_table,0,4*ENVIRONMENT_TABLE_SIZE);
}

// Task function for scheduler
void scheduler(void)
{
    DataType d;
    while (1)
    {
        // Do any pending host commands issued within HPI interrupts
        if (SEM_pend(&SEM_hpiIntBackend,10)) backend();
        if (SEM_pend(&SEM_scheduler,0)) {
            readRegister(SCHEDULER_CONTROL_REGISTER,&d);
            if (d.asInt) do_groups(timestamp);
        }
    }
}

/* We need to be able to load the group table, operation table and operand
   table from Python, before turning control to the DSP scheduler */

/*
int main(int argc, char *argv[]) {
    long long now;
    group_table[0].priority_and_period = 3;
    group_table[0].operation_address = 1;
    group_table[1].priority_and_period = (2<<12) + 2;
    group_table[1].operation_address = 2;
    group_table[2].priority_and_period = 4;
    group_table[2].operation_address = 3;
    group_table[3].priority_and_period = (1<<12) + 3;
    group_table[3].operation_address = 4;
    dump_runqueue();
    printf("Inserting group at address 1 at time 3\n");
    insert_into_runqueue(0,3);
    dump_runqueue();
    printf("Inserting group at address 2 at time 2\n");
    insert_into_runqueue(1,2);
    dump_runqueue();
    printf("Inserting group at address 3 at time 4\n");
    insert_into_runqueue(2,4);
    dump_runqueue();
    printf("Inserting group at address 4 at time 3\n");
    insert_into_runqueue(3,3);
    dump_runqueue();
    // Start doing stuff
    for (now=0; now<20; now++) {
        printf("Now = %ld\n",now);
        do_groups(now);
        //dump_runqueue();
    }
    return 0;
}
*/
