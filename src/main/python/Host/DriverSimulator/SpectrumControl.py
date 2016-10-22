#!/usr/bin/python
#
"""
File Name: SpectrumControl.py
Purpose: Classes for temperature controllers

File History:
    26-Sep-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""
import math

from Host.autogen import interface
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.DriverSimulator.Utilities import prop_das, prop_fpga

APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)


class SpectrumControl(object):
    active = prop_das(interface.SPECT_CNTRL_ACTIVE_SCHEME_REGISTER)
    ambientPressure = prop_das(interface.AMBIENT_PRESSURE_REGISTER)
    analyzerTuningMode = prop_das(interface.ANALYZER_TUNING_MODE_REGISTER)
    cavityPressure = prop_das(interface.CAVITY_PRESSURE_REGISTER)
    cavityTemperature = prop_das(interface.CAVITY_TEMPERATURE_REGISTER)
    dasStatus = prop_das(interface.DAS_STATUS_REGISTER)
    defaultThreshold = prop_das(interface.SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER)
    ditherTimeout = prop_das(interface.SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER)
    dwell = prop_das(interface.SPECT_CNTRL_DWELL_COUNT_REGISTER)
    etalonTemperature = prop_das(interface.ETALON_TEMPERATURE_REGISTER)
    fpgaPztOffset = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_PZT_OFFSET)
    injectControlMode = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MODE_B, interface.INJECT_CONTROL_MODE_W)
    iter = prop_das(interface.SPECT_CNTRL_SCHEME_ITER_REGISTER)
    laser1CoarseCurrent = prop_das(interface.LASER1_MANUAL_COARSE_CURRENT_REGISTER)
    laser1Temp = prop_das(interface.LASER1_TEMPERATURE_REGISTER)
    laser1TempSetpoint = prop_das(interface.LASER1_TEMP_CNTRL_SETPOINT_REGISTER)
    laser2CoarseCurrent = prop_das(interface.LASER2_MANUAL_COARSE_CURRENT_REGISTER)
    laser2Temp = prop_das(interface.LASER2_TEMPERATURE_REGISTER)
    laser2TempSetpoint = prop_das(interface.LASER2_TEMP_CNTRL_SETPOINT_REGISTER)
    laser3CoarseCurrent = prop_das(interface.LASER3_MANUAL_COARSE_CURRENT_REGISTER)
    laser3Temp = prop_das(interface.LASER3_TEMPERATURE_REGISTER)
    laser3TempSetpoint = prop_das(interface.LASER3_TEMP_CNTRL_SETPOINT_REGISTER)
    laser4CoarseCurrent = prop_das(interface.LASER4_MANUAL_COARSE_CURRENT_REGISTER)
    laser4Temp = prop_das(interface.LASER4_TEMPERATURE_REGISTER)
    laser4TempSetpoint = prop_das(interface.LASER4_TEMP_CNTRL_SETPOINT_REGISTER)
    laserSelect = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER_SELECT_B, interface.INJECT_CONTROL_LASER_SELECT_W)
    laserShutdownEnabled = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B, interface.INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W)
    lockEnabled = prop_fpga(interface.FPGA_RDMAN, interface.RDMAN_OPTIONS, interface.RDMAN_OPTIONS_LOCK_ENABLE_B, interface.RDMAN_OPTIONS_LOCK_ENABLE_W)
    rampTimeout = prop_das(interface.SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER)

    mode = prop_das(interface.SPECT_CNTRL_MODE_REGISTER)
    next = prop_das(interface.SPECT_CNTRL_NEXT_SCHEME_REGISTER)
    pztIncrPerFsr = prop_das(interface.PZT_INCR_PER_CAVITY_FSR)
    pztOffsetUpdateFactor = prop_das(interface.PZT_OFFSET_UPDATE_FACTOR)
    pztOffsetVL1 = prop_das(interface.PZT_OFFSET_VIRTUAL_LASER1)
    pztOffsetVL2 = prop_das(interface.PZT_OFFSET_VIRTUAL_LASER2)
    pztOffsetVL3 = prop_das(interface.PZT_OFFSET_VIRTUAL_LASER3)
    pztOffsetVL4 = prop_das(interface.PZT_OFFSET_VIRTUAL_LASER4)
    pztOffsetVL5 = prop_das(interface.PZT_OFFSET_VIRTUAL_LASER5)
    pztOffsetVL6 = prop_das(interface.PZT_OFFSET_VIRTUAL_LASER6)
    pztOffsetVL7 = prop_das(interface.PZT_OFFSET_VIRTUAL_LASER7)
    pztOffsetVL8 = prop_das(interface.PZT_OFFSET_VIRTUAL_LASER8)
    rampDitherMode = prop_fpga(interface.FPGA_RDMAN, interface.RDMAN_CONTROL, interface.RDMAN_CONTROL_RAMP_DITHER_B, interface.RDMAN_CONTROL_RAMP_DITHER_W)
    ringdownThreshold = prop_fpga(interface.FPGA_RDMAN, interface.RDMAN_THRESHOLD)
    row = prop_das(interface.SPECT_CNTRL_SCHEME_ROW_REGISTER)
    schemeOffsetVL1 = prop_das(interface.SCHEME_OFFSET_VIRTUAL_LASER1)
    schemeOffsetVL2 = prop_das(interface.SCHEME_OFFSET_VIRTUAL_LASER2)
    schemeOffsetVL3 = prop_das(interface.SCHEME_OFFSET_VIRTUAL_LASER3)
    schemeOffsetVL4 = prop_das(interface.SCHEME_OFFSET_VIRTUAL_LASER4)
    schemeOffsetVL5 = prop_das(interface.SCHEME_OFFSET_VIRTUAL_LASER5)
    schemeOffsetVL6 = prop_das(interface.SCHEME_OFFSET_VIRTUAL_LASER6)
    schemeOffsetVL7 = prop_das(interface.SCHEME_OFFSET_VIRTUAL_LASER7)
    schemeOffsetVL8 = prop_das(interface.SCHEME_OFFSET_VIRTUAL_LASER8)
    soaShutdownEnabled = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B, interface.INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W)
    state = prop_das(interface.SPECT_CNTRL_STATE_REGISTER)
    virtLaser = prop_das(interface.VIRTUAL_LASER_REGISTER)

    allowDither = prop_fpga(interface.FPGA_RDMAN, interface.RDMAN_OPTIONS, interface.RDMAN_OPTIONS_DITHER_ENABLE_B, interface.RDMAN_OPTIONS_DITHER_ENABLE_W)
    eta1_offset = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_ETA1_OFFSET)
    ref1_offset = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_REF1_OFFSET)
    eta2_offset = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_ETA2_OFFSET)
    ref2_offset = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_REF2_OFFSET)

    def __init__(self, sim):
        self.sim = sim
        self.das_registers = sim.das_registers
        self.fpga_registers = sim.fpga_registers
        self.schemeCounter = 0
        # incrCounter increments to incicate where a spectrum ends and a fit should take place. It interacts
        #  with the fit flag in schemes
        self.incrCounter = 0
        self.incrCounterNext = 0
        self.useMemo = 0
        self.prevState = interface.SPECT_CNTRL_IdleState
        self.rdParams = None
        self.incrFlag = 0
        self.iter = 0
        self.dwell = 0
        self.row = 0
        self.virtualTime = None
        self.wlmAngleSetpoint = None
        self.activeMemo = None
        self.rowMemo = None
        self.ratio1Center = None
        self.ratio2Center = None
        self.ratio1Multiplier = None
        self.ratio2Multiplier = None

    def setAutomaticLaserCurrentControl(self):
        self.sim.wrDasReg("LASER1_CURRENT_CNTRL_STATE_REGISTER", "LASER_CURRENT_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER2_CURRENT_CNTRL_STATE_REGISTER", "LASER_CURRENT_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER3_CURRENT_CNTRL_STATE_REGISTER", "LASER_CURRENT_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER4_CURRENT_CNTRL_STATE_REGISTER", "LASER_CURRENT_CNTRL_AutomaticState")
        # Setting the FPGA optical injection block to automatic mode has to be done independently
        #  of setting the individual current controllers. Care is needed since the current controllers
        #  periodically write to the INJECT_CONTROL register.
        self.injectControlMode = 1

    def setAutomaticLaserTemperatureControl(self):
        self.sim.wrDasReg("LASER1_TEMP_CNTRL_STATE_REGISTER", "TEMP_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER2_TEMP_CNTRL_STATE_REGISTER", "TEMP_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER3_TEMP_CNTRL_STATE_REGISTER", "TEMP_CNTRL_AutomaticState")
        self.sim.wrDasReg("LASER4_TEMP_CNTRL_STATE_REGISTER", "TEMP_CNTRL_AutomaticState")

    def setManualLaserCurrentControl(self):
        self.sim.wrDasReg("LASER1_CURRENT_CNTRL_STATE_REGISTER", "LASER_CURRENT_CNTRL_ManualState")
        self.sim.wrDasReg("LASER2_CURRENT_CNTRL_STATE_REGISTER", "LASER_CURRENT_CNTRL_ManualState")
        self.sim.wrDasReg("LASER3_CURRENT_CNTRL_STATE_REGISTER", "LASER_CURRENT_CNTRL_ManualState")
        self.sim.wrDasReg("LASER4_CURRENT_CNTRL_STATE_REGISTER", "LASER_CURRENT_CNTRL_ManualState")

    def step(self):
        stateAtStart = self.state
        if self.state == interface.SPECT_CNTRL_StartingState:
            # Start of a new scheme
            self.useMemo = 0
            self.incrCounterNext = self.incrCounter + 1
            self.schemeCounter += 1
            self.setAutomaticLaserTemperatureControl()
            self.setAutomaticLaserCurrentControl()
            self.state = interface.SPECT_CNTRL_RunningState
            if self.mode in [
                interface.SPECT_CNTRL_SchemeSingleMode,
                interface.SPECT_CNTRL_SchemeMultipleMode,
                interface.SPECT_CNTRL_SchemeMultipleNoRepeatMode,
            ]:
                # For schemes, enable frequency locking unless we are in FSR hopping mode
                if self.mode == interface.ANALYZER_TUNING_FsrHoppingTuningMode:
                    self.lockEnabled = 0
                else:
                    self.lockEnabled = 1
                self.iter = 0
                self.row = 0
                self.dwell = 0
                # When starting acquisition, go to scheme specified by next
                self.active = self.next
        elif self.state == interface.SPECT_CNTRL_StartManualState:
            # Start of a manual temperature control mode (no scheme)
            self.lockEnabled = 0
            self.useMemo = 0
            self.incrCounterNext = self.incrCounter + 1
            self.schemeCounter += 1
            self.mode = interface.SPECT_CNTRL_ContinuousManualTempMode
            self.setAutomaticLaserCurrentControl()
            self.state = interface.SPECT_CNTRL_RunningState
        elif self.state == interface.SPECT_CNTRL_RunningState:
            # Collect ringdowns
            if self.prevState in [
                interface.SPECT_CNTRL_StartingState,
                interface.SPECT_CNTRL_StartManualState,
                interface.SPECT_CNTRL_PausedState
            ]:
                self.switchToRampMode()
                self.laserShutdownEnabled = 1
                self.soaShutdownEnabled = 1
                self.sim.startRdcycle = True
        elif self.state == interface.SPECT_CNTRL_IdleState:
            if self.prevState != interface.SPECT_CNTRL_IdleState:
                self.switchToRampMode()
                self.setManualLaserCurrentControl()
            self.useMemo = False
        elif self.state == interface.SPECT_CNTRL_DiagnosticState:
            self.switchToRampMode()
            self.setAutomaticLaserCurrentControl()
        else:
            self.switchToRampMode()

        self.prevState = stateAtStart
        return interface.STATUS_OK

    def switchToRampMode(self):
        self.sim.tunerSimulator.switchToRampMode()

    def collectSpectrum(self, now):
        if self.state != interface.SPECT_CNTRL_RunningState:
            self.virtualTime = None
            self.sim.tunerSimulator.timestamp = None
            return
        if self.virtualTime is None:
            self.virtualTime = now
        if self.sim.tunerSimulator.timestamp is None:
            self.sim.tunerSimulator.timestamp = now
        else:
            while self.virtualTime < now:
                self.setupNextRdParams()
                self.virtualTime = self.doRingdown()
                if self.virtualTime is None:
                    break

    def doRingdown(self):
        self.advanceDwellCounter()
        #
        # We need to find the laser wavenumber range that can be achieved on the basis
        #  of the laser temperature, laser current and the specified
        #  wavelength monitor angle setpoint
        #
        etalonTemp = self.rdParams.etalonTemperature
        aLaserNum = 1 + ((self.rdParams.injectionSettings & interface.INJECTION_SETTINGS_actualLaserMask) >> interface.INJECTION_SETTINGS_actualLaserShift)
        coarseLaserCurrent = self.rdParams.coarseLaserCurrent
        laserSimulator = [
            self.sim.laser1Simulator,
            self.sim.laser2Simulator,
            self.sim.laser3Simulator,
            self.sim.laser4Simulator
        ][aLaserNum - 1]
        # Fetch the temperature setpoint and the actual temperature of the laser
        laserTempSetpoint = [
            self.laser1TempSetpoint,
            self.laser2TempSetpoint,
            self.laser3TempSetpoint,
            self.laser4TempSetpoint,
        ][aLaserNum - 1]
        laserTemperature = [
            self.laser1Temp,
            self.laser2Temp,
            self.laser3Temp,
            self.laser4Temp,
        ][aLaserNum - 1]
        if abs(laserTemperature-laserTempSetpoint) > 1.0:
            # print "Laser temperature difference too large"
            return None

        minCurrent = laserSimulator.getLaserCurrent(coarseLaserCurrent, fine=10000, laserOn=True)
        maxCurrent = laserSimulator.getLaserCurrent(coarseLaserCurrent, fine=55000, laserOn=True)
        maxWavenumber, _ = laserSimulator.getLaserOutput(current=minCurrent)
        minWavenumber, _ = laserSimulator.getLaserOutput(current=maxCurrent)
        wlmModel = self.sim.injectionSimulator.wlmModel
        minAngle = wlmModel.getWlmAngle(minWavenumber, etalonTemp, self.ambientPressure)
        maxAngle = wlmModel.getWlmAngle(maxWavenumber, etalonTemp, self.ambientPressure)
        # Need to determine if the wlmAngleSetpoint is within the angle range. Find wavenumber
        #  corresponding to the target angle
        # print "MinAngle %.3f, MaxAngle %.3f, AngleDiff %.3f, TargetAngle %.3f" % (minAngle, maxAngle, maxAngle-minAngle, self.wlmAngleSetpoint)
        #
        fine = 32768
        if self.lockEnabled:
            for _ in range(8):
                laserCurrent = laserSimulator.getLaserCurrent(coarseLaserCurrent, fine=fine, laserOn=True)
                wavenumber, power = laserSimulator.getLaserOutput(current=laserCurrent)
                wlmModel = self.sim.injectionSimulator.wlmModel
                eta1, ref1, eta2, ref2 = wlmModel.calcOutputs(wavenumber, power, etalonTemp, self.ambientPressure)
                ratio1 = (eta1 - self.eta1_offset) / (ref1 - self.ref1_offset)
                ratio2 = (eta2 - self.eta2_offset) / (ref2 - self.ref2_offset)
                lockError = self.ratio1Multiplier * (ratio1 - self.ratio1Center) + self.ratio2Multiplier * (ratio2 - self.ratio2Center)
                # print "Fine", fine, "LockError", lockError
                fine += 20000 * lockError
                if fine < 0 or fine > 65535:
                    print "Lock failed"
                    return None
        else:
            laserCurrent = laserSimulator.getLaserCurrent(coarseLaserCurrent, fine=fine, laserOn=True)
            wavenumber, power = laserSimulator.getLaserOutput(current=laserCurrent)
            wlmModel = self.sim.injectionSimulator.wlmModel
            eta1, ref1, eta2, ref2 = wlmModel.calcOutputs(wavenumber, power, etalonTemp, self.ambientPressure)
            ratio1 = (eta1 - self.eta1_offset) / (ref1 - self.ref1_offset)
            ratio2 = (eta2 - self.eta2_offset) / (ref2 - self.ref2_offset)

        vLaserParams = self.sim.driver.virtualLaserParams[self.virtLaser + 1]
        # Calculate the angle in the WLM plane, corrected by the ambienRampt pressure and etalon temperature
        arctanvar1 = (vLaserParams["ratio1Scale"] * (ratio2 - vLaserParams["ratio2Center"]) -
                      vLaserParams["ratio2Scale"] * (ratio1 - vLaserParams["ratio1Center"]) * math.sin(vLaserParams["phase"]))
        arctanvar2 = vLaserParams["ratio2Scale"] * (ratio1 - vLaserParams["ratio1Center"]) * math.cos(vLaserParams["phase"])
        # TODO: Add pressure correction
        thetaC = vLaserParams["tempSensitivity"] * (self.rdParams.etalonTemperature - vLaserParams["calTemp"]) + math.atan2(arctanvar1,arctanvar2)

        # Model the PZT
        cavityFsr = 0.0206
        pztThrow = 1.5*1.5e-4  # Maximum PZT motion in cm
        alpha = wavenumber / cavityFsr
        dz = 1.0 / (2 * cavityFsr * alpha * pztThrow)  # Separation between resonances in normalized PZT units
        z0 = dz * (math.ceil(alpha) - alpha)  # Smallest non-negative normalized PZT position for resonance
        z = z0
        # Calculate allowed tuner values that will lead to ringdowns
        allowedValues = []
        while z < 1.0:
            allowedValues.append(int(65536*z - self.fpgaPztOffset) % 65536)
            z += dz
        #
        # Find when the ringdown will occur
        result = self.sim.tunerSimulator.getNextAt(allowedValues, ["up"])
        if result is None:
            self.sim.tunerSimulator.switchToRampMode()
            result = self.sim.tunerSimulator.getNextAt(allowedValues, ["up"], self.virtualTime + 0.001 * self.ditherTimeout)
            if result is None:
                print "Ramp mode timeout"
                return self.virtualTime + 0.001 * (self.ditherTimeout + self.rampTimeout)
        tunerValue, slope, ts = result
        self.sim.tunerSimulator.value = tunerValue
        self.sim.tunerSimulator.slope = slope
        self.sim.tunerSimulator.timestamp = ts
        # Compute the loss using the spectral model here
        loss = 0.001 * self.sim.driver.spectraSimulator(wavenumber, self.cavityPressure, self.cavityTemperature)
        rdResult = interface.RingdownEntryType()
        rdResult.timestamp = int(ts)
        rdResult.wlmAngle = thetaC
        rdResult.uncorrectedAbsorbance = loss  # ppm/cm
        rdResult.correctedAbsorbance = loss  # ppm/cm
        rdResult.status = self.rdParams.status
        rdResult.count = self.rdParams.countAndSubschemeId >> 16
        rdResult.tunerValue = tunerValue
        rdResult.pztValue = (tunerValue + self.fpgaPztOffset) % 65536
        rdResult.laserUsed = self.rdParams.injectionSettings & (
            interface.INJECTION_SETTINGS_virtualLaserMask |
            interface.INJECTION_SETTINGS_actualLaserMask)
        rdResult.ringdownThreshold = self.rdParams.ringdownThreshold
        rdResult.subschemeId = self.rdParams.countAndSubschemeId & 0xFFFF
        rdResult.schemeVersionAndTable = self.rdParams.schemeTableAndRow >> 16
        rdResult.schemeRow = self.rdParams.schemeTableAndRow & 0xFFFF
        rdResult.ratio1 = int(32768 * ratio1)
        rdResult.ratio2 = int(32768 * ratio2)
        rdResult.fineLaserCurrent = int(fine)
        rdResult.coarseLaserCurrent = self.rdParams.coarseLaserCurrent
        rdResult.fitAmplitude = 50000
        rdResult.fitBackground = 100
        rdResult.fitRmsResidual = 10
        rdResult.laserTemperature = self.rdParams.laserTemperature
        rdResult.etalonTemperature = self.rdParams.etalonTemperature
        rdResult.cavityPressure = self.rdParams.cavityPressure
        self.sim.ringdown_queue.append(rdResult)
        # Check for transition to dither mode
        if self.allowDither:
            self.sim.tunerSimulator.switchToDitherMode(tunerValue)
        # Update the PZT centering if requested
        if (self.analyzerTuningMode == interface.ANALYZER_TUNING_CavityLengthTuningMode and
            0 != (rdResult.subschemeId & interface.SUBSCHEME_ID_RecenterMask)):
            pztOffset = [self.pztOffsetVL1,
                         self.pztOffsetVL2,
                         self.pztOffsetVL3,
                         self.pztOffsetVL4,
                         self.pztOffsetVL5,
                         self.pztOffsetVL6,
                         self.pztOffsetVL7,
                         self.pztOffsetVL8][self.virtLaser]
            pztOffset += self.pztOffsetUpdateFactor * (tunerValue - 32768)
            if pztOffset > 0.6 * self.pztIncrPerFsr:
                pztOffset -= self.pztIncrPerFsr
            elif pztOffset < -0.6 * self.pztIncrPerFsr:
                pztOffset += self.pztIncrPerFsr
            # print "pztOffset [VL %d] = %d" % (self.virtLaser+1, pztOffset)
            if self.virtLaser == 0:
                self.pztOffsetVL1 = pztOffset
            elif self.virtLaser == 1:
                self.pztOffsetVL2 = pztOffset
            elif self.virtLaser == 2:
                self.pztOffsetVL3 = pztOffset
            elif self.virtLaser == 3:
                self.pztOffsetVL4 = pztOffset
            elif self.virtLaser == 4:
                self.pztOffsetVL5 = pztOffset
            elif self.virtLaser == 5:
                self.pztOffsetVL6 = pztOffset
            elif self.virtLaser == 6:
                self.pztOffsetVL7 = pztOffset
            elif self.virtLaser == 7:
                self.pztOffsetVL8 = pztOffset
        return ts

    def setupLaserTemperatureAndPztOffset(self, useMemo):
        # The memo is used to bypass the setup if the scheme table and row have
        #  not changed since the last time ther laser temperature and PZT offset
        #  were set
        if self.mode == interface.SPECT_CNTRL_ContinuousMode:
            vLaserParams = self.sim.driver.virtualLaserParams[self.virtLaser + 1]
            pztOffset = [self.pztOffsetVL1,
                         self.pztOffsetVL2,
                         self.pztOffsetVL3,
                         self.pztOffsetVL4,
                         self.pztOffsetVL5,
                         self.pztOffsetVL6,
                         self.pztOffsetVL7,
                         self.pztOffsetVL8][self.virtLaser]
            self.fpgaPztOffset = pztOffset % 65536
        elif self.mode == interface.SPECT_CNTRL_ContinuousManualTempMode:
            self.fpgaPztOffset = 0
        else:
            if (self.useMemo and self.active == self.activeMemo and self.row == self.rowMemo):
                return
            scheme = self.sim.driver.schemeTables[self.active]
            schemeRow = scheme.rows[self.row]
            self.virtLaser = schemeRow.virtualLaser  # zero-origin
            vLaserParams = self.sim.driver.virtualLaserParams[self.virtLaser + 1]
            laserTemp = 0.001 * schemeRow.laserTemp  # scheme temperatures are in milli-degrees C
            aLaserNum = 1 + vLaserParams["actualLaser"] & 3
            if laserTemp != 0:
                schemeOffset = [self.schemeOffsetVL1,
                                self.schemeOffsetVL2,
                                self.schemeOffsetVL3,
                                self.schemeOffsetVL4,
                                self.schemeOffsetVL5,
                                self.schemeOffsetVL6,
                                self.schemeOffsetVL7,
                                self.schemeOffsetVL8][self.virtLaser]
                if aLaserNum == 1:
                    self.laser1TempSetpoint = laserTemp + schemeOffset
                elif aLaserNum == 2:
                    self.laser2TempSetpoint = laserTemp + schemeOffset
                elif aLaserNum == 3:
                    self.laser3TempSetpoint = laserTemp + schemeOffset
                elif aLaserNum == 4:
                    self.laser4TempSetpoint = laserTemp + schemeOffset
            # The PZT offset for this row is the sum of the PZT offset for the virtual laser from the appropriate
            #  register and any setpoint in the scheme file. Note that all PZT values are interpreted modulo 65536
            pztOffset = [self.pztOffsetVL1,
                         self.pztOffsetVL2,
                         self.pztOffsetVL3,
                         self.pztOffsetVL4,
                         self.pztOffsetVL5,
                         self.pztOffsetVL6,
                         self.pztOffsetVL7,
                         self.pztOffsetVL8][self.virtLaser] + schemeRow.pztSetpoint
            self.fpgaPztOffset = pztOffset % 65536
            self.activeMemo = self.active
            self.rowMemo = self.row

    def setupNextRdParams(self):
        self.incrCounter = self.incrCounterNext
        r = interface.RingdownParamsType()
        if self.mode == interface.SPECT_CNTRL_ContinuousMode:
            # In continuous mode, we run with the parameter values currently in the registers
            vLaserParams = self.sim.driver.virtualLaserParams[self.virtLaser + 1]
            laserNum = vLaserParams["actualLaser"] & 3  # zero-origin
            # Start filling out the ringdown parameters structure
            r.injectionSettings = ((self.virtLaser << interface.INJECTION_SETTINGS_virtualLaserShift) |
                                   (laserNum << interface.INJECTION_SETTINGS_actualLaserShift))
            r.laserTemperature = [self.laser1Temp, self.laser2Temp, self.laser3Temp, self.laser4Temp][laserNum]
            r.coarseLaserCurrent = int([self.laser1CoarseCurrent, self.laser2CoarseCurrent, self.laser3CoarseCurrent, self.laser4CoarseCurrent][laserNum])
            r.etalonTemperature = self.etalonTemperature
            r.cavityPressure = self.cavityPressure
            r.ambientPressure = self.ambientPressure
            r.schemeTableAndRow = 0
            r.countAndSubschemeId = (self.incrCounter << 16)
            r.ringdownThreshold = self.defaultThreshold
            r.status = 0
            self.laserSelect = laserNum
            self.ringdownThreshold = r.ringdownThreshold
        elif self.mode == interface.SPECT_CNTRL_ContinuousManualTempMode:
            # Get actual laser number from FPGA and virtual laser number from register
            #  In this way, if a virtual laser number is specified, it is used (for frequency conversion)
            #  but if not, it will still work.
            laserNum = self.laserSelect
            r.injectionSettings = ((self.virtLaser << interface.INJECTION_SETTINGS_virtualLaserShift) |
                                   (laserNum << interface.INJECTION_SETTINGS_actualLaserShift))
            r.laserTemperature = [self.laser1Temp, self.laser2Temp, self.laser3Temp, self.laser4Temp][laserNum]
            r.coarseLaserCurrent = int([self.laser1CoarseCurrent, self.laser2CoarseCurrent, self.laser3CoarseCurrent, self.laser4CoarseCurrent][laserNum])
            r.etalonTemperature = self.etalonTemperature
            r.cavityPressure = self.cavityPressure
            r.ambientPressure = self.ambientPressure
            r.schemeTableAndRow = 0
            r.countAndSubschemeId = 0
            r.ringdownThreshold = self.defaultThreshold
            r.status = 0
            self.ringdownThreshold = r.ringdownThreshold
        else:
            # We are running a scheme
            # print "Scheme %d: iter %d, row %d, dwell %d" % (self.active, self.iter, self.row, self.dwell)
            while True:
                #  This loop allows for zero-dwell rows in a scheme which just set the temperature
                #  of a laser without causing a ringdown

                self.setupLaserTemperatureAndPztOffset(self.useMemo)
                self.useMemo = 1
                self.scheme = self.sim.driver.schemeTables[self.active]
                schemeRow = self.scheme.rows[self.row]
                if schemeRow.dwellCount > 0:
                    break
                self.incrFlag = self.scheme.rows[self.row].subschemeId & interface.SUBSCHEME_ID_IncrMask
                self.advanceSchemeRow()
                self.incrCounter = self.incrCounterNext

            self.scheme = self.sim.driver.schemeTables[self.active]
            schemeRow = self.scheme.rows[self.row]
            self.virtLaser = schemeRow.virtualLaser  # zero-origin
            vLaserParams = self.sim.driver.virtualLaserParams[self.virtLaser + 1]
            self.wlmAngleSetpoint = schemeRow.setpoint
            laserNum = vLaserParams["actualLaser"] & 3  # zero-origin
            # We record the loss directly in a special set of 8 registers if the least-significant
            #  bits in the pztSetpoint field of the scheme are set appropriately
            lossTag = schemeRow.pztSetpoint & 7
            # Start filling out the ringdown parameters structure
            r.injectionSettings = ((lossTag << interface.INJECTION_SETTINGS_lossTagShift) |
                                (self.virtLaser << interface.INJECTION_SETTINGS_virtualLaserShift) |
                                (laserNum << interface.INJECTION_SETTINGS_actualLaserShift))
            r.laserTemperature = [self.laser1Temp, self.laser2Temp, self.laser3Temp, self.laser4Temp][laserNum]
            r.coarseLaserCurrent = int([self.laser1CoarseCurrent, self.laser2CoarseCurrent, self.laser3CoarseCurrent, self.laser4CoarseCurrent][laserNum])
            r.etalonTemperature = self.etalonTemperature
            r.cavityPressure = self.cavityPressure
            r.ambientPressure = self.ambientPressure
            r.schemeTableAndRow = (self.active << 16) | (self.row & 0xFFFF)
            # Check IncrMask in subscheme ID. If it is set, we should increment incrCounter
            #  the next time we advance to the next scheme row
            self.incrFlag = schemeRow.subschemeId & interface.SUBSCHEME_ID_IncrMask
            r.countAndSubschemeId = (self.incrCounter << 16) | (schemeRow.subschemeId & 0xFFFF)
            r.ringdownThreshold = schemeRow.threshold
            if r.ringdownThreshold == 0:
                r.ringdownThreshold = self.defaultThreshold
            r.status = self.schemeCounter & interface.RINGDOWN_STATUS_SequenceMask
            if self.mode in [interface.SPECT_CNTRL_SchemeSingleMode,
                            interface.SPECT_CNTRL_SchemeMultipleMode,
                            interface.SPECT_CNTRL_SchemeMultipleNoRepeatMode]:
                r.status |= interface.RINGDOWN_STATUS_SchemeActiveMask
            # Determine if this is the last ringdown of a scheme and set flags appropriately
            if ((self.iter >= self.scheme.numRepeats - 1 or self.mode == interface.SPECT_CNTRL_SchemeMultipleNoRepeatMode) and
                (self.row >= self.scheme.numRows - 1) and
                (self.dwell >= schemeRow.dwellCount -1)):
                # We need to decide if acquisition is continuing or not. Acquisition stops if the scheme is run in Single mode, or
                #  if we are running a non-looping sequence and have reached the last scheme in the sequence
                if self.mode == interface.SPECT_CNTRL_SchemeSingleMode:
                    r.status |= interface.RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask
                elif self.mode in [interface.SPECT_CNTRL_SchemeMultipleMode, interface.SPECT_CNTRL_SchemeMultipleNoRepeatMode]:
                    r.status |= interface.RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask
            # Correct the setpoint angle for temperature
            theta = schemeRow.setpoint - vLaserParams["tempSensitivity"] * (r.etalonTemperature - vLaserParams["calTemp"])
            # TODO: Add pressure dependence if needed
            # Compute ratio multipliers and ratio centers for laser locking
            minScale = min(vLaserParams["ratio1Scale"], vLaserParams["ratio2Scale"])
            self.ratio1Multiplier = -minScale * math.sin(theta + vLaserParams["phase"]) / vLaserParams["ratio1Scale"]
            self.ratio2Multiplier = minScale * math.cos(theta) / vLaserParams["ratio2Scale"]
            self.ratio1Center = vLaserParams["ratio1Center"]
            self.ratio2Center = vLaserParams["ratio2Center"]

            self.laserSelect = laserNum
            self.ringdownThreshold = r.ringdownThreshold

        self.rdParams = r

    def advanceDwellCounter(self):
        self.dwell += 1
        schemeRow = self.scheme.rows[self.row]
        if self.dwell >= schemeRow.dwellCount:
            self.advanceSchemeRow()

    def advanceSchemeRow(self):
        self.row += 1
        if self.incrFlag:
            self.incrCounterNext = self.incrCounter
            self.incrFlag = 0
        if self.row >= self.scheme.numRows:
            self.advanceSchemeIteration()
        else:
            self.dwell = 0

    def advanceSchemeIteration(self):
        self.iter += 1
        if self.iter >= self.scheme.numRepeats or self.mode == interface.SPECT_CNTRL_SchemeMultipleNoRepeatMode:
            self.advanceScheme()
        else:
            self.row = 0
            self.dwell = 0

    def advanceScheme(self):
        self.iter = 0
        self.dwell = 0
        self.row = 0
        if self.mode == interface.SPECT_CNTRL_SchemeSingleMode:
            self.state = interface.SPECT_CNTRL_IdleState
        # The next line causes the sequencer to load another scheme
        self.active = self.next
