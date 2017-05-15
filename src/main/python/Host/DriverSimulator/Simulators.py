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
        self.coarse_sens = float(coarse_sens)
        self.fine_sens = float(fine_sens)
        self.offset = float(offset)

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
    #  changes by 50GHz. The sensitivity of the laser frequency to temperature is
    #  thus -13.7329 GHz/degree or -0.45808 wavenumber/degree
    #
    # The nominal frequency of the laser is attained at a laser current of 150mA
    #  and a laser temperature of 25 degC
    def __init__(self,
                 nominal_wn = 6237.0, wn_temp_sens = -0.45808, wn_current_sens = -0.035344,
                 thresh0 = 0.8, char_temp=90., eff=0.17, eff_temp_sens=-7e-4):
        self.nominal_wn = float(nominal_wn)
        self.wn_temp_sens = float(wn_temp_sens)
        self.wn_current_sens = float(wn_current_sens)
        self.thresh0 = float(thresh0)
        self.char_temp = float(char_temp)
        self.eff = float(eff)
        self.eff_temp_sens = float(eff_temp_sens)


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
        self.offset = float(offset)
        assert len(num) == len(den)
        degree = len(num) - 1
        self.state = degree * [0.0]
        self.thermA = float(thermA)
        self.thermB = float(thermB)
        self.thermC = float(thermC)
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
                 fsr=1.66782, cal_temp=45, temp_sensitivity=-0.19, cal_pressure=760,
                 pressureC0=0.0, pressureC1=0.0, pressureC2=0.0, pressureC3=0.0):
        self.rho = float(rho)
        self.Ieta1fac = float(Ieta1fac)
        self.Ieta2fac = float(Ieta2fac)
        self.Iref1fac = float(Iref1fac)
        self.Iref2fac = float(Iref2fac)
        self.eta1_offset = float(eta1_offset)
        self.eta2_offset = float(eta2_offset)
        self.ref1_offset = float(ref1_offset)
        self.ref2_offset = float(ref2_offset)
        self.epsilon = float(epsilon)
        self.fsr = float(fsr)
        self.cal_temp = float(cal_temp)
        self.temp_sensitivity = float(temp_sensitivity)
        self.cal_pressure = float(cal_pressure)
        self.pressureC0 = float(pressureC0)
        self.pressureC1 = float(pressureC1)
        self.pressureC2 = float(pressureC2)
        self.pressureC3 = float(pressureC3)

    def getWlmAngle(self, wavenumber, etalonTemp, ambientPressure):
        dP = ambientPressure - self.cal_pressure
        # Calculate the wavelength monitor angle corrected by the etalon temperature and ambient pressure
        return (2 * math.pi * wavenumber / self.fsr -
                self.temp_sensitivity * (etalonTemp - self.cal_temp) -
                (self.pressureC0 + dP * (self.pressureC1 + dP * (self.pressureC2 + dP * self.pressureC3))))

    def calcOutputs(self, wavenumber, power, etalonTemp, ambientPressure):
        # Get the wavelength monitor angle
        theta = self.getWlmAngle(wavenumber, etalonTemp, ambientPressure)
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
    etalonTemp = prop_das(interface.ETALON_TEMPERATURE_REGISTER)
    ambientPressure = prop_das(interface.AMBIENT_PRESSURE_REGISTER)

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
        wavenumber, power = laserSimulator.getLaserOutput()
        self.nextEta1, self.nextRef1, self.nextEta2, self.nextRef2 = self.wlmModel.calcOutputs(wavenumber, power, self.etalonTemp, self.ambientPressure)
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
    temp = None
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

    def getLaserCurrent(self, coarse=None, fine=None, laserOn=None):
        # Get the laser current for specified coarse and fine DAC settings and
        #  state of laserOn. If any argument is omitted, use the values presently
        #  found in the DAS registers.
        if laserOn is None:
            laserOn = self.isLaserOn()
        if coarse is None:
            coarse = self.fpgaCoarse
        if fine is None:
            fine = self.fpgaFine
        return self.dacModel.dacToCurrent(coarse, fine) if laserOn else 0.0

    def getLaserOutput(self, temp=None, current=None):
        # Return laser wavenumber and power for specified laser temperature
        #  and current. If any argument is omitted, use the values presently
        #  found in the DAS registers.
        if temp is None:
            temp = self.getLaserTemp()
        if current is None:
            current = self.getLaserCurrent()
        wavenumber = self.opticalModel.calcWavenumber(temp, current)
        power = self.opticalModel.calcPower(temp, current)
        return wavenumber, power

    def getLaserTemp(self):
        # Return current value of laser temperature
        return self.temp

    def isLaserOn(self):
        # Return if currently selected laser is on
        return self.currentEnable and self.laserEnable

    def step(self):
        # Note that we can only call tecToTemp once per step, since this
        #  advances the thermal model
        self.nextTemp = self.thermalModel.tecToTemp(self.tec)
        self.nextThermRes = self.thermalModel.tempToResistance(self.nextTemp)
        self.nextCurrentMonitor = self.getLaserCurrent()

    def update(self):
        if self.nextCurrentMonitor is not None:
            self.currentMonitor = self.nextCurrentMonitor
        if self.nextThermRes is not None:
            self.thermRes = self.nextThermRes


