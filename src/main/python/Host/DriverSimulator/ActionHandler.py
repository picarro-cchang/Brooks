#!/usr/bin/python
#
"""
File Name: ActionHandler.py
Purpose: Implementation of action functions for the Das simulator

File History:
    25-Sep-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""
import math

from Host.autogen import interface
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.DriverSimulator.LaserCurrentControl import (
    Laser1CurrentControl, Laser2CurrentControl, Laser3CurrentControl, Laser4CurrentControl)
from Host.DriverSimulator.Simulators import (
    Laser1Simulator, Laser2Simulator, Laser3Simulator, Laser4Simulator, LaserOpticalModel)
from Host.DriverSimulator.TempControl import (
    Laser1TempControl, Laser2TempControl, Laser3TempControl, Laser4TempControl)

APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)


class ActionHandler(object):
    def __init__(self, sim):
        self.sim = sim
        self.action = {
            interface.ACTION_WRITE_BLOCK: self.writeBlock,
            interface.ACTION_SET_TIMESTAMP: self.setTimestamp,
            interface.ACTION_GET_TIMESTAMP: self.getTimestamp,
            interface.ACTION_INIT_RUNQUEUE: self.initRunqueue,
            interface.ACTION_TEST_SCHEDULER: self.testScheduler,
            interface.ACTION_STREAM_REGISTER_ASFLOAT: self.streamRegisterAsFloat,
            interface.ACTION_STREAM_FPGA_REGISTER_ASFLOAT: self.streamFpgaRegisterAsFloat,
            interface.ACTION_RESISTANCE_TO_TEMPERATURE: self.resistanceToTemperature,
            interface.ACTION_UPDATE_FROM_SIMULATORS: self.updateFromSimulators,
            interface.ACTION_STEP_SIMULATORS: self.stepSimulators,
            interface.ACTION_TEMP_CNTRL_LASER1_INIT: self.tempCntrlLaser1Init,
            interface.ACTION_TEMP_CNTRL_LASER1_STEP: self.tempCntrlLaser1Step,
            interface.ACTION_TEMP_CNTRL_LASER2_INIT: self.tempCntrlLaser2Init,
            interface.ACTION_TEMP_CNTRL_LASER2_STEP: self.tempCntrlLaser2Step,
            interface.ACTION_TEMP_CNTRL_LASER3_INIT: self.tempCntrlLaser3Init,
            interface.ACTION_TEMP_CNTRL_LASER3_STEP: self.tempCntrlLaser3Step,
            interface.ACTION_TEMP_CNTRL_LASER4_INIT: self.tempCntrlLaser4Init,
            interface.ACTION_TEMP_CNTRL_LASER4_STEP: self.tempCntrlLaser4Step,
            interface.ACTION_FILTER: self.filter,
            interface.ACTION_FLOAT_REGISTER_TO_FPGA: self.floatRegisterToFpga,
            interface.ACTION_FPGA_TO_FLOAT_REGISTER: self.fpgaToFloatRegister,
            interface.ACTION_INT_TO_FPGA: self.intToFpga,
            interface.ACTION_CURRENT_CNTRL_LASER1_INIT: self.currentCntrlLaser1Init,
            interface.ACTION_CURRENT_CNTRL_LASER1_STEP: self.currentCntrlLaser1Step,
            interface.ACTION_CURRENT_CNTRL_LASER2_INIT: self.currentCntrlLaser2Init,
            interface.ACTION_CURRENT_CNTRL_LASER2_STEP: self.currentCntrlLaser2Step,
            interface.ACTION_CURRENT_CNTRL_LASER3_INIT: self.currentCntrlLaser3Init,
            interface.ACTION_CURRENT_CNTRL_LASER3_STEP: self.currentCntrlLaser3Step,
            interface.ACTION_CURRENT_CNTRL_LASER4_INIT: self.currentCntrlLaser4Init,
            interface.ACTION_CURRENT_CNTRL_LASER4_STEP: self.currentCntrlLaser4Step,
            interface.ACTION_SIMULATE_LASER_CURRENT_READING: self.simulateLaserCurrentReading,
            interface.ACTION_UPDATE_WLMSIM_LASER_TEMP: self.updateWlmsimLaserTemp,
            interface.ACTION_SPECTRUM_CNTRL_INIT: self.spectCntrlInit,
            interface.ACTION_SPECTRUM_CNTRL_STEP: self.spectCntrlStep,
        }

    def currentCntrlLaser1Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser1CurrentControl = Laser1CurrentControl(self.sim)
        return interface.STATUS_OK

    def currentCntrlLaser1Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser1CurrentControl.step()

    def currentCntrlLaser2Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser2CurrentControl = Laser2CurrentControl(self.sim)
        return interface.STATUS_OK

    def currentCntrlLaser2Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser2CurrentControl.step()

    def currentCntrlLaser3Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser3CurrentControl = Laser3CurrentControl(self.sim)
        return interface.STATUS_OK

    def currentCntrlLaser3Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser3CurrentControl.step()

    def currentCntrlLaser4Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser4CurrentControl = Laser4CurrentControl(self.sim)
        return interface.STATUS_OK

    def currentCntrlLaser4Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser4CurrentControl.step()

    def doAction(self, command, params, env, when):
        if command in self.action:
            return self.action[command](params, env, when, command)
        else:
            print "Unimplemented action: %d" % command

    def filter(self, params, env, when, command):
        if 2 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        MAX_ORDER = 8
        x = self.sim.rdDasReg(params[0])
        filtEnv = self.sim.envStore[env]
        div = filtEnv.den[0]
        if div == 0:
            y = 0
            return interface.ERROR_BAD_FILTER_COEFF
        y = filtEnv.state[0] + (filtEnv.num[0] / div) * (x + filtEnv.offset)
        for i in range(MAX_ORDER - 1):
            filtEnv.state[i] = filtEnv.state[i+1] + (filtEnv.num[i+1] * (x + filtEnv.offset) - filtEnv.den[i+1]*y) / div
        filtEnv.state[MAX_ORDER - 1] = (filtEnv.num[MAX_ORDER] * (x + filtEnv.offset)  - filtEnv.den[MAX_ORDER]*y) / div
        self.sim.wrDasReg(params[1], y)
        return interface.STATUS_OK

    def floatRegisterToFpga(self, params, env, when, command):
        # Copy contents of a floating point register to an FPGA register,
        #  treating value as an unsigned int. The FPGA register is the sum
        #  of two arguments so that we can pass a block base and an offset within
        #  the block.
        if 3 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.wrFPGA(params[1], params[2], int(self.sim.rdDasReg(params[0])))
        return interface.STATUS_OK

    def fpgaToFloatRegister(self, params, env, when, command):
        # Copy contents of an FPGA register to a floating point register,
        #  treating value as an unsigned short. The FPGA register is the sum
        #  of two arguments so that we can pass a block base and an offset within
        #  the block.
        if 3 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.wrDasReg(params[2], self.sim.rdFPGA(params[0], params[1]))
        return interface.STATUS_OK

    def getTimestamp(self, params, env, when, command):
        # Timestamp is an integer number of ms
        if 2 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        ts = self.sim.getDasTimestamp()
        self.sim.wrDasReg(params[0], ts & 0xFFFFFFFF)
        self.sim.wrDasReg(params[1], ts >> 32)
        return interface.STATUS_OK

    def initRunqueue(self, params, env, when, command):
        if 1 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        if params[0] != len(self.sim.operationGroups):
            Log("Incorrect number of operation groups in initRunqueue")
        self.sim.initScheduler()
        return interface.STATUS_OK

    def intToFpga(self, params, env, when, command):
        # Copy integer (passed as first parameter) to the specified FPGA register.
        #  The FPGA register is the sum of two arguments so that we can pass a
        #  block base and an offset within the block.
        if 3 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.wrFPGA(params[1], params[2], params[0])
        return interface.STATUS_OK

    def resistanceToTemperature(self, params, env, when, command):
        if 5 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        resistance = self.sim.rdDasReg(params[0])
        constA = self.sim.rdDasReg(params[1])
        constB = self.sim.rdDasReg(params[2])
        constC = self.sim.rdDasReg(params[3])
        if 1.0 < resistance < 5.0e6:
            lnR = math.log(resistance)
            result = 1/(constA + (constB * lnR) + (constC * lnR ** 3)) - 273.15
            self.sim.wrDasReg(params[4], result)
        else:
            self.sim.dsp_message_queue.append((when, interface.LOG_LEVEL_CRITICAL, "Bad resistance in resistanceToTemperature"))
        return interface.STATUS_OK

    def setTimestamp(self, params, env, when, command):
        # Timestamp is an integer number of ms 
        if 2 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        ts = params[0] + (params[1] << 32)
        self.sim.setDasTimestamp(ts)
        return interface.STATUS_OK

    def simulateLaserCurrentReading(self, params, env, when, command):
        # For the specified laser number (1-origin), place the simulated laser current reading (obtained
        #  by combining coarse and fine laser contributions) into the specified register.  The scaling is
        #  360nA/fine_current unit, and 10 fine_current units = 1 coarse_current unit.
        if 2 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        dac = 0
        if params[0] == 1:
            dac = 10*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER1_COARSE_CURRENT) + 2*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER1_FINE_CURRENT)
        elif params[0] == 2:
            dac = 10*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER2_COARSE_CURRENT) + 2*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER2_FINE_CURRENT)
        elif params[0] == 3:
            dac = 10*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER3_COARSE_CURRENT) + 2*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER3_FINE_CURRENT)
        elif params[0] == 4:
            dac = 10*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER4_COARSE_CURRENT) + 2*self.sim.rdFPGA(interface.FPGA_INJECT, interface.INJECT_LASER4_FINE_CURRENT)
        current = 0.00036*dac
        self.sim.wrDasReg(params[1], current)
        return interface.STATUS_OK

    def spectCntrlInit(self, params, env, when, command):
        pass

    def spectCntrlStep(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.spectrumControl.step()

    def stepSimulators(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        for simulator in self.sim.simulators:
            simulator.step()
        self.sim.injectionSimulator.step()
        self.sim.spectrumSimulator.step()
        return interface.STATUS_OK

    def streamFpgaRegisterAsFloat(self, params, env, when, command):
        """This action streams the value of an FPGA register. The first parameter
            is the stream number, the second is the location in the FPGA map and
            the third is the register number."""
        if 3 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        streamNum = params[0]
        value = self.sim.rdFPGA(params[1], params[2])
        self.sim.sensor_queue.append((when, streamNum, value))

    def streamRegisterAsFloat(self, params, env, when, command):
        """This action streams the value of a register. The first parameter
            is the stream number and the second is the register number."""
        if 2 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        streamNum = params[0]
        value = self.sim.rdDasReg(params[1])
        self.sim.sensor_queue.append((when, streamNum, value))

    def testScheduler(self, params, env, when, command):
        # Send back parmeters via DSP message queue to test operation
        #  of scheduler
        message = "At %d testScheduler %s" % (when, " ".join(["%d" % param for param in params]))
        self.sim.dsp_message_queue.append((when, interface.LOG_LEVEL_STANDARD, message))
        return interface.STATUS_OK

    def tempCntrlLaser1Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser1TempControl = Laser1TempControl(self.sim)
        self.sim.laser1Simulator = Laser1Simulator(self.sim, opticalModel=LaserOpticalModel(nominal_wn=6237.0))
        self.sim.addSimulator(self.sim.laser1Simulator)
        return interface.STATUS_OK

    def tempCntrlLaser2Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser2TempControl = Laser2TempControl(self.sim)
        self.sim.laser2Simulator = Laser2Simulator(self.sim, opticalModel=LaserOpticalModel(nominal_wn=6058.0))
        self.sim.addSimulator(self.sim.laser2Simulator)
        return interface.STATUS_OK

    def tempCntrlLaser3Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser3TempControl = Laser3TempControl(self.sim)
        self.sim.laser3Simulator = Laser3Simulator(self.sim)
        self.sim.addSimulator(self.sim.laser3Simulator)
        return interface.STATUS_OK

    def tempCntrlLaser4Init(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        self.sim.laser4TempControl = Laser4TempControl(self.sim)
        self.sim.laser4Simulator = Laser4Simulator(self.sim)
        self.sim.addSimulator(self.sim.laser4Simulator)
        return interface.STATUS_OK

    def tempCntrlLaser1Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser1TempControl.step()

    def tempCntrlLaser2Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser2TempControl.step()

    def tempCntrlLaser3Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser3TempControl.step()

    def tempCntrlLaser4Step(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        return self.sim.laser4TempControl.step()

    def updateFromSimulators(self, params, env, when, command):
        if 0 != len(params):
            return interface.ERROR_BAD_NUM_PARAMS
        for simulator in self.sim.simulators:
            simulator.update()
        self.sim.injectionSimulator.update()
        self.sim.spectrumSimulator.update()
        return interface.STATUS_OK

    def unknownAction(self, params, env, when, command):
        self.sim.dsp_message_queue.append((when, interface.LOG_LEVEL_CRITICAL, "Unknown action code %d" % command))
        return interface.STATUS_OK

    def updateWlmsimLaserTemp(self, params, env, when, command):
        # In the simulator, this action has been hijacked to also compute the
        #  wavelength monitor outputs and the ratios based on the temperature 
        #  and current of the selected laser
        laserNum = self.sim.readBitsFPGA(
            interface.FPGA_INJECT + interface.INJECT_CONTROL,
            interface.INJECT_CONTROL_LASER_SELECT_B, 
            interface.INJECT_CONTROL_LASER_SELECT_W) + 1
        laserTemp = self.sim.rdDasReg("LASER%d_TEMPERATURE_REGISTER" % laserNum)
        laserCurrent = 0.00036 * (10 * self.sim.rdFPGA(
            "FPGA_INJECT", 
            "INJECT_LASER%d_COARSE_CURRENT" % laserNum) + 
            2 * self.sim.rdFPGA(
            "FPGA_INJECT", 
            "INJECT_LASER%d_FINE_CURRENT" % laserNum))
        return interface.STATUS_OK

    def writeBlock(self, params, env, when, command):
        offset = params[0]
        for i in range(len(params)-1):
            self.sim.sharedMem[offset + i] = params[i + 1]
        return interface.STATUS_OK
