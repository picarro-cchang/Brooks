#!/usr/bin/python
#
"""
File Name: Simulators.py
Purpose: Simulators for analyzer components

File History:
    19-Sep-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""
import math

from Host.autogen import interface
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.DriverSimulator.Utilities import prop_das, prop_fpga
from Host.Common.SharedTypes import ctypesToDict
APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)

class Simulator(object):
    # Base class for simulators that are stepped by the scheduler. The step
    #  method of the simulator is run with lowest priority to compute all the
    #  values of the sensors on the next cycle. The update method is run with
    #  highest priority to place these values in the sensor registers

    def step(self):
        raise NotImplementedError("Must be overridden in subclass")

    def update(self):
        raise NotImplementedError("Must be overridden in subclass")


class LaserDacModel(object):
    # The relationship between laser current DACs and laser current in mA is
    #
    # current = 0.00036 * (10*coarse + 2*fine)
    # Thus for coarse = 36000 and fine = 32768, we have a current of 153.193 mA
    #  1mA of current change results from changing the coarse value by 277.78 digU
    #  or the fine value by 1388,89 digU
    def __init__(self, coarse_sens = 0.0036, fine_sens = 0.00072, offset = 0):
        self.coarse_sens = coarse_sens
        self.fine_sens = fine_sens
        self.offset = offset

    def dacToCurrent(self, coarse, fine):
        return self.offset + self.coarse_sens * coarse + self.fine_sens * fine


class LaserOpticalModel(object):
    # The default parameters are based on the following model implemented in the FPGA
    # When 5*coarse + fine changes by 65536, the laser frequency changes by
    #  one FSR of the wavelength monitor or 50GHz (1.66782 wavenumbers)
    # The sensitivity of the laser frequency to current is thus -1.0596 GHz/mA
    #  or -0.035344 wavenumber/mA
    #
    # When 18*laserTemp(in millidegrees) changes by 65536, the laser frequency
    #  changes by 50GHz. The sensitivity of the laser frequency to current is
    #  thus -13.7329 GHz/degree or -0.45808 wavenumber/degree
    #
    # The nominal frequency of the laser is attained at a laser current of 150mA
    #  and a laser temperature of 25 degC
    def __init__(self,
                 nominal_wn = 6237.0, wn_temp_sens = -0.45808, wn_current_sens = -0.035344,
                 thresh0 = 0.8, char_temp=90., eff=0.17, eff_temp_sens=-7e-4):
        self.nominal_wn = nominal_wn
        self.wn_temp_sens = wn_temp_sens
        self.wn_current_sens = wn_current_sens
        self.thresh0 = thresh0
        self.char_temp = char_temp
        self.eff = eff
        self.eff_temp_sens = eff_temp_sens

    def calcWavenumber(self, temp, current):
        """The wavenumber is given by a bilinear model. nominal_wn is the wavenumber produced
            at 25C and 150mA current. The wavenumber changes away from this operating point
            according to the wn_temp_sens (per degree C) and wn_current_sens (per mA)"""
        return self.nominal_wn + self.wn_temp_sens * (temp - 25.0) + self.wn_current_sens * (current - 150.0)

    def calcPower(self, temp, current):
        """The laser threshold is modelled as thresh (mA) = thresh0 * exp((273.15 + temp)/char_temp).
            At 25C the efficiency is eff, so the power output in mW is eff * (current - thresh).
            At other temperatures, the efficiency is corrected using eff_temp_sens"""
        thresh = self.thresh0 * math.exp((temp + 273.15) / self.char_temp)
        eff = self.eff + self.eff_temp_sens * (temp - 25.0)
        return eff * (current - thresh) if current > thresh else 0.0


class LaserThermalModel(object):
    def __init__(self, num=None, den=None, offset=-40000,
                 thermA=0.00112789997365, thermB=0.000234289997024, thermC=8.72979981636e-08):
        """Represent the thermal characteristics of a laser as a ratio of z transforms
        and the thermistor by its Steinhart Hart coefficients"""
        if num is None:
            num = [0.00000000e+00, -2.98418514e-05, -1.01071361e-04, 6.39149028e-05,
                   5.23341031e-05, 2.66718772e-05, -1.01386506e-05, -9.73607948e-06]
        self.num = num
        if den is None:
            den = [1.00000000e+00, -1.37628382e+00, 2.19598434e-02, 1.01673929e-01,
                   2.99996581e-01, 2.93872141e-02, -7.45088401e-02, -1.42310788e-04]
        self.den = den
        self.offset = offset
        assert len(num) == len(den)
        degree = len(num) - 1
        self.state = degree * [0.0]
        self.thermA = thermA
        self.thermB = thermB
        self.thermC = thermC
        self.initState()

    def initState(self):
        """Initialize the state to the steady-state associated with no TEC current"""
        degree = len(self.num) - 1
        ss_in = 32768
        ss_out = (ss_in + self.offset) * sum(self.num[0:degree + 1])/sum(self.den[0:degree + 1])
        for i in reversed(xrange(degree)):
            self.state[i] = (ss_in + self.offset) * self.num[i + 1] - ss_out * self.den[i + 1]
            if i < degree - 1:
                self.state[i] += self.state[i + 1]

    def tecToTemp(self, tec):
        degree = len(self.num) - 1
        divisor = self.den[0]
        assert divisor != 0.0
        temp = self.state[0] + (self.num[0] / divisor) * (tec + self.offset)
        for i in xrange(degree - 1):
            self.state[i] = self.state[i+1] + (self.num[i+1] * (tec + self.offset) - self.den[i+1]*temp) / divisor
        self.state[degree - 1] = (self.num[degree] * (tec + self.offset) - self.den[degree]*temp) / divisor
        return temp

    def tempToResistance(self, temp):
        def cubeRoot(x):
            return x ** (1.0/3.0)
        y = (self.thermA-1.0/(temp + 273.15))/self.thermC
        x = math.sqrt((self.thermB/(3.0*self.thermC))**3 + (y/2.0)**2)
        return math.exp(cubeRoot(x - 0.5*y) - cubeRoot(x + 0.5*y))


class WlmModel(object):
    # This code simulates the behavior of the wavelength monitor. The wavelength monitor
    #  angle is theta and the etalon reflectivity factor is rho.
    # eta1 = rho * Ieta1 * (1 + cos(theta)) / (1 + rho * cos(theta)) + eta1_offset
    # ref1 = Iref1 * (1 - rho)/ (1 + rho * cos(theta)) + ref1_offset
    # eta2 = rho * Ieta2 * (1 + sin(theta + epsilon)) / (1 + rho * sin(theta + epsilon)) + eta2_offset
    # ref2 = Iref2 * (1 - rho)/ (1 + rho * sin(theta + epsilon)) + ref2_offset
    def __init__(self, rho=0.2, Ieta1fac=3000, Ieta2fac=3000, Iref1fac=1500, Iref2fac=1500,
                 eta1_offset=6000, eta2_offset=6000, ref1_offset=6000, ref2_offset=6000, epsilon=0,
                 fsr=1.66782):
        self.rho = rho
        self.Ieta1fac = Ieta1fac
        self.Ieta2fac = Ieta2fac
        self.Iref1fac = Iref1fac
        self.Iref2fac = Iref2fac
        self.eta1_offset = eta1_offset
        self.eta2_offset = eta2_offset
        self.ref1_offset = ref1_offset
        self.ref2_offset = ref2_offset
        self.epsilon = epsilon
        self.fsr = fsr

    def calcOutputs(self, wavenumber, power):
        theta = 2 * math.pi * wavenumber / self.fsr
        ct = math.cos(theta)
        ste = math.sin(theta + self.epsilon)
        eta1 = self.rho * self.Ieta1fac * power * (1 + ct) / (1 + self.rho * ct) + self.eta1_offset
        ref1 = self.Iref1fac * power * (1 - self.rho) / (1 + self.rho * ct) + self.ref1_offset
        eta2 = self.rho * self.Ieta2fac * power * (1 + ste) / (1 + self.rho * ste) + self.eta2_offset
        ref2 = self.Iref2fac * power * (1 - self.rho) / (1 + self.rho * ste) + self.ref2_offset
        return eta1, ref1, eta2, ref2


class InjectionSimulator(Simulator):
    eta1Offset = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_ETA1_OFFSET)
    ref1Offset = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_REF1_OFFSET)
    eta2Offset = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_ETA2_OFFSET)
    ref2Offset = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_REF2_OFFSET)
    eta1 = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_ETA1)
    ref1 = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_REF1)
    eta2 = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_ETA2)
    ref2 = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_REF2)
    ratio1 = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_RATIO1)
    ratio2 = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_RATIO2)
    laserIndex = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER_SELECT_B, interface.INJECT_CONTROL_LASER_SELECT_W)

    def __init__(self, sim, wlmModel=None):
        self.sim = sim
        self.das_registers = sim.das_registers
        self.fpga_registers = sim.fpga_registers
        if wlmModel is None:
            wlmModel = WlmModel()
        assert isinstance(wlmModel, WlmModel)
        self.wlmModel = wlmModel
        self.nextEta1 = None
        self.nextEta2 = None
        self.nextRef1 = None
        self.nextRef2 = None
        self.nextRatio1 = None
        self.nextRatio2 = None

    def step(self):
        laserNum = self.laserIndex + 1
        laserSimulator = [self.sim.laser1Simulator, self.sim.laser2Simulator, self.sim.laser3Simulator, self.sim.laser4Simulator][laserNum - 1]
        wavenumber = laserSimulator.opticalModel.calcWavenumber(laserSimulator.nextTemp, laserSimulator.nextCurrentMonitor)
        power = laserSimulator.opticalModel.calcPower(laserSimulator.nextTemp, laserSimulator.nextCurrentMonitor)
        self.nextEta1, self.nextRef1, self.nextEta2, self.nextRef2 = self.wlmModel.calcOutputs(wavenumber, power)
        self.nextRatio1 = 32768 * float(self.nextEta1 - self.eta1Offset) / (self.nextRef1 - self.ref1Offset)
        self.nextRatio2 = 32768 * float(self.nextEta2 - self.eta2Offset) / (self.nextRef2 - self.ref2Offset)

    def update(self):
        if self.nextEta1 is not None:
            self.eta1 = self.nextEta1
        if self.nextEta2 is not None:
            self.eta2 = self.nextEta2
        if self.nextRef1 is not None:
            self.ref1 = self.nextRef1
        if self.nextRef2 is not None:
            self.ref2 = self.nextRef2
        if self.nextRatio1 is not None:
            self.ratio1 = self.nextRatio1
        if self.nextRatio2 is not None:
            self.ratio2 = self.nextRatio2


class LaserSimulator(Simulator):
    tec = None
    thermRes = None
    currentMonitor = None
    fpgaCoarse = None
    fpgaFine = None
    currentEnable = None
    laserEnable = None

    # This code simulates the behavior of a laser
    def __init__(self, sim, dacModel=None, opticalModel=None, thermalModel=None):
        self.sim = sim
        self.das_registers = sim.das_registers
        self.fpga_registers = sim.fpga_registers
        if dacModel is None:
            dacModel = LaserDacModel()
        assert isinstance(dacModel, LaserDacModel)
        self.dacModel = dacModel
        if opticalModel is None:
            opticalModel = LaserOpticalModel()
        assert isinstance(opticalModel, LaserOpticalModel)
        self.opticalModel = opticalModel
        if thermalModel is None:
            thermalModel = LaserThermalModel()
        assert isinstance(thermalModel, LaserThermalModel)
        self.thermalModel = thermalModel
        self.nextCurrentMonitor = None
        self.nextTemp = None
        self.nextThermRes = None

    def step(self):
        self.nextTemp = self.thermalModel.tecToTemp(self.tec)
        self.nextThermRes = self.thermalModel.tempToResistance(self.nextTemp)
        laserOn = self.currentEnable and self.laserEnable
        self.nextCurrentMonitor = self.dacModel.dacToCurrent(self.fpgaCoarse, self.fpgaFine) if laserOn else 0.0
        nextWavenumber = self.opticalModel.calcWavenumber(self.nextTemp, self.nextCurrentMonitor)
        nextPower = self.opticalModel.calcPower(self.nextTemp, self.nextCurrentMonitor)

    def update(self):
        if self.nextCurrentMonitor is not None:
            self.currentMonitor = self.nextCurrentMonitor
        if self.nextThermRes is not None:
            self.thermRes = self.nextThermRes


class Laser1Simulator(LaserSimulator):
    tec = prop_das(interface.LASER1_TEC_REGISTER)
    thermRes = prop_das(interface.LASER1_RESISTANCE_REGISTER)
    currentMonitor = prop_das(interface.LASER1_CURRENT_MONITOR_REGISTER)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER1_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER1_FINE_CURRENT)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER1_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER1_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER1_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER1_ENABLE_W)
    laserNum = 1


class Laser2Simulator(LaserSimulator):
    tec = prop_das(interface.LASER2_TEC_REGISTER)
    thermRes = prop_das(interface.LASER2_RESISTANCE_REGISTER)
    currentMonitor = prop_das(interface.LASER2_CURRENT_MONITOR_REGISTER)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER2_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER2_FINE_CURRENT)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER2_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER2_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER2_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER2_ENABLE_W)
    laserNum = 2


class Laser3Simulator(LaserSimulator):
    tec = prop_das(interface.LASER3_TEC_REGISTER)
    thermRes = prop_das(interface.LASER3_RESISTANCE_REGISTER)
    currentMonitor = prop_das(interface.LASER3_CURRENT_MONITOR_REGISTER)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER3_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER3_FINE_CURRENT)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER3_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER3_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER3_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER3_ENABLE_W)
    laserNum = 3


class Laser4Simulator(LaserSimulator):
    tec = prop_das(interface.LASER4_TEC_REGISTER)
    thermRes = prop_das(interface.LASER4_RESISTANCE_REGISTER)
    currentMonitor = prop_das(interface.LASER4_CURRENT_MONITOR_REGISTER)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER4_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER4_FINE_CURRENT)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER4_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER4_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER4_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER4_ENABLE_W)
    laserNum = 4


class SpectrumSimulator(Simulator):
    state = prop_das(interface.SPECT_CNTRL_STATE_REGISTER)
    mode = prop_das(interface.SPECT_CNTRL_MODE_REGISTER)
    active = prop_das(interface.SPECT_CNTRL_ACTIVE_SCHEME_REGISTER)
    next = prop_das(interface.SPECT_CNTRL_NEXT_SCHEME_REGISTER)
    iter = prop_das(interface.SPECT_CNTRL_SCHEME_ITER_REGISTER)
    row = prop_das(interface.SPECT_CNTRL_SCHEME_ROW_REGISTER)
    dwell = prop_das(interface.SPECT_CNTRL_DWELL_COUNT_REGISTER)
    defaultThreshold = prop_das(interface.SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER)
    analyzerTuningMode = prop_das(interface.ANALYZER_TUNING_MODE_REGISTER)
    virtLaser = prop_das(interface.VIRTUAL_LASER_REGISTER)
    ambientPressure = prop_das(interface.AMBIENT_PRESSURE_REGISTER)
    cavityPressure = prop_das(interface.CAVITY_PRESSURE_REGISTER)
    etalonTemperature = prop_das(interface.ETALON_TEMPERATURE_REGISTER)
    laser1Temp = prop_das(interface.LASER1_TEMPERATURE_REGISTER)
    laser2Temp = prop_das(interface.LASER2_TEMPERATURE_REGISTER)
    laser3Temp = prop_das(interface.LASER3_TEMPERATURE_REGISTER)
    laser4Temp = prop_das(interface.LASER4_TEMPERATURE_REGISTER)
    laser1CoarseCurrent = prop_das(interface.LASER1_MANUAL_COARSE_CURRENT_REGISTER)
    laser2CoarseCurrent = prop_das(interface.LASER2_MANUAL_COARSE_CURRENT_REGISTER)
    laser3CoarseCurrent = prop_das(interface.LASER3_MANUAL_COARSE_CURRENT_REGISTER)
    laser4CoarseCurrent = prop_das(interface.LASER4_MANUAL_COARSE_CURRENT_REGISTER)
    def __init__(self, sim):
        self.sim = sim
        self.das_registers = sim.das_registers
        self.fpga_registers = sim.fpga_registers
        self.spectrumControl = sim.spectrumControl
        self.incrFlag = 0
        self.iter = 0
        self.dwell = 0
        self.row = 0
        self.virtualTime = None

    def step(self):
        if self.state != interface.SPECT_CNTRL_RunningState:
            return
        now = self.sim.getDasTimestamp()
        if self.virtualTime is None:
            self.virtualTime = now
        else:
            while self.virtualTime < now:
                self.setupNextRdParams()
                self.doRingdown()

    def doRingdown(self):
        self.advanceDwellCounter()
        self.virtualTime += 10 # ms between ringdowns
        print "Performing ringdown"

    def setupNextRdParams(self):
        print "Scheme %d: iter %d, row %d, dwell %d" % (self.active, self.iter, self.row, self.dwell)

        while True:
            #  This loop allows for zero-dwell rows in a scheme which just set the temperature
            #  of a laser without causing a ringdown

            # self.setupLaserTemperatureAndPztOffset(self.sim.spectrumControl.useMemo)
            self.sim.spectrumControl.useMemo = 1
            self.scheme = self.sim.driver.schemeTables[self.active]
            schemeRow = self.scheme.rows[self.row]
            if schemeRow.dwellCount > 0:
                break
            self.incrFlag = self.scheme.rows[self.row].subschemeId & interface.SUBSCHEME_ID_IncrMask
            self.advanceSchemeRow()
            self.sim.spectrumControl.incrCounter = self.sim.spectrumControl.incrCounterNext

        self.scheme = self.sim.driver.schemeTables[self.active]
        schemeRow = self.scheme.rows[self.row]
        self.virtLaser = schemeRow.virtualLaser  # zero-origin
        vlaserParams = self.sim.driver.virtualLaserParams[self.virtLaser + 1]
        setpoint = schemeRow.setpoint
        laserNum = vlaserParams["actualLaser"] & 3  # zero-origin
        # We record the loss directly in a special set of 8 registers if the least-significant
        #  bits in the pztSetpoint field of the scheme are set appropriately
        lossTag = schemeRow.pztSetpoint & 7
        # Start filling out the ringdown result structure
        r = interface.RingdownParamsType()
        r.injectionSettings = ((lossTag << interface.INJECTION_SETTINGS_lossTagShift) |
                               (self.virtLaser << interface.INJECTION_SETTINGS_virtualLaserShift) |
                               (laserNum << interface.INJECTION_SETTINGS_actualLaserShift))
        r.laserTemperature = [self.laser1Temp, self.laser2Temp, self.laser3Temp, self.laser4Temp][laserNum]
        r.coarseLaserCurrent = int([self.laser1CoarseCurrent, self.laser2CoarseCurrent, self.laser3CoarseCurrent, self.laser4CoarseCurrent][laserNum])
        r.etalonTemperature = self.etalonTemperature
        r.cavityPressure = self.cavityPressure
        r.ambientPressure = self.ambientPressure
        r.schemeTableAndRow = (self.active << 16) | (self.row & 0xFFFF)
        laserTempAsInt = int(1000*r.laserTemperature)
        # Check IncrMask in subscheme ID. If it is set, we should increment incrCounter
        #  (in spectrumControl) the next time we advance to the next scheme row
        self.incrFlag = schemeRow.subschemeId & interface.SUBSCHEME_ID_IncrMask
        r.countAndSubschemeId = (self.sim.spectrumControl.incrCounter << 16) | (schemeRow.subschemeId & 0xFFFF)
        r.ringdownThreshold = schemeRow.threshold
        if r.ringdownThreshold == 0:
            r.ringdownThreshold = self.defaultThreshold
        r.status = self.sim.spectrumControl.schemeCounter & interface.RINGDOWN_STATUS_SequenceMask
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
                self.status |= interface.RINGDOWN_STATUS_SchemeCompleteAcqStoppingMask
            elif self.mode in [interface.SPECT_CNTRL_SchemeMultipleMode, interface.SPECT_CNTRL_SchemeMultipleNoRepeatMode]:
                self.status |= interface.RINGDOWN_STATUS_SchemeCompleteAcqContinuingMask


    def advanceDwellCounter(self):
        self.dwell += 1
        schemeRow = self.scheme.rows[self.row]
        if self.dwell >= schemeRow.dwellCount:
            self.advanceSchemeRow()

    def advanceSchemeRow(self):
        self.row += 1
        if self.incrFlag:
            self.spectrumControl.incrCounterNext = self.spectrumControl.incrCounter
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

    def update(self):
        print "Updating spectrum simulator"


class TunerSimulator(Simulator):
    sweepRampLow = prop_das(interface.TUNER_SWEEP_RAMP_LOW_REGISTER)
    sweepRampHigh = prop_das(interface.TUNER_SWEEP_RAMP_HIGH_REGISTER)
    windowRampLow = prop_das(interface.TUNER_WINDOW_RAMP_LOW_REGISTER)
    windowRampHigh = prop_das(interface.TUNER_WINDOW_RAMP_HIGH_REGISTER)
    sweepDitherLowOffset = prop_das(interface.TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER)
    sweepDitherHighOffset = prop_das(interface.TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER)
    windowDitherLowOffset = prop_das(interface.TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER)
    windowDitherHighOffset = prop_das(interface.TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER)
    ditherModeTimeout = prop_das(interface.SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER)
    rampModeTimeout = prop_das(interface.SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER)
    ditherModeTimeout = prop_das(interface.SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER)
    analyzerTuningMode = prop_das(interface.ANALYZER_TUNING_MODE_REGISTER)
    virtLaser = prop_das(interface.VIRTUAL_LASER_REGISTER)

    sweepLow = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_SWEEP_LOW)
    sweepHigh = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_SWEEP_HIGH)
    windowLow = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_WINDOW_LOW)
    windowHigh = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_WINDOW_HIGH)
    rampDitherMode = prop_fpga(interface.FPGA_RDMAN, interface.RDMAN_CONTROL, interface.RDMAN_CONTROL_RAMP_DITHER_B, interface.RDMAN_CONTROL_RAMP_DITHER_W)
    rdTimeout = prop_fpga(interface.FPGA_RDMAN, interface.RDMAN_TIMEOUT_DURATION)

    laserLockerTuningOffsetSelect = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_CS, interface.LASERLOCKER_CS_TUNING_OFFSET_SEL_B, interface.LASERLOCKER_CS_TUNING_OFFSET_SEL_W)
    directTune = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_OPTIONS, interface.LASERLOCKER_OPTIONS_DIRECT_TUNE_B, interface.LASERLOCKER_OPTIONS_DIRECT_TUNE_W)
    tunePzt = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_CS, interface.TWGEN_CS_TUNE_PZT_B, interface.TWGEN_CS_TUNE_PZT_W)

    def __init__(self, sim):
        self.sim = sim
        self.das_registers = sim.das_registers
        self.fpga_registers = sim.fpga_registers
        self.spectrumControl = sim.spectrumControl

    def switchToRampMode(self):
        self.sweepLow = self.sweepRampLow
        self.sweepHigh = self.sweepRampHigh
        self.windowLow = self.windowRampLow
        self.windowHigh = self.windowRampHigh
        self.rdTimeout = self.rampModeTimeout
        self.rampDitherMode = 0

    def switchToDitherMode(self, center):
        # Switch to dither mode centered about the given value, if this is possible. Otherwise
        #  go to ramp mode in the hope that a ringdown will then occur.
        sweepLow = int(center -  self.sweepDitherLowOffset) & 0xFFFF
        sweepHigh = int(center +  self.sweepDitherHighOffset) & 0xFFFF
        windowLow = int(center -  self.windowDitherLowOffset) & 0xFFFF
        windowHigh = int(center +  self.windowDitherHighOffset) & 0xFFFF
        if windowHigh > sweepHigh:
            windowHigh = sweepHigh
        if windowLow < sweepLow:
            windowLow = sweepLow
        if sweeepHigh > self.sweepRampHigh or sweepLow < self.sweepRampLow:
            self.switchToDitherMode()
        else:
            self.sweepLow = sweepLow
            self.sweepHigh = sweepHigh
            self.windowLow = windowLow
            self.windowHigh = windowHigh
            self.rdTimeout = self.ditherModeTimeout
            self.rampDitherMode = 1

    def setCavityLengthTuningMode(self):
        self.laserLockerTuningOffsetSelect = 0  # Use register
        self.directTune = 0  # Use laser locker for laser current control
        self.tunePzt = 1  # Connect PZT to tuner

    def setLaserCurrentTuningMode(self):
        self.laserLockerTuningOffsetSelect = 1  # Use tuner
        self.directTune = 0  # Use laser locker for laser current control
        self.tunePzt = 0  # Disconnect PZT from tuner

    def setFsrHoppingMode(self):
        self.laserLockerTuningOffsetSelect = 1  # Use tuner
        self.directTune = 1  # Use tuner for laser current control
        self.tunePzt = 0  # Disconnect PZT from tuner