class Laser1Simulator(LaserSimulator):
    tec = prop_das(interface.LASER1_TEC_REGISTER)
    temp = prop_das(interface.LASER1_TEMPERATURE_REGISTER)
    thermRes = prop_das(interface.LASER1_RESISTANCE_REGISTER)
    currentMonitor = prop_das(interface.LASER1_CURRENT_MONITOR_REGISTER)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER1_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER1_FINE_CURRENT)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER1_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER1_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER1_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER1_ENABLE_W)
    laserNum = 1


class Laser2Simulator(LaserSimulator):
    tec = prop_das(interface.LASER2_TEC_REGISTER)
    temp = prop_das(interface.LASER2_TEMPERATURE_REGISTER)
    thermRes = prop_das(interface.LASER2_RESISTANCE_REGISTER)
    currentMonitor = prop_das(interface.LASER2_CURRENT_MONITOR_REGISTER)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER2_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER2_FINE_CURRENT)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER2_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER2_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER2_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER2_ENABLE_W)
    laserNum = 2


class Laser3Simulator(LaserSimulator):
    tec = prop_das(interface.LASER3_TEC_REGISTER)
    temp = prop_das(interface.LASER3_TEMPERATURE_REGISTER)
    thermRes = prop_das(interface.LASER3_RESISTANCE_REGISTER)
    currentMonitor = prop_das(interface.LASER3_CURRENT_MONITOR_REGISTER)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER3_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER3_FINE_CURRENT)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER3_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER3_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER3_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER3_ENABLE_W)
    laserNum = 3


class Laser4Simulator(LaserSimulator):
    tec = prop_das(interface.LASER4_TEC_REGISTER)
    temp = prop_das(interface.LASER4_TEMPERATURE_REGISTER)
    thermRes = prop_das(interface.LASER4_RESISTANCE_REGISTER)
    currentMonitor = prop_das(interface.LASER4_CURRENT_MONITOR_REGISTER)
    fpgaCoarse = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER4_COARSE_CURRENT)
    fpgaFine = prop_fpga(interface.FPGA_INJECT, interface.INJECT_LASER4_FINE_CURRENT)
    currentEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_LASER4_CURRENT_ENABLE_B, interface.INJECT_CONTROL_LASER4_CURRENT_ENABLE_W)
    laserEnable = prop_fpga(interface.FPGA_INJECT, interface.INJECT_CONTROL, interface.INJECT_CONTROL_MANUAL_LASER4_ENABLE_B, interface.INJECT_CONTROL_MANUAL_LASER4_ENABLE_W)
    laserNum = 4


