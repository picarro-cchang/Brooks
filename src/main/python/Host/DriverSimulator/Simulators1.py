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

APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)


class Simulator(object):
    # Base class for simulators that are stepped by the scheduler
    def step(self):
        raise NotImplementedError("Must be overridden in subclass")


class LaserDacModel(object):
    # The relationship between laser current DACs and laser current in mA is
    #
    # current = 0.00036 * (10*coarse + 2*fine)
    # Thus for coarse = 36000 and fine = 32768, we have a current of 153.193 mA
    #  1mA of current change results from changing the coarse value by 277.78 digU
    #  or the fine value by 1388,89 digU
    def __init__(self, coarse_sens=0.0036, fine_sens=0.00072, offset=0):
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
                 nominal_wn=6237.0,
                 wn_temp_sens=-0.45808,
                 wn_current_sens=-0.035344,
                 thresh0=0.8,
                 char_temp=90.,
                 eff=0.17,
                 eff_temp_sens=-7e-4):
        self.nominal_wn = nominal_wn
        self.wn_temp_sens = wn_temp_sens
        self.wn_current_sens = wn_current_sens
        self.thresh0 = thresh0
        self.char_temp - char_temp
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
    def __init__(self,
                 num=None,
                 den=None,
                 offset=-40000,
                 thermA=0.00112789997365,
                 thermB=0.000234289997024,
                 thermC=8.72979981636e-08):
        """Represent the thermal characteristics of a laser as a ratio of z transforms
        and the thermistor by its Steinhart Hart coefficients"""
        if num is None:
            num = [
                0.00000000e+00, -2.98418514e-05, -1.01071361e-04, 6.39149028e-05, 5.23341031e-05, 2.66718772e-05, -1.01386506e-05,
                -9.73607948e-06
            ]
        self.num = num
        self.thermA = thermA
        if den is None:
            den = [
                1.00000000e+00, -1.37628382e+00, 2.19598434e-02, 1.01673929e-01, 2.99996581e-01, 2.93872141e-02, -7.45088401e-02,
                -1.42310788e-04
            ]
        self.den = den
        self.offset = offset
        assert len(num) == len(den)
        degree = len(num) - 1
        self.state = degree * [0.0]

    def initState(self):
        """Initialize the state to the steady-state associated with no TEC current"""
        degree = len(self.num) - 1
        ss_in = 32768
        ss_out = (ss_in + self.offset) * sum(self.num[0:degree + 1]) / sum(self.den[0:degree + 1])
        for i in reversed(xrange(degree)):
            self.state[i] = (ss_in + self.offset) * self.num[i + 1] - ss_out * self.den[i + 1]
            if i < degree - 1:
                self.state[i] += self.state[i + 1]

    def tecToTemp(self, tec, temp):
        degree = len(self.num) - 1
        divisor = self.den[0]
        assert divisor != 0.0
        temp = self.state[0] + (self.num[0] / divisor) * (tec + self.offset)
        for i in xrange(degree - 1):
            self.state[i] = self.state[i + 1] + (self.num[i + 1] * (tec + self.offset) - self.den[i + 1] * temp) / divisor
        self.state[degree - 1] = (self.num[degree] * (tec + self.offset) - self.den[degree] * temp) / divisor
        return temp

    def tempToResistance(self, temp):
        def cubeRoot(x):
            return x**(1.0 / 3.0)

        y = (self.thermA - 1.0 / (temp + 273.15)) / self.thermC
        x = math.sqrt((self.thermB / (3.0 * self.thermC))**3 + (y / 2.0)**2)
        return math.exp(cubeRoot(x - 0.5 * y) - cubeRoot(x + 0.5 * y))


class LaserSimulator(Simulator):
    tec = None
    thermRes = None
    currentMonitor = None
    fpgaCoarse = None
    fpgaFine = None

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
        self.nextThermRes = None

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


class InjectionSimulator(object):
    pass


class WlmModel(object):
    # This code simulates the behavior of the wavelength monitor. The wavelength monitor
    #  angle is theta and the etalon reflectivity factor is rho.
    # eta1 = rho * Ieta1 * (1 + cos(theta)) / (1 + rho * cos(theta)) + eta1_offset
    # ref1 = Iref1 * (1 - rho)/ (1 + rho * cos(theta)) + ref1_offset
    # eta2 = rho * Ieta2 * (1 + sin(theta + epsilon)) / (1 + rho * sin(theta + epsilon)) + eta2_offset
    # ref2 = Iref2 * (1 - rho)/ (1 + rho * sin(theta + epsilon)) + ref2_offset
    pass
