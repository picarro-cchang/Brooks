/*
 * FILE:
 *   read_flow_sensor.h
 *
 * DESCRIPTION:
 *   Routines to communicate with Honeywell flow sensor
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   22-Jun-2012  sze  Initial version.
 *
 *  Copyright (c) 2012 Picarro, Inc. All rights reserved
 */
#ifndef  _READ_FLOW_SENSOR_H_
#define  _READ_FLOW_SENSOR_H_

int read_flow_sensor(I2C_device *i2c);
#endif
