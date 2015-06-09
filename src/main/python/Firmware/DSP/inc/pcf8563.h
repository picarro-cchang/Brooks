/*
 * FILE:
 *   pcf8563.h
 *
 * DESCRIPTION:
 *   Routines to communicate with PCF8563 real-time clock
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   7-May-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _PCF8563_H_
#define  _PCF8563_H_

void pcf8563_init();
#endif

void pcf8563_set_time(unsigned int year,unsigned int month,
                      unsigned int day, unsigned int hours,
                      unsigned int minutes,unsigned int seconds,
                      unsigned int weekday);

void pcf8563_get_time(unsigned int *year,unsigned int *month,
                      unsigned int *day,unsigned int *hours,
                      unsigned int *minutes,unsigned int *seconds,
                      unsigned int *weekday);

void pcf8563_init();