class PressureSimulator(Simulator):
    cavityPressure = prop_das(interface.CAVITY_PRESSURE_REGISTER)
    cavityPressureAdc = prop_das(interface.CAVITY_PRESSURE_ADC_REGISTER)
    flow = prop_das(interface.FLOW1_REGISTER)
    inlet = prop_das(interface.VALVE_CNTRL_INLET_VALVE_REGISTER)
    outlet = prop_das(interface.VALVE_CNTRL_OUTLET_VALVE_REGISTER)

    def __init__(self, sim, inletMaxConductance=0.3, outletMaxConductance=2.0,
                 adcScale=6.92300018272e-05, adcOffset=0.0):
        self.sim = sim
        self.das_registers = sim.das_registers
        self.fpga_registers = sim.fpga_registers
        self.inletPressure = 760
        self.outletPressure = 5  # Pump base pressure
        self.inletMaxConductance = float(inletMaxConductance)
        self.outletMaxConductance = float(outletMaxConductance)
        self.nextFlow = 0.0
        self.nextPressure = 760
        self.dt = 0.2
        self.adcScale = float(adcScale)
        self.adcOffset = float(adcOffset)

    def valveModel(self, value, maxConductance, center=32768, range=4096):
        return 0.5*maxConductance*(1.0 + math.tanh(float((value - center) / range)))

    def step(self):
        inConductance = self.valveModel(self.inlet, self.inletMaxConductance)
        outConductance = self.valveModel(self.outlet, self.outletMaxConductance)
        inFlow = (self.inletPressure - self.cavityPressure) * inConductance
        outFlow = (self.cavityPressure - self.outletPressure) * outConductance
        self.nextFlow = inFlow
        self.nextPressure = self.cavityPressure + (inFlow - outFlow)*self.dt

    def update(self):
        self.flow = self.nextFlow
        self.cavityPressureAdc = (self.nextPressure - self.adcOffset)/self.adcScale


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

    slopeUp = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_SLOPE_UP)
    slopeDown = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_SLOPE_DOWN)
    sweepLow = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_SWEEP_LOW)
    sweepHigh = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_SWEEP_HIGH)
    windowLow = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_WINDOW_LOW)
    windowHigh = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_WINDOW_HIGH)
    rampDitherMode = prop_fpga(interface.FPGA_RDMAN, interface.RDMAN_CONTROL, interface.RDMAN_CONTROL_RAMP_DITHER_B, interface.RDMAN_CONTROL_RAMP_DITHER_W)
    rdTimeout = prop_fpga(interface.FPGA_RDMAN, interface.RDMAN_TIMEOUT_DURATION)

    laserLockerTuningOffsetSelect = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_CS, interface.LASERLOCKER_CS_TUNING_OFFSET_SEL_B, interface.LASERLOCKER_CS_TUNING_OFFSET_SEL_W)
    directTune = prop_fpga(interface.FPGA_LASERLOCKER, interface.LASERLOCKER_OPTIONS, interface.LASERLOCKER_OPTIONS_DIRECT_TUNE_B, interface.LASERLOCKER_OPTIONS_DIRECT_TUNE_W)
    tunePzt = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_CS, interface.TWGEN_CS_TUNE_PZT_B, interface.TWGEN_CS_TUNE_PZT_W)
    fpgaPztOffset = prop_fpga(interface.FPGA_TWGEN, interface.TWGEN_PZT_OFFSET)

    def __init__(self, sim):
        self.sim = sim
        self.das_registers = sim.das_registers
        self.fpga_registers = sim.fpga_registers
        self.spectrumControl = sim.spectrumControl
        self.timestamp = None
        self.slope = "up"  # or "down"
        self.value = (self.windowLow + self.windowHigh) // 2

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
        sweepLow = int(center - self.sweepDitherLowOffset) & 0xFFFF
        sweepHigh = int(center + self.sweepDitherHighOffset) & 0xFFFF
        windowLow = int(center - self.windowDitherLowOffset) & 0xFFFF
        windowHigh = int(center + self.windowDitherHighOffset) & 0xFFFF
        if windowHigh > sweepHigh:
            windowHigh = sweepHigh
        if windowLow < sweepLow:
            windowLow = sweepLow
        if sweepHigh > self.sweepRampHigh or sweepLow < self.sweepRampLow:
            self.switchToRampMode()
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

    def valueChange(self, slope, timeMs):
        """Find change in tuner value after `timeMs` ms at the given `slope`"""
        # Tuner accumulator has 9 extra bits of precision (512 times superresolution)
        # Each step takes 0.01ms
        return slope * timeMs * 100.0 / 512

    def timeRequired(self, change, slope):
        """Find time required (in ms) to change in tuner value by `change` at
         the given `slope`"""
        # Tuner accumulator has 9 extra bits of precision (512 times superresolution)
        # Each step takes 0.01ms
        #
        # Added the factor 0.25 to speed up the simulator for testing purposes.
        # See the Scheduler in DasSimulator.py.
        # RSF 15Feb2017
        #
        return 0.25 * change * 512 * 0.01 / slope

    def getStateAt(self, ts):
        """Get tuner value and slope at the specified timestamp `ts` in ms
            Note that the value of ts may be non-integral
        """
        sweep = self.sweepHigh - self.sweepLow
        sweepUpMs = self.timeRequired(sweep, self.slopeUp)
        sweepDownMs = self.timeRequired(sweep, self.slopeDown)
        periodMs = sweepUpMs + sweepDownMs
        #
        # Calculate the interval to the time requested modulo the period of the tuner
        #  waveform, giving a remainder
        #
        durationMs = ts - self.timestamp
        remainderMs = durationMs % periodMs
        if self.slope == "up":
            #
            #  If we are currently on the up slope, we hit sweepHigh after hitHighMs and
            #      sweepLow after hitHighMs + sweepDownMs.
            #
            #  ______________ sweepHigh
            #     /\
            #       \  /
            #  ______\/______ sweepLow
            #
            hitHighMs = self.timeRequired(self.sweepHigh - self.value, self.slopeUp)
            if remainderMs < hitHighMs:
                return self.value + self.valueChange(self.slopeUp, remainderMs), "up"
            elif remainderMs < hitHighMs + sweepDownMs:
                return self.sweepHigh - self.valueChange(self.slopeDown, remainderMs - hitHighMs), "down"
            else:
                return self.sweepLow + self.valueChange(self.slopeUp, remainderMs - hitHighMs - sweepDownMs), "up"
        else:
            #
            #  If we are currently on the down slope, we hit sweepLow after hitLowMs and
            #      sweepHigh after hitLowMs + sweepUpMs.
            #
            #  ______________ sweepHigh
            #       /\
            #      /  \
            #  __\/__________ sweepLow
            #
            hitLowMs = self.timeRequired(self.value - self.sweepLow, self.slopeDown)
            if remainderMs < hitLowMs:
                return self.value - self.valueChange(self.slopeDown, remainderMs), "down"
            elif remainderMs < hitLowMs + sweepUpMs:
                return self.sweepLow + self.valueChange(self.slopeUp, remainderMs - hitLowMs), "up"
            else:
                return self.sweepHigh - self.valueChange(self.slopeDown, remainderMs - hitLowMs - sweepUpMs), "down"

    def getNextAt(self, allowedValues, allowedSlopes, ts=None):
        """Find the timestamp (milliseconds) after ts (or the current time) when the tuner is next at one of the
            values in `allowedValues` with a slope in `allowedSlopes`. Return the timestamp, value and slope
            or None if the tuner will never reach this.
        """
        # Remove all values not within the window
        allowedValues = sorted([value for value in allowedValues if self.windowLow <= value <= self.windowHigh])
        if allowedValues and allowedSlopes:
            # Start the evolution from `value` and `slope` at the specified timestamp `ts`
            if ts is None:
                ts = self.timestamp
                slope = self.slope
                value = self.value
            else:
                value, slope = self.getStateAt(ts)
            #
            # Find first allowed value above and below the current value
            nextUp = None
            for av in allowedValues:
                if av > value:
                    nextUp = av
                    break
            nextDown = None
            for av in reversed(allowedValues):
                if av < value:
                    nextDown = av
                    break
            #
            sweep = self.sweepHigh - self.sweepLow
            if slope == "up":
                if "up" in allowedSlopes and nextUp is not None:
                    return nextUp, "up", ts + self.timeRequired(nextUp - value, self.slopeUp)
                hitHighMs = self.timeRequired(self.sweepHigh - value, self.slopeUp)
                if "down" in allowedSlopes:
                    return allowedValues[-1], "down", ts + hitHighMs + self.timeRequired(self.sweepHigh - allowedValues[-1], self.slopeDown)
                elif "up" in allowedSlopes:
                    sweepDownMs = self.timeRequired(sweep, self.slopeDown)
                    return allowedValues[0], "up", ts + hitHighMs + sweepDownMs + self.timeRequired(allowedValues[0] - self.sweepLow, self.slopeUp)
            elif slope == "down":
                if "down" in allowedSlopes and nextDown is not None:
                    return nextDown, "down", ts + self.timeRequired(value - nextDown, self.slopeDown)
                hitLowMs = self.timeRequired(value - self.sweepLow, self.slopeDown)
                if "up" in allowedSlopes:
                    return allowedValues[0], "up", ts + hitLowMs + self.timeRequired(allowedValues[0] - self.sweepLow, self.slopeUp)
                elif "down" in allowedSlopes:
                    sweepUpMs = self.timeRequired(sweep, self.slopeUp)
                    return allowedValues[-1], "down", ts + hitLowMs + sweepUpMs + self.timeRequired(self.sweepHigh - allowedValues[-1], self.slopeDown)
        return None


class WarmBoxThermalSimulator(Simulator):
    etalonResistance = prop_das(interface.ETALON_RESISTANCE_REGISTER)
    warmBoxTemperature = prop_das(interface.WARM_BOX_TEMPERATURE_REGISTER)

    def __init__(self, sim, thermA=0.00112789997365, thermB=0.000234289997024, thermC=8.72979981636e-08):
        # thermistor coefficients for etalon thermistor
        self.sim = sim
        self.das_registers = sim.das_registers
        """Represent the thermistor by its Steinhart Hart coefficients"""
        self.thermA = float(thermA)
        self.thermB = float(thermB)
        self.thermC = float(thermC)
        self.nextEtalonResistance = 5800.0

    def tempToResistance(self, temp):
        def cubeRoot(x):
            return x ** (1.0/3.0)
        y = (self.thermA-1.0/(temp + 273.15))/self.thermC
        x = math.sqrt((self.thermB/(3.0*self.thermC))**3 + (y/2.0)**2)
        return math.exp(cubeRoot(x - 0.5*y) - cubeRoot(x + 0.5*y))

    def step(self):
        self.nextEtalonResistance = self.tempToResistance(self.warmBoxTemperature)

    def update(self):
        self.etalonResistance = self.nextEtalonResistance

