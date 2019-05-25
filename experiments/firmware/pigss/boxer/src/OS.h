/**
 * @file    OS.h
 * @author  Ferenc Nemeth
 * @date    21 Jul 2018
 * @brief   This is a really simple, non-preemptive task scheduler.
 *          You can register tasks with their runnable function and the periodic time you want to call them.
 *          With a help of a timer the tasks get into READY state after every time period (except if they are SUSPENDED) and
 *          they get called and executed in the main()'s inifinte loop. After they are finished everything starts over.
 *          This Scheduler helps you to keep your tasks and timing organized.
 *
 *          Copyright (c) 2018 Ferenc Nemeth - https://github.com/ferenc-nemeth/
 */ 

#ifndef OS_H_
#define OS_H_

#include <avr/io.h>
#include <stddef.h>

// Maximum number of tasks that can be registered
#define OS_MAX_TASK_NUM ((uint8_t)10u)

// Maximum task period (ms)
#define OS_MAX_TIME     ((uint16_t)10000u)

// Minimum task period (ms)
#define OS_MIN_TIME     ((uint16_t)1u)

typedef void (*fncPtr)(void);           /**< Function pointer for registering tasks. */

/**
 * States of the tasks.
 */
typedef enum
{
    BLOCKED = 0,                        /**< In the BLOCKED state the task waits for the timer to put it into READY state. */
    READY,                              /**< In the READY state the task is ready to be called and executed in the main function. */
    SUSPENDED                           /**< In the SUSPENDED state the task is ignored by the timer and executer. */
} OS_state;

/**
 * Variables of the tasks.
 */
typedef struct
{
  // Task that gets called periodically
  fncPtr      function;

  // Time between tasks
  uint16_t     time_burst;

  // Time since the task was called
  uint16_t     time_cnt;

  // The state of the task
  OS_state    state;
} OS_struct;

/**
 * Feedback and error handling for the task creation.
 */
typedef enum
{
    OK = 0,                             /**< OK:    Everything went as expected. */
    NOK_NULL_PTR,                       /**< ERROR: Null pointer as a task. */
    NOK_TIME_LIMIT,                     /**< ERROR: The time period is more or less, than the limits. */
    NOK_CNT_LIMIT,                      /**< ERROR: Something horrible happened, time to panic! */
    NOK_UNKNOWN
} OS_feedback;

/**
 * Functions.
 */
OS_feedback OS_TaskCreate(fncPtr task, uint8_t default_time_burst, OS_state default_state);
void OS_TaskTimer(void);
void OS_TaskExecution(void);
OS_state OS_GetTaskSate(uint8_t task_number);
uint16_t OS_GetTaskBurstTime(uint8_t task_number);
uint16_t OS_GetTaskCntTime(uint8_t task_number);
void OS_SetTaskSate(uint8_t task_number, OS_state new_state);
void OS_SetTaskBurstTime(uint8_t task_number, uint16_t new_time_burst);
void OS_SetTaskCntTime(uint8_t task_number, uint16_t new_time_cnt);

#endif /* OS_H_ */
