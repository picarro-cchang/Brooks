#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""
 Modbus TestKit: Implementation of Modbus protocol in python

 (C)2009 - Luc Jean - luc.jean@gmail.com
 (C)2009 - Apidev - http://www.apidev.fr

 This is distributed under GNU LGPL license, see license.txt
"""

import sys
import serial
import time
#add logging capability
import logging

import Host.Utilities.ModbusIntrf.modbus as modbus
import Host.Utilities.ModbusIntrf.utils as utils
import Host.Utilities.ModbusIntrf.defines as cst
import Host.Utilities.ModbusIntrf.modbus_rtu as modbus_rtu

logger = utils.create_logger("console")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        actionCode = int(sys.argv[1])
    else:
        actionCode = 0

    if len(sys.argv) > 2:
        startReg = int(sys.argv[2])
    else:
        startReg = 2000

    if len(sys.argv) > 3:
        arg = int(sys.argv[3])
    else:
        arg = 0

    if len(sys.argv) > 4:
        repeat = int(sys.argv[4])
    else:
        repeat = 1

    actionDict = {0: cst.READ_HOLDING_REGISTERS,
                  1: cst.WRITE_SINGLE_REGISTER}

    argDict = {0: {"quantity_of_x": arg},
               1: {"output_value": arg}}

    baudrate = 9600
    print "\n%d" % baudrate
    try:
        #Connect to the slave
        ser = serial.Serial(port="COM8", baudrate=baudrate, bytesize=8, parity=serial.PARITY_NONE, stopbits=1, xonxoff=1)
        master = modbus_rtu.RtuMaster(ser)
        master.set_timeout(5.0)
        master.set_verbose(True)
        logger.info("connected")

        #logger.info(master.execute(1, cst.READ_HOLDING_REGISTERS, 2001, 1))
        for i in range(repeat):
            print master.execute(1, actionDict[actionCode], startReg, **argDict[actionCode])
            time.sleep(65.0)
        #send some queries
        #logger.info(master.execute(1, cst.READ_COILS, 2000, 10))
        #logger.info(master.execute(1, cst.READ_DISCRETE_INPUTS, 0, 8))
        #logger.info(master.execute(1, cst.READ_INPUT_REGISTERS, 100, 3))
        #logger.info(master.execute(1, cst.READ_HOLDING_REGISTERS, 100, 12))
        #logger.info(master.execute(1, cst.WRITE_SINGLE_COIL, 7, output_value=1))
        #logger.info(master.execute(1, cst.WRITE_SINGLE_REGISTER, 100, output_value=54))
        #logger.info(master.execute(1, cst.WRITE_MULTIPLE_COILS, 0, output_value=[1, 1, 0, 1, 1, 0, 1, 1]))
        #logger.info(master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 100, output_value=xrange(12)))

    except modbus.ModbusError, e:
        logger.error("%s- Code=%d" % (e, e.get_exception_code()))
        ser.close()

    except Exception, err:
        print "ERROR: %r" % err
        ser.close()