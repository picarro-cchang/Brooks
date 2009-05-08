/*
 * FILE:
 *   ds1631.h
 *
 * DESCRIPTION:
 *   Routines to communicate with DS1631 temperature sensor
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   6-May-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _DS1631_H_
#define  _DS1631_H_

void ds1631_reset();
void ds1631_startConvert();
void ds1631_writeConfig(unsigned int w);
unsigned int ds1631_readConfig();
unsigned int ds1631_readTemperature();
float ds1631_readTemperatureAsFloat();

void ds1631_init();
#endif
