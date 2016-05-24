/*
 * FILE:
 *   i2c_dsp.h
 *
 * DESCRIPTION:
 *   Routines to communicate with I2C on the DSP
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   6-May-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef  _I2C_DSP_H_
#define  _I2C_DSP_H_

#include <std.h>
#include <csl_i2c.h>

#define I2C_BUSY     (-1)
#define I2C_NACK     (-2)
#define I2C_NARDY    (-3)
#define I2C_NRRDY    (-4)
#define I2C_NXRDY    (-5)
#define I2C_BADPAGE  (-6)

/*
typedef struct {
    I2C_Handle *hI2C;
    int addr;
} I2C_devAddr;
*/

extern I2C_Handle hI2C[2];

/*
extern I2C_devAddr laser_thermistor_I2C, laser_current_I2C, etalon_thermistor_I2C, warm_box_heatsink_thermistor_I2C;
extern I2C_devAddr logic_eeprom_I2C, wlm_eeprom_I2C, laser_eeprom_I2C;
extern I2C_devAddr warm_box_thermistor_I2C, hot_box_heatsink_thermistor_I2C, cavity_thermistor_I2C;
extern I2C_devAddr das_temp_sensor_I2C, laser_tec_current_monitor_I2C, valve_pump_tec_I2C_old, valve_pump_tec_I2C_new;
extern I2C_devAddr cavity_pressure_I2C, ambient_pressure_I2C;
*/

int initializeI2C(I2C_Handle hI2c);
int I2C_write_bytes(I2C_Handle hI2c,int i2caddr,Uint8 *buffer,int nbytes);
int I2C_write_bytes_nostart(I2C_Handle hI2c,Uint8 *buffer,int nbytes);
int I2C_read_bytes(I2C_Handle hI2c,int i2caddr,Uint8 *buffer,int nbytes);
int I2C_check_ack(I2C_Handle hI2c,int i2caddr);
void dspI2CInit();
void setI2C0Mux(int channel);
int fetchI2C0Mux();
int getI2C0Mux();
void setI2C1Mux(int channel);
int fetchI2C1Mux();
int getI2C1Mux();
int getI2CMode(I2C_Handle hI2c);
int getI2CStatus(I2C_Handle hI2c);
int ltc2485_read(int ident);
int read_flow_sensor(int ident);
int rdd_read(int ident);
void rdd_write(int ident, int data, int nbytes);

#endif
